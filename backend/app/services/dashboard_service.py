"""Agregasi data untuk Ringkasan Dashboard."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import DATA_LABEL
from app.ml.service import latest_runs_by_medicine
from app.models.models import (
    ActivityLog,
    Medicine,
    ModelEvaluation,
    PredictionResult,
    Sale,
    User,
)
from app.services.inventory_service import inventory_rows


def _date_bounds(db: Session, start: date | None, end: date | None, weeks: int) -> tuple[date, date]:
    max_date = db.scalar(select(func.max(Sale.sale_date)))
    if max_date is None:
        today = date.today()
        return today - timedelta(days=weeks * 7), today
    end = end or max_date
    start = start or (end - timedelta(days=weeks * 7 - 1))
    return start, end


def _period_totals(db: Session, start: date, end: date) -> dict[str, float]:
    row = db.execute(
        select(func.coalesce(func.sum(Sale.total_price), 0), func.coalesce(func.sum(Sale.quantity), 0))
        .where(Sale.sale_date.between(start, end))
    ).one()
    return {"revenue": float(row[0]), "demand": int(row[1])}


def _delta(current: float, previous: float) -> float | None:
    if previous <= 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _weekly_sales(db: Session, medicine_id: int | None = None, limit_weeks: int = 8) -> dict[date, int]:
    query = select(Sale.sale_date, Sale.quantity)
    if medicine_id:
        query = query.where(Sale.medicine_id == medicine_id)
    rows = db.execute(query).all()
    if not rows:
        return {}
    values: dict[date, int] = {}
    for sale_date, quantity in rows:
        week = sale_date - timedelta(days=sale_date.weekday())
        values[week] = values.get(week, 0) + quantity
    selected = sorted(values)[-limit_weeks:]
    return {week: values[week] for week in selected}


def dashboard_overview(
    db: Session,
    weeks: int = 4,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    weeks = weeks if weeks in (4, 12, 26, 52) else 4
    start, end = _date_bounds(db, start, end, weeks)
    period_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)

    current = _period_totals(db, start, end)
    previous = _period_totals(db, prev_start, prev_end)
    priority_count = db.scalar(
        select(func.count()).select_from(Medicine).where(Medicine.is_priority.is_(True), Medicine.is_active.is_(True))
    ) or 0

    latest_runs = latest_runs_by_medicine(db)
    evaluations = []
    for medicine_id, run in latest_runs.items():
        row = db.execute(
            select(ModelEvaluation.mape, ModelEvaluation.wape, Medicine.is_priority)
            .join(Medicine, Medicine.id == ModelEvaluation.medicine_id)
            .where(
                ModelEvaluation.medicine_id == medicine_id,
                ModelEvaluation.model_name == run.model_name,
                ModelEvaluation.wape.is_not(None),
            )
            .limit(1)
        ).first()
        if row:
            evaluations.append(row)
    priority_wapes = [row[1] for row in evaluations if row[2]]
    all_wapes = [row[1] for row in evaluations]
    wape_values = priority_wapes or all_wapes
    wape = round(sum(wape_values) / len(wape_values), 2) if wape_values else None
    priority_mapes = [row[0] for row in evaluations if row[2] and row[0] is not None]
    all_mapes = [row[0] for row in evaluations if row[0] is not None]
    mape_values = priority_mapes or all_mapes
    mape = round(sum(mape_values) / len(mape_values), 2) if mape_values else None

    # Tren aktual mingguan dan prediksi backtest pada pekan yang sama.
    weekly = _weekly_sales(db, limit_weeks=weeks)
    weeks_sorted = sorted(weekly)[-weeks:]
    backtest_map: dict[date, float] = {}
    for run in latest_runs.values():
        for result in run.results:
            if result.kind == "backtest":
                backtest_map[result.target_date] = backtest_map.get(result.target_date, 0) + result.predicted_value

    trend = {
        "labels": [week.strftime("%d %b") for week in weeks_sorted],
        "weeks": [week.isoformat() for week in weeks_sorted],
        "actual": [weekly.get(week, 0) for week in weeks_sorted],
        "predicted": [round(backtest_map.get(week, 0), 0) if week in backtest_map else None for week in weeks_sorted],
    }

    forecast_by_week: dict[int, float] = {}
    for run in latest_runs.values():
        for result in run.results:
            if result.kind == "forecast" and result.week_number <= 4:
                forecast_by_week[result.week_number] = forecast_by_week.get(result.week_number, 0) + result.predicted_value
    forecast_values = [round(forecast_by_week.get(i, 0)) for i in range(1, 5)]
    total_forecast = sum(forecast_values)

    # Top obat berdasarkan kuantitas penjualan pada periode.
    top_rows = db.execute(
        select(Medicine.id, Medicine.name, Medicine.unit,
               func.sum(Sale.quantity).label("sold"))
        .join(Sale, Sale.medicine_id == Medicine.id)
        .where(Sale.sale_date.between(start, end))
        .group_by(Medicine.id)
        .order_by(func.sum(Sale.quantity).desc())
        .limit(5)
    ).all()
    top_medicines = []
    for med_id, name, unit, sold in top_rows:
        spark = list(_weekly_sales(db, med_id, 8).values())
        run = latest_runs.get(med_id)
        predicted = 0
        if run:
            predicted = round(sum(
                item.predicted_value for item in run.results
                if item.kind == "forecast" and item.week_number <= 4
            ))
        top_medicines.append({
            "medicine_id": med_id,
            "name": name,
            "unit": unit,
            "sold": int(sold),
            "predicted": predicted,
            "sparkline": spark,
        })

    inventory = inventory_rows(db)
    stock_counts = {"aman": 0, "perlu_perhatian": 0, "kritis": 0}
    for row in inventory:
        stock_counts[row["status"]] = stock_counts.get(row["status"], 0) + 1
    total_stock = max(sum(stock_counts.values()), 1)
    stock = {
        **stock_counts,
        "total": sum(stock_counts.values()),
        "percent_aman": round(stock_counts["aman"] / total_stock * 100, 1),
        "percent_perhatian": round(stock_counts["perlu_perhatian"] / total_stock * 100, 1),
        "percent_kritis": round(stock_counts["kritis"] / total_stock * 100, 1),
    }

    activities = db.execute(
        select(ActivityLog, User.full_name)
        .join(User, User.id == ActivityLog.user_id, isouter=True)
        .order_by(ActivityLog.created_at.desc())
        .limit(6)
    ).all()
    activity_rows = [{
        "id": log.id,
        "type": log.activity_type,
        "description": log.description,
        "user": full_name or "Sistem",
        "created_at": log.created_at.isoformat(),
    } for log, full_name in activities]

    if forecast_values[3] > forecast_values[0]:
        insight = "Prediksi menunjukkan tren peningkatan permintaan."
        insight_level = "success"
    elif forecast_values[3] < forecast_values[0]:
        insight = "Prediksi menunjukkan tren penurunan permintaan."
        insight_level = "warning"
    else:
        insight = "Prediksi menunjukkan permintaan yang relatif stabil."
        insight_level = "info"

    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}",
            "weeks": weeks,
        },
        "kpis": {
            "revenue": round(current["revenue"], 2),
            "revenue_delta": _delta(current["revenue"], previous["revenue"]),
            "demand": current["demand"],
            "demand_delta": _delta(current["demand"], previous["demand"]),
            "priority_count": priority_count,
            "mape": mape,
            "wape": wape,
            "accuracy": round(max(0.0, 100 - wape), 2) if wape is not None else None,
            "wape_label": "Rata-rata WAPE model utama",
            "wape_medicine_count": len(wape_values),
            "mape_label": "Rata-rata model utama",
            "mape_medicine_count": len(mape_values),
        },
        "trend": trend,
        "prediction_summary": {
            "weeks": [{"label": f"Minggu {i}", "value": value} for i, value in enumerate(forecast_values, start=1)],
            "total": total_forecast,
            "insight": insight,
            "insight_level": insight_level,
            "horizon": 4,
        },
        "top_medicines": top_medicines,
        "stock": stock,
        "activities": activity_rows,
        "is_demo": False,
        "data_label": DATA_LABEL,
        "data_note": (
            "Data aktual dari stok opname dan pembelian. Permintaan adalah estimasi, "
            "bukan transaksi kasir."
        ),
    }
