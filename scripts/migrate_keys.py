"""
Миграция ключей (Итерация 1.1b): переименование ключей данных.

Применяет RENAME_MAP рекурсивно к:
  - components.default_payload
  - slide_data.payload
Затем нужно перезапустить generate_schemas.py (или запустить этот скрипт
вместе с ним) — схемы пересоберутся уже по новым именам.

Запуск: python scripts/migrate_keys.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend import models

# camelCase -> snake_case (унификация стиля ключей)
RENAME_MAP = {
    "baseColor": "base_color",
    "peakColor": "peak_color",
    "resultBase": "result_base",
    "resultLabel": "result_label",
    "resultSuffix": "result_suffix",
    "totalMs": "total_ms",
    "startMs": "start_ms",
    "durationMs": "duration_ms",
}


def rename_keys(obj):
    if isinstance(obj, dict):
        return {RENAME_MAP.get(k, k): rename_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rename_keys(v) for v in obj]
    return obj


def run():
    db = SessionLocal()
    try:
        comps = db.query(models.Component).all()
        for c in comps:
            if c.default_payload:
                c.default_payload = rename_keys(c.default_payload)

        slides = db.query(models.SlideData).all()
        for sd in slides:
            if sd.payload:
                sd.payload = rename_keys(sd.payload)

        db.commit()
        print(f"Ключи переименованы: {len(comps)} компонентов, {len(slides)} слайдов.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
