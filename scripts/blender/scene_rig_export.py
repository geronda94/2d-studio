"""Blender → SceneRig 1.0 exporter.

Run inside Blender (background or UI):

    blender --background character.blend \
      --python scripts/blender/scene_rig_export.py -- \
      --id character-hero --family human --archetype humanoid \
      --license "CC BY 4.0" --author "You" --out dist/

It checks the armature against the canonical SceneRig set, exports a GLB,
writes <id>.scenerig.json and validates the result with backend.rig.

The scene must contain one armature and at least one mesh with an Armature
modifier. Rest pose is expected to be A-pose, metres, facing -Y in Blender
(+Z after glTF conversion), origin between the feet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy  # noqa: F401 - only available inside Blender

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from backend.rig.archetypes import (  # noqa: E402
    archetype_by_name,
    infer_archetype,
    map_bones,
)
from backend.rig.validate import print_report, validate_manifest  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _slug(value: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in value)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")[:64] or "character"


def _find_armature():
    active = bpy.context.view_layer.objects.active
    if active and active.type == "ARMATURE":
        return active
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def _find_meshes(armature):
    """All meshes bound to the armature (an RPM avatar has several)."""
    out = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if any(m.type == "ARMATURE" and m.object == armature for m in obj.modifiers):
            out.append(obj)
        elif obj.parent == armature:
            out.append(obj)
    return out


def _bone_angle(armature, source_name: str | None):
    if not source_name:
        return None
    bone = armature.data.bones.get(source_name)
    if not bone:
        return None
    head = bone.head_local
    tail = bone.tail_local
    dx, dy, dz = tail.x - head.x, tail.y - head.y, tail.z - head.z
    horiz = math.hypot(dx, dy)
    if horiz < 1e-6 and abs(dz) < 1e-6:
        return None
    return math.degrees(math.atan2(-dz, horiz))


def _mesh_stats(mesh_objs):
    tris = 0
    verts = 0
    unweighted = 0
    max_infl = 0
    bad_sum = 0
    for mesh_obj in mesh_objs:
        mesh = mesh_obj.data
        verts += len(mesh.vertices)
        try:
            mesh.calc_loop_triangles()
            tris += len(mesh.loop_triangles)
        except Exception:
            tris += sum(len(p.vertices) - 2 for p in mesh.polygons)
        for v in mesh.vertices:
            groups = [g for g in v.groups if g.weight > 1e-5]
            if not groups:
                unweighted += 1
                continue
            max_infl = max(max_infl, len(groups))
            total = sum(g.weight for g in groups)
            if abs(total - 1.0) > 0.01:
                bad_sum += 1
    return {
        "tris": tris,
        "verts": verts,
        "meshes": len(mesh_objs),
        "unweighted": unweighted,
        "max_influences": max_infl,
        "bad_weight_sum": bad_sum,
    }


def _shape_keys(mesh_objs):
    names = []
    for mesh_obj in mesh_objs:
        keys = mesh_obj.data.shape_keys
        if not keys:
            continue
        for kb in keys.key_blocks:
            if kb.name != "Basis" and kb.name not in names:
                names.append(kb.name)
    return names


def _actions():
    out = []
    fps = bpy.context.scene.render.fps or 30
    for action in bpy.data.actions:
        try:
            start, end = action.frame_range
        except Exception:
            continue
        duration = max(0.0, (float(end) - float(start)) / float(fps))
        out.append({"name": action.name, "duration": round(duration, 4), "fps": fps})
    return out


def _export_glb(path: Path, armature, mesh_objs):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    for mesh_obj in mesh_objs:
        mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    kwargs = {
        "filepath": str(path),
        "export_format": "GLB",
        "use_selection": True,
        "export_yup": True,
        "export_apply": False,
        "export_animations": True,
        "export_skins": True,
        "export_morph": True,
        "export_extras": True,
        "export_def_bones": False,
        "export_animation_mode": "ACTIONS",
        "export_nla_strips": True,
    }
    props = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    kwargs = {k: v for k, v in kwargs.items() if k in props}
    bpy.ops.export_scene.gltf(**kwargs)


def build(args):
    scene = bpy.context.scene
    armature = _find_armature()
    if not armature:
        raise SystemExit("no armature in the scene")
    mesh_objs = _find_meshes(armature)
    bone_names = [b.name for b in armature.data.bones]
    mapping, unmapped, duplicates = map_bones(bone_names)
    arch = archetype_by_name(args.archetype) if args.archetype else infer_archetype(bone_names)
    if arch is None:
        raise SystemExit(f"unknown archetype: {args.archetype}")
    family = args.family or arch.family
    if family != arch.family:
        raise SystemExit(f"family {family!r} does not match archetype {arch.slug}")

    print(f"armature:   {armature.name} ({len(bone_names)} bones)")
    print(f"archetype:  {arch.slug} (inferred: {args.archetype is None})")
    print(f"mapped:     {len(mapping)}/{len(bone_names)}")
    if unmapped:
        print("unmapped:   " + ", ".join(unmapped))
    if duplicates:
        print(f"duplicates: {duplicates}")

    if mesh_objs:
        stats = _mesh_stats(mesh_objs)
        print(f"meshes:     {', '.join(o.name for o in mesh_objs)} {stats}")
        if stats["unweighted"]:
            print(f"WARNING:    {stats['unweighted']} vertices have no weights")
        if stats["max_influences"] > 4:
            print(f"WARNING:    {stats['max_influences']} influences on a vertex (max 4)")
        if stats["bad_weight_sum"]:
            print(f"WARNING:    {stats['bad_weight_sum']} vertices have weights not summing to 1")
    else:
        stats = {"tris": 0, "verts": 0}
        print("WARNING:    no mesh with an Armature modifier")

    for side in ("L", "R"):
        src = mapping.get(f"upperArm.{side}")
        angle = _bone_angle(armature, src)
        if angle is not None:
            print(f"arm {side}:     {angle:.1f}° below horizontal (A-pose is 35–55°)")
    src_toe = mapping.get("toe.L")
    if src_toe:
        bone = armature.data.bones.get(src_toe)
        if bone:
            dy = bone.tail_local.y - bone.head_local.y
            print(f"toe L:      Blender Y delta {dy:+.3f} (forward should be negative)")

    out_dir = Path(args.out).resolve() if args.out else Path(bpy.data.filepath).parent / "dist"
    asset_id = args.id or _slug(Path(bpy.data.filepath).stem or armature.name)
    manifest_path = Path(args.manifest).resolve() if args.manifest else out_dir / f"{asset_id}.scenerig.json"
    glb_path = out_dir / f"{asset_id}.glb"

    if not args.no_export:
        _export_glb(glb_path, armature, mesh_objs)
        print(f"glb:        {glb_path} ({glb_path.stat().st_size} bytes)")

    rel_glb = os.path.relpath(glb_path, manifest_path.parent).replace(os.sep, "/")
    morphs = _shape_keys(mesh_objs)
    clips = [
        {
            "name": a["name"],
            "file": rel_glb,
            "loop": False,
            "fps": a["fps"],
            "duration": a["duration"],
        }
        for a in _actions() if a["duration"] > 0
    ]
    license_name = args.license or "TBD"
    license_obj = {"name": license_name}
    if args.author:
        license_obj["author"] = args.author
    if args.source:
        license_obj["source"] = args.source

    manifest = {
        "format": "scenerig/1",
        "id": asset_id,
        "title": args.title or armature.name,
        "family": family,
        "archetype": arch.archetype,
        "geometry": {
            "file": rel_glb,
            "units": "m",
            "up": "Y",
            "facing": "+Z",
            "tris": stats.get("tris", 0),
        },
        "rest": {"pose": "A", "origin": "feet"},
        "bones": {
            "canonical": not unmapped and not duplicates,
            "map": {src: canon for canon, src in mapping.items()},
            "extra": unmapped,
        },
        "face": {
            "morphs": morphs,
            "visemes": "oculus-15" if any(m.startswith("viseme_") for m in morphs) else "none",
            "engine_map": "scene-10" if any(m.startswith("viseme_") for m in morphs) else "none",
        },
        "sockets": [],
        "clips": clips,
        "license": license_obj,
        "tags": [family, arch.archetype],
    }
    if glb_path.exists():
        manifest["geometry"]["sha256"] = _sha256(glb_path)
    if bpy.data.filepath:
        manifest["source"] = {"blender": Path(bpy.data.filepath).name}

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest:   {manifest_path}")
    if license_name == "TBD":
        print("note:       license.name is TBD — set it before publishing")

    if not args.no_validate and glb_path.exists():
        rep = validate_manifest(manifest_path)
        print_report(rep)
        return 0 if rep.ok else 1
    return 0


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    ap = argparse.ArgumentParser(description="Export a Blender armature to SceneRig")
    ap.add_argument("--id", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--family", choices=["human", "animal", "winged"], default=None)
    ap.add_argument("--archetype", choices=["humanoid", "quadruped", "avian", "insectoid"], default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--license", default=None)
    ap.add_argument("--author", default=None)
    ap.add_argument("--source", default=None)
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    code = build(args)
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
