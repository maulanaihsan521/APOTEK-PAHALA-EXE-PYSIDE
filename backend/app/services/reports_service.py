"""Penyusunan data laporan (ringkasan, tabel, grafik, ekspor)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.service import latest_runs_by_medicine
from app.ml.trainer import MODEL_LABELS
from app.models.models import (
    Medicine, ModelEvaluation, ProcurementRecommendation, Sale, User, WeatherData,
)
from app.services.inventory_service import inventory_rows
from app.core.config import DATA_LABEL, DATA_SOURCE_NOTE

REPORT_TYPES = {
    "sales": "Laporan Penjualan",
    "demand": "Laporan Permintaan Obat",
    "prediction": "Laporan Prediksi",
    "model_evaluation": "Laporan Evaluasi Model",
    "stock": "Laporan Stok",
    "procurement": "Laporan Rekomendasi Pengadaan",
}


def _default_range(db: Session) -> tuple[date, date]:
    bounds = db.execute(select(func.min(Sale.sale_date), func.max(Sale.sale_date))).one()
    min_date, max_date = bounds
    if not min_date or not max_date:
        today = date.today()
        return today - timedelta(days=30), today
    return min_date, max_date


def _format_rupiah(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


def build_report(
    db: Session,
    report_type: str,
    start: date | None = None,
    end: date | None = None,
    user: User | None = None,
) -> dict[str, Any]:
    if report_type not in REPORT_TYPES:
        raise ValueError("Jenis laporan tidak dikenal.")
    default_start, default_end = _default_range(db)
    start = start or default_start
    end = end or default_end
    if start > end:
        raise ValueError("Tanggal awal tidak boleh melebihi tanggal akhir.")
    title = REPORT_TYPES[report_type]
    meta = {
        "Periode": f"{start:%d %b %Y} - {end:%d %b %Y}",
        "Label data": DATA_LABEL,
        "Dibuat oleh": user.full_name if user else "Sistem",
    }
    columns: list[str] = []
    rows: list[list[Any]] = []
    summary: list[tuple[str, str]] = []
    chart: list[tuple[str, float]] = []
    notes = ""

    if report_type == "sales":
        data = db.execute(
            select(Medicine.name, Medicine.unit,
                   func.sum(Sale.quantity), func.sum(Sale.total_price), func.count(Sale.id))
            .join(Sale, Sale.medicine_id == Medicine.id)
            .where(Sale.sale_date.between(start, end))
            .group_by(Medicine.id)
            .order_by(func.sum(Sale.total_price).desc())
        ).all()
        total_qty = sum(row[2] or 0 for row in data)
        total_revenue = sum(row[3] or 0 for row in data)
        transactions = sum(row[4] or 0 for row in data)
        summary = [
            ("Estimasi nilai permintaan", _format_rupiah(total_revenue)),
            ("Total kuantitas", f"{int(total_qty):,} unit".replace(",", ".")),
            ("Baris data mingguan", f"{transactions:,}".replace(",", ".")),
            ("Jumlah obat", f"{len(data)} jenis"),
            ("Rata-rata per baris", _format_rupiah(total_revenue / transactions) if transactions else "-"),
        ]
        columns = ["Nama Obat", "Satuan", "Kuantitas", "Estimasi Nilai", "Baris Data"]
        rows = [[name, unit, int(qty or 0), _format_rupiah(float(revenue or 0)), int(count or 0)]
                for name, unit, qty, revenue, count in data]
        chart = [(name, float(revenue or 0)) for name, _u, _q, revenue, _c in data[:7]]
        notes = (
            "Laporan disusun dari data permintaan yang tercatat pada database. "
            + DATA_SOURCE_NOTE
        )

    elif report_type == "demand":
        data = db.execute(
            select(Medicine.name, func.sum(Sale.quantity), func.count(func.distinct(
                (func.strftime("%Y-%W", Sale.sale_date))
            )))
            .join(Sale, Sale.medicine_id == Medicine.id)
            .where(Sale.sale_date.between(start, end))
            .group_by(Medicine.id)
            .order_by(func.sum(Sale.quantity).desc())
        ).all()
        total = sum(row[1] or 0 for row in data)
        weeks = ((end - start).days + 1) / 7
        summary = [
            ("Total permintaan", f"{int(total):,} unit".replace(",", ".")),
            ("Rata-rata per pekan", f"{total / max(weeks, 1):,.0f} unit".replace(",", ".")),
            ("Jumlah obat", f"{len(data)} jenis"),
            ("Rentang", f"{start:%d %b %Y} - {end:%d %b %Y}"),
        ]
        columns = ["Nama Obat", "Total Permintaan", "Rata-rata per Pekan", "Pekan Aktif"]
        rows = [[name, int(qty or 0), round(float(qty or 0) / max(weeks, 1), 1), int(active or 0)]
                for name, qty, active in data]
        chart = [(name, float(qty or 0)) for name, qty, _a in data[:7]]
        notes = DATA_SOURCE_NOTE + " Nilai rupiah dihitung dari harga jual terakhir pada master obat."

    elif report_type == "prediction":
        latest = latest_runs_by_medicine(db)
        evaluations = {
            (ev.medicine_id, ev.model_name): ev
            for ev in db.scalars(select(ModelEvaluation)).all()
        }
        data = []
        total_forecast = 0.0
        for medicine in db.scalars(select(Medicine).where(Medicine.is_active.is_(True)).order_by(Medicine.name)).all():
            run = latest.get(medicine.id)
            if not run:
                continue
            forecast = sum(item.predicted_value for item in run.results if item.kind == "forecast" and item.week_number <= 4)
            total_forecast += forecast
            metrics = evaluations.get((medicine.id, run.model_name))
            data.append([medicine.name, MODEL_LABELS.get(run.model_name, run.model_name), round(forecast),
                         metrics.mae if metrics else "-", metrics.rmse if metrics else "-",
                         metrics.wape if metrics else "-", metrics.mape if metrics else "-"])
        wapes = [row[5] for row in data if isinstance(row[5], (int, float))]
        model_counts: dict[str, int] = {}
        for medicine in db.scalars(select(Medicine).where(Medicine.is_active.is_(True))).all():
            run = latest.get(medicine.id)
            if run:
                model_counts[run.model_name] = model_counts.get(run.model_name, 0) + 1
        selected_models = ", ".join(
            f"{MODEL_LABELS.get(name, name)} ({count})"
            for name, count in sorted(model_counts.items(), key=lambda item: -item[1])
        ) or "-"
        summary = [
            ("Total prakiraan 4 pekan", f"{total_forecast:,.0f} unit".replace(",", ".")),
            ("Obat diprediksi", f"{len(data)} jenis"),
            ("Rata-rata WAPE", f"{sum(wapes) / len(wapes):.2f}%" if wapes else "-"),
            ("Model terpilih", f"Otomatis per obat · {selected_models}"),
        ]
        columns = ["Nama Obat", "Model", "Prakiraan 4 Pekan", "MAE", "RMSE", "WAPE (%)", "MAPE (%)"]
        rows = data
        chart = [(row[0], row[2]) for row in data[:7]]
        notes = ("Prakiraan merupakan estimasi model, bukan kepastian. WAPE dipakai sebagai ukuran kesalahan "
                 "utama karena lebih stabil saat permintaan mingguan rendah. MAPE dihitung pada data uji "
                 "kronologis; nilai aktual nol tidak diikutkan dalam perhitungan persentase.")

    elif report_type == "model_evaluation":
        data = db.execute(
            select(Medicine.name, ModelEvaluation.model_name, ModelEvaluation.mae,
                   ModelEvaluation.rmse, ModelEvaluation.wape, ModelEvaluation.mape,
                   ModelEvaluation.test_size)
            .join(Medicine, Medicine.id == ModelEvaluation.medicine_id)
            .order_by(Medicine.name, ModelEvaluation.model_name)
        ).all()
        averages = db.execute(
            select(ModelEvaluation.model_name, func.avg(ModelEvaluation.mae),
                   func.avg(ModelEvaluation.rmse), func.avg(ModelEvaluation.wape),
                   func.avg(ModelEvaluation.mape))
            .group_by(ModelEvaluation.model_name)
        ).all()
        summary = [
            (MODEL_LABELS.get(name, name),
             f"MAE {mae:.2f} | RMSE {rmse:.2f} | WAPE {wape:.2f}% | MAPE {mape:.2f}%")
            for name, mae, rmse, wape, mape in averages
        ]
        summary.append(("Catatan", "Data uji dipisahkan kronologis; tidak ada pengacakan."))
        columns = ["Nama Obat", "Model", "MAE", "RMSE", "WAPE (%)", "MAPE (%)", "Data Uji"]
        rows = [[name, MODEL_LABELS.get(model, model), mae, rmse, wape, mape, test_size]
                for name, model, mae, rmse, wape, mape, test_size in data]
        chart = [(MODEL_LABELS.get(name, name)[:16], float(wape or 0))
                 for name, _mae, _rmse, wape, _mape in averages]
        notes = ("WAPE lebih rendah menunjukkan total kesalahan lebih kecil dibanding total permintaan. "
                 "MAPE dilaporkan sebagai pembanding; pekan dengan nilai aktual nol tidak diikutkan.")

    elif report_type == "stock":
        rows_data = inventory_rows(db)
        summary = [
            ("Jumlah obat", f"{len(rows_data)} jenis"),
            ("Total stok fisik", f"{sum(r['physical_stock'] for r in rows_data):,} unit".replace(",", ".")),
            ("Stok aman", f"{sum(1 for r in rows_data if r['status'] == 'aman')} obat"),
            ("Perlu perhatian", f"{sum(1 for r in rows_data if r['status'] == 'perlu_perhatian')} obat"),
            ("Kritis", f"{sum(1 for r in rows_data if r['status'] == 'kritis')} obat"),
        ]
        columns = ["Kode", "Nama Obat", "Stok Sistem", "Stok Fisik", "Selisih",
                   "Minimum", "Status", "Tanggal Opname"]
        rows = [[r["code"], r["name"], r["system_stock"], r["physical_stock"], r["difference"],
                 r["min_stock"], r["status"].replace("_", " ").title(), r["last_opname_date"] or "-"]
                for r in rows_data]
        chart = [(r["name"], float(r["physical_stock"])) for r in rows_data[:7]]
        notes = ("Stok bersumber dari stock opname terakhir. Tanggal opname ditampilkan agar posisi stok "
                 "tidak dibaca sebagai kondisi harian terkini.")

    elif report_type == "procurement":
        recommendation = db.scalar(
            select(ProcurementRecommendation).order_by(
                ProcurementRecommendation.created_at.desc()).limit(1)
        )
        if not recommendation:
            summary = [("Status", "Belum ada rekomendasi pengadaan")]
            columns = ["Nama Obat", "Stok", "Prediksi", "Saran", "Final", "Urgensi"]
            notes = "Buat rekomendasi terlebih dahulu melalui menu Rekomendasi Pengadaan."
        else:
            items = recommendation.items
            summary = [
                ("Kode rekomendasi", recommendation.code),
                ("Status", recommendation.status.title()),
                ("Periode", f"{recommendation.period_weeks} pekan"),
                ("Jumlah item", f"{len(items)} obat"),
                ("Total perkiraan", _format_rupiah(recommendation.total_estimated_cost)),
            ]
            columns = ["Nama Obat", "Stok Saat Ini", "Prediksi Kebutuhan", "Stok Pengaman",
                       "Rekomendasi", "Jumlah Final", "Urgensi"]
            rows = [[item.medicine.name if item.medicine else "-", item.current_stock,
                     round(item.predicted_demand), item.safety_stock, item.recommended_qty,
                     item.final_qty, item.urgency.title()] for item in items]
            chart = [(item.medicine.name if item.medicine else "-", float(item.final_qty))
                     for item in items[:7]]
            notes = ("Rekomendasi dihitung dari prakiraan permintaan, stok fisik, stok pengaman, dan lead time. "
                     "Angka adalah usulan yang perlu ditinjau manajemen.")

    return {
        "type": report_type,
        "title": title,
        "meta": meta,
        "summary": summary,
        "columns": columns,
        "rows": rows,
        "chart": chart,
        "notes": notes,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def report_dataframe(report: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(report["rows"], columns=report["columns"])
