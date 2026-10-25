"""User-authored scene assets (objects, characters, environments).

Built-in entries live in scene_library.py. This router stores editable
SceneAsset 1.0 manifests plus uploaded geometry under /uploads/scene-assets.
"""
from __future__ import annotations

import os
import re
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..rig import validate_glb

router = APIRouter(prefix="/scene-assets", tags=["scene-assets"])

UPLOAD_DIR = "/app/uploads" if os.path.exists("/app") else "uploads"
ASSET_DIR = os.path.join(UPLOAD_DIR, "scene-assets")
os.makedirs(ASSET_DIR, exist_ok=True)

MAX_BYTES = 64 * 1024 * 1024
ALLOWED = {".glb", ".svg", ".png", ".jpg", ".jpeg", ".webp"}
SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe(name: str) -> str:
    base = os.path.basename(name or "asset")
    base = SAFE.sub("-", base).strip("-") or "asset"
    return base[:120]


def _get(db: Session, key: str) -> models.SceneAsset:
    row = None
    if key.isdigit():
        row = db.query(models.SceneAsset).filter(models.SceneAsset.id == int(key)).first()
    if row is None:
        row = db.query(models.SceneAsset).filter(models.SceneAsset.slug == key).first()
    if row is None:
        raise HTTPException(status_code=404, detail="scene asset not found")
    return row


@router.get("", response_model=list[schemas.SceneAsset])
def list_assets(
    kind: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.SceneAsset)
    if kind:
        query = query.filter(models.SceneAsset.kind == kind)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.SceneAsset.slug.ilike(like),
                                 models.SceneAsset.title.ilike(like)))
    return query.order_by(models.SceneAsset.updated_at.desc()).limit(limit).all()


@router.get("/{key}", response_model=schemas.SceneAsset)
def get_asset(key: str, db: Session = Depends(get_db)):
    return _get(db, key)


@router.post("", response_model=schemas.SceneAsset, status_code=201)
def create_asset(payload: schemas.SceneAssetCreate, db: Session = Depends(get_db)):
    if db.query(models.SceneAsset).filter(models.SceneAsset.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="slug already exists")
    row = models.SceneAsset(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{asset_id}", response_model=schemas.SceneAsset)
def update_asset(asset_id: int, payload: schemas.SceneAssetUpdate,
                 db: Session = Depends(get_db)):
    row = db.query(models.SceneAsset).filter(models.SceneAsset.id == asset_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="scene asset not found")
    dup = db.query(models.SceneAsset).filter(
        models.SceneAsset.slug == payload.slug,
        models.SceneAsset.id != asset_id,
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="slug already exists")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    row = db.query(models.SceneAsset).filter(models.SceneAsset.id == asset_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="scene asset not found")
    db.delete(row)
    db.commit()
    return {"deleted": asset_id}


@router.post("/upload")
async def upload_asset(file: UploadFile = File(...)):
    """Store a GLB/SVG/image under /uploads/scene-assets and validate GLBs."""
    name = _safe(file.filename or "asset")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=415, detail=f"allowed: {sorted(ALLOWED)}")
    if ext == ".gltf":
        raise HTTPException(status_code=415, detail="export .glb, not .gltf")
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file is larger than 64 MB")

    stored = f"{uuid.uuid4().hex[:12]}-{name}"
    path = os.path.join(ASSET_DIR, stored)
    with open(path, "wb") as fh:
        fh.write(raw)

    validation = None
    if ext == ".glb":
        report = validate_glb(path, None, require_rig=False)
        validation = report.to_dict()
        validation["path"] = name

    return {
        "url": f"/uploads/scene-assets/{stored}",
        "filename": stored,
        "original": name,
        "size": len(raw),
        "kind": "prop3d" if ext == ".glb" else "prop2d",
        "validation": validation,
    }
