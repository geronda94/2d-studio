#!/usr/bin/env python3
"""Длинное_06 «MVP за несколько недель» — озвучка (7 блоков) + таймлайн + EndMarker.

Сценарий в формате 6 глав (VO/СЛАЙДЫ); финальная глава делится на ВЫВОД и CTA,
чтобы уложиться в стандартный 7-блочный пайплайн. Последняя глава = вывод + CTA.
Запуск с хоста: python3 scripts/build_long06.py
"""
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401

BASE = "http://localhost:8002"
FOLDER_LONG = 1
SCENARIO_TXT = "/root/projects/YouTube Channel/it2b/готовые_сценарии/Тексты_под_озвучку/Месяц_2/Длинное_06 — MVP за несколько недель.txt"
TITLE = "06 - MVP за несколько недель"

VOICE = "Charon"
AUDIO_PROFILE = "A confident and dynamic tech expert with a deep, resonant voice. Clear and projecting, never whispers or mumbles."
SCENE = "A high-end tech YouTube channel for IT2B — business automation and AI."
SPEEDUP = 1.08
GAP = 200

LONG_PRESETS = {
    "tezis": {"pace": "Confident and brisk. Clear articulation, natural short pauses.", "tone": "Direct, expert, no hype.", "style": "Thesis — set the stakes.", "temperature": 0.8},
    "hype": {"pace": "Conversational and engaging, with slight irony.", "tone": "Storytelling, grounded.", "style": "Hype vs reality.", "temperature": 0.8},
    "how": {"pace": "Measured and thoughtful. Explain clearly, don't rush.", "tone": "Analytical, pragmatic.", "style": "How I think about the task.", "temperature": 0.75},
    "project": {"pace": "Narrative and vivid, with tension at the conflict.", "tone": "Honest, concrete.", "style": "Real project story.", "temperature": 0.8},
    "where": {"pace": "Calm, honest, matter-of-fact.", "tone": "Straightforward.", "style": "Where it doesn't work.", "temperature": 0.75},
    "conclusion": {"pace": "Firm and conclusive. Every word lands.", "tone": "Wise, memorable.", "style": "Conclusion — one idea.", "temperature": 0.8},
    "cta": {"pace": "Warm and personal, unhurried.", "tone": "Friendly, inviting.", "style": "Soft CTA.", "temperature": 0.8},
}
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]


def api_post(path, data=None):
    r = requests.post(f"{BASE}{path}", json=data)
    r.raise_for_status()
    return r.json()


def api_get(path, **params):
    r = requests.get(f"{BASE}{path}", params=params or None)
    r.raise_for_status()
    return r.json()


def parse_txt(path):
    raw = open(path, encoding="utf-8").read().strip()
    paras = [" ".join(p.split()) for p in raw.split("\n\n") if p.strip()]
    # 8 абзацев: 1 тезис, 2 миф, 3 метод, 4-6 проект, 7 границы, 8 вывод+CTA
    assert len(paras) == 8, f"ожидал 8 абзацев, получил {len(paras)}"
    tezis, hype, how = paras[0], paras[1], paras[2]
    project = " ".join(paras[3:6])
    where = paras[6]
    final = paras[7]
    marker = "Если у тебя есть идея"
    i = final.find(marker)
    if i < 0:
        conclusion, cta = final, ""
    else:
        conclusion, cta = final[:i].strip(), final[i:].strip()
    texts = {"tezis": tezis, "hype": hype, "how": how, "project": project,
             "where": where, "conclusion": conclusion, "cta": cta}
    return [{"id": s, "label": s.upper(), "text": texts[s]} for s in SECTIONS]


def generate_tts(pres_id, text, batch_id, preset):
    p = LONG_PRESETS[preset]
    print(f"  TTS [{preset}]: {text[:60]}...")
    return api_post(f"/ai/presentations/{pres_id}/generate-speech", {
        "text": text, "voice": VOICE, "audio_profile": AUDIO_PROFILE,
        "style": p["style"], "pace": p["pace"], "tone": p["tone"],
        "scene": SCENE, "temperature": p["temperature"], "batch_id": batch_id,
    })


def speedup_and_upload(pres_id, media, factor):
    import subprocess
    src = media["file_path"]
    host = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", src.lstrip("/"))
    out = host.replace(".wav", f"_sp{int(factor * 100)}.wav")
    subprocess.run(["ffmpeg", "-y", "-i", host, "-filter:a", f"atempo={factor}", out],
                   check=True, capture_output=True)
    with open(out, "rb") as fh:
        r = requests.post(f"{BASE}/presentations/{pres_id}/media",
                          files={"file": (os.path.basename(out), fh, "audio/wav")})
    r.raise_for_status()
    try:
        os.remove(out)
    except OSError:
        pass
    return r.json()


def main():
    sections = parse_txt(SCENARIO_TXT)
    print(f"Sections: {[s['id'] for s in sections]}")
    for s in sections:
        print(f"  {s['id']}: {len(s['text'].split())} слов")
    pres = api_post("/presentations/", {"title": TITLE, "folder_id": FOLDER_LONG})
    pres_id = pres["id"]
    print(f"Created presentation {pres_id}")
    batch_id = f"long_06_{int(time.time())}"

    voice_clips = []
    for s in sections:
        media = generate_tts(pres_id, s["text"], batch_id, s["id"])
        if SPEEDUP > 1.01:
            media = speedup_and_upload(pres_id, media, SPEEDUP)
            print(f"    speedup x{SPEEDUP} → {media['file_path']}")
        dur = api_get("/ai/audio-duration", file_path=media["file_path"])["duration_ms"]
        voice_clips.append({"id": s["id"], "label": s["label"], "src": media["file_path"],
                            "media_id": media["id"], "duration_ms": dur,
                            "ai_settings": media.get("ai_settings", {})})
        print(f"    [{s['id']}]: {dur:.0f}ms")

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
    print("Bounds: " + " | ".join(f"{vc['label']} {vc['start_time']:.0f}-{vc['end_time']:.0f}" for vc in voice_clips))


if __name__ == "__main__":
    main()
