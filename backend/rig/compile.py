"""Compile a SceneRig manifest into a canonical GLB.

Renames skeleton nodes from source names (Mixamo/RPM/Rigify/VRM/custom) to the
canonical SceneRig names, preserving indices and animation channels. This is
the step that removes runtime retargeting and name adapters.

Only .glb input is supported (external-buffer .gltf would need embedding).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
from pathlib import Path

from . import glb as glbmod
from .archetypes import map_bones, normalize_bone
from .validate import Report, validate_manifest

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_glb(doc_json: dict, bin_bytes: bytes) -> bytes:
    """Serialise a glTF JSON dictionary + BIN chunk back into a GLB."""
    raw_json = json.dumps(doc_json, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raw_json += b" " * ((4 - len(raw_json) % 4) % 4)
    if bin_bytes:
        bin_bytes += b"\x00" * ((4 - len(bin_bytes) % 4) % 4)
    total = 12 + 8 + len(raw_json) + ((8 + len(bin_bytes)) if bin_bytes else 0)
    out = bytearray(struct.pack("<III", GLB_MAGIC, 2, total))
    out += struct.pack("<II", len(raw_json), CHUNK_JSON) + raw_json
    if bin_bytes:
        out += struct.pack("<II", len(bin_bytes), CHUNK_BIN) + bin_bytes
    return bytes(out)


def _source_map(manifest: dict, node_names: list[str]) -> tuple[dict[str, str], list[str], dict]:
    """Build source -> canonical, honouring manifest bones.map over aliases."""
    override = (manifest.get("bones") or {}).get("map") or {}
    source_to_canon: dict[str, str] = {}
    unmapped: list[str] = []
    canon_to_sources: dict[str, list[str]] = {}
    for name in node_names:
        candidate = override.get(name) if isinstance(override, dict) and name in override else name
        canon = normalize_bone(candidate)
        if not canon:
            unmapped.append(name)
            continue
        source_to_canon[name] = canon
        canon_to_sources.setdefault(canon, []).append(name)
    duplicates = {c: names for c, names in canon_to_sources.items() if len(names) > 1}
    return source_to_canon, unmapped, duplicates


def compile_rig(manifest_path: str | Path, out_dir: str | Path | None = None,
                *, write_manifest: bool = True) -> tuple[Report, Path]:
    """Compile a scenerig manifest. Returns (report, manifest_out_path)."""
    src_manifest = Path(manifest_path).resolve()
    data = json.loads(src_manifest.read_text(encoding="utf-8"))
    rep = Report(path=str(src_manifest), kind="compile")
    if data.get("format") != "scenerig/1":
        rep.error("compile.format", "only scenerig/1 can be compiled")
        return rep, src_manifest

    geom_rel = (data.get("geometry") or {}).get("file")
    if not geom_rel:
        rep.error("compile.geometry", "geometry.file is required")
        return rep, src_manifest
    geom_path = (src_manifest.parent / geom_rel).resolve()
    if not geom_path.exists():
        rep.error("compile.geometry", f"geometry file not found: {geom_path}")
        return rep, src_manifest
    if geom_path.suffix.lower() != ".glb":
        rep.error("compile.geometry", "only .glb input is supported")
        return rep, src_manifest

    doc = glbmod.read(geom_path)
    joint_ids = glbmod.skin_joint_indices(doc)
    joint_names = [str((doc.nodes[i] or {}).get("name") or "") for i in joint_ids]
    source_to_canon, unmapped, duplicates = _source_map(data, joint_names)
    if duplicates:
        for canon, sources in duplicates.items():
            rep.error("compile.duplicate", f"{canon} maps from several joints: {sources}")
    # Rename only skin joints. Mesh nodes can legitimately share bone-like names
    # (e.g. an "EyeLeft" mesh and a "LeftEye" bone); renaming them would collide.
    renamed = 0
    for i in joint_ids:
        node = doc.nodes[i]
        name = str(node.get("name") or "")
        canon = source_to_canon.get(name)
        if canon and canon != name:
            node["name"] = canon
            renamed += 1

    out_dir = Path(out_dir).resolve() if out_dir else src_manifest.parent / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_id = str(data.get("id") or "asset")
    glb_name = f"{asset_id}.glb"
    glb_out = out_dir / glb_name
    glb_out.write_bytes(write_glb(doc.json, doc.bin))

    data.setdefault("geometry", {})["file"] = glb_name
    data["geometry"]["sha256"] = sha256(glb_out)
    data["geometry"]["tris"] = glbmod.triangle_count(doc)
    data.setdefault("bones", {})["canonical"] = len(unmapped) == 0 and not duplicates
    data["bones"]["map"] = {}
    data["bones"]["extra"] = unmapped
    for clip in data.get("clips") or []:
        rel = clip.get("file")
        if not rel:
            continue
        if rel == geom_rel:
            clip["file"] = glb_name
            continue
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            rep.warn("compile.clip_path", f"clip {clip.get('name')!r}: keeping external path {rel!r}")
            continue
        src_clip = (src_manifest.parent / rel_path).resolve()
        if src_clip.exists():
            dst_clip = out_dir / rel_path
            dst_clip.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_clip, dst_clip)
        else:
            rep.warn("compile.clip_missing", f"clip {clip.get('name')!r}: file not found: {src_clip}")
    data.setdefault("source", {})["sha256"] = sha256(src_manifest)

    manifest_out = out_dir / f"{asset_id}.scenerig.json"
    if write_manifest:
        manifest_out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")

    rep.facts.update({
        "renamed_nodes": renamed,
        "unmapped_nodes": unmapped,
        "glb": str(glb_out),
        "manifest": str(manifest_out) if write_manifest else None,
    })
    if unmapped:
        rep.warn("compile.unmapped", f"{len(unmapped)} node(s) kept as extra: " + ", ".join(unmapped[:12]))
    if write_manifest:
        sub = validate_manifest(manifest_out)
        rep.children.append(sub)
    return rep, manifest_out


def compile_path(manifest_path: str | Path, out_dir: str | Path | None = None,
                 *, write_manifest: bool = True) -> tuple[Report, Path]:
    return compile_rig(manifest_path, out_dir, write_manifest=write_manifest)
