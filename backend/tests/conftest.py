"""Konfigurasi pengujian backend Apotek Pahala.

Menggunakan direktori sementara dan database SQLite terpisah agar database
utama tidak pernah tersentuh oleh pengujian.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

_TMP = Path(tempfile.mkdtemp(prefix="apotek-pahala-tests-"))
os.environ["APOTEK_STORAGE_DIR"] = str(_TMP / "storage")
os.environ["APOTEK_DB_PATH"] = str(_TMP / "storage" / "test.db")
os.environ["APOTEK_MODEL_DIR"] = str(_TMP / "models")
os.environ["APOTEK_BACKUP_DIR"] = str(_TMP / "backups")
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-32chars"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ.pop("DATABASE_URL", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import (  # noqa: E402
    Inventory,
    Medicine,
    Notification,
    Role,
    Sale,
    User,
    WeatherData,
)
from app.services.settings_service import set_json  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    """Bangun skema dan data uji yang cukup untuk melatih model."""
    Base.metadata.create_all(bind=engine)
    last_monday = date(2026, 11, 16)
    start = last_monday - timedelta(weeks=149)
    ids: dict[str, int] = {}

    with SessionLocal() as db:
        admin_role = Role(name="admin", description="Administrator")
        staff_role = Role(name="petugas", description="Petugas apotek")
        db.add_all([admin_role, staff_role])
        db.flush()

        admin = User(
            username="admin",
            full_name="Admin Pengujian",
            email="admin@test.local",
            password_hash=hash_password("admin123"),
            role_id=admin_role.id,
        )
        petugas = User(
            username="petugas",
            full_name="Petugas Pengujian",
            email="petugas@test.local",
            password_hash=hash_password("petugas123"),
            role_id=staff_role.id,
        )
        db.add_all([admin, petugas])
        db.flush()
        ids["admin_id"] = admin.id
        ids["petugas_id"] = petugas.id

        medicines = [
            Medicine(
                code="TEST-AML", name="Amlodipine Test 5mg", category="Kardiovaskular",
                unit="Strip", price=1500, min_stock=40, safety_stock=60,
                purchase_unit="Box", is_priority=True,
            ),
            Medicine(
                code="TEST-MET", name="Metformin Test 500mg", category="Metabolik",
                unit="Strip", price=900, min_stock=30, safety_stock=50,
                purchase_unit="Box", is_priority=False,
            ),
        ]
        db.add_all(medicines)
        db.flush()
        ids["medicine_1"] = medicines[0].id
        ids["medicine_2"] = medicines[1].id

        for index, medicine in enumerate(medicines):
            db.add(Inventory(
                medicine_id=medicine.id,
                system_stock=120,
                physical_stock=120,
                last_opname_date=last_monday,
            ))
            for week in range(150):
                quantity = 45 + (week % 12) * 3 + (10 if index == 0 else 0)
                db.add(Sale(
                    transaction_code=f"TEST-{medicine.code}-{week:03d}",
                    sale_date=start + timedelta(weeks=week),
                    medicine_id=medicine.id,
                    quantity=quantity,
                    unit_price=medicine.price,
                    total_price=quantity * medicine.price,
                    source="test",
                    created_by=admin.id,
                ))

        for week in range(152):
            day = start + timedelta(weeks=week)
            db.add(WeatherData(
                weather_date=day,
                temperature=23.5 + (week % 5) * 0.4,
                rainfall=12.0 + (week % 7) * 4.5,
                humidity=81.0 + (week % 4),
                source="Test fixture",
            ))

        db.add(Notification(
            title="Notifikasi pengujian",
            message="Notifikasi untuk memverifikasi endpoint.",
            category="stock",
            level="info",
        ))
        set_json(db, "model_settings", {
            "primary_model": "random_forest",
            "n_estimators": 32,
            "max_depth": 8,
            "min_samples_leaf": 2,
            "random_state": 42,
            "test_ratio": 0.2,
            "horizon_weeks": 4,
            "weather_scenario": "normal_iklim",
            "n_jobs": 1,
        })
        db.commit()

    yield ids


@pytest.fixture(scope="session")
def client(seeded_database) -> TestClient:
    # Tanpa context manager agar lifespan tidak menjalankan seeder penuh;
    # skema dan data sudah disiapkan oleh fixture seeded_database.
    return TestClient(app)


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def tokens(client: TestClient) -> dict[str, str]:
    return {
        "admin": _login(client, "admin", "admin123"),
        "petugas": _login(client, "petugas", "petugas123"),
    }


@pytest.fixture(scope="session")
def auth(tokens: dict[str, str]):
    def headers(role: str = "admin") -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens[role]}"}

    return headers


@pytest.fixture(scope="session")
def ids(seeded_database) -> dict[str, int]:
    return seeded_database
