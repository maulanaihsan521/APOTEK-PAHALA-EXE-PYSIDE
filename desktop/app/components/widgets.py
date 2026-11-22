"""Komponen antarmuka bersama untuk aplikasi desktop."""
from __future__ import annotations

from typing import Any, Callable, Iterable

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.icons import icon, logo_pixmap, pixmap, stateful_icon
from app.core.theme import theme


def hand_cursor(widget: QWidget) -> None:
    widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))


def set_variant(widget: QWidget, variant: str) -> None:
    widget.setProperty("variant", variant)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def refresh_style(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class ElidedLabel(QLabel):
    """Label satu baris yang memendek dengan elipsis dan menyimpan teks lengkap di tooltip."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._apply_elide()

    def _apply_elide(self) -> None:
        if self.width() > 2:
            self.setTextFormat(Qt.TextFormat.PlainText)
            super().setText(
                self.fontMetrics().elidedText(
                    self._full_text, Qt.TextElideMode.ElideRight, max(0, self.width() - 2)
                )
            )
        else:
            super().setText(self._full_text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_elide()


def fit_dialog_to_screen(dialog: QDialog, margin: int = 44) -> None:
    """Batasi ukuran dialog agar tombol aksi tetap terlihat di layar kecil."""
    screen = dialog.screen() or QApplication.primaryScreen()
    if screen is None:
        return
    available = screen.availableGeometry()
    max_width = max(320, available.width() - margin)
    max_height = max(320, available.height() - margin)
    width = min(dialog.width(), max_width)
    height = min(dialog.height(), max_height)
    if (width, height) != (dialog.width(), dialog.height()):
        dialog.resize(width, height)
    frame = dialog.frameGeometry()
    x = frame.x()
    y = frame.y()
    if x + width > available.right():
        x = available.right() - width - 8
    if y + height > available.bottom():
        y = available.bottom() - height - 8
    x = max(available.left() + 8, x)
    y = max(available.top() + 8, y)
    if (x, y) != (frame.x(), frame.y()):
        dialog.move(x, y)


class Card(QFrame):
    def __init__(
        self,
        parent: QWidget | None = None,
        padding: int = 18,
        spacing: int = 12,
        shadow: bool = True,
        object_name: str = "Card",
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)
        self._shadow: QGraphicsDropShadowEffect | None = None
        if shadow:
            self._shadow = QGraphicsDropShadowEffect(self)
            self._shadow.setBlurRadius(26)
            self._shadow.setOffset(0, 5)
            self.setGraphicsEffect(self._shadow)
            self._update_shadow()
            theme.changed.connect(self._update_shadow)

    def _update_shadow(self) -> None:
        if not self._shadow:
            return
        color = QColor(theme.tokens["shadow"])
        color.setAlpha(110 if theme.is_dark else 30)
        self._shadow.setColor(color)


class SoftCard(QFrame):
    def __init__(self, parent: QWidget | None = None, padding: int = 14, object_name: str = "SoftCard") -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(10)


class IconBox(QLabel):
    def __init__(
        self,
        name: str,
        color_role: str = "primary",
        bg_role: str = "primary_soft",
        size: int = 38,
        icon_size: int = 18,
        parent: QWidget | None = None,
        radius: int | None = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._color_role = color_role
        self._bg_role = bg_role
        self._icon_size = icon_size
        self._radius = radius if radius is not None else max(8, size // 3)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh()
        theme.changed.connect(self._refresh)

    def set_icon(self, name: str) -> None:
        self._name = name
        self._refresh()

    def _bg_color(self) -> str:
        tokens = theme.tokens
        mapping = {
            "primary_soft": tokens["primary_soft"],
            "primary_bg": tokens["primary_soft"],
            "success_bg": tokens["success_bg"],
            "warning_bg": tokens["warning_bg"],
            "danger_bg": tokens["danger_bg"],
            "info_bg": tokens["info_bg"],
            "purple_bg": tokens["purple_bg"],
            "surface_alt": tokens["surface_alt"],
            "accent_soft": tokens["accent_soft"],
            "accent_bg": tokens["accent_soft"],
            "white": tokens["surface"],
        }
        return mapping.get(self._bg_role, tokens["surface_alt"])

    def _refresh(self) -> None:
        color = theme.color(self._color_role)
        self.setPixmap(pixmap(self._name, color, self._icon_size, 2.0))
        self.setStyleSheet(
            f"background-color: {self._bg_color()}; border-radius: {self._radius}px;"
        )


class ThemedButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        icon_name: str | None = None,
        icon_role: str = "text",
        icon_size: int = 16,
        parent: QWidget | None = None,
        compact: bool = False,
    ) -> None:
        super().__init__(text, parent)
        self._icon_name = icon_name
        self._icon_role = icon_role
        self._icon_size = icon_size
        self._default_text = text
        self._loading = False
        set_variant(self, variant)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if compact:
            self.setProperty("flat", "true")
        if icon_name:
            self._refresh_icon()
        theme.changed.connect(self._on_theme)

    def _refresh_icon(self) -> None:
        if not self._icon_name:
            return
        color = theme.color(self._icon_role)
        self.setIcon(icon(self._icon_name, color, self._icon_size))

    def _on_theme(self) -> None:
        self._refresh_icon()

    def start_loading(self, text: str = "Memproses...") -> None:
        if self._loading:
            return
        self._loading = True
        self._default_text = self.text()
        self.setText(text)
        self.setEnabled(False)

    def stop_loading(self) -> None:
        if not self._loading:
            return
        self._loading = False
        self.setText(self._default_text)
        self.setEnabled(True)


class IconButton(QPushButton):
    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        role: str = "muted",
        size: int = 34,
        icon_size: int = 17,
        variant: str | None = "outline",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._name = icon_name
        self._role = role
        self._icon_size = icon_size
        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if variant:
            set_variant(self, variant)
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        color = theme.color(self._role)
        self.setIcon(icon(self._name, color, self._icon_size))


class NavButton(QPushButton):
    def __init__(self, text: str, icon_name: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._name = icon_name
        self.setCheckable(True)
        self.setProperty("nav", "true")
        self.setMinimumHeight(39)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        self.setIcon(
            stateful_icon(
                self._name,
                theme.tokens["sidebar_muted"],
                "#FFFFFF",
                18,
                2.0,
            )
        )


class BellButton(QPushButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Notifikasi")
        self._count = 0
        self._refreshing = False
        self._badge = QLabel(self)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setFixedHeight(17)
        self._badge.hide()
        self._refresh()
        theme.changed.connect(self._refresh)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_badge()

    def _place_badge(self) -> None:
        if self._count <= 0:
            return
        width = 17 if self._count < 10 else 23
        self._badge.setFixedWidth(width)
        self._badge.move(self.width() - width - 1, 1)

    def _refresh(self) -> None:
        self.setIcon(icon("bell", theme.color("text_soft"), 19, 2.0))
        self.setStyleSheet(
            f"QPushButton {{ background: {theme.tokens['surface']}; border: 1px solid {theme.tokens['border']};"
            f" border-radius: 12px; }}"
            f"QPushButton:hover {{ background: {theme.tokens['hover']}; }}"
        )
        self._badge.setStyleSheet(
            f"background: {theme.tokens['danger']}; color: white; border-radius: 8px;"
            "font-size: 10px; font-weight: 700; padding: 0px 2px;"
        )
        self._place_badge()

    def set_count(self, count: int) -> None:
        self._count = max(0, int(count))
        if self._count:
            self._badge.setText("9+" if self._count > 9 else str(self._count))
            self._badge.show()
        else:
            self._badge.hide()
        self._place_badge()


class Badge(QLabel):
    TONES = {
        "primary": ("primary_soft", "primary"),
        "success": ("success_bg", "success"),
        "warning": ("warning_bg", "warning_text"),
        "danger": ("danger_bg", "danger_text"),
        "info": ("info_bg", "info_text"),
        "purple": ("purple_bg", "purple"),
        "neutral": ("surface_alt", "muted"),
    }

    def __init__(self, text: str = "", tone: str = "neutral", dot: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tone = tone
        self._dot = dot
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(("●  " if dot else "") + text)
        self._refresh()
        theme.changed.connect(self._refresh)

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self._refresh()

    def _refresh(self) -> None:
        tokens = theme.tokens
        bg_key, fg_key = self.TONES.get(self._tone, self.TONES["neutral"])
        bg = tokens[bg_key]
        fg = tokens[fg_key]
        border = tokens["border"] if self._tone == "neutral" else bg
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {border};"
            "border-radius: 9px; padding: 2px 8px; font-size: 11px; font-weight: 700;"
        )


class KpiCard(QFrame):
    def __init__(
        self,
        label: str,
        icon_name: str,
        tone: str = "primary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tone = tone
        self._icon_name = icon_name
        self.setObjectName("Card")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 4)
        self.setGraphicsEffect(self._shadow)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._stripe = QFrame(self)
        self._stripe.setFixedWidth(4)
        outer.addWidget(self._stripe)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 15, 18, 14)
        layout.setSpacing(5)
        outer.addWidget(content, 1)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.icon_box = IconBox(icon_name, "primary", "primary_soft", 40, 18)
        top.addWidget(self.icon_box)
        self.title = QLabel(label)
        self.title.setObjectName("KpiLabel")
        self.title.setWordWrap(True)
        top.addWidget(self.title, 1)
        layout.addLayout(top)

        self.value = QLabel("—")
        self.value.setObjectName("KpiValue")
        layout.addWidget(self.value)

        bottom = QHBoxLayout()
        bottom.setSpacing(7)
        self.delta = QLabel("")
        self.delta.hide()
        bottom.addWidget(self.delta)
        self.hint = QLabel("")
        self.hint.setObjectName("KpiHint")
        self.hint.setWordWrap(True)
        bottom.addWidget(self.hint, 1)
        layout.addLayout(bottom)

        self._refresh()
        theme.changed.connect(self._refresh)

    def set_value(self, value: str, hint: str = "", delta: float | None = None) -> None:
        self.value.setText(value)
        self.hint.setText(hint)
        if delta is None:
            self.delta.hide()
        else:
            positive = delta >= 0
            arrow = "↑" if positive else "↓"
            self.delta.setText(f"{arrow} {abs(delta):.1f}%".replace(".", ","))
            self.delta.show()
            tokens = theme.tokens
            bg = tokens["success_bg"] if positive else tokens["danger_bg"]
            fg = tokens["success"] if positive else tokens["danger_text"]
            self.delta.setStyleSheet(
                f"background: {bg}; color: {fg}; border-radius: 8px; padding: 2px 6px;"
                "font-size: 11px; font-weight: 700;"
            )

    def _refresh(self) -> None:
        mapping = {
            "primary": ("primary", "primary_soft"),
            "info": ("info", "info_bg"),
            "warning": ("warning", "warning_bg"),
            "accent": ("accent", "accent_soft"),
            "purple": ("purple", "purple_bg"),
            "success": ("success", "success_bg"),
        }
        fg, bg = mapping.get(self._tone, mapping["primary"])
        self._stripe.setStyleSheet(f"background-color: {theme.color(fg)}; border-top-left-radius: 13px; border-bottom-left-radius: 13px;")
        self.icon_box._color_role = fg
        self.icon_box._bg_role = bg
        self.icon_box._refresh()
        color = QColor(theme.tokens["shadow"])
        color.setAlpha(110 if theme.is_dark else 30)
        self._shadow.setColor(color)


class StatTile(QFrame):
    def __init__(
        self,
        label: str,
        icon_name: str,
        tone: str = "primary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SoftCard")
        self._tone = tone
        self.setMinimumHeight(120)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        self.icon_box = IconBox(icon_name, tone if tone != "warning" else "warning_text", f"{tone}_bg", 40, 17)
        layout.addWidget(self.icon_box)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = QLabel(label)
        self.title.setObjectName("MutedSmall")
        self.title.setWordWrap(True)
        self.value = QLabel("—")
        self.value.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.sub = QLabel("")
        self.sub.setObjectName("MutedSmall")
        self.sub.setWordWrap(True)
        text.addWidget(self.title)
        text.addWidget(self.value)
        text.addWidget(self.sub)
        layout.addLayout(text, 1)
        theme.changed.connect(self._refresh)

    def set_value(self, value: str, sub: str = "") -> None:
        self.value.setText(value)
        self.sub.setText(sub)
        self.sub.setVisible(bool(sub))

    def _refresh(self) -> None:
        self.icon_box._bg_role = f"{self._tone}_bg"
        self.icon_box._color_role = "warning_text" if self._tone == "warning" else self._tone
        self.icon_box._refresh()


class ResponsiveCardRow(QWidget):
    """Deretan kartu yang otomatis membungkus saat lebar layar terbatas."""

    def __init__(
        self,
        cards: Iterable[QWidget],
        spacing: int = 12,
        min_width: int = 200,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._cards = list(cards)
        self._spacing = spacing
        self._min_width = min_width
        self._columns = 0
        self._signature: tuple[int, tuple[int, ...]] | None = None
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(spacing)
        for card in self._cards:
            card.setParent(self)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._apply_columns(1)

    def _visible_cards(self) -> list[QWidget]:
        return [card for card in self._cards if not card.isHidden()]

    def _card_height(self, cards: list[QWidget], minimum: bool = False) -> int:
        heights = []
        for card in cards:
            hint = card.minimumSizeHint() if minimum else card.sizeHint()
            heights.append(max(hint.height(), card.minimumHeight()))
        return max(heights, default=0)

    def _grid_height(self, columns: int, minimum: bool = False) -> int:
        cards = self._visible_cards()
        rows = max(1, (len(cards) + columns - 1) // columns)
        height = 0
        for row in range(rows):
            batch = cards[row * columns:(row + 1) * columns]
            height += self._card_height(batch, minimum)
        return height + max(0, rows - 1) * self._spacing

    def minimumSizeHint(self) -> QSize:
        """Jangan biarkan jumlah kolom saat ini memaksa lebar halaman.

        QGridLayout menghitung lebar minimum dari semua kolom. Pada jendela
        minimum, hal itu membuat baris kartu 4 kolom memaksa halaman melebar
        sehingga kartu terakhir terpotong. Minimum width cukup satu kartu;
        jumlah kolom ditentukan ulang dari lebar yang tersedia.
        """
        cards = self._visible_cards()
        if not cards:
            return QSize(0, 0)
        columns = max(1, self._columns)
        return QSize(self._min_width, self._grid_height(columns, minimum=True))

    def sizeHint(self) -> QSize:
        cards = self._visible_cards()
        if not cards:
            return QSize(0, 0)
        columns = max(1, self._columns)
        return QSize(self._min_width, self._grid_height(columns))

    def _candidate_columns(self, count: int | None = None) -> list[int]:
        """Urutkan jumlah kolom dari yang paling rapi dan paling lega.

        Kolom dipilih agar baris terakhir tidak menyisakan satu kartu
        menggantung. Contoh: 4 kartu menjadi 4 atau 2 kolom, bukan 3 + 1.
        """
        total = len(self._cards) if count is None else count
        if total <= 1:
            return [1]
        candidates = list(range(1, total + 1))

        def waste(columns: int) -> int:
            rows = (total + columns - 1) // columns
            return rows * columns - total

        candidates.sort(key=lambda columns: (waste(columns), -columns))
        return candidates

    def _apply_columns(self, columns: int) -> None:
        cards = self._visible_cards()
        signature = (columns, tuple(id(card) for card in cards))
        if signature == self._signature:
            return
        while self._grid.count():
            self._grid.takeAt(0)
        for index, card in enumerate(cards):
            self._grid.addWidget(card, index // columns, index % columns)
        for column in range(len(self._cards)):
            self._grid.setColumnStretch(column, 1 if column < columns else 0)
        self._columns = columns
        self._signature = signature
        self.updateGeometry()

    def refresh(self) -> None:
        cards = self._visible_cards()
        if not cards:
            return
        width = self.width()
        for columns in self._candidate_columns(len(cards)):
            required = columns * self._min_width + (columns - 1) * self._spacing
            if width >= required:
                self._apply_columns(columns)
                return
        self._apply_columns(1)

    def resizeEvent(self, event) -> None:
        self.refresh()
        super().resizeEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.refresh)


class SectionHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str | None = None,
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.icon_box: IconBox | None = None
        if icon_name:
            self.icon_box = IconBox(icon_name, "primary", "primary_soft", 30, 15, radius=8)
            layout.addWidget(self.icon_box)
        text = QVBoxLayout()
        text.setSpacing(1)
        self.title = QLabel(title)
        self.title.setObjectName("SectionTitle")
        self.title.setWordWrap(True)
        text.addWidget(self.title)
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("SectionSubtitle")
        self.subtitle.setWordWrap(True)
        self.subtitle.setVisible(bool(subtitle))
        text.addWidget(self.subtitle)
        layout.addLayout(text, 1)
        if action:
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignVCenter)


class SearchInput(QLineEdit):
    def __init__(self, placeholder: str = "Cari...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(40)
        self._action = self.addAction(QIcon(), QLineEdit.ActionPosition.LeadingPosition)
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        self._action.setIcon(icon("search", theme.color("muted"), 16))


class SegmentedControl(QFrame):
    changed = Signal(object)

    def __init__(self, options: Iterable[tuple[Any, str]], current: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Segment")
        self._buttons: dict[Any, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(0)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for value, label in options:
            button = QPushButton(str(label).replace("&", "&&"), self)
            button.setCheckable(True)
            button.setProperty("segment", "true")
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.setMinimumHeight(26)
            group.addButton(button)
            layout.addWidget(button)
            self._buttons[value] = button
            button.clicked.connect(lambda _checked=False, v=value: self.changed.emit(v))
        self.set_value(current if current is not None else next(iter(self._buttons), None))

    def set_value(self, value: Any) -> None:
        button = self._buttons.get(value)
        if button:
            button.setChecked(True)

    def value(self) -> Any:
        for value, button in self._buttons.items():
            if button.isChecked():
                return value
        return None


class Field(QWidget):
    def __init__(
        self,
        label: str,
        widget: QWidget,
        hint: str = "",
        required: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        if label:
            text = QLabel(label + (" *" if required else ""))
            text.setObjectName("FieldLabel")
            layout.addWidget(text)
        layout.addWidget(widget)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("Hint")
            hint_label.setWordWrap(True)
            layout.addWidget(hint_label)
        self.widget = widget


class EmptyState(QWidget):
    def __init__(
        self,
        title: str,
        description: str = "",
        icon_name: str = "info",
        action: QWidget | None = None,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24 if compact else 34, 16, 24 if compact else 34)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_box = IconBox(icon_name, "primary", "primary_soft", 48 if not compact else 40, 22 if not compact else 18)
        layout.addWidget(self.icon_box, 0, Qt.AlignmentFlag.AlignHCenter)
        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(self.title)
        if description:
            self.description = QLabel(description)
            self.description.setObjectName("Muted")
            self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.description.setWordWrap(True)
            self.description.setMaximumWidth(420)
            layout.addWidget(self.description, 0, Qt.AlignmentFlag.AlignHCenter)
        if action:
            layout.addSpacing(4)
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignHCenter)


class InlineBanner(QFrame):
    TONES = {
        "info": ("info_bg", "info_text", "info"),
        "success": ("success_bg", "success", "circle-check"),
        "warning": ("warning_bg", "warning_text", "triangle-alert"),
        "danger": ("danger_bg", "danger_text", "circle-alert"),
    }

    def __init__(
        self,
        message: str = "",
        tone: str = "info",
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tone = tone
        self._message = message
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(8)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        self.text = QLabel(message)
        self.text.setWordWrap(True)
        layout.addWidget(self.text, 1)
        if action:
            layout.addWidget(action)
        self._refresh()
        theme.changed.connect(self._refresh)

    def set_message(self, message: str, tone: str | None = None) -> None:
        self._message = message
        if tone:
            self._tone = tone
        self.text.setText(message)
        self._refresh()

    def _refresh(self) -> None:
        tokens = theme.tokens
        bg_key, fg_key, icon_name = self.TONES.get(self._tone, self.TONES["info"])
        self.setStyleSheet(
            f"QFrame {{ background: {tokens[bg_key]}; border: 1px solid {tokens[bg_key]}; border-radius: 10px; }}"
            f"QLabel {{ color: {tokens[fg_key]}; font-size: 12px; background: transparent; border: none; }}"
        )
        self.icon_label.setPixmap(pixmap(icon_name, tokens[fg_key], 15, 2.0))


class Toast(QFrame):
    def __init__(self, parent: QWidget, message: str, tone: str = "success") -> None:
        super().__init__(parent)
        self._tone = tone
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMaximumWidth(390)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(9)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(17, 17)
        layout.addWidget(self.icon_label)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 12px;")
        layout.addWidget(label, 1)
        close = QPushButton("×", self)
        close.setFixedSize(20, 20)
        close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close.clicked.connect(self.dismiss)
        layout.addWidget(close, 0, Qt.AlignmentFlag.AlignTop)
        self._apply_style()
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._closing = False
        theme.changed.connect(self._apply_style)

    def _apply_style(self) -> None:
        tokens = theme.tokens
        mapping = {
            "success": ("success", "circle-check"),
            "error": ("danger", "circle-alert"),
            "warning": ("warning", "triangle-alert"),
            "info": ("info", "info"),
        }
        color_key, icon_name = mapping.get(self._tone, mapping["info"])
        self.setStyleSheet(
            f"QFrame {{ background: {tokens['surface']}; border: 1px solid {tokens['border']};"
            f" border-left: 3px solid {tokens[color_key]}; border-radius: 10px; }}"
            "QLabel { background: transparent; border: none; }"
            f"QPushButton {{ background: transparent; border: none; color: {tokens['muted']};"
            "font-size: 15px; font-weight: 700; padding: 0; }"
            f"QPushButton:hover {{ color: {tokens['danger']}; }}"
        )
        self.icon_label.setPixmap(pixmap(icon_name, tokens[color_key], 16, 2.0))

    def fade_in(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def dismiss(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._finish)
        self._anim.start()

    def _finish(self) -> None:
        manager = getattr(self.parent(), "_toast_manager", None)
        if manager:
            manager.remove(self)
        self.deleteLater()


class ToastManager:
    def __init__(self, parent: QWidget) -> None:
        self.parent = parent
        self.toasts: list[Toast] = []
        parent._toast_manager = self  # type: ignore[attr-defined]

    def show(self, message: str, tone: str = "success") -> None:
        toast = Toast(self.parent, message, tone)
        toast.adjustSize()
        self.toasts.append(toast)
        toast.show()
        toast.raise_()
        self._reposition()
        toast.fade_in()
        QTimer.singleShot(4200, toast.dismiss)

    def remove(self, toast: Toast) -> None:
        if toast in self.toasts:
            self.toasts.remove(toast)
        self._reposition()

    def _reposition(self) -> None:
        margin = 22
        y = self.parent.height() - margin
        for toast in reversed(self.toasts):
            toast.adjustSize()
            width = min(390, max(260, toast.sizeHint().width()))
            height = toast.sizeHint().height()
            toast.resize(width, height)
            y -= height
            toast.move(self.parent.width() - width - margin, y)
            y -= 10


class Spinner(QWidget):
    def __init__(self, size: int = 22, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._rotate)
        self._timer.start()

    def _rotate(self) -> None:
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.color("primary")))
        pen.setWidthF(max(2.0, self.width() / 11))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        rect = self.rect().adjusted(3, 3, -3, -3)
        painter.drawArc(rect, int(-self._angle * 16), int(250 * 16))
        painter.end()


class Table(QTableWidget):
    def __init__(self, columns: list[str], parent: QWidget | None = None) -> None:
        super().__init__(0, len(columns), parent)
        self.setHorizontalHeaderLabels(columns)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.horizontalHeader().setFixedHeight(40)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setCornerButtonEnabled(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def set_headers(self, headers: list[str], stretch_column: int | None = None) -> None:
        for index, text in enumerate(headers):
            item = self.horizontalHeaderItem(index)
            if item:
                item.setText(text)
        if stretch_column is not None:
            self.horizontalHeader().setSectionResizeMode(stretch_column, QHeaderView.ResizeMode.Stretch)

    def add_item(
        self,
        row: int,
        column: int,
        text: str,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
        data: Any = None,
        color: str | None = None,
        bold: bool = False,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setToolTip(text)
        item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        if color:
            item.setForeground(QColor(color))
        if bold:
            font = item.font()
            font.setPixelSize(max(8, round(theme.scale(13))))
            font.setBold(True)
            item.setFont(font)
        if data is not None:
            item.setData(Qt.ItemDataRole.UserRole, data)
        self.setItem(row, column, item)
        return item

class Avatar(QLabel):
    def __init__(self, text: str = "", size: int = 36, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(text)
        theme.changed.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"background: {theme.tokens['secondary']}; color: #FFFFFF; border-radius: {self._size // 2}px;"
            f"font-size: {max(10, self._size // 3)}px; font-weight: 700;"
        )


class BrandMark(QLabel):
    def __init__(self, size: int = 64, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setPixmap(logo_pixmap(size))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class Divider(QFrame):
    def __init__(self, parent: QWidget | None = None, vertical: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("VDivider" if vertical else "Divider")
        if vertical:
            self.setFixedWidth(1)
        else:
            self.setFixedHeight(1)
