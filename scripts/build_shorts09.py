#!/usr/bin/env python3
"""Сборка Шортс_09 (обновлённый сценарий) «$500 в месяц за CRM» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_09 — Hubspot за 500 в месяц через 3 года это....txt"
TITLE = "09 - Hubspot за 500 евро в месяц (v2)"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("s09b_01", "hook", "InfographicCards", "$500 в месяц за <em>CRM</em>", "а сделки в WhatsApp", {"variant": "tech", "items": [
        {"id": 1, "label": "Подписка", "value": "$500", "trend": "каждый месяц", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "CRM", "value": "Куплена", "trend": "Hubspot", "color": A2, "icon": "heroicons:circle-stack", "start_time": 800},
        {"id": 3, "label": "Менеджеры", "value": "WhatsApp", "trend": "личный телефон", "color": A4, "icon": "heroicons:chat-bubble-left", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Книжка", "trend": "дорогая и мёртвая", "color": A3, "icon": "heroicons:book-open", "start_time": 2400}]}),
    ("s09b_02", "most", "ComparisonTable", "Платишь за <em>прозрачность</em>", "получаешь книжку", {"variant": "tech", "headers": ["", "Ожидание", "Реальность"], "items": [
        {"id": "r1", "label": "Прозрачность", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Сделки в системе", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Данные у компании", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Дорогая записная книжка", "values": [False, True], "start_time": 2400}]}),
    ("s09b_03", "proof", "CrmCardSlide", "Карточка <em>перегружена</em>", "менеджер не открывает", {"variant": "tech", "customer": {"name": "Сделка в Hubspot", "avatar_text": "H", "id_text": "ID: #9999", "status": "висит"},
        "fields": [
            {"label": "ЭТАПОВ", "value": "10 из 10", "field_icon": "heroicons:queue-list", "field_color": "brand-blue", "start_time": 300},
            {"label": "ОБЯЗ. ПОЛЕЙ", "value": "18", "field_icon": "heroicons:clipboard-document-list", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ИСТОЧНИК", "value": "—", "field_icon": "heroicons:question-mark-circle", "field_color": "brand-blue", "start_time": 1900},
            {"label": "ЗАПОЛНЯЕТ", "value": "для галочки", "field_icon": "heroicons:pencil", "field_color": "brand-amber", "start_time": 2700}],
        "buttons": [
            {"text": "Заполнить всё", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Закрыть", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("s09b_04", "proof", "PremiumChecklist", "Первый месяц <em>красиво</em>", "пока не открыли карточку", {"variant": "tech", "items": [
        {"label": "Воронка", "desc": "этапы настроены", "icon": "heroicons:funnel", "color": "brand-blue", "start_time": 0},
        {"label": "Отчёты", "desc": "графики бодрые", "icon": "heroicons:chart-bar", "color": "brand-amber", "start_time": 800},
        {"label": "Контроль", "desc": "руководство довольно", "icon": "heroicons:eye", "color": "brand-green", "start_time": 1600}]}),
    ("s09b_05", "proof", "ChatMockupSlide", "«В этих <em>макаронах</em>»", "разбираться не буду", {"variant": "tech", "bot_name": "Менеджер", "bot_subtitle": "внутри CRM", "bot_avatar": "М", "messages": [
        {"role": "user", "text": "Карточка сделки в Hubspot, 10 этапов.", "start_time": 0},
        {"role": "assistant", "text": "В этих макаронах разбираться не буду.", "start_time": 1500},
        {"role": "user", "text": "Ок, закрываю в WhatsApp.", "start_time": 3000}]}),
    ("s09b_06", "proof", "ReceiptCard", "", "", {"variant": "tech", "title": "ПОДПИСКА", "subtitle": "Hubspot", "currency": "$", "total_text": "ЗА 3 ГОДА", "footer_text": "ЗА ЗАПИСНУЮ КНИЖКУ", "total_start_time": 2600, "items": [
        {"name": "Год 1", "price": 6000, "start_time": 300},
        {"name": "Год 2", "price": 6000, "start_time": 1100},
        {"name": "Год 3", "price": 6000, "start_time": 1900}]}),
    ("s09b_07", "proof", "ProcessFunnel", "Десять <em>этапов</em>", "заполняют два", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Сделки", "count": 100, "icon": "heroicons:briefcase", "color": A1, "start_time": 0},
        {"label": "Дошли до CRM", "count": 10, "icon": "heroicons:circle-stack", "color": A2, "start_time": 800},
        {"label": "Заполнены честно", "count": 2, "icon": "heroicons:pencil", "color": A3, "start_time": 1600},
        {"label": "Данные компании", "count": 1, "icon": "heroicons:lock-closed", "color": A4, "start_time": 2400}]}),
    ("s09b_08", "proof", "ArchitectureDiagram", "Сделка <em>в телефоне</em>", "у компании нет доступа", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Торг", "subtitle": "в WhatsApp", "icon": "lucide:message-circle", "color": "chart-4", "start_time": 0, "is_main": False, "to": ["phone"]},
        {"id": "phone", "title": "Личный телефон", "subtitle": "герметично", "icon": "lucide:smartphone", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["deal"]},
        {"id": "deal", "title": "Сделка $40 000", "subtitle": "через полгода", "icon": "heroicons:banknotes", "color": "chart-6", "start_time": 1600, "is_main": False, "to": []}]}),
    ("s09b_09", "proof", "MetricScales", "Требует <em>больше</em>", "чем возвращает", {"variant": "tech", "title": "Требует больше", "subtitle": "чем возвращает", "metrics": [
        {"id": 1, "label": "Времени на CRM", "percentage": 100, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 0},
        {"id": 2, "label": "Пользы продавцу", "percentage": 20, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 800},
        {"id": 3, "label": "Выбор быстрого пути", "percentage": 100, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 1600}]}),
    ("s09b_10", "payoff", "AnimatedStatsSlide", "Система <em>мертва</em>", "подписка не лечит", {"variant": "tech", "stats": [
        {"label": "Подписка за 3 года", "value": 18000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Сделка в телефоне", "value": 40000, "suffix": "$", "color": A4, "icon": "lucide:package", "start_time": 800},
        {"label": "Шагов у продавца", "value": 2, "suffix": "", "color": A1, "icon": "lucide:route", "start_time": 1600}]}),
    ("s09b_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
