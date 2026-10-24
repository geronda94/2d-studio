"""Russian text -> 10 visemes (server-side helper for the editor).

The same approximation as scripts/text_to_visemes.py, kept importable by the
API. For production use TTS/Whisper phoneme timestamps.
"""
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


def viseme_for(ch: str) -> int:
    ch = ch.lower()
    return VOWELS.get(ch, CONSONANTS.get(ch, 0))


def convert_words(words):
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


def text_to_visemes(text: str, start: int = 700, end: int = 6000):
    """Evenly distribute a phrase over [start, end] ms by character weight."""
    words = [w for w in str(text or "").split() if w]
    if not words:
        return []
    total = sum(max(1, len(w)) for w in words)
    span = max(200, int(end) - int(start))
    cursor = int(start)
    out_words = []
    for w in words:
        share = max(1, len(w)) / total
        dur = max(180, int(span * share))
        out_words.append({"word": w, "start": cursor, "end": cursor + dur})
        cursor += dur
    return convert_words(out_words)
