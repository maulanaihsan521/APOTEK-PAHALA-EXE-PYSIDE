"""Tema terang/gelap dan stylesheet aplikasi desktop."""
from __future__ import annotations

from string import Template

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from app.core.config import FONT_SCALES, ICONS_DIR


def mix(first: str, second: str, weight: float) -> str:
    """Campur dua warna hex; weight 0 = first, 1 = second."""
    first = first.lstrip("#")
    second = second.lstrip("#")
    a = [int(first[index : index + 2], 16) for index in (0, 2, 4)]
    b = [int(second[index : index + 2], 16) for index in (0, 2, 4)]
    value = [round(a[i] + (b[i] - a[i]) * weight) for i in range(3)]
    return "#" + "".join(f"{channel:02X}" for channel in value)


LIGHT = {
    "bg": "#F5F8FA",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FBFC",
    "surface_soft": "#F1F7F5",
    "text": "#18343D",
    "text_soft": "#3E5B64",
    "muted": "#718096",
    "muted_light": "#93A3AC",
    "border": "#E3EBEF",
    "border_strong": "#D3E0E5",
    "primary": "#087F6B",
    "primary_hover": "#076B5A",
    "primary_dark": "#0B5F52",
    "primary_soft": "#E7F6F0",
    "secondary": "#0B5F52",
    "accent": "#20B58A",
    "accent_soft": "#DDF4EB",
    "success": "#16A36A",
    "success_bg": "#E8F7F0",
    "warning": "#F2A93B",
    "warning_text": "#A97412",
    "warning_bg": "#FEF4E2",
    "danger": "#E55353",
    "danger_text": "#C14343",
    "danger_bg": "#FDECEC",
    "info": "#3985D6",
    "info_text": "#2F73B9",
    "info_bg": "#EAF3FC",
    "purple": "#8B5CF6",
    "purple_bg": "#F1ECFE",
    "sidebar_top": "#0B5F52",
    "sidebar_bottom": "#073B33",
    "sidebar_text": "#DCEDE8",
    "sidebar_muted": "#8FBBB0",
    "sidebar_active": "#108C76",
    "sidebar_hover": "#145E52",
    "input_bg": "#F8FBFC",
    "table_header": "#F5F8FA",
    "hover": "#F0F7F5",
    "selected": "#E6F5F0",
    "segment_bg": "#EDF2F4",
    "track": "#EDF2F5",
    "scroll": "#C9D6D3",
    "tooltip_bg": "#18343D",
    "tooltip_text": "#FFFFFF",
    "shadow": "#102E28",
    "overlay": "#08231E",
    "white": "#FFFFFF",
    "chevron": "#718096",
}

DARK = {
    "bg": "#0E1A18",
    "surface": "#152622",
    "surface_alt": "#1A2D28",
    "surface_soft": "#17302B",
    "text": "#E9F3F0",
    "text_soft": "#C4D8D3",
    "muted": "#9AAFA9",
    "muted_light": "#7E948E",
    "border": "#263D37",
    "border_strong": "#314C45",
    "primary": "#1FA98D",
    "primary_hover": "#25BA9C",
    "primary_dark": "#0B5F52",
    "primary_soft": "#153B33",
    "secondary": "#7FD3BC",
    "accent": "#2FC79C",
    "accent_soft": "#153B33",
    "success": "#38C78A",
    "success_bg": "#14382C",
    "warning": "#F4B454",
    "warning_text": "#F4C579",
    "warning_bg": "#382F1C",
    "danger": "#F17878",
    "danger_text": "#F49A9A",
    "danger_bg": "#3A2222",
    "info": "#64A8E8",
    "info_text": "#8CC2F2",
    "info_bg": "#1C2F42",
    "purple": "#A98BF9",
    "purple_bg": "#2A2340",
    "sidebar_top": "#0A2B25",
    "sidebar_bottom": "#071F1B",
    "sidebar_text": "#D7E9E4",
    "sidebar_muted": "#88A9A1",
    "sidebar_active": "#117F6B",
    "sidebar_hover": "#123E36",
    "input_bg": "#1A2D28",
    "table_header": "#1A2D28",
    "hover": "#1C332D",
    "selected": "#1D3F37",
    "segment_bg": "#20362F",
    "track": "#2A403A",
    "scroll": "#3B544D",
    "tooltip_bg": "#E9F3F0",
    "tooltip_text": "#10211C",
    "shadow": "#000000",
    "overlay": "#020A08",
    "white": "#FFFFFF",
    "chevron": "#9AAFA9",
}

QSS = Template(
    """
* {
    outline: 0;
}
QWidget {
    color: $text;
    font-family: "Segoe UI", "Inter", "Arial";
    font-size: ${fs}px;
}
QMainWindow, QWidget#AppRoot, QWidget#PageRoot, QScrollArea#PageScroll {
    background-color: $bg;
}
QDialog {
    background-color: $surface;
}
QFrame#Card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 14px;
}
QFrame#CardTight {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
QFrame#SoftCard {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 12px;
}
QFrame#TintCard {
    background-color: $surface_soft;
    border: 1px solid $border;
    border-radius: 14px;
}
QFrame#Divider {
    background-color: $border;
    border: none;
    max-height: 1px;
    min-height: 1px;
}
QFrame#VDivider {
    background-color: $border;
    border: none;
    max-width: 1px;
    min-width: 1px;
}
QLabel {
    background: transparent;
    border: none;
}
QLabel#PageTitle {
    font-size: ${fs_page}px;
    font-weight: 700;
    color: $text;
}
QLabel#PageSubtitle {
    font-size: ${fs_sm}px;
    color: $muted;
}
QLabel#SectionTitle {
    font-size: ${fs_lg}px;
    font-weight: 700;
    color: $text;
}
QLabel#SectionSubtitle {
    font-size: ${fs_xs}px;
    color: $muted;
}
QLabel#Muted {
    color: $muted;
}
QLabel#MutedSmall {
    color: $muted_light;
    font-size: ${fs_xs}px;
}
QLabel#TablePrimary {
    color: $text;
    font-size: ${fs_cell}px;
    font-weight: 600;
}
QLabel#TableMeta {
    color: $muted_light;
    font-size: ${fs_meta}px;
}
QLabel#KpiLabel {
    color: $muted;
    font-size: ${fs_sm}px;
    font-weight: 600;
}
QLabel#KpiValue {
    color: $text;
    font-size: ${fs_kpi}px;
    font-weight: 700;
}
QLabel#KpiHint {
    color: $muted_light;
    font-size: ${fs_xs}px;
}
QLabel#FieldLabel {
    color: $text;
    font-size: ${fs_sm}px;
    font-weight: 600;
}
QLabel#Hint {
    color: $muted;
    font-size: ${fs_xs}px;
}
QLabel#ErrorText {
    color: $danger_text;
    font-size: ${fs_sm}px;
}
QLabel#BrandName {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 800;
}
QLabel#BrandSub {
    color: $sidebar_muted;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
}
QLabel#HeroTitle {
    color: #FFFFFF;
    font-size: 38px;
    font-weight: 800;
}
QLabel#HeroText {
    color: rgba(255, 255, 255, 78%);
    font-size: 15px;
}
QLabel#LoginTitle {
    color: $text;
    font-size: 26px;
    font-weight: 800;
}
QLabel#LoginSubtitle {
    color: $muted;
    font-size: 14px;
}
QFrame#LoginDivider {
    background-color: $border;
    border: none;
    max-height: 1px;
    min-height: 1px;
}
QLabel#LoginMeta {
    color: $muted_light;
    font-size: 11px;
}
QLabel#LoginFooter {
    color: $muted_light;
    font-size: 11px;
}
QPushButton#LoginLink {
    background: transparent;
    border: none;
    color: $primary;
    font-size: 11px;
    padding: 2px 4px;
}
QPushButton#LoginLink:hover {
    background: $primary_soft;
    border-radius: 6px;
}
QPushButton {
    background-color: transparent;
    border: none;
    color: $text;
    padding: 8px 14px;
    border-radius: 9px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: $hover;
}
QPushButton:pressed {
    background-color: $selected;
}
QPushButton:disabled {
    color: $muted_light;
}
QPushButton[variant="primary"] {
    background-color: $primary;
    color: #FFFFFF;
    padding: 9px 16px;
}
QPushButton[variant="primary"]:hover {
    background-color: $primary_hover;
}
QPushButton[variant="primary"]:disabled {
    background-color: $border_strong;
    color: $muted;
}
QPushButton[variant="secondary"] {
    background-color: $primary_soft;
    color: $primary;
    padding: 9px 16px;
}
QPushButton[variant="secondary"]:hover {
    background-color: $accent_soft;
}
QPushButton[variant="outline"] {
    background-color: $surface;
    border: 1px solid $border;
    color: $text;
    padding: 8px 14px;
}
QPushButton[variant="outline"]:hover {
    border-color: $primary;
    color: $primary;
    background-color: $hover;
}
QPushButton[variant="ghost"] {
    background-color: transparent;
    color: $muted;
}
QPushButton[variant="ghost"]:hover {
    background-color: $hover;
    color: $primary;
}
QPushButton[variant="danger"] {
    background-color: $danger;
    color: #FFFFFF;
    padding: 9px 16px;
}
QPushButton[variant="danger"]:hover {
    background-color: #C94444;
}
QPushButton[variant="danger-soft"] {
    background-color: $danger_bg;
    color: $danger_text;
    padding: 8px 14px;
}
QPushButton[variant="danger-soft"]:hover {
    background-color: $danger_bg;
    border: 1px solid $danger;
}
QPushButton[flat="true"] {
    padding: 5px 8px;
    font-size: ${fs_xs}px;
}
QPushButton[segment="true"] {
    background-color: transparent;
    color: $muted;
    padding: 6px 13px;
    border-radius: 7px;
    font-size: ${fs_sm}px;
    font-weight: 600;
}
QPushButton[segment="true"]:hover {
    color: $primary;
    background: transparent;
}
QPushButton[segment="true"]:checked {
    background-color: $surface;
    color: $primary;
}
QFrame#Segment {
    background-color: $segment_bg;
    border-radius: 9px;
}
QPushButton[pill="true"] {
    background-color: $surface;
    border: 1px solid $border;
    color: $muted;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: ${fs_sm}px;
    font-weight: 600;
}
QPushButton[pill="true"]:hover {
    border-color: $primary;
    color: $primary;
}
QPushButton[pill="true"]:checked {
    background-color: $primary;
    border-color: $primary;
    color: #FFFFFF;
}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: $input_bg;
    border: 1px solid $border;
    border-radius: 9px;
    padding: 6px 10px;
    min-height: 22px;
    color: $text;
    selection-background-color: $primary;
    selection-color: #FFFFFF;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTextEdit:hover {
    border-color: $border_strong;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {
    border-color: $primary;
    background-color: $surface;
}
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {
    color: $muted_light;
    background-color: $surface_alt;
}
QLineEdit[error="true"], QComboBox[error="true"] {
    border-color: $danger;
    background-color: $danger_bg;
}
QComboBox {
    padding-right: 26px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}
QComboBox::down-arrow {
    image: url("$icons/chevron-down-$mode.svg");
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: $primary_soft;
    selection-color: $text;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 8px;
    border-radius: 6px;
}
QDateEdit::drop-down {
    border: none;
    width: 24px;
}
QDateEdit::down-arrow {
    image: url("$icons/chevron-down-$mode.svg");
    width: 12px;
    height: 12px;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}
QTextEdit, QPlainTextEdit {
    padding: 8px 10px;
}
QCheckBox {
    spacing: 8px;
    color: $text;
    font-size: ${fs_sm}px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 1px solid $border_strong;
    background: $surface;
}
QCheckBox::indicator:hover {
    border-color: $primary;
}
QCheckBox::indicator:checked {
    background: $primary;
    border-color: $primary;
    image: url("$icons/check-white.svg");
}
QTableWidget, QTableView {
    background-color: transparent;
    alternate-background-color: $surface_alt;
    border: none;
    gridline-color: transparent;
    selection-background-color: $selected;
    selection-color: $text;
    font-size: ${fs_cell}px;
}
QTableWidget::item, QTableView::item {
    padding-left: 8px;
    padding-right: 8px;
    border-bottom: 1px solid $border;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: $selected;
    color: $text;
}
QHeaderView {
    background-color: transparent;
}
QHeaderView::section {
    background-color: $table_header;
    color: $muted;
    border: none;
    border-bottom: 1px solid $border;
    padding-left: 6px;
    padding-right: 6px;
    padding-top: 8px;
    padding-bottom: 8px;
    font-size: ${fs_xs}px;
    font-weight: 700;
}
QHeaderView::section:first {
    border-top-left-radius: 8px;
}
QHeaderView::section:last {
    border-top-right-radius: 8px;
}
QTableCornerButton::section {
    background-color: $table_header;
    border: none;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: $scroll;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: $muted;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: $scroll;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background: $muted;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QToolTip {
    background-color: $tooltip_bg;
    color: $tooltip_text;
    border: none;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}
QMenu {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 9px;
    padding: 5px;
}
QMenu::item {
    padding: 7px 26px 7px 12px;
    border-radius: 6px;
    color: $text;
    font-size: ${fs_sm}px;
}
QMenu::item:selected {
    background-color: $primary_soft;
    color: $primary;
}
QMenu::separator {
    height: 1px;
    background: $border;
    margin: 5px 8px;
}
QMenu::icon {
    left: 8px;
}
QProgressBar {
    background-color: $track;
    border: none;
    border-radius: 4px;
    max-height: 8px;
    min-height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: $primary;
    border-radius: 4px;
}
QFrame#Sidebar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 $sidebar_top, stop:1 $sidebar_bottom);
    border: none;
}
QFrame#Sidebar QPushButton[nav="true"] {
    background-color: transparent;
    color: $sidebar_text;
    text-align: left;
    padding: 7px 8px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
}
QFrame#Sidebar QPushButton[nav="true"]:hover {
    background-color: $sidebar_hover;
    color: #FFFFFF;
}
QFrame#Sidebar QPushButton[nav="true"]:checked {
    background-color: $sidebar_active;
    color: #FFFFFF;
}
QFrame#Sidebar QPushButton[theme="true"] {
    background-color: rgba(255, 255, 255, 6%);
    color: $sidebar_text;
    padding: 7px 8px;
    border-radius: 9px;
    font-size: ${fs_xs}px;
    font-weight: 600;
}
QFrame#Sidebar QPushButton[theme="true"]:hover {
    background-color: rgba(255, 255, 255, 12%);
}
QFrame#Sidebar QPushButton[theme="true"]:checked {
    background-color: rgba(255, 255, 255, 18%);
    color: #FFFFFF;
}
QLabel#SidebarVersion {
    color: $sidebar_muted;
    font-size: 10px;
}
QLabel#SidebarCopyright {
    color: $sidebar_muted;
    font-size: 9px;
}
QFrame#TopBar {
    background-color: $bg;
    border: none;
}
QFrame#LoginRight {
    background-color: $bg;
}
QFrame#LoginLeft {
    background-color: $primary_dark;
}
QFrame#LoginCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 16px;
}
QLabel#Chip {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 11px;
    padding: 4px 9px;
    color: $muted;
    font-size: ${fs_xs}px;
    font-weight: 600;
}
QTabWidget::pane {
    border: 1px solid $border;
    border-radius: 10px;
    background: $surface;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: $muted;
    padding: 8px 16px;
    border: none;
    font-weight: 600;
    font-size: ${fs_sm}px;
}
QTabBar::tab:selected {
    color: $primary;
    border-bottom: 2px solid $primary;
}
QListWidget {
    background: transparent;
    border: none;
    outline: 0;
}
QListWidget::item {
    border-radius: 8px;
    padding: 6px;
}
QListWidget::item:selected {
    background: $selected;
    color: $text;
}
QFileDialog QWidget {
    background-color: $surface;
}
"""
)


def _ensure_theme_assets() -> None:
    """Buat ikon kecil yang diwarnai untuk stylesheet (chevron & check)."""
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for name, color in (("chevron-down-light.svg", "#718096"), ("chevron-down-dark.svg", "#9AAFA9")):
        target = ICONS_DIR / name
        if not target.exists():
            base = ICONS_DIR / "chevron-down.svg"
            if base.exists():
                target.write_text(
                    base.read_text(encoding="utf-8").replace("currentColor", color), encoding="utf-8"
                )
    check_target = ICONS_DIR / "check-white.svg"
    if not check_target.exists():
        base = ICONS_DIR / "check.svg"
        if base.exists():
            check_target.write_text(
                base.read_text(encoding="utf-8").replace("currentColor", "#FFFFFF"), encoding="utf-8"
            )


def build_palette(tokens: dict[str, str]) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(tokens["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(tokens["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens["surface_alt"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(tokens["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(tokens["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens["primary"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tokens["tooltip_bg"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tokens["tooltip_text"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(tokens["muted_light"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(tokens["primary"]))
    return palette


def build_qss(tokens: dict[str, str], font_scale: str = "normal") -> str:
    factor = FONT_SCALES.get(font_scale, 1.0)
    sizes = {
        "fs": round(15 * factor),
        "fs_xs": round(13 * factor),
        "fs_sm": round(14 * factor),
        "fs_lg": round(17 * factor),
        "fs_kpi": round(30 * factor),
        "fs_page": round(28 * factor),
        "fs_cell": round(13 * factor),
        "fs_meta": round(12 * factor),
    }
    payload = {**tokens, **{key: str(value) for key, value in sizes.items()}}
    payload["icons"] = ICONS_DIR.as_posix()
    payload["mode"] = "dark" if tokens is DARK else "light"
    return QSS.safe_substitute(payload)


class ThemeManager(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.mode = "light"
        self.font_scale = "normal"
        self.tokens = LIGHT
        self._app: QApplication | None = None

    @property
    def is_dark(self) -> bool:
        return self.tokens is DARK

    def effective_mode(self) -> str:
        if self.mode != "auto":
            return self.mode
        app = self._app or QApplication.instance()
        if app is not None:
            hint = app.styleHints().colorScheme()
            if hint == Qt.ColorScheme.Dark:
                return "dark"
        return "light"

    def apply(self, app: QApplication, mode: str | None = None, font_scale: str | None = None) -> None:
        self._app = app
        if mode is not None:
            self.mode = mode
        if font_scale is not None:
            self.font_scale = font_scale
        _ensure_theme_assets()
        self.tokens = DARK if self.effective_mode() == "dark" else LIGHT
        app.setPalette(build_palette(self.tokens))
        font = QFont("Segoe UI", max(8, round(11 * FONT_SCALES.get(self.font_scale, 1.0))))
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app.setFont(font)
        app.setStyleSheet(build_qss(self.tokens, self.font_scale))
        self.changed.emit()

    def set_mode(self, mode: str) -> None:
        if mode not in {"light", "dark", "auto"}:
            return
        self.mode = mode
        if self._app:
            self.apply(self._app)

    def set_font_scale(self, scale: str) -> None:
        self.font_scale = scale if scale in FONT_SCALES else "normal"
        if self._app:
            self.apply(self._app)

    def color(self, role: str) -> str:
        mapping = {
            "text": "text",
            "muted": "muted",
            "muted_light": "muted_light",
            "primary": "primary",
            "secondary": "secondary",
            "accent": "accent",
            "success": "success",
            "warning": "warning",
            "danger": "danger",
            "info": "info",
            "purple": "purple",
            "white": "white",
            "sidebar": "sidebar_text",
            "sidebar_muted": "sidebar_muted",
        }
        return self.tokens.get(mapping.get(role, role), self.tokens["text"])

    def scale(self, value: float) -> float:
        return value * FONT_SCALES.get(self.font_scale, 1.0)


theme = ThemeManager()
