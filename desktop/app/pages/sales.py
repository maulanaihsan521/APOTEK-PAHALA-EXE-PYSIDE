"""Halaman Data Penjualan."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import (
    ConfirmDialog,
    DateRangeDialog,
    ImportWizardDialog,
    SaleDialog,
)
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    ElidedLabel,
    IconButton,
    InlineBanner,
    ResponsiveCardRow,
    SearchInput,
    SectionHeader,
    StatTile,
    Table,
    ThemedButton,
    set_variant,
)
from app.core.theme import theme
from app.core.icons import icon
from app.core.utils import format_date, number, rupiah, source_label
from app.pages.common import PageNotice, download_export


class SalesPage(PageBase):
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
        self._serial = 0
        self._medicines: list[dict] = []
        self._medicines_loaded = False
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(380)
        self._debounce.timeout.connect(self._search_changed)

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        filter_card = Card(padding=14, spacing=10)
        row = QHBoxLayout()
        row.setSpacing(9)
        self.search = SearchInput("Cari ID catatan, nama, atau kode obat...")
        self.search.setMinimumWidth(260)
        self.search.textChanged.connect(lambda _text: self._debounce.start())
        row.addWidget(self.search, 2)
        self.medicine_filter = QComboBox()
        self.medicine_filter.addItem("Semua obat", None)
        self.medicine_filter.setMinimumWidth(190)
        self.medicine_filter.currentIndexChanged.connect(self._filter_changed)
        row.addWidget(FieldLike("Obat", self.medicine_filter), 1)
        self.date_button = QPushButton("  Semua periode")
        self.date_button.setProperty("variant", "outline")
        self.date_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_button.setMinimumHeight(40)
        self.date_button.clicked.connect(self._choose_dates)
        row.addWidget(FieldLike("Periode", self.date_button), 1)
        self.reset_date = QPushButton("Reset")
        self.reset_date.setProperty("variant", "ghost")
        self.reset_date.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_date.clicked.connect(self._reset_dates)
        self.reset_date.hide()
        row.addWidget(self.reset_date, 0, Qt.AlignmentFlag.AlignBottom)
        filter_card.body.addLayout(row)
        self.body.addWidget(filter_card)

        self.stat_transactions = StatTile("Baris data", "receipt-text", "primary")
        self.stat_quantity = StatTile("Estimasi kuantitas", "boxes", "info")
        self.stat_revenue = StatTile("Estimasi nilai", "wallet", "accent")
        self.stat_average = StatTile("Rata-rata per baris", "chart-column", "purple")
        self.body.addWidget(
            ResponsiveCardRow(
                [self.stat_transactions, self.stat_quantity, self.stat_revenue, self.stat_average],
                spacing=12,
                min_width=232,
            )
        )
        source_note = QLabel(
            "Riwayat 2022–2026 adalah estimasi permintaan mingguan dari stok opname dan pembelian, "
            "bukan transaksi kasir. Baris yang Anda tambahkan secara manual dicatat sebagai penjualan manual."
        )
        source_note.setObjectName("MutedSmall")
        source_note.setWordWrap(True)
        self.body.addWidget(source_note)

        table_card = Card(padding=16, spacing=8)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(
            SectionHeader("Riwayat Permintaan & Penjualan", "Data tersimpan dan siap dianalisis.", "shopping-bag"),
            1,
        )
        if self.is_admin:
            self.import_button = ThemedButton("Impor", "outline", "upload")
            self.import_button.setToolTip("Impor data penjualan dari berkas Excel atau CSV")
            self.import_button.clicked.connect(self._open_import)
            header_row.addWidget(self.import_button)
        self.export_csv = ThemedButton("CSV", "ghost", "download", compact=True)
        self.export_csv.setToolTip("Ekspor data penjualan ke CSV")
        self.export_csv.clicked.connect(lambda: self._export("csv"))
        header_row.addWidget(self.export_csv)
        self.export_excel = ThemedButton("Excel", "outline", "file-spreadsheet")
        self.export_excel.setToolTip("Ekspor data penjualan ke Excel")
        self.export_excel.clicked.connect(lambda: self._export("xlsx"))
        header_row.addWidget(self.export_excel)
        self.add_button = ThemedButton("Tambah", "primary", "plus")
        self.add_button.setToolTip("Tambah penjualan manual")
        self.add_button.clicked.connect(self._add_sale)
        header_row.addWidget(self.add_button)
        table_card.body.addLayout(header_row)
        self.count_label = QLabel("")
        self.count_label.setObjectName("MutedSmall")
        self.table = Table(
            ["Tanggal / ID", "Nama Obat", "Jumlah", "Harga", "Total", "Sumber", "Aksi"]
        )
        self._row_codes: dict[int, str] = {}
        self.table.setMinimumHeight(470)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        # Nominal mengikuti isinya agar tidak terpotong pada penskalaan 125%.
        for column in (2, 3, 4):
            header.setSectionResizeMode(column, header.ResizeMode.ResizeToContents)
        for column in (0, 1):
            item = self.table.horizontalHeaderItem(column)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.setColumnWidth(0, 190)
        self.table.setColumnWidth(5, 106)
        self.table.setColumnWidth(6, 78)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        table_card.body.addWidget(self.table)
        pager = QHBoxLayout()
        pager.setSpacing(6)
        self.prev_button = ThemedButton("Sebelumnya", "outline", "chevron-left", compact=True)
        self.prev_button.clicked.connect(lambda: self._goto(self.page - 1))
        pager.addWidget(self.prev_button)
        self.page_label = QLabel("Halaman 1 dari 1")
        self.page_label.setObjectName("Muted")
        pager.addWidget(self.page_label)
        self.next_button = ThemedButton("Berikutnya", "outline", "chevron-right", compact=True)
        self.next_button.clicked.connect(lambda: self._goto(self.page + 1))
        pager.addWidget(self.next_button)
        pager.addSpacing(6)
        pager.addWidget(QLabel("Baris"))
        self.size_combo = QComboBox()
        for size in (15, 25, 50, 100):
            self.size_combo.addItem(str(size), size)
        self.size_combo.currentIndexChanged.connect(self._size_changed)
        pager.addWidget(self.size_combo)
        pager.addStretch(1)
        pager.addWidget(self.count_label)
        pager.addSpacing(4)
        self.reload_button = IconButton("refresh-cw", "Muat ulang data", "muted", 34, 17, "ghost")
        self.reload_button.clicked.connect(self.load)
        pager.addWidget(self.reload_button)
        table_card.body.addLayout(pager)
        self.body.addWidget(table_card)
        self.body.addStretch(1)
        theme.changed.connect(self._refresh_styles)
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        self.date_button.setStyleSheet("")
        self.date_button.setIcon(icon("calendar-range", theme.tokens["muted"], 15))
        self.date_button.setIconSize(QSize(15, 15))
        self.reset_date.setStyleSheet("")

    def on_show(self) -> None:
        if not self._medicines_loaded:
            self._load_medicines()
        else:
            self.load()

    def _load_medicines(self) -> None:
        self.runner.submit(
            lambda: self.api.get("/medicines", timeout=30),
            self._medicines_ready,
            lambda message, status: self.notice.show_message(message, "danger"),
        )

    def _medicines_ready(self, medicines: list) -> None:
        self._medicines = medicines
        self._medicines_loaded = True
        self.medicine_filter.blockSignals(True)
        self.medicine_filter.clear()
        self.medicine_filter.addItem("Semua obat", None)
        for medicine in medicines:
            self.medicine_filter.addItem(medicine.get("name", "-"), medicine.get("id"))
        self.medicine_filter.blockSignals(False)
        self.load()

    def _filter_changed(self) -> None:
        self.page = 1
        self.load()

    def _search_changed(self) -> None:
        self.page = 1
        self.load()

    def _size_changed(self) -> None:
        self.page_size = int(self.size_combo.currentData() or 15)
        self.page = 1
        self.load()

    def _choose_dates(self) -> None:
        dialog = DateRangeDialog("Filter Periode Penjualan", self.start or None, self.end or None, self)
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
        medicine_id = self.medicine_filter.currentData()
        if medicine_id:
            params["medicine_id"] = medicine_id
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end
        return params

    def load(self) -> None:
        self._serial += 1
        serial = self._serial
        params = self._params()
        self.notice.show_message("Memuat data permintaan...", "info")

        def task() -> dict:
            sales = self.api.get("/sales", params=params, timeout=45)
            summary_params = {}
            if self.start:
                summary_params["start"] = self.start
            if self.end:
                summary_params["end"] = self.end
            summary = self.api.get("/sales/summary", params=summary_params, timeout=30)
            return {"sales": sales, "summary": summary}

        self.runner.submit(
            task,
            lambda payload: self._apply(payload, serial),
            lambda message, status: self._failed(message, status, serial),
        )

    def _failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._serial:
            self.notice.show_message(message, "danger")

    def _apply(self, payload: dict, serial: int) -> None:
        if serial != self._serial:
            return
        self.notice.clear()
        data = payload.get("sales", {})
        items = data.get("items", [])
        self.total = data.get("total", 0)
        self.pages = data.get("pages", 1)
        self.page = data.get("page", self.page)
        self.page_label.setText(f"Halaman {self.page} dari {self.pages}")
        self.prev_button.setEnabled(self.page > 1)
        self.next_button.setEnabled(self.page < self.pages)
        start_row = (self.page - 1) * self.page_size + 1 if self.total else 0
        end_row = min(self.page * self.page_size, self.total)
        self.count_label.setText(f"{start_row}–{end_row} / {number(self.total)} baris")
        self.table.setRowCount(0)
        self.table.clearSpans()
        self.table.setRowCount(len(items))
        self._row_codes = {}
        for row, sale in enumerate(items):
            code = sale.get("transaction_code", "-")
            self._row_codes[row] = code
            # Tanggal dan ID digabung agar kolom nama obat tetap lega.
            date_cell = QWidget()
            date_layout = QVBoxLayout(date_cell)
            date_layout.setContentsMargins(4, 3, 4, 3)
            date_layout.setSpacing(0)
            date_label = QLabel(format_date(sale.get("sale_date")))
            date_label.setObjectName("TablePrimary")
            date_layout.addWidget(date_label)
            code_label = ElidedLabel(code if code != "-" else "")
            code_label.setObjectName("TableMeta")
            date_layout.addWidget(code_label)
            date_cell.setToolTip(code)
            self.table.setCellWidget(row, 0, date_cell)
            medicine = QWidget()
            medicine_layout = QVBoxLayout(medicine)
            medicine_layout.setContentsMargins(4, 3, 4, 3)
            medicine_layout.setSpacing(0)
            name = ElidedLabel(sale.get("medicine_name", "-"))
            name.setObjectName("TablePrimary")
            medicine_layout.addWidget(name)
            detail = sale.get("unit") or ""
            code = sale.get("medicine_code") or ""
            if code:
                detail = f"{detail} · Kode {code}" if detail else f"Kode {code}"
            code_label = ElidedLabel(detail)
            code_label.setObjectName("TableMeta")
            medicine_layout.addWidget(code_label)
            self.table.setCellWidget(row, 1, medicine)
            self.table.add_item(row, 2, number(sale.get("quantity")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(row, 3, rupiah(sale.get("unit_price")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(
                row, 4, rupiah(sale.get("total_price")), Qt.AlignmentFlag.AlignRight,
                color=theme.tokens["text"], bold=True,
            )
            badge = Badge(source_label(sale.get("source")), "neutral" if sale.get("source") != "import" else "info")
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 5, holder)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            if self.is_admin:
                edit = IconButton("pencil-line", "Ubah baris data", "primary", 30, 16, "ghost")
                edit.clicked.connect(lambda _checked=False, item=sale: self._edit_sale(item))
                actions_layout.addWidget(edit)
                delete = IconButton("trash-2", "Hapus baris data", "danger", 30, 16, "ghost")
                delete.clicked.connect(lambda _checked=False, item=sale: self._delete_sale(item))
                actions_layout.addWidget(delete)
            else:
                label = QLabel("—")
                label.setObjectName("MutedSmall")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                actions_layout.addWidget(label)
            self.table.setCellWidget(row, 6, actions)
        self.table.scrollToTop()
        summary = payload.get("summary", {})
        self.stat_transactions.set_value(number(summary.get("transactions", self.total)), "baris permintaan tercatat")
        self.stat_quantity.set_value(f"{number(summary.get('quantity', 0))} unit", "estimasi unit permintaan")
        self.stat_revenue.set_value(rupiah(summary.get("revenue", 0)), "estimasi nilai permintaan")
        transactions = summary.get("transactions", 0) or 0
        average = (summary.get("revenue", 0) or 0) / transactions if transactions else 0
        self.stat_average.set_value(rupiah(average), "per baris data")

    def _goto(self, page: int) -> None:
        if 1 <= page <= self.pages and page != self.page:
            self.page = page
            self.load()

    def _add_sale(self) -> None:
        if not self._medicines_loaded:
            self.toast("Daftar obat belum siap. Coba beberapa saat lagi.", "warning")
            return
        dialog = SaleDialog(self.api, self._medicines, parent=self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Data penjualan ditambahkan.", "success")

    def _edit_selected(self) -> None:
        if not self.is_admin:
            return
        row = self.table.currentRow()
        if row < 0:
            return
        # Data lengkap diambil dari API karena tabel menyimpan ringkasan.
        transaction_code = self._row_codes.get(row, "")
        if not transaction_code:
            return
        self._edit_by_code(transaction_code)

    def _edit_by_code(self, transaction_code: str) -> None:
        try:
            data = self.api.get("/sales", params={"q": transaction_code, "page_size": 5}, timeout=20)
            item = next((sale for sale in data.get("items", []) if sale.get("transaction_code") == transaction_code), None)
        except Exception as exc:  # noqa: BLE001
            self.toast(str(exc), "error")
            return
        if item:
            self._edit_sale(item)

    def _edit_sale(self, sale: dict) -> None:
        dialog = SaleDialog(self.api, self._medicines, sale, self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Data berhasil diperbarui.", "success")

    def _delete_sale(self, sale: dict) -> None:
        if not ConfirmDialog.ask(
            self,
            "Hapus baris data?",
            f"Baris {sale.get('transaction_code', '')} akan dihapus permanen dan tidak dapat dikembalikan.",
            "Hapus",
            danger=True,
        ):
            return
        self.runner.submit(
            lambda: self.api.delete(f"/sales/{sale['id']}", timeout=30),
            lambda _result: (self.toast("Baris data dihapus.", "success"), self.load()),
            lambda message, status: self.toast(message, "error"),
        )

    def _open_import(self) -> None:
        dialog = ImportWizardDialog(self.api, "sales", self, on_done=self.load)
        dialog.exec()

    def _export(self, fmt: str) -> None:
        params = self._params()
        params.pop("page", None)
        params.pop("page_size", None)
        params["fmt"] = fmt
        fallback = "Data_Penjualan.xlsx" if fmt == "xlsx" else "Data_Penjualan.csv"
        download_export(
            self,
            self.api,
            "/sales/export",
            fallback,
            params=params,
            file_filter="Excel (*.xlsx)" if fmt == "xlsx" else "CSV (*.csv)",
        )


class FieldLike(QWidget):
    def __init__(self, label: str, widget: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        text = QLabel(label)
        text.setObjectName("Hint")
        layout.addWidget(text)
        layout.addWidget(widget)
