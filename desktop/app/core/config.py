"""Konfigurasi aplikasi desktop Apotek Pahala."""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths

APP_NAME = "Apotek Pahala"
APP_SUBTITLE = "Pharmacy Intelligence"
APP_VERSION = "1.0.0"
APP_YEAR = "2026"
DEVELOPER = "Capstone Project — Teknik Universitas"

DESKTOP_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = DESKTOP_DIR.parent
ASSETS_DIR = DESKTOP_DIR / "app" / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
LOGO_PATH = ASSETS_DIR / "logo.png"
BACKEND_DIR = ROOT_DIR / "backend"

DEFAULT_API_BASE = os.getenv("APOTEK_API_BASE", "http://127.0.0.1:8000/api").rstrip("/")

DISPLAY_MODES = ("light", "dark", "auto")
FONT_SCALES = {"small": 0.92, "normal": 1.0, "large": 1.1}

MONTHS_ID = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}
MONTHS_ID_LONG = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


class Preferences:
    """Penyimpanan preferensi lokal (registry Windows melalui QSettings)."""

    def __init__(self) -> None:
        self._settings = QSettings("ApotekPahala", "PharmacyIntelligenceDesktop")
        if not self._settings.contains("server/base_url"):
            self._settings.setValue("server/base_url", DEFAULT_API_BASE)

    # -- server ---------------------------------------------------------
    @property
    def base_url(self) -> str:
        value = str(self._settings.value("server/base_url", DEFAULT_API_BASE)).strip().rstrip("/")
        return value or DEFAULT_API_BASE

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._settings.setValue("server/base_url", value.strip().rstrip("/"))

    # -- sesi -----------------------------------------------------------
    @property
    def token(self) -> str:
        return str(self._settings.value("session/token", "") or "")

    @token.setter
    def token(self, value: str) -> None:
        self._settings.setValue("session/token", value or "")

    @property
    def last_username(self) -> str:
        return str(self._settings.value("session/last_username", "") or "")

    @last_username.setter
    def last_username(self, value: str) -> None:
        self._settings.setValue("session/last_username", value or "")

    @property
    def remember_session(self) -> bool:
        value = self._settings.value("session/remember", True)
        return str(value).lower() in {"1", "true", "yes"}

    @remember_session.setter
    def remember_session(self, value: bool) -> None:
        self._settings.setValue("session/remember", bool(value))

    # -- tampilan -------------------------------------------------------
    @property
    def theme(self) -> str:
        return str(self._settings.value("display/theme", "light") or "light")

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings.setValue("display/theme", value)

    @property
    def font_scale(self) -> str:
        return str(self._settings.value("display/font_scale", "normal") or "normal")

    @font_scale.setter
    def font_scale(self, value: str) -> None:
        self._settings.setValue("display/font_scale", value)

    # -- jendela --------------------------------------------------------
    @property
    def geometry(self) -> bytes:
        value = self._settings.value("window/geometry")
        return value if isinstance(value, bytes) else b""

    @geometry.setter
    def geometry(self, value: bytes) -> None:
        self._settings.setValue("window/geometry", value)

    @property
    def window_state(self) -> bytes:
        value = self._settings.value("window/state")
        return value if isinstance(value, bytes) else b""

    @window_state.setter
    def window_state(self, value: bytes) -> None:
        self._settings.setValue("window/state", value)

    def sync(self) -> None:
        self._settings.sync()


PREFS = Preferences()


def downloads_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    path = Path(location) if location else Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path
