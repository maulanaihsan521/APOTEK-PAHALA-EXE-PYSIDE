"""Dialog formulir, konfirmasi, filter tanggal, import, dan entitas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.components.widgets import (
    Badge,
    Divider,
    Field,
    IconBox,
    InlineBanner,
    Table,
    ThemedButton,
    fit_dialog_to_screen,
    set_variant,
)
from app.core.api import ApiError
from app.core.async_worker import AsyncRunner
from app.core.config import MONTHS_ID_LONG
from app.core.theme import theme
from app.core.utils import format_date, from_qdate, number, rupiah, to_qdate


def _label(text: str, object_name: str = "FieldLabel") -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def _readonly_row(label: str, value: str) -> tuple[QWidget, QLabel]:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    left = _label(label, "Muted")
    right = QLabel(value)
    right.setStyleSheet("font-weight: 600;")
    layout.addWidget(left)
    layout.addStretch(1)
    layout.addWidget(right)
    return widget, right


class FormDialog(QDialog):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str = "pencil-line",
        parent: QWidget | None = None,
        width: int = 470,
        save_text: str = "Simpan",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(width)
        self._on_save: Callable[[], bool | None] | None = None
        self._runner = AsyncRunner(self)
        self.setStyleSheet(
            f"QDialog {{ background: {theme.tokens['surface']}; }}"
            f"QLabel#DialogTitle {{ font-size: 17px; font-weight: 800; color: {theme.tokens['text']}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(13)
        head = QHBoxLayout()
        head.setSpacing(11)
        box = IconBox(icon_name, "primary", "primary_soft", 38, 18)
        head.addWidget(box)
        text = QVBoxLayout()
        text.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("DialogTitle")
        text.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("Muted")
            sub.setWordWrap(True)
            text.addWidget(sub)
        head.addLayout(text, 1)
        layout.addLayout(head)
        layout.addWidget(Divider(self))
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.form_host = QWidget()
        self.form_host.setStyleSheet("background: transparent;")
        self.form = QVBoxLayout(self.form_host)
        self.form.setContentsMargins(0, 0, 2, 0)
        self.form.setSpacing(11)
        self.scroll.setWidget(self.form_host)
        layout.addWidget(self.scroll, 1)
        self.error = QLabel("")
        self.error.setObjectName("ErrorText")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch(1)
        self.cancel_button = ThemedButton("Batal", "outline")
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.cancel_button)
        # QPushButton memperlakukan "&" sebagai penanda tombol pintas; escape agar
        # label seperti "Simpan & Uji" tampil apa adanya.
        self.save_button = ThemedButton(save_text.replace("&", "&&"), "primary", "check")
        self.save_button.clicked.connect(self._save)
        footer.addWidget(self.save_button)
        layout.addLayout(footer)

    def field(self, label: str, widget: QWidget, required: bool = False, hint: str = "") -> Field:
        field = Field(label, widget, hint, required)
        self.form.addWidget(field)
        return field

    def row(self, *widgets: QWidget, ratios: tuple[int, ...] | None = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        for index, widget in enumerate(widgets):
            row.addWidget(widget, ratios[index] if ratios and index < len(ratios) else 1)
        self.form.addLayout(row)
        return row

    def note(self, text: str, tone: str = "info") -> InlineBanner:
        banner = InlineBanner(text, tone)
        self.form.addWidget(banner)
        return banner

    def bind_save(self, callback: Callable[[], bool | None]) -> None:
        self._on_save = callback

    def _submit_async(
        self,
        task: Callable[[], Any],
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[], None] | None = None,
    ) -> None:
        def ok(result: Any) -> None:
            self.set_busy(False)
            if on_success:
                on_success(result)
            self.accept()

        def bad(message: str, _status: int) -> None:
            self.set_busy(False)
            self.show_error(message)
            if on_error:
                on_error()

        self._runner.submit(task, ok, bad)

    def _save(self) -> None:
        self.error.hide()
        if self._on_save is None:
            self.accept()
            return
        try:
            result = self._on_save()
        except ApiError as exc:
            self.show_error(exc.message)
            return
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))
            return
        if result is False:
            return
        self.accept()

    def show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.show()

    def set_busy(self, busy: bool, text: str = "Menyimpan...") -> None:
        self.save_button.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)
        if busy:
            self.save_button.setText(text)
        else:
            self.save_button.setText("Simpan")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_content_height()
        fit_dialog_to_screen(self)

    def _fit_content_height(self) -> None:
        """Naikkan tinggi dialog bila isi form hanya kurang sedikit."""
        if self.form_host.sizeHint().height() <= 0:
            return
        chrome = self.height() - self.scroll.viewport().height()
        needed = self.form_host.sizeHint().height() + chrome + 2
        if needed > self.height():
            screen = self.screen() or QApplication.primaryScreen()
            limit = screen.availableGeometry().height() - 44 if screen else needed
            if needed <= limit:
                self.resize(self.width(), needed)


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        parent: QWidget | None = None,
        confirm_text: str = "Ya, lanjutkan",
        danger: bool = True,
        icon_name: str = "triangle-alert",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(13)
        row = QHBoxLayout()
        row.setSpacing(12)
        box = IconBox(icon_name, "danger_text" if danger else "primary", "danger_bg" if danger else "primary_soft", 42, 20)
        row.addWidget(box, 0, Qt.AlignmentFlag.AlignTop)
        text = QVBoxLayout()
        text.setSpacing(5)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 800;")
        text.addWidget(heading)
        body = QLabel(message)
        body.setObjectName("Muted")
        body.setWordWrap(True)
        text.addWidget(body)
        row.addLayout(text, 1)
        layout.addLayout(row)
        footer = QHBoxLayout()
        footer.addStretch(1)
        cancel = ThemedButton("Batal", "outline")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        confirm = ThemedButton(confirm_text, "danger" if danger else "primary", icon_name="trash-2" if danger else "check")
        confirm.clicked.connect(self.accept)
        footer.addWidget(confirm)
        layout.addLayout(footer)

    @staticmethod
    def ask(
        parent: QWidget,
        title: str,
        message: str,
        confirm_text: str = "Ya, lanjutkan",
        danger: bool = True,
    ) -> bool:
        dialog = ConfirmDialog(title, message, parent, confirm_text, danger)
        return dialog.exec() == QDialog.DialogCode.Accepted


class DateRangeDialog(QDialog):
    """Dialog filter tanggal dengan preset rentang."""

    def __init__(
        self,
        title: str = "Filter Periode",
        start: str | None = None,
        end: str | None = None,
        parent: QWidget | None = None,
        default_end: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(430)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(13)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 800;")
        layout.addWidget(heading)
        subtitle = QLabel("Pilih rentang tanggal data yang ingin ditampilkan.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)
        presets = QHBoxLayout()
        presets.setSpacing(6)
        for label, days in (("30 hari", 30), ("90 hari", 90), ("1 tahun", 365)):
            button = QPushButton(label, self)
            button.setProperty("pill", "true")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, value=days: self._preset(value))
            presets.addWidget(button)
        presets.addStretch(1)
        layout.addLayout(presets)
        dates = QHBoxLayout()
        dates.setSpacing(10)
        self.start = QDateEdit(self)
        self.start.setCalendarPopup(True)
        self.start.setDisplayFormat("dd/MM/yyyy")
        self.start.setDate(to_qdate(start))
        self.end = QDateEdit(self)
        self.end.setCalendarPopup(True)
        self.end.setDisplayFormat("dd/MM/yyyy")
        self.end.setDate(to_qdate(end or default_end))
        dates.addWidget(Field("Tanggal mulai", self.start))
        dates.addWidget(Field("Tanggal akhir", self.end))
        layout.addLayout(dates)
        footer = QHBoxLayout()
        footer.addStretch(1)
        cancel = ThemedButton("Batal", "outline")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        apply = ThemedButton("Terapkan", "primary", "filter")
        apply.clicked.connect(self._validate)
        footer.addWidget(apply)
        layout.addLayout(footer)

    def _preset(self, days: int) -> None:
        end = QDate.currentDate()
        self.end.setDate(end)
        self.start.setDate(end.addDays(-(days - 1)))

    def _validate(self) -> None:
        if self.start.date() > self.end.date():
            QMessageBox.warning(self, "Periode tidak valid", "Tanggal mulai tidak boleh melebihi tanggal akhir.")
            return
        self.accept()

    def values(self) -> tuple[str, str]:
        return from_qdate(self.start.date()), from_qdate(self.end.date())


class ImportWizardDialog(QDialog):
    """Wizard import: unggah, petakan kolom, validasi, lalu proses."""

    completed = Signal()

    TYPES = [
        ("sales", "Data Penjualan"),
        ("weather", "Data Cuaca"),
        ("medicines", "Master Obat"),
        ("inventory", "Stok Fisik"),
    ]
    REQUIRED_LABELS = {
        "sales": {
            "sale_date": "Tanggal penjualan",
            "medicine_code": "Kode obat",
            "quantity": "Jumlah",
            "unit_price": "Harga satuan",
            "transaction_code": "ID transaksi",
            "medicine_name": "Nama obat",
        },
        "weather": {
            "weather_date": "Tanggal cuaca",
            "temperature": "Suhu",
            "rainfall": "Curah hujan",
            "humidity": "Kelembapan",
        },
        "medicines": {
            "code": "Kode obat",
            "name": "Nama obat",
            "category": "Kategori",
            "unit": "Satuan",
            "price": "Harga",
            "min_stock": "Minimum stok",
            "safety_stock": "Stok pengaman",
        },
        "inventory": {
            "medicine_code": "Kode obat",
            "system_stock": "Stok sistem",
            "physical_stock": "Stok fisik",
            "last_opname_date": "Tanggal opname",
        },
    }

    def __init__(self, api, import_type: str | None = None, parent: QWidget | None = None, on_done: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self.api = api
        self.on_done = on_done
        self.preview: dict | None = None
        self.path: str | None = None
        self.setWindowTitle("Import Data")
        self.setModal(True)
        self.resize(820, 640)
        self.setStyleSheet(f"QDialog {{ background: {theme.tokens['surface']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(11)
        head.addWidget(IconBox("upload", "primary", "primary_soft", 38, 18))
        text = QVBoxLayout()
        text.setSpacing(2)
        title = QLabel("Import Data")
        title.setStyleSheet("font-size: 17px; font-weight: 800;")
        text.addWidget(title)
        subtitle = QLabel("Unggah CSV/XLS/XLSX, periksa pemetaan kolom, lalu proses. Maksimal 50.000 baris.")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        text.addWidget(subtitle)
        head.addLayout(text, 1)
        layout.addLayout(head)
        layout.addWidget(Divider(self))

        picker = QHBoxLayout()
        picker.setSpacing(9)
        self.type_combo = QComboBox(self)
        for value, label in self.TYPES:
            self.type_combo.addItem(label, value)
        if import_type:
            index = self.type_combo.findData(import_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            self.type_combo.setEnabled(False)
        picker.addWidget(Field("Jenis data", self.type_combo))
        self.file_label = QLabel("Belum ada berkas dipilih")
        self.file_label.setObjectName("Muted")
        self.file_label.setWordWrap(True)
        picker.addWidget(Field("Berkas", self.file_label), 1)
        choose = ThemedButton("Pilih Berkas", "outline", "file-spreadsheet")
        choose.clicked.connect(self._choose_file)
        picker.addWidget(choose, 0, Qt.AlignmentFlag.AlignBottom)
        download = ThemedButton("Template", "ghost", "download")
        download.clicked.connect(self._download_template)
        picker.addWidget(download, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(picker)

        self.banner = InlineBanner(
            "Data hasil import wajib diverifikasi. Data aktual berasal dari stok opname dan pembelian Apotek Pahala; permintaan merupakan estimasi.",
            "info",
        )
        layout.addWidget(self.banner)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        self.result = QLabel("")
        self.result.setWordWrap(True)
        self.result.hide()
        layout.addWidget(self.result)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.cancel = ThemedButton("Batal", "outline")
        self.cancel.clicked.connect(self.reject)
        footer.addWidget(self.cancel)
        self.commit = ThemedButton("Proses Import", "primary", "upload")
        self.commit.setEnabled(False)
        self.commit.clicked.connect(self._commit)
        footer.addWidget(self.commit)
        layout.addLayout(footer)
        self._mapping_widgets: dict[str, QComboBox] = {}
        self._runner = AsyncRunner(self)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        fit_dialog_to_screen(self)

    def _choose_file(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, "Pilih berkas data", "", "Data (*.csv *.xls *.xlsx);;Semua berkas (*.*)"
        )
        if not path:
            return
        self.path = path
        self.file_label.setText(Path(path).name)
        self._load_preview()

    def _load_preview(self) -> None:
        if not self.path:
            return
        import_type = self.type_combo.currentData()

        def task() -> Any:
            return self.api.upload(
                "/imports/preview", self.path, {"import_type": import_type}, timeout=120
            )

        def ok(preview: dict) -> None:
            self.preview = preview
            self._render_preview()

        def bad(message: str, _status: int) -> None:
            self.banner.set_message(message, "danger")
            self.preview = None
            self.commit.setEnabled(False)

        self._runner.submit(task, ok, bad)

    def _clear_content(self) -> None:
        for index in reversed(range(self.content_layout.count())):
            item = self.content_layout.takeAt(index)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        self._mapping_widgets.clear()

    def _clear_layout(self, layout) -> None:
        for index in reversed(range(layout.count())):
            item = layout.takeAt(index)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _render_preview(self) -> None:
        self._clear_content()
        if not self.preview:
            return
        preview = self.preview
        rows = preview.get("total_rows", 0)
        valid = preview.get("valid_preview", 0)
        errors = preview.get("error_preview", [])
        missing = preview.get("missing", [])
        if missing:
            self.banner.set_message(
                "Kolom wajib belum terdeteksi otomatis: " + ", ".join(missing) + ". Petakan secara manual di bawah.",
                "warning",
            )
        else:
            self.banner.set_message(
                f"{rows:,} baris terbaca; {valid} baris contoh valid. Periksa pemetaan sebelum memproses.".replace(",", "."),
                "success" if not errors else "warning",
            )

        summary = QFrame()
        summary.setObjectName("SoftCard")
        summary_row = QHBoxLayout(summary)
        summary_row.setContentsMargins(14, 11, 14, 11)
        for label, value in (
            ("Berkas", preview.get("file_name", "-")),
            ("Total baris", f"{rows:,}".replace(",", ".")),
            ("Valid (contoh)", str(valid)),
            ("Error (contoh)", str(len(errors))),
        ):
            block = QVBoxLayout()
            block.setSpacing(1)
            key = QLabel(label)
            key.setObjectName("MutedSmall")
            block.addWidget(key)
            val = QLabel(str(value))
            val.setStyleSheet("font-size: 13px; font-weight: 700;")
            block.addWidget(val)
            summary_row.addLayout(block, 1)
        self.content_layout.addWidget(summary)

        mapping_title = QLabel("Pemetaan Kolom")
        mapping_title.setStyleSheet("font-size: 14px; font-weight: 800;")
        self.content_layout.addWidget(mapping_title)
        hint = QLabel("Pilih kolom berkas yang sesuai untuk setiap field. Kolom bertanda * wajib diisi.")
        hint.setObjectName("MutedSmall")
        self.content_layout.addWidget(hint)
        mapping_frame = QFrame()
        mapping_frame.setObjectName("SoftCard")
        grid = QGridLayout(mapping_frame)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(9)
        required = preview.get("required", [])
        mapping = preview.get("mapping", {})
        columns = preview.get("columns", [])
        labels = self.REQUIRED_LABELS.get(preview.get("import_type", ""), {})
        for index, field in enumerate(list(mapping.keys()) or required):
            column, row = index % 2, index // 2
            combo = QComboBox()
            combo.addItem("— tidak dipakai —", "")
            for name in columns:
                combo.addItem(str(name), name)
            selected = mapping.get(field, "")
            if selected:
                position = combo.findData(selected)
                if position >= 0:
                    combo.setCurrentIndex(position)
            grid.addWidget(Field(labels.get(field, field) + (" *" if field in required else ""), combo), row, column)
            self._mapping_widgets[field] = combo
        self.content_layout.addWidget(mapping_frame)

        sample = preview.get("sample_rows", [])
        if sample:
            sample_title = QLabel("Contoh Data")
            sample_title.setStyleSheet("font-size: 14px; font-weight: 800;")
            self.content_layout.addWidget(sample_title)
            table = Table(list(sample[0].keys()))
            table.setRowCount(len(sample))
            table.setMinimumHeight(190)
            for row_index, record in enumerate(sample):
                for column_index, key in enumerate(sample[0].keys()):
                    table.add_item(row_index, column_index, str(record.get(key, ""))[:80])
            table.resizeColumnsToContents()
            self.content_layout.addWidget(table)

        if errors:
            error_title = QLabel("Contoh Kesalahan")
            error_title.setStyleSheet("font-size: 14px; font-weight: 800;")
            self.content_layout.addWidget(error_title)
            for error in errors[:8]:
                message = QLabel(f"Baris {error.get('row')}: {error.get('message')}")
                message.setObjectName("ErrorText")
                message.setWordWrap(True)
                self.content_layout.addWidget(message)
        self.content_layout.addStretch(1)
        self.commit.setEnabled(True)

    def _mapping_payload(self) -> dict[str, str]:
        mapping = {}
        for field, combo in self._mapping_widgets.items():
            value = combo.currentData()
            if value:
                mapping[field] = value
        return mapping

    def _commit(self) -> None:
        if not self.preview:
            return
        mapping = self._mapping_payload()
        missing = [field for field in self.preview.get("required", []) if not mapping.get(field)]
        if missing:
            labels = self.REQUIRED_LABELS.get(self.preview.get("import_type", ""), {})
            self.banner.set_message(
                "Kolom wajib belum dipetakan: " + ", ".join(labels.get(field, field) for field in missing),
                "danger",
            )
            return
        if not ConfirmDialog.ask(
            self,
            "Proses import?",
            f"Data akan ditambahkan ke database. {self.preview.get('total_rows', 0):,} baris akan diperiksa.".replace(",", "."),
            "Ya, proses",
            danger=False,
        ):
            return
        data = {
            "file_token": self.preview.get("file_token", ""),
            "import_type": self.preview.get("import_type", ""),
            "mapping_json": json.dumps(mapping, ensure_ascii=False),
            "skip_duplicates": "true",
        }
        self.commit.setEnabled(False)

        def task() -> Any:
            return self.api.post_form("/imports/commit", data=data, timeout=300)

        def ok(result: dict) -> None:
            self.result.setText(
                f"Import selesai: {result.get('inserted', 0):,} baris masuk, "
                f"{result.get('skipped', 0):,} baris dilewati. Kode batch: {result.get('batch_code', '-')}."
                .replace(",", ".")
            )
            self.result.setStyleSheet(
                f"background: {theme.tokens['success_bg']}; color: {theme.tokens['success']};"
                "border-radius: 9px; padding: 10px 12px; font-size: 12px; font-weight: 600;"
            )
            self.result.show()
            self.commit.setEnabled(False)
            self.commit.setText("Selesai")
            try:
                self.commit.clicked.disconnect()
            except RuntimeError:
                pass
            self.commit.clicked.connect(self.accept)
            self.completed.emit()
            if self.on_done:
                self.on_done()

        def bad(message: str, _status: int) -> None:
            self.banner.set_message(message, "danger")
            self.commit.setEnabled(True)

        self._runner.submit(task, ok, bad)

    def _download_template(self) -> None:
        import_type = self.type_combo.currentData()

        def task() -> Any:
            return self.api.download(f"/imports/template/{import_type}", f"template_{import_type}.csv")

        def ok(content_name: tuple[bytes, str]) -> None:
            content, name = content_name
            path, _filter = QFileDialog.getSaveFileName(self, "Simpan template", name, "CSV (*.csv)")
            if not path:
                return
            Path(path).write_bytes(content)
            self.banner.set_message(f"Template disimpan ke {path}.", "success")

        def bad(message: str, _status: int) -> None:
            self.banner.set_message(message, "danger")

        self._runner.submit(task, ok, bad)


class MedicineDialog(FormDialog):
    def __init__(self, api, medicine: dict | None = None, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.medicine = medicine
        self.on_saved = on_saved
        super().__init__(
            "Ubah Obat" if medicine else "Tambah Obat",
            "Lengkapi master data obat. Perubahan langsung tersedia di seluruh modul.",
            "pill",
            parent,
            width=560,
        )
        self.code = QLineEdit(medicine.get("code", "") if medicine else "")
        self.code.setPlaceholderText("Contoh: 40100")
        self.name = QLineEdit(medicine.get("name", "") if medicine else "")
        self.name.setPlaceholderText("Nama obat")
        self.category = QComboBox()
        self.category.setEditable(True)
        for value in ("Kardiovaskular", "Analgesik", "Antibiotik", "Vitamin", "Antihistamin", "Saluran Cerna", "Kortikosteroid", "Umum"):
            self.category.addItem(value)
        if medicine and medicine.get("category"):
            self.category.setCurrentText(medicine["category"])
        self.unit = QComboBox()
        self.unit.setEditable(True)
        for value in ("Strip", "Box", "Botol", "Tube", "Tablet", "Kapsul", "Sachet"):
            self.unit.addItem(value)
        if medicine and medicine.get("unit"):
            self.unit.setCurrentText(medicine["unit"])
        self.purchase_unit = QComboBox()
        self.purchase_unit.setEditable(True)
        self.purchase_unit.addItems(["Strip", "Box", "Botol", "Tube"])
        if medicine and medicine.get("purchase_unit"):
            self.purchase_unit.setCurrentText(medicine["purchase_unit"])
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 1_000_000_000)
        self.price.setDecimals(0)
        self.price.setPrefix("Rp ")
        self.price.setSingleStep(500)
        self.price.setValue(float(medicine.get("price", 0)) if medicine else 0)
        self.min_stock = QSpinBox()
        self.min_stock.setRange(0, 1_000_000)
        self.min_stock.setValue(int(medicine.get("min_stock", 0)) if medicine else 0)
        self.safety_stock = QSpinBox()
        self.safety_stock.setRange(0, 1_000_000)
        self.safety_stock.setValue(int(medicine.get("safety_stock", 0)) if medicine else 0)
        self.lead_time = QSpinBox()
        self.lead_time.setRange(0, 365)
        self.lead_time.setSuffix(" hari")
        self.lead_time.setValue(int(medicine.get("lead_time_days", 7)) if medicine else 7)
        self.system_stock = QSpinBox()
        self.system_stock.setRange(0, 1_000_000)
        self.system_stock.setValue(int(medicine.get("system_stock", 0)) if medicine else 0)
        self.physical_stock = QSpinBox()
        self.physical_stock.setRange(0, 1_000_000)
        self.physical_stock.setValue(int(medicine.get("physical_stock", 0)) if medicine else 0)
        self.priority = QCheckBox("Tandai sebagai obat prioritas untuk analisis")
        self.priority.setChecked(bool(medicine.get("is_priority")) if medicine else False)
        self.row(
            Field("Kode obat", self.code, required=True),
            Field("Nama obat", self.name, required=True),
            ratios=(1, 2),
        )
        self.row(Field("Kategori", self.category), Field("Satuan", self.unit))
        self.row(Field("Harga jual", self.price), Field("Satuan pembelian", self.purchase_unit))
        self.row(
            Field("Minimum stok", self.min_stock),
            Field("Stok pengaman", self.safety_stock),
            Field("Lead time", self.lead_time),
        )
        self.row(Field("Stok sistem", self.system_stock), Field("Stok fisik", self.physical_stock))
        self.form.addWidget(self.priority)
        if not medicine:
            self.note("Stok awal dicatat sebagai stok sistem dan fisik. Riwayat perubahan tersedia di Manajemen Stok.", "info")
        self.bind_save(self._save_medicine)

    def _save_medicine(self) -> bool:
        payload = {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "category": self.category.currentText().strip() or "Umum",
            "unit": self.unit.currentText().strip() or "Strip",
            "price": float(self.price.value()),
            "min_stock": int(self.min_stock.value()),
            "safety_stock": int(self.safety_stock.value()),
            "lead_time_days": int(self.lead_time.value()),
            "purchase_unit": self.purchase_unit.currentText().strip() or "Strip",
            "is_priority": self.priority.isChecked(),
        }
        if not payload["code"] or len(payload["name"]) < 2:
            self.show_error("Kode dan nama obat wajib diisi.")
            return False
        self.set_busy(True)

        def task() -> Any:
            if self.medicine:
                return self.api.put(f"/medicines/{self.medicine['id']}", payload)
            payload["system_stock"] = int(self.system_stock.value())
            payload["physical_stock"] = int(self.physical_stock.value())
            return self.api.post("/medicines", payload)

        self._submit_async(task, lambda _result: self.on_saved() if self.on_saved else None)
        return False


class SaleDialog(FormDialog):
    def __init__(
        self,
        api,
        medicines: list[dict],
        sale: dict | None = None,
        parent: QWidget | None = None,
        on_saved: Callable[[], None] | None = None,
    ) -> None:
        self.api = api
        self.sale = sale
        self.on_saved = on_saved
        super().__init__(
            "Ubah Transaksi" if sale else "Tambah Penjualan",
            "Catat transaksi penjualan. Total dihitung otomatis dari jumlah dan harga satuan.",
            "shopping-bag",
            parent,
            width=540,
        )
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.date.setDate(to_qdate(sale.get("sale_date") if sale else None))
        self.medicine = QComboBox()
        for item in medicines:
            self.medicine.addItem(f"{item['name']} · {item.get('unit', '')}", item)
        if sale:
            index = self.medicine.findData(next((m for m in medicines if m["id"] == sale.get("medicine_id")), None))
            if index >= 0:
                self.medicine.setCurrentIndex(index)
        self.code = QLineEdit(sale.get("transaction_code", "") if sale else "")
        self.code.setPlaceholderText("Kosongkan untuk dibuat otomatis")
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1_000_000)
        self.quantity.setValue(int(sale.get("quantity", 1)) if sale else 1)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 1_000_000_000)
        self.price.setDecimals(0)
        self.price.setPrefix("Rp ")
        self.price.setSingleStep(500)
        self.price.setValue(float(sale.get("unit_price", 0)) if sale else 0)
        self.total = QLabel("Rp 0")
        self.total.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {theme.tokens['primary']};")
        self.field("Tanggal transaksi", self.date, required=True)
        self.field("Obat", self.medicine, required=True)
        self.field("ID transaksi", self.code)
        self.row(Field("Jumlah", self.quantity), Field("Harga satuan", self.price))
        total_row = QHBoxLayout()
        total_row.addWidget(_label("Total"))
        total_row.addStretch(1)
        total_row.addWidget(self.total)
        self.form.addLayout(total_row)
        self.quantity.valueChanged.connect(self._update_total)
        self.price.valueChanged.connect(self._update_total)
        self.medicine.currentIndexChanged.connect(self._medicine_changed)
        self._medicine_changed()
        self._update_total()
        self.note("Penjualan baru langsung memengaruhi data analitik dan prediksi berikutnya.", "info")
        self.bind_save(self._save_sale)

    def _medicine_changed(self) -> None:
        medicine = self.medicine.currentData()
        if medicine and not self.sale:
            self.price.setValue(float(medicine.get("price", 0)))
        self._update_total()

    def _update_total(self) -> None:
        total = float(self.quantity.value()) * float(self.price.value())
        self.total.setText(rupiah(total))

    def _save_sale(self) -> bool:
        medicine = self.medicine.currentData()
        if not medicine:
            self.show_error("Pilih obat terlebih dahulu.")
            return False
        if self.price.value() <= 0:
            self.show_error("Harga satuan harus lebih dari nol.")
            return False
        payload = {
            "sale_date": from_qdate(self.date.date()),
            "medicine_id": medicine["id"],
            "quantity": int(self.quantity.value()),
            "unit_price": float(self.price.value()),
        }
        self.set_busy(True)

        def task() -> Any:
            if self.sale:
                return self.api.put(f"/sales/{self.sale['id']}", payload)
            payload["transaction_code"] = self.code.text().strip()
            return self.api.post("/sales", payload)

        self._submit_async(task, lambda _result: self.on_saved() if self.on_saved else None)
        return False


class WeatherDialog(FormDialog):
    def __init__(self, api, weather: dict | None = None, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.weather = weather
        self.on_saved = on_saved
        super().__init__(
            "Ubah Data Cuaca" if weather else "Tambah Data Cuaca",
            "Data cuaca harian digunakan sebagai fitur tambahan pada model permintaan.",
            "cloud-rain",
            parent,
            width=470,
        )
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.date.setDate(to_qdate(weather.get("weather_date") if weather else None))
        self.date.setEnabled(not bool(weather))
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-10, 60)
        self.temperature.setDecimals(1)
        self.temperature.setSuffix(" °C")
        self.temperature.setValue(float(weather.get("temperature", 27)) if weather else 27)
        self.rainfall = QDoubleSpinBox()
        self.rainfall.setRange(0, 1000)
        self.rainfall.setDecimals(1)
        self.rainfall.setSuffix(" mm")
        self.rainfall.setValue(float(weather.get("rainfall", 0)) if weather else 0)
        self.humidity = QDoubleSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setDecimals(1)
        self.humidity.setSuffix(" %")
        self.humidity.setValue(float(weather.get("humidity", 80)) if weather else 80)
        self.field("Tanggal", self.date, required=True)
        self.row(Field("Suhu rata-rata", self.temperature), Field("Curah hujan", self.rainfall))
        self.field("Kelembapan", self.humidity)
        self.note("Satu tanggal hanya boleh memiliki satu catatan cuaca.", "info")
        self.bind_save(self._save_weather)

    def _save_weather(self) -> bool:
        payload = {
            "temperature": float(self.temperature.value()),
            "rainfall": float(self.rainfall.value()),
            "humidity": float(self.humidity.value()),
        }
        self.set_busy(True)

        def task() -> Any:
            if self.weather:
                return self.api.put(f"/weather/{self.weather['id']}", payload)
            payload["weather_date"] = from_qdate(self.date.date())
            return self.api.post("/weather", payload)

        self._submit_async(task, lambda _result: self.on_saved() if self.on_saved else None)
        return False


class StockAdjustDialog(FormDialog):
    def __init__(self, api, medicine: dict, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.medicine = medicine
        self.on_saved = on_saved
        super().__init__(
            "Penyesuaian Stok",
            f"{medicine.get('name', '')} · stok fisik saat ini {medicine.get('physical_stock', 0)} {medicine.get('unit', '')}",
            "boxes",
            parent,
            width=450,
            save_text="Simpan Stok",
        )
        self.system_stock = QSpinBox()
        self.system_stock.setRange(0, 10_000_000)
        self.system_stock.setValue(int(medicine.get("system_stock", 0)))
        self.physical_stock = QSpinBox()
        self.physical_stock.setRange(0, 10_000_000)
        self.physical_stock.setValue(int(medicine.get("physical_stock", 0)))
        self.change_type = QComboBox()
        for value, label in (
            ("opname", "Stock opname"),
            ("penambahan", "Penambahan"),
            ("pengurangan", "Pengurangan"),
            ("koreksi", "Koreksi"),
        ):
            self.change_type.addItem(label, value)
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Alasan penyesuaian (wajib, minimal 3 karakter)")
        self.note_edit.setFixedHeight(74)
        self.field("Stok sistem", self.system_stock)
        self.field("Stok fisik", self.physical_stock)
        self.field("Jenis perubahan", self.change_type)
        self.field("Catatan", self.note_edit, required=True)
        self.bind_save(self._save_adjustment)

    def _save_adjustment(self) -> bool:
        note = self.note_edit.toPlainText().strip()
        if len(note) < 3:
            self.show_error("Catatan penyesuaian wajib diisi (minimal 3 karakter).")
            return False
        payload = {
            "system_stock": int(self.system_stock.value()),
            "physical_stock": int(self.physical_stock.value()),
            "change_type": self.change_type.currentData(),
            "note": note,
            "last_opname_date": from_qdate(QDate.currentDate()) if self.change_type.currentData() == "opname" else None,
        }
        self.set_busy(True)
        self._submit_async(
            lambda: self.api.post(f"/inventory/{self.medicine['id']}/adjust", payload),
            lambda _result: self.on_saved() if self.on_saved else None,
        )
        return False


class ProcurementEditDialog(FormDialog):
    def __init__(self, api, recommendation_id: int, item: dict, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.recommendation_id = recommendation_id
        self.item = item
        self.on_saved = on_saved
        super().__init__(
            "Ubah Jumlah Pembelian",
            f"{item.get('name', '')} · saran sistem {item.get('recommended_qty', 0)} {item.get('unit', '')}",
            "pencil-line",
            parent,
            width=440,
        )
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 1_000_000)
        self.quantity.setValue(int(item.get("final_qty", item.get("recommended_qty", 0))))
        self.quantity.setSuffix(f" {item.get('unit', '')}")
        self.reason = QTextEdit()
        self.reason.setPlaceholderText("Alasan perubahan jumlah (wajib)")
        self.reason.setFixedHeight(72)
        self.field("Jumlah final", self.quantity, required=True)
        self.field("Alasan perubahan", self.reason, required=True)
        self.bind_save(self._save_edit)

    def _save_edit(self) -> bool:
        reason = self.reason.toPlainText().strip()
        if len(reason) < 3:
            self.show_error("Alasan perubahan wajib diisi (minimal 3 karakter).")
            return False
        payload = {"final_qty": int(self.quantity.value()), "reason": reason}
        self.set_busy(True)
        self._submit_async(
            lambda: self.api.patch(f"/procurement/{self.recommendation_id}/items/{self.item['id']}", payload),
            lambda _result: self.on_saved() if self.on_saved else None,
        )
        return False


class ChangePasswordDialog(FormDialog):
    def __init__(self, api, parent: QWidget | None = None) -> None:
        self.api = api
        super().__init__(
            "Ganti Password",
            "Gunakan password baru yang kuat dan tidak dipakai di layanan lain.",
            "key-round",
            parent,
            width=430,
            save_text="Perbarui Password",
        )
        self.old = QLineEdit()
        self.old.setEchoMode(QLineEdit.EchoMode.Password)
        self.new = QLineEdit()
        self.new.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.field("Password lama", self.old, required=True)
        self.field("Password baru", self.new, required=True, hint="Minimal 8 karakter.")
        self.field("Ulangi password baru", self.confirm, required=True)
        self.bind_save(self._save_password)

    def _save_password(self) -> bool:
        if len(self.new.text()) < 8:
            self.show_error("Password baru minimal 8 karakter.")
            return False
        if self.new.text() != self.confirm.text():
            self.show_error("Konfirmasi password tidak sama.")
            return False
        payload = {"old_password": self.old.text(), "new_password": self.new.text()}
        self.set_busy(True)
        self._submit_async(lambda: self.api.post("/auth/change-password", payload))
        return False


class UserDialog(FormDialog):
    def __init__(self, api, user: dict | None = None, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.user = user
        self.on_saved = on_saved
        super().__init__(
            "Ubah Akun" if user else "Tambah Akun",
            "Akun Admin dapat mengelola data master, import, backup, dan pengguna.",
            "user-round",
            parent,
            width=460,
        )
        self.username = QLineEdit(user.get("username", "") if user else "")
        self.username.setEnabled(not bool(user))
        self.full_name = QLineEdit(user.get("full_name", "") if user else "")
        self.email = QLineEdit((user or {}).get("email") or "")
        self.role = QComboBox()
        self.role.addItems(["Admin", "Petugas"])
        if user and user.get("role"):
            self.role.setCurrentText(user["role"])
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Kosongkan jika tidak diubah" if user else "Minimal 8 karakter")
        self.active = QCheckBox("Akun aktif")
        self.active.setChecked(bool(user.get("is_active", True)) if user else True)
        self.field("Nama pengguna", self.username, required=True)
        self.field("Nama lengkap", self.full_name, required=True)
        self.field("Email", self.email)
        self.field("Role", self.role)
        self.field("Password", self.password, required=not bool(user))
        self.form.addWidget(self.active)
        self.bind_save(self._save_user)

    def _save_user(self) -> bool:
        payload: dict[str, Any] = {
            "full_name": self.full_name.text().strip(),
            "email": self.email.text().strip() or None,
            "role": self.role.currentText().lower(),
            "is_active": self.active.isChecked(),
        }
        if self.password.text():
            payload["password"] = self.password.text()
        if not self.user and len(self.password.text()) < 8:
            self.show_error("Password minimal 8 karakter.")
            return False
        if not self.user:
            payload.update({
                "username": self.username.text().strip(),
                "password": self.password.text(),
            })
        self.set_busy(True)
        if self.user:
            self._submit_async(lambda: self.api.put(f"/users/{self.user['id']}", payload), lambda _result: self.on_saved() if self.on_saved else None)
        else:
            self._submit_async(lambda: self.api.post("/users", payload), lambda _result: self.on_saved() if self.on_saved else None)
        return False


class ServerDialog(FormDialog):
    def __init__(self, api, parent: QWidget | None = None, on_saved: Callable[[], None] | None = None) -> None:
        self.api = api
        self.on_saved = on_saved
        super().__init__(
            "Koneksi Server",
            "Aplikasi desktop terhubung ke backend FastAPI yang sama dengan versi web.",
            "server",
            parent,
            width=470,
            save_text="Simpan & Uji",
        )
        self.url = QLineEdit(api.base_url)
        self.url.setPlaceholderText("http://127.0.0.1:8000/api")
        self.field("Alamat API", self.url, required=True, hint="Gunakan http://127.0.0.1:8000/api untuk backend lokal.")
        self.status = InlineBanner("Klik Simpan & Uji untuk memeriksa koneksi.", "info")
        self.form.addWidget(self.status)
        self.bind_save(self._save_server)

    def _save_server(self) -> bool:
        url = self.url.text().strip().rstrip("/")
        if not url.startswith("http"):
            self.show_error("Alamat API harus diawali http:// atau https://")
            return False
        old = self.api.base_url
        self.api.set_base_url(url)
        self.set_busy(True)

        def task() -> Any:
            return self.api.health(timeout=5)

        def ok(health: dict[str, Any]) -> None:
            self.set_busy(False)
            self.status.set_message(
                f"Terhubung. Versi {health.get('version', '-')} · {health.get('medicines', 0)} obat.",
                "success",
            )
            if self.on_saved:
                self.on_saved()
            self.accept()

        def bad(message: str, _status: int) -> None:
            self.api.set_base_url(old)
            self.set_busy(False)
            self.status.set_message(message, "danger")

        self._runner.submit(task, ok, bad)
        return False
