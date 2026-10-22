#!/usr/bin/env python3
"""Re-voice an existing presentation from a teleprompter .txt file.

- Generates 1 TTS clip per semantic block (hook/most/proof/payoff/cta)
- Rebuilds audio_timeline (200ms gaps = pauses ONLY between blocks)
- Remaps existing slides piecewise onto new section bounds (payloads preserved)
- Moves EndMarkerSlide to total + 1000ms

Run: docker compose exec backend python scripts/revoice_from_file.py --pres-id 16 --file scripts/_inbox/shorts02.txt
"""
import argparse
import os
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
from generate_short import (
    load_scenario_from_file, generate_tts, get_duration,
    build_audio_timeline, SECTION_PRESET,
)

BASE = "http://localhost:8000"
GAP = 200  # ms pause between semantic blocks (the ONLY pauses)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pres-id", type=int, required=True)
    ap.add_argument("--file", type=str, required=True)
    ap.add_argument("--gap", type=float, default=GAP)
    ap.add_argument("--speedup", type=float, default=1.0,
                    help="ffmpeg atempo speedup factor (e.g. 1.2 = 20%% faster)")
    args = ap.parse_args()

    scenario = load_scenario_from_file(args.file)
    print(f"Scenario: {scenario['title']} ({len(scenario['sections'])} sections)")

    pres = requests.get(f"{BASE}/presentations/{args.pres_id}").json()
    old_clips = None
    if pres.get("audio_timeline"):
        for t in pres["audio_timeline"]["tracks"]:
            if t["id"] == "main":
                old_clips = t["clips"]
    if not old_clips or len(old_clips) < 5:
        raise SystemExit("Need existing timeline with >=5 clips to derive old bounds")

    # Old bounds by position: first=hook, second=most, last=cta,
    # second-last=payoff, everything between=proof
    old_bounds = {
        "hook": (old_clips[0]["start_time"], old_clips[0]["end_time"]),
        "most": (old_clips[1]["start_time"], old_clips[1]["end_time"]),
        "proof": (old_clips[2]["start_time"], old_clips[-3]["end_time"]),
        "payoff": (old_clips[-2]["start_time"], old_clips[-2]["end_time"]),
        "cta": (old_clips[-1]["start_time"], old_clips[-1]["end_time"]),
    }
    print("Old bounds:", {k: (round(a), round(b)) for k, (a, b) in old_bounds.items()})

    # 1. Generate new TTS (1 call per block)
    batch_id = f"revoice_{args.pres_id}_{int(time.time())}"
    voice_clips = []
    for section in scenario["sections"]:
        preset = SECTION_PRESET.get(section["id"], "proof_narrative")
        media = generate_tts(args.pres_id, section["text"], batch_id, preset=preset, speedup=args.speedup)
        dur = get_duration(media["file_path"])
        voice_clips.append({"section_id": section["id"], "file_path": media["file_path"],
                            "media_id": media["id"], "duration_ms": dur})
        print(f"  [{preset}] {section['label']}: {dur}ms")

    # 2. New layout
    t = 0.0
    new_bounds = {}
    for vc in voice_clips:
        s, e = t, t + vc["duration_ms"]
        vc["start_time"], vc["end_time"] = s, e
        new_bounds[vc["section_id"]] = (s, e)
        t = e + args.gap
    total = t - args.gap
    print("New bounds:", {k: (round(a), round(b)) for k, (a, b) in new_bounds.items()})
    print(f"TOTAL: {total:.0f}ms ({total/1000:.1f}s)")

    # Section id of old proof clips: map section order hook/most/proof/payoff/hook_out
    order = ["hook", "most", "proof", "payoff", "hook_out"]
    new_by_order = {sec: new_bounds[sec] for sec in order}

    def remap(old_t):
        # Exact match at section start → snap to new section start (highest priority)
        for sec in ["hook", "most", "proof", "payoff", "cta", "hook_out"]:
            a, b = old_bounds.get(sec, old_bounds.get("proof"))
            if a is None:
                continue
            na, nb = new_by_order.get(sec, new_by_order["proof"])
            if abs(float(old_t) - float(a)) < 1:
                return round(float(na), 1)
        # Fractional match within section bounds
        for sec in ["hook", "most", "proof", "payoff", "cta", "hook_out"]:
            a, b = old_bounds.get(sec, old_bounds.get("proof"))
            if a is None:
                continue
            na, nb = new_by_order.get(sec, new_by_order["proof"])
            if float(a) <= float(old_t) <= float(b) + 1:
                span = float(nb) - float(na)
                frac = 0.0 if float(b) <= float(a) else min(1.0, max(0.0, (float(old_t) - float(a)) / (float(b) - float(a))))
                return round(float(na) + frac * span, 1)
        # Fallback: nearest section start only (never end)
        best, best_d = None, None
        for sec, (na, nb) in new_by_order.items():
            d = abs(float(old_t) - float(na))
            if best_d is None or d < best_d:
                best, best_d = float(na), d
        print(f"  WARN remap fallback for {old_t} -> {best}")
        return round(best if best is not None else float(old_t), 1)

    # 3. Remap slides (payloads + events preserved)
    for s in pres["slides"]:
        if s["slide_id"].startswith("end_"):
            new_t = round(total + 1000, 1)
        else:
            new_t = remap(float(s["start_time"]))
        body = {"slide_id": s["slide_id"], "component": s["component"],
                "start_time": new_t, "title": s.get("title") or "",
                "subtitle": s.get("subtitle") or "", "layout": s.get("layout") or "col",
                "order_index": s.get("order_index", 0)}
        if s.get("data") and (s["data"].get("payload") is not None):
            body["data"] = {"payload": s["data"]["payload"]}
        if s.get("events"):
            body["events"] = [{"time": e["time"], "action": e.get("action"),
                               "event_type": e.get("event_type"),
                               "payload": e.get("payload")} for e in s["events"]]
        r = requests.put(f"{BASE}/presentations/slides/{s['id']}", json=body)
        if r.status_code != 200:
            print(f"SLIDE FAIL {s['slide_id']}: {r.status_code} {r.text[:200]}")
        else:
            print(f"  slide {s['slide_id']}: {s['start_time']:.0f} → {new_t:.0f}")

    # 4. New timeline (BGM = same file as before, keep first overlay clip src)
    bgm_path = None
    if pres.get("audio_timeline"):
        for tr in pres["audio_timeline"]["tracks"]:
            if tr["id"] == "overlay" and tr.get("clips"):
                bgm_path = tr["clips"][0]["src"]
    from generate_short import BGM_FILE
    timeline = build_audio_timeline(voice_clips, bgm_path or BGM_FILE)
    r = requests.put(f"{BASE}/presentations/{args.pres_id}", json={"audio_timeline": timeline})
    print("timeline PUT:", r.status_code)
    print(f"DONE: pres {args.pres_id}, total {total/1000:.1f}s, preview http://localhost:5174/p/{args.pres_id}")


if __name__ == "__main__":
    main()
