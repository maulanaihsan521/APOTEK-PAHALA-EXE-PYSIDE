"""Pembantu format angka, tanggal, dan label bahasa Indonesia."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from PySide6.QtCore import QDate

from app.core.config import MONTHS_ID, MONTHS_ID_LONG

DASH = "—"


def _to_local(value: datetime) -> datetime:
    """Timestamp API tanpa zona dianggap UTC, lalu ditampilkan di zona lokal."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone()


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _to_local(value).date()
    if isinstance(value, date):
        return value
    if isinstance(value, QDate):
        return date(value.year(), value.month(), value.day()) if value.isValid() else None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        # String tanggal murni tidak dikonversi; timestamp UTC menjadi tanggal lokal.
        return _to_local(parsed).date() if ("T" in text or " " in text) else parsed.date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _as_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _to_local(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    try:
        return _to_local(datetime.fromisoformat(text.replace("Z", "+00:00")))
    except ValueError:
        parsed = _as_date(text)
        return datetime(parsed.year, parsed.month, parsed.day) if parsed else None


def number(value: Any, decimals: int = 0) -> str:
    if value is None:
        return DASH
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals <= 0:
        return f"{numeric:,.0f}".replace(",", ".")
    return f"{numeric:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rupiah(value: Any, decimals: int = 0) -> str:
    if value is None:
        return DASH
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"Rp {number(numeric, decimals)}"


def compact_rupiah(value: Any) -> str:
    if value is None:
        return DASH
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if numeric < 0 else ""
    numeric = abs(numeric)
    if numeric >= 1_000_000_000_000:
        return f"{sign}Rp {number(numeric / 1_000_000_000_000, 1)} T"
    if numeric >= 1_000_000_000:
        return f"{sign}Rp {number(numeric / 1_000_000_000, 1)} M"
    if numeric >= 1_000_000:
        return f"{sign}Rp {number(numeric / 1_000_000, 1)} jt"
    if numeric >= 1_000:
        return f"{sign}Rp {number(numeric / 1_000, 0)} rb"
    return f"{sign}Rp {number(numeric, 0)}"


def percent(value: Any, decimals: int = 1, signed: bool = False) -> str:
    if value is None:
        return DASH
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    prefix = "+" if signed and numeric > 0 else ""
    return f"{prefix}{number(numeric, decimals)}%"


def format_date(value: Any, with_year: bool = True) -> str:
    parsed = _as_date(value)
    if not parsed:
        return DASH
    text = f"{parsed.day:02d} {MONTHS_ID[parsed.month]}"
    return f"{text} {parsed.year}" if with_year else text


def format_date_long(value: Any) -> str:
    parsed = _as_date(value)
    if not parsed:
        return DASH
    return f"{parsed.day:02d} {MONTHS_ID_LONG[parsed.month]} {parsed.year}"


def format_datetime(value: Any) -> str:
    parsed = _as_datetime(value)
    if not parsed:
        return DASH
    return f"{format_date(parsed)} · {parsed.strftime('%H:%M')}"


def format_time(value: Any) -> str:
    parsed = _as_datetime(value)
    return parsed.strftime("%H:%M") if parsed else DASH


def relative_time(value: Any) -> str:
    parsed = _as_datetime(value)
    if not parsed:
        return DASH
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    delta = now - parsed
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "baru saja"
    if seconds < 3600:
        return f"{seconds // 60} menit lalu"
    if seconds < 86_400:
        return f"{seconds // 3600} jam lalu"
    if seconds < 604_800:
        return f"{seconds // 86_400} hari lalu"
    return format_date(parsed)


def today() -> date:
    return date.today()


def today_iso() -> str:
    return date.today().isoformat()


def month_start_iso() -> str:
    current = date.today()
    return current.replace(day=1).isoformat()


def days_ago_iso(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def to_qdate(value: Any) -> QDate:
    parsed = _as_date(value) or date.today()
    return QDate(parsed.year, parsed.month, parsed.day)


def from_qdate(value: QDate) -> str:
    return value.toString("yyyy-MM-dd") if value.isValid() else today_iso()


def initials(name: str | None) -> str:
    if not name:
        return "AP"
    parts = [item for item in name.replace("-", " ").split() if item]
    if not parts:
        return "AP"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def status_label(status: str | None) -> str:
    return {
        "aman": "Aman",
        "perlu_perhatian": "Perlu perhatian",
        "kritis": "Kritis",
    }.get(status or "", status or DASH)


def urgency_label(value: str | None) -> str:
    return {"kritis": "Kritis", "tinggi": "Tinggi", "sedang": "Sedang", "rendah": "Rendah"}.get(
        value or "", value or DASH
    )


def activity_label(activity_type: str | None) -> str:
    return {
        "sale": "Penjualan",
        "stock": "Stok",
        "prediction": "Prediksi",
        "training": "Pelatihan",
        "procurement": "Pengadaan",
        "login": "Akun",
        "logout": "Akun",
        "import": "Import",
        "backup": "Database",
        "medicine": "Obat",
        "settings": "Pengaturan",
        "weather": "Cuaca",
        "account": "Akun",
    }.get(activity_type or "", (activity_type or "Sistem").replace("_", " ").title())


def change_type_label(value: str | None) -> str:
    return {
        "opname": "Stock opname",
        "penambahan": "Penambahan",
        "pengurangan": "Pengurangan",
        "koreksi": "Koreksi",
        "import": "Import",
    }.get(value or "", (value or DASH).replace("_", " ").title())


def source_label(value: str | None) -> str:
    mapping = {
        "manual": "Manual",
        "import": "Import",
        "import berkas": "Import",
        "opname": "Stok opname",
        "stok_opname": "Stok opname",
        "stock_opname": "Stok opname",
    }
    key = str(value or "").strip().lower()
    if key in mapping:
        return mapping[key]
    return (str(value or DASH).replace("_", " ").title()).strip() or DASH


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 11:
        return "Selamat pagi"
    if hour < 15:
        return "Selamat siang"
    if hour < 19:
        return "Selamat sore"
    return "Selamat malam"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def dict_get(payload: dict, *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def truncate(text: str, length: int = 42) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"
