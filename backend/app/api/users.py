"""Pengelolaan akun pengguna (khusus Admin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import user_payload
from app.core.deps import require_admin
from app.core.security import hash_password
from app.database.database import get_db
from app.models.models import Role, User
from app.schemas.schemas import UserCreate, UserUpdate
from app.services.activity_service import log_activity

router = APIRouter(prefix="/users", tags=["Pengguna"])


@router.get("", summary="Daftar akun")
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.full_name)).all()
    return [user_payload(user) for user in users]


@router.post("", status_code=201, summary="Tambah akun")
def create_user(payload: UserCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="Nama pengguna sudah digunakan.")
    role = db.scalar(select(Role).where(Role.name == payload.role))
    if not role:
        raise HTTPException(status_code=400, detail="Role tidak valid.")
    user = User(
        username=payload.username.strip(),
        full_name=payload.full_name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    log_activity(db, admin, "user", f"Akun {user.username} dibuat.", "user", None)
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.put("/{user_id}", summary="Ubah akun")
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan.")
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Anda tidak dapat menonaktifkan akun sendiri.")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        role = db.scalar(select(Role).where(Role.name == payload.role))
        if not role:
            raise HTTPException(status_code=400, detail="Role tidak valid.")
        user.role_id = role.id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    log_activity(db, admin, "user", f"Akun {user.username} diperbarui.", "user", user.id)
    db.commit()
    return user_payload(user)


@router.delete("/{user_id}", summary="Nonaktifkan akun")
def deactivate_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Anda tidak dapat menonaktifkan akun sendiri.")
    user.is_active = False
    log_activity(db, admin, "user", f"Akun {user.username} dinonaktifkan.", "user", user.id)
    db.commit()
    return {"message": "Akun berhasil dinonaktifkan."}
