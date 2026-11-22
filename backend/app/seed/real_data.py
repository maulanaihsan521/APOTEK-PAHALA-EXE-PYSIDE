"""Importer data aktual Apotek Pahala.

Sumber:
- ``ST*.DBF`` : observasi stok opname (ST_PC, ST_PHISIC, ST_PRICE).
- ``BL*.DBF`` : pembelian/retur/mutasi (BL_JML).
- ``datasets/cuaca_bandung_harian.csv`` : cuaca harian NASA POWER.

Permintaan mingguan diturunkan dari perubahan stok opname ditambah pembelian
bersih pada interval yang sama, lalu dialokasikan merata ke hari-hari interval.
Cara ini dipakai karena folder sumber tidak memuat transaksi kasir. Metode ini
transparan, bukan transaksi penjualan mentah, dan ditampilkan pada antarmuka.

Perintah:
    python -m app.seed.real_data --reset
    python -m app.seed.real_data --reset --skip-train
    python -m app.seed.real_data --export-only
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import os
import pickle
import struct
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import (
    APP_VERSION,
    DATASET_DIR,
    DEFAULT_MODEL_SETTINGS,
    DEFAULT_PROCUREMENT_SETTINGS,
    ROOT_DIR,
    STORAGE_DIR,
)
from app.core.security import hash_password
from app.database.database import Base, SessionLocal, engine
from app.ml.service import run_prediction
from app.models.models import (
    ActivityLog,
    ApplicationSetting,
    Inventory,
    InventoryMovement,
    Medicine,
    Notification,
    Role,
    Sale,
    User,
    WeatherData,
)
from app.services.activity_service import log_activity, notify
from app.services.procurement_service import create_recommendation
from app.services.settings_service import set_json

REAL_LABEL = "AKTUAL"
START_DATE = date(2022, 1, 1)
DEFAULT_PASSWORD_ADMIN = "admin123"
DEFAULT_PASSWORD_PETUGAS = "petugas123"

SOURCE_DIR = Path(os.getenv("APOTEK_SOURCE_DIR", ROOT_DIR / "DATA APOTEK PAHALA"))
CACHE_DIR = STORAGE_DIR / "source_cache"
REAL_DATASET_DIR = DATASET_DIR / "real"
WEATHER_BASE = DATASET_DIR / "cuaca_bandung_harian.csv"
WEATHER_LOCATION = {
    "name": "Bandung",
    "latitude": -6.9175,
    "longitude": 107.6191,
    "source": "NASA POWER MERRA-2",
}

# Enam obat prioritas yang diminta pengguna + 14 obat volume tertinggi dengan
# data stok memadai. Nama prioritas memakai penulisan yang diminta pengguna;
# nama asli dari DBF disimpan pada metadata.
MEDICINE_SPECS = [
    {"code": "40100", "name": "AMLODIPINE 5MG 30'S", "category": "Kardiovaskular", "unit": "Tablet", "priority": True},
    {"code": "2640", "name": "VOLTADEX 50MG 50'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": True},
    {"code": "695", "name": "DEXTEEM PLUS 100'S", "category": "Vitamin & Suplemen", "unit": "Tablet", "priority": True},
    {"code": "4576", "name": "AMLODIPINE 10MG 30'S", "category": "Kardiovaskular", "unit": "Tablet", "priority": True},
    {"code": "7059", "name": "METFORMIN 500MG", "category": "Antidiabetes", "unit": "Tablet", "priority": True},
    {"code": "2970", "name": "METHYLPREDNISOLON 4MG", "category": "Kortikosteroid", "unit": "Tablet", "priority": True},
    {"code": "1722", "name": "NEURALGIN RX KAPLET 100'S", "category": "Analgesik & Antiinflamasi", "unit": "Kapsul", "priority": False},
    {"code": "1885", "name": "PARACETAMOL 500MG 100'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": False},
    {"code": "1264", "name": "KALMETHASONE 200'S", "category": "Kortikosteroid", "unit": "Tablet", "priority": False},
    {"code": "7079", "name": "CETIRIZINE TAB 10MG", "category": "Antihistamin", "unit": "Tablet", "priority": False},
    {"code": "2110", "name": "RENADINAC 50 100'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": False},
    {"code": "8908", "name": "LICODEXON 0.5MG 200'S", "category": "Kortikosteroid", "unit": "Tablet", "priority": False},
    {"code": "22", "name": "TEOSAL", "category": "Saluran Pernapasan", "unit": "Tablet", "priority": False},
    {"code": "8001", "name": "DEXAHARSEN 0.5 200'S", "category": "Kortikosteroid", "unit": "Tablet", "priority": False},
    {"code": "73", "name": "ALLOPURINOL 100MG 100'S", "category": "Asam Urat", "unit": "Tablet", "priority": False},
    {"code": "3343", "name": "SIMVASTATIN 10MG", "category": "Kardiovaskular", "unit": "Tablet", "priority": False},
    {"code": "1705", "name": "NEO RHEUMACYL 20'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": False},
    {"code": "2044", "name": "PROMAG TAB 4X30 TAB", "category": "Saluran Cerna", "unit": "Tablet", "priority": False},
    {"code": "1985", "name": "NA.DIKLOFENAK 50MG 50'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": False},
    {"code": "2195", "name": "SANMOL TAB 100'S", "category": "Analgesik & Antiinflamasi", "unit": "Tablet", "priority": False},
]


# ---------------------------------------------------------------------------
# Pembacaan DBF dan cache
# ---------------------------------------------------------------------------

def read_dbf(path: Path) -> list[dict[str, str]]:
    """Membaca file DBF (dBase III/IV) tanpa dependensi eksternal."""
    raw = path.read_bytes()
    count = struct.unpack("<I", raw[4:8])[0]
    header_len, record_len = struct.unpack("<HH", raw[8:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while pos < header_len and raw[pos] != 0x0D:
        chunk = raw[pos:pos + 32]
        name = chunk[:11].split(b"\x00")[0].decode("latin1")
        fields.append((name, chunk[16]))
        pos += 32
    rows: list[dict[str, str]] = []
    for index in range(count):
        record = raw[header_len + index * record_len:header_len + (index + 1) * record_len]
        if not record or record[:1] == b"*":
            continue
        offset = 1
        values: dict[str, str] = {}
        for name, length in fields:
            values[name] = record[offset:offset + length].decode("cp1252", "replace").strip()
            offset += length
        rows.append(values)
    return rows


def dbf_date(path: Path) -> date | None:
    token = path.stem[2:]
    try:
        if len(token) == 4:  # BLMMYY -> awal bulan
            return date(2000 + int(token[2:4]), int(token[0:2]), 1)
        if len(token) == 6:  # DDMMYY
            return date(2000 + int(token[4:6]), int(token[2:4]), int(token[0:2]))
    except ValueError:
        return None
    return None


def number(value: str | None) -> float:
    try:
        return float((value or "0").replace(",", "."))
    except ValueError:
        return 0.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def load_source_rows(kind: str, refresh: bool = False) -> list[tuple[date, dict[str, str]]]:
    """Muat baris ST/BL dari cache pickle, atau baca seluruh DBF bila perlu."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{kind}.pkl"
    if cache_file.exists() and not refresh:
        with cache_file.open("rb") as handle:
            return pickle.load(handle)
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Folder sumber tidak ditemukan: {SOURCE_DIR}")
    rows: list[tuple[date, dict[str, str]]] = []
    files = sorted(SOURCE_DIR.glob(f"{kind}*.DBF"))
    for index, path in enumerate(files, start=1):
        day = dbf_date(path)
        if day is None:
            continue
        for row in read_dbf(path):
            rows.append((day, row))
        if index % 200 == 0:
            print(f"  {kind}: {index}/{len(files)} file")
    with cache_file.open("wb") as handle:
        pickle.dump(rows, handle, protocol=4)
    return rows


# ---------------------------------------------------------------------------
# Derivasi permintaan mingguan
# ---------------------------------------------------------------------------

def aggregate_observations(st_rows: list[tuple[date, dict[str, str]]]) -> dict[str, dict[date, dict]]:
    observations: dict[str, dict[date, dict]] = defaultdict(dict)
    for day, row in st_rows:
        if day < START_DATE:
            continue
        code = row.get("ST_KODEBR", "").strip()
        if not code:
            continue
        target = observations[code].setdefault(day, {
            "pc": 0.0,
            "physical": 0.0,
            "price": 0.0,
            "prices": [],
            "costs": [],
            "names": Counter(),
            "rows": 0,
        })
        target["pc"] += number(row.get("ST_PC"))
        target["physical"] += number(row.get("ST_PHISIC"))
        target["rows"] += 1
        name = row.get("ST_NAMABRG", "").strip()
        if name:
            target["names"][name] += 1
        price = number(row.get("ST_PRICE"))
        if price > 0:
            target["price"] = price
            target["prices"].append(price)
        cost = number(row.get("ST_COST"))
        if cost > 0:
            target["costs"].append(cost)
    return observations


def aggregate_purchases(bl_rows: list[tuple[date, dict[str, str]]]) -> dict[str, dict[date, float]]:
    purchases: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for day, row in bl_rows:
        if day < START_DATE:
            continue
        code = row.get("BL_KODEBR", "").strip()
        if code:
            purchases[code][day] += number(row.get("BL_JML"))
    return purchases


def derive_weekly(
    code: str,
    observations: dict[str, dict[date, dict]],
    purchases: dict[str, dict[date, float]],
) -> tuple[pd.Series | None, dict]:
    """Hitung deret permintaan mingguan dari interval stok opname.

    Nilai negatif (biasanya koreksi stok) dicoba dengan stok fisik. Bila tetap
    negatif, interval dianggap hilang dan minggu yang tidak tercakup penuh
    diinterpolasi. Untuk obat bervolume tinggi, minggu bernilai nol yang
    tersisa juga diinterpolasi karena bukan permintaan riil.
    """
    records = sorted(observations.get(code, {}).items())
    stats = {
        "observations": len(records),
        "negative_intervals": 0,
        "sum_negative": 0.0,
        "max_gap_days": 0,
        "first_date": records[0][0] if records else None,
        "last_date": records[-1][0] if records else None,
        "last_stock": 0.0,
        "last_system": 0.0,
        "last_price": 0.0,
        "last_cost": 0.0,
        "last_name": "",
        "coverage_days": 0,
    }
    if len(records) < 2:
        return None, stats

    latest = records[-1][1]
    stats["last_stock"] = latest["physical"]
    stats["last_system"] = latest["pc"]
    prices = sorted(latest.get("prices", []))
    stats["last_price"] = prices[len(prices) // 2] if prices else latest["price"]
    costs = sorted(latest.get("costs", []))
    stats["last_cost"] = costs[len(costs) // 2] if costs else 0.0
    stats["last_name"] = latest["names"].most_common(1)[0][0] if latest["names"] else ""
    if stats["last_price"] <= 0:
        for _, value in reversed(records):
            if value["price"] > 0:
                stats["last_price"] = value["price"]
                break
    if stats["last_cost"] <= 0:
        for _, value in reversed(records):
            values = sorted(value.get("costs", []))
            if values:
                stats["last_cost"] = values[len(values) // 2]
                break
    if not stats["last_name"]:
        for _, value in reversed(records):
            if value["names"]:
                stats["last_name"] = value["names"].most_common(1)[0][0]
                break

    purchase_map = purchases.get(code, {})
    purchase_days = sorted(purchase_map)
    prefix = [0.0]
    for day in purchase_days:
        prefix.append(prefix[-1] + purchase_map[day])

    def bought_between(start: date, end: date) -> float:
        left = bisect.bisect_right(purchase_days, start)
        right = bisect.bisect_right(purchase_days, end)
        return prefix[right] - prefix[left]

    daily: dict[date, float] = {}
    covered: set[date] = set()
    for (d1, v1), (d2, v2) in zip(records, records[1:]):
        span = (d2 - d1).days
        if span <= 0:
            continue
        stats["max_gap_days"] = max(stats["max_gap_days"], span)
        bought = bought_between(d1, d2)
        demand = v1["pc"] + bought - v2["pc"]
        if demand < 0:
            demand = v1["physical"] + bought - v2["physical"]
        if demand < 0:
            stats["negative_intervals"] += 1
            stats["sum_negative"] += demand
            continue
        rate = demand / span
        for offset in range(1, span + 1):
            day = d1 + timedelta(days=offset)
            daily[day] = rate
            covered.add(day)

    if not daily:
        return None, stats
    stats["coverage_days"] = len(covered)

    series = pd.Series(daily).sort_index()
    series.index = pd.to_datetime(series.index)
    weekly_sum = series.resample("W-MON", label="left", closed="left").sum()
    coverage = (
        pd.Series(1, index=pd.DatetimeIndex(sorted(covered)))
        .resample("W-MON", label="left", closed="left")
        .sum()
    )
    weekly = weekly_sum[coverage >= 7]
    if weekly.empty:
        return None, stats
    full_index = pd.date_range(weekly.index.min(), weekly.index.max(), freq="7D")
    weekly = weekly.reindex(full_index).interpolate(limit_direction="both")
    if float(weekly.median()) > 20:
        weekly = weekly.mask(weekly <= 0).interpolate(limit_direction="both")
    weekly = weekly.clip(lower=0).round().astype(int)
    weekly.index.name = "week"
    return weekly, stats


def build_dataset(weather_csv: Path = WEATHER_BASE) -> dict:
    print("[1/4] Membaca file stok dan pembelian ...")
    st_rows = load_source_rows("ST")
    bl_rows = load_source_rows("BL")
    print(f"      ST {len(st_rows):,} baris, BL {len(bl_rows):,} baris")
    observations = aggregate_observations(st_rows)
    purchases = aggregate_purchases(bl_rows)

    print("[2/4] Menurunkan permintaan mingguan ...")
    medicine_rows: list[dict] = []
    weekly_rows: list[dict] = []
    details: list[dict] = []
    for spec in MEDICINE_SPECS:
        code = spec["code"]
        weekly, stats = derive_weekly(code, observations, purchases)
        if weekly is None or len(weekly) < 120:
            raise ValueError(f"Data {spec['name']} ({code}) tidak cukup: {len(weekly) if weekly is not None else 0} pekan")
        recent = weekly.tail(12)
        average = float(recent.mean())
        minimum = max(1, math.ceil(average * 1.2))
        safety = max(1, math.ceil(average * 0.8))
        price = int(round(stats["last_price"] or 0))
        if price <= 0:
            raise ValueError(f"Harga {spec['name']} tidak ditemukan")
        medicine_rows.append({
            "code": code,
            "name": spec["name"],
            "category": spec["category"],
            "unit": spec["unit"],
            "price": price,
            "cost_price": int(round(stats["last_cost"] or price)),
            "min_stock": minimum,
            "safety_stock": safety,
            "lead_time_days": 7,
            "purchase_unit": spec["unit"],
            "is_priority": "1" if spec["priority"] else "0",
            "system_stock": int(round(stats["last_system"])),
            "physical_stock": int(round(stats["last_stock"])),
            "last_opname_date": stats["last_date"].isoformat() if stats["last_date"] else "",
            "avg_weekly_demand": round(average, 1),
            "data_start": weekly.index.min().date().isoformat(),
            "data_end": weekly.index.max().date().isoformat(),
            "source_name": stats["last_name"],
            "observations": stats["observations"],
            "negative_intervals": stats["negative_intervals"],
            "weeks": len(weekly),
        })
        for week, quantity in weekly.items():
            if quantity <= 0:
                continue
            weekly_rows.append({
                "week": week.date().isoformat(),
                "medicine_code": code,
                "quantity": int(quantity),
                "unit_price": price,
                "total_price": int(quantity) * price,
            })
        details.append({**spec, **{
            "source_name": stats["last_name"],
            "observations": stats["observations"],
            "negative_intervals": stats["negative_intervals"],
            "first_date": stats["first_date"].isoformat() if stats["first_date"] else "",
            "last_date": stats["last_date"].isoformat() if stats["last_date"] else "",
            "weeks": len(weekly),
            "total_demand": int(weekly.sum()),
            "avg_weekly": round(float(weekly.mean()), 1),
            "max_gap_days": stats["max_gap_days"],
        }})
        print(f"      {spec['name']:30} {len(weekly):3d} pekan, total {int(weekly.sum()):8,d}")

    print("[3/4] Menyiapkan cuaca harian ...")
    if not weather_csv.exists():
        raise FileNotFoundError(
            f"Cuaca belum tersedia: {weather_csv}. Jalankan scripts/fetch_weather.py terlebih dahulu."
        )
    weather = pd.read_csv(weather_csv, parse_dates=["weather_date"])
    weather["weather_date"] = weather["weather_date"].dt.date
    weather_rows = [
        {
            "weather_date": row.weather_date.isoformat(),
            "temperature": round(float(row.temperature), 2),
            "rainfall": round(float(row.rainfall), 2),
            "humidity": round(float(row.humidity), 2),
            "source": "NASA POWER MERRA-2 (Bandung, -6.9175, 107.6191)",
        }
        for row in weather.itertuples(index=False)
    ]
    sales_start = min(row["week"] for row in weekly_rows)
    sales_end = max(row["week"] for row in weekly_rows)
    weather_start = weather["weather_date"].min().isoformat()
    weather_end = weather["weather_date"].max().isoformat()

    print("[4/4] Menyusun metadata ...")
    metadata = {
        "dataset_label": REAL_LABEL,
        "app_version": APP_VERSION,
        "generated_at": _utcnow().isoformat(timespec="seconds") + "Z",
        "source_folder": str(SOURCE_DIR),
        "source_files": {
            "stock": len(list(SOURCE_DIR.glob("ST*.DBF"))) if SOURCE_DIR.exists() else 0,
            "purchase": len(list(SOURCE_DIR.glob("BL*.DBF"))) if SOURCE_DIR.exists() else 0,
        },
        "method": (
            "Permintaan mingguan = perubahan stok sistem (ST_PC) + pembelian bersih (BL_JML) "
            "antara dua tanggal opname, dialokasikan merata ke hari interval. Bila hasilnya negatif, "
            "dipakai stok fisik (ST_PHISIC); bila tetap negatif, interval dianggap hilang dan "
            "minggu yang tidak tercakup penuh diinterpolasi."
        ),
        "important_note": (
            "Folder sumber tidak memiliki tabel transaksi kasir. Angka permintaan adalah estimasi "
            "dari stok opname dan pembelian, bukan penjualan harian mentah."
        ),
        "period": {"sales_start": sales_start, "sales_end": sales_end,
                   "weather_start": weather_start, "weather_end": weather_end},
        "weather": {
            **WEATHER_LOCATION,
            "rows": len(weather_rows),
            "note": "Lokasi acuan Bandung; dapat diganti pada menu Pengaturan/Data Cuaca.",
        },
        "medicines": details,
        "counts": {
            "medicines": len(medicine_rows),
            "weekly_sales": len(weekly_rows),
            "weather_days": len(weather_rows),
            "total_demand": sum(row["quantity"] for row in weekly_rows),
        },
    }
    return {
        "medicines": medicine_rows,
        "sales": weekly_rows,
        "weather": weather_rows,
        "metadata": metadata,
    }


def export_dataset(dataset: dict, out_dir: Path = REAL_DATASET_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "obat.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dataset["medicines"][0].keys()))
        writer.writeheader()
        writer.writerows(dataset["medicines"])
    with (out_dir / "permintaan_mingguan.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dataset["sales"][0].keys()))
        writer.writeheader()
        writer.writerows(dataset["sales"])
    with (out_dir / "cuaca_harian.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["weather_date", "temperature", "rainfall", "humidity", "source"])
        writer.writeheader()
        writer.writerows(dataset["weather"])
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(dataset["metadata"], handle, ensure_ascii=False, indent=2)
    print(f"      Diekspor ke {out_dir}")


# ---------------------------------------------------------------------------
# Seeding database
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _create_users(db: Session) -> tuple[User, User]:
    admin_role = Role(name="admin", description="Administrator sistem dan pengadaan")
    staff_role = Role(name="petugas", description="Petugas apotek / kasir")
    db.add_all([admin_role, staff_role])
    db.flush()
    admin = User(
        username="admin",
        full_name="Admin Apotek",
        email="admin@apotekpahala.local",
        password_hash=hash_password(DEFAULT_PASSWORD_ADMIN),
        role_id=admin_role.id,
    )
    petugas = User(
        username="petugas",
        full_name="Petugas Apotek",
        email="petugas@apotekpahala.local",
        password_hash=hash_password(DEFAULT_PASSWORD_PETUGAS),
        role_id=staff_role.id,
    )
    db.add_all([admin, petugas])
    db.flush()
    return admin, petugas


def _create_medicines(db: Session, rows: list[dict]) -> list[Medicine]:
    medicines: list[Medicine] = []
    for row in rows:
        medicine = Medicine(
            code=row["code"],
            name=row["name"],
            category=row["category"],
            unit=row["unit"],
            price=float(row["price"]),
            cost_price=float(row.get("cost_price", 0) or 0),
            min_stock=int(row["min_stock"]),
            safety_stock=int(row["safety_stock"]),
            lead_time_days=int(row["lead_time_days"]),
            purchase_unit=row["purchase_unit"],
            is_priority=row["is_priority"] in ("1", "true", "True"),
            is_demo=False,
        )
        db.add(medicine)
        db.flush()
        db.add(Inventory(
            medicine_id=medicine.id,
            system_stock=int(row["system_stock"]),
            physical_stock=int(row["physical_stock"]),
            last_opname_date=date.fromisoformat(row["last_opname_date"]) if row["last_opname_date"] else None,
        ))
        medicines.append(medicine)
    db.flush()
    return medicines


def _create_sales(db: Session, medicine_ids: dict[str, int], rows: list[dict], admin: User) -> int:
    payload = []
    for row in rows:
        medicine_id = medicine_ids.get(row["medicine_code"])
        if not medicine_id:
            continue
        week = date.fromisoformat(row["week"])
        payload.append({
            "transaction_code": f"REAL-{week:%Y%m%d}-{row['medicine_code']}",
            "sale_date": week,
            "medicine_id": medicine_id,
            "quantity": int(row["quantity"]),
            "unit_price": float(row["unit_price"]),
            "total_price": float(row["total_price"]),
            "is_demo": False,
            "source": "stok_opname",
            "created_by": admin.id,
            "created_at": _utcnow(),
        })
    for start in range(0, len(payload), 4000):
        db.bulk_insert_mappings(Sale, payload[start:start + 4000])
        db.flush()
    return len(payload)


def _create_weather(db: Session, rows: list[dict]) -> int:
    payload = [{
        "weather_date": date.fromisoformat(row["weather_date"]),
        "temperature": float(row["temperature"]),
        "rainfall": float(row["rainfall"]),
        "humidity": float(row["humidity"]),
        "source": row["source"],
        "is_demo": False,
        "updated_at": _utcnow(),
    } for row in rows]
    for start in range(0, len(payload), 4000):
        db.bulk_insert_mappings(WeatherData, payload[start:start + 4000])
        db.flush()
    return len(payload)


def _create_movements(db: Session, medicines: list[Medicine], admin: User) -> None:
    for medicine in medicines:
        inventory = medicine.inventory or db.scalar(
            select(Inventory).where(Inventory.medicine_id == medicine.id)
        )
        if not inventory:
            continue
        when = datetime.combine(inventory.last_opname_date or date.today(), time(8, 0))
        db.add(InventoryMovement(
            medicine_id=medicine.id,
            movement_date=when,
            stock_before=inventory.system_stock,
            stock_after=inventory.physical_stock,
            change_type="opname",
            quantity_change=inventory.physical_stock - inventory.system_stock,
            user_id=admin.id,
            note="Stok opname terakhir dari data aktual Apotek Pahala.",
        ))


def _create_settings(db: Session, metadata: dict) -> None:
    set_json(db, "model_settings", DEFAULT_MODEL_SETTINGS)
    set_json(db, "procurement_settings", DEFAULT_PROCUREMENT_SETTINGS)
    set_json(db, "display_settings", {
        "theme": "light", "font_scale": "normal", "chart_preference": "line",
    })
    set_json(db, "weather_location", WEATHER_LOCATION)
    set_json(db, "data_source", {
        "dataset_label": REAL_LABEL,
        "dataset_type": "Data aktual Apotek Pahala",
        "sales_method": metadata["method"],
        "important_note": metadata["important_note"],
        "weather_source": metadata["weather"]["source"] + " - " + metadata["weather"]["name"],
        "weather_updated_at": metadata["period"]["weather_end"],
        "sales_records": metadata["counts"]["weekly_sales"],
        "medicine_count": metadata["counts"]["medicines"],
        "weather_days": metadata["counts"]["weather_days"],
        "period_start": metadata["period"]["sales_start"],
        "period_end": metadata["period"]["sales_end"],
        "source_folder": metadata["source_folder"],
        "generated_at": metadata["generated_at"],
    })


def _create_messages(db: Session, admin: User, metadata: dict) -> None:
    log_activity(
        db, admin, "system",
        "Database data aktual Apotek Pahala disiapkan dari stok opname dan pembelian.",
        "system", None,
    )
    log_activity(
        db, admin, "prediction",
        f"Model prediksi otomatis dilatih untuk {metadata['counts']['medicines']} obat pada data aktual.",
        "prediction_run", None,
    )
    notify(
        db, "info", "Data aktual aktif",
        "Aplikasi memakai data stok opname dan pembelian Apotek Pahala 2022-2026. "
        "Permintaan merupakan estimasi, bukan transaksi kasir.",
        "info",
    )
    critical = db.execute(
        select(Medicine.name).join(Inventory, Inventory.medicine_id == Medicine.id)
        .where(Inventory.physical_stock <= Medicine.min_stock)
    ).scalars().all()
    if critical:
        notify(
            db, "stock", "Stok kritis terdeteksi",
            ", ".join(critical[:3]) + (" dan lainnya." if len(critical) > 3 else " berada pada level kritis."),
            "danger",
        )


def seed_from_dataset(dataset: dict, reset: bool = False, train: bool = True) -> dict:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        existing = db.scalar(select(User.id).limit(1))
        if existing:
            print("Database sudah berisi data. Gunakan --reset untuk membangun ulang.")
            return {"seeded": False}

        print("[1/6] Membuat akun dan peran ...")
        admin, _petugas = _create_users(db)
        print("[2/6] Membuat master obat dan stok ...")
        medicines = _create_medicines(db, dataset["medicines"])
        medicine_ids = {medicine.code: medicine.id for medicine in medicines}
        db.commit()

        print("[3/6] Menyimpan permintaan mingguan ...")
        sales_count = _create_sales(db, medicine_ids, dataset["sales"], admin)
        _create_movements(db, medicines, admin)
        db.commit()

        print("[4/6] Menyimpan cuaca harian ...")
        weather_count = _create_weather(db, dataset["weather"])
        _create_settings(db, dataset["metadata"])
        db.commit()

        if train:
            print(f"[5/6] Melatih model untuk {len(medicines)} obat ...")
            for index, medicine in enumerate(medicines, start=1):
                try:
                    run_prediction(db, medicine, 4, None, admin, None, save=True, silent=True)
                    print(f"      {index}/{len(medicines)} {medicine.name}")
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    print(f"      ! Gagal melatih {medicine.name}: {exc}")

        print("[6/6] Membuat rekomendasi dan catatan ...")
        try:
            create_recommendation(db, 4, admin, "Rekomendasi awal berbasis prakiraan empat pekan data aktual.")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"      ! Rekomendasi dilewati: {exc}")
        _create_messages(db, admin, dataset["metadata"])
        db.commit()
        return {
            "seeded": True,
            "medicines": len(medicines),
            "sales": sales_count,
            "weather_days": weather_count,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _load_export(export_dir: Path) -> dict:
    metadata = json.loads((export_dir / "metadata.json").read_text(encoding="utf-8"))
    return {
        "medicines": _read_csv(export_dir / "obat.csv"),
        "sales": _read_csv(export_dir / "permintaan_mingguan.csv"),
        "weather": _read_csv(export_dir / "cuaca_harian.csv"),
        "metadata": metadata,
    }


def seed_from_export(export_dir: Path = REAL_DATASET_DIR, reset: bool = False, train: bool = True) -> dict:
    """Dipakai aplikasi saat database kosong; membaca CSV hasil ekspor."""
    return seed_from_dataset(_load_export(export_dir), reset=reset, train=train)


def seed_real(reset: bool = False, train: bool = True, refresh_cache: bool = False) -> dict:
    if refresh_cache:
        load_source_rows("ST", refresh=True)
        load_source_rows("BL", refresh=True)
    dataset = build_dataset()
    export_dataset(dataset)
    return seed_from_dataset(dataset, reset=reset, train=train)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importer data aktual Apotek Pahala")
    parser.add_argument("--reset", action="store_true", help="Hapus database lalu buat ulang")
    parser.add_argument("--skip-train", action="store_true", help="Lewati pelatihan model")
    parser.add_argument("--refresh-cache", action="store_true", help="Baca ulang seluruh DBF")
    parser.add_argument("--export-only", action="store_true", help="Hanya ekspor CSV, tanpa mengubah database")
    args = parser.parse_args()
    if args.export_only:
        dataset = build_dataset()
        export_dataset(dataset)
        print(json.dumps(dataset["metadata"]["counts"], indent=2, ensure_ascii=False))
        return
    result = seed_real(reset=args.reset, train=not args.skip_train, refresh_cache=args.refresh_cache)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
