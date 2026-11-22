"""Halaman Data Cuaca."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.charts import WeatherChart
from app.components.dialogs import ConfirmDialog, DateRangeDialog, ImportWizardDialog, WeatherDialog
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    IconButton,
    ResponsiveCardRow,
    SearchInput,
    SectionHeader,
    SegmentedControl,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.icons import icon
from app.core.theme import theme
from app.core.utils import format_date, format_datetime, number
from app.pages.common import PageNotice, download_export


class WeatherPage(PageBase):
    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self.is_admin = str(user.get("role", "")).lower() == "admin"
        self.page = 1
        self.page_size = 15
        self.pages = 1
        self.total = 0
        self.start = ""
        self.end = ""
        self.weeks = 12
        self._serial = 0
        self._bmkg_busy = False
        self._bmkg_timer = QTimer(self)
        self._bmkg_timer.setInterval(30 * 60 * 1000)
        self._bmkg_timer.timeout.connect(self._on_bmkg_auto_update)

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        filter_card = Card(padding=14, spacing=10)
        row = QHBoxLayout()
        row.setSpacing(9)
        self.search = SearchInput("Cari tanggal cuaca...")
        self.search.setMinimumWidth(220)
        self.search.textChanged.connect(self._search_changed)
        row.addWidget(self.search, 2)
        self.date_button = QPushButton("  Semua periode")
        self.date_button.setProperty("variant", "outline")
        self.date_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_button.setIcon(icon("calendar-range", theme.tokens["muted"], 15))
        self.date_button.setIconSize(QSize(15, 15))
        self.date_button.clicked.connect(self._choose_dates)
        row.addWidget(_Field("Periode", self.date_button), 1)
        self.reset_date = QPushButton("Reset")
        self.reset_date.setProperty("variant", "ghost")
        self.reset_date.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_date.clicked.connect(self._reset_dates)
        self.reset_date.hide()
        row.addWidget(self.reset_date, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        if self.is_admin:
            self.bmkg_button = ThemedButton("BMKG Banjar", "outline", "plug-zap")
            self.bmkg_button.setToolTip("Perbarui data cuaca dari BMKG (Krandegan, Banjarnegara)")
            self.bmkg_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.bmkg_button.setMaximumWidth(120)
            self.bmkg_button.clicked.connect(self._update_from_bmkg)
            row.addWidget(self.bmkg_button, 0, Qt.AlignmentFlag.AlignBottom)
            self.import_button = ThemedButton("Import", "outline", "upload")
            self.import_button.clicked.connect(self._open_import)
            row.addWidget(self.import_button, 0, Qt.AlignmentFlag.AlignBottom)
        self.export_csv = ThemedButton("CSV", "ghost", "download", compact=True)
        self.export_csv.clicked.connect(lambda: self._export("csv"))
        row.addWidget(self.export_csv, 0, Qt.AlignmentFlag.AlignBottom)
        self.export_excel = ThemedButton("Excel", "outline", "file-spreadsheet")
        self.export_excel.clicked.connect(lambda: self._export("xlsx"))
        row.addWidget(self.export_excel, 0, Qt.AlignmentFlag.AlignBottom)
        if self.is_admin:
            self.add_button = ThemedButton("Tambah Data", "primary", "plus")
            self.add_button.clicked.connect(self._add_weather)
            row.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignBottom)
        filter_card.body.addLayout(row)
        self.body.addWidget(filter_card)

        self.tile_temperature = StatTile("Suhu rata-rata", "thermometer", "warning")
        self.tile_rainfall = StatTile("Curah hujan", "cloud-rain", "info")
        self.tile_humidity = StatTile("Kelembapan", "droplets", "accent")
        self.tile_days = StatTile("Hari tercatat", "calendar-days", "primary")
        self.body.addWidget(
            ResponsiveCardRow(
                [self.tile_temperature, self.tile_rainfall, self.tile_humidity, self.tile_days],
                spacing=12,
                min_width=232,
            )
        )

        chart_card = Card(padding=17, spacing=8)
        chart_action = QWidget()
        chart_layout = QHBoxLayout(chart_action)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(8)
        self.source_badge = Badge("NASA POWER", "info")
        chart_layout.addWidget(self.source_badge)
        self.week_segment = SegmentedControl([(12, "12 Pekan"), (26, "26 Pekan"), (52, "1 Tahun")], 12)
        self.week_segment.changed.connect(self._weeks_changed)
        chart_layout.addWidget(self.week_segment)
        chart_card.body.addWidget(
            SectionHeader(
                "Tren Cuaca Mingguan",
                "Rata-rata suhu dan kelembapan, total curah hujan per pekan.",
                "cloud-rain",
                chart_action,
            )
        )
        self.chart = WeatherChart(height=300)
        chart_card.body.addWidget(self.chart)
        source_row = QHBoxLayout()
        self.source_label = QLabel("Sumber: —")
        self.source_label.setObjectName("MutedSmall")
        source_row.addWidget(self.source_label)
        source_row.addStretch(1)
        self.updated_label = QLabel("")
        self.updated_label.setObjectName("MutedSmall")
        source_row.addWidget(self.updated_label)
        chart_card.body.addLayout(source_row)
        self.body.addWidget(chart_card)

        table_card = Card(padding=16, spacing=8)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(
            SectionHeader("Data Cuaca Harian", "Satu catatan per tanggal; data dipakai sebagai fitur model.", "calendar-days"),
            1,
        )
        self.count_label = QLabel("")
        self.count_label.setObjectName("MutedSmall")
        header.addWidget(self.count_label)
        table_card.body.addLayout(header)
        self.table = Table(["Tanggal", "Suhu", "Curah Hujan", "Kelembapan", "Sumber", "Aksi"])
        self.table.setMinimumHeight(410)
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().ResizeMode.Stretch)
        for column, width in ((1, 95), (2, 110), (3, 110), (4, 115), (5, 85)):
            self.table.setColumnWidth(column, width)
        header_item = self.table.horizontalHeaderItem(0)
        if header_item:
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.verticalHeader().setDefaultSectionSize(44)
        table_card.body.addWidget(self.table)
        pager = QHBoxLayout()
        pager.setSpacing(7)
        self.prev_button = ThemedButton("Sebelumnya", "outline", "chevron-left", compact=True)
        self.prev_button.clicked.connect(lambda: self._goto(self.page - 1))
        pager.addWidget(self.prev_button)
        self.page_label = QLabel("Halaman 1 dari 1")
        self.page_label.setObjectName("Muted")
        pager.addWidget(self.page_label)
        self.next_button = ThemedButton("Berikutnya", "outline", "chevron-right", compact=True)
        self.next_button.clicked.connect(lambda: self._goto(self.page + 1))
        pager.addWidget(self.next_button)
        pager.addSpacing(10)
        pager.addWidget(QLabel("Baris"))
        self.size_combo = QComboBox()
        for size in (15, 25, 50):
            self.size_combo.addItem(str(size), size)
        self.size_combo.currentIndexChanged.connect(self._size_changed)
        pager.addWidget(self.size_combo)
        pager.addStretch(1)
        self.reload_button = ThemedButton("Muat Ulang", "ghost", "refresh-cw", compact=True)
        self.reload_button.clicked.connect(self.load)
        pager.addWidget(self.reload_button)
        table_card.body.addLayout(pager)
        self.body.addWidget(table_card)
        self.body.addStretch(1)

    def on_show(self) -> None:
        super().on_show()
        self.load()
        self._bmkg_timer.start()

    def hideEvent(self, event) -> None:
        self._bmkg_timer.stop()
        super().hideEvent(event)

    def _on_bmkg_auto_update(self) -> None:
        if not self.is_admin or self._bmkg_busy or not self._bmkg_timer.isActive():
            return
        self._update_from_bmkg()

    def _search_changed(self) -> None:
        self.page = 1
        self.load()

    def _size_changed(self) -> None:
        self.page_size = int(self.size_combo.currentData() or 15)
        self.page = 1
        self.load()

    def _weeks_changed(self, weeks: Any) -> None:
        self.weeks = int(weeks)
        self._load_series()

    def _choose_dates(self) -> None:
        dialog = DateRangeDialog("Filter Periode Cuaca", self.start or None, self.end or None, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.start, self.end = dialog.values()
            self.date_button.setText(f"  {format_date(self.start)} – {format_date(self.end)}")
            self.reset_date.show()
            self.page = 1
            self.load()

    def _reset_dates(self) -> None:
        self.start = self.end = ""
        self.date_button.setText("  Semua periode")
        self.reset_date.hide()
        self.page = 1
        self.load()

    def _params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"page": self.page, "page_size": self.page_size}
        if self.search.text().strip():
            params["q"] = self.search.text().strip()
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end
        return params

    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat data cuaca...", "info")
        params = self._params()

        def task() -> dict:
            rows = self.api.get("/weather", params=params, timeout=45)
            summary = self.api.get("/weather/summary", params={"weeks": self.weeks}, timeout=45)
            return {"rows": rows, "summary": summary}

        self.runner.submit(
            task,
            lambda payload: self._apply(payload, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _load_series(self) -> None:
        self._serial += 1
        serial = self._serial
        self.runner.submit(
            lambda: self.api.get("/weather/summary", params={"weeks": self.weeks}, timeout=45),
            lambda summary: self._apply_summary(summary) if serial == self._serial else None,
            lambda message, status: self._failed(message, status, serial),
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._serial:
            self.notice.show_message(message, "danger")

    def _apply(self, payload: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.clear()
        rows = payload.get("rows", {})
        items = rows.get("items", [])
        self.total = rows.get("total", 0)
        self.pages = rows.get("pages", 1)
        self.page = rows.get("page", self.page)
        self.page_label.setText(f"Halaman {self.page} dari {self.pages}")
        self.prev_button.setEnabled(self.page > 1)
        self.next_button.setEnabled(self.page < self.pages)
        start_row = (self.page - 1) * self.page_size + 1 if self.total else 0
        end_row = min(self.page * self.page_size, self.total)
        self.count_label.setText(f"{start_row}–{end_row} / {number(self.total)} hari")
        self.table.setRowCount(0)
        self.table.clearSpans()
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.add_item(row, 0, format_date(item.get("weather_date")), bold=True)
            self.table.add_item(row, 1, f"{number(item.get('temperature'), 1)} °C")
            self.table.add_item(row, 2, f"{number(item.get('rainfall'), 1)} mm")
            self.table.add_item(row, 3, f"{number(item.get('humidity'), 1)} %")
            source_text = item.get("source") or "Manual"
            badge_text = "NASA POWER" if "NASA" in source_text else source_text
            badge = Badge(badge_text, "neutral")
            badge.setToolTip(source_text)
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 4, holder)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            if self.is_admin:
                edit = IconButton("pencil-line", "Ubah data cuaca", "primary", 28, 14, "ghost")
                edit.clicked.connect(lambda _checked=False, value=item: self._edit_weather(value))
                actions_layout.addWidget(edit)
                delete = IconButton("trash-2", "Hapus data cuaca", "danger", 28, 14, "ghost")
                delete.clicked.connect(lambda _checked=False, value=item: self._delete_weather(value))
                actions_layout.addWidget(delete)
            else:
                label = QLabel("—")
                label.setObjectName("MutedSmall")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                actions_layout.addWidget(label)
            self.table.setCellWidget(row, 5, actions)
        self._apply_summary(payload.get("summary", {}))

    def _apply_summary(self, summary: dict) -> None:
        self.tile_temperature.set_value(
            f"{number(summary.get('temperature'), 1)} °C",
            f"{self.weeks} pekan terakhir",
        )
        self.tile_rainfall.set_value(
            f"{number(summary.get('rainfall'), 1)} mm",
            f"akumulasi {self.weeks} pekan",
        )
        self.tile_humidity.set_value(
            f"{number(summary.get('humidity'), 1)} %",
            "rata-rata periode",
        )
        self.tile_days.set_value(
            number(summary.get("daily_count", 0)),
            "hari data harian",
        )
        self.chart.set_data(
            summary.get("labels", []),
            summary.get("temperature_series", []),
            summary.get("rainfall_series", []),
        )
        self.source_label.setText(f"Sumber data: {summary.get('source', '—')}")
        source_text = str(summary.get("source", ""))
        if "BMKG" in source_text:
            badge_text = "BMKG"
        elif "NASA" in source_text:
            badge_text = "NASA POWER"
        else:
            badge_text = "SUMBER DATA"
        self.source_badge.setText(badge_text)
        updated = summary.get("updated_at")
        self.updated_label.setText(
            f"Diperbarui {format_date(updated)} · {summary.get('daily_count', 0)} hari data harian"
            if updated
            else "Belum ada data cuaca"
        )

    def _goto(self, page: int) -> None:
        if 1 <= page <= self.pages and page != self.page:
            self.page = page
            self.load()

    def _add_weather(self) -> None:
        dialog = WeatherDialog(self.api, parent=self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Data cuaca ditambahkan.", "success")

    def _edit_weather(self, item: dict) -> None:
        dialog = WeatherDialog(self.api, item, self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Data cuaca diperbarui.", "success")

    def _delete_weather(self, item: dict) -> None:
        if not ConfirmDialog.ask(
            self,
            "Hapus data cuaca?",
            f"Catatan cuaca tanggal {format_date(item.get('weather_date'))} akan dihapus permanen.",
            "Hapus",
        ):
            return
        self.runner.submit(
            lambda: self.api.delete(f"/weather/{item['id']}", timeout=30),
            lambda _result: (self.toast("Data cuaca dihapus.", "success"), self.load()),
            lambda message, status: self.toast(message, "error"),
        )

    def _update_from_bmkg(self) -> None:
        self._serial += 1
        serial = self._serial
        self._bmkg_busy = True
        if self.is_admin and hasattr(self, "bmkg_button"):
            self.bmkg_button.setEnabled(False)
        self.notice.show_message("Memperbarui data cuaca BMKG Banjar...", "info")

        def task() -> dict:
            return self.api.post("/weather/bmkg/banjar", timeout=90)

        def done(result: dict) -> None:
            self._bmkg_busy = False
            if serial != self._serial:
                return
            if self.is_admin and hasattr(self, "bmkg_button"):
                self.bmkg_button.setEnabled(True)
            self.toast(
                result.get("message") or "Data cuaca BMKG Banjar diperbarui.",
                "success",
            )
            self.load()

        def failed(message: str, _status: int) -> None:
            self._bmkg_busy = False
            if serial == self._serial:
                if self.is_admin and hasattr(self, "bmkg_button"):
                    self.bmkg_button.setEnabled(True)
                self.notice.show_message(message, "danger")

        self.runner.submit(task, done, failed)

    def _open_import(self) -> None:
        dialog = ImportWizardDialog(self.api, "weather", self, on_done=self.load)
        dialog.exec()

    def _export(self, fmt: str) -> None:
        params = {}
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end
        params["fmt"] = fmt
        fallback = "Data_Cuaca.xlsx" if fmt == "xlsx" else "Data_Cuaca.csv"
        download_export(
            self,
            self.api,
            "/weather/export",
            fallback,
            params=params,
            file_filter="Excel (*.xlsx)" if fmt == "xlsx" else "CSV (*.csv)",
        )


class _Field(QWidget):
    def __init__(self, label: str, widget: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        text = QLabel(label)
        text.setObjectName("Hint")
        layout.addWidget(text)
        layout.addWidget(widget)
