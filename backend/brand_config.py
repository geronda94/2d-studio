"""BRAND KIT: чистые функции конфига проекта (без FastAPI/БД).

Вынесены из роутеров, чтобы тестировать без поднятия приложения и БД.
"""
from __future__ import annotations

import json
import os
import uuid

# Приватные поля контактов не отдаём тем, у кого нет прав на редактирование.
PRIVATE_CONTACT_KEYS = ("email", "phone")

# Секции, которые отдаются публично (для рендера/просмотра) без редакторских прав.
PUBLIC_SECTIONS = ("brand", "defaults", "contacts")

MAX_CONFIG_BYTES = 200_000


def public_config(cfg: dict) -> dict:
    """Публичная (viewer) часть конфига: brand + defaults + контакты без email/phone.
    Деловые настройки (voice/audio) наружу не отдаём."""
    if not isinstance(cfg, dict):
        return {}
    out = {}
    for key in PUBLIC_SECTIONS:
        if key in cfg:
            out[key] = cfg[key]
    contacts = out.get("contacts")
    if isinstance(contacts, dict):
        out["contacts"] = {k: v for k, v in contacts.items()
                           if k not in PRIVATE_CONTACT_KEYS}
    return out


# Секции, которые мержатся рекурсивно (частичное обновление не теряет соседние поля).
_DEEP_SECTIONS = {"brand", "contacts", "voice", "audio", "defaults"}


def _deep_merge(dst: dict, src: dict) -> dict:
    out = dict(dst)
    for k, v in src.items():
        if v is None:
            out.pop(k, None)  # явный null = удалить ключ
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def merge_config(old: dict, body: dict) -> dict:
    """Рекурсивный merge: brand/contacts/voice/audio/defaults мержатся поглубинно
    (частичное обновление сохраняет остальные поля); `null` удаляет ключ.
    Прочие секции заменяются целиком. Бросает ValueError при неверном типе/размере."""
    if not isinstance(body, dict):
        raise ValueError("config должен быть объектом")
    if len(json.dumps(body, ensure_ascii=False)) > MAX_CONFIG_BYTES:
        raise ValueError("config слишком большой")
    merged = dict(old) if isinstance(old, dict) else {}
    for k, v in body.items():
        if k in _DEEP_SECTIONS and isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


SPEECH_DEFAULTS = {
    "voice": "Charon",
    "audio_profile": "A confident and dynamic tech expert with a deep, resonant voice.",
    "style": "Engaging and professional.",
    "pace": "Fast, continuous, and energetic, with absolutely no long pauses.",
    "tone": "Authoritative, convincing, and lively.",
    "scene": "A high-end tech YouTube channel.",
    "temperature": 0.9,
}


def resolve_speech_params(req: dict, config: dict) -> dict:
    """Приоритет для параметров озвучки: запрос → config.voice (BRAND KIT) → встроенный дефолт."""
    voice_cfg = (config or {}).get("voice") or {}
    out = {}
    for k, default in SPEECH_DEFAULTS.items():
        v = (req or {}).get(k)
        if v is None:
            v = voice_cfg.get(k)
        if v is None:
            v = default
        out[k] = v
    try:
        out["temperature"] = float(out["temperature"])
    except (TypeError, ValueError):
        out["temperature"] = 0.9
    return out


def local_media_path(src: str):
    """Локальный путь только для известных схем (/media, /uploads) и существующих
    файлов; иначе None (не скармливаем ffprobe произвольные пути из конфига)."""
    if not src:
        return None
    if src.startswith("/media/"):
        p = src.replace("/media/", "/app/backend/media/")
    elif src.startswith("/uploads/"):
        p = src.replace("/uploads/", "/app/uploads/")
    else:
        return None
    return p if os.path.exists(p) else None


_DURATION_CACHE: dict = {}


def probe_duration_ms(path: str, fallback: int = 0) -> int:
    if not path:
        return fallback
    # Кэш по (путь, mtime) — если файл заменили, длительность пересчитается.
    try:
        cache_key = (path, os.path.getmtime(path))
    except OSError:
        cache_key = (path, 0)
    if cache_key in _DURATION_CACHE:
        return _DURATION_CACHE[cache_key]
    try:
        import subprocess
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, timeout=4,
        )
        dur = int(float(json.loads(out.stdout)["format"]["duration"]) * 1000)
        if dur > 0:
            _DURATION_CACHE[cache_key] = dur
        return dur or fallback
    except Exception:
        return fallback


def seed_bgm_from_config(pres, config, *, path_resolver=local_media_path,
                         duration_probe=probe_duration_ms) -> bool:
    """BRAND KIT: подкладывает фоновую музыку проекта в новую презентацию.
    Возвращает True, если дорожка создана. Битый/отсутствующий файл НЕ сейвит."""
    cfg = config or {}
    audio = cfg.get("audio") or {}
    src = str(audio.get("bgm") or "").strip()
    if not src:
        return False
    local = path_resolver(src)
    if local is None:
        print(f"[brand] BGM '{src}' not found locally — skip seeding", flush=True)
        return False
    dur = duration_probe(local, fallback=0)
    if dur <= 0:
        print(f"[brand] BGM '{src}' duration unknown — skip seeding", flush=True)
        return False
    try:
        vol = float(audio.get("volume", 0.15))
    except (TypeError, ValueError):
        vol = 0.15
    pres.audio_timeline = {"tracks": [
        {"id": "main", "type": "voiceover", "clips": []},
        {"id": "bgm", "type": "bgm", "clips": [{
            "id": "bgm_" + uuid.uuid4().hex[:8],
            "name": os.path.basename(src), "src": src, "type": "audio",
            "start_time": 0, "end_time": dur, "media_offset": 0,
            "volume": vol, "muted": False,
        }]},
    ]}
    return True
