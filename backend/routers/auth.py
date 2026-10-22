"""Аутентификация: регистрация, логин, логаут, текущий пользователь (AUTH_PLAN Ф1).

Cookie-сессия + CSRF (см. backend/auth.py). Открытая регистрация с rate-limit.
"""
from __future__ import annotations

import datetime
import os
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .. import models
from ..auth import (
    AUTH_MODE,
    _session_from_request,
    clear_cookies,
    create_session,
    get_current_user,
    hash_password,
    require_user,
    verify_csrf,
    verify_password,
)
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Примитивный rate-limit (in-memory). Позже — Redis. ---
_ATTEMPTS: dict = defaultdict(deque)
_RATE_LIMIT = int(os.environ.get("AUTH_RATE_LIMIT", "12"))
_RATE_WINDOW = 60.0


def _rate_limit(key: str) -> None:
    now = time.monotonic()
    dq = _ATTEMPTS[key]
    while dq and now - dq[0] > _RATE_WINDOW:
        dq.popleft()
    if len(dq) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Слишком много попыток, попробуйте позже")
    dq.append(now)


class RegisterIn(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "@" not in v or len(v) < 5:
            raise ValueError("Некорректный email")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


def _public_user(u: models.User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "is_superadmin": bool(u.is_superadmin),
    }


@router.post("/register")
def register(body: RegisterIn, request: Request, response: Response,
             db: Session = Depends(get_db)):
    _rate_limit(f"reg:{request.client.host if request.client else '?'}")
    exists = db.query(models.User).filter(models.User.email == body.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email уже зарегистрирован")
    user = models.User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=(body.display_name or body.email.split("@")[0])[:80],
    )
    # Супер-админ НЕ назначается автоматически (публичная открытая регистрация).
    # Админ создаётся bootstrap-ом из env ADMIN_EMAIL/ADMIN_PASSWORD (см. main.py).
    db.add(user)
    db.commit()
    db.refresh(user)
    create_session(db, user, request, response)
    return {"user": _public_user(user), "mode": AUTH_MODE}


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response,
          db: Session = Depends(get_db)):
    email = (body.email or "").strip().lower()
    _rate_limit(f"login:{request.client.host if request.client else '?'}:{email}")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    user.last_login_at = datetime.datetime.utcnow()
    db.commit()
    create_session(db, user, request, response)
    return {"user": _public_user(user), "mode": AUTH_MODE}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db),
           _csrf: None = Depends(verify_csrf)):
    sess = _session_from_request(request, db)
    if sess:
        sess.revoked_at = datetime.datetime.utcnow()
        db.commit()
    clear_cookies(response)
    return {"ok": True}


@router.get("/me")
def me(user: Optional[models.User] = Depends(get_current_user)):
    return {"user": _public_user(user) if user else None, "mode": AUTH_MODE}


class PasswordIn(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _np(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


@router.post("/password")
def change_password(body: PasswordIn, request: Request,
                    db: Session = Depends(get_db),
                    _csrf: None = Depends(verify_csrf),
                    user: models.User = Depends(require_user)):
    """Смена пароля. Все прочие сессии отзываются, текущая остаётся."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный текущий пароль")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    sess = _session_from_request(request, db)
    keep_id = sess.id if sess else -1
    for s in db.query(models.UserSession).filter(
            models.UserSession.user_id == user.id,
            models.UserSession.id != keep_id,
            models.UserSession.revoked_at.is_(None)).all():
        s.revoked_at = datetime.datetime.utcnow()
    db.commit()
    return {"ok": True}
