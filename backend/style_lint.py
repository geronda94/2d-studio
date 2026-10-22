"""
Style-lint payload: вкусовые проверки поверх схемы (`validation.py`).

Возвращает warnings (НЕ блокируют сохранение, светятся в редакторе):
    [{"path": "items[2].start_time", "type": "dense_timing", "message": "..."}, ...]

Правила v1 (см. docs/STYLE_FLEX_PLAN.md P1):
- no-hex: поле типа `color` со значением `#...` → warning (только типизированные поля;
  `code`/`html`/`long_text` не трогаем — там hex подсветки синтаксиса легитимен).
- accent-budget: distinct акцентов (`color`/`*_color` кроме `border_*`/`btn_*`/`bg_*`)
  больше MAX_ACCENTS (4 = шахматка) → один warning.
- density: шаг `start_time` между соседними айтемами < MIN_DENSITY_MS (800, AGENTS.md §8.3).
  gap == 0 (намеренная синхронность) и InteractiveArchitecture (своя механика) — skip.
- contrast (только slide-уровень, нужна тема): `text-primary` vs фон слайда < 4.5.
"""
import re
from typing import Any, Dict, List, Optional

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_VAR = re.compile(r"^var\(\s*(--[A-Za-z0-9_\-]+)\s*\)$")

MIN_DENSITY_MS = 800
MAX_ACCENTS = 4  # шахматка item-accent-1..4 — максимум; 5+ цветов = warning
MIN_CONTRAST = 4.5

# Фирменные hex логотипов — фиксированы брендом, не темой (Vue/Mongo/Postgres). Не флагаем.
_BRAND_HEX = frozenset({"#42b883", "#009688", "#336791"})
# Плотность не применима: своя механика появления (AGENTS.md §8.3, §4.4).
_SKIP_DENSITY_SLUGS = frozenset({"InteractiveArchitecture"})


def _join(path: str, key: str) -> str:
    return str(key) if path == "" else f"{path}.{key}"


def _norm_accent(value: Any) -> Optional[str]:
    """var(--x) и x считаем одним акцентом; регистр игнорируем."""
    if not isinstance(value, str):
        return None
    v = value.strip()
    m = _VAR.match(v)
    if m:
        v = m.group(1).lstrip("-")
    return v.lower() or None


def _is_accent_key(key: str) -> bool:
    if key == "color":
        return True
    return (key.endswith("_color")
            and not key.startswith(("border_", "btn_", "bg_")))


def _hex_to_rgb(value: str) -> Optional[tuple]:
    m = re.match(r"^#([0-9a-fA-F]{6})$", (value or "").strip())
    if not m:
        return None
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _luminance(rgb: tuple) -> float:
    def ch(c: int) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast_ratio(a: str, b: str) -> Optional[float]:
    ra, rb = _hex_to_rgb(a), _hex_to_rgb(b)
    if not ra or not rb:
        return None
    la, lb = _luminance(ra), _luminance(rb)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


def _token_value(tokens: Dict, key: str) -> Optional[str]:
    """Значение токена из мержа (формат _merge_tokens: {key: {key,type,value}})."""
    if not tokens or not isinstance(tokens, dict):
        return None
    tok = tokens.get(key)
    if tok is None:
        return None
    if isinstance(tok, dict):
        return tok.get("value")
    return tok if isinstance(tok, str) else None


def _resolve_var(value: Any, tokens: Dict) -> Any:
    """Резолв var(--X) и голого ключа X через токены; остальное как есть."""
    if not isinstance(value, str):
        return value
    v = value.strip()
    m = _VAR.match(v)
    if m:
        return _token_value(tokens, m.group(1).lstrip("-")) or value
    if tokens and isinstance(tokens, dict) and v in tokens:
        return _token_value(tokens, v) or value
    return value


def _collect_accents(payload: Any, schema: Dict, path: str = "") -> Dict[str, str]:
    """norm accent -> first path. Используется и warnings, и preset-errors."""
    accents: Dict[str, str] = {}

    def walk(node: Any, node_schema: Dict, p: str):
        if not isinstance(node_schema, dict):
            return
        stype = node_schema.get("type")
        if stype == "object":
            if not isinstance(node, dict):
                return
            for key, value in node.items():
                fschema = node_schema.get("fields", {}).get(key)
                if fschema is None:
                    continue
                if _is_accent_key(key):
                    norm = _norm_accent(value)
                    if norm and norm not in accents:
                        accents[norm] = _join(p, key)
                walk(value, fschema, _join(p, key))
        elif stype == "array":
            if not isinstance(node, list):
                return
            item_schema = node_schema.get("item")
            if item_schema:
                for i, item in enumerate(node):
                    walk(item, item_schema, f"{p}[{i}]")

    walk(payload, schema or {}, path)
    return accents


def lint_payload(payload: Any, schema: Dict, path: str = "",
                 component_slug: Optional[str] = None) -> List[Dict]:
    """Правила no-hex / accent-budget / density. Чистый обход payload+schema."""
    warnings: List[Dict] = []

    def walk(node: Any, node_schema: Dict, p: str):
        if not isinstance(node_schema, dict):
            return
        stype = node_schema.get("type")
        if stype == "object":
            if not isinstance(node, dict):
                return
            for key, value in node.items():
                fschema = node_schema.get("fields", {}).get(key)
                if fschema is None:
                    continue
                ftype = fschema.get("type")
                if (ftype == "color" and isinstance(value, str)
                        and _HEX.match(value.strip())
                        and value.strip().lower() not in _BRAND_HEX):
                    warnings.append({
                        "path": _join(p, key), "type": "no-hex",
                        "message": f"hex '{value}': используй токен (var(--item-accent-N)/var(--color-*)) — правки темы применятся автоматически"})
                walk(value, fschema, _join(p, key))
        elif stype == "array":
            if not isinstance(node, list):
                return
            item_schema = node_schema.get("item")
            if item_schema:
                for i, item in enumerate(node):
                    walk(item, item_schema, f"{p}[{i}]")
            # плотность start_time (AGENTS.md §8.3: шаг ≥ 800мс)
            prev = None
            check_density = component_slug not in _SKIP_DENSITY_SLUGS
            for i, item in enumerate(node):
                if not isinstance(item, dict):
                    continue
                t = item.get("start_time")
                if isinstance(t, (int, float)) and not isinstance(t, bool):
                    gap = (t - prev) if prev is not None else None
                    # gap == 0 — намеренная синхронность (появляются вместе), не флаговать
                    if check_density and gap is not None and 0 < gap < MIN_DENSITY_MS:
                        warnings.append({
                            "path": f"{p}[{i}].start_time", "type": "dense_timing",
                            "message": f"шаг {int(gap)}мс < {MIN_DENSITY_MS}мс — анимации не успеют отыграть и наслоятся (§8.3)"})
                    if prev is None or t >= prev:
                        prev = t

    walk(payload, schema or {}, path)
    accents = _collect_accents(payload, schema, path)
    if len(accents) > MAX_ACCENTS:
        shown = ", ".join(f"{v} ({k})" for k, v in list(accents.items())[:6])
        warnings.append({
            "path": path, "type": "accent-budget",
            "message": f"акцентов {len(accents)} > {MAX_ACCENTS} ({shown}) — максимум шахматка item-accent-1..4"})
    return warnings


def lint_preset(payload: Any, schema: Dict, title: Any, effective_variant: Optional[str],
                rules: Optional[Dict], path: str = "") -> List[Dict]:
    """Проверка вектора пресета — ERRORS (блокируют save залоченной презентации).
    rules: {"variant": slug, "max_accents": int, "title_em": bool}."""
    errors: List[Dict] = []
    rules = rules or {}
    want_variant = rules.get("variant")
    if want_variant and effective_variant and effective_variant != want_variant:
        errors.append({
            "path": "variant", "type": "wrong-variant",
            "message": f"вариант '{effective_variant}' вне вектора пресета (нужен '{want_variant}')"})
    max_accents = rules.get("max_accents")
    if max_accents is not None and schema:
        accents = _collect_accents(payload, schema, path)
        if len(accents) > int(max_accents):
            shown = ", ".join(f"{v} ({k})" for k, v in list(accents.items())[:6])
            errors.append({
                "path": path, "type": "accent-budget",
                "message": f"акцентов {len(accents)} > {max_accents} ({shown}) — вектор пресета"})
    if rules.get("title_em") and isinstance(title, str) and title.strip():
        import re as _re
        if not _re.search(r"<em[\s>]", title):
            errors.append({
                "path": "title", "type": "title-em",
                "message": "вектор пресета требует <em> в заголовке (акцентная часть)"})
    return errors


def lint_slide_contrast(title: Any, tokens: Dict, surface_bg: Any) -> List[Dict]:
    """Контраст заголовка (text-primary) vs фон слайда. Без темы/hex — молча skip."""
    text = (title or "")
    if not isinstance(text, str) or not text.strip():
        return []
    text_val = _token_value(tokens, "text-primary") or "#FFFFFF"
    surf_val = _resolve_var(surface_bg, tokens)
    if not isinstance(surf_val, str):
        return []
    # прозрачный surface (derevnya) → виден контейнер bg-base
    if surf_val.strip().lower() == "transparent":
        surf_val = _token_value(tokens, "bg-base") or surf_val
    ratio = _contrast_ratio(text_val, surf_val)
    if ratio is None or ratio >= MIN_CONTRAST:
        return []
    return [{
        "path": "title", "type": "low-contrast",
        "message": f"контраст заголовка {ratio:.1f} < {MIN_CONTRAST} (text-primary vs фон) — текст будет нечитаемым"}]
