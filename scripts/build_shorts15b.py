#!/usr/bin/env python3
"""Шортс_15 v2 (новый сценарий, формат VO/ЭКРАН) — по-строчная сборка.

14 VO-строк = 14 аудио-клипов = 14 слайдов. Озвучка на каждую строку,
слайд ставится на старт её клипа (точная синхронизация).
Запуск с хоста: python3 scripts/build_shorts15b.py
"""
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_TXT = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_2/Шортс_15 — ИИ квалифицирует клиента лучше стажера.txt"
TITLE = "15 - ИИ квалифицирует клиента лучше стажёра (v2)"
GAP = 200

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"

# (slide_id, component, title, subtitle, payload) — по одной на каждую VO-строку
SLIDES = [
    ("sh15_01", "AnimatedStatsSlide", "Упущенная <em>сделка</em>", "−$30 000", {"variant": "tech", "stats": [
        {"label": "Сделка", "value": 30000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Причина", "value": 1, "suffix": "вопрос", "color": A1, "icon": "heroicons:question-mark-circle", "start_time": 0}]}),
    ("sh15_02", "QuoteCard", "Одна <em>причина</em>", "один вопрос", {"variant": "tech",
        "quote": "Причина — один незаданный вопрос.", "author": "Игорь", "author_title": "IT2B", "source": "разбор кейса"}),
    ("sh15_03", "CrmCardSlide", "Поставщик <em>стройматериалов</em>", "сотня обращений в день", {"variant": "tech", "customer": {"name": "Стройматериалы", "avatar_text": "С", "id_text": "ID: #q-15", "status": "поток"},
        "fields": [
            {"label": "ОБРАЩЕНИЙ В ДЕНЬ", "value": "100", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-blue", "start_time": 0},
            {"label": "КАНАЛ", "value": "Чат", "field_icon": "heroicons:device-phone-mobile", "field_color": "brand-amber", "start_time": 0},
            {"label": "СЕГМЕНТ", "value": "Стройматериалы", "field_icon": "heroicons:building-office", "field_color": "brand-green", "start_time": 0},
            {"label": "ПОТЕРЯ", "value": "Оптовик", "field_icon": "heroicons:user-minus", "field_color": "brand-orange", "start_time": 0}],
        "buttons": [
            {"text": "Снять рутину", "btn_color": "", "btn_text_color": "", "start_time": 0},
            {"text": "Отдать боту", "btn_color": "", "btn_text_color": "", "start_time": 0}]}),
    ("sh15_04", "PremiumChecklist", "Три вопроса <em>как робот</em>", "одно и то же", {"variant": "tech", "items": [
        {"label": "Бюджет", "desc": "первый вопрос", "icon": "heroicons:banknotes", "color": "brand-blue", "start_time": 0},
        {"label": "Сроки", "desc": "каждому клиенту", "icon": "heroicons:calendar-days", "color": "brand-amber", "start_time": 0},
        {"label": "Объём", "desc": "по шаблону", "icon": "heroicons:cube", "color": "brand-green", "start_time": 0}]}),
    ("sh15_05", "StatsBarChart", "Восьмидесятый <em>чат</em>", "автопилот", {"variant": "tech", "base_color": "var(--brand-blue)", "peak_color": "var(--brand-amber)", "data": [
        {"label": "Чат 1", "value": 10, "start_time": 0},
        {"label": "Чат 40", "value": 40, "start_time": 0},
        {"label": "Чат 80", "value": 80, "highlight": True, "start_time": 0},
        {"label": "Чат 100", "value": 100, "start_time": 0}]}),
    ("sh15_06", "InfographicCards", "Крупный <em>оптовик</em>", "среди сотни серых", {"variant": "tech", "items": [
        {"id": 1, "label": "Оптовик", "value": "1", "trend": "среди сотни", "color": A1, "icon": "heroicons:user", "start_time": 0},
        {"id": 2, "label": "Сделка", "value": "$30 000", "trend": "на кону", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 3, "label": "Вопрос", "value": "Не задан", "trend": "про рег. номер", "color": A4, "icon": "heroicons:document-text", "start_time": 0},
        {"id": 4, "label": "Итог", "value": "Ушёл", "trend": "к конкуренту", "color": A2, "icon": "heroicons:arrow-right-circle", "start_time": 0}]}),
    ("sh15_07", "DefinitionBlock", "Регистрационный <em>номер</em>", "один вопрос", {"variant": "tech",
        "term": "Регистрационный номер",
        "definition": "Один вопрос, который отделяет крупного заказчика от потока остальных. Менеджер забыл его задать.",
        "examples": [
            {"id": "d1", "text": "К восьмидесятому чату внимание слабеет.", "start_time": 0},
            {"id": "d2", "text": "Именно в этом чате сидел оптовик.", "start_time": 0}],
        "related_terms": ["Оптовик", "Фильтр", "Внимание"]}),
    ("sh15_08", "AnimatedStatsSlide", "За клиентом <em>завод</em>", "а заявку слили", {"variant": "tech", "stats": [
        {"label": "За клиентом", "value": 1, "suffix": "завод", "color": A2, "icon": "heroicons:building-office-2", "start_time": 0},
        {"label": "Сделка", "value": 30000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Дней до конкурента", "value": 1, "suffix": "", "color": A1, "icon": "heroicons:calendar-days", "start_time": 0}]}),
    ("sh15_09", "ComparisonTable", "Кто <em>подписал</em>", "через день", {"variant": "tech", "headers": ["", "Ты", "Конкурент"], "items": [
        {"id": "r1", "label": "Ответил первым", "values": [False, True], "start_time": 0},
        {"id": "r2", "label": "Спросил рег. номер", "values": [False, True], "start_time": 0},
        {"id": "r3", "label": "Подписал договор", "values": [False, True], "start_time": 0}]}),
    ("sh15_10", "QuoteCard", "Дело не в <em>менеджере</em>", "а в нагрузке", {"variant": "tech",
        "quote": "Дело не в менеджере. Человек не создан быть фильтром весь день.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод"}),
    ("sh15_11", "PremiumChecklist", "Человек <em>устаёт</em>", "фильтрует хуже робота", {"variant": "tech", "items": [
        {"label": "Устаёт к вечеру", "desc": "внимание слабеет", "icon": "heroicons:fire", "color": "brand-blue", "start_time": 0},
        {"label": "Фильтрует хуже робота", "desc": "пропускает важное", "icon": "heroicons:cpu-chip", "color": "brand-amber", "start_time": 0},
        {"label": "Ошибается на автопилоте", "desc": "теряет оптовика", "icon": "heroicons:exclamation-triangle", "color": "brand-green", "start_time": 0}]}),
    ("sh15_12", "ArchitectureDiagram", "Первую линию — <em>боту</em>", "фильтр в начале", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Обращения", "subtitle": "сотни в день", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["bot"]},
        {"id": "bot", "title": "Бот-фильтр", "subtitle": "первая линия", "icon": "lucide:bot", "color": "chart-2", "start_time": 0, "is_main": True, "to": ["mgr"]},
        {"id": "mgr", "title": "Менеджер", "subtitle": "только тёплые", "icon": "lucide:user-check", "color": "chart-3", "start_time": 0, "is_main": False, "to": ["deal"]},
        {"id": "deal", "title": "Сделка", "subtitle": "не теряется", "icon": "lucide:check-check", "color": "chart-4", "start_time": 0, "is_main": False, "to": []}]}),
    ("sh15_13", "ProcessFunnel", "Только <em>готовые</em>", "мусор отсечён", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Обращения", "count": 100, "icon": "heroicons:chat-bubble-left", "color": A1, "start_time": 0},
        {"label": "Бот-фильтр", "count": 60, "icon": "heroicons:funnel", "color": A2, "start_time": 0},
        {"label": "Готовы покупать", "count": 35, "icon": "lucide:user-check", "color": A3, "start_time": 0},
        {"label": "Допущены", "count": 20, "icon": "heroicons:check-badge", "color": A4, "start_time": 0}]}),
    ("sh15_14", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
]

PRESETS = ["hook"] + ["proof_narrative"] * (len(SLIDES) - 2) + ["cta"]


def validate(comp, payload):
    r = requests.post(f"{BASE}/components/{comp}/validate", json={"payload": payload})
    r.raise_for_status()
    return r.json()


def main():
    lines = [l.strip() for l in open(SCENARIO_TXT, encoding="utf-8") if l.strip()]
    assert len(lines) == len(SLIDES), f"{len(lines)} строк VO vs {len(SLIDES)} слайдов"

    pres_id = gs.create_presentation(TITLE)
    batch_id = f"short15b_{int(time.time())}"
    print(f"\n--- Per-line TTS ({len(lines)} clips) ---")
    voice_clips, starts = [], []
    t = 0.0
    for i, (line, preset) in enumerate(zip(lines, PRESETS)):
        media = gs.generate_tts(pres_id, line, batch_id, preset=preset)
        dur = gs.get_duration(media["file_path"])
        voice_clips.append({"file_path": media["file_path"], "start_time": t, "end_time": t + dur,
                            "ai_settings": media.get("ai_settings", {})})
        starts.append(t)
        print(f"  [{preset}] {line[:50]}… {dur:.0f}ms @ {t:.0f}")
        t = t + dur + GAP
    total = t - GAP

    timeline = gs.build_audio_timeline(voice_clips, gs.BGM_FILE)
    requests.put(f"{BASE}/presentations/{pres_id}", json={"audio_timeline": timeline}).raise_for_status()
    gs.create_slide(pres_id, f"end_{pres_id}", "EndMarkerSlide", total + 1000, 999, layout="col")
    normalize_bgm_track(pres_id)
    print(f"  TOTAL {total:.0f}ms, EndMarker {total+1000:.0f}ms")

    print("\n--- Creating slides ---")
    ok, fail = 0, []
    for i, (sid, comp, title, sub, payload) in enumerate(SLIDES):
        res = validate(comp, payload)
        if not res.get("valid"):
            print(f"INVALID {sid} {comp}: {res.get('errors')}")
            fail.append(sid)
            continue
        for w in res.get("warnings", []):
            print(f"  warn {sid}: {w.get('type')} @ {w.get('path')}")
        gs.create_slide(pres_id, sid, comp, starts[i], i + 1, title=title, subtitle=sub, payload=payload)
        print(f"  OK {sid:<9} {starts[i]:>7.0f}ms  {comp}")
        ok += 1
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5174/p/{pres_id}")


if __name__ == "__main__":
    main()
