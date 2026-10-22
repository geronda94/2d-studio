from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..permissions import enforce_write

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(enforce_write)],
)


def _project_summary(db: Session, project: models.Project) -> Dict[str, Any]:
    """Метаданные проекта + папки с числом презентаций (без слайдов/payload)."""
    from sqlalchemy import func
    fp = models.folder_presentation
    counts = dict(
        db.query(fp.c.folder_id, func.count(fp.c.presentation_id))
        .join(models.Presentation, models.Presentation.id == fp.c.presentation_id)
        .filter(models.Presentation.is_archived.is_(False))
        .group_by(fp.c.folder_id)
        .all()
    )
    folders = [
        {
            "id": f.id, "slug": f.slug, "title": f.title, "desc": f.desc,
            "theme": f.theme, "icon": f.icon, "project_id": f.project_id,
            "is_archived": bool(getattr(f, "is_archived", False)),
            "presentations_count": counts.get(f.id, 0),
        }
        for f in (project.folders or [])
        if not getattr(f, "is_archived", False)
    ]
    return {
        "id": project.id, "slug": project.slug, "title": project.title,
        "description": project.description, "is_template": project.is_template,
        "default_variant": project.default_variant, "palette_source": project.palette_source,
        "owner_id": project.owner_id, "parent_id": project.parent_id,
        "brief": project.brief, "folders": folders,
    }


def _hash_api_key(raw: str) -> str:
    import hashlib
    return hashlib.sha256(raw.encode()).hexdigest()


def _visible_filter(q, user: Optional[models.User]):
    """Видимость проекта: шаблоны — всем; личные — владельцу и участникам;
    системные (owner_id NULL) — всем; супер-админ — все."""
    from ..permissions import AUTH_MODE
    if AUTH_MODE != "on":
        # Dev/локальный запуск без аутентификации — как до AUTH_PLAN: видно всё.
        return q
    if user is not None and getattr(user, "is_superadmin", False):
        return q
    cond = models.Project.is_template.is_(True)
    if user is None:
        cond = cond | models.Project.owner_id.is_(None)
    else:
        from sqlalchemy import select
        member_ids = select(models.ProjectMember.project_id).where(
            models.ProjectMember.user_id == user.id)
        cond = cond | (models.Project.owner_id == user.id) | models.Project.id.in_(member_ids)
    return q.filter(cond)


def _get_visible_project(db: Session, project_id: int, user: Optional[models.User]):
    """Доступ к проекту: супер-админ/владелец/участник — да; шаблон — да; иначе 403."""
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    from ..permissions import AUTH_MODE
    if AUTH_MODE != "on":
        # Dev/локальный запуск без аутентификации — доступ ко всем проектам.
        return proj
    if user is not None and getattr(user, "is_superadmin", False):
        return proj
    if proj.is_template:
        return proj
    from ..permissions import project_role
    if project_role(db, project_id, user) is not None:
        return proj
    raise HTTPException(status_code=403, detail="Project belongs to another owner")


@router.get("/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, include_archived: bool = False,
                  templates_only: bool = False, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    q = _visible_filter(db.query(models.Project), user)
    if templates_only:
        q = q.filter(models.Project.is_template.is_(True))
    if not include_archived:
        q = q.filter(models.Project.is_archived.is_(False))
    return q.offset(skip).limit(limit).all()


def _palettes_query(db: Session, user: Optional[models.User]):
    """Общий запрос витрины палитр (используется полной и summary-ручкой)."""
    from sqlalchemy import or_, select
    conds = [models.Project.is_template.is_(True), models.Project.owner_id.is_(None)]
    if user is not None:
        member_ids = select(models.ProjectMember.project_id).where(
            models.ProjectMember.user_id == user.id)
        conds.append(models.Project.owner_id == user.id)
        conds.append(models.Project.id.in_(member_ids))
    return db.query(models.Project).filter(
        models.Project.is_archived.is_(False), or_(*conds)
    ).order_by(models.Project.is_template.desc(), models.Project.id)


@router.get("/palettes", response_model=List[schemas.Project])
def read_palettes(db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_current_user)):
    """Витрина палитр: системные шаблоны + системные проекты (owner_id IS NULL,
    напр. it2b/history/derevnya) + собственные проекты/участие пользователя.
    Проект-получатель из списка исключает фронт (нельзя применить себя к себе)."""
    return _palettes_query(db, user).all()


@router.get("/palettes/summary", response_model=List[schemas.ProjectSummary])
def read_palettes_summary(db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_current_user)):
    """Лёгкая витрина палитр (без слайдов/payload) — для списковых экранов."""
    return [_project_summary(db, p) for p in _palettes_query(db, user).all()]



@router.get("/summary", response_model=List[schemas.ProjectSummary])
def read_projects_summary(skip: int = 0, limit: int = 100, include_archived: bool = False,
                          templates_only: bool = False, db: Session = Depends(get_db),
                          user: Optional[models.User] = Depends(get_current_user)):
    """Лёгкий список проектов для списочных экранов (без слайдов/payload).
    Отдаёт папки с presentations_count — фронт не тянет мегабайты вложенных данных."""
    q = _visible_filter(db.query(models.Project), user)
    if templates_only:
        q = q.filter(models.Project.is_template.is_(True))
    if not include_archived:
        q = q.filter(models.Project.is_archived.is_(False))
    return [_project_summary(db, p) for p in q.offset(skip).limit(limit).all()]


@router.get("/{project_slug}/summary", response_model=schemas.ProjectSummary)
def read_project_summary(project_slug: str, db: Session = Depends(get_db),
                         user: Optional[models.User] = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.slug == project_slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _get_visible_project(db, project.id, user)
    return _project_summary(db, project)


@router.get("/{project_id}/media", response_model=List[schemas.MediaFile])
def read_project_media(project_id: int, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    _get_visible_project(db, project_id, user)  # AUTH_PLAN Ф4a: не отдавать медиа чужого проекта
    media_files = db.query(models.MediaFile)\
        .join(models.Presentation, models.MediaFile.presentation_id == models.Presentation.id)\
        .join(models.folder_presentation, models.Presentation.id == models.folder_presentation.c.presentation_id)\
        .join(models.Folder, models.folder_presentation.c.folder_id == models.Folder.id)\
        .filter(models.Folder.project_id == project_id)\
        .distinct()\
        .all()
    return media_files

import uuid
import re


_RU_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _slugify(title: str) -> str:
    s = (title or "").lower()
    s = "".join(_RU_MAP.get(ch, ch) for ch in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "project"


@router.post("/", response_model=schemas.Project)
def create_project(req: schemas.ProjectCreateRequest, db: Session = Depends(get_db),
                   user: Optional[models.User] = Depends(get_current_user)):
    """Создание проекта из шаблона палитры (UX-1): полный сет токенов копируется
    в скоуп проекта (самодостаточность — не полагаемся на global-fallback)."""
    if not (req.title or "").strip():
        raise HTTPException(status_code=400, detail="Title is required")
    template_slug = req.template or "it2b"
    template = db.query(models.Project).filter(models.Project.slug == template_slug).first()
    if not template:
        raise HTTPException(status_code=400, detail=f"Template project '{template_slug}' not found")
    _get_visible_project(db, template.id, user)  # нельзя брать чужую приватную палитру по slug

    base = (_slugify(req.slug) if req.slug else _slugify(req.title)) or "project"
    slug, i = base, 2
    while db.query(models.Project).filter(models.Project.slug == slug).first():
        slug = f"{base}-{i}"
        i += 1

    project = models.Project(slug=slug, title=req.title, description=req.description or "",
                             palette_source=template_slug, owner_id=(user.id if user else None),
                             parent_id=template.id)
    db.add(project)
    db.flush()

    folder_slug = f"drafts-{slug}"
    if not db.query(models.Folder).filter(models.Folder.slug == folder_slug).first():
        db.add(models.Folder(slug=folder_slug, title="Черновики", project_id=project.id))

    # Полный сет палитры шаблона (мерж global→template) → свои строки проекта
    merged = _merge_tokens(db, project_id=template.id)
    for key, tok in merged.items():
        value = tok.get("value") if isinstance(tok, dict) else tok
        if value is None:
            continue
        db.add(models.DesignToken(
            project_id=project.id,
            token_key=key,
            token_type=tok.get("type", "color") if isinstance(tok, dict) else "color",
            value=str(value),
            is_custom=False,
        ))
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/brief")
def get_brief(project_id: int, db: Session = Depends(get_db),
              user: Optional[models.User] = Depends(get_current_user)):
    project = _get_visible_project(db, project_id, user)
    return {"brief": getattr(project, "brief", None)}


@router.put("/{project_id}/brief")
def put_brief(project_id: int, req: schemas.ProjectBrief, db: Session = Depends(get_db),
              user: Optional[models.User] = Depends(get_current_user)):
    """Бриф проекта (знание для агента): о чём, аудитория, tone, must/forbidden, voice."""
    project = _get_visible_project(db, project_id, user)
    from sqlalchemy.orm.attributes import flag_modified
    project.brief = req.dict(exclude_unset=True)
    flag_modified(project, "brief")
    db.commit()
    return {"brief": project.brief}


# Серверный кэш QR: data -> svg (перегенерация дорогая, а контент меняется редко)
_QR_CACHE: dict = {}
_QR_CACHE_MAX = 128


@router.get("/{project_id}/qr.svg")
def project_qr_svg(project_id: int, db: Session = Depends(get_db)):
    """Авто-QR проекта (BRAND KIT): SVG из brand.qr_data → contacts.telegram (t.me) → contacts.site.
    Публичный (QR кодирует и так публичные контакты), кэшируется в памяти и на клиенте."""
    from fastapi.responses import Response
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    cfg = getattr(project, "config", None) or {}
    data = str(cfg.get("brand", {}).get("qr_data") or "").strip()
    if not data:
        tg = str(cfg.get("contacts", {}).get("telegram") or "").strip()
        if tg:
            data = "https://t.me/" + tg.lstrip("@")
    if not data:
        data = str(cfg.get("contacts", {}).get("site") or "").strip()
    if not data:
        raise HTTPException(status_code=404, detail="QR data not configured for project")
    if len(data) > 1024:
        raise HTTPException(status_code=400, detail="QR data too long")
    svg = _QR_CACHE.get(data)
    if svg is None:
        try:
            import io
            import segno
            qr = segno.make(data, error="m")
            buf = io.BytesIO()
            qr.save(buf, kind="svg", scale=6, border=2, dark="#111111", light="#ffffff")
            svg = buf.getvalue()
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"QR generation failed: {e}")
        if len(_QR_CACHE) >= _QR_CACHE_MAX:
            _QR_CACHE.clear()
        _QR_CACHE[data] = svg
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/{project_id}/config")
def get_project_config(project_id: int, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    """Конфиг проекта (BRAND KIT): brand-ассеты, контакты, дефолты компонентов."""
    project = _get_visible_project(db, project_id, user)
    return {"config": getattr(project, "config", None) or {}}


@router.put("/{project_id}/config")
def put_project_config(project_id: int, body: Dict[str, Any], db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    """Секционный MERGE конфига (brand/contacts/defaults/voice/audio): присланные
    секции заменяются целиком, остальные сохраняются. Мутации /projects/* — только owner."""
    from ..brand_config import merge_config
    project = _get_visible_project(db, project_id, user)
    old = getattr(project, "config", None) or {}
    try:
        merged = merge_config(old, body)
    except ValueError as e:
        code = 413 if "большой" in str(e) else 400
        raise HTTPException(status_code=code, detail=str(e))
    from sqlalchemy.orm.attributes import flag_modified
    project.config = merged
    flag_modified(project, "config")
    db.commit()
    return {"config": project.config}


@router.post("/{project_id}/fork", response_model=schemas.Project)
def fork_project(project_id: int, req: schemas.ProjectForkRequest, db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    """Форк темы: личная копия проекта-источника (owner_id=текущий, parent_id=источник).
    Системный шаблон при этом НЕ меняется. Кастомы источника копируются как managed-снимок."""
    source = _get_visible_project(db, project_id, user)
    base = _slugify(req.title or f"{source.title} (моя)")
    slug, i = base, 2
    while db.query(models.Project).filter(models.Project.slug == slug).first():
        slug = f"{base}-{i}"
        i += 1
    fork = models.Project(
        slug=slug,
        title=req.title or f"{source.title} (моя)",
        description=f"Личная тема на основе «{source.title}»",
        is_template=False,
        owner_id=(user.id if user else None),
        parent_id=source.id,
        palette_source=source.slug,
        default_variant=getattr(source, "default_variant", None),
    )
    db.add(fork)
    db.flush()
    # Копия палитры источника (replace-снимок; кастомы уже влиты в набор)
    merged = _merge_tokens(db, project_id=source.id)
    for key, tok in merged.items():
        value = tok.get("value") if isinstance(tok, dict) else tok
        if value is None:
            continue
        db.add(models.DesignToken(
            project_id=fork.id, token_key=key,
            token_type=tok.get("type", "color") if isinstance(tok, dict) else "color",
            value=str(value), is_custom=False))
    db.add(models.Folder(slug=f"drafts-{slug}", title="Черновики", project_id=fork.id))
    db.commit()
    db.refresh(fork)
    return fork


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, req: schemas.ProjectUpdate, db: Session = Depends(get_db),
                   user: Optional[models.User] = Depends(get_current_user)):
    """Настройки проекта (UX-4): название/описание/дефолтный вариант (400 на битый вариант)."""
    project = _get_visible_project(db, project_id, user)
    data = req.dict(exclude_unset=True)
    if "default_variant" in data and data["default_variant"]:
        var = db.query(models.StyleVariant).filter(
            models.StyleVariant.slug == data["default_variant"]).first()
        if not var:
            raise HTTPException(status_code=400, detail=f"Variant '{data['default_variant']}' not found")
    for key in ("title", "description", "default_variant"):
        if key in data:
            setattr(project, key, data[key])
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=dict)
def delete_project(project_id: int, db: Session = Depends(get_db),
                   user: Optional[models.User] = Depends(get_current_user)):
    """Мягкое удаление проекта (архив, STUDIO). Шаблоны витрины удалять запрещено."""
    project = _get_visible_project(db, project_id, user)
    if getattr(project, "is_template", False):
        raise HTTPException(status_code=403, detail="Template projects cannot be deleted")
    project.is_archived = True
    db.commit()
    return {"status": "archived"}


@router.get("/{project_slug}", response_model=schemas.Project)
def read_project(project_slug: str, db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.slug == project_slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _get_visible_project(db, project.id, user)  # 403 если чужой личный

    # Filter out archived folders and archived presentations
    active_folders = []
    for f in project.folders:
        if not getattr(f, 'is_archived', False):
            f.presentations = [p for p in f.presentations if not getattr(p, 'is_archived', False)]
            active_folders.append(f)
            
    project.folders = active_folders
    # Приватные презентации не отдаём тем, у кого нет доступа (иначе visibility
    # обходилась бы через карточку проекта).
    from ..permissions import can_view_presentation
    for f in project.folders:
        f.presentations = [p for p in f.presentations if can_view_presentation(db, p, user)]
    return project

@router.get("/{project_id}/folders")
def list_project_folders(project_id: int, db: Session = Depends(get_db),
                         user: Optional[models.User] = Depends(get_current_user)):
    """Список активных папок проекта — для выбора scope при выдаче прав (Ф4b)."""
    project = _get_visible_project(db, project_id, user)
    from ..permissions import project_role, rank as _rank
    if not (user is not None and getattr(user, "is_superadmin", False)):
        if _rank(project_role(db, project_id, user)) < _rank("viewer"):
            raise HTTPException(status_code=403, detail="Нет доступа к папкам проекта")
    return [
        {"id": f.id, "title": f.title, "slug": f.slug}
        for f in project.folders if not getattr(f, "is_archived", False)
    ]


@router.post("/{project_id}/folders", response_model=schemas.Folder)
def create_folder(project_id: int, folder: schemas.FolderCreate, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    db_project = _get_visible_project(db, project_id, user)

    slug = folder.slug
    if not slug:
        slug = str(uuid.uuid4())[:8]

    db_folder = models.Folder(
        title=folder.title,
        slug=slug,
        desc=folder.desc or "",
        theme=folder.theme or "blue",
        icon=folder.icon or "folder",
        project_id=project_id,
        is_archived=False
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder


# ── Дизайн-токены (Фаза 2) ────────────────────────────────────────────────

def _infer_token_type(key: str) -> str:
    if key == "font_link":
        return "font_link"
    if key.startswith("font-"):
        return "font_family"
    if key.startswith("gradient") or "gradient" in key:
        return "gradient"
    if key.startswith("glow") or key.startswith("pattern"):
        return "effect"
    if key.startswith("shadow") or "shadow" in key:
        return "shadow"
    if key.startswith("radius") or "radius" in key:
        return "radius"
    return "color"


def _merge_tokens(db: Session, project_id: int = None, presentation_id: int = None, slide_id: int = None) -> Dict[str, Dict[str, Any]]:
    """Возвращает токены, слитые по иерархии: global → project → presentation → slide."""
    merged: Dict[str, Dict[str, Any]] = {}

    def apply(tokens):
        for t in tokens:
            if t.is_archived:
                continue
            merged[t.token_key] = {"key": t.token_key, "type": t.token_type, "value": t.value,
                                   "custom": bool(getattr(t, "is_custom", False))}

    # global (все уровни NULL)
    apply(db.query(models.DesignToken).filter(
        models.DesignToken.project_id.is_(None),
        models.DesignToken.presentation_id.is_(None),
        models.DesignToken.slide_id.is_(None),
    ).all())
    # project
    if project_id is not None:
        apply(db.query(models.DesignToken).filter(
            models.DesignToken.project_id == project_id,
            models.DesignToken.presentation_id.is_(None),
            models.DesignToken.slide_id.is_(None),
        ).all())
    # presentation
    if presentation_id is not None:
        apply(db.query(models.DesignToken).filter(
            models.DesignToken.presentation_id == presentation_id,
            models.DesignToken.slide_id.is_(None),
        ).all())
    # slide
    if slide_id is not None:
        apply(db.query(models.DesignToken).filter(
            models.DesignToken.slide_id == slide_id,
        ).all())
    return merged


@router.get("/{project_id}/tokens")
def get_project_tokens(project_id: int, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    _get_visible_project(db, project_id, user)
    tokens = _merge_tokens(db, project_id=project_id)
    return {"tokens": tokens}


@router.put("/{project_id}/tokens")
def upsert_project_tokens(project_id: int, req: schemas.DesignTokensUpsert, db: Session = Depends(get_db),
                          user: Optional[models.User] = Depends(get_current_user)):
    _get_visible_project(db, project_id, user)

    for key, value in req.tokens.items():
        if value is None:
            continue
        token = db.query(models.DesignToken).filter(
            models.DesignToken.project_id == project_id,
            models.DesignToken.presentation_id.is_(None),
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.token_key == key,
        ).first()
        if token:
            token.value = str(value)
        else:
            db.add(models.DesignToken(
                project_id=project_id,
                token_key=key,
                token_type=_infer_token_type(key),
                value=str(value),
                is_custom=True,  # создан через API/библиотеку — можно удалять
            ))
    db.commit()
    return {"tokens": _merge_tokens(db, project_id=project_id)}


@router.get("/{project_id}/tokens/coverage")
def token_coverage(project_id: int, db: Session = Depends(get_db),
                   user: Optional[models.User] = Depends(get_current_user)):
    """Полнота переменных (UX-3): сверка ключей проекта с каноном GLOBAL_TOKENS.
    missing = ключи канона без значения (мерж молча подтянет global — тема «плывёт»);
    extra = ключи проекта вне канона (кастомы — информативно, не ошибка)."""
    from scripts.seed_tokens import GLOBAL_TOKENS
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    _get_visible_project(db, project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    own = {t.token_key for t in db.query(models.DesignToken).filter(
        models.DesignToken.project_id == project_id,
        models.DesignToken.presentation_id.is_(None),
        models.DesignToken.slide_id.is_(None)).all()}
    canonical = [k for k in GLOBAL_TOKENS.keys() if k != "font_link"]
    missing = [k for k in canonical if k not in own]
    extra = sorted(k for k in own if k not in GLOBAL_TOKENS)
    return {"total": len(canonical), "covered": len(canonical) - len(missing),
            "missing": missing, "extra": extra}


@router.post("/{project_id}/tokens/repair")
def repair_tokens(project_id: int, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    """Дотянуть недостающие ключи из global-значений (UX-3). Только добавляет,
    ничего не затирает; новые строки — managed (сид владеет)."""
    from scripts.seed_tokens import GLOBAL_TOKENS
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    _get_visible_project(db, project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    own = {t.token_key for t in db.query(models.DesignToken).filter(
        models.DesignToken.project_id == project_id,
        models.DesignToken.presentation_id.is_(None),
        models.DesignToken.slide_id.is_(None)).all()}
    added = []
    for key in GLOBAL_TOKENS:
        if key == "font_link" or key in own:
            continue
        db.add(models.DesignToken(
            project_id=project_id,
            token_key=key,
            token_type=_infer_token_type(key),
            value=str(GLOBAL_TOKENS[key]),
            is_custom=False,
        ))
        added.append(key)
    db.commit()
    return {"added": added, "tokens": _merge_tokens(db, project_id=project_id)}


@router.post("/{project_id}/apply-variant")
def apply_variant_to_presentations(project_id: int, req: schemas.ProjectVariantApply,
                                    db: Session = Depends(get_db),
                                    user: Optional[models.User] = Depends(get_current_user)):
    """Применить вариант ко всем презентациям проекта (STUDIO): ставит presentation.variant.
    Слайды с явным payload.variant не трогаем (per-slide override сильнее)."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    _get_visible_project(db, project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.variant:
        var = db.query(models.StyleVariant).filter(
            models.StyleVariant.slug == req.variant).first()
        if not var:
            raise HTTPException(status_code=400, detail=f"Variant '{req.variant}' not found")
    ids = set()
    for folder in (project.folders or []):
        for pres in (folder.presentations or []):
            if not getattr(pres, "is_archived", False):
                ids.add(pres.id)
    n = 0
    for pid in ids:
        pres = db.query(models.Presentation).filter(models.Presentation.id == pid).first()
        if pres and pres.variant != req.variant:
            pres.variant = req.variant
            n += 1
    db.commit()
    return {"updated": n, "total": len(ids), "variant": req.variant}


@router.delete("/{project_id}/tokens/{key}")
def delete_project_token(project_id: int, key: str, db: Session = Depends(get_db),
                         user: Optional[models.User] = Depends(get_current_user)):
    """Удаление токена — только custom (созданные через библиотеку). Дефолты сидов удалять запрещено."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    _get_visible_project(db, project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    token = db.query(models.DesignToken).filter(
        models.DesignToken.project_id == project_id,
        models.DesignToken.presentation_id.is_(None),
        models.DesignToken.slide_id.is_(None),
        models.DesignToken.token_key == key,
    ).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if not getattr(token, "is_custom", False):
        raise HTTPException(status_code=403, detail="Default tokens cannot be deleted")
    db.delete(token)
    db.commit()
    return {"tokens": _merge_tokens(db, project_id=project_id)}


@router.post("/{project_id}/palette/copy")
def copy_palette(project_id: int, req: schemas.PaletteCopyRequest, db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    """«Взять себе» из библиотеки (UX-2): полный сет палитры источника в скоуп проекта.
    Перезаписывает managed-значения, кастомы проекта не трогает никогда."""
    project = _get_visible_project(db, project_id, user)
    # Источник: сам slug, иначе legacy-вариант 'template-<slug>'.
    # Берём первый, который существует И видим пользователю (шаблон/владение/участие),
    # чтобы старые palette_source ('history') работали и для не-админов.
    candidates = [str(req.from_project)]
    if not str(req.from_project).startswith("template-"):
        candidates.append(f"template-{req.from_project}")
    source = None
    for slug in candidates:
        cand = db.query(models.Project).filter(models.Project.slug == slug).first()
        if not cand:
            continue
        try:
            _get_visible_project(db, cand.id, user)
            source = cand
            break
        except HTTPException:
            continue
    if not source:
        raise HTTPException(status_code=400, detail=f"Source project '{req.from_project}' not found")
    if source.id == project.id:
        raise HTTPException(status_code=400, detail="Source and target are the same project")
    merged = _merge_tokens(db, project_id=source.id)
    source_keys = set(merged.keys())
    copied, skipped = 0, 0
    for key, tok in merged.items():
        value = tok.get("value") if isinstance(tok, dict) else tok
        if value is None:
            continue
        existing = db.query(models.DesignToken).filter(
            models.DesignToken.project_id == project_id,
            models.DesignToken.presentation_id.is_(None),
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.token_key == key,
        ).first()
        if existing:
            if getattr(existing, "is_custom", False):
                skipped += 1
                continue
            existing.value = str(value)
            copied += 1
        else:
            db.add(models.DesignToken(
                project_id=project_id,
                token_key=key,
                token_type=tok.get("type", "color") if isinstance(tok, dict) else "color",
                value=str(value),
                is_custom=False,
            ))
            copied += 1
    # REPLACE-семантика: managed-токены, которых нет в палитре-источнике, удаляем —
    # иначе при смене палитры «застревают» иллюстрации/градиенты прошлой темы (лес у tech).
    removed = 0
    for t in db.query(models.DesignToken).filter(
            models.DesignToken.project_id == project_id,
            models.DesignToken.presentation_id.is_(None),
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.is_custom.is_(False)).all():
        if t.token_key not in source_keys:
            db.delete(t)
            removed += 1
    project.palette_source = source.slug
    db.commit()
    # Структурные ключи сцены (не цвета): фон/лес/шум/оверлеи — копируются вместе с
    # палитрой, т.к. без них тема выглядит сломанной. Фронт показывает их отдельно.
    from scripts.seed_tokens import GLOBAL_TOKENS as _CANON
    structural = sorted(k for k, tok in merged.items()
                        if k not in _CANON and (tok.get("value") if isinstance(tok, dict) else tok))
    return {"copied": copied, "removed": removed, "skipped_custom": skipped, "structural": structural,
            "tokens": _merge_tokens(db, project_id=project_id)}


# ---------------------------------------------------------------------------
# Участники проекта (AUTH_PLAN Ф2). Владелец — projects.owner_id,
# project_members — помощники (editor правит контент, viewer только смотрит).
# Мутации под /projects/ уже требуют роль owner (permissions.enforce_write).
# ---------------------------------------------------------------------------

from pydantic import BaseModel as _BaseModel


class MemberIn(_BaseModel):
    email: str
    role: str = "editor"  # editor | viewer
    scope_folder_id: Optional[int] = None  # NULL = весь проект (AUTH_PLAN Ф4b)


class MemberRoleIn(_BaseModel):
    role: str
    scope_folder_id: Optional[int] = None


class TransferIn(_BaseModel):
    email: str


def _norm_role(role: str) -> str:
    r = (role or "").strip().lower()
    if r not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="role должен быть editor или viewer")
    return r


def _find_user_by_email(db: Session, email: str) -> models.User:
    u = db.query(models.User).filter(models.User.email == (email or "").strip().lower()).first()
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")
    return u


@router.get("/{project_id}/members")
def list_members(project_id: int, db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    project = _get_visible_project(db, project_id, user)
    # email участников — не публичные данные: только владелец/участник/админ
    from ..permissions import project_role, rank as _rank
    if not (user is not None and getattr(user, "is_superadmin", False)):
        if _rank(project_role(db, project_id, user)) < _rank("viewer"):
            raise HTTPException(status_code=403, detail="Нет доступа к команде проекта")
    out = []
    for m in db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == project_id).all():
        u = db.query(models.User).filter(models.User.id == m.user_id).first()
        out.append({
            "user_id": m.user_id,
            "email": u.email if u else None,
            "display_name": u.display_name if u else None,
            "role": m.role,
            "scope_folder_id": m.scope_folder_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    owner = None
    if project.owner_id:
        ou = db.query(models.User).filter(models.User.id == project.owner_id).first()
        if ou:
            owner = {"user_id": ou.id, "email": ou.email, "display_name": ou.display_name}
    return {"owner": owner, "members": out}


@router.post("/{project_id}/members")
def add_member(project_id: int, body: MemberIn, db: Session = Depends(get_db),
               user: Optional[models.User] = Depends(get_current_user)):
    project = _get_visible_project(db, project_id, user)
    role = _norm_role(body.role)
    target = _find_user_by_email(db, body.email)
    if target.id == project.owner_id:
        raise HTTPException(status_code=400, detail="Это владелец проекта")
    existing = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == target.id).first()
    scope = body.scope_folder_id
    if scope is not None:
        f = db.query(models.Folder).filter(models.Folder.id == scope,
                                           models.Folder.project_id == project_id).first()
        if not f:
            raise HTTPException(status_code=400, detail="Папка не принадлежит проекту")
    if existing:
        existing.role = role
        existing.scope_folder_id = scope
        db.commit()
        return {"user_id": target.id, "email": target.email, "role": role, "scope_folder_id": scope}
    m = models.ProjectMember(project_id=project_id, user_id=target.id, role=role,
                             scope_folder_id=scope, invited_by=user.id if user else None)
    db.add(m)
    db.commit()
    return {"user_id": target.id, "email": target.email, "role": role, "scope_folder_id": scope}


@router.put("/{project_id}/members/{member_user_id}")
def update_member(project_id: int, member_user_id: int, body: MemberRoleIn,
                  db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    _get_visible_project(db, project_id, user)
    role = _norm_role(body.role)
    scope = body.scope_folder_id
    if scope is not None:
        f = db.query(models.Folder).filter(models.Folder.id == scope,
                                           models.Folder.project_id == project_id).first()
        if not f:
            raise HTTPException(status_code=400, detail="Папка не принадлежит проекту")
    m = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == member_user_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Участник не найден")
    m.role = role
    m.scope_folder_id = scope
    db.commit()
    return {"user_id": member_user_id, "role": role, "scope_folder_id": scope}


@router.delete("/{project_id}/members/{member_user_id}")
def remove_member(project_id: int, member_user_id: int, db: Session = Depends(get_db),
                  user: Optional[models.User] = Depends(get_current_user)):
    _get_visible_project(db, project_id, user)
    m = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == member_user_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Участник не найден")
    db.delete(m)
    db.commit()
    return {"status": "removed"}


@router.post("/{project_id}/transfer")
def transfer_ownership(project_id: int, body: TransferIn, db: Session = Depends(get_db),
                       user: Optional[models.User] = Depends(get_current_user)):
    project = _get_visible_project(db, project_id, user)
    if project.owner_id != (user.id if user else None) and not (
            user is not None and user.is_superadmin):
        raise HTTPException(status_code=403, detail="Только владелец может передать проект")
    target = _find_user_by_email(db, body.email)
    prev_owner_id = project.owner_id
    # указанный участник становится владельцем (его member-запись больше не нужна)
    db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == target.id).delete()
    # Прежний владелец НЕ теряет доступ — остаётся редактором проекта
    # (иначе передача владения молча отбирала бы у него доступ целиком).
    if prev_owner_id and prev_owner_id != target.id:
        ex = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == prev_owner_id).first()
        if ex:
            ex.role = "editor"
        else:
            db.add(models.ProjectMember(project_id=project_id, user_id=prev_owner_id,
                                        role="editor", invited_by=user.id if user else None))
    project.owner_id = target.id
    db.commit()
    return {"owner": {"user_id": target.id, "email": target.email},
            "previous_owner": {"user_id": prev_owner_id, "role": "editor"}}
