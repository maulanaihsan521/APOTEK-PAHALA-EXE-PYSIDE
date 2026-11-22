"""Render logo SVG menjadi PNG untuk laporan dan ikon PWA."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets" / "logo.svg"


def render(size: int, target: Path, background: str | None = None, padding: float = 0.0) -> None:
    renderer = QSvgRenderer(str(SVG))
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if background:
        painter.fillRect(0, 0, size, size, QColor(background))
    inset = size * padding
    renderer.render(painter, QRectF(inset, inset, size - inset * 2, size - inset * 2))
    painter.end()
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(target))
    print(f"created {target} ({size}px)")


def main() -> int:
    render(512, ROOT / "assets" / "logo.png", padding=0.0)
    public = ROOT / "mobile-web" / "public"
    render(192, public / "icon-192.png", background="#0B4F45", padding=0.13)
    render(512, public / "icon-512.png", background="#0B4F45", padding=0.13)
    render(180, public / "apple-touch-icon.png", background="#0B4F45", padding=0.13)
    render(128, ROOT / "desktop" / "app" / "assets" / "logo.png", padding=0.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
