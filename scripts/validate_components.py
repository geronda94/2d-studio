import json
import os
import sys
import requests

from backend.database import SessionLocal
from backend import models

BASE = "http://localhost:8000"
H = {"X-Internal-Token": os.environ.get("INTERNAL_API_TOKEN", "")}

db = SessionLocal()
bad = 0
total = 0
for slug in sys.argv[1:]:
    comp = db.query(models.Component).filter(models.Component.slug == slug).first()
    if not comp:
        print(f"{slug}: NOT FOUND")
        bad += 1
        continue
    for label, payload in (("default", comp.default_payload or {}), ("example", comp.example or {})):
        if not payload:
            continue
        total += 1
        r = requests.post(f"{BASE}/components/{slug}/validate?strict=true&lint=true",
                          headers=H, json={"payload": payload}, timeout=30)
        d = r.json()
        errs = d.get("errors", [])
        warns = d.get("warnings", [])
        ok = d.get("valid") and not errs
        if not ok:
            bad += 1
        print(f"{slug:22} {label:8} {'OK' if ok else 'FAIL'} e={len(errs)} w={len(warns)}")
        for e in errs[:5]:
            print(f"    ERR {e.get('path')}: {e.get('message')}")
        for w in warns[:5]:
            print(f"    WARN {w.get('path')}: {w.get('message')}")

print(f"\nDONE blocks={total} bad={bad}")
