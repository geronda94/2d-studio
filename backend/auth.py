"""Аутентификация и авторизация (AUTH_PLAN).

Ф1: пароли (scrypt, stdlib), сессии в БД (только sha256 токена), cookie + CSRF,
резолвер текущего пользователя. Ф2+ сюда добавятся зависимости ролей проекта.

Cookie:
  sid  — httpOnly, SameSite=Lax, Secure (env COOKIE_SECURE), сессионный токен.
  csrf — читаемая JS, для double-submit CSRF на мутациях.
"""
from __future__ import annotations

import datetime
import hashlib
import hmac
import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from . import models
from .database import get_db

SESSION_TTL_DAYS = int(os.environ.get("SESSION_TTL_DAYS", "30"))
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
AUTH_MODE = os.environ.get("AUTH_MODE", "off").lower()

_SID_COOKIE = "sid"
_CSRF_COOKIE = "csrf"

# --- scrypt params (OWASP-light, ~16MB) ---
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_DKLEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored:
        return False
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode("utf-8"), salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(hash_hex)),
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def create_session(db: Session, user: models.User, request: Request,
                   response: Response) -> models.UserSession:
    raw = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    sess = models.UserSession(
        user_id=user.id,
        token_hash=_hash_token(raw),
        csrf_token=csrf,
        expires_at=_now() + datetime.timedelta(days=SESSION_TTL_DAYS),
        user_agent=(request.headers.get("user-agent") or "")[:256],
        ip=(request.client.host if request.client else None),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    _set_cookies(response, raw, csrf)
    return sess


def _set_cookies(response: Response, raw: str, csrf: str) -> None:
    max_age = SESSION_TTL_DAYS * 24 * 3600
    response.set_cookie(
        _SID_COOKIE, raw, max_age=max_age, httponly=True,
        samesite="lax", secure=COOKIE_SECURE, path="/",
    )
    # csrf читается JS (double-submit). httpOnly=False намеренно.
    response.set_cookie(
        _CSRF_COOKIE, csrf, max_age=max_age, httponly=False,
        samesite="lax", secure=COOKIE_SECURE, path="/",
    )


def clear_cookies(response: Response) -> None:
    response.delete_cookie(_SID_COOKIE, path="/")
    response.delete_cookie(_CSRF_COOKIE, path="/")


def _session_from_request(request: Request, db: Session) -> Optional[models.UserSession]:
    raw = request.cookies.get(_SID_COOKIE)
    if not raw:
        return None
    sess = db.query(models.UserSession).filter(
        models.UserSession.token_hash == _hash_token(raw),
        models.UserSession.revoked_at.is_(None),
    ).first()
    if not sess or sess.expires_at < _now():
        return None
    return sess


def resolve_auth(db: Session, request: Request):
    """Возвращает (user, api_key|None). Cookie-сессия, иначе Bearer API-ключ."""
    sess = _session_from_request(request, db)
    if sess:
        user = db.query(models.User).filter(models.User.id == sess.user_id).first()
        if user and user.is_active:
            return user, None
        return None, None

    authz = request.headers.get("authorization")
    if authz and authz.lower().startswith("bearer "):
        raw = authz.split(" ", 1)[1].strip()
        key = db.query(models.ApiKey).filter(
            models.ApiKey.key_hash == _hash_token(raw),
            models.ApiKey.is_active.is_(True),
        ).first()
        if key and key.owner_id:
            u = db.query(models.User).filter(models.User.id == key.owner_id).first()
            # заблокированный пользователь не должен ходить даже по API-ключу
            if u and u.is_active:
                return u, key
    return None, None


def resolve_current_user(db: Session, request: Request) -> Optional[models.User]:
    return resolve_auth(db, request)[0]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    return resolve_current_user(db, request)


def require_user(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def verify_csrf(request: Request, db: Session = Depends(get_db)) -> None:
    """Double-submit CSRF: заголовок X-CSRF-Token должен совпасть с csrf сессии.
    Вызывать на мутациях cookie-сессией. Bearer-запросы (без cookie) не требуют CSRF."""
    sess = _session_from_request(request, db)
    if sess is None:
        return  # нет cookie-сессии — нечего защищать (Bearer/аноним)
    header = request.headers.get("x-csrf-token") or ""
    if not hmac.compare_digest(header, sess.csrf_token or ""):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
