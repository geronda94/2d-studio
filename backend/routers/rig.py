"""Rig API: canonical archetypes and GLB validation for the browser studio."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..rig import archetype_by_name, archetypes_payload, validate_glb, validate_manifest

router = APIRouter(prefix="/rig", tags=["rig"])

MAX_BYTES = 64 * 1024 * 1024


@router.get("/archetypes")
def read_archetypes():
    """Canonical bone sets for the Rig Studio UI and AI agents."""
    return {"archetypes": archetypes_payload()}


@router.get("/health")
def rig_health():
    return {"ok": True, "validator": "scenerig/1"}


@router.post("/validate")
async def validate_upload(
    file: UploadFile = File(...),
    archetype: str | None = Form(default=None),
    require_rig: bool = Form(default=True),
):
    """Validate an uploaded .glb/.gltf.

    For characters pass `archetype` (and keep `require_rig=true`). For static
    props pass `require_rig=false`. The file is written to a temporary path and
    removed afterwards; nothing is stored in the database.
    """
    name = (file.filename or "upload.glb").lower()
    if not name.endswith((".glb", ".gltf")):
        raise HTTPException(status_code=415, detail="expected .glb or .gltf")
    arch = None
    if archetype:
        arch = archetype_by_name(archetype)
        if arch is None:
            known = [a["archetype"] for a in archetypes_payload()]
            raise HTTPException(status_code=422, detail=f"unknown archetype; known: {known}")

    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file is larger than 64 MB")

    suffix = ".gltf" if name.endswith(".gltf") else ".glb"
    fd, path = tempfile.mkstemp(prefix="scenerig-", suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        report = validate_glb(path, arch, require_rig=require_rig)
        out = report.to_dict()
        out["path"] = file.filename or "upload"
        return out
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


@router.post("/validate-manifest")
async def validate_manifest_upload(
    manifest: str = Form(...),
    file: UploadFile | None = File(default=None),
):
    """Validate a scenerig/sceneasset/sceneclip JSON, optionally with its GLB.

    The manifest is parsed and written to a temporary folder. If `file` is
    given, it is saved under its own base name and the manifest's
    `geometry.file` is pointed at it, so relative paths resolve.
    """
    try:
        data = json.loads(manifest)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="manifest must be a JSON object")

    with tempfile.TemporaryDirectory(prefix="sceneasset-") as td:
        base = Path(td)
        if file is not None:
            raw = await file.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise HTTPException(status_code=413, detail="file is larger than 64 MB")
            name = Path(file.filename or "asset.glb").name
            data.setdefault("geometry", {})["file"] = name
            (base / name).write_bytes(raw)
        mp = base / "manifest.json"
        mp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        report = validate_manifest(mp)
        out = report.to_dict()
        out["path"] = file.filename if file is not None else "manifest.json"
        return out
