"""Сид проекта Diademas (перенос темы прототипа Church/DIADEMAS).

Создаёт:
  1. `diademas` — рабочий проект (owner = ADMIN/пользователь), ОСНОВНАЯ дневная
     палитра Overcast/Forest, default_variant='diademas'.
  2. `template-diademas-dark` — тёмная палитра Midnight/Gold для витрины
     (is_template=True), переключается в презентации через `palette_source`.
     (Звёздная сцена отложена — тёмная схема лежит про запас.)
  3. `template-diademas-day` — ДНЕВНАЯ палитра Overcast/Forest (лесной зелёный)
     как шаблон витрины (is_template=True). Нужна, чтобы зелёную Diademas можно
     было применить из пикера, не завися от managed-токенов рабочего проекта.

Все палитры заполнены ВСЕМ каноническим набором токенов (89 ключей GLOBAL_TOKENS),
значения выведены из CSS-переменных прототипа (`frontend/src/assets/css/main.css`).

P0-конвенция: по умолчанию только досев отсутствующих; `--force` перезаписывает
managed-значения; кастомы (is_custom) не трогаются никогда.

Запуск: docker compose exec backend python scripts/seed_diademas.py [--force]
        [--owner-email iiiliev.igor@gmail.com]
"""
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from scripts.seed_tokens import GLOBAL_TOKENS, _infer_token_type
from scripts.gen_diademas_bg import (
    STARFIELD_URI, CLOUDS_URI, NOISE_URI, STAR_PATTERN_URI, DOT_PATTERN_URI,
)

DEFAULT_OWNER_EMAIL = "iiiliev.igor@gmail.com"

FONT_LINK = (
    "https://fonts.googleapis.com/css2?"
    "family=EB+Garamond:ital,wght@0,400;0,500;0,700;1,400"
    "&family=Inter:wght@400;500;600;700"
    "&family=Cinzel:wght@400;500;600"
    "&family=Noto+Serif+Georgian:wght@400;700"
    "&family=Space+Mono:wght@400;700&display=swap"
)

DIADEMAS_BRIEF = {
    "about": "Diademas — премиальный бренд (прототип Church/DIADEMAS). Основная схема — "
             "дневная Overcast Sky / True Forest: пасмурное небо, белые блоки и "
             "благородный лесной зелёный.",
    "audience": "Сообщество, прихожане, партнёры",
    "tone": "Торжественный, тёплый, спокойный, премиальный",
    "must": ["светлая база", "лесной зелёный", "воздух", "серифные акценты", "мягкие тени"],
    "forbidden": ["неоновые кислотные цвета", "эмодзи", "суетливые анимации", "тяжёлые чёрные тени"],
    "voice": "Спокойный, вдохновляющий, достойный",
}

# ── Тёмная палитра (Midnight/Gold) — запасная (звёздная сцена отложена) ─────
DIADEMAS_DARK = {
    # Поверхности
    "bg-base": "#040815",
    "bg-surface": "#0D1528",
    "bg-surface-2": "#121B33",
    "bg-hover": "#151E36",
    "bg-overlay": NOISE_URI,

    # Границы
    "border-main": "#1E293B",
    "border-strong": "#334155",
    "border-accent": "#C7A557",

    # Текст
    "text-primary": "#F1F5F9",
    "text-secondary": "#94A3B8",
    "text-muted": "#64748B",
    "text-on-color": "#0A0F1A",

    # Роли (золото)
    "color-primary": "#C7A557",
    "color-primary-soft": "#2A2416",
    "color-secondary": "#A68A48",
    "color-secondary-soft": "#26200F",
    "color-accent": "#E8C165",
    "color-accent-soft": "#33290F",
    "color-accent-2": "#FDE68A",
    "color-accent-2-soft": "#332B12",
    "color-success": "#52B788",
    "color-success-soft": "#10291F",
    "color-warning": "#F0B048",
    "color-warning-soft": "#33280F",
    "color-error": "#E5484D",
    "color-error-soft": "#331417",

    # Данные и графики
    "chart-1": "#C7A557",
    "chart-2": "#52B788",
    "chart-3": "#FDE68A",
    "chart-4": "#2D6A4F",
    "chart-5": "#92400E",
    "chart-6": "#A68A48",
    "chart-grid": "rgba(148, 163, 184, 0.12)",
    "chart-axis": "#7C6E4A",

    # Эффекты
    "gradient-primary": "linear-gradient(135deg, #C7A557 0%, #E8C165 100%)",
    "gradient-accent": "linear-gradient(135deg, #A68A48 0%, #FDE68A 100%)",
    "gradient-hero": "linear-gradient(180deg, #02040A 0%, #040815 50%, #0D1528 100%)",
    "gradient-surface": "linear-gradient(160deg, #121B33 0%, #0D1528 100%)",
    "gradient-text": "linear-gradient(90deg, #FDE68A 0%, #C7A557 100%)",
    "gradient-chart": "linear-gradient(180deg, rgba(199,165,87,0.5) 0%, rgba(199,165,87,0) 100%)",
    "glow-primary": "0 0 30px rgba(199, 165, 87, 0.35)",
    "glow-accent": "0 0 30px rgba(255, 245, 220, 0.28)",
    "shadow-color": "rgba(0, 0, 0, 0.55)",
    "glass-bg": "rgba(13, 21, 40, 0.5)",
    "pattern-bg": STAR_PATTERN_URI,
    "bg-overlay-light": "rgba(255, 255, 255, 0.5)",

    # Сцена (STUDIO)
    "bg-image": ("radial-gradient(700px 520px at 18% 3%, rgb(199 165 87 / 0.10), transparent 62%), "
                 "radial-gradient(900px 700px at 84% 100%, rgb(56 90 150 / 0.12), transparent 66%)"),
    "bg-decorations": STARFIELD_URI,
    "bg-decorations-size": "cover",
    "bg-overlay-opacity": "0.08",

    # Состояния
    "color-primary-strong": "#E8C165",
    "color-secondary-strong": "#C7A557",
    "color-accent-strong": "#FFF5DC",
    "color-accent-2-strong": "#FFEFC2",
    "color-success-strong": "#74C69D",
    "color-warning-strong": "#F6D378",
    "color-error-strong": "#F87171",
    "text-on-primary": "#0A0F1A",
    "text-on-accent": "#0A0F1A",

    # Алиасы читаемости
    "color-danger": "#E5484D",
    "color-danger-soft": "#331417",
    "color-danger-strong": "#F87171",
    "color-info": "#A68A48",
    "color-info-soft": "#26200F",
    "color-info-strong": "#C7A557",

    # Шахматка айтемов
    "item-accent-1": "#C7A557",
    "item-accent-2": "#52B788",
    "item-accent-3": "#FDE68A",
    "item-accent-4": "#A68A48",

    # Шахматка фонов слайдов
    "slide-bg-1": "#040815",
    "slide-bg-2": "#0A1226",
    "slide-bg-3": "#0D1528",
    "slide-bg-4": "#151E36",

    # Шрифты (прототип: body = spiritual/EB Garamond, headings/UI = tech/Inter)
    "font-sans": '"EB Garamond", Georgia, serif',
    "font-heading": '"Inter", sans-serif',
    "font-mono": '"Space Mono", monospace',
    "font_link": FONT_LINK,

    # Типографическая шкала
    "type-display": "3.5rem",
    "type-h1": "2.5rem",
    "type-h2": "1.85rem",
    "type-body": "1.125rem",
    "type-caption": "0.85rem",

    # Алиасы совместимости (gradient <em>: brand-light-blue → brand-blue)
    "brand-blue": "#C7A557",
    "brand-light-blue": "#FDE68A",
    "brand-green": "#52B788",
    "brand-amber": "#F0B048",
    "brand-orange": "#E8C165",
    "brand-accent": "#E8C165",
    "bg-surface-hover": "#151E36",
}

# ── Светлая палитра (Overcast Sky / True Forest) — ОСНОВНАЯ ─────────────────
DIADEMAS_LIGHT = {
    # Поверхности
    "bg-base": "#CFD8E1",
    "bg-surface": "#FFFFFF",
    "bg-surface-2": "#EDF1F7",
    "bg-hover": "#BFCAD3",
    "bg-overlay": NOISE_URI,

    # Границы
    "border-main": "#A9B8C4",
    "border-strong": "#8FA3B3",
    "border-accent": "#2D6A4F",

    # Текст
    "text-primary": "#0F172A",
    "text-secondary": "#2D3748",
    "text-muted": "#64748B",
    "text-on-color": "#FFFFFF",

    # Роли (лес/изумруд)
    "color-primary": "#2D6A4F",
    "color-primary-soft": "#DCE9E2",
    "color-secondary": "#40916C",
    "color-secondary-soft": "#DDEDE4",
    "color-accent": "#52B788",
    "color-accent-soft": "#E3F3EA",
    "color-accent-2": "#99D98C",
    "color-accent-2-soft": "#EAF7E4",
    "color-success": "#40916C",
    "color-success-soft": "#DDEDE4",
    "color-warning": "#B7791F",
    "color-warning-soft": "#F7ECD0",
    "color-error": "#B42318",
    "color-error-soft": "#F7DBD9",

    # Данные и графики
    "chart-1": "#2D6A4F",
    "chart-2": "#40916C",
    "chart-3": "#52B788",
    "chart-4": "#99D98C",
    "chart-5": "#B7791F",
    "chart-6": "#6B7280",
    "chart-grid": "rgba(15, 23, 42, 0.08)",
    "chart-axis": "#64748B",

    # Эффекты
    "gradient-primary": "linear-gradient(135deg, #2D6A4F 0%, #40916C 100%)",
    "gradient-accent": "linear-gradient(135deg, #52B788 0%, #99D98C 100%)",
    "gradient-hero": "radial-gradient(120% 100% at 50% 20%, #EAF1F7 0%, #CFD8E1 60%, #BFCAD3 100%)",
    "gradient-surface": "linear-gradient(160deg, #FFFFFF 0%, #EDF1F7 100%)",
    "gradient-text": "linear-gradient(90deg, #1B4332 0%, #52B788 100%)",
    "gradient-chart": "linear-gradient(180deg, rgba(45,106,79,0.4) 0%, rgba(45,106,79,0) 100%)",
    "glow-primary": "0 0 24px rgba(45, 106, 79, 0.25)",
    "glow-accent": "0 0 24px rgba(82, 183, 136, 0.25)",
    "shadow-color": "rgba(15, 23, 42, 0.12)",
    "glass-bg": "rgba(255, 255, 255, 0.6)",
    "pattern-bg": DOT_PATTERN_URI,
    "bg-overlay-light": "rgba(255, 255, 255, 0.6)",

    # Сцена (STUDIO)
    "bg-image": ("radial-gradient(700px 480px at 20% 0%, rgb(255 255 255 / 0.55), transparent 65%), "
                 "radial-gradient(900px 620px at 85% 100%, rgb(64 145 108 / 0.08), transparent 68%)"),
    "bg-decorations": CLOUDS_URI,
    "bg-decorations-size": "cover",
    "bg-overlay-opacity": "0.06",

    # Состояния
    "color-primary-strong": "#1B4332",
    "color-secondary-strong": "#2D6A4F",
    "color-accent-strong": "#40916C",
    "color-accent-2-strong": "#74C69D",
    "color-success-strong": "#2D6A4F",
    "color-warning-strong": "#975A16",
    "color-error-strong": "#912018",
    "text-on-primary": "#FFFFFF",
    "text-on-accent": "#FFFFFF",

    # Алиасы читаемости
    "color-danger": "#B42318",
    "color-danger-soft": "#F7DBD9",
    "color-danger-strong": "#912018",
    "color-info": "#40916C",
    "color-info-soft": "#DDEDE4",
    "color-info-strong": "#2D6A4F",

    # Шахматка айтемов
    "item-accent-1": "#2D6A4F",
    "item-accent-2": "#40916C",
    "item-accent-3": "#99D98C",
    "item-accent-4": "#B7791F",

    # Шахматка фонов слайдов
    "slide-bg-1": "#CFD8E1",
    "slide-bg-2": "#DDE4EC",
    "slide-bg-3": "#EAF1F7",
    "slide-bg-4": "#FFFFFF",

    # Шрифты (те же, что в тёмной)
    "font-sans": '"EB Garamond", Georgia, serif',
    "font-heading": '"Inter", sans-serif',
    "font-mono": '"Space Mono", monospace',
    "font_link": FONT_LINK,

    # Типографическая шкала
    "type-display": "3.5rem",
    "type-h1": "2.5rem",
    "type-h2": "1.85rem",
    "type-body": "1.125rem",
    "type-caption": "0.85rem",

    # Алиасы совместимости (gradient <em>: brand-light-blue → brand-blue)
    "brand-blue": "#2D6A4F",
    "brand-light-blue": "#99D98C",
    "brand-green": "#40916C",
    "brand-amber": "#B7791F",
    "brand-orange": "#52B788",
    "brand-accent": "#52B788",
    "bg-surface-hover": "#BFCAD3",
}


def _seed_tokens(db, project_id, tokens, force=False):
    """P0-конвенция: создать отсутствующие; --force — обновить managed; кастомы не трогать."""
    created = updated = skipped = 0
    for key, value in tokens.items():
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
            if force:
                existing.value = value
                existing.is_custom = False
                updated += 1
        else:
            db.add(models.DesignToken(
                project_id=project_id,
                token_key=key,
                token_type=_infer_token_type(key),
                value=value,
                is_custom=False,
            ))
            created += 1
    return created, updated, skipped


def run(force=False, owner_email=DEFAULT_OWNER_EMAIL):
    models.Base.metadata.create_all(bind=engine)

    # Палитры обязаны покрывать весь канон (иначе проект получит «дыры»).
    missing = set(GLOBAL_TOKENS) - set(DIADEMAS_DARK)
    extra_dark = set(DIADEMAS_DARK) - set(GLOBAL_TOKENS)
    missing_l = set(GLOBAL_TOKENS) - set(DIADEMAS_LIGHT)
    extra_l = set(DIADEMAS_LIGHT) - set(GLOBAL_TOKENS)
    assert not missing, f"DIADEMAS_DARK не хватает ключей: {sorted(missing)}"
    assert not missing_l, f"DIADEMAS_LIGHT не хватает ключей: {sorted(missing_l)}"
    assert not extra_dark, f"DIADEMAS_DARK лишние ключи: {sorted(extra_dark)}"
    assert not extra_l, f"DIADEMAS_LIGHT лишние ключи: {sorted(extra_l)}"

    db = SessionLocal()
    try:
        owner = db.query(models.User).filter(models.User.email == owner_email.lower()).first()
        if not owner:
            raise SystemExit(f"Пользователь '{owner_email}' не найден — назначить владельца нельзя")

        # 1) Рабочий проект diademas — ОСНОВНАЯ дневная палитра (Overcast/Forest)
        project = db.query(models.Project).filter(models.Project.slug == "diademas").first()
        if not project:
            project = models.Project(
                slug="diademas",
                title="Diademas",
                description="Основная тема Diademas: светлая Overcast/Forest — пасмурное небо и лесной зелёный.",
                is_template=False,
                owner_id=owner.id,
                default_variant="diademas",
                brief=DIADEMAS_BRIEF,
            )
            db.add(project)
            db.flush()
            print(f"Создан проект «diademas» (id={project.id}, owner={owner.email})")
        else:
            project.title = "Diademas"
            project.description = "Основная тема Diademas: светлая Overcast/Forest — пасмурное небо и лесной зелёный."
            project.owner_id = owner.id
            project.is_template = False
            project.default_variant = "diademas"
            project.brief = DIADEMAS_BRIEF
            print(f"Обновлён проект «diademas» (id={project.id}, owner={owner.email})")

        # BRAND KIT (ProjectBrand): имя + лого. Мерж — контакты/дефолты не затираем,
        # уже заданный лого не перезаписываем (P0-дух: ручная правка переживает пересев).
        from sqlalchemy.orm.attributes import flag_modified
        cfg = dict(getattr(project, "config", None) or {})
        brand = dict(cfg.get("brand") or {})
        brand.setdefault("name", "Diademas")
        brand.setdefault("logo", "/media/diademas_logo.svg")
        cfg["brand"] = brand
        project.config = cfg
        flag_modified(project, "config")
        print(f"BRAND KIT: name={brand.get('name')} logo={brand.get('logo')}")

        folder_slug = "drafts-diademas"
        if not db.query(models.Folder).filter(models.Folder.slug == folder_slug).first():
            db.add(models.Folder(slug=folder_slug, title="Черновики", project_id=project.id))

        c, u, s = _seed_tokens(db, project.id, DIADEMAS_LIGHT, force=force)
        print(f"«diademas» (дневная): +{c} ~{u} skip-custom {s}")

        # 2) Палитра-шаблон template-diademas-dark (тёмная, про запас)
        dark = db.query(models.Project).filter(
            models.Project.slug == "template-diademas-dark").first()
        if not dark:
            # миграция со старого slug (был светлым шаблоном, стал тёмным)
            legacy = db.query(models.Project).filter(
                models.Project.slug == "template-diademas-light").first()
            if legacy:
                legacy.slug = "template-diademas-dark"
                dark = legacy
        if not dark:
            dark = models.Project(
                slug="template-diademas-dark",
                title="Diademas · Золото (шаблон)",
                description="Тёмная Midnight/Gold палитра Diademas (звёздная сцена) для витрины.",
                is_template=True,
                owner_id=None,
                default_variant="diademas",
            )
            db.add(dark)
            db.flush()
            print(f"Создан шаблон «template-diademas-dark» (id={dark.id})")
        else:
            dark.title = "Diademas · Золото (шаблон)"
            dark.description = "Тёмная Midnight/Gold палитра Diademas (звёздная сцена) для витрины."
            dark.is_template = True
            dark.default_variant = "diademas"
            print(f"Обновлён шаблон «template-diademas-dark» (id={dark.id})")

        c, u, s = _seed_tokens(db, dark.id, DIADEMAS_DARK, force=force)
        print(f"«template-diademas-dark» (тёмная): +{c} ~{u} skip-custom {s}")

        # 3) Палитра-шаблон template-diademas-day (дневная Overcast/Forest, зелёная)
        day = db.query(models.Project).filter(
            models.Project.slug == "template-diademas-day").first()
        if not day:
            day = models.Project(
                slug="template-diademas-day",
                title="Diademas · Лес (шаблон)",
                description="Светлая Overcast/Forest палитра Diademas: пасмурное небо и лесной зелёный.",
                is_template=True,
                owner_id=None,
                default_variant="diademas",
            )
            db.add(day)
            db.flush()
            print(f"Создан шаблон «template-diademas-day» (id={day.id})")
        else:
            day.title = "Diademas · Лес (шаблон)"
            day.description = "Светлая Overcast/Forest палитра Diademas: пасмурное небо и лесной зелёный."
            day.is_template = True
            day.default_variant = "diademas"
            print(f"Обновлён шаблон «template-diademas-day» (id={day.id})")

        c, u, s = _seed_tokens(db, day.id, DIADEMAS_LIGHT, force=force)
        print(f"«template-diademas-day» (дневная): +{c} ~{u} skip-custom {s}")

        db.commit()
        print("Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Сид проекта Diademas + светлой палитры-шаблона.")
    ap.add_argument("--force", action="store_true",
                    help="Перезаписать managed-значения токенов")
    ap.add_argument("--owner-email", default=DEFAULT_OWNER_EMAIL,
                    help="Email владельца проекта diademas")
    args = ap.parse_args()
    run(force=args.force, owner_email=args.owner_email)
