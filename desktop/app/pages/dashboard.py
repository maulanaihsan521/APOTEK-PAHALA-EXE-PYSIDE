"""Halaman Ringkasan Apotek."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.charts import MiniBars, Sparkline, TrendChart
from app.components.layout import PageBase
from app.components.widgets import (
    Card,
    ElidedLabel,
    IconBox,
    InlineBanner,
    KpiCard,
    ResponsiveCardRow,
    SectionHeader,
    SegmentedControl,
    SoftCard,
    Table,
    ThemedButton,
    refresh_style,
)
from app.core.icons import icon
from app.core.theme import theme
from app.core.utils import compact_rupiah, format_date, format_datetime, number, percent, relative_time
from app.pages.common import PageNotice, activity_icon, clear_layout, link_button


class ActivityDialog(QDialog):
    def __init__(self, api, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("Semua Aktivitas")
        self.setModal(True)
        self.resize(640, 600)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        title = QLabel("Riwayat Aktivitas")
        title.setStyleSheet("font-size: 17px; font-weight: 800;")
        head.addWidget(title)
        head.addStretch(1)
        layout.addLayout(head)
        self.banner = InlineBanner("Memuat aktivitas...", "info")
        layout.addWidget(self.banner)
        self.rows = QVBoxLayout()
        self.rows.setSpacing(2)
        holder = QWidget()
        holder.setLayout(self.rows)
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(holder)
        layout.addWidget(scroll, 1)
        close = ThemedButton("Tutup", "outline")
        close.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close)
        layout.addLayout(footer)
        self._load()

    def _load(self) -> None:
        try:
            payload = self.api.get("/activities", params={"page_size": 60}, timeout=30)
        except Exception as exc:  # noqa: BLE001
            self.banner.set_message(str(exc), "danger")
            return
        items = payload.get("items", [])
        self.banner.set_message(f"{payload.get('total', len(items))} aktivitas tercatat", "info")
        clear_layout(self.rows)
        for item in items:
            icon_name, color_role, bg_role = activity_icon(item.get("type"))
            row = QFrame()
            row.setStyleSheet(f"QFrame {{ border-bottom: 1px solid {theme.tokens['border']}; }}")
            item_layout = QHBoxLayout(row)
            item_layout.setContentsMargins(2, 8, 2, 8)
            item_layout.setSpacing(10)
            item_layout.addWidget(IconBox(icon_name, color_role, bg_role, 30, 14))
            text = QVBoxLayout()
            text.setSpacing(1)
            desc = QLabel(item.get("description", ""))
            desc.setWordWrap(True)
            desc.setStyleSheet("font-size: 12px;")
            text.addWidget(desc)
            meta = QLabel(f"{item.get('user', 'Sistem')} · {relative_time(item.get('created_at'))}")
            meta.setObjectName("MutedSmall")
            text.addWidget(meta)
            item_layout.addLayout(text, 1)
            self.rows.addWidget(row)
        self.rows.addStretch(1)


class PeriodDialog(QDialog):
    def __init__(self, current: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Periode Analisis")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        title = QLabel("Periode Analisis")
        title.setStyleSheet("font-size: 16px; font-weight: 800;")
        layout.addWidget(title)
        note = QLabel("Pilih panjang periode ringkasan. Grafik menggunakan pekan permintaan terakhir yang tersedia.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.segment = SegmentedControl([(4, "4 Minggu"), (12, "12 Minggu"), (52, "52 Minggu")], current)
        layout.addWidget(self.segment)
        footer = QHBoxLayout()
        footer.addStretch(1)
        cancel = ThemedButton("Batal", "outline")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        apply = ThemedButton("Terapkan", "primary", "filter")
        apply.clicked.connect(self.accept)
        footer.addWidget(apply)
        layout.addLayout(footer)

    def weeks(self) -> int:
        return int(self.segment.value() or 4)


class DashboardPage(PageBase):
    navigate = Signal(str)
    period_changed = Signal(dict)

    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self.weeks = 4
        self._serial = 0
        self._data: dict[str, Any] = {}
        self._period: dict[str, Any] = {}

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        self.kpi_revenue = KpiCard("Estimasi Nilai Permintaan", "wallet", "accent")
        self.kpi_demand = KpiCard("Total Permintaan", "pill", "info")
        self.kpi_priority = KpiCard("Obat Prioritas", "triangle-alert", "warning")
        self.kpi_mape = KpiCard("Akurasi Prediksi", "target", "purple")
        self.kpi_mape.setToolTip(
            "Akurasi dihitung dari WAPE: rata-rata persentase selisih prakiraan "
            "terhadap permintaan aktual. Semakin kecil WAPE, semakin akurat."
        )
        self.kpi_row = ResponsiveCardRow(
            [self.kpi_revenue, self.kpi_demand, self.kpi_priority, self.kpi_mape],
            spacing=14,
            min_width=232,
        )
        self.body.addWidget(self.kpi_row)

        middle = QHBoxLayout()
        middle.setSpacing(14)
        self.chart_card = Card(padding=17, spacing=8)
        chart_action = QWidget()
        chart_action_layout = QHBoxLayout(chart_action)
        chart_action_layout.setContentsMargins(0, 0, 0, 0)
        chart_action_layout.setSpacing(8)
        self.range_segment = SegmentedControl(
            [(4, "4 Mgg"), (12, "12 Mgg"), (52, "1 Thn")], 4
        )
        self.range_segment.changed.connect(self._change_weeks)
        chart_action_layout.addWidget(self.range_segment)
        self.chart_card.body.addWidget(
            SectionHeader(
                "Tren & Prediksi",
                "Data aktual vs hasil backtest model.",
                "chart-column",
                chart_action,
            )
        )
        self.chart = TrendChart(height=285)
        self.chart.setMinimumWidth(380)
        self.chart_card.body.addWidget(self.chart, 1)
        middle.addWidget(self.chart_card, 3)

        self.prediction_card = Card(padding=17, spacing=9)
        self.prediction_card.body.addWidget(
            SectionHeader("Ringkasan Prediksi", "Prakiraan empat pekan ke depan.", "calendar-days")
        )
        self.prediction_rows_layout = QVBoxLayout()
        self.prediction_rows_layout.setSpacing(0)
        self.prediction_rows: list[tuple[QLabel, QLabel]] = []
        self.unit_label = "unit"
        for index in range(4):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(2, 9, 2, 9)
            row_layout.setSpacing(8)
            label = QLabel(f"Minggu {index + 1}")
            label.setObjectName("Muted")
            row_layout.addWidget(label, 1)
            value = QLabel("—")
            value.setStyleSheet("font-size: 17px; font-weight: 800;")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(value)
            self.prediction_rows_layout.addWidget(row)
            if index < 3:
                divider = QFrame()
                divider.setFixedHeight(1)
                divider.setStyleSheet(f"background: {theme.tokens['border']};")
                self.prediction_rows_layout.addWidget(divider)
            self.prediction_rows.append((label, value))
        self.prediction_card.body.addLayout(self.prediction_rows_layout)
        self._insight_message = "Menunggu data prediksi..."
        self._insight_level = "success"
        self.insight = QFrame()
        self.insight.setObjectName("SoftCard")
        self.insight_layout = QHBoxLayout(self.insight)
        self.insight_layout.setContentsMargins(12, 10, 12, 10)
        self.insight_layout.setSpacing(9)
        self.insight_icon = IconBox("sparkles", "success", "success_bg", 31, 15)
        self.insight_layout.addWidget(self.insight_icon, 0, Qt.AlignmentFlag.AlignTop)
        self.insight_text = QLabel("Menunggu data prediksi...")
        self.insight_text.setWordWrap(True)
        self.insight_text.setStyleSheet("font-size: 12px;")
        self.insight_layout.addWidget(self.insight_text, 1)
        self.prediction_card.body.addWidget(self.insight)
        footer_row = QHBoxLayout()
        self.prediction_total = QLabel("Total —")
        self.prediction_total.setObjectName("MutedSmall")
        footer_row.addWidget(self.prediction_total)
        footer_row.addStretch(1)
        footer_row.addWidget(link_button("Lihat detail  →", lambda: self.navigate.emit("prediction")))
        self.prediction_card.body.addLayout(footer_row)
        middle.addWidget(self.prediction_card, 2)
        self.body.addLayout(middle)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)
        self.top_card = Card(padding=17, spacing=8)
        top_action = link_button("Lihat semua  →", lambda: self.navigate.emit("sales"))
        self.top_card.body.addWidget(
            SectionHeader(
                "Obat dengan Permintaan Tertinggi",
                "Berdasarkan estimasi permintaan pada periode aktif.",
                "chart-column",
                top_action,
            )
        )
        self.top_table = Table(["Nama Obat", "Permintaan", "Prediksi", "Tren"])
        self.top_table.setMinimumHeight(230)
        self.top_table.horizontalHeader().setSectionResizeMode(0, self.top_table.horizontalHeader().ResizeMode.Stretch)
        for column, width in ((1, 96), (2, 76), (3, 88)):
            self.top_table.setColumnWidth(column, width)
        self.top_table.verticalHeader().setDefaultSectionSize(46)
        self.top_card.body.addWidget(self.top_table)
        bottom.addWidget(self.top_card, 3)

        self.stock_card = Card(padding=17, spacing=8)
        self.stock_card.body.addWidget(
            SectionHeader(
                "Status Persediaan",
                "Ringkasan status stok seluruh obat aktif.",
                "boxes",
                link_button("Lihat Detail  →", lambda: self.navigate.emit("stock")),
            )
        )
        self.stock_bars = MiniBars()
        self.stock_bars.setMinimumHeight(126)
        self.stock_card.body.addWidget(self.stock_bars)
        stock_footer = QHBoxLayout()
        self.stock_total = QLabel("—")
        self.stock_total.setObjectName("MutedSmall")
        stock_footer.addWidget(self.stock_total)
        stock_footer.addStretch(1)
        self.stock_period = QLabel("")
        self.stock_period.setObjectName("MutedSmall")
        stock_footer.addWidget(self.stock_period)
        self.stock_card.body.addLayout(stock_footer)
        bottom.addWidget(self.stock_card, 2)
        self.body.addLayout(bottom)

        self.activity_card = Card(padding=17, spacing=6)
        activity_action = link_button("Lihat semua  →", self._open_activities)
        self.activity_card.body.addWidget(
            SectionHeader(
                "Aktivitas Terbaru",
                "Jejak audit perubahan data dan proses sistem.",
                "activity",
                activity_action,
            )
        )
        self.activities_layout = QVBoxLayout()
        self.activities_layout.setSpacing(0)
        self.activity_card.body.addLayout(self.activities_layout)
        self.body.addWidget(self.activity_card)
        self.body.addStretch(1)
        theme.changed.connect(self._refresh_footer_text)
        theme.changed.connect(self._restyle_insight)

    def on_show(self) -> None:
        self.load()

    def period_clicked(self) -> None:
        dialog = PeriodDialog(self.weeks, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            weeks = dialog.weeks()
            if weeks != self.weeks:
                self.weeks = weeks
                self.range_segment.set_value(weeks)
                self.load()

    def _change_weeks(self, weeks: Any) -> None:
        self.weeks = int(weeks)
        self.load()

    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat ringkasan apotek...", "info")
        self.runner.submit(
            lambda: self.api.get("/dashboard/overview", params={"weeks": self.weeks}, timeout=45),
            lambda data: self._apply(data, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.show_message(message, "danger")

    def _apply(self, data: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self._data = data
        self.notice.clear()
        period = data.get("period", {})
        kpis = data.get("kpis", {})
        start_label = format_date(period.get("start"))
        end_label = format_date(period.get("end"))
        range_hint = f"{start_label} – {end_label}"
        self.kpi_revenue.set_value(
            compact_rupiah(kpis.get("revenue", 0)),
            "vs periode sebelumnya",
            kpis.get("revenue_delta"),
        )
        self.kpi_demand.set_value(
            f"{number(kpis.get('demand', 0))} unit",
            "vs periode sebelumnya",
            kpis.get("demand_delta"),
        )
        self.kpi_priority.set_value(
            f"{number(kpis.get('priority_count', 0))} obat",
            "Perlu perhatian khusus",
        )
        accuracy = kpis.get("accuracy")
        wape = kpis.get("wape")
        self.kpi_mape.set_value(
            percent(accuracy, 2),
            f"WAPE {percent(wape, 2)}",
        )
        self.kpi_mape.setToolTip(
            f"WAPE {percent(wape, 2)} dari {kpis.get('wape_medicine_count', 0)} obat prioritas. "
            "Semakin kecil WAPE, semakin dekat prakiraan dengan permintaan aktual."
        )
        trend = data.get("trend", {})
        self.chart.set_data(
            trend.get("labels", []),
            trend.get("actual", []),
            trend.get("predicted", []),
        )
        summary = data.get("prediction_summary", {})
        weeks = summary.get("weeks", [])
        totals = [int(item.get("value", 0)) for item in weeks]
        self.unit_label = self._unit_from_tops(data.get("top_medicines", []))
        for index, (label, value) in enumerate(self.prediction_rows):
            if index < len(weeks):
                label.setText(weeks[index].get("label", f"Minggu {index + 1}"))
                value.setText(f"{number(totals[index])} {self.unit_label}")
                label.show()
                value.show()
            else:
                label.hide()
                value.hide()
        total = summary.get("total", sum(totals))
        self.prediction_total.setText(
            f"Total {summary.get('horizon', 4)} pekan · {number(total)} {self.unit_label}"
        )
        insight = summary.get("insight", "Belum ada insight prediksi.")
        level = summary.get("insight_level", "info")
        self._set_insight(insight, level)

        top = data.get("top_medicines", [])
        self._render_top(top, range_hint)
        self._render_stock(data.get("stock", {}), range_hint)
        self._render_activities(data.get("activities", []))
        self._refresh_footer_text()
        self._period = period
        self.period_changed.emit(period)

    @staticmethod
    def _unit_from_tops(top: list[dict]) -> str:
        units = [item.get("unit") for item in top if item.get("unit")]
        return units[0] if units else "unit"

    def _set_insight(self, text: str, level: str) -> None:
        self._insight_message = text
        self._insight_level = level
        self._restyle_insight()

    def _restyle_insight(self) -> None:
        tokens = theme.tokens
        mapping = {
            "success": ("success_bg", "success", "sparkles"),
            "warning": ("warning_bg", "warning_text", "triangle-alert"),
            "danger": ("danger_bg", "danger_text", "circle-alert"),
            "info": ("info_bg", "info_text", "info"),
        }
        bg_key, fg_key, icon_name = mapping.get(self._insight_level, mapping["info"])
        self.insight.setStyleSheet(
            f"QFrame#SoftCard {{ background: {tokens[bg_key]}; border: 1px solid {tokens[bg_key]}; border-radius: 10px; }}"
        )
        self.insight_icon._color_role = fg_key
        self.insight_icon._bg_role = bg_key
        self.insight_icon.set_icon(icon_name)
        self.insight_text.setText(self._insight_message)
        self.insight_text.setStyleSheet(f"font-size: 12px; color: {tokens[fg_key]};")

    def _render_top(self, top: list[dict], hint: str) -> None:
        self.top_table.setRowCount(0)
        self.top_table.setRowCount(len(top))
        for row_index, item in enumerate(top):
            name_widget = QWidget()
            name_layout = QVBoxLayout(name_widget)
            name_layout.setContentsMargins(4, 4, 4, 4)
            name_layout.setSpacing(0)
            name = ElidedLabel(item.get("name", "-"))
            name.setObjectName("TablePrimary")
            name_layout.addWidget(name)
            unit = ElidedLabel(f"{item.get('unit', '')}")
            unit.setObjectName("TableMeta")
            name_layout.addWidget(unit)
            self.top_table.setCellWidget(row_index, 0, name_widget)
            self.top_table.add_item(
                row_index, 1, number(item.get("sold", 0)), Qt.AlignmentFlag.AlignRight, color=theme.tokens["text_soft"]
            )
            self.top_table.add_item(
                row_index, 2, number(item.get("predicted", 0)), Qt.AlignmentFlag.AlignRight,
                color=theme.tokens["primary"], bold=True,
            )
            spark = Sparkline(item.get("sparkline", []), height=30)
            holder = QWidget()
            spark_layout = QHBoxLayout(holder)
            spark_layout.setContentsMargins(6, 2, 4, 2)
            spark_layout.addWidget(spark)
            self.top_table.setCellWidget(row_index, 3, holder)
        if not top:
            self.top_table.setRowCount(1)
            self.top_table.setSpan(0, 0, 1, 4)
            self.top_table.add_item(0, 0, "Belum ada data permintaan pada periode ini.", Qt.AlignmentFlag.AlignCenter, color=theme.tokens["muted"])

    def _render_stock(self, stock: dict, hint: str) -> None:
        tokens = theme.tokens
        self.stock_bars.set_rows(
            [
                ("Aman", stock.get("aman", 0), stock.get("percent_aman", 0), tokens["success"]),
                ("Perlu perhatian", stock.get("perlu_perhatian", 0), stock.get("percent_perhatian", 0), tokens["warning"]),
                ("Kritis", stock.get("kritis", 0), stock.get("percent_kritis", 0), tokens["danger"]),
            ]
        )
        self.stock_total.setText(f"{stock.get('total', 0)} obat aktif dipantau")
        self.stock_period.setText(hint)
        self.stock_period.setVisible(bool(hint))

    def _render_activities(self, activities: list[dict]) -> None:
        clear_layout(self.activities_layout)
        if not activities:
            empty = QLabel("Belum ada aktivitas tercatat.")
            empty.setObjectName("Muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(70)
            self.activities_layout.addWidget(empty)
            return
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        for index, item in enumerate(activities[:6]):
            row, column = index % 3, index // 3
            icon_name, color_role, bg_role = activity_icon(item.get("type"))
            block = QFrame()
            block.setMinimumHeight(58)
            item_layout = QHBoxLayout(block)
            item_layout.setContentsMargins(2, 8, 2, 8)
            item_layout.setSpacing(10)
            item_layout.addWidget(IconBox(icon_name, color_role, bg_role, 32, 15), 0, Qt.AlignmentFlag.AlignTop)
            text = QVBoxLayout()
            text.setSpacing(1)
            desc = QLabel(item.get("description", ""))
            desc.setWordWrap(True)
            desc.setStyleSheet("font-size: 12px;")
            desc.setMaximumWidth(380)
            text.addWidget(desc)
            meta = QLabel(
                f"{item.get('user', 'Sistem')} · {relative_time(item.get('created_at'))}"
            )
            meta.setObjectName("MutedSmall")
            text.addWidget(meta)
            item_layout.addLayout(text, 1)
            grid.addWidget(block, row, column)
        self.activities_layout.addLayout(grid)

    def _refresh_footer_text(self) -> None:
        # Segarkan warna teks kecil yang diset langsung saat tema berubah.
        for label in (self.prediction_total, self.stock_total, self.stock_period):
            label.setStyleSheet(f"color: {theme.tokens['muted']}; font-size: 12px;")

    def _open_activities(self) -> None:
        dialog = ActivityDialog(self.api, self)
        dialog.exec()
