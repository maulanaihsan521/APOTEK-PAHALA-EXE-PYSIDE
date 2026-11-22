# -*- coding: utf-8 -*-
"""Generate the technical PDF: frameworks, libraries, and data methods.

Output: docs/PANDUAN_FRAMEWORK_DAN_METODE_DATA.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "PANDUAN_FRAMEWORK_DAN_METODE_DATA.pdf"
LOGO = ROOT / "assets" / "logo.png"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_DIR = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("SegoeUI", str(FONT_DIR / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("SegoeUI-Bold", str(FONT_DIR / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("SegoeUI-Italic", str(FONT_DIR / "segoeuii.ttf")))
pdfmetrics.registerFont(TTFont("SegoeUI-BoldItalic", str(FONT_DIR / "segoeuiz.ttf")))
pdfmetrics.registerFontFamily(
    "SegoeUI",
    normal="SegoeUI",
    bold="SegoeUI-Bold",
    italic="SegoeUI-Italic",
    boldItalic="SegoeUI-BoldItalic",
)
pdfmetrics.registerFont(TTFont("Consolas", str(FONT_DIR / "consola.ttf")))
pdfmetrics.registerFont(TTFont("Consolas-Bold", str(FONT_DIR / "consolab.ttf")))

# ---------------------------------------------------------------------------
# Palette and geometry
# ---------------------------------------------------------------------------
INK = colors.HexColor("#18343D")
BODY = colors.HexColor("#2D454E")
MUTED = colors.HexColor("#617A83")
TEAL = colors.HexColor("#087F6B")
DARK = colors.HexColor("#0B4F45")
ACCENT = colors.HexColor("#20B58A")
MINT = colors.HexColor("#E8F5F1")
SOFT = colors.HexColor("#F3F7F8")
LINE = colors.HexColor("#D9E5E9")
AMBER = colors.HexColor("#F2A93B")
WHITE = colors.white
CANVAS = colors.HexColor("#F7FAFA")

PAGE_W, PAGE_H = A4
MARGIN = 44
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------
def style(name: str, **kwargs) -> ParagraphStyle:
    base = dict(fontName="SegoeUI", fontSize=9.5, leading=14.1, textColor=BODY)
    base.update(kwargs)
    return ParagraphStyle(name=name, **base)


body = style("Body", alignment=TA_JUSTIFY, spaceAfter=5.2)
body_tight = style("BodyTight", alignment=TA_JUSTIFY, spaceAfter=2.5)
small = style("Small", fontSize=8.4, leading=12.0, textColor=MUTED, alignment=TA_JUSTIFY)
caption = style("Caption", fontSize=7.8, leading=10.4, textColor=MUTED, alignment=TA_LEFT)
bullet = style(
    "Bullet",
    fontSize=9.3,
    leading=13.4,
    leftIndent=13,
    bulletIndent=2,
    spaceAfter=2.6,
    alignment=TA_LEFT,
)
bullet_small = style(
    "BulletSmall",
    fontSize=8.6,
    leading=12.2,
    leftIndent=12,
    bulletIndent=1,
    spaceAfter=1.8,
    alignment=TA_LEFT,
)
h1 = style(
    "H1",
    fontName="SegoeUI-Bold",
    fontSize=15.5,
    leading=19,
    textColor=WHITE,
    backColor=DARK,
    borderPadding=(6, 9, 6, 9),
    spaceBefore=6,
    spaceAfter=10,
    keepWithNext=True,
    alignment=TA_LEFT,
)
h2 = style(
    "H2",
    fontName="SegoeUI-Bold",
    fontSize=11.4,
    leading=14.2,
    textColor=DARK,
    backColor=MINT,
    borderPadding=(3.5, 6, 3.5, 6),
    spaceBefore=10,
    spaceAfter=5,
    keepWithNext=True,
    alignment=TA_LEFT,
)
h3 = style(
    "H3",
    fontName="SegoeUI-Bold",
    fontSize=9.9,
    leading=13,
    textColor=TEAL,
    spaceBefore=7,
    spaceAfter=2.5,
    keepWithNext=True,
    alignment=TA_LEFT,
)
table_header = style(
    "TableHeader",
    fontName="SegoeUI-Bold",
    fontSize=7.7,
    leading=9.8,
    textColor=WHITE,
    alignment=TA_LEFT,
)
table_cell = style(
    "TableCell",
    fontSize=7.7,
    leading=10.2,
    textColor=BODY,
    alignment=TA_LEFT,
)
table_cell_small = style(
    "TableCellSmall",
    fontSize=7.25,
    leading=9.6,
    textColor=BODY,
    alignment=TA_LEFT,
)
table_cell_center = style(
    "TableCellCenter",
    fontSize=7.7,
    leading=10.2,
    textColor=BODY,
    alignment=TA_CENTER,
)
callout_title = style(
    "CalloutTitle",
    fontName="SegoeUI-Bold",
    fontSize=8.6,
    leading=11.2,
    textColor=DARK,
    spaceAfter=2,
)
callout_body = style(
    "CalloutBody",
    fontSize=8.5,
    leading=12.2,
    textColor=BODY,
    alignment=TA_JUSTIFY,
)
code_style = ParagraphStyle(
    "Code",
    fontName="Consolas",
    fontSize=7.7,
    leading=10.2,
    textColor=colors.HexColor("#173B42"),
)
cover_eyebrow = style(
    "CoverEyebrow",
    fontName="SegoeUI-Bold",
    fontSize=8.2,
    leading=11,
    textColor=TEAL,
    spaceAfter=5,
)
cover_title = style(
    "CoverTitle",
    fontName="SegoeUI-Bold",
    fontSize=28,
    leading=33,
    textColor=INK,
    spaceAfter=6,
)
cover_sub = style(
    "CoverSub",
    fontName="SegoeUI",
    fontSize=13.2,
    leading=18,
    textColor=TEAL,
    spaceAfter=4,
)
cover_body = style(
    "CoverBody",
    fontSize=9.7,
    leading=15,
    textColor=MUTED,
    alignment=TA_LEFT,
)
cover_meta_label = style(
    "CoverMetaLabel",
    fontName="SegoeUI-Bold",
    fontSize=7.2,
    leading=9,
    textColor=TEAL,
)
cover_meta_value = style(
    "CoverMetaValue",
    fontSize=8.4,
    leading=11.6,
    textColor=INK,
)
kpi_value = style(
    "KpiValue",
    fontName="SegoeUI-Bold",
    fontSize=20,
    leading=23,
    textColor=DARK,
    alignment=TA_LEFT,
)
kpi_label = style(
    "KpiLabel",
    fontName="SegoeUI-Bold",
    fontSize=7.4,
    leading=9.6,
    textColor=TEAL,
)
kpi_sub = style(
    "KpiSub",
    fontSize=7.2,
    leading=9.4,
    textColor=MUTED,
)
box_title = style(
    "BoxTitle",
    fontName="SegoeUI-Bold",
    fontSize=8.4,
    leading=10.8,
    textColor=DARK,
    spaceAfter=3,
)
box_item = style(
    "BoxItem",
    fontSize=7.5,
    leading=10.2,
    textColor=BODY,
    leftIndent=7,
    bulletIndent=0,
)
arrow_style = style(
    "Arrow",
    fontName="SegoeUI-Bold",
    fontSize=18,
    leading=20,
    textColor=ACCENT,
    alignment=TA_CENTER,
)
toc0 = style(
    "TOC0",
    fontName="SegoeUI",
    fontSize=9.4,
    leading=17,
    textColor=INK,
    leftIndent=0,
    firstLineIndent=0,
)
toc1 = style(
    "TOC1",
    fontName="SegoeUI",
    fontSize=8.2,
    leading=12.6,
    textColor=MUTED,
    leftIndent=14,
    firstLineIndent=0,
)

# ---------------------------------------------------------------------------
# Small builders
# ---------------------------------------------------------------------------
def p(text: str, st=body) -> Paragraph:
    return Paragraph(text, st)


def bullets(items: list[str], st=bullet) -> list[Paragraph]:
    return [Paragraph(item, st, bulletText="•") for item in items]


def rule(color=TEAL, thickness=2.2, width=CONTENT_W) -> Table:
    t = Table([[""]], colWidths=[width], rowHeights=[thickness])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def data_table(
    rows: list[list],
    widths: list[float],
    *,
    header: bool = True,
    font: ParagraphStyle = table_cell,
    zebra: bool = True,
    repeat: int = 1,
    align_center_cols: tuple[int, ...] = (),
    pad: float = 4.2,
) -> Table:
    cooked: list[list] = []
    for r_index, row in enumerate(rows):
        cooked_row = []
        for c_index, cell in enumerate(row):
            if isinstance(cell, str):
                st = table_header if (header and r_index == 0) else font
                cooked_row.append(Paragraph(cell, st))
            else:
                cooked_row.append(cell)
        cooked.append(cooked_row)
    table = Table(
        cooked,
        colWidths=widths,
        repeatRows=repeat if header else 0,
        hAlign="LEFT",
    )
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.8),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, DARK),
        ]
    if zebra:
        start = 1 if header else 0
        for i in range(start, len(cooked)):
            if (i - start) % 2 == 1:
                commands.append(("BACKGROUND", (0, i), (-1, i), SOFT))
    for col in align_center_cols:
        commands.append(("ALIGN", (col, 0), (col, -1), "CENTER"))
    table.setStyle(TableStyle(commands))
    return table


def callout(title: str, text: str, color: str = "#087F6B", bg: str = "#E8F5F1") -> Table:
    inner = [Paragraph(title, callout_title), Paragraph(text, callout_body)]
    table = Table([[inner]], colWidths=[CONTENT_W])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                ("LINEBEFORE", (0, 0), (0, -1), 3.2, colors.HexColor(color)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def code_block(text: str) -> Table:
    table = Table([[Preformatted(text.strip("\n"), code_style)]], colWidths=[CONTENT_W])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F6F7")),
                ("BOX", (0, 0), (-1, -1), 0.45, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def kpi_card(value: str, label: str, sub: str, accent=TEAL) -> Table:
    inner = [
        [Paragraph(value, kpi_value)],
        [Paragraph(label, kpi_label)],
        [Paragraph(sub, kpi_sub)],
    ]
    card = Table(inner, colWidths=[(CONTENT_W - 16) / 3])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LINEABOVE", (0, 0), (-1, 0), 3, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return card


def kpi_grid(cards: list[Table]) -> Table:
    rows = [cards[i : i + 3] for i in range(0, len(cards), 3)]
    for row in rows:
        while len(row) < 3:
            row.append("")
    grid = Table(rows, colWidths=[(CONTENT_W - 12) / 3] * 3)
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return grid


def layer_box(title: str, items: list[str], accent=TEAL) -> Table:
    content = [[Paragraph(title, box_title)]]
    for item in items:
        content.append([Paragraph(item, box_item, bulletText="•")])
    box = Table(content, colWidths=[142])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LINEABOVE", (0, 0), (-1, 0), 3, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return box


# ---------------------------------------------------------------------------
# Document template
# ---------------------------------------------------------------------------
class ApotekDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self._h1 = 0
        self._h2 = 0
        cover_frame = Frame(
            MARGIN,
            46,
            CONTENT_W,
            PAGE_H - 46 - 46,
            id="cover",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        content_frame = Frame(
            MARGIN,
            58,
            CONTENT_W,
            PAGE_H - 58 - 64,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="Cover", frames=[cover_frame], onPage=self.draw_cover),
                PageTemplate(id="Content", frames=[content_frame], onPage=self.draw_content),
            ]
        )

    def draw_cover(self, canv, doc):
        canv.saveState()
        canv.setFillColor(CANVAS)
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        # Left accent bar
        canv.setFillColor(TEAL)
        canv.rect(0, 0, 8 * mm, PAGE_H, stroke=0, fill=1)
        # Decorative circles (light solid colors, not alpha, for consistent PDF rendering)
        canv.setFillColor(colors.HexColor("#E4F1ED"))
        canv.circle(PAGE_W - 20, PAGE_H - 76, 118, stroke=0, fill=1)
        canv.setFillColor(colors.HexColor("#E9F6F0"))
        canv.circle(PAGE_W - 58, 104, 66, stroke=0, fill=1)
        # Bottom rule and credit
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.7)
        canv.line(MARGIN, 38, PAGE_W - MARGIN, 38)
        canv.setFont("SegoeUI", 7.2)
        canv.setFillColor(MUTED)
        canv.drawString(
            MARGIN,
            24,
            "Dokumen teknis internal • Apotek Pahala • Versi 1.0.0",
        )
        canv.restoreState()

    def draw_content(self, canv, doc):
        canv.saveState()
        # Header
        canv.setFillColor(TEAL)
        canv.rect(MARGIN, PAGE_H - 35, 6, 6, stroke=0, fill=1)
        canv.setFont("SegoeUI-Bold", 7.4)
        canv.setFillColor(TEAL)
        canv.drawString(MARGIN + 11, PAGE_H - 35, "APOTEK PAHALA")
        canv.setFont("SegoeUI", 7.0)
        canv.setFillColor(MUTED)
        canv.drawRightString(
            PAGE_W - MARGIN,
            PAGE_H - 35,
            "DOKUMEN TEKNIS  •  FRAMEWORK DAN METODE DATA",
        )
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.55)
        canv.line(MARGIN, PAGE_H - 42, PAGE_W - MARGIN, PAGE_H - 42)
        # Footer
        canv.line(MARGIN, 40, PAGE_W - MARGIN, 40)
        canv.setFont("SegoeUI", 7.1)
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN, 27, "Versi 1.0.0  •  22 November 2026")
        canv.drawRightString(PAGE_W - MARGIN, 27, f"Halaman {doc.page}")
        canv.restoreState()

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        name = flowable.style.name
        text = flowable.getPlainText()
        if name == "H1":
            self._h1 += 1
            key = f"h1-{self._h1}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
            self.notify("TOCEntry", (0, text, self.page))
        elif name == "H2":
            self._h2 += 1
            key = f"h2-{self._h2}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=1, closed=True)


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------
story: list = []

# ------------------------------- Cover -------------------------------------
story += [
    Spacer(1, 30),
    Image(str(LOGO), width=62, height=62, hAlign="LEFT"),
    Spacer(1, 30),
    p("DOKUMEN TEKNIS  •  VERSI 1.0.0", cover_eyebrow),
    p("Framework, Library,<br/>dan Metode Pengolahan Data", cover_title),
    Spacer(1, 2),
    p("Apotek Pahala — Pharmacy Intelligence", cover_sub),
    Spacer(1, 10),
    rule(TEAL, 2.6, 86),
    Spacer(1, 16),
    p(
        "Penjelasan fungsi setiap framework dan library yang dipakai, "
        "serta metode input, pembersihan, validasi, transformasi, dan "
        "pemodelan data aktual dari file sumber sampai siap digunakan.",
        cover_body,
    ),
    Spacer(1, 26),
]

cover_meta = [
    [
        [Paragraph("LINGKUP", cover_meta_label), Paragraph("Backend, desktop, mobile web, pipeline data, pemodelan, dan packaging", cover_meta_value)],
        [Paragraph("PLATFORM", cover_meta_label), Paragraph("Windows 10/11 untuk pengembangan • Windows 7 SP1 x64 untuk paket", cover_meta_value)],
    ],
    [
        [Paragraph("SUMBER ACUAN", cover_meta_label), Paragraph("Kode sumber, konfigurasi, dan dataset aktual di repositori proyek", cover_meta_value)],
        [Paragraph("TANGGAL", cover_meta_label), Paragraph("22 November 2026", cover_meta_value)],
    ],
]
meta_table = Table(cover_meta, colWidths=[(CONTENT_W - 10) / 2] * 2)
meta_table.setStyle(
    TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]
    )
)
story += [
    meta_table,
    Spacer(1, 20),
    callout(
        "Cara membaca dokumen",
        "Bagian 1–2 menjelaskan komponen dan teknologi beserta fungsinya. "
        "Bagian 3–6 menjelaskan perlakuan data secara berurutan: input, "
        "pembersihan, fitur, lalu model. Bagian 7–8 memuat perintah reproduksi, "
        "peta berkas, batasan, dan tata kelola.",
    ),
    Spacer(1, 18),
    p(
        "<b>Tim Capstone Design — Sistem Informasi, Universitas Telkom • 2026</b>",
        style("CoverCredit", fontSize=8.6, leading=11.5, textColor=INK),
    ),
    p(
        "Disusun dari implementasi aktual, bukan deskripsi generik. "
        "Angka evaluasi berasal dari pelatihan terakhir pada data yang tersedia.",
        style("CoverNote", fontSize=7.6, leading=10.2, textColor=MUTED),
    ),
    Spacer(1, 34),
    rule(LINE, 0.8),
    Spacer(1, 12),
    p(
        "Satu backend. Satu database. Dua antarmuka.",
        style(
            "CoverStatement",
            fontName="SegoeUI-Italic",
            fontSize=14.5,
            leading=19,
            textColor=TEAL,
        ),
    ),
    Spacer(1, 3),
    p(
        "Desktop PySide untuk analisis mendalam; mobile PWA untuk akses cepat "
        "dari perangkat lain di jaringan yang sama.",
        style("CoverStatementSub", fontSize=8.4, leading=11.5, textColor=MUTED),
    ),
    NextPageTemplate("Content"),
    PageBreak(),
]

# ------------------------------- Ringkasan ---------------------------------
story += [
    p("Ringkasan Eksekutif", h1),
    p(
        "Apotek Pahala adalah aplikasi analitik persediaan obat dengan satu backend "
        "FastAPI dan dua antarmuka: desktop PySide serta mobile web React yang "
        "dapat dipasang sebagai PWA. Keduanya memakai database SQLite dan endpoint "
        "REST yang sama, sehingga angka dashboard, prediksi, stok, pengadaan, dan "
        "laporan selalu berasal dari satu sumber kebenaran.",
    ),
    p(
        "Data aktual berasal dari 1.085 berkas stok opname <b>ST*.DBF</b>, 2.894 berkas "
        "pembelian <b>BL*.DBF</b>, dan cuaca harian NASA POWER. Folder sumber tidak "
        "memuat transaksi kasir, sehingga permintaan diestimasi dari perubahan stok "
        "ditambah pembelian bersih, lalu dibersihkan, divalidasi, diagregasi mingguan, "
        "dan dipakai untuk melatih tiga model regresi.",
    ),
    Spacer(1, 6),
    kpi_grid(
        [
            kpi_card("20", "JENIS OBAT", "6 obat prioritas"),
            kpi_card("4.478", "BARIS PERMINTAAN", "Mingguan, 2022–2026"),
            kpi_card("1.727", "HARI CUACA", "NASA POWER MERRA-2"),
            kpi_card("3", "ALGORITMA", "RF, Decision Tree, Linear"),
            kpi_card("8", "MODUL APLIKASI", "Desktop dan mobile"),
            kpi_card("2", "ANTARMUKA", "PySide dan React PWA"),
        ]
    ),
    Spacer(1, 8),
    callout(
        "Tiga hal yang perlu dipahami",
        "<b>Pertama</b>, angka permintaan adalah estimasi operasional, bukan penjualan "
        "kasir harian. <b>Kedua</b>, pembersihan data tidak mengarang nilai: interval "
        "yang tidak valid dibuang atau diinterpolasi hanya bila minggu tersebut tidak "
        "tercakup penuh. <b>Ketiga</b>, model dipilih per obat memakai WAPE data uji "
        "kronologis, bukan akurasi yang diklaim untuk masa depan.",
        "#F2A93B",
        "#FFF6E7",
    ),
    Spacer(1, 8),
    p("Daftar Isi", h2),
]

toc = TableOfContents()
toc.levelStyles = [toc0]
toc.dotsMinLevel = 0
story += [toc, PageBreak()]

# ------------------------------- 1. Sistem ---------------------------------
story += [
    p("1. Gambaran Sistem", h1),
    p(
        "Arsitektur aplikasi sengaja dibuat sederhana: satu API, satu database, dan "
        "dua klien. Pemisahan ini memungkinkan desktop dan mobile menampilkan data "
        "yang identik tanpa sinkronisasi manual, sekaligus menjaga paket Windows 7 "
        "tetap dapat berjalan tanpa Python atau Node.js di komputer target.",
    ),
    p("1.1 Lapisan aplikasi", h2),
]

presentation = layer_box(
    "PRESENTASI",
    [
        "Desktop PySide6 / PySide2",
        "Mobile web React + PWA",
        "requests / fetch ke REST API",
    ],
    TEAL,
)
application = layer_box(
    "APLIKASI",
    [
        "FastAPI + Uvicorn",
        "JWT, RBAC Admin/Petugas",
        "Layanan import, laporan, ML",
    ],
    ACCENT,
)
data_layer = layer_box(
    "DATA DAN ANALITIK",
    [
        "SQLite satu sumber data",
        "pandas, NumPy, scikit-learn",
        "ReportLab, OpenPyXL",
    ],
    AMBER,
)
arch = Table(
    [[presentation, p("→", arrow_style), application, p("→", arrow_style), data_layer]],
    colWidths=[148, 22, 148, 22, 148],
)
arch.setStyle(
    TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )
)
story += [
    arch,
    Spacer(1, 4),
    p(
        "Gambar 1. Alur utama: klien memanggil API, API mengakses SQLite dan pipeline "
        "analitik, lalu mengembalikan JSON atau berkas laporan.",
        caption,
    ),
    Spacer(1, 4),
    p("1.2 Prinsip yang dijaga", h2),
]
story += bullets(
    [
        "<b>Satu sumber kebenaran.</b> Desktop, mobile, dashboard, dan laporan membaca database SQLite yang sama; tidak ada database terpisah per antarmuka.",
        "<b>API-first.</b> Semua operasi data melewati endpoint REST, sehingga aturan validasi dan hak akses diterapkan di server, bukan hanya disembunyikan di UI.",
        "<b>Real data only.</b> Tidak ada fallback ke data demonstrasi. Bila dataset aktual tidak ditemukan, database dibiarkan kosong dan error dicatat.",
        "<b>Dapat direproduksi.</b> Data mentah DBF dipisahkan dari data turunan CSV; setiap proses ekspor menulis <font name='Consolas'>metadata.json</font> berisi metode, periode, dan statistik kualitas.",
        "<b>Kompatibel ke belakang.</b> Kode desktop ditransformasi ke PySide2/Python 3.8 untuk paket Windows 7, sementara pengembangan memakai PySide6/Python 3.14.",
    ]
)
story += [
    Spacer(1, 4),
    p("1.3 Modul fungsional", h2),
    p(
        "Kedelapan modul berikut adalah cakupan aplikasi. Modul yang sama muncul di "
        "desktop dan mobile dengan kedalaman interaksi yang berbeda.",
    ),
]

module_rows = [
    ["Modul", "Fungsi utama", "Keluaran"],
    ["Ringkasan Dashboard", "KPI, tren permintaan, prakiraan, stok kritis, aktivitas", "Kartu KPI dan grafik"],
    ["Prediksi Permintaan", "Latih dan pilih model per obat, evaluasi, prakiraan 1–12 pekan", "Metrik, grafik, ekspor"],
    ["Data Penjualan", "Riwayat estimasi permintaan mingguan, filter, ekspor", "Tabel dan CSV/XLSX"],
    ["Data Cuaca", "Suhu, curah hujan, kelembapan harian", "Tabel dan ekspor"],
    ["Manajemen Stok", "Stock opname, penyesuaian, riwayat pergerakan", "Stok sistem/fisik"],
    ["Rekomendasi Pengadaan", "Formula transparan, edit jumlah, approve/cancel", "Draf dan approval"],
    ["Laporan", "PDF, Excel, CSV untuk enam jenis laporan", "Berkas unduhan"],
    ["Pengaturan", "Profil, model, pengadaan, tampilan, backup/restore, pengguna", "Konfigurasi tersimpan"],
]
story += [
    data_table(module_rows, [108, 268, 131], font=table_cell_small),
    p("Tabel 1. Modul aplikasi dan keluarannya.", caption),
    Spacer(1, 2),
    callout(
        "Catatan arsitektur",
        "Desktop dapat mendeteksi backend yang belum berjalan lalu mencoba menjalankan "
        "<font name='Consolas'>backend/run.py</font> dan menunggu health check. Pada "
        "mode produksi, mobile web hasil build disajikan langsung oleh backend dari "
        "<font name='Consolas'>mobile-web/dist</font>, sehingga tidak perlu Vite.",
    ),
    PageBreak(),
]

# ------------------------------- 2. Framework ------------------------------
story += [
    p("2. Framework dan Library", h1),
    p(
        "Tabel pada bagian ini menjelaskan <b>apa</b> teknologi yang dipakai, "
        "<b>versi</b> yang menjadi acuan, <b>fungsi teknisnya</b>, dan <b>perannya</b> "
        "di Apotek Pahala. Versi pengembangan adalah versi minimum pada "
        "<font name='Consolas'>requirements</font>; paket Windows 7 memakai pin versi "
        "di <font name='Consolas'>packaging/requirements-win7.txt</font>.",
    ),
    p("2.1 Backend dan API", h2),
]

backend_rows = [
    ["Teknologi", "Versi", "Fungsi teknis", "Peran di Apotek Pahala"],
    ["Python", "3.14 dev<br/>3.8.10 Win7", "Runtime bahasa untuk backend, desktop, pipeline data, dan skrip build.", "Menjalankan seluruh kode server, importer, pelatihan model, dan tooling."],
    ["FastAPI", "≥ 0.110", "Framework web ASGI: routing, dependency injection, validasi request, dokumentasi OpenAPI.", "Menyediakan REST API untuk desktop dan mobile, termasuk Swagger di <font name='Consolas'>/api/docs</font>."],
    ["Uvicorn", "≥ 0.29", "Server ASGI yang menjalankan aplikasi FastAPI.", "Menjadi proses backend pada port 8000, baik saat pengembangan maupun paket."],
    ["Pydantic", "≥ 2.6", "Validasi dan serialisasi data berbasis tipe.", "Menjaga bentuk request/response API dan pesan kesalahan tetap konsisten."],
    ["pydantic-settings", "≥ 2.2", "Dukungan konfigurasi berbasis environment.", "Melengkapi pembacaan konfigurasi; kode aktif juga memakai python-dotenv."],
    ["SQLAlchemy", "≥ 2.0", "ORM dan query builder dengan transaksi serta relasi.", "Memetakan tabel obat, penjualan, cuaca, stok, pengadaan, pengguna, dan log."],
    ["SQLite", "stdlib", "Basis data relasional tertanam dalam satu berkas.", "Menyimpan seluruh data aplikasi di <font name='Consolas'>storage/apotek_pahala.db</font>."],
    ["PyJWT", "≥ 2.8", "Encoding dan decoding JSON Web Token.", "Token akses HS256 berisi subjek, peran, dan masa berlaku 12 jam."],
    ["python-multipart", "≥ 0.0.9", "Parser upload multipart/form-data.", "Menerima berkas CSV/XLS/XLSX pada import wizard."],
    ["python-dotenv", "≥ 1.0", "Membaca variabel dari berkas <font name='Consolas'>.env</font>.", "Menjaga secret dan path tidak ditulis langsung di kode."],
    ["pandas", "≥ 2.2", "Struktur DataFrame, agregasi, resampling, pembacaan CSV/Excel.", "Mengolah DBF hasil parsing, membentuk deret mingguan, dan fitur model."],
    ["NumPy", "≥ 1.26", "Array dan operasi numerik.", "Menghitung metrik, transformasi sinus/cosinus, dan operasi prediksi."],
    ["scikit-learn", "≥ 1.4", "Algoritma machine learning dan metrik regresi.", "Melatih Random Forest, Decision Tree, dan Linear Regression."],
    ["OpenPyXL", "≥ 3.1", "Membaca dan menulis workbook Excel.", "Menghasilkan laporan dan ekspor <font name='Consolas'>.xlsx</font>."],
    ["ReportLab", "≥ 4.1", "Menyusun dokumen PDF secara programatik.", "Membuat laporan PDF, termasuk tabel, ringkasan, dan tanda tangan."],
    ["pytest", "≥ 8.0", "Framework pengujian.", "Menjalankan 17 tes integrasi API pada backend."],
    ["httpx", "≥ 0.27", "Klien HTTP untuk pengujian dan integrasi.", "Dipakai test client untuk memanggil endpoint FastAPI."],
]
story += [
    data_table(backend_rows, [82, 58, 178, 189], font=table_cell_small),
    p("Tabel 2. Framework dan library backend.", caption),
    Spacer(1, 2),
    callout(
        "Mengapa FastAPI dan SQLAlchemy?",
        "FastAPI memberi validasi request, dokumentasi otomatis, dan performa ASGI "
        "tanpa boilerplate besar. SQLAlchemy memisahkan model data dari SQL mentah, "
        "sehingga query dashboard, laporan, dan pengadaan tetap konsisten dan mudah "
        "dirawat. SQLite dipilih karena aplikasi berjalan lokal di satu apotek dan "
        "tidak membutuhkan server database terpisah.",
    ),
    PageBreak(),
]

story += [
    p("2.2 Desktop", h2),
]
desktop_rows = [
    ["Teknologi", "Versi", "Fungsi teknis", "Peran di Apotek Pahala"],
    ["PySide6", "≥ 6.7<br/>dev 6.12", "Binding resmi Qt6 untuk Python: widget, layout, dialog, tabel, sinyal.", "Membangun antarmuka desktop delapan modul pada lingkungan pengembangan."],
    ["PySide2", "5.15.2.1", "Binding Qt5 untuk Python 3.8.", "Menjadi dasar paket Windows 7 SP1 x64 yang tidak memerlukan Python."],
    ["Qt Widgets + QSS", "bawaan Qt", "Layout, komponen, dan styling berbasis stylesheet.", "Menyusun tema terang/gelap, token tipografi, tombol, tabel, dan badge."],
    ["requests", "≥ 2.31", "Klien HTTP sederhana.", "Login, CRUD, unduh laporan, dan komunikasi ke backend."],
    ["Aset SVG 2x", "internal", "Ikon vektor dirender pada ukuran 2x lalu diperkecil.", "Menjaga ikon pensil/hapus tetap tajam pada scaling 125%."],
]
story += [
    data_table(desktop_rows, [82, 58, 178, 189], font=table_cell_small),
    p("Tabel 3. Teknologi desktop dan alasan pemakaiannya.", caption),
    Spacer(1, 4),
    p("2.3 Mobile web dan PWA", h2),
]
mobile_rows = [
    ["Teknologi", "Versi", "Fungsi teknis", "Peran di Apotek Pahala"],
    ["React", "19.1", "Library komponen UI berbasis state.", "Membangun halaman Beranda, Prediksi, Stok, dan modul mobile lainnya."],
    ["TypeScript", "5.9", "Superset JavaScript dengan tipe statis.", "Menjaga kontrak data API, props komponen, dan form tetap aman."],
    ["Vite", "7.1", "Dev server, HMR, proxy, dan bundler produksi.", "Melayani pengembangan di port 5173 dan memproxy <font name='Consolas'>/api</font> ke backend."],
    ["Tailwind CSS", "3.4", "Utility CSS dengan token tema.", "Menyusun layout responsif, warna, kartu, tabel, dan mode gelap."],
    ["Recharts", "3.2", "Komponen grafik berbasis SVG.", "Menampilkan tren permintaan, perbandingan aktual/prakiraan, dan KPI."],
    ["Lucide React", "0.548", "Kumpulan ikon SVG.", "Menyediakan ikon antarmuka yang konsisten dan ringan."],
    ["PostCSS + Autoprefixer", "8.5 / 10.4", "Pipeline transformasi CSS dan penambahan prefix vendor.", "Memastikan CSS Tailwind kompatibel dengan browser target."],
    ["@fontsource-variable/inter", "5.2", "Font Inter dibundel sebagai aset.", "Tipografi konsisten tanpa bergantung font sistem pengguna."],
    ["PWA native", "manifest + SW", "Manifest, service worker, dan cache shell.", "Aplikasi dapat dipasang ke layar utama; shell tetap terbuka saat offline."],
]
story += [
    data_table(mobile_rows, [96, 54, 176, 181], font=table_cell_small),
    p("Tabel 4. Teknologi mobile web dan PWA.", caption),
    Spacer(1, 4),
    p("2.4 Data science, dokumentasi, dan packaging", h2),
]
tool_rows = [
    ["Teknologi", "Versi", "Fungsi teknis", "Peran di Apotek Pahala"],
    ["pandas + NumPy", "≥ 2.2 / ≥ 1.26", "Manipulasi tabel dan komputasi numerik.", "Membersihkan data, membentuk lag/rolling, dan menyiapkan matriks fitur."],
    ["scikit-learn", "≥ 1.4", "Algoritma regresi dan metrik.", "Melatih tiga model, menghitung MAE/RMSE/WAPE, dan memilih model terbaik."],
    ["PyInstaller", "5.13.2", "Membekukan aplikasi Python beserta dependensi.", "Menghasilkan EXE desktop dan backend untuk paket Windows 7 (mode one-dir)."],
    ["libcst", "tooling modern", "Transformasi AST dengan preservasi format.", "Mengubah anotasi Python 3.14 dan kode PySide6 agar kompatibel dengan Python 3.8/PySide2."],
    ["Inno Setup", "6.2.2", "Compiler installer Windows.", "Membuat installer, shortcut, uninstaller, dan antarmuka bahasa Indonesia."],
    ["PowerShell", "bawaan Windows", "Orkestrasi skrip build.", "Menjalankan staging, PyInstaller, ZIP portabel, dan Inno Setup."],
    ["Graphify", "tooling", "Analisis AST, graf kode, dan community detection.", "Membuat peta kode di <font name='Consolas'>graphify-out/</font> untuk penelusuran arsitektur."],
]
story += [
    data_table(tool_rows, [92, 58, 176, 181], font=table_cell_small),
    p("Tabel 5. Tooling data science, dokumentasi, dan packaging.", caption),
    Spacer(1, 3),
    callout(
        "Mengapa PyInstaller mode one-dir?",
        "Mode one-dir menghasilkan folder aplikasi dengan EXE dan dependensi yang "
        "sudah terurai. Pendekatan ini lebih ramah untuk Windows 7 karena tidak perlu "
        "mengekstrak ribuan berkas ke folder sementara setiap kali aplikasi dibuka, "
        "lebih mudah diperiksa, dan lebih stabil untuk paket yang dipasang di folder "
        "Program Files.",
    ),
]

# ------------------------------- 3. Input ----------------------------------
story += [
    p("3. Input Data", h1),
    p(
        "Ada tiga pintu masuk data. Pipeline batch DBF dipakai untuk membangun dataset "
        "awal dari arsip apotek; import wizard dipakai Admin untuk pembaruan operasional; "
        "dan data cuaca dapat diganti melalui CSV atau import. Semua jalur bermuara pada "
        "tabel dan aturan validasi yang sama.",
    ),
    p("3.1 Ringkasan jalur input", h2),
]
input_rows = [
    ["Jalur", "Masukan", "Pelaksana", "Keluaran"],
    ["Batch DBF", "1.085 <font name='Consolas'>ST*.DBF</font> + 2.894 <font name='Consolas'>BL*.DBF</font> + CSV cuaca", "Developer/Admin", "<font name='Consolas'>datasets/real/*.csv</font>, <font name='Consolas'>metadata.json</font>, database"],
    ["Import wizard", "CSV/XLS/XLSX, maks. 15 MB, maks. 50.000 baris", "Admin", "Penjualan, cuaca, obat, atau stok + batch import"],
    ["Data cuaca", "CSV NASA POWER atau unggahan berkas", "Admin", "Tabel <font name='Consolas'>weather_days</font>"],
]
story += [
    data_table(input_rows, [74, 202, 70, 161], font=table_cell_small),
    p("Tabel 6. Tiga jalur input data.", caption),
    Spacer(1, 3),
    p("3.2 Pipeline batch dari DBF", h2),
    p(
        "Pipeline ini dijalankan dari folder <font name='Consolas'>backend</font> dengan "
        "<font name='Consolas'>python -m app.seed.real_data</font>. Ia membaca arsip "
        "mentah, membentuk data turunan, menyimpan ke database, lalu melatih model.",
    ),
]

batch_steps = [
    ["Langkah", "Apa yang terjadi", "Detail teknis"],
    ["1. Inventaris berkas", "Mengumpulkan berkas stok opname dan pembelian.", "<font name='Consolas'>ST*.DBF</font> = opname; <font name='Consolas'>BL*.DBF</font> = pembelian/retur/mutasi."],
    ["2. Parsing DBF", "Membaca dBase III/IV tanpa library eksternal.", "Header, jumlah record, panjang record, field descriptor; record bertanda <font name='Consolas'>*</font> dilewati."],
    ["3. Decode teks", "Mengubah byte menjadi teks.", "Encoding <font name='Consolas'>cp1252</font> dengan <font name='Consolas'>replace</font>, lalu <font name='Consolas'>strip()</font>."],
    ["4. Cache", "Mempercepat pembacaan ulang.", "Pickle <font name='Consolas'>storage/source_cache/ST.pkl</font> dan <font name='Consolas'>BL.pkl</font>; <font name='Consolas'>--refresh-cache</font> memaksa baca ulang."],
    ["5. Agregasi", "Menggabungkan baris per kode obat dan tanggal.", "Sum <font name='Consolas'>ST_PC</font>, <font name='Consolas'>ST_PHISIC</font>; nama terbanyak; median harga dan biaya."],
    ["6. Derivasi permintaan", "Menghitung permintaan antar dua opname.", "<font name='Consolas'>D = ST_PC(t1) + BL(t1..t2] − ST_PC(t2)</font>."],
    ["7. Fallback negatif", "Menangani koreksi stok yang membuat D negatif.", "Jika D &lt; 0, pakai <font name='Consolas'>ST_PHISIC</font>; jika tetap negatif, interval dibuang dan dihitung."],
    ["8. Alokasi harian", "Menyebar D merata ke hari interval.", "<font name='Consolas'>rate = D / jumlah_hari</font>, lalu dijumlahkan per pekan Senin–Minggu."],
    ["9. Filter cakupan", "Hanya memakai pekan yang teramati penuh.", "Pekan diterima bila 7 dari 7 hari tercakup."],
    ["10. Interpolasi", "Mengisi pekan yang hilang di antara dua opname.", "Reindex rentang penuh; interpolasi dua arah; minggu nol pada obat bervolume tinggi (&gt; 20) juga diinterpolasi."],
    ["11. Pembersihan akhir", "Menjaga nilai tetap wajar.", "<font name='Consolas'>clip(lower=0)</font>, pembulatan, dan konversi ke integer."],
    ["12. Ekspor", "Menulis dataset turunan dan metadata.", "<font name='Consolas'>obat.csv</font>, <font name='Consolas'>permintaan_mingguan.csv</font>, <font name='Consolas'>cuaca_harian.csv</font>, <font name='Consolas'>metadata.json</font>."],
]
story += [
    data_table(batch_steps, [78, 164, 265], font=table_cell_small),
    p("Tabel 7. Pipeline batch DBF langkah demi langkah.", caption),
    Spacer(1, 4),
    callout(
        "Mengapa memakai stok opname, bukan penjualan kasir?",
        "Arsip yang tersedia hanya berisi stok opname dan pembelian. Tidak ada tabel "
        "transaksi kasir, sehingga penjualan harian tidak dapat diklaim. Pendekatan "
        "stok awal + pembelian - stok akhir adalah metode inventaris yang transparan "
        "dan dapat diaudit kembali ke berkas sumber.",
    ),
]

story += [
    p("3.3 Import wizard untuk pembaruan operasional", h2),
    p(
        "Import wizard dipakai Admin saat ada data baru di luar pipeline batch. Alurnya "
        "memisahkan unggah dan commit, sehingga pengguna dapat melihat pratinjau sebelum "
        "data ditulis permanen.",
    ),
]
wizard_rows = [
    ["Tahap", "Perilaku sistem"],
    ["1. Pilih jenis", "Penjualan, cuaca, obat, atau stok. Setiap jenis punya kolom wajib dan aturan validasi sendiri."],
    ["2. Unduh template", "Template CSV disediakan agar nama kolom dan format tanggal tidak salah."],
    ["3. Unggah berkas", "Hanya CSV/XLS/XLSX, maksimum 15 MB, maksimum 50.000 baris; berkas kosong ditolak."],
    ["4. Baca berkas", "CSV: deteksi delimiter otomatis dan fallback encoding UTF-8-sig → latin-1. Excel: dibaca via pandas/OpenPyXL. Sel kosong diisi string kosong; nama kolom di-trim."],
    ["5. Petakan kolom", "Nama kolom dinormalisasi (huruf kecil, spasi/underscore disederhanakan) lalu dicocokkan ke alias."],
    ["6. Pratinjau", "200 baris pertama divalidasi; API mengembalikan total baris, jumlah valid, dan maksimal 20 error."],
    ["7. Commit", "Seluruh baris divalidasi ulang, duplikat dilewati, data dimasukkan, lalu batch, aktivitas, dan notifikasi dicatat."],
]
story += [
    data_table(wizard_rows, [82, 425], font=table_cell_small),
    p("Tabel 8. Alur import wizard.", caption),
    Spacer(1, 4),
    p("3.4 Alias kolom yang dikenali", h2),
    p(
        "Alias membuat pengguna tidak harus menulis nama kolom teknis. Pencocokan "
        "dilakukan setelah normalisasi, sehingga <font name='Consolas'>Kode Obat</font>, "
        "<font name='Consolas'>kode_obat</font>, dan <font name='Consolas'>kode</font> "
        "dianggap sama.",
    ),
]
alias_rows = [
    ["Kolom target", "Contoh alias yang diterima"],
    ["sale_date", "sale_date, tanggal, tgl, date, tanggal penjualan"],
    ["medicine_code", "medicine_code, kode obat, kode, code, kode barang, kode_obat"],
    ["quantity", "quantity, jumlah, qty, terjual, kuantitas"],
    ["unit_price", "unit_price, harga satuan, harga, price, harga_satuan"],
    ["weather_date", "weather_date, tanggal, tgl, date"],
    ["temperature", "temperature, suhu, suhu rata-rata, temp"],
    ["rainfall", "rainfall, curah hujan, hujan, rain"],
    ["humidity", "humidity, kelembapan, kelembaban, humidity (%)"],
    ["system_stock", "system_stock, stok sistem, stok_sistem"],
    ["physical_stock", "physical_stock, stok fisik, stok_fisik"],
]
story += [
    data_table(alias_rows, [104, 403], font=table_cell_small),
    p("Tabel 9. Contoh alias kolom pada import wizard.", caption),
    Spacer(1, 4),
    p("3.5 Aturan validasi per jenis import", h2),
]
validation_rows = [
    ["Jenis", "Kolom wajib", "Aturan validasi", "Kebijakan duplikat"],
    ["Penjualan", "sale_date, medicine_code, quantity", "Tanggal valid; kode obat terdaftar; jumlah bilangan bulat &gt; 0; harga ≥ 0.", "Kode transaksi + obat yang sama dilewati."],
    ["Cuaca", "weather_date, temperature, rainfall, humidity", "Tanggal valid; suhu −10…60 °C; kelembapan 0…100%; curah hujan ≥ 0.", "Tanggal yang sama dilewati."],
    ["Obat", "code, name, price", "Kode dan nama wajib; harga/stok minimum numerik; kategori/satuan default bila kosong.", "Kode obat yang sama dilewati; baris inventaris 0/0 dibuat otomatis."],
    ["Stok", "medicine_code, system_stock, physical_stock", "Kode terdaftar; stok bilangan bulat ≥ 0; tanggal opname opsional.", "Nilai sistem dan fisik identik dilewati; perubahan dicatat sebagai movement."],
]
story += [
    data_table(validation_rows, [54, 126, 205, 122], font=table_cell_small),
    p("Tabel 10. Validasi import per jenis data.", caption),
    Spacer(1, 4),
    p("3.6 Parsing angka dan tanggal", h2),
]
story += bullets(
    [
        "<b>Angka.</b> Simbol <font name='Consolas'>Rp</font> dan spasi dibuang; format <font name='Consolas'>1.234,56</font> dan <font name='Consolas'>1,234.56</font> sama-sama dikenali; koma desimal dikonversi ke titik.",
        "<b>Tanggal.</b> Format ISO <font name='Consolas'>YYYY-MM-DD</font> dibaca lebih dulu agar tanggal ambigu seperti <font name='Consolas'>2027-01-03</font> tidak tertukar menjadi 3 Januari vs 1 Maret; jika gagal, baru dipakai <font name='Consolas'>dayfirst=True</font>.",
        "<b>Kode obat.</b> Pencocokan lookup memakai huruf kecil, sehingga perbedaan kapitalisasi tidak menghasilkan duplikat.",
        "<b>Nilai kosong.</b> Sel kosong menjadi string kosong; pada kolom opsional angka dianggap 0, pada kolom wajib baris ditolak.",
        "<b>Batas berkas.</b> Ekstensi, ukuran, jumlah baris, dan berkas kosong diperiksa sebelum parsing untuk mencegah beban berlebih.",
    ]
)
story += [
    Spacer(1, 2),
    callout(
        "Jejak audit import",
        "Setiap commit membuat <font name='Consolas'>ImportBatch</font> berisi kode batch, "
        "jenis, nama berkas, jumlah baris, jumlah masuk, jumlah dilewati, dan daftar error. "
        "Admin juga menerima notifikasi dan aktivitas tercatat, sehingga import tidak "
        "menjadi operasi senyap.",
    ),
]

# ------------------------------- 4. Cleaning -------------------------------
story += [
    CondPageBreak(300),
    p("4. Pembersihan dan Validasi Data", h1),
    p(
        "Pembersihan dilakukan berlapis: dari tingkat berkas, record, aturan bisnis, "
        "hingga deret waktu. Prinsipnya adalah memperbaiki yang tidak valid tanpa "
        "mengarang data yang tidak ada. Setiap koreksi yang berdampak pada kualitas "
        "dicatat di metadata atau statistik interval.",
    ),
    p("4.1 Prinsip pembersihan", h2),
]
story += bullets(
    [
        "<b>Tidak menambah data sintetis.</b> Tidak ada data demo atau nilai acak yang dipakai untuk menutupi kekosongan.",
        "<b>Tidak membuang outlier nyata.</b> Lonjakan permintaan yang valid dipertahankan; yang dibatasi hanya nilai negatif dan interval yang tidak dapat dipertanggungjawabkan.",
        "<b>Transparan.</b> Jumlah observasi, interval negatif, gap maksimum, dan jumlah pekan disimpan di metadata.",
        "<b>Idempoten.</b> Menjalankan ulang pipeline dengan sumber yang sama menghasilkan dataset yang sama; cache hanya diperbarui bila diminta.",
        "<b>Terpisah.</b> Data mentah tetap di folder sumber; data turunan ditulis ke <font name='Consolas'>datasets/real/</font> dan tidak menimpa arsip.",
    ]
)
story += [
    Spacer(1, 3),
    p("4.2 Matriks masalah dan tindakan", h2),
]
cleaning_rows = [
    ["Masalah", "Deteksi", "Tindakan", "Dampak/jejak"],
    ["Record DBF terhapus", "Byte pertama record = <font name='Consolas'>*</font>", "Record dilewati.", "Tidak masuk agregasi."],
    ["Encoding tidak seragam", "Decode <font name='Consolas'>cp1252</font>", "Karakter tak dikenal diganti, teks di-trim.", "Nama obat tetap terbaca."],
    ["Nama berkas tanggal invalid", "Panjang token/ValueError", "Berkas dilewati.", "Tidak menghentikan seluruh batch."],
    ["Baris ganda kode + tanggal", "Grouping per kode dan tanggal", "Nilai stok dijumlahkan; nama modus; harga/biaya median.", "Satu observasi per hari."],
    ["Angka kosong atau koma", "<font name='Consolas'>number()</font>", "Koma menjadi titik; gagal → 0.0.", "Nilai tidak valid tidak merusak pipeline."],
    ["Permintaan negatif", "Rumus D &lt; 0", "Fallback ke stok fisik; jika tetap negatif, interval dibuang.", "Dihitung di <font name='Consolas'>negative_intervals</font>."],
    ["Gap opname panjang", "Selisih tanggal interval", "Hanya pekan dengan 7/7 hari tercakup yang dipakai; sisanya diinterpolasi.", "Gap maksimum dicatat."],
    ["Pekan nol pada obat ramai", "Median mingguan &gt; 20", "Minggu nol diinterpolasi karena bukan permintaan riil.", "Deret lebih stabil."],
    ["Cuaca hilang", "Join kiri terhadap pekan", "Forward/backward fill; jika tabel kosong dipakai default 24 °C / 0 / 82%.", "Fitur tetap lengkap."],
    ["Harga/biaya kosong", "Nilai ≤ 0", "Median harga positif terakhir; cadangan harga positif sebelumnya; biaya fallback ke harga jual.", "Harga obat selalu terisi."],
    ["Stok negatif saat import", "Validasi bilangan bulat", "Baris ditolak dan dicatat sebagai error.", "Tidak masuk database."],
    ["Duplikat saat import", "Kode transaksi/tanggal/kode obat", "Baris dilewati; jumlah skip dilaporkan.", "Batch tetap seimbang."],
]
story += [
    data_table(cleaning_rows, [88, 105, 204, 110], font=table_cell_small),
    p("Tabel 11. Masalah data yang umum dan tindakan yang diterapkan.", caption),
    Spacer(1, 4),
    p("4.3 Mengapa interpolasi dibatasi", h2),
    p(
        "Interpolasi hanya dilakukan pada pekan yang tidak tercakup penuh oleh interval "
        "opname, bukan pada setiap nilai kosong. Minggu yang benar-benar tidak memiliki "
        "observasi penuh tidak dianggap nol, karena nol bisa berarti obat habis atau "
        "memang tidak ada permintaan. Untuk obat bervolume tinggi (median mingguan di "
        "atas 20), minggu bernilai nol yang tersisa juga diinterpolasi karena lebih "
        "mungkin merupakan celah pencatatan daripada permintaan nol. Nilai akhir tetap "
        "dipotong agar tidak negatif dan dibulatkan ke integer.",
    ),
    p("4.4 Indikator kualitas yang disimpan", h2),
]
quality_rows = [
    ["Field metadata", "Arti", "Kegunaan"],
    ["observations", "Jumlah observasi opname per obat.", "Menilai kepadatan riwayat."],
    ["negative_intervals", "Jumlah interval yang D-nya negatif setelah fallback.", "Menandai kualitas pencatatan stok."],
    ["max_gap_days", "Jarak maksimum antar opname.", "Mengukur risiko interpolasi panjang."],
    ["coverage_days", "Jumlah hari yang tercakup interval valid.", "Menilai kelengkapan deret."],
    ["weeks", "Jumlah pekan bersih setelah filter.", "Memastikan syarat minimum model."],
    ["total_demand", "Total permintaan estimasi selama periode.", "Kontrol kewajaran volume."],
]
story += [
    data_table(quality_rows, [100, 236, 171], font=table_cell_small),
    p("Tabel 12. Indikator kualitas pada metadata dataset.", caption),
    Spacer(1, 3),
    callout(
        "Batas yang harus dihormati",
        "Pipeline menghentikan proses bila satu obat memiliki kurang dari 120 pekan data "
        "atau harga tidak ditemukan. Ini disengaja: lebih baik gagal dengan pesan jelas "
        "daripada melatih model dari deret yang terlalu pendek atau harga nol.",
        "#E55353",
        "#FDEEEE",
    ),
]

# ------------------------------- 5. Features -------------------------------
story += [
    p("5. Rekayasa Fitur", h1),
    p(
        "Setelah deret permintaan mingguan bersih, sistem membentuk matriks fitur untuk "
        "setiap obat. Tujuannya memberi model konteks historis, pola musiman, dan kondisi "
        "cuaca tanpa membocorkan informasi masa depan.",
    ),
    p("5.1 Dari data harian ke pekan Senin", h2),
    p(
        "Setiap tanggal penjualan dipetakan ke hari Senin pada pekan yang sama, lalu "
        "kuantitas dijumlahkan. Pekan yang tidak memiliki baris tetap dimasukkan sebagai "
        "nol agar jarak antar pekan konsisten. Deret kemudian diurutkan dan dipakai "
        "sebagai target <font name='Consolas'>demand</font>.",
    ),
    p("5.2 Daftar fitur", h2),
]
feature_rows = [
    ["Kelompok", "Field", "Arti dan formula", "Tujuan"],
    ["Lag pendek", "lag_1 … lag_8", "Permintaan 1–8 pekan sebelumnya.", "Menangkap momentum jangka pendek."],
    ["Lag tahunan", "lag_52", "Permintaan pekan yang sama tahun lalu.", "Menangkap musim tahunan."],
    ["Rata-rata bergulir", "roll_mean_4/8/12", "Rata-rata permintaan 4, 8, atau 12 pekan sebelumnya.", "Menghaluskan noise dan tren."],
    ["Fluktuasi", "roll_std_4", "Simpangan baku 4 pekan sebelumnya.", "Mengukur ketidakstabilan permintaan."],
    ["Kalender", "week_of_year, month", "Pekan ISO dan bulan target.", "Menangkap pola musiman."],
    ["Siklus", "sin_week, cos_week", "sin/cos dari 2π × pekan ISO / 52.", "Representasi musiman kontinu."],
    ["Cuaca", "temperature, rainfall, humidity", "Rata-rata suhu, total hujan, rata-rata kelembapan per pekan.", "Menghubungkan permintaan dengan kondisi lingkungan."],
    ["Target", "demand", "Total permintaan pekan berjalan.", "Variabel yang dipelajari model."],
]
story += [
    data_table(feature_rows, [76, 122, 194, 115], font=table_cell_small),
    p("Tabel 13. Fitur yang dipakai model.", caption),
    Spacer(1, 4),
    p("5.3 Pencegahan kebocoran data", h2),
]
story += bullets(
    [
        "<b>Semua fitur bergulir memakai <font name='Consolas'>shift(1)</font>.</b> Rata-rata dan simpangan baku dihitung dari pekan sebelum target, bukan termasuk target.",
        "<b>Lag 52 dan roll_mean_12 wajib tersedia.</b> Baris yang belum memiliki riwayat cukup dibuang, sehingga model tidak belajar dari nilai kosong.",
        "<b>Pemisahan kronologis.</b> Data uji selalu pekan terakhir; tidak ada pengacakan yang memungkinkan model melihat masa depan.",
        "<b>Prakiraan rekursif.</b> Hasil prediksi pekan pertama masuk kembali sebagai lag untuk pekan berikutnya; tidak ada nilai aktual masa depan yang dipakai.",
        "<b>Cuaca masa depan memakai skenario iklim.</b> Untuk prakiraan, suhu/hujan/kelembapan diambil dari rata-rata historis pekan ISO yang sama, bukan data cuaca yang belum terjadi.",
    ]
)
story += [
    Spacer(1, 3),
    p("5.4 Contoh perhitungan permintaan", h2),
    callout(
        "Contoh interval 14 hari",
        "Stok sistem pada opname pertama 120 unit, pembelian bersih selama interval 30 unit, "
        "dan stok sistem pada opname kedua 100 unit. Maka D = 120 + 30 − 100 = 50 unit. "
        "Laju harian = 50 / 14 = 3,57 unit/hari, sehingga satu pekan penuh menyumbang sekitar "
        "25 unit. Jika hasil ini negatif, sistem mencoba stok fisik; bila tetap negatif, "
        "interval tersebut tidak dipakai.",
    ),
    Spacer(1, 3),
    p("5.5 Prakiraan 1–12 pekan", h2),
    p(
        "Model final dilatih pada seluruh data bersih, lalu memprediksi pekan pertama setelah "
        "data terakhir. Nilai prediksi dimasukkan ke riwayat untuk membentuk lag pekan "
        "berikutnya, demikian seterusnya sampai horizon yang diminta. Batas bawah dan atas "
        "dihitung dari prediksi ± 1,96 × RMSE model terpilih, lalu batas bawah dipotong di nol. "
        "Interval ini adalah pendekatan statistik sederhana, bukan interval kepercayaan penuh.",
    ),
]

# ------------------------------- 6. Modeling -------------------------------
story += [
    p("6. Pemodelan dan Evaluasi", h1),
    p(
        "Sistem membandingkan tiga algoritma regresi untuk setiap obat, memilih yang "
        "paling baik pada data uji kronologis, lalu melatih ulang model terpilih pada "
        "seluruh data. Pendekatan per obat penting karena pola permintaan tiap obat "
        "berbeda; satu model global akan menyamarkan perbedaan tersebut.",
    ),
    p("6.1 Tiga algoritma", h2),
]
model_rows = [
    ["Algoritma", "Cara kerja", "Kelebihan", "Peran"],
    ["Random Forest Regression", "Banyak pohon keputusan yang dilatih pada sampel dan fitur acak, hasilnya dirata-rata.", "Menangkap hubungan non-linear, tahan noise, memberi feature importance.", "Kandidat utama; sering terpilih."],
    ["Decision Tree Regression", "Satu pohon yang membagi data berdasarkan ambang fitur.", "Mudah dijelaskan dan divisualisasikan.", "Pembanding interpretable."],
    ["Linear Regression", "Mencari kombinasi linear fitur yang meminimalkan error.", "Cepat, sederhana, menjadi baseline.", "Pembanding dan fallback untuk pola linear."],
]
story += [
    data_table(model_rows, [88, 190, 132, 97], font=table_cell_small),
    p("Tabel 14. Algoritma yang dibandingkan.", caption),
    Spacer(1, 4),
    p("6.2 Parameter default", h2),
]
param_rows = [
    ["Parameter", "Nilai", "Keterangan"],
    ["primary_model", "auto", "Latih ketiganya, pilih WAPE uji terendah."],
    ["n_estimators", "400", "Jumlah pohon Random Forest."],
    ["max_depth", "4", "Kedalaman maksimum; membatasi overfitting pada data mingguan."],
    ["min_samples_leaf", "3", "Minimum sampel di daun pohon."],
    ["random_state", "42", "Membuat hasil dapat direproduksi."],
    ["test_ratio", "0,2", "20% data terakhir menjadi data uji kronologis."],
    ["horizon_weeks", "4", "Horizon prakiraan default; dapat 1–12 pekan."],
]
story += [
    data_table(param_rows, [104, 76, 327], font=table_cell_small),
    p("Tabel 15. Parameter model default pada konfigurasi aplikasi.", caption),
    Spacer(1, 4),
    p("6.3 Alur pelatihan dan pemilihan", h2),
]
story += bullets(
    [
        "Bangun deret mingguan per obat dan matriks fitur; minimal 60 pekan bersih setelah fitur terbentuk.",
        "Bagi data secara kronologis: ukuran uji = maksimum 12 pekan atau 20% data, dibatasi agar data latih tetap minimal 60 baris, dan tidak kurang dari 8 baris uji.",
        "Latih Random Forest, Decision Tree, dan Linear Regression pada data latih.",
        "Hitung MAE, RMSE, WAPE, dan MAPE pada data uji untuk setiap model.",
        "Mode <font name='Consolas'>auto</font> memilih WAPE terkecil; jika seri, MAE terkecil menjadi penentu.",
        "Latih ulang model terpilih pada seluruh data, lalu buat prakiraan rekursif 1–12 pekan.",
        "Simpan metrik, feature importance, backtest, dan prakiraan ke database agar dashboard, laporan, dan pengadaan memakai angka yang sama.",
    ]
)
story += [
    Spacer(1, 3),
    p("6.4 Metrik evaluasi", h2),
]
metric_rows = [
    ["Metrik", "Formula", "Arti"],
    ["MAE", "mean(|y − ŷ|)", "Rata-rata error absolut dalam unit permintaan."],
    ["RMSE", "sqrt(mean((y − ŷ)²))", "Error kuadratik; lebih sensitif pada error besar."],
    ["WAPE", "Σ|y − ŷ| / Σy × 100%", "Total error relatif terhadap total permintaan; metrik utama."],
    ["MAPE", "mean(|y − ŷ| / y) × 100%, y &gt; 0", "Rata-rata error persen; hanya pekan dengan aktual positif."],
    ["Accuracy indikatif", "maks(0, 100 − WAPE)", "Pelengkap komunikasi; bukan jaminan akurasi masa depan."],
]
story += [
    data_table(metric_rows, [80, 176, 251], font=table_cell_small),
    p("Tabel 16. Metrik evaluasi dan interpretasinya.", caption),
    Spacer(1, 3),
    callout(
        "Cara membaca WAPE",
        "WAPE 12,38% berarti total error absolut model sekitar 12,38% dari total permintaan "
        "aktual pada data uji, bukan berarti setiap baris salah 12,38%. WAPE dipilih karena "
        "lebih stabil daripada MAPE ketika permintaan mingguan sangat rendah atau nol. "
        "Nilai lebih rendah lebih baik.",
        "#3985D6",
        "#EEF5FC",
    ),
]

story += [
    p("6.5 Hasil evaluasi terakhir", h2),
    p(
        "Angka berikut berasal dari pelatihan terakhir pada data aktual yang tersedia. "
        "Data historis dapat berubah bila stock opname baru diimpor dan model dilatih ulang.",
    ),
]
result_rows = [
    ["Indikator", "Hasil", "Catatan"],
    ["Model terpilih", "Random Forest 14 obat<br/>Linear Regression 5 obat<br/>Decision Tree 1 obat", "Dipilih otomatis per obat berdasarkan WAPE uji."],
    ["WAPE seluruh 20 obat", "12,38%", "Akurasi indikatif 87,62%."],
    ["WAPE 6 obat prioritas", "10,19%", "Akurasi indikatif 89,81%."],
    ["Periode data", "10 Jan 2022 – 14 Sep 2026", "4.478 baris permintaan mingguan."],
    ["Cuaca", "1 Jan 2022 – 23 Sep 2026", "1.727 hari, NASA POWER MERRA-2."],
]
story += [
    data_table(result_rows, [108, 210, 189], font=table_cell_small),
    p("Tabel 17. Ringkasan hasil evaluasi terakhir.", caption),
    Spacer(1, 4),
    p("6.6 WAPE obat prioritas", h2),
]
priority_rows = [
    ["Obat prioritas", "WAPE", "Akurasi indikatif"],
    ["Amlodipine 10mg 30's", "13,42%", "86,58%"],
    ["Amlodipine 5mg 30's", "8,08%", "91,92%"],
    ["Dexteem Plus 100's", "10,03%", "89,97%"],
    ["Metformin 500mg", "10,98%", "89,02%"],
    ["Methylprednisolon 4mg", "12,97%", "87,03%"],
    ["Voltadex 50mg 50's", "5,67%", "94,33%"],
]
story += [
    data_table(priority_rows, [238, 100, 169], font=table_cell_small, align_center_cols=(1, 2)),
    p("Tabel 18. Evaluasi enam obat prioritas pada pelatihan terakhir.", caption),
    Spacer(1, 4),
    p("6.7 Feature importance", h2),
    p(
        "Untuk Random Forest dan Decision Tree, kepentingan fitur dihitung dari penurunan "
        "impuritas yang dinormalisasi. Untuk Linear Regression, dipakai nilai absolut "
        "koefisien yang dinormalisasi. Hasilnya ditampilkan di desktop dan mobile sebagai "
        "petunjuk fitur yang paling berpengaruh, bukan sebagai klaim kausalitas. Lag "
        "permintaan jangka pendek, rata-rata bergulir, dan lag tahunan biasanya mendominasi; "
        "cuaca memberi kontribusi tambahan yang bervariasi antar obat.",
    ),
    Spacer(1, 2),
    callout(
        "Batas interpretasi",
        "Model ini memprediksi permintaan untuk perencanaan persediaan, bukan diagnosis "
        "medis atau keputusan klinis. Evaluasi dilakukan pada data historis yang terbatas; "
        "perubahan pola pasien, harga, atau kebijakan apotek dapat menurunkan performa.",
        "#F2A93B",
        "#FFF6E7",
    ),
]

# ------------------------------- 7. Reproduksi -----------------------------
story += [
    p("7. Reproduksi, Berkas, dan Keamanan", h1),
    p(
        "Bagian ini memuat perintah yang dipakai untuk menjalankan, menguji, dan "
        "membangun ulang aplikasi, peta berkas penting, konfigurasi lingkungan, serta "
        "kontrol keamanan yang sudah diterapkan.",
    ),
    p("7.1 Perintah utama", h2),
]
story += [
    p("Menjalankan backend dan desktop", h3),
    code_block(
        """
# Dari root proyek
python -m pip install -r requirements.txt

# Backend (port 8000)
run_backend.bat
# atau
cd backend
python run.py --host 0.0.0.0 --port 8000

# Desktop
run_desktop.bat
"""
    ),
    Spacer(1, 4),
    p("Mobile web", h3),
    code_block(
        """
cd mobile-web
npm install
npm run dev        # http://localhost:5173, proxy /api -> 127.0.0.1:8000
npm run build      # hasil ke mobile-web/dist
"""
    ),
    Spacer(1, 4),
    p("Menyiapkan ulang data aktual", h3),
    code_block(
        """
cd backend
python -m app.seed.real_data --reset
python -m app.seed.real_data --reset --refresh-cache
python -m app.seed.real_data --reset --skip-train
python -m app.seed.real_data --export-only
"""
    ),
    Spacer(1, 4),
    p("Pengujian dan paket Windows 7", h3),
    code_block(
        """
cd backend
python -m pytest tests -q

# Build paket Windows 7 (butuh Python 3.8.10 x64 + Inno Setup 6)
$env:APOTEK_PY38 = "C:\\path\\ke\\python38\\Scripts\\python.exe"
$env:APOTEK_ISCC = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
powershell -ExecutionPolicy Bypass -File packaging\\build_win7.ps1
"""
    ),
    Spacer(1, 4),
    p("7.2 Peta berkas penting", h2),
]
file_rows = [
    ["Berkas", "Isi dan fungsi"],
    ["<font name='Consolas'>backend/app/seed/real_data.py</font>", "Parsing DBF, derivasi permintaan, ekspor CSV, seeding database."],
    ["<font name='Consolas'>backend/app/api/imports.py</font>", "Import wizard: preview, mapping, validasi, commit, riwayat batch."],
    ["<font name='Consolas'>backend/app/ml/features.py</font>", "Agregasi mingguan, lag/rolling, kalender, cuaca, prakiraan rekursif."],
    ["<font name='Consolas'>backend/app/ml/trainer.py</font>", "Tiga model, split kronologis, metrik, pemilihan otomatis, feature importance."],
    ["<font name='Consolas'>backend/app/core/config.py</font>", "Path, database, secret, CORS, batas upload, parameter model default."],
    ["<font name='Consolas'>backend/app/core/security.py</font>", "Hash PBKDF2-SHA256 dan token JWT HS256."],
    ["<font name='Consolas'>desktop/app/core/theme.py</font>", "Token warna, tipografi, QSS, dan ukuran komponen desktop."],
    ["<font name='Consolas'>mobile-web/package.json</font>", "Dependensi dan skrip React/Vite/Tailwind."],
    ["<font name='Consolas'>packaging/prepare_win7.py</font>", "Staging, transformasi PySide6 → PySide2, penyesuaian path data."],
    ["<font name='Consolas'>packaging/specs/*.spec</font>", "Aturan PyInstaller untuk desktop dan backend."],
    ["<font name='Consolas'>packaging/installer.iss</font>", "Definisi installer Inno Setup dan bahasa Indonesia."],
    ["<font name='Consolas'>datasets/real/metadata.json</font>", "Metode, periode, jumlah data, dan statistik kualitas."],
]
story += [
    data_table(file_rows, [222, 285], font=table_cell_small),
    p("Tabel 19. Berkas yang menjadi acuan implementasi.", caption),
]

story += [
    p("7.3 Konfigurasi lingkungan", h2),
]
env_rows = [
    ["Variabel", "Default", "Fungsi"],
    ["SECRET_KEY", "dibuat otomatis", "Kunci JWT; jika kosong, dibuat di <font name='Consolas'>storage/secret.key</font>."],
    ["APOTEK_DB_PATH", "<font name='Consolas'>storage/apotek_pahala.db</font>", "Lokasi database SQLite."],
    ["APOTEK_STORAGE_DIR", "<font name='Consolas'>storage/</font>", "Folder database, upload, dan secret."],
    ["APOTEK_MODEL_DIR", "<font name='Consolas'>models/</font>", "Folder artefak model bila disimpan."],
    ["APOTEK_BACKUP_DIR", "<font name='Consolas'>backups/</font>", "Folder backup database."],
    ["ACCESS_TOKEN_EXPIRE_MINUTES", "720", "Masa berlaku token (12 jam)."],
    ["APOTEK_HOST / APOTEK_PORT", "0.0.0.0 / 8000", "Alamat dan port backend."],
    ["CORS_ORIGINS", "localhost:5173, 8000", "Origin yang diizinkan untuk mobile web."],
]
story += [
    data_table(env_rows, [146, 138, 223], font=table_cell_small),
    p("Tabel 20. Variabel lingkungan utama.", caption),
    Spacer(1, 4),
    p("7.4 Kontrol keamanan", h2),
]
story += bullets(
    [
        "<b>Password.</b> Disimpan sebagai hash PBKDF2-HMAC-SHA256 dengan 210.000 iterasi dan salt acak; password asli tidak pernah disimpan.",
        "<b>Token.</b> JWT HS256 berisi subjek, peran, dan waktu kedaluwarsa 12 jam; kunci dibuat per instalasi dan tidak dibundel di paket.",
        "<b>Otorisasi.</b> Endpoint Admin diperiksa di server melalui dependency, bukan hanya dengan menyembunyikan tombol di UI.",
        "<b>Upload.</b> Dibatasi 15 MB, hanya CSV/XLS/XLSX, maksimum 50.000 baris; nama file diubah menjadi token UUID.",
        "<b>Restore.</b> Berkas SQLite divalidasi sebelum menimpa database; backup otomatis dibuat dan pengguna harus login ulang.",
        "<b>Repositori.</b> <font name='Consolas'>.gitignore</font> mengecualikan database produksi, <font name='Consolas'>secret.key</font>, <font name='Consolas'>.env</font>, backup, cache, dan build.",
    ]
)
story += [
    Spacer(1, 3),
    callout(
        "Catatan operasional",
        "Ganti password bawaan Admin dan Petugas setelah login pertama. Untuk pemakaian "
        "di jaringan kantor, batasi akses port 8000 dengan firewall dan gunakan HTTPS "
        "melalui reverse proxy. Jangan menyalin <font name='Consolas'>storage/secret.key</font> "
        "ke komputer lain; biarkan aplikasi membuat kunci baru per profil pengguna.",
        "#E55353",
        "#FDEEEE",
    ),
]

# ------------------------------- 8. Batasan -------------------------------
story += [
    p("8. Batasan dan Tata Kelola", h1),
    p(
        "Dokumen ini menjelaskan implementasi, bukan menjanjikan hasil di luar data yang "
        "tersedia. Batasan berikut perlu dipahami oleh pengguna, penguji, dan pengambil "
        "keputusan.",
    ),
]
limit_rows = [
    ["Batasan", "Dampak", "Mitigasi"],
    ["Tidak ada transaksi kasir", "Permintaan adalah estimasi dari stok dan pembelian, bukan penjualan harian.", "Label estimasi konsisten; integrasikan POS bila tersedia."],
    ["Hanya 20 jenis obat", "Bukan katalog lengkap apotek.", "Tambahkan spesifikasi/import obat sesuai kebutuhan."],
    ["Gap opname tidak seragam", "Interpolasi meningkat bila jarak opname panjang.", "Perbanyak frekuensi opname; pantau <font name='Consolas'>max_gap_days</font>."],
    ["Cuaca acuan Bandung", "Kondisi lokal apotek lain bisa berbeda.", "Ganti lokasi/CSV cuaca di menu data cuaca."],
    ["Performa model dapat berubah", "WAPE historis bukan jaminan masa depan.", "Latih ulang berkala; pantau error dan drift."],
    ["Windows 7 sudah legacy", "Dukungan keamanan dan pembaruan terbatas.", "Jalankan di jaringan terisolasi; rencanakan migrasi."],
    ["Akun bawaan", "Risiko akses tidak sah bila tidak diganti.", "Ganti password, batasi peran, audit aktivitas."],
    ["Artefak build besar", "Tidak cocok masuk riwayat Git.", "Gunakan <font name='Consolas'>.gitignore</font> dan GitHub Release untuk installer."],
]
story += [
    data_table(limit_rows, [112, 202, 193], font=table_cell_small),
    p("Tabel 21. Batasan utama dan cara mitigasinya.", caption),
    Spacer(1, 4),
    p("8.1 Rekomendasi pengembangan", h2),
]
story += bullets(
    [
        "Integrasikan data transaksi kasir/POS agar permintaan diukur langsung, bukan diestimasi dari selisih stok.",
        "Tambahkan pemantauan drift dan jadwal pelatihan ulang otomatis, misalnya bulanan atau setelah opname besar.",
        "Perluas cakupan obat dan kategori, serta sediakan validasi master obat yang lebih ketat.",
        "Tambahkan kalibrasi interval prakiraan dan uji backtest bergulir (walk-forward) untuk periode yang lebih panjang.",
        "Otomatiskan backup terjadwal dan uji restore di lingkungan terpisah.",
        "Siapkan jalur migrasi dari Windows 7 ke Windows 10/11 untuk mengurangi risiko keamanan.",
    ]
)
story += [
    Spacer(1, 3),
    p("8.2 Pernyataan penutup", h2),
    p(
        "Framework dan library di atas dipilih untuk memenuhi kebutuhan aplikasi lokal "
        "yang dapat berjalan di Windows 7 tanpa dependensi cloud. Kekuatan utama sistem "
        "bukan pada satu algoritma, melainkan pada rantai yang dapat diaudit: berkas "
        "sumber, aturan pembersihan, dataset turunan, metadata, model, metrik, dan "
        "laporan. Setiap tahap dapat dijalankan ulang dan diperiksa.",
    ),
    PageBreak(),
]

# ------------------------------- Lampiran A --------------------------------
story += [
    p("Lampiran A. Glosarium", h1),
]
glossary_rows = [
    ["Istilah", "Penjelasan"],
    ["API", "Antarmuka program yang memungkinkan desktop dan mobile meminta data ke backend."],
    ["ASGI", "Standar server aplikasi Python asynchronous; dipakai Uvicorn untuk FastAPI."],
    ["ORM", "Object-Relational Mapping; SQLAlchemy memetakan tabel ke objek Python."],
    ["JWT", "JSON Web Token; token bertanda tangan untuk membuktikan identitas dan peran."],
    ["PBKDF2", "Fungsi derivasi kunci berbasis password dengan iterasi dan salt."],
    ["PWA", "Progressive Web App; situs yang dapat dipasang dan memiliki service worker."],
    ["QSS", "Qt Style Sheets; cara menata widget Qt dengan aturan mirip CSS."],
    ["Lag", "Nilai permintaan dari sejumlah pekan sebelumnya."],
    ["Rolling mean", "Rata-rata bergerak dari jendela pekan tertentu."],
    ["WAPE", "Weighted Absolute Percentage Error; total error absolut dibagi total aktual."],
    ["MAPE", "Mean Absolute Percentage Error; rata-rata error persen per observasi."],
    ["One-dir", "Mode PyInstaller yang menghasilkan folder aplikasi, bukan satu file EXE."],
    ["Feature importance", "Ukuran kontribusi fitur terhadap prediksi model."],
    ["Chronological split", "Pembagian data latih/uji berdasarkan urutan waktu, bukan acak."],
]
story += [
    data_table(glossary_rows, [120, 387], font=table_cell_small),
    p("Tabel 22. Istilah teknis yang dipakai dalam dokumen.", caption),
    Spacer(1, 6),
    p("Lampiran B. Bukti Validasi Terakhir", h1),
    p(
        "Pemeriksaan berikut sudah dijalankan pada lingkungan pengembangan dan paket "
        "Windows 7. Bukti lengkap tercatat di <font name='Consolas'>docs/PENGUJIAN.md</font>, "
        "<font name='Consolas'>docs/WINDOWS7.md</font>, dan "
        "<font name='Consolas'>docs/WORK_LOG.md</font>.",
    ),
]
proof_rows = [
    ["Pemeriksaan", "Hasil"],
    ["Kompilasi Python", "<font name='Consolas'>python -m compileall -q packaging desktop\\app desktop\\run.py</font> lulus."],
    ["Tes backend", "17 tes lulus dengan <font name='Consolas'>pytest</font>."],
    ["QA desktop 8 halaman", "Tidak ada overflow horizontal (<font name='Consolas'>hmax=0</font>), badge/tombol tidak terpotong."],
    ["Kesehatan paket", "Health check backend mengembalikan HTTP 200."],
    ["Login paket", "Admin dan Petugas berhasil login; endpoint Admin menolak Petugas."],
    ["ZIP portabel", "Ekstraksi 1.297 berkas; aplikasi berjalan."],
    ["Installer", "1.299 berkas; silent install dan uninstall berhasil."],
    ["Data pengguna", "Database pengguna tetap ada setelah uninstall (sesuai desain)."],
    ["Graphify", "1.742 node, 5.321 edge, 84 komunitas."],
    ["Windows 7 fisik", "Belum diuji pada mesin/VM Windows 7 fisik; menjadi batasan validasi."],
]
story += [
    data_table(proof_rows, [140, 367], font=table_cell_small),
    p("Tabel 23. Ringkasan bukti validasi.", caption),
    Spacer(1, 6),
    callout(
        "Kesimpulan",
        "Dokumen ini menunjukkan bahwa setiap framework memiliki peran yang jelas dan "
        "setiap tahap data memiliki aturan yang dapat diperiksa. Untuk pertanyaan teknis "
        "lebih rinci, mulai dari berkas pada Tabel 19; untuk pertanyaan hasil, gunakan "
        "metrik dan periode pada Tabel 17–18.",
    ),
]

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ApotekDoc(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=58,
        bottomMargin=58,
        title="Apotek Pahala — Framework, Library, dan Metode Pengolahan Data",
        author="Tim Capstone Design — Sistem Informasi, Universitas Telkom",
        subject="Penjelasan framework dan metode input, pembersihan, serta pemodelan data",
        creator="Apotek Pahala documentation generator",
    )
    doc.multiBuild(story)
    print(f"PDF ditulis: {OUT}")
    print(f"Ukuran: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
