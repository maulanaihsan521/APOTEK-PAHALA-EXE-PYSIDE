"""Halaman Laporan."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.charts import BarChart
from app.components.dialogs import DateRangeDialog
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    InlineBanner,
    ResponsiveCardRow,
    SectionHeader,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.icons import icon
from app.core.theme import theme
from app.core.utils import format_date, format_datetime
from app.pages.common import PageNotice, clear_layout, download_export

REPORT_TYPES = [
    ("sales", "Laporan Penjualan"),
    ("demand", "Laporan Permintaan Obat"),
    ("prediction", "Laporan Prediksi"),
    ("model_evaluation", "Laporan Evaluasi Model"),
    ("stock", "Laporan Stok"),
    ("procurement", "Laporan Rekomendasi Pengadaan"),
]

TILE_ICONS = [
    ("chart-column", "primary"),
    ("boxes", "info"),
    ("receipt-text", "accent"),
    ("wallet", "warning"),
    ("pill", "purple"),
    ("badge-check", "success"),
]


class ReportsPage(PageBase):
    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self.start = ""
        self.end = ""
        self._serial = 0
        self._types_loaded = False
        self._report: dict[str, Any] = {}
        self._tiles: list[StatTile] = []

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        controls = Card(padding=15, spacing=9)
        row = QHBoxLayout()
        row.setSpacing(9)
        row.addWidget(QLabel("Jenis laporan"))
        self.type_combo = QComboBox()
        for value, label in REPORT_TYPES:
            self.type_combo.addItem(label, value)
        self.type_combo.setMinimumWidth(215)
        self.type_combo.currentIndexChanged.connect(self._type_changed)
        row.addWidget(self.type_combo, 1)
        self.date_button = QPushButton("  Semua periode")
        self.date_button.setProperty("variant", "outline")
        self.date_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_button.setMinimumHeight(40)
        self.date_button.setMinimumWidth(170)
        self.date_button.setIcon(icon("calendar-range", theme.tokens["muted"], 15))
        self.date_button.setIconSize(QSize(15, 15))
        self.date_button.clicked.connect(self._choose_dates)
        row.addWidget(self.date_button)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setProperty("variant", "ghost")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self._reset_dates)
        self.reset_button.hide()
        row.addWidget(self.reset_button)
        row.addStretch(1)
        self.refresh_button = ThemedButton("", "ghost", "refresh-cw", compact=True)
        self.refresh_button.setToolTip("Muat ulang laporan")
        self.refresh_button.setFixedWidth(40)
        self.refresh_button.clicked.connect(self.load)
        row.addWidget(self.refresh_button)
        self.export_pdf = ThemedButton("PDF", "outline", "file-text", compact=True)
        self.export_pdf.setToolTip("Ekspor laporan ke PDF")
        self.export_pdf.clicked.connect(lambda: self._export("pdf"))
        row.addWidget(self.export_pdf)
        self.export_excel = ThemedButton("Excel", "outline", "file-spreadsheet", compact=True)
        self.export_excel.setToolTip("Ekspor laporan ke Excel")
        self.export_excel.clicked.connect(lambda: self._export("xlsx"))
        row.addWidget(self.export_excel)
        self.export_csv = ThemedButton("CSV", "ghost", "download", compact=True)
        self.export_csv.setToolTip("Ekspor laporan ke CSV")
        self.export_csv.clicked.connect(lambda: self._export("csv"))
        row.addWidget(self.export_csv)
        controls.body.addLayout(row)
        self.body.addWidget(controls)

        self.banner = InlineBanner("Pilih jenis laporan lalu terapkan periode.", "info")
        self.body.addWidget(self.banner)

        tiles = []
        for index, (icon_name, tone) in enumerate(TILE_ICONS):
            tile = StatTile(f"Ringkasan {index + 1}", icon_name, tone)
            tile.set_value("—")
            tiles.append(tile)
            self._tiles.append(tile)
        self.period_tile = tiles[-1]
        self.tile_row = ResponsiveCardRow(tiles, spacing=12, min_width=225)
        self.body.addWidget(self.tile_row)

        chart_card = Card(padding=16, spacing=8)
        chart_head = QHBoxLayout()
        chart_head.setContentsMargins(0, 0, 0, 0)
        chart_head.addWidget(
            SectionHeader(
                "Grafik Utama Laporan",
                "Kontribusi nilai terbesar pada laporan yang dipilih.",
                "chart-column",
            ),
            1,
        )
        self.actual_badge = Badge("DATA AKTUAL", "success")
        chart_head.addWidget(self.actual_badge)
        chart_card.body.addLayout(chart_head)
        self.chart = BarChart(height=300, value_prefix="")
        chart_card.body.addWidget(self.chart)
        self.chart_note = QLabel("Grafik mengikuti data laporan yang sedang ditampilkan.")
        self.chart_note.setObjectName("MutedSmall")
        chart_card.body.addWidget(self.chart_note)
        self.body.addWidget(chart_card)

        table_card = Card(padding=16, spacing=8)
        table_head = QHBoxLayout()
        table_head.setContentsMargins(0, 0, 0, 0)
        table_head.addWidget(
            SectionHeader("Rincian Laporan", "Data sesuai periode dan jenis laporan yang dipilih.", "table-2"),
            1,
        )
        self.count_label = QLabel("")
        self.count_label.setObjectName("MutedSmall")
        table_head.addWidget(self.count_label)
        table_card.body.addLayout(table_head)
        self.table_holder = QVBoxLayout()
        self.table_holder.setSpacing(6)
        table_card.body.addLayout(self.table_holder)
        self.table = Table(["Belum ada data"])
        self.table.setMinimumHeight(420)
        self.table.setMaximumHeight(500)
        self.table_holder.addWidget(self.table)
        self.table_note = QLabel("")
        self.table_note.setObjectName("MutedSmall")
        self.table_note.setWordWrap(True)
        table_card.body.addWidget(self.table_note)
        self.body.addWidget(table_card)

        info_card = Card(padding=16, spacing=7)
        info_card.body.addWidget(SectionHeader("Catatan Laporan", "Metadata dokumen dan sumber data.", "file-text"))
        self.meta_holder = QHBoxLayout()
        self.meta_holder.setSpacing(8)
        self.meta_holder.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_card.body.addLayout(self.meta_holder)
        self.notes = QLabel("")
        self.notes.setObjectName("Muted")
        self.notes.setWordWrap(True)
        info_card.body.addWidget(self.notes)
        self.body.addWidget(info_card)
        self.body.addStretch(1)

    def on_show(self) -> None:
        if not self._types_loaded:
            self._load_types()
        else:
            self.load()

    def _load_types(self) -> None:
        self.runner.submit(
            lambda: self.api.get("/reports/types", timeout=20),
            self._types_ready,
            lambda _message, _status: self.load(),
        )

    def _types_ready(self, types: list) -> None:
        self._types_loaded = True
        if not types:
            self.load()
            return
        current = self.type_combo.currentData()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for item in types:
            self.type_combo.addItem(item.get("label", ""), item.get("value", ""))
        index = self.type_combo.findData(current)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.type_combo.blockSignals(False)
        self.load()

    def _type_changed(self) -> None:
        self.load()

    def _choose_dates(self) -> None:
        dialog = DateRangeDialog(
            "Filter Periode Laporan",
            self.start or self._report.get("start"),
            self.end or self._report.get("end"),
            self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.start, self.end = dialog.values()
            self.date_button.setText(f"  {format_date(self.start)} – {format_date(self.end)}")
            self.reset_button.show()
            self.load()

    def _reset_dates(self) -> None:
        self.start = self.end = ""
        self.date_button.setText("  Semua periode")
        self.reset_button.hide()
        self.load()

    def _params(self) -> dict:
        params = {"type": self.type_combo.currentData() or "sales"}
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end
        return params

    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        params = self._params()
        self.notice.show_message("Menyusun laporan...", "info")
        self.runner.submit(
            lambda: self.api.get("/reports/summary", params=params, timeout=90),
            lambda data: self._apply(data, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._serial:
            self.notice.show_message(message, "danger")

    def _apply(self, data: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self._report = data
        self.notice.clear()
        self.banner.set_message(
            f"{data.get('title', 'Laporan')} · {data.get('meta', {}).get('Periode', 'seluruh periode')} · "
            f"dibuat {format_datetime(data.get('generated_at'))}",
            "info",
        )
        self.actual_badge.setText("DATA AKTUAL")
        self.actual_badge.set_tone("success")
        self.actual_badge.setVisible(True)
        summary = data.get("summary", [])
        for index, tile in enumerate(self._tiles[:5]):
            if index < len(summary):
                label, value = summary[index]
                tile.title.setText(str(label))
                tile.set_value(str(value), "")
                tile.show()
            else:
                tile.hide()
        start = str(data.get("start") or self.start or "")
        end = str(data.get("end") or self.end or "")
        self.period_tile.title.setText("Periode laporan")
        if start and end:
            start_label = format_date(start)
            end_label = format_date(end)
            same_year = start[:4] == end[:4]
            self.period_tile.set_value(
                format_date(end) if same_year else f"{start[:4]} – {end[:4]}",
                f"{start_label} – {end_label}",
            )
        else:
            self.period_tile.set_value("Seluruh data", "Semua tanggal tersedia")
        self.period_tile.show()
        self.tile_row.refresh()
        chart = data.get("chart", []) or []
        labels = [str(item[0]) for item in chart]
        values = [float(item[1]) for item in chart]
        self.chart.set_data(labels, values)
        self.chart_note.setText(
            "Grafik nilai teratas pada laporan ini. Data aktual Apotek Pahala."
            if chart
            else "Laporan ini tidak menyediakan grafik nilai."
        )
        columns = [str(column) for column in data.get("columns", [])]
        rows = data.get("rows", [])
        count = len(rows)
        self.count_label.setText(f"{count} baris data")
        if columns:
            table = Table(columns)
            table.setMinimumHeight(420)
            table.setMaximumHeight(500)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header_item = table.horizontalHeaderItem(0)
            if header_item:
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            table.verticalHeader().setDefaultSectionSize(40)
            table.setRowCount(count)
            for row_index, record in enumerate(rows):
                for column_index, value in enumerate(record):
                    if column_index >= len(columns):
                        break
                    text = str(value)
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        text = f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", ".")
                        table.add_item(
                            row_index,
                            column_index,
                            text,
                            Qt.AlignmentFlag.AlignRight,
                        )
                    else:
                        table.add_item(row_index, column_index, text)
            self.table_holder.removeWidget(self.table)
            self.table.deleteLater()
            self.table = table
            self.table_holder.addWidget(table)
            for column_index in range(1, min(len(columns), 7)):
                table.resizeColumnToContents(column_index)
        self.table_note.setText(
            f"{count} baris ditampilkan. Ekspor Excel memuat seluruh data; PDF dibatasi 80 baris."
            if count
            else "Tidak ada baris data pada periode ini."
        )
        clear_layout(self.meta_holder)
        meta = data.get("meta", {}) or {}
        for key, value in meta.items():
            chip = QLabel(f"{key}: {value}")
            chip.setObjectName("Chip")
            self.meta_holder.addWidget(chip)
        self.notes.setText(str(data.get("notes", "")))

    def _export(self, fmt: str) -> None:
        if not self._report:
            self.toast("Laporan belum siap. Tunggu proses pemuatan selesai.", "warning")
            return
        params = self._params()
        params["fmt"] = fmt
        base = str(self._report.get("title", "Laporan")).replace(" ", "_")
        filters = {
            "pdf": ("PDF (*.pdf)", "pdf"),
            "xlsx": ("Excel (*.xlsx)", "xlsx"),
            "csv": ("CSV (*.csv)", "csv"),
        }[fmt]
        download_export(
            self,
            self.api,
            "/reports/export",
            f"{base}.{filters[1]}",
            params=params,
            file_filter=filters[0],
        )
