"""Черновик Tier 0 (10 примитивов) в проектах IT2B и Diademas.

Запуск (в backend-контейнере): python scripts/build_tier0_draft.py
"""
import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
import _api_auth  # noqa: F401,E402

BASE = os.environ.get("API_BASE", "http://localhost:8001")
STEP_MS = 6000
START_OFFSET = 500

SLIDES = [
    ("ParetoChart", "Причины <em>простоев</em>", "Правило 80/20"),
    ("WaterfallChart", "Мост <em>выручки</em>", "Q1 → Q2"),
    ("SCurve", "Сроки и <em>бюджет</em>", "Освоенный объём · SPI/CPI"),
    ("ControlChart", "Стабильность <em>процесса</em>", "Контрольная карта"),
    ("RadarProfile", "Профиль <em>компетенций</em>", "Мы и рынок"),
    ("HeatmapMatrix", "Карта <em>рисков</em>", "Вероятность × срок"),
    ("QuadrantMatrix", "Что делать <em>первым</em>", "Эффект и простота"),
    ("CohortGrid", "Удержание по <em>когортам</em>", "Retention"),
    ("NodeFlow", "Цепочка <em>производства</em>", "Поток и статусы"),
    ("NotationTable", "Смета <em>раздела</em>", "Группы и итоги"),
]

PROJECTS = [
    {"title": "Демо: Tier 0 примитивы (IT2B)", "folder_id": 3, "variant": "tech"},
    {"title": "Демо: Tier 0 примитивы (Diademas)", "folder_id": 24, "variant": "diademas"},
]


def api(method, path, body=None):
    fn = getattr(requests, method.lower())
    r = fn(BASE + path, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else None


def main():
    comps = {c["slug"]: c for c in api("GET", "/components/")}
    made = []
    for proj in PROJECTS:
        for p in (api("GET", "/presentations/") or []):
            if p.get("title") == proj["title"]:
                try:
                    api("DELETE", f"/presentations/{p['id']}")
                except Exception as e:
                    print("warn archive:", e)
        pres = api("POST", "/presentations/", {"title": proj["title"], "folder_id": proj["folder_id"]})
        pid = pres["id"]
        for idx, (slug, s_title, s_sub) in enumerate(SLIDES):
            payload = copy.deepcopy(comps[slug].get("default_payload") or {})
            payload["variant"] = proj["variant"]
            payload.pop("title", None)
            payload.pop("subtitle", None)
            v = api("POST", f"/components/{slug}/validate?lint=true", {"payload": payload})
            if not v.get("valid"):
                raise SystemExit(f"invalid {slug}: {v.get('errors')}")
            api("POST", f"/presentations/{pid}/slides", {
                "slide_id": f"tier0-{pid}-{slug}", "component": slug,
                "start_time": START_OFFSET + idx * STEP_MS, "order_index": idx,
                "title": s_title, "subtitle": s_sub, "data": {"payload": payload},
            })
        marker_t = START_OFFSET + len(SLIDES) * STEP_MS + 3000
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"tier0-{pid}-end", "component": "EndMarkerSlide",
            "start_time": marker_t, "order_index": 999, "title": "", "subtitle": "",
            "data": {"payload": {}},
        })
        print(f"  /p/{pid} — {proj['title']}")
        made.append(pid)
    print("ГОТОВО:", made)


if __name__ == "__main__":
    main()
