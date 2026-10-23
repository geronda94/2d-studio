#!/usr/bin/env python3
"""Generate Pravoslavie cast portraits with Gemini image + chroma key.

Run on the host (needs Pillow and network):
    python scripts/generate_prav_portraits.py

Output: core/public/portraits/{host,cohost,priest,historian,sociologist}.png
"""
import base64
import io
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
OUT = ROOT / "core" / "public" / "portraits"
OUT.mkdir(parents=True, exist_ok=True)


def load_key():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GEMINI_API_KEY not found")


STYLE = (
    "Using the exact same editorial 2D vector illustration style, line weight, color palette, "
    "soft studio rim light and level of face detail as the reference image, create a waist-up "
    "bust portrait, front view, centered, looking at the camera. Isolated on a perfectly flat "
    "solid pure green background (#00FF00), no shadow, no floor, no gradient, no text, no border. "
    "Keep the head and shoulders fully inside the frame with space around them."
)

CHARACTERS = {
    "host": (
        "A 32-year-old European man, short brown hair, full neat brown beard, thin round glasses, "
        "light blue button shirt, friendly confident expression."
    ),
    "cohost": (
        "A 33-year-old European woman, modest navy headscarf covering the hair, soft burgundy "
        "cardigan over a cream blouse, calm warm expression, no glasses, Orthodox modest style."
    ),
    "priest": (
        "A 48-year-old European man, long dark beard, black cassock with a white collar, a gold "
        "Orthodox cross on the chest, black kamilavka hat, calm wise expression."
    ),
    "historian": (
        "A 55-year-old European man, gray beard, round glasses, brown tweed jacket over a light "
        "shirt, thoughtful scholarly expression."
    ),
    "sociologist": (
        "A 40-year-old European man, short dark hair, neat beard, round glasses, dark gray shirt "
        "with a charcoal vest, analytical calm expression."
    ),
}


def api_image(key, model, reference_b64, prompt):
    body = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": "image/png", "data": reference_b64}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.load(r)
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in parts:
        if "inlineData" in p:
            return base64.b64decode(p["inlineData"]["data"])
    raise RuntimeError("no image in response")


def chroma_key(raw, out_path):
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            dist = math.sqrt((r - 0) ** 2 + (g - 255) ** 2 + (b - 0) ** 2)
            if dist < 70:
                alpha = 0
            elif dist < 150:
                alpha = int((dist - 70) / 80 * 255)
            else:
                alpha = 255
            # despill: suppress green cast on edges
            if g > (r + b) / 2:
                g = int((r + b) / 2)
            px[x, y] = (r, g, b, min(a, alpha))
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        pad = 12
        canvas = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
        canvas.paste(img, (pad, pad))
        img = canvas
    img.save(out_path, "PNG")
    print("saved", out_path, img.size)


def main():
    key = load_key()
    ref_path = OUT / "host.png"
    if not ref_path.exists():
        raise SystemExit(f"reference not found: {ref_path}")
    ref_b64 = base64.b64encode(ref_path.read_bytes()).decode()
    for slug, desc in CHARACTERS.items():
        if slug == "host":
            continue
        prompt = f"{STYLE}\n\nCharacter: {desc}"
        raw = None
        last = None
        for model in ("gemini-3-pro-image", "gemini-3.1-flash-image"):
            try:
                raw = api_image(key, model, ref_b64, prompt)
                print("generated", slug, "with", model)
                break
            except Exception as e:
                last = e
                print("failed", slug, model, str(e)[:180])
        if not raw:
            print("SKIP", slug, last)
            continue
        (OUT / f"raw-{slug}.png").write_bytes(raw)
        chroma_key(raw, OUT / f"{slug}.png")


if __name__ == "__main__":
    main()
