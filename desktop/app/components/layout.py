"""Kerangka jendela desktop: title bar, sidebar, top bar, dan halaman bergulir."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.widgets import (
    Avatar,
    Badge,
    BrandMark,
    IconBox,
    IconButton,
    NavButton,
    SectionHeader,
    ThemedButton,
    fit_dialog_to_screen,
    refresh_style,
)
from app.core.async_worker import AsyncRunner
from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, APP_YEAR
from app.core.icons import icon, logo_pixmap, pixmap, stateful_icon
from app.core.theme import theme
from app.core.utils import relative_time


class TitleBar(QFrame):
    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self.setFixedHeight(40)
        self.setObjectName("TitleBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 4, 0)
        layout.setSpacing(8)
        logo = QLabel(self)
        logo.setPixmap(logo_pixmap(19))
        logo.setFixedSize(20, 20)
        logo.setScaledContents(True)
        layout.addWidget(logo)
        title = QLabel(f"{APP_NAME} — {APP_SUBTITLE}")
        title.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(title)
        layout.addStretch(1)
        self._buttons: list[QPushButton] = []
        for name, tooltip, slot in (
            ("minus", "Minimalkan", self._minimize),
            ("square", "Perbesar", self._toggle_maximize),
            ("x", "Tutup", self._close),
        ):
            button = QPushButton(self)
            button.setFixedSize(43, 30)
            button.setToolTip(tooltip)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(slot)
            button.setProperty("windowControl", name)
            layout.addWidget(button)
            self._buttons.append(button)
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        tokens = theme.tokens
        self.setStyleSheet(
            f"QFrame#TitleBar {{ background: {tokens['surface']}; border-bottom: 1px solid {tokens['border']}; }}"
            f"QFrame#TitleBar QLabel {{ color: {tokens['text']}; background: transparent; }}"
            f"QFrame#TitleBar QPushButton {{ background: transparent; border: none; border-radius: 4px; }}"
            f"QFrame#TitleBar QPushButton:hover {{ background: {tokens['hover']}; }}"
            f"QFrame#TitleBar QPushButton[windowControl=\"x\"]:hover {{ background: #E55353; }}"
        )
        for button, name in zip(self._buttons, ("minus", "square", "x")):
            glyph = {"minus": "—", "square": "▢", "x": "✕"}[name]
            button.setText(glyph)
            button.setStyleSheet(
                f"QPushButton {{ color: {tokens['text_soft']}; font-size: {12 if name != 'x' else 11}px;"
                f" font-weight: 500; padding: 0; }}"
                "QPushButton:hover { color: #FFFFFF; }"
            )

    def _minimize(self) -> None:
        self._window.showMinimized()

    def _toggle_maximize(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def _close(self) -> None:
        self._window.close()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._window.windowHandle()
            if handle is not None and handle.startSystemMove():
                return
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and not self._window.isMaximized():
            offset = getattr(self, "_drag_offset", None)
            if offset is not None:
                self._window.move(event.globalPosition().toPoint() - offset)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)


class Sidebar(QFrame):
    nav_selected = Signal(str)
    theme_mode_changed = Signal(str)

    NAV_ITEMS = [
        ("dashboard", "Ringkasan", "house"),
        ("prediction", "Prediksi Permintaan", "trending-up"),
        ("sales", "Data Penjualan", "shopping-bag"),
        ("weather", "Data Cuaca", "cloud-rain"),
        ("stock", "Manajemen Stok", "boxes"),
        ("procurement", "Rekomendasi Pengadaan", "clipboard-list"),
        ("reports", "Laporan", "file-text"),
        ("settings", "Pengaturan", "settings"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(286)
        self._buttons: dict[str, NavButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(3)

        # Blok merek diberi tinggi tetap supaya logo tidak pernah menimpa
        # tulisan "Apotek Pahala" saat jendela berada di ukuran minimum.
        brand = QWidget()
        brand.setFixedHeight(150)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(2)
        mark_card = QFrame()
        mark_card.setFixedSize(72, 72)
        mark_card.setStyleSheet("background: rgba(255,255,255,0.96); border-radius: 20px;")
        mark_layout = QVBoxLayout(mark_card)
        mark_layout.setContentsMargins(9, 9, 9, 9)
        mark_layout.addWidget(BrandMark(54))
        brand_layout.addWidget(mark_card, 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel("Apotek\nPahala")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setFixedHeight(60)
        name.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: 800;")
        brand_layout.addWidget(name, 0, Qt.AlignmentFlag.AlignHCenter)
        subtitle = QLabel("Pharmacy Intelligence")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFixedHeight(14)
        subtitle.setStyleSheet(f"color: {theme.tokens['sidebar_muted']}; font-size: 10px; font-weight: 500;")
        brand_layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(brand)
        layout.addSpacing(10)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for key, label, icon_name in self.NAV_ITEMS:
            button = NavButton(label, icon_name, self)
            button.clicked.connect(lambda _checked=False, value=key: self.nav_selected.emit(value))
            self._group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)
        self._buttons["dashboard"].setChecked(True)
        layout.addStretch(1)

        theme_card = QFrame(self)
        theme_card.setStyleSheet("background: rgba(255,255,255,0.07); border-radius: 12px;")
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(5, 5, 5, 5)
        theme_layout.setSpacing(4)
        theme_row = QHBoxLayout()
        theme_row.setSpacing(5)
        self._theme_group = QButtonGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_buttons: dict[str, QPushButton] = {}
        for mode, label, icon_name in (("light", "Terang", "sun"), ("dark", "Gelap", "moon")):
            button = QPushButton(label, theme_card)
            button.setCheckable(True)
            button.setProperty("theme", "true")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(32)
            button.setIconSize(QSize(15, 15))
            self._theme_group.addButton(button)
            self._theme_buttons[mode] = button
            button.clicked.connect(lambda _checked=False, value=mode: self._set_mode(value))
            theme_row.addWidget(button)
        theme_layout.addLayout(theme_row)
        layout.addWidget(theme_card)
        layout.addSpacing(6)

        version = QFrame(self)
        version.setStyleSheet("background: rgba(255,255,255,0.07); border-radius: 12px;")
        version_layout = QVBoxLayout(version)
        version_layout.setContentsMargins(10, 6, 10, 6)
        version_layout.setSpacing(1)
        version_label = QLabel(f"Versi {APP_VERSION}")
        version_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700;")
        version_layout.addWidget(version_label)
        copy = QLabel(f"© {APP_YEAR} Apotek Pahala")
        copy.setStyleSheet(f"color: {theme.tokens['sidebar_muted']}; font-size: 10px;")
        version_layout.addWidget(copy)
        layout.addWidget(version)

        theme.changed.connect(self._refresh_theme_buttons)

    def _set_mode(self, mode: str) -> None:
        self.theme_mode_changed.emit(mode)

    def set_mode(self, mode: str) -> None:
        effective = mode if mode in {"light", "dark"} else ("dark" if theme.is_dark else "light")
        button = self._theme_buttons.get(effective)
        if button:
            button.setChecked(True)
        self._refresh_theme_buttons()

    def _refresh_theme_buttons(self) -> None:
        effective = "dark" if theme.is_dark else "light"
        self._theme_group.setExclusive(False)
        for mode, button in self._theme_buttons.items():
            button.setChecked(mode == effective)
        self._theme_group.setExclusive(True)
        for mode, button in self._theme_buttons.items():
            name = "sun" if mode == "light" else "moon"
            button.setIcon(
                stateful_icon(
                    name,
                    theme.tokens["sidebar_muted"],
                    "#FFFFFF",
                    15,
                    2.0,
                )
            )
            if button.isChecked():
                button.setStyleSheet(
                    f"QPushButton[theme=\"true\"] {{ background: rgba(255,255,255,0.16); color: #FFFFFF;"
                    " border-radius: 9px; font-size: 12px; font-weight: 700; }}"
                )
            else:
                button.setStyleSheet(
                    f"QPushButton[theme=\"true\"] {{ background: transparent; color: {theme.tokens['sidebar_muted']};"
                    " border-radius: 9px; font-size: 12px; font-weight: 600; }"
                    "QPushButton[theme=\"true\"]:hover { background: rgba(255,255,255,0.09); color: #FFFFFF; }"
                )

    def set_active(self, key: str) -> None:
        button = self._buttons.get(key)
        if button:
            button.setChecked(True)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 9))
        path = QPainterPath()
        path.moveTo(QPointF(self.width() * 0.35, self.height() * 0.70))
        path.cubicTo(
            QPointF(self.width() * 0.70, self.height() * 0.60),
            QPointF(self.width() * 0.38, self.height() * 0.82),
            QPointF(self.width() * 0.95, self.height() * 0.78),
        )
        path.cubicTo(
            QPointF(self.width() * 0.70, self.height() * 0.92),
            QPointF(self.width() * 0.55, self.height() * 0.80),
            QPointF(self.width() * 0.35, self.height() * 0.70),
        )
        painter.drawPath(path)
        path2 = QPainterPath()
        path2.moveTo(-10, self.height() * 0.93)
        path2.cubicTo(
            QPointF(self.width() * 0.30, self.height() * 0.82),
            QPointF(self.width() * 0.40, self.height() * 1.02),
            QPointF(self.width() * 0.75, self.height() * 0.95),
        )
        path2.cubicTo(
            QPointF(self.width() * 0.50, self.height() * 1.06),
            QPointF(self.width() * 0.20, self.height() * 1.02),
            QPointF(-10, self.height() * 0.93),
        )
        painter.drawPath(path2)
        painter.end()


class TopBar(QFrame):
    notifications_clicked = Signal()
    user_menu_requested = Signal(QPoint)
    period_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(96)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 17, 30, 13)
        layout.setSpacing(14)

        title_block = QHBoxLayout()
        title_block.setSpacing(12)
        self._accent = QFrame(self)
        self._accent.setFixedWidth(4)
        self._accent.setFixedHeight(46)
        self._accent.setStyleSheet(f"background: {theme.tokens['primary']}; border-radius: 2px;")
        title_block.addWidget(self._accent)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = QLabel("Ringkasan Apotek")
        self.title.setObjectName("PageTitle")
        text.addWidget(self.title)
        self.subtitle = QLabel("Pantau permintaan, persediaan, dan prediksi kebutuhan apotek.")
        self.subtitle.setObjectName("PageSubtitle")
        text.addWidget(self.subtitle)
        title_block.addLayout(text)
        layout.addLayout(title_block, 1)

        self.period = QPushButton()
        self.period.setObjectName("PeriodChip")
        self.period.setCursor(Qt.CursorShape.PointingHandCursor)
        self.period.setMinimumHeight(40)
        self.period.setIconSize(QSize(15, 15))
        self.period.clicked.connect(self.period_clicked.emit)
        layout.addWidget(self.period)

        self.bell = QPushButton(self)
        self.bell.setFixedSize(42, 42)
        self.bell.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bell.setToolTip("Notifikasi")
        self.bell.clicked.connect(self.notifications_clicked.emit)
        layout.addWidget(self.bell)

        self.user_button = QPushButton(self)
        self.user_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_button.setMinimumHeight(46)
        self.user_button.setIconSize(QSize(30, 30))
        self.user_button.clicked.connect(lambda: self.user_menu_requested.emit(self.user_button.mapToGlobal(QPoint(0, self.user_button.height()))))
        layout.addWidget(self.user_button)
        self._count = 0
        self._badge = QLabel(self.bell)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.hide()
        self._user_name = "Admin"
        self._user_role = "Admin"
        self._initials = "A"
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        tokens = theme.tokens
        self.setStyleSheet(
            f"QFrame#TopBar {{ background: {tokens['bg']}; border: none; }}"
            f"QLabel#PageTitle {{ color: {tokens['text']}; font-size: 28px; font-weight: 800; }}"
            f"QLabel#PageSubtitle {{ color: {tokens['muted']}; font-size: 13px; }}"
            f"QPushButton#PeriodChip {{ background: {tokens['surface']}; border: 1px solid {tokens['border']};"
            f" border-radius: 10px; color: {tokens['text_soft']}; padding: 8px 13px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton#PeriodChip:hover {{ border-color: {tokens['primary']}; color: {tokens['primary']}; }}"
        )
        self._accent.setStyleSheet(f"background: {tokens['primary']}; border-radius: 2px;")
        self.period.setIcon(icon("calendar-range", tokens["muted"], 15))
        self.bell.setIcon(icon("bell", tokens["text_soft"], 19))
        self.bell.setStyleSheet(
            f"QPushButton {{ background: {tokens['surface']}; border: 1px solid {tokens['border']};"
            f" border-radius: 11px; }} QPushButton:hover {{ background: {tokens['hover']};"
            f" border-color: {tokens['border_strong']}; }}"
        )
        self._badge.setStyleSheet(
            f"background: {tokens['danger']}; color: white; border-radius: 8px;"
            "font-size: 10px; font-weight: 700; padding: 0 2px;"
        )
        self._badge.resize(17 if self._count < 10 else 23, 17)
        self._badge.move(self.bell.width() - self._badge.width() - 1, 0)
        self.user_button.setStyleSheet(
            f"QPushButton {{ background: {tokens['surface']}; border: 1px solid {tokens['border']};"
            f" border-radius: 11px; padding: 4px 11px 4px 5px; color: {tokens['text']};"
            "font-size: 13px; font-weight: 600; text-align: left; }"
            f"QPushButton:hover {{ border-color: {tokens['primary']}; }}"
        )
        self._render_user_icon()

    def _render_user_icon(self) -> None:
        tokens = theme.tokens
        size = 30
        canvas = QPixmap(size * 2, size * 2)
        canvas.setDevicePixelRatio(2)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(tokens["secondary"]))
        painter.drawEllipse(QRectF(0, 0, size, size))
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI")
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, self._initials)
        painter.end()
        from PySide6.QtGui import QIcon

        self.user_button.setIcon(QIcon(canvas))
        self.user_button.setText(f"  {self._user_name}  ▾")

    def set_page(self, title: str, subtitle: str) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def set_period(self, text: str) -> None:
        self.period.setText(f"  {text}")
        self.period.setVisible(bool(text))

    def set_user(self, name: str, role: str, initials: str) -> None:
        self._user_name = name
        self._user_role = role
        self._initials = initials
        self._render_user_icon()

    def set_count(self, count: int) -> None:
        self._count = max(0, int(count))
        if self._count:
            self._badge.setText("9+" if self._count > 9 else str(self._count))
            self._badge.show()
            self._badge.raise_()
        else:
            self._badge.hide()

    def period_text(self) -> str:
        return self.period.text().strip()


class PageScroll(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PageScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self._content = QWidget()
        self._content.setObjectName("PageRoot")
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(28, 4, 28, 26)
        self._layout.setSpacing(18)
        self.setWidget(self._content)

    @property
    def content(self) -> QWidget:
        return self._content

    @property
    def body(self) -> QVBoxLayout:
        return self._layout

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self._layout.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)

    def add_stretch(self) -> None:
        self._layout.addStretch(1)


class PageBase(QWidget):
    """Halaman dengan area gulir dan pembantu untuk header konten."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PageRoot")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.scroll = PageScroll(self)
        outer.addWidget(self.scroll)
        self.body = self.scroll.body
        self._dialogs: list[QDialog] = []

    def section(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str | None = None,
        action: QWidget | None = None,
    ) -> SectionHeader:
        header = SectionHeader(title, subtitle, icon_name, action)
        self.body.addWidget(header)
        return header

    def toast(self, message: str, tone: str = "success") -> None:
        window = self.window()
        manager = getattr(window, "toast", None)
        if callable(manager):
            manager(message, tone)

    def register_dialog(self, dialog: QDialog) -> QDialog:
        self._dialogs.append(dialog)
        dialog.finished.connect(lambda _result: self._dialogs.remove(dialog) if dialog in self._dialogs else None)
        return dialog

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.on_show()

    def show_event(self, event) -> None:
        """Alias lama; Qt memanggil showEvent (camelCase)."""
        self.showEvent(event)

    def on_show(self) -> None:
        """Hook saat halaman ditampilkan."""


class NotificationDialog(QDialog):
    changed = Signal()

    def __init__(self, api, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self._runner = AsyncRunner(self)
        self.setWindowTitle("Notifikasi")
        self.setModal(True)
        self.setMinimumSize(520, 560)
        self._items: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        self.title = QLabel("Notifikasi")
        self.title.setObjectName("SectionTitle")
        head.addWidget(self.title)
        head.addStretch(1)
        self.mark_all = QPushButton("Tandai semua dibaca")
        self.mark_all.setProperty("variant", "ghost")
        self.mark_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mark_all.clicked.connect(self._mark_all)
        head.addWidget(self.mark_all)
        layout.addLayout(head)
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)
        self.empty = QLabel("Tidak ada notifikasi.")
        self.empty.setObjectName("Muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)
        close = ThemedButton("Tutup", "outline")
        close.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        fit_dialog_to_screen(self)

    def refresh(self) -> None:
        def task() -> dict:
            return self.api.get("/notifications", params={"limit": 50}, timeout=15)

        def ok(payload: dict) -> None:
            self._items = payload.get("items", [])
            for index in reversed(range(self.list_layout.count())):
                item = self.list_layout.takeAt(index)
                if item.widget():
                    item.widget().deleteLater()
            self.empty.setVisible(not self._items)
            for item in self._items:
                self.list_layout.addWidget(self._item_card(item))

        def bad(message: str, _status: int) -> None:
            self.empty.setText(message)
            self.empty.show()

        self._runner.submit(task, ok, bad)

    def _item_card(self, item: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("SoftCard")
        config = {
            "success": ("success", "circle-check", "success_bg"),
            "warning": ("warning_text", "triangle-alert", "warning_bg"),
            "danger": ("danger_text", "circle-alert", "danger_bg"),
            "info": ("info_text", "info", "info_bg"),
        }
        color_role, icon_name, bg_role = config.get(item.get("level", "info"), config["info"])
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)
        box = IconBox(icon_name, color_role, bg_role, 32, 15)
        row.addWidget(box)
        text = QVBoxLayout()
        text.setSpacing(2)
        title_row = QHBoxLayout()
        title = QLabel(item.get("title", "Notifikasi"))
        title.setStyleSheet("font-size: 12px; font-weight: 700;")
        title_row.addWidget(title)
        if not item.get("is_read"):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {theme.tokens['primary']}; font-size: 9px;")
            title_row.addWidget(dot)
        title_row.addStretch(1)
        time_label = QLabel(relative_time(item.get("created_at")))
        time_label.setObjectName("MutedSmall")
        title_row.addWidget(time_label)
        text.addLayout(title_row)
        message = QLabel(item.get("message", ""))
        message.setObjectName("Muted")
        message.setWordWrap(True)
        text.addWidget(message)
        row.addLayout(text, 1)
        if not item.get("is_read"):
            button = IconButton("check", "Tandai dibaca", "primary", 28, 14, "ghost")
            button.clicked.connect(lambda _checked=False, item_id=item.get("id"): self._mark_read(item_id))
            row.addWidget(button)
        return card

    def _mark_read(self, notification_id: int) -> None:
        def task() -> Any:
            return self.api.post(f"/notifications/{notification_id}/read", timeout=15)

        def ok(_result: Any) -> None:
            self.refresh()
            self.changed.emit()

        def bad(message: str, _status: int) -> None:
            self.empty.setText(message)
            self.empty.show()

        self._runner.submit(task, ok, bad)

    def _mark_all(self) -> None:
        def task() -> Any:
            return self.api.post("/notifications/read-all", timeout=20)

        def ok(_result: Any) -> None:
            self.refresh()
            self.changed.emit()

        def bad(message: str, _status: int) -> None:
            self.empty.setText(message)
            self.empty.show()

        self._runner.submit(task, ok, bad)
