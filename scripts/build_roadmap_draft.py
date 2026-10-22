"""Черновики «Roadmap-компоненты» для демонстрации 18 новых компонентов.

Собирает по одной презентации в проекте IT2B (папка drafts) и Diademas
(папка drafts-diademas): по одному слайду на каждый новый компонент + EndMarkerSlide.

Запуск (в backend-контейнере):
    python scripts/build_roadmap_draft.py
"""
import os
import sys
import copy
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
import _api_auth  # noqa: F401,E402  (сайд-эффект: X-Internal-Token)

BASE = os.environ.get("API_BASE", "http://localhost:8001")
STEP_MS = 6000
START_OFFSET = 500

# (slug, slide title, subtitle) — порядок = порядок слайдов
SLIDES = [
    # P1
    ("SpecTable", "Спецификация <em>решения</em>", "Таблица параметров"),
    ("KpiDashboard", "Ключевые <em>метрики</em>", "Дашборд показателей"),
    ("GanttChart", "План <em>запуска</em>", "Диаграмма Ганта"),
    ("TeamGrid", "Команда <em>проекта</em>", "Кто ведёт внедрение"),
    ("PricingTable", "Тарифы <em>и пакеты</em>", "Выбор под задачу"),
    # P2
    ("FlashCards", "Проверьте <em>себя</em>", "Флэш-карточки"),
    ("QuizSlide", "Что снижает <em>галлюцинации</em>?", "Викторина"),
    ("StepByStep", "Как мы <em>запускаем</em> агента", "Пошаговый процесс"),
    ("DefinitionBlock", "Что такое <em>векторный поиск</em>", "Определение"),
    ("KnowledgeGraph", "Карта <em>связей</em>", "Граф знаний"),
    # P3
    ("TimelineEras", "Эпохи <em>развития</em>", "От механизации к ИИ"),
    ("QuoteCard", "Цитата <em>дня</em>", "Мысль о будущем"),
    ("MapVisualization", "География <em>клиентов</em>", "Точки и связи"),
    ("HistoricalCompare", "Как было и <em>как стало</em>", "До и после"),
    # P4
    ("CircularGauge", "Прогресс <em>внедрения</em>", "Круговые метрики"),
    ("SustainabilityTimeline", "Путь к <em>устойчивости</em>", "Этапы перехода"),
    ("ValuesTable", "Наши <em>ценности</em>", "Практика и результат"),
    ("OrganicGrid", "Направления <em>работы</em>", "Органическая сетка"),
]

PROJECTS = [
    {"title": "Демо: 18 новых компонентов (IT2B)", "folder_id": 3, "variant": "tech"},
    {"title": "Демо: 18 новых компонентов (Diademas)", "folder_id": 24, "variant": "diademas"},
]


def api(method, path, body=None):
    # Вызываем метод-специфичные обёртки requests.* — _api_auth патчит именно их
    # (добавляет X-Internal-Token и переписывает :8001 → :8000 внутри контейнера).
    fn = getattr(requests, method.lower())
    r = fn(BASE + path, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else None


def main():
    comps = {c["slug"]: c for c in api("GET", "/components/")}
    missing = [s for s, _, _ in SLIDES if s not in comps]
    if missing:
        raise SystemExit(f"нет компонентов в БД: {missing}")

    created = []
    for proj in PROJECTS:
        title = proj["title"]
        # архивируем прежний такой же черновик
        for p in (api("GET", "/presentations/") or []):
            if p.get("title") == title:
                try:
                    api("DELETE", f"/presentations/{p['id']}")
                except Exception as e:
                    print("warn archive:", e)

        pres = api("POST", "/presentations/", {"title": title, "folder_id": proj["folder_id"]})
        pid = pres["id"]
        print(f"\n== {title} (id={pid})")

        for idx, (slug, s_title, s_sub) in enumerate(SLIDES):
            payload = copy.deepcopy(comps[slug].get("default_payload") or {})
            payload["variant"] = proj["variant"]
            # не дублировать заголовок: он уже на слайде
            payload.pop("title", None)
            payload.pop("subtitle", None)

            v = api("POST", f"/components/{slug}/validate?lint=true", {"payload": payload})
            if not v.get("valid"):
                raise SystemExit(f"invalid {slug}: {v.get('errors')}")

            body = {
                "slide_id": f"roadmap-{pid}-{slug}",
                "component": slug,
                "start_time": START_OFFSET + idx * STEP_MS,
                "order_index": idx,
                "title": s_title,
                "subtitle": s_sub,
                "data": {"payload": payload},
            }
            api("POST", f"/presentations/{pid}/slides", body)
            print(f"  + {slug:24s} @ {body['start_time']}ms")

        marker_t = START_OFFSET + len(SLIDES) * STEP_MS + 3000
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"roadmap-{pid}-end",
            "component": "EndMarkerSlide",
            "start_time": marker_t,
            "order_index": 999,
            "title": "",
            "subtitle": "",
            "data": {"payload": {}},
        })
        print(f"  + EndMarkerSlide @ {marker_t}ms  ->  /p/{pid}")
        created.append((title, pid))

    print("\nГОТОВО:")
    for t, pid in created:
        print(f"  /p/{pid}  — {t}")


if __name__ == "__main__":
    main()
