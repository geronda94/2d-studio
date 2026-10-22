#!/usr/bin/env python3
"""Сборка Шортс_07 «Галлюцинация агента в реальном диалоге» в проекте IT2B.

Правила: docs/AGENT_PLAYBOOK.md §12 (BGM bgm/0.15/offset 20000/до EndMarker, Outro-эталон,
токены, иконки, ≥800мс, ≥2000мс). Запуск с хоста: python3 scripts/build_shorts07.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_07 — Галлюцинация агента в реальном диалоге.txt"
TITLE = "07 - Галлюцинация агента в реальном диалоге"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    ("s07_01", "hook", "ChatMockupSlide", "Бот <em>назвал</em> номер", "которого нет", {"variant": "tech", "bot_name": "AI-агент", "bot_subtitle": "входящие", "bot_avatar": "AI", "messages": [
        {"role": "user", "text": "Нужен сертификат на партию.", "start_time": 0},
        {"role": "assistant", "text": "Сертификат EN 10204 3.2, номер 8841-C.", "start_time": 1500},
        {"role": "user", "text": "Отлично, бронирую.", "start_time": 3000}]}),
    ("s07_02", "most", "InfographicCards", "Хотели <em>разгрузить</em> рутину", "получили конфликт", {"variant": "tech", "items": [
        {"id": 1, "label": "Отдел", "value": "Разгрузить", "trend": "хотел рутину", "color": A1, "icon": "heroicons:user-group", "start_time": 0},
        {"id": 2, "label": "Бот", "value": "Уверен", "trend": "номера не существует", "color": A4, "icon": "heroicons:face-frown", "start_time": 800},
        {"id": 3, "label": "Переписка", "value": "Не отозвать", "trend": "уже у клиента", "color": A3, "icon": "heroicons:chat-bubble-left", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Конфликт", "trend": "на пустом месте", "color": A2, "icon": "heroicons:fire", "start_time": 2400}]}),
    ("s07_03", "proof", "ComparisonTable", "Где нормально, <em>где фантазия</em>", "одна система", {"variant": "tech", "headers": ["", "Обычное", "Нестандарт"], "items": [
        {"id": "r1", "label": "Есть на складе", "values": [True, True], "start_time": 0},
        {"id": "r2", "label": "Срок поставки", "values": [True, True], "start_time": 800},
        {"id": "r3", "label": "Номер сертификата", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Конкретные документы", "values": [True, False], "start_time": 2400}]}),
    ("s07_04", "proof", "ArchitectureDiagram", "Откуда <em>номер</em>", "база пустая", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Закупщик", "subtitle": "Чехия", "icon": "lucide:message-circle", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core"]},
        {"id": "core", "title": "ИИ-агент", "subtitle": "нет в базе", "icon": "lucide:cpu", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["out"]},
        {"id": "out", "title": "Фантазия", "subtitle": "номер 8841-C", "icon": "lucide:sparkles", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["book"]},
        {"id": "book", "title": "Бронь", "subtitle": "€12 000", "icon": "lucide:package", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s07_05", "proof", "ReceiptCard", "", "", {"variant": "tech", "title": "БРОНЬ", "subtitle": "под номер 8841-C", "currency": "€", "total_text": "РИСК", "footer_text": "ДОКУМЕНТА НЕ СУЩЕСТВУЕТ", "total_start_time": 2600, "items": [
        {"name": "Партия комплектующих", "price": 8000, "start_time": 300},
        {"name": "Логистика", "price": 2500, "start_time": 1100},
        {"name": "Упаковка", "price": 1500, "start_time": 1900}]}),
    ("s07_06", "proof", "MetricScales", "Насколько <em>уверен</em>", "при пустой базе", {"variant": "tech", "title": "Насколько уверен", "subtitle": "при пустой базе", "metrics": [
        {"id": 1, "label": "Уверенность ответа", "percentage": 99, "color": G2c, "start_time": 0},
        {"id": 2, "label": "Опора на базу", "percentage": 2, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Документ реально есть", "percentage": 1, "color": G3c, "start_time": 1600}]}),
    ("s07_07", "proof", "PremiumChecklist", "Стоп-кран <em>по базе</em>", "железом, не промптом", {"variant": "tech", "items": [
        {"label": "Нет строки в базе", "desc": "бот не отвечает", "icon": "heroicons:lock-closed", "color": "brand-blue", "start_time": 0},
        {"label": "Пишет «передал инженеру»", "desc": "и замолкает", "icon": "heroicons:paper-airplane", "color": "brand-amber", "start_time": 800},
        {"label": "Фантазия отключена", "desc": "на уровне логики", "icon": "heroicons:shield-check", "color": "brand-green", "start_time": 1600}]}),
    ("s07_08", "proof", "AnimatedStatsSlide", "Реплики <em>из базы</em>", "а не из воздуха", {"variant": "tech", "stats": [
        {"label": "Ответов из базы", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:database", "start_time": 0},
        {"label": "Ответов сверх базы", "value": 1, "suffix": "", "color": A4, "icon": "lucide:alert-triangle", "start_time": 800},
        {"label": "Стоп-правил", "value": 12, "suffix": "", "color": A1, "icon": "lucide:list-checks", "start_time": 1600}]}),
    ("s07_09", "payoff", "ProcessFunnel", "Правильный <em>маршрут</em>", "вопрос без ответа", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Вопрос", "count": 100, "icon": "heroicons:chat-bubble-left", "color": A1, "start_time": 0},
        {"label": "Проверка базы", "count": 100, "icon": "heroicons:circle-stack", "color": A2, "start_time": 800},
        {"label": "Нет строки", "count": 20, "icon": "heroicons:no-symbol", "color": A3, "start_time": 1600},
        {"label": "Инженеру", "count": 20, "icon": "heroicons:user", "color": A4, "start_time": 2400}]}),
    ("s07_10", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
