"""Halaman Pengaturan: profil, tampilan, model, database, akun, dan informasi."""
from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QUrl, Signal, qVersion
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import (
    ChangePasswordDialog,
    ConfirmDialog,
    MedicineDialog,
    ServerDialog,
    UserDialog,
)
from app.components.layout import PageBase
from app.components.widgets import (
    Avatar,
    Badge,
    Card,
    Divider,
    Field,
    IconBox,
    IconButton,
    InlineBanner,
    SectionHeader,
    SegmentedControl,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, APP_YEAR, PREFS
from app.core.theme import theme
from app.core.utils import format_date, format_datetime, initials, number
from app.pages.common import PageNotice, clear_layout

MODEL_OPTIONS = [
    ("auto", "Otomatis (WAPE terkecil)"),
    ("random_forest", "Random Forest Regression"),
    ("decision_tree", "Decision Tree Regression"),
    ("linear_regression", "Linear Regression"),
]


class SettingsPage(PageBase):
    theme_changed = Signal(str)
    font_scale_changed = Signal(str)
    logout_requested = Signal()
    profile_changed = Signal(dict)
    server_changed = Signal()

    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self.is_admin = str(user.get("role", "")).lower() == "admin"
        self._loaded = False
        self._serial = 0
        self._settings: dict[str, Any] = {}
        self._users: list[dict] = []
        self._backups: list[dict] = []
        self._tabs: list[str] = []

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        hero = Card(padding=18, spacing=12)
        hero_row = QHBoxLayout()
        hero_row.setSpacing(14)
        self.avatar = Avatar(initials(user.get("full_name", "")), 56)
        hero_row.addWidget(self.avatar)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(2)
        self.hero_name = QLabel(user.get("full_name", "Pengguna"))
        self.hero_name.setStyleSheet("font-size: 18px; font-weight: 800;")
        hero_text.addWidget(self.hero_name)
        self.hero_meta = QLabel(f"@{user.get('username', '-')} · {str(user.get('role', '')).title()}")
        self.hero_meta.setObjectName("Muted")
        hero_text.addWidget(self.hero_meta)
        self.hero_badge = Badge("Sesi aktif", "success")
        hero_badge_row = QHBoxLayout()
        hero_badge_row.setSpacing(6)
        hero_badge_row.addWidget(self.hero_badge)
        hero_badge_row.addStretch(1)
        hero_text.addLayout(hero_badge_row)
        hero_row.addLayout(hero_text, 1)
        self.server_label = QLabel("")
        self.server_label.setObjectName("MutedSmall")
        self.server_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hero_row.addWidget(self.server_label)
        hero.body.addLayout(hero_row)
        self.body.addWidget(hero)

        tab_options = [("profile", "Profil & Tampilan")]
        if self.is_admin:
            tab_options.extend(
                [
                    ("model", "Model & Pengadaan"),
                    ("database", "Database"),
                    ("users", "Akun Pengguna"),
                ]
            )
        tab_options.append(("about", "Tentang Aplikasi"))
        self._tabs = [value for value, _label in tab_options]
        self.tabs = SegmentedControl(tab_options, self._tabs[0])
        self.tabs.changed.connect(self._tab_changed)
        tab_row = QHBoxLayout()
        tab_row.addWidget(self.tabs)
        tab_row.addStretch(1)
        self.body.addLayout(tab_row)

        self.stack = QStackedWidget()
        self.body.addWidget(self.stack)
        self.stack.addWidget(self._build_profile_tab())
        if self.is_admin:
            self.stack.addWidget(self._build_model_tab())
            self.stack.addWidget(self._build_database_tab())
            self.stack.addWidget(self._build_users_tab())
        self.stack.addWidget(self._build_about_tab())
        self.body.addStretch(1)
        self._refresh_server_label()

    # ------------------------------------------------------------------
    # Pembangun tab
    # ------------------------------------------------------------------
    def _build_profile_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        profile_card = Card(padding=16, spacing=10)
        profile_card.body.addWidget(
            SectionHeader("Profil Pengguna", "Perbarui nama lengkap dan alamat email akun.", "user-round")
        )
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(9)
        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("Nama lengkap")
        self.profile_email = QLineEdit()
        self.profile_email.setPlaceholderText("nama@apotekpahala.local")
        form.addWidget(Field("Nama lengkap", self.profile_name, required=True), 0, 0)
        form.addWidget(Field("Email", self.profile_email), 0, 1)
        profile_card.body.addLayout(form)
        profile_footer = QHBoxLayout()
        self.profile_role = QLabel("")
        self.profile_role.setObjectName("MutedSmall")
        profile_footer.addWidget(self.profile_role)
        profile_footer.addStretch(1)
        self.profile_save = ThemedButton("Simpan Profil", "primary", "check")
        self.profile_save.clicked.connect(self._save_profile)
        profile_footer.addWidget(self.profile_save)
        profile_card.body.addLayout(profile_footer)
        layout.addWidget(profile_card)

        display_card = Card(padding=16, spacing=10)
        display_card.body.addWidget(
            SectionHeader("Tampilan", "Pilih tema dan ukuran huruf. Perubahan langsung diterapkan.", "palette")
        )
        display_row = QHBoxLayout()
        display_row.setSpacing(18)
        theme_col = QVBoxLayout()
        theme_col.setSpacing(5)
        theme_title = QLabel("Tema aplikasi")
        theme_title.setObjectName("FieldLabel")
        theme_col.addWidget(theme_title)
        self.theme_segment = SegmentedControl(
            [("light", "Terang"), ("dark", "Gelap"), ("auto", "Otomatis")], "light"
        )
        self.theme_segment.changed.connect(self._theme_changed)
        theme_col.addWidget(self.theme_segment)
        theme_hint = QLabel("Otomatis mengikuti pengaturan tema sistem operasi.")
        theme_hint.setObjectName("MutedSmall")
        theme_col.addWidget(theme_hint)
        display_row.addLayout(theme_col, 1)
        font_col = QVBoxLayout()
        font_col.setSpacing(5)
        font_title = QLabel("Ukuran huruf")
        font_title.setObjectName("FieldLabel")
        font_col.addWidget(font_title)
        self.font_segment = SegmentedControl(
            [("small", "Kecil"), ("normal", "Normal"), ("large", "Besar")], "normal"
        )
        self.font_segment.changed.connect(self._font_changed)
        font_col.addWidget(self.font_segment)
        font_hint = QLabel("Ukuran huruf memengaruhi seluruh halaman desktop.")
        font_hint.setObjectName("MutedSmall")
        font_col.addWidget(font_hint)
        display_row.addLayout(font_col, 1)
        display_card.body.addLayout(display_row)
        layout.addWidget(display_card)

        security_card = Card(padding=16, spacing=10)
        security_card.body.addWidget(
            SectionHeader("Keamanan & Sesi", "Kelola password dan keluar dari aplikasi desktop.", "shield-check")
        )
        security_row = QHBoxLayout()
        security_row.setSpacing(9)
        self.password_button = ThemedButton("Ganti Password", "outline", "key-round")
        self.password_button.clicked.connect(self._change_password)
        security_row.addWidget(self.password_button)
        security_row.addStretch(1)
        self.logout_button = ThemedButton("Keluar dari Aplikasi", "danger-soft", "log-out")
        self.logout_button.clicked.connect(self._logout)
        security_row.addWidget(self.logout_button)
        security_card.body.addLayout(security_row)
        security_note = QLabel(
            "Sesi disimpan hanya bila opsi \"Ingat sesi saya\" dicentang saat masuk. "
            "Keluar akan mengakhiri sesi server dan menghapus token lokal."
        )
        security_note.setObjectName("MutedSmall")
        security_note.setWordWrap(True)
        security_card.body.addWidget(security_note)
        layout.addWidget(security_card)
        return page

    def _build_model_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        model_card = Card(padding=16, spacing=10)
        model_card.body.addWidget(
            SectionHeader(
                "Parameter Model",
                "Digunakan saat pelatihan ulang model. Hasil prediksi lama tidak berubah otomatis.",
                "cpu",
            )
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(9)
        self.model_primary = QComboBox()
        for value, label in MODEL_OPTIONS:
            self.model_primary.addItem(label, value)
        self.model_trees = QSpinBox()
        self.model_trees.setRange(10, 1500)
        self.model_trees.setSingleStep(50)
        self.model_trees.setSuffix(" pohon")
        self.model_depth = QSpinBox()
        self.model_depth.setRange(0, 100)
        self.model_depth.setSpecialValueText("Tak terbatas")
        self.model_leaf = QSpinBox()
        self.model_leaf.setRange(1, 50)
        self.model_test = QSpinBox()
        self.model_test.setRange(10, 40)
        self.model_test.setSingleStep(5)
        self.model_test.setSuffix(" %")
        self.model_horizon = QComboBox()
        for value in range(1, 13):
            self.model_horizon.addItem(f"{value} pekan", value)
        self.model_random = QSpinBox()
        self.model_random.setRange(0, 1_000_000)
        self.model_jobs = QComboBox()
        for value, label in ((-1, "Semua inti prosesor"), (1, "1 inti"), (2, "2 inti"), (4, "4 inti")):
            self.model_jobs.addItem(label, value)
        self.model_weather = QComboBox()
        self.model_weather.addItem("Normal iklim (skenario saat ini)", "normal_iklim")
        grid.addWidget(Field("Model utama", self.model_primary), 0, 0)
        grid.addWidget(Field("Jumlah pohon", self.model_trees), 0, 1)
        grid.addWidget(Field("Kedalaman maksimum", self.model_depth), 0, 2)
        grid.addWidget(Field("Minimum sampel daun", self.model_leaf), 1, 0)
        grid.addWidget(Field("Proporsi data uji", self.model_test), 1, 1)
        grid.addWidget(Field("Horizon bawaan", self.model_horizon), 1, 2)
        grid.addWidget(Field("Random state", self.model_random), 2, 0)
        grid.addWidget(Field("Paralelisme", self.model_jobs), 2, 1)
        grid.addWidget(Field("Skenario cuaca", self.model_weather), 2, 2)
        model_card.body.addLayout(grid)
        model_card.body.addWidget(
            InlineBanner(
                "Mode otomatis memilih Random Forest, Decision Tree, atau Linear Regression dengan WAPE "
                "terkecil pada data uji untuk setiap obat. Pilihan manual memakai satu algoritma untuk semua obat.",
                "info",
            )
        )
        model_footer = QHBoxLayout()
        model_footer.addStretch(1)
        self.model_save = ThemedButton("Simpan Parameter Model", "primary", "check")
        self.model_save.clicked.connect(self._save_model)
        model_footer.addWidget(self.model_save)
        model_card.body.addLayout(model_footer)
        layout.addWidget(model_card)

        procurement_card = Card(padding=16, spacing=10)
        procurement_card.body.addWidget(
            SectionHeader(
                "Asumsi Pengadaan",
                "Asumsi dipakai saat menghitung rekomendasi pembelian baru.",
                "clipboard-list",
            )
        )
        proc_grid = QGridLayout()
        proc_grid.setHorizontalSpacing(12)
        proc_grid.setVerticalSpacing(9)
        self.proc_lead = QSpinBox()
        self.proc_lead.setRange(0, 365)
        self.proc_lead.setSuffix(" hari")
        self.proc_safety = QSpinBox()
        self.proc_safety.setRange(0, 365)
        self.proc_safety.setSuffix(" hari")
        self.proc_review = QSpinBox()
        self.proc_review.setRange(1, 365)
        self.proc_review.setSuffix(" hari")
        self.proc_rounding = QSpinBox()
        self.proc_rounding.setRange(1, 1000)
        self.proc_rounding.setSuffix(" unit")
        self.proc_horizon = QComboBox()
        for value in range(1, 13):
            self.proc_horizon.addItem(f"{value} pekan", value)
        proc_grid.addWidget(Field("Waktu tunggu (lead time)", self.proc_lead), 0, 0)
        proc_grid.addWidget(Field("Stok pengaman", self.proc_safety), 0, 1)
        proc_grid.addWidget(Field("Periode telaah", self.proc_review), 0, 2)
        proc_grid.addWidget(Field("Pembulatan pembelian", self.proc_rounding), 1, 0)
        proc_grid.addWidget(Field("Horizon bawaan", self.proc_horizon), 1, 1)
        procurement_card.body.addLayout(proc_grid)
        proc_footer = QHBoxLayout()
        proc_footer.addStretch(1)
        self.proc_save = ThemedButton("Simpan Asumsi Pengadaan", "primary", "check")
        self.proc_save.clicked.connect(self._save_procurement)
        proc_footer.addWidget(self.proc_save)
        procurement_card.body.addLayout(proc_footer)
        layout.addWidget(procurement_card)

        note = InlineBanner(
            "Perubahan parameter tidak melatih ulang model secara otomatis. "
            "Gunakan tombol \"Latih Ulang Semua\" pada halaman Prediksi Permintaan.",
            "info",
        )
        layout.addWidget(note)
        return page

    def _build_database_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        info_card = Card(padding=16, spacing=10)
        info_card.body.addWidget(
            SectionHeader("Database Aplikasi", "SQLite lokal yang dipakai bersama oleh desktop dan web.", "database")
        )
        tiles = QHBoxLayout()
        tiles.setSpacing(12)
        self.db_size = StatTile("Ukuran database", "database", "primary")
        self.db_sales = StatTile("Baris permintaan", "receipt-text", "info")
        self.db_weather = StatTile("Hari cuaca", "cloud-rain", "accent")
        self.db_predictions = StatTile("Riwayat prediksi", "trending-up", "purple")
        for tile in (self.db_size, self.db_sales, self.db_weather, self.db_predictions):
            tiles.addWidget(tile, 1)
        info_card.body.addLayout(tiles)
        self.db_path = QLabel("")
        self.db_path.setObjectName("MutedSmall")
        self.db_path.setWordWrap(True)
        self.db_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_card.body.addWidget(self.db_path)
        db_actions = QHBoxLayout()
        db_actions.setSpacing(8)
        self.backup_button = ThemedButton("Buat Backup", "primary", "database-backup")
        self.backup_button.clicked.connect(self._backup)
        db_actions.addWidget(self.backup_button)
        self.restore_button = ThemedButton("Restore dari Berkas", "outline", "rotate-ccw")
        self.restore_button.clicked.connect(self._restore)
        db_actions.addWidget(self.restore_button)
        self.open_folder = ThemedButton("Buka Folder Backup", "ghost", "folder-open")
        self.open_folder.clicked.connect(self._open_backup_folder)
        db_actions.addWidget(self.open_folder)
        db_actions.addStretch(1)
        self.db_refresh = ThemedButton("Muat Ulang", "ghost", "refresh-cw", compact=True)
        self.db_refresh.clicked.connect(self.load)
        db_actions.addWidget(self.db_refresh)
        info_card.body.addLayout(db_actions)
        layout.addWidget(info_card)

        backup_card = Card(padding=16, spacing=8)
        backup_head = QHBoxLayout()
        backup_head.setContentsMargins(0, 0, 0, 0)
        backup_head.addWidget(
            SectionHeader("Riwayat Backup", "Salinan database tersimpan di folder backup backend.", "history"),
            1,
        )
        self.backup_count = QLabel("")
        self.backup_count.setObjectName("MutedSmall")
        backup_head.addWidget(self.backup_count)
        backup_card.body.addLayout(backup_head)
        self.backup_table = Table(["Nama Berkas", "Ukuran", "Dibuat"])
        self.backup_table.setMinimumHeight(220)
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setColumnWidth(1, 110)
        self.backup_table.setColumnWidth(2, 190)
        self.backup_table.verticalHeader().setDefaultSectionSize(36)
        backup_card.body.addWidget(self.backup_table)
        warning = InlineBanner(
            "Restore menimpa seluruh database aktif dan mengakhiri sesi. "
            "Sistem otomatis membuat backup sebelum restore. Gunakan hanya berkas .db Apotek Pahala.",
            "warning",
        )
        backup_card.body.addWidget(warning)
        layout.addWidget(backup_card)
        return page

    def _build_users_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        card = Card(padding=16, spacing=8)
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.addWidget(
            SectionHeader("Akun Pengguna", "Kelola akses Admin dan Petugas. Hanya Admin yang dapat mengubah akun.", "users"),
            1,
        )
        self.user_refresh = ThemedButton("Muat Ulang", "ghost", "refresh-cw", compact=True)
        self.user_refresh.clicked.connect(self._load_users)
        head.addWidget(self.user_refresh)
        self.add_user_button = ThemedButton("Tambah Akun", "primary", "user-plus")
        self.add_user_button.clicked.connect(self._add_user)
        head.addWidget(self.add_user_button)
        card.body.addLayout(head)
        self.user_count = QLabel("")
        self.user_count.setObjectName("MutedSmall")
        card.body.addWidget(self.user_count)
        self.user_table = Table(["Nama", "Username", "Email", "Role", "Status", "Aksi"])
        self.user_table.setMinimumHeight(320)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in ((1, 120), (2, 210), (3, 100), (4, 100), (5, 84)):
            self.user_table.setColumnWidth(column, width)
        self.user_table.verticalHeader().setDefaultSectionSize(42)
        card.body.addWidget(self.user_table)
        role_note = QLabel(
            "Admin: akses penuh termasuk data master, import, backup, dan pengguna. "
            "Petugas: operasional harian, prediksi, stok, dan pengadaan tanpa persetujuan."
        )
        role_note.setObjectName("MutedSmall")
        role_note.setWordWrap(True)
        card.body.addWidget(role_note)
        layout.addWidget(card)
        return page

    def _build_about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        about_card = Card(padding=18, spacing=10)
        about_head = QHBoxLayout()
        about_head.setSpacing(14)
        about_head.addWidget(IconBox("pill", "primary", "primary_soft", 52, 24, radius=15))
        about_text = QVBoxLayout()
        about_text.setSpacing(2)
        name = QLabel(APP_NAME)
        name.setStyleSheet("font-size: 20px; font-weight: 800;")
        about_text.addWidget(name)
        subtitle = QLabel(f"{APP_SUBTITLE} · Versi {APP_VERSION}")
        subtitle.setObjectName("Muted")
        about_text.addWidget(subtitle)
        about_head.addLayout(about_text, 1)
        about_card.body.addLayout(about_head)
        self.about_tagline = QLabel("Solusi analitik untuk persediaan obat yang lebih tepat.")
        self.about_tagline.setWordWrap(True)
        self.about_tagline.setStyleSheet("font-size: 13px; font-weight: 600;")
        about_card.body.addWidget(self.about_tagline)
        about_card.body.addWidget(Divider())
        self.about_developer = QLabel("")
        self.about_developer.setObjectName("Muted")
        self.about_developer.setWordWrap(True)
        about_card.body.addWidget(self.about_developer)
        self.about_tech = QLabel("")
        self.about_tech.setObjectName("MutedSmall")
        self.about_tech.setWordWrap(True)
        about_card.body.addWidget(self.about_tech)
        self.about_modules = QLabel("")
        self.about_modules.setObjectName("MutedSmall")
        self.about_modules.setWordWrap(True)
        about_card.body.addWidget(self.about_modules)
        layout.addWidget(about_card)

        server_card = Card(padding=16, spacing=10)
        server_card.body.addWidget(
            SectionHeader("Koneksi Server", "Backend FastAPI yang sama dipakai oleh aplikasi desktop dan web.", "server")
        )
        server_row = QHBoxLayout()
        server_row.setSpacing(9)
        self.server_status = QLabel("")
        self.server_status.setObjectName("Muted")
        self.server_status.setWordWrap(True)
        server_row.addWidget(self.server_status, 1)
        self.server_button = ThemedButton("Ubah Koneksi", "outline", "server")
        self.server_button.clicked.connect(self._server_dialog)
        server_row.addWidget(self.server_button)
        self.health_button = ThemedButton("Uji Koneksi", "ghost", "activity")
        self.health_button.clicked.connect(self._health_check)
        server_row.addWidget(self.health_button)
        server_card.body.addLayout(server_row)
        self.health_banner = InlineBanner("Klik Uji Koneksi untuk memeriksa status backend.", "info")
        server_card.body.addWidget(self.health_banner)
        layout.addWidget(server_card)

        source_card = Card(padding=16, spacing=8)
        source_card.body.addWidget(
            SectionHeader("Sumber & Metode Data", "Asal data dan batas penggunaan hasil model.", "database")
        )
        source_text = QLabel(
            "Data permintaan historis merupakan estimasi yang dihitung dari perubahan stok opname dan "
            "pembelian bersih Apotek Pahala 2022–2026, karena folder sumber tidak memuat transaksi kasir. "
            "Data cuaca berasal dari NASA POWER untuk lokasi acuan Bandung. Hasil prediksi adalah estimasi "
            "model, bukan kepastian, dan sebaiknya dipadukan dengan pertimbangan apoteker."
        )
        source_text.setObjectName("Muted")
        source_text.setWordWrap(True)
        source_card.body.addWidget(source_text)
        layout.addWidget(source_card)
        return page

    # ------------------------------------------------------------------
    # Navigasi tab
    # ------------------------------------------------------------------
    def _tab_changed(self, value: Any) -> None:
        key = str(value)
        try:
            index = self._tabs.index(key)
        except ValueError:
            index = 0
        self.stack.setCurrentIndex(index)

    def on_show(self) -> None:
        self.load()

    # ------------------------------------------------------------------
    # Pemuatan data
    # ------------------------------------------------------------------
    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat pengaturan aplikasi...", "info")

        def task() -> dict:
            settings = self.api.get("/settings", timeout=45)
            users = self.api.get("/users", timeout=45) if self.is_admin else []
            return {"settings": settings, "users": users}

        self.runner.submit(
            task,
            lambda payload: self._apply(payload, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._serial:
            self.notice.show_message(message, "danger")

    def _apply(self, payload: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.clear()
        self._loaded = True
        settings = payload.get("settings", {})
        self._settings = settings
        self._users = payload.get("users", []) or []
        self._backups = settings.get("backups", []) or []
        profile = settings.get("profile", {}) or {}
        self.profile_name.setText(profile.get("full_name", ""))
        self.profile_email.setText(profile.get("email") or "")
        self.profile_role.setText(
            f"@{profile.get('username', '-')} · peran {str(profile.get('role', '')).title()}"
        )
        display = settings.get("display", {}) or {}
        self.theme_segment.set_value(display.get("user_theme", display.get("theme", "light")))
        self.font_segment.set_value(display.get("user_font_scale", display.get("font_scale", "normal")))
        model = settings.get("model", {}) or {}
        if self.is_admin:
            index = self.model_primary.findData(model.get("primary_model", "auto"))
            if index >= 0:
                self.model_primary.setCurrentIndex(index)
            self.model_trees.setValue(int(model.get("n_estimators", 400)))
            self.model_depth.setValue(int(model.get("max_depth", 4)))
            self.model_leaf.setValue(int(model.get("min_samples_leaf", 3)))
            self.model_test.setValue(round(float(model.get("test_ratio", 0.2)) * 100))
            horizon_index = self.model_horizon.findData(int(model.get("horizon_weeks", 4)))
            if horizon_index >= 0:
                self.model_horizon.setCurrentIndex(horizon_index)
            self.model_random.setValue(int(model.get("random_state", 42)))
            jobs_index = self.model_jobs.findData(int(model.get("n_jobs", -1)))
            if jobs_index >= 0:
                self.model_jobs.setCurrentIndex(jobs_index)
            scenario_index = self.model_weather.findData(model.get("weather_scenario", "normal_iklim"))
            if scenario_index >= 0:
                self.model_weather.setCurrentIndex(scenario_index)
            procurement = settings.get("procurement", {}) or {}
            self.proc_lead.setValue(int(procurement.get("lead_time_days", 7)))
            self.proc_safety.setValue(int(procurement.get("safety_stock_days", 14)))
            self.proc_review.setValue(int(procurement.get("review_period_days", 7)))
            self.proc_rounding.setValue(int(procurement.get("rounding_unit", 1)))
            proc_horizon = self.proc_horizon.findData(int(procurement.get("default_horizon_weeks", 4)))
            if proc_horizon >= 0:
                self.proc_horizon.setCurrentIndex(proc_horizon)
            self._render_database(settings.get("database", {}) or {})
            self._render_backups()
            self._render_users()
        self._render_about(settings.get("app", {}) or {})
        self.server_label.setText(f"Server: {self.api.server_root}")
        self._refresh_server_label()

    def _refresh_server_label(self) -> None:
        self.server_label.setText(f"{self.api.base_url}")
        self.server_status.setText(
            f"Alamat API aktif: {self.api.base_url}. Backend menyajikan data yang sama untuk desktop dan web."
        )

    def _render_about(self, app: dict) -> None:
        self.about_tagline.setText(app.get("tagline", "Solusi analitik untuk persediaan obat yang lebih tepat."))
        self.about_developer.setText(
            f"Developer: {app.get('developer', 'Tim Capstone Design')} · © {APP_YEAR} {APP_NAME}"
        )
        technology = app.get("technology", [])
        runtime = f"Python {platform.python_version()} · Qt {qVersion()}"
        self.about_tech.setText(
            "Teknologi: " + " · ".join(str(item) for item in technology) + f"\nRuntime desktop: {runtime}"
        )
        modules = app.get("modules", [])
        self.about_modules.setText("Modul: " + ", ".join(str(item) for item in modules))

    def _render_database(self, database: dict) -> None:
        counts = database.get("counts", {}) or {}
        self.db_size.set_value(database.get("size_label", "—"), str(database.get("engine", "SQLite")))
        self.db_sales.set_value(number(counts.get("sales", 0)), "baris permintaan")
        self.db_weather.set_value(number(counts.get("weather_days", 0)), "hari cuaca")
        self.db_predictions.set_value(number(counts.get("prediction_runs", 0)), "run tersimpan")
        path = database.get("path", "")
        modified = database.get("last_modified")
        self.db_path.setText(
            f"Lokasi: {path}"
            + (f" · diperbarui {format_datetime(modified)}" if modified else "")
        )

    def _render_backups(self) -> None:
        self.backup_table.setRowCount(0)
        self.backup_table.setRowCount(len(self._backups))
        for row, item in enumerate(self._backups):
            self.backup_table.add_item(row, 0, item.get("name", "-"))
            self.backup_table.add_item(row, 1, item.get("size_label", "-"), Qt.AlignmentFlag.AlignRight)
            self.backup_table.add_item(row, 2, format_datetime(item.get("created_at")))
        if not self._backups:
            self.backup_table.setRowCount(1)
            self.backup_table.setSpan(0, 0, 1, 3)
            self.backup_table.add_item(
                0, 0, "Belum ada backup. Klik \"Buat Backup\" untuk membuat salinan database.",
                Qt.AlignmentFlag.AlignCenter, color=theme.tokens["muted"],
            )
        self.backup_count.setText(f"{len(self._backups)} berkas backup")

    def _render_users(self) -> None:
        self.user_table.setRowCount(0)
        self.user_table.setRowCount(len(self._users))
        self.user_count.setText(f"{len(self._users)} akun terdaftar")
        for row, item in enumerate(self._users):
            self.user_table.add_item(row, 0, item.get("full_name", "-"), bold=True)
            self.user_table.add_item(row, 1, "@" + str(item.get("username", "-")))
            self.user_table.add_item(row, 2, item.get("email") or "—")
            role = str(item.get("role", "")).title()
            role_badge = Badge(role, "primary" if role.lower() == "admin" else "info")
            role_holder = QWidget()
            role_layout = QHBoxLayout(role_holder)
            role_layout.setContentsMargins(0, 0, 0, 0)
            role_layout.addWidget(role_badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.user_table.setCellWidget(row, 3, role_holder)
            active = bool(item.get("is_active", True))
            status_badge = Badge("Aktif" if active else "Nonaktif", "success" if active else "neutral")
            status_holder = QWidget()
            status_layout = QHBoxLayout(status_holder)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.addWidget(status_badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.user_table.setCellWidget(row, 4, status_holder)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(1)
            edit = IconButton("pencil-line", "Ubah akun", "primary", 28, 14, "ghost")
            edit.clicked.connect(lambda _checked=False, value=item: self._edit_user(value))
            actions_layout.addWidget(edit)
            if int(item.get("id", 0)) != int(self.user.get("id", 0)):
                deactivate = IconButton("user-x", "Nonaktifkan akun", "danger", 28, 14, "ghost")
                deactivate.clicked.connect(lambda _checked=False, value=item: self._deactivate_user(value))
                actions_layout.addWidget(deactivate)
            self.user_table.setCellWidget(row, 5, actions)

    # ------------------------------------------------------------------
    # Aksi profil & tampilan
    # ------------------------------------------------------------------
    def _save_profile(self) -> None:
        if not self._loaded:
            return
        name = self.profile_name.text().strip()
        if len(name) < 3:
            self.toast("Nama lengkap minimal 3 karakter.", "error")
            return
        payload = {"full_name": name, "email": self.profile_email.text().strip() or None}
        self.profile_save.start_loading("Menyimpan...")
        self.runner.submit(
            lambda: self.api.put("/settings/profile", payload, timeout=45),
            lambda result: self._profile_saved(payload, result),
            lambda message, status: (self.profile_save.stop_loading(), self.toast(message, "error")),
            self.profile_save.stop_loading,
        )

    def _profile_saved(self, payload: dict, _result: dict) -> None:
        self.toast("Profil berhasil diperbarui.", "success")
        self.hero_name.setText(payload.get("full_name", ""))
        self.profile_changed.emit(payload)
        self.notice.show_message("Profil tersimpan.", "success")

    def _theme_changed(self, value: Any) -> None:
        mode = str(value)
        self.theme_changed.emit(mode)
        if self._loaded:
            self._save_display(theme_mode=mode)

    def _font_changed(self, value: Any) -> None:
        scale = str(value)
        self.font_scale_changed.emit(scale)
        if self._loaded:
            self._save_display(font_scale=scale)

    def _save_display(self, theme_mode: str | None = None, font_scale: str | None = None) -> None:
        payload = {
            "theme": theme_mode or self.theme_segment.value(),
            "font_scale": font_scale or self.font_segment.value(),
        }
        self.runner.submit(
            lambda: self.api.put("/settings/display", payload, timeout=30),
            lambda _result: None,
            lambda message, status: self.toast(f"Preferensi tampilan gagal disimpan: {message}", "error"),
        )

    def _change_password(self) -> None:
        dialog = ChangePasswordDialog(self.api, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Password berhasil diperbarui.", "success")

    def _logout(self) -> None:
        if ConfirmDialog.ask(
            self,
            "Keluar dari aplikasi?",
            "Sesi server akan diakhiri dan Anda perlu masuk kembali untuk menggunakan aplikasi.",
            "Ya, keluar",
            danger=False,
        ):
            self.logout_requested.emit()

    # ------------------------------------------------------------------
    # Aksi parameter
    # ------------------------------------------------------------------
    def _save_model(self) -> None:
        payload = {
            "primary_model": self.model_primary.currentData() or "auto",
            "n_estimators": int(self.model_trees.value()),
            "max_depth": int(self.model_depth.value()),
            "min_samples_leaf": int(self.model_leaf.value()),
            "random_state": int(self.model_random.value()),
            "test_ratio": round(self.model_test.value() / 100, 2),
            "horizon_weeks": int(self.model_horizon.currentData() or 4),
            "weather_scenario": self.model_weather.currentData() or "normal_iklim",
            "n_jobs": int(self.model_jobs.currentData() or -1),
        }
        self.model_save.start_loading("Menyimpan...")
        self.runner.submit(
            lambda: self.api.put("/settings/model", payload, timeout=45),
            lambda _result: (self.toast("Parameter model disimpan.", "success"), self.notice.show_message("Parameter model tersimpan.", "success")),
            lambda message, status: self.toast(message, "error"),
            self.model_save.stop_loading,
        )

    def _save_procurement(self) -> None:
        payload = {
            "lead_time_days": int(self.proc_lead.value()),
            "safety_stock_days": int(self.proc_safety.value()),
            "review_period_days": int(self.proc_review.value()),
            "rounding_unit": int(self.proc_rounding.value()),
            "default_horizon_weeks": int(self.proc_horizon.currentData() or 4),
        }
        self.proc_save.start_loading("Menyimpan...")
        self.runner.submit(
            lambda: self.api.put("/settings/procurement", payload, timeout=45),
            lambda _result: (self.toast("Asumsi pengadaan disimpan.", "success"), self.notice.show_message("Asumsi pengadaan tersimpan.", "success")),
            lambda message, status: self.toast(message, "error"),
            self.proc_save.stop_loading,
        )

    # ------------------------------------------------------------------
    # Aksi database
    # ------------------------------------------------------------------
    def _backup(self) -> None:
        self.backup_button.start_loading("Membuat backup...")
        self.runner.submit(
            lambda: self.api.post("/settings/database/backup", timeout=180),
            self._backup_done,
            lambda message, status: self.toast(message, "error"),
            self.backup_button.stop_loading,
        )

    def _backup_done(self, result: dict) -> None:
        self.toast(
            f"Backup dibuat: {result.get('file', '-')} ({result.get('size_label', '-')}).",
            "success",
        )
        self.load()

    def _open_backup_folder(self) -> None:
        folder = None
        if self._backups:
            folder = Path(self._backups[0].get("path", "")).parent
        elif self._settings.get("database", {}).get("path"):
            folder = Path(self._settings["database"]["path"]).parent / "backups"
        if folder and folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        else:
            self.toast("Folder backup belum tersedia. Buat backup terlebih dahulu.", "warning")

    def _restore(self) -> None:
        path, _selected = QFileDialog.getOpenFileName(
            self, "Pilih berkas database", "", "Database SQLite (*.db)"
        )
        if not path:
            return
        if not ConfirmDialog.ask(
            self,
            "Restore database?",
            "Seluruh data aktif akan diganti dengan isi berkas yang dipilih. Sistem membuat backup otomatis "
            "sebelum restore, lalu sesi Anda berakhir dan aplikasi meminta masuk kembali.",
            "Ya, restore sekarang",
            danger=True,
        ):
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.restore_button.start_loading("Memulihkan...")
        self.runner.submit(
            lambda: self.api.upload(
                "/settings/database/restore?confirm=true", path, timeout=240
            ),
            self._restore_done,
            lambda message, status: self.toast(message, "error"),
            lambda: (QApplication.restoreOverrideCursor(), self.restore_button.stop_loading()),
        )

    def _restore_done(self, result: dict) -> None:
        self.toast(result.get("message", "Database berhasil direstore."), "success")
        self.logout_requested.emit()

    # ------------------------------------------------------------------
    # Aksi pengguna
    # ------------------------------------------------------------------
    def _load_users(self) -> None:
        self.user_refresh.start_loading("Memuat...")
        self.runner.submit(
            lambda: self.api.get("/users", timeout=45),
            self._users_ready,
            lambda message, status: self.toast(message, "error"),
            self.user_refresh.stop_loading,
        )

    def _users_ready(self, users: list) -> None:
        self._users = users or []
        self._render_users()

    def _add_user(self) -> None:
        dialog = UserDialog(self.api, parent=self, on_saved=self._load_users)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Akun baru ditambahkan.", "success")

    def _edit_user(self, item: dict) -> None:
        dialog = UserDialog(self.api, item, self, on_saved=self._load_users)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Akun diperbarui.", "success")
            if int(item.get("id", 0)) == int(self.user.get("id", 0)):
                self.load()

    def _deactivate_user(self, item: dict) -> None:
        if not ConfirmDialog.ask(
            self,
            "Nonaktifkan akun?",
            f"Akun {item.get('username', '')} tidak dapat masuk lagi. Riwayat aktivitas tetap tersimpan.",
            "Nonaktifkan",
            danger=True,
        ):
            return
        self.runner.submit(
            lambda: self.api.delete(f"/users/{item.get('id')}", timeout=45),
            lambda _result: (self.toast("Akun dinonaktifkan.", "success"), self._load_users()),
            lambda message, status: self.toast(message, "error"),
        )

    # ------------------------------------------------------------------
    # Aksi server
    # ------------------------------------------------------------------
    def _server_dialog(self) -> None:
        dialog = ServerDialog(self.api, self)
        dialog.on_saved = self._server_saved
        dialog.exec()

    def _server_saved(self) -> None:
        self._refresh_server_label()
        self.server_changed.emit()
        self.health_banner.set_message(
            f"Terhubung ke {self.api.base_url}. Sesi saat ini tetap memakai token yang ada.",
            "success",
        )
        self.load()

    def _health_check(self) -> None:
        self.health_button.start_loading("Menguji...")
        self.health_banner.set_message("Menguji koneksi ke server...", "info")
        self.runner.submit(
            self.api.health,
            self._health_ok,
            self._health_error,
            self.health_button.stop_loading,
        )

    def _health_ok(self, payload: dict) -> None:
        self.health_banner.set_message(
            f"Server terhubung · versi {payload.get('version', '-')} · database {payload.get('database', '-')} · "
            f"{payload.get('medicines', 0)} obat aktif.",
            "success",
        )

    def _health_error(self, message: str, _status: int) -> None:
        self.health_banner.set_message(message, "danger")
