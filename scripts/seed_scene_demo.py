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

DEMO_CODE = TPL["code"]
DEMO_PROPS = TPL["default_props"]
DEMO_DURATION = TPL["duration"]
DEMO_VIEW = TPL.get("view") or "day"
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
            }
        else:
            db.add(models.SlideData(slide_id=scene.id, payload={
                "kind": "scene",
                "code": DEMO_CODE,
                "props": DEMO_PROPS,
                "props_schema": TPL.get("props_schema") or {},
                "duration": DEMO_DURATION,
                "view": DEMO_VIEW,
            }))

        end = db.query(models.Slide).filter(
            models.Slide.presentation_id == pres_id,
            models.Slide.component == "EndMarkerSlide",
        ).first()
        target_end = DEMO_DURATION + 1000
        if not end:
            db.add(models.Slide(
                presentation_id=pres_id,
                slide_id="scene-demo-end",
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
        print(f"Project: {project.id} ({project.slug})")
        print(f"Folder:  {folder.id} ({folder.slug})")
        print(f"Presentation: {pres_id} — open /p/{pres_id}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
