from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..permissions import enforce_write

router = APIRouter(
    prefix="/variants",
    tags=["variants"],
    dependencies=[Depends(enforce_write)],
)


@router.get("/", response_model=List[schemas.StyleVariant])
def read_variants(db: Session = Depends(get_db)):
    return db.query(models.StyleVariant).filter(
        models.StyleVariant.is_archived.is_(False)
    ).order_by(models.StyleVariant.id).all()


@router.get("/{slug}", response_model=schemas.StyleVariant)
def read_variant(slug: str, db: Session = Depends(get_db)):
    variant = db.query(models.StyleVariant).filter(
        models.StyleVariant.slug == slug,
        models.StyleVariant.is_archived.is_(False),
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant


@router.post("/", response_model=schemas.StyleVariant)
def create_variant(variant: schemas.StyleVariantCreate, db: Session = Depends(get_db)):
    exists = db.query(models.StyleVariant).filter(models.StyleVariant.slug == variant.slug).first()
    if exists:
        raise HTTPException(status_code=409, detail="Variant slug already exists")
    db_variant = models.StyleVariant(
        slug=variant.slug,
        name=variant.name,
        description=variant.description,
        config=variant.config,
        is_custom=True,  # создан через API — сиды не трогают (P0)
    )
    db.add(db_variant)
    db.commit()
    db.refresh(db_variant)
    return db_variant
