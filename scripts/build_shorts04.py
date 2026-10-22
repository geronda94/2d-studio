#!/usr/bin/env python3
"""Сборка Шортс_04 «Пытались закрывать сделки силами ИИ» в проекте IT2B.

Шаги: презентация (папка Шортсы) → TTS по 5 блокам → audio_timeline → EndMarker → слайды.
Запуск с хоста: python3 scripts/build_shorts04.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)
import generate_short as gs  # noqa: E402

BASE = gs.BASE
SCENARIO_PATH = "/root/projects/YouTube Channel/готовые_сценарии/Тексты_под_озвучку/Месяц_1/Шортс_04 — Пытались закрывать сделки силами ИИ Вот чем закончилось.txt"
TITLE = "04 - Пытались закрывать сделки силами ИИ"

# (sid, block, component, title, subtitle, payload)
# Стандартный OutroSlide IT2B — всегда одинаковый (как в p19/p20/p21):
IT2B_OUTRO = {
    "logo": "/media/it2b_logo_v2.png",
    "qr_code": "/media/it2b_qr_v2.png",
    "handle": "",
    "headline": "",
}

# BGM IT2B: играет с 0-й секунды таймлайна, но начало трека обрезано (эталон p35 ≈ 20с).
BGM_MEDIA_OFFSET_MS = 20000
BGM_SRC = "/media/bgm_automated_horizon_v2.mp3"

SLIDES = [
    ("s04_01", "hook", "ChatMockupSlide", "Бот вместо <em>продавца</em>", "сделки уходят тихо", {
        "variant": "tech", "bot_name": "AI-агент", "bot_subtitle": "закрывает сделки", "bot_avatar": "AI",
        "messages": [
            {"role": "user", "text": "Сможете отгрузить тремя машинами в разные склады?", "start_time": 0},
            {"role": "assistant", "text": "Такой информации нет в базе", "start_time": 1200},
            {"role": "user", "text": "Ок, поищу другого поставщика", "start_time": 2400},
        ]}),
    ("s04_02", "most", "ComparisonTable", "Сильнее <em>человека</em>?", "только на прайсе", {
        "variant": "tech", "headers": ["", "Бот", "Продавец"],
        "items": [
            {"id": "r1", "label": "Знает прайс", "values": [True, True], "start_time": 0},
            {"id": "r2", "label": "Считает сроки", "values": [True, True], "start_time": 800},
            {"id": "r3", "label": "Держит торг", "values": [False, True], "start_time": 1600},
            {"id": "r4", "label": "Ищет вариант", "values": [False, True], "start_time": 2400},
        ]}),
    ("s04_03", "proof", "ArchitectureDiagram", "Агент — <em>квалификатор</em>", "торг забирает человек", {
        "variant": "tech", "show_data_flow": True,
        "nodes": [
            {"id": "in1", "title": "Запрос", "subtitle": "логистика", "icon": "lucide:message-circle", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
            {"id": "core1", "title": "ИИ-агент", "subtitle": "факты и прайс", "icon": "lucide:cpu", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["out1"]},
            {"id": "out1", "title": "Нестандарт", "subtitle": "стоп", "icon": "lucide:alert-triangle", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["hand1"]},
            {"id": "hand1", "title": "Менеджер", "subtitle": "ведёт торг", "icon": "lucide:user-check", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []},
        ]}),
    ("s04_04", "proof", "ReceiptCard", "", "", {
        "variant": "tech", "title": "ЗАКАЗ НА €25 000", "subtitle": "нестандартный торг", "currency": "€",
        "total_text": "ПОТЕРЯНО", "footer_text": "СДЕЛКА НЕ СОСТОЯЛАСЬ", "total_start_time": 2600,
        "items": [
            {"name": "Комплектующие", "price": 16000, "start_time": 300},
            {"name": "Логистика", "price": 6000, "start_time": 1100},
            {"name": "Монтаж", "price": 3000, "start_time": 1900},
        ]}),
    ("s04_05", "proof", "InfographicCards", "Факты <em>против</em> торга", "что умеет бот", {
        "variant": "tech",
        "items": [
            {"id": 1, "label": "Прайс и наличие", "value": "Да", "trend": "ответ за секунду", "color": "var(--item-accent-1)", "icon": "heroicons:document-text", "start_time": 0},
            {"id": 2, "label": "Сроки доставки", "value": "Да", "trend": "считает точно", "color": "var(--item-accent-2)", "icon": "heroicons:truck", "start_time": 800},
            {"id": 3, "label": "Нестандартный торг", "value": "Нет", "trend": "только человек", "color": "var(--item-accent-3)", "icon": "heroicons:hand-raised", "start_time": 1600},
            {"id": 4, "label": "Сделка", "value": "€0", "trend": "клиент ушёл", "color": "var(--item-accent-4)", "icon": "heroicons:x-circle", "start_time": 2400},
        ]}),
    ("s04_06", "proof", "ProcessFunnel", "Маршрут <em>запроса</em>", "до живого человека", {
        "variant": "tech", "layout": "horizontal",
        "steps": [
            {"label": "Запрос", "count": 100, "icon": "heroicons:chat-bubble-left", "color": "var(--item-accent-1)", "start_time": 0},
            {"label": "Прайс", "count": 70, "icon": "heroicons:document-text", "color": "var(--item-accent-2)", "start_time": 800},
            {"label": "Сроки", "count": 40, "icon": "heroicons:truck", "color": "var(--item-accent-3)", "start_time": 1600},
            {"label": "Торг", "count": 5, "icon": "heroicons:user", "color": "var(--item-accent-4)", "start_time": 2400},
        ]}),
    ("s04_07", "proof", "MetricScales", "Где <em>делегируют</em> лишнее", "и теряют сделки", {
        "variant": "tech", "title": "Где делегируют лишнее", "subtitle": "и теряют сделки",
        "metrics": [
            {"id": 1, "label": "Вопросы по прайсу", "percentage": 95, "color": "linear-gradient(to right, #34D399, #2DD4BF)", "start_time": 0},
            {"id": 2, "label": "Нестандартный торг", "percentage": 20, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 800},
            {"id": 3, "label": "Сложные сделки", "percentage": 5, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 1600},
        ]}),
    ("s04_08", "payoff", "PremiumChecklist", "Территория <em>человека</em>", "за пределами регламента", {
        "variant": "tech",
        "items": [
            {"label": "Квалификация", "desc": "ИИ собирает вводные", "icon": "heroicons:clipboard-document-check", "color": "brand-blue", "start_time": 0},
            {"label": "Нестандартный торг", "desc": "чат забирает человек", "icon": "heroicons:user-group", "color": "brand-amber", "start_time": 800},
            {"label": "Регламент", "desc": "граница полномочий", "icon": "lucide:fence", "color": "brand-green", "start_time": 1600},
        ]}),
    ("s04_09", "payoff", "AnimatedStatsSlide", "Автоматизированный <em>отказ</em>", "если поручить закрытие", {
        "variant": "tech",
        "stats": [
            {"label": "Решает ИИ", "value": 90, "suffix": "%", "color": "var(--item-accent-2)", "icon": "lucide:bot", "start_time": 0},
            {"label": "Сложные сделки", "value": 10, "suffix": "%", "color": "var(--item-accent-3)", "icon": "lucide:users", "start_time": 800},
            {"label": "Передал человеку", "value": 100, "suffix": "%", "color": "var(--item-accent-1)", "icon": "lucide:arrow-right-left", "start_time": 1600},
        ]}),
    ("s04_10", "cta", "OutroSlide", "", "", {
        "variant": "tech", **IT2B_OUTRO,
    }),
]


def validate(comp, payload):
    r = requests.post(f"{BASE}/components/{comp}/validate", json={"payload": payload})
    r.raise_for_status()
    return r.json()


def compute_times(voice_clips):
    by = {vc["section_id"]: vc for vc in voice_clips}
    proof = by["proof"]; payoff = by["payoff"]
    proof_dur = proof["end_time"] - proof["start_time"]
    payoff_dur = payoff["end_time"] - payoff["start_time"]
    n_proof = sum(1 for s in SLIDES if s[1] == "proof")
    n_payoff = sum(1 for s in SLIDES if s[1] == "payoff")
    step_p = max(2000, min(5200, int(proof_dur / n_proof)))
    step_pay = max(2000, min(4200, int(payoff_dur / n_payoff)))
    starts = {}
    for sid, block, *_ in SLIDES:
        if block == "hook": starts[sid] = float(by["hook"]["start_time"])
        elif block == "most": starts[sid] = float(by["most"]["start_time"])
        elif block == "payoff": starts[sid] = by["payoff"]["start_time"] + (int(sid[-2:]) - 8) * step_pay
        elif block == "cta": starts[sid] = float(by["hook_out"]["start_time"])
    pi = 0
    for sid, block, *_ in SLIDES:
        if block == "proof":
            starts[sid] = proof["start_time"] + pi * step_p
            pi += 1
    # enforce global monotonic >= 2000ms
    ordered = [s[0] for s in SLIDES]
    for i in range(1, len(ordered)):
        starts[ordered[i]] = max(starts[ordered[i]], starts[ordered[i - 1]] + 2000)
    return starts


def normalize_bgm_track(pres_id):
    """Фоновая музыка IT2B — всегда на дорожке `bgm` (vol 0.15) и **покрывает весь таймлайн
    до EndMarker**. Если трек короче ролика — выкладываем несколько клипов подряд (loop)."""
    d = requests.get(f"{BASE}/presentations/{pres_id}").json()
    tracks = d["audio_timeline"]["tracks"]
    main = next(t for t in tracks if t["id"] == "main")
    end_marker = next((s["start_time"] for s in d["slides"] if s["component"] == "EndMarkerSlide"), None)
    video_end = end_marker or (max((c["end_time"] for c in main["clips"]), default=0) + 2000)

    dur = requests.get(f"{BASE}/ai/audio-duration", params={"file_path": BGM_SRC}).json()["duration_ms"]
    usable = max(1000.0, dur - BGM_MEDIA_OFFSET_MS)
    clips, i, t = [], 0, 0.0
    while t < video_end - 1:
        length = min(usable, video_end - t)
        clips.append({
            "id": f"bgm_{i}", "name": BGM_SRC.split("/")[-1], "src": BGM_SRC,
            "start_time": round(t), "end_time": round(t + length),
            "media_offset": BGM_MEDIA_OFFSET_MS, "volume": 0.15, "muted": False,
            "type": "audio", "playbackRate": 1.0,
        })
        t += length
        i += 1

    bgm = next(t for t in tracks if t["id"] == "bgm")
    overlay = next(t for t in tracks if t["id"] == "overlay")
    bgm["clips"] = clips
    overlay["clips"] = [c for c in overlay.get("clips", []) if c.get("type") != "audio"]
    requests.put(f"{BASE}/presentations/{pres_id}", json={"audio_timeline": {"tracks": tracks}})
    print(f"BGM: {len(clips)} клип(ов) на дорожке 'bgm', vol 0.15, offset {BGM_MEDIA_OFFSET_MS}ms, "
          f"покрытие 0→{round(video_end)}ms (трек {round(dur)}ms)")


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
