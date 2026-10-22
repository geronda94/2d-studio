"""Серверные прогоны ИИ (ENTERPRISE Ф3): неподделываемый провенанс.

Клиент не может придумать ai_run_id — он выдаётся сервером и валидируется в
enforce_write (run↔bot↔project↔status). Мутации агента несут X-AI-Run-Id.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..permissions import (
    enforce_write, idempotency_guard, is_dev_full_access, project_role, rank,
    resolve_api_key, resolve_effective_user,
)

router = APIRouter(tags=["ai-runs"], dependencies=[Depends(enforce_write)])


class AiRunIn(BaseModel):
    project_id: int
    agent: Optional[str] = None
    model: Optional[str] = None
    base_version: Optional[int] = None


class AiRunFinishIn(BaseModel):
    status: str = "finished"  # finished | failed


def _ser(r: models.AiRun) -> dict:
    return {"run_id": r.run_id, "project_id": r.project_id, "agent": r.agent,
            "model": r.model, "base_version": r.base_version, "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None}


@router.post("/ai/runs", dependencies=[Depends(idempotency_guard)])
def create_ai_run(body: AiRunIn, request: Request, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    if not is_dev_full_access():
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Права проверяем у ЭФФЕКТИВНОГО субъекта (бот с on-behalf = человек),
        # иначе делегирование не могло бы создать ИИ-прогон.
        key = resolve_api_key(db, request)
        effective, _on_behalf, _atype, err, _deleg = resolve_effective_user(db, request, key, user)
        if err:
            raise HTTPException(status_code=403, detail=err)
        if rank(project_role(db, body.project_id, effective)) < rank("editor"):
            raise HTTPException(status_code=403, detail="Недостаточно прав на проект")
    run = models.AiRun(
        run_id=uuid.uuid4().hex, bot_user_id=getattr(user, "id", None), project_id=body.project_id,
        agent=body.agent, model=body.model, base_version=body.base_version, status="running")
    db.add(run)
    db.commit()
    return _ser(run)


@router.post("/ai/runs/{run_id}/finish")
def finish_ai_run(run_id: str, body: AiRunFinishIn, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    run = db.query(models.AiRun).filter(models.AiRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not (user is not None and (user.is_superadmin or run.bot_user_id == user.id)):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    run.status = body.status if body.status in ("finished", "failed") else "finished"
    import datetime
    run.finished_at = datetime.datetime.utcnow()
    db.commit()
    return _ser(run)


@router.get("/ai/runs/{run_id}")
def get_ai_run(run_id: str, db: Session = Depends(get_db),
               user: Optional[models.User] = Depends(get_current_user)):
    run = db.query(models.AiRun).filter(models.AiRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _ser(run)
