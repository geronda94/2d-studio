"""Аудит (ENTERPRISE Ф1): транзакционная запись + redaction + deny-логирование.

Идея: контекст доступа кладётся в `session.info['audit_ctx']`, а строка аудита
дописывается в ту же транзакцию хуком `before_commit` — мутация и лог коммитятся
вместе (или вместе откатываются). Deny-события пишутся отдельной сессией.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

from . import models

# Ключи, значения которых нельзя хранить (секреты) и PII.
_SECRET_KEYS = ("password", "token", "secret", "key", "cookie", "authorization", "csrf")
_PII_KEYS = ("email", "phone", "telegram", "whatsapp")
_REDACTED = "***"
_MAX_STR = 500


def _mask_scalar(v):
    if isinstance(v, str):
        return v[:_MAX_STR] + ("…" if len(v) > _MAX_STR else "")
    return v


def mask(value):
    """Рекурсивно вырезает секреты и PII. Строки обрезает по длине."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            kl = str(k).lower()
            if any(s in kl for s in _SECRET_KEYS):
                out[k] = _REDACTED
            elif any(p in kl for p in _PII_KEYS):
                out[k] = _mask_pii(v)
            else:
                out[k] = mask(v)
        return out
    if isinstance(value, list):
        return [mask(v) for v in value]
    return _mask_scalar(value)


def _mask_pii(v):
    if not isinstance(v, str) or "@" not in v:
        return _REDACTED if v else v
    user, _, domain = v.partition("@")
    return f"{user[:1]}{_REDACTED}@{domain[:1]}{_REDACTED}"


def set_context(session: Session, ctx: dict) -> None:
    session.info["audit_ctx"] = ctx


def queue(session: Session, **overrides) -> None:
    """Поставить строку аудита в очередь текущей сессии (уйдёт в том же коммите)."""
    ctx = dict(session.info.get("audit_ctx") or {})
    ctx.update(overrides)
    session.info.setdefault("audit_entries", []).append(ctx)


def _entry_to_row(ctx: dict) -> models.AuditLog:
    return models.AuditLog(
        request_id=ctx.get("request_id"),
        actor_type=ctx.get("actor_type") or "system",
        actor_user_id=ctx.get("actor_user_id"),
        actor_key_id=ctx.get("actor_key_id"),
        on_behalf_of_user_id=ctx.get("on_behalf_of_user_id"),
        effective_user_id=ctx.get("effective_user_id"),
        project_id=ctx.get("project_id"),
        presentation_id=ctx.get("presentation_id"),
        slide_id=ctx.get("slide_id"),
        action=ctx.get("action"),
        method=ctx.get("method"),
        path=ctx.get("path"),
        status=ctx.get("status"),
        decision=ctx.get("decision") or "allow",
        deny_reason=ctx.get("deny_reason"),
        ip=ctx.get("ip"),
        user_agent=(ctx.get("user_agent") or "")[:256] or None,
        ai_run_id=ctx.get("ai_run_id"),
        diff=mask(ctx.get("diff")) if ctx.get("diff") is not None else None,
        meta=mask(ctx.get("meta")) if ctx.get("meta") is not None else None,
    )


def _outbox_enabled() -> bool:
    # outbox нужен только при настроенном внешнем sink; иначе не копим мусор.
    return bool(os.environ.get("AUDIT_WEBHOOK_URL"))


def _before_commit(session: Session):
    entries = session.info.get("audit_entries")
    if not entries or session.info.get("audit_flushed"):
        return  # уже записали в этом коммите — не дублируем при повторных commit()
    for ctx in list(entries):
        session.add(_entry_to_row(ctx))
        if _outbox_enabled():
            session.add(models.AuditOutbox(payload={
                "action": ctx.get("action"), "actor_user_id": ctx.get("actor_user_id"),
                "effective_user_id": ctx.get("effective_user_id"),
                "project_id": ctx.get("project_id"),
            }))
    session.info["audit_flushed"] = True


def _clear(session: Session):
    session.info.pop("audit_ctx", None)
    session.info.pop("audit_entries", None)
    session.info.pop("audit_flushed", None)


def _after_commit(session: Session):
    _clear(session)


def _after_rollback(session: Session):
    _clear(session)


def register() -> None:
    """Навесить хуки один раз при старте приложения."""
    if getattr(register, "_done", False):
        return
    event.listen(Session, "before_commit", _before_commit)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    register._done = True


def write_row(ctx: dict) -> None:
    """Записать строку аудита немедленно отдельной сессией (для событий без транзакции:
    deny и аудит чтений)."""
    try:
        from .database import SessionLocal
        db = SessionLocal()
        try:
            db.add(_entry_to_row(ctx))
            db.commit()
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        print(f"[audit] write failed: {e}", flush=True)


def log_deny(ctx: dict) -> None:
    write_row({**ctx, "decision": "deny"})


# --- Семантическое имя действия -------------------------------------------------
_ACTION_RULES = [
    (re.compile(r"/projects/\d+/config"), "project.config_update"),
    (re.compile(r"/projects/\d+/brief"), "project.brief_update"),
    (re.compile(r"/projects/\d+/members"), "project.member_update"),
    (re.compile(r"/projects/\d+/transfer"), "project.transfer"),
    (re.compile(r"/projects/\d+/tokens"), "project.tokens_update"),
    (re.compile(r"/projects/\d+/fork"), "project.fork"),
    (re.compile(r"/presentations/\d+/change-set"), "presentation.change_set"),
    (re.compile(r"/presentations/\d+/style"), "presentation.style_update"),
    (re.compile(r"/presentations/\d+/tokens"), "presentation.tokens_update"),
    (re.compile(r"/presentations/\d+/palette"), "presentation.palette"),
    (re.compile(r"/presentations/\d+/slides"), "slide.upsert"),
    (re.compile(r"/presentations/slides/"), "slide.upsert"),
    (re.compile(r"/presentations/\d+/media"), "media.upsert"),
    (re.compile(r"/presentations/\d+/revisions"), "presentation.revision_restore"),
    (re.compile(r"/api-keys"), "apikey.manage"),
    (re.compile(r"/admin/users"), "admin.user_update"),
    (re.compile(r"/renders"), "render.manage"),
    (re.compile(r"/ai/"), "ai.run"),
]


def derive_action(method: str, path: str) -> str:
    for rx, name in _ACTION_RULES:
        if rx.search(path or ""):
            return name
    seg = [s for s in (path or "").strip("/").split("/") if s and not s.isdigit()]
    return f"{method.lower()}.{'/'.join(seg[:2]) or 'unknown'}"
