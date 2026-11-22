"""Grafik kustom berbasis QPainter untuk aplikasi desktop Apotek Pahala."""
from __future__ import annotations

from math import ceil
from typing import Iterable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from app.core.theme import theme
from app.core.utils import number


def _font(size: float, weight: int = 400) -> QFont:
    font = QFont("Segoe UI")
    font.setPixelSize(max(8, round(size + 1.0)))
    font.setWeight(QFont.Weight(weight))
    return font


def _nice_max(value: float) -> float:
    if value <= 0:
        return 10.0
    magnitude = 10 ** (len(str(int(value))) - 1)
    for factor in (1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):
        candidate = factor * magnitude
        if candidate >= value:
            return candidate
    return 10 * magnitude


def _wrap_label(metrics: QFontMetrics, text: str, width: float, max_lines: int = 2) -> list[str]:
    """Bagi label grafik menjadi beberapa baris agar nama panjang tetap terbaca."""
    words = str(text).split()
    if not words:
        return [""]
    # Batas karakter membuat label pendek tetap aman pada layar dengan skala
    # berbeda, karena lebar hasil ukur font dapat berbeda saat digambar.
    available = max(24.0, width)
    max_chars = 16
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        fits = (
            metrics.horizontalAdvance(candidate) <= available
            and len(candidate) <= max_chars
        )
        if not current or fits:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        overflow = " ".join(lines[max_lines - 1:])
        lines = lines[: max_lines - 1] + [overflow]
    return [
        metrics.elidedText(line, Qt.TextElideMode.ElideRight, int(available))
        for line in lines
    ]


class ChartBase(QWidget):
    def __init__(self, parent: QWidget | None = None, height: int = 260) -> None:
        super().__init__(parent)
        self.setMinimumHeight(height)
        self.setMouseTracking(True)
        self._hover = -1
        theme.changed.connect(self.update)

    def leaveEvent(self, _event) -> None:
        self._hover = -1
        self.update()

    def _tokens(self) -> dict:
        return theme.tokens

    def _draw_empty(self, painter: QPainter, text: str = "Belum ada data untuk ditampilkan") -> None:
        painter.setPen(QColor(self._tokens()["muted"]))
        painter.setFont(_font(11))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    def _tooltip(self, painter: QPainter, anchor: QPointF, lines: Sequence[str], accent: str) -> None:
        tokens = self._tokens()
        painter.setFont(_font(10))
        metrics = QFontMetrics(painter.font())
        width = max(metrics.horizontalAdvance(line) for line in lines) + 22 if lines else 10
        height = len(lines) * (metrics.height() + 2) + 14
        x = anchor.x() + 12
        if x + width > self.width() - 6:
            x = anchor.x() - width - 12
        y = max(8.0, anchor.y() - height - 10)
        rect = QRectF(x, y, width, height)
        painter.setPen(QPen(QColor(tokens["border"]), 1))
        painter.setBrush(QColor(tokens["surface"]))
        painter.drawRoundedRect(rect, 7, 7)
        painter.setPen(QColor(accent))
        painter.setBrush(QColor(accent))
        painter.drawRoundedRect(QRectF(x, y + 8, 3, height - 16), 1.5, 1.5)
        painter.setPen(QColor(tokens["text"]))
        for index, line in enumerate(lines):
            baseline = y + 9 + metrics.height() + index * (metrics.height() + 2)
            painter.drawText(QPointF(x + 11, baseline), line)


class Sparkline(QWidget):
    def __init__(
        self,
        values: Sequence[float] | None = None,
        color: str | None = None,
        parent: QWidget | None = None,
        height: int = 30,
        line_width: float = 1.7,
    ) -> None:
        super().__init__(parent)
        self._values = list(values or [])
        self._color = color
        self._width = line_width
        self.setFixedHeight(height)
        self.setMinimumWidth(72)
        theme.changed.connect(self.update)

    def set_values(self, values: Sequence[float]) -> None:
        self._values = list(values)
        self.update()

    def paintEvent(self, _event) -> None:
        if len(self._values) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = self._tokens()
        color = QColor(self._color or tokens["primary"])
        values = [float(value) for value in self._values]
        low, high = min(values), max(values)
        span = high - low or 1.0
        rect = self.rect().adjusted(2, 3, -3, -3)
        points = [
            QPointF(
                rect.left() + index / (len(values) - 1) * rect.width(),
                rect.bottom() - (value - low) / span * rect.height(),
            )
            for index, value in enumerate(values)
        ]
        area = QPainterPath(QPointF(points[0].x(), rect.bottom()))
        area.lineTo(points[0])
        for point in points[1:]:
            area.lineTo(point)
        area.lineTo(points[-1].x(), rect.bottom())
        area.closeSubpath()
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        top = QColor(color)
        top.setAlpha(46)
        gradient.setColorAt(0, top)
        bottom = QColor(color)
        bottom.setAlpha(0)
        gradient.setColorAt(1, bottom)
        painter.fillPath(area, gradient)
        pen = QPen(color, self._width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(points[-1], 2.2, 2.2)
        painter.end()

    def _tokens(self) -> dict:
        return theme.tokens


class TrendChart(ChartBase):
    """Grafik garis aktual + prediksi dengan area lembut dan tooltip."""

    def __init__(
        self,
        labels: Sequence[str] | None = None,
        actual: Sequence[float] | None = None,
        predicted: Sequence[float | None] | None = None,
        parent: QWidget | None = None,
        height: int = 275,
        actual_label: str = "Aktual",
        predicted_label: str = "Prediksi",
        suffix: str = "",
        show_legend: bool = True,
    ) -> None:
        super().__init__(parent, height)
        self.labels = list(labels or [])
        self.actual = [float(value) for value in (actual or [])]
        self.predicted = [None if value is None else float(value) for value in (predicted or [])]
        self.actual_label = actual_label
        self.predicted_label = predicted_label
        self.suffix = suffix
        self.show_legend = show_legend

    def set_data(
        self,
        labels: Sequence[str],
        actual: Sequence[float],
        predicted: Sequence[float | None] | None = None,
    ) -> None:
        self.labels = list(labels)
        self.actual = [float(value) for value in actual]
        self.predicted = [None if value is None else float(value) for value in (predicted or [])]
        self._hover = -1
        self.update()

    def _values(self) -> list[float]:
        values = list(self.actual)
        values.extend(value for value in self.predicted if value is not None)
        return values

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = self._tokens()
        if not self.labels or not self.actual:
            self._draw_empty(painter)
            painter.end()
            return
        values = self._values()
        maximum = _nice_max(max(values) * 1.12 if values else 10)
        left, top, right, bottom = 46, 14, 16, 58 if self.show_legend else 24
        plot = QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        grid_pen = QPen(QColor(tokens["border"]), 1)
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setFont(_font(9))
        for step in range(5):
            ratio = step / 4
            y = plot.bottom() - ratio * plot.height()
            value = maximum * ratio
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(tokens["muted_light"]))
            painter.drawText(
                QRectF(0, y - 8, left - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                number(value),
            )
        count = len(self.labels)
        if count == 1:
            xs = [plot.center().x()]
        else:
            xs = [plot.left() + index / (count - 1) * plot.width() for index in range(count)]

        def to_point(index: int, value: float) -> QPointF:
            return QPointF(xs[index], plot.bottom() - (value / maximum) * plot.height())

        if count == 1:
            actual_points = [to_point(0, self.actual[0])]
        else:
            actual_points = [to_point(index, value) for index, value in enumerate(self.actual)]
        if len(actual_points) >= 2:
            area = QPainterPath(QPointF(actual_points[0].x(), plot.bottom()))
            area.lineTo(actual_points[0])
            for point in actual_points[1:]:
                area.lineTo(point)
            area.lineTo(actual_points[-1].x(), plot.bottom())
            area.closeSubpath()
            gradient = QLinearGradient(0, plot.top(), 0, plot.bottom())
            top_color = QColor(tokens["primary"])
            top_color.setAlpha(46)
            gradient.setColorAt(0, top_color)
            bottom_color = QColor(tokens["primary"])
            bottom_color.setAlpha(2)
            gradient.setColorAt(1, bottom_color)
            painter.fillPath(area, gradient)

        painter.setPen(QPen(QColor(tokens["primary"]), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        path = QPainterPath(actual_points[0])
        for point in actual_points[1:]:
            path.lineTo(point)
        painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(tokens["primary"]))
        for point in actual_points:
            painter.drawEllipse(point, 3.0, 3.0)
        painter.setBrush(QColor(tokens["surface"]))
        painter.setPen(QPen(QColor(tokens["primary"]), 2.0))
        for point in actual_points:
            painter.drawEllipse(point, 3.0, 3.0)

        predicted_points: list[tuple[int, QPointF]] = []
        for index, value in enumerate(self.predicted):
            if value is None or index >= count:
                continue
            predicted_points.append((index, to_point(index, value)))
        if predicted_points:
            pen = QPen(QColor(tokens["accent"]), 2.1, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
            pen.setDashPattern([4, 3])
            painter.setPen(pen)
            path = QPainterPath(predicted_points[0][1])
            for _index, point in predicted_points[1:]:
                path.lineTo(point)
            painter.drawPath(path)
            painter.setBrush(QColor(tokens["surface"]))
            painter.setPen(QPen(QColor(tokens["accent"]), 2.0))
            for _index, point in predicted_points:
                painter.drawEllipse(point, 3.2, 3.2)

        painter.setPen(QColor(tokens["muted"]))
        painter.setFont(_font(9))
        metrics = painter.fontMetrics()
        max_ticks = max(3, int(plot.width() // 96))
        if count <= max_ticks:
            tick_indices = list(range(count))
        else:
            stride = (count - 1) / (max_ticks - 1)
            tick_indices = sorted({int(round(i * stride)) for i in range(max_ticks)})
            tick_indices[0] = 0
            tick_indices[-1] = count - 1
        kept: list[int] = []
        for index in tick_indices:
            if kept:
                previous = kept[-1]
                gap = (metrics.horizontalAdvance(str(self.labels[previous])) + 18) / 2
                gap += (metrics.horizontalAdvance(str(self.labels[index])) + 18) / 2
                if xs[index] - xs[previous] < gap:
                    if index == count - 1 and len(kept) > 1:
                        kept[-1] = index
                    continue
            kept.append(index)
        for index in kept:
            label = self.labels[index]
            width = 82
            x = min(max(xs[index] - width / 2, 0), self.width() - width)
            painter.drawText(
                QRectF(x, plot.bottom() + 8, width, 16),
                Qt.AlignmentFlag.AlignHCenter,
                str(label),
            )

        if self.show_legend:
            legend_y = self.height() - 14
            center = self.width() / 2
            items = [(self.actual_label, tokens["primary"])]
            if any(value is not None for value in self.predicted):
                items.append((self.predicted_label, tokens["accent"]))
            widths = []
            painter.setFont(_font(9, 600))
            metrics = QFontMetrics(painter.font())
            for label, _color in items:
                widths.append(26 + metrics.horizontalAdvance(label) + 18)
            x = center - sum(widths) / 2
            for (label, color), width in zip(items, widths):
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(color))
                painter.drawEllipse(QPointF(x + 5, legend_y - 2), 3.6, 3.6)
                painter.setPen(QColor(tokens["muted"]))
                painter.drawText(QPointF(x + 14, legend_y + 2), label)
                x += width

        if 0 <= self._hover < count:
            x = xs[self._hover]
            painter.setPen(QPen(QColor(tokens["border_strong"]), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            lines = [str(self.labels[self._hover])]
            if self._hover < len(self.actual):
                lines.append(f"{self.actual_label}: {number(self.actual[self._hover])}{self.suffix}")
            if self._hover < len(self.predicted) and self.predicted[self._hover] is not None:
                lines.append(f"{self.predicted_label}: {number(self.predicted[self._hover])}{self.suffix}")
            anchor = QPointF(x, to_point(self._hover, self.actual[self._hover]).y())
            self._tooltip(painter, anchor, lines, tokens["primary"])
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not self.labels:
            return
        left, right = 46, 16
        width = max(1, self.width() - left - right)
        ratio = min(1.0, max(0.0, (event.position().x() - left) / width))
        index = round(ratio * (len(self.labels) - 1)) if len(self.labels) > 1 else 0
        if index != self._hover:
            self._hover = index
            self.update()


class ForecastChart(ChartBase):
    """Riwayat aktual + prakiraan dengan pita interval kepercayaan."""

    def __init__(self, parent: QWidget | None = None, height: int = 300) -> None:
        super().__init__(parent, height)
        self.labels: list[str] = []
        self.history: list[float] = []
        self.forecast: list[float] = []
        self.lower: list[float] = []
        self.upper: list[float] = []

    def set_data(
        self,
        labels: Sequence[str],
        history: Sequence[float],
        forecast: Sequence[float],
        lower: Sequence[float] | None = None,
        upper: Sequence[float] | None = None,
    ) -> None:
        self.labels = list(labels)
        self.history = [float(value) for value in history]
        self.forecast = [float(value) for value in forecast]
        self.lower = [float(value) for value in (lower or [])]
        self.upper = [float(value) for value in (upper or [])]
        self._hover = -1
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = self._tokens()
        if not self.labels:
            self._draw_empty(painter)
            painter.end()
            return
        all_values = list(self.history) + list(self.forecast) + list(self.upper) + list(self.lower)
        maximum = _nice_max(max(all_values) * 1.12 if all_values else 10)
        left, top, right, bottom = 46, 14, 16, 40
        plot = QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        grid_pen = QPen(QColor(tokens["border"]), 1)
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setFont(_font(9))
        for step in range(5):
            ratio = step / 4
            y = plot.bottom() - ratio * plot.height()
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(tokens["muted_light"]))
            painter.drawText(QRectF(0, y - 8, left - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number(maximum * ratio))
        total = len(self.labels)
        xs = [plot.left() + (index / (total - 1) * plot.width() if total > 1 else plot.width() / 2) for index in range(total)]
        split = len(self.history)

        def ypos(value: float) -> float:
            return plot.bottom() - min(1.0, max(0.0, value / maximum)) * plot.height()

        if split and split < total and len(self.upper) == len(self.forecast) and len(self.lower) == len(self.forecast):
            band_points_top = [QPointF(xs[split - 1], ypos(self.history[-1]))]
            band_points_bottom = [QPointF(xs[split - 1], ypos(self.history[-1]))]
            for index, value in enumerate(self.upper):
                band_points_top.append(QPointF(xs[split + index], ypos(value)))
            for index, value in enumerate(self.lower):
                band_points_bottom.append(QPointF(xs[split + index], ypos(value)))
            band = QPainterPath(band_points_top[0])
            for point in band_points_top[1:]:
                band.lineTo(point)
            for point in reversed(band_points_bottom):
                band.lineTo(point)
            band.closeSubpath()
            color = QColor(tokens["accent"])
            color.setAlpha(28)
            painter.fillPath(band, color)

        history_points = [QPointF(xs[index], ypos(value)) for index, value in enumerate(self.history)]
        if history_points:
            area = QPainterPath(QPointF(history_points[0].x(), plot.bottom()))
            area.lineTo(history_points[0])
            for point in history_points[1:]:
                area.lineTo(point)
            area.lineTo(history_points[-1].x(), plot.bottom())
            area.closeSubpath()
            gradient = QLinearGradient(0, plot.top(), 0, plot.bottom())
            first = QColor(tokens["primary"])
            first.setAlpha(48)
            second = QColor(tokens["primary"])
            second.setAlpha(2)
            gradient.setColorAt(0, first)
            gradient.setColorAt(1, second)
            painter.fillPath(area, gradient)
            painter.setPen(QPen(QColor(tokens["primary"]), 2.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            path = QPainterPath(history_points[0])
            for point in history_points[1:]:
                path.lineTo(point)
            painter.drawPath(path)

        if self.forecast:
            forecast_points = [QPointF(xs[split + index], ypos(value)) for index, value in enumerate(self.forecast)]
            if history_points:
                forecast_points.insert(0, history_points[-1])
            pen = QPen(QColor(tokens["accent"]), 2.2, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
            pen.setDashPattern([5, 3])
            painter.setPen(pen)
            path = QPainterPath(forecast_points[0])
            for point in forecast_points[1:]:
                path.lineTo(point)
            painter.drawPath(path)
            painter.setPen(QPen(QColor(tokens["accent"]), 2.0))
            painter.setBrush(QColor(tokens["surface"]))
            for point in forecast_points[1:]:
                painter.drawEllipse(point, 3.4, 3.4)

        painter.setFont(_font(9))
        metrics = painter.fontMetrics()
        max_ticks = max(3, int(plot.width() // 96))
        if total <= max_ticks:
            tick_indices = list(range(total))
        else:
            stride = (total - 1) / (max_ticks - 1)
            tick_indices = sorted({int(round(i * stride)) for i in range(max_ticks)})
            tick_indices[0] = 0
            tick_indices[-1] = total - 1
        kept: list[int] = []
        for index in tick_indices:
            if kept:
                previous = kept[-1]
                gap = (metrics.horizontalAdvance(str(self.labels[previous])) + 18) / 2
                gap += (metrics.horizontalAdvance(str(self.labels[index])) + 18) / 2
                if xs[index] - xs[previous] < gap:
                    if index == total - 1 and len(kept) > 1:
                        kept[-1] = index
                    continue
            kept.append(index)
        for index in kept:
            label = self.labels[index]
            width = 76
            x = min(max(xs[index] - width / 2, 0), self.width() - width)
            painter.setPen(QColor(tokens["muted"]))
            painter.drawText(QRectF(x, plot.bottom() + 8, width, 16), Qt.AlignmentFlag.AlignHCenter, str(label))
        legend_y = self.height() - 13
        painter.setFont(_font(9, 600))
        painter.setPen(QColor(tokens["muted"]))
        painter.setBrush(QColor(tokens["primary"]))
        painter.drawEllipse(QPointF(plot.left(), legend_y - 2), 3.5, 3.5)
        painter.drawText(QPointF(plot.left() + 10, legend_y + 2), "Historis")
        if self.forecast:
            painter.setBrush(QColor(tokens["accent"]))
            painter.drawEllipse(QPointF(plot.left() + 78, legend_y - 2), 3.5, 3.5)
            painter.drawText(QPointF(plot.left() + 88, legend_y + 2), "Prakiraan")
            painter.setPen(QColor(tokens["muted"]))
            painter.drawText(QPointF(plot.left() + 174, legend_y + 2), "Area = interval keyakinan")
        if 0 <= self._hover < total:
            x = xs[self._hover]
            painter.setPen(QPen(QColor(tokens["border_strong"]), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            lines = [str(self.labels[self._hover])]
            if self._hover < len(self.history):
                lines.append(f"Aktual: {number(self.history[self._hover])}")
            else:
                idx = self._hover - split
                if 0 <= idx < len(self.forecast):
                    lines.append(f"Prakiraan: {number(self.forecast[idx])}")
                    if idx < len(self.lower) and idx < len(self.upper):
                        lines.append(f"Rentang: {number(self.lower[idx])} – {number(self.upper[idx])}")
            anchor = QPointF(x, plot.top() + plot.height() * 0.25)
            self._tooltip(painter, anchor, lines, tokens["accent"])
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not self.labels:
            return
        left, right = 46, 16
        ratio = min(1.0, max(0.0, (event.position().x() - left) / max(1, self.width() - left - right)))
        index = round(ratio * (len(self.labels) - 1)) if len(self.labels) > 1 else 0
        if index != self._hover:
            self._hover = index
            self.update()


class BarChart(ChartBase):
    def __init__(
        self,
        labels: Sequence[str] | None = None,
        values: Sequence[float] | None = None,
        parent: QWidget | None = None,
        height: int = 250,
        color: str | None = None,
        value_prefix: str = "",
        value_suffix: str = "",
    ) -> None:
        super().__init__(parent, height)
        self.labels = list(labels or [])
        self.values = [float(value) for value in (values or [])]
        self.color = color
        self.value_prefix = value_prefix
        self.value_suffix = value_suffix

    def set_data(self, labels: Sequence[str], values: Sequence[float]) -> None:
        self.labels = list(labels)
        self.values = [float(value) for value in values]
        self._hover = -1
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = self._tokens()
        if not self.labels or not self.values:
            self._draw_empty(painter)
            painter.end()
            return
        maximum = _nice_max(max(self.values) * 1.12 if self.values else 10)
        painter.setFont(_font(9))
        metrics = QFontMetrics(painter.font())
        # Margin kiri menyesuaikan label nilai agar angka miliaran tidak terpotong.
        left = max(46.0, metrics.horizontalAdvance(number(maximum)) + 14)
        slot_width = max(40.0, (self.width() - left - 12) / max(1, len(self.values)))
        label_lines = [_wrap_label(metrics, str(label), slot_width - 6) for label in self.labels]
        max_lines = max(len(lines) for lines in label_lines)
        bottom = 18 + max_lines * 14
        left, top, right, bottom = left, 16, 12, bottom
        plot = QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        grid_pen = QPen(QColor(tokens["border"]), 1)
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        for step in range(5):
            ratio = step / 4
            y = plot.bottom() - ratio * plot.height()
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(tokens["muted_light"]))
            painter.drawText(QRectF(0, y - 8, left - 10, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number(maximum * ratio))
        count = len(self.values)
        slot = plot.width() / max(1, count)
        bar_width = min(42.0, slot * 0.56)
        color = QColor(self.color or tokens["primary"])
        for index, value in enumerate(self.values):
            bar_height = 0 if maximum <= 0 else (value / maximum) * plot.height()
            rect = QRectF(
                plot.left() + slot * index + (slot - bar_width) / 2,
                plot.bottom() - bar_height,
                bar_width,
                bar_height,
            )
            if self._hover == index:
                hover = QColor(color)
                hover.setAlpha(255)
                painter.setBrush(hover)
            else:
                painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, min(7.0, bar_width / 2.4), min(7.0, bar_width / 2.4))
            lines = label_lines[index]
            painter.setPen(QColor(tokens["muted"]))
            painter.setFont(_font(9.5 if len(lines) > 1 else 10))
            for line_index, line in enumerate(lines):
                painter.drawText(
                    QRectF(plot.left() + slot * index, plot.bottom() + 7 + line_index * 14, slot, 15),
                    Qt.AlignmentFlag.AlignHCenter,
                    line,
                )
            painter.setPen(QColor(tokens["text_soft"]))
            painter.setFont(_font(9.5, 600))
            text = f"{self.value_prefix}{number(value)}{self.value_suffix}"
            if metrics.horizontalAdvance(text) < slot - 2:
                painter.drawText(
                    QRectF(plot.left() + slot * index, max(plot.top(), rect.top() - 14), slot, 12),
                    Qt.AlignmentFlag.AlignHCenter,
                    text,
                )
            painter.setFont(_font(9))
        if 0 <= self._hover < count:
            anchor = QPointF(plot.left() + slot * self._hover + slot / 2, plot.top() + 10)
            self._tooltip(
                painter,
                anchor,
                [str(self.labels[self._hover]), f"{self.value_prefix}{number(self.values[self._hover])}{self.value_suffix}"],
                color.name(),
            )
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not self.values:
            return
        left, right = 46, 12
        width = max(1, self.width() - left - right)
        ratio = min(0.999, max(0.0, (event.position().x() - left) / width))
        index = int(ratio * len(self.values))
        if index != self._hover:
            self._hover = index
            self.update()


class WeatherChart(ChartBase):
    def __init__(self, parent: QWidget | None = None, height: int = 250) -> None:
        super().__init__(parent, height)
        self.labels: list[str] = []
        self.temperatures: list[float] = []
        self.rainfall: list[float] = []

    def set_data(self, labels: Sequence[str], temperatures: Sequence[float], rainfall: Sequence[float]) -> None:
        self.labels = list(labels)
        self.temperatures = [float(value) for value in temperatures]
        self.rainfall = [float(value) for value in rainfall]
        self._hover = -1
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = self._tokens()
        if not self.labels:
            self._draw_empty(painter)
            painter.end()
            return
        max_rain = _nice_max(max(self.rainfall) * 1.2 if self.rainfall else 10)
        min_temp = min(self.temperatures) - 3 if self.temperatures else 0
        max_temp = max(self.temperatures) + 3 if self.temperatures else 1
        temp_span = max_temp - min_temp or 1
        left, top, right, bottom = 56, 30, 56, 46
        plot = QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        count = len(self.labels)
        slot = plot.width() / max(1, count)
        bar_width = min(28.0, slot * 0.52)
        for step in range(4):
            ratio = step / 3
            y = plot.top() + ratio * plot.height()
            painter.setPen(QPen(QColor(tokens["border"]), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setFont(_font(9))
            painter.setPen(QColor(tokens["warning"]))
            painter.drawText(
                QRectF(0, y - 8, left - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{max_temp - ratio * temp_span:.0f}°",
            )
            painter.setPen(QColor(tokens["info"]))
            painter.drawText(
                QRectF(plot.right() + 8, y - 8, right - 8, 16),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{max_rain * (1 - ratio):.1f}" if max_rain < 10 else f"{max_rain * (1 - ratio):.0f}",
            )
        for index, value in enumerate(self.rainfall):
            height = value / max_rain * plot.height() if max_rain else 0
            rect = QRectF(plot.left() + slot * index + (slot - bar_width) / 2, plot.bottom() - height, bar_width, height)
            color = QColor(tokens["info"])
            color.setAlpha(155)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 3, 3)
        points = []
        for index, value in enumerate(self.temperatures):
            x = plot.left() + slot * index + slot / 2
            y = plot.bottom() - (value - min_temp) / temp_span * plot.height()
            points.append(QPointF(x, y))
        if points:
            pen = QPen(QColor(tokens["warning"]), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            path = QPainterPath(points[0])
            for point in points[1:]:
                path.lineTo(point)
            painter.drawPath(path)
            painter.setPen(QPen(QColor(tokens["warning"]), 1.8))
            painter.setBrush(QColor(tokens["surface"]))
            for point in points:
                painter.drawEllipse(point, 3.2, 3.2)
        painter.setFont(_font(9))
        step = max(1, ceil(count / 8))
        for index, label in enumerate(self.labels):
            if index % step != 0 and index != count - 1:
                continue
            painter.setPen(QColor(tokens["muted"]))
            painter.drawText(
                QRectF(plot.left() + slot * index - 20, plot.bottom() + 8, slot + 40, 16),
                Qt.AlignmentFlag.AlignHCenter,
                str(label),
            )
        painter.setFont(_font(8.5, 600))
        painter.setPen(QColor(tokens["muted"]))
        painter.setBrush(QColor(tokens["warning"]))
        painter.drawEllipse(QPointF(plot.left(), 16), 3.5, 3.5)
        painter.drawText(QPointF(plot.left() + 9, 20), "Suhu (°C)")
        painter.setBrush(QColor(tokens["info"]))
        painter.drawEllipse(QPointF(plot.left() + 88, 16), 3.5, 3.5)
        painter.drawText(QPointF(plot.left() + 97, 20), "Curah hujan (mm)")
        if 0 <= self._hover < count:
            x = plot.left() + slot * self._hover + slot / 2
            painter.setPen(QPen(QColor(tokens["border_strong"]), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            lines = [str(self.labels[self._hover])]
            if self._hover < len(self.temperatures):
                lines.append(f"Suhu: {number(self.temperatures[self._hover], 1)}°C")
            if self._hover < len(self.rainfall):
                lines.append(f"Hujan: {number(self.rainfall[self._hover], 1)} mm")
            self._tooltip(painter, QPointF(x, plot.top() + 10), lines, tokens["warning"])
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not self.labels:
            return
        left, right = 56, 56
        ratio = min(0.999, max(0.0, (event.position().x() - left) / max(1, self.width() - left - right)))
        index = int(ratio * len(self.labels))
        if index != self._hover:
            self._hover = index
            self.update()


class FeatureBars(QWidget):
    """Daftar fitur penting dengan bar horizontal."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.items: list[tuple[str, float]] = []
        self.setMinimumHeight(60)
        theme.changed.connect(self.update)

    def set_items(self, items: Iterable[tuple[str, float]]) -> None:
        self.items = [(label, float(value)) for label, value in items]
        self.setMinimumHeight(max(48, len(self.items) * 30 + 4))
        self.update()

    def paintEvent(self, _event) -> None:
        if not self.items:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = theme.tokens
        maximum = max(value for _label, value in self.items) or 1
        painter.setFont(_font(9.5))
        row_height = 30
        for index, (label, value) in enumerate(self.items):
            y = index * row_height
            painter.setPen(QColor(tokens["text_soft"]))
            painter.drawText(QRectF(0, y + 4, self.width() * 0.55, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label[:34])
            bar_rect = QRectF(self.width() * 0.57, y + 10, self.width() * 0.28, 6)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(tokens["track"]))
            painter.drawRoundedRect(bar_rect, 3, 3)
            fill = QRectF(bar_rect.left(), bar_rect.top(), max(3.0, bar_rect.width() * value / maximum), bar_rect.height())
            painter.setBrush(QColor(tokens["primary"]))
            painter.drawRoundedRect(fill, 3, 3)
            painter.setPen(QColor(tokens["text"]))
            painter.setFont(_font(9, 700))
            painter.drawText(
                QRectF(self.width() * 0.87, y + 4, self.width() * 0.13, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{value * 100:.1f}%",
            )
            painter.setFont(_font(9.5))
        painter.end()


class MiniBars(QWidget):
    """Bar horizontal ringkas untuk distribusi status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rows: list[tuple[str, float, float, str]] = []
        self.setMinimumHeight(40)
        theme.changed.connect(self.update)

    def set_rows(self, rows: Iterable[tuple[str, float, float, str]]) -> None:
        """rows: (label, value, percentage, color)"""
        self.rows = list(rows)
        self.setMinimumHeight(max(30, len(self.rows) * 38))
        self.update()

    def paintEvent(self, _event) -> None:
        if not self.rows:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tokens = theme.tokens
        for index, (label, value, percentage, color) in enumerate(self.rows):
            y = index * 38
            painter.setFont(_font(9.5, 600))
            painter.setPen(QColor(tokens["text"]))
            painter.drawText(QRectF(0, y + 2, self.width() * 0.32, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
            painter.setFont(_font(9.5))
            painter.setPen(QColor(tokens["muted"]))
            painter.drawText(
                QRectF(self.width() * 0.33, y + 2, self.width() * 0.18, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{number(value)} obat",
            )
            bar_rect = QRectF(self.width() * 0.53, y + 8, self.width() * 0.32, 7)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(tokens["track"]))
            painter.drawRoundedRect(bar_rect, 3.5, 3.5)
            fill = QRectF(bar_rect.left(), bar_rect.top(), max(0.0, min(1.0, percentage / 100)) * bar_rect.width(), bar_rect.height())
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(fill, 3.5, 3.5)
            painter.setFont(_font(9.5, 700))
            painter.setPen(QColor(tokens["text"]))
            painter.drawText(
                QRectF(self.width() * 0.87, y + 2, self.width() * 0.13, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{percentage:.1f}%",
            )
        painter.end()
