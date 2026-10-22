"""Черновик Tier 1 (32 доменных архетипа) в проектах IT2B и Diademas.

Запуск (в backend-контейнере): python scripts/build_domain_v2_draft.py
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
    # Строительство
    ("BoqSmeta", "Смета <em>раздела</em>", "Ведомость объёмов"),
    ("ObjectPassport", "Паспорт <em>объекта</em>", "Ключевые ТЭП"),
    ("FloorPlanZones", "Зоны <em>на плане</em>", "Площади и стоимость"),
    ("HandoverMatrix", "Матрица <em>сдачи</em>", "Этажи × системы"),
    ("SnagBoard", "Реестр <em>замечаний</em>", "Punch-list"),
    ("SafetyDashboard", "Охрана <em>труда</em>", "Leading и lagging"),
    ("SiteLogisticsMap", "Стройгенплан и <em>логистика</em>", "Объекты и потоки"),
    ("ChangeOrderLog", "Журнал <em>изменений</em>", "Бюджет и сроки"),
    # Образование
    ("LearningObjectives", "Цели <em>обучения</em>", "Формула ABCD"),
    ("BloomLadder", "Лестница <em>Блума</em>", "Шесть уровней"),
    ("LessonArc", "Дуга <em>урока</em>", "Фазы и тайминг"),
    ("CurriculumMap", "Карта <em>программы</em>", "Курсы × результаты"),
    ("AssessmentBlueprint", "Спецификация <em>теста</em>", "Стандарт и баллы"),
    ("ItemAnalysis", "Анализ <em>заданий</em>", "Сложность и дискриминация"),
    ("StudentGrowth", "Динамика <em>роста</em>", "Срезы и цель"),
    ("TimetableGrid", "Сетка <em>расписания</em>", "Неделя × пара"),
    # Промышленность
    ("OeeDashboard", "Эффективность <em>оборудования</em>", "OEE = A×P×Q"),
    ("PaceBoard", "Темп <em>смены</em>", "План и факт"),
    ("ShiftHandover", "Сменный <em>отчёт</em>", "Выпуск и простои"),
    ("YamazumiBalance", "Балансировка <em>линии</em>", "Элементы и такт"),
    ("ValueStreamMap", "Поток <em>ценности</em>", "VA и lead time"),
    ("MachineStatusBoard", "Статусы <em>оборудования</em>", "MTBF и MTTR"),
    ("MaintenanceBoard", "Доска <em>ТОиР</em>", "ППР и заявки"),
    ("AbcXyzMatrix", "ABC/XYZ <em>матрица</em>", "Ценность и спрос"),
    # B2B
    ("PipelineBoard", "Воронка <em>пайплайна</em>", "Стадии и покрытие"),
    ("MarketSizing", "Объём <em>рынка</em>", "TAM / SAM / SOM"),
    ("RevenueWaterfall", "Мост <em>выручки</em>", "New → churn"),
    ("CohortRetention", "Когортное <em>удержание</em>", "NRR и GRR"),
    ("OrgChart", "Оргструктура <em>компании</em>", "Роли и штат"),
    ("UnitEconomics", "Юнит-<em>экономика</em>", "CAC, LTV, payback"),
    ("UseOfFunds", "Распределение <em>инвестиций</em>", "Направления и вехи"),
    ("JourneyMap", "Путь <em>клиента</em>", "Стадии и боли"),
]

PROJECTS = [
    {"title": "Демо: Tier 1 доменные (IT2B)", "folder_id": 3, "variant": "tech"},
    {"title": "Демо: Tier 1 доменные (Diademas)", "folder_id": 24, "variant": "diademas"},
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
            src = comps[slug].get("example") or comps[slug].get("default_payload") or {}
            payload = copy.deepcopy(src)
            payload["variant"] = proj["variant"]
            payload.pop("title", None)
            payload.pop("subtitle", None)
            v = api("POST", f"/components/{slug}/validate?lint=true", {"payload": payload})
            if not v.get("valid"):
                raise SystemExit(f"invalid {slug}: {v.get('errors')}")
            api("POST", f"/presentations/{pid}/slides", {
                "slide_id": f"t1-{pid}-{slug}", "component": slug,
                "start_time": START_OFFSET + idx * STEP_MS, "order_index": idx,
                "title": s_title, "subtitle": s_sub, "data": {"payload": payload},
            })
        marker_t = START_OFFSET + len(SLIDES) * STEP_MS + 3000
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"t1-{pid}-end", "component": "EndMarkerSlide",
            "start_time": marker_t, "order_index": 999, "title": "", "subtitle": "",
            "data": {"payload": {}},
        })
        print(f"  /p/{pid} — {proj['title']}")
        made.append(pid)
    print("ГОТОВО:", made)


if __name__ == "__main__":
    main()
