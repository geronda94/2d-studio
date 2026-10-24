#!/usr/bin/env python3
"""Fetch the Mixamo clips used by the 3D avatar.

The animations are free for commercial use under Adobe's Mixamo terms, but
redistribution of the raw assets is restricted — keep them out of public repos
and copy them to servers manually. Run this locally, then:

    python scripts/extract_avatar_anims.py
    python scripts/build_avatar_asset.py
"""
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DST = ROOT / "core" / "public" / "models" / "anim"
BASE = "https://raw.githubusercontent.com/MisterYI/deevid-mixamo-assets/main/anim"

CLIPS = [
    "Idle", "Neutral_Idle", "Standing_Idle", "Talking",
    "Standing_Greeting", "Pointing", "Shrugging", "Hard_Head_Nod",
    "Agreeing", "Thinking", "Look_Around", "Strong_Gesture",
    "Standing_Thumbs_Up", "Dismissing_Gesture", "Look_Away_Gesture",
    "Standing_Clap",
]


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for name in CLIPS:
        path = DST / (name + ".glb")
        if path.exists() and path.stat().st_size > 1000:
            print("skip", name)
            continue
        url = f"{BASE}/{name}.glb"
        print("get ", name)
        urllib.request.urlretrieve(url, path)
    print(f"done: {len(CLIPS)} clips in {DST}")


if __name__ == "__main__":
    main()
