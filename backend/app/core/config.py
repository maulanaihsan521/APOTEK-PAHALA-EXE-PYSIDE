"""Konfigurasi aplikasi Apotek Pahala.

Seluruh path dihitung relatif terhadap root proyek sehingga aplikasi dapat
dijalankan dari komputer mana pun tanpa konfigurasi khusus developer.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

APP_NAME = "Apotek Pahala"
APP_SUBTITLE = "Pharmacy Intelligence"
APP_VERSION = "1.0.0"
APP_YEAR = "2026"
DEVELOPER = "Tim Capstone Design - Sistem Informasi, Universitas Telkom"

STORAGE_DIR = Path(os.getenv("APOTEK_STORAGE_DIR", ROOT_DIR / "storage"))
DATASET_DIR = ROOT_DIR / "datasets"
MODEL_DIR = Path(os.getenv("APOTEK_MODEL_DIR", ROOT_DIR / "models"))
BACKUP_DIR = Path(os.getenv("APOTEK_BACKUP_DIR", ROOT_DIR / "backups"))
UPLOAD_DIR = STORAGE_DIR / "uploads"
for _p in (STORAGE_DIR, DATASET_DIR, MODEL_DIR, BACKUP_DIR, UPLOAD_DIR):
    _p.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("APOTEK_DB_PATH", STORAGE_DIR / "apotek_pahala.db"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

_SECRET_FILE = STORAGE_DIR / "secret.key"


def _load_secret() -> str:
    env_secret = os.getenv("SECRET_KEY", "").strip()
    if env_secret:
        return env_secret
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_text(encoding="utf-8").strip()
    value = secrets.token_urlsafe(48)
    _SECRET_FILE.write_text(value, encoding="utf-8")
    return value


SECRET_KEY = _load_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

HOST = os.getenv("APOTEK_HOST", "0.0.0.0")
PORT = int(os.getenv("APOTEK_PORT", "8000"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
).split(",")

MAX_UPLOAD_MB = 15
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Konfigurasi default model (dapat diubah dari menu Pengaturan)
DEFAULT_MODEL_SETTINGS = {
    "primary_model": "auto",
    "n_estimators": 400,
    "max_depth": 4,          # 0 = tanpa batas; 4 membatasi overfitting pada data mingguan
    "min_samples_leaf": 3,
    "random_state": 42,
    "test_ratio": 0.2,
    "horizon_weeks": 4,
    "weather_scenario": "normal_iklim",
    "n_jobs": -1,
}

DEFAULT_PROCUREMENT_SETTINGS = {
    "lead_time_days": 7,
    "safety_stock_days": 14,
    "review_period_days": 7,
    "rounding_unit": 1,
    "default_horizon_weeks": 4,
}

DATA_LABEL = "AKTUAL"
DATA_SOURCE_NOTE = (
    "Permintaan historis merupakan estimasi dari perubahan stok opname dan pembelian, "
    "bukan transaksi kasir harian."
)
