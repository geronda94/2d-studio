"""Демо CharacterStats: один персонаж + группа. Diademas, folder 24."""
import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
from scripts import _api_auth  # noqa: F401,E402

BASE = os.environ.get("API_BASE", "http://localhost:8002")
TITLE = "Демо: Персонаж со статами (Diademas)"

GROUP = {
    "variant": "diademas",
    "mode": "group",
    "max_stat": 10,
    "show_values": True,
    "source_note": "Шкалы условны и отражают житийные свидетельства",
    "characters": [
        {"id": "peter", "name": "Ап. Пётр", "subtitle": "Камень веры", "image": "", "color": "var(--item-accent-1)", "start_time": 0,
         "stats": [{"label": "Вера", "value": 9, "icon": "lucide:anchor"}, {"label": "Проповедь", "value": 10, "icon": "lucide:megaphone"}, {"label": "Смирение", "value": 7, "icon": "lucide:feather"}],
         "traits": [{"label": "Первоапостол", "icon": "lucide:key"}]},
        {"id": "paul", "name": "Ап. Павел", "subtitle": "Апостол языков", "image": "", "color": "var(--item-accent-2)", "start_time": 1000,
         "stats": [{"label": "Ревность", "value": 10, "icon": "lucide:flame"}, {"label": "Богословие", "value": 10, "icon": "lucide:book-open"}, {"label": "Смирение", "value": 8, "icon": "lucide:feather"}],
         "traits": [{"label": "Миссионер", "icon": "lucide:map"}]},
        {"id": "john", "name": "Ап. Иоанн", "subtitle": "Апостол любви", "image": "", "color": "var(--item-accent-3)", "start_time": 2000,
         "stats": [{"label": "Любовь", "value": 10, "icon": "lucide:heart"}, {"label": "Прозорливость", "value": 9, "icon": "lucide:eye"}, {"label": "Смирение", "value": 9, "icon": "lucide:feather"}],
         "traits": [{"label": "Тайновидец", "icon": "lucide:scroll"}]},
    ],
}


def api(method, path, body=None):
    fn = getattr(requests, method.lower())
    r = fn(BASE + path, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else None


def main():
    comps = {c["slug"]: c for c in api("GET", "/components/")}
    for p in (api("GET", "/presentations/") or []):
        if p.get("title") == TITLE:
            api("DELETE", f"/presentations/{p['id']}")
    pid = api("POST", "/presentations/", {"title": TITLE, "folder_id": 24})["id"]

    slides = [
        ("single", copy.deepcopy(comps["CharacterStats"]["default_payload"]), "Персонаж и <em>статы</em>", "Один герой крупно"),
        ("group", GROUP, "Собор <em>апостолов</em>", "Группа людей сеткой"),
    ]
    for i, (key, payload, title, sub) in enumerate(slides):
        payload["variant"] = "diademas"
        v = api("POST", "/components/CharacterStats/validate?lint=true", {"payload": payload})
        if not v.get("valid"):
            raise SystemExit(f"invalid {key}: {v.get('errors')}")
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"char-{pid}-{key}", "component": "CharacterStats",
            "start_time": 500 + i * 6000, "order_index": i,
            "title": title, "subtitle": sub, "data": {"payload": payload},
        })
    api("POST", f"/presentations/{pid}/slides", {
        "slide_id": f"char-{pid}-end", "component": "EndMarkerSlide",
        "start_time": 500 + len(slides) * 6000 + 3000, "order_index": 999,
        "title": "", "subtitle": "", "data": {"payload": {}},
    })
    print(f"  /p/{pid} — {TITLE}")


if __name__ == "__main__":
    main()
