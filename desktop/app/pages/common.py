"""Pembantu umum untuk halaman desktop."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.widgets import IconBox, InlineBanner, ThemedButton
from app.core.api import ApiError
from app.core.theme import theme


def download_export(
    page,
    api,
    path: str,
    fallback: str,
    params: dict | None = None,
    file_filter: str = "Semua berkas (*.*)",
) -> str | None:
    """Unduh berkas dari API lalu minta lokasi simpan. Mengembalikan path."""
    try:
        content, suggested = api.download(path, fallback, params=params)
    except ApiError as exc:
        page.toast(exc.message, "error")
        return None
    target, _selected = QFileDialog.getSaveFileName(page, "Simpan berkas", suggested, file_filter)
    if not target:
        return None
    target_path = Path(target)
    if target_path.suffix.lower() not in {".pdf", ".xlsx", ".csv"}:
        suffix = Path(suggested).suffix
        if suffix:
            target_path = target_path.with_suffix(suffix)
    try:
        target_path.write_bytes(content)
    except OSError as exc:
        page.toast(f"Gagal menyimpan berkas: {exc}", "error")
        return None
    page.toast(f"Berkas disimpan: {target_path.name}", "success")
    return str(target_path)



def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


def icon_button(text: str, icon_name: str, variant: str = "outline") -> ThemedButton:
    return ThemedButton(text, variant, icon_name=icon_name)


def status_badge(status: str, text: str | None = None):
    from app.components.widgets import Badge

    mapping = {
        "aman": ("success", "Aman"),
        "perlu_perhatian": ("warning", "Perlu perhatian"),
        "kritis": ("danger", "Kritis"),
        "approved": ("success", "Disetujui"),
        "draft": ("warning", "Draf"),
        "cancelled": ("neutral", "Dibatalkan"),
        "success": ("success", "Berhasil"),
        "danger": ("danger", "Kritis"),
        "warning": ("warning", "Perhatian"),
        "info": ("info", "Info"),
        "rendah": ("neutral", "Rendah"),
        "sedang": ("info", "Sedang"),
        "tinggi": ("warning", "Tinggi"),
    }
    tone, label = mapping.get(status, ("neutral", text or status))
    return Badge(text or label, tone)


def activity_icon(activity_type: str) -> tuple[str, str, str]:
    mapping = {
        "sale": ("shopping-bag", "primary", "primary_soft"),
        "stock": ("boxes", "warning_text", "warning_bg"),
        "prediction": ("trending-up", "info_text", "info_bg"),
        "training": ("cpu", "purple", "purple_bg"),
        "procurement": ("clipboard-list", "success", "success_bg"),
        "login": ("user-round", "info_text", "info_bg"),
        "logout": ("log-out", "muted", "surface_alt"),
        "import": ("upload", "info_text", "info_bg"),
        "backup": ("database-backup", "success", "success_bg"),
        "medicine": ("pill", "primary", "primary_soft"),
        "settings": ("settings", "muted", "surface_alt"),
        "weather": ("cloud-rain", "info_text", "info_bg"),
        "account": ("user-round", "primary", "primary_soft"),
        "user": ("user-round", "primary", "primary_soft"),
    }
    return mapping.get(activity_type or "", ("activity", "muted", "surface_alt"))


def metric_block(label: str, value: str, hint: str = "") -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)
    title = QLabel(label)
    title.setObjectName("MutedSmall")
    layout.addWidget(title)
    number = QLabel(value)
    number.setStyleSheet("font-size: 16px; font-weight: 800;")
    layout.addWidget(number)
    if hint:
        hint_label = QLabel(hint)
        hint_label.setObjectName("MutedSmall")
        layout.addWidget(hint_label)
    return widget


class PageNotice(InlineBanner):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", "info", parent=parent)
        self.hide()

    def show_message(self, message: str, tone: str = "info") -> None:
        self.set_message(message, tone)
        self.show()

    def clear(self) -> None:
        self.hide()


def screen_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 14px; font-weight: 800;")
    return label


def link_button(text: str, callback) -> QPushButton:
    button = QPushButton(text)
    button.setProperty("variant", "ghost")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setStyleSheet(f"QPushButton {{ color: {theme.tokens['primary']}; font-size: 11px; padding: 2px 5px; }}")
    button.clicked.connect(callback)
    return button
