"""Aplikasi FastAPI Apotek Pahala - Pharmacy Intelligence."""
from __future__ import annotations

import logging
import mimetypes
import socket
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.api import (
    activity,
    auth,
    dashboard,
    imports,
    inventory,
    medicines,
    predictions,
    procurement,
    reports,
    sales,
    settings as settings_api,
    users,
    weather,
)
from app.api.settings import app_info
from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, CORS_ORIGINS, ROOT_DIR
from app.database.database import Base, SessionLocal, engine
from app.models.models import Medicine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("apotek")

WEB_DIST = ROOT_DIR / "mobile-web" / "dist"

# Windows reads .js from the registry as text/plain, which breaks ES module loading.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("application/json", ".json")


def _lan_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        value = sock.getsockname()[0]
        sock.close()
        return value
    except OSError:
        return "127.0.0.1"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database.database import ensure_schema
    ensure_schema()
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Medicine)) or 0
    if count == 0:
        logger.info("Database kosong. Menyiapkan data aktual Apotek Pahala dan melatih model ...")
        from app.seed.real_data import seed_from_export
        try:
            seed_from_export(reset=False, train=True)
            logger.info("Data aktual siap.")
        except Exception:
            logger.exception(
                "Gagal menyiapkan data aktual. Pastikan folder datasets/real tersedia. "
                "Database dibiarkan kosong agar tidak menampilkan data demonstrasi."
            )
    logger.info("Apotek Pahala API berjalan di http://127.0.0.1:8000 (LAN: http://%s:8000)", _lan_ip())
    yield


app = FastAPI(
    title="Apotek Pahala - Pharmacy Intelligence API",
    description=(
        "API sistem informasi dan analitik persediaan obat Apotek Pahala. "
        "Mendukung dashboard desktop dan mobile web dengan database yang sama."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
for router in (
    auth.router,
    users.router,
    dashboard.router,
    medicines.router,
    sales.router,
    weather.router,
    inventory.router,
    predictions.router,
    procurement.router,
    reports.router,
    settings_api.router,
    imports.router,
    activity.router,
):
    app.include_router(router, prefix=API_PREFIX)


@app.get("/api/health", tags=["Sistem"], summary="Status layanan")
@app.get("/health", include_in_schema=False)
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            medicines_count = db.scalar(select(func.count()).select_from(Medicine)) or 0
        return {
            "status": "ok",
            "app": APP_NAME,
            "version": APP_VERSION,
            "database": "connected",
            "medicines": medicines_count,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Health check gagal")
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(exc)})


@app.get("/api/app-info", tags=["Sistem"], summary="Informasi aplikasi")
def public_app_info():
    return app_info()


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request: Request, exc: IntegrityError):
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "Data yang Anda kirim bertentangan dengan data yang sudah ada."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception):
    logger.exception("Kesalahan tidak tertangani")
    return JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan pada server. Silakan coba lagi atau hubungi Admin."},
    )


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
else:
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def landing():
        return f"""
        <html lang="id"><head><meta charset="utf-8"><title>{APP_NAME}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body {{ margin:0; font-family:'Segoe UI',sans-serif; background:#F5F8FA; color:#18343D;
               display:flex; align-items:center; justify-content:center; min-height:100vh; }}
        .card {{ background:#fff; border:1px solid #E3EBEF; border-radius:18px; padding:40px 44px;
                 max-width:560px; box-shadow:0 12px 40px rgba(11,95,82,.08); }}
        h1 {{ margin:0; color:#0B5F52; }} p {{ color:#718096; line-height:1.6; }}
        a {{ display:inline-block; margin-top:8px; padding:11px 20px; background:#087F6B; color:#fff;
             text-decoration:none; border-radius:10px; font-weight:600; }}
        .muted {{ font-size:12px; color:#718096; margin-top:20px; }}
        </style></head><body><div class="card">
        <h1>{APP_NAME}</h1><p style="margin-top:2px;color:#087F6B;font-weight:600;">{APP_SUBTITLE}</p>
        <p>Backend API berjalan. Antarmuka mobile web belum dibangun.<br>
        Jalankan <code>npm install</code> dan <code>npm run build</code> pada folder
        <code>mobile-web</code>, lalu muat ulang halaman ini.</p>
        <a href="/api/docs">Buka Dokumentasi API</a>
        <div class="muted">Versi {APP_VERSION} - Data aktual Apotek Pahala.</div>
        </div></body></html>
        """
