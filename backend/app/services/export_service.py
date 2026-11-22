"""Ekspor CSV, Excel, dan PDF dengan identitas visual Apotek Pahala."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
from fastapi.responses import Response, StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, DATA_SOURCE_NOTE, ROOT_DIR

PRIMARY = "#087F6B"
SECONDARY = "#0B5F52"
ACCENT = "#20B58A"
TEXT = "#18343D"
MUTED = "#718096"
BORDER = "#E3EBEF"
SUCCESS = "#16A36A"
WARNING = "#F2A93B"
DANGER = "#E55353"

LOGO_PATH = ROOT_DIR / "assets" / "logo.png"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def _safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in name).strip("_")


def _meta_text(meta: dict[str, str] | None) -> str:
    if not meta:
        return ""
    return "  |  ".join(f"{key}: {value}" for key, value in meta.items())


def csv_response(df: pd.DataFrame, filename: str) -> StreamingResponse:
    buffer = io.BytesIO()
    buffer.write("\ufeff".encode("utf-8"))
    df.to_csv(buffer, index=False, encoding="utf-8")
    buffer.seek(0)
    name = f"{_safe_name(filename)}_{timestamp()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


def excel_response(
    df: pd.DataFrame,
    filename: str,
    title: str,
    meta: dict[str, str] | None = None,
) -> StreamingResponse:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan"
    total_cols = max(len(df.columns), 1)
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    cell = sheet.cell(row=1, column=1, value=f"{APP_NAME} - {title}")
    cell.font = Font(name="Segoe UI", size=15, bold=True, color=PRIMARY.replace("#", ""))
    cell.alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 28

    sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    subtitle = sheet.cell(row=2, column=1, value=f"{APP_SUBTITLE} | {_meta_text(meta)}")
    subtitle.font = Font(name="Segoe UI", size=9, color=MUTED.replace("#", ""))

    sheet.merge_cells(start_row=3, start_column=1, end_row=3, end_column=total_cols)
    generated = sheet.cell(
        row=3, column=1,
        value=f"Dibuat {datetime.now():%d %B %Y %H:%M} - Versi {APP_VERSION}",
    )
    generated.font = Font(name="Segoe UI", size=8, italic=True, color=MUTED.replace("#", ""))

    header_row = 5
    fill = PatternFill("solid", fgColor=PRIMARY.replace("#", ""))
    thin = Side(style="thin", color=BORDER.replace("#", ""))
    for index, column in enumerate(df.columns, start=1):
        header = sheet.cell(row=header_row, column=index, value=str(column))
        header.fill = fill
        header.font = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
        header.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        header.border = Border(bottom=thin)
    sheet.row_dimensions[header_row].height = 26

    for row_index, record in enumerate(df.itertuples(index=False), start=header_row + 1):
        for col_index, value in enumerate(record, start=1):
            cell = sheet.cell(row=row_index, column=col_index, value=value)
            cell.font = Font(name="Segoe UI", size=9, color=TEXT.replace("#", ""))
            cell.border = Border(bottom=thin)
            if row_index % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F5F8FA")

    for index, column in enumerate(df.columns, start=1):
        samples = df[column].astype(str).head(200)
        width = min(max(12, max(len(str(column)), *(len(value) for value in samples)) + 2), 42)
        sheet.column_dimensions[get_column_letter(index)].width = width

    if len(df):
        sheet.auto_filter.ref = f"A{header_row}:{get_column_letter(len(df.columns))}{header_row + len(df)}"
        sheet.freeze_panes = f"A{header_row + 1}"

    # Lembar informasi
    info = workbook.create_sheet("Informasi")
    info["A1"] = "Informasi Dokumen"
    info["A1"].font = Font(name="Segoe UI", size=13, bold=True, color=PRIMARY.replace("#", ""))
    rows = [
        ("Nama aplikasi", APP_NAME),
        ("Subjudul", APP_SUBTITLE),
        ("Jenis laporan", title),
        ("Dibuat", datetime.now().strftime("%d %B %Y %H:%M")),
        ("Versi aplikasi", APP_VERSION),
        ("Catatan data", DATA_SOURCE_NOTE),
    ]
    for index, (key, value) in enumerate(rows, start=3):
        info.cell(row=index, column=1, value=key).font = Font(name="Segoe UI", bold=True)
        info.cell(row=index, column=2, value=value).font = Font(name="Segoe UI")
    info.column_dimensions["A"].width = 22
    info.column_dimensions["B"].width = 80

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    name = f"{_safe_name(filename)}_{timestamp()}.xlsx"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


def _bar_chart(series: Sequence[tuple[str, float]], width: float = 460, height: float = 150) -> Drawing:
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 10
    chart.y = 22
    chart.height = height - 40
    chart.width = width - 30
    chart.data = [[value for _, value in series]]
    chart.categoryAxis.categoryNames = [label for label, _ in series]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.fillColor = colors.HexColor(MUTED)
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labels.fillColor = colors.HexColor(MUTED)
    chart.valueAxis.strokeColor = colors.HexColor(BORDER)
    chart.categoryAxis.strokeColor = colors.HexColor(BORDER)
    chart.bars[0].fillColor = colors.HexColor(ACCENT)
    chart.bars[0].strokeColor = colors.HexColor(ACCENT)
    chart.barSpacing = 2
    drawing.add(chart)
    return drawing


def pdf_response(
    title: str,
    meta: dict[str, str] | None,
    summary: Sequence[tuple[str, str]],
    table_headers: Sequence[str],
    table_rows: Sequence[Sequence[Any]],
    filename: str,
    chart: Sequence[tuple[str, float]] | None = None,
    notes: str | None = None,
    landscape_mode: bool = False,
) -> StreamingResponse:
    buffer = io.BytesIO()
    page_size = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"{APP_NAME} - {title}",
        author=APP_NAME,
        subject=title,
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor(TEXT), leading=13,
    )
    muted = ParagraphStyle(
        "Muted", parent=body, fontSize=8, textColor=colors.HexColor(MUTED),
    )
    heading = ParagraphStyle(
        "Heading", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=19, textColor=colors.HexColor(PRIMARY), spaceAfter=4,
    )
    story: list[Any] = []

    logo = None
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=20 * mm, height=20 * mm)
    header_left = [
        Paragraph(f'<font color="{SECONDARY}"><b>{APP_NAME}</b></font>', ParagraphStyle(
            "Brand", parent=body, fontSize=17, leading=19, textColor=colors.HexColor(SECONDARY),
        )),
        Paragraph(APP_SUBTITLE, muted),
        Paragraph("Solusi Analitik untuk Persediaan Obat yang Lebih Tepat", muted),
    ]
    header_table = Table(
        [[logo or "", header_left]],
        colWidths=[24 * mm, page_size[0] - 56 * mm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor(PRIMARY)),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(title, heading))
    meta_line = f"Periode: {meta.get('Periode', '-')}" if meta else ""
    if meta and "Periode" in meta:
        extra = "  |  ".join(f"{k}: {v}" for k, v in meta.items() if k != "Periode")
        meta_line += f"  |  {extra}" if extra else ""
    story.append(Paragraph(meta_line, muted))
    story.append(Paragraph(f"Dibuat: {datetime.now():%d %B %Y %H:%M}  |  Versi aplikasi {APP_VERSION}", muted))
    story.append(Spacer(1, 10))

    if summary:
        summary_data = [[key, value] for key, value in summary]
        summary_table = Table(summary_data, colWidths=[60 * mm, (page_size[0] - 56 * mm) - 60 * mm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8FA")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor(BORDER)),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(TEXT)),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

    if chart:
        story.append(_bar_chart(chart))
        story.append(Spacer(1, 8))

    if table_headers and table_rows:
        cell_style = ParagraphStyle("Cell", parent=body, fontSize=7.5, leading=10)
        header_style = ParagraphStyle("Header", parent=cell_style, fontName="Helvetica-Bold",
                                      textColor=colors.white, fontSize=7.5)
        data = [[Paragraph(str(h), header_style) for h in table_headers]]
        for row in table_rows:
            data.append([Paragraph(str(value), cell_style) for value in row])
        col_width = (page_size[0] - 32 * mm) / max(len(table_headers), 1)
        table = Table(data, colWidths=[col_width] * len(table_headers), repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor(BORDER)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for index in range(1, len(data)):
            if index % 2 == 0:
                style.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor("#F9FBFC")))
        table.setStyle(TableStyle(style))
        story.append(table)

    if notes:
        story.append(Spacer(1, 8))
        note_table = Table([[Paragraph(notes, muted)]], colWidths=[page_size[0] - 32 * mm])
        note_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF9F5")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFE8D8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(note_table)

    def on_page(canvas, doc_object):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(16 * mm, 9 * mm,
                          f"{APP_NAME} - {APP_SUBTITLE}  |  Data aktual Apotek Pahala")
        canvas.drawRightString(page_size[0] - 16 * mm, 9 * mm, f"Halaman {doc_object.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    name = f"{_safe_name(filename)}_{timestamp()}.pdf"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
