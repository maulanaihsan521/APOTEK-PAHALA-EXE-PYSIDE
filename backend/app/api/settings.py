"""Pengaturan model, pengadaan, tampilan, database, dan informasi aplikasi."""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    APP_YEAR,
    BACKUP_DIR,
    DATABASE_URL,
    DB_PATH,
    DEVELOPER,
    ROOT_DIR,
)
from app.core.deps import get_current_user, require_admin
from app.database.database import engine, get_db
from app.models.models import (
    ApplicationSetting, Medicine, PredictionRun, Sale, User, WeatherData,
)
from app.schemas.schemas import (
    ModelSettings,
    ProcurementSettings,
    ProfileUpdate,
    SettingUpdate,
)
from app.services.activity_service import log_activity
from app.services.settings_service import (
    get_display_config,
    get_json,
    get_model_config,
    get_procurement_config,
    set_json,
)

router = APIRouter(prefix="/settings", tags=["Pengaturan"])


def app_info() -> dict:
    return {
        "name": APP_NAME,
        "subtitle": APP_SUBTITLE,
        "tagline": "Solusi Analitik untuk Persediaan Obat yang Lebih Tepat",
        "version": APP_VERSION,
        "year": APP_YEAR,
        "developer": DEVELOPER,
        "technology": [
            "Python", "FastAPI", "SQLAlchemy", "SQLite",
            "Qt (PySide) desktop", "React + TypeScript + Tailwind (mobile web)",
            "scikit-learn (Random Forest, Decision Tree, Linear Regression)", "Recharts", "ReportLab", "OpenPyXL",
        ],
        "roles": ["Admin", "Petugas"],
        "modules": [
            "Ringkasan Dashboard", "Prediksi Permintaan", "Data Penjualan", "Data Cuaca",
            "Manajemen Stok", "Rekomendasi Pengadaan", "Laporan", "Pengaturan",
        ],
    }


def database_info(db: Session) -> dict:
    sizes = {}
    for path in (DB_PATH, Path(f"{DB_PATH}-wal")):
        if path.exists():
            sizes[path.name] = path.stat().st_size
    counts = {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "medicines": db.scalar(select(func.count()).select_from(Medicine)) or 0,
        "sales": db.scalar(select(func.count()).select_from(Sale)) or 0,
        "weather_days": db.scalar(select(func.count()).select_from(WeatherData)) or 0,
        "prediction_runs": db.scalar(select(func.count()).select_from(PredictionRun)) or 0,
    }
    return {
        "path": str(DB_PATH),
        "relative_path": str(DB_PATH.relative_to(ROOT_DIR)) if DB_PATH.is_relative_to(ROOT_DIR) else str(DB_PATH),
        "size_bytes": sum(sizes.values()),
        "size_label": f"{sum(sizes.values()) / (1024 * 1024):.2f} MB",
        "connected": DB_PATH.exists(),
        "engine": "SQLite",
        "counts": counts,
        "last_modified": datetime.fromtimestamp(DB_PATH.stat().st_mtime, tz=timezone.utc).isoformat() if DB_PATH.exists() else None,
    }


def list_backups() -> list[dict]:
    backups = []
    for path in sorted(BACKUP_DIR.glob("*.db"), key=lambda item: item.stat().st_mtime, reverse=True):
        backups.append({
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "size_label": f"{path.stat().st_size / (1024 * 1024):.2f} MB",
            "created_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return backups


@router.get("", summary="Seluruh pengaturan")
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "model": get_model_config(db),
        "procurement": get_procurement_config(db),
        "display": {
            **get_display_config(db),
            "user_theme": user.theme,
            "user_font_scale": user.font_scale,
        },
        "database": database_info(db),
        "dataset": get_json(db, "data_source", {}),
        "backups": list_backups(),
        "app": app_info(),
        "profile": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.name if user.role else "",
        },
    }


@router.put("/model", summary="Simpan parameter model (Admin)")
def update_model(payload: ModelSettings, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    set_json(db, "model_settings", payload.model_dump())
    log_activity(db, admin, "settings", "Parameter model diperbarui.", "settings", None)
    db.commit()
    return {"message": "Parameter model disimpan.", "model": payload.model_dump()}


@router.put("/procurement", summary="Simpan asumsi pengadaan (Admin)")
def update_procurement(payload: ProcurementSettings, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    set_json(db, "procurement_settings", payload.model_dump())
    log_activity(db, admin, "settings", "Asumsi pengadaan diperbarui.", "settings", None)
    db.commit()
    return {"message": "Asumsi pengadaan disimpan.", "procurement": payload.model_dump()}


@router.put("/display", summary="Simpan preferensi tampilan")
def update_display(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.theme:
        user.theme = payload.theme
        display = get_display_config(db)
        display["theme"] = payload.theme
        set_json(db, "display_settings", display)
    if payload.font_scale:
        user.font_scale = payload.font_scale
        display = get_display_config(db)
        display["font_scale"] = payload.font_scale
        set_json(db, "display_settings", display)
    db.commit()
    return {"message": "Preferensi tampilan disimpan.", "theme": user.theme, "font_scale": user.font_scale}


@router.put("/profile", summary="Perbarui profil")
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.full_name:
        user.full_name = payload.full_name.strip()
    if payload.email is not None:
        user.email = payload.email
    if payload.theme:
        user.theme = payload.theme
    if payload.font_scale:
        user.font_scale = payload.font_scale
    log_activity(db, user, "account", "Profil pengguna diperbarui.", "user", user.id)
    db.commit()
    return {"message": "Profil berhasil diperbarui."}


@router.get("/app-info", summary="Informasi aplikasi")
def get_app_info():
    return app_info()


@router.get("/database/backups", summary="Daftar backup")
def backups(_: User = Depends(require_admin)):
    return list_backups()


@router.post("/database/backup", summary="Buat backup database (Admin)")
def backup_database(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"apotek_pahala_{datetime.now():%Y%m%d_%H%M%S}.db"
    try:
        source = sqlite3.connect(DB_PATH)
        destination = sqlite3.connect(target)
        with destination:
            source.backup(destination)
        source.close()
        destination.close()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Backup gagal: {exc}") from exc
    log_activity(db, admin, "backup", f"Backup database dibuat: {target.name}.", "database", None)
    db.commit()
    return {"message": "Backup berhasil dibuat.", "file": target.name, "size_label": f"{target.stat().st_size / (1024 * 1024):.2f} MB"}


@router.post("/database/restore", summary="Restore database (Admin)")
async def restore_database(
    file: UploadFile = File(...),
    confirm: bool = False,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not confirm:
        raise HTTPException(status_code=400, detail="Konfirmasi restore diperlukan. Centang konfirmasi terlebih dahulu.")
    if not file.filename or not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Berkas restore harus berekstensi .db.")
    content = await file.read()
    if len(content) < 4096:
        raise HTTPException(status_code=400, detail="Berkas database tidak valid.")
    temp_path = Path(tempfile.gettempdir()) / f"apotek_restore_{datetime.now():%Y%m%d%H%M%S}.db"
    temp_path.write_bytes(content)
    try:
        connection = sqlite3.connect(temp_path)
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        check = connection.execute("PRAGMA integrity_check").fetchone()
        connection.close()
        if check[0] != "ok":
            raise HTTPException(status_code=400, detail="Berkas database rusak (integrity check gagal).")
        if not {"users", "medicines", "sales"}.issubset(tables):
            raise HTTPException(status_code=400, detail="Berkas bukan database Apotek Pahala yang valid.")
    except sqlite3.Error as exc:
        raise HTTPException(status_code=400, detail=f"Berkas database tidak dapat dibaca: {exc}") from exc

    # Backup otomatis sebelum menimpa database aktif.
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"before_restore_{datetime.now():%Y%m%d_%H%M%S}.db"
    try:
        source = sqlite3.connect(DB_PATH)
        destination = sqlite3.connect(backup_path)
        with destination:
            source.backup(destination)
        source.close()
        destination.close()
    except sqlite3.Error:
        pass

    db.close()
    engine.dispose()
    shutil.copy2(temp_path, DB_PATH)
    for suffix in ("-wal", "-shm"):
        wal = Path(f"{DB_PATH}{suffix}")
        if wal.exists():
            wal.unlink()
    temp_path.unlink(missing_ok=True)
    engine.dispose()
    return {
        "message": "Database berhasil direstore. Silakan masuk kembali.",
        "backup_before_restore": backup_path.name,
    }
