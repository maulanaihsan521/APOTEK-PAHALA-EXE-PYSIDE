"""Eksekusi permintaan jaringan tanpa membekukan antarmuka."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from app.core.api import ApiError


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str, int)
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self.fn = fn
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            value = self.fn()
        except ApiError as exc:
            self.signals.error.emit(exc.message, exc.status or 0)
        except Exception as exc:  # noqa: BLE001 - ditampilkan sebagai pesan ramah
            self.signals.error.emit(str(exc) or exc.__class__.__name__, -1)
        else:
            self.signals.result.emit(value)
        finally:
            self.signals.finished.emit()


class AsyncRunner(QObject):
    """Pengelola tugas latar belakang; hasil dikirim kembali ke thread UI."""

    def __init__(self, parent: QObject | None = None, max_threads: int = 6) -> None:
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(max_threads)
        self._active: set[Worker] = set()

    def submit(
        self,
        fn: Callable[[], Any],
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[str, int], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> Worker:
        worker = Worker(fn)
        if on_result is not None:
            worker.signals.result.connect(on_result)
        if on_error is not None:
            worker.signals.error.connect(on_error)
        if on_finished is not None:
            worker.signals.finished.connect(on_finished)
        worker.signals.finished.connect(lambda: self._active.discard(worker))
        self._active.add(worker)
        self.pool.start(worker)
        return worker

    def shutdown(self) -> None:
        self.pool.clear()
        self.pool.waitForDone(2500)
