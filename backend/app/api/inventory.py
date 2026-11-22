"""Manajemen stok dan riwayat perubahan."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.models import Inventory, InventoryMovement, Medicine, User
from app.schemas.schemas import StockAdjustment
from app.services.activity_service import log_activity, notify
from app.services.export_service import csv_response, excel_response
from app.services.inventory_service import inventory_rows, stock_status

router = APIRouter(prefix="/inventory", tags=["Persediaan"])


@router.get("", summary="Daftar persediaan")
def list_inventory(
    q: str = "",
    category: str = "",
    status_filter: str = Query(default="", alias="status"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = inventory_rows(db)
    if q:
        term = q.lower()
        rows = [row for row in rows if term in row["name"].lower() or term in row["code"].lower()]
    if category:
        rows = [row for row in rows if row["category"] == category]
    if status_filter:
        rows = [row for row in rows if row["status"] == status_filter]
    return rows


@router.get("/summary", summary="Ringkasan status persediaan")
def inventory_summary(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = inventory_rows(db)
    counts = {"aman": 0, "perlu_perhatian": 0, "kritis": 0}
    for row in rows:
        counts[row["status"]] += 1
    total_units = sum(row["physical_stock"] for row in rows)
    total_system = sum(row["system_stock"] for row in rows)
    total = max(len(rows), 1)
    return {
        **counts,
        "total": len(rows),
        "total_units": total_units,
        "total_system": total_system,
        "difference": total_units - total_system,
        "percent_aman": round(counts["aman"] / total * 100, 1),
        "percent_perhatian": round(counts["perlu_perhatian"] / total * 100, 1),
        "percent_kritis": round(counts["kritis"] / total * 100, 1),
        "last_opname_date": max((row["last_opname_date"] for row in rows if row["last_opname_date"]), default=None),
    }


@router.get("/movements", summary="Riwayat perubahan stok")
def list_movements(
    medicine_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(InventoryMovement, Medicine, User).join(
        Medicine, Medicine.id == InventoryMovement.medicine_id
    ).join(User, User.id == InventoryMovement.user_id, isouter=True)
    if medicine_id:
        query = query.where(InventoryMovement.medicine_id == medicine_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(InventoryMovement.movement_date.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [{
            "id": movement.id,
            "medicine_id": movement.medicine_id,
            "medicine_name": medicine.name,
            "date": movement.movement_date.isoformat(),
            "stock_before": movement.stock_before,
            "stock_after": movement.stock_after,
            "change_type": movement.change_type,
            "quantity_change": movement.quantity_change,
            "user": user.full_name if user else "Sistem",
            "note": movement.note,
        } for movement, medicine, user in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/export", summary="Ekspor data stok")
def export_inventory(
    fmt: str = "csv",
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = inventory_rows(db)
    df = pd.DataFrame([{
        "Kode Obat": row["code"],
        "Nama Obat": row["name"],
        "Kategori": row["category"],
        "Satuan": row["unit"],
        "Stok Sistem": row["system_stock"],
        "Stok Fisik": row["physical_stock"],
        "Selisih": row["difference"],
        "Minimum Stok": row["min_stock"],
        "Status": row["status"].replace("_", " ").title(),
        "Tanggal Opname": row["last_opname_date"] or "-",
    } for row in rows])
    meta = {"Jumlah obat": str(len(df)), "Sumber": "Stock opname terakhir (data aktual)"}
    if fmt == "xlsx":
        return excel_response(df, "Data_Stok", "Laporan Persediaan Obat", meta)
    return csv_response(df, "Data_Stok")


@router.post("/{medicine_id}/adjust", summary="Penyesuaian stok")
def adjust_stock(
    medicine_id: int,
    payload: StockAdjustment,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    inventory = db.scalar(select(Inventory).where(Inventory.medicine_id == medicine_id))
    if not inventory:
        inventory = Inventory(medicine_id=medicine_id, system_stock=0, physical_stock=0)
        db.add(inventory)
        db.flush()
    before = inventory.physical_stock
    if payload.system_stock is not None:
        inventory.system_stock = payload.system_stock
    if payload.physical_stock is not None:
        inventory.physical_stock = payload.physical_stock
    if payload.last_opname_date:
        inventory.last_opname_date = payload.last_opname_date
    elif payload.change_type == "opname":
        inventory.last_opname_date = date.today()
    after = inventory.physical_stock
    db.add(InventoryMovement(
        medicine_id=medicine_id,
        stock_before=before,
        stock_after=after,
        change_type=payload.change_type,
        quantity_change=after - before,
        user_id=user.id,
        note=payload.note,
    ))
    log_activity(
        db, user, "stock",
        f"Stok {medicine.name} disesuaikan dari {before} menjadi {after} ({payload.change_type}).",
        "inventory", inventory.id,
    )
    status_value = stock_status(after, medicine.min_stock)
    if status_value == "kritis":
        notify(db, "stock", "Stok kritis", f"{medicine.name} tersisa {after} {medicine.unit}.", "danger")
    elif status_value == "perlu_perhatian":
        notify(db, "stock", "Stok perlu perhatian", f"{medicine.name} tersisa {after} {medicine.unit}.", "warning")
    db.commit()
    return {
        "message": "Stok berhasil diperbarui.",
        "medicine_id": medicine_id,
        "system_stock": inventory.system_stock,
        "physical_stock": inventory.physical_stock,
        "status": status_value,
    }


@router.get("/{medicine_id}/history", summary="Riwayat stok satu obat")
def medicine_history(
    medicine_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    rows = db.scalars(
        select(InventoryMovement)
        .where(InventoryMovement.medicine_id == medicine_id)
        .order_by(InventoryMovement.movement_date.desc())
        .limit(50)
    ).all()
    return [{
        "id": row.id,
        "date": row.movement_date.isoformat(),
        "stock_before": row.stock_before,
        "stock_after": row.stock_after,
        "change_type": row.change_type,
        "quantity_change": row.quantity_change,
        "note": row.note,
    } for row in rows]
