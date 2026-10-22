#!/usr/bin/env python3
"""Сборка Шортс_14 «Утренний созвон с остывшим клиентом» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_2/Шортс_14 — Утренний созвон с остывшим клиентом.txt"
TITLE = "14 - Утренний созвон с остывшим клиентом"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s14_01", "hook", "InfographicCards", "Заявка в <em>час ночи</em>", "утром клиент уже не тот", {"variant": "tech", "items": [
        {"id": 1, "label": "Заявка", "value": "1:00", "trend": "ночи", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"id": 2, "label": "Утром", "value": "Звонок", "trend": "менеджер набирает", "color": A2, "icon": "heroicons:phone", "start_time": 800},
        {"id": 3, "label": "Клиент", "value": "В пробке", "trend": "свои дела", "color": A4, "icon": "heroicons:truck", "start_time": 1600},
        {"id": 4, "label": "Зачем звонил", "value": "Не помнит", "trend": "эмоция ушла", "color": A3, "icon": "heroicons:question-mark-circle", "start_time": 2400}]}),
    ("s14_02", "most", "ComparisonTable", "Клиент <em>остывает</em>", "за ночь", {"variant": "tech", "headers": ["", "Ночью", "Утром"], "items": [
        {"id": "r1", "label": "Горячий клиент", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Помнит, зачем писал", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Остыл", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Ушёл к конкуренту", "values": [False, True], "start_time": 2400}]}),
    ("s14_03", "proof", "QuoteCard", "Голос <em>клиента</em>", "к утру", {"variant": "tech",
        "quote": "До утра никто не ответит. Завтра я уже у конкурента.",
        "author": "Клиент", "author_title": "писал ночью", "source": "утренний звонок"}),
    ("s14_04", "proof", "CrmCardSlide", "Крепкая <em>оптовая</em>", "болезнь роста", {"variant": "tech", "customer": {"name": "Оптовая компания", "avatar_text": "О", "id_text": "ID: #morning-14", "status": "остыл"},
        "fields": [
            {"label": "СЕГМЕНТ", "value": "Опт", "field_icon": "heroicons:building-office", "field_color": "brand-blue", "start_time": 300},
            {"label": "ЗАЯВКА", "value": "1:00", "field_icon": "heroicons:clock", "field_color": "brand-amber", "start_time": 1100},
            {"label": "СДЕЛКА", "value": "$12 000", "field_icon": "heroicons:banknotes", "field_color": "brand-green", "start_time": 1900},
            {"label": "ИТОГ", "value": "После праздников", "field_icon": "heroicons:arrow-right-circle", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Перезвонить утром", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Застолбить слот", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s14_05", "proof", "AnimatedStatsSlide", "Сделка <em>остыла</em>", "за одну ночь", {"variant": "tech", "stats": [
        {"label": "Заявка пришла", "value": 1, "suffix": "ночи", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"label": "Сделка на кону", "value": 12000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Эмоция ушла", "value": 100, "suffix": "%", "color": A4, "icon": "heroicons:face-frown", "start_time": 1600}]}),
    ("s14_06", "proof", "ChatMockupSlide", "Утренний <em>звонок</em>", "клиент уже не тот", {"variant": "tech", "bot_name": "Клиент", "bot_subtitle": "утром", "bot_avatar": "К", "messages": [
        {"role": "user", "text": "Доброе утро! По вашей вчерашней заявке.", "start_time": 0},
        {"role": "assistant", "text": "Я сейчас в пробке, наберите после праздников.", "start_time": 1500},
        {"role": "user", "text": "Вчера же была срочная заявка.", "start_time": 3000}]}),
    ("s14_07", "proof", "ArchitectureDiagram", "Что <em>сломалось</em>", "ночью", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заявка 1:00", "subtitle": "горячая", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["bot"]},
        {"id": "bot", "title": "Старый автоответчик", "subtitle": "молчит", "icon": "lucide:message-circle", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["morning"]},
        {"id": "morning", "title": "Утро: звонок", "subtitle": "слишком поздно", "icon": "lucide:sun", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["cold"]},
        {"id": "cold", "title": "Эмоция ушла", "subtitle": "сделка отложена", "icon": "lucide:snowflake", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s14_08", "proof", "PremiumChecklist", "Что делает <em>агент</em>", "тонко", {"variant": "tech", "items": [
        {"label": "Мгновенно шлёт спецификацию", "desc": "ночью, на пике", "icon": "heroicons:document-text", "color": "brand-blue", "start_time": 0},
        {"label": "Мягко ставит созвон", "desc": "застолбить утро", "icon": "heroicons:calendar-days", "color": "brand-amber", "start_time": 800},
        {"label": "Держит интерес тёплым", "desc": "до разговора", "icon": "heroicons:fire", "color": "brand-green", "start_time": 1600}]}),
    ("s14_09", "proof", "ProcessFunnel", "Ночная <em>схема</em>", "интерес заморожен", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Заявка 1:00", "count": 100, "icon": "heroicons:inbox", "color": A1, "start_time": 0},
        {"label": "Спецификация", "count": 85, "icon": "heroicons:document-text", "color": A2, "start_time": 800},
        {"label": "Слот на утро", "count": 70, "icon": "heroicons:calendar-days", "color": A3, "start_time": 1600},
        {"label": "Тёплый лид", "count": 55, "icon": "heroicons:sun", "color": A4, "start_time": 2400}]}),
    ("s14_10", "payoff", "AnimatedStatsSlide", "Сохранить <em>интерес</em>", "до разговора с человеком", {"variant": "tech", "stats": [
        {"label": "Тёплый интерес", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:fire", "start_time": 0},
        {"label": "Слот на утро", "value": 1, "suffix": "шаг", "color": A2, "icon": "heroicons:sun", "start_time": 800},
        {"label": "Сделка не рвётся", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:hand-raised", "start_time": 1600}]}),
    ("s14_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
    print(f"Preview: http://localhost:5175/p/{pres_id}")


if __name__ == "__main__":
    main()
