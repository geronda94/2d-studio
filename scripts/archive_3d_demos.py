#!/usr/bin/env python3
"""Archive the two dead 3D demos (/p/10 3D Avatar, /p/11 Poly duo).

The 3D/Babylon runtime was frozen on 2026-10-27 and moved to `drafts/3d/`, so
those scenes now throw (`SceneKit.babylonCharacter is not a function`,
`SceneRig is not defined`) and render a blank slide.  Instead of deleting the
presentations we replace the broken scene with a small, valid Paper Cast card
that says where the 3D went and links to the live demos.

    docker compose exec -T backend python scripts/archive_3d_demos.py
"""
from __future__ import annotations

import json
import os
import urllib.request

API = os.environ.get("API_BASE", "http://localhost:8000")

CARD_HTML = """
<div class="scene archive-card">
  <div class="layer layer-world" data-layer="world">
    <div class="ac-grid"></div>
  </div>
  <div class="layer layer-overlay" data-layer="overlay">
    <div class="ac-kicker">{{kicker}}</div>
    <h1 class="ac-title">{{title}}</h1>
    <p class="ac-text">{{text}}</p>
    <a class="ac-link" href="/p/12">{{link}}</a>
  </div>
</div>
"""

CARD_CSS = """
.archive-card { position:absolute; inset:0; background: #0d1117; overflow:hidden; }
.ac-grid {
  position:absolute; inset:-20%;
  background:
    linear-gradient(rgba(103,216,200,.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(103,216,200,.06) 1px, transparent 1px);
  background-size: 56px 56px;
  transform: perspective(600px) rotateX(58deg);
  transform-origin: 50% 100%;
  mask-image: radial-gradient(ellipse at 50% 70%, #000 30%, transparent 72%);
}
.layer-overlay {
  position:absolute; inset:0; display:flex; flex-direction:column;
  justify-content:center; gap: 14px; padding: 0 clamp(24px, 8vw, 140px);
}
.ac-kicker {
  font: 11px/1.2 ui-monospace, Menlo, monospace; letter-spacing:.22em;
  text-transform: uppercase; color: #67d8c8;
}
.ac-title {
  margin:0; font: 700 clamp(30px, 5.4vw, 68px)/1.05 var(--font-heading, ui-sans-serif);
  color: #f4efe4; letter-spacing:-.02em;
}
.ac-text {
  margin:0; max-width: 46ch; font: 400 clamp(14px, 1.5vw, 19px)/1.45 var(--font-sans, system-ui);
  color: rgba(244,239,228,.72);
}
.ac-link {
  align-self:flex-start; margin-top: 8px; padding: 10px 16px; border-radius: 999px;
  border: 1px solid rgba(103,216,200,.45); color:#67d8c8; text-decoration:none;
  font: 600 13px/1 ui-monospace, Menlo, monospace; letter-spacing:.08em;
}
.ac-link:hover { background: rgba(103,216,200,.10); }
"""

CARD_JS = """
const q = (s) => document.querySelector(s);
const p = window.__sceneProps || {};
q('.ac-kicker').textContent = p.kicker || '3D АРХИВ';
q('.ac-title').textContent = p.title || '';
q('.ac-text').textContent = p.text || '';
q('.ac-link').textContent = p.link_label || 'Paper Cast →';
const tl = gsap.timeline({ paused: true });
tl.from('.ac-kicker', { opacity: 0, y: 10, duration: 0.5, ease: 'power2.out' }, 0)
  .from('.ac-title', { opacity: 0, y: 24, duration: 0.7, ease: 'power4.out' }, 0.08)
  .from('.ac-text', { opacity: 0, y: 16, duration: 0.6, ease: 'power2.out' }, 0.22)
  .from('.ac-link', { opacity: 0, y: 12, duration: 0.5, ease: 'power2.out' }, 0.36);
window.scene = { seek(t) { tl.seek(t / 1000) } };
"""


def api(path: str, method: str = "GET", payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read()
        return json.loads(body) if body else None


def patch(presentation_id: int, title: str, scene_title: str, props: dict) -> None:
    scenes = api(f"/presentations/{presentation_id}/scenes")
    if not scenes:
        print(f"  p/{presentation_id}: no scenes, skipped")
        return
    scene = scenes[0]
    # PUT /scenes/{id} expects a full SlideCreate (slide_id, component,
    # start_time and order_index are required): send the scene back with the
    # fields we want to change.
    payload = {
        "slide_id": scene["slide_id"],
        "component": "__scene__",
        "start_time": scene.get("start_time", 0) or 0,
        "order_index": scene.get("order_index", 0) or 0,
        "title": scene_title,
        "subtitle": scene.get("subtitle", ""),
        "layout": scene.get("layout") or "col",
        "kind": "scene",
        "duration": 6000,
        "code": {"html": CARD_HTML.strip(), "css": CARD_CSS.strip(), "js": CARD_JS.strip()},
        "props": props,
        "props_schema": {},
        "track": scene.get("track") or "main",
        "z_index": scene.get("z_index") or 0,
    }
    api(f"/presentations/scenes/{scene['id']}", "PUT", payload)
    print(f"  p/{presentation_id}: scene {scene['id']} → archive card")


def main() -> None:
    pres = api("/presentations")
    titles = {p["id"]: p.get("title", "") for p in pres}
    plan = {
        10: dict(
            scene_title="3D Avatar — архив",
            props={
                "kicker": "3D АРХИВ / 2026-10-27",
                "title": "3D-аватар заархивирован",
                "text": "Babylon и GLB-аватары заморожены: продакшн-персонажи теперь рисуются на Canvas 2D. Исходники лежат в drafts/3d.",
                "link_label": "Paper Cast →",
            },
        ),
       11: dict(
            scene_title="Poly duo — архив",
            props={
                "kicker": "3D АРХИВ / 2026-10-27",
                "title": "Полигональные персонажи заархивированы",
                "text": "Риг SceneRig и GLB-модели Mark/Mira перенесены в drafts/3d. Живая замена — два бумажных персонажа с общим скелетом.",
                "link_label": "Смотреть Paper duo →",
            },
        ),
    }
    for pid, cfg in plan.items():
        print(f"p/{pid} «{titles.get(pid, '?')}»")
        patch(pid, titles.get(pid, ""), cfg["scene_title"], cfg["props"])


if __name__ == "__main__":
    main()
