"""Halaman Rekomendasi Pengadaan."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import ConfirmDialog, FormDialog, ProcurementEditDialog
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    Divider,
    ElidedLabel,
    EmptyState,
    IconBox,
    IconButton,
    InlineBanner,
    ResponsiveCardRow,
    SectionHeader,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.theme import theme
from app.core.utils import format_date, format_datetime, number, rupiah, urgency_label
from app.pages.common import PageNotice, clear_layout, download_export


URGENCY_TONES = {
    "kritis": "danger",
    "tinggi": "warning",
    "sedang": "info",
    "rendah": "success",
}


class GenerateDialog(FormDialog):
    def __init__(self, api, parent=None, on_saved=None) -> None:
        self.api = api
        self.on_saved = on_saved
        super().__init__(
            "Buat Rekomendasi Pengadaan",
            "Sistem menghitung usulan pembelian dari prakiraan permintaan, stok fisik, stok pengaman, dan waktu tunggu (lead time).",
            "clipboard-list",
            parent,
            width=500,
            save_text="Hitung Rekomendasi",
        )
        self.period = QComboBox()
        for value in (2, 4, 8, 12):
            self.period.addItem(f"{value} pekan", value)
        self.period.setCurrentIndex(1)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Catatan pengadaan (opsional)")
        self.notes.setFixedHeight(80)
        self.field("Periode pengadaan", self.period, required=True)
        self.field("Catatan", self.notes)
        self.note(
            "Angka rekomendasi bersifat usulan, bukan keputusan otomatis. Admin dapat menyesuaikan jumlah dengan alasan.",
            "info",
        )
        self.bind_save(self._generate)

    def _generate(self) -> bool:
        payload = {
            "period_weeks": int(self.period.currentData() or 4),
            "notes": self.notes.toPlainText().strip() or None,
        }
        self.set_busy(True)

        def task() -> Any:
            return self.api.post("/procurement/generate", payload, timeout=180)

        def ok(result: Any) -> None:
            if self.on_saved:
                self.on_saved(result)

        self._submit_async(task, ok)
        return False


class ItemDetailDialog(QDialog):
    def __init__(self, item: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Detail Item Pengadaan")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(IconBox("clipboard-list", "primary", "primary_soft", 38, 18))
        text = QVBoxLayout()
        text.setSpacing(2)
        title = QLabel(item.get("name", "Obat"))
        title.setStyleSheet("font-size: 17px; font-weight: 800;")
        text.addWidget(title)
        subtitle = QLabel(f"{item.get('code', '')} · {item.get('category', '')} · {item.get('unit', '')}")
        subtitle.setObjectName("Muted")
        text.addWidget(subtitle)
        head.addLayout(text, 1)
        head.addWidget(Badge(urgency_label(item.get("urgency")), URGENCY_TONES.get(item.get("urgency", ""), "neutral")))
        layout.addLayout(head)
        layout.addWidget(Divider(self))
        grid = QHBoxLayout()
        grid.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(7)
        for label, value in (
            ("Stok fisik", f"{number(item.get('current_stock'))} {item.get('unit', '')}"),
            ("Minimum stok", number(item.get("min_stock"))),
            ("Prakiraan kebutuhan", f"{number(item.get('predicted_demand'), 2)} {item.get('unit', '')}"),
            ("Stok pengaman", number(item.get("safety_stock"))),
        ):
            left.addLayout(self._row(label, value))
        right = QVBoxLayout()
        right.setSpacing(7)
        for label, value in (
            ("Saran sistem", f"{number(item.get('recommended_qty'))} {item.get('unit', '')}"),
            ("Jumlah final", f"{number(item.get('final_qty'))} {item.get('unit', '')}"),
            ("Harga beli satuan", rupiah(item.get("unit_price"))),
            ("Subtotal", rupiah(item.get("subtotal"))),
        ):
            right.addLayout(self._row(label, value, bold=label in {"Jumlah final", "Subtotal"}))
        grid.addLayout(left, 1)
        grid.addLayout(right, 1)
        layout.addLayout(grid)
        reason_title = QLabel("Perhitungan transparan")
        reason_title.setStyleSheet("font-size: 13px; font-weight: 800;")
        layout.addWidget(reason_title)
        reason = QLabel(item.get("reason", "—"))
        reason.setObjectName("Muted")
        reason.setWordWrap(True)
        layout.addWidget(reason)
        if item.get("adjustment_reason"):
            adjust_title = QLabel("Alasan penyesuaian Admin")
            adjust_title.setStyleSheet("font-size: 13px; font-weight: 800;")
            layout.addWidget(adjust_title)
            adjustment = QLabel(item.get("adjustment_reason", ""))
            adjustment.setWordWrap(True)
            adjustment.setStyleSheet(
                f"background: {theme.tokens['warning_bg']}; color: {theme.tokens['warning_text']};"
                "border-radius: 9px; padding: 9px 11px; font-size: 12px;"
            )
            layout.addWidget(adjustment)
        footer = QHBoxLayout()
        footer.addStretch(1)
        close = ThemedButton("Tutup", "outline")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        layout.addLayout(footer)

    @staticmethod
    def _row(label: str, value: str, bold: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        key = QLabel(label)
        key.setObjectName("Muted")
        row.addWidget(key)
        row.addStretch(1)
        val = QLabel(str(value))
        val.setStyleSheet("font-size: 12px; font-weight: 800;" if bold else "font-size: 12px; font-weight: 600;")
        row.addWidget(val)
        return row


class ProcurementPage(PageBase):
    def __init__(self, api, runner, user: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.runner = runner
        self.user = user
        self.is_admin = str(user.get("role", "")).lower() == "admin"
        self._serial = 0
        self._current: dict | None = None
        self._history: list[dict] = []
        self._selected_id: int | None = None

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        header = Card(padding=16, spacing=10)
        head_row = QHBoxLayout()
        head_row.setContentsMargins(0, 0, 0, 0)
        head_row.addWidget(
            SectionHeader(
                "Rekomendasi Pengadaan",
                "Usulan pembelian berbasis prakiraan permintaan dan kondisi stok terkini.",
                "clipboard-list",
            ),
            1,
        )
        self.generate_button = ThemedButton("Buat Rekomendasi", "primary", "plus")
        self.generate_button.clicked.connect(self._generate)
        head_row.addWidget(self.generate_button)
        header.body.addLayout(head_row)
        self.assumption_banner = InlineBanner("", "info")
        header.body.addWidget(self.assumption_banner)
        self.body.addWidget(header)

        self.tile_status = StatTile("Status rekomendasi", "badge-check", "primary")
        self.tile_period = StatTile("Periode pengadaan", "calendar-days", "info")
        self.tile_items = StatTile("Jumlah item", "boxes", "accent")
        self.tile_cost = StatTile("Estimasi biaya", "wallet", "warning")
        self.stats_row = ResponsiveCardRow(
            [self.tile_status, self.tile_period, self.tile_items, self.tile_cost],
            spacing=12,
            min_width=232,
        )
        self.body.addWidget(self.stats_row)

        self.detail_card = Card(padding=16, spacing=9)
        detail_head = QVBoxLayout()
        detail_head.setContentsMargins(0, 0, 0, 0)
        detail_head.setSpacing(8)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_block = QVBoxLayout()
        title_block.setSpacing(1)
        self.detail_title = QLabel("Rekomendasi Terbaru")
        self.detail_title.setObjectName("SectionTitle")
        title_block.addWidget(self.detail_title)
        self.detail_subtitle = QLabel("Memuat rekomendasi...")
        self.detail_subtitle.setObjectName("SectionSubtitle")
        title_block.addWidget(self.detail_subtitle)
        title_row.addLayout(title_block, 1)
        self.status_badge = Badge("—", "neutral")
        title_row.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignTop)
        detail_head.addLayout(title_row)

        # Tombol aksi dipisah ke baris sendiri agar header tidak memaksa
        # halaman melebar pada ukuran jendela minimum.
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.addStretch(1)
        self.export_pdf = ThemedButton("PDF", "ghost", "file-text", compact=True)
        self.export_pdf.clicked.connect(lambda: self._export("pdf"))
        action_row.addWidget(self.export_pdf)
        self.export_excel = ThemedButton("Excel", "ghost", "file-spreadsheet", compact=True)
        self.export_excel.clicked.connect(lambda: self._export("xlsx"))
        action_row.addWidget(self.export_excel)
        self.export_csv = ThemedButton("CSV", "ghost", "download", compact=True)
        self.export_csv.clicked.connect(lambda: self._export("csv"))
        action_row.addWidget(self.export_csv)
        action_row.addSpacing(6)
        self.cancel_button = ThemedButton("Batalkan", "outline", "x")
        self.cancel_button.clicked.connect(self._cancel)
        self.cancel_button.setVisible(self.is_admin)
        action_row.addWidget(self.cancel_button)
        self.approve_button = ThemedButton("Setujui", "primary", "check")
        self.approve_button.clicked.connect(self._approve)
        self.approve_button.setVisible(self.is_admin)
        action_row.addWidget(self.approve_button)
        detail_head.addLayout(action_row)
        detail_card_head = detail_head
        self.detail_card.body.addLayout(detail_card_head)
        self.table = Table(
            [
                "Nama Obat",
                "Stok",
                "Prediksi",
                "Aman",
                "Usulan",
                "Final",
                "Subtotal",
                "Urgensi",
                "Aksi",
            ]
        )
        self.table.setMinimumHeight(430)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in ((1, 60), (2, 76), (3, 58), (4, 64), (5, 62), (6, 114), (7, 76), (8, 78)):
            self.table.setColumnWidth(column, width)
        item = self.table.horizontalHeaderItem(0)
        if item:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.itemDoubleClicked.connect(lambda _item: self._detail_selected())
        self.detail_card.body.addWidget(self.table)
        self.detail_footer = QLabel("")
        self.detail_footer.setObjectName("MutedSmall")
        self.detail_footer.setWordWrap(True)
        self.detail_card.body.addWidget(self.detail_footer)
        self.body.addWidget(self.detail_card)

        self.empty_card = Card(padding=16, spacing=10)
        self.empty_holder = QVBoxLayout()
        self.empty_holder.setSpacing(8)
        self.empty_card.body.addLayout(self.empty_holder)
        self.body.addWidget(self.empty_card)

        self.history_card = Card(padding=16, spacing=8)
        history_head = QHBoxLayout()
        history_head.setContentsMargins(0, 0, 0, 0)
        history_head.addWidget(
            SectionHeader(
                "Riwayat Rekomendasi",
                "Buka rekomendasi sebelumnya untuk melihat rincian atau mengekspor dokumen.",
                "history",
            ),
            1,
        )
        self.refresh_button = ThemedButton("Muat Ulang", "ghost", "refresh-cw", compact=True)
        self.refresh_button.clicked.connect(self.load)
        history_head.addWidget(self.refresh_button)
        self.history_card.body.addLayout(history_head)
        self.history_table = Table(["Kode", "Dibuat", "Periode", "Status", "Item", "Estimasi Biaya", "Aksi"])
        self.history_table.setMinimumHeight(220)
        history_header = self.history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        history_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for column, width in ((2, 100), (3, 108), (4, 64), (5, 140), (6, 92)):
            self.history_table.setColumnWidth(column, width)
        for column in (0, 1):
            item = self.history_table.horizontalHeaderItem(column)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        self.history_card.body.addWidget(self.history_table)
        self.body.addWidget(self.history_card)
        self.body.addStretch(1)

        self.approve_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self.load()

    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat rekomendasi pengadaan...", "info")
        if self._selected_id:
            self.runner.submit(
                lambda: self.api.get(f"/procurement/{self._selected_id}", timeout=45),
                lambda data: self._apply_selected(data, serial),
                lambda message, status: self._failed(message, status, serial),
            )
            return
        self.runner.submit(
            lambda: (
                self.api.get("/procurement/latest", timeout=45),
                self.api.get("/procurement", timeout=45),
            ),
            lambda payload: self._apply(payload[0], payload[1], serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _apply_selected(self, data: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.clear()
        self._current = data
        self._selected_id = data.get("id")
        self._show_detail(data)
        self._refresh_history()

    def _refresh_history(self) -> None:
        self._serial += 1
        serial = self._serial
        self.runner.submit(
            lambda: self.api.get("/procurement", timeout=45),
            lambda history: self._history_ready(history, serial),
            lambda _message, _status: None,
        )

    def _history_ready(self, history: list, serial: int) -> None:
        if serial != self._serial:
            return
        self._history = history or []
        self._render_history()

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._serial:
            self.notice.show_message(message, "danger")

    def _apply(self, latest: dict, history: list, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.clear()
        self._history = history or []
        self._render_history()
        if not latest.get("available"):
            self._current = None
            self._selected_id = None
            self._show_empty(latest.get("message", "Belum ada rekomendasi pengadaan."))
            self._reset_stats()
            return
        self._current = latest
        self._selected_id = latest.get("id")
        self._show_detail(latest)

    def _reset_stats(self) -> None:
        self.detail_card.hide()
        self.stats_row_visible(False)
        for tile in (self.tile_status, self.tile_period, self.tile_items, self.tile_cost):
            tile.set_value("—", "")
        self.assumption_banner.set_message(
            "Rekomendasi dihitung dari hasil prediksi terbaru. Jalankan prediksi terlebih dahulu bila belum tersedia.",
            "info",
        )

    def stats_row_visible(self, visible: bool) -> None:
        self.stats_row.setVisible(visible)
        if visible:
            self.stats_row.refresh()

    def _show_empty(self, message: str) -> None:
        self.empty_card.show()
        clear_layout(self.empty_holder)
        action = ThemedButton("Buat Rekomendasi", "primary", "plus")
        action.clicked.connect(self._generate)
        self.empty_holder.addWidget(
            EmptyState(
                "Belum ada rekomendasi",
                message
                + " Pastikan hasil prediksi sudah tersedia, lalu buat rekomendasi baru.",
                "clipboard-list",
                action,
            )
        )

    def _show_detail(self, data: dict) -> None:
        self.empty_card.hide()
        self.detail_card.show()
        self.stats_row_visible(True)
        status = data.get("status", "draft")
        status_tones = {"draft": "warning", "approved": "success", "cancelled": "neutral"}
        self.detail_title.setText(f"Rekomendasi {data.get('code', '-')}")
        self.detail_subtitle.setText(
            f"Dibuat {format_datetime(data.get('created_at'))} · diperbarui {format_datetime(data.get('updated_at'))}"
        )
        label = {"draft": "Draf", "approved": "Disetujui", "cancelled": "Dibatalkan"}.get(status, status.title())
        self.status_badge.setText(label)
        self.status_badge.set_tone(status_tones.get(status, "neutral"))
        self.approve_button.setEnabled(self.is_admin and status == "draft")
        self.cancel_button.setEnabled(self.is_admin and status != "approved" and status != "cancelled")
        assumptions = data.get("assumptions", {}) or {}
        lead = assumptions.get("lead_time_days", 7)
        safety = assumptions.get("safety_stock_days", 14)
        rounding = assumptions.get("rounding_unit", 1)
        forecast_start = data.get("forecast_start")
        forecast_end = data.get("forecast_end")
        window = (
            f" Data prakiraan: {format_date(forecast_start)} – {format_date(forecast_end)}."
            if forecast_start and forecast_end
            else ""
        )
        self.assumption_banner.set_message(
            "Formula: prakiraan permintaan + stok pengaman + kebutuhan selama waktu tunggu (lead time) − stok fisik. "
            f"Asumsi aktif: waktu tunggu {lead} hari, stok pengaman {safety} hari, pembulatan {rounding} unit. "
            f"Angka adalah usulan yang dapat disesuaikan Admin.{window}",
            "info",
        )
        self.tile_status.set_value(label, f"Kode {data.get('code', '-')}")
        period_hint = (
            f"{format_date(forecast_start)} – {format_date(forecast_end)}"
            if forecast_start and forecast_end
            else f"Dibuat {format_date(data.get('created_at'))}"
        )
        self.tile_period.set_value(f"{data.get('period_weeks', 4)} pekan", period_hint)
        self.tile_items.set_value(
            f"{number(data.get('total_items', 0))} item",
            f"{number(data.get('total_units', 0))} unit total",
        )
        self.tile_cost.set_value(
            rupiah(data.get("total_estimated_cost", 0)),
            "perkiraan biaya pembelian",
        )
        items = data.get("items", [])
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name_widget = QWidget()
            name_layout = QVBoxLayout(name_widget)
            name_layout.setContentsMargins(4, 3, 4, 3)
            name_layout.setSpacing(0)
            name = ElidedLabel(item.get("name", "-"))
            name.setObjectName("TablePrimary")
            name_layout.addWidget(name)
            meta = ElidedLabel(f"{item.get('code', '')} · {item.get('unit', '')}")
            meta.setObjectName("TableMeta")
            name_layout.addWidget(meta)
            self.table.setCellWidget(row, 0, name_widget)
            self.table.add_item(row, 1, number(item.get("current_stock")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(
                row, 2, number(item.get("predicted_demand")),
                Qt.AlignmentFlag.AlignRight, color=theme.tokens["info_text"],
            )
            self.table.add_item(row, 3, number(item.get("safety_stock")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(
                row, 4, number(item.get("recommended_qty")),
                Qt.AlignmentFlag.AlignRight, color=theme.tokens["muted"],
            )
            self.table.add_item(
                row, 5, number(item.get("final_qty")),
                Qt.AlignmentFlag.AlignRight, color=theme.tokens["primary"], bold=True,
            )
            self.table.add_item(
                row, 6, rupiah(item.get("subtotal")),
                Qt.AlignmentFlag.AlignRight, bold=True,
            )
            badge = Badge(urgency_label(item.get("urgency")), URGENCY_TONES.get(item.get("urgency", ""), "neutral"))
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 7, holder)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            detail = IconButton("info", "Detail perhitungan", "info_text", 30, 16, "ghost")
            detail.clicked.connect(lambda _checked=False, value=item: self._open_detail(value))
            actions_layout.addWidget(detail)
            if self.is_admin and status == "draft":
                edit = IconButton("pencil-line", "Ubah jumlah final", "primary", 30, 16, "ghost")
                edit.clicked.connect(lambda _checked=False, value=item: self._edit_item(value))
                actions_layout.addWidget(edit)
            self.table.setCellWidget(row, 8, actions)
        self.table.scrollToTop()
        notes = data.get("notes")
        footer = (
            f"{len(items)} item · total {number(data.get('total_units', 0))} unit · "
            f"estimasi {rupiah(data.get('total_estimated_cost', 0))}."
        )
        if notes:
            footer += f" Catatan: {notes}"
        self.detail_footer.setText(footer)

    def _render_history(self) -> None:
        self.history_table.setRowCount(0)
        self.history_table.setRowCount(len(self._history))
        status_tones = {"draft": "warning", "approved": "success", "cancelled": "neutral"}
        for row, item in enumerate(self._history):
            status = item.get("status", "draft")
            self.history_table.add_item(row, 0, item.get("code", "-"), bold=True)
            self.history_table.add_item(row, 1, format_datetime(item.get("created_at")))
            self.history_table.add_item(row, 2, f"{item.get('period_weeks', '-')} pekan")
            label = {"draft": "Draf", "approved": "Disetujui", "cancelled": "Dibatalkan"}.get(status, status.title())
            badge = Badge(label, status_tones.get(status, "neutral"))
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.history_table.setCellWidget(row, 3, holder)
            self.history_table.add_item(row, 4, number(item.get("total_items", 0)), Qt.AlignmentFlag.AlignRight)
            self.history_table.add_item(row, 5, rupiah(item.get("total_estimated_cost", 0)), Qt.AlignmentFlag.AlignRight)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            open_button = IconButton("folder-open", "Buka rekomendasi", "primary", 28, 14, "ghost")
            open_button.clicked.connect(lambda _checked=False, value=item: self._open_recommendation(value))
            actions_layout.addWidget(open_button)
            export_button = IconButton("download", "Ekspor PDF", "muted", 28, 14, "ghost")
            export_button.clicked.connect(
                lambda _checked=False, value=item: self._export_for(value.get("id"), "pdf", value.get("code", "pengadaan"))
            )
            actions_layout.addWidget(export_button)
            self.history_table.setCellWidget(row, 6, actions)
        if not self._history:
            self.history_table.setRowCount(1)
            self.history_table.setSpan(0, 0, 1, 7)
            self.history_table.add_item(
                0, 0, "Belum ada riwayat rekomendasi pengadaan.",
                Qt.AlignmentFlag.AlignCenter, color=theme.tokens["muted"],
            )

    # ------------------------------------------------------------------
    def _generate(self) -> None:
        dialog = GenerateDialog(self.api, self, on_saved=self._generated)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass

    def _generated(self, result: dict) -> None:
        self.toast(f"Rekomendasi {result.get('code', 'baru')} berhasil dibuat.", "success")
        self._current = result
        self._selected_id = result.get("id")
        self._show_detail(result)
        self._refresh_history()

    def _edit_item(self, item: dict) -> None:
        if not self._current:
            return
        dialog = ProcurementEditDialog(
            self.api,
            self._current.get("id"),
            item,
            self,
            on_saved=self._item_changed,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.toast("Jumlah pembelian diperbarui.", "success")

    def _item_changed(self) -> None:
        if self._current:
            self._reload_current(self._current.get("id"))

    def _open_detail(self, item: dict) -> None:
        ItemDetailDialog(item, self).exec()

    def _detail_selected(self) -> None:
        if not self._current:
            return
        row = self.table.currentRow()
        items = self._current.get("items", [])
        if 0 <= row < len(items):
            self._open_detail(items[row])

    def _open_recommendation(self, item: dict) -> None:
        self._selected_id = item.get("id")
        self._reload_current(item.get("id"))

    def _reload_current(self, recommendation_id: int | None) -> None:
        if not recommendation_id:
            return
        self._serial += 1
        serial = self._serial
        self.notice.show_message("Memuat rincian rekomendasi...", "info")
        self.runner.submit(
            lambda: self.api.get(f"/procurement/{recommendation_id}", timeout=45),
            lambda data: self._apply_selected(data, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _approve(self) -> None:
        if not self._current or not self.is_admin:
            return
        if not ConfirmDialog.ask(
            self,
            "Setujui rekomendasi?",
            f"Rekomendasi {self._current.get('code', '')} akan ditandai disetujui dan siap dijadikan daftar pembelian. "
            "Jumlah final tidak dapat diubah setelah disetujui.",
            "Ya, setujui",
            danger=False,
        ):
            return
        self._action(f"/procurement/{self._current['id']}/approve", "Rekomendasi disetujui.")

    def _cancel(self) -> None:
        if not self._current or not self.is_admin:
            return
        if not ConfirmDialog.ask(
            self,
            "Batalkan rekomendasi?",
            f"Rekomendasi {self._current.get('code', '')} akan ditandai dibatalkan dan tidak dapat diaktifkan kembali.",
            "Ya, batalkan",
        ):
            return
        self._action(f"/procurement/{self._current['id']}/cancel", "Rekomendasi dibatalkan.")

    def _action(self, path: str, message: str) -> None:
        recommendation_id = self._current.get("id") if self._current else None
        self.runner.submit(
            lambda: self.api.post(path, timeout=45),
            lambda _result: (self.toast(message, "success"), self._reload_current(recommendation_id)),
            lambda error, status: self.toast(error, "error"),
        )

    def _export(self, fmt: str) -> None:
        if not self._current:
            self.toast("Belum ada rekomendasi untuk diekspor.", "error")
            return
        self._export_for(self._current.get("id"), fmt, self._current.get("code", "pengadaan"))

    def _export_for(self, recommendation_id: int | None, fmt: str, code: str) -> None:
        if not recommendation_id:
            return
        filters = {
            "pdf": ("PDF (*.pdf)", "pdf"),
            "xlsx": ("Excel (*.xlsx)", "xlsx"),
            "csv": ("CSV (*.csv)", "csv"),
        }[fmt]
        download_export(
            self,
            self.api,
            f"/procurement/{recommendation_id}/export",
            f"Pengadaan_{code}.{filters[1]}",
            params={"fmt": fmt},
            file_filter=filters[0],
        )
