"""
Общий хелпер: гарантирует наличие derived-колонок у таблицы components.

Модель Component описывает колонки payload_schema / example / manifest,
но на существующей БД (восстановленной из дампа или после re-seed)
эти колонки могут отсутствовать. Все derived-генераторы вызывают ensure_columns()
перед обращением к models.Component, чтобы не падать на отсутствующей колонке.
"""
from backend.database import engine
from sqlalchemy import text

DERIVED_COLUMNS = {
    "payload_schema": "JSON",
    "example": "JSON",
    "manifest": "TEXT",
}


def ensure_columns():
    with engine.connect() as conn:
        for col, typ in DERIVED_COLUMNS.items():
            conn.execute(text(f"ALTER TABLE components ADD COLUMN IF NOT EXISTS {col} {typ}"))
        conn.commit()
