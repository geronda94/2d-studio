#!/usr/bin/env python3
"""Сборка Шортс_11 «Клиент ушёл из-за формы» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_11 — Клиент ушел к конкуренту потому что форма на сайте висела 10 секунд.txt"
TITLE = "11 - Клиент ушёл из-за формы на 10 секунд"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s11_01", "hook", "InfographicCards", "Заявка на <em>$5 000</em>", "и тишина в ответ", {"variant": "tech", "items": [
        {"id": 1, "label": "Клиент", "value": "$5 000", "trend": "заполнил заявку", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "Действие", "value": "Отправить", "trend": "нажал кнопку", "color": A2, "icon": "heroicons:cursor-arrow-rays", "start_time": 800},
        {"id": 3, "label": "Ответ", "value": "Ничего", "trend": "сайт молчит", "color": A4, "icon": "heroicons:bell-slash", "start_time": 1600},
        {"id": 4, "label": "Тишина", "value": "10 сек", "trend": "слишком долго", "color": A3, "icon": "heroicons:clock", "start_time": 2400}]}),
    ("s11_02", "most", "ComparisonTable", "Кнопка <em>молчит</em>", "и в аналитике «успех»", {"variant": "tech", "headers": ["", "Должно", "Факт"], "items": [
        {"id": "r1", "label": "Подтверждение за 0,5 сек", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Экран «заявка принята»", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Пуш менеджеру", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "В аналитике «успешно»", "values": [False, True], "start_time": 2400}]}),
    ("s11_03", "proof", "QuoteCard", "Голос <em>клиента</em>", "после клика", {"variant": "tech",
        "quote": "Нажал — и тишина. Меня тут не ждут.",
        "author": "Клиент", "author_title": "заполнил форму", "source": "закрывает вкладку"}),
    ("s11_04", "proof", "CrmCardSlide", "Дистрибьютор <em>запчастей</em>", "дорогие лиды", {"variant": "tech", "customer": {"name": "Запчасти для станков", "avatar_text": "Д", "id_text": "ID: #lead-11", "status": "ушёл"},
        "fields": [
            {"label": "СЕГМЕНТ", "value": "Дистрибьютор", "field_icon": "heroicons:truck", "field_color": "brand-blue", "start_time": 300},
            {"label": "ЛИДЫ", "value": "Дорогие", "field_icon": "heroicons:banknotes", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ЗАЯВКА", "value": "$5 000", "field_icon": "heroicons:document-text", "field_color": "brand-green", "start_time": 1900},
            {"label": "ИТОГ", "value": "К конкуренту", "field_icon": "heroicons:arrow-right-circle", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Показать экран", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Дать ответ", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s11_05", "proof", "AnimatedStatsSlide", "Десять <em>секунд</em> тишины", "и вкладка закрыта", {"variant": "tech", "stats": [
        {"label": "Тишина", "value": 10, "suffix": "сек", "color": A3, "icon": "heroicons:clock", "start_time": 0},
        {"label": "Терпение клиента", "value": 1, "suffix": "сек", "color": A4, "icon": "heroicons:hourglass", "start_time": 800},
        {"label": "Заявок потеряно", "value": 1, "suffix": "", "color": A1, "icon": "heroicons:user-minus", "start_time": 1600}]}),
    ("s11_06", "proof", "ArchitectureDiagram", "Что <em>произошло</em>", "по шагам", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клик", "subtitle": "отправить", "icon": "lucide:mouse-pointer-click", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["load"]},
        {"id": "load", "title": "Лоадер", "subtitle": "крутится", "icon": "lucide:loader", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["silent"]},
        {"id": "silent", "title": "Тишина 10 сек", "subtitle": "нет ответа", "icon": "lucide:timer", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["gone"]},
        {"id": "gone", "title": "Вкладка закрыта", "subtitle": "клиент ушёл", "icon": "lucide:x", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s11_07", "proof", "ReceiptCard", "", "", {"variant": "tech", "title": "ЗАЯВКА", "subtitle": "$5 000", "currency": "$", "total_text": "ПОТЕРЯНО", "footer_text": "КНОПКА МОЛЧАЛА", "total_start_time": 2600, "items": [
        {"name": "Клиент", "price": 2500, "start_time": 300},
        {"name": "Реклама", "price": 1500, "start_time": 1100},
        {"name": "Доверие", "price": 1000, "start_time": 1900}]}),
    ("s11_08", "proof", "PremiumChecklist", "Что не сделал <em>подрядчик</em>", "прошлый разработчик", {"variant": "tech", "items": [
        {"label": "Экран «заявка принята»", "desc": "клиент видит тишину", "icon": "heroicons:check-circle", "color": "brand-blue", "start_time": 0},
        {"label": "Письмо клиенту", "desc": "подтверждение на почту", "icon": "heroicons:envelope", "color": "brand-amber", "start_time": 800},
        {"label": "Пуш менеджеру", "desc": "телефон уже в почте", "icon": "heroicons:bell", "color": "brand-green", "start_time": 1600}]}),
    ("s11_09", "proof", "ProcessFunnel", "Мой <em>ответ</em> за 0,5с", "экран · письмо · пуш", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Клик", "count": 100, "icon": "heroicons:cursor-arrow-rays", "color": A1, "start_time": 0},
        {"label": "Экран принято", "count": 90, "icon": "heroicons:check-badge", "color": A2, "start_time": 800},
        {"label": "Письмо", "count": 80, "icon": "heroicons:envelope", "color": A3, "start_time": 1600},
        {"label": "Пуш", "count": 70, "icon": "heroicons:bell", "color": A4, "start_time": 2400}]}),
    ("s11_10", "payoff", "AnimatedStatsSlide", "Код он <em>не читает</em>", "он читает тишину", {"variant": "tech", "stats": [
        {"label": "Тишина", "value": 10, "suffix": "сек", "color": A3, "icon": "heroicons:clock", "start_time": 0},
        {"label": "Нужный ответ", "value": 1, "suffix": "сек", "color": A1, "icon": "heroicons:bolt", "start_time": 800},
        {"label": "Читает тишину", "value": 100, "suffix": "%", "color": A4, "icon": "heroicons:message-circle", "start_time": 1600}]}),
    ("s11_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
