"""API-ключи агента/пользователя (AI_PLATFORM Ф4).

Плейнтекст отдаётся ОДИН раз при создании; в БД только sha256-хэш.
При `AUTH_MODE=on` запросы с `Authorization: Bearer <key>` резолвят owner_id
(см. projects._current_owner).
"""
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
from ..auth import get_current_user, require_user
from ..database import get_db
from ..permissions import enforce_write
from .projects import _hash_api_key

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
    dependencies=[Depends(enforce_write)],
)


@router.post("/", response_model=dict)
def create_api_key(req: schemas.ApiKeyCreate, db: Session = Depends(get_db),
                   user: models.User = Depends(require_user)):
    """Создать ключ можно только для СЕБЯ. `kind=service` создаёт бот-аккаунт
    (владелец — текущий пользователь) и выдаёт ему ключ (ENTERPRISE Ф3)."""
    raw = "pk_" + secrets.token_hex(24)
    scopes = [s for s in (req.scopes or ["read", "write"]) if s in ("read", "write", "admin")]
    if "admin" in scopes and not getattr(user, "is_superadmin", False):
        scopes = [s for s in scopes if s != "admin"]

    kind = (req.kind or "personal").lower()
    if kind not in ("personal", "service"):
        raise HTTPException(status_code=400, detail="kind: personal | service")
    owner_id = user.id

    if kind == "service":
        # бот-аккаунт: без пароля, не логинится, владелец — человек
        bot = models.User(
            email=f"bot_{secrets.token_hex(8)}@service.local", password_hash="",
            display_name=(req.bot_name or req.label or "bot")[:80],
            is_bot=True, owner_user_id=user.id, is_active=True)
        db.add(bot)
        db.flush()
        owner_id = bot.id
        # project-scoped бот сразу получает editor-участие в проекте
        if req.project_id is not None:
            db.add(models.ProjectMember(project_id=req.project_id, user_id=bot.id,
                                        role="editor", invited_by=user.id))

    if req.project_id is not None:
        from ..permissions import project_role, rank
        if rank(project_role(db, req.project_id, user)) < rank("owner"):
            raise HTTPException(status_code=403, detail="Ключ на проект — только владелец проекта")

    row = models.ApiKey(
        key_hash=_hash_api_key(raw),
        owner_id=owner_id,
        label=req.label,
        scopes=scopes or ["read", "write"],
        is_active=True,
        kind=kind,
        created_by_user_id=user.id,
        project_id=req.project_id,
        can_delegate=bool(req.can_delegate) if kind == "service" else False,
        rate_limit=req.rate_limit,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    # плейнтекст показываем только сейчас
    return {"id": row.id, "key": raw, "owner_id": row.owner_id, "kind": row.kind,
            "bot_user_id": owner_id if kind == "service" else None,
            "can_delegate": bool(row.can_delegate), "project_id": row.project_id,
            "label": row.label, "scopes": row.scopes}


@router.get("/", response_model=List[schemas.ApiKeyOut])
def list_api_keys(db: Session = Depends(get_db),
                  user: models.User = Depends(require_user)):
    q = db.query(models.ApiKey)
    if not getattr(user, "is_superadmin", False):
        q = q.filter(models.ApiKey.owner_id == user.id)
    return q.order_by(models.ApiKey.id.desc()).all()


@router.delete("/{key_id}", response_model=dict)
def revoke_api_key(key_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(require_user)):
    q = db.query(models.ApiKey).filter(models.ApiKey.id == key_id)
    if not getattr(user, "is_superadmin", False):
        q = q.filter(models.ApiKey.owner_id == user.id)
    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.is_active = False
    db.commit()
    return {"status": "revoked", "id": key_id}


@router.get("/whoami")
def whoami(user: Optional[models.User] = Depends(get_current_user)):
    """Проверка авторизации: при AUTH_MODE=on вернёт пользователя по сессии/ключу."""
    return {"mode": os.environ.get("AUTH_MODE", "off").lower(),
            "owner_id": user.id if user else None}
