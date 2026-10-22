#!/usr/bin/env python3
"""Длинное_02 «Что ИИ-агент реально умеет в продажах» — озвучка (7 блоков) + таймлайн + EndMarker.

Отличия от шортсов: папка «Длинные» (folder_id=1), 7 семантических блоков, спокойные пресеты.
Слайды добавляются отдельным скриптом (`build_long02_slides.py`) по длительностям отсюда.
Запуск с хоста: python3 scripts/build_long02.py
"""
import os
import re
import sys
import time

import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)

BASE = "http://localhost:8001"
FOLDER_LONG = 1
SCENARIO_MD = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Месяц_1/Длинное_03 — Почему сайты на Tilda не конвертируют и при чём здесь архитектура.md"
TITLE = "03 - Почему сайты на Tilda не конвертируют"

VOICE = "Charon"
AUDIO_PROFILE = "A confident and dynamic tech expert with a deep, resonant voice. Clear and projecting, never whispers or mumbles."
SCENE = "A high-end tech YouTube channel for IT2B — business automation and AI."
BGM_END_MS = 2000

# Спокойнее, чем шортсовые пресеты (длинный формат, ~13 мин)
LONG_PRESETS = {
    "tezis": {"pace": "Confident and brisk. Clear articulation, natural short pauses.", "tone": "Direct, expert, no hype.", "style": "Thesis — set the stakes.", "temperature": 0.8},
    "hype": {"pace": "Conversational and engaging, with slight irony.", "tone": "Storytelling, grounded.", "style": "Hype vs reality.", "temperature": 0.8},
    "how": {"pace": "Measured and thoughtful. Explain clearly, don't rush.", "tone": "Analytical, pragmatic.", "style": "How I think about the task.", "temperature": 0.75},
    "project": {"pace": "Narrative and vivid, with tension at the conflict.", "tone": "Honest, concrete.", "style": "Real project story.", "temperature": 0.8},
    "where": {"pace": "Calm, honest, matter-of-fact.", "tone": "Straightforward.", "style": "Where it doesn't work.", "temperature": 0.75},
    "conclusion": {"pace": "Firm and conclusive. Every word lands.", "tone": "Wise, memorable.", "style": "Conclusion — one idea.", "temperature": 0.8},
    "cta": {"pace": "Warm and personal, unhurried.", "tone": "Friendly, inviting.", "style": "Soft CTA.", "temperature": 0.8},
}
SECTION_PRESET = {
    "ТЕЗИС": "tezis", "ХАЙП VS РЕАЛЬНОСТЬ": "hype", "КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ": "how",
    "РЕАЛЬНЫЙ ПРОЕКТ": "project", "ГДЕ НЕ РАБОТАЕТ": "where", "ВЫВОД": "conclusion", "МЯГКИЙ CTA": "cta",
}


def api_post(path, data=None):
    r = requests.post(f"{BASE}{path}", json=data)
    r.raise_for_status()
    return r.json()


def api_get(path, **params):
    r = requests.get(f"{BASE}{path}", params=params or None)
    r.raise_for_status()
    return r.json()


def parse_md_sections(path):
    raw = open(path, encoding="utf-8").read()
    body = raw.split("## СЦЕНАРИЙ", 1)[1].split("## ОПИСАНИЕ ДЛЯ YOUTUBE", 1)[0]
    parts = re.split(r"###\s*\[([^\]]+)\][^\n]*", body)
    # parts: [pre, label1, text1, label2, text2, ...]
    sections = []
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        text = parts[i + 1] if i + 1 < len(parts) else ""
        paras, cur = [], []
        for ln in text.splitlines():
            t = ln.strip()
            if not t:
                if cur:
                    paras.append(" ".join(cur)); cur = []
                continue
            if t.startswith("#") or t.startswith("[ВИЗУАЛ") or re.match(r"^\*\*[^*]+\*\*$", t):
                continue
            t = re.sub(r"\[(?:ВИЗУАЛ|визуал)[^\]]*\]", " ", t)
            cur.append(re.sub(r"\s+", " ", t).strip())
        if cur:
            paras.append(" ".join(cur))
        sections.append({"id": SECTION_PRESET.get(label.upper(), "project"), "label": label,
                         "text": "\n\n".join(paras)})
    return sections


def generate_tts(pres_id, text, batch_id, preset):
    p = LONG_PRESETS[preset]
    print(f"  TTS [{preset}]: {text[:60]}...")
    return api_post(f"/ai/presentations/{pres_id}/generate-speech", {
        "text": text, "voice": VOICE, "audio_profile": AUDIO_PROFILE,
        "style": p["style"], "pace": p["pace"], "tone": p["tone"],
        "scene": SCENE, "temperature": p["temperature"], "batch_id": batch_id,
    })


def main():
    sections = parse_md_sections(SCENARIO_MD)
    print(f"Sections: {[s['label'] for s in sections]}")
    pres = api_post("/presentations/", {"title": TITLE, "folder_id": FOLDER_LONG})
    pres_id = pres["id"]
    print(f"Created presentation {pres_id}")
    batch_id = f"long_03_{int(time.time())}"

    voice_clips = []
    for s in sections:
        media = generate_tts(pres_id, s["text"], batch_id, s["id"])
        dur = api_get("/ai/audio-duration", file_path=media["file_path"])["duration_ms"]
        voice_clips.append({"id": s["id"], "label": s["label"], "src": media["file_path"],
                            "media_id": media["id"], "duration_ms": dur,
                            "ai_settings": media.get("ai_settings", {})})
        print(f"    [{s['id']}] {s['label']}: {dur:.0f}ms")

    GAP = 400
    t = 0.0
    main_clips = []
    for i, vc in enumerate(voice_clips):
        vc["start_time"] = t
        vc["end_time"] = t + vc["duration_ms"]
        main_clips.append({"id": f"ai_{i}", "name": os.path.basename(vc["src"]), "src": vc["src"],
                           "start_time": vc["start_time"], "end_time": vc["end_time"],
                           "media_offset": 0, "volume": 1.0, "muted": False, "type": "ai_voice",
                           "ai_settings": vc["ai_settings"], "playbackRate": 1.0})
        print(f"  {vc['label']}: {vc['start_time']:.0f} → {vc['end_time']:.0f}ms")
        t = vc["end_time"] + GAP
    total = t - GAP
    print(f"  TOTAL: {total:.0f}ms ({total/1000:.1f}s)")

    timeline = {"tracks": [
        {"id": "main", "type": "voiceover", "clips": main_clips},
        {"id": "overlay", "type": "voiceover", "clips": []},
        {"id": "bgm", "type": "bgm", "clips": []},
        {"id": "sfx", "type": "sfx", "clips": []},
    ]}
    requests.put(f"{BASE}/presentations/{pres_id}", json={"audio_timeline": timeline}).raise_for_status()

    end_ms = total + 1000
    api_post(f"/presentations/{pres_id}/slides", {
        "slide_id": f"end_{pres_id}", "component": "EndMarkerSlide", "start_time": end_ms,
        "order_index": 999, "layout": "col", "data": {"payload": {}},
    })
    print(f"  EndMarker at {end_ms:.0f}ms")
    print(f"\nPRES_ID={pres_id}")
    print(f"Bounds: " + " | ".join(f"{vc['label']} {vc['start_time']:.0f}-{vc['end_time']:.0f}" for vc in voice_clips))


if __name__ == "__main__":
    main()
