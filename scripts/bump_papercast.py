#!/usr/bin/env python3
"""Bump PaperCast asset versions in one place.

    python scripts/bump_papercast.py --paper 15 --animals 6

Updates core/public/vendor/versions.json and every `?v=` reference in
core/public/*.html and core/src/scenes/runtime.js.
"""
import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'core/public/vendor/versions.json'
TARGETS = list((ROOT / 'core/public').glob('*.html')) + [ROOT / 'core/src/scenes/runtime.js']


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper')
    ap.add_argument('--animals')
    ap.add_argument('--stage')
    args = ap.parse_args()
    data = json.loads(MANIFEST.read_text())
    if args.paper:
        data['paper'] = args.paper
    if args.animals:
        data['animals'] = args.animals
    if args.stage:
        data['stage'] = args.stage
    MANIFEST.write_text(json.dumps(data, indent=2) + '\n')
    for path in TARGETS:
        if not path.exists():
            continue
        text = path.read_text()
        text = re.sub(r'paper-cast\.js\?v=\d+', f"paper-cast.js?v={data['paper']}", text)
        text = re.sub(r'paper-cast-animals\.js\?v=\d+', f"paper-cast-animals.js?v={data['animals']}", text)
        if 'stage' in data:
            text = re.sub(r'paper-cast-stage\.js\?v=\d+', f"paper-cast-stage.js?v={data['stage']}", text)
        path.write_text(text)
    print(f"paper={data['paper']} animals={data['animals']}")


if __name__ == '__main__':
    main()
