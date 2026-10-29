#!/usr/bin/env python3
"""Import a GLB/GLTF into a SceneRig 1.0 manifest.

Reads the skeleton, maps bone names to the canonical SceneRig set, collects
morph targets and animations, and writes a *.scenerig.json draft.

Run from the repo root:
    python scripts/rig_import.py core/public/models/brunette.glb \
        --id character-brunette --family human --archetype humanoid

The result is a draft: fill in license, title, sockets and clips, then:
    python -m backend.rig validate path/to/character.scenerig.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.rig import glb
from backend.rig.archetypes import (
    archetype_by_name,
    infer_archetype,
    map_bones,
)
from backend.rig.validate import print_report, validate_manifest


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(value: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in value)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")[:64] or "character"


def build_manifest(args) -> dict:
    src = Path(args.input).resolve()
    doc = glb.read(src)
    names = glb.joint_names(doc)
    if not names:
        raise SystemExit("no skin joints found; this is not a character rig")

    mapping, unmapped, duplicates = map_bones(names)
    arch = archetype_by_name(args.archetype) if args.archetype else infer_archetype(names)
    if arch is None:
        raise SystemExit(f"unknown archetype: {args.archetype}")
    family = args.family or arch.family
    if family != arch.family:
        raise SystemExit(f"family {family!r} does not match archetype {arch.slug}")

    morphs = glb.morph_target_names(doc)
    anims = glb.animation_info(doc)
    tris = glb.triangle_count(doc)

    manifest_path = Path(args.out).resolve() if args.out else src.with_suffix(".scenerig.json")
    rel_glb = os.path.relpath(src, manifest_path.parent).replace(os.sep, "/")

    visemes = "oculus-15" if any(m.startswith("viseme_") for m in morphs) else "none"
    face = {
        "morphs": morphs,
        "visemes": visemes,
        "engine_map": "scene-10" if visemes != "none" else "none",
    }
    if "jaw" in mapping:
        face["jaw_bone"] = "jaw"

    clips = []
    for anim in anims:
        if anim["duration"] <= 0:
            continue
        clips.append({
            "name": anim["name"],
            "file": rel_glb,
            "loop": False,
            "fps": 30,
            "duration": round(anim["duration"], 4),
        })

    copyright_ = str((doc.json.get("asset") or {}).get("copyright") or "").strip()
    license_name = args.license or "TBD"
    author = args.author or copyright_ or None
    license_obj = {"name": license_name}
    if author:
        license_obj["author"] = author
    if args.source:
        license_obj["source"] = args.source

    manifest = {
        "format": "scenerig/1",
        "id": args.id or slugify(src.stem),
        "title": args.title or src.stem,
        "family": family,
        "archetype": arch.archetype,
        "geometry": {
            "file": rel_glb,
            "sha256": sha256(src),
            "units": "m",
            "up": "Y",
            "facing": "+Z",
            "tris": tris,
        },
        "rest": {"pose": "A", "origin": "feet"},
        "bones": {
            "canonical": not unmapped and not duplicates,
            "map": {src_name: canon for canon, src_name in mapping.items()},
            "extra": unmapped,
        },
        "face": face,
        "sockets": [],
        "clips": clips,
        "license": license_obj,
        "tags": [family, arch.archetype],
    }

    # Report on the console; the manifest itself stays data-only.
    print(f"input:      {src}")
    print(f"glb:        {doc.asset_version}, {len(names)} joints, {len(morphs)} morphs, {tris} tris")
    print(f"archetype:  {arch.slug} (inferred: {args.archetype is None})")
    print(f"mapped:     {len(mapping)}/{len(names)}")
    if unmapped:
        print(f"unmapped:   {', '.join(unmapped)}")
    if duplicates:
        print(f"duplicates: {duplicates}")
    if anims:
        print("animations: " + ", ".join(f"{a['name']} ({a['duration']:.2f}s)" for a in anims))
    print(f"output:     {manifest_path}")
    if license_name == "TBD":
        print("note:       license.name is TBD — set it before publishing")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Import a GLB into a SceneRig manifest")
    ap.add_argument("input")
    ap.add_argument("--out", default=None)
    ap.add_argument("--id", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--family", choices=["human", "animal", "winged"], default=None)
    ap.add_argument("--archetype", choices=["humanoid", "quadruped", "avian", "insectoid"], default=None)
    ap.add_argument("--license", default=None)
    ap.add_argument("--author", default=None)
    ap.add_argument("--source", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)

    src = Path(args.input)
    if not src.exists():
        print(f"not found: {src}", file=sys.stderr)
        return 2

    manifest = build_manifest(args)
    out = Path(args.out) if args.out else src.with_suffix(".scenerig.json")
    if out.exists() and not args.force:
        print(f"refusing to overwrite {out} (use --force)", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")

    if not args.no_validate:
        rep = validate_manifest(out)
        print_report(rep)
        return 0 if rep.ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
