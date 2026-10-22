"""
Сид вариантов отрисовки (типизация, Фаза 2.3).

Единый JSON-config описывает, КАК рисуются части компонентов:
  - item:    айтемы/ноды (тип фона solid|gradient|blur|transparent, радиус, тень, рамка, отступы)
  - line:    линии соединений (цвет, стиль solid|dashed|dotted, ширина, анимация none|dash|particles|pulse|solid)
  - surface: фон контейнера

Цвета ссылаются на ключи токенов темы (bg-surface, brand-light-blue, ...),
поэтому вариант ложится поверх любой палитры (IT2B / историческая / ...).

Запуск: python scripts/seed_variants.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models


VARIANTS = {
    "tech": {
        "name": "Технический",
        "description": "Современный tech-стиль: стеклянные карточки с blur, анимированные штрих-линии.",
        "config": {
            "item": {
                "bg": {"type": "solid", "value": "bg-surface"},
                "border": {"width": 1, "style": "solid", "color": "border-main"},
                "radius": "16px",
                "shadow": "0 8px 24px rgb(0 0 0 / 0.25)",
                "spacing": {"padding": "12px", "gap": "8px"},
            },
            "item_primary": {
                "bg": {"type": "solid", "value": "bg-surface"},
                "border": {"width": 1, "style": "solid", "color": "border-main"},
                "radius": "16px",
                "shadow": "none",
                "spacing": {"padding": "16px", "gap": "8px"},
            },
            "line": {"style": "dashed", "width": 2, "animation": "dash"},
            # Ритм анимаций (P3): дефолты = текущие хардкоды компонентов.
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            "surface": {"bg": {"type": "solid", "value": "bg-base"}},
            "components": {
                # tech — сплошные карточки, но схема остаётся стеклянной (спека §10.1).
                "ArchitectureDiagram": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface", "opacity": 0.7, "blur": "16px"}},
                },
                "TerminalMockup": {
                    "item": {"bg": {"type": "solid", "value": "bg-surface-hover"}},
                },
                "CodeExplain": {
                    "item": {"bg": {"type": "solid", "value": "bg-surface-hover"}},
                },
                "BrowserMockup": {
                    "item": {"bg": {"type": "solid", "value": "bg-surface-hover"}},
                },
            },
        },
    },
    "classic": {
        "name": "Классический (Editorial)",
        "description": "Премиальный журнальный стиль: элегантные тени, тонкие рамки, изящная типографика.",
        "config": {
            "item": {
                "bg": {"type": "solid", "value": "bg-surface"},
                "border": {"width": 1, "style": "solid", "color": "border-main"},
                "radius": "8px",
                "shadow": "0 16px 40px rgba(44, 39, 36, 0.08)",
                "spacing": {"padding": "16px", "gap": "10px"},
            },
            "item_primary": {
                "bg": {"type": "solid", "value": "bg-surface-2"},
                "border": {"width": 1, "style": "solid", "color": "border-strong"},
                "radius": "8px",
                "shadow": "0 20px 48px rgba(44, 39, 36, 0.12)",
                "spacing": {"padding": "20px", "gap": "12px"},
            },
            "line": {"style": "solid", "width": 1, "animation": "none"},
            # Ритм анимаций (P3): дефолты = текущие хардкоды компонентов.
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            "surface": {"bg": {"type": "solid", "value": "bg-base"}},
            "components": {
                "ArchitectureDiagram": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface", "opacity": 0.8, "blur": "12px"}},
                },
            },
        },
    },
    "industrial": {
        "name": "Индустриальный",
        "description": "Резкий механический стиль: острые углы, толстые линии, минимум декора.",
        "config": {
            "item": {
                "bg": {"type": "solid", "value": "bg-surface"},
                "border": {"width": 2, "style": "solid"},
                "radius": "0px",
                "shadow": "none",
                "spacing": {"padding": "14px", "gap": "10px"},
            },
            "line": {"style": "solid", "width": 3, "animation": "solid"},
            # Ритм анимаций (P3): дефолты = текущие хардкоды компонентов.
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            "surface": {"bg": {"type": "solid", "value": "bg-base"}},
        },
    },
    "educational": {
        "name": "Обучающий",
        "description": "Дружелюбный стиль: мягкий градиент, крупные скругления, частицы в линиях.",
        "config": {
            "item": {
                "bg": {"type": "gradient", "from": "bg-surface", "to": "bg-surface-hover", "angle": 135},
                "border": {"width": 1, "style": "solid"},
                "radius": "20px",
                "shadow": "0 6px 16px rgb(0 0 0 / 0.10)",
                "spacing": {"padding": "14px", "gap": "12px"},
            },
            "line": {"style": "dashed", "width": 2, "animation": "particles"},
            # Ритм анимаций (P3): дефолты = текущие хардкоды компонентов.
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            "surface": {"bg": {"type": "solid", "value": "bg-base"}},
        },
    },
    "derevnya": {
        "name": "Экостиль (Derevnya)",
        "description": "Природная гармония: мягкие формы, воздушные тени и растительные акценты.",
        "config": {
            "item": {
                "bg": {"type": "solid", "value": "bg-surface"},
                "border": {"width": 1, "style": "solid", "color": "border-main"},
                "radius": "16px",
                "shadow": "0 16px 40px rgba(44, 33, 26, 0.06)",
                "spacing": {"padding": "16px", "gap": "10px"},
            },
            "item_primary": {
                "bg": {"type": "solid", "value": "bg-surface-2"},
                "border": {"width": 1, "style": "solid", "color": "border-strong"},
                "radius": "24px",
                "shadow": "0 24px 60px rgba(44, 33, 26, 0.15)",
                "spacing": {"padding": "24px", "gap": "16px"},
            },
            "line": {"style": "solid", "width": 1, "animation": "none"},
            # Ритм анимаций (P3): дефолты = текущие хардкоды компонентов.
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            # Прозрачный фон слайда: тема derevnya живёт подложкой контейнера
            # (bg-image glow-пятна + bg-decorations лес + noise). Solid перекроет иллюстрацию.
            "surface": {"bg": {"type": "transparent", "value": "bg-base"}},
            "components": {
                "ArchitectureDiagram": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface", "opacity": 0.92, "blur": "12px"}},
                },
            },
        },
    },
    "diademas": {
        "name": "Diademas",
        "description": "Премиальный стиль DIADEMAS: золото на полуночном синем — строгий "
                       "радиус 8px, тонкие рамки, стеклянные акценты и прозрачная поверхность "
                       "(звёздная сцена работает под слайдом).",
        "config": {
            "item": {
                "bg": {"type": "blur", "value": "bg-surface", "opacity": 0.5, "blur": "12px"},
                "border": {"width": 1, "style": "solid", "color": "border-main"},
                "radius": "8px",
                "shadow": "0 8px 24px rgb(0 0 0 / 0.14)",
                "spacing": {"padding": "12px", "gap": "8px"},
            },
            "item_primary": {
                "bg": {"type": "blur", "value": "bg-surface-2", "opacity": 0.6, "blur": "16px"},
                "border": {"width": 1, "style": "solid", "color": "border-strong"},
                "radius": "8px",
                "shadow": "0 12px 32px rgb(0 0 0 / 0.20)",
                "spacing": {"padding": "16px", "gap": "10px"},
            },
            "line": {"style": "solid", "width": 1, "animation": "none"},
            "motion": {"appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000},
            # Прозрачная поверхность: сцена (bg-image → облака → шум) — фон слайда.
            "surface": {"bg": {"type": "transparent", "value": "bg-base"}},
            "components": {
                "ArchitectureDiagram": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface", "opacity": 0.55, "blur": "12px"}},
                },
                # Фуллскрины (код/терминал/браузер) — тоже стекло, но плотнее: читаемость.
                "TerminalMockup": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface-2", "opacity": 0.7, "blur": "10px"}},
                },
                "CodeExplain": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface-2", "opacity": 0.7, "blur": "10px"}},
                },
                "BrowserMockup": {
                    "item": {"bg": {"type": "blur", "value": "bg-surface-2", "opacity": 0.7, "blur": "10px"}},
                },
            },
        },
    },
}


def run(force=False):
    models.Base.metadata.create_all(bind=engine)

    # Миграция без alembic: колонка is_custom для существующих БД
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE style_variants ADD COLUMN IF NOT EXISTS is_custom BOOLEAN DEFAULT FALSE"
        )

    db = SessionLocal()
    try:
        for slug, data in VARIANTS.items():
            existing = db.query(models.StyleVariant).filter(models.StyleVariant.slug == slug).first()
            if existing:
                if getattr(existing, "is_custom", False) and not force:
                    print(f"Пропущен кастомный вариант «{slug}» (перезапись только с --force)")
                    continue
                existing.name = data["name"]
                existing.description = data["description"]
                existing.config = data["config"]
                existing.is_archived = False
                existing.is_custom = False
                print(f"Обновлён вариант «{slug}»")
            else:
                db.add(models.StyleVariant(
                    slug=slug,
                    name=data["name"],
                    description=data["description"],
                    config=data["config"],
                    is_custom=False,
                ))
                print(f"Создан вариант «{slug}»")

        db.commit()
        print(f"Готово: {len(VARIANTS)} вариантов.")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Сид вариантов. По умолчанию досеивает отсутствующие и обновляет managed; кастомы — только с --force.")
    ap.add_argument("--force", action="store_true", help="Перезаписать и кастомные варианты из файла")
    run(force=ap.parse_args().force)
