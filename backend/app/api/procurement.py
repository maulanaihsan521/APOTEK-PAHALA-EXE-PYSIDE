"""Rekomendasi pengadaan berbasis prediksi dan stok."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.database.database import get_db
from app.models.models import Medicine, ProcurementItem, ProcurementRecommendation, User
from app.schemas.schemas import ProcurementCreate, ProcurementEditItem
from app.services.activity_service import log_activity, notify
from app.services.export_service import csv_response, excel_response, pdf_response
from app.services.procurement_service import create_recommendation, latest, serialize

router = APIRouter(prefix="/procurement", tags=["Pengadaan"])


@router.get("", summary="Daftar rekomendasi pengadaan")
def list_recommendations(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(ProcurementRecommendation).order_by(ProcurementRecommendation.created_at.desc()).limit(30)
    ).all()
    return [serialize(row, detail=False) for row in rows]


@router.get("/latest", summary="Rekomendasi terbaru")
def latest_recommendation(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = latest(db)
    if not row:
        return {"available": False, "message": "Belum ada rekomendasi pengadaan."}
    return {"available": True, **serialize(row)}


@router.post("/generate", status_code=201, summary="Buat rekomendasi pengadaan")
def generate(
    payload: ProcurementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        recommendation = create_recommendation(db, payload.period_weeks, user, payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize(recommendation)


@router.get("/{recommendation_id}", summary="Detail rekomendasi")
def get_recommendation(
    recommendation_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(ProcurementRecommendation, recommendation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan.")
    return serialize(row)


@router.post("/{recommendation_id}/approve", summary="Setujui rekomendasi (Admin)")
def approve(
    recommendation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.get(ProcurementRecommendation, recommendation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan.")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Hanya rekomendasi berstatus draf yang dapat disetujui.")
    row.status = "approved"
    log_activity(db, admin, "procurement", f"Rekomendasi {row.code} disetujui.", "procurement", row.id)
    notify(db, "procurement", "Rekomendasi disetujui", f"{row.code} siap dijadikan daftar pembelian.", "success")
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.post("/{recommendation_id}/cancel", summary="Batalkan rekomendasi")
def cancel(
    recommendation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.get(ProcurementRecommendation, recommendation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan.")
    if row.status == "approved":
        raise HTTPException(status_code=400, detail="Rekomendasi yang sudah disetujui tidak dapat dibatalkan.")
    row.status = "cancelled"
    log_activity(db, admin, "procurement", f"Rekomendasi {row.code} dibatalkan.", "procurement", row.id)
    db.commit()
    return serialize(row)


@router.patch("/{recommendation_id}/items/{item_id}", summary="Ubah jumlah pembelian")
def edit_item(
    recommendation_id: int,
    item_id: int,
    payload: ProcurementEditItem,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.get(ProcurementRecommendation, recommendation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan.")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Perubahan hanya dapat dilakukan pada draf.")
    item = db.get(ProcurementItem, item_id)
    if not item or item.recommendation_id != recommendation_id:
        raise HTTPException(status_code=404, detail="Item rekomendasi tidak ditemukan.")
    item.final_qty = payload.final_qty
    item.adjustment_reason = payload.reason
    row.total_estimated_cost = round(
        sum(entry.final_qty * entry.unit_price for entry in row.items), 2
    )
    log_activity(db, admin, "procurement",
                 f"Jumlah {item.medicine.name if item.medicine else 'obat'} diubah menjadi {payload.final_qty}.",
                 "procurement_item", item.id)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/{recommendation_id}/export", summary="Ekspor rekomendasi")
def export_recommendation(
    recommendation_id: int,
    fmt: str = "pdf",
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(ProcurementRecommendation, recommendation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rekomendasi tidak ditemukan.")
    data = serialize(row)
    table_rows = [[
        item["name"], f"{item['current_stock']:,}".replace(",", "."),
        f"{item['predicted_demand']:,.0f}".replace(",", "."),
        f"{item['safety_stock']:,}".replace(",", "."),
        f"{item['recommended_qty']:,}".replace(",", "."),
        f"{item['final_qty']:,}".replace(",", "."),
        f"Rp {item['subtotal']:,.0f}".replace(",", "."),
        item["urgency"].title(),
    ] for item in data["items"]]
    meta = {
        "Periode": f"{row.period_weeks} pekan",
        "Status": row.status.title(),
        "Kode": row.code,
    }
    if fmt == "xlsx":
        import pandas as pd
        df = pd.DataFrame(table_rows, columns=[
            "Nama Obat", "Stok Saat Ini", "Prediksi Kebutuhan", "Stok Pengaman",
            "Rekomendasi", "Jumlah Final", "Subtotal", "Urgensi",
        ])
        return excel_response(df, f"Pengadaan_{row.code}", "Rekomendasi Pengadaan", meta)
    if fmt == "csv":
        import pandas as pd
        df = pd.DataFrame(table_rows, columns=[
            "Nama Obat", "Stok Saat Ini", "Prediksi Kebutuhan", "Stok Pengaman",
            "Rekomendasi", "Jumlah Final", "Subtotal", "Urgensi",
        ])
        return csv_response(df, f"Pengadaan_{row.code}")
    summary = [
        ("Kode rekomendasi", row.code),
        ("Status", row.status.title()),
        ("Periode pengadaan", f"{row.period_weeks} pekan"),
        ("Jumlah item", str(len(data["items"]))),
        ("Total perkiraan biaya", f"Rp {row.total_estimated_cost:,.0f}".replace(",", ".")),
    ]
    return pdf_response(
        "Rekomendasi Pengadaan Obat", meta, summary,
        ["Nama Obat", "Stok", "Prediksi", "Safety", "Saran", "Final", "Subtotal", "Urgensi"],
        table_rows, f"Pengadaan_{row.code}",
        chart=[(item["name"][:14], item["final_qty"]) for item in data["items"][:8]],
        notes=("Rekomendasi dihitung dari prakiraan permintaan dikurangi stok fisik, ditambah stok pengaman "
               "dan kebutuhan lead time. Angka merupakan usulan, bukan keputusan otomatis."),
        landscape_mode=True,
    )
