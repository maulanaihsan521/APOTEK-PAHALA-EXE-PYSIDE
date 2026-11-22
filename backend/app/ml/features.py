"""Feature engineering deret permintaan mingguan.

Fitur mengikuti metodologi laporan: lag 1-8 pekan, lag tahunan 52 pekan,
rata-rata bergulir 4/8/12 pekan, deviasi bergulir 4 pekan, fitur kalender
(pekan ISO, transformasi sinus/cosinus, bulan), dan tiga variabel cuaca.
Seluruh fitur bergulir memakai shift(1) agar tidak ada kebocoran target.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Callable

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Sale, WeatherData

LAGS = list(range(1, 9))
ROLL_WINDOWS = [4, 8, 12]
FEATURE_COLUMNS = (
    [f"lag_{lag}" for lag in LAGS]
    + ["lag_52"]
    + [f"roll_mean_{w}" for w in ROLL_WINDOWS]
    + ["roll_std_4", "week_of_year", "sin_week", "cos_week", "month",
       "temperature", "rainfall", "humidity"]
)


class InsufficientDataError(Exception):
    """Dataset belum cukup untuk melatih model."""


@dataclass
class DatasetBundle:
    features: pd.DataFrame
    weekly: pd.DataFrame
    last_week: pd.Timestamp
    weather_weekly: pd.DataFrame


def monday(value: date) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts - pd.Timedelta(days=ts.weekday())


def load_weekly(db: Session, medicine_id: int) -> pd.DataFrame:
    rows = db.execute(
        select(Sale.sale_date, Sale.quantity).where(Sale.medicine_id == medicine_id)
    ).all()
    if not rows:
        raise InsufficientDataError(
            "Belum ada data permintaan untuk obat ini. Tambahkan data terlebih dahulu."
        )
    frame = pd.DataFrame(rows, columns=["sale_date", "quantity"])
    frame["sale_date"] = pd.to_datetime(frame["sale_date"])
    frame["week"] = frame["sale_date"] - pd.to_timedelta(frame["sale_date"].dt.weekday, unit="D")
    weekly = frame.groupby("week", as_index=True)["quantity"].sum().sort_index()
    full_index = pd.date_range(weekly.index.min(), weekly.index.max(), freq="7D")
    weekly = weekly.reindex(full_index, fill_value=0)
    weekly.index.name = "week"
    return weekly.to_frame("demand")


def load_weather_weekly(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(WeatherData.weather_date, WeatherData.temperature,
               WeatherData.rainfall, WeatherData.humidity)
    ).all()
    if not rows:
        return pd.DataFrame(columns=["temperature", "rainfall", "humidity"])
    frame = pd.DataFrame(rows, columns=["weather_date", "temperature", "rainfall", "humidity"])
    frame["weather_date"] = pd.to_datetime(frame["weather_date"])
    frame["week"] = frame["weather_date"] - pd.to_timedelta(frame["weather_date"].dt.weekday, unit="D")
    weekly = frame.groupby("week").agg(
        temperature=("temperature", "mean"),
        rainfall=("rainfall", "sum"),
        humidity=("humidity", "mean"),
    )
    weekly.index.name = "week"
    return weekly


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    index = pd.DatetimeIndex(df.index)
    iso = index.isocalendar()
    df["week_of_year"] = iso.week.to_numpy()
    df["month"] = index.month.to_numpy()
    df["sin_week"] = np.sin(2 * np.pi * df["week_of_year"] / 52.0)
    df["cos_week"] = np.cos(2 * np.pi * df["week_of_year"] / 52.0)
    return df


def build_dataset(db: Session, medicine_id: int) -> DatasetBundle:
    weekly = load_weekly(db, medicine_id)
    if len(weekly) < 60:
        raise InsufficientDataError(
            f"Data hanya {len(weekly)} pekan. Minimal 60 pekan diperlukan untuk membentuk lag tahunan."
        )
    weather = load_weather_weekly(db)
    df = weekly.copy()
    for lag in LAGS + [52]:
        df[f"lag_{lag}"] = df["demand"].shift(lag)
    shifted = df["demand"].shift(1)
    for window in ROLL_WINDOWS:
        df[f"roll_mean_{window}"] = shifted.rolling(window).mean()
    df["roll_std_4"] = shifted.rolling(4).std()
    df = add_calendar(df)
    if weather.empty:
        df["temperature"] = 24.0
        df["rainfall"] = 0.0
        df["humidity"] = 82.0
    else:
        df = df.join(weather, how="left")
        df[["temperature", "rainfall", "humidity"]] = (
            df[["temperature", "rainfall", "humidity"]].ffill().bfill()
        )
    df = df.dropna(subset=["lag_52", "roll_mean_12", "roll_std_4"]).copy()
    if len(df) < 60:
        raise InsufficientDataError("Data bersih tidak mencukupi setelah pembentukan fitur.")
    return DatasetBundle(
        features=df,
        weekly=weekly,
        last_week=weekly.index.max(),
        weather_weekly=weather,
    )


def climatic_weather(weather_weekly: pd.DataFrame, target: pd.Timestamp) -> dict[str, float]:
    """Skenario normal iklim: rata-rata historis menurut pekan ISO."""
    if weather_weekly.empty:
        return {"temperature": 24.0, "rainfall": 15.0, "humidity": 82.0}
    iso_week = target.isocalendar().week
    weeks = weather_weekly.index.isocalendar().week.to_numpy()
    same_week = weather_weekly[weeks == iso_week]
    if same_week.empty:
        same_week = weather_weekly
    return {
        "temperature": float(same_week["temperature"].mean()),
        "rainfall": float(same_week["rainfall"].mean()),
        "humidity": float(same_week["humidity"].mean()),
    }


def _feature_row(history: pd.Series, target: pd.Timestamp, bundle: DatasetBundle) -> dict[str, float]:
    row: dict[str, float] = {}
    for lag in LAGS + [52]:
        row[f"lag_{lag}"] = float(history.iloc[-lag]) if len(history) >= lag else float(history.mean())
    for window in ROLL_WINDOWS:
        window_values = history.iloc[-window:]
        row[f"roll_mean_{window}"] = float(window_values.mean())
    row["roll_std_4"] = float(history.iloc[-4:].std(ddof=0)) if len(history) >= 4 else 0.0
    iso_week = target.isocalendar().week
    row["week_of_year"] = iso_week
    row["month"] = target.month
    row["sin_week"] = math.sin(2 * math.pi * iso_week / 52.0)
    row["cos_week"] = math.cos(2 * math.pi * iso_week / 52.0)
    row.update(climatic_weather(bundle.weather_weekly, target))
    return row


def forecast_recursive(
    bundle: DatasetBundle,
    horizon: int,
    predict_fn: Callable[[pd.DataFrame], np.ndarray],
    start: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Prakiraan rekursif. Setiap hasil prediksi masuk kembali sebagai lag."""
    history = bundle.weekly["demand"].astype(float).copy()
    start = start or (bundle.last_week + pd.Timedelta(days=7))
    predictions: list[float] = []
    dates: list[pd.Timestamp] = []
    rows: list[dict[str, float]] = []
    for step in range(horizon):
        target = start + pd.Timedelta(days=7 * step)
        row = _feature_row(history, target, bundle)
        X = pd.DataFrame([row])[FEATURE_COLUMNS]
        value = max(0.0, float(predict_fn(X)[0]))
        predictions.append(value)
        dates.append(target)
        rows.append(row)
        history.loc[target] = value
    result = pd.DataFrame(rows, index=pd.DatetimeIndex(dates, name="week"))
    result["predicted"] = predictions
    return result
