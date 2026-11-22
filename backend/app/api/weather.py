"""Data cuaca historis."""
from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.database.database import get_db
from app.models.models import User, WeatherData
from app.schemas.schemas import WeatherCreate, WeatherUpdate
from app.services.activity_service import log_activity
from app.services.export_service import csv_response, excel_response

router = APIRouter(prefix="/weather", tags=["Cuaca"])


@router.get("", summary="Data cuaca harian")
def list_weather(
    q: str = "",
    start: date | None = None,
    end: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(WeatherData)
    if start:
        query = query.where(WeatherData.weather_date >= start)
    if end:
        query = query.where(WeatherData.weather_date <= end)
    if q:
        term = f"%{q}%"
        query = query.where(WeatherData.weather_date.cast(String).ilike(term))
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(WeatherData.weather_date.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [{
            "id": row.id,
            "weather_date": row.weather_date.isoformat(),
            "temperature": row.temperature,
            "rainfall": row.rainfall,
            "humidity": row.humidity,
            "source": row.source,
            "is_demo": row.is_demo,
        } for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/summary", summary="Ringkasan dan tren cuaca mingguan")
def weather_summary(
    weeks: int = Query(default=12, ge=1, le=104),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(WeatherData.weather_date, WeatherData.temperature,
               WeatherData.rainfall, WeatherData.humidity)
        .order_by(WeatherData.weather_date)
    ).all()
    if not rows:
        return {
            "temperature": None, "rainfall": None, "humidity": None,
            "labels": [], "temperature_series": [], "rainfall_series": [],
            "humidity_series": [], "source": "-", "updated_at": None, "daily_count": 0,
        }
    frame = pd.DataFrame(rows, columns=["date", "temperature", "rainfall", "humidity"])
    frame["date"] = pd.to_datetime(frame["date"])
    latest = frame["date"].max()
    cutoff = latest - pd.Timedelta(days=weeks * 7 - 1)
    recent = frame[frame["date"] >= cutoff].copy()
    recent["week"] = recent["date"] - pd.to_timedelta(recent["date"].dt.weekday, unit="D")
    weekly = recent.groupby("week").agg(
        temperature=("temperature", "mean"),
        rainfall=("rainfall", "sum"),
        humidity=("humidity", "mean"),
    )
    source = db.scalar(select(WeatherData.source).order_by(WeatherData.updated_at.desc()).limit(1)) or "-"
    return {
        "temperature": round(float(recent["temperature"].mean()), 1),
        "rainfall": round(float(recent["rainfall"].sum()), 1),
        "humidity": round(float(recent["humidity"].mean()), 1),
        "labels": [week.strftime("%d %b") for week in weekly.index],
        "temperature_series": [round(value, 1) for value in weekly["temperature"]],
        "rainfall_series": [round(value, 1) for value in weekly["rainfall"]],
        "humidity_series": [round(value, 1) for value in weekly["humidity"]],
        "source": source,
        "updated_at": latest.date().isoformat(),
        "daily_count": int(len(frame)),
        "is_demo": bool(db.scalar(select(WeatherData.is_demo).limit(1))),
    }


@router.get("/export", summary="Ekspor data cuaca")
def export_weather(
    fmt: str = "csv",
    start: date | None = None,
    end: date | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(WeatherData).order_by(WeatherData.weather_date)
    if start:
        query = query.where(WeatherData.weather_date >= start)
    if end:
        query = query.where(WeatherData.weather_date <= end)
    rows = db.scalars(query).all()
    df = pd.DataFrame([{
        "Tanggal": row.weather_date.isoformat(),
        "Suhu (°C)": row.temperature,
        "Curah Hujan (mm)": row.rainfall,
        "Kelembapan (%)": row.humidity,
        "Sumber": row.source,
    } for row in rows])
    meta = {"Periode": f"{start or 'awal'} s.d. {end or 'akhir'}", "Jumlah baris": str(len(df))}
    if fmt == "xlsx":
        return excel_response(df, "Data_Cuaca", "Data Cuaca Harian", meta)
    return csv_response(df, "Data_Cuaca")


@router.post("", status_code=201, summary="Tambah data cuaca")
def create_weather(payload: WeatherCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(WeatherData).where(WeatherData.weather_date == payload.weather_date)):
        raise HTTPException(status_code=409, detail="Data cuaca untuk tanggal tersebut sudah ada.")
    row = WeatherData(
        weather_date=payload.weather_date,
        temperature=payload.temperature,
        rainfall=payload.rainfall,
        humidity=payload.humidity,
        source="Input manual",
    )
    db.add(row)
    log_activity(db, admin, "weather", f"Data cuaca {payload.weather_date} ditambahkan.", "weather", None)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "weather_date": row.weather_date.isoformat(),
            "temperature": row.temperature, "rainfall": row.rainfall,
            "humidity": row.humidity, "source": row.source, "is_demo": row.is_demo}


@router.put("/{weather_id}", summary="Ubah data cuaca")
def update_weather(
    weather_id: int,
    payload: WeatherUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.get(WeatherData, weather_id)
    if not row:
        raise HTTPException(status_code=404, detail="Data cuaca tidak ditemukan.")
    for field in ("temperature", "rainfall", "humidity"):
        value = getattr(payload, field)
        if value is not None:
            setattr(row, field, value)
    log_activity(db, admin, "weather", f"Data cuaca {row.weather_date} diperbarui.", "weather", row.id)
    db.commit()
    return {"message": "Data cuaca diperbarui."}


@router.delete("/{weather_id}", summary="Hapus data cuaca")
def delete_weather(weather_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(WeatherData, weather_id)
    if not row:
        raise HTTPException(status_code=404, detail="Data cuaca tidak ditemukan.")
    log_activity(db, admin, "weather", f"Data cuaca {row.weather_date} dihapus.", "weather", row.id)
    db.delete(row)
    db.commit()
    return {"message": "Data cuaca dihapus."}
