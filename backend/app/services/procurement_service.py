"""Perhitungan rekomendasi pengadaan yang transparan.

Formula (seluruh asumsi ditampilkan pada antarmuka):
  prediksi kebutuhan  = total prakiraan permintaan selama periode pengadaan
  rata-rata mingguan  = prediksi / periode
  stok pengaman       = ceil(rata-rata mingguan x safety_stock_days / 7)
  kebutuhan lead time = ceil(rata-rata mingguan x lead_time_days / 7)
  kebutuhan bersih    = max(0, prediksi + stok pengaman + kebutuhan lead time - stok fisik)
  rekomendasi         = dibulatkan ke atas sesuai satuan pembelian
Rekomendasi bukan keputusan otomatis; pengguna dapat mengubah jumlah dengan alasan.
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.ml.service import forecast_for
from app.models.models import (
    Inventory,
    Medicine,
    ProcurementItem,
    ProcurementRecommendation,
    User,
)
from app.services.activity_service import log_activity, notify
from app.services.settings_service import get_procurement_config


def _urgency(current: int, min_stock: int, net: float, avg_week: float) -> str:
    if current <= min_stock * 0.5 or (current < min_stock and net > 0):
        return "kritis"
    if current < min_stock or net >= avg_week * 2:
        return "tinggi"
    if net > 0:
        return "sedang"
    return "rendah"


def build_items(db: Session, period_weeks: int, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or get_procurement_config(db)
    safety_days = int(config.get("safety_stock_days", 14))
    lead_days = int(config.get("lead_time_days", 7))
    rounding = max(1, int(config.get("rounding_unit", 1)))
    medicines = db.scalars(select(Medicine).where(Medicine.is_active.is_(True)).order_by(Medicine.name)).all()
    rows: list[dict[str, Any]] = []
    for medicine in medicines:
        inventory = medicine.inventory or db.scalar(
            select(Inventory).where(Inventory.medicine_id == medicine.id)
        )
        current = inventory.physical_stock if inventory else 0
        predicted, run = forecast_for(db, medicine.id, period_weeks)
        if run is None:
            continue
        forecast_start = run.start_date
        forecast_end = forecast_start + timedelta(days=7 * max(period_weeks, 1) - 1)
        avg_week = predicted / max(period_weeks, 1)
        safety = math.ceil(avg_week * safety_days / 7)
        lead = math.ceil(avg_week * lead_days / 7)
        min_gap = max(0, medicine.min_stock - current)
        net = max(0.0, predicted + safety + lead - current)
        recommended = int(math.ceil(max(net, min_gap) / rounding) * rounding)
        urgency = _urgency(current, medicine.min_stock, net, avg_week)
        reason = (
            f"Prakiraan {period_weeks} pekan {predicted:,.0f} {medicine.unit}; "
            f"stok fisik {current:,}; stok pengaman {safety:,}; kebutuhan waktu tunggu {lead:,}; "
            f"minimum stok {medicine.min_stock:,}."
        ).replace(",", ".")
        rows.append({
            "medicine_id": medicine.id,
            "name": medicine.name,
            "code": medicine.code,
            "unit": medicine.unit,
            "current_stock": current,
            "predicted_demand": round(predicted, 2),
            "safety_stock": safety,
            "min_stock": medicine.min_stock,
            "recommended_qty": recommended,
            "final_qty": recommended,
            "unit_price": medicine.cost_price or medicine.price,
            "urgency": urgency,
            "reason": reason,
            "forecast_start": forecast_start,
            "forecast_end": forecast_end,
        })
    rows.sort(key=lambda row: ({"kritis": 0, "tinggi": 1, "sedang": 2, "rendah": 3}[row["urgency"]], -row["predicted_demand"]))
    return rows


def create_recommendation(
    db: Session,
    period_weeks: int,
    user: User | None,
    notes: str | None = None,
) -> ProcurementRecommendation:
    config = get_procurement_config(db)
    items = build_items(db, period_weeks, config)
    if not items:
        raise ValueError(
            "Belum ada hasil prediksi. Jalankan prediksi terlebih dahulu melalui menu Prediksi Permintaan."
        )
    prefix = f"PRC-{date.today():%Y%m%d}"
    count_today = db.scalar(
        select(func.count()).select_from(ProcurementRecommendation)
        .where(ProcurementRecommendation.code.like(f"{prefix}-%"))
    ) or 0
    code = f"{prefix}-{count_today + 1:03d}"
    assumptions = dict(config)
    starts = [row.get("forecast_start") for row in items if row.get("forecast_start")]
    ends = [row.get("forecast_end") for row in items if row.get("forecast_end")]
    if starts:
        assumptions["forecast_start"] = min(starts).isoformat()
    if ends:
        assumptions["forecast_end"] = max(ends).isoformat()
    recommendation = ProcurementRecommendation(
        code=code,
        period_weeks=period_weeks,
        status="draft",
        assumptions_json=json.dumps(assumptions, ensure_ascii=False),
        notes=notes,
        created_by=user.id if user else None,
    )
    db.add(recommendation)
    db.flush()
    total = 0.0
    for row in items:
        item = ProcurementItem(
            recommendation_id=recommendation.id,
            medicine_id=row["medicine_id"],
            current_stock=row["current_stock"],
            predicted_demand=row["predicted_demand"],
            safety_stock=row["safety_stock"],
            min_stock=row["min_stock"],
            recommended_qty=row["recommended_qty"],
            final_qty=row["final_qty"],
            unit_price=row["unit_price"],
            urgency=row["urgency"],
            reason=row["reason"],
        )
        total += row["final_qty"] * row["unit_price"]
        db.add(item)
    recommendation.total_estimated_cost = round(total, 2)
    log_activity(db, user, "procurement", f"Rekomendasi pengadaan {code} dibuat.", "procurement", recommendation.id)
    notify(db, "procurement", "Rekomendasi baru", f"{code} berisi {len(items)} usulan pembelian.", "info")
    db.commit()
    db.refresh(recommendation)
    return recommendation


def serialize(recommendation: ProcurementRecommendation, detail: bool = True) -> dict[str, Any]:
    assumptions = json.loads(recommendation.assumptions_json) if recommendation.assumptions_json else {}
    items = []
    if detail:
        for item in recommendation.items:
            items.append({
                "id": item.id,
                "medicine_id": item.medicine_id,
                "name": item.medicine.name if item.medicine else "",
                "code": item.medicine.code if item.medicine else "",
                "unit": item.medicine.unit if item.medicine else "",
                "category": item.medicine.category if item.medicine else "",
                "current_stock": item.current_stock,
                "predicted_demand": item.predicted_demand,
                "safety_stock": item.safety_stock,
                "min_stock": item.min_stock,
                "recommended_qty": item.recommended_qty,
                "final_qty": item.final_qty,
                "unit_price": item.unit_price,
                "subtotal": round(item.final_qty * item.unit_price, 2),
                "urgency": item.urgency,
                "reason": item.reason,
                "adjustment_reason": item.adjustment_reason,
            })
    return {
        "id": recommendation.id,
        "code": recommendation.code,
        "period_weeks": recommendation.period_weeks,
        "status": recommendation.status,
        "total_estimated_cost": recommendation.total_estimated_cost,
        "created_at": recommendation.created_at.isoformat(),
        "updated_at": recommendation.updated_at.isoformat(),
        "notes": recommendation.notes,
        "assumptions": assumptions,
        "forecast_start": assumptions.get("forecast_start"),
        "forecast_end": assumptions.get("forecast_end"),
        "items": items,
        "total_items": len(recommendation.items),
        "total_units": sum(item.final_qty for item in recommendation.items),
    }


def latest(db: Session) -> ProcurementRecommendation | None:
    return db.scalar(
        select(ProcurementRecommendation)
        .order_by(desc(ProcurementRecommendation.created_at), desc(ProcurementRecommendation.id))
        .limit(1)
    )
