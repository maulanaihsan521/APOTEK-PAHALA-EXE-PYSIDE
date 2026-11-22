"""Pemuatan ikon SVG Lucide dengan pewarnaan sesuai tema."""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.core.config import ICONS_DIR


@lru_cache(maxsize=512)
def _svg_source(name: str) -> str:
    path = ICONS_DIR / f"{name}.svg"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _device_ratio() -> float:
    app = QGuiApplication.instance()
    screen = app.primaryScreen() if app else None
    return max(1.0, screen.devicePixelRatio() if screen else 1.0)


# Render 2x lalu turunkan dengan smooth scaling. Pada DPI 125% (Windows 7),
# ikon 16 px tetap tajam tanpa garis yang tampak pecah.
_SUPERSAMPLE = 2


@lru_cache(maxsize=2048)
def pixmap(name: str, color: str = "#18343D", size: int = 18, stroke: float = 2.0) -> QPixmap:
    """Render ikon SVG menjadi QPixmap dengan warna tertentu."""
    ratio = _device_ratio() * _SUPERSAMPLE
    target = QSize(max(1, round(size * ratio)), max(1, round(size * ratio)))
    canvas = QPixmap(target)
    canvas.fill(Qt.GlobalColor.transparent)
    source = _svg_source(name)
    if not source:
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(color))
        pen.setWidthF(max(1.0, stroke * ratio))
        painter.setPen(pen)
        painter.drawEllipse(2 * ratio, 2 * ratio, (size - 4) * ratio, (size - 4) * ratio)
        painter.end()
        canvas.setDevicePixelRatio(ratio)
        return canvas
    source = source.replace("currentColor", color)
    if stroke != 2.0:
        source = source.replace('stroke-width="2"', f'stroke-width="{stroke}"')
    renderer = QSvgRenderer(QByteArray(source.encode("utf-8")))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    canvas.setDevicePixelRatio(ratio)
    return canvas


def icon(name: str, color: str = "#18343D", size: int = 18, stroke: float = 2.0) -> QIcon:
    return QIcon(pixmap(name, color, size, stroke))


def stateful_icon(
    name: str,
    off_color: str,
    on_color: str,
    size: int = 18,
    stroke: float = 2.0,
) -> QIcon:
    """Ikon yang berubah warna ketika tombol checkable aktif (State.On)."""
    result = QIcon()
    result.addPixmap(pixmap(name, off_color, size, stroke), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(pixmap(name, on_color, size, stroke), QIcon.Mode.Normal, QIcon.State.On)
    result.addPixmap(pixmap(name, on_color, size, stroke), QIcon.Mode.Active, QIcon.State.On)
    result.addPixmap(pixmap(name, off_color, size, stroke), QIcon.Mode.Disabled, QIcon.State.Off)
    return result


def logo_pixmap(size: int = 64) -> QPixmap:
    from app.core.config import LOGO_PATH

    ratio = _device_ratio()
    canvas = QPixmap(round(size * ratio), round(size * ratio))
    canvas.fill(Qt.GlobalColor.transparent)
    source = QPixmap(str(LOGO_PATH))
    if source.isNull():
        return canvas
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawPixmap(0, 0, round(size * ratio), round(size * ratio), source)
    painter.end()
    canvas.setDevicePixelRatio(ratio)
    return canvas
