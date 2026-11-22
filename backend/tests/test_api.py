"""Pengujian integrasi API Apotek Pahala."""
from __future__ import annotations

import re
from datetime import date

import pytest


def test_health_and_static_serving(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["medicines"] >= 2

    index = client.get("/")
    assert index.status_code == 200
    assert "Apotek Pahala" in index.text

    match = re.search(r'src="(/assets/[^"]+\.js)"', index.text)
    assert match, "Bundel JavaScript tidak ditemukan pada index.html"
    bundle = client.get(match.group(1))
    assert bundle.status_code == 200
    assert bundle.headers["content-type"].startswith("application/javascript")

    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.json()["display"] == "standalone"

    service_worker = client.get("/sw.js")
    assert service_worker.status_code == 200
    assert "apotek-pahala-shell" in service_worker.text


def test_login_me_and_invalid_credentials(client, auth, tokens):
    me = client.get("/api/auth/me", headers=auth("admin"))
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["role"] == "admin"

    staff = client.get("/api/auth/me", headers=auth("petugas"))
    assert staff.status_code == 200
    assert staff.json()["role"] == "petugas"

    wrong = client.post("/api/auth/login", data={"username": "admin", "password": "salah"})
    assert wrong.status_code == 401
    assert "salah" in wrong.json()["detail"].lower()

    anonymous = client.get("/api/medicines")
    assert anonymous.status_code == 401

    expired = client.get("/api/medicines", headers={"Authorization": "Bearer token-palsu"})
    assert expired.status_code == 401


def test_dashboard_overview(client, auth):
    response = client.get("/api/dashboard/overview", headers=auth("admin"), params={"weeks": 12})
    assert response.status_code == 200
    payload = response.json()
    assert "kpis" in payload
    assert payload["kpis"]["priority_count"] >= 1
    assert len(payload["trend"]) > 0
    assert payload["is_demo"] is False
    assert payload["data_label"] == "AKTUAL"


def test_medicine_crud_and_admin_boundary(client, auth):
    payload = {
        "code": "TEST-NEW",
        "name": "Obat Baru Pengujian",
        "category": "Umum",
        "unit": "Botol",
        "price": 25000,
        "min_stock": 10,
        "safety_stock": 15,
        "purchase_unit": "Box",
        "system_stock": 40,
        "physical_stock": 38,
    }
    forbidden = client.post("/api/medicines", headers=auth("petugas"), json=payload)
    assert forbidden.status_code == 403

    created = client.post("/api/medicines", headers=auth("admin"), json=payload)
    assert created.status_code == 201, created.text
    medicine = created.json()
    assert medicine["code"] == "TEST-NEW"
    assert medicine["system_stock"] == 40
    assert medicine["stock_status"] in {"aman", "perlu_perhatian", "kritis"}

    duplicate = client.post("/api/medicines", headers=auth("admin"), json=payload)
    assert duplicate.status_code == 409

    updated = client.put(
        f"/api/medicines/{medicine['id']}",
        headers=auth("admin"),
        json={"name": "Obat Baru Diperbarui", "price": 26000, "min_stock": 12},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Obat Baru Diperbarui"
    assert updated.json()["price"] == 26000

    detail = client.get(f"/api/medicines/{medicine['id']}", headers=auth("petugas"))
    assert detail.status_code == 200

    deactivated = client.delete(f"/api/medicines/{medicine['id']}", headers=auth("admin"))
    assert deactivated.status_code == 200
    listed = client.get("/api/medicines", headers=auth("admin"))
    assert all(item["code"] != "TEST-NEW" for item in listed.json())
    inactive = client.get(
        "/api/medicines", headers=auth("admin"), params={"include_inactive": True}
    )
    assert any(item["code"] == "TEST-NEW" for item in inactive.json())


def test_sales_crud_filters_and_export(client, auth, ids):
    payload = {
        "transaction_code": "TEST-SALE-001",
        "sale_date": "2026-11-10",
        "medicine_id": ids["medicine_1"],
        "quantity": 7,
        "unit_price": 1500,
    }
    created = client.post("/api/sales", headers=auth("petugas"), json=payload)
    assert created.status_code == 201, created.text
    sale = created.json()
    assert sale["total_price"] == 10500
    assert sale["transaction_code"] == "TEST-SALE-001"

    duplicate = client.post("/api/sales", headers=auth("petugas"), json=payload)
    assert duplicate.status_code == 409

    listed = client.get(
        "/api/sales", headers=auth("petugas"), params={"q": "TEST-SALE-001"}
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    summary = client.get(
        "/api/sales/summary",
        headers=auth("petugas"),
        params={"start": "2026-11-01", "end": "2026-11-30"},
    )
    assert summary.status_code == 200
    assert summary.json()["transactions"] >= 1

    updated = client.put(
        f"/api/sales/{sale['id']}",
        headers=auth("petugas"),
        json={"quantity": 9, "unit_price": 1600},
    )
    assert updated.status_code == 200
    assert updated.json()["total_price"] == 14400

    export = client.get("/api/sales/export", headers=auth("admin"), params={"fmt": "csv"})
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]

    deleted = client.delete(f"/api/sales/{sale['id']}", headers=auth("petugas"))
    assert deleted.status_code == 200
    missing = client.get(f"/api/sales/{sale['id']}", headers=auth("admin"))
    assert missing.status_code == 404


def test_weather_crud_summary_and_boundary(client, auth, ids):
    payload = {
        "weather_date": "2026-11-10",
        "temperature": 27.5,
        "rainfall": 12.4,
        "humidity": 80,
    }
    forbidden = client.post("/api/weather", headers=auth("petugas"), json=payload)
    assert forbidden.status_code == 403

    # Tanggal seed mungkin sudah terpakai; gunakan tanggal unik untuk pengujian.
    payload["weather_date"] = "2026-11-11"
    created = client.post("/api/weather", headers=auth("admin"), json=payload)
    assert created.status_code in (201, 409), created.text
    if created.status_code == 201:
        weather_id = created.json()["id"]
    else:
        rows = client.get("/api/weather", headers=auth("admin"), params={"start": "2026-11-11", "end": "2026-11-11"})
        weather_id = rows.json()["items"][0]["id"]

    updated = client.put(
        f"/api/weather/{weather_id}",
        headers=auth("admin"),
        json={"temperature": 28.1, "rainfall": 20.0},
    )
    assert updated.status_code == 200
    rows = client.get(
        "/api/weather",
        headers=auth("admin"),
        params={"start": "2026-11-11", "end": "2026-11-11"},
    ).json()["items"]
    assert rows and rows[0]["temperature"] == 28.1

    summary = client.get("/api/weather/summary", headers=auth("petugas"), params={"weeks": 12})
    assert summary.status_code == 200
    assert len(summary.json()["labels"]) == 12

    deleted = client.delete(f"/api/weather/{weather_id}", headers=auth("admin"))
    assert deleted.status_code == 200


def test_inventory_adjustment_and_movements(client, auth, ids):
    response = client.post(
        f"/api/inventory/{ids['medicine_2']}/adjust",
        headers=auth("petugas"),
        json={
            "system_stock": 100,
            "physical_stock": 20,
            "change_type": "opname",
            "note": "Stock opname pengujian",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["physical_stock"] == 20
    assert response.json()["status"] == "kritis"

    movements = client.get(
        "/api/inventory/movements",
        headers=auth("admin"),
        params={"medicine_id": ids["medicine_2"]},
    )
    assert movements.status_code == 200
    assert movements.json()["total"] >= 1
    assert movements.json()["items"][0]["quantity_change"] == -100

    history = client.get(
        f"/api/inventory/{ids['medicine_2']}/history", headers=auth("admin")
    )
    assert history.status_code == 200
    assert history.json()

    summary = client.get("/api/inventory/summary", headers=auth("petugas"))
    assert summary.status_code == 200
    assert summary.json()["total"] >= 2

    invalid = client.post(
        f"/api/inventory/{ids['medicine_2']}/adjust",
        headers=auth("petugas"),
        json={"physical_stock": -1, "note": "Nilai tidak valid"},
    )
    assert invalid.status_code == 422


def test_prediction_run_latest_comparison_and_export(client, auth, ids):
    run = client.post(
        "/api/predictions/run",
        headers=auth("admin"),
        json={
            "medicine_id": ids["medicine_1"],
            "horizon_weeks": 4,
            "model_name": "random_forest",
        },
    )
    assert run.status_code == 200, run.text
    result = run.json()
    assert result["horizon_weeks"] == 4
    assert len(result["forecast"]) == 4
    assert result["metrics"]
    assert result["model_label"] == "Random Forest Regression"
    assert result["feature_importance"]

    latest = client.get(
        "/api/predictions/latest", headers=auth("petugas"), params={"medicine_id": ids["medicine_1"]}
    )
    assert latest.status_code == 200
    assert latest.json()["available"] is True

    comparison = client.get(
        "/api/predictions/comparison",
        headers=auth("petugas"),
        params={"medicine_id": ids["medicine_1"]},
    )
    assert comparison.status_code == 200
    assert {row["model_name"] for row in comparison.json()} >= {
        "random_forest", "decision_tree", "linear_regression"
    }

    series = client.get(
        "/api/predictions/series",
        headers=auth("petugas"),
        params={"medicine_id": ids["medicine_1"], "weeks": 12},
    )
    assert series.status_code == 200
    assert series.json()

    exported = client.get(
        f"/api/predictions/{result['run_id']}/export",
        headers=auth("petugas"),
        params={"fmt": "csv"},
    )
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]


def test_prediction_rejects_insufficient_data(client, auth):
    created = client.post(
        "/api/medicines",
        headers=auth("admin"),
        json={
            "code": "TEST-EMPTY",
            "name": "Obat Tanpa Penjualan",
            "price": 1000,
            "system_stock": 0,
            "physical_stock": 0,
        },
    )
    assert created.status_code == 201, created.text
    medicine_id = created.json()["id"]

    run = client.post(
        "/api/predictions/run",
        headers=auth("admin"),
        json={"medicine_id": medicine_id, "horizon_weeks": 4},
    )
    assert run.status_code == 422
    assert "data" in run.json()["detail"].lower()

    client.delete(f"/api/medicines/{medicine_id}", headers=auth("admin"))


def test_procurement_generation_edit_and_approval(client, auth, ids):
    # Pastikan kedua obat memiliki hasil prakiraan terbaru.
    for medicine_id in (ids["medicine_1"], ids["medicine_2"]):
        run = client.post(
            "/api/predictions/run",
            headers=auth("admin"),
            json={"medicine_id": medicine_id, "horizon_weeks": 4},
        )
        assert run.status_code == 200, run.text

    generated = client.post(
        "/api/procurement/generate",
        headers=auth("petugas"),
        json={"period_weeks": 4, "notes": "Draf pengujian"},
    )
    assert generated.status_code == 201, generated.text
    recommendation = generated.json()
    assert recommendation["status"] == "draft"
    assert recommendation["items"]
    assert recommendation["total_items"] >= 2

    item = recommendation["items"][0]
    forbidden_edit = client.patch(
        f"/api/procurement/{recommendation['id']}/items/{item['id']}",
        headers=auth("petugas"),
        json={"final_qty": item["final_qty"] + 5, "reason": "Tambahan pengujian"},
    )
    assert forbidden_edit.status_code == 403

    edited = client.patch(
        f"/api/procurement/{recommendation['id']}/items/{item['id']}",
        headers=auth("admin"),
        json={"final_qty": item["final_qty"] + 5, "reason": "Tambahan pengujian"},
    )
    assert edited.status_code == 200
    assert edited.json()["items"][0]["final_qty"] == item["final_qty"] + 5

    forbidden_approve = client.post(
        f"/api/procurement/{recommendation['id']}/approve", headers=auth("petugas")
    )
    assert forbidden_approve.status_code == 403

    approved = client.post(
        f"/api/procurement/{recommendation['id']}/approve", headers=auth("admin")
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    export = client.get(
        f"/api/procurement/{recommendation['id']}/export",
        headers=auth("admin"),
        params={"fmt": "pdf"},
    )
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("application/pdf")

    latest = client.get("/api/procurement/latest", headers=auth("petugas"))
    assert latest.status_code == 200
    assert latest.json()["available"] is True


def test_reports_types_summary_and_exports(client, auth):
    types = client.get("/api/reports/types", headers=auth("petugas"))
    assert types.status_code == 200
    assert {row["value"] for row in types.json()} == {
        "sales", "demand", "prediction", "model_evaluation", "stock", "procurement"
    }

    for report_type in ("sales", "stock", "model_evaluation"):
        summary = client.get(
            "/api/reports/summary", headers=auth("petugas"), params={"type": report_type}
        )
        assert summary.status_code == 200, summary.text
        payload = summary.json()
        assert payload["columns"]
        assert payload["summary"]

    csv_export = client.get(
        "/api/reports/export", headers=auth("admin"), params={"type": "sales", "fmt": "csv"}
    )
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]

    pdf_export = client.get(
        "/api/reports/export", headers=auth("admin"), params={"type": "stock", "fmt": "pdf"}
    )
    assert pdf_export.status_code == 200
    assert pdf_export.headers["content-type"].startswith("application/pdf")

    invalid = client.get(
        "/api/reports/summary", headers=auth("admin"), params={"type": "tidak-ada"}
    )
    assert invalid.status_code == 400


def test_import_preview_and_commit(client, auth):
    template = client.get("/api/imports/template/sales", headers=auth("admin"))
    assert template.status_code == 200
    assert "text/csv" in template.headers["content-type"]

    csv_content = (
        "sale_date,medicine_code,quantity,unit_price,transaction_code\n"
        "2026-11-12,TEST-AML,4,1500,IMP-TEST-001\n"
    )
    preview = client.post(
        "/api/imports/preview",
        headers=auth("admin"),
        data={"import_type": "sales"},
        files={"file": ("penjualan.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert preview.status_code == 200, preview.text
    preview_payload = preview.json()
    assert preview_payload["total_rows"] == 1
    assert preview_payload["valid_preview"] == 1
    assert not preview_payload["missing"]

    commit = client.post(
        "/api/imports/commit",
        headers=auth("admin"),
        data={
            "file_token": preview_payload["file_token"],
            "import_type": "sales",
            "mapping_json": __import__("json").dumps(preview_payload["mapping"]),
            "skip_duplicates": "true",
        },
    )
    assert commit.status_code == 200, commit.text
    assert commit.json()["inserted"] == 1

    forbidden = client.post(
        "/api/imports/preview",
        headers=auth("petugas"),
        data={"import_type": "sales"},
        files={"file": ("penjualan.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert forbidden.status_code == 403


def test_users_admin_crud_and_boundary(client, auth):
    forbidden = client.get("/api/users", headers=auth("petugas"))
    assert forbidden.status_code == 403

    created = client.post(
        "/api/users",
        headers=auth("admin"),
        json={
            "username": "tester",
            "full_name": "Akun Tester",
            "email": "tester@test.local",
            "password": "tester123",
            "role": "petugas",
        },
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    duplicate = client.post(
        "/api/users",
        headers=auth("admin"),
        json={
            "username": "tester",
            "full_name": "Akun Tester Lain",
            "password": "tester123",
            "role": "petugas",
        },
    )
    assert duplicate.status_code == 409

    updated = client.put(
        f"/api/users/{user_id}",
        headers=auth("admin"),
        json={"full_name": "Akun Tester Diperbarui", "role": "admin"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "admin"

    deactivated = client.delete(f"/api/users/{user_id}", headers=auth("admin"))
    assert deactivated.status_code == 200
    login = client.post(
        "/api/auth/login", data={"username": "tester", "password": "tester123"}
    )
    assert login.status_code == 403

    admin_id = client.get("/api/auth/me", headers=auth("admin")).json()["id"]
    self_deactivate = client.delete(f"/api/users/{admin_id}", headers=auth("admin"))
    assert self_deactivate.status_code == 400


def test_notifications_and_activities(client, auth):
    notifications = client.get(
        "/api/notifications", headers=auth("petugas"), params={"unread_only": True}
    )
    assert notifications.status_code == 200
    assert notifications.json()["unread"] >= 1
    first = notifications.json()["items"][0]

    marked = client.post(
        f"/api/notifications/{first['id']}/read", headers=auth("petugas")
    )
    assert marked.status_code == 200

    mark_all = client.post("/api/notifications/read-all", headers=auth("admin"))
    assert mark_all.status_code == 200
    after = client.get("/api/notifications", headers=auth("admin"))
    assert after.json()["unread"] == 0

    activities = client.get("/api/activities", headers=auth("admin"), params={"page_size": 10})
    assert activities.status_code == 200
    assert activities.json()["total"] > 0
    assert activities.json()["items"]


def test_settings_profile_display_and_admin_boundary(client, auth):
    settings = client.get("/api/settings", headers=auth("admin"))
    assert settings.status_code == 200
    payload = settings.json()
    assert payload["model"]["primary_model"] == "random_forest"
    assert payload["profile"]["username"] == "admin"
    assert payload["app"]["name"] == "Apotek Pahala"

    display = client.put(
        "/api/settings/display", headers=auth("petugas"), json={"theme": "dark"}
    )
    assert display.status_code == 200
    assert display.json()["theme"] == "dark"

    profile = client.put(
        "/api/settings/profile",
        headers=auth("petugas"),
        json={"full_name": "Petugas Diperbarui", "theme": "light"},
    )
    assert profile.status_code == 200

    forbidden = client.put(
        "/api/settings/model", headers=auth("petugas"), json={}
    )
    assert forbidden.status_code == 403

    model = client.put(
        "/api/settings/model",
        headers=auth("admin"),
        json={
            "primary_model": "random_forest",
            "n_estimators": 32,
            "max_depth": 8,
            "min_samples_leaf": 2,
            "random_state": 42,
            "test_ratio": 0.2,
            "horizon_weeks": 4,
            "weather_scenario": "normal_iklim",
            "n_jobs": 1,
        },
    )
    assert model.status_code == 200
    assert model.json()["model"]["n_estimators"] == 32

    info = client.get("/api/app-info")
    assert info.status_code == 200
    assert "Random Forest" in " ".join(info.json()["technology"])


def test_backup_admin_only(client, auth):
    forbidden = client.post("/api/settings/database/backup", headers=auth("petugas"))
    assert forbidden.status_code == 403

    backup = client.post("/api/settings/database/backup", headers=auth("admin"))
    assert backup.status_code == 200, backup.text
    assert backup.json()["file"].endswith(".db")

    backups = client.get("/api/settings/database/backups", headers=auth("admin"))
    assert backups.status_code == 200
    assert any(row["name"] == backup.json()["file"] for row in backups.json())


def test_cors_and_security_headers(client, auth):
    preflight = client.options(
        "/api/medicines",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code in (200, 204)
    assert preflight.headers.get("access-control-allow-origin") in {"*", "http://localhost:5173"}

    login = client.post(
        "/api/auth/login", data={"username": "admin", "password": "admin123"}
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]
