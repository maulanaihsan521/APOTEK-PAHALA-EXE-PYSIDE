"""Master data obat."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.database.database import get_db
from app.models.models import Inventory, Medicine, Sale, User
from app.schemas.schemas import MedicineCreate, MedicineUpdate
from app.services.activity_service import log_activity, notify
from app.services.inventory_service import stock_status

router = APIRouter(prefix="/medicines", tags=["Obat"])


def medicine_payload(medicine: Medicine) -> dict:
    inventory = medicine.inventory or Inventory(medicine_id=medicine.id, system_stock=0, physical_stock=0)
    return {
        "id": medicine.id,
        "code": medicine.code,
        "name": medicine.name,
        "category": medicine.category,
        "unit": medicine.unit,
        "price": medicine.price,
        "min_stock": medicine.min_stock,
        "safety_stock": medicine.safety_stock,
        "lead_time_days": medicine.lead_time_days,
        "purchase_unit": medicine.purchase_unit,
        "is_priority": medicine.is_priority,
        "is_demo": medicine.is_demo,
        "is_active": medicine.is_active,
        "system_stock": inventory.system_stock,
        "physical_stock": inventory.physical_stock,
        "difference": inventory.physical_stock - inventory.system_stock,
        "stock_status": stock_status(inventory.physical_stock, medicine.min_stock),
        "last_opname_date": inventory.last_opname_date.isoformat() if inventory.last_opname_date else None,
    }


@router.get("", summary="Daftar obat")
def list_medicines(
    q: str = "",
    category: str = "",
    status_filter: str = Query(default="", alias="status"),
    include_inactive: bool = False,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Medicine)
    if not include_inactive:
        query = query.where(Medicine.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        query = query.where((Medicine.name.ilike(term)) | (Medicine.code.ilike(term)))
    if category:
        query = query.where(Medicine.category == category)
    medicines = db.scalars(query.order_by(Medicine.name)).all()
    rows = [medicine_payload(medicine) for medicine in medicines]
    if status_filter:
        rows = [row for row in rows if row["stock_status"] == status_filter]
    return rows


@router.get("/categories", summary="Kategori obat")
def categories(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = db.scalars(select(Medicine.category).distinct().order_by(Medicine.category)).all()
    return [value for value in values if value]


@router.get("/{medicine_id}", summary="Detail obat")
def get_medicine(medicine_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    return medicine_payload(medicine)


@router.post("", status_code=201, summary="Tambah obat")
def create_medicine(payload: MedicineCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Medicine).where(Medicine.code == payload.code)):
        raise HTTPException(status_code=409, detail="Kode obat sudah digunakan.")
    if db.scalar(select(Medicine).where(func.lower(Medicine.name) == payload.name.lower())):
        raise HTTPException(status_code=409, detail="Nama obat sudah terdaftar.")
    medicine = Medicine(
        code=payload.code.strip(),
        name=payload.name.strip(),
        category=payload.category,
        unit=payload.unit,
        price=payload.price,
        min_stock=payload.min_stock,
        safety_stock=payload.safety_stock,
        lead_time_days=payload.lead_time_days,
        purchase_unit=payload.purchase_unit,
        is_priority=payload.is_priority,
    )
    db.add(medicine)
    db.flush()
    db.add(Inventory(
        medicine_id=medicine.id,
        system_stock=payload.system_stock,
        physical_stock=payload.physical_stock,
    ))
    log_activity(db, admin, "medicine", f"Obat {medicine.name} ditambahkan.", "medicine", medicine.id)
    db.commit()
    db.refresh(medicine)
    return medicine_payload(medicine)


@router.put("/{medicine_id}", summary="Ubah obat")
def update_medicine(
    medicine_id: int,
    payload: MedicineUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    if payload.code and payload.code != medicine.code:
        if db.scalar(select(Medicine).where(Medicine.code == payload.code, Medicine.id != medicine_id)):
            raise HTTPException(status_code=409, detail="Kode obat sudah digunakan.")
        medicine.code = payload.code
    for field in ("name", "category", "unit", "price", "min_stock", "safety_stock",
                  "lead_time_days", "purchase_unit", "is_priority", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(medicine, field, value)
    log_activity(db, admin, "medicine", f"Data obat {medicine.name} diperbarui.", "medicine", medicine.id)
    db.commit()
    db.refresh(medicine)
    inventory = medicine.inventory
    physical_stock = inventory.physical_stock if inventory else 0
    if physical_stock <= medicine.min_stock:
        notify(db, "stock", "Stok kritis", f"{medicine.name} berada pada level kritis.", "danger")
        db.commit()
    return medicine_payload(medicine)


@router.delete("/{medicine_id}", summary="Nonaktifkan obat")
def delete_medicine(medicine_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    medicine = db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    medicine.is_active = False
    log_activity(db, admin, "medicine", f"Obat {medicine.name} dinonaktifkan.", "medicine", medicine.id)
    db.commit()
    return {"message": "Obat berhasil dinonaktifkan. Riwayat data permintaan tetap tersimpan."}
