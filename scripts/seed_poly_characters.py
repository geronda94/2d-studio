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
        "title": "Mark",
        "source_url": "/models/characters/character-mark.glb",
        "rig": "/models/characters/character-mark.scenerig.json",
        "appearance": {
            "skin": "#b8805e", "hair": "#1a130f", "top": "#294d8c",
            "bottom": "#292b33", "shoes": "#141417", "eyes": "#2e6147",
            "lips": "#8c3d38", "glasses": False, "hood": True, "scale": 1,
        },
    },
    {
        "slug": "character-mira",
        "title": "Mira",
        "source_url": "/models/characters/character-mira.glb",
        "rig": "/models/characters/character-mira.scenerig.json",
        "appearance": {
            "skin": "#dba68a", "hair": "#752914", "top": "#33734f",
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
                "category": "character",
                "family": "human",
                "archetype": "humanoid",
                "rig": a["rig"],
                "geometry": {"type": "gltf", "file": a["source_url"],
                             "units": "m", "up": "Y", "facing": "+Z"},
                "appearance": a["appearance"],
                "license": {"name": "CC0", "author": "SceneEngine"},
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
