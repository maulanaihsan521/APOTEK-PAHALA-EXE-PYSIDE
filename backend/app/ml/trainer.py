"""Training dan evaluasi model Random Forest, Decision Tree, Linear Regression.

Pembagian data dilakukan kronologis (tanpa pengacakan) agar tidak ada
kebocoran informasi masa depan ke data latih.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.tree import DecisionTreeRegressor

from app.ml.features import (
    FEATURE_COLUMNS,
    DatasetBundle,
    forecast_recursive,
)

MODEL_LABELS = {
    "random_forest": "Random Forest Regression",
    "decision_tree": "Decision Tree Regression",
    "linear_regression": "Linear Regression",
}

FEATURE_LABELS = {
    "lag_1": "Permintaan 1 pekan lalu",
    "lag_2": "Permintaan 2 pekan lalu",
    "lag_3": "Permintaan 3 pekan lalu",
    "lag_4": "Permintaan 4 pekan lalu",
    "lag_5": "Permintaan 5 pekan lalu",
    "lag_6": "Permintaan 6 pekan lalu",
    "lag_7": "Permintaan 7 pekan lalu",
    "lag_8": "Permintaan 8 pekan lalu",
    "lag_52": "Permintaan pekan sama tahun lalu",
    "roll_mean_4": "Rata-rata 4 pekan terakhir",
    "roll_mean_8": "Rata-rata 8 pekan terakhir",
    "roll_mean_12": "Rata-rata 12 pekan terakhir",
    "roll_std_4": "Fluktuasi 4 pekan terakhir",
    "week_of_year": "Pekan ke berapa dalam tahun",
    "sin_week": "Pola musiman (sinus)",
    "cos_week": "Pola musiman (cosinus)",
    "month": "Bulan",
    "temperature": "Suhu rata-rata",
    "rainfall": "Curah hujan",
    "humidity": "Kelembapan",
}


def build_model(name: str, config: dict[str, Any]):
    random_state = int(config.get("random_state", 42))
    if name == "random_forest":
        depth = int(config.get("max_depth", 0)) or None
        return RandomForestRegressor(
            n_estimators=int(config.get("n_estimators", 400)),
            max_depth=depth,
            min_samples_leaf=int(config.get("min_samples_leaf", 2)),
            random_state=random_state,
            n_jobs=int(config.get("n_jobs", -1)),
        )
    if name == "decision_tree":
        depth = int(config.get("max_depth", 0)) or 10
        return DecisionTreeRegressor(
            max_depth=depth,
            min_samples_leaf=int(config.get("min_samples_leaf", 2)),
            random_state=random_state,
        )
    return LinearRegression()


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.maximum(0, np.asarray(predicted, dtype=float))
    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(math.sqrt(mean_squared_error(actual, predicted)))
    nonzero = actual > 0
    zero_count = int((~nonzero).sum())
    if nonzero.sum() == 0:
        mape = None
    else:
        mape = float(np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])) * 100)
    # WAPE = total error / total permintaan aktual. Metrik ini dipakai sebagai
    # ukuran utama karena MAPE meledak pada pekan dengan permintaan sangat
    # rendah (mis. pekan ketika stok hampir kosong), bukan karena model buruk.
    total_actual = float(actual.sum())
    wape = (
        float(np.abs(actual - predicted).sum() / total_actual * 100)
        if total_actual > 0 else None
    )
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2) if mape is not None else None,
        "wape": round(wape, 2) if wape is not None else None,
        "mape_zero_actual": zero_count,
        "accuracy_indikatif": round(max(0.0, 100 - wape), 2) if wape is not None else None,
    }


def feature_importance(model, name: str) -> list[dict[str, Any]]:
    if name == "linear_regression":
        raw = np.abs(np.asarray(model.coef_, dtype=float)).ravel()
    else:
        raw = np.asarray(model.feature_importances_, dtype=float)
    total = raw.sum() or 1.0
    pairs = [
        {"feature": col, "label": FEATURE_LABELS.get(col, col), "importance": round(float(value / total), 4)}
        for col, value in zip(FEATURE_COLUMNS, raw)
    ]
    return sorted(pairs, key=lambda item: item["importance"], reverse=True)


def train_and_evaluate(
    bundle: DatasetBundle,
    config: dict[str, Any],
    horizon: int,
    start_date: pd.Timestamp | None = None,
    primary_model: str | None = None,
) -> dict[str, Any]:
    features = bundle.features
    requested = primary_model or config.get("primary_model", "auto")
    test_ratio = float(config.get("test_ratio", 0.2))
    test_size = max(12, int(round(len(features) * test_ratio)))
    test_size = min(test_size, len(features) - 60)
    if test_size < 8:
        raise ValueError("Data tidak cukup untuk membentuk data uji kronologis.")

    train = features.iloc[:-test_size]
    test = features.iloc[-test_size:]
    X_train, y_train = train[FEATURE_COLUMNS], train["demand"].to_numpy(dtype=float)
    X_test, y_test = test[FEATURE_COLUMNS], test["demand"].to_numpy(dtype=float)

    trained: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    metrics: dict[str, dict[str, Any]] = {}
    for name in MODEL_LABELS:
        model = build_model(name, config)
        model.fit(X_train, y_train)
        pred = np.maximum(0, model.predict(X_test))
        trained[name] = model
        predictions[name] = pred
        metrics[name] = compute_metrics(y_test, pred)

    # Mode otomatis memilih algoritma dengan WAPE terkecil pada data uji.
    if requested == "auto":
        primary = min(
            MODEL_LABELS,
            key=lambda name: (
                metrics[name].get("wape") if metrics[name].get("wape") is not None else float("inf"),
                metrics[name].get("mae", float("inf")),
            ),
        )
    else:
        primary = requested

    # Model final dilatih pada seluruh data untuk prakiraan ke depan.
    final_model = build_model(primary, config)
    final_model.fit(features[FEATURE_COLUMNS], features["demand"].to_numpy(dtype=float))
    forecast = forecast_recursive(
        bundle, horizon, lambda X: final_model.predict(X[FEATURE_COLUMNS]), start_date
    )
    residual_std = max(float(metrics[primary]["rmse"]), 1.0)
    forecast["lower_bound"] = (forecast["predicted"] - 1.96 * residual_std).clip(lower=0)
    forecast["upper_bound"] = forecast["predicted"] + 1.96 * residual_std

    backtest = pd.DataFrame({
        "week": test.index,
        "actual": y_test,
        "predicted": predictions[primary],
    })

    return {
        "primary_model": primary,
        "requested_model": requested,
        "model_label": MODEL_LABELS[primary],
        "metrics": metrics,
        "primary_metrics": metrics[primary],
        "backtest": backtest,
        "forecast": forecast[["predicted", "lower_bound", "upper_bound"]],
        "feature_importance": feature_importance(final_model, primary),
        "train_size": int(len(train)),
        "test_size": int(len(test)),
        "train_start": train.index.min(),
        "train_end": train.index.max(),
        "test_start": test.index.min(),
        "test_end": test.index.max(),
        "horizon": horizon,
    }
