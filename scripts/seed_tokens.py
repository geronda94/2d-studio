"""
Сид дизайн-токенов (Фаза 2, Итерация 2.2).

1. Глобальные дефолтные токены (project_id = None) — текущий стиль IT2B.
2. Второй проект «Исторический» со своей палитрой (project_id = history).
Содержит семантические токены из TOKEN_SPEC.md.

Запуск: python scripts/seed_tokens.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models

try:
    from gen_forest_bg import FOREST_URI
except ImportError:  # запуск не из scripts/
    from scripts.gen_forest_bg import FOREST_URI


def _infer_token_type(key: str) -> str:
    if key == "font_link":
        return "font_link"
    if key.startswith("font-"):
        return "font_family"
    if "gradient" in key or key in ("bg-image", "bg-decorations"):
        return "gradient"
    if key.startswith("glow") or key.startswith("pattern"):
        return "effect"
    if key.endswith("-size") or key.endswith("-position") or key.endswith("-opacity"):
        return "text"
    if "shadow" in key:
        return "shadow"
    return "color"


# ── Глобальные дефолты (стиль IT2B) ────────────────────────────────────────
GLOBAL_TOKENS = {
    # Поверхности
    "bg-base": "#0B1322",
    "bg-surface": "#152033",
    "bg-surface-2": "#1C2A42",
    "bg-hover": "#1F2D44",
    "bg-overlay": "rgba(6, 11, 22, 0.72)",

    # Границы
    "border-main": "#2A3A55",
    "border-strong": "#3D5175",
    "border-accent": "#38BDF8",

    # Текст
    "text-primary": "#F8FAFC",
    "text-secondary": "#A6B4C8",
    "text-muted": "#6C7C96",
    "text-on-color": "#FFFFFF",

    # Роли
    "color-primary": "#2563EB",
    "color-primary-soft": "#17284A",
    "color-secondary": "#38BDF8",
    "color-secondary-soft": "#0E2E3A",
    "color-accent": "#F97316",
    "color-accent-soft": "#3A2410",
    "color-accent-2": "#8B5CF6",
    "color-accent-2-soft": "#241E4A",
    "color-success": "#10B981",
    "color-success-soft": "#0E2E26",
    "color-warning": "#F59E0B",
    "color-warning-soft": "#3A2C0E",
    "color-error": "#EF4444",
    "color-error-soft": "#3A1717",

    # Данные и графики
    "chart-1": "#2563EB",
    "chart-2": "#38BDF8",
    "chart-3": "#8B5CF6",
    "chart-4": "#F472B6",
    "chart-5": "#F97316",
    "chart-6": "#10B981",
    "chart-grid": "rgba(148, 163, 184, 0.12)",
    "chart-axis": "#64748B",

    # Эффекты
    "gradient-primary": "linear-gradient(135deg, #3B82F6 0%, #22D3EE 100%)",
    "gradient-accent": "linear-gradient(135deg, #F97316 0%, #F43F5E 100%)",
    "gradient-hero": "linear-gradient(135deg, #0B1322 0%, #17284A 55%, #1C2A42 100%)",
    "gradient-surface": "linear-gradient(160deg, #18243A 0%, #131E30 100%)",
    "gradient-text": "linear-gradient(90deg, #38BDF8 0%, #8B5CF6 100%)",
    "gradient-chart": "linear-gradient(180deg, rgba(37,99,235,0.5) 0%, rgba(37,99,235,0) 100%)",
    "glow-primary": "0 0 30px rgba(37, 99, 235, 0.35)",
    "glow-accent": "0 0 30px rgba(249, 115, 22, 0.35)",
    "shadow-color": "rgba(0, 0, 0, 0.45)",
    "glass-bg": "rgba(21, 32, 51, 0.55)",
    "pattern-bg": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'%3E%3Ccircle cx='1' cy='1' r='1' fill='%2394a3b8' fill-opacity='0.06'/%3E%3C/svg%3E\")",
    "bg-overlay-light": "rgba(255, 255, 255, 0.55)",

    # Сцена (STUDIO): стандартный набор слоёв фона — есть в КАЖДОМ проекте и в каноне
    # coverage. По умолчанию выключены ("none" = CSS-корректное «пусто»). Иллюстрация
    # (bg-decorations) — обычная переменная палитры: derevnya задаёт лес, остальные — none.
    # Слой включается значением, а не отдельным флагом.
    "bg-image": "none",
    "bg-decorations": "none",
    "bg-decorations-size": "100% auto",
    "bg-overlay-opacity": "1",

    # Состояния (hover/active — на тёмной теме ярче)
    "color-primary-strong": "#60A5FA",
    "color-secondary-strong": "#7DD3FC",
    "color-accent-strong": "#FB923C",
    "color-accent-2-strong": "#A78BFA",
    "color-success-strong": "#34D399",
    "color-warning-strong": "#FBBF24",
    "color-error-strong": "#F87171",
    "text-on-primary": "#FFFFFF",
    "text-on-accent": "#FFFFFF",

    # Алиасы читаемости (danger/info = синонимы error/secondary — ИИ понимает оба имени)
    "color-danger": "#EF4444",
    "color-danger-soft": "#3A1717",
    "color-danger-strong": "#F87171",
    "color-info": "#38BDF8",
    "color-info-soft": "#0E2E3A",
    "color-info-strong": "#7DD3FC",

    # Шахматные акценты для айтемов (4 гармоничных цвета, циклично: item-accent-{(i%4)+1})
    # Значения = бизнес-палитра (secondary/success/warning/accent-2), пер-темно различаются
    "item-accent-1": "#38BDF8",
    "item-accent-2": "#10B981",
    "item-accent-3": "#F59E0B",
    "item-accent-4": "#8B5CF6",

    # Шахматные фоны слайдов (циклично slide-bg-{(i%4)+1}) — едва уловимая смена глубины
    # Избегаем точного совпадения с bg-surface (#152033) чтобы фуллскрин Code/Browser не сливались
    "slide-bg-1": "#0B1322",
    "slide-bg-2": "#0F1D33",
    "slide-bg-3": "#121E32",
    "slide-bg-4": "#1C2A42",

    # Шрифты
    "font-sans": '"Inter", sans-serif',
    "font-heading": '"Space Grotesk", sans-serif',
    "font-mono": '"Space Mono", monospace',
    "font_link": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap",

    # Типографическая шкала (P4): tech-значения = текущие классы (text-4xl/text-lg),
    # tech не меняется; history/derevnya дифференцируются
    "type-display": "3.5rem",
    "type-h1": "2.25rem",
    "type-h2": "1.75rem",
    "type-body": "1.125rem",
    "type-caption": "0.8rem",

    # Алиасы (Оставлены для совместимости со старыми payload)
    "brand-blue": "#2563EB",
    "brand-light-blue": "#38BDF8",
    "brand-green": "#10B981",
    "brand-amber": "#F59E0B",
    "brand-orange": "#EA580C",
    "brand-accent": "#F97316",
    "bg-surface-hover": "#1F2D44",
}

# ── Второй проект «Исторический» ───────────────────────────────────────────
HISTORICAL_PROJECT = {
    "slug": "history",
    "title": "Исторический",
    "description": "Проект в историческом стиле для тестирования тем",
}

HISTORICAL_TOKENS = {
    # Поверхности — светлый тёплый алебастр (Neoclassic / Editorial)
    "bg-base": "#FBF9F6",
    "bg-surface": "#F3F0EA",
    "bg-surface-2": "#EAE5DE",
    "bg-hover": "#EAE5DE",
    "bg-overlay": "rgba(44, 39, 36, 0.5)",

    # Границы
    "border-main": "#D4CFC9",
    "border-strong": "#B3A796",
    "border-accent": "#6B2927",

    # Текст — эспрессо/графит
    "text-primary": "#2C2724",
    "text-secondary": "#5C544D",
    "text-muted": "#8A8179",
    "text-on-color": "#FBF9F6",

    # Роли — премиальные винные, изумрудные и золотые оттенки
    "color-primary": "#6B2927",
    "color-primary-soft": "#EBE2E1",
    "color-secondary": "#3E5C76",
    "color-secondary-soft": "#E2EAF1",
    "color-accent": "#B89254",
    "color-accent-soft": "#F2EBE1",
    "color-accent-2": "#7D5C43",
    "color-accent-2-soft": "#EFE7DD",
    "color-success": "#244B3B",
    "color-success-soft": "#DCE6E1",
    "color-warning": "#C9A227",
    "color-warning-soft": "#F5EAC8",
    "color-error": "#873230",
    "color-error-soft": "#EBD8D7",

    # Данные и графики
    "chart-1": "#6B2927",
    "chart-2": "#244B3B",
    "chart-3": "#B89254",
    "chart-4": "#3B5C7D",
    "chart-5": "#7D5C43",
    "chart-6": "#4B3230",
    "chart-grid": "rgba(44, 39, 36, 0.08)",
    "chart-axis": "#8A8179",

    # Эффекты
    "gradient-primary": "linear-gradient(135deg, #6B2927 0%, #873230 100%)",
    "gradient-accent": "linear-gradient(135deg, #B89254 0%, #CFA765 100%)",
    "gradient-hero": "radial-gradient(120% 100% at 50% 20%, #FFFFFF 0%, #FBF9F6 60%, #EAE5DE 100%)",
    "gradient-surface": "linear-gradient(160deg, #FBF9F6 0%, #F3F0EA 100%)",
    "gradient-text": "linear-gradient(90deg, #6B2927 0%, #B89254 100%)",
    "gradient-chart": "linear-gradient(180deg, rgba(107,41,39,0.3) 0%, rgba(107,41,39,0) 100%)",
    "glow-primary": "0 0 24px rgba(107, 41, 39, 0.2)",
    "glow-accent": "0 0 24px rgba(184, 146, 84, 0.2)",
    "shadow-color": "rgba(44, 39, 36, 0.1)",
    "glass-bg": "rgba(243, 240, 234, 0.7)",
    "pattern-bg": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E\")",
    "bg-overlay-light": "rgba(255, 255, 255, 0.6)",

    # Состояния (на светлой теме — темнее/насыщеннее)
    "color-primary-strong": "#4A1B1A",
    "color-secondary-strong": "#2A4157",
    "color-accent-strong": "#8E6F3A",
    "color-accent-2-strong": "#5E4530",
    "color-success-strong": "#173428",
    "color-warning-strong": "#A8851A",
    "color-error-strong": "#5E2120",
    "text-on-primary": "#FBF9F6",
    "text-on-accent": "#FBF9F6",

    # Алиасы читаемости
    "color-danger": "#873230",
    "color-danger-soft": "#EBD8D7",
    "color-danger-strong": "#5E2120",
    "color-info": "#3E5C76",
    "color-info-soft": "#E2EAF1",
    "color-info-strong": "#2A4157",

    # Шахматные акценты (4 винно-изумрудно-золотых, под бумажную палитру)
    "item-accent-1": "#6B2927",
    "item-accent-2": "#244B3B",
    "item-accent-3": "#B89254",
    "item-accent-4": "#3B5C7D",

    # Шахматные фоны слайдов (бумага: база → светлее → теплее → белый)
    "slide-bg-1": "#FBF9F6",
    "slide-bg-2": "#F3F0EA",
    "slide-bg-3": "#EAE5DE",
    "slide-bg-4": "#FFFFFF",

    # Типографическая шкала (P4): editorial serif — крупнее, с присутствием
    "type-display": "4rem",
    "type-h1": "2.75rem",
    "type-h2": "2rem",
    "type-body": "1.15rem",
    "type-caption": "0.85rem",

    # Шрифты - Cormorant Garamond для элегантности, Inter для чистоты интерфейса
    "font-sans": '"Inter", sans-serif',
    "font-heading": '"Cormorant Garamond", Georgia, serif',
    "font-mono": '"Space Mono", "Courier New", monospace',
    "font_link": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Space+Mono:wght@400;700&display=swap",

    # Алиасы (Оставлены для совместимости)
    "brand-blue": "#6B2927",
    "brand-light-blue": "#3E5C76",
    "brand-green": "#244B3B",
    "brand-amber": "#B89254",
    "brand-orange": "#6B2927",
    "brand-accent": "#B89254",
    "bg-surface-hover": "#EAE5DE",
}

# ── Проект IT2B: точечные переопределения поверх глобалок ────────────────────
# (глобалки И ЕСТЬ стиль it2b; сюда — только то, что не должно течь в другие проекты)
IT2B_PROJECT_SLUG = "it2b"
IT2B_TOKENS = {
    # Глубина фона под стекло: едва заметные glow-пятна, чтобы blur было что преломлять.
    # Держим в скоупе проекта: в бумажной history-теме им не место.
    "bg-image": "radial-gradient(600px 400px at 15% 8%, rgb(56 189 248 / 0.07), transparent 70%), radial-gradient(700px 500px at 85% 92%, rgb(37 99 235 / 0.08), transparent 70%)",
}

# ── Третий проект «Экопоселение» ───────────────────────────────────────────
DEREVNYA_PROJECT = {
    "slug": "derevnya",
    "title": "Экопоселение",
    "description": "Экостиль FLACON (Природная гамма, Outfit + Lora)",
}

DEREVNYA_TOKENS = {
    # Поверхности
    "bg-base": "#FFFFFF",
    "bg-image": "radial-gradient(circle at 15% 0%, rgba(255, 209, 102, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(162, 212, 144, 0.12) 0%, transparent 60%), radial-gradient(circle at 80% 40%, rgba(255, 140, 0, 0.05) 0%, transparent 50%), radial-gradient(circle at 0% 100%, rgba(255, 179, 71, 0.10) 0%, transparent 60%)",
    "bg-overlay": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E\")",
    "bg-overlay-opacity": "0.02",
    "bg-surface": "rgba(255, 255, 255, 0.92)",
    "bg-surface-2": "rgba(255, 248, 235, 0.8)",
    "bg-surface-hover": "rgba(201, 122, 30, 0.04)",
    "bg-hover": "rgba(201, 122, 30, 0.04)",
    # Уютный SVG-фон (солнце + холмы, bottom center через движок)
    # Уютный лес собирается генератором (см. gen_forest_bg.py) — не инлайнить
    "bg-decorations": FOREST_URI,
    "bg-decorations-size": "100% auto",

    # Границы
    "border-main": "rgba(216, 123, 34, 0.15)",
    "border-strong": "rgba(74, 96, 56, 0.2)",
    "border-accent": "#D87B22",

    # Текст
    "text-primary": "#2C211A",
    "text-secondary": "#6B5B50",
    "text-muted": "rgba(44, 33, 26, 0.5)",
    "text-on-color": "#FFFFFF",

    # Основные цвета (Sunset & Forest)
    "color-primary": "#D87B22",
    "color-primary-soft": "rgba(216, 123, 34, 0.15)",
    "color-secondary": "#4A6038",
    "color-secondary-soft": "rgba(74, 96, 56, 0.15)",
    "color-accent": "#E89538",
    "color-accent-soft": "rgba(232, 149, 56, 0.15)",
    "color-accent-2": "#384A2A",
    "color-accent-2-soft": "rgba(56, 74, 42, 0.15)",
    "color-success": "#4A6038",
    "color-success-soft": "rgba(74, 96, 56, 0.15)",
    "color-warning": "#F0B048",
    "color-warning-soft": "rgba(240, 176, 72, 0.15)",
    "color-error": "#FF4D4F",
    "color-error-soft": "rgba(255, 77, 79, 0.15)",

    # Насыщенные (для hover/акцентов)
    "color-primary-strong": "#B66318",
    "color-secondary-strong": "#384A2A",
    "color-accent-strong": "#D87B22",
    "color-accent-2-strong": "#2E4024",
    "color-success-strong": "#384A2A",
    "color-warning-strong": "#D87B22",
    "color-error-strong": "#D9363E",
    "text-on-primary": "#FFFFFF",
    "text-on-accent": "#FFFFFF",

    # Алиасы читаемости
    "color-danger": "#FF4D4F",
    "color-danger-soft": "rgba(255, 77, 79, 0.15)",
    "color-danger-strong": "#D9363E",
    "color-info": "#4A6038",
    "color-info-soft": "rgba(74, 96, 56, 0.15)",
    "color-info-strong": "#384A2A",

    # Шахматные акценты (4 природные: sunset/forest/sand/pine)
    "item-accent-1": "#D87B22",
    "item-accent-2": "#4A6038",
    "item-accent-3": "#E89538",
    "item-accent-4": "#5E724F",

    # Шахматные фоны слайдов (природа: белый → крем → персик → лён)
    "slide-bg-1": "#FFFFFF",
    "slide-bg-2": "#FFF8EB",
    "slide-bg-3": "#F5E9D2",
    "slide-bg-4": "#EAE5DE",

    # Цвета графиков
    "chart-1": "#D87B22",
    "chart-2": "#4A6038",
    "chart-3": "#E89538",
    "chart-4": "#5E724F",
    "chart-5": "#F0B048",
    "chart-6": "#2E4024",
    "chart-grid": "rgba(216, 123, 34, 0.15)",
    "chart-axis": "#2C211A",

    # Градиенты и свечения (из FLACON startup.css: sunset/forest/sunlight)
    "gradient-primary": "linear-gradient(135deg, #E89538 0%, #D87B22 100%)",
    "gradient-accent": "linear-gradient(135deg, #F0B048 0%, #E89538 100%)",
    "gradient-surface": "linear-gradient(160deg, #FFFFFF 0%, #FFF8EB 100%)",
    "gradient-hero": "radial-gradient(120% 100% at 50% 20%, #FFFFFF 0%, #FFF8EB 60%, #F5E9D2 100%)",
    "gradient-text": "linear-gradient(90deg, #D87B22 0%, #B66318 100%)",
    "gradient-chart": "linear-gradient(180deg, rgba(216,123,34,0.5) 0%, rgba(216,123,34,0) 100%)",
    "glow-primary": "0 8px 24px rgba(216, 123, 34, 0.25)",
    "glow-accent": "0 12px 30px rgba(44, 33, 26, 0.12)",
    "glass-bg": "rgba(255, 255, 255, 0.6)",

    # Типографическая шкала (P4): мягко крупнее tech
    "type-display": "3.25rem",
    "type-h1": "2.5rem",
    "type-h2": "1.85rem",
    "type-body": "1.125rem",
    "type-caption": "0.8rem",

    # Шрифты
    "font-sans": '"Outfit", sans-serif',
    "font-heading": '"Lora", serif',
    "font-mono": '"Space Grotesk", sans-serif',
    "font_link": "https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=Outfit:wght@300;400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap",

    # Алиасы
    "brand-blue": "#D87B22",
    "brand-light-blue": "#E89538",
    "brand-green": "#4A6038",
    "brand-amber": "#F0B048",
    "brand-orange": "#D87B22",
    "brand-accent": "#384A2A",
    "bg-surface-hover": "rgba(201, 122, 30, 0.04)",
}


def _seed_tokens(db, scope_project_id, tokens, force=False):
    """P0-конвенция: по умолчанию только досеиваем отсутствующие ключи.
    Кастомы (is_custom) не трогаем никогда. Значения managed-ключей — только с force=True."""
    for key, value in tokens.items():
        existing = db.query(models.DesignToken).filter(
            models.DesignToken.project_id == scope_project_id,
            models.DesignToken.presentation_id.is_(None),
            models.DesignToken.slide_id.is_(None),
            models.DesignToken.token_key == key,
        ).first()
        if existing:
            if getattr(existing, "is_custom", False):
                continue  # кастом пользователя — сид не трогает никогда
            if force:
                existing.value = value
                existing.is_custom = False
            # без --force: значение не трогаем (ручная доводка переживает пересев)
        else:
            db.add(models.DesignToken(
                project_id=scope_project_id,
                token_key=key,
                token_type=_infer_token_type(key),
                value=value,
                is_custom=False,
            ))


def run(force=False):
    models.Base.metadata.create_all(bind=engine)

    # Миграция без alembic: колонка is_custom для существующих БД
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE design_tokens ADD COLUMN IF NOT EXISTS is_custom BOOLEAN DEFAULT FALSE"
        )

    db = SessionLocal()
    try:
        # 1. Глобальные дефолты (IT2B)
        _seed_tokens(db, None, GLOBAL_TOKENS, force=force)
        print(f"Глобальные токены: {len(GLOBAL_TOKENS)} (стиль IT2B)")

        # 1b. Точечные переопределения IT2B (не должны течь в другие проекты)
        it2b = db.query(models.Project).filter(models.Project.slug == IT2B_PROJECT_SLUG).first()
        if it2b:
            _seed_tokens(db, it2b.id, IT2B_TOKENS, force=force)
            print(f"Токены проекта it2b: {len(IT2B_TOKENS)}")

        # 2. Проект «Исторический»
        project = db.query(models.Project).filter(models.Project.slug == HISTORICAL_PROJECT["slug"]).first()
        if not project:
            project = models.Project(**HISTORICAL_PROJECT)
            db.add(project)
            db.flush()
            print(f"Создан проект «{project.title}» (id={project.id})")
        else:
            print(f"Проект «{project.title}» уже есть (id={project.id})")

        _seed_tokens(db, project.id, HISTORICAL_TOKENS, force=force)
        print(f"Токены проекта history: {len(HISTORICAL_TOKENS)}")

        # 3. Проект «Экопоселение» (Derevnya)
        project3 = db.query(models.Project).filter(models.Project.slug == DEREVNYA_PROJECT["slug"]).first()
        if not project3:
            project3 = models.Project(**DEREVNYA_PROJECT)
            db.add(project3)
            db.flush()
            print(f"Создан проект «{project3.title}» (id={project3.id})")
        else:
            print(f"Проект «{project3.title}» уже есть (id={project3.id})")

        _seed_tokens(db, project3.id, DEREVNYA_TOKENS, force=force)
        print(f"Токены проекта derevnya: {len(DEREVNYA_TOKENS)}")

        db.commit()
        print("Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Сид токенов. По умолчанию только досеивает отсутствующие; --force перезаписывает значения managed-ключей.")
    ap.add_argument("--force", action="store_true", help="Перезаписать значения managed-ключей из файла (кастомы не трогает никогда)")
    run(force=ap.parse_args().force)
