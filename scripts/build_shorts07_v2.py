#!/usr/bin/env python3
"""Шортс_07 v2 «Галлюцинация агента» — НОВЫЕ компоненты (9) + Outro.

Переиспользует озвучку/таймлайн из p65 (без повторного TTS). Создаёт новую презентацию.
Запуск с хоста: python3 scripts/build_shorts07_v2.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SRC_PRES = 65
TITLE = "07 - Галлюцинация агента (v2, новые компоненты)"
SECTIONS = ["hook", "most", "proof", "payoff", "hook_out"]

DANGER = "var(--color-danger)"
SUCCESS = "var(--color-success)"
SECOND = "var(--color-secondary)"
WARN = "var(--color-warning)"
ACCENT = "var(--color-accent)"

SLIDES = [
    ("v2_01", "hook", "NodeFlow", "Откуда <em>фейк-номер</em>", "нет строки в базе", {
        "variant": "tech", "flow_layout": "layered",
        "nodes": [
            {"id": "cl", "label": "Клиент", "icon": "heroicons:user", "status": "info", "x": 10, "y": 50, "start_time": 0},
            {"id": "bot", "label": "ИИ-агент", "icon": "heroicons:cpu-chip", "status": "warn", "x": 40, "y": 50, "start_time": 800},
            {"id": "fake", "label": "Фейк-номер", "icon": "heroicons:document-text", "status": "warn", "x": 68, "y": 50, "start_time": 1600},
            {"id": "book", "label": "Бронь €12k", "icon": "heroicons:banknotes", "status": "ok", "x": 92, "y": 50, "start_time": 2400}],
        "edges": [
            {"from": "cl", "to": "bot", "label": "вопрос"},
            {"from": "bot", "to": "fake", "label": "нет в базе"},
            {"from": "fake", "to": "book", "label": "8841-C"}]}),
    ("v2_02", "most", "QuadrantMatrix", "Где агент <em>надёжен</em>", "а где выдумывает", {
        "variant": "tech",
        "points": [
            {"label": "Прайс", "x": 85, "y": 80, "bubble": 26, "color": SUCCESS},
            {"label": "Сроки", "x": 75, "y": 70, "bubble": 24, "color": SECOND},
            {"label": "Сертификат", "x": 10, "y": 15, "bubble": 30, "color": DANGER}],
        "x_label": "Опора на базу", "y_label": "Польза клиенту",
        "quadrant_labels": ["Быстрые победы", "Стратегические", "В зоне риска", "Отложить"]}),
    ("v2_03", "proof", "HeatmapMatrix", "Карта <em>базы</em>", "где пусто", {
        "variant": "tech",
        "rows": ["Склад", "Сроки", "Цены", "Сертификаты"],
        "cols": ["Данные", "Полнота", "Актуальность"],
        "cells": [["L", "L", "L"], ["L", "L", "M"], ["M", "M", "M"], ["H", "H", "H"]],
        "scale": "rag", "source_note": "Пробел в сертификатах — красный"}),
    ("v2_04", "proof", "DefinitionBlock", "Что такое <em>галлюцинация</em>", "термин", {
        "variant": "tech",
        "term": "Галлюцинация агента",
        "definition": "Уверенный, но фактически неверный ответ модели, не опирающийся на базу.",
        "examples": [
            {"id": "d1", "text": "Выдумывает сертификат, которого нет.", "start_time": 1000},
            {"id": "d2", "text": "Называет точный номер 8841-C.", "start_time": 2000}],
        "related_terms": ["Стоп-правило", "RAG", "Фактчекинг"]}),
    ("v2_05", "proof", "WaterfallChart", "€12 000 под <em>фейк</em>", "что осталось", {
        "variant": "tech",
        "start_label": "Бронь", "start_value": 12,
        "steps": [{"label": "Документа нет", "delta": -12, "kind": "neg"}],
        "end_label": "Реально", "value_prefix": "€", "value_suffix": "k"}),
    ("v2_06", "proof", "ControlChart", "Ответ <em>вне</em> нормы", "дрейф параметра", {
        "variant": "tech",
        "points": [12.1, 11.8, 12.2, 12.0, 11.9, 12.3, 15.4, 12.1, 11.8, 12.0, 12.2, 11.9],
        "mean": 12.1, "ucl": 13.0, "lcl": 11.3, "unit": "", "violations": [6]}),
    ("v2_07", "proof", "StepByStep", "Стоп-правило", "железом, не промптом", {
        "variant": "tech", "title": "", "subtitle": "", "layout": "horizontal",
        "steps": [
            {"id": "s1", "number": 1, "title": "Нет строки", "description": "В базе нет ответа.", "icon": "heroicons:no-symbol", "color": DANGER, "start_time": 0},
            {"id": "s2", "number": 2, "title": "Не отвечать", "description": "Бот не импровизирует.", "icon": "heroicons:hand-raised", "color": WARN, "start_time": 800},
            {"id": "s3", "number": 3, "title": "Передать", "description": "«Передал инженеру».", "icon": "heroicons:paper-airplane", "color": SECOND, "start_time": 1600},
            {"id": "s4", "number": 4, "title": "Замолчать", "description": "Ждёт человека.", "icon": "heroicons:bell-slash", "color": SUCCESS, "start_time": 2400}]}),
    ("v2_08", "proof", "CircularGauge", "Уверенность <em>vs</em> база", "одна система", {
        "variant": "tech", "title": "", "subtitle": "",
        "gauges": [
            {"id": "g1", "value": 99, "max": 100, "unit": "%", "label": "Уверенность", "color": DANGER, "icon": "heroicons:bolt", "start_time": 0},
            {"id": "g2", "value": 2, "max": 100, "unit": "%", "label": "Опора на базу", "color": SECOND, "icon": "heroicons:circle-stack", "start_time": 800},
            {"id": "g3", "value": 1, "max": 100, "unit": "%", "label": "Документ есть", "color": WARN, "icon": "heroicons:document-text", "start_time": 1600}]}),
    ("v2_09", "payoff", "JourneyMap", "Путь <em>ошибки</em>", "от вопроса до конфликта", {
        "variant": "tech",
        "stages": [
            {"name": "Вопрос", "kpi": "сертификат", "touchpoints": ["WhatsApp"], "pains": ["В базе пусто"], "start_time": 0},
            {"name": "Фантазия", "kpi": "номер 8841-C", "touchpoints": ["Чат бота"], "pains": ["Факта нет"], "start_time": 800},
            {"name": "Бронь", "kpi": "€12 000", "touchpoints": ["Договорённость"], "pains": ["Под фейк-номер"], "start_time": 1600},
            {"name": "Конфликт", "kpi": "утром", "touchpoints": ["Чат инженера"], "pains": ["Документа не было"], "start_time": 2400}]}),
    ("v2_10", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
]


def validate(comp, payload):
    r = requests.post(f"{BASE}/components/{comp}/validate", json={"payload": payload})
    r.raise_for_status()
    return r.json()


def main():
    src = requests.get(f"{BASE}/presentations/{SRC_PRES}").json()
    pres = requests.post(f"{BASE}/presentations/", json={"title": TITLE, "folder_id": 2}).json()
    pid = pres["id"]
    print(f"Created presentation {pid}")

    # Копируем озвучку/музыку и маркер из p65
    requests.put(f"{BASE}/presentations/{pid}", json={"audio_timeline": src["audio_timeline"]}).raise_for_status()
    em = next(s for s in src["slides"] if s["component"] == "EndMarkerSlide")
    requests.post(f"{BASE}/presentations/{pid}/slides", json={
        "slide_id": f"end_{pid}", "component": "EndMarkerSlide", "start_time": em["start_time"],
        "order_index": 999, "layout": "col", "data": {"payload": {}}}).raise_for_status()

    clips = sorted([c for t in src["audio_timeline"]["tracks"] if t["id"] == "main" for c in t["clips"]],
                   key=lambda c: c["start_time"])
    bounds = {SECTIONS[i]: (clips[i]["start_time"], clips[i]["end_time"]) for i in range(len(SECTIONS))}
    counts = {}
    for _, sec, *_ in SLIDES:
        key = "hook_out" if sec == "cta" else sec
        counts[key] = counts.get(key, 0) + 1
    starts = {}
    for sec, (s, e) in bounds.items():
        n = counts.get(sec, 0)
        if not n:
            continue
        step = max(2000, min(5200, int((e - s) / n)))
        idx = 0
        for sid, sc, *_ in SLIDES:
            key = "hook_out" if sc == "cta" else sc
            if key == sec:
                starts[sid] = s + idx * step
                idx += 1
    ordered = [x[0] for x in SLIDES]
    for i in range(1, len(ordered)):
        starts[ordered[i]] = max(starts[ordered[i]], starts[ordered[i - 1]] + 2000)

    print("--- Creating slides ---")
    ok, fail = 0, []
    for i, (sid, sec, comp, title, sub, payload) in enumerate(SLIDES, start=1):
        res = validate(comp, payload)
        if not res.get("valid"):
            print(f"INVALID {sid} {comp}: {res.get('errors')}")
            fail.append(sid)
            continue
        for w in res.get("warnings", []):
            print(f"  warn {sid}: {w.get('type')} @ {w.get('path')}")
        gs.create_slide(pid, sid, comp, starts[sid], i, title=title, subtitle=sub, payload=payload)
        print(f"  OK {sid:<8} {starts[sid]:>6.0f}ms  {comp}")
        ok += 1
    normalize_bgm_track(pid)
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5174/p/{pid}")


if __name__ == "__main__":
    main()
