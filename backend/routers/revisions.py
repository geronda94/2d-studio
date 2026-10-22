"""Версии проекта (ENTERPRISE Ф2): список, diff, checkpoint, restore."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models, revisions
from ..auth import get_current_user
from ..database import get_db
from ..permissions import is_dev_full_access, project_role, rank

router = APIRouter(tags=["revisions"])


class CheckpointIn(BaseModel):
    label: Optional[str] = None


class RestoreIn(BaseModel):
    dry_run: bool = True


def _rev_meta(r: models.ProjectRevision) -> dict:
    return {
        "n": r.n, "created_at": r.created_at.isoformat() if r.created_at else None,
        "author_user_id": r.author_user_id, "on_behalf_of_user_id": r.on_behalf_of_user_id,
        "source": r.source, "label": r.label, "content_hash": r.content_hash,
        "size_bytes": r.size_bytes, "is_checkpoint": r.is_checkpoint,
    }


def _require_role(db, project_id, user, need="viewer"):
    if is_dev_full_access():
        return  # dev/локальный режим без авторизации — полный доступ
    if user is not None and getattr(user, "is_superadmin", False):
        return
    if rank(project_role(db, project_id, user)) < rank(need):
        raise HTTPException(status_code=403, detail="Недостаточно прав на проект")


@router.get("/projects/{project_id}/revisions")
def list_project_revisions(project_id: int, limit: int = Query(50, le=200),
                           db: Session = Depends(get_db),
                           user: Optional[models.User] = Depends(get_current_user)):
    _require_role(db, project_id, user, "viewer")
    return [_rev_meta(r) for r in revisions.list_revisions(db, project_id, limit)]


@router.get("/projects/{project_id}/revisions/{n}")
def get_project_revision(project_id: int, n: int, db: Session = Depends(get_db),
                         user: Optional[models.User] = Depends(get_current_user)):
    _require_role(db, project_id, user, "viewer")
    r = db.query(models.ProjectRevision).filter(
        models.ProjectRevision.project_id == project_id,
        models.ProjectRevision.n == n).first()
    if not r:
        raise HTTPException(status_code=404, detail="Revision not found")
    return {**_rev_meta(r), "diff_vs_current": revisions.diff_snapshot(db, project_id, r.snapshot)}


@router.post("/projects/{project_id}/checkpoint")
def create_checkpoint(project_id: int, body: CheckpointIn, db: Session = Depends(get_db),
                      user: Optional[models.User] = Depends(get_current_user)):
    _require_role(db, project_id, user, "owner")
    rev = revisions.create_revision(
        db, project_id, source="manual", label=body.label or "checkpoint",
        author_user_id=getattr(user, "id", None), force=True)
    return _rev_meta(rev) if rev else {"error": "empty snapshot"}


@router.post("/projects/{project_id}/revisions/{n}/restore")
def restore_project_revision(project_id: int, n: int, body: RestoreIn,
                             db: Session = Depends(get_db),
                             user: Optional[models.User] = Depends(get_current_user)):
    _require_role(db, project_id, user, "owner")
    r = db.query(models.ProjectRevision).filter(
        models.ProjectRevision.project_id == project_id,
        models.ProjectRevision.n == n).first()
    if not r or not r.snapshot:
        raise HTTPException(status_code=404, detail="Revision not found")
    res = revisions.restore_snapshot(db, project_id, r.snapshot, dry_run=body.dry_run,
                                     author_user_id=getattr(user, "id", None))
    return res
