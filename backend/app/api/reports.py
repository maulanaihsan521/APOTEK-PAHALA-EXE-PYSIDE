"""Laporan: ringkasan dan ekspor PDF, Excel, CSV."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.models import User
from app.services.export_service import csv_response, excel_response, pdf_response
from app.services.reports_service import REPORT_TYPES, build_report, report_dataframe
from app.services.reports_service import _default_range

router = APIRouter(prefix="/reports", tags=["Laporan"])


@router.get("/types", summary="Jenis laporan tersedia")
def types():
    return [{"value": key, "label": value} for key, value in REPORT_TYPES.items()]


@router.get("/range", summary="Rentang tanggal data tersedia")
def data_range(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _default_range(db)
    return {"start": start.isoformat(), "end": end.isoformat()}


@router.get("/summary", summary="Ringkasan laporan")
def summary(
    type: str = "sales",
    start: date | None = None,
    end: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return build_report(db, type, start, end, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/export", summary="Ekspor laporan")
def export(
    type: str = "sales",
    fmt: str = "pdf",
    start: date | None = None,
    end: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = build_report(db, type, start, end, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    df = report_dataframe(report)
    meta = report["meta"]
    filename = f"{report['title'].replace(' ', '_')}_{start or ''}_{end or ''}".strip("_")
    if fmt == "xlsx":
        return excel_response(df, filename, report["title"], meta)
    if fmt == "csv":
        return csv_response(df, filename)
    if fmt != "pdf":
        raise HTTPException(status_code=400, detail="Format ekspor harus pdf, xlsx, atau csv.")
    max_rows = 80
    rows = report["rows"][:max_rows]
    note = report["notes"]
    if len(report["rows"]) > max_rows:
        note += f" Tabel menampilkan {max_rows} dari {len(report['rows'])} baris; ekspor Excel memuat seluruh data."
    return pdf_response(
        report["title"],
        meta,
        report["summary"],
        report["columns"],
        rows,
        filename,
        chart=report["chart"] or None,
        notes=note,
        landscape_mode=len(report["columns"]) > 5,
    )
