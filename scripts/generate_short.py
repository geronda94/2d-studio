#!/usr/bin/env python3
"""
Пайплайн генерации шортс-презентации из сценария.

Этапы:
1. Создаёт презентацию в папке "Шортсы" проекта IT2B
2. Генерирует TTS для каждой сцены
3. Получает длительности аудио через ffprobe
4. Транскрибирует через Whisper (word-level timestamps)
5. Рассчитывает boundaries сцен по первым словам
6. Создаёт слайды (1 слайд на 3-5 сек, без повторов компонентов в ближайших 4)
7. Собирает audio_timeline (voice + BGM на 15%)

Запуск: docker compose exec backend python scripts/generate_short.py --short 2
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from typing import Any

import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8002"
API = f"{BASE}"
FOLDER_ID_SHORTS = 2  # Папка "Шортсы" в проекте IT2B

# ─── Voice settings — per-segment presets for emotional contrast ───────
# 🔒 LOCKED BASE TEMPLATE (calibrated on p/16, 2026-09-14)
# Gemini TTS: "very fast" prompt, no ffmpeg speedup
# Pauses: 200ms between blocks only, continuous inside
# Slides: 3-5s each, ~14 slides per ~53s short
# Do NOT change presets without re-calibrating on a new reference presentation.
VOICE = "Charon"
AUDIO_PROFILE = "A confident and dynamic tech expert with a deep, resonant voice. Clear and projecting, never whispers or mumbles."
SCENE = "A high-end tech YouTube channel for IT2B — business automation and AI."

# Base defaults (used only as fallback when no preset matches)
STYLE = "Engaging and professional."
PACE = "Very fast, rapid-fire, urgent. Squeeze words together, minimal gaps."
TONE = "Authoritative, convincing, and lively."
TEMPERATURE = 0.8

# ====================================================================
# BASE TEMPLATE — pace/tone/style presets (locked after p/16 calibration)
# Target: ~55s for a typical short (5 semantic blocks, ~500 words)
# Speed: "very fast" Gemini prompt + no ffmpeg speedup (speedup=1.0)
# Pauses: 200ms BETWEEN blocks only; continuous flow INSIDE blocks.
# ====================================================================
VOICE_PRESETS = {
    "hook": {
        "pace": "Very fast, rapid-fire, urgent. Squeeze words together, minimal gaps. Like a 5-second elevator pitch you need to finish before the doors close.",
        "tone": "Provocative, sharp, alarming.",
        "style": "Hook — grab attention in 3 seconds.",
        "temperature": 0.9,
    },
    "most": {
        "pace": "Very fast, brisk and driving. Keep pushing forward, barely pause between sentences. Urgent storytelling.",
        "tone": "Storytelling, slightly ironic, grounded.",
        "style": "Bridge — connect hook to proof.",
        "temperature": 0.8,
    },
    "proof_narrative": {
        "pace": "Very fast, rapid-fire. Deliver information densely, minimal breathing space between sentences. News-anchor speed or faster.",
        "tone": "Grounded, vivid, confident.",
        "style": "Narrative — tell the story fast.",
        "temperature": 0.8,
    },
    "payoff": {
        "pace": "Fast, firm, decisive. No dragging, no drawn-out words. Every word earns its place.",
        "tone": "Wise, conclusive, memorable.",
        "style": "Payoff — the lesson.",
        "temperature": 0.8,
    },
    "cta": {
        "pace": "Fast and personal. Straight to the point like a friend texting you back quickly. No filler.",
        "tone": "Friendly, direct, inviting.",
        "style": "CTA — personal invitation.",
        "temperature": 0.8,
    },
}

# Map section.id → preset name (one chunk per section, no intra-block splits)
SECTION_PRESET = {
    "hook": "hook",
    "most": "most",
    "proof": "proof_narrative",
    "payoff": "payoff",
    "hook_out": "cta",
}

# ─── Scenario data ──────────────────────────────────────────────────────
SCENARIOS = {
    2: {
        "title": "02 - ИИ-агент начал врать клиентам",
        "sections": [
            {
                "id": "hook",
                "label": "HOOK",
                "text": "Поставил ИИ-агента разгрузить поддержку. А он пообещал клиенту скидку, которой в природе нет.",
                "time_range": "0-3",
            },
            {
                "id": "most",
                "label": "МОСТ",
                "text": "И по факту, вместо роста продаж, ты смотришь, как нейросеть радостно раздаёт твои деньги.",
                "time_range": "3-8",
            },
            {
                "id": "proof",
                "label": "PROOF",
                "text": (
                    "Смотри, как это обычно бывает. Месяц всё работает идеально. "
                    "Агент отвечает на частые вопросы. Разгрузил поддержку наполовину. "
                    "И поначалу всё выглядит отлично. "
                    "Но потом приходит оптовый заказчик: А если возьму партию на полгода? "
                    "Агент выдаёт: Сделаем персональную скидку 30%. "
                    "Сделка на 15 000 евро встаёт намертво. "
                    "Клиент скринит экран. Ждёт свои условия. "
                    "И самое страшное — ты узнаёшь об этом последним. "
                    "Нейросеть просто угадывает продолжение текста. Ей дали инструкцию отвечай клиентам. "
                    "Хотя нужно было задать жёсткий коридор. Шаг в сторону — зови живого менеджера."
                ),
                "time_range": "8-45",
            },
            {
                "id": "payoff",
                "label": "PAYOFF",
                "text": "Поэтому учти один нюанс. ИИ-агент без чётко прописанных границ — это просто фантазёр с прямым доступом к твоему кошельку.",
                "time_range": "45-55",
            },
            {
                "id": "hook_out",
                "label": "HOOK OUT",
                "text": "Скинь мне лично в Telegram инструкцию своего бота — я посмотрю, где он может слить сделку.",
                "time_range": "55-60",
            },
        ],
    },
    3: {
        "title": "03 - Менеджер уволился и унёс базу",
        "sections": [
            {
                "id": "hook",
                "label": "HOOK",
                "text": "Менеджер уволился. И забрал половину твоей базы прямо в своём личном WhatsApp.",
                "time_range": "0-3",
            },
            {
                "id": "most",
                "label": "МОСТ",
                "text": "Ты срочно покупаешь дорогую CRM, надеясь всё исправить. А она просто фиксирует этот хаос за твои же деньги.",
                "time_range": "3-8",
            },
            {
                "id": "proof",
                "label": "PROOF",
                "text": (
                    "Смотри, как это бывает. Покупаешь годовую подписку на Hubspot. Нанимаешь интегратора. "
                    "Ждёшь прозрачных продаж. "
                    "И поначалу все довольны. "
                    "Но через три месяца открываешь воронку — а там пусто. "
                    "Сделка на 30 тысяч евро висит в статусе в работе. Хотя клиент уже неделю как купил у конкурента. "
                    "Менеджеры заносят данные в пятницу вечером, чисто для галочки. Вся переписка идёт с личных телефонов. "
                    "Никто не прописал жёсткий регламент до покупки. Софт просто натянули поверх бардака."
                ),
                "time_range": "8-45",
            },
            {
                "id": "payoff",
                "label": "PAYOFF",
                "text": "Поэтому учти: CRM ничего не исправляет. Сначала ты строишь порядок на бумаге, и только потом покупаешь инструмент.",
                "time_range": "45-55",
            },
            {
                "id": "hook_out",
                "label": "HOOK OUT",
                "text": "Скинь мне лично в Telegram скриншот своей воронки продаж — я покажу, где вы прямо сейчас теряете деньги.",
                "time_range": "55-60",
            },
        ],
    },
}

# ─── BGM file (from IT2B media library) ─────────────────────────────────
BGM_FILE = "/media/bgm_automated_horizon_v2.mp3"  # Automated_Horizon.mp3 (v2 — cache-bust Cloudflare)


def api_post(path: str, data: dict = None, **kwargs) -> dict:
    url = f"{API}{path}"
    r = requests.post(url, json=data, **kwargs)
    r.raise_for_status()
    return r.json()


def api_get(path: str) -> Any:
    url = f"{API}{path}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def generate_tts(presentation_id: int, text: str, batch_id: str, preset: str = None, speedup: float = 1.0) -> dict:
    """Generate TTS for a text block with optional preset, return MediaFile.
    speedup: ffmpeg atempo factor (>1.0 = faster). Applied after Gemini TTS."""
    if preset and preset in VOICE_PRESETS:
        p = VOICE_PRESETS[preset]
        pace = p["pace"]
        tone = p["tone"]
        style = p["style"]
        temperature = p["temperature"]
    else:
        pace = PACE
        tone = TONE
        style = STYLE
        temperature = TEMPERATURE
    payload = {
        "text": text,
        "voice": VOICE,
        "audio_profile": AUDIO_PROFILE,
        "style": style,
        "pace": pace,
        "tone": tone,
        "scene": SCENE,
        "temperature": temperature,
        "batch_id": batch_id,
    }
    print(f"  TTS [{preset or 'default'}]: {text[:60]}...")
    result = api_post(f"/ai/presentations/{presentation_id}/generate-speech", payload)
    print(f"  → {result['file_path']} (id={result['id']})")

    # Apply atempo speedup if requested
    if speedup > 1.01:
        src = result["file_path"]
        if src.startswith("/media/"):
            src_full = f"/app/backend{src}"
        else:
            src_full = src
        sped = src_full.replace(".wav", f"_sp{int(speedup*100)}.wav")
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_full, "-filter:a", f"atempo={speedup}", sped],
            capture_output=True, timeout=30,
        )
        # Upload sped-up file via media endpoint
        import requests as _req
        with open(sped, "rb") as f:
            files = {"file": (os.path.basename(sped), f, "audio/wav")}
            r = _req.post(f"{BASE}/presentations/{presentation_id}/media", files=files)
            if r.status_code in (200, 201):
                result = r.json()
                print(f"  → sped up {speedup}x → {result['file_path']}")
            else:
                print(f"  → speedup upload failed ({r.status_code}), using original")
        # Cleanup
        for pth in (sped,):
            try: os.remove(pth)
            except: pass

    return result


def get_duration(file_path: str) -> float:
    """Get audio duration in ms via ffprobe endpoint."""
    result = api_get(f"/ai/audio-duration?file_path={file_path}")
    return result["duration_ms"]


def create_presentation(title: str) -> int:
    """Create presentation in shorts folder, return id."""
    result = api_post("/presentations/", {
        "title": title,
        "folder_id": FOLDER_ID_SHORTS,
    })
    print(f"Created presentation: {title} (id={result['id']})")
    return result["id"]


def create_slide(presentation_id: int, slide_id: str, component: str,
                 start_time: float, order_index: int, title: str = "",
                 subtitle: str = "", layout: str = "col",
                 payload: dict = None) -> dict:
    """Create a single slide."""
    data = {"payload": payload or {}}
    body = {
        "slide_id": slide_id,
        "component": component,
        "start_time": start_time,
        "order_index": order_index,
        "title": title,
        "subtitle": subtitle,
        "layout": layout,
        "data": data,
    }
    return api_post(f"/presentations/{presentation_id}/slides", body)


def build_audio_timeline(voice_clips: list, bgm_path: str) -> dict:
    """Build audio_timeline with voiceover + BGM at 15%."""
    main_clips = []
    for i, vc in enumerate(voice_clips):
        main_clips.append({
            "id": f"ai_{i}",
            "name": os.path.basename(vc["file_path"]),
            "src": vc["file_path"],
            "start_time": vc["start_time"],
            "end_time": vc["end_time"],
            "media_offset": 0,
            "volume": 1.0,
            "muted": False,
            "type": "ai_voice",
            "ai_settings": vc.get("ai_settings", {}),
            "playbackRate": 1.0,
        })

    # BGM on overlay track at 15% volume, looping
    total_duration = voice_clips[-1]["end_time"] if voice_clips else 60000
    bgm_clips = [{
        "id": "bgm_0",
        "name": os.path.basename(bgm_path),
        "src": bgm_path,
        "start_time": 0,
        "end_time": total_duration + 2000,
        "media_offset": 0,
        "volume": 0.15,
        "muted": False,
        "type": "audio",
        "playbackRate": 1.0,
    }]

    return {
        "tracks": [
            {"id": "main", "type": "voiceover", "clips": main_clips},
            {"id": "overlay", "type": "voiceover", "clips": bgm_clips},
            {"id": "bgm", "type": "bgm", "clips": []},
            {"id": "sfx", "type": "sfx", "clips": []},
        ]
    }


def load_scenario_from_file(path: str, title: str = None) -> dict:
    """Load staccato teleprompter text, auto-split into sections by paragraph position.

    Convention: para[0]=hook, para[1]=most, para[-2]=payoff, para[-1]=cta,
    everything in between joined as proof.
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()
    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    # Flatten single newlines inside a paragraph into spaces
    paras = [" ".join(p.split("\n")).strip() for p in paras]
    if len(paras) < 4:
        raise ValueError(f"Need at least 4 paragraphs (hook/most/proof+payoff/cta), got {len(paras)} in {path}")
    if title is None:
        title = os.path.splitext(os.path.basename(path))[0]
    return {
        "title": title,
        "sections": [
            {"id": "hook", "label": "HOOK", "text": paras[0], "time_range": "0-3"},
            {"id": "most", "label": "МОСТ", "text": paras[1], "time_range": "3-8"},
            {"id": "proof", "label": "PROOF", "text": " ".join(paras[2:-2]), "time_range": "8-45"},
            {"id": "payoff", "label": "PAYOFF", "text": paras[-2], "time_range": "45-55"},
            {"id": "hook_out", "label": "HOOK OUT", "text": paras[-1], "time_range": "55-60"},
        ],
    }


def run_pipeline(short_num: int = None, scenario: dict = None):
    if scenario is None:
        scenario = SCENARIOS[short_num]
    label = f"Шортс #{short_num}" if short_num is not None else "FILE"
    print(f"\n{'='*60}")
    print(f"  PIPELINE: {label} — {scenario['title']}")
    print(f"{'='*60}\n")

    # 1. Create presentation
    pres_id = create_presentation(scenario["title"])
    batch_id = f"short_{short_num if short_num is not None else 'file'}_{int(time.time())}"

    # 2. Generate TTS — one call per semantic block, continuous flow inside.
    # Pauses exist ONLY between blocks (200ms timeline gaps below).
    print(f"\n--- Generating TTS (1 call per semantic block) ---")
    voice_clips = []
    for section in scenario["sections"]:
        preset = SECTION_PRESET.get(section["id"], "proof_narrative")
        media = generate_tts(pres_id, section["text"], batch_id, preset=preset)
        duration_ms = get_duration(media["file_path"])
        voice_clips.append({
            "section_id": section["id"],
            "label": section["label"],
            "preset": preset,
            "file_path": media["file_path"],
            "media_id": media["id"],
            "ai_settings": media.get("ai_settings", {}),
            "duration_ms": duration_ms,
        })
        print(f"  [{preset}] {section['label']}: {duration_ms}ms")

    # 3. Calculate timeline positions
    print(f"\n--- Calculating timeline ---")
    current_time = 0.0
    for vc in voice_clips:
        vc["start_time"] = current_time
        vc["end_time"] = current_time + vc["duration_ms"]
        current_time = vc["end_time"] + 200  # 200ms gap between clips
        print(f"  {vc['label']}: {vc['start_time']:.0f}ms → {vc['end_time']:.0f}ms ({vc['duration_ms']:.0f}ms)")

    total_duration = current_time
    print(f"  TOTAL: {total_duration:.0f}ms ({total_duration/1000:.1f}s)")

    # 4. Build audio timeline
    print(f"\n--- Building audio timeline ---")
    timeline = build_audio_timeline(voice_clips, BGM_FILE)
    r = requests.put(f"{API}/presentations/{pres_id}", json={"audio_timeline": timeline})
    r.raise_for_status()
    print(f"  Audio timeline saved ({len(timeline['tracks'])} tracks)")

    # 5. End marker
    end_time = total_duration + 1000
    create_slide(pres_id, f"end_{pres_id}", "EndMarkerSlide", end_time, 999, layout="col")
    print(f"  EndMarkerSlide at {end_time:.0f}ms")

    print(f"\n{'='*60}")
    print(f"  DONE: Presentation {pres_id} created with {len(voice_clips)} audio clips")
    print(f"  Preview: http://localhost:5175/p/{pres_id}")
    print(f"  REMINDER: ~half of title words must be in <em> tags (gradient in tech variant)")
    print(f"{'='*60}\n")

    return pres_id, voice_clips


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--short", type=int, default=None, help="Short number from SCENARIOS (2 or 3)")
    parser.add_argument("--file", type=str, default=None, help="Path to teleprompter .txt (auto-sectioned)")
    parser.add_argument("--title", type=str, default=None, help="Presentation title (with --file)")
    args = parser.parse_args()

    if args.file:
        scenario = load_scenario_from_file(args.file, title=args.title)
        print(f"Loaded {args.file}: {len(scenario['sections'])} sections")
        for s in scenario["sections"]:
            print(f"  {s['label']}: {s['text'][:70]}...")
        run_pipeline(scenario=scenario)
    elif args.short is not None:
        if args.short not in SCENARIOS:
            print(f"Error: unknown short {args.short}. Available: {list(SCENARIOS.keys())}")
            sys.exit(1)
        run_pipeline(args.short)
    else:
        print("Error: provide --short N or --file PATH")
        sys.exit(1)
