"""Deteksi dan jalankan backend lokal dari aplikasi desktop."""
from __future__ import annotations

import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from app.core.config import BACKEND_DIR


class BackendLauncher(QObject):
    ready = Signal(str)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process: QProcess | None = None
        self._attempts = 0
        self._timer = QTimer(self)
        self._timer.setInterval(900)
        self._timer.timeout.connect(self._probe)
        self._base_root = "http://127.0.0.1:8000"
        self._output_tail: list[str] = []

    @staticmethod
    def is_local(url: str) -> bool:
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            return False
        return host in {"127.0.0.1", "localhost", "::1", "0.0.0.0"}

    @staticmethod
    def healthy(url: str, timeout: float = 2.0) -> bool:
        try:
            parsed = urlparse(url)
            root = f"{parsed.scheme or 'http'}://{parsed.netloc or '127.0.0.1:8000'}"
            response = requests.get(f"{root}/api/health", timeout=timeout)
            return response.status_code == 200 and response.json().get("status") == "ok"
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def port_open(host: str = "127.0.0.1", port: int = 8000, timeout: float = 0.35) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def start(self, api_url: str) -> None:
        parsed = urlparse(api_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8000
        self._base_root = f"{parsed.scheme or 'http'}://{host}:{port}"
        self._attempts = 0
        self._output_tail.clear()

        if self.healthy(f"{self._base_root}/api"):
            self.status.emit("Backend sudah berjalan.")
            self.ready.emit(self._base_root)
            return

        if self.port_open(host, port):
            # Port hidup tetapi health belum siap (mis. sedang startup).
            self.status.emit("Menunggu backend selesai memuat...")
            self._timer.start()
            return

        run_script = BACKEND_DIR / "run.py"
        if not run_script.exists():
            self.failed.emit(
                f"Berkas backend tidak ditemukan di {run_script}. Jalankan backend secara manual."
            )
            return

        if self.process is None:
            self.process = QProcess(self)
            self.process.setWorkingDirectory(str(BACKEND_DIR))
            self.process.setProgram(sys.executable)
            self.process.setArguments(["run.py", "--host", host, "--port", str(port)])
            self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            self.process.readyReadStandardOutput.connect(self._read_output)
            self.process.finished.connect(self._on_process_finished)

        self.status.emit("Menjalankan backend lokal...")
        self.process.start()
        self._timer.start()

    def _read_output(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        for line in data.splitlines():
            if line.strip():
                self._output_tail.append(line.strip())
                self._output_tail = self._output_tail[-12:]

    def _on_process_finished(self, code: int, _status) -> None:
        if self._timer.isActive():
            self._timer.stop()
            detail = " | ".join(self._output_tail[-3:]) or f"kode keluar {code}"
            self.failed.emit(f"Backend berhenti sebelum siap. {detail}")

    def _probe(self) -> None:
        self._attempts += 1
        if self.healthy(f"{self._base_root}/api", timeout=1.2):
            self._timer.stop()
            self.status.emit("Backend siap digunakan.")
            self.ready.emit(self._base_root)
            return
        if self._attempts >= 26:
            self._timer.stop()
            detail = " | ".join(self._output_tail[-3:])
            self.failed.emit(
                "Backend tidak merespons setelah 23 detik. " + (detail or "Periksa terminal backend.")
            )

    def stop(self) -> None:
        self._timer.stop()
        if self.process:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
            self.process = None
