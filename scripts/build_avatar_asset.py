#!/usr/bin/env python3
"""Wrap a .glb avatar into a classic script for sandboxed iframes.

Scenes run in a sandbox without allow-same-origin, so fetch() of the model is
blocked. A <script src="/models/avatar.glb.js"> is allowed and cached by the
browser; it sets window.__avatarGlb to base64, which BabylonCharacter decodes.

    python scripts/build_avatar_asset.py
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "core" / "public" / "models" / "brunette.glb"
DST = ROOT / "core" / "public" / "models" / "brunette.glb.js"


def main():
    data = SRC.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    DST.write_text('window.__avatarGlb="%s";\n' % b64, encoding="utf-8")
    print(f"{SRC.name}: {len(data)/1048576:.2f} MB -> {DST.name}: {DST.stat().st_size/1048576:.2f} MB")


if __name__ == "__main__":
    main()
