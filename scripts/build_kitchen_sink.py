"""Kitchen-sink: по одному слайду на каждый зарегистрированный компонент (для QA).

Запуск (в backend-контейнере): python scripts/build_kitchen_sink.py
"""
import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
from scripts import _api_auth  # noqa: F401,E402

BASE = os.environ.get("API_BASE", "http://localhost:8002")
TITLE = "QA: kitchen-sink (все компоненты)"
FOLDER_ID = 3
STEP_MS = 6000


def api(method, path, body=None):
    fn = getattr(requests, method.lower())
    r = fn(BASE + path, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:200]}")
    return r.json() if r.text else None


def main():
    comps = [c for c in api("GET", "/components/") if c["slug"] != "EndMarkerSlide"]
    comps.sort(key=lambda c: c["slug"])
    for p in (api("GET", "/presentations/") or []):
        if p.get("title") == TITLE:
            api("DELETE", f"/presentations/{p['id']}")
    pid = api("POST", "/presentations/", {"title": TITLE, "folder_id": FOLDER_ID})["id"]

    idx = 0
    for c in comps:
        payload = copy.deepcopy(c.get("example") or c.get("default_payload") or {})
        payload.pop("title", None)
        payload.pop("subtitle", None)
        v = api("POST", f"/components/{c['slug']}/validate?lint=true", {"payload": payload})
        if not v.get("valid"):
            print("skip invalid", c["slug"], v.get("errors")[:1])
            continue
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"ks-{pid}-{c['slug']}", "component": c["slug"],
            "start_time": 500 + idx * STEP_MS, "order_index": idx,
            "title": c["title"], "subtitle": c["slug"], "data": {"payload": payload},
        })
        idx += 1
    api("POST", f"/presentations/{pid}/slides", {
        "slide_id": f"ks-{pid}-end", "component": "EndMarkerSlide",
        "start_time": 500 + idx * STEP_MS + 3000, "order_index": 9999,
        "title": "", "subtitle": "", "data": {"payload": {}},
    })
    print(f"  /p/{pid} — {TITLE} — slides={idx}")


if __name__ == "__main__":
    main()
