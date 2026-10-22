#!/usr/bin/env python3
"""Сборка Шортс_08 «Скорость 6 секунд против 1.8» в проекте IT2B.

Правила: docs/AGENT_PLAYBOOK.md §12. Запуск с хоста: python3 scripts/build_shorts08.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_08 — Скорость 6 секунд против 1.8 вот разница в деньгах.txt"
TITLE = "08 - Скорость 6 секунд против 1.8"

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    ("s08_01", "hook", "InfographicCards", "Клик <em>оплачен</em>", "экран белый", {"variant": "tech", "items": [
        {"id": 1, "label": "Клик", "value": "Оплачен", "trend": "списали сразу", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "Экран", "value": "Белый", "trend": "клиент ждёт", "color": A4, "icon": "heroicons:computer-desktop", "start_time": 800},
        {"id": 3, "label": "Секунды", "value": "Идут", "trend": "бюджет тает", "color": A3, "icon": "heroicons:clock", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Закрыл", "trend": "заявки нет", "color": A2, "icon": "heroicons:x-circle", "start_time": 2400}]}),
    ("s08_02", "most", "ComparisonTable", "Дольше <em>двух секунд</em>", "и клики не доходят", {"variant": "tech", "headers": ["", "6 сек", "1.8 сек"], "items": [
        {"id": "r1", "label": "Клиент ждёт", "values": [False, True], "start_time": 0},
        {"id": "r2", "label": "Доживает до оффера", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Деньги за клик ушли", "values": [True, True], "start_time": 1600},
        {"id": "r4", "label": "Заявка", "values": [False, True], "start_time": 2400}]}),
    ("s08_03", "proof", "ArchitectureDiagram", "Путь <em>клика</em>", "до закрытой вкладки", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Реклама", "subtitle": "клик 2€", "icon": "lucide:mouse-pointer-click", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["white"]},
        {"id": "white", "title": "Белый экран", "subtitle": "5 сек", "icon": "lucide:monitor", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["vid"]},
        {"id": "vid", "title": "Видео 20 МБ", "subtitle": "догрузка", "icon": "lucide:video", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["out"]},
        {"id": "out", "title": "Закрыл", "subtitle": "в машине, 4G", "icon": "lucide:log-out", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("s08_04", "proof", "AnimatedStatsSlide", "Цифры <em>потерь</em>", "те же деньги", {"variant": "tech", "stats": [
        {"label": "Клик", "value": 2, "suffix": "€", "color": A3, "icon": "lucide:mouse-pointer-click", "start_time": 0},
        {"label": "Отказы", "value": 80, "suffix": "%", "color": A4, "icon": "lucide:log-out", "start_time": 800},
        {"label": "Фоновое видео", "value": 20, "suffix": "МБ", "color": A1, "icon": "lucide:video", "start_time": 1600}]}),
    ("s08_05", "proof", "StatsBarChart", "Загрузка <em>по секундам</em>", "сколько доживает", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Загрузка по секундам", "subtitle": "сколько доживает", "data": [
        {"label": "0–1с", "value": 100, "highlight": True, "start_time": 0},
        {"label": "1–2с", "value": 55, "start_time": 800},
        {"label": "2–5с", "value": 12, "start_time": 1600},
        {"label": ">5с", "value": 4, "start_time": 2400}]}),
    ("s08_06", "proof", "ReceiptCard", "", "", {"variant": "tech", "title": "РЕКЛАМА", "subtitle": "Google Ads", "currency": "€", "total_text": "СПИСАНО", "footer_text": "КЛИКИ НЕ ДОШЛИ", "total_start_time": 2600, "items": [
        {"name": "Клики (2€ × 100)", "price": 200, "start_time": 300},
        {"name": "Ведение", "price": 80, "start_time": 1100},
        {"name": "Креативы", "price": 20, "start_time": 1900}]}),
    ("s08_07", "proof", "TerminalMockup", "Замер <em>загрузки</em>", "с телефона", {"variant": "tech", "commands": [
        {"cmd": "$ measure https://doma.io", "output": "TTFB 3.9s\nLCP 6.0s\nvideo: 20 MB\nbounce: 80%", "start_time": 300},
        {"cmd": "$ measure https://doma.io --after", "output": "LCP 1.8s\nweight: 0.9 MB\nleads: growing", "start_time": 2200}]}),
    ("s08_08", "proof", "PremiumChecklist", "Что <em>срезал</em>", "ради скорости", {"variant": "tech", "items": [
        {"label": "Фоновое видео", "desc": "20 МБ в топку", "icon": "heroicons:video-camera-slash", "color": "brand-blue", "start_time": 0},
        {"label": "Тяжёлые шрифты", "desc": "оставил системные", "icon": "heroicons:language", "color": "brand-amber", "start_time": 800},
        {"label": "Лишние скрипты", "desc": "только необходимое", "icon": "heroicons:code-bracket", "color": "brand-green", "start_time": 1600}]}),
    ("s08_09", "payoff", "MetricScales", "Секунда <em>не дошла</em>", "ты её уже оплатил", {"variant": "tech", "title": "Секунда не дошла", "subtitle": "ты её уже оплатил", "metrics": [
        {"id": 1, "label": "Оплачено", "percentage": 100, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Дошло до клиента", "percentage": 20, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Оставили заявку", "percentage": 5, "color": G3c, "start_time": 1600}]}),
    ("s08_10", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5174/p/{pres_id}")


if __name__ == "__main__":
    main()
