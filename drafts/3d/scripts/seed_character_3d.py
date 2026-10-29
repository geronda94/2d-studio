#!/usr/bin/env python3
"""Create the "3D avatar" demo presentation (Babylon + Ready Player Me).

Run inside the backend container:
    python scripts/seed_character_3d.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from backend.scene_library import get_template
from text_to_visemes import convert

TEMPLATE_SLUG = "character-3d"
TITLE = "3D Avatar"

TPL = get_template(TEMPLATE_SLUG)
if not TPL:
    raise SystemExit(f"Template not found: {TEMPLATE_SLUG}")

PROPS = dict(TPL.get("default_props") or {})
PROPS["headline"] = "Живой 3D-аватар"
PROPS["kicker"] = "3D STUDIO"
PROPS["preset"] = "bust"
PROPS["mood"] = "neutral"
PROPS["gestures"] = [
    {"at": 2600, "type": "nod", "duration": 1200},
    {"at": 4400, "type": "wave", "duration": 1800},
]
PROPS["gaze"] = {"x": 0.15, "y": 0}
PROPS["visemes"] = convert([
    {"word": "Привет,", "start": 700, "end": 1250},
    {"word": "это", "start": 1250, "end": 1550},
    {"word": "трёхмерный", "start": 1550, "end": 2350},
    {"word": "аватар", "start": 2350, "end": 3000},
    {"word": "на", "start": 3200, "end": 3400},
    {"word": "сцене", "start": 3400, "end": 4000},
])
DURATION = TPL["duration"]


def run():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        project = db.query(models.Project).filter(models.Project.slug == "scene-demo").first()
        if not project:
            project = models.Project(slug="scene-demo", title="SceneEngine", description="2D scene engine demo")
            db.add(project)
            db.flush()

        folder = db.query(models.Folder).filter(models.Folder.slug == "scenes").first()
        if not folder:
            folder = models.Folder(slug="scenes", title="Сцены", project_id=project.id)
            db.add(folder)
            db.flush()

        pres = db.query(models.Presentation).filter(models.Presentation.title == TITLE).first()
        if not pres:
            pres = models.Presentation(
                title=TITLE,
                variant="tech",
                audio_timeline={"tracks": []},
                visibility="public",
            )
            db.add(pres)
            db.flush()
            folder.presentations.append(pres)
        pres_id = pres.id

        scene = db.query(models.Slide).filter(
            models.Slide.presentation_id == pres_id,
            models.Slide.slide_id == "scene-3d-avatar-1",
        ).first()
        if not scene:
            scene = models.Slide(
                presentation_id=pres_id,
                slide_id="scene-3d-avatar-1",
                component="__scene__",
                start_time=0,
                title=TITLE,
                subtitle="",
                layout="col",
                order_index=0,
            )
            db.add(scene)
            db.flush()
        payload = {
            "kind": "scene",
            "code": TPL["code"],
            "props": PROPS,
            "props_schema": TPL.get("props_schema") or {},
            "duration": DURATION,
            "view": TPL.get("view") or "dark",
            "cues": TPL.get("cues") or [],
        }
        scene.kind = "scene"
        scene.duration = DURATION
        scene.code = TPL["code"]
        scene.props = PROPS
        scene.props_schema = TPL.get("props_schema") or {}
        scene.track = scene.track or "main"
        scene.z_index = scene.z_index or 0
        if scene.data:
            scene.data.payload = payload
        else:
            db.add(models.SlideData(slide_id=scene.id, payload=payload))

        end = db.query(models.Slide).filter(
            models.Slide.presentation_id == pres_id,
            models.Slide.component == "EndMarkerSlide",
        ).first()
        target_end = DURATION + 1000
        if not end:
            db.add(models.Slide(
                presentation_id=pres_id,
                slide_id="scene-3d-avatar-end",
                component="EndMarkerSlide",
                start_time=target_end,
                title="Конец",
                subtitle="",
                layout="col",
                order_index=1,
            ))
        else:
            end.start_time = target_end

        db.commit()
        print(f"Presentation: {pres_id} — open /p/{pres_id}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
