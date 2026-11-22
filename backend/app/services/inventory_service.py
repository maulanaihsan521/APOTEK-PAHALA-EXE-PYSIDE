"""Aturan status persediaan yang transparan dan dapat dikonfigurasi."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_PROCUREMENT_SETTINGS
from app.models.models import Inventory, Medicine


def stock_status(physical_stock: float, min_stock: float) -> str:
    """Aman, perlu_perhatian, atau kritis.

    Aturan: kritis bila stok <= minimum; perlu perhatian bila stok < 1,5 x
    minimum; aman bila selebihnya. Ambang dapat disesuaikan pada kode ini.
    """
    if physical_stock <= min_stock:
        return "kritis"
    if physical_stock < min_stock * 1.5:
        return "perlu_perhatian"
    return "aman"


def inventory_rows(db: Session) -> list[dict]:
    rows = db.execute(
        select(Medicine, Inventory).join(Inventory, Inventory.medicine_id == Medicine.id, isouter=True)
        .where(Medicine.is_active.is_(True))
        .order_by(Medicine.name)
    ).all()
    result = []
    for medicine, inventory in rows:
        system_stock = inventory.system_stock if inventory else 0
        physical_stock = inventory.physical_stock if inventory else 0
        result.append({
            "inventory_id": inventory.id if inventory else None,
            "medicine_id": medicine.id,
            "code": medicine.code,
            "name": medicine.name,
            "category": medicine.category,
            "unit": medicine.unit,
            "price": medicine.price,
            "system_stock": system_stock,
            "physical_stock": physical_stock,
            "difference": physical_stock - system_stock,
            "min_stock": medicine.min_stock,
            "safety_stock": medicine.safety_stock,
            "status": stock_status(physical_stock, medicine.min_stock),
            "last_opname_date": inventory.last_opname_date.isoformat() if inventory and inventory.last_opname_date else None,
            "updated_at": inventory.updated_at.isoformat() if inventory else None,
            "is_priority": medicine.is_priority,
        })
    return result


def get_procurement_assumptions(db: Session, config: dict | None = None) -> dict:
    return dict(DEFAULT_PROCUREMENT_SETTINGS) if config is None else config
