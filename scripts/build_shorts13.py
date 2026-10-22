#!/usr/bin/env python3
"""Сборка Шортс_13 «30% заявок приходит ночью» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_13 — 30 процентов заявок приходит ночью и теряется.txt"
TITLE = "13 - 30% заявок приходит ночью"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s13_01", "hook", "InfographicCards", "Заявка в <em>23:40</em>", "отвечать некому", {"variant": "tech", "items": [
        {"id": 1, "label": "Время", "value": "23:40", "trend": "ночь", "color": A1, "icon": "heroicons:clock", "start_time": 0},
        {"id": 2, "label": "Реклама", "value": "Оплачена", "trend": "крутится 24/7", "color": A2, "icon": "heroicons:banknotes", "start_time": 800},
        {"id": 3, "label": "Офис", "value": "Спит", "trend": "никто не ответит", "color": A4, "icon": "heroicons:moon", "start_time": 1600},
        {"id": 4, "label": "Утром", "value": "Поздно", "trend": "купил у другого", "color": A3, "icon": "heroicons:bell-slash", "start_time": 2400}]}),
    ("s13_02", "most", "ComparisonTable", "Клиент <em>остывает</em>", "к утру", {"variant": "tech", "headers": ["", "В 23:40", "К 10 утра"], "items": [
        {"id": "r1", "label": "Горячий клиент", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Готов оставить заявку", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Остыл", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Купил у другого", "values": [False, True], "start_time": 2400}]}),
    ("s13_03", "proof", "QuoteCard", "Голос <em>клиента</em>", "утром", {"variant": "tech",
        "quote": "Мне нужно было ночью. Никто не ответил. Утром я уже заказал в другом месте.",
        "author": "Клиент", "author_title": "оставил заявку в 23:40", "source": "менеджер звонит днём"}),
    ("s13_04", "proof", "CrmCardSlide", "Дистрибьютор <em>расходников</em>", "для лабораторий", {"variant": "tech", "customer": {"name": "Расходники для лабораторий", "avatar_text": "Л", "id_text": "ID: #night-13", "status": "утрачён"},
        "fields": [
            {"label": "СЕГМЕНТ", "value": "Дистрибьютор", "field_icon": "heroicons:building-office", "field_color": "brand-blue", "start_time": 300},
            {"label": "РЕКЛАМА", "value": "24/7", "field_icon": "heroicons:megaphone", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ЗАЯВКА", "value": "23:40", "field_icon": "heroicons:clock", "field_color": "brand-green", "start_time": 1900},
            {"label": "ИТОГ", "value": "У другого", "field_icon": "heroicons:arrow-right-circle", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Ответить ночью", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Взять утром", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s13_05", "proof", "AnimatedStatsSlide", "Ночью <em>30%</em>", "заявок остывает", {"variant": "tech", "stats": [
        {"label": "Заявок приходит ночью", "value": 30, "suffix": "%", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"label": "Часов до ответа", "value": 10, "suffix": "", "color": A4, "icon": "heroicons:clock", "start_time": 800},
        {"label": "Клик сгорел", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:fire", "start_time": 1600}]}),
    ("s13_06", "proof", "ArchitectureDiagram", "Ночная <em>заявка</em>", "и тихий офис", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заявка 23:40", "subtitle": "завсклад в смене", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["chat"]},
        {"id": "chat", "title": "Чат", "subtitle": "офис спит", "icon": "lucide:message-circle", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["morning"]},
        {"id": "morning", "title": "Утро: «актуально?»", "subtitle": "слишком поздно", "icon": "lucide:sun", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["lost"]},
        {"id": "lost", "title": "Клиент у другого", "subtitle": "на приёмке", "icon": "lucide:user-x", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s13_07", "proof", "ChatMockupSlide", "«Вам ещё <em>актуально</em>?»", "в десять утра", {"variant": "tech", "bot_name": "Менеджер", "bot_subtitle": "пишет утром", "bot_avatar": "М", "messages": [
        {"role": "user", "text": "Вам ещё актуально? Готов оформить заказ.", "start_time": 0},
        {"role": "assistant", "text": "Я уже заказал в другом месте.", "start_time": 1500},
        {"role": "user", "text": "Понял. Клиент остыл за ночь.", "start_time": 3000}]}),
    ("s13_08", "proof", "PremiumChecklist", "Что фиксирует <em>агент</em>", "на пике интереса", {"variant": "tech", "items": [
        {"label": "Позиция", "desc": "что нужно клиенту", "icon": "heroicons:cube", "color": "brand-blue", "start_time": 0},
        {"label": "Объём", "desc": "сколько и как срочно", "icon": "heroicons:scale", "color": "brand-amber", "start_time": 800},
        {"label": "Контакт", "desc": "живой номер, не пустой", "icon": "heroicons:user", "color": "brand-green", "start_time": 1600}]}),
    ("s13_09", "proof", "ProcessFunnel", "Ночной <em>маршрут</em>", "от заявки до утра", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Заявка 23:40", "count": 100, "icon": "heroicons:inbox", "color": A1, "start_time": 0},
        {"label": "Агент отвечает", "count": 85, "icon": "heroicons:cpu-chip", "color": A2, "start_time": 800},
        {"label": "Слот на утро", "count": 70, "icon": "heroicons:calendar-days", "color": A3, "start_time": 1600},
        {"label": "Тёплый лид", "count": 55, "icon": "heroicons:sun", "color": A4, "start_time": 2400}]}),
    ("s13_10", "payoff", "AnimatedStatsSlide", "Удержать, <em>не продать</em>", "ночью — только интерес", {"variant": "tech", "stats": [
        {"label": "Удержать интерес", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:bolt", "start_time": 0},
        {"label": "Слот на утро", "value": 1, "suffix": "шаг", "color": A2, "icon": "heroicons:sun", "start_time": 800},
        {"label": "Конфликт без человека", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:exclamation-triangle", "start_time": 1600}]}),
    ("s13_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
        print(f"  OK {sid:<9} {starts[sid]:>6.0f}ms  {comp}")
        ok += 1
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5174/p/{pres_id}")


if __name__ == "__main__":
    main()
