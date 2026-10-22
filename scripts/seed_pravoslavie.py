#!/usr/bin/env python3
"""Create the Pravoslavie channel project, cast, studio and demo scenes.

Run inside backend:
    python scripts/seed_pravoslavie.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from backend.scene_library import get_template


def _scene_payload(tpl, props=None, *, title=None, view=None, cues=None):
    p = dict(tpl.get("default_props") or {})
    if props:
        p.update(props)
    return {
        "kind": "scene",
        "code": tpl["code"],
        "props": p,
        "props_schema": tpl.get("props_schema") or {},
        "duration": tpl["duration"],
        "view": view or tpl.get("view") or "",
        "cues": cues if cues is not None else (tpl.get("cues") or []),
    }


def _add_scene(db, pres_id, slide_id, tpl_slug, start, order, *, title, props=None, view=None):
    tpl = get_template(tpl_slug)
    if not tpl:
        print(f"skip {tpl_slug}: template not found")
        return None
    slide = db.query(models.Slide).filter(models.Slide.slide_id == slide_id).first()
    if not slide:
        slide = models.Slide(
            presentation_id=pres_id,
            slide_id=slide_id,
            component="__scene__",
            start_time=start,
            order_index=order,
        )
        db.add(slide)
        db.flush()
    payload = _scene_payload(tpl, props, title=title, view=view)
    slide.title = title
    slide.subtitle = ""
    slide.layout = "col"
    slide.start_time = start
    slide.order_index = order
    slide.component = "__scene__"
    slide.kind = "scene"
    slide.duration = payload["duration"]
    slide.code = payload["code"]
    slide.props = payload["props"]
    slide.props_schema = payload["props_schema"]
    slide.track = slide.track or "main"
    slide.z_index = slide.z_index or 0
    if slide.data:
        slide.data.payload = payload
    else:
        db.add(models.SlideData(slide_id=slide.id, payload=payload))
    return slide


def _presentation(db, folder, title, *, slug):
    pres = db.query(models.Presentation).filter(models.Presentation.title == title).first()
    if not pres:
        pres = models.Presentation(title=title, variant="tech", audio_timeline={"tracks": []})
        db.add(pres)
        db.flush()
        folder.presentations.append(pres)
    return pres


def _finish(db, pres_id, end_time, order):
    end = db.query(models.Slide).filter(
        models.Slide.presentation_id == pres_id,
        models.Slide.component == "EndMarkerSlide",
    ).first()
    if not end:
        db.add(models.Slide(
            presentation_id=pres_id,
            slide_id=f"prav-end-{pres_id}",
            component="EndMarkerSlide",
            start_time=end_time,
            title="Конец",
            subtitle="",
            layout="col",
            order_index=order,
        ))
    else:
        end.start_time = end_time
        end.order_index = order


def run():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        project = db.query(models.Project).filter(models.Project.slug == "pravoslavie").first()
        if not project:
            project = models.Project(
                slug="pravoslavie",
                title="Механизм",
                description="Социальная история, православие, разбор механизмов.",
            )
            db.add(project)
            db.flush()

        folder = db.query(models.Folder).filter(models.Folder.slug == "pravoslavie").first()
        if not folder:
            folder = models.Folder(slug="pravoslavie", title="Pravoslavie", project_id=project.id)
            db.add(folder)
            db.flush()

        # 1. Studio demo
        demo = _presentation(db, folder, "Prav · Studio demo", slug="prav-studio-demo")
        scenes = [
            ("prav-studio-host", 0, "Студия: ведущий", {"monitor_media": ""}),
            ("prav-studio-panel", 7000, "Панель: ведущий, священник, историк", {"monitor_media": ""}),
            ("prav-empire-history", 15000, "Империя накануне", {"caption": "Империя накануне"}),
            ("prav-church-quote", 23000, "Цитата в храме", {"quote": "Вера на языке, а сердце в стороне.", "author": "По мотивам Писания"}),
            ("prav-outro", 30000, "Финал: ведущий и соведущая", {"headline": "Дальше — самое горькое", "handle": "@mechanism"}),
        ]
        for i, (slug, start, title, props) in enumerate(scenes):
            _add_scene(db, demo.id, f"prav-demo-{i+1}", slug, start, i, title=title, props=props)
        _finish(db, demo.id, 36000, len(scenes))

        # 2. Episode 1 visual board (no audio yet)
        ep1 = _presentation(db, folder, "Э1 — С чего начался упадок", slug="prav-ep1")
        ep1_scenes = [
            ("prav-studio-host", 0, "Вход: студия", {"monitor_media": ""}),
            ("prav-ancient-rus", 7000, "Древняя Русь", {"caption": "Древняя Русь · до империи"}),
            ("prav-empire-history", 14000, "Империя до 1905", {"caption": "Империя до 1905"}),
            ("prav-soviet-history", 21000, "Советский город", {"caption": "Советский город · 1930-е"}),
            ("prav-timeline", 28000, "Сто лет упадка: таймлайн", {"caption": "Сто лет упадка"}),
            ("prav-church-quote", 35000, "Вера на языке", {"quote": "Этот народ приближается ко Мне устами, а сердце его далеко.", "author": "Исаия 29:13"}),
            ("prav-studio-panel", 42000, "Разбор: священник и историк", {"monitor_media": ""}),
            ("prav-outro", 50000, "Финал выпуска", {"headline": "Дальше — лагеря", "handle": "@mechanism"}),
        ]
        for i, (slug, start, title, props) in enumerate(ep1_scenes):
            _add_scene(db, ep1.id, f"prav-ep1-{i+1}", slug, start, i, title=title, props=props)
        _finish(db, ep1.id, 56000, len(ep1_scenes))

        db.commit()
        print(f"Project: {project.id} ({project.slug})")
        print(f"Folder:  {folder.id} ({folder.slug})")
        print(f"Demo:    /p/{demo.id}")
        print(f"Episode: /p/{ep1.id}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
