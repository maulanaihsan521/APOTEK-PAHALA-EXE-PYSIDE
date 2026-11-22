"""Import wizard: unggah, preview, pemetaan kolom, validasi, commit."""
from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ALLOWED_EXTENSIONS, DATASET_DIR, MAX_UPLOAD_MB, UPLOAD_DIR
from app.core.deps import require_admin
from app.database.database import get_db
from app.models.models import (
    ImportBatch, Inventory, InventoryMovement, Medicine, Sale, User, WeatherData,
)
from app.services.activity_service import log_activity, notify
from app.services.export_service import csv_response

router = APIRouter(prefix="/imports", tags=["Import Data"])

REQUIRED = {
    "sales": ["sale_date", "medicine_code", "quantity"],
    "weather": ["weather_date", "temperature", "rainfall", "humidity"],
    "medicines": ["code", "name", "price"],
    "inventory": ["medicine_code", "system_stock", "physical_stock"],
}

ALIASES = {
    "sale_date": ["sale_date", "tanggal", "tgl", "date", "tanggal penjualan"],
    "medicine_code": ["medicine_code", "kode obat", "kode", "code", "kode barang", "kode_obat"],
    "medicine_name": ["medicine_name", "nama obat", "nama", "name", "nama_obat"],
    "quantity": ["quantity", "jumlah", "qty", "terjual", "kuantitas"],
    "unit_price": ["unit_price", "harga satuan", "harga", "price", "harga_satuan"],
    "transaction_code": ["transaction_code", "id transaksi", "no transaksi", "kode transaksi", "transaction"],
    "weather_date": ["weather_date", "tanggal", "tgl", "date"],
    "temperature": ["temperature", "suhu", "suhu rata-rata", "temp"],
    "rainfall": ["rainfall", "curah hujan", "hujan", "rain"],
    "humidity": ["humidity", "kelembapan", "kelembaban", "humidity (%)"],
    "code": ["code", "kode", "kode obat", "kode_obat"],
    "name": ["name", "nama", "nama obat", "nama_obat"],
    "category": ["category", "kategori"],
    "unit": ["unit", "satuan"],
    "price": ["price", "harga", "harga satuan"],
    "min_stock": ["min_stock", "minimum stok", "stok minimum", "min stok"],
    "safety_stock": ["safety_stock", "stok pengaman", "safety stok"],
    "system_stock": ["system_stock", "stok sistem", "stok_sistem"],
    "physical_stock": ["physical_stock", "stok fisik", "stok_fisik"],
    "last_opname_date": ["last_opname_date", "tanggal opname", "tgl opname"],
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _read_file(path: Path) -> pd.DataFrame:
    extension = path.suffix.lower()
    try:
        if extension == ".csv":
            try:
                frame = pd.read_csv(path, dtype=str, sep=None, engine="python", encoding="utf-8-sig")
            except UnicodeDecodeError:
                frame = pd.read_csv(path, dtype=str, sep=None, engine="python", encoding="latin-1")
        else:
            frame = pd.read_excel(path, dtype=str)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Berkas tidak dapat dibaca: {exc}") from exc
    frame = frame.fillna("")
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame


def _suggest_mapping(columns: list[str]) -> dict[str, str]:
    normalized = {_slug(column): column for column in columns}
    mapping: dict[str, str] = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if _slug(alias) in normalized:
                mapping[target] = normalized[_slug(alias)]
                break
    return mapping


def _to_float(value) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace("Rp", "").replace(" ", "")
    if not text:
        return 0.0
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    return float(text)


def _to_date(value) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    # Format ISO (YYYY-MM-DD) harus dibaca apa adanya; dayfirst akan menukar
    # bulan dan hari pada tanggal ISO yang ambigu seperti 2027-01-03.
    parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _validate_row(import_type: str, row: dict, medicine_lookup: dict[str, Medicine]) -> tuple[str | None, dict]:
    clean: dict = {}
    if import_type == "sales":
        sale_date = _to_date(row.get("sale_date"))
        if not sale_date:
            return "Tanggal tidak valid.", clean
        code = str(row.get("medicine_code", "")).strip()
        medicine = medicine_lookup.get(code.lower())
        if not medicine:
            return f"Kode obat '{code}' tidak terdaftar.", clean
        try:
            quantity = int(float(str(row.get("quantity", "0")).replace(".", "").replace(",", ".")))
        except ValueError:
            return "Jumlah bukan angka yang valid.", clean
        if quantity <= 0:
            return "Jumlah harus lebih dari nol.", clean
        try:
            price = _to_float(row.get("unit_price") or medicine.price)
        except ValueError:
            return "Harga satuan tidak valid.", clean
        if price < 0:
            return "Harga tidak boleh negatif.", clean
        clean = {
            "sale_date": sale_date,
            "medicine": medicine,
            "quantity": quantity,
            "unit_price": price,
            "transaction_code": str(row.get("transaction_code", "")).strip(),
        }
    elif import_type == "weather":
        weather_date = _to_date(row.get("weather_date"))
        if not weather_date:
            return "Tanggal cuaca tidak valid.", clean
        try:
            temperature = _to_float(row.get("temperature"))
            rainfall = _to_float(row.get("rainfall"))
            humidity = _to_float(row.get("humidity"))
        except ValueError:
            return "Nilai cuaca harus berupa angka.", clean
        if not (-10 <= temperature <= 60):
            return "Suhu di luar rentang wajar (-10 sampai 60 °C).", clean
        if not (0 <= humidity <= 100):
            return "Kelembapan harus 0-100%.", clean
        if rainfall < 0:
            return "Curah hujan tidak boleh negatif.", clean
        clean = {"weather_date": weather_date, "temperature": temperature,
                 "rainfall": rainfall, "humidity": humidity}
    elif import_type == "medicines":
        code = str(row.get("code", "")).strip()
        name = str(row.get("name", "")).strip()
        if not code:
            return "Kode obat wajib diisi.", clean
        if not name:
            return "Nama obat wajib diisi.", clean
        try:
            price = _to_float(row.get("price"))
            min_stock = int(float(str(row.get("min_stock") or 0)))
        except ValueError:
            return "Harga/stok minimum tidak valid.", clean
        clean = {
            "code": code, "name": name,
            "category": str(row.get("category") or "Umum").strip(),
            "unit": str(row.get("unit") or "Strip").strip(),
            "price": price, "min_stock": min_stock,
            "safety_stock": int(float(str(row.get("safety_stock") or 0) or 0)),
        }
    elif import_type == "inventory":
        code = str(row.get("medicine_code", "")).strip()
        medicine = medicine_lookup.get(code.lower())
        if not medicine:
            return f"Kode obat '{code}' tidak terdaftar.", clean
        try:
            system_stock = int(float(str(row.get("system_stock") or 0)))
            physical_stock = int(float(str(row.get("physical_stock") or 0)))
        except ValueError:
            return "Stok harus berupa angka bulat.", clean
        if system_stock < 0 or physical_stock < 0:
            return "Stok tidak boleh negatif.", clean
        clean = {
            "medicine": medicine, "system_stock": system_stock,
            "physical_stock": physical_stock,
            "last_opname_date": _to_date(row.get("last_opname_date")),
        }
    return None, clean


def _load_medicine_lookup(db: Session) -> dict[str, Medicine]:
    medicines = db.scalars(select(Medicine)).all()
    lookup = {}
    for medicine in medicines:
        lookup[medicine.code.lower()] = medicine
        lookup[medicine.name.lower()] = medicine
    return lookup


@router.get("/template/{import_type}", summary="Unduh template import")
def download_template(import_type: str):
    mapping = {
        "sales": "template_penjualan.csv",
        "weather": "template_cuaca.csv",
        "medicines": "template_obat.csv",
        "inventory": "template_stok.csv",
    }
    if import_type not in mapping:
        raise HTTPException(status_code=404, detail="Jenis template tidak dikenal.")
    path = DATASET_DIR / mapping[import_type]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template belum tersedia. Jalankan seeder terlebih dahulu.")
    df = pd.read_csv(path, dtype=str)
    return csv_response(df, f"Template_{import_type}")


@router.post("/preview", summary="Unggah dan pratinjau berkas")
async def preview_import(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if import_type not in REQUIRED:
        raise HTTPException(status_code=400, detail="Jenis import tidak dikenal.")
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format berkas harus CSV, XLS, atau XLSX.")
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Ukuran berkas melebihi {MAX_UPLOAD_MB} MB.")
    token = uuid.uuid4().hex
    target = UPLOAD_DIR / f"{token}{extension}"
    target.write_bytes(content)
    frame = _read_file(target)
    if frame.empty:
        raise HTTPException(status_code=422, detail="Berkas tidak berisi data.")
    if len(frame) > 50_000:
        raise HTTPException(status_code=422, detail="Maksimal 50.000 baris per import.")
    columns = list(frame.columns)
    mapping = _suggest_mapping(columns)
    missing = [field for field in REQUIRED[import_type] if field not in mapping]
    lookup = _load_medicine_lookup(db)
    errors, valid = [], 0
    for index, record in frame.head(200).iterrows():
        row = {target_field: record.get(column, "") for target_field, column in mapping.items()}
        error, _clean = _validate_row(import_type, row, lookup)
        if error:
            errors.append({"row": int(index) + 2, "message": error})
        else:
            valid += 1
    return {
        "file_token": token,
        "file_name": file.filename,
        "import_type": import_type,
        "columns": columns,
        "mapping": mapping,
        "required": REQUIRED[import_type],
        "missing": missing,
        "total_rows": int(len(frame)),
        "sample_rows": frame.head(8).to_dict("records"),
        "valid_preview": valid,
        "error_preview": errors[:20],
    }


@router.post("/commit", summary="Proses import")
def commit_import(
    file_token: str = Form(...),
    import_type: str = Form(...),
    mapping_json: str = Form(...),
    skip_duplicates: bool = Form(True),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if import_type not in REQUIRED:
        raise HTTPException(status_code=400, detail="Jenis import tidak dikenal.")
    try:
        mapping = json.loads(mapping_json)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Pemetaan kolom tidak valid.") from exc
    missing = [field for field in REQUIRED[import_type] if not mapping.get(field)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Kolom wajib belum dipetakan: {', '.join(missing)}")
    matches = list(UPLOAD_DIR.glob(f"{file_token}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Berkas pratinjau tidak ditemukan. Unggah ulang.")
    path = matches[0]
    frame = _read_file(path)
    lookup = _load_medicine_lookup(db)
    inserted = skipped = 0
    errors: list[dict] = []
    batch_code = f"IMP-{datetime.now():%Y%m%d%H%M%S}"
    seen_codes: set[tuple[str, int]] = set()
    seen_dates: set[date] = set()

    for index, record in frame.iterrows():
        row = {target_field: record.get(column, "") for target_field, column in mapping.items() if column in frame.columns}
        error, clean = _validate_row(import_type, row, lookup)
        if error:
            if len(errors) < 100:
                errors.append({"row": int(index) + 2, "message": error})
            skipped += 1
            continue
        if import_type == "sales":
            medicine: Medicine = clean["medicine"]
            code = clean["transaction_code"] or (
                f"IMP-{clean['sale_date']:%Y%m%d}-{medicine.code}-{clean['quantity']}-{int(clean['unit_price'])}"
            )
            key = (code, medicine.id)
            if key in seen_codes or db.scalar(
                select(Sale).where(Sale.transaction_code == code, Sale.medicine_id == medicine.id)
            ):
                skipped += 1
                continue
            seen_codes.add(key)
            db.add(Sale(
                transaction_code=code,
                sale_date=clean["sale_date"],
                medicine_id=medicine.id,
                quantity=clean["quantity"],
                unit_price=clean["unit_price"],
                total_price=round(clean["quantity"] * clean["unit_price"], 2),
                source="import",
                created_by=user.id,
            ))
            inserted += 1
        elif import_type == "weather":
            if clean["weather_date"] in seen_dates or db.scalar(
                select(WeatherData).where(WeatherData.weather_date == clean["weather_date"])
            ):
                skipped += 1
                continue
            seen_dates.add(clean["weather_date"])
            db.add(WeatherData(
                weather_date=clean["weather_date"], temperature=clean["temperature"],
                rainfall=clean["rainfall"], humidity=clean["humidity"],
                source="Import berkas",
            ))
            inserted += 1
        elif import_type == "medicines":
            if db.scalar(select(Medicine).where(Medicine.code == clean["code"])):
                skipped += 1
                continue
            medicine = Medicine(
                code=clean["code"], name=clean["name"], category=clean["category"],
                unit=clean["unit"], price=clean["price"], min_stock=clean["min_stock"],
                safety_stock=clean["safety_stock"], is_demo=False,
            )
            db.add(medicine)
            db.flush()
            db.add(Inventory(medicine_id=medicine.id, system_stock=0, physical_stock=0))
            lookup[medicine.code.lower()] = medicine
            inserted += 1
        elif import_type == "inventory":
            medicine = clean["medicine"]
            inventory = db.scalar(select(Inventory).where(Inventory.medicine_id == medicine.id))
            if not inventory:
                inventory = Inventory(medicine_id=medicine.id, system_stock=0, physical_stock=0)
                db.add(inventory)
                db.flush()
            if skip_duplicates and inventory.system_stock == clean["system_stock"] and inventory.physical_stock == clean["physical_stock"]:
                skipped += 1
                continue
            before = inventory.physical_stock
            inventory.system_stock = clean["system_stock"]
            inventory.physical_stock = clean["physical_stock"]
            if clean["last_opname_date"]:
                inventory.last_opname_date = clean["last_opname_date"]
            db.add(InventoryMovement(
                medicine_id=medicine.id,
                stock_before=before,
                stock_after=clean["physical_stock"],
                change_type="import",
                quantity_change=clean["physical_stock"] - before,
                user_id=user.id,
                note=f"Import stok {batch_code}",
            ))
            inserted += 1
        if inserted and inserted % 500 == 0:
            db.flush()

    batch = ImportBatch(
        batch_code=batch_code,
        import_type=import_type,
        file_name=path.name,
        total_rows=int(len(frame)),
        inserted_rows=inserted,
        skipped_rows=skipped,
        errors_json=json.dumps(errors, ensure_ascii=False),
        user_id=user.id,
    )
    db.add(batch)
    log_activity(db, user, "import",
                 f"Import {import_type} selesai: {inserted} baris masuk, {skipped} dilewati.",
                 "import", None)
    notify(db, "import", "Import data selesai",
           f"{inserted} baris {import_type} berhasil diimpor, {skipped} dilewati.",
           "success" if inserted else "warning")
    db.commit()
    path.unlink(missing_ok=True)
    return {
        "batch_code": batch_code,
        "import_type": import_type,
        "total_rows": int(len(frame)),
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
    }


@router.get("/history", summary="Riwayat import")
def import_history(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(30)).all()
    return [{
        "id": row.id,
        "batch_code": row.batch_code,
        "import_type": row.import_type,
        "file_name": row.file_name,
        "total_rows": row.total_rows,
        "inserted_rows": row.inserted_rows,
        "skipped_rows": row.skipped_rows,
        "created_at": row.created_at.isoformat(),
    } for row in rows]
