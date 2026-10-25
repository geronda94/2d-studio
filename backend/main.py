import os
from dotenv import load_dotenv
# Load .env file from the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import presentations, components, projects, ai, renders, variants, presets, api_keys, auth, admin, audit as audit_router, revisions as revisions_router, ai_runs as ai_runs_router, delegations as delegations_router, scene_library, rig as rig_router, scene_assets
from . import audit

models.Base.metadata.create_all(bind=engine)


def _ensure_columns():
    """Идемпотентные ALTER для новых колонок (инвариант проекта: только ADD ... IF NOT EXISTS)."""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS visibility VARCHAR DEFAULT 'public'",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS config JSON",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS version INT DEFAULT 0",
        "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS version INT DEFAULT 0",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS kind VARCHAR DEFAULT 'legacy'",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS duration FLOAT",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS code JSON",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS props JSON",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS props_schema JSON",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS track VARCHAR DEFAULT 'main'",
        "ALTER TABLE slides ADD COLUMN IF NOT EXISTS z_index INT DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS owner_user_id INT",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS kind VARCHAR DEFAULT 'personal'",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS created_by_user_id INT",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS project_id INT",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS can_delegate BOOLEAN DEFAULT false",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rate_limit INT",
        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ",
        # ENTERPRISE Ф4: audit_log append-only на уровне БД (запрет UPDATE/DELETE).
        """CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END; $$ LANGUAGE plpgsql""",
        "DROP TRIGGER IF EXISTS audit_log_no_change ON audit_log",
        "CREATE TRIGGER audit_log_no_change BEFORE UPDATE OR DELETE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION audit_log_immutable()",
        # 1 запись = 1 связка проект+пользователь (AUTH_PLAN Ф2)
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_project_members_project_user "
        "ON project_members (project_id, user_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_project_revisions_project_n "
        "ON project_revisions (project_id, n)",
    ]
    with engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
            except Exception as e:  # noqa: BLE001
                print(f"ensure_columns skip: {e}", flush=True)


_ensure_columns()


def _bootstrap_admin():
    """Создать/повысить супер-админа из env (AUTH_PLAN Ф2). Публичная регистрация
    НЕ даёт прав админа — только владелец .env через ADMIN_EMAIL/ADMIN_PASSWORD."""
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not email:
        return
    from .database import SessionLocal
    from .auth import hash_password
    db = SessionLocal()
    try:
        u = db.query(models.User).filter(models.User.email == email).first()
        if not u:
            if not password:
                return
            u = models.User(email=email, password_hash=hash_password(password),
                            display_name="Admin", is_superadmin=True)
            db.add(u)
        elif not u.is_superadmin:
            u.is_superadmin = True
        db.commit()
    finally:
        db.close()


_bootstrap_admin()

# Транзакционные хуки аудита (ENTERPRISE Ф1).
audit.register()


def _fail_stale_render_jobs():
    """Если бэкенд перезапустили посреди рендера, дочерние процессы убиты вместе
    с контейнером, а job остался 'rendering'/'pending' навсегда. Помечаем failed."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        n = db.query(models.RenderJob).filter(
            models.RenderJob.status.in_(("rendering", "pending"))).update(
            {models.RenderJob.status: "failed",
             models.RenderJob.error_log: "interrupted by server restart"},
            synchronize_session=False)
        db.commit()
        if n:
            print(f"[renders] stale jobs marked failed: {n}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[renders] stale cleanup skip: {e}", flush=True)
    finally:
        db.close()


_fail_stale_render_jobs()


def _start_audit_exporter():
    """ENTERPRISE Ф4: доставка аудита во внешний sink (SIEM/webhook) из durable outbox.
    Включается env AUDIT_WEBHOOK_URL; иначе выключено. Плюс ретеншен доставленного."""
    url = os.environ.get("AUDIT_WEBHOOK_URL")
    if not url:
        return
    import datetime
    import json
    import threading
    import time
    import urllib.request

    def _worker():
        while True:
            time.sleep(10)
            from .database import SessionLocal
            db = SessionLocal()
            try:
                rows = db.query(models.AuditOutbox).filter(
                    models.AuditOutbox.delivered_at.is_(None)
                ).order_by(models.AuditOutbox.id).limit(100).all()
                for r in rows:
                    try:
                        req = urllib.request.Request(
                            url, data=json.dumps(r.payload or {}).encode(),
                            headers={"Content-Type": "application/json"}, method="POST")
                        urllib.request.urlopen(req, timeout=5)
                        r.delivered_at = datetime.datetime.utcnow()
                    except Exception:
                        break  # sink недоступен — оставим в outbox, повторим позже
                # ретеншен: доставленное старше 7 дней — чистим (аудит в audit_log не трогаем)
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
                db.query(models.AuditOutbox).filter(
                    models.AuditOutbox.delivered_at.isnot(None),
                    models.AuditOutbox.delivered_at < cutoff).delete()
                db.commit()
            except Exception as e:  # noqa: BLE001
                print(f"[audit] exporter error: {e}", flush=True)
            finally:
                db.close()

    threading.Thread(target=_worker, daemon=True).start()


_start_audit_exporter()


def _cleanup_sessions():
    """Удаляем истёкшие сессии (гигиена AUTH_PLAN)."""
    import datetime
    from .database import SessionLocal
    db = SessionLocal()
    try:
        db.query(models.UserSession).filter(
            models.UserSession.expires_at < datetime.datetime.utcnow()).delete()
        # идемпотентные ключи старше суток — чистим (иначе растут)
        db.query(models.IdempotencyKey).filter(
            models.IdempotencyKey.created_at < datetime.datetime.utcnow() - datetime.timedelta(days=1)
        ).delete()
        db.commit()
    except Exception as e:  # noqa: BLE001
        print(f"session cleanup skip: {e}", flush=True)
    finally:
        db.close()


_cleanup_sessions()

app = FastAPI(title="Presentation Editor API")

# Cookie-сессия (AUTH_PLAN Ф1): с credentials нельзя allow_origins=["*"].
# Если задан FRONTEND_ORIGIN — ограничиваемся им, иначе dev-режим (тот же origin через прокси).
_frontend_origin = os.environ.get("FRONTEND_ORIGIN")
_allowed_origins = [o.strip() for o in _frontend_origin.split(",") if o.strip()] if _frontend_origin else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/media/") or request.url.path.startswith("/uploads/"):
        # immutable только для успешных ответов: иначе CDN (Cloudflare) кэширует 404 на год
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-store"
    return response

UPLOAD_DIR = "/app/uploads" if os.path.exists("/app") else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

MEDIA_DIR = "/app/backend/media" if os.path.exists("/app") else "backend/media"
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.include_router(projects.router)
app.include_router(presentations.router)
app.include_router(ai.router)
app.include_router(components.router)
app.include_router(renders.router)
app.include_router(variants.router)
app.include_router(presets.router)
app.include_router(api_keys.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(audit_router.router)
app.include_router(revisions_router.router)
app.include_router(ai_runs_router.router)
app.include_router(delegations_router.router)
app.include_router(scene_library.router)
app.include_router(rig_router.router)
app.include_router(scene_assets.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Presentation Editor API"}

