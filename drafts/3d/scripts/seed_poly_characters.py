#!/usr/bin/env python3
"""Register Mark and Mira as editable character assets in the library.

Run inside the backend container:
    python scripts/seed_poly_characters.py
"""
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import models
from backend.database import SessionLocal, engine

ASSETS = [
    {
        "slug": "character-mark",
        "title": "Mark HD",
        "base": "mark",
        "source_url": "/models/hero/mark-hd.glb",
        "rig": None,
        "appearance": {
            "skin": "#c98b6b", "hair": "#241812", "top": "#2d5f46",
            "bottom": "#45454c", "shoes": "#151312", "eyes": "#3c6a8a",
            "lips": "#8f4d45", "glasses": False, "hood": False, "scale": 1,
        },
    },
    {
        "slug": "character-mira",
        "title": "Mira HD",
        "base": "mira",
        "source_url": "/models/brunette.glb",
        "rig": "/models/brunette.scenerig.json",
        "appearance": {
            "skin": "#dba68a", "hair": "#3a2018", "top": "#33734f",
            "bottom": "#382b3d", "shoes": "#3d1c1a", "eyes": "#3373a0",
            "lips": "#ad4c4c", "glasses": True, "hood": False, "scale": 1,
        },
    },
]


def run():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for a in ASSETS:
            manifest = {
                "format": "sceneasset/1",
                "id": a["slug"],
                "title": a["title"],
                "kind": "character",
                "base": a.get("base"),
                "category": "character",
                "family": "human",
                "archetype": "humanoid",
                "rig": a["rig"],
                "geometry": {"type": "gltf", "file": a["source_url"],
                             "units": "m", "up": "Y", "facing": "+Z"},
                "appearance": a["appearance"],
                "license": {"name": "check-local-source", "author": "SceneEngine / Avatar SDK / Ready Player Me"},
            }
            row = db.query(models.SceneAsset).filter(models.SceneAsset.slug == a["slug"]).first()
            if row:
                row.title = a["title"]
                row.kind = "character"
                row.category = "character"
                row.manifest = manifest
                row.source_url = a["source_url"]
            else:
                db.add(models.SceneAsset(
                    slug=a["slug"], title=a["title"], kind="character",
                    category="character", manifest=manifest,
                    source_url=a["source_url"],
                ))
        db.commit()
        print("seeded:", ", ".join(a["slug"] for a in ASSETS))
    finally:
        db.close()


if __name__ == "__main__":
    run()
