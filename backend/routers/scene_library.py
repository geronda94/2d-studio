from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

from ..scene_library import (
    compatibility_matrix,
    get_environment,
    get_object,
    get_template,
    list_environments,
    list_objects,
    list_templates,
    objects_for_environment,
    validate_composition,
)

router = APIRouter(prefix="/scene-library", tags=["scene-library"])


class CompositionRequest(BaseModel):
    environment: str
    objects: List[str] = []


@router.get("/templates")
def read_templates():
    return list_templates()


@router.get("/templates/{slug}")
def read_template(slug: str):
    t = get_template(slug)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.get("/environments")
def read_environments():
    return list_environments()


@router.get("/environments/{slug}")
def read_environment(slug: str):
    e = get_environment(slug)
    if not e:
        raise HTTPException(status_code=404, detail="Environment not found")
    return e


@router.get("/environments/{slug}/objects")
def read_environment_objects(slug: str):
    if not get_environment(slug):
        raise HTTPException(status_code=404, detail="Environment not found")
    return objects_for_environment(slug)


@router.get("/objects")
def read_objects(environment: Optional[str] = None):
    if environment:
        if not get_environment(environment):
            raise HTTPException(status_code=404, detail="Environment not found")
        return objects_for_environment(environment)
    return list_objects()


@router.get("/objects/{slug}")
def read_object(slug: str):
    o = get_object(slug)
    if not o:
        raise HTTPException(status_code=404, detail="Object not found")
    return o


@router.get("/compatibility")
def read_compatibility():
    return compatibility_matrix()


@router.post("/validate-composition")
def validate(body: CompositionRequest):
    return validate_composition(body.environment, body.objects)


@router.get("/learnings", response_model=List[schemas.SceneLearning])
def read_learnings(
    category: Optional[str] = None,
    status: Optional[str] = "active",
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.SceneLearning)
    if category:
        query = query.filter(models.SceneLearning.category == category)
    if status:
        query = query.filter(models.SceneLearning.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            models.SceneLearning.symptom.ilike(like)
            | models.SceneLearning.rule.ilike(like)
            | models.SceneLearning.fix.ilike(like)
        )
    return query.order_by(models.SceneLearning.created_at.desc()).limit(200).all()


@router.post("/learnings", response_model=schemas.SceneLearning)
def create_learning(payload: schemas.SceneLearningCreate, db: Session = Depends(get_db)):
    data = payload.dict()
    # AI proposals never go straight into the active rulebook.
    if data.get("source") == "ai" and (not data.get("status") or data.get("status") == "active"):
        data["status"] = "proposed"
    row = models.SceneLearning(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/learnings/{learning_id}/approve", response_model=schemas.SceneLearning)
def approve_learning(learning_id: int, db: Session = Depends(get_db)):
    row = db.query(models.SceneLearning).filter(models.SceneLearning.id == learning_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Learning not found")
    row.status = "active"
    db.commit()
    db.refresh(row)
    return row


@router.post("/learnings/{learning_id}/archive", response_model=schemas.SceneLearning)
def archive_learning(learning_id: int, db: Session = Depends(get_db)):
    row = db.query(models.SceneLearning).filter(models.SceneLearning.id == learning_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Learning not found")
    row.status = "archived"
    db.commit()
    db.refresh(row)
    return row
