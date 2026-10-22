"""QA-презентации для проверки новых компонентов в разных темах/вариантах.

Создаёт по презентации с 18 новыми компонентами для каждого варианта:
  classic     → проект history  (папка 5), тёмная/светлая бумажная тема
  derevnya    → проект derevnya (папка 6), эко-тема
  industrial  → проект it2b     (папка 3)
  educational → проект it2b     (папка 3)

Запуск (в backend-контейнере): python scripts/build_variant_qa.py
"""
import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
import _api_auth  # noqa: F401,E402

BASE = os.environ.get("API_BASE", "http://localhost:8002")
STEP_MS = 6000
START_OFFSET = 500

SLIDES = [
    ("SpecTable", "Спецификация <em>решения</em>", "Таблица параметров"),
    ("KpiDashboard", "Ключевые <em>метрики</em>", "Дашборд показателей"),
    ("GanttChart", "План <em>запуска</em>", "Диаграмма Ганта"),
    ("TeamGrid", "Команда <em>проекта</em>", "Кто ведёт внедрение"),
    ("PricingTable", "Тарифы <em>и пакеты</em>", "Выбор под задачу"),
    ("FlashCards", "Проверьте <em>себя</em>", "Флэш-карточки"),
    ("QuizSlide", "Что снижает <em>галлюцинации</em>?", "Викторина"),
    ("StepByStep", "Как мы <em>запускаем</em> агента", "Пошаговый процесс"),
    ("DefinitionBlock", "Что такое <em>векторный поиск</em>", "Определение"),
    ("KnowledgeGraph", "Карта <em>связей</em>", "Граф знаний"),
    ("TimelineEras", "Эпохи <em>развития</em>", "От механизации к ИИ"),
    ("QuoteCard", "Цитата <em>дня</em>", "Мысль о будущем"),
    ("MapVisualization", "География <em>клиентов</em>", "Точки и связи"),
    ("HistoricalCompare", "Как было и <em>как стало</em>", "До и после"),
    ("CircularGauge", "Прогресс <em>внедрения</em>", "Круговые метрики"),
    ("SustainabilityTimeline", "Путь к <em>устойчивости</em>", "Этапы перехода"),
    ("ValuesTable", "Наши <em>ценности</em>", "Практика и результат"),
    ("OrganicGrid", "Направления <em>работы</em>", "Органическая сетка"),
]

TARGETS = [
    {"variant": "classic", "folder_id": 5, "title": "QA: 18 новых компонентов (history · classic)"},
    {"variant": "derevnya", "folder_id": 6, "title": "QA: 18 новых компонентов (derevnya · eco)"},
    {"variant": "industrial", "folder_id": 3, "title": "QA: 18 новых компонентов (it2b · industrial)"},
    {"variant": "educational", "folder_id": 3, "title": "QA: 18 новых компонентов (it2b · educational)"},
]


def api(method, path, body=None):
    fn = getattr(requests, method.lower())
    r = fn(BASE + path, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else None


def main():
    comps = {c["slug"]: c for c in api("GET", "/components/")}
    out = []
    for t in TARGETS:
        for p in (api("GET", "/presentations/") or []):
            if p.get("title") == t["title"]:
                try:
                    api("DELETE", f"/presentations/{p['id']}")
                except Exception as e:
                    print("warn archive:", e)
        pres = api("POST", "/presentations/", {"title": t["title"], "folder_id": t["folder_id"]})
        pid = pres["id"]
        for idx, (slug, s_title, s_sub) in enumerate(SLIDES):
            payload = copy.deepcopy(comps[slug].get("default_payload") or {})
            payload["variant"] = t["variant"]
            payload.pop("title", None)
            payload.pop("subtitle", None)
            v = api("POST", f"/components/{slug}/validate?lint=true", {"payload": payload})
            if not v.get("valid"):
                raise SystemExit(f"invalid {slug}/{t['variant']}: {v.get('errors')}")
            api("POST", f"/presentations/{pid}/slides", {
                "slide_id": f"qa-{t['variant']}-{pid}-{slug}",
                "component": slug,
                "start_time": START_OFFSET + idx * STEP_MS,
                "order_index": idx,
                "title": s_title,
                "subtitle": s_sub,
                "data": {"payload": payload},
            })
        marker_t = START_OFFSET + len(SLIDES) * STEP_MS + 3000
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"qa-{t['variant']}-{pid}-end",
            "component": "EndMarkerSlide",
            "start_time": marker_t,
            "order_index": 999,
            "title": "", "subtitle": "", "data": {"payload": {}},
        })
        print(f"{t['variant']:12s} -> /p/{pid}  ({t['title']})")
        out.append((t["variant"], pid))
    print("\nГОТОВО:", out)


if __name__ == "__main__":
    main()
