"""Чтение аудита (ENTERPRISE Ф1). Просмотр — владелец проекта / свои действия."""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..permissions import is_dev_full_access, project_role, rank

router = APIRouter(tags=["audit"])


def _serialize(a: models.AuditLog) -> dict:
    return {
        "id": a.id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "request_id": a.request_id,
        "actor_type": a.actor_type,
        "actor_user_id": a.actor_user_id,
        "actor_key_id": a.actor_key_id,
        "on_behalf_of_user_id": a.on_behalf_of_user_id,
        "effective_user_id": a.effective_user_id,
        "project_id": a.project_id,
        "presentation_id": a.presentation_id,
        "slide_id": a.slide_id,
        "action": a.action,
        "method": a.method,
        "path": a.path,
        "status": a.status,
        "decision": a.decision,
        "deny_reason": a.deny_reason,
        "ip": a.ip,
        "ai_run_id": a.ai_run_id,
        "diff": a.diff,
        "meta": a.meta,
    }


@router.get("/projects/{project_id}/audit")
def project_audit(project_id: int, actor: Optional[int] = None, action: Optional[str] = None,
                  decision: Optional[str] = None,
                  since: Optional[datetime.datetime] = None,
                  limit: int = Query(100, le=500),
                  db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    """Аудит проекта. Читать может владелец (или супер-админ)."""
    if not is_dev_full_access():
        if not (user is not None and getattr(user, "is_superadmin", False)):
            if rank(project_role(db, project_id, user)) < rank("owner"):
                raise HTTPException(status_code=403, detail="Только владелец видит аудит проекта")
    q = db.query(models.AuditLog).filter(models.AuditLog.project_id == project_id)
    if actor is not None:
        q = q.filter(models.AuditLog.effective_user_id == actor)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if decision:
        q = q.filter(models.AuditLog.decision == decision)
    if since is not None:
        q = q.filter(models.AuditLog.created_at >= since)
    rows = q.order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    return [_serialize(a) for a in rows]


@router.get("/audit/me")
def my_audit(limit: int = Query(100, le=500),
             db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    rows = db.query(models.AuditLog).filter(
        (models.AuditLog.effective_user_id == user.id)
        | (models.AuditLog.actor_user_id == user.id)
    ).order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    return [_serialize(a) for a in rows]
