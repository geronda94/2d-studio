#!/usr/bin/env python3
"""Сборка Шортс_12 «Данные клиентов в WhatsApp» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_12 — Данные клиентов в WhatsApp что с этим не так.txt"
TITLE = "12 - Данные клиентов в WhatsApp"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s12_01", "hook", "InfographicCards", "База в <em>WhatsApp</em>", "и уходит вместе с ним", {"variant": "tech", "items": [
        {"id": 1, "label": "Вся база", "value": "WhatsApp", "trend": "личный", "color": A1, "icon": "heroicons:chat-bubble-left", "start_time": 0},
        {"id": 2, "label": "Менеджеров", "value": "4 человека", "trend": "свои номера", "color": A2, "icon": "heroicons:users", "start_time": 800},
        {"id": 3, "label": "Уходит", "value": "Менеджер", "trend": "к конкуренту", "color": A4, "icon": "heroicons:user-minus", "start_time": 1600},
        {"id": 4, "label": "Забирает", "value": "Телефон", "trend": "с базой внутри", "color": A3, "icon": "heroicons:device-phone-mobile", "start_time": 2400}]}),
    ("s12_02", "most", "ComparisonTable", "Чей <em>телефон</em>", "того и клиент", {"variant": "tech", "headers": ["", "Клиенту", "Компании"], "items": [
        {"id": "r1", "label": "Удобно писать напрямую", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "История переписки", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Доступ к диалогам", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Контроль продаж", "values": [False, True], "start_time": 2400}]}),
    ("s12_03", "proof", "QuoteCard", "Голос <em>клиента</em>", "после ухода менеджера", {"variant": "tech",
        "quote": "Я всегда писал менеджеру лично. Он ушёл — и мой заказ ушёл с ним.",
        "author": "Клиент", "author_title": "оптовый склад", "source": "звонит новый менеджер"}),
    ("s12_04", "proof", "CrmCardSlide", "Оптовый <em>склад</em>", "стройматериалы", {"variant": "tech", "customer": {"name": "Склад стройматериалов", "avatar_text": "С", "id_text": "ID: #acc-12", "status": "потеря"},
        "fields": [
            {"label": "СЕГМЕНТ", "value": "Склад", "field_icon": "heroicons:building-office", "field_color": "brand-blue", "start_time": 300},
            {"label": "МЕНЕДЖЕРОВ", "value": "4", "field_icon": "heroicons:users", "field_color": "brand-amber", "start_time": 1100},
            {"label": "КАНАЛ", "value": "Личные номера", "field_icon": "heroicons:device-phone-mobile", "field_color": "brand-green", "start_time": 1900},
            {"label": "ИТОГ", "value": "Ушёл", "field_icon": "heroicons:arrow-right-circle", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Найти клиента", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Перевести диалог", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s12_05", "proof", "AnimatedStatsSlide", "Три <em>года</em> на личных", "одна мышка — и нет", {"variant": "tech", "stats": [
        {"label": "Менеджеров", "value": 4, "suffix": "", "color": A2, "icon": "heroicons:users", "start_time": 0},
        {"label": "Лет с личных номеров", "value": 3, "suffix": "", "color": A4, "icon": "heroicons:calendar-days", "start_time": 800},
        {"label": "Менеджеров ушло", "value": 1, "suffix": "", "color": A3, "icon": "heroicons:user-minus", "start_time": 1600}]}),
    ("s12_06", "proof", "ChatMockupSlide", "«Мы с Андреем <em>договорились</em>»", "новый менеджер звонит", {"variant": "tech", "bot_name": "Заказчик", "bot_subtitle": "отвечает новому", "bot_avatar": "З", "messages": [
        {"role": "user", "text": "Здравствуйте! Я новый менеджер, по вашему заказу.", "start_time": 0},
        {"role": "assistant", "text": "Мы с Андреем договорились на отсрочку.", "start_time": 1500},
        {"role": "user", "text": "В базе про это ничего нет.", "start_time": 3000}]}),
    ("s12_07", "proof", "ArchitectureDiagram", "База ушла <em>с Андреем</em>", "вместе с телефоном", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заказчик", "subtitle": "три года", "icon": "lucide:user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["phone"]},
        {"id": "phone", "title": "Личный номер", "subtitle": "Андрея", "icon": "lucide:smartphone", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["out"]},
        {"id": "out", "title": "Андрей уходит", "subtitle": "к конкуренту", "icon": "lucide:log-out", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["gone"]},
        {"id": "gone", "title": "Заказчик ушёл", "subtitle": "условия помнит он", "icon": "lucide:user-x", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s12_08", "proof", "PremiumChecklist", "Что уходит <em>с менеджером</em>", "не с компанией", {"variant": "tech", "items": [
        {"label": "История переписки", "desc": "вся коммуникация", "icon": "heroicons:chat-bubble-left", "color": "brand-blue", "start_time": 0},
        {"label": "Договорённости", "desc": "условия и отсрочки", "icon": "heroicons:document-text", "color": "brand-amber", "start_time": 800},
        {"label": "Повторные заказы", "desc": "заказчик идёт за ним", "icon": "heroicons:arrow-path", "color": "brand-green", "start_time": 1600}]}),
    ("s12_09", "proof", "ProcessFunnel", "Диалог <em>в карточке</em>", "телефон больше не сейф", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Личный чат", "count": 100, "icon": "heroicons:chat-bubble-left", "color": A1, "start_time": 0},
        {"label": "WhatsApp API", "count": 85, "icon": "heroicons:link", "color": A2, "start_time": 800},
        {"label": "Карточка сделки", "count": 70, "icon": "heroicons:rectangle-stack", "color": A3, "start_time": 1600},
        {"label": "История у компании", "count": 55, "icon": "heroicons:lock-closed", "color": A4, "start_time": 2400}]}),
    ("s12_10", "payoff", "AnimatedStatsSlide", "В <em>чужом кармане</em>", "значит, не твои продажи", {"variant": "tech", "stats": [
        {"label": "История в чужом кармане", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:hand-raised", "start_time": 0},
        {"label": "Контроль компании", "value": 10, "suffix": "%", "color": A4, "icon": "heroicons:shield-check", "start_time": 800},
        {"label": "Клиент идёт за менеджером", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:user-minus", "start_time": 1600}]}),
    ("s12_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
