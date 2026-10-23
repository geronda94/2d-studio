#!/usr/bin/env python3
"""Approximate Russian text -> 10 visemes for lip-sync.

Input (JSON):  [{"word":"привет","start":0,"end":600}, ...]  (ms)
Output (JSON): [{"t":0,"viseme":2}, {"t":120,"viseme":1}, ...]

This is an approximation for a state-machine mouth. For production, prefer
phoneme-level timestamps from TTS/Whisper + a proper Rive/DragonBones rig.
"""
import json
import sys

# 0 neutral, 1 AEI, 2 BMP, 3 FV, 4 CDGKNRSTXYZ, 5 U, 6 ChJSh, 7 L, 8 O, 9 QW
VOWELS = {
    "а": 1, "э": 1, "я": 1, "е": 1, "и": 1, "ы": 1,
    "о": 8, "ё": 8,
    "у": 5, "ю": 5,
}
CONSONANTS = {
    "м": 2, "б": 2, "п": 2,
    "ф": 3, "в": 3,
    "ч": 6, "ш": 6, "ж": 6, "щ": 6,
    "л": 7,
    "к": 4, "г": 4, "х": 4, "д": 4, "т": 4, "з": 4, "с": 4,
    "ц": 4, "р": 4, "н": 4, "й": 4,
}


def viseme_for(ch):
    ch = ch.lower()
    if ch in VOWELS:
        return VOWELS[ch]
    if ch in CONSONANTS:
        return CONSONANTS[ch]
    return 0


def convert(words):
    out = []
    for w in words:
        text = str(w.get("word") or w.get("text") or "")
        letters = [c for c in text if c.isalpha()]
        if not letters:
            continue
        start = float(w.get("start", 0))
        end = float(w.get("end", start + 300))
        step = max(40.0, (end - start) / max(1, len(letters)))
        for i, ch in enumerate(letters):
            out.append({"t": int(start + i * step), "viseme": viseme_for(ch)})
    out.sort(key=lambda x: x["t"])
    return out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    data = json.load(open(path, encoding="utf-8")) if path else json.load(sys.stdin)
    print(json.dumps(convert(data), ensure_ascii=False, indent=2))
