"""Halaman masuk desktop dengan panel hero dan formulir."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import ServerDialog
from app.components.widgets import (
    BrandMark,
    IconBox,
    InlineBanner,
    ThemedButton,
    icon,
    refresh_style,
)
from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, APP_YEAR, PREFS
from app.core.theme import theme
from app.core.utils import initials


class HeroPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LoginLeft")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 48, 52, 40)
        layout.setSpacing(0)

        logo_box = QFrame(self)
        logo_box.setFixedSize(86, 86)
        logo_box.setStyleSheet("background: rgba(255,255,255,0.96); border-radius: 22px;")
        logo_layout = QVBoxLayout(logo_box)
        logo_layout.setContentsMargins(11, 11, 11, 11)
        logo_layout.addWidget(BrandMark(64))
        layout.addWidget(logo_box)
        layout.addSpacing(24)

        brand = QLabel(APP_NAME)
        brand.setStyleSheet("color: #FFFFFF; font-size: 38px; font-weight: 800; letter-spacing: -0.5px;")
        layout.addWidget(brand)
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.66); font-size: 15px; font-weight: 500; letter-spacing: 0.5px;")
        layout.addWidget(subtitle)
        layout.addSpacing(22)

        divider = QFrame(self)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255,255,255,0.16);")
        layout.addWidget(divider)
        layout.addSpacing(20)

        tagline = QLabel("Keputusan persediaan yang lebih tepat,\nberbasis permintaan historis dan cuaca.")
        tagline.setStyleSheet("color: rgba(255,255,255,0.90); font-size: 18px; font-weight: 600; line-height: 1.5;")
        layout.addWidget(tagline)
        layout.addSpacing(22)

        for icon_name, text in (
            ("brain", "Prediksi permintaan otomatis (Random Forest, Decision Tree, Linear Regression)"),
            ("cloud-rain", "Integrasi permintaan historis dan faktor cuaca"),
            ("clipboard-check", "Rekomendasi pengadaan yang transparan dan dapat diaudit"),
        ):
            row = QHBoxLayout()
            row.setSpacing(10)
            icon_label = QLabel()
            icon_label.setFixedSize(26, 26)
            icon_label.setPixmap(
                self._circle_icon(icon_name)
            )
            row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("color: rgba(255,255,255,0.78); font-size: 13px;")
            row.addWidget(text_label, 1)
            layout.addLayout(row)
            layout.addSpacing(9)
        layout.addStretch(1)

        demo = QFrame(self)
        demo.setStyleSheet(
            "background: rgba(255,255,255,0.09); border: 1px solid rgba(255,255,255,0.13); border-radius: 13px;"
        )
        demo_layout = QVBoxLayout(demo)
        demo_layout.setContentsMargins(14, 11, 14, 14)
        demo_layout.setSpacing(4)
        demo_title = QLabel("DATA AKTUAL APOTEK PAHALA")
        demo_title.setStyleSheet("color: #8FE3C8; font-size: 11px; font-weight: 800; letter-spacing: 1.4px;")
        demo_layout.addWidget(demo_title)
        demo_text = QLabel(
            "Data stok opname dan pembelian Apotek Pahala 2022–2026. Permintaan merupakan estimasi, "
            "bukan transaksi kasir; hasil prediksi tetap perlu ditinjau apoteker."
        )
        demo_text.setWordWrap(True)
        demo_text.setStyleSheet("color: rgba(255,255,255,0.68); font-size: 12px; line-height: 1.4;")
        demo_layout.addWidget(demo_text)
        layout.addWidget(demo)
        layout.addSpacing(16)
        copy = QLabel(f"© {APP_YEAR} Apotek Pahala · Capstone Project")
        copy.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 10px;")
        layout.addWidget(copy)

    def _circle_icon(self, name: str):
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QIcon, QPixmap
        from app.core.icons import pixmap

        base = pixmap(name, "#B8F2DE", 18)
        canvas = QPixmap(52, 52)
        canvas.setDevicePixelRatio(2)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.drawEllipse(QRectF(1, 1, 24, 24))
        painter.drawPixmap(3, 3, 18, 18, base)
        painter.end()
        return canvas

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#0E7563"))
        gradient.setColorAt(0.52, QColor("#0B5F52"))
        gradient.setColorAt(1, QColor("#06362F"))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 11))
        painter.drawEllipse(QRectF(self.width() * 0.60, -self.width() * 0.20, self.width() * 0.72, self.width() * 0.72))
        painter.setBrush(QColor(255, 255, 255, 8))
        painter.drawEllipse(QRectF(-self.width() * 0.24, self.height() * 0.72, self.width() * 0.64, self.width() * 0.64))
        # Daun dekoratif di kanan bawah.
        painter.setBrush(QColor(32, 181, 138, 40))
        leaf = QPainterPath()
        leaf.moveTo(self.width() * 0.80, self.height() * 0.44)
        leaf.cubicTo(
            QPointF(self.width() * 0.72, self.height() * 0.60),
            QPointF(self.width() * 0.92, self.height() * 0.72),
            QPointF(self.width() * 0.99, self.height() * 0.92),
        )
        leaf.cubicTo(
            QPointF(self.width() * 0.76, self.height() * 0.86),
            QPointF(self.width() * 0.66, self.height() * 0.66),
            QPointF(self.width() * 0.80, self.height() * 0.44),
        )
        painter.drawPath(leaf)
        painter.end()
        super().paintEvent(event)


class LoginPage(QWidget):
    login_succeeded = Signal(dict)
    server_changed = Signal()
    start_backend_requested = Signal()

    def __init__(self, api, runner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.setObjectName("PageRoot")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        hero = HeroPanel(self)
        layout.addWidget(hero, 58)

        right = QFrame(self)
        right.setObjectName("LoginRight")
        self.right_panel = right
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(56, 34, 56, 26)
        right_layout.setSpacing(0)
        right_layout.addStretch(1)

        card = QFrame(self)
        card.setObjectName("Card")
        card.setMaximumWidth(430)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 12)
        color = QColor(theme.tokens["shadow"])
        color.setAlpha(30)
        shadow.setColor(color)
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 28, 30, 26)
        card_layout.setSpacing(0)

        heading = QLabel("Selamat datang kembali")
        heading.setObjectName("LoginTitle")
        card_layout.addWidget(heading)
        sub = QLabel("Masuk untuk memantau permintaan, stok, dan prakiraan kebutuhan apotek.")
        sub.setObjectName("LoginSubtitle")
        sub.setWordWrap(True)
        card_layout.addWidget(sub)
        card_layout.addSpacing(22)

        username_label = QLabel("Nama pengguna")
        username_label.setObjectName("FieldLabel")
        card_layout.addWidget(username_label)
        card_layout.addSpacing(5)
        self.username = QLineEdit(PREFS.last_username)
        self.username.setPlaceholderText("Masukkan nama pengguna")
        self.username.setMinimumHeight(42)
        self._user_action = self.username.addAction(icon("user-round", theme.tokens["muted"], 16), QLineEdit.ActionPosition.LeadingPosition)
        card_layout.addWidget(self.username)
        card_layout.addSpacing(13)

        password_label = QLabel("Password")
        password_label.setObjectName("FieldLabel")
        card_layout.addWidget(password_label)
        card_layout.addSpacing(5)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Masukkan password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMinimumHeight(42)
        self._pass_action = self.password.addAction(icon("lock-keyhole", theme.tokens["muted"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self._eye = self.password.addAction(icon("eye", theme.tokens["muted"], 16), QLineEdit.ActionPosition.TrailingPosition)
        self._eye.triggered.connect(self._toggle_password)
        card_layout.addWidget(self.password)
        card_layout.addSpacing(10)

        options = QHBoxLayout()
        self.remember = QCheckBox("Ingat sesi saya")
        self.remember.setChecked(PREFS.remember_session)
        options.addWidget(self.remember)
        options.addStretch(1)
        self.server_button = QPushButton("Pengaturan server")
        self.server_button.setObjectName("LoginLink")
        self.server_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.server_button.clicked.connect(self._server_dialog)
        options.addWidget(self.server_button)
        card_layout.addLayout(options)
        card_layout.addSpacing(6)

        self.error = InlineBanner("", "danger")
        self.error.hide()
        card_layout.addWidget(self.error)
        card_layout.addSpacing(10)

        self.submit = ThemedButton("Masuk ke Aplikasi", "primary", "arrow-right", icon_role="white")
        self.submit.setMinimumHeight(44)
        self.submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit.clicked.connect(self._submit)
        card_layout.addWidget(self.submit)
        card_layout.addSpacing(19)

        divider_row = QHBoxLayout()
        line = QFrame()
        line.setObjectName("LoginDivider")
        line.setFixedHeight(1)
        divider_row.addWidget(line, 1)
        or_label = QLabel("AKUN BAWAAN")
        or_label.setObjectName("LoginMeta")
        or_label.setStyleSheet("font-weight: 700; letter-spacing: 1px;")
        divider_row.addWidget(or_label)
        line2 = QFrame()
        line2.setObjectName("LoginDivider")
        line2.setFixedHeight(1)
        divider_row.addWidget(line2, 1)
        card_layout.addLayout(divider_row)
        card_layout.addSpacing(11)

        demo_row = QHBoxLayout()
        demo_row.setSpacing(8)
        admin = QPushButton("Isi Admin")
        admin.setProperty("variant", "outline")
        admin.setCursor(Qt.CursorShape.PointingHandCursor)
        admin.clicked.connect(lambda: self._fill("admin", "admin123"))
        demo_row.addWidget(admin)
        officer = QPushButton("Isi Petugas")
        officer.setProperty("variant", "outline")
        officer.setCursor(Qt.CursorShape.PointingHandCursor)
        officer.clicked.connect(lambda: self._fill("petugas", "petugas123"))
        demo_row.addWidget(officer)
        card_layout.addLayout(demo_row)
        card_layout.addSpacing(6)
        demo_note = QLabel("Ganti kata sandi bawaan setelah login pertama")
        demo_note.setObjectName("LoginMeta")
        demo_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(demo_note)
        right_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch(1)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {theme.tokens['warning']}; font-size: 8px;")
        status_row.addWidget(self.status_dot)
        self.status_text = QLabel("Memeriksa koneksi server...")
        self.status_text.setObjectName("LoginFooter")
        status_row.addWidget(self.status_text)
        status_row.addStretch(1)
        self.retry = QPushButton("Periksa ulang")
        self.retry.setObjectName("LoginLink")
        self.retry.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry.clicked.connect(self.check_health)
        status_row.addWidget(self.retry)
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("LoginFooter")
        status_row.addWidget(version)
        right_layout.addLayout(status_row)
        layout.addWidget(right, 42)

        self.username.returnPressed.connect(lambda: self.password.setFocus())
        self.password.returnPressed.connect(self._submit)
        self._loading = False
        theme.changed.connect(self._refresh_theme)
        self._refresh_theme()

    def _refresh_theme(self) -> None:
        tokens = theme.tokens
        self._user_action.setIcon(icon("user-round", tokens["muted"], 16))
        self._pass_action.setIcon(icon("lock-keyhole", tokens["muted"], 16))
        self._eye.setIcon(icon("eye", tokens["muted"], 16))
        tone = getattr(self, "_status_tone", "warning")
        self.status_dot.setStyleSheet(f"color: {tokens[tone]}; font-size: 8px;")

    def _toggle_password(self) -> None:
        if self.password.echoMode() == QLineEdit.EchoMode.Password:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye.setIcon(icon("eye-off", theme.tokens["muted"], 16))
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye.setIcon(icon("eye", theme.tokens["muted"], 16))

    def _fill(self, username: str, password: str) -> None:
        self.username.setText(username)
        self.password.setText(password)
        self.password.setFocus()

    def _server_dialog(self) -> None:
        dialog = ServerDialog(self.api, self)
        dialog.on_saved = lambda: (self.server_changed.emit(), self.check_health())
        dialog.exec()

    def _submit(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self._show_error("Nama pengguna dan password wajib diisi.")
            return
        self.error.hide()
        PREFS.remember_session = self.remember.isChecked()
        PREFS.last_username = username
        self._set_loading(True)
        self.api.set_token("")
        self.runner.submit(
            lambda: self.api.login(username, password),
            self._on_success,
            self._on_error,
            lambda: self._set_loading(False),
        )

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        self.submit.setEnabled(not loading)
        self.submit.setText("Memproses..." if loading else "Masuk ke Aplikasi")

    def _show_error(self, message: str) -> None:
        self.error.set_message(message, "danger")
        self.error.show()

    def _on_error(self, message: str, status: int) -> None:
        if status == 0:
            self._status_tone = "danger"
            self.status_dot.setStyleSheet(f"color: {theme.tokens['danger']}; font-size: 8px;")
            self.status_text.setText("Server tidak terhubung")
        self._show_error(message)

    def _on_success(self, payload: dict) -> None:
        user = payload.get("user", {})
        PREFS.last_username = user.get("username", self.username.text().strip())
        self.password.clear()
        self.login_succeeded.emit(user)

    def check_health(self) -> None:
        self._status_tone = "warning"
        self.status_dot.setStyleSheet(f"color: {theme.tokens['warning']}; font-size: 8px;")
        self.status_text.setText("Memeriksa koneksi server...")
        self.runner.submit(
            self.api.health,
            self._on_health,
            self._on_health_error,
        )

    def _on_health(self, payload: dict) -> None:
        self._status_tone = "success"
        self.status_dot.setStyleSheet(f"color: {theme.tokens['success']}; font-size: 8px;")
        database = payload.get("database", "-")
        database_label = "terhubung" if database == "connected" else str(database)
        self.status_text.setText(
            f"Server terhubung · {payload.get('medicines', 0)} obat · database {database_label}"
        )

    def _on_health_error(self, message: str, _status: int) -> None:
        self._status_tone = "danger"
        self.status_dot.setStyleSheet(f"color: {theme.tokens['danger']}; font-size: 8px;")
        self.status_text.setText("Server tidak terhubung. Jalankan backend lalu periksa ulang.")
        self.retry.setText("Coba lagi")
