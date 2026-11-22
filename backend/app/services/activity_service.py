"""Pencatatan aktivitas dan notifikasi."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import ActivityLog, Notification, User


def log_activity(
    db: Session,
    user: User | None,
    activity_type: str,
    description: str,
    object_type: str | None = None,
    object_id: int | None = None,
) -> None:
    db.add(ActivityLog(
        user_id=user.id if user else None,
        activity_type=activity_type,
        description=description,
        object_type=object_type,
        object_id=object_id,
    ))


def notify(
    db: Session,
    category: str,
    title: str,
    message: str,
    level: str = "info",
    user_id: int | None = None,
) -> None:
    db.add(Notification(
        category=category,
        title=title,
        message=message,
        level=level,
        user_id=user_id,
    ))
