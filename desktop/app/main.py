"""Jendela utama dan kerangka aplikasi desktop Apotek Pahala."""
from __future__ import annotations

from typing import Any

import requests
from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import ConfirmDialog
from app.components.layout import NotificationDialog, Sidebar, TitleBar, TopBar
from app.components.widgets import ToastManager
from app.core.api import ApiClient
from app.core.async_worker import AsyncRunner
from app.core.backend import BackendLauncher
from app.core.config import APP_NAME, APP_SUBTITLE, PREFS
from app.core.icons import icon
from app.core.theme import theme
from app.core.utils import format_date, initials
from app.pages.dashboard import DashboardPage
from app.pages.login import LoginPage
from app.pages.prediction import PredictionPage
from app.pages.procurement import ProcurementPage
from app.pages.reports import ReportsPage
from app.pages.sales import SalesPage
from app.pages.settings import SettingsPage
from app.pages.stock import StockPage
from app.pages.weather import WeatherPage

PAGE_META: dict[str, tuple[str, str]] = {
    "dashboard": (
        "Ringkasan Apotek",
        "Pantau permintaan, persediaan, dan prediksi kebutuhan apotek.",
    ),
    "prediction": (
        "Prediksi Permintaan",
        "Prakiraan kebutuhan obat dari permintaan historis dan cuaca.",
    ),
    "sales": (
        "Data Penjualan",
        "Kelola data permintaan, transaksi manual, impor, dan ekspor laporan.",
    ),
    "weather": (
        "Data Cuaca",
        "Riwayat cuaca harian sebagai faktor pendukung model prediksi.",
    ),
    "stock": (
        "Manajemen Stok",
        "Pantau persediaan, batas minimum, dan pergerakan stok obat.",
    ),
    "procurement": (
        "Rekomendasi Pengadaan",
        "Usulan pembelian dari prakiraan permintaan dan kondisi stok terkini.",
    ),
    "reports": (
        "Laporan",
        "Susun, tinjau, dan ekspor laporan operasional apotek.",
    ),
    "settings": (
        "Pengaturan",
        "Profil, tampilan, model, database, dan akun pengguna.",
    ),
}

ROLE_LABELS = {"admin": "Admin", "petugas": "Petugas"}


class AppShell(QWidget):
    """Kerangka setelah login: sidebar, top bar, dan seluruh halaman modul."""

    logout_requested = Signal()
    theme_requested = Signal(str)
    font_scale_requested = Signal(str)
    profile_changed = Signal(dict)
    server_changed = Signal()

    def __init__(self, api: ApiClient, runner: AsyncRunner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AppRoot")
        self.api = api
        self.runner = runner
        self.user = dict(user)
        self.is_admin = str(self.user.get("role", "")).lower() == "admin"
        self._notif_serial = 0

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = Sidebar(self)
        outer.addWidget(self.sidebar)

        right = QWidget(self)
        right.setObjectName("AppRoot")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.topbar = TopBar(right)
        right_layout.addWidget(self.topbar)
        self.stack = QStackedWidget(right)
        self.stack.setObjectName("PageStack")
        right_layout.addWidget(self.stack, 1)
        outer.addWidget(right, 1)

        self.pages: dict[str, QWidget] = {
            "dashboard": DashboardPage(api, runner, self.user, self),
            "prediction": PredictionPage(api, runner, self.user, self),
            "sales": SalesPage(api, runner, self.user, self),
            "weather": WeatherPage(api, runner, self.user, self),
            "stock": StockPage(api, runner, self.user, self),
            "procurement": ProcurementPage(api, runner, self.user, self),
            "reports": ReportsPage(api, runner, self.user, self),
            "settings": SettingsPage(api, runner, self.user, self),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.dashboard: DashboardPage = self.pages["dashboard"]  # type: ignore[assignment]
        self.settings: SettingsPage = self.pages["settings"]  # type: ignore[assignment]

        self.sidebar.set_mode(PREFS.theme)
        self.topbar.set_user(
            self.user.get("full_name") or self.user.get("username", "Pengguna"),
            ROLE_LABELS.get(str(self.user.get("role", "")).lower(), str(self.user.get("role", "")).title()),
            initials(self.user.get("full_name") or self.user.get("username", "")),
        )
        self.sidebar.nav_selected.connect(self.navigate)
        self.sidebar.theme_mode_changed.connect(self._theme_from_sidebar)
        self.topbar.period_clicked.connect(self._open_period)
        self.topbar.notifications_clicked.connect(self._open_notifications)
        self.topbar.user_menu_requested.connect(self._open_user_menu)
        self.dashboard.navigate.connect(self.navigate)
        self.dashboard.period_changed.connect(self._period_ready)
        self.pages["prediction"].navigate.connect(self.navigate)  # type: ignore[attr-defined]
        self.settings.theme_changed.connect(self._theme_from_settings)
        self.settings.font_scale_changed.connect(self.font_scale_requested.emit)
        self.settings.logout_requested.connect(self.logout_requested.emit)
        self.settings.profile_changed.connect(self._profile_saved)
        self.settings.server_changed.connect(self.server_changed.emit)

        self.topbar.set_period(f"{self.dashboard.weeks} minggu terakhir")
        self.topbar.set_page(*PAGE_META["dashboard"])

        self._notif_timer = QTimer(self)
        self._notif_timer.setInterval(60_000)
        self._notif_timer.timeout.connect(self.refresh_notifications)
        self._notif_timer.start()
        QTimer.singleShot(700, self.refresh_notifications)

    # ------------------------------------------------------------------
    # Navigasi
    # ------------------------------------------------------------------
    def navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)
        self.topbar.set_page(*PAGE_META.get(key, ("Apotek Pahala", "")))
        self.topbar.period.setVisible(key == "dashboard")
        if key == "dashboard":
            self._period_ready(getattr(self.dashboard, "_period", {}) or {})
        self.refresh_notifications()

    def _open_period(self) -> None:
        self.dashboard.period_clicked()
        if self.stack.currentWidget() is self.dashboard:
            self.topbar.set_period(f"{self.dashboard.weeks} minggu terakhir")

    def _period_ready(self, period: dict) -> None:
        if not isinstance(period, dict):
            return
        start = format_date(period.get("start")) if period.get("start") else ""
        end = format_date(period.get("end")) if period.get("end") else ""
        text = f"{start} – {end}" if start and end else f"{self.dashboard.weeks} minggu terakhir"
        if self.stack.currentWidget() is self.dashboard:
            self.topbar.set_period(text)

    # ------------------------------------------------------------------
    # Tema dan profil
    # ------------------------------------------------------------------
    def _theme_from_sidebar(self, mode: str) -> None:
        if "theme_segment" in vars(self.settings):
            self.settings.theme_segment.set_value(mode)
        self.theme_requested.emit(mode)

    def _theme_from_settings(self, mode: str) -> None:
        self.sidebar.set_mode(mode)
        self.theme_requested.emit(mode)

    def _profile_saved(self, payload: dict) -> None:
        self.user.update(payload or {})
        if self.settings.hero_name:
            self.settings.hero_name.setText(self.user.get("full_name", ""))
        self.topbar.set_user(
            self.user.get("full_name") or self.user.get("username", "Pengguna"),
            ROLE_LABELS.get(str(self.user.get("role", "")).lower(), str(self.user.get("role", "")).title()),
            initials(self.user.get("full_name") or self.user.get("username", "")),
        )
        self.profile_changed.emit(payload)

    # ------------------------------------------------------------------
    # Notifikasi dan menu pengguna
    # ------------------------------------------------------------------
    def refresh_notifications(self) -> None:
        self._notif_serial += 1
        serial = self._notif_serial
        self.runner.submit(
            lambda: self.api.get("/notifications", params={"unread_only": True, "limit": 1}, timeout=20),
            lambda payload: self._notifications_ready(payload, serial),
            lambda _message, _status: None,
        )

    def _notifications_ready(self, payload: dict, serial: int) -> None:
        if serial != self._notif_serial:
            return
        self.topbar.set_count(int(payload.get("unread", 0) or 0))

    def _open_notifications(self) -> None:
        dialog = NotificationDialog(self.api, self)
        dialog.changed.connect(self.refresh_notifications)
        dialog.exec()
        self.refresh_notifications()

    def _open_user_menu(self, position: QPoint) -> None:
        tokens = theme.tokens
        menu = QMenu(self)
        name = QLabel(self.user.get("full_name") or self.user.get("username", "Pengguna"))
        name.setStyleSheet(f"color: {tokens['text']}; font-size: 13px; font-weight: 800; padding: 4px 10px;")
        role = QLabel(
            f"@{self.user.get('username', '-')} · "
            f"{ROLE_LABELS.get(str(self.user.get('role', '')).lower(), str(self.user.get('role', '')).title())}"
        )
        role.setStyleSheet(f"color: {tokens['muted']}; font-size: 11px; padding: 0 10px 5px 10px;")
        from PySide6.QtWidgets import QWidgetAction

        name_action = QWidgetAction(menu)
        name_action.setDefaultWidget(name)
        menu.addAction(name_action)
        role_action = QWidgetAction(menu)
        role_action.setDefaultWidget(role)
        menu.addAction(role_action)
        menu.addSeparator()
        profile = menu.addAction(icon("user-round", tokens["text_soft"], 16), "Profil & Pengaturan")
        profile.triggered.connect(lambda: self.navigate("settings"))
        reload_action = menu.addAction(icon("refresh-cw", tokens["text_soft"], 16), "Muat Ulang Halaman")
        reload_action.triggered.connect(self._reload_current)
        health = menu.addAction(icon("activity", tokens["text_soft"], 16), "Periksa Koneksi Server")
        health.triggered.connect(self._check_health)
        menu.addSeparator()
        logout = menu.addAction(icon("log-out", tokens["danger"], 16), "Keluar dari Aplikasi")
        logout.triggered.connect(self._confirm_logout)
        menu.exec(position)

    def _reload_current(self) -> None:
        page = self.stack.currentWidget()
        if hasattr(page, "on_show"):
            page.on_show()  # type: ignore[call-arg]
            self._toast("Halaman dimuat ulang.", "info")

    def _check_health(self) -> None:
        self.runner.submit(
            self.api.health,
            lambda payload: self._toast(
                f"Server terhubung · {payload.get('medicines', 0)} obat aktif · "
                f"database {payload.get('database', '-')}.",
                "success",
            ),
            lambda message, _status: self._toast(message, "error"),
        )

    def _confirm_logout(self) -> None:
        if ConfirmDialog.ask(
            self,
            "Keluar dari aplikasi?",
            "Sesi akan diakhiri dan Anda perlu masuk kembali untuk menggunakan aplikasi.",
            "Ya, keluar",
            danger=False,
        ):
            self.logout_requested.emit()

    def _toast(self, message: str, tone: str = "success") -> None:
        manager = getattr(self.window(), "toast", None)
        if callable(manager):
            manager(message, tone)

    def stop_timers(self) -> None:
        self._notif_timer.stop()


class MainWindow(QMainWindow):
    """Jendela frameless yang menggabungkan login dan aplikasi utama."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE}")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1220, 680)
        self.setObjectName("MainWindow")

        self.api = ApiClient()
        self.runner = AsyncRunner(self, max_threads=6)
        self.api.on_unauthorized = self._queue_unauthorized
        self.launcher = BackendLauncher(self)
        self.launcher.ready.connect(self._backend_ready)
        self.launcher.failed.connect(self._backend_failed)
        self.launcher.status.connect(self._backend_status)

        self.user: dict = {}
        self.shell: AppShell | None = None
        self.shell_active = False
        self.login_page: LoginPage | None = None
        self._backend_started = False
        self._restore_attempted = False
        self._session_closing = False

        root = QWidget(self)
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.titlebar = TitleBar(self)
        root_layout.addWidget(self.titlebar)

        self.content = QStackedWidget(root)
        self.content.setObjectName("PageStack")
        root_layout.addWidget(self.content, 1)

        self.toast_manager = ToastManager(root)
        self.toast = self.toast_manager.show

        self.grip = QSizeGrip(root)
        self.grip.setFixedSize(18, 18)
        self.grip.setToolTip("Ubah ukuran jendela")
        self.grip.raise_()

        if not PREFS.remember_session:
            self.api.clear_session()

        self._build_login()
        self._restore_window()
        QTimer.singleShot(0, self._boot_backend)

    # ------------------------------------------------------------------
    # Siklus hidup
    # ------------------------------------------------------------------
    def _build_login(self) -> None:
        self.login_page = LoginPage(self.api, self.runner, self)
        self.login_page.login_succeeded.connect(self._enter_shell)
        self.login_page.server_changed.connect(self._server_changed)
        self.login_page.start_backend_requested.connect(self._restart_backend)
        self.content.addWidget(self.login_page)
        self.content.setCurrentWidget(self.login_page)

    def _boot_backend(self) -> None:
        if self._backend_started:
            return
        self._backend_started = True
        if BackendLauncher.is_local(self.api.base_url):
            self.launcher.start(self.api.base_url)
        else:
            self._backend_ready(self.api.server_root)

    def _restart_backend(self) -> None:
        self.launcher.stop()
        self._backend_started = False
        self._boot_backend()

    # ------------------------------------------------------------------
    # Status backend dan sesi
    # ------------------------------------------------------------------
    def _backend_ready(self, _root: str) -> None:
        if self.login_page is not None:
            self.login_page.check_health()
            self.login_page.status_text.setText("Server siap. Memeriksa sesi...")
        self._restore_session()

    def _backend_failed(self, message: str) -> None:
        if self.login_page is not None:
            self.login_page._on_health_error(message, 0)
        if self.shell_active:
            self.toast(message, "error")

    def _backend_status(self, message: str) -> None:
        if self.login_page is not None and not self.shell_active:
            self.login_page.status_text.setText(message)

    def _restore_session(self) -> None:
        if self._restore_attempted or self.shell is not None:
            return
        self._restore_attempted = True
        if not PREFS.remember_session or not self.api.token:
            return
        if self.login_page is not None:
            self.login_page.status_text.setText("Memulihkan sesi tersimpan...")
        self.runner.submit(
            self.api.me,
            lambda user: self._session_restored(user),
            self._session_restore_failed,
        )

    def _session_restored(self, user: dict) -> None:
        if self.content.currentWidget() is not self.login_page:
            return
        self._enter_shell(user, restored=True)

    def _session_restore_failed(self, _message: str, status: int) -> None:
        if status in {401, 403}:
            self.api.clear_session()
            PREFS.token = ""
            if self.login_page is not None:
                self.login_page.status_text.setText("Sesi tersimpan berakhir. Silakan masuk kembali.")
        elif status == 0:
            self._restore_attempted = False
        if self.login_page is not None:
            self.login_page.check_health()

    def _enter_shell(self, user: dict, restored: bool = False) -> None:
        if not user:
            self.toast("Data pengguna tidak lengkap. Silakan masuk kembali.", "error")
            return
        old = self.shell
        if old is not None:
            self.content.removeWidget(old)
            old.deleteLater()
            self.shell = None
        self.user = dict(user)
        self.user.setdefault("role", "petugas")
        if PREFS.remember_session:
            PREFS.token = self.api.token
        else:
            PREFS.token = ""
        PREFS.last_username = self.user.get("username", PREFS.last_username)
        PREFS.sync()

        self.shell = AppShell(self.api, self.runner, self.user, self)
        self.shell.logout_requested.connect(self._logout)
        self.shell.theme_requested.connect(self._apply_theme)
        self.shell.font_scale_requested.connect(self._apply_font_scale)
        self.shell.profile_changed.connect(self._profile_updated)
        self.shell.server_changed.connect(self._server_changed)
        self.content.addWidget(self.shell)
        self.content.setCurrentWidget(self.shell)
        self.shell_active = True
        self.setWindowTitle(
            f"{APP_NAME} — {self.user.get('full_name') or self.user.get('username', 'Pengguna')}"
        )
        if restored:
            self.toast(
                f"Selamat datang kembali, {self.user.get('full_name') or self.user.get('username', '')}.",
                "success",
            )
        else:
            self.toast(
                f"Berhasil masuk sebagai "
                f"{ROLE_LABELS.get(str(self.user.get('role', '')).lower(), str(self.user.get('role', '')).title())}.",
                "success",
            )
        QTimer.singleShot(250, self.shell.refresh_notifications)

    def _profile_updated(self, payload: dict) -> None:
        self.user.update(payload or {})
        if self.shell is not None:
            self.shell.user.update(payload or {})

    def _detach_shell(self, message: str | None = None) -> None:
        if self.shell is None:
            return
        self.shell.stop_timers()
        self.shell_active = False
        self.content.setCurrentWidget(self.login_page)
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE}")
        self._restore_attempted = True
        if self.login_page is not None:
            self.login_page.check_health()
        if message:
            self.toast(message, "warning")

    def _logout(self) -> None:
        token = self.api.token
        root = self.api.server_root
        if token:
            self.runner.submit(lambda: self._remote_logout(root, token))
        self.api.clear_session()
        PREFS.token = ""
        PREFS.sync()
        self._detach_shell("Anda telah keluar dari aplikasi.")

    @staticmethod
    def _remote_logout(root: str, token: str) -> None:
        try:
            requests.post(
                f"{root}/api/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
                timeout=4,
            )
        except requests.RequestException:
            pass

    def _queue_unauthorized(self) -> None:
        QTimer.singleShot(0, self, self._handle_unauthorized)

    def _handle_unauthorized(self) -> None:
        if not self.shell_active or self._session_closing:
            return
        self._session_closing = True
        try:
            self.api.clear_session()
            PREFS.token = ""
            self._detach_shell("Sesi Anda berakhir. Silakan masuk kembali.")
        finally:
            self._session_closing = False

    # ------------------------------------------------------------------
    # Tema, server, dan jendela
    # ------------------------------------------------------------------
    def _apply_theme(self, mode: str) -> None:
        if mode not in {"light", "dark", "auto"}:
            return
        PREFS.theme = mode
        PREFS.sync()
        app = QApplication.instance()
        if app is not None:
            theme.apply(app, mode, theme.font_scale)
        if self.shell is not None:
            self.shell.sidebar.set_mode(mode)

    def _apply_font_scale(self, scale: str) -> None:
        PREFS.font_scale = scale
        PREFS.sync()
        app = QApplication.instance()
        if app is not None:
            theme.apply(app, PREFS.theme, scale)

    def _server_changed(self) -> None:
        was_active = self.shell_active
        self.api.clear_session()
        PREFS.token = ""
        PREFS.sync()
        self._restore_attempted = True
        self._backend_started = False
        self.launcher.stop()
        if was_active:
            self._detach_shell("Koneksi server diubah. Silakan masuk kembali.")
        else:
            if self.login_page is not None:
                self.login_page.check_health()
        QTimer.singleShot(0, self._boot_backend)

    def _restore_window(self) -> None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        geometry = PREFS.geometry
        restored = False
        if geometry:
            restored = self.restoreGeometry(geometry)
        if available is not None:
            # Geometri tersimpan bisa berasal dari monitor yang lebih besar.
            # Batasi ke layar aktif agar sisi kanan/bawah tidak terpotong.
            max_width = max(self.minimumWidth(), available.width() - 24)
            max_height = max(self.minimumHeight(), available.height() - 24)
            if not restored:
                # Tampilan pertama dibuat lebih lega, tetapi tetap menyisakan
                # ruang di sekitar jendela agar tidak menutupi taskbar.
                width = min(1600, max(self.minimumWidth(), available.width() - 64))
                height = min(970, max(self.minimumHeight(), available.height() - 64))
                self.resize(width, height)
            elif self.width() > max_width or self.height() > max_height:
                self.resize(min(self.width(), max_width), min(self.height(), max_height))
            frame = self.frameGeometry()
            if not restored or not available.contains(frame):
                self.move(available.center() - self.rect().center())
        elif not restored:
            self.resize(1460, 900)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.grip.move(self.width() - self.grip.width() - 2, self.height() - self.grip.height() - 2)
        self.grip.raise_()

    def closeEvent(self, event: QCloseEvent) -> None:
        PREFS.geometry = bytes(self.saveGeometry())
        PREFS.sync()
        if self.shell is not None:
            self.shell.stop_timers()
        self.runner.shutdown()
        self.launcher.stop()
        event.accept()
