#!/usr/bin/env python3
"""Сборка Шортс_10 «Почему кастомный код дешевле nocode» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_10 — Почему кастомный код дешевле nocode на дистанции.txt"
TITLE = "10 - Почему кастомный код дешевле nocode"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s10_01", "hook", "InfographicCards", "«Бесплатный» <em>конструктор</em>", "через год — $500 в месяц", {"variant": "tech", "items": [
        {"id": 1, "label": "Конструктор", "value": "$0", "trend": "на старте", "color": A1, "icon": "heroicons:gift", "start_time": 0},
        {"id": 2, "label": "Подписка", "value": "$500", "trend": "через год", "color": A2, "icon": "heroicons:banknotes", "start_time": 800},
        {"id": 3, "label": "Операции", "value": "10 000", "trend": "и растут", "color": A3, "icon": "heroicons:bolt", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "$18 000", "trend": "за три года", "color": A4, "icon": "heroicons:calendar-days", "start_time": 2400}]}),
    ("s10_02", "most", "ComparisonTable", "Экономия на <em>старте</em>", "счёт выставляет платформа", {"variant": "tech", "headers": ["", "Старт", "Рост"], "items": [
        {"id": "r1", "label": "Экономия выглядит умной", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Копейки за операции", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Счёт выставляет платформа", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Растут операции", "values": [False, True], "start_time": 2400}]}),
    ("s10_03", "proof", "CrmCardSlide", "Онлайн-школа <em>на Make</em>", "сначала копейки", {"variant": "tech", "customer": {"name": "Школа B2B-курсов", "avatar_text": "M", "id_text": "сценарий #make", "status": "растёт"},
        "fields": [
            {"label": "ПЛАТФОРМА", "value": "Make", "field_icon": "heroicons:bolt", "field_color": "brand-blue", "start_time": 300},
            {"label": "ВОРОНКА", "value": "работает", "field_icon": "heroicons:funnel", "field_color": "brand-green", "start_time": 1100},
            {"label": "ОПЕРАЦИИ", "value": "10 000", "field_icon": "heroicons:arrow-trending-up", "field_color": "brand-amber", "start_time": 1900},
            {"label": "СЧЁТ", "value": "$500", "field_icon": "heroicons:banknotes", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Добавить акцию", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Расширить лимит", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s10_04", "proof", "StatsBarChart", "Операции <em>выросли</em>", "подписка догнала", {"variant": "tech", "base_color": "var(--brand-blue)", "peak_color": "var(--brand-amber)", "data": [
        {"label": "Мес 1", "value": 200, "start_time": 0},
        {"label": "Мес 2", "value": 900, "start_time": 900},
        {"label": "Мес 3", "value": 2500, "start_time": 1800},
        {"label": "Мес 4", "value": 4800, "start_time": 2700},
        {"label": "Мес 5", "value": 7500, "start_time": 3600},
        {"label": "Мес 6", "value": 10000, "highlight": True, "start_time": 4500}]}),
    ("s10_05", "proof", "PremiumChecklist", "Что тянет <em>счёт</em>", "на росте операций", {"variant": "tech", "items": [
        {"label": "Сценарий на каждую акцию", "desc": "новая строка в счёте", "icon": "heroicons:rocket-launch", "color": A2, "start_time": 0},
        {"label": "Лимиты операций", "desc": "перерасход по тарифу", "icon": "lucide:gauge", "color": A3, "start_time": 800},
        {"label": "Абонентка платформы", "desc": "$500 каждый месяц", "icon": "heroicons:banknotes", "color": A4, "start_time": 1600}]}),
    ("s10_06", "proof", "ArchitectureDiagram", "Путь <em>заявки</em>", "четыре шага", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заявка", "subtitle": "реклама", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["tbl"]},
        {"id": "tbl", "title": "Таблица", "subtitle": "данные", "icon": "lucide:table", "color": "chart-2", "start_time": 800, "is_main": False, "to": ["mail"]},
        {"id": "mail", "title": "Письмо", "subtitle": "клиенту", "icon": "lucide:mail", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["slack"]},
        {"id": "slack", "title": "Slack", "subtitle": "уведомление", "icon": "lucide:message-square", "color": "chart-6", "start_time": 2400, "is_main": True, "to": []}]}),
    ("s10_07", "proof", "ReceiptCard", "", "", {"variant": "tech", "title": "ПОДПИСКА", "subtitle": "Make", "currency": "$", "total_text": "ЗА 3 ГОДА", "footer_text": "ЗА АРЕНДУ СЧЁТЧИКА", "total_start_time": 2600, "items": [
        {"name": "Год 1", "price": 6000, "start_time": 300},
        {"name": "Год 2", "price": 6000, "start_time": 1100},
        {"name": "Год 3", "price": 6000, "start_time": 1900}]}),
    ("s10_08", "proof", "ComparisonTable", "Make или <em>свой сервер</em>", "считаем на дистанции", {"variant": "tech", "headers": ["", "Свой сервер", "Make"], "items": [
        {"id": "r1", "label": "Цена за операции", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Лимиты и перерасход", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "$500 каждый месяц", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Платишь один раз", "values": [True, False], "start_time": 2400}]}),
    ("s10_09", "proof", "MetricScales", "Дёшево <em>на малом</em>", "дорого на росте", {"variant": "tech", "metrics": [
        {"id": 1, "label": "Операций мало — дёшево", "percentage": 20, "color": "linear-gradient(to right, #22C55E, #4ADE80)", "start_time": 0},
        {"id": 2, "label": "Операций много — счёт растёт", "percentage": 100, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 800},
        {"id": 3, "label": "Свой контур — фикс", "percentage": 5, "color": "linear-gradient(to right, #3B82F6, #60A5FA)", "start_time": 1600}]}),
    ("s10_10", "payoff", "AnimatedStatsSlide", "Арендуешь <em>счётчик</em>", "свой контур — один раз", {"variant": "tech", "stats": [
        {"label": "Абонентка за 3 года", "value": 18000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Платформа в месяц", "value": 500, "suffix": "$", "color": A4, "icon": "heroicons:credit-card", "start_time": 800},
        {"label": "Шагов в контуре", "value": 4, "suffix": "", "color": A1, "icon": "lucide:route", "start_time": 1600}]}),
    ("s10_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
