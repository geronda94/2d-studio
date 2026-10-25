"""SceneRig / SceneAsset validator.

Pure stdlib. Validates a GLB against a canonical archetype and validates
*.scenerig.json / *.sceneasset.json / *.sclip.json manifests.

Exit codes (CLI): 0 = no errors, 1 = errors, 2 = cannot read/parse input.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import glb as glbmod
from .archetypes import (
    ARCHETYPES,
    Archetype,
    archetype_by_name,
    face_min_missing,
    infer_archetype,
    map_bones,
    normalize_bone,
    required_missing,
)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
ALLOWED_PATHS = {"translation", "rotation", "scale", "weights"}
MAX_INFLUENCES = 4


@dataclass
class Issue:
    level: str
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = {"level": self.level, "code": self.code, "message": self.message}
        if self.context:
            out["context"] = self.context
        return out


@dataclass
class Report:
    path: str
    kind: str = "glb"
    archetype: str | None = None
    issues: list[Issue] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    children: list["Report"] = field(default_factory=list)

    def add(self, level: str, code: str, message: str, **context) -> None:
        self.issues.append(Issue(level, code, message, context))

    def error(self, code: str, message: str, **context) -> None:
        self.add("error", code, message, **context)

    def warn(self, code: str, message: str, **context) -> None:
        self.add("warning", code, message, **context)

    def info(self, code: str, message: str, **context) -> None:
        self.add("info", code, message, **context)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors and all(c.ok for c in self.children)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "kind": self.kind,
            "archetype": self.archetype,
            "ok": self.ok,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "facts": self.facts,
            "issues": [i.to_dict() for i in self.issues],
            "children": [c.to_dict() for c in self.children],
        }


# ── helpers ─────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _angle_below_horizontal(a, b) -> float | None:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    horiz = math.hypot(dx, dz)
    if horiz < 1e-6 and abs(dy) < 1e-6:
        return None
    return math.degrees(math.atan2(-dy, horiz))


# ── GLB validation ──────────────────────────────────────────────────────────

def validate_glb(
    path: str | Path,
    archetype: Archetype | None = None,
    *,
    require_rig: bool = True,
    manifest: dict | None = None,
) -> Report:
    p = Path(path)
    rep = Report(path=str(p), kind="glb")
    try:
        doc = glbmod.read(p)
    except glbmod.GLBError as exc:
        rep.error("glb.parse", str(exc))
        return rep

    # Header / asset
    if doc.asset_version != "2.0":
        rep.error("gltf.version", f"asset.version is {doc.asset_version!r}, expected '2.0'")
    if not doc.nodes:
        rep.error("gltf.nodes", "no nodes")
    if not doc.meshes:
        rep.warn("gltf.meshes", "no meshes")

    names = glbmod.joint_names(doc)
    morphs = glbmod.morph_target_names(doc)
    prims = glbmod.primitive_attributes(doc)
    tris = glbmod.triangle_count(doc)
    bounds = glbmod.position_bounds(doc)
    anims = glbmod.animation_info(doc)

    rep.facts.update({
        "nodes": len(doc.nodes),
        "joints": len(names),
        "skins": len(doc.skins),
        "meshes": len(doc.meshes),
        "morphs": len(morphs),
        "triangles": tris,
        "materials": glbmod.material_count(doc),
        "textures": glbmod.texture_count(doc),
        "animations": len(anims),
    })

    if not doc.skins:
        if require_rig:
            rep.error("skin.missing", "no skin: a character needs exactly one skin")
        else:
            rep.info("skin.none", "no skin (allowed for a static prop)")
    elif len(doc.skins) > 1:
        rep.warn("skin.multiple", f"{len(doc.skins)} skins; runtime expects one")

    # Archetype. Static/mechanical props may have a skeleton (door, wheel) but
    # are not expected to match a character archetype.
    check_rig = require_rig or archetype is not None
    if not names:
        if require_rig:
            rep.error("bones.none", "skin has no joints")
            return rep
        rep.info("bones.none", "no skin joints (static asset)")
        archetype = None
    elif archetype is None and check_rig:
        archetype = infer_archetype(names)
        rep.info("archetype.inferred", f"inferred {archetype.slug}",
                 confidence=None)
    elif archetype is None:
        rep.info("bones.skipped", "no archetype check (static/mechanical asset)")

    mapping, unmapped, duplicates = map_bones(names) if names else ({}, [], {})
    if manifest and names:
        _apply_bone_overrides(names, mapping, unmapped, duplicates, manifest, rep)
    declared_extra = set(((manifest or {}).get("bones") or {}).get("extra") or [])
    if declared_extra:
        unknown_extra = sorted(declared_extra - set(names))
        if unknown_extra:
            rep.warn("bones.extra_unknown",
                     "manifest declares bones not present in the GLB: " + ", ".join(unknown_extra[:12]),
                     bones=unknown_extra)
        unmapped = [u for u in unmapped if u not in declared_extra]
    rep.facts.update({
        "bone_map": mapping,
        "bones_mapped": len(mapping),
        "bones_unmapped": len(unmapped),
    })
    if archetype is not None:
        rep.archetype = archetype.slug
        missing = required_missing(archetype, mapping)
        if missing:
            rep.error("bones.missing", "missing required bones: " + ", ".join(missing),
                      bones=missing)
        if duplicates:
            for canon, sources in duplicates.items():
                rep.error("bones.duplicate", f"{canon} mapped from several bones: {sources}",
                          canonical=canon, sources=sources)
        if unmapped:
            rep.warn("bones.unmapped", f"{len(unmapped)} unmapped bone(s): " + ", ".join(unmapped[:12]),
                     bones=unmapped)
        optional = set(archetype.optional)
        recognized = set(mapping)
        extras = sorted(recognized - set(archetype.required) - optional)
        if extras:
            rep.warn("bones.extra", "bones outside the archetype: " + ", ".join(extras[:12]),
                     bones=extras)

    # Skinning attributes and weights
    if doc.skins:
        _validate_skinning(doc, prims, rep)

    # Morphs
    if archetype is not None and archetype.face_min:
        if not morphs:
            jaw = mapping.get("jaw") or mapping.get("beak")
            if not jaw:
                rep.warn("face.missing",
                         "no morph targets and no jaw/beak bone: lipsync is unavailable")
        else:
            missing_face = face_min_missing(archetype, morphs)
            if missing_face:
                rep.warn("face.min", "missing recommended face morphs: " + ", ".join(missing_face),
                         morphs=missing_face)
    if len(morphs) > 80:
        rep.warn("face.budget", f"{len(morphs)} morph targets; over mobile budget (80)")

    # Bounds, units, rest pose
    if bounds:
        lo, hi = bounds
        height = hi[1] - lo[1]
        rep.facts.update({"bounds_min": list(lo), "bounds_max": list(hi), "height": round(height, 3)})
        if height > 20:
            rep.warn("units.scale", f"height {height:.2f} looks like millimetres, expected metres")
        elif height < 0.05:
            rep.warn("units.scale", f"height {height:.2f} looks like centimetres, expected metres")
        elif archetype is not None and archetype.archetype == "humanoid" and not (1.2 <= height <= 2.4):
            rep.warn("units.height", f"human height {height:.2f} m is outside 1.2–2.4 m")
        if archetype is not None and abs(lo[1]) > 0.2:
            rep.warn("pose.ground", f"feet are {lo[1]:.3f} m off the ground")
    else:
        rep.warn("geometry.bounds", "POSITION accessors have no min/max")

    if archetype is not None:
        _validate_pose(doc, archetype, mapping, rep)

    # Animations
    joint_set = set(glbmod.skin_joint_indices(doc))
    for anim in anims:
        if anim["channels"] == 0:
            rep.warn("anim.empty", f"animation {anim['name']!r} has no channels")
        if anim["duration"] <= 0:
            rep.error("anim.duration", f"animation {anim['name']!r} has zero duration")
        if anim["min_keys"] < 2:
            rep.warn("anim.keys", f"animation {anim['name']!r} has channels with fewer than 2 keys")
        for node in anim["targets"]:
            if node not in joint_set and doc.nodes and node < len(doc.nodes):
                # Morph-weight channels target the mesh node, not a joint: allowed.
                if "weights" not in anim["paths"]:
                    rep.warn("anim.target", f"animation {anim['name']!r} targets a non-joint node",
                             node=node, name=(doc.nodes[node] or {}).get("name"))
        for path_name in anim["paths"]:
            if path_name not in ALLOWED_PATHS:
                rep.warn("anim.path", f"animation {anim['name']!r} uses unknown path {path_name!r}")

    # Budgets
    if tris > 60_000:
        rep.warn("budget.tris", f"{tris} triangles; over the 60k character budget")
    if glbmod.material_count(doc) > 8:
        rep.warn("budget.materials", f"{glbmod.material_count(doc)} materials; over 8")

    if manifest:
        _validate_manifest_against_gltf(manifest, doc, anims, rep)

    return rep



def _apply_bone_overrides(
    names: list[str],
    mapping: dict[str, str],
    unmapped: list[str],
    duplicates: dict[str, list[str]],
    manifest: dict,
    rep: Report,
) -> None:
    """Honour bones.map (source -> canonical) from the manifest.

    The map is how a non-standard rig declares its own names without teaching
    the global alias table.
    """
    override = (manifest.get("bones") or {}).get("map") or {}
    if not isinstance(override, dict):
        rep.error("bones.map", "bones.map must be an object")
        return
    name_set = set(names)
    for src, canon in override.items():
        if not isinstance(src, str) or not isinstance(canon, str):
            rep.error("bones.map", "bones.map must map strings to strings")
            continue
        if src not in name_set:
            rep.warn("bones.map_source", f"bones.map references a bone not in the GLB: {src!r}")
            continue
        expected = normalize_bone(canon)
        if expected is None:
            rep.error("bones.map_canon", f"bones.map target {canon!r} is not a canonical bone")
            continue
        # Drop a previous mapping of this source under another canonical name.
        for key, val in list(mapping.items()):
            if val == src:
                del mapping[key]
        if expected in mapping and mapping[expected] != src:
            duplicates.setdefault(expected, [mapping[expected]]).append(src)
            continue
        mapping[expected] = src
        if src in unmapped:
            unmapped.remove(src)
    rep.info("bones.map", f"{len(override)} manifest bone mapping(s) applied")

def _validate_skinning(doc, prims: list[dict], rep: Report) -> None:
    has_skin = bool(doc.skins)
    if not has_skin:
        return
    for prim in prims:
        attrs = prim["attributes"]
        label = f"mesh {prim['mesh']} primitive {prim['primitive']}"
        if "JOINTS_0" not in attrs or "WEIGHTS_0" not in attrs:
            rep.error("weights.attributes", f"{label} has no JOINTS_0/WEIGHTS_0")
            continue
        if "JOINTS_1" in attrs or "WEIGHTS_1" in attrs:
            rep.warn("weights.sets", f"{label} has more than one weight set")
        joints_idx = attrs.get("JOINTS_0")
        weights_idx = attrs.get("WEIGHTS_0")
        if joints_idx is None or weights_idx is None:
            continue
        try:
            joints = glbmod.read_accessor(doc, int(joints_idx), limit=200)
            weights = glbmod.read_accessor(doc, int(weights_idx), limit=200)
        except glbmod.GLBError as exc:
            rep.warn("weights.read", f"{label}: {exc}")
            continue
        if not weights:
            if glbmod.accessor_info(doc, int(weights_idx)).get("sparse"):
                rep.warn("weights.sparse", f"{label}: sparse weights are not expanded")
            continue
        bad_sum = 0
        bad_infl = 0
        worst = 0.0
        n = min(len(weights), len(joints)) or len(weights)
        for i in range(n):
            w = weights[i]
            total = sum(w)
            worst = max(worst, abs(total - 1.0))
            if abs(total - 1.0) > 0.01:
                bad_sum += 1
            influences = sum(1 for x in w if abs(x) > 1e-5)
            if influences > MAX_INFLUENCES:
                bad_infl += 1
        if bad_sum:
            frac = bad_sum / n
            level = "error" if worst > 0.15 or frac > 0.05 else "warning"
            rep.add(level, "weights.sum",
                    f"{label}: {bad_sum}/{n} sampled vertices have weights not summing to 1 "
                    f"(worst {worst:.3f})", worst=round(worst, 4), sampled=n)
        if bad_infl:
            rep.error("weights.influences",
                      f"{label}: {bad_infl} sampled vertices have more than {MAX_INFLUENCES} influences")
        if worst > 0.05:
            rep.info("weights.sample", f"{label}: sampled {n} vertices (worst sum error {worst:.3f})")


def _validate_pose(doc, archetype: Archetype, mapping: dict[str, str], rep: Report) -> None:
    names = glbmod.joint_names(doc)
    node_ids = glbmod.skin_joint_indices(doc)
    by_name = {name: node for name, node in zip(names, node_ids)}
    pos = glbmod.joint_world_positions(doc)
    idx = {canon: by_name[src] for canon, src in mapping.items() if src in by_name}

    def p(canon: str):
        i = idx.get(canon)
        return pos.get(i) if i is not None else None

    # A-pose: shoulder -> elbow angle below horizontal.
    for side in ("L", "R"):
        a, b = p(f"shoulder.{side}"), p(f"upperArm.{side}")
        c = p(f"lowerArm.{side}")
        if b and c:
            angle = _angle_below_horizontal(b, c)
            if angle is not None:
                if angle < 15:
                    rep.warn("pose.tpose", f"arm {side} is nearly horizontal ({angle:.0f}°): expected A-pose 35–55°")
                elif angle > 75:
                    rep.warn("pose.arms_low", f"arm {side} points down ({angle:.0f}°): expected A-pose 35–55°")
                rep.facts[f"arm_angle_{side}"] = round(angle, 1)
                break

    # Facing: ankle -> toe should point +Z.
    for side in ("L", "R"):
        a = p(f"foot.{side}")
        b = p(f"toe.{side}")
        if a and b:
            dz = b[2] - a[2]
            dx = b[0] - a[0]
            norm = math.hypot(dx, dz)
            if norm > 1e-6:
                dot = dz / norm
                rep.facts["facing_dot_z"] = round(dot, 3)
                if dot < -0.3:
                    rep.warn("pose.facing", f"feet point away from +Z (dot {dot:.2f})")
                elif abs(dot) < 0.2:
                    rep.warn("pose.facing_uncertain", f"foot direction is ambiguous (dot {dot:.2f})")
            break

    # Insectoids/humanoids: head above hips.
    hips = p("hips") or p("thorax")
    head = p("head")
    if hips and head and head[1] < hips[1]:
        rep.warn("pose.upside_down", "head is below hips")


def _validate_manifest_against_gltf(manifest: dict, doc, anims, rep: Report) -> None:
    face = manifest.get("face") or {}
    declared = face.get("morphs") or []
    if declared:
        actual = set(glbmod.morph_target_names(doc))
        absent = [m for m in declared if m not in actual]
        if absent:
            rep.warn("face.declared", "manifest declares missing morphs: " + ", ".join(absent[:12]),
                     morphs=absent)
    for clip in manifest.get("clips") or []:
        if not isinstance(clip, dict):
            continue
        name = clip.get("name")
        declared_duration = clip.get("duration")
        if declared_duration and name:
            match = next((a for a in anims if a["name"] == name), None)
            if match and abs(float(declared_duration) - match["duration"]) > 0.15:
                rep.warn("clip.duration",
                         f"clip {name!r}: manifest {declared_duration}s, glTF {match['duration']:.3f}s")


# ── manifest validation ─────────────────────────────────────────────────────

def validate_manifest(path: str | Path) -> Report:
    p = Path(path)
    rep = Report(path=str(p), kind="manifest")
    try:
        data = _read_json(p)
    except (OSError, json.JSONDecodeError) as exc:
        rep.error("manifest.read", str(exc))
        return rep
    fmt = data.get("format")
    rep.facts["format"] = fmt
    if fmt == "scenerig/1":
        _validate_rig_manifest(p, data, rep)
    elif fmt == "sceneasset/1":
        _validate_asset_manifest(p, data, rep)
    elif fmt == "sceneclip/1":
        _validate_clip_data(p, data, rep)
    else:
        rep.error("manifest.format", f"unknown format {fmt!r}")
    return rep


def _validate_rig_manifest(p: Path, data: dict, rep: Report) -> None:
    base = p.parent
    if not ID_RE.match(str(data.get("id") or "")):
        rep.error("manifest.id", "id must match [a-z0-9][a-z0-9-]{1,63}")
    family = data.get("family")
    archetype = archetype_by_name(str(data.get("archetype") or ""))
    if not archetype:
        rep.error("manifest.archetype", f"unknown archetype {data.get('archetype')!r}")
    elif family not in ("human", "animal", "winged"):
        rep.error("manifest.family", f"unknown family {family!r}")
    elif archetype.family != family:
        rep.error("manifest.family", f"family {family!r} does not match archetype {archetype.slug}")
    lic = data.get("license") or {}
    if not lic.get("name"):
        rep.error("manifest.license", "license.name is required")

    geom = data.get("geometry") or {}
    geom_path = base / str(geom.get("file") or "")
    if not geom.get("file"):
        rep.error("manifest.geometry", "geometry.file is required")
    elif not geom_path.exists():
        rep.error("manifest.geometry", f"geometry file not found: {geom_path}")
    else:
        expected = geom.get("sha256")
        if expected and _sha256(geom_path).lower() != str(expected).lower():
            rep.error("manifest.sha256", "geometry.sha256 does not match")
        child = validate_glb(geom_path, archetype, require_rig=True, manifest=data)
        rep.children.append(child)
        rep.archetype = archetype.slug

    # Clips
    seen_clips = set()
    for clip in data.get("clips") or []:
        name = clip.get("name")
        if not name:
            rep.error("clip.name", "clip.name is required")
            continue
        if name in seen_clips:
            rep.error("clip.duplicate", f"duplicate clip name {name!r}")
        seen_clips.add(name)
        file = clip.get("file")
        if not file:
            rep.error("clip.file", f"clip {name!r} has no file")
            continue
        cp = base / file
        if not cp.exists():
            rep.error("clip.file", f"clip {name!r}: file not found: {cp}")
            continue
        sub = Report(path=str(cp), kind="clip")
        if cp.suffix.lower() == ".json":
            try:
                cdata = _read_json(cp)
            except (OSError, json.JSONDecodeError) as exc:
                sub.error("clip.read", str(exc))
            else:
                _validate_clip_data(cp, cdata, sub, duration_hint=clip.get("duration"),
                                    bones=set((data.get("bones") or {}).get("extra") or []))
        else:
            try:
                cdoc = glbmod.read(cp)
            except glbmod.GLBError as exc:
                sub.error("clip.parse", str(exc))
            else:
                cinfo = glbmod.animation_info(cdoc)
                if not cinfo:
                    sub.warn("clip.animations", "file has no animations")
                for anim in cinfo:
                    sub.facts.setdefault("animations", []).append(
                        {"name": anim["name"], "duration": anim["duration"]})
        rep.children.append(sub)

    # Sockets: every socket must point at a mapped or declared-extra bone.
    mapped = set()
    for child in rep.children:
        mapped.update((child.facts.get("bone_map") or {}).keys())
    extra = set((data.get("bones") or {}).get("extra") or [])
    seen_sockets = set()
    for socket in data.get("sockets") or []:
        name = socket.get("name")
        bone = socket.get("bone")
        if not name:
            rep.error("socket.name", "socket needs a name")
        elif name in seen_sockets:
            rep.error("socket.duplicate", f"duplicate socket name {name!r}")
        seen_sockets.add(name)
        if not bone:
            rep.error("socket.bone", f"socket {name!r} needs a bone")
        elif mapped and bone not in mapped and bone not in extra:
            rep.error("socket.bone", f"socket {name!r} references unknown bone {bone!r}",
                      bone=bone, known=sorted(mapped)[:12])


def _validate_asset_manifest(p: Path, data: dict, rep: Report) -> None:
    base = p.parent
    if not ID_RE.match(str(data.get("id") or "")):
        rep.error("manifest.id", "id must match [a-z0-9][a-z0-9-]{1,63}")
    kind = data.get("kind")
    if kind not in ("character", "prop3d", "prop2d", "environment", "fx"):
        rep.error("manifest.kind", f"unknown kind {kind!r}")
    lic = data.get("license") or {}
    if not lic.get("name"):
        rep.error("manifest.license", "license.name is required")

    geom = data.get("geometry") or {}
    gtype = geom.get("type")
    if not gtype:
        rep.error("manifest.geometry", "geometry.type is required")
    gfile = geom.get("file")
    if gfile:
        gp = base / gfile
        if not gp.exists():
            rep.error("manifest.geometry", f"geometry file not found: {gp}")
        elif geom.get("sha256") and _sha256(gp).lower() != str(geom["sha256"]).lower():
            rep.error("manifest.sha256", "geometry.sha256 does not match")
        elif kind in ("character", "prop3d"):
            sub = validate_glb(gp, None, require_rig=(kind == "character"))
            rep.children.append(sub)

    if kind == "character":
        family = data.get("family")
        arche = archetype_by_name(str(data.get("archetype") or ""))
        if not arche or not family:
            rep.error("manifest.rig", "character needs family and archetype")
        elif arche.family != family:
            rep.error("manifest.rig", f"family {family!r} does not match archetype {arche.slug}")
        rig = data.get("rig")
        if rig:
            rp = base / rig
            if not rp.exists():
                rep.error("manifest.rig", f"rig manifest not found: {rp}")
            else:
                rep.children.append(validate_manifest(rp))

    if kind == "environment":
        layers = data.get("layers") or []
        ids = set()
        for layer in layers:
            lid = layer.get("id")
            if not lid:
                rep.error("env.layer.id", "layer needs an id")
            elif lid in ids:
                rep.error("env.layer.duplicate", f"duplicate layer id {lid!r}")
            ids.add(lid)
            depth = layer.get("depth", 0)
            if not isinstance(depth, (int, float)) or not (0 <= depth <= 1):
                rep.error("env.layer.depth", f"layer {lid!r}: depth must be 0..1")
            if layer.get("file"):
                lp = base / layer["file"]
                if not lp.exists():
                    rep.error("env.layer.file", f"layer {lid!r}: file not found: {lp}")
        palette = data.get("palette") or {}
        for view in (data.get("compat") or {}).get("views") or []:
            if view not in palette and palette:
                rep.warn("env.palette", f"view {view!r} has no palette entry")

    if kind == "fx" and not data.get("fx"):
        rep.warn("fx.missing", "fx asset has no fx definition")


def _validate_clip_data(
    p: Path,
    data: dict,
    rep: Report,
    *,
    duration_hint: float | None = None,
    bones: set[str] | None = None,
) -> None:
    rep.kind = "clip"
    bones = bones or set()
    if data.get("format") != "sceneclip/1":
        rep.error("clip.format", "format must be sceneclip/1")
    name = data.get("name")
    if not name or not re.match(r"^[a-zA-Z0-9_.-]{1,64}$", str(name)):
        rep.error("clip.name", "invalid clip name")
    fps = data.get("fps")
    if not isinstance(fps, (int, float)) or fps <= 0:
        rep.error("clip.fps", "fps must be > 0")
    duration = data.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        rep.error("clip.duration", "duration must be > 0")
        duration = duration_hint or 0
    elif duration_hint and abs(float(duration) - float(duration_hint)) > 0.05:
        rep.warn("clip.duration_hint",
                 f"clip duration {duration}s differs from manifest hint {duration_hint}s")

    tracks = data.get("tracks") or {}
    if not tracks:
        rep.warn("clip.tracks", "clip has no bone tracks")
    for bone, channels in tracks.items():
        canon = normalize_bone(bone)
        if canon is None and bone not in bones:
            rep.error("clip.bone", f"unknown bone {bone!r}", bone=bone)
        if not isinstance(channels, dict) or not channels:
            rep.error("clip.channel", f"bone {bone!r} has no channels")
            continue
        for channel, keys in channels.items():
            if channel not in ("rotation", "translation", "scale"):
                rep.warn("clip.channel", f"bone {bone!r}: unknown channel {channel!r}")
                continue
            need = 5 if channel == "rotation" else 4
            if not isinstance(keys, list) or not keys:
                rep.error("clip.keys", f"bone {bone!r}.{channel}: no keys")
                continue
            last_t = -1.0
            for key in keys:
                if not isinstance(key, list) or len(key) != need:
                    rep.error("clip.key", f"bone {bone!r}.{channel}: key must be [{need} values]")
                    break
                t = float(key[0])
                if t < 0 or t > float(duration) + 1e-6:
                    rep.error("clip.key_time", f"bone {bone!r}.{channel}: time {t} outside 0..{duration}")
                    break
                if t < last_t - 1e-9:
                    rep.error("clip.key_order", f"bone {bone!r}.{channel}: keys are not sorted")
                    break
                last_t = t
            if len(keys) < 2 and duration > 0.2:
                rep.warn("clip.keys", f"bone {bone!r}.{channel}: fewer than 2 keys")

    face = data.get("face") or {}
    for morph, keys in face.items():
        if not isinstance(keys, list):
            rep.error("clip.face", f"face {morph!r}: keys must be a list")
            continue
        last_t = -1.0
        for key in keys:
            if not isinstance(key, list) or len(key) != 2:
                rep.error("clip.face", f"face {morph!r}: key must be [time, weight]")
                break
            t, w = float(key[0]), float(key[1])
            if t < 0 or t > float(duration) + 1e-6:
                rep.error("clip.face_time", f"face {morph!r}: time {t} outside 0..{duration}")
                break
            if t < last_t - 1e-9:
                rep.error("clip.key_order", f"face {morph!r}: keys are not sorted")
                break
            if w < -1e-6 or w > 1 + 1e-6:
                rep.warn("clip.face_weight", f"face {morph!r}: weight {w} outside 0..1")
            last_t = t

    for event in data.get("events") or []:
        t = event.get("t")
        if not isinstance(t, (int, float)) or t < 0 or t > float(duration) + 1e-6:
            rep.error("clip.event", "event time outside the clip")
        if not event.get("name"):
            rep.error("clip.event", "event needs a name")


# ── dispatch ────────────────────────────────────────────────────────────────

def validate_path(path: str | Path, archetype: str | None = None) -> Report:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".json":
        return validate_manifest(p)
    arch = archetype_by_name(archetype) if archetype else None
    return validate_glb(p, arch)


def print_report(rep: Report, *, indent: int = 0) -> None:
    pad = "  " * indent
    status = "OK" if rep.ok else "FAIL"
    print(f"{pad}=== {rep.path} ===")
    if rep.archetype:
        print(f"{pad}archetype: {rep.archetype}")
    if rep.facts:
        facts = ", ".join(f"{k}={v}" for k, v in rep.facts.items()
                          if isinstance(v, (str, int, float, bool)))
        if facts:
            print(f"{pad}{facts[:300]}")
    print(f"{pad}status: {status} ({len(rep.errors)} errors, {len(rep.warnings)} warnings)")
    for level, items in (("ERRORS", rep.errors), ("WARNINGS", rep.warnings),
                         ("INFO", [i for i in rep.issues if i.level == "info"])):
        if not items:
            continue
        print(f"{pad}{level}:")
        for issue in items:
            print(f"{pad}  [{issue.code}] {issue.message}")
    for child in rep.children:
        print_report(child, indent=indent + 1)
