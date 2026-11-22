"""Aktivitas dan pusat notifikasi."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.models import ActivityLog, Notification, User

router = APIRouter(tags=["Aktivitas"])


@router.get("/activities", summary="Riwayat aktivitas")
def activities(
    activity_type: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(ActivityLog, User).join(User, User.id == ActivityLog.user_id, isouter=True)
    if activity_type:
        query = query.where(ActivityLog.activity_type == activity_type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [{
            "id": log.id,
            "type": log.activity_type,
            "description": log.description,
            "object_type": log.object_type,
            "object_id": log.object_id,
            "user": user.full_name if user else "Sistem",
            "created_at": log.created_at.isoformat(),
        } for log, user in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/notifications", summary="Daftar notifikasi")
def notifications(
    unread_only: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Notification)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    rows = db.scalars(query.order_by(Notification.created_at.desc()).limit(limit)).all()
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.is_read.is_(False))
    ) or 0
    return {
        "unread": unread,
        "items": [{
            "id": row.id,
            "category": row.category,
            "title": row.title,
            "message": row.message,
            "level": row.level,
            "is_read": row.is_read,
            "created_at": row.created_at.isoformat(),
        } for row in rows],
    }


@router.post("/notifications/{notification_id}/read", summary="Tandai notifikasi dibaca")
def mark_read(notification_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(Notification, notification_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan.")
    row.is_read = True
    db.commit()
    return {"message": "Notifikasi ditandai dibaca."}


@router.post("/notifications/read-all", summary="Tandai semua dibaca")
def mark_all(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        update(Notification).where(Notification.is_read.is_(False)).values(is_read=True)
    )
    db.commit()
    return {"message": "Semua notifikasi ditandai dibaca."}
