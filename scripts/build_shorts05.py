#!/usr/bin/env python3
"""Сборка Шортс_05 «Сайт выглядит дорого. Заявок ноль» в проекте IT2B.

Правила (см. docs/AGENT_PLAYBOOK.md §12): BGM на дорожке `bgm` (0.15, offset 20000, до EndMarker),
OutroSlide-эталон (лого+QR), токены вместо hex, айтемы ≥800мс, валидация перед созданием.
Запуск с хоста: python3 scripts/build_shorts05.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_05 — Сайт выглядит дорого Заявок ноль.txt"
TITLE = "05 - Сайт выглядит дорого. Заявок ноль"

BAD_LANDING_HTML = '''<div style="display:flex;flex-direction:column;width:100%;min-height:100cqh;box-sizing:border-box;background:#0b1322;color:#f8fafc;font-family:Inter,system-ui,sans-serif;overflow:hidden;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:10px;padding:12px 16px;flex-shrink:0;">
    <span style="font-weight:800;letter-spacing:2px;font-size:13px;white-space:nowrap;flex-shrink:0;">AURORA <span style="color:#38bdf8;">GLAMP</span></span>
    <div style="display:flex;gap:12px;font-size:11px;color:rgba(255,255,255,0.65);white-space:nowrap;min-width:0;overflow:hidden;">
      <span>О нас</span><span>Локации</span><span>Галерея</span>
    </div>
    <div style="font-size:18px;line-height:1;color:rgba(255,255,255,0.8);flex-shrink:0;">&#8801;</div>
  </div>
  <div style="position:relative;flex:1;min-height:0;display:flex;align-items:flex-end;background:url('https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&q=80&w=1600') center/cover no-repeat;">
    <div style="position:absolute;inset:0;background:linear-gradient(180deg, rgba(11,19,34,0.10) 0%, rgba(11,19,34,0.55) 55%, rgba(11,19,34,0.92) 100%);"></div>
    <div style="position:relative;padding:18px 18px 22px;max-width:560px;">
      <div style="font-size:10px;letter-spacing:4px;color:#7dd3fc;">GLAMPING &middot; С 2019 ГОДА</div>
      <div style="font-size:26px;font-weight:800;line-height:1.14;margin:10px 0 8px;">Панорама леса<br/>прямо с террасы</div>
      <div style="font-size:13px;line-height:1.5;color:rgba(255,255,255,0.75);max-width:380px;">Приватные капсулы среди сосен, панорамные окна и завтрак на террасе.</div>
    </div>
  </div>
  <div style="padding:10px 16px;font-size:10px;color:rgba(255,255,255,0.32);display:flex;justify-content:space-between;gap:12px;border-top:1px solid rgba(255,255,255,0.06);white-space:nowrap;flex-shrink:0;">
    <span>&copy; 2026 Aurora Glamp</span><span>Цены — по запросу</span>
  </div>
</div>'''

SLIDES = [
    ("s05_01", "hook", "InfographicCards", "Дорогой <em>сайт</em>", "заявок — ноль", {
        "variant": "tech",
        "items": [
            {"id": 1, "label": "Бюджет", "value": "€5k", "trend": "в дизайн", "color": "var(--item-accent-1)", "icon": "heroicons:banknotes", "start_time": 0},
            {"id": 2, "label": "Заявки", "value": "0", "trend": "с сайта", "color": "var(--item-accent-4)", "icon": "heroicons:inbox-arrow-down", "start_time": 800},
            {"id": 3, "label": "Первый экран", "value": "3D", "trend": "светится", "color": "var(--item-accent-3)", "icon": "heroicons:sparkles", "start_time": 1600},
            {"id": 4, "label": "Оффер", "value": "?", "trend": "не понять", "color": "var(--item-accent-2)", "icon": "heroicons:question-mark-circle", "start_time": 2400},
        ]}),
    ("s05_02", "most", "ComparisonTable", "Красота <em>против</em> оффера", "клиент решает за 3 сек", {
        "variant": "tech", "headers": ["", "Продающий сайт", "Премиум-сайт"],
        "items": [
            {"id": "r1", "label": "Красивая анимация", "values": [True, True], "start_time": 0},
            {"id": "r2", "label": "Оффер за 3 секунды", "values": [True, False], "start_time": 800},
            {"id": "r3", "label": "Цена на первом экране", "values": [True, False], "start_time": 1600},
            {"id": "r4", "label": "Кнопка на виду", "values": [True, False], "start_time": 2400},
        ]}),
    ("s05_03", "proof", "BrowserMockup", "Лендинг за <em>€5000</em>", "цены нет, кнопка в меню", {
        "variant": "tech",
        "items": [
            {"id": "b1", "url": "auroraglamp.com", "type": "html", "content": BAD_LANDING_HTML,
             "scroll": False, "image_position": "top", "start_time": 0},
        ]}),
    ("s05_04", "proof", "MetricScales", "Что не <em>найти</em>", "за первые секунды", {
        "variant": "tech", "title": "Что не найти", "subtitle": "за первые секунды",
        "metrics": [
            {"id": 1, "label": "Оффер понятен сразу", "percentage": 10, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 0},
            {"id": 2, "label": "Цена видна на 1 экране", "percentage": 5, "color": "linear-gradient(to right, #EF4444, #FB923C)", "start_time": 800},
            {"id": 3, "label": "Кнопка на виду", "percentage": 8, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 1600},
        ]}),
    ("s05_05", "proof", "ProcessFunnel", "Воронка <em>теряет</em> всех", "от клика до заявки", {
        "variant": "tech", "layout": "horizontal",
        "steps": [
            {"label": "Реклама", "count": 100, "icon": "heroicons:megaphone", "color": "var(--item-accent-1)", "start_time": 0},
            {"label": "Открыли", "count": 60, "icon": "heroicons:arrow-top-right-on-square", "color": "var(--item-accent-3)", "start_time": 800},
            {"label": "Поняли оффер", "count": 12, "icon": "heroicons:eye", "color": "var(--item-accent-4)", "start_time": 1600},
            {"label": "Заявка", "count": 1, "icon": "heroicons:check-circle", "color": "var(--item-accent-2)", "start_time": 2400},
        ]}),
    ("s05_06", "proof", "StatsBarChart", "Внимание <em>тает</em>", "по экранам вниз", {
        "variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)",
        "title": "Внимание тает", "subtitle": "по экранам вниз",
        "data": [
            {"label": "1 экран", "value": 100, "highlight": True, "start_time": 0},
            {"label": "2 экран", "value": 30, "start_time": 800},
            {"label": "3 экран", "value": 8, "start_time": 1600},
            {"label": "Уход", "value": 3, "start_time": 2400},
        ]}),
    ("s05_07", "proof", "ReceiptCard", "", "", {
        "variant": "tech", "title": "СЧЁТ ЗА ДИЗАЙН", "subtitle": "лендинг глэмпинга", "currency": "€",
        "total_text": "ЗА КРАСОТУ", "footer_text": "ЗАЯВОК — НОЛЬ", "total_start_time": 2600,
        "items": [
            {"name": "Дизайн", "price": 3500, "start_time": 300},
            {"name": "3D-анимации", "price": 1000, "start_time": 1100},
            {"name": "Шрифты и эффекты", "price": 500, "start_time": 1900},
        ]}),
    ("s05_08", "proof", "PremiumChecklist", "Что должно быть <em>на первом</em>", "экране", {
        "variant": "tech",
        "items": [
            {"label": "Оффер", "desc": "что и для кого — за 3 секунды", "icon": "heroicons:bolt", "color": "brand-blue", "start_time": 0},
            {"label": "Цена и даты", "desc": "конкретика вместо «уточняйте»", "icon": "heroicons:currency-euro", "color": "brand-amber", "start_time": 800},
            {"label": "Одна кнопка", "desc": "путь без квеста", "icon": "heroicons:cursor-arrow-rays", "color": "brand-green", "start_time": 1600},
        ]}),
    ("s05_09", "payoff", "AnimatedStatsSlide", "Дизайн ведёт к <em>действию</em>", "или в никуда", {
        "variant": "tech",
        "stats": [
            {"label": "Теряет красота", "value": 97, "suffix": "%", "color": "var(--item-accent-4)", "icon": "lucide:trending-down", "start_time": 0},
            {"label": "Решает оффер", "value": 3, "suffix": "сек", "color": "var(--item-accent-2)", "icon": "lucide:eye", "start_time": 800},
            {"label": "Цена ошибки", "value": 5000, "suffix": "€", "color": "var(--item-accent-3)", "icon": "lucide:wallet", "start_time": 1600},
        ]}),
    ("s05_10", "cta", "OutroSlide", "", "", {
        "variant": "tech", **IT2B_OUTRO,
    }),
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
