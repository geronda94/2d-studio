"""Делегирования «бот от имени пользователя» (ENTERPRISE Ф3).

Согласие обязательно: delegation активируется только после approve субъектом.
"""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..permissions import enforce_write

router = APIRouter(tags=["delegations"], dependencies=[Depends(enforce_write)])


class DelegationIn(BaseModel):
    bot_user_id: int
    subject_user_id: Optional[int] = None
    subject_email: Optional[str] = None
    project_id: Optional[int] = None


def _ser(d: models.BotDelegation) -> dict:
    return {
        "id": d.id, "bot_user_id": d.bot_user_id, "subject_user_id": d.subject_user_id,
        "project_id": d.project_id,
        "approved": d.approved_at is not None,
        "revoked": d.revoked_at is not None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _require_user(user):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")


@router.post("/delegations")
def request_delegation(body: DelegationIn, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    """Запрос делегирования создаёт владелец бота (или супер-админ). Согласие — за subject."""
    _require_user(user)
    bot = db.query(models.User).filter(models.User.id == body.bot_user_id).first()
    if not bot or not getattr(bot, "is_bot", False):
        raise HTTPException(status_code=404, detail="Бот не найден")
    if not (user.is_superadmin or getattr(bot, "owner_user_id", None) == user.id):
        raise HTTPException(status_code=403, detail="Только владелец бота может запросить делегирование")
    if body.subject_user_id is not None:
        subj = db.query(models.User).filter(models.User.id == body.subject_user_id).first()
    elif body.subject_email:
        subj = db.query(models.User).filter(
            models.User.email == body.subject_email.strip().lower()).first()
    else:
        raise HTTPException(status_code=400, detail="Укажите subject_user_id или subject_email")
    if not subj or not subj.is_active:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    existing = db.query(models.BotDelegation).filter(
        models.BotDelegation.bot_user_id == bot.id,
        models.BotDelegation.subject_user_id == subj.id,
        models.BotDelegation.project_id == body.project_id,
        models.BotDelegation.revoked_at.is_(None)).first()
    if existing:
        return _ser(existing)
    d = models.BotDelegation(bot_user_id=bot.id, subject_user_id=subj.id, project_id=body.project_id)
    db.add(d)
    db.commit()
    return _ser(d)


@router.post("/delegations/{delegation_id}/approve")
def approve_delegation(delegation_id: int, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    _require_user(user)
    d = db.query(models.BotDelegation).filter(models.BotDelegation.id == delegation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Делегирование не найдено")
    if d.subject_user_id != user.id and not user.is_superadmin:
        raise HTTPException(status_code=403, detail="Одобрить может только сам пользователь")
    d.approved_at = datetime.datetime.utcnow()
    d.approved_by = user.id
    d.revoked_at = None
    db.commit()
    return _ser(d)


@router.post("/delegations/{delegation_id}/revoke")
def revoke_delegation(delegation_id: int, db: Session = Depends(get_db),
                      user: Optional[models.User] = Depends(get_current_user)):
    _require_user(user)
    d = db.query(models.BotDelegation).filter(models.BotDelegation.id == delegation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Делегирование не найдено")
    bot = db.query(models.User).filter(models.User.id == d.bot_user_id).first()
    allowed = user.is_superadmin or d.subject_user_id == user.id or \
        (bot is not None and getattr(bot, "owner_user_id", None) == user.id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    d.revoked_at = datetime.datetime.utcnow()
    db.commit()
    return _ser(d)


@router.get("/delegations/me")
def my_delegations(db: Session = Depends(get_db),
                   user: Optional[models.User] = Depends(get_current_user)):
    _require_user(user)
    bots = db.query(models.User.id).filter(models.User.owner_user_id == user.id).all()
    bot_ids = [b[0] for b in bots]
    q = db.query(models.BotDelegation).filter(
        (models.BotDelegation.subject_user_id == user.id)
        | (models.BotDelegation.bot_user_id.in_(bot_ids or [-1])))
    return [_ser(d) for d in q.all()]
