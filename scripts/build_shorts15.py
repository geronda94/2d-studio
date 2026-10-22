#!/usr/bin/env python3
"""Сборка Шортс_15 «ИИ квалифицирует клиента лучше стажёра» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_2/Шортс_15 — ИИ квалифицирует клиента лучше стажера.txt"
TITLE = "15 - ИИ квалифицирует клиента лучше стажёра"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s15_01", "hook", "InfographicCards", "Полдня <em>консультаций</em>", "и «я просто приценивался»", {"variant": "tech", "items": [
        {"id": 1, "label": "Менеджер", "value": "Полдня", "trend": "в чате", "color": A1, "icon": "heroicons:chat-bubble-left", "start_time": 0},
        {"id": 2, "label": "Ответ клиента", "value": "Приценивался", "trend": "спасибо, нет", "color": A4, "icon": "heroicons:face-frown", "start_time": 800},
        {"id": 3, "label": "Менеджер", "value": "Выгорает", "trend": "одно и то же", "color": A3, "icon": "heroicons:fire", "start_time": 1600},
        {"id": 4, "label": "Время", "value": "Сгорело", "trend": "без сделки", "color": A2, "icon": "heroicons:clock", "start_time": 2400}]}),
    ("s15_02", "most", "ComparisonTable", "Человек <em>или логика</em>", "первая линия", {"variant": "tech", "headers": ["", "Живой человек", "Машинная логика"], "items": [
        {"id": "r1", "label": "Устаёт к 80-му чату", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Копирует одно и то же", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Держит алгоритм", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Не пропускает оптовика", "values": [False, True], "start_time": 2400}]}),
    ("s15_03", "proof", "QuoteCard", "Голос <em>клиента</em>", "в конце диалога", {"variant": "tech",
        "quote": "Слишком много вопросов. Пойду туда, где посчитают быстрее.",
        "author": "Клиент", "author_title": "устал от расспросов", "source": "уходит к другим"}),
    ("s15_04", "proof", "CrmCardSlide", "Поставщик <em>стройматериалов</em>", "сотня обращений в день", {"variant": "tech", "customer": {"name": "Стройматериалы", "avatar_text": "С", "id_text": "ID: #qual-15", "status": "пропущен"},
        "fields": [
            {"label": "СЕГМЕНТ", "value": "Стройматериалы", "field_icon": "heroicons:building-office", "field_color": "brand-blue", "start_time": 300},
            {"label": "ОБРАЩЕНИЙ ДНЁМ", "value": "100", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ПРОПУЩЕН", "value": "Оптовик", "field_icon": "heroicons:user-minus", "field_color": "brand-green", "start_time": 1900},
            {"label": "СДЕЛКА", "value": "$30 000", "field_icon": "heroicons:banknotes", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Отдать рутину ИИ", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Допуск после фильтра", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s15_05", "proof", "AnimatedStatsSlide", "Сотня <em>обращений</em>", "и один пропуск", {"variant": "tech", "stats": [
        {"label": "Обращений в день", "value": 100, "suffix": "", "color": A1, "icon": "heroicons:chat-bubble-left", "start_time": 0},
        {"label": "Вопросов-шаблон", "value": 3, "suffix": "", "color": A2, "icon": "heroicons:list-bullet", "start_time": 800},
        {"label": "Пропущенная сделка", "value": 30000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 1600}]}),
    ("s15_06", "proof", "ChatMockupSlide", "Как <em>робот</em>", "одни и те же вопросы", {"variant": "tech", "bot_name": "Менеджер", "bot_subtitle": "копирует шаблон", "bot_avatar": "М", "messages": [
        {"role": "user", "text": "Добрый день! Какой у вас бюджет и сроки?", "start_time": 0},
        {"role": "assistant", "text": "Я просто прицениваюсь, спасибо.", "start_time": 1500},
        {"role": "user", "text": "А объём подскажите? Алло?", "start_time": 3000}]}),
    ("s15_07", "proof", "ArchitectureDiagram", "Два <em>этапа</em>", "новая архитектура", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Обращение", "subtitle": "сотни в день", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["bot"]},
        {"id": "bot", "title": "ИИ-бот", "subtitle": "жёсткий алгоритм", "icon": "lucide:bot", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["filter"]},
        {"id": "filter", "title": "Фильтр", "subtitle": "отсекает мусор", "icon": "lucide:funnel", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["mgr"]},
        {"id": "mgr", "title": "Менеджер", "subtitle": "только тёплые", "icon": "lucide:user-check", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s15_08", "proof", "PremiumChecklist", "Три вопроса <em>как робот</em>", "рутина", {"variant": "tech", "items": [
        {"label": "Бюджет", "desc": "всегда первый вопрос", "icon": "heroicons:banknotes", "color": "brand-blue", "start_time": 0},
        {"label": "Сроки", "desc": "копирует из шаблона", "icon": "heroicons:calendar-days", "color": "brand-amber", "start_time": 800},
        {"label": "Объём", "desc": "к 80-му чату забывает", "icon": "heroicons:cube", "color": "brand-green", "start_time": 1600}]}),
    ("s15_09", "proof", "ProcessFunnel", "Что <em>осталось</em>", "в CRM утром", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Сотни обращений", "count": 100, "icon": "heroicons:chat-bubble-left", "color": A1, "start_time": 0},
        {"label": "Фильтр ИИ", "count": 60, "icon": "heroicons:funnel", "color": A2, "start_time": 800},
        {"label": "Тёплые заказчики", "count": 35, "icon": "lucide:user-check", "color": A3, "start_time": 1600},
        {"label": "Допущены к менеджеру", "count": 20, "icon": "heroicons:clipboard-document-check", "color": A4, "start_time": 2400}]}),
    ("s15_10", "payoff", "AnimatedStatsSlide", "Доверять <em>слишком дорого</em>", "уставшему человеку", {"variant": "tech", "stats": [
        {"label": "Машинная логика", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:cpu-chip", "start_time": 0},
        {"label": "Выгорание менеджера", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:fire", "start_time": 800},
        {"label": "Пропущенная сделка", "value": 30000, "suffix": "$", "color": A4, "icon": "heroicons:banknotes", "start_time": 1600}]}),
    ("s15_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
