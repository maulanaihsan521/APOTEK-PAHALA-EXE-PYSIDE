"""Data penjualan: CRUD, filter, dan ekspor."""
from __future__ import annotations

import random
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.models import Medicine, Sale, User
from app.schemas.schemas import SaleCreate, SaleUpdate
from app.services.activity_service import log_activity
from app.services.export_service import csv_response, excel_response

router = APIRouter(prefix="/sales", tags=["Penjualan"])


def sale_payload(sale: Sale, medicine: Medicine | None = None) -> dict:
    medicine = medicine or sale.medicine
    return {
        "id": sale.id,
        "transaction_code": sale.transaction_code,
        "sale_date": sale.sale_date.isoformat(),
        "medicine_id": sale.medicine_id,
        "medicine_name": medicine.name if medicine else "",
        "medicine_code": medicine.code if medicine else "",
        "unit": medicine.unit if medicine else "",
        "quantity": sale.quantity,
        "unit_price": sale.unit_price,
        "total_price": sale.total_price,
        "is_demo": sale.is_demo,
        "source": sale.source,
    }


def _filters(query, q: str, medicine_id: int | None, start: date | None, end: date | None):
    if q:
        term = f"%{q.strip()}%"
        query = query.where(
            Sale.transaction_code.ilike(term)
            | Medicine.name.ilike(term)
            | Medicine.code.ilike(term)
        )
    if medicine_id:
        query = query.where(Sale.medicine_id == medicine_id)
    if start:
        query = query.where(Sale.sale_date >= start)
    if end:
        query = query.where(Sale.sale_date <= end)
    return query


@router.get("", summary="Daftar transaksi penjualan")
def list_sales(
    q: str = "",
    medicine_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=200),
    sort_by: str = "sale_date",
    sort_dir: str = "desc",
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = select(Sale, Medicine).join(Medicine, Medicine.id == Sale.medicine_id)
    base = _filters(base, q, medicine_id, start, end)
    count_query = _filters(
        select(func.count()).select_from(Sale).join(Medicine, Medicine.id == Sale.medicine_id),
        q, medicine_id, start, end,
    )
    total = db.scalar(count_query) or 0
    sort_columns = {
        "sale_date": Sale.sale_date,
        "quantity": Sale.quantity,
        "total_price": Sale.total_price,
        "medicine_name": Medicine.name,
        "transaction_code": Sale.transaction_code,
    }
    column = sort_columns.get(sort_by, Sale.sale_date)
    ordering = column.desc() if sort_dir == "desc" else column.asc()
    rows = db.execute(
        base.order_by(ordering, Sale.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [sale_payload(sale, medicine) for sale, medicine in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/summary", summary="Ringkasan penjualan")
def sales_summary(
    start: date | None = None,
    end: date | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(
        func.coalesce(func.sum(Sale.quantity), 0),
        func.coalesce(func.sum(Sale.total_price), 0),
        func.count(Sale.id),
    ).select_from(Sale)
    if start:
        query = query.where(Sale.sale_date >= start)
    if end:
        query = query.where(Sale.sale_date <= end)
    quantity, revenue, count = db.execute(query).one()
    return {"quantity": int(quantity), "revenue": float(revenue), "transactions": int(count)}


@router.get("/export", summary="Ekspor data penjualan")
def export_sales(
    fmt: str = "csv",
    q: str = "",
    medicine_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Sale, Medicine).join(Medicine, Medicine.id == Sale.medicine_id)
    query = _filters(query, q, medicine_id, start, end).order_by(Sale.sale_date.desc())
    rows = db.execute(query).all()
    df = pd.DataFrame([{
        "ID Transaksi": sale.transaction_code,
        "Tanggal": sale.sale_date.isoformat(),
        "Kode Obat": medicine.code,
        "Nama Obat": medicine.name,
        "Jumlah": sale.quantity,
        "Satuan": medicine.unit,
        "Harga Satuan": sale.unit_price,
        "Total Harga": sale.total_price,
        "Sumber": sale.source,
    } for sale, medicine in rows])
    meta = {"Periode": f"{start or 'awal'} s.d. {end or 'akhir'}", "Jumlah baris": str(len(df))}
    if fmt == "xlsx":
        return excel_response(df, "Data_Penjualan", "Data Penjualan", meta)
    return csv_response(df, "Data_Penjualan")


@router.get("/{sale_id}", summary="Detail transaksi")
def get_sale(sale_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    return sale_payload(sale)


@router.post("", status_code=201, summary="Tambah transaksi")
def create_sale(payload: SaleCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine or not medicine.is_active:
        raise HTTPException(status_code=400, detail="Obat tidak ditemukan atau sudah tidak aktif.")
    code = payload.transaction_code.strip() or (
        f"TRX-{payload.sale_date:%Y%m%d}-{medicine.code}-{random.randint(1000, 9999)}"
    )
    duplicate = db.scalar(
        select(Sale).where(Sale.transaction_code == code, Sale.medicine_id == medicine.id)
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Transaksi dengan ID tersebut sudah ada.")
    unit_price = payload.unit_price if payload.unit_price > 0 else medicine.price
    sale = Sale(
        transaction_code=code,
        sale_date=payload.sale_date,
        medicine_id=medicine.id,
        quantity=payload.quantity,
        unit_price=unit_price,
        total_price=round(payload.quantity * unit_price, 2),
        source="manual",
        created_by=user.id,
    )
    db.add(sale)
    log_activity(db, user, "sale", f"Penjualan {medicine.name} sebanyak {payload.quantity} {medicine.unit} ditambahkan.", "sale", None)
    db.commit()
    db.refresh(sale)
    return sale_payload(sale, medicine)


@router.put("/{sale_id}", summary="Ubah transaksi")
def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    if payload.sale_date is not None:
        sale.sale_date = payload.sale_date
    if payload.medicine_id is not None:
        medicine = db.get(Medicine, payload.medicine_id)
        if not medicine:
            raise HTTPException(status_code=400, detail="Obat tidak ditemukan.")
        sale.medicine_id = medicine.id
    if payload.quantity is not None:
        sale.quantity = payload.quantity
    if payload.unit_price is not None:
        sale.unit_price = payload.unit_price
    sale.total_price = round(sale.quantity * sale.unit_price, 2)
    log_activity(db, user, "sale", f"Transaksi {sale.transaction_code} diperbarui.", "sale", sale.id)
    db.commit()
    db.refresh(sale)
    return sale_payload(sale)


@router.delete("/{sale_id}", summary="Hapus transaksi")
def delete_sale(sale_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    log_activity(db, user, "sale", f"Transaksi {sale.transaction_code} dihapus.", "sale", sale.id)
    db.delete(sale)
    db.commit()
    return {"message": "Transaksi berhasil dihapus."}
