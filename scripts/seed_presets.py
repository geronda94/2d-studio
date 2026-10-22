"""
Сид векторов стилей (P2): style_presets.

Пресет = палитра-проект + вариант + правила. ИИ выбирает пресет, а не комбинирует
свободно. P0-конвенция: кастомы (is_custom) не трогаем никогда; managed обновляем
из файла; удаление — только через API и только custom.

Запуск: python scripts/seed_presets.py [--force]
"""
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models


PRESETS = {
    "it2b-tech": {
        "title": "IT2B · Технический",
        "palette": "it2b",
        "variant": "tech",
        "rules": {"max_accents": 4, "title_em": True},
    },
    "history-classic": {
        "title": "История · Классика",
        "palette": "history",
        "variant": "classic",
        "rules": {"max_accents": 4, "title_em": True},
    },
    "derevnya-eco": {
        "title": "Деревня · Эко",
        "palette": "derevnya",
        "variant": "derevnya",
        "rules": {"max_accents": 4, "title_em": True},
    },
    "diademas-gold": {
        "title": "Diademas · Золото",
        "palette": "template-diademas-dark",
        "variant": "diademas",
        "rules": {"max_accents": 4, "title_em": True},
    },
    "diademas-forest": {
        "title": "Diademas · Лес",
        "palette": "diademas",
        "variant": "diademas",
        "rules": {"max_accents": 4, "title_em": True},
    },
}


def run(force=False):
    models.Base.metadata.create_all(bind=engine)

    # Миграция без alembic: колонки вектора для существующих БД
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS style_preset VARCHAR")
        conn.exec_driver_sql(
            "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS style_lock BOOLEAN DEFAULT FALSE")
        conn.exec_driver_sql(
            "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS chessboard BOOLEAN DEFAULT FALSE")
        conn.exec_driver_sql(
            "ALTER TABLE presentations ADD COLUMN IF NOT EXISTS palette_source VARCHAR")

    db = SessionLocal()
    try:
        for slug, data in PRESETS.items():
            # ссылки целы?
            if data.get("palette") and not db.query(models.Project).filter(
                    models.Project.slug == data["palette"]).first():
                print(f"Пропущен «{slug}»: нет проекта-палитры '{data['palette']}'")
                continue
            if data.get("variant") and not db.query(models.StyleVariant).filter(
                    models.StyleVariant.slug == data["variant"]).first():
                print(f"Пропущен «{slug}»: нет варианта '{data['variant']}'")
                continue
            existing = db.query(models.StylePreset).filter(
                models.StylePreset.slug == slug).first()
            if existing:
                if getattr(existing, "is_custom", False) and not force:
                    print(f"Пропущен кастомный пресет «{slug}» (перезапись только с --force)")
                    continue
                existing.title = data["title"]
                existing.palette = data.get("palette")
                existing.variant = data.get("variant")
                existing.rules = data.get("rules")
                existing.is_archived = False
                existing.is_custom = False
                print(f"Обновлён пресет «{slug}»")
            else:
                db.add(models.StylePreset(
                    slug=slug,
                    title=data["title"],
                    palette=data.get("palette"),
                    variant=data.get("variant"),
                    rules=data.get("rules"),
                    is_custom=False,
                ))
                print(f"Создан пресет «{slug}»")
        db.commit()
        print(f"Готово: {len(PRESETS)} пресетов.")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Сид пресетов стилей.")
    ap.add_argument("--force", action="store_true",
                    help="Перезаписать и кастомные пресеты из файла")
    run(force=ap.parse_args().force)
