"""
Генератор payload_schema для компонентов.

Итерация 1.1 (bootstrap): автоматически выводит схему (тип каждого поля)
из default_payload каждого компонента по явным правилам. Результат — поле
`payload_schema` в таблице components. Схему в дальнейшем уточняем вручную.

Запуск (внутри backend-контейнера):
    python scripts/generate_schemas.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from sqlalchemy import text
from scripts._ensure_columns import ensure_columns

# ── Канонические типы полей ────────────────────────────────────────────────
# text       — однострочный текст
# long_text  — многострочный текст (textarea)
# code       — код/терминал (моноширинный многострочный)
# html       — сырой HTML
# number     — число (float)
# boolean    — переключатель
# color      — hex-цвет (пипетка + палитра)
# gradient   — градиент (CSS linear-gradient)
# image      — картинка (медиа-библиотека)
# video      — видео (медиа-библиотека)
# audio      — аудио (медиа-библиотека)
# icon       — иконка (иконка-пикер)
# time       — время в мс (тайм-пикер)
# position   — позиция "x% y%"
# enum       — выбор из списка (с `options`)
# array      — массив (с `item`)
# object     — вложенный объект (с `fields`)

TIME_KEYS = {
    "start_time", "starttime", "duration", "delay", "total_start_time",
    "startms", "durationms", "totalms",  # camelCase (legacy)
    "start_ms", "duration_ms", "total_ms",  # snake_case (новый канон)
    "zoom_duration", "scroll_duration",
    "trim_start", "trim_end", "time",
}
COLOR_KEYS = {
    "color", "base_color", "peak_color", "field_color", "btn_color",
    "btn_text_color", "accent_color", "border_color", "fill", "stroke",
    "basecolor", "peakcolor",
    "lamp_color", "flame_color",
}
GRADIENT_KEYS = {"gradient"}
ICON_KEYS = {"icon", "field_icon", "btn_icon"}
IMAGE_KEYS = {"image", "avatar", "logo", "photo", "bg", "background", "media_url", "src", "img", "qr_code"}
VIDEO_KEYS = {"video", "video_url", "media"}
AUDIO_KEYS = {"audio", "audio_src"}
POSITION_KEYS = {"object_position", "target_position", "image_position", "position"}
LONG_TEXT_KEYS = {
    "desc", "description", "details", "text",
    # Roadmap P2/P3/P4 — длинные смысловые поля (textarea в редакторе)
    "definition", "explanation", "quote", "back", "practice", "result",
    "impact", "event",
}
CODE_KEYS = {"code", "cmd", "output"}
# Полиморфное поле: картинка ИЛИ html, зависит от соседнего `type` (BrowserMockup).
# Типим как image (дефолтный случай), а редактор обрабатывает обе ветки спец-кейсом.
POLYMORPHIC_IMAGE_KEYS = {"content"}

# Полиморфные массивы: элементы могут быть разного типа (строка ИЛИ объект и т.п.),
# поэтому их содержимое не типизируем строго, а min_items = 0 (массив опционален).
PERMISSIVE_ARRAYS = {"to", "values"}

ENUM_OPTIONS = {
    "role": ["user", "bot", "assistant"],
    "sender": ["user", "bot", "assistant"],
    "align": ["left", "center", "right"],
    "size": ["1x1", "1x2", "2x1", "2x2", "3x2", "4x2"],
    "frame": ["browser", "mobile", "none"],
    "layout": ["horizontal", "vertical"],
    "lamp_side": ["left", "right"],
    # Roadmap P3/P4
    "transition_style": ["slide", "fade", "wipe"],
    "color_scheme": ["neutral", "warm", "cool"],
    # Roadmap V2 — Tier 0 primitives
    "scale": ["rag", "irms", "bloom", "custom"],
    "notation": ["irms", "rag", "bloom", "dok", "custom"],
    "density": ["compact", "comfortable", "board"],
    "flow_layout": ["layered", "radial", "coords"],
}


def infer_scalar_type(key: str, value) -> str:
    k = key.lower()

    if k in TIME_KEYS:
        return "time"
    if k in GRADIENT_KEYS:
        return "gradient"
    if k in POLYMORPHIC_IMAGE_KEYS:
        return "image"
    if k in COLOR_KEYS:
        return "color"
    if k in ICON_KEYS:
        return "icon"
    if k in AUDIO_KEYS:
        return "audio"
    if k in VIDEO_KEYS:
        return "video"
    if k in IMAGE_KEYS:
        return "image"
    if k in POSITION_KEYS:
        return "position"
    if k in ENUM_OPTIONS:
        return "enum"
    if k in CODE_KEYS:
        return "code"
    if k in LONG_TEXT_KEYS:
        return "long_text"

    # по типу значения
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, float):
        return "number"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, str):
        return "text"
    return "text"


def build_schema(obj):
    """Рекурсивно строит схему по образцу значения."""
    if isinstance(obj, list):
        item = obj[0] if obj else None
        n = len(obj)
        if isinstance(item, dict):
            # union ключей по ВСЕМ элементам массива: поля, встречающиеся не в первом
            # элементе (badge/btn_icon/highlight/is_focused), иначе выпадают из схемы
            # и валидатор в strict ругается unknown_field, а редактор/агент их не видит.
            merged = dict(item)
            for extra in obj[1:]:
                if isinstance(extra, dict):
                    for k, v in extra.items():
                        if k not in merged:
                            merged[k] = v
            return {
                "type": "array",
                "min_items": 1,
                "max_items": max(n * 2, 6),
                "item": build_schema(merged),
            }
        if isinstance(item, list):
            return {
                "type": "array",
                "min_items": 1,
                "max_items": max(n * 2, 6),
                "item": build_schema(item),
            }
        return {
            "type": "array",
            "min_items": 1,
            "max_items": max(n * 2, 6),
            "item": {"type": infer_scalar_type("item", item) if item is not None else "text"},
        }
    if isinstance(obj, dict):
        fields = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                if k in PERMISSIVE_ARRAYS and isinstance(v, list):
                    # полиморфный/опциональный массив — не типизируем элементы
                    fields[k] = {
                        "type": "array",
                        "min_items": 0,
                        "max_items": max(len(v) * 2, 6),
                        "item": None,
                    }
                else:
                    fields[k] = build_schema(v)
            else:
                fields[k] = {"type": infer_scalar_type(k, v)}
                if fields[k]["type"] == "enum" and k.lower() in ENUM_OPTIONS:
                    fields[k]["options"] = ENUM_OPTIONS[k.lower()]
        return {"type": "object", "fields": fields}
    return {"type": infer_scalar_type("value", obj)}


def run():
    # 1. Гарантируем наличие derived-колонок (payload_schema, example, manifest)
    ensure_columns()

    db = SessionLocal()
    try:
        comps = db.query(models.Component).all()
        # Доступные варианты отрисовки (типизация, Фаза 2.3) → enum для top-level `variant`.
        variant_slugs = [
            v.slug for v in db.query(models.StyleVariant)
            .filter(models.StyleVariant.is_archived.is_(False))
            .order_by(models.StyleVariant.id)
            .all()
        ]
        for c in comps:
            schema = build_schema(c.default_payload or {})
            # Топ-левел `variant` — это вариант отрисовки (в отличие от вложенного ProductCard.items[].variant).
            if variant_slugs and isinstance(c.default_payload, dict) and "variant" in (c.default_payload or {}):
                fields = schema.setdefault("fields", {})
                if "variant" in fields:
                    fields["variant"] = {"type": "enum", "options": variant_slugs}
            c.payload_schema = schema
            print(f"{c.slug:28s} -> {len(schema.get('fields', {}))} top-level fields")
        db.commit()
        print(f"\nСхемы сгенерированы для {len(comps)} компонентов.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
