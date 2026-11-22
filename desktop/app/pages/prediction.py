"""Halaman Prediksi Permintaan."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.charts import FeatureBars, ForecastChart, TrendChart
from app.components.dialogs import ConfirmDialog
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    Divider,
    Field,
    IconBox,
    InlineBanner,
    ResponsiveCardRow,
    SectionHeader,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.theme import theme
from app.core.utils import format_date, format_datetime, from_qdate, number, percent, safe_float
from app.pages.common import PageNotice, clear_layout, download_export


MODEL_LABELS = {
    "auto": "Otomatis (WAPE terkecil)",
    "random_forest": "Random Forest Regression",
    "decision_tree": "Decision Tree Regression",
    "linear_regression": "Linear Regression",
}

COMPACT_MODEL_LABELS = {
    "auto": "Otomatis",
    "random_forest": "RF",
    "decision_tree": "DT",
    "linear_regression": "LR",
}


class PredictionPage(PageBase):
    navigate = Signal(str)

    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self._options: list[dict] = []
        self._latest: dict | None = None
        self._serial = 0
        self._options_loaded = False
        self._running = False

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        controls = Card(padding=16, spacing=11)
        controls.body.addWidget(
            SectionHeader(
                "Prediksi Permintaan Obat",
                "Estimasi dari permintaan historis (stok opname + pembelian) dan cuaca. Model dipilih otomatis per obat berdasarkan WAPE terkecil.",
                "brain",
            )
        )
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.medicine_combo = QComboBox()
        self.medicine_combo.setMinimumWidth(280)
        self.medicine_combo.currentIndexChanged.connect(self._medicine_changed)
        top_row.addWidget(Field("Pilih obat", self.medicine_combo), 3)
        self.horizon_combo = QComboBox()
        for value in (1, 2, 4, 8, 12):
            self.horizon_combo.addItem(f"{value} pekan", value)
        self.horizon_combo.setCurrentIndex(2)
        top_row.addWidget(Field("Horizon", self.horizon_combo), 1)
        self.model_combo = QComboBox()
        for value, label in MODEL_LABELS.items():
            self.model_combo.addItem(label, value)
        top_row.addWidget(Field("Model", self.model_combo), 2)
        controls.body.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        self.auto_date = QCheckBox("Mulai otomatis dari pekan setelah data terakhir")
        self.auto_date.setChecked(True)
        self.auto_date.toggled.connect(self._auto_date_toggled)
        bottom_row.addWidget(self.auto_date)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setDate(QDate.currentDate().addDays(1))
        self.start_date.setEnabled(False)
        self.start_field = Field("Tanggal mulai (opsional)", self.start_date)
        self.start_field.setVisible(False)
        bottom_row.addWidget(self.start_field)
        bottom_row.addStretch(1)
        if str(self.user.get("role", "")).lower() == "admin":
            self.train_button = ThemedButton("Latih Ulang Semua", "outline", "cpu")
            self.train_button.setToolTip("Latih ulang model seluruh obat aktif (Admin)")
            self.train_button.clicked.connect(self._train_all)
            bottom_row.addWidget(self.train_button)
        self.run_button = ThemedButton("Jalankan Analisis", "primary", "play")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self._run_prediction)
        bottom_row.addWidget(self.run_button)
        controls.body.addLayout(bottom_row)
        self.body.addWidget(controls)

        self.stat_average = StatTile("Permintaan rata-rata", "chart-column", "primary")
        self.stat_forecast = StatTile("Total prakiraan", "trending-up", "accent")
        self.stat_mape = StatTile("Rata-rata error", "target", "warning")
        self.stat_accuracy = StatTile("Akurasi prediksi", "badge-check", "info")
        self.stat_mape.setToolTip(
            "WAPE: rata-rata persentase selisih prakiraan terhadap permintaan aktual. "
            "Semakin kecil nilainya, semakin akurat prediksi."
        )
        self.stat_accuracy.setToolTip(
            "Perkiraan akurasi = 100% dikurangi WAPE. Angka ini indikatif, bukan jaminan permintaan nyata."
        )
        self.body.addWidget(
            ResponsiveCardRow(
                [self.stat_average, self.stat_forecast, self.stat_mape, self.stat_accuracy],
                spacing=12,
                min_width=232,
            )
        )
        self.metric_help = QLabel(
            "WAPE mengukur rata-rata selisih prakiraan terhadap permintaan aktual; semakin kecil, "
            "semakin akurat. MAE dan RMSE adalah ukuran selisih dalam unit obat."
        )
        self.metric_help.setObjectName("MutedSmall")
        self.metric_help.setWordWrap(True)
        self.body.addWidget(self.metric_help)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(14)
        chart_card = Card(padding=17, spacing=8)
        chart_header = QHBoxLayout()
        chart_header.setContentsMargins(0, 0, 0, 0)
        chart_header.addWidget(
            SectionHeader("Grafik Aktual & Prakiraan", "Garis putus-putus adalah estimasi model; area menunjukkan interval keyakinan.", "chart-column"),
            1,
        )
        chart_card.body.addLayout(chart_header)
        self.forecast_chart = ForecastChart(height=300)
        chart_card.body.addWidget(self.forecast_chart, 1)
        chart_row.addWidget(chart_card, 7)

        info_card = Card(padding=17, spacing=8)
        info_card.body.addWidget(SectionHeader("Informasi Model", "Model dan evaluasi data uji kronologis.", "cpu"))
        self.info_box = QVBoxLayout()
        self.info_box.setSpacing(0)
        self.info_labels: dict[str, QLabel] = {}
        for key, label in (
            ("medicine", "Obat"),
            ("model", "Model"),
            ("train", "Periode latih"),
            ("sizes", "Data latih / uji"),
            ("metrics", "MAE / RMSE"),
            ("mape", "WAPE / MAPE"),
            ("horizon", "Horizon"),
            ("created", "Dibuat"),
        ):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 6, 0, 6)
            row_layout.setSpacing(8)
            key_label = QLabel(label)
            key_label.setObjectName("Muted")
            key_label.setMinimumWidth(84)
            row_layout.addWidget(key_label)
            value = QLabel("—")
            value.setWordWrap(True)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value.setStyleSheet("font-size: 12px; font-weight: 600;")
            tooltips = {
                "metrics": "MAE: rata-rata selisih absolut. RMSE: akar rata-rata kuadrat selisih. Semakin kecil, semakin akurat.",
                "mape": "WAPE lebih stabil daripada MAPE saat permintaan mingguan rendah. Semakin kecil, semakin akurat.",
            }
            if key in tooltips:
                key_label.setToolTip(tooltips[key])
                value.setToolTip(tooltips[key])
            row_layout.addWidget(value, 1)
            self.info_box.addWidget(row)
            if key != "created":
                divider = QFrame()
                divider.setFixedHeight(1)
                divider.setStyleSheet(f"background: {theme.tokens['border']};")
                self.info_box.addWidget(divider)
            self.info_labels[key] = value
        info_card.body.addLayout(self.info_box)
        demo_row = QHBoxLayout()
        self.model_badge = Badge("MODEL AKTUAL", "success")
        demo_row.addWidget(self.model_badge)
        demo_row.addStretch(1)
        self.info_note = QLabel("Bukan jaminan permintaan nyata")
        self.info_note.setObjectName("MutedSmall")
        demo_row.addWidget(self.info_note)
        info_card.body.addLayout(demo_row)
        chart_row.addWidget(info_card, 3)
        self.body.addLayout(chart_row)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(14)
        forecast_card = Card(padding=17, spacing=8)
        export_row = QWidget()
        export_layout = QHBoxLayout(export_row)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.setSpacing(5)
        for fmt, label, icon_name in (("pdf", "PDF", "file-text"), ("xlsx", "Excel", "file-spreadsheet"), ("csv", "CSV", "download")):
            button = ThemedButton(label, "ghost", icon_name, compact=True)
            button.clicked.connect(lambda _checked=False, value=fmt: self._export(value))
            export_layout.addWidget(button)
        forecast_card.body.addWidget(
            SectionHeader("Rincian Prakiraan", "Nilai per pekan beserta rentang estimasi.", "calendar-days", export_row)
        )
        self.forecast_table = Table(["Pekan", "Tanggal", "Prediksi", "Min", "Maks"])
        self.forecast_table.setMinimumHeight(230)
        self.forecast_table.horizontalHeader().setSectionResizeMode(1, self.forecast_table.horizontalHeader().ResizeMode.Stretch)
        for column, width in ((0, 70), (2, 100), (3, 68), (4, 68)):
            self.forecast_table.setColumnWidth(column, width)
        for column in (0, 1):
            item = self.forecast_table.horizontalHeaderItem(column)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.forecast_table.verticalHeader().setDefaultSectionSize(40)
        forecast_card.body.addWidget(self.forecast_table)
        detail_row.addWidget(forecast_card, 3)

        feature_card = Card(padding=17, spacing=8)
        feature_card.body.addWidget(
            SectionHeader("Kepentingan Fitur", "Kontribusi relatif fitur pada model terbaru.", "scan-line")
        )
        self.features = FeatureBars()
        feature_card.body.addWidget(self.features)
        self.feature_note = QLabel("Fitur cuaca dan musiman membantu model menangkap pola permintaan.")
        self.feature_note.setObjectName("MutedSmall")
        self.feature_note.setWordWrap(True)
        feature_card.body.addWidget(self.feature_note)
        feature_card.body.addStretch(1)
        detail_row.addWidget(feature_card, 2)
        self.body.addLayout(detail_row)

        eval_row = QHBoxLayout()
        eval_row.setSpacing(14)
        backtest_card = Card(padding=17, spacing=8)
        backtest_card.body.addWidget(
            SectionHeader("Backtest Model", "Perbandingan aktual dan prediksi pada data uji kronologis.", "history")
        )
        self.backtest_chart = TrendChart(height=250, actual_label="Aktual", predicted_label="Prediksi")
        backtest_card.body.addWidget(self.backtest_chart)
        eval_row.addWidget(backtest_card, 3)

        comparison_card = Card(padding=17, spacing=8)
        comparison_card.body.addWidget(
            SectionHeader("Perbandingan Algoritma", "Metrik evaluasi model untuk obat yang dipilih.", "cpu")
        )
        self.comparison_table = Table(["Model", "MAE", "RMSE", "WAPE"])
        self.comparison_table.setMinimumHeight(190)
        comparison_header = self.comparison_table.horizontalHeader()
        comparison_header.setSectionResizeMode(0, comparison_header.ResizeMode.Stretch)
        for column in (1, 2, 3):
            comparison_header.setSectionResizeMode(column, comparison_header.ResizeMode.ResizeToContents)
        self.comparison_table.verticalHeader().setDefaultSectionSize(40)
        comparison_card.body.addWidget(self.comparison_table)
        self.comparison_note = QLabel(
            "WAPE = total selisih dibagi total permintaan aktual; lebih stabil daripada MAPE saat "
            "permintaan mingguan rendah. Metrik lebih kecil lebih baik. Angka hijau adalah WAPE terkecil "
            "pada data uji; baris tebal adalah model yang dipakai saat ini. "
            "RF = Random Forest, DT = Decision Tree, LR = Linear Regression."
        )
        self.comparison_note.setObjectName("MutedSmall")
        self.comparison_note.setWordWrap(True)
        comparison_card.body.addWidget(self.comparison_note)
        eval_row.addWidget(comparison_card, 2)
        self.body.addLayout(eval_row)

        history_card = Card(padding=17, spacing=8)
        history_card.body.addWidget(
            SectionHeader("Riwayat Prediksi", "Hasil analisis terakhir yang tersimpan untuk seluruh obat.", "history")
        )
        self.history_table = Table(["Waktu", "Obat", "Model", "Horizon", "WAPE", "Status"])
        self.history_table.setMinimumHeight(240)
        self.history_table.horizontalHeader().setSectionResizeMode(1, self.history_table.horizontalHeader().ResizeMode.Stretch)
        for column, width in ((0, 170), (2, 196), (3, 86), (4, 82), (5, 96)):
            self.history_table.setColumnWidth(column, width)
        for column in (0, 1):
            item = self.history_table.horizontalHeaderItem(column)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        history_card.body.addWidget(self.history_table)
        self.body.addWidget(history_card)
        self.body.addStretch(1)

    def on_show(self) -> None:
        if not self._options_loaded:
            self._load_options()
        else:
            self._load_medicine(self._current_medicine_id())

    def _current_medicine_id(self) -> int | None:
        data = self.medicine_combo.currentData()
        return int(data["id"]) if data else None

    def _load_options(self) -> None:
        self.notice.show_message("Memuat daftar obat...", "info")
        self.runner.submit(
            lambda: self.api.get("/predictions/options", timeout=30),
            self._options_ready,
            lambda message, status: self.notice.show_message(message, "danger"),
        )

    def _options_ready(self, options: list) -> None:
        self._options = options or []
        self._options_loaded = True
        self.medicine_combo.blockSignals(True)
        self.medicine_combo.clear()
        for item in self._options:
            marker = "★ " if item.get("is_priority") else ""
            self.medicine_combo.addItem(f"{marker}{item.get('name', '-')}  ·  {item.get('unit', '')}", item)
        self.medicine_combo.blockSignals(False)
        if self._options:
            priority = next((index for index, item in enumerate(self._options) if item.get("is_priority")), 0)
            self.medicine_combo.setCurrentIndex(priority)
        self._load_medicine(self._current_medicine_id())

    def _medicine_changed(self) -> None:
        if self._options_loaded:
            self._load_medicine(self._current_medicine_id())

    def _auto_date_toggled(self, checked: bool) -> None:
        self.start_date.setEnabled(not checked)
        self.start_field.setVisible(not checked)

    def _load_medicine(self, medicine_id: int | None) -> None:
        if not medicine_id:
            return
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat hasil prediksi...", "info")
        self.run_button.setEnabled(False)

        def task() -> dict:
            latest = self.api.get("/predictions/latest", params={"medicine_id": medicine_id}, timeout=45)
            series = self.api.get("/predictions/series", params={"medicine_id": medicine_id, "weeks": 52}, timeout=45)
            history = self.api.get("/predictions/history", params={"medicine_id": medicine_id, "limit": 10}, timeout=30)
            return {"latest": latest, "series": series, "history": history, "medicine_id": medicine_id}

        self.runner.submit(
            task,
            lambda payload: self._apply(payload, serial),
            lambda message, status: self._failed(message, status, serial),
            lambda: self.run_button.setEnabled(True) if serial == self._serial else None,
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.show_message(message, "danger")

    def _apply(self, payload: dict, serial: int) -> None:
        if serial != self._serial:
            return
        medicine_id = payload.get("medicine_id")
        if medicine_id != self._current_medicine_id():
            return
        self.notice.clear()
        latest = payload.get("latest") or {}
        series = payload.get("series") or {}
        history = payload.get("history") or []
        self._render_history(history)
        if not latest.get("available"):
            self._latest = None
            self.notice.show_message(
                latest.get("message", "Belum ada hasil prediksi untuk obat ini. Jalankan analisis terlebih dahulu."),
                "info",
            )
            self.forecast_chart.set_data([], [], [])
            self.forecast_table.setRowCount(0)
            self.backtest_chart.set_data([], [], [])
            self.features.set_items([])
            self.comparison_table.setRowCount(0)
            for tile in (self.stat_average, self.stat_forecast, self.stat_mape, self.stat_accuracy):
                tile.set_value("—")
            for label in self.info_labels.values():
                label.setText("—")
            self.horizon_combo.setCurrentIndex(2)
            return
        self._latest = latest
        if latest.get("start_date"):
            parsed = QDate.fromString(str(latest.get("start_date")), "yyyy-MM-dd")
            if parsed.isValid():
                self.start_date.setDate(parsed)
        self.model_badge.setText("MODEL AKTUAL")
        self.model_badge.set_tone("success")
        medicine = latest.get("medicine", {})
        unit = medicine.get("unit", "unit")
        forecast = latest.get("forecast", [])
        total = sum(safe_float(item.get("predicted")) for item in forecast)
        metrics = latest.get("metrics", {}) or {}
        model_name = latest.get("model_name", "random_forest")
        requested_model = (latest.get("params") or {}).get("requested_model", model_name)
        model_metric = metrics.get(model_name, {}) or {}
        wape = model_metric.get("wape")
        accuracy = model_metric.get("accuracy_indikatif")
        average = safe_float(series.get("average")) if series.get("available") else None
        self.stat_average.set_value(
            f"{number(average)} {unit}" if average is not None else "—",
            f"{series.get('active_weeks', 0)} pekan aktif",
        )
        self.stat_forecast.set_value(
            f"{number(total)} {unit}",
            f"{latest.get('horizon_weeks', 4)} pekan mulai {format_date(latest.get('start_date'))}",
        )
        self.stat_mape.set_value(
            percent(wape, 2),
            f"MAE {number(model_metric.get('mae'), 2)} · RMSE {number(model_metric.get('rmse'), 2)}",
        )
        self.stat_accuracy.set_value(
            percent(accuracy, 2),
            "100% − WAPE",
        )
        self.horizon_combo.blockSignals(True)
        index = self.horizon_combo.findData(latest.get("horizon_weeks", 4))
        if index >= 0:
            self.horizon_combo.setCurrentIndex(index)
        self.horizon_combo.blockSignals(False)
        model_index = self.model_combo.findData(requested_model)
        if model_index >= 0:
            self.model_combo.blockSignals(True)
            self.model_combo.setCurrentIndex(model_index)
            self.model_combo.blockSignals(False)

        history_points = series.get("history", []) if series.get("available") else []
        history_points = history_points[-16:]
        labels = [format_date(item.get("week"), with_year=False) for item in history_points]
        values = [safe_float(item.get("demand")) for item in history_points]
        forecast_labels = [format_date(item.get("date"), with_year=False) for item in forecast]
        self.forecast_chart.set_data(
            labels + forecast_labels,
            values,
            [safe_float(item.get("predicted")) for item in forecast],
            [safe_float(item.get("lower_bound")) for item in forecast],
            [safe_float(item.get("upper_bound")) for item in forecast],
        )
        self._fill_forecast_table(forecast, unit)
        self.features.set_items(
            [(item.get("label", item.get("feature", "")), safe_float(item.get("importance"))) for item in (latest.get("feature_importance") or [])[:9]]
        )
        self.feature_note.setText(
            "Kontribusi fitur dari model terbaru. Cuaca dan pola musiman dapat memengaruhi permintaan."
        )
        for key, value in (
            ("medicine", medicine.get("name", "-")),
            (
                "model",
                latest.get("model_label", MODEL_LABELS.get(model_name, model_name))
                + (" · dipilih otomatis" if requested_model == "auto" else ""),
            ),
            ("train", f"{format_date(latest.get('train_start'))} – {format_date(latest.get('train_end'))}"),
            ("sizes", f"{number(latest.get('train_size'))} / {number(latest.get('test_size'))} baris"),
            ("metrics", f"{number(model_metric.get('mae'), 2)} / {number(model_metric.get('rmse'), 2)} {unit}"),
            ("mape", f"{percent(wape, 2)} / {percent(model_metric.get('mape'), 2)}"),
            ("horizon", f"{latest.get('horizon_weeks', 4)} pekan"),
            ("created", format_datetime(latest.get("created_at"))),
        ):
            self.info_labels[key].setText(str(value))
        self._fill_backtest(latest.get("backtest", []))
        self._fill_comparison(metrics, model_name)
        if series.get("available") and not series.get("history"):
            self.notice.show_message("Data historis belum tersedia untuk obat ini.", "warning")

    def _fill_forecast_table(self, forecast: list[dict], unit: str) -> None:
        self.forecast_table.setRowCount(len(forecast))
        for row, item in enumerate(forecast):
            self.forecast_table.add_item(row, 0, f"Pekan {item.get('week_number', row + 1)}", bold=True)
            self.forecast_table.add_item(row, 1, format_date(item.get("date")))
            self.forecast_table.add_item(row, 2, f"{number(item.get('predicted'))} {unit}", Qt.AlignmentFlag.AlignRight, color=theme.tokens["primary"], bold=True)
            self.forecast_table.add_item(row, 3, number(item.get("lower_bound")), Qt.AlignmentFlag.AlignRight)
            self.forecast_table.add_item(row, 4, number(item.get("upper_bound")), Qt.AlignmentFlag.AlignRight)

    def _fill_backtest(self, backtest: list[dict]) -> None:
        rows = backtest[-20:]
        labels = [format_date(item.get("week"), with_year=False) for item in rows]
        actual = [safe_float(item.get("actual")) for item in rows]
        predicted = [safe_float(item.get("predicted")) for item in rows]
        self.backtest_chart.set_data(labels, actual, predicted)

    def _fill_comparison(self, metrics: dict, active_model: str) -> None:
        rows = []
        for name in ("random_forest", "decision_tree", "linear_regression"):
            if name not in metrics:
                continue
            values = metrics[name]
            rows.append((name, values))
        best = min((values.get("wape") for _name, values in rows if values.get("wape") is not None), default=None)
        self.comparison_table.setRowCount(len(rows))
        for index, (name, values) in enumerate(rows):
            label = COMPACT_MODEL_LABELS.get(name, MODEL_LABELS.get(name, name))
            if name == active_model:
                label += "  ★"
            wape = values.get("wape")
            tone = theme.tokens["success"] if wape == best else theme.tokens["text_soft"]
            item = self.comparison_table.add_item(index, 0, label, bold=name == active_model)
            item.setToolTip(MODEL_LABELS.get(name, name))
            self.comparison_table.add_item(index, 1, number(values.get("mae"), 2), Qt.AlignmentFlag.AlignRight)
            self.comparison_table.add_item(index, 2, number(values.get("rmse"), 2), Qt.AlignmentFlag.AlignRight)
            self.comparison_table.add_item(index, 3, percent(wape, 2), Qt.AlignmentFlag.AlignRight, color=tone, bold=wape == best)

    def _render_history(self, rows: list[dict]) -> None:
        self.history_table.setRowCount(len(rows))
        for index, run in enumerate(rows):
            metrics = run.get("metrics") or {}
            model_metric = metrics.get(run.get("model_name"), {}) or {}
            self.history_table.add_item(index, 0, format_datetime(run.get("created_at")))
            self.history_table.add_item(index, 1, run.get("medicine_name", "-"))
            self.history_table.add_item(index, 2, run.get("model_label", "-"))
            self.history_table.add_item(index, 3, f"{run.get('horizon_weeks', '-')} pekan")
            self.history_table.add_item(index, 4, percent(model_metric.get("wape"), 2), Qt.AlignmentFlag.AlignRight)
            status = str(run.get("status", "-")).lower()
            status_label = {"completed": "Selesai", "failed": "Gagal", "running": "Diproses"}.get(status, status.title())
            self.history_table.add_item(index, 5, status_label)

    def _run_prediction(self) -> None:
        medicine = self.medicine_combo.currentData()
        if not medicine:
            self.toast("Pilih obat terlebih dahulu.", "error")
            return
        payload = {
            "medicine_id": int(medicine["id"]),
            "horizon_weeks": int(self.horizon_combo.currentData() or 4),
            "model_name": self.model_combo.currentData() or "random_forest",
            "save": True,
        }
        if not self.auto_date.isChecked():
            payload["start_date"] = from_qdate(self.start_date.date())
        self.run_button.start_loading("Menganalisis...")
        self.notice.show_message("Menjalankan model prediksi...", "info")
        self.runner.submit(
            lambda: self.api.post("/predictions/run", payload, timeout=180),
            self._run_done,
            self._run_failed,
            self.run_button.stop_loading,
        )

    def _run_done(self, result: dict) -> None:
        self.toast(
            f"Prediksi {result.get('medicine', {}).get('name', 'obat')} berhasil dibuat.",
            "success",
        )
        self._load_medicine(self._current_medicine_id())
        if hasattr(self, "train_button"):
            self.train_button.stop_loading() if hasattr(self.train_button, "stop_loading") else None

    def _run_failed(self, message: str, _status: int) -> None:
        self.notice.show_message(message, "danger")
        self.toast(message, "error")

    def _train_all(self) -> None:
        if not ConfirmDialog.ask(
            self,
            "Latih ulang seluruh model?",
            "Proses ini melatih ulang model prediksi untuk seluruh obat aktif dan dapat memakan waktu. Data prediksi lama tetap tersimpan.",
            "Ya, latih ulang",
            danger=False,
        ):
            return
        self.train_button.start_loading("Melatih...")
        self.notice.show_message("Melatih ulang model seluruh obat...", "info")
        self.runner.submit(
            lambda: self.api.post("/predictions/train-all", timeout=600),
            self._train_done,
            self._train_failed,
            self.train_button.stop_loading,
        )

    def _train_done(self, result: dict) -> None:
        self.notice.show_message(result.get("message", "Pelatihan selesai."), "success")
        self.toast(result.get("message", "Pelatihan selesai."), "success")
        self._load_medicine(self._current_medicine_id())

    def _train_failed(self, message: str, _status: int) -> None:
        self.notice.show_message(message, "danger")
        self.toast(message, "error")

    def _export(self, fmt: str) -> None:
        if not self._latest:
            self.toast("Belum ada hasil prediksi untuk diekspor.", "error")
            return
        run_id = self._latest.get("run_id")
        medicine = self._latest.get("medicine", {})
        code = medicine.get("code", "obat")
        filters = {
            "pdf": ("PDF (*.pdf)", "pdf"),
            "xlsx": ("Excel (*.xlsx)", "xlsx"),
            "csv": ("CSV (*.csv)", "csv"),
        }[fmt]
        download_export(
            self,
            self.api,
            f"/predictions/{run_id}/export",
            f"Prediksi_{code}.{filters[1]}",
            params={"fmt": fmt},
            file_filter=filters[0],
        )
