"""Права доступа к проектам/презентациям (AUTH_PLAN Ф2).

Резолв роли: супер-админ → 'owner' везде; владелец проекта (projects.owner_id) →
'owner'; участник из project_members → 'editor'|'viewer'. Шаблоны/системные проекты
(owner_id NULL) правят только супер-админы.

`enforce_write` вешается на роутеры как dependency: срабатывает только при
AUTH_MODE=on и только на мутирующих методах. Внутренние вызовы с loopback
(render-скрипт) пропускаются.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

import hmac
import uuid

from . import audit, models
from .auth import _hash_token, _session_from_request, get_current_user, require_user
from .database import get_db

AUTH_MODE = os.environ.get("AUTH_MODE", "off").lower()

ROLE_RANK = {"viewer": 1, "editor": 2, "owner": 3}
_SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
# Доверенный внутренний вызов (render-воркер) идентифицируется общим секретом,
# НЕ IP-адресом: иначе за реверс-прокси на том же хосте (или при client=None)
# авторизацию можно было обойти целиком.
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")


def rank(role: Optional[str]) -> int:
    return ROLE_RANK.get(role or "", 0)


def project_role(db: Session, project_id: int, user: Optional[models.User]) -> Optional[str]:
    if user is None or project_id is None:
        return None
    if user.is_superadmin:
        return "owner"
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        return None
    if proj.owner_id == user.id:
        return "owner"
    m = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user.id,
    ).first()
    return m.role if m else None


def presentation_project_ids(db: Session, presentation_id: int) -> list:
    rows = (
        db.query(models.Folder.project_id)
        .join(models.folder_presentation,
              models.folder_presentation.c.folder_id == models.Folder.id)
        .filter(models.folder_presentation.c.presentation_id == presentation_id)
        .all()
    )
    return [r[0] for r in rows if r[0] is not None]


def presentation_folders(db: Session, presentation_id: int) -> list:
    """[(folder_id, project_id)] — все папки, в которых лежит презентация."""
    rows = (
        db.query(models.Folder.id, models.Folder.project_id)
        .join(models.folder_presentation,
              models.folder_presentation.c.folder_id == models.Folder.id)
        .filter(models.folder_presentation.c.presentation_id == presentation_id)
        .all()
    )
    return [(r[0], r[1]) for r in rows]


def presentation_role(db: Session, presentation_id: int,
                      user: Optional[models.User]) -> Optional[str]:
    """Роль с учётом папочного скоупа (AUTH_PLAN Ф4b).

    Владелец проекта/супер-админ → owner. Участник даёт свою роль только если
    его `scope_folder_id` = NULL (весь проект) либо входит в папки этой презентации."""
    if user is None or presentation_id is None:
        return None
    if user.is_superadmin:
        return "owner"
    folders = presentation_folders(db, presentation_id)
    if not folders:
        # презентация без папок — проект не определить; владение только по owner_id
        return None
    folder_ids = {fid for fid, _ in folders}
    best = None
    for fid, pid in folders:
        if pid is None:
            continue
        proj = db.query(models.Project).filter(models.Project.id == pid).first()
        if proj and proj.owner_id == user.id:
            return "owner"
        m = db.query(models.ProjectMember).filter(
            models.ProjectMember.project_id == pid,
            models.ProjectMember.user_id == user.id,
        ).first()
        if not m:
            continue
        if m.scope_folder_id is None or m.scope_folder_id in folder_ids:
            if rank(m.role) > rank(best):
                best = m.role
    return best


def can_view_presentation(db: Session, pres, user: Optional[models.User]) -> bool:
    """Публичные (visibility != 'private') видны всем; приватные — owner/editor/viewer.
    Несуществующая/скрытая → False (наружу отдаём 404, не палим существование)."""
    if pres is None:
        return False
    if (getattr(pres, "visibility", None) or "public") != "private":
        return True
    return rank(presentation_role(db, pres.id, user)) >= rank("viewer")


def require_view_presentation(presentation_id: int, db: Session = Depends(get_db),
                              user: Optional[models.User] = Depends(get_current_user)):
    """Dependency для публичных GET: 404, если презентация приватная и нет доступа."""
    pres = db.query(models.Presentation).filter(
        models.Presentation.id == presentation_id).first()
    if not can_view_presentation(db, pres, user):
        raise HTTPException(status_code=404, detail="Presentation not found")
    return pres


def slide_presentation_id(db: Session, slide_pk: int) -> Optional[int]:
    s = db.query(models.Slide).filter(models.Slide.id == slide_pk).first()
    return s.presentation_id if s else None


def slide_role(db: Session, slide_pk: int, user: Optional[models.User]) -> Optional[str]:
    return presentation_role(db, slide_presentation_id(db, slide_pk), user)


def folder_project_id(db: Session, folder_id: int) -> Optional[int]:
    f = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
    return f.project_id if f else None


def folder_role(db: Session, folder_id: int, user: Optional[models.User]) -> Optional[str]:
    return project_role(db, folder_project_id(db, folder_id), user)


# ---------------------------------------------------------------- dependencies

def require_superadmin(user: models.User = Depends(require_user)) -> models.User:
    if not getattr(user, "is_superadmin", False):
        raise HTTPException(status_code=403, detail="Только администратор")
    return user


def require_project_role(min_role: str = "owner"):
    def dep(project_id: int, db: Session = Depends(get_db),
            user: Optional[models.User] = Depends(get_current_user)):
        role = project_role(db, project_id, user)
        if rank(role) < rank(min_role):
            raise HTTPException(status_code=403, detail="Недостаточно прав на проект")
        return role
    return dep


def require_presentation_role(min_role: str = "editor"):
    def dep(presentation_id: int, db: Session = Depends(get_db),
            user: Optional[models.User] = Depends(get_current_user)):
        role = presentation_role(db, presentation_id, user)
        if rank(role) < rank(min_role):
            raise HTTPException(status_code=403, detail="Недостаточно прав на презентацию")
        return role
    return dep


# ------------------------------------------------------ router-level enforcement

def _is_internal(request: Request) -> bool:
    """Внутренний вызов render-воркера: заголовок X-Internal-Token = env INTERNAL_API_TOKEN.
    Без заданного токена внутренний обход выключен (fail-closed)."""
    if not INTERNAL_API_TOKEN:
        return False
    supplied = request.headers.get("x-internal-token") or ""
    return bool(supplied) and hmac.compare_digest(supplied, INTERNAL_API_TOKEN)


def _presentation_id_from_body(request: Request, body: bytes) -> Optional[int]:
    try:
        import json
        data = json.loads(body or b"{}")
        pid = data.get("presentation_id")
        return int(pid) if pid is not None else None
    except Exception:
        return None


def _int_or_none(v):
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


AI_RUNS_REQUIRED = os.environ.get("AI_RUNS_REQUIRED", "false").lower() == "true"
AUDIT_LOG_READS = os.environ.get("AUDIT_LOG_READS", "false").lower() == "true"
_READ_AUDIT_PREFIXES = ("/presentations", "/projects", "/admin", "/audit", "/api-keys")


def _log_read(request: Request, db: Session) -> None:
    """Аудит чувствительных чтений (за флагом). Пишется отдельной сессией — у GET нет коммита."""
    try:
        key = resolve_api_key(db, request)
        user = get_current_user(request, db)
        pp = request.path_params or {}
        path = request.url.path
        audit.write_row({
            "request_id": request.headers.get("x-request-id") or uuid.uuid4().hex,
            "actor_type": "service" if (key is not None and getattr(key, "kind", "personal") == "service")
            else ("user" if user else "system"),
            "actor_user_id": getattr(user, "id", None),
            "actor_key_id": getattr(key, "id", None),
            "effective_user_id": getattr(user, "id", None),
            "action": f"read.{path.strip('/').split('/')[0]}",
            "method": request.method, "path": path, "status": 200, "decision": "allow",
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "project_id": _int_or_none(pp.get("project_id") or pp.get("id")),
            "presentation_id": _int_or_none(pp.get("presentation_id")),
        })
    except Exception:
        pass
_RATE: dict = {}


def _rate_ok(key) -> bool:
    """Простейший лимит на ключ (in-memory; при нескольких воркерах — заменить на Redis)."""
    limit = getattr(key, "rate_limit", None)
    if not limit:
        return True
    import time
    now = time.time()
    bucket = _RATE.setdefault(key.id, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= int(limit):
        return False
    bucket.append(now)
    return True


def _target_project_ids(db: Session, pp: dict) -> list:
    pid = pp.get("project_id") or pp.get("id")
    if pid is not None:
        return [int(pid)]
    pres = pp.get("presentation_id")
    if pres is not None:
        return presentation_project_ids(db, int(pres))
    return []


def idempotency_guard(request: Request, db: Session = Depends(get_db)):
    """Дубликат мутации с тем же Idempotency-Key → 409. Ключ пишется в транзакцию
    эндпоинта (flush здесь): при успехе коммитится, при откате — исчезает."""
    key = request.headers.get("idempotency-key")
    if not key or request.method in _SAFE_METHODS:
        return
    from sqlalchemy.exc import IntegrityError
    user = get_current_user(request, db)
    db.add(models.IdempotencyKey(key=key[:128], actor_user_id=getattr(user, "id", None)))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate_request")


def is_dev_full_access() -> bool:
    """Dev/локальный режим: авторизация выключена — доступ как до AUTH_PLAN."""
    return AUTH_MODE != "on"


def resolve_api_key(db: Session, request: Request):
    authz = request.headers.get("authorization")
    if not (authz and authz.lower().startswith("bearer ")):
        return None
    raw = authz.split(" ", 1)[1].strip()
    return db.query(models.ApiKey).filter(
        models.ApiKey.key_hash == _hash_token(raw),
        models.ApiKey.is_active.is_(True)).first()


def resolve_effective_user(db: Session, request: Request, key, user):
    """Кто «эффективно» действует: для service-ключа с consent — subject, иначе сам user.
    Возвращает (effective, on_behalf_id, actor_type, error_reason|None, deleg_project_id|None)."""
    if key is not None and getattr(key, "kind", "personal") == "service":
        actor_type = "service"
    elif user is not None:
        actor_type = "user"
    else:
        actor_type = "system"
    effective, on_behalf, deleg_project = user, None, None
    if actor_type == "service":
        hdr = request.headers.get("x-on-behalf-of")
        if hdr:
            if not getattr(key, "can_delegate", False):
                return user, None, actor_type, "delegation_not_allowed", None
            if hdr.strip().isdigit():
                subj = db.query(models.User).filter(models.User.id == int(hdr)).first()
            else:
                subj = db.query(models.User).filter(
                    models.User.email == hdr.strip().lower()).first()
            if not subj or not subj.is_active:
                return user, None, actor_type, "delegation_subject_invalid", None
            deleg = db.query(models.BotDelegation).filter(
                models.BotDelegation.bot_user_id == getattr(key, "owner_id", None),
                models.BotDelegation.subject_user_id == subj.id,
                models.BotDelegation.approved_at.isnot(None),
                models.BotDelegation.revoked_at.is_(None)).first()
            if not deleg:
                return user, None, actor_type, "delegation_not_approved", None
            effective, on_behalf = subj, subj.id
            deleg_project = deleg.project_id
    return effective, on_behalf, actor_type, None, deleg_project


async def enforce_write(request: Request, db: Session = Depends(get_db)):
    """Единый шлюз мутаций при AUTH_MODE=on + аудит (ENTERPRISE Ф1/Ф3).

    Публичны: GET/HEAD/OPTIONS, /auth/*, статика, внутренний токен. Остальное требует
    аутентификации; каталог/админка — супер-админ; /projects — владелец; /presentations —
    editor (стиль/токены/палитра — owner); /ai, /renders — editor презентации.
    Боты (service-ключи) действуют от имени subject (consent), права проверяются у subject,
    боту запрещены owner-операции. Allow пишется транзакционно, deny — немедленно.
    """
    if AUTH_MODE != "on":
        return
    path = request.url.path
    if request.method in _SAFE_METHODS:
        if AUDIT_LOG_READS and path.startswith(_READ_AUDIT_PREFIXES):
            _log_read(request, db)
        return
    if path.startswith(("/auth/", "/media/", "/uploads/")):
        return
    if _is_internal(request):
        return

    pp = request.path_params or {}
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex

    def make_ctx(user, key, effective=None, on_behalf=None, ai_run=None, **extra):
        if key is not None and getattr(key, "kind", "personal") == "service":
            atype = "service"
        elif user is not None:
            atype = "user"
        else:
            atype = "system"
        eff = effective if effective is not None else user
        ctx = {
            "request_id": request_id,
            "actor_type": atype,
            "actor_user_id": getattr(user, "id", None),
            "actor_key_id": getattr(key, "id", None),
            "effective_user_id": getattr(eff, "id", None),
            "on_behalf_of_user_id": on_behalf,
            "action": audit.derive_action(request.method, path),
            "method": request.method, "path": path,
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "project_id": _int_or_none(pp.get("project_id") or pp.get("id")),
            "presentation_id": _int_or_none(pp.get("presentation_id")),
            "slide_id": str(pp.get("slide_id")) if pp.get("slide_id") is not None else None,
            "ai_run_id": ai_run or request.headers.get("x-ai-run-id"),
        }
        ctx.update(extra)
        return ctx

    def deny(user, key, code, reason, effective=None, on_behalf=None, ai_run=None, **extra):
        audit.log_deny(make_ctx(user, key, effective=effective, on_behalf=on_behalf,
                                ai_run=ai_run, decision="deny", status=code,
                                deny_reason=reason, **extra))
        raise HTTPException(status_code=code, detail=reason)

    def allow(user, key, effective=None, on_behalf=None, ai_run=None, **extra):
        audit.set_context(db, make_ctx(user, key, effective=effective, on_behalf=on_behalf,
                                       ai_run=ai_run, status=200, **extra))
        audit.queue(db)

    # Строгий CSRF (double-submit) — только для cookie-сессии.
    sess = _session_from_request(request, db)
    if sess is not None:
        header = request.headers.get("x-csrf-token") or ""
        if not hmac.compare_digest(header, sess.csrf_token or ""):
            deny(None, None, 403, "csrf_invalid")

    # Скоуп API-ключа: ключ только с `read` не может мутировать.
    authz = request.headers.get("authorization")
    key = None
    if authz and authz.lower().startswith("bearer "):
        raw = authz.split(" ", 1)[1].strip()
        key = db.query(models.ApiKey).filter(
            models.ApiKey.key_hash == _hash_token(raw),
            models.ApiKey.is_active.is_(True)).first()
        if key:
            scopes = key.scopes or []
            if "admin" not in scopes and "write" not in scopes:
                deny(None, key, 403, "scope_write_required")

    user = get_current_user(request, db)

    # --- ENTERPRISE Ф3: делегирование, scope, ai-run, rate-limit ---
    effective, on_behalf, actor_type, deleg_err, deleg_project = \
        resolve_effective_user(db, request, key, user)
    ai_run = None
    if deleg_err:
        deny(user, key, 403, deleg_err)
    if actor_type == "service" and not _rate_ok(key):
        deny(user, key, 429, "rate_limited")

    # Scope API-ключа на проект — для ЛЮБОГО ключа (не только service).
    # Цель может быть в теле (ai/runs, renders), а не только в пути.
    tgt = _target_project_ids(db, pp)
    if not tgt and path.startswith(("/ai/runs", "/renders")):
        try:
            import json as _json
            _body = await request.body()
            _data = _json.loads(_body or b"{}")
            if path.startswith("/ai/runs") and _data.get("project_id") is not None:
                tgt = [int(_data["project_id"])]
            elif path.startswith("/renders") and _data.get("presentation_id") is not None:
                tgt = presentation_project_ids(db, int(_data["presentation_id"]))
        except Exception:
            pass
    # Создание презентации в папке (folder_id в теле) — тоже цель для scope.
    if not tgt and path.rstrip("/") == "/presentations":
        try:
            import json as _json
            _data = _json.loads(await request.body() or b"{}")
            if _data.get("folder_id") is not None:
                _pid = folder_project_id(db, int(_data["folder_id"]))
                tgt = [_pid] if _pid else []
        except Exception:
            pass
    # Цель может быть не в пути-проекте: слайд (по pk) и папка — резолвим проект.
    if not tgt:
        _sid = pp.get("slide_id")
        if _sid is not None and path.startswith("/presentations/slides"):
            _pres = slide_presentation_id(db, int(_sid))
            tgt = presentation_project_ids(db, _pres) if _pres else []
        elif pp.get("folder_id") is not None:
            _pid = folder_project_id(db, int(pp.get("folder_id")))
            tgt = [_pid] if _pid else []

    if key is not None and getattr(key, "project_id", None) is not None and tgt:
        if int(key.project_id) not in tgt:
            deny(user, key, 403, "key_project_scope")
    # Делегирование, ограниченное проектом: цель обязана совпасть.
    if deleg_project is not None and tgt and int(deleg_project) not in tgt:
        deny(user, key, 403, "delegation_project_scope")

    # Провенанс ИИ: заголовок X-AI-Run-Id валидируется для ЛЮБОГО актора.
    run_hdr = request.headers.get("x-ai-run-id")
    if run_hdr:
        run = db.query(models.AiRun).filter(models.AiRun.run_id == run_hdr).first()
        owner_ok = key is not None and run is not None and run.bot_user_id == getattr(key, "owner_id", None)
        if not run or run.status != "running" or not owner_ok:
            deny(user, key, 403, "ai_run_invalid")
        ai_run = run.run_id
    elif AI_RUNS_REQUIRED:
        deny(user, key, 403, "ai_run_required")

    def ok(**extra):
        allow(user, key, effective=effective, on_behalf=on_behalf, ai_run=ai_run, **extra)

    def no(code, reason, **extra):
        deny(user, key, code, reason, effective=effective, on_behalf=on_behalf, **extra)

    # Каталог и админка — супер-админ (ботам запрещено, даже от имени админа).
    if path.startswith(("/components", "/variants", "/presets", "/admin")):
        if effective is None:
            no(401, "authentication_required")
        if not effective.is_superadmin:
            no(403, "admin_only")
        if actor_type == "service":
            no(403, "bot_forbidden")
        ok()
        return

    # API-ключи: аутентификация обязательна (владение проверяет роутер).
    if path.startswith("/api-keys"):
        if effective is None:
            no(401, "authentication_required")
        if actor_type == "service":
            no(403, "bot_forbidden")  # ключи создаёт человек, не бот
        ok()
        return

    if effective is None:
        no(401, "authentication_required")

    # Супер-админ проходит всё, НО не бот: для service-акторов идём дальше,
    # чтобы применить cap (иначе бот «от имени админа» обходил бы ограничения).
    if effective.is_superadmin and actor_type != "service":
        ok()
        return

    # AI-runs и делегирования: только факт аутентификации (права — внутри роутеров).
    if path.startswith(("/ai/runs", "/delegations")):
        if effective is None:
            no(401, "authentication_required")
        ok()
        return

    need = "editor"
    role: Optional[str] = None

    if path.startswith("/projects"):
        pid = pp.get("project_id") or pp.get("id")
        if pid is None or path.endswith("/fork"):
            if actor_type == "service":
                no(403, "bot_forbidden")  # проекты создаёт человек
            ok()  # создание/форк — видимость проверяет роутер
            return
        role = project_role(db, int(pid), effective)
        need = "owner"

    elif path.startswith("/presentations"):
        if any(seg in path for seg in ("/style", "/tokens", "/palette")):
            need = "owner"
        pid = pp.get("presentation_id")
        if pid is not None:
            role = presentation_role(db, int(pid), effective)
        else:
            sid = pp.get("slide_id")
            if sid is not None:
                role = slide_role(db, int(sid), effective)
            else:
                fid = pp.get("folder_id")
                if fid is not None:
                    role = folder_role(db, int(fid), effective)
                    need = "owner"
                else:
                    ok()  # POST /presentations/ — создание
                    return

    elif path.startswith("/ai"):
        pid = pp.get("presentation_id")
        role = presentation_role(db, int(pid), effective) if pid is not None else None
        need = "editor"

    elif path.startswith("/renders"):
        body = await request.body()
        pid = _presentation_id_from_body(request, body)
        if pid is None:
            job_id = pp.get("job_id")
            if job_id is not None:
                job = db.query(models.RenderJob).filter(
                    models.RenderJob.id == int(job_id)).first()
                pid = job.presentation_id if job else None
        if pid is None:
            no(403, "insufficient_role")
        role = presentation_role(db, pid, effective)
        need = "editor"

    else:
        return

    # Cap бота: owner-операции (стиль/токены/палитра/команда/передача/удаление) запрещены.
    if actor_type == "service" and need == "owner":
        no(403, "bot_forbidden", role=role, need=need)

    if rank(role) < rank(need):
        no(403, "insufficient_role", role=role, need=need)
    ok(role=role, need=need)
