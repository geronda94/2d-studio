from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
from ..database import get_db
from ..permissions import enforce_write

router = APIRouter(
    prefix="/presets",
    tags=["presets"],
    dependencies=[Depends(enforce_write)],
)


def _check_refs(db: Session, palette: Optional[str], variant: Optional[str]):
    """Пресет ссылается только на существующие палитру-проект и вариант."""
    if palette:
        proj = db.query(models.Project).filter(models.Project.slug == palette).first()
        if not proj:
            raise HTTPException(status_code=400, detail=f"Palette project '{palette}' not found")
    if variant:
        var = db.query(models.StyleVariant).filter(models.StyleVariant.slug == variant).first()
        if not var:
            raise HTTPException(status_code=400, detail=f"Variant '{variant}' not found")


@router.get("/", response_model=List[schemas.StylePreset])
def read_presets(db: Session = Depends(get_db)):
    return db.query(models.StylePreset).filter(
        models.StylePreset.is_archived.is_(False)
    ).order_by(models.StylePreset.id).all()


@router.get("/{slug}", response_model=schemas.StylePreset)
def read_preset(slug: str, db: Session = Depends(get_db)):
    preset = db.query(models.StylePreset).filter(
        models.StylePreset.slug == slug,
        models.StylePreset.is_archived.is_(False),
    ).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.post("/", response_model=schemas.StylePreset)
def create_preset(preset: schemas.StylePresetCreate, db: Session = Depends(get_db)):
    exists = db.query(models.StylePreset).filter(models.StylePreset.slug == preset.slug).first()
    if exists:
        raise HTTPException(status_code=409, detail="Preset slug already exists")
    _check_refs(db, preset.palette, preset.variant)
    db_preset = models.StylePreset(
        slug=preset.slug,
        title=preset.title,
        palette=preset.palette,
        variant=preset.variant,
        rules=preset.rules,
        is_custom=True,  # создан через API — сиды не трогают (P0)
    )
    db.add(db_preset)
    db.commit()
    db.refresh(db_preset)
    return db_preset


@router.delete("/{slug}", response_model=dict)
def delete_preset(slug: str, db: Session = Depends(get_db)):
    """Удаление — только custom. Дефолтные пресеты сидов защищены (как токены)."""
    preset = db.query(models.StylePreset).filter(models.StylePreset.slug == slug).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    if not getattr(preset, "is_custom", False):
        raise HTTPException(status_code=403, detail="Default presets cannot be deleted")
    db.delete(preset)
    db.commit()
    return {"status": "deleted"}
