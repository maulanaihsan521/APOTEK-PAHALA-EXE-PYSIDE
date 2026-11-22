"""Pengelolaan application_settings (model, pengadaan, tampilan)."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_MODEL_SETTINGS, DEFAULT_PROCUREMENT_SETTINGS
from app.models.models import ApplicationSetting


def get_json(db: Session, key: str, default: dict[str, Any]) -> dict[str, Any]:
    row = db.scalar(select(ApplicationSetting).where(ApplicationSetting.key == key))
    if not row:
        return dict(default)
    try:
        value = json.loads(row.value)
        if isinstance(value, dict):
            return {**default, **value}
    except (ValueError, TypeError):
        pass
    return dict(default)


def set_json(db: Session, key: str, value: dict[str, Any]) -> None:
    row = db.scalar(select(ApplicationSetting).where(ApplicationSetting.key == key))
    payload = json.dumps(value, ensure_ascii=False)
    if row:
        row.value = payload
    else:
        db.add(ApplicationSetting(key=key, value=payload))


def get_model_config(db: Session) -> dict[str, Any]:
    return get_json(db, "model_settings", DEFAULT_MODEL_SETTINGS)


def set_model_config(db: Session, value: dict[str, Any]) -> None:
    set_json(db, "model_settings", value)


def get_procurement_config(db: Session) -> dict[str, Any]:
    return get_json(db, "procurement_settings", DEFAULT_PROCUREMENT_SETTINGS)


def set_procurement_config(db: Session, value: dict[str, Any]) -> None:
    set_json(db, "procurement_settings", value)


def get_display_config(db: Session) -> dict[str, Any]:
    return get_json(db, "display_settings", {
        "theme": "light",
        "font_scale": "normal",
        "chart_preference": "line",
    })
