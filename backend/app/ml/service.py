"""Layanan prediksi: menjalankan pipeline, menyimpan hasil, dan membaca riwayat."""
from __future__ import annotations

import json
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.ml.features import (
    DatasetBundle,
    InsufficientDataError,
    build_dataset,
    monday,
)
from app.ml.trainer import MODEL_LABELS, train_and_evaluate
from app.models.models import (
    Medicine,
    ModelEvaluation,
    PredictionResult,
    PredictionRun,
    Sale,
    User,
)
from app.services.activity_service import log_activity, notify
from app.services.settings_service import get_model_config


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def run_prediction(
    db: Session,
    medicine: Medicine,
    horizon: int,
    start_date: date | None,
    user: User | None,
    model_name: str | None = None,
    save: bool = True,
    silent: bool = False,
) -> dict[str, Any]:
    config = get_model_config(db)
    requested = model_name or config.get("primary_model", "auto")
    bundle = build_dataset(db, medicine.id)
    if start_date:
        start = monday(start_date)
    else:
        # Semua obat memakai periode prakiraan yang sama: pekan setelah tanggal
        # data terakhir di seluruh apotek, bukan setelah data terakhir obat itu.
        last_observed = db.scalar(select(func.max(Sale.sale_date)))
        base = pd.Timestamp(last_observed) if last_observed else bundle.last_week
        start = monday((base + pd.Timedelta(days=7)).date())
    if start <= bundle.last_week:
        start = bundle.last_week + pd.Timedelta(days=7)
    result = train_and_evaluate(bundle, config, horizon, start, requested)
    primary = result["primary_model"]
    run_params = {**config, "requested_model": requested, "selected_model": primary}

    run = PredictionRun(
        medicine_id=medicine.id,
        model_name=primary,
        horizon_weeks=horizon,
        start_date=start.date(),
        train_start=result["train_start"].date(),
        train_end=result["train_end"].date(),
        status="completed",
        params_json=json.dumps(run_params, ensure_ascii=False),
        metrics_json=json.dumps(result["metrics"], ensure_ascii=False),
        feature_importance_json=json.dumps(result["feature_importance"], ensure_ascii=False),
        dataset_version="real-v1",
        is_demo=medicine.is_demo,
        created_by=user.id if user else None,
    )
    db.add(run)
    db.flush()

    for idx, row in enumerate(result["backtest"].itertuples(index=False), start=1):
        db.add(PredictionResult(
            run_id=run.id,
            kind="backtest",
            week_number=idx,
            target_date=row.week.date(),
            predicted_value=round(float(row.predicted), 2),
            actual_value=round(float(row.actual), 2),
        ))
    for idx, (week, row) in enumerate(result["forecast"].iterrows(), start=1):
        db.add(PredictionResult(
            run_id=run.id,
            kind="forecast",
            week_number=idx,
            target_date=week.date(),
            predicted_value=round(float(row["predicted"]), 2),
            lower_bound=round(float(row["lower_bound"]), 2),
            upper_bound=round(float(row["upper_bound"]), 2),
        ))

    for name, values in result["metrics"].items():
        evaluation = db.scalar(
            select(ModelEvaluation).where(
                ModelEvaluation.medicine_id == medicine.id,
                ModelEvaluation.model_name == name,
            )
        )
        payload = {
            "mae": values["mae"],
            "rmse": values["rmse"],
            "mape": values["mape"],
            "wape": values["wape"],
            "train_size": result["train_size"],
            "test_size": result["test_size"],
            "mape_zero_actual": values["mape_zero_actual"],
            "params_json": json.dumps(run_params, ensure_ascii=False),
            "feature_importance_json": json.dumps(result["feature_importance"], ensure_ascii=False),
            "dataset_version": run.dataset_version,
            "is_demo": medicine.is_demo,
        }
        if evaluation:
            for key, value in payload.items():
                setattr(evaluation, key, value)
        else:
            db.add(ModelEvaluation(medicine_id=medicine.id, model_name=name, **payload))

    if not silent:
        log_activity(
            db, user, "prediction",
            f"Prediksi {medicine.name} {horizon} pekan berhasil dijalankan.",
            "prediction_run", run.id,
        )
        notify(
            db, "prediction", "Prediksi selesai",
            f"Prakiraan {medicine.name} untuk {horizon} pekan telah diperbarui.",
            "success",
        )
    if save:
        db.commit()
        db.refresh(run)
    return run_payload(run, medicine, result)


def run_payload(run: PredictionRun, medicine: Medicine, result: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "run_id": run.id,
        "medicine": {
            "id": medicine.id,
            "code": medicine.code,
            "name": medicine.name,
            "unit": medicine.unit,
            "category": medicine.category,
        },
        "model_name": run.model_name,
        "model_label": MODEL_LABELS.get(run.model_name, run.model_name),
        "horizon_weeks": run.horizon_weeks,
        "start_date": _iso(run.start_date),
        "train_start": _iso(run.train_start),
        "train_end": _iso(run.train_end),
        "created_at": run.created_at.isoformat(),
        "is_demo": run.is_demo,
        "metrics": result["metrics"] if result else (json.loads(run.metrics_json) if run.metrics_json else {}),
        "feature_importance": result["feature_importance"] if result else (
            json.loads(run.feature_importance_json) if run.feature_importance_json else []
        ),
        "train_size": result["train_size"] if result else None,
        "test_size": result["test_size"] if result else None,
        "backtest": [
            {"week": row.week.date().isoformat(),
             "actual": float(row.actual),
             "predicted": float(row.predicted)}
            for row in result["backtest"].itertuples(index=False)
        ] if result else [],
        "forecast": [
            {
                "week_number": item.week_number,
                "date": item.target_date.isoformat(),
                "predicted": item.predicted_value,
                "lower_bound": item.lower_bound,
                "upper_bound": item.upper_bound,
            }
            for item in run.results if item.kind == "forecast"
        ],
        "params": json.loads(run.params_json) if run.params_json else {},
    }


def serialize_run(db: Session, run: PredictionRun) -> dict[str, Any]:
    medicine = db.get(Medicine, run.medicine_id)
    data = run_payload(run, medicine) if medicine else {}
    actuals = [
        {"week": item.target_date.isoformat(), "value": item.actual_value}
        for item in run.results if item.kind == "backtest"
    ]
    data["actuals"] = actuals
    # Prediksi tersimpan tidak membawa objek hasil pelatihan, jadi susun ulang
    # kurva backtest dari PredictionResult agar evaluasi tetap dapat ditampilkan.
    data["backtest"] = [
        {
            "week": item.target_date.isoformat(),
            "actual": float(item.actual_value or 0),
            "predicted": float(item.predicted_value),
        }
        for item in run.results if item.kind == "backtest"
    ]
    evaluation = db.scalar(
        select(ModelEvaluation).where(
            ModelEvaluation.medicine_id == run.medicine_id,
            ModelEvaluation.model_name == run.model_name,
        )
    )
    if evaluation:
        data["test_size"] = evaluation.test_size
        data["train_size"] = evaluation.train_size
    return data


def latest_run(db: Session, medicine_id: int, min_horizon: int = 1) -> PredictionRun | None:
    return db.scalar(
        select(PredictionRun)
        .where(
            PredictionRun.medicine_id == medicine_id,
            PredictionRun.status == "completed",
            PredictionRun.horizon_weeks >= min_horizon,
        )
        .order_by(desc(PredictionRun.created_at), desc(PredictionRun.id))
        .limit(1)
    )


def latest_runs_by_medicine(db: Session) -> dict[int, PredictionRun]:
    runs = db.scalars(
        select(PredictionRun)
        .where(PredictionRun.status == "completed")
        .order_by(desc(PredictionRun.created_at), desc(PredictionRun.id))
    ).all()
    latest: dict[int, PredictionRun] = {}
    for run in runs:
        latest.setdefault(run.medicine_id, run)
    return latest


def forecast_for(db: Session, medicine_id: int, weeks: int = 4) -> tuple[float, PredictionRun | None]:
    run = latest_run(db, medicine_id)
    if not run:
        return 0.0, None
    total = sum(
        item.predicted_value
        for item in run.results
        if item.kind == "forecast" and item.week_number <= weeks
    )
    return float(total), run


def demand_history(bundle: DatasetBundle, weeks: int = 52) -> list[dict[str, Any]]:
    frame = bundle.weekly.tail(weeks)
    return [
        {"week": index.date().isoformat(), "demand": int(value)}
        for index, value in frame["demand"].items()
    ]
