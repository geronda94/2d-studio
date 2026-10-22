"""
Валидатор payload компонента против его payload_schema.

Проверяет: типы полей, обязательные (required), границы массива (min_items/max_items),
enum-значения и монотонность start_time внутри массивов.

Возвращает список структурированных ошибок:
    [{"path": "nodes[0].title", "type": "missing_required", "message": "..."}, ...]
Пустой список = данные валидны. Ошибки понятны и человеку, и ИИ (для ретрая).
"""
import re
from typing import Any, Dict, List, Optional

# Типы, значения которых — строка
_STRING_TYPES = {
    "text", "long_text", "code", "html", "color", "gradient",
    "image", "video", "audio", "icon", "position",
}

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_TOKEN_KEY = re.compile(r"^[a-z0-9][a-z0-9_\-]*$", re.I)
_ICON = re.compile(r"^[a-z0-9][a-z0-9_\-]*(:[a-z0-9_\-/]+)?$", re.I)
_GRADIENT = re.compile(r"^(linear|radial)-gradient\s*\(", re.I)


def _join(path: str, key: str) -> str:
    if path == "":
        return str(key)
    return f"{path}.{key}"


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _validate_scalar(value: Any, schema: Dict, path: str) -> List[Dict]:
    errors = []
    if _is_empty(value):
        return errors

    stype = schema.get("type")

    if stype == "color":
        if not isinstance(value, str):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалась строка, получен {type(value).__name__}"})
        elif not (_HEX_COLOR.match(value) or _TOKEN_KEY.match(value)
                  or _GRADIENT.match(value) or value.startswith("var(")
                  or value.startswith("rgb(") or value.startswith("rgba(")
                  or value.startswith("color-mix(")):
            # rgb()/rgba()/color-mix() — легитимные CSS-цвета (в т.ч. getColorAlpha);
            # раньше отвергались и ломали строгую валидацию payload.
            errors.append({"path": path, "type": "invalid_format",
                           "message": f"цвет '{value[:60]}': ожидается hex, gradient(...), ключ токена, var(...) или rgb()/rgba()"})
    elif stype == "icon":
        if not isinstance(value, str):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалась строка, получен {type(value).__name__}"})
        elif " " in value or not _ICON.match(value):
            errors.append({"path": path, "type": "invalid_format",
                           "message": f"иконка '{value}': ожидается 'name' или 'prefix:name'"})
    elif stype in ("image", "video", "audio"):
        if not isinstance(value, str):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалась строка, получен {type(value).__name__}"})
        elif value.lstrip().startswith("<"):
            pass  # полиморфное поле content: html вместо медиа (см. AGENTS.md §7)
        elif " " in value:
            errors.append({"path": path, "type": "invalid_format",
                           "message": f"медиа '{value[:60]}': ожидается путь/URL без пробелов"})
    elif stype in _STRING_TYPES:
        if not isinstance(value, str):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалась строка, получен {type(value).__name__}"})
    elif stype in ("number", "integer"):
        # int и float взаимозаменяемы (JSON не различает надёжно)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалось число, получен {type(value).__name__}"})
    elif stype == "boolean":
        if not isinstance(value, bool):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидался boolean, получен {type(value).__name__}"})
    elif stype == "time":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидалось число (мс), получен {type(value).__name__}"})
    elif stype == "enum":
        options = schema.get("options", [])
        if value not in options:
            errors.append({"path": path, "type": "invalid_enum",
                           "message": f"значение '{value}' не входит в допустимые: {options}"})
    return errors


def validate_payload(payload: Any, schema: Dict, path: str = "",
                   strict: bool = False) -> List[Dict]:
    """Рекурсивная валидация payload против схемы.

    strict=True: неизвестные поля и подозрительные значения — тоже ошибки
    (тип unknown_field). По умолчанию выключен ради обратной совместимости.
    Монотонность start_time проверяется всегда (обещано контрактом).
    """
    if not schema or not isinstance(schema, dict):
        return []

    errors = []
    stype = schema.get("type")

    if stype == "object":
        fields = schema.get("fields", {})
        # 1. обязательные поля
        for key, fschema in fields.items():
            if fschema.get("required") and (not isinstance(payload, dict) or _is_empty(payload.get(key))):
                errors.append({"path": _join(path, key), "type": "missing_required",
                               "message": f"поле '{key}' обязательно"})
        # 2. валидация присутствующих полей (неизвестные поля игнорируем — обратная совместимость)
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key in fields:
                    errors += validate_payload(value, fields[key], _join(path, key), strict)
                elif strict:
                    errors.append({"path": _join(path, key), "type": "unknown_field",
                                   "message": f"поле '{key}' отсутствует в схеме"})
        return errors

    if stype == "array":
        if not isinstance(payload, list):
            errors.append({"path": path, "type": "type_mismatch",
                           "message": f"ожидался массив, получен {type(payload).__name__}"})
            return errors

        n = len(payload)
        min_items = schema.get("min_items")
        max_items = schema.get("max_items")
        if min_items is not None and n < min_items:
            errors.append({"path": path, "type": "min_items",
                           "message": f"нужно минимум {min_items} элементов, получено {n}"})
        if max_items is not None and n > max_items:
            errors.append({"path": path, "type": "max_items",
                           "message": f"максимум {max_items} элементов, получено {n}"})

        item_schema = schema.get("item")
        for i, item in enumerate(payload):
            # item_schema None => полиморфный массив (элементы не типизируем)
            if item_schema:
                errors += validate_payload(item, item_schema, f"{path}[{i}]", strict)
        # монотонность start_time (локальное время слайда, мс — см. AGENTS.md §8)
        prev, prev_idx = None, None
        for i, item in enumerate(payload):
            if isinstance(item, dict):
                t = item.get("start_time")
                if isinstance(t, (int, float)) and not isinstance(t, bool):
                    if prev is not None and t < prev:
                        errors.append({
                            "path": f"{path}[{i}].start_time", "type": "non_monotonic_start_time",
                            "message": f"start_time {t} < {prev} из {path}[{prev_idx}] — элементы должны идти по нарастающей"})
                    else:
                        prev, prev_idx = t, i
        return errors

    return _validate_scalar(payload, schema, path)


def validate_component_payload(payload: Any, component, strict: bool = False) -> List[Dict]:
    """Валидация payload против схемы компонента (объект models.Component)."""
    if not component or not component.payload_schema:
        return []
    return validate_payload(payload, component.payload_schema, strict=strict)
