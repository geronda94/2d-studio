"""Администрирование пользователей (AUTH_PLAN Ф5). Только супер-админ.

Список/блокировка/выдача прав/сброс пароля. Защита от самоблокировки:
нельзя снять с себя супер-админа и деактивировать себя.
"""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .. import models
from ..auth import hash_password
from ..database import get_db
from ..permissions import enforce_write, require_superadmin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(enforce_write)],
)


def _public(u: models.User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "is_active": bool(u.is_active),
        "is_superadmin": bool(u.is_superadmin),
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


class UserUpdateIn(BaseModel):
    is_active: Optional[bool] = None
    is_superadmin: Optional[bool] = None


class ResetPasswordIn(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _np(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


@router.get("/users")
def list_users(db: Session = Depends(get_db),
               _admin: models.User = Depends(require_superadmin)):
    users = db.query(models.User).order_by(models.User.id).all()
    return [_public(u) for u in users]


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserUpdateIn, db: Session = Depends(get_db),
                admin: models.User = Depends(require_superadmin)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if u.id == admin.id:
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="Нельзя деактивировать себя")
        if body.is_superadmin is False:
            raise HTTPException(status_code=400, detail="Нельзя снять супер-админа с себя")
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.is_superadmin is not None:
        u.is_superadmin = body.is_superadmin
    db.commit()
    return _public(u)


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, body: ResetPasswordIn, db: Session = Depends(get_db),
                   _admin: models.User = Depends(require_superadmin)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    u.password_hash = hash_password(body.new_password)
    # отзываем все сессии пользователя
    for s in db.query(models.UserSession).filter(
            models.UserSession.user_id == u.id,
            models.UserSession.revoked_at.is_(None)).all():
        s.revoked_at = datetime.datetime.utcnow()
    db.commit()
    return {"ok": True, "user_id": u.id}
