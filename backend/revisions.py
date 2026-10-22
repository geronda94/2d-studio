"""Версии проекта (ENTERPRISE Ф2): снапшот, дедуп, diff, безопасный откат.

Снапшот — контент проекта: meta/config/brief, токены project+presentation scope,
папки со связями, презентации и их слайды (payload). Участники/ключи/владение
в снапшот НЕ входят (их откат запрещён — безопасность).
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from sqlalchemy.orm import Session

from . import models


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_snapshot(db: Session, project_id: int) -> dict:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return {}
    # папки проекта
    folders = db.query(models.Folder).filter(models.Folder.project_id == project_id).all()
    folder_ids = [f.id for f in folders]
    # презентации проекта через folder_presentation
    pres_ids = set()
    folder_links = []
    for f in folders:
        ids = [p.id for p in f.presentations]
        folder_links.append({"slug": f.slug, "presentation_ids": ids})
        pres_ids.update(ids)
    pres_list = []
    for pid in sorted(pres_ids):
        p = db.query(models.Presentation).filter(models.Presentation.id == pid).first()
        if not p:
            continue
        slides = []
        for s in db.query(models.Slide).filter(models.Slide.presentation_id == pid)\
                .order_by(models.Slide.order_index).all():
            slides.append({
                "slide_id": s.slide_id, "component": s.component, "start_time": s.start_time,
                "title": s.title, "subtitle": s.subtitle, "layout": s.layout,
                "order_index": s.order_index, "payload": (s.data.payload if s.data else {}) or {},
            })
        pres_list.append({
            "id": p.id, "title": p.title, "audio_src": p.audio_src,
            "audio_timeline": p.audio_timeline, "variant": p.variant,
            "style_preset": p.style_preset, "style_lock": p.style_lock,
            "chessboard": p.chessboard, "palette_source": p.palette_source,
            "visibility": p.visibility, "slides": slides,
        })
    # токены: project-scope + presentation-scope презентаций проекта (палитры уровня презы)
    pres_id_list = [p["id"] for p in pres_list]
    tok_q = db.query(models.DesignToken).filter(models.DesignToken.is_archived.is_(False))
    if pres_id_list:
        from sqlalchemy import or_
        tok_q = tok_q.filter(or_(models.DesignToken.project_id == project_id,
                                 models.DesignToken.presentation_id.in_(pres_id_list)))
    else:
        tok_q = tok_q.filter(models.DesignToken.project_id == project_id)
    tokens = []
    for t in tok_q.all():
        tokens.append({
            "token_key": t.token_key, "token_type": t.token_type, "value": t.value,
            "presentation_id": t.presentation_id, "slide_id": t.slide_id,
            "is_custom": t.is_custom,
        })
    return {
        "project": {
            "slug": project.slug, "title": project.title, "description": project.description,
            "default_variant": project.default_variant, "palette_source": project.palette_source,
            "brief": project.brief, "config": project.config,
        },
        "tokens": tokens,
        "folders": [{
            "slug": f.slug, "title": f.title, "desc": f.desc, "theme": f.theme,
            "icon": f.icon, "is_archived": f.is_archived,
        } for f in folders],
        "folder_links": folder_links,
        "presentations": pres_list,
    }


def snapshot_hash(snapshot: dict) -> str:
    return hashlib.sha256(_canon(snapshot).encode("utf-8")).hexdigest()


def create_revision(db: Session, project_id: int, *, source: str = "manual",
                    label: Optional[str] = None, author_user_id: Optional[int] = None,
                    on_behalf_of_user_id: Optional[int] = None, force: bool = False):
    """Создать ревизию. Если контент не изменился и force=False — не пишем (дедуп)."""
    snap = build_snapshot(db, project_id)
    if not snap:
        return None
    h = snapshot_hash(snap)
    last = db.query(models.ProjectRevision).filter(
        models.ProjectRevision.project_id == project_id
    ).order_by(models.ProjectRevision.n.desc()).first()
    if last and last.content_hash == h and not force:
        return None
    size = len(_canon(snap).encode("utf-8"))
    # UNIQUE(project_id, n): при гонке возможен конфликт — повтор с ПЕРЕсчётом n.
    from sqlalchemy.exc import IntegrityError
    for _attempt in range(3):
        last = db.query(models.ProjectRevision).filter(
            models.ProjectRevision.project_id == project_id
        ).order_by(models.ProjectRevision.n.desc()).first()
        n = (last.n if last else 0) + 1
        rev = models.ProjectRevision(
            project_id=project_id, n=n, author_user_id=author_user_id,
            on_behalf_of_user_id=on_behalf_of_user_id, source=source, label=label,
            content_hash=h, snapshot=snap, size_bytes=size, is_checkpoint=True)
        db.add(rev)
        try:
            db.commit()
            db.refresh(rev)
            return rev
        except IntegrityError:
            db.rollback()
    return None


def list_revisions(db: Session, project_id: int, limit: int = 50) -> list:
    return db.query(models.ProjectRevision).filter(
        models.ProjectRevision.project_id == project_id
    ).order_by(models.ProjectRevision.n.desc()).limit(limit).all()


def diff_snapshot(db: Session, project_id: int, snapshot: dict) -> dict:
    """Что изменится при откате к snapshot (add/remove/change по сущностям)."""
    cur = build_snapshot(db, project_id)
    tgt = snapshot or {}

    def keyed(seq, key):
        return {x.get(key): x for x in (seq or [])}

    cur_slides = {}
    for p in cur.get("presentations", []):
        cur_slides[p["id"]] = keyed(p.get("slides"), "slide_id")
    tgt_slides = {}
    for p in tgt.get("presentations", []):
        tgt_slides[p["id"]] = keyed(p.get("slides"), "slide_id")

    def _pres_meta(seq):
        # сравниваем презентации БЕЗ слайдов (иначе изменение слайда = +changed у презы)
        return {p.get("id"): {k: v for k, v in p.items() if k != "slides"} for p in (seq or [])}

    cur_pres = _pres_meta(cur.get("presentations"))
    tgt_pres = _pres_meta(tgt.get("presentations"))
    cur_folders = keyed(cur.get("folders"), "slug")
    tgt_folders = keyed(tgt.get("folders"), "slug")

    slides_added = slides_removed = slides_changed = 0
    for pid, tgt_s in tgt_slides.items():
        cur_s = cur_slides.get(pid, {})
        for sid, val in tgt_s.items():
            if sid not in cur_s:
                slides_added += 1
            elif _canon(cur_s[sid]) != _canon(val):
                slides_changed += 1
        slides_removed += sum(1 for sid in cur_s if sid not in tgt_s)

    return {
        "presentations": {
            "added": [k for k in tgt_pres if k not in cur_pres],
            "removed": [k for k in cur_pres if k not in tgt_pres],
            "changed": [k for k in tgt_pres if k in cur_pres
                        and _canon(cur_pres[k]) != _canon(tgt_pres[k])],
        },
        "folders": {
            "added": [k for k in tgt_folders if k not in cur_folders],
            "removed": [k for k in cur_folders if k not in tgt_folders],
            "changed": [k for k in tgt_folders if k in cur_folders
                        and _canon(cur_folders[k]) != _canon(tgt_folders[k])],
        },
        "slides": {"added": slides_added, "removed": slides_removed, "changed": slides_changed},
    }


def restore_snapshot(db: Session, project_id: int, snapshot: dict, dry_run: bool = True,
                     author_user_id: Optional[int] = None,
                     on_behalf_of_user_id: Optional[int] = None) -> dict:
    """Откат КОНТЕНТА проекта к snapshot. Участники/ключи/владение не трогаем.
    dry_run=True — только diff. apply — в одной транзакции, затем новая ревизия source=restore."""
    diff = diff_snapshot(db, project_id, snapshot)
    if dry_run:
        return {"dry_run": True, "diff": diff}

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project or not snapshot:
        return {"dry_run": False, "error": "project or snapshot missing"}

    meta = snapshot.get("project") or {}
    for k in ("title", "description", "default_variant", "palette_source"):
        if k in meta:
            setattr(project, k, meta[k])
    project.brief = meta.get("brief")
    project.config = meta.get("config")

    # проектные токены: заменяем полностью (managed + custom снапшота)
    db.query(models.DesignToken).filter(
        models.DesignToken.project_id == project_id,
        models.DesignToken.presentation_id.is_(None),
        models.DesignToken.slide_id.is_(None)).delete()
    for t in snapshot.get("tokens", []):
        if t.get("presentation_id") is None and t.get("slide_id") is None:
            db.add(models.DesignToken(
                project_id=project_id, token_key=t["token_key"], token_type=t.get("token_type", "color"),
                value=t.get("value"), is_custom=bool(t.get("is_custom"))))

    # папки: upsert по slug + УДАЛЯЕМ появившиеся после снапшота (иначе «откат» неполный)
    existing = {f.slug: f for f in db.query(models.Folder).filter(
        models.Folder.project_id == project_id).all()}
    target_slugs = {f["slug"] for f in snapshot.get("folders", [])}
    extra_ids = [f.id for slug, f in existing.items() if slug not in target_slugs]
    if extra_ids:
        # снять ссылки участников на удаляемые папки (иначе FK scope_folder_id)
        db.query(models.ProjectMember).filter(
            models.ProjectMember.scope_folder_id.in_(extra_ids)).update(
            {models.ProjectMember.scope_folder_id: None}, synchronize_session=False)
    for slug, obj in existing.items():
        if slug not in target_slugs:
            db.delete(obj)
    for f in snapshot.get("folders", []):
        obj = existing.get(f["slug"])
        if obj is None:
            obj = models.Folder(project_id=project_id, slug=f["slug"])
            db.add(obj)
        obj.title = f.get("title")
        obj.desc = f.get("desc")
        obj.theme = f.get("theme")
        obj.icon = f.get("icon")
        obj.is_archived = bool(f.get("is_archived"))
    db.flush()
    folders_by_slug = {f.slug: f for f in db.query(models.Folder).filter(
        models.Folder.project_id == project_id).all()}

    # presentation-scope токены: заменяем для презентаций снапшота (палитры уровня презы)
    snap_pres_ids = [p["id"] for p in snapshot.get("presentations", [])]
    if snap_pres_ids:
        db.query(models.DesignToken).filter(
            models.DesignToken.presentation_id.in_(snap_pres_ids),
            models.DesignToken.slide_id.is_(None)).delete(synchronize_session=False)
        db.flush()
    for t in snapshot.get("tokens", []):
        if t.get("presentation_id") is not None and t.get("slide_id") is None:
            db.add(models.DesignToken(
                presentation_id=t["presentation_id"], token_key=t["token_key"],
                token_type=t.get("token_type", "color"), value=t.get("value"),
                is_custom=bool(t.get("is_custom"))))

    # презентации + слайды (только существующие id; новые не создаём)
    for p in snapshot.get("presentations", []):
        obj = db.query(models.Presentation).filter(models.Presentation.id == p["id"]).first()
        if not obj:
            continue
        for k in ("title", "audio_src", "audio_timeline", "variant", "style_preset",
                  "style_lock", "chessboard", "palette_source", "visibility"):
            if k in p:
                setattr(obj, k, p[k])
        # слайды: полная замена (slide_id сохраняем). Сначала снять slide-scope токены,
        # иначе FK design_tokens.slide_id → slides.id помешает удалению.
        old_slide_ids = [row[0] for row in db.query(models.Slide.id).filter(
            models.Slide.presentation_id == obj.id).all()]
        if old_slide_ids:
            db.query(models.DesignToken).filter(
                models.DesignToken.slide_id.in_(old_slide_ids)).delete(
                synchronize_session=False)
        for s in db.query(models.Slide).filter(models.Slide.presentation_id == obj.id).all():
            db.delete(s)  # cascade удалит slide_data/director_events
        db.flush()
        for idx, sl in enumerate(p.get("slides", [])):
            slide = models.Slide(
                presentation_id=obj.id, slide_id=sl["slide_id"], component=sl["component"],
                start_time=sl.get("start_time") or 0, title=sl.get("title"),
                subtitle=sl.get("subtitle"), layout=sl.get("layout"),
                order_index=sl.get("order_index", idx))
            db.add(slide)
            db.flush()
            db.add(models.SlideData(slide_id=slide.id, payload=sl.get("payload") or {}))
        # ENTERPRISE Ф2: восстановление слайдов бампает версию презентации
        obj.version = (obj.version or 0) + 1

    # связи папка↔презентация
    for f in db.query(models.Folder).filter(models.Folder.project_id == project_id).all():
        f.presentations = []
    db.flush()
    for link in snapshot.get("folder_links", []):
        folder = folders_by_slug.get(link["slug"])
        if not folder:
            continue
        for pid in link.get("presentation_ids", []):
            pres = db.query(models.Presentation).filter(models.Presentation.id == pid).first()
            if pres:
                folder.presentations.append(pres)

    project.version = (project.version or 0) + 1
    db.commit()
    create_revision(db, project_id, source="restore", label="restore",
                    author_user_id=author_user_id,
                    on_behalf_of_user_id=on_behalf_of_user_id, force=True)
    return {"dry_run": False, "diff": diff}
