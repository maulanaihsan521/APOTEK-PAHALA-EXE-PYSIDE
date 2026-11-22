"""Halaman Manajemen Stok dan master obat."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.components.dialogs import ConfirmDialog, ImportWizardDialog, MedicineDialog, StockAdjustDialog
from app.components.layout import PageBase
from app.components.widgets import (
    Badge,
    Card,
    ElidedLabel,
    IconButton,
    ResponsiveCardRow,
    SearchInput,
    SectionHeader,
    SegmentedControl,
    StatTile,
    Table,
    ThemedButton,
)
from app.core.theme import theme
from app.core.utils import change_type_label, format_date, format_datetime, number, rupiah, status_label
from app.pages.common import PageNotice, download_export, status_badge


class StockHistoryDialog(QDialog):
    def __init__(self, api, row: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.row = row
        self.setWindowTitle("Riwayat Stok")
        self.setModal(True)
        self.resize(660, 520)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(11)
        title = QLabel(f"Riwayat Stok · {row.get('name', '')}")
        title.setStyleSheet("font-size: 16px; font-weight: 800;")
        layout.addWidget(title)
        subtitle = QLabel(
            f"Stok sistem {number(row.get('system_stock'))} · stok fisik {number(row.get('physical_stock'))} "
            f"{row.get('unit', '')} · opname {format_date(row.get('last_opname_date'))}"
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)
        self.table = Table(["Tanggal", "Awal", "Akhir", "Perubahan", "Jenis", "Catatan"])
        self.table.setMinimumHeight(340)
        self.table.horizontalHeader().setSectionResizeMode(5, self.table.horizontalHeader().ResizeMode.Stretch)
        for column, width in ((0, 105), (1, 66), (2, 66), (3, 82), (4, 126)):
            self.table.setColumnWidth(column, width)
        self.table.verticalHeader().setDefaultSectionSize(38)
        layout.addWidget(self.table)
        self.status = QLabel("Memuat riwayat...")
        self.status.setObjectName("MutedSmall")
        layout.addWidget(self.status)
        close = ThemedButton("Tutup", "outline")
        close.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close)
        layout.addLayout(footer)
        self._load()

    def _load(self) -> None:
        try:
            rows = self.api.get(f"/inventory/{self.row['medicine_id']}/history", timeout=25)
        except Exception as exc:  # noqa: BLE001
            self.status.setText(str(exc))
            return
        self.status.setText(f"{len(rows)} perubahan terakhir")
        self.table.setRowCount(len(rows))
        for index, item in enumerate(rows):
            change = item.get("quantity_change", 0)
            color = theme.tokens["success"] if change > 0 else theme.tokens["danger_text"] if change < 0 else theme.tokens["muted"]
            self.table.add_item(index, 0, format_datetime(item.get("date")))
            self.table.add_item(index, 1, number(item.get("stock_before")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(index, 2, number(item.get("stock_after")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(
                index, 3, f"{'+' if change > 0 else ''}{number(change)}",
                Qt.AlignmentFlag.AlignRight, color=color, bold=True,
            )
            self.table.add_item(index, 4, change_type_label(item.get("change_type")))
            self.table.add_item(index, 5, item.get("note") or "—")


class StockPage(PageBase):
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
        self.move_page = 1
        self.move_page_size = 12
        self.move_pages = 1
        self.move_total = 0
        self._stock_serial = 0
        self._move_serial = 0
        self._categories_loaded = False
        self._stock_rows: list[dict] = []
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(350)
        self._debounce.timeout.connect(self._search_changed)
        self._tab = "stock"

        self.notice = PageNotice()
        self.body.addWidget(self.notice)

        filter_card = Card(padding=14, spacing=9)
        top = QHBoxLayout()
        top.setSpacing(9)
        self.search = SearchInput("Cari nama atau kode obat...")
        self.search.setMinimumWidth(240)
        self.search.textChanged.connect(lambda _text: self._debounce.start())
        top.addWidget(self.search, 2)
        self.category_combo = QComboBox()
        self.category_combo.addItem("Semua kategori", "")
        self.category_combo.currentIndexChanged.connect(self._filter_changed)
        top.addWidget(_Field("Kategori", self.category_combo), 1)
        self.status_combo = QComboBox()
        for value, label in (("", "Semua status"), ("aman", "Aman"), ("perlu_perhatian", "Perlu perhatian"), ("kritis", "Kritis")):
            self.status_combo.addItem(label, value)
        self.status_combo.currentIndexChanged.connect(self._filter_changed)
        top.addWidget(_Field("Status", self.status_combo), 1)
        top.addStretch(1)
        filter_card.body.addLayout(top)
        self.body.addWidget(filter_card)

        self.tile_units = StatTile("Total unit fisik", "boxes", "primary")
        self.tile_aman = StatTile("Stok aman", "circle-check", "success")
        self.tile_warning = StatTile("Perlu perhatian", "triangle-alert", "warning")
        self.tile_critical = StatTile("Stok kritis", "circle-alert", "danger")
        self.body.addWidget(
            ResponsiveCardRow(
                [self.tile_units, self.tile_aman, self.tile_warning, self.tile_critical],
                spacing=12,
                min_width=232,
            )
        )

        tab_row = QHBoxLayout()
        tab_row.setSpacing(10)
        self.tabs = SegmentedControl([("stock", "Daftar Stok"), ("movements", "Riwayat Pergerakan")], "stock")
        self.tabs.changed.connect(self._tab_changed)
        tab_row.addWidget(self.tabs)
        tab_row.addStretch(1)
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("MutedSmall")
        tab_row.addWidget(self.summary_label)
        self.body.addLayout(tab_row)

        self.stack = QStackedWidget()
        self.body.addWidget(self.stack)

        stock_card = Card(padding=16, spacing=8)
        stock_head = QHBoxLayout()
        stock_head.setContentsMargins(0, 0, 0, 0)
        stock_head.addWidget(
            SectionHeader("Daftar Stok Obat", "Stok fisik berasal dari stock opname terakhir.", "boxes"),
            1,
        )
        if self.is_admin:
            self.import_button = ThemedButton("Impor", "outline", "upload")
            self.import_button.setToolTip("Impor data stok dari berkas Excel atau CSV")
            self.import_button.clicked.connect(self._open_import)
            stock_head.addWidget(self.import_button)
        self.export_csv = ThemedButton("CSV", "ghost", "download", compact=True)
        self.export_csv.setToolTip("Ekspor daftar stok ke CSV")
        self.export_csv.clicked.connect(lambda: self._export("csv"))
        stock_head.addWidget(self.export_csv)
        self.export_excel = ThemedButton("Excel", "outline", "file-spreadsheet")
        self.export_excel.setToolTip("Ekspor daftar stok ke Excel")
        self.export_excel.clicked.connect(lambda: self._export("xlsx"))
        stock_head.addWidget(self.export_excel)
        if self.is_admin:
            self.add_button = ThemedButton("Tambah", "primary", "plus")
            self.add_button.setToolTip("Tambah obat baru")
            self.add_button.clicked.connect(self._add_medicine)
            stock_head.addWidget(self.add_button)
        else:
            self.adjust_button = ThemedButton("Sesuaikan Stok", "primary", "boxes")
            self.adjust_button.clicked.connect(self._adjust_selected)
            stock_head.addWidget(self.adjust_button)
        stock_card.body.addLayout(stock_head)
        self.count_label = QLabel("")
        self.count_label.setObjectName("MutedSmall")
        self.table = Table(
            ["Nama Obat", "Stok Sistem", "Stok Fisik", "Selisih", "Minimum", "Status", "Aksi"]
        )
        self.table.setMinimumHeight(460)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        for column in (1, 2, 3, 4):
            header.setSectionResizeMode(column, header.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(5, 118)
        self.table.setColumnWidth(6, 140)
        item = self.table.horizontalHeaderItem(0)
        if item:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.verticalHeader().setDefaultSectionSize(48)
        stock_card.body.addWidget(self.table)
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
        for size in (15, 25, 50):
            self.size_combo.addItem(str(size), size)
        self.size_combo.currentIndexChanged.connect(self._size_changed)
        pager.addWidget(self.size_combo)
        pager.addStretch(1)
        pager.addWidget(self.count_label)
        pager.addSpacing(4)
        self.reload_button = IconButton("refresh-cw", "Muat ulang data", "muted", 34, 17, "ghost")
        self.reload_button.clicked.connect(self.load)
        pager.addWidget(self.reload_button)
        stock_card.body.addLayout(pager)
        self.stack.addWidget(stock_card)

        movements_card = Card(padding=16, spacing=8)
        move_head = QHBoxLayout()
        move_head.setContentsMargins(0, 0, 0, 0)
        move_head.addWidget(
            SectionHeader("Riwayat Pergerakan Stok", "Jejak audit setiap penyesuaian stok.", "history"),
            1,
        )
        self.move_count = QLabel("")
        self.move_count.setObjectName("MutedSmall")
        move_head.addWidget(self.move_count)
        movements_card.body.addLayout(move_head)
        self.move_table = Table(["Tanggal", "Obat", "Awal", "Akhir", "Perubahan", "Jenis", "Petugas", "Catatan"])
        self.move_table.setMinimumHeight(460)
        header = self.move_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        for column, width in ((0, 108), (1, 180), (2, 54), (3, 54), (4, 74), (5, 100), (6, 104)):
            self.move_table.setColumnWidth(column, width)
        self.move_table.verticalHeader().setDefaultSectionSize(42)
        movements_card.body.addWidget(self.move_table)
        move_pager = QHBoxLayout()
        move_pager.setSpacing(7)
        self.move_prev = ThemedButton("Sebelumnya", "outline", "chevron-left", compact=True)
        self.move_prev.clicked.connect(lambda: self._goto_movement(self.move_page - 1))
        move_pager.addWidget(self.move_prev)
        self.move_page_label = QLabel("Halaman 1 dari 1")
        self.move_page_label.setObjectName("Muted")
        move_pager.addWidget(self.move_page_label)
        self.move_next = ThemedButton("Berikutnya", "outline", "chevron-right", compact=True)
        self.move_next.clicked.connect(lambda: self._goto_movement(self.move_page + 1))
        move_pager.addWidget(self.move_next)
        move_pager.addSpacing(10)
        move_pager.addWidget(QLabel("Baris"))
        self.move_size = QComboBox()
        for size in (12, 25, 50):
            self.move_size.addItem(str(size), size)
        self.move_size.currentIndexChanged.connect(self._move_size_changed)
        move_pager.addWidget(self.move_size)
        move_pager.addStretch(1)
        self.move_reload = ThemedButton("Muat Ulang", "ghost", "refresh-cw", compact=True)
        self.move_reload.clicked.connect(self.load_movements)
        move_pager.addWidget(self.move_reload)
        movements_card.body.addLayout(move_pager)
        self.stack.addWidget(movements_card)
        self.body.addStretch(1)

    def on_show(self) -> None:
        if not self._categories_loaded:
            self._load_categories()
        self.load()
        if self._tab == "movements":
            self.load_movements()

    def _load_categories(self) -> None:
        self.runner.submit(
            lambda: self.api.get("/medicines/categories", timeout=25),
            self._categories_ready,
            lambda message, status: self.notice.show_message(message, "danger"),
        )

    def _categories_ready(self, categories: list) -> None:
        self._categories_loaded = True
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Semua kategori", "")
        for category in categories:
            self.category_combo.addItem(category, category)
        self.category_combo.blockSignals(False)

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

    def _move_size_changed(self) -> None:
        self.move_page_size = int(self.move_size.currentData() or 12)
        self.move_page = 1
        self.load_movements()

    def _tab_changed(self, value: Any) -> None:
        self._tab = str(value)
        self.stack.setCurrentIndex(0 if self._tab == "stock" else 1)
        if self._tab == "movements" and not self.move_table.rowCount():
            self.load_movements()

    def load(self) -> None:
        self._stock_serial += 1
        serial = self._stock_serial
        params: dict[str, Any] = {"q": self.search.text().strip()}
        if self.category_combo.currentData():
            params["category"] = self.category_combo.currentData()
        if self.status_combo.currentData():
            params["status"] = self.status_combo.currentData()
        self.notice.show_message("Memuat data persediaan...", "info")
        self.runner.submit(
            lambda: (
                self.api.get("/inventory", params=params, timeout=45),
                self.api.get("/inventory/summary", timeout=45),
            ),
            lambda result: self._apply_stock(result[0], result[1], serial),
            lambda message, status: self._stock_failed(message, status, serial),
        )

    def _stock_failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._stock_serial:
            self.notice.show_message(message, "danger")

    def _apply_stock(self, rows: list[dict], summary: dict, serial: int) -> None:
        if serial != self._stock_serial:
            return
        self.notice.clear()
        self._stock_rows = rows
        self.total = len(rows)
        self.pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        if self.page > self.pages:
            self.page = self.pages
        start = (self.page - 1) * self.page_size
        page_rows = rows[start:start + self.page_size]
        self.page_label.setText(f"Halaman {self.page} dari {self.pages}")
        self.prev_button.setEnabled(self.page > 1)
        self.next_button.setEnabled(self.page < self.pages)
        self.count_label.setText(
            f"{start + 1 if page_rows else 0}–{start + len(page_rows)} / {number(self.total)} obat"
        )
        self.summary_label.setText(
            f"Opname terakhir: {format_date(summary.get('last_opname_date'))} · selisih fisik {number(summary.get('difference'))} unit"
        )
        self.tile_units.set_value(
            number(summary.get("total_units")),
            f"selisih {number(summary.get('difference'))} dari stok sistem",
        )
        self.tile_aman.set_value(
            number(summary.get("aman")),
            f"{number(summary.get('percent_aman'), 1)}% dari {summary.get('total', 0)} obat",
        )
        self.tile_warning.set_value(
            number(summary.get("perlu_perhatian")),
            f"{number(summary.get('percent_perhatian'), 1)}% dari {summary.get('total', 0)} obat",
        )
        self.tile_critical.set_value(
            number(summary.get("kritis")),
            f"{number(summary.get('percent_kritis'), 1)}% dari {summary.get('total', 0)} obat",
        )
        self.table.setRowCount(0)
        self.table.clearSpans()
        self.table.setRowCount(len(page_rows))
        for index, item in enumerate(page_rows):
            name_widget = QWidget()
            name_layout = QVBoxLayout(name_widget)
            name_layout.setContentsMargins(4, 3, 4, 3)
            name_layout.setSpacing(0)
            name = ElidedLabel(item.get("name", "-"))
            name.setObjectName("TablePrimary")
            name_layout.addWidget(name)
            meta_parts = [part for part in (item.get("code", ""), item.get("unit", ""), item.get("category", "")) if part]
            meta = ElidedLabel(" · ".join(str(part) for part in meta_parts))
            meta.setObjectName("TableMeta")
            name_layout.addWidget(meta)
            self.table.setCellWidget(index, 0, name_widget)
            self.table.add_item(index, 1, number(item.get("system_stock")), Qt.AlignmentFlag.AlignRight)
            self.table.add_item(index, 2, number(item.get("physical_stock")), Qt.AlignmentFlag.AlignRight, bold=True)
            difference = item.get("difference", 0)
            color = theme.tokens["success"] if difference == 0 else theme.tokens["danger_text"] if difference < 0 else theme.tokens["info_text"]
            self.table.add_item(
                index, 3, f"{'+' if difference > 0 else ''}{number(difference)}",
                Qt.AlignmentFlag.AlignRight, color=color, bold=True,
            )
            self.table.add_item(index, 4, number(item.get("min_stock")), Qt.AlignmentFlag.AlignRight)
            badge = status_badge(item.get("status", ""))
            wrapper = QWidget()
            wrapper_layout = QHBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(index, 5, wrapper)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(1)
            adjust = IconButton("sliders-horizontal", "Sesuaikan stok", "primary", 30, 16, "ghost")
            adjust.clicked.connect(lambda _checked=False, item=item: self._adjust(item))
            actions_layout.addWidget(adjust)
            history = IconButton("history", "Riwayat stok", "info_text", 30, 16, "ghost")
            history.clicked.connect(lambda _checked=False, item=item: self._history(item))
            actions_layout.addWidget(history)
            if self.is_admin:
                edit = IconButton("pencil-line", "Ubah master obat", "muted", 30, 16, "ghost")
                edit.clicked.connect(lambda _checked=False, item=item: self._edit_medicine(item))
                actions_layout.addWidget(edit)
                delete = IconButton("trash-2", "Nonaktifkan obat", "danger", 30, 16, "ghost")
                delete.clicked.connect(lambda _checked=False, item=item: self._delete_medicine(item))
                actions_layout.addWidget(delete)
            self.table.setCellWidget(index, 6, actions)
        self.table.scrollToTop()

    def _goto(self, page: int) -> None:
        if 1 <= page <= self.pages and page != self.page:
            self.page = page
            self.load()

    def load_movements(self) -> None:
        self._move_serial += 1
        serial = self._move_serial
        params = {"page": self.move_page, "page_size": self.move_page_size}
        self.runner.submit(
            lambda: self.api.get("/inventory/movements", params=params, timeout=45),
            lambda payload: self._apply_movements(payload, serial),
            lambda message, status: self._move_failed(message, status, serial),
        )

    def _move_failed(self, message: str, _status: int, serial: int) -> None:
        if serial == self._move_serial:
            self.toast(message, "error")

    def _apply_movements(self, payload: dict, serial: int) -> None:
        if serial != self._move_serial:
            return
        items = payload.get("items", [])
        self.move_total = payload.get("total", 0)
        self.move_pages = payload.get("pages", 1)
        self.move_page = payload.get("page", self.move_page)
        self.move_page_label.setText(f"Halaman {self.move_page} dari {self.move_pages}")
        self.move_prev.setEnabled(self.move_page > 1)
        self.move_next.setEnabled(self.move_page < self.move_pages)
        self.move_count.setText(f"{number(self.move_total)} perubahan tercatat")
        self.move_table.setRowCount(0)
        self.move_table.setRowCount(len(items))
        for index, item in enumerate(items):
            change = item.get("quantity_change", 0)
            color = theme.tokens["success"] if change > 0 else theme.tokens["danger_text"] if change < 0 else theme.tokens["muted"]
            self.move_table.add_item(index, 0, format_datetime(item.get("date")))
            self.move_table.add_item(index, 1, item.get("medicine_name", "-"))
            self.move_table.add_item(index, 2, number(item.get("stock_before")), Qt.AlignmentFlag.AlignRight)
            self.move_table.add_item(index, 3, number(item.get("stock_after")), Qt.AlignmentFlag.AlignRight)
            self.move_table.add_item(
                index, 4, f"{'+' if change > 0 else ''}{number(change)}",
                Qt.AlignmentFlag.AlignRight, color=color, bold=True,
            )
            self.move_table.add_item(index, 5, change_type_label(item.get("change_type")))
            self.move_table.add_item(index, 6, item.get("user", "Sistem"))
            self.move_table.add_item(index, 7, item.get("note") or "—")
        self.move_table.scrollToTop()

    def _goto_movement(self, page: int) -> None:
        if 1 <= page <= self.move_pages and page != self.move_page:
            self.move_page = page
            self.load_movements()

    def _adjust(self, row: dict) -> None:
        dialog = StockAdjustDialog(self.api, row, self, on_saved=self._after_stock_change)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Stok berhasil diperbarui.", "success")

    def _after_stock_change(self) -> None:
        self.load()
        if self._tab == "movements":
            self.load_movements()

    def _adjust_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._stock_rows):
            self.toast("Pilih obat pada tabel terlebih dahulu.", "warning")
            return
        start = (self.page - 1) * self.page_size
        item = self._stock_rows[start + row]
        self._adjust(item)

    def _history(self, row: dict) -> None:
        dialog = StockHistoryDialog(self.api, row, self)
        dialog.exec()

    def _add_medicine(self) -> None:
        dialog = MedicineDialog(self.api, parent=self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Obat baru ditambahkan.", "success")

    def _edit_medicine(self, row: dict) -> None:
        try:
            medicine = self.api.get(f"/medicines/{row['medicine_id']}", timeout=25)
        except Exception as exc:  # noqa: BLE001
            self.toast(str(exc), "error")
            return
        dialog = MedicineDialog(self.api, medicine, self, on_saved=self.load)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast("Master obat diperbarui.", "success")

    def _delete_medicine(self, row: dict) -> None:
        if not ConfirmDialog.ask(
            self,
            "Nonaktifkan obat?",
            f"{row.get('name', '')} akan dinonaktifkan dari daftar aktif. Riwayat data permintaan tetap tersimpan.",
            "Nonaktifkan",
        ):
            return
        self.runner.submit(
            lambda: self.api.delete(f"/medicines/{row['medicine_id']}", timeout=30),
            lambda _result: (self.toast("Obat dinonaktifkan.", "success"), self.load()),
            lambda message, status: self.toast(message, "error"),
        )

    def _open_import(self) -> None:
        dialog = ImportWizardDialog(self.api, "inventory", self, on_done=self._after_stock_change)
        dialog.exec()

    def _export(self, fmt: str) -> None:
        params = {"fmt": fmt}
        fallback = "Data_Stok.xlsx" if fmt == "xlsx" else "Data_Stok.csv"
        download_export(
            self,
            self.api,
            "/inventory/export",
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
