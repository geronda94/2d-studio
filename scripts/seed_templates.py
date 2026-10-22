"""
Сид витрины библиотеки палитр (UX-2): отдельные template-* проекты.

Почему отдельные, а не флаг на it2b/history/derevnya: пользовательские правки
рабочих проектов не должны течь в витрину. Источники: global (tech), history,
derevnya. P0-конвенция: кастомы не трогаем, managed обновляем из файла.

Запуск: python scripts/seed_templates.py [--force]
"""
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from scripts.seed_tokens import (
    GLOBAL_TOKENS, IT2B_TOKENS, HISTORICAL_TOKENS, DEREVNYA_TOKENS, _infer_token_type,
)


TEMPLATES = {
    "template-tech": {
        "title": "IT2B · Технический (шаблон)",
        "description": "Тёмная tech-палитра для витрины. Берите себе кнопкой «Взять себе».",
        # tech-палитра = global + точечный оверрайд it2b (glow bg-image), иначе витрина врёт
        "tokens": {**GLOBAL_TOKENS, **IT2B_TOKENS},
    },
    "template-history": {
        "title": "История · Классика (шаблон)",
        "description": "Бумажная editorial-палитра для витрины.",
        "tokens": HISTORICAL_TOKENS,
    },
    "template-derevnya": {
        "title": "Деревня · Эко (шаблон)",
        "description": "Природная палитра с лесом для витрины.",
        "tokens": DEREVNYA_TOKENS,
    },
}


def run(force=False):
    models.Base.metadata.create_all(bind=engine)

    # Миграция без alembic
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE"
        )
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS default_variant VARCHAR"
        )
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS palette_source VARCHAR"
        )
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id INTEGER")
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS parent_id INTEGER")
        conn.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS brief JSON")

    db = SessionLocal()
    try:
        for slug, data in TEMPLATES.items():
            project = db.query(models.Project).filter(
                models.Project.slug == slug).first()
            if not project:
                project = models.Project(
                    slug=slug, title=data["title"],
                    description=data["description"], is_template=True)
                db.add(project)
                db.flush()
                print(f"Создан шаблон «{slug}»")
            else:
                project.title = data["title"]
                project.description = data["description"]
                project.is_template = True
            created, updated, skipped = 0, 0, 0
            for key, value in data["tokens"].items():
                existing = db.query(models.DesignToken).filter(
                    models.DesignToken.project_id == project.id,
                    models.DesignToken.presentation_id.is_(None),
                    models.DesignToken.slide_id.is_(None),
                    models.DesignToken.token_key == key,
                ).first()
                if existing:
                    if getattr(existing, "is_custom", False) and not force:
                        skipped += 1
                        continue
                    existing.value = value
                    existing.is_custom = False
                    updated += 1
                else:
                    db.add(models.DesignToken(
                        project_id=project.id,
                        token_key=key,
                        token_type=_infer_token_type(key),
                        value=value,
                        is_custom=False,
                    ))
                    created += 1
            print(f"«{slug}»: +{created} ~{updated} skip-custom {skipped}")
        db.commit()
        print("Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Сид витрины палитр.")
    ap.add_argument("--force", action="store_true",
                    help="Перезаписать и кастомные токены шаблонов")
    run(force=ap.parse_args().force)
