"""Prediksi permintaan, evaluasi model, dan riwayat prediksi."""
from __future__ import annotations

import json
import time
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.database.database import get_db
from app.ml.features import InsufficientDataError, build_dataset, load_weekly
from app.ml.service import demand_history, latest_run, run_prediction, run_payload, serialize_run
from app.ml.trainer import MODEL_LABELS
from app.models.models import Medicine, ModelEvaluation, PredictionRun, Sale, User
from app.schemas.schemas import PredictionRequest
from app.services.activity_service import log_activity, notify
from app.services.export_service import csv_response, excel_response, pdf_response
from app.services.settings_service import get_model_config

router = APIRouter(prefix="/predictions", tags=["Prediksi"])


@router.get("/options", summary="Obat yang dapat diprediksi")
def prediction_options(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Medicine.id, Medicine.name, Medicine.code, Medicine.unit, Medicine.is_priority,
               func.count(func.distinct(Sale.sale_date)))
        .join(Sale, Sale.medicine_id == Medicine.id, isouter=True)
        .where(Medicine.is_active.is_(True))
        .group_by(Medicine.id)
        .order_by(Medicine.is_priority.desc(), Medicine.name)
    ).all()
    latest = {}
    for run in db.scalars(select(PredictionRun).order_by(PredictionRun.created_at.desc())).all():
        latest.setdefault(run.medicine_id, run)
    return [{
        "id": med_id,
        "name": name,
        "code": code,
        "unit": unit,
        "is_priority": priority,
        "sales_days": int(days or 0),
        "last_prediction": latest[med_id].created_at.isoformat() if med_id in latest else None,
    } for med_id, name, code, unit, priority, days in rows]


@router.post("/run", summary="Jalankan prediksi")
def predict(
    payload: PredictionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan.")
    try:
        return run_prediction(
            db, medicine, payload.horizon_weeks, payload.start_date, user,
            payload.model_name, save=payload.save,
        )
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/latest", summary="Prediksi terbaru")
def latest(
    medicine_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if medicine_id:
        run = latest_run(db, medicine_id)
        if not run:
            return {"available": False, "message": "Belum ada prediksi untuk obat ini."}
        return {"available": True, **serialize_run(db, run)}
    runs = {}
    for medicine in db.scalars(select(Medicine).where(Medicine.is_active.is_(True))).all():
        run = latest_run(db, medicine.id)
        if run:
            runs[medicine.id] = serialize_run(db, run)
    return {"available": bool(runs), "runs": runs}


@router.get("/history", summary="Riwayat prediksi")
def history(
    medicine_id: int | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(PredictionRun, Medicine).join(Medicine, Medicine.id == PredictionRun.medicine_id)
    if medicine_id:
        query = query.where(PredictionRun.medicine_id == medicine_id)
    rows = db.execute(
        query.order_by(PredictionRun.created_at.desc()).limit(limit)
    ).all()
    return [{
        "id": run.id,
        "medicine_id": run.medicine_id,
        "medicine_name": medicine.name,
        "model_name": run.model_name,
        "model_label": MODEL_LABELS.get(run.model_name, run.model_name),
        "horizon_weeks": run.horizon_weeks,
        "start_date": run.start_date.isoformat(),
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "metrics": json.loads(run.metrics_json) if run.metrics_json else {},
        "is_demo": run.is_demo,
    } for run, medicine in rows]


@router.get("/comparison", summary="Perbandingan algoritma")
def comparison(
    medicine_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(ModelEvaluation, Medicine).join(Medicine, Medicine.id == ModelEvaluation.medicine_id)
    if medicine_id:
        query = query.where(ModelEvaluation.medicine_id == medicine_id)
    rows = db.execute(query).all()
    return [{
        "medicine_id": ev.medicine_id,
        "medicine_name": medicine.name,
        "model_name": ev.model_name,
        "model_label": MODEL_LABELS.get(ev.model_name, ev.model_name),
        "mae": ev.mae,
        "rmse": ev.rmse,
        "mape": ev.mape,
        "wape": ev.wape,
        "accuracy_indikatif": round(max(0.0, 100 - ev.wape), 2) if ev.wape is not None else None,
        "train_size": ev.train_size,
        "test_size": ev.test_size,
        "mape_zero_actual": ev.mape_zero_actual,
        "trained_at": ev.trained_at.isoformat(),
        "is_demo": ev.is_demo,
    } for ev, medicine in rows]


@router.get("/evaluations/summary", summary="Rata-rata metrik per algoritma")
def evaluation_summary(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(ModelEvaluation.model_name,
               func.avg(ModelEvaluation.mae),
               func.avg(ModelEvaluation.rmse),
               func.avg(ModelEvaluation.mape),
               func.avg(ModelEvaluation.wape),
               func.count(ModelEvaluation.id),
               func.max(ModelEvaluation.trained_at))
        .group_by(ModelEvaluation.model_name)
    ).all()
    result = [{
        "model_name": name,
        "model_label": MODEL_LABELS.get(name, name),
        "mae": round(float(mae), 2) if mae is not None else None,
        "rmse": round(float(rmse), 2) if rmse is not None else None,
        "mape": round(float(mape), 2) if mape is not None else None,
        "wape": round(float(wape), 2) if wape is not None else None,
        "accuracy_indikatif": round(max(0.0, 100 - float(wape)), 2) if wape is not None else None,
        "medicine_count": int(count),
        "trained_at": trained.isoformat() if trained else None,
    } for name, mae, rmse, mape, wape, count, trained in rows]
    order = {"random_forest": 0, "linear_regression": 1, "decision_tree": 2}
    return sorted(result, key=lambda row: order.get(row["model_name"], 9))


@router.get("/feature-importance", summary="Kepentingan fitur model terbaru")
def feature_importance(
    medicine_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = latest_run(db, medicine_id)
    if not run:
        return {"available": False, "features": []}
    features = json.loads(run.feature_importance_json) if run.feature_importance_json else []
    return {
        "available": bool(features),
        "medicine_id": medicine_id,
        "model_name": run.model_name,
        "features": features[:12],
        "trained_at": run.created_at.isoformat(),
    }


@router.get("/series", summary="Deret permintaan historis")
def series(
    medicine_id: int,
    weeks: int = Query(default=52, ge=8, le=104),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        bundle = build_dataset(db, medicine_id)
    except InsufficientDataError as exc:
        return {"available": False, "message": str(exc), "history": []}
    frame = bundle.weekly.tail(weeks)
    return {
        "available": True,
        "history": [
            {"week": index.date().isoformat(), "demand": int(value)}
            for index, value in frame["demand"].items()
        ],
        "average": round(float(frame["demand"].mean()), 1),
        "maximum": int(frame["demand"].max()),
        "active_weeks": int((frame["demand"] > 0).sum()),
        "total_weeks": int(len(frame)),
    }


@router.get("/model/status", summary="Status model dan dataset")
def model_status(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = get_model_config(db)
    evaluations = db.scalars(select(ModelEvaluation).order_by(ModelEvaluation.trained_at.desc())).all()
    latest = evaluations[0].trained_at if evaluations else None
    sales_count = db.scalar(select(func.count()).select_from(Sale)) or 0
    min_date, max_date = db.execute(
        select(func.min(Sale.sale_date), func.max(Sale.sale_date))
    ).one()
    unique_medicines = db.scalar(
        select(func.count()).select_from(select(Sale.medicine_id).distinct().subquery())
    ) or 0
    primary = config.get("primary_model", "auto")
    return {
        "ready": bool(evaluations),
        "model_config": config,
        "primary_model": primary,
        "primary_model_label": (
            "Otomatis (WAPE terkecil)" if primary == "auto" else MODEL_LABELS.get(primary, primary)
        ),
        "trained_medicines": len({ev.medicine_id for ev in evaluations}),
        "last_trained_at": latest.isoformat() if latest else None,
        "dataset": {
            "sales_records": int(sales_count),
            "date_start": min_date.isoformat() if min_date else None,
            "date_end": max_date.isoformat() if max_date else None,
            "medicines_with_sales": int(unique_medicines),
            "label": "AKTUAL",
        },
        "metrics_note": (
            "MAE dan RMSE dalam satuan unit. WAPE adalah ukuran kesalahan utama (total selisih "
            "dibagi total permintaan aktual) dan lebih stabil daripada MAPE saat permintaan mingguan "
            "sangat rendah. MAPE dihitung hanya pada pekan dengan nilai aktual lebih dari nol. Data "
            "aktual merupakan estimasi permintaan dari stok opname dan pembelian, bukan transaksi kasir."
        ),
    }


@router.post("/train-all", summary="Latih ulang seluruh model (Admin)")
def train_all(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    started = time.time()
    medicines = db.scalars(select(Medicine).where(Medicine.is_active.is_(True))).all()
    trained, failed = [], []
    for medicine in medicines:
        try:
            run_prediction(db, medicine, 4, None, admin, None, save=True, silent=True)
            trained.append(medicine.name)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            failed.append({"medicine": medicine.name, "error": str(exc)})
    log_activity(db, admin, "training", f"Pelatihan ulang model selesai untuk {len(trained)} obat.", "model", None)
    notify(db, "training", "Training model selesai", f"{len(trained)} obat berhasil dilatih ulang.", "success")
    db.commit()
    return {
        "trained": len(trained),
        "failed": failed,
        "duration_seconds": round(time.time() - started, 1),
        "message": f"{len(trained)} model berhasil dilatih ulang.",
    }


@router.get("/{run_id}/export", summary="Ekspor hasil prediksi")
def export_prediction(
    run_id: int,
    fmt: str = "csv",
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.get(PredictionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Riwayat prediksi tidak ditemukan.")
    medicine = db.get(Medicine, run.medicine_id)
    payload = serialize_run(db, run)
    rows = [{
        "Pekan": item.week_number,
        "Tanggal": item.target_date.isoformat(),
        "Prediksi (unit)": item.predicted_value,
        "Batas Bawah": item.lower_bound,
        "Batas Atas": item.upper_bound,
    } for item in run.results if item.kind == "forecast"]
    df = pd.DataFrame(rows)
    meta = {"Periode": f"{run.start_date} s.d. {run.start_date}", "Obat": medicine.name,
            "Model": payload["model_label"]}
    if fmt == "xlsx":
        return excel_response(df, f"Prediksi_{medicine.code}", f"Prediksi Permintaan - {medicine.name}", meta)
    if fmt == "pdf":
        metrics = payload["metrics"].get(run.model_name, {})
        summary = [
            ("Obat", medicine.name),
            ("Model", payload["model_label"]),
            ("Horizon", f"{run.horizon_weeks} pekan"),
            ("MAE", f"{metrics.get('mae', '-')} unit"),
            ("RMSE", f"{metrics.get('rmse', '-')} unit"),
            ("WAPE", f"{metrics.get('wape', '-')}%"),
            ("MAPE", f"{metrics.get('mape', '-')}%"),
            ("Total prakiraan", f"{sum(item.predicted_value for item in run.results if item.kind == 'forecast'):,.0f} {medicine.unit}"),
        ]
        table_rows = [[item.week_number, item.target_date.isoformat(), f"{item.predicted_value:,.0f}",
                       f"{item.lower_bound:,.0f}", f"{item.upper_bound:,.0f}"] for item in run.results if item.kind == "forecast"]
        return pdf_response(
            f"Prediksi Permintaan - {medicine.name}", meta, summary,
            ["Pekan", "Tanggal", "Prediksi", "Batas Bawah", "Batas Atas"],
            table_rows, f"Prediksi_{medicine.code}",
            chart=[(item.target_date.strftime("%d %b"), item.predicted_value) for item in run.results if item.kind == "forecast"],
            notes="Prakiraan merupakan estimasi model dan bukan kepastian. Cuaca horizon menggunakan skenario normal iklim.",
        )
    return csv_response(df, f"Prediksi_{medicine.code}")
