"""Klien HTTP untuk backend FastAPI Apotek Pahala."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote

import requests

from app.core.config import DEFAULT_API_BASE, PREFS


class ApiError(RuntimeError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _extract_filename(header: str | None, fallback: str) -> str:
    if not header:
        return fallback
    match = re.search(r"filename\*=UTF-8''([^;]+)", header, re.IGNORECASE)
    if match:
        return unquote(match.group(1).strip())
    match = re.search(r"filename=\"?([^\";]+)\"?", header, re.IGNORECASE)
    if match:
        return unquote(match.group(1).strip())
    return fallback


def _detail_message(payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            parts = []
            for item in detail:
                if isinstance(item, dict):
                    location = ".".join(str(part) for part in item.get("loc", []) if part not in {"body", "query"})
                    message = str(item.get("msg", "Nilai tidak valid"))
                    parts.append(f"{location}: {message}" if location else message)
                else:
                    parts.append(str(item))
            return "; ".join(parts) or "Permintaan tidak valid."
        message = payload.get("message")
        if isinstance(message, str):
            return message
    if isinstance(payload, str) and payload.strip():
        return payload.strip()
    return "Permintaan tidak dapat diproses oleh server."


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or PREFS.base_url or DEFAULT_API_BASE).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "ApotekPahala-Desktop/1.0"})
        self.token = PREFS.token
        self.on_unauthorized: Callable[[], None] | None = None
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    # -- utilitas -------------------------------------------------------
    def set_base_url(self, value: str) -> None:
        self.base_url = value.strip().rstrip("/") or DEFAULT_API_BASE
        PREFS.base_url = self.base_url

    @property
    def server_root(self) -> str:
        if self.base_url.endswith("/api"):
            return self.base_url[:-4]
        return self.base_url

    def set_token(self, token: str | None) -> None:
        self.token = token or ""
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.session.headers.pop("Authorization", None)

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path == "/health":
            return f"{self.server_root}/health"
        if not path.startswith("/"):
            path = "/" + path
        if path.startswith("/api/"):
            return f"{self.server_root}{path}"
        return f"{self.base_url}{path}"

    def _handle(self, response: requests.Response) -> Any:
        if response.status_code == 401:
            if self.on_unauthorized:
                self.on_unauthorized()
            raise ApiError("Sesi Anda berakhir. Silakan masuk kembali.", 401)
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise ApiError(_detail_message(payload), response.status_code)
        if response.status_code == 204:
            return None
        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        try:
            return response.json()
        except ValueError:
            return response.text

    def _request(self, method: str, path: str, timeout: float = 45, **kwargs: Any) -> Any:
        try:
            response = self.session.request(method, self._url(path), timeout=timeout, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            raise ApiError(
                "Tidak dapat terhubung ke server Apotek Pahala. Pastikan backend berjalan di "
                f"{self.server_root}.",
                0,
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise ApiError("Server tidak merespons tepat waktu. Coba lagi beberapa saat.", 0) from exc
        except requests.exceptions.RequestException as exc:
            raise ApiError(f"Gagal menghubungi server: {exc}", 0) from exc
        return self._handle(response)

    # -- metode HTTP ----------------------------------------------------
    def get(self, path: str, params: dict | None = None, timeout: float = 45) -> Any:
        return self._request("GET", path, params=params, timeout=timeout)

    def post(self, path: str, json: dict | None = None, timeout: float = 90) -> Any:
        return self._request("POST", path, json=json, timeout=timeout)

    def put(self, path: str, json: dict | None = None, timeout: float = 45) -> Any:
        return self._request("PUT", path, json=json, timeout=timeout)

    def patch(self, path: str, json: dict | None = None, timeout: float = 45) -> Any:
        return self._request("PATCH", path, json=json, timeout=timeout)

    def delete(self, path: str, timeout: float = 45) -> Any:
        return self._request("DELETE", path, timeout=timeout)

    def post_form(self, path: str, data: dict, files: dict | None = None, timeout: float = 90) -> Any:
        return self._request("POST", path, data=data, files=files, timeout=timeout)

    # -- autentikasi ----------------------------------------------------
    def login(self, username: str, password: str) -> dict:
        payload = self._request(
            "POST",
            "/auth/login",
            data={"username": username.strip(), "password": password},
            timeout=20,
        )
        token = payload.get("access_token", "")
        self.set_token(token)
        return payload

    def me(self) -> dict:
        return self._request("GET", "/auth/me", timeout=15)

    def health(self) -> dict:
        return self._request("GET", "/health", timeout=5)

    def logout_remote(self) -> None:
        try:
            self._request("POST", "/auth/logout", timeout=8)
        except ApiError:
            pass

    def clear_session(self, forget_token: bool = True) -> None:
        self.set_token("")
        if forget_token:
            PREFS.token = ""

    # -- unduhan & unggahan --------------------------------------------
    def download(self, path: str, fallback_name: str, params: dict | None = None) -> tuple[bytes, str]:
        try:
            response = self.session.get(self._url(path), params=params, timeout=120)
        except requests.exceptions.RequestException as exc:
            raise ApiError("Unduhan gagal: koneksi ke server terputus.") from exc
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise ApiError(_detail_message(payload), response.status_code)
        name = _extract_filename(response.headers.get("Content-Disposition"), fallback_name)
        return response.content, name

    def upload(self, path: str, file_path: str | Path, fields: dict | None = None, timeout: float = 180) -> Any:
        source = Path(file_path)
        try:
            with source.open("rb") as handle:
                files = {"file": (source.name, handle, "application/octet-stream")}
                return self._request("POST", path, data=fields or {}, files=files, timeout=timeout)
        except OSError as exc:
            raise ApiError(f"Berkas tidak dapat dibaca: {exc}") from exc


def save_download(content: bytes, target_dir: Path, suggested_name: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / suggested_name
    stem, suffix = target.stem, target.suffix
    counter = 2
    while target.exists():
        target = target_dir / f"{stem} ({counter}){suffix}"
        counter += 1
    target.write_bytes(content)
    return target
