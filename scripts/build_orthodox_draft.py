"""Демо православного канала (40 компонентов) в проекте Diademas.

Запуск (в backend-контейнере): python scripts/build_orthodox_draft.py
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
    ("VerseFocus", "Слово <em>в начале</em>", "Ин. 1:1"),
    ("ScriptureParallel", "Три <em>перевода</em>", "Синодальный · ЦСЯ · оригинал"),
    ("ParableExplainer", "Притча о <em>сеятеле</em>", "Образ и смысл"),
    ("ProphecyFulfillment", "Пророчество и <em>исполнение</em>", "Ветхий → Новый Завет"),
    ("GenealogyTree", "Родословие <em>Христа</em>", "От Авраама до Иосифа"),
    ("CommandmentBoard", "Заповеди <em>блаженств</em>", "Путь восхождения"),
    ("VirtuesRadar", "Профиль <em>добродетелей</em>", "Подвижник и человек"),
    ("AsceticFeats", "Подвиги <em>аскезы</em>", "Пост, молитва, бдение"),
    ("SaintQuote", "Слово <em>святого</em>", "Изречение и источник"),
    ("RelicsMap", "География <em>святынь</em>", "Монастыри и мощи"),
    ("LawParallel", "Закон <em>духа</em>", "Физика и Писание"),
    ("SeedAndSoil", "Почва <em>сердца</em>", "Притча как модель"),
    ("ScienceFaithParallel", "Наука и <em>вера</em>", "Открытие и Писание"),
    ("CosmologyGenesis", "Свет <em>первый</em>", "Большой взрыв и Шестоднев"),
    ("SacredNumbers", "Числа <em>Писания</em>", "Семь, сорок, двенадцать"),
    ("FineTuningScales", "Тонкая <em>настройка</em>", "Антропный принцип"),
    ("ArchaeologyConfirms", "Археология и <em>Библия</em>", "Находки и подтверждения"),
    ("FigureCard", "Личность в <em>истории</em>", "Эпоха и вклад"),
    ("RulerCompare", "Правители и <em>вера</em>", "Дела и наследие"),
    ("InfluenceMap", "Карта <em>влияния</em>", "Кто на кого повлиял"),
    ("ConceptDiptych", "Два <em>понятия</em>", "Вера и знание"),
    ("ArgumentStructure", "Структура <em>аргумента</em>", "Тезис и вывод"),
    ("ApologeticsQA", "Возражение и <em>ответ</em>", "Апологетика"),
    ("WorldviewMatrix", "Картина <em>мира</em>", "Мировоззрения"),
    ("TheologicalSchools", "Школы <em>богословия</em>", "Акценты и отцы"),
    ("PassionsVirtues", "Страсти и <em>добродетели</em>", "Парные шкалы"),
    ("SoulStructure", "Устроение <em>души</em>", "Ум, воля, чувства"),
    ("StagesOfSin", "Развитие <em>греха</em>", "От помысла к страсти"),
    ("LadderOfVirtues", "Лествица <em>добродетелей</em>", "Восхождение"),
    ("EmotionHealing", "Исцеление <em>чувств</em>", "Состояние и врачество"),
    ("HabitLoop", "Петля <em>привычки</em>", "И духовная замена"),
    ("LoveTypes", "Виды <em>любви</em>", "Агапэ, эрос, филия"),
    ("FamilyOrder", "Порядок <em>семьи</em>", "Роли и основание"),
    ("ReconciliationPath", "Путь <em>примирения</em>", "Шаги"),
    ("ChurchAsBody", "Церковь как <em>тело</em>", "Центр и служения"),
    ("MoralDecline", "Упадок <em>нравов</em>", "Динамика морали"),
    ("ValuesOfEpochs", "Ценности <em>эпох</em>", "Чем жили цивилизации"),
    ("CivilizationCycle", "Цикл <em>цивилизаций</em>", "Подъём и упадок"),
    ("ChristianityImpact", "Влияние <em>христианства</em>", "Было и стало"),
    ("PersecutionWaves", "Волны <em>гонений</em>", "Период и масштаб"),
]

TITLE = "Православный канал: 40 компонентов (Diademas)"
FOLDER_ID = 24
VARIANT = "diademas"


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
            try:
                api("DELETE", f"/presentations/{p['id']}")
            except Exception as e:
                print("warn archive:", e)
    pres = api("POST", "/presentations/", {"title": TITLE, "folder_id": FOLDER_ID})
    pid = pres["id"]
    for idx, (slug, s_title, s_sub) in enumerate(SLIDES):
        src = comps[slug].get("example") or comps[slug].get("default_payload") or {}
        payload = copy.deepcopy(src)
        payload["variant"] = VARIANT
        required = set(comps[slug].get("payload_schema", {}).get("fields", {}).keys())
        req = {k for k, f in comps[slug].get("payload_schema", {}).get("fields", {}).items()
               if isinstance(f, dict) and f.get("required")}
        if "title" not in req:
            payload.pop("title", None)
        if "subtitle" not in req:
            payload.pop("subtitle", None)
        v = api("POST", f"/components/{slug}/validate?lint=true", {"payload": payload})
        if not v.get("valid"):
            raise SystemExit(f"invalid {slug}: {v.get('errors')}")
        api("POST", f"/presentations/{pid}/slides", {
            "slide_id": f"orth-{pid}-{slug}", "component": slug,
            "start_time": START_OFFSET + idx * STEP_MS, "order_index": idx,
            "title": s_title, "subtitle": s_sub, "data": {"payload": payload},
        })
    marker_t = START_OFFSET + len(SLIDES) * STEP_MS + 3000
    api("POST", f"/presentations/{pid}/slides", {
        "slide_id": f"orth-{pid}-end", "component": "EndMarkerSlide",
        "start_time": marker_t, "order_index": 999, "title": "", "subtitle": "",
        "data": {"payload": {}},
    })
    print(f"  /p/{pid} — {TITLE}")


if __name__ == "__main__":
    main()
