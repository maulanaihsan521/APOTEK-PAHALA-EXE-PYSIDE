"""Penjalan aplikasi desktop Apotek Pahala — Pharmacy Intelligence."""
from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

DESKTOP_DIR = Path(__file__).resolve().parent
if str(DESKTOP_DIR) not in sys.path:
    sys.path.insert(0, str(DESKTOP_DIR))


def _configure_qt5_scaling() -> bool:
    """Samakan skala Qt5 dengan Qt6 pada Windows yang memakai text scaling.

    Qt6 otomatis memperbesar seluruh antarmuka mengikuti penskalaan Windows.
    Qt5 hanya memperbesar font berbasis poin sehingga tabel dan baris tombol
    dapat melebihi lebar halaman. Pada build PySide2, QT_SCALE_FACTOR dipakai
    agar ukuran jendela dan tata letak sama dengan build sumber.
    """
    try:
        import PySide2  # noqa: F401
    except ImportError:
        return False
    if sys.platform != "win32" or os.environ.get("QT_SCALE_FACTOR"):
        return True
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics"
        ) as key:
            dpi = int(winreg.QueryValueEx(key, "AppliedDPI")[0])
    except (OSError, ValueError, TypeError):
        return True
    if dpi > 96:
        scale = f"{dpi / 96:.3f}".rstrip("0").rstrip(".")
        os.environ["QT_SCALE_FACTOR"] = scale
    return True


QT5 = _configure_qt5_scaling()

from PySide6.QtCore import QStandardPaths, Qt  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, LOGO_PATH, PREFS  # noqa: E402
from app.core.theme import theme  # noqa: E402
from app.main import MainWindow  # noqa: E402


def _log_path() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    base = Path(location) if location else Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ApotekPahala"
    base.mkdir(parents=True, exist_ok=True)
    return base / "desktop-error.log"


def _install_exception_hook() -> None:
    def handle(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        detail = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            with _log_path().open("a", encoding="utf-8") as handle_file:
                handle_file.write(f"\n[{datetime.now().isoformat(timespec='seconds')}]\n{detail}\n")
        except OSError:
            pass
        app = QApplication.instance()
        if app is not None:
            box = QMessageBox()
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle(f"{APP_NAME} — Kesalahan")
            box.setText("Terjadi kesalahan tak terduga pada antarmuka desktop.")
            box.setInformativeText(f"{exc_type.__name__}: {exc_value}")
            box.setDetailedText(detail)
            box.exec()
        else:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "ApotekPahala.PharmacyIntelligence.Desktop.1"
            )
        except Exception:  # noqa: BLE001 - tidak fatal pada sistem non-Windows
            pass

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
    if QT5 and hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(f"{APP_NAME} — {APP_SUBTITLE}")
    app.setOrganizationName("ApotekPahala")
    app.setOrganizationDomain("apotekpahala.local")
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))
    _install_exception_hook()

    theme.apply(app, PREFS.theme, PREFS.font_scale)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
