"""Загрузчик метаданных православного канала (docs/ROADMAP_ORTHODOX.md).

Читает scripts/_orthodox_meta/*.json (slug/title/description/manifest/categories/
required/payload) и отдаёт записи для seed_components.py и seed_manifests.py.
"""
import glob
import json
import os

_META_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_orthodox_meta")


def build():
    out = []
    for path in sorted(glob.glob(os.path.join(_META_DIR, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        cats = d.get("categories") or ["ui"]
        out.append({
            "slug": d["slug"],
            "title": d["title"],
            "cat": cats[0],
            "payload": d["payload"],
            "description": d.get("description", ""),
            "manifest": d.get("manifest", ""),
            "required": d.get("required", []),
        })
    return out
