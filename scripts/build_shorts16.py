#!/usr/bin/env python3
"""Сборка Шортс_16 «Ошибка: пытаться закрыть сделку ночью» в проекте IT2B."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_2/Шортс_16 — Ошибка пытаться закрыть сделку ночью.txt"
TITLE = "16 - Ошибка: пытаться закрыть сделку ночью"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

SLIDES = [
    ("sh16_01", "hook", "InfographicCards", "Бот <em>давит</em> на клиента", "и сделка сгорает", {"variant": "tech", "items": [
        {"id": 1, "label": "Ночной бот", "value": "Должен спасать", "trend": "лиды", "color": A1, "icon": "heroicons:cpu-chip", "start_time": 0},
        {"id": 2, "label": "На деле", "value": "Давит", "trend": "на клиента", "color": A4, "icon": "heroicons:hand-raised", "start_time": 800},
        {"id": 3, "label": "Ссылка", "value": "На оплату", "trend": "сразу", "color": A3, "icon": "heroicons:credit-card", "start_time": 1600},
        {"id": 4, "label": "Сделка", "value": "$5 000", "trend": "сгорела", "color": A2, "icon": "heroicons:banknotes", "start_time": 2400}]}),
    ("sh16_02", "most", "ComparisonTable", "Спасать <em>или</em> дожимать", "в чём ошибка", {"variant": "tech", "headers": ["", "Должен", "Делает"], "items": [
        {"id": "r1", "label": "Спасать лид", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Удерживать контакт", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Давить ссылкой на оплату", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Пугать напором", "values": [False, True], "start_time": 2400}]}),
    ("sh16_03", "proof", "QuoteCard", "Что говорит <em>бот</em>", "ночью", {"variant": "tech",
        "quote": "Мне сразу ссылку на оплату. Закрою.",
        "author": "Автоматика", "author_title": "давит на клиента", "source": "когда он не готов"}),
    ("sh16_04", "proof", "CrmCardSlide", "Сложный <em>продукт</em>", "чек от $5 000", {"variant": "tech", "customer": {"name": "Сложный продукт", "avatar_text": "П", "id_text": "ID: #push-16", "status": "чёрный список"},
        "fields": [
            {"label": "ПРОДУКТ", "value": "Сложный", "field_icon": "heroicons:cube", "field_color": "brand-blue", "start_time": 300},
            {"label": "ЧЕК", "value": "От $5 000", "field_icon": "heroicons:banknotes", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ВОПРОС", "value": "Ночью", "field_icon": "heroicons:moon", "field_color": "brand-green", "start_time": 1900},
            {"label": "ИТОГ", "value": "Чёрный список", "field_icon": "heroicons:no-symbol", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Ответить мягко", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Столбить звонок", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("sh16_05", "proof", "AnimatedStatsSlide", "Простыня <em>и напор</em>", "вместо ответа", {"variant": "tech", "stats": [
        {"label": "Чек на кону", "value": 5000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Простыня текста", "value": 100, "suffix": "%", "color": A4, "icon": "heroicons:document-text", "start_time": 800},
        {"label": "Контакт потерян", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:user-minus", "start_time": 1600}]}),
    ("sh16_06", "proof", "ChatMockupSlide", "Простой <em>вопрос</em>", "и гигантская простыня", {"variant": "tech", "bot_name": "Заказчик", "bot_subtitle": "пишет ночью", "bot_avatar": "З", "messages": [
        {"role": "user", "text": "Подскажите, есть в наличии?", "start_time": 0},
        {"role": "assistant", "text": "У нас огромные преимущества! Вот ссылка на оплату.", "start_time": 1500},
        {"role": "user", "text": "Слишком напористо. Закрываю чат.", "start_time": 3000}]}),
    ("sh16_07", "proof", "ArchitectureDiagram", "Контакт <em>потерян</em>", "за одну ночь", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Вопрос ночью", "subtitle": "простой", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["spam"]},
        {"id": "spam", "title": "Простыня + оплата", "subtitle": "бездушная автоматика", "icon": "lucide:file-text", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["scared"]},
        {"id": "scared", "title": "Клиент пугается", "subtitle": "закрывает чат", "icon": "lucide:user-x", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["block"]},
        {"id": "block", "title": "Чёрный список", "subtitle": "утром уже поздно", "icon": "lucide:ban", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("sh16_08", "proof", "PremiumChecklist", "Два <em>правила</em>", "новая логика", {"variant": "tech", "items": [
        {"label": "Только базовые вопросы", "desc": "без инициативы", "icon": "heroicons:chat-bubble-left", "color": "brand-blue", "start_time": 0},
        {"label": "Без продажи в лоб", "desc": "никакого давления", "icon": "heroicons:hand-raised", "color": "brand-amber", "start_time": 800},
        {"label": "Слот звонка на утро", "desc": "мягко, но уверенно", "icon": "heroicons:calendar-days", "color": "brand-green", "start_time": 1600}]}),
    ("sh16_09", "proof", "ProcessFunnel", "Что <em>настроил</em>", "вместо дожима", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Вопрос ночью", "count": 100, "icon": "heroicons:inbox", "color": A1, "start_time": 0},
        {"label": "Базовый ответ", "count": 85, "icon": "heroicons:chat-bubble-left", "color": A2, "start_time": 800},
        {"label": "Слот на утро", "count": 70, "icon": "heroicons:calendar-days", "color": A3, "start_time": 1600},
        {"label": "Живой контакт", "count": 55, "icon": "heroicons:sun", "color": A4, "start_time": 2400}]}),
    ("sh16_10", "payoff", "AnimatedStatsSlide", "Только <em>удержание</em>", "ночью — не продажа", {"variant": "tech", "stats": [
        {"label": "Удержание контакта", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:hand-raised", "start_time": 0},
        {"label": "Слот звонка утром", "value": 1, "suffix": "шаг", "color": A2, "icon": "heroicons:sun", "start_time": 800},
        {"label": "Иллюзия продать ночью", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:exclamation-triangle", "start_time": 1600}]}),
    ("sh16_11", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
