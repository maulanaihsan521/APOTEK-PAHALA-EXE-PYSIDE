"""Endpoint Ringkasan Dashboard."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.models import User
from app.services.dashboard_service import dashboard_overview

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", summary="Ringkasan dashboard terpadu")
def overview(
    weeks: int = Query(default=4, ge=1, le=52),
    start: date | None = None,
    end: date | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dashboard_overview(db, weeks=weeks, start=start, end=end)
