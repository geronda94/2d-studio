#!/usr/bin/env python3
"""Сборка Шортс_06 «Что делать когда старая интеграция упала» в проекте IT2B.

Правила: docs/AGENT_PLAYBOOK.md §12 (BGM bgm/0.15/offset 20000/до EndMarker, Outro-эталон,
токены, иконки, ≥800мс, ≥2000мс). Запуск с хоста: python3 scripts/build_shorts06.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_06 — Что делать когда старая интеграция упала а разработчик пропал.txt"
TITLE = "06 - Что делать когда старая интеграция упала"

SLIDES = [
    ("s06_01", "hook", "ArchitectureDiagram", "Заявки есть — <em>продаж нет</em>", "цепочка оборвалась", {
        "variant": "tech", "show_data_flow": True,
        "nodes": [
            {"id": "in1", "title": "Заявки", "subtitle": "с сайта", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["mid"]},
            {"id": "mid", "title": "Скрипт", "subtitle": "Make", "icon": "lucide:workflow", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["out1"]},
            {"id": "out1", "title": "Диспетчер", "subtitle": "молчит", "icon": "lucide:bell-off", "color": "chart-5", "start_time": 1600, "is_main": False, "to": []},
        ]}),
    ("s06_02", "most", "InfographicCards", "Реклама <em>крутится</em>", "а заявки не доходят", {
        "variant": "tech",
        "items": [
            {"id": 1, "label": "Реклама", "value": "Идёт", "trend": "клики списываются", "color": "var(--item-accent-1)", "icon": "heroicons:megaphone", "start_time": 0},
            {"id": 2, "label": "Деньги", "value": "Уходят", "trend": "за трафик", "color": "var(--item-accent-4)", "icon": "heroicons:banknotes", "start_time": 800},
            {"id": 3, "label": "Цепочка", "value": "Порвал", "trend": "один сервис", "color": "var(--item-accent-3)", "icon": "heroicons:link-slash", "start_time": 1600},
            {"id": 4, "label": "Узнал", "value": "Клиент", "trend": "а не система", "color": "var(--item-accent-2)", "icon": "heroicons:face-frown", "start_time": 2400},
        ]}),
    ("s06_03", "proof", "TerminalMockup", "Разбор <em>чужого</em> сценария", "ноль документации", {
        "variant": "tech",
        "commands": [
            {"cmd": "$ open make --scenario lega-flow", "output": "modules: 14\nnames: !!! no-name !!!\nnode #7 -> key: OLD_PROVIDER_KEY (revoked)\ndocs: none", "start_time": 300},
            {"cmd": "$ make --run", "output": "ERROR 401: provider token revoked\nflow: STOPPED\ndeal stuck: 1 (EUR 8000)", "start_time": 2200},
        ]}),
    ("s06_04", "proof", "AnimatedStatsSlide", "Заявка <em>повисла</em>", "тишина вместо звонка", {
        "variant": "tech",
        "stats": [
            {"label": "Заявка", "value": 8000, "suffix": "€", "color": "var(--item-accent-3)", "icon": "lucide:package", "start_time": 0},
            {"label": "Простой", "value": 2, "suffix": "дня", "color": "var(--item-accent-4)", "icon": "lucide:clock", "start_time": 800},
            {"label": "Клиент ушёл", "value": 1, "suffix": "", "color": "var(--item-accent-1)", "icon": "lucide:user-x", "start_time": 1600},
        ]}),
    ("s06_05", "proof", "Roadmap", "Собрал <em>заново</em>", "пять понятных шагов", {
        "variant": "tech",
        "items": [
            {"label": "Форма", "desc": "приём заявки", "icon": "heroicons:document-arrow-up", "color": "chart-1", "start_time": 0},
            {"label": "Проверка", "desc": "валидация данных", "icon": "heroicons:shield-check", "color": "chart-2", "start_time": 800},
            {"label": "Таблица", "desc": "запись сделки", "icon": "heroicons:table-cells", "color": "chart-3", "start_time": 1600},
            {"label": "Telegram", "desc": "карточка диспетчеру", "icon": "heroicons:paper-airplane", "color": "chart-4", "start_time": 2400},
            {"label": "Лог", "desc": "видно, где упало", "icon": "heroicons:list-bullet", "color": "chart-2", "start_time": 3200},
        ]}),
    ("s06_06", "proof", "PremiumChecklist", "Что делает <em>надёжным</em>", "против «пропавшего» автора", {
        "variant": "tech",
        "items": [
            {"label": "Понятные имена", "desc": "модули без «no-name»", "icon": "heroicons:tag", "color": "brand-blue", "start_time": 0},
            {"label": "Логи на шагах", "desc": "видно, где оборвалось", "icon": "heroicons:document-text", "color": "brand-green", "start_time": 800},
            {"label": "Документация", "desc": "понятно не одному человеку", "icon": "heroicons:book-open", "color": "brand-amber", "start_time": 1600},
        ]}),
    ("s06_07", "proof", "StatsBarChart", "Заявки <em>по неделям</em>", "обрыв и восстановление", {
        "variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)",
        "title": "Заявки по неделям", "subtitle": "обрыв и восстановление",
        "data": [
            {"label": "Неделя 1", "value": 45, "start_time": 0},
            {"label": "Обрыв", "value": 4, "start_time": 800},
            {"label": "Починка", "value": 20, "start_time": 1600},
            {"label": "После", "value": 48, "highlight": True, "start_time": 2400},
        ]}),
    ("s06_08", "payoff", "MetricScales", "Кто <em>понимает</em> систему", "зависимость от человека", {
        "variant": "tech", "title": "Кто понимает систему", "subtitle": "зависимость от человека",
        "metrics": [
            {"id": 1, "label": "Понимает автор", "percentage": 100, "color": "linear-gradient(to right, #34D399, #2DD4BF)", "start_time": 0},
            {"id": 2, "label": "Понимает команда", "percentage": 10, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 800},
            {"id": 3, "label": "Риск при уходе", "percentage": 95, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 1600},
        ]}),
    ("s06_09", "cta", "OutroSlide", "", "", {
        "variant": "tech", **IT2B_OUTRO,
    }),
]


def validate(comp, payload):
    r = requests.post(f"{BASE}/components/{comp}/validate", json={"payload": payload})
    r.raise_for_status()
    return r.json()


def compute_times(voice_clips):
    by = {vc["section_id"]: vc for vc in voice_clips}
    key = {"hook": "hook", "most": "most", "proof": "proof", "payoff": "payoff", "cta": "hook_out"}
    counts = {}
    for _, block, *_ in SLIDES:
        counts[block] = counts.get(block, 0) + 1
    starts = {}
    for block, section in key.items():
        clip = by[section]
        n = counts.get(block, 0)
        if not n:
            continue
        step = max(2000, min(5200, int((clip["end_time"] - clip["start_time"]) / n)))
        idx = 0
        for sid, b, *_ in SLIDES:
            if b == block:
                starts[sid] = clip["start_time"] + idx * step
                idx += 1
    ordered = [s[0] for s in SLIDES]
    for i in range(1, len(ordered)):
        starts[ordered[i]] = max(starts[ordered[i]], starts[ordered[i - 1]] + 2000)
    return starts


def main():
    scenario = gs.load_scenario_from_file(SCENARIO_PATH, title=TITLE)
    print(f"Loaded scenario: {scenario['title']} — {len(scenario['sections'])} blocks")
    pres_id, voice_clips = gs.run_pipeline(scenario=scenario)
    normalize_bgm_track(pres_id)

    starts = compute_times(voice_clips)
    print("\n--- Creating slides ---")
    ok, fail = 0, []
    for i, (sid, block, comp, title, sub, payload) in enumerate(SLIDES, start=1):
        res = validate(comp, payload)
        if not res.get("valid"):
            print(f"INVALID {sid} {comp}: {res.get('errors')}")
            fail.append(sid)
            continue
        for w in res.get("warnings", []):
            print(f"  warn {sid}: {w.get('type')} @ {w.get('path')}")
        gs.create_slide(pres_id, sid, comp, starts[sid], i, title=title, subtitle=sub, payload=payload)
        print(f"  OK {sid:<8} {starts[sid]:>6.0f}ms  {comp}")
        ok += 1

    print(f"\nDone: {ok}/{len(SLIDES)} slides. Failed: {fail}")
    print(f"Preview: http://localhost:5174/p/{pres_id}")


if __name__ == "__main__":
    main()
