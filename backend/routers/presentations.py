from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from typing import List

from typing import Optional
from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..permissions import enforce_write, idempotency_guard, presentation_role, rank, require_view_presentation
from ..brand_config import public_config as _public_config, seed_bgm_from_config as _seed_bgm_from_config
from ..validation import validate_component_payload
from .projects import _merge_tokens

router = APIRouter(
    prefix="/presentations",
    tags=["presentations"],
    dependencies=[Depends(enforce_write)],
)


def _validate_slide_payload(component_slug: str, payload: dict, db: Session):
    """Проверяет payload слайда против схемы компонента. Поднимает 422 при ошибках."""
    if component_slug is None or payload is None:
        return
    comp = db.query(models.Component).filter(models.Component.slug == component_slug).first()
    if not comp:
        return  # компонент не найден — не блокируем (обратная совместимость)
    errors = validate_component_payload(payload, comp)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Payload не прошёл валидацию", "errors": errors},
        )


def _bump_presentation_version(db: Session, presentation_id: int):
    """ENTERPRISE Ф2: инкремент версии презентации на контентную мутацию."""
    if not presentation_id:
        return
    p = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if p:
        p.version = (p.version or 0) + 1


def _snapshot_slides(db: Session, presentation_id: int) -> list:
    """Снимок слайдов презентации для ревизии."""
    out = []
    for s in db.query(models.Slide).filter(
            models.Slide.presentation_id == presentation_id).order_by(models.Slide.order_index).all():
        payload = s.data.payload if s.data else {}
        out.append({"slide_id": s.slide_id, "component": s.component, "start_time": s.start_time,
                    "title": s.title, "subtitle": s.subtitle, "layout": s.layout,
                    "order_index": s.order_index, "payload": payload})
    return out


def _log_revision(db: Session, presentation_id: int, ops: list):
    """Фоновый лог правок (AI_PLATFORM Ф1). Никогда не роняет основной путь."""
    try:
        if not presentation_id:
            return
        last = db.query(models.PresentationRevision).filter(
            models.PresentationRevision.presentation_id == presentation_id
        ).order_by(models.PresentationRevision.n.desc()).first()
        n = (last.n if last else 0) + 1
        db.add(models.PresentationRevision(
            presentation_id=presentation_id, n=n, ops=ops,
            snapshot=_snapshot_slides(db, presentation_id)))
        db.commit()
    except Exception:
        db.rollback()  # лог не должен мешать записи


def _lint_slide_warnings(db: Session, presentation_id: int, component_slug: str,
                         payload: dict, title: str) -> list:
    """Style-lint слайда (P1): payload-правила + контраст заголовка. Не блокирует."""
    from ..style_lint import lint_payload, lint_slide_contrast
    warnings: list = []
    comp = db.query(models.Component).filter(models.Component.slug == component_slug).first()
    if comp and comp.payload_schema and isinstance(payload, dict):
        warnings += lint_payload(payload, comp.payload_schema, component_slug=component_slug)
    try:
        pres = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
        project_id = None
        pres_variant = None
        if pres:
            pres_variant = getattr(pres, "variant", None)
            for folder in (pres.folders or []):
                if getattr(folder, "project_id", None):
                    project_id = folder.project_id
                    break
        tokens = _merge_tokens(db, project_id=project_id)
        variant_slug = ((payload or {}).get("variant") if isinstance(payload, dict) else None) or pres_variant or "tech"
        surface_bg = None
        var = db.query(models.StyleVariant).filter(models.StyleVariant.slug == variant_slug).first()
        if var and isinstance(var.config, dict):
            surface_bg = (var.config.get("surface") or {}).get("bg", {}).get("value")
        warnings += lint_slide_contrast(title, tokens, surface_bg)
    except Exception:
        pass  # линт никогда не роняет сохранение
    return warnings

@router.get("/folders", response_model=List[schemas.Folder])
def read_folders(include_archived: bool = False, db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    """Список папок (AUTH_PLAN Ф4c). Требует входа; отдаёт только папки видимых
    проектов; приватные презентации вырезаются. Раньше отдавал ВСЁ анониму."""
    from ..permissions import AUTH_MODE, can_view_presentation
    from .projects import _visible_filter
    q = db.query(models.Folder).filter(models.Folder.is_archived.is_(False))
    is_admin = user is not None and getattr(user, "is_superadmin", False)
    if AUTH_MODE == "on" and not is_admin:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        proj_ids = [r[0] for r in _visible_filter(db.query(models.Project.id), user).all()]
        q = q.filter(models.Folder.project_id.in_(proj_ids))
    folders = q.all()
    for f in folders:
        if not include_archived:
            f.presentations = [p for p in f.presentations if not getattr(p, "is_archived", False)]
        f.presentations = [p for p in f.presentations if can_view_presentation(db, p, user)]
    return folders

@router.get("/folders/{slug}", response_model=schemas.Folder)
def read_folder(slug: str, include_archived: bool = False, db: Session = Depends(get_db),
                user: Optional[models.User] = Depends(get_current_user)):
    from ..permissions import AUTH_MODE, can_view_presentation
    from .projects import _get_visible_project
    folder = db.query(models.Folder).filter(models.Folder.slug == slug).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    is_admin = user is not None and getattr(user, "is_superadmin", False)
    if AUTH_MODE == "on" and not is_admin:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if folder.project_id is None:
            raise HTTPException(status_code=403, detail="Folder has no project")
        _get_visible_project(db, folder.project_id, user)
    if not include_archived:
        folder.presentations = [p for p in folder.presentations if not getattr(p, "is_archived", False)]
    folder.presentations = [p for p in folder.presentations if can_view_presentation(db, p, user)]
    return folder


@router.get("/folders/{slug}/summary", response_model=schemas.FolderSummary)
def read_folder_summary(slug: str, include_archived: bool = False, db: Session = Depends(get_db),
                        user: Optional[models.User] = Depends(get_current_user)):
    """Лёгкая папка: презентации без слайдов (slides_count) + slug проекта для
    навигации. Один запрос вместо выгрузки всех папок со всеми слайдами."""
    from ..permissions import AUTH_MODE, can_view_presentation
    from .projects import _get_visible_project
    folder = db.query(models.Folder).filter(models.Folder.slug == slug).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    is_admin = user is not None and getattr(user, "is_superadmin", False)
    if AUTH_MODE == "on" and not is_admin:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if folder.project_id is None:
            raise HTTPException(status_code=403, detail="Folder has no project")
        _get_visible_project(db, folder.project_id, user)
    presentations = list(folder.presentations or [])
    if not include_archived:
        presentations = [p for p in presentations if not getattr(p, "is_archived", False)]
    presentations = [p for p in presentations if can_view_presentation(db, p, user)]
    return {
        "id": folder.id, "slug": folder.slug, "title": folder.title, "desc": folder.desc,
        "theme": folder.theme, "icon": folder.icon, "project_id": folder.project_id,
        "is_archived": bool(getattr(folder, "is_archived", False)),
        "project_slug": folder.project.slug if folder.project else None,
        "presentations": [
            {
                "id": p.id, "title": p.title, "is_archived": bool(getattr(p, "is_archived", False)),
                "visibility": getattr(p, "visibility", "public"), "variant": p.variant,
                "style_preset": p.style_preset, "chessboard": getattr(p, "chessboard", False),
                "slides_count": len(p.slides or []),
            }
            for p in presentations
        ],
    }


@router.get("/search/media")
def search_media(q: str, type: str = 'image', source: str = 'searxng', engines: str = ''):
    if source == 'searxng':
        categories = 'images' if type == 'image' else 'videos'
        # Request from the SearXNG backend locally or via HTTP bypassing CORS
        url = f"https://search.it2b.top/search?q={q}&format=json&categories={categories}"
        if engines:
            mapped_engines = []
            for eng in engines.split(','):
                eng = eng.strip()
                if eng == 'pixabay':
                    mapped_engines.append('pixabay images' if type == 'image' else 'pixabay videos')
                elif eng == 'bing':
                    mapped_engines.append('bing images' if type == 'image' else 'bing videos')
                else:
                    mapped_engines.append(eng)
            url += f"&engines={','.join(mapped_engines)}"
        try:
            import requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for r in data.get('results', []):
                results.append({
                    "id": r.get('url'),
                    "url": r.get('img_src') or r.get('url'),
                    "thumbnail": r.get('thumbnail') or r.get('thumbnail_src') or r.get('img_src') or r.get('url'),
                    "title": r.get('title'),
                    "source": r.get('engine') or r.get('source', 'SearXNG'),
                    "format": r.get('img_format', ''),
                    "content": r.get('content', ''),
                    "source_url": r.get('url'),
                    "iframe": r.get('iframe_src', '')
                })
            return {"results": results}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"SearXNG error: {str(e)}")
            
    return {"results": []}

@router.get("/", response_model=List[schemas.Presentation])
def read_presentations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    """Список презентаций (AUTH_PLAN Ф3). При AUTH_MODE=on отдаём только
    презентации видимых проектов (владелец/участник/шаблоны/системные) —
    плюс «осиротевшие» без папок (обратная совместимость). Супер-админ видит все."""
    from ..permissions import AUTH_MODE
    from .projects import _visible_filter
    from sqlalchemy import select
    q = db.query(models.Presentation)
    if AUTH_MODE == "on":
        is_admin = user is not None and getattr(user, "is_superadmin", False)
        if not is_admin:
            # только видимые проекты + «осиротевшие» без папок
            proj_ids = [r[0] for r in _visible_filter(db.query(models.Project.id), user).all()]
            in_visible_projects = select(models.folder_presentation.c.presentation_id).join(
                models.Folder,
                models.Folder.id == models.folder_presentation.c.folder_id,
            ).where(models.Folder.project_id.in_(proj_ids))
            no_folder = ~models.Presentation.id.in_(
                select(models.folder_presentation.c.presentation_id))
            q = q.filter(models.Presentation.id.in_(in_visible_projects) | no_folder)
            # приватные презентации не показываем в списке без явного доступа
            q = q.filter((models.Presentation.visibility != "private")
                         | models.Presentation.visibility.is_(None))
    return q.offset(skip).limit(limit).all()


@router.get("/{presentation_id}/access")
def presentation_access(presentation_id: int, db: Session = Depends(get_db),
                        user: Optional[models.User] = Depends(get_current_user)):
    """Права текущего запроса на презентацию (AUTH_PLAN Ф2). Публичный read,
    возвращает role: owner|editor|viewer|null. Фронт прячет редактор при can_edit=false."""
    role = presentation_role(db, presentation_id, user)
    return {
        "role": role,
        "can_edit": rank(role) >= rank("editor"),
        "can_style": rank(role) >= rank("owner"),
        "authenticated": user is not None,
    }


@router.get("/{presentation_id}/config", dependencies=[Depends(require_view_presentation)])
def presentation_config(presentation_id: int, db: Session = Depends(get_db),
                        user: Optional[models.User] = Depends(get_current_user)):
    """BRAND KIT проекта презентации: brand-ассеты, контакты, дефолты компонентов.
    Фронт мержит defaults[<Component>] под payload — чтобы не дублировать лого/QR/контакты
    в каждом слайде. Для не-редакторов отдаём только публичную часть (без email/phone)."""
    from ..permissions import presentation_project_ids
    pids = presentation_project_ids(db, presentation_id)
    cfg = {}
    chosen = pids[0] if pids else None
    for pid in pids:
        proj = db.query(models.Project).filter(models.Project.id == pid).first()
        if proj and getattr(proj, "config", None):
            cfg = proj.config
            chosen = pid
            break
    can_manage = rank(presentation_role(db, presentation_id, user)) >= rank("editor")
    public_cfg = (cfg or {}) if can_manage else _public_config(cfg)
    return {"project_id": chosen, "config": public_cfg}


@router.get("/{presentation_id}/style", dependencies=[Depends(require_view_presentation)])
def get_presentation_style(presentation_id: int, db: Session = Depends(get_db)):
    """Вектор стилей презентации: пресет (разрезолвленный) + лок."""
    pres = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")
    preset = None
    if getattr(pres, "style_preset", None):
        preset = db.query(models.StylePreset).filter(
            models.StylePreset.slug == pres.style_preset,
            models.StylePreset.is_archived.is_(False),
        ).first()
    return {
        "style_preset": getattr(pres, "style_preset", None),
        "style_lock": bool(getattr(pres, "style_lock", False)),
        "preset": ({
            "slug": preset.slug, "title": preset.title, "palette": preset.palette,
            "variant": preset.variant, "rules": preset.rules or {},
        } if preset else None),
    }


@router.put("/{presentation_id}/style")
def update_presentation_style(presentation_id: int, req: schemas.PresentationStyleUpdate,
                              db: Session = Depends(get_db)):
    """Назначить пресет и/или лок. Ссылки проверяются (400 при битых)."""
    pres = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")
    data = req.dict(exclude_unset=True)
    if "style_preset" in data and data["style_preset"]:
        preset = db.query(models.StylePreset).filter(
            models.StylePreset.slug == data["style_preset"],
            models.StylePreset.is_archived.is_(False),
        ).first()
        if not preset:
            raise HTTPException(status_code=400, detail=f"Preset '{data['style_preset']}' not found")
        pres.style_preset = data["style_preset"]
    elif "style_preset" in data:
        pres.style_preset = None
    if "style_lock" in data:
        pres.style_lock = bool(data["style_lock"])
    # Лок без вектора — молча ничего не защищает: запрещаем явно
    if pres.style_lock and not pres.style_preset:
        raise HTTPException(status_code=400, detail="style_lock requires style_preset")
    db.commit()
    db.refresh(pres)
    return {
        "style_preset": getattr(pres, "style_preset", None),
        "style_lock": bool(getattr(pres, "style_lock", False)),
    }


def _enforce_preset_lock(db: Session, presentation_id: int, component_slug: str,
                         payload: dict, title: str):
    """Вектор залоченной презентации: variant + rules пресета как ERRORS → 422."""
    from ..style_lint import lint_preset
    pres = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not pres or not getattr(pres, "style_lock", False) or not getattr(pres, "style_preset", None):
        return
    preset = db.query(models.StylePreset).filter(
        models.StylePreset.slug == pres.style_preset,
        models.StylePreset.is_archived.is_(False),
    ).first()
    if not preset:
        return
    comp = db.query(models.Component).filter(models.Component.slug == component_slug).first()
    effective = ((payload or {}).get("variant") if isinstance(payload, dict) else None) \
        or getattr(pres, "variant", None) or "tech"
    rules = {"variant": getattr(preset, "variant", None), **(preset.rules or {})}
    errors = lint_preset(payload, comp.payload_schema if comp and comp.payload_schema else None,
                         title, effective, rules)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": f"Слайд вне вектора пресета '{preset.slug}'", "errors": errors},
        )


@router.get("/{presentation_id}/tokens", dependencies=[Depends(require_view_presentation)])
def get_presentation_tokens(presentation_id: int, db: Session = Depends(get_db)):
    """Токены темы проекта, к которому принадлежит презентация (Фаза 2)."""
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    # презентация → папка → проект
    project_id = None
    for folder in presentation.folders:
        if folder.project_id:
            project_id = folder.project_id
            break

    # ВАЖНО: передаём presentation_id — иначе presentation-scope слой игнорируется
    tokens = _merge_tokens(db, project_id=project_id, presentation_id=presentation_id)
    own = db.query(models.DesignToken).filter(
        models.DesignToken.presentation_id == presentation_id,
        models.DesignToken.slide_id.is_(None)).count()
    return {"project_id": project_id, "palette_source": getattr(presentation, "palette_source", None),
            "presentation_tokens": own, "tokens": tokens}


@router.put("/{presentation_id}/tokens")
def upsert_presentation_tokens(presentation_id: int, req: schemas.DesignTokensUpsert,
                               db: Session = Depends(get_db)):
    """Точечная правка токенов на уровне ПРЕЗЕНТАЦИИ (перекрывает проект)."""
    from .projects import _infer_token_type
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    for key, value in req.tokens.items():
        if value is None:
            continue
        token = db.query(models.DesignToken).filter(
            models.DesignToken.presentation_id == presentation_id,
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.token_key == key,
        ).first()
        if token:
            token.value = str(value)
        else:
            db.add(models.DesignToken(
                presentation_id=presentation_id,
                token_key=key,
                token_type=_infer_token_type(key),
                value=str(value),
                is_custom=True,
            ))
    db.commit()
    project_id = None
    for folder in presentation.folders:
        if folder.project_id:
            project_id = folder.project_id
            break
    return {"tokens": _merge_tokens(db, project_id=project_id, presentation_id=presentation_id)}


@router.delete("/{presentation_id}/tokens/{key}")
def delete_presentation_token(presentation_id: int, key: str, db: Session = Depends(get_db)):
    """Удаление presentation-scope токена — только custom."""
    token = db.query(models.DesignToken).filter(
        models.DesignToken.presentation_id == presentation_id,
        models.DesignToken.slide_id.is_(None),
        models.DesignToken.token_key == key,
    ).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if not getattr(token, "is_custom", False):
        raise HTTPException(status_code=403, detail="Only custom tokens can be deleted")
    db.delete(token)
    db.commit()
    return {"status": "deleted"}


@router.post("/{presentation_id}/palette/copy")
def copy_palette_to_presentation(presentation_id: int, req: schemas.PaletteCopyRequest,
                                 db: Session = Depends(get_db)):
    """Взять палитру из проекта/шаблона ТОЛЬКО для этой презентации (presentation-scope)."""
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    source = db.query(models.Project).filter(models.Project.slug == req.from_project).first()
    if not source:
        raise HTTPException(status_code=400, detail=f"Source project '{req.from_project}' not found")
    merged = _merge_tokens(db, project_id=source.id)
    source_keys = set(merged.keys())
    copied = 0
    for key, tok in merged.items():
        value = tok.get("value") if isinstance(tok, dict) else tok
        if value is None:
            continue
        existing = db.query(models.DesignToken).filter(
            models.DesignToken.presentation_id == presentation_id,
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.token_key == key,
        ).first()
        if existing:
            if getattr(existing, "is_custom", False):
                continue
            existing.value = str(value)
        else:
            db.add(models.DesignToken(
                presentation_id=presentation_id,
                token_key=key,
                token_type=tok.get("type", "color") if isinstance(tok, dict) else "color",
                value=str(value),
                is_custom=False,
            ))
        copied += 1
    # REPLACE: managed-переопределения, которых нет в источнике, убираем (лес не «застревает»)
    removed = 0
    for t in db.query(models.DesignToken).filter(
            models.DesignToken.presentation_id == presentation_id,
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.is_custom.is_(False)).all():
        if t.token_key not in source_keys:
            db.delete(t)
            removed += 1
    presentation.palette_source = source.slug
    db.commit()
    return {"copied": copied, "removed": removed, "palette_source": source.slug}


@router.post("/{presentation_id}/palette/clear")
def clear_presentation_palette(presentation_id: int, db: Session = Depends(get_db)):
    """Сбросить presentation-scope палитру → презентация снова наследует проект.
    Кастомные токены презентации сохраняем."""
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    q = db.query(models.DesignToken).filter(
        models.DesignToken.presentation_id == presentation_id,
        models.DesignToken.slide_id.is_(None),
        models.DesignToken.is_custom.is_(False),
    )
    n = q.count()
    q.delete(synchronize_session=False)
    presentation.palette_source = None
    db.commit()
    return {"removed": n}


def _op_effective_variant(db, pres, op):
    """Эффективный вариант слайда для preset-lock (payload.variant → presentation.variant → tech)."""
    v = getattr(op, "variant", None)
    if not v and isinstance(op.payload, dict):
        v = op.payload.get("variant")
    return v or getattr(pres, "variant", None) or "tech"


@router.post("/{presentation_id}/change-set", dependencies=[Depends(idempotency_guard)])
def apply_change_set(presentation_id: int, req: schemas.ChangeSetRequest,
                     db: Session = Depends(get_db),
                     user: Optional[models.User] = Depends(get_current_user)):
    """Атомарный набор операций (AI_PLATFORM Ф2). dry_run=true (по умолчанию) —
    только проверка и diff, ничего не пишем. apply — одна транзакция, rollback при ошибке."""
    from ..style_lint import lint_payload, lint_preset
    pres = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    # Операции уровня СТИЛЯ доступны только владельцу (AUTH_PLAN: тема — не editor).
    _style_ops = {"set_tokens", "apply_palette", "set_presentation_variant"}
    if any((op.op or "").strip() in _style_ops for op in (req.ops or [])):
        from ..permissions import AUTH_MODE
        if AUTH_MODE == "on" and rank(presentation_role(db, presentation_id, user)) < rank("owner"):
            raise HTTPException(status_code=403, detail="Стиль/палитра — только владелец проекта")

    # быстрый доступ к слайдам по slide_id
    def slides_map():
        return {s.slide_id: s for s in db.query(models.Slide).filter(
            models.Slide.presentation_id == presentation_id).all()}

    errors, warnings, diff = [], [], []
    S = slides_map()

    for i, op in enumerate(req.ops or []):
        p = f"ops[{i}]"
        kind = (op.op or "").strip()
        if kind == "add_slide":
            if not op.slide_id or not op.component:
                errors.append({"path": p, "type": "missing_field",
                               "message": "add_slide требует slide_id и component"})
                continue
            if op.slide_id in S:
                errors.append({"path": p, "type": "duplicate",
                               "message": f"slide_id '{op.slide_id}' уже существует"})
                continue
            comp = db.query(models.Component).filter(models.Component.slug == op.component).first()
            if not comp:
                errors.append({"path": p, "type": "unknown_component",
                               "message": f"компонент '{op.component}' не найден"})
                continue
            payload = op.payload or {}
            errors += [{"path": f"{p}.{e['path']}", "type": e["type"], "message": e["message"]}
                       for e in validate_component_payload(payload, comp)]
            warnings += [{"path": f"{p}.{w['path']}", "type": w["type"], "message": w["message"]}
                         for w in lint_payload(payload, comp.payload_schema, component_slug=op.component)]
            if getattr(pres, "style_lock", False) and getattr(pres, "style_preset", None):
                pr = db.query(models.StylePreset).filter(
                    models.StylePreset.slug == pres.style_preset).first()
                if pr:
                    rules = {"variant": pr.variant, **(pr.rules or {})}
                    errors += [{"path": f"{p}.{e['path']}", "type": e["type"], "message": e["message"]}
                               for e in lint_preset(payload, comp.payload_schema, op.title,
                                                    _op_effective_variant(db, pres, op), rules)]
            diff.append({"op": kind, "slide_id": op.slide_id, "component": op.component,
                         "change": "create", "title": op.title})
        elif kind in ("update_slide", "set_slide_variant"):
            sl = S.get(op.slide_id)
            if not sl:
                errors.append({"path": p, "type": "not_found",
                               "message": f"слайд '{op.slide_id}' не найден"})
                continue
            cur = (sl.data.payload if sl.data else {}) or {}
            new_payload = dict(cur)
            if kind == "set_slide_variant":
                if op.variant:
                    new_payload["variant"] = op.variant
                else:
                    new_payload.pop("variant", None)
            else:
                if op.payload is not None:
                    new_payload = dict(op.payload)
                if op.patch:
                    new_payload.update(op.patch)
            comp = db.query(models.Component).filter(models.Component.slug == sl.component).first()
            if comp:
                errors += [{"path": f"{p}.{e['path']}", "type": e["type"], "message": e["message"]}
                           for e in validate_component_payload(new_payload, comp)]
                warnings += [{"path": f"{p}.{w['path']}", "type": w["type"], "message": w["message"]}
                             for w in lint_payload(new_payload, comp.payload_schema, component_slug=sl.component)]
            diff.append({"op": kind, "slide_id": op.slide_id, "change": "modify",
                         "fields": (["variant"] if kind == "set_slide_variant"
                                    else list((op.payload or op.patch or {}).keys())),
                         "title": op.title or sl.title})
        elif kind == "delete_slide":
            if not S.get(op.slide_id):
                errors.append({"path": p, "type": "not_found",
                               "message": f"слайд '{op.slide_id}' не найден"})
                continue
            diff.append({"op": kind, "slide_id": op.slide_id, "change": "delete",
                         "title": S[op.slide_id].title})
        elif kind == "reorder_slides":
            ids = op.order or []
            missing = [x for x in ids if x not in S]
            if missing:
                errors.append({"path": p, "type": "not_found", "message": f"нет слайдов: {missing}"})
            diff.append({"op": kind, "change": "reorder", "order": ids})
        elif kind == "set_presentation_variant":
            diff.append({"op": kind, "change": "presentation.variant",
                         "from": getattr(pres, "variant", None), "to": op.variant})
        elif kind == "set_tokens":
            diff.append({"op": kind, "change": "tokens", "keys": list((op.tokens or {}).keys())})
        elif kind == "apply_palette":
            diff.append({"op": kind, "change": "palette", "from_project": op.from_project})
        else:
            errors.append({"path": p, "type": "unknown_op", "message": f"неизвестная операция '{kind}'"})

    result = {"valid": len(errors) == 0, "errors": errors, "warnings": warnings, "diff": diff}
    if req.dry_run or errors:
        return result

    # ENTERPRISE Ф2: авто-точка перед применением правок ИИ (не разрушающе).
    try:
        from ..revisions import create_revision
        from ..permissions import presentation_project_ids
        for _pid in presentation_project_ids(db, presentation_id):
            create_revision(db, _pid, source="ai", label="before change-set",
                            on_behalf_of_user_id=getattr(user, "id", None))
    except Exception as _e:  # noqa: BLE001
        print(f"[revisions] pre-change-set checkpoint skipped: {_e}", flush=True)

    # ---- apply: одна транзакция, rollback при любой ошибке ----
    try:
        for op in req.ops:
            kind = op.op
            if kind == "add_slide":
                s = models.Slide(presentation_id=presentation_id, slide_id=op.slide_id,
                                 component=op.component, start_time=op.start_time or 0,
                                 title=op.title, subtitle=op.subtitle, layout="col",
                                 order_index=op.order_index if op.order_index is not None else 0)
                db.add(s); db.flush()
                db.add(models.SlideData(slide_id=s.id, payload=op.payload or {}))
            elif kind == "update_slide":
                sl = db.query(models.Slide).filter(
                    models.Slide.presentation_id == presentation_id,
                    models.Slide.slide_id == op.slide_id).first()
                cur = (sl.data.payload if sl.data else {}) or {}
                new_payload = dict(op.payload) if op.payload is not None else dict(cur)
                if op.patch:
                    new_payload.update(op.patch)
                if sl.data:
                    db.delete(sl.data)
                db.add(models.SlideData(slide_id=sl.id, payload=new_payload))
                if op.title is not None: sl.title = op.title
                if op.subtitle is not None: sl.subtitle = op.subtitle
                if op.start_time is not None: sl.start_time = op.start_time
                if op.order_index is not None: sl.order_index = op.order_index
            elif kind == "set_slide_variant":
                sl = db.query(models.Slide).filter(
                    models.Slide.presentation_id == presentation_id,
                    models.Slide.slide_id == op.slide_id).first()
                cur = dict((sl.data.payload if sl.data else {}) or {})
                if op.variant: cur["variant"] = op.variant
                else: cur.pop("variant", None)
                if sl.data: db.delete(sl.data)
                db.add(models.SlideData(slide_id=sl.id, payload=cur))
            elif kind == "delete_slide":
                sl = db.query(models.Slide).filter(
                    models.Slide.presentation_id == presentation_id,
                    models.Slide.slide_id == op.slide_id).first()
                if sl: db.delete(sl)
            elif kind == "reorder_slides":
                for idx, sid in enumerate(op.order or []):
                    sl = db.query(models.Slide).filter(
                        models.Slide.presentation_id == presentation_id,
                        models.Slide.slide_id == sid).first()
                    if sl: sl.order_index = idx
            elif kind == "set_presentation_variant":
                pres.variant = op.variant
            elif kind == "set_tokens":
                from .projects import _infer_token_type
                for key, value in (op.tokens or {}).items():
                    if value is None: continue
                    tok = db.query(models.DesignToken).filter(
                        models.DesignToken.presentation_id == presentation_id,
                        models.DesignToken.slide_id.is_(None),
                        models.DesignToken.token_key == key).first()
                    if tok: tok.value = str(value)
                    else: db.add(models.DesignToken(
                        presentation_id=presentation_id, token_key=key,
                        token_type=_infer_token_type(key), value=str(value), is_custom=True))
            elif kind == "apply_palette":
                src = db.query(models.Project).filter(models.Project.slug == op.from_project).first()
                if not src:
                    raise ValueError(f"source '{op.from_project}' not found")
                merged = _merge_tokens(db, project_id=src.id)
                keys = set(merged.keys())
                for key, tok in merged.items():
                    value = tok.get("value") if isinstance(tok, dict) else tok
                    if value is None: continue
                    t = db.query(models.DesignToken).filter(
                        models.DesignToken.presentation_id == presentation_id,
                        models.DesignToken.slide_id.is_(None),
                        models.DesignToken.token_key == key).first()
                    if t: t.value = str(value)
                    else: db.add(models.DesignToken(
                        presentation_id=presentation_id, token_key=key,
                        token_type=tok.get("type", "color") if isinstance(tok, dict) else "color",
                        value=str(value), is_custom=False))
                for t in db.query(models.DesignToken).filter(
                        models.DesignToken.presentation_id == presentation_id,
                        models.DesignToken.slide_id.is_(None),
                        models.DesignToken.is_custom.is_(False)).all():
                    if t.token_key not in keys: db.delete(t)
                pres.palette_source = src.slug
        # ENTERPRISE Ф2: ИИ-правки тоже бампают версию (optimistic locking не слеп).
        _bump_presentation_version(db, presentation_id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"change-set apply failed: {e}")

    _log_revision(db, presentation_id, [{"op": o.op, "slide_id": o.slide_id} for o in req.ops])
    result["applied"] = True
    return result


@router.get("/{presentation_id}/ai-context", dependencies=[Depends(require_view_presentation)])
def get_ai_context(presentation_id: int, db: Session = Depends(get_db)):
    """Единый контекст для ИИ-агента (AI_PLATFORM Ф1, read-only): brief + тема +
    пресет + допустимые варианты + каталог компонентов + покрытие + сводка слайдов."""
    presentation = db.query(models.Presentation).filter(
        models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    project_id = None
    for folder in presentation.folders:
        if folder.project_id:
            project_id = folder.project_id
            break

    tokens = _merge_tokens(db, project_id=project_id, presentation_id=presentation_id)

    preset = None
    if getattr(presentation, "style_preset", None):
        p = db.query(models.StylePreset).filter(
            models.StylePreset.slug == presentation.style_preset,
            models.StylePreset.is_archived.is_(False)).first()
        if p:
            preset = {"slug": p.slug, "title": p.title, "palette": p.palette,
                      "variant": p.variant, "rules": p.rules or {},
                      "lock": bool(getattr(presentation, "style_lock", False))}

    variants = [{"slug": v.slug, "name": v.name, "config": v.config}
                for v in db.query(models.StyleVariant).filter(
                    models.StyleVariant.is_archived.is_(False)).all()]

    comps = [{"slug": c.slug, "title": c.title, "manifest": c.manifest,
              "payload_schema": c.payload_schema, "example": c.example}
             for c in db.query(models.Component).order_by(models.Component.id).all()]

    project = db.query(models.Project).filter(models.Project.id == project_id).first() if project_id else None
    brief = getattr(project, "brief", None) if project else None

    slides = [{"slide_id": s.slide_id, "component": s.component,
               "start_time": s.start_time, "order_index": s.order_index, "title": s.title,
               "variant": (s.data.payload or {}).get("variant") if s.data else None}
              for s in db.query(models.Slide).filter(
                  models.Slide.presentation_id == presentation_id
              ).order_by(models.Slide.order_index).all()]

    return {
        "presentation": {"id": presentation.id, "title": presentation.title,
                         "variant": presentation.variant,
                         "style_preset": getattr(presentation, "style_preset", None),
                         "palette_source": getattr(presentation, "palette_source", None),
                         "chessboard": bool(getattr(presentation, "chessboard", False))},
        "project": {"id": project_id, "slug": getattr(project, "slug", None)} if project else None,
        "config": getattr(project, "config", None) if project else None,
        "brief": brief,
        "tokens": tokens,
        "preset": preset,
        "variants": variants,
        "components": comps,
        "slides": slides,
    }


@router.get("/{presentation_id}/revisions", dependencies=[Depends(require_view_presentation)])
def get_revisions(presentation_id: int, db: Session = Depends(get_db)):
    """История правок презентации (AI_PLATFORM Ф1)."""
    rows = db.query(models.PresentationRevision).filter(
        models.PresentationRevision.presentation_id == presentation_id
    ).order_by(models.PresentationRevision.n.desc()).limit(50).all()
    return [{"n": r.n, "ops": r.ops, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows]


@router.post("/{presentation_id}/revisions/{n}/restore")
def restore_revision(presentation_id: int, n: int, db: Session = Depends(get_db)):
    """Откат к ревизии n: пересобирает слайды из снимка. Пишет новую ревизию."""
    rev = db.query(models.PresentationRevision).filter(
        models.PresentationRevision.presentation_id == presentation_id,
        models.PresentationRevision.n == n).first()
    if not rev or not rev.snapshot:
        raise HTTPException(status_code=404, detail="Revision not found")
    # снести текущие слайды
    for s in db.query(models.Slide).filter(models.Slide.presentation_id == presentation_id).all():
        db.delete(s)
    db.commit()
    # восстановить из снимка
    for item in rev.snapshot:
        s = models.Slide(
            presentation_id=presentation_id, slide_id=item.get("slide_id"),
            component=item.get("component"), start_time=item.get("start_time") or 0,
            title=item.get("title"), subtitle=item.get("subtitle"),
            layout=item.get("layout"), order_index=item.get("order_index") or 0)
        db.add(s)
        db.flush()
        db.add(models.SlideData(slide_id=s.id, payload=item.get("payload") or {}))
    db.commit()
    _log_revision(db, presentation_id, [{"op": "restore_revision", "n": n}])
    return {"status": "restored", "n": n, "slides": len(rev.snapshot)}


@router.get("/{presentation_id}/global-media", response_model=List[schemas.MediaFile], dependencies=[Depends(require_view_presentation)])
def read_presentation_global_media(presentation_id: int, db: Session = Depends(get_db)):
    # Find the folder(s) this presentation belongs to
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
        
    media_files = db.query(models.MediaFile)\
        .join(models.Presentation, models.MediaFile.presentation_id == models.Presentation.id)\
        .join(models.folder_presentation, models.Presentation.id == models.folder_presentation.c.presentation_id)\
        .join(models.Folder, models.folder_presentation.c.folder_id == models.Folder.id)\
        .filter(models.Folder.project_id.in_(
            db.query(models.Folder.project_id)\
            .join(models.folder_presentation)\
            .filter(models.folder_presentation.c.presentation_id == presentation_id)
        ))\
        .distinct()\
        .all()
    return media_files

@router.get("/{presentation_id}", response_model=schemas.Presentation, dependencies=[Depends(require_view_presentation)])
def read_presentation(presentation_id: int, db: Session = Depends(get_db)):
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return presentation

@router.post("/", response_model=schemas.Presentation)
def create_presentation(presentation: schemas.PresentationCreate, db: Session = Depends(get_db)):
    db_presentation = models.Presentation(
        title=presentation.title,
        audio_src=presentation.audio_src,
        audio_timeline=presentation.audio_timeline,
        variant=presentation.variant,
    )
    db.add(db_presentation)

    if presentation.folder_id:
        folder = db.query(models.Folder).filter(models.Folder.id == presentation.folder_id).first()
        if folder:
            folder.presentations.append(db_presentation)
            proj = None
            if folder.project_id:
                proj = db.query(models.Project).filter(
                    models.Project.id == folder.project_id).first()
            # UX-4: дефолтный вариант проекта, если явно не задан
            if not db_presentation.variant and proj and getattr(proj, "default_variant", None):
                db_presentation.variant = proj.default_variant
            # BRAND KIT: фоновая музыка проекта в новую презентацию (если таймлайн не задан)
            if not db_presentation.audio_timeline and proj:
                _seed_bgm_from_config(db_presentation, getattr(proj, "config", None))

    db.commit()
    db.refresh(db_presentation)
    return db_presentation

@router.put("/{presentation_id}", response_model=schemas.Presentation)
def update_presentation(presentation_id: int, presentation: schemas.PresentationUpdate,
                        db: Session = Depends(get_db),
                        user: Optional[models.User] = Depends(get_current_user)):
    db_presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not db_presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    from sqlalchemy.orm.attributes import flag_modified
    update_data = presentation.dict(exclude_unset=True)

    # Видимость (public/private) — приватность шаринга: только владелец/супер-админ.
    if "visibility" in update_data:
        if update_data["visibility"] not in ("public", "private"):
            raise HTTPException(status_code=400, detail="visibility: public или private")
        from ..permissions import AUTH_MODE
        if AUTH_MODE == "on" and rank(presentation_role(db, presentation_id, user)) < rank("owner"):
            raise HTTPException(status_code=403, detail="Менять видимость может только владелец")

    # Защита BGM: если клиент присылает audio_timeline без фоновой музыки,
    # а раньше она была — не теряем её (UI-сохранения не должны гасить BGM).
    # Музыка — клипы с type=="audio"; защищаем по id дорожки (bgm/overlay).
    new_tl = update_data.get("audio_timeline")
    old_tl = getattr(db_presentation, "audio_timeline", None)
    if isinstance(new_tl, dict) and isinstance(old_tl, dict):
        new_tracks = new_tl.get("tracks")
        if isinstance(new_tracks, list):
            old_bgm_by_track = {}
            for t in (old_tl.get("tracks") or []):
                clips = [c for c in (t.get("clips") or []) if c.get("type") == "audio"]
                if clips:
                    old_bgm_by_track[t.get("id")] = clips
            for tid, clips in old_bgm_by_track.items():
                nt = next((t for t in new_tracks if t.get("id") == tid), None)
                if nt is not None and any(c.get("type") == "audio" for c in (nt.get("clips") or [])):
                    continue
                # не дублировать: если этот же файл уже есть в любой дорожке — не возвращаем
                existing_srcs = {c.get("src") for t in new_tracks for c in (t.get("clips") or [])}
                if any(c.get("src") in existing_srcs for c in clips):
                    continue
                if nt is None:
                    new_tracks.append({"id": tid, "type": "bgm" if tid == "bgm" else "voiceover",
                                       "clips": clips})
                else:
                    nt["clips"] = clips

    # ENTERPRISE Ф2: optimistic locking — 409 при рассинхроне версий.
    exp = update_data.pop("expected_version", None)
    if exp is not None and int(exp) != int(db_presentation.version or 0):
        raise HTTPException(status_code=409, detail="version_conflict")

    for key, value in update_data.items():
        setattr(db_presentation, key, value)
        if key == "audio_timeline":
            flag_modified(db_presentation, "audio_timeline")

    db_presentation.version = (db_presentation.version or 0) + 1
    db.commit()
    db.refresh(db_presentation)
    return db_presentation

@router.post("/{presentation_id}/slides", response_model=schemas.Slide)
def create_slide_for_presentation(
    presentation_id: int, slide: schemas.SlideCreate, db: Session = Depends(get_db)
):
    _validate_slide_payload(slide.component, slide.data.payload if slide.data else None, db)
    _enforce_preset_lock(db, presentation_id, slide.component,
                         slide.data.payload if slide.data else None, slide.title)

    db_slide = models.Slide(
        presentation_id=presentation_id,
        slide_id=slide.slide_id,
        component=slide.component,
        start_time=slide.start_time,
        title=slide.title,
        subtitle=slide.subtitle,
        layout=slide.layout,
        order_index=slide.order_index
    )
    db.add(db_slide)
    _bump_presentation_version(db, presentation_id)
    db.commit()
    db.refresh(db_slide)
    
    if slide.data:
        db_data = models.SlideData(slide_id=db_slide.id, payload=slide.data.payload)
        db.add(db_data)
        
    if slide.events:
        for event in slide.events:
            db_event = models.DirectorEvent(
                slide_id=db_slide.id,
                time=event.time,
                action=event.action,
                event_type=event.event_type,
                payload=event.payload
            )
            db.add(db_event)
            
    db.commit()
    db.refresh(db_slide)
    _log_revision(db, presentation_id, [{"op": "add_slide", "slide_id": slide.slide_id,
                                         "component": slide.component}])
    db_slide.warnings = _lint_slide_warnings(
        db, presentation_id, slide.component, slide.data.payload if slide.data else None, slide.title)
    return db_slide

@router.put("/slides/{slide_id}", response_model=schemas.Slide)
def update_slide(slide_id: int, slide: schemas.SlideCreate, db: Session = Depends(get_db)):
    db_slide = db.query(models.Slide).filter(models.Slide.id == slide_id).first()
    if not db_slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    _validate_slide_payload(slide.component, slide.data.payload if slide.data else None, db)
    if db_slide.presentation_id:
        _enforce_preset_lock(db, db_slide.presentation_id, slide.component,
                             slide.data.payload if slide.data else None, slide.title)

    db_slide.slide_id = slide.slide_id
    db_slide.component = slide.component
    db_slide.start_time = slide.start_time
    db_slide.title = slide.title
    db_slide.subtitle = slide.subtitle
    db_slide.layout = slide.layout
    db_slide.order_index = slide.order_index
    
    if db_slide.data:
        db.delete(db_slide.data)
    if slide.data:
        db_data = models.SlideData(slide_id=db_slide.id, payload=slide.data.payload)
        db.add(db_data)
        
    for ev in db_slide.events:
        db.delete(ev)
    if slide.events:
        for event in slide.events:
            db_event = models.DirectorEvent(
                slide_id=db_slide.id,
                time=event.time,
                action=event.action,
                event_type=event.event_type,
                payload=event.payload
            )
            db.add(db_event)

    _bump_presentation_version(db, db_slide.presentation_id)
    db.commit()
    db.refresh(db_slide)
    try:
        pres_id = db_slide.presentation_id
    except Exception:
        pres_id = None
    _log_revision(db, pres_id, [{"op": "update_slide", "slide_id": slide.slide_id,
                                "component": slide.component}])
    db_slide.warnings = _lint_slide_warnings(
        db, pres_id, slide.component, slide.data.payload if slide.data else None, slide.title) if pres_id else []
    return db_slide

@router.delete("/slides/{slide_id}", response_model=dict)
def delete_slide(slide_id: int, db: Session = Depends(get_db)):
    db_slide = db.query(models.Slide).filter(models.Slide.id == slide_id).first()
    if not db_slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    pres_id = db_slide.presentation_id
    slide_key = db_slide.slide_id
    db.delete(db_slide)
    _bump_presentation_version(db, pres_id)
    db.commit()
    _log_revision(db, pres_id, [{"op": "delete_slide", "slide_id": slide_key}])
    return {"status": "success"}

MEDIA_DIR = "/app/backend/media" if os.path.exists("/app") else "backend/media"
os.makedirs(MEDIA_DIR, exist_ok=True)

@router.post("/{presentation_id}/media", response_model=schemas.MediaFile)
def upload_media(presentation_id: int, file: UploadFile = File(...), file_type: str = Form(None), db: Session = Depends(get_db)):
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
        
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(MEDIA_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    _file_type = "other"
    if file_type:
        _file_type = file_type
    elif file.content_type.startswith("image/"):
        _file_type = "image"
    elif file.content_type.startswith("audio/"):
        _file_type = "audio"
    elif file.content_type.startswith("video/"):
        _file_type = "video"
        
    db_media = models.MediaFile(
        presentation_id=presentation_id,
        filename=file.filename,
        file_type=_file_type,
        file_path=f"/media/{unique_filename}"
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

@router.delete("/{presentation_id}/media/{media_id}", response_model=dict)
def delete_media(presentation_id: int, media_id: int, db: Session = Depends(get_db)):
    db_media = db.query(models.MediaFile).filter(models.MediaFile.id == media_id, models.MediaFile.presentation_id == presentation_id).first()
    if not db_media:
        raise HTTPException(status_code=404, detail="Media not found")
        
    db.delete(db_media)
    db.commit()
    
    try:
        if db_media.file_path.startswith('/uploads/'):
            filename = db_media.file_path.split('/uploads/')[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        print("Error deleting physical file:", e)
        
    return {"status": "success"}
import requests
from pydantic import BaseModel
from urllib.parse import urlparse

class UrlDownloadRequest(BaseModel):
    url: str

@router.post("/{presentation_id}/media/url", response_model=schemas.MediaFile)
def download_media_from_url(presentation_id: int, req: UrlDownloadRequest, db: Session = Depends(get_db)):
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
        
    try:
        response = requests.get(req.url, stream=True, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download URL: {str(e)}")
        
    content_type = response.headers.get('content-type', '')
    
    file_type = "other"
    ext = ".bin"
    if content_type.startswith("image/"):
        file_type = "image"
        if "jpeg" in content_type or "jpg" in content_type: ext = ".jpg"
        elif "png" in content_type: ext = ".png"
        elif "webp" in content_type: ext = ".webp"
        elif "gif" in content_type: ext = ".gif"
        elif "svg" in content_type: ext = ".svg"
    elif content_type.startswith("audio/"):
        file_type = "audio"
        ext = ".mp3" # simplified
    elif content_type.startswith("video/"):
        file_type = "video"
        ext = ".mp4" # simplified
    else:
        # Try to guess from url
        path = urlparse(req.url).path
        _, url_ext = os.path.splitext(path)
        if url_ext:
            ext = url_ext
            
    # Fallback for search engines that return images without proper content-type
    if file_type == "other" and req.url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        file_type = "image"
        
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        for chunk in response.iter_content(chunk_size=8192):
            buffer.write(chunk)
            
    # Try to extract a reasonable filename
    original_filename = os.path.basename(urlparse(req.url).path)
    if not original_filename:
        original_filename = f"downloaded_file{ext}"
        
    db_media = models.MediaFile(
        presentation_id=presentation_id,
        filename=original_filename,
        file_type=file_type,
        file_path=f"/uploads/{unique_filename}"
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

@router.get("/{presentation_id}/media/search-sfx")
def search_sfx(presentation_id: int, query: str = "", db: Session = Depends(get_db)):
    db_presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not db_presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
        
    api_key = os.environ.get("FREESOUND_API_KEY")
    if not api_key:
        # Mock response for UI development if no API key is provided
        return {
            "hits": [
                {"id": 1, "name": "Whoosh Transition", "tags": "whoosh, swoosh", "duration": 2, "url": "mock_whoosh", "preview": "https://cdn.freesound.org/previews/415/415209_5121236-hq.mp3"},
                {"id": 2, "name": "Cinematic Hit", "tags": "impact, hit", "duration": 4, "url": "mock_hit", "preview": "https://cdn.freesound.org/previews/415/415209_5121236-hq.mp3"}
            ]
        }
        
    # FreeSound API with Creative Commons 0 (Public Domain) filter for copyright safety
    url = f"https://freesound.org/apiv2/search/text/?query={query}&filter=license:%22Creative+Commons+0%22&fields=id,name,tags,duration,previews&token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        hits = []
        for res in data.get('results', []):
            previews = res.get('previews', {})
            preview_url = previews.get('preview-hq-mp3') or previews.get('preview-lq-mp3')
            if preview_url:
                hits.append({
                    "id": res.get('id'),
                    "name": res.get('name'),
                    "tags": ", ".join(res.get('tags', [])[:3]),
                    "duration": res.get('duration'),
                    "url": preview_url,
                    "preview": preview_url
                })
        return {"hits": hits}
    else:
        raise HTTPException(status_code=500, detail="Failed to fetch from FreeSound")

class SfxDownloadRequest(BaseModel):
    url: str
    name: str

@router.post("/{presentation_id}/media/download-sfx", response_model=schemas.MediaFile)
def download_sfx(presentation_id: int, req: SfxDownloadRequest, db: Session = Depends(get_db)):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
        
    if req.url.startswith("mock_"):
        raise HTTPException(status_code=400, detail="Cannot download mock SFX. Please add FREESOUND_API_KEY to .env")
        
    try:
        response = requests.get(req.url, stream=True, timeout=10)
        response.raise_for_status()
        
        unique_filename = f"sfx_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        db_media = models.MediaFile(
            presentation_id=presentation_id,
            filename=req.name or "Downloaded SFX",
            file_type="sfx",
            file_path=f"/uploads/{unique_filename}"
        )
        db.add(db_media)
        db.commit()
        db.refresh(db_media)
        return db_media
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download SFX: {str(e)}")

@router.put("/folders/{folder_id}", response_model=schemas.Folder)
def update_folder(folder_id: int, folder: schemas.FolderUpdate, db: Session = Depends(get_db)):
    db_folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if folder.title is not None:
        db_folder.title = folder.title
    if folder.desc is not None:
        db_folder.desc = folder.desc
    if folder.theme is not None:
        db_folder.theme = folder.theme
    if folder.icon is not None:
        db_folder.icon = folder.icon
    if folder.is_archived is not None:
        db_folder.is_archived = folder.is_archived

    db.commit()
    db.refresh(db_folder)
    return db_folder

@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    db_folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Soft delete
    db_folder.is_archived = True
    db.commit()
    return {"ok": True}

@router.post("/{presentation_id}/restore")
def restore_presentation(presentation_id: int, db: Session = Depends(get_db)):
    """Восстановить презентацию из архива (снять is_archived)."""
    db_presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not db_presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    db_presentation.is_archived = False
    db.commit()
    return {"ok": True, "id": presentation_id, "is_archived": False}


@router.delete("/{presentation_id}")
def delete_presentation(presentation_id: int, db: Session = Depends(get_db)):
    db_presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not db_presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    # Soft delete
    db_presentation.is_archived = True
    db.commit()
    return {"ok": True}
