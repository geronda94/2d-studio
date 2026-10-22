from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..permissions import enforce_write
from ..validation import validate_component_payload

router = APIRouter(
    prefix="/components",
    tags=["components"],
    dependencies=[Depends(enforce_write)],
)

@router.get("/types", response_model=List[schemas.ComponentType])
def read_component_types(db: Session = Depends(get_db)):
    return db.query(models.ComponentType).all()

@router.post("/types", response_model=schemas.ComponentType)
def create_component_type(type_data: schemas.ComponentTypeCreate, db: Session = Depends(get_db)):
    db_type = models.ComponentType(**type_data.dict())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

@router.delete("/types/{type_id}", response_model=dict)
def delete_component_type(type_id: int, db: Session = Depends(get_db)):
    db_type = db.query(models.ComponentType).filter(models.ComponentType.id == type_id).first()
    if not db_type:
        raise HTTPException(status_code=404, detail="Type not found")
    db.delete(db_type)
    db.commit()
    return {"status": "success"}

@router.get("/categories", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.post("/categories", response_model=schemas.Category)
def create_category(category_data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_cat = models.Category(**category_data.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.delete("/categories/{category_id}", response_model=dict)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return {"status": "success"}

@router.get("/", response_model=List[schemas.Component])
def read_components(db: Session = Depends(get_db)):
    return db.query(models.Component).all()


@router.post("/{slug}/validate", response_model=schemas.ValidationResult)
def validate_payload(slug: str, req: schemas.ValidateRequest, strict: bool = False, lint: bool = False, db: Session = Depends(get_db)):
    """Проверка payload против схемы компонента. Для ИИ и ручной проверки перед сохранением.
    lint=true — плюс style-lint (warnings, не блокируют): no-hex, accent-budget, density."""
    from ..style_lint import lint_payload
    comp = db.query(models.Component).filter(models.Component.slug == slug).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
    errors = validate_component_payload(req.payload, comp, strict=strict)
    warnings = lint_payload(req.payload, comp.payload_schema, component_slug=slug) if lint else []
    return schemas.ValidationResult(
        valid=len(errors) == 0,
        errors=[schemas.ValidationError(**e) for e in errors],
        warnings=[schemas.ValidationError(**w) for w in warnings]
    )

@router.post("/", response_model=schemas.Component)
def create_component(comp: schemas.ComponentCreate, db: Session = Depends(get_db)):
    db_comp = models.Component(
        slug=comp.slug,
        title=comp.title,
        description=comp.description,
        type_id=comp.type_id,
        default_payload=comp.default_payload,
        payload_schema=comp.payload_schema,
        example=comp.example,
        manifest=comp.manifest,
        is_custom=True,  # создан через API — сиды не трогают
    )
    if comp.category_ids:
        categories = db.query(models.Category).filter(models.Category.id.in_(comp.category_ids)).all()
        db_comp.categories = categories

    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.put("/{component_id}", response_model=schemas.Component)
def update_component(component_id: int, comp: schemas.ComponentCreate, db: Session = Depends(get_db)):
    db_comp = db.query(models.Component).filter(models.Component.id == component_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Component not found")

    db_comp.slug = comp.slug
    db_comp.title = comp.title
    db_comp.description = comp.description
    db_comp.type_id = comp.type_id
    db_comp.default_payload = comp.default_payload
    db_comp.payload_schema = comp.payload_schema
    db_comp.example = comp.example
    db_comp.manifest = comp.manifest

    if comp.category_ids is not None:
        categories = db.query(models.Category).filter(models.Category.id.in_(comp.category_ids)).all()
        db_comp.categories = categories

    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.delete("/{component_id}", response_model=dict)
def delete_component(component_id: int, db: Session = Depends(get_db)):
    db_comp = db.query(models.Component).filter(models.Component.id == component_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Component not found")
    db.delete(db_comp)
    db.commit()
    return {"status": "success"}
