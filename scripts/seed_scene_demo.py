#!/usr/bin/env python3
"""Create a clean SceneEngine demo project with one 2D scene.

Run inside the backend container:
    python scripts/seed_scene_demo.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from backend.scene_library import get_template

TEMPLATE_SLUG = "forest-drive"
TPL = get_template(TEMPLATE_SLUG)
if not TPL:
    raise SystemExit(f"Template not found: {TEMPLATE_SLUG}")
TPL2 = get_template("cinematic-forest")

DEMO_CODE = TPL["code"]
DEMO_PROPS = TPL["default_props"]
DEMO_DURATION = TPL["duration"]
DEMO_VIEW = TPL.get("view") or "day"
DEMO_CUES = TPL.get("cues") or []
DEMO2_DURATION = TPL2["duration"] if TPL2 else 7000
DEMO2_VIEW = (TPL2.get("view") if TPL2 else "") or "day"
DEMO2_CUES = TPL2.get("cues") if TPL2 else []
DEMO_TITLE = "Forest drive"


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

        pres = db.query(models.Presentation).filter(models.Presentation.title == "Demo Scene").first()
        if not pres:
            pres = models.Presentation(
                title="Demo Scene",
                variant="tech",
                audio_timeline={"tracks": []},
                visibility="public",
            )
            db.add(pres)
            db.flush()
            folder.presentations.append(pres)
            pres_id = pres.id
        else:
            pres_id = pres.id

        scene = db.query(models.Slide).filter(
            models.Slide.presentation_id == pres_id,
            models.Slide.slide_id == "scene-demo-1",
        ).first()
        if not scene:
            scene = models.Slide(
                presentation_id=pres_id,
                slide_id="scene-demo-1",
                component="__scene__",
                start_time=0,
                title=DEMO_TITLE,
                subtitle="",
                layout="col",
                order_index=0,
            )
            db.add(scene)
            db.flush()
        scene.kind = "scene"
        scene.duration = DEMO_DURATION
        scene.code = DEMO_CODE
        scene.props = DEMO_PROPS
        scene.props_schema = TPL.get("props_schema") or {}
        scene.track = scene.track or "main"
        scene.z_index = scene.z_index or 0
        if scene.data:
            scene.data.payload = {
                "kind": "scene",
                "code": DEMO_CODE,
                "props": DEMO_PROPS,
                "props_schema": TPL.get("props_schema") or {},
                "duration": DEMO_DURATION,
                "view": DEMO_VIEW,
                "cues": DEMO_CUES,
            }
        else:
            db.add(models.SlideData(slide_id=scene.id, payload={
                "kind": "scene",
                "code": DEMO_CODE,
                "props": DEMO_PROPS,
                "props_schema": TPL.get("props_schema") or {},
                "duration": DEMO_DURATION,
                "view": DEMO_VIEW,
                "cues": DEMO_CUES,
            }))

        if TPL2:
            scene2 = db.query(models.Slide).filter(
                models.Slide.presentation_id == pres_id,
                models.Slide.slide_id == "scene-demo-2",
            ).first()
            start2 = DEMO_DURATION + 1000
            if not scene2:
                scene2 = models.Slide(
                    presentation_id=pres_id,
                    slide_id="scene-demo-2",
                    component="__scene__",
                    start_time=start2,
                    title="Cinematic forest",
                    subtitle="",
                    layout="col",
                    order_index=1,
                )
                db.add(scene2)
                db.flush()
            scene2.kind = "scene"
            scene2.duration = DEMO2_DURATION
            scene2.code = TPL2["code"]
            scene2.props = TPL2.get("default_props") or {}
            scene2.props_schema = TPL2.get("props_schema") or {}
            scene2.track = scene2.track or "main"
            scene2.z_index = scene2.z_index or 0
            payload2 = {
                "kind": "scene",
                "code": TPL2["code"],
                "props": TPL2.get("default_props") or {},
                "props_schema": TPL2.get("props_schema") or {},
                "duration": DEMO2_DURATION,
                "view": DEMO2_VIEW,
                "cues": DEMO2_CUES,
            }
            if scene2.data:
                scene2.data.payload = payload2
            else:
                db.add(models.SlideData(slide_id=scene2.id, payload=payload2))

        end = db.query(models.Slide).filter(
            models.Slide.presentation_id == pres_id,
            models.Slide.component == "EndMarkerSlide",
        ).first()
        target_end = DEMO_DURATION + 1000 + DEMO2_DURATION + 1000 if TPL2 else DEMO_DURATION + 1000
        if not end:
            db.add(models.Slide(
                presentation_id=pres_id,
                slide_id="scene-demo-end",
                component="EndMarkerSlide",
                start_time=target_end,
                title="Конец",
                subtitle="",
                layout="col",
                order_index=2 if TPL2 else 1,
            ))
        else:
            end.start_time = target_end

        db.commit()
        print(f"Project: {project.id} ({project.slug})")
        print(f"Folder:  {folder.id} ({folder.slug})")
        print(f"Presentation: {pres_id} — open /p/{pres_id}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
