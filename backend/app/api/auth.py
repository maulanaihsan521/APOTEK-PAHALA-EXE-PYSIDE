"""Autentikasi, profil, dan perubahan password."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import PasswordChange, Token, UserOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.name if user.role else "",
        "is_active": user.is_active,
        "theme": user.theme,
        "font_scale": user.font_scale,
    }


@router.post("/login", response_model=Token, summary="Masuk ke aplikasi")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form_data.username.strip()))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nama pengguna atau password salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun Anda dinonaktifkan. Hubungi Admin.")
    from datetime import datetime
    user.last_login = datetime.utcnow()
    log_activity(db, user, "login", f"{user.full_name} masuk ke aplikasi.", "user", user.id)
    db.commit()
    token = create_access_token(user.username, user.role.name if user.role else "petugas")
    return {"access_token": token, "token_type": "bearer", "user": user_payload(user)}


@router.get("/me", response_model=UserOut, summary="Profil pengguna aktif")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)


@router.post("/change-password", summary="Ganti password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Password lama tidak sesuai.")
    if payload.old_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Password baru harus berbeda dari password lama.")
    user.password_hash = hash_password(payload.new_password)
    log_activity(db, user, "account", "Password akun diperbarui.", "user", user.id)
    db.commit()
    return {"message": "Password berhasil diperbarui."}


@router.post("/logout", summary="Keluar aplikasi")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_activity(db, user, "logout", f"{user.full_name} keluar dari aplikasi.", "user", user.id)
    db.commit()
    return {"message": "Berhasil keluar."}
