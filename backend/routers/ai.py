from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..permissions import enforce_write
from .. import models, schemas
import os
import uuid
import struct
import time
import subprocess
import json
import httpx
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(enforce_write)],
)

MEDIA_DIR = "/app/backend/media" if os.path.exists("/app") else "backend/media"
os.makedirs(MEDIA_DIR, exist_ok=True)

def parse_audio_mime_type(mime_type: str) -> dict:
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except: pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except: pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1,
        num_channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b"data", data_size
    )
    return header + audio_data

@router.post("/presentations/{presentation_id}/generate-speech", response_model=schemas.MediaFile)
def generate_speech(presentation_id: int, request: schemas.GenerateSpeechRequest, db: Session = Depends(get_db)):
    presentation = db.query(models.Presentation).filter(models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")

    # BRAND KIT: если параметр не задан явно — берём голос проекта (config.voice),
    # иначе встроенный дефолт. Так скрипты/пайплайн используют настройки проекта.
    project = None
    for folder in presentation.folders:
        if folder.project_id:
            project = db.query(models.Project).filter(
                models.Project.id == folder.project_id).first()
            break
    from ..brand_config import resolve_speech_params
    sp = resolve_speech_params(request.dict(), getattr(project, "config", None))

    client = genai.Client(api_key=api_key)
    model = "gemini-3.1-flash-tts-preview"
    
    generate_content_config = types.GenerateContentConfig(
        temperature=sp["temperature"],
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=sp["voice"]
                )
            )
        ),
    )

    prompt = f"""Read the following transcript based on the audio profile and director's note.

# Audio Profile
{sp["audio_profile"]}

# Director's note
Style: {sp["style"]} Pace: {sp["pace"]} Tone: {sp["tone"]}

## Scene:
{sp["scene"]}

## Transcript:
{request.text}"""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")

    if not response.candidates:
        raise HTTPException(status_code=500, detail="No output from Gemini API")

    part = response.candidates[0].content.parts[0]
    if part.inline_data and part.inline_data.data:
        pcm_data = part.inline_data.data
        mime_type = part.inline_data.mime_type
    else:
        raise HTTPException(status_code=500, detail="API did not return audio data")

    wav_data = convert_to_wav(pcm_data, mime_type)
    
    unique_filename = f"ai_voice_{uuid.uuid4().hex}.wav"
    file_path = os.path.join(MEDIA_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(wav_data)

    settings = {
        "voice": sp["voice"],
        "audio_profile": sp["audio_profile"],
        "style": sp["style"],
        "pace": sp["pace"],
        "tone": sp["tone"],
        "scene": sp["scene"],
        "temperature": sp["temperature"],
        "batch_id": request.batch_id
    }

    media_file = models.MediaFile(
        presentation_id=presentation_id,
        filename=unique_filename,
        file_type="ai_voice",
        file_path=f"/media/{unique_filename}",
        ai_text=request.text,
        ai_settings=settings
    )
    db.add(media_file)
    db.commit()
    db.refresh(media_file)

    return media_file


# ---------------------------------------------------------------------------
# Audio utilities: duration detection + Whisper transcription
# ---------------------------------------------------------------------------

@router.post("/presentations/{presentation_id}/generate-slides")
def generate_slides(presentation_id: int, request: schemas.GenerateSlidesRequest,
                    db: Session = Depends(get_db)):
    """Генерация слайдов из сценария/брифа (AI_PLATFORM Ф3). Возвращает ПРЕДЛОЖЕНИЕ (ops),
    по умолчанию не применяет. Валидация — через change-set (dry_run), затем опционально apply."""
    from . import presentations as pres_router
    presentation = db.query(models.Presentation).filter(
        models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")

    # Контекст проекта: бриф + каталог компонентов
    project = None
    for folder in presentation.folders:
        if folder.project_id:
            project = db.query(models.Project).filter(models.Project.id == folder.project_id).first()
            break
    brief = request.brief.dict(exclude_unset=True) if request.brief else (getattr(project, "brief", None) if project else None)

    comps = db.query(models.Component).order_by(models.Component.id).all()
    catalog = [{"slug": c.slug, "title": c.title, "manifest": c.manifest,
                "payload_schema": c.payload_schema, "example": c.example} for c in comps]

    prompt = f"""Ты — режиссёр презентаций. Верни СТРОГО JSON без markdown:
{{"ops":[ ... ]}}

Доступные операции:
- add_slide: {{"op":"add_slide","slide_id":"уникальный","component":"slug","start_time":мс,"title":"<em>..</em>","payload":{{...}}}}
- update_slide / delete_slide / set_slide_variant / reorder_slides — при необходимости.

Правила:
- component выбирай по manifest; payload заполняй строго по payload_schema, ориентируясь на example.
- title: ~половина слов в <em>.
- start_time слайдов: шаг >= 2000мс. Внутри payload start_time айтемов: шаг >= 800мс.
- Не добавляй поля вне схемы.

Бриф проекта: {json.dumps(brief, ensure_ascii=False) if brief else "нет"}
Желаемое число слайдов: {request.slide_count or "на твоё усмотрение"}

Задание человека:
{request.script or "Сделай презентацию по брифу"}

Каталог компонентов (slug/manifest/schema/example):
{json.dumps(catalog, ensure_ascii=False)}"""

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash"),
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.6),
        )
        text = (resp.text or "").strip()
        data = json.loads(text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    ops = data.get("ops") if isinstance(data, dict) else None
    if not isinstance(ops, list):
        raise HTTPException(status_code=502, detail="LLM вернул неверный формат (ожидался {'ops':[...]})")

    # Валидация предложения через change-set (dry_run), без записи
    cs = schemas.ChangeSetRequest(ops=[schemas.ChangeOp(**o) for o in ops], dry_run=True)
    check = pres_router.apply_change_set(presentation_id, cs, db)

    applied = False
    if request.apply and check.get("valid"):
        cs_apply = schemas.ChangeSetRequest(ops=[schemas.ChangeOp(**o) for o in ops], dry_run=False)
        check = pres_router.apply_change_set(presentation_id, cs_apply, db)
        applied = True

    return {"ops": ops, "applied": applied,
            "valid": check.get("valid"), "errors": check.get("errors"),
            "warnings": check.get("warnings"), "diff": check.get("diff")}


@router.post("/presentations/{presentation_id}/generate-from-audio")
def generate_from_audio(presentation_id: int, request: schemas.GenerateFromAudioRequest,
                        db: Session = Depends(get_db)):
    """Аудио→слайды (AI_PLATFORM Ф3.2): по сегментам транскрипта (text+тайминги) строит
    слайды, СИНХРОНИЗИРУЯ start_time со стартом сегмента. По умолчанию только предложение."""
    from . import presentations as pres_router
    presentation = db.query(models.Presentation).filter(
        models.Presentation.id == presentation_id).first()
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    segments = [s.dict() for s in (request.segments or [])]
    if not segments:
        # fallback: клипы озвучки таймлайна (текст из media ai_text, если есть)
        tl = presentation.audio_timeline or {}
        tracks = tl.get("tracks") or []
        main = next((t for t in tracks if t.get("id") in ("main", "voiceover")), tracks[0] if tracks else None)
        for c in (main.get("clips") if main else []) or []:
            if c.get("start_time") is not None:
                segments.append({"text": c.get("name") or c.get("text") or "",
                                 "start_ms": c.get("start_time"),
                                 "end_ms": c.get("end_time")})
    if not segments:
        raise HTTPException(status_code=400, detail="Нет сегментов: передайте segments или озвучку в презентации")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")

    project = None
    for folder in presentation.folders:
        if folder.project_id:
            project = db.query(models.Project).filter(models.Project.id == folder.project_id).first()
            break
    brief = getattr(project, "brief", None) if project else None

    comps = db.query(models.Component).order_by(models.Component.id).all()
    catalog = [{"slug": c.slug, "title": c.title, "manifest": c.manifest,
                "payload_schema": c.payload_schema, "example": c.example} for c in comps]

    prompt = f"""Ты — режиссёр. Дан транскрипт озвучки с таймингами (сегменты). Сделай по слайду
на каждый смысловой сегмент. Верни СТРОГО JSON: {{"ops":[{{"op":"add_slide","slide_id":"...",
"component":"slug","start_time":<start_ms сегмента>,"title":"<em>..</em>","payload":{{...}}}}]}}
Число add_slide должно равняться числу сегментов, в том же порядке и с тем же start_time.
component выбирай по manifest; payload — строго по payload_schema/example; title с <em>.

Бриф проекта: {json.dumps(brief, ensure_ascii=False) if brief else "нет"}
Сегменты (порядок и start_ms обязательны):
{json.dumps(segments, ensure_ascii=False)}
Каталог: {json.dumps(catalog, ensure_ascii=False)}"""

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash"),
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.5),
        )
        data = json.loads((resp.text or "").strip())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    ops = data.get("ops") if isinstance(data, dict) else None
    if not isinstance(ops, list):
        raise HTTPException(status_code=502, detail="LLM вернул неверный формат")

    # Жёсткая синхронизация: add_slide[i].start_time = segments[i].start_ms
    adds = [o for o in ops if isinstance(o, dict) and o.get("op") == "add_slide"]
    for i, o in enumerate(adds):
        if i < len(segments):
            o["start_time"] = segments[i].get("start_ms")

    cs = schemas.ChangeSetRequest(ops=[schemas.ChangeOp(**o) for o in ops], dry_run=True)
    check = pres_router.apply_change_set(presentation_id, cs, db)
    if request.apply and check.get("valid"):
        cs_apply = schemas.ChangeSetRequest(ops=[schemas.ChangeOp(**o) for o in ops], dry_run=False)
        check = pres_router.apply_change_set(presentation_id, cs_apply, db)
        check["applied"] = True
    return {"ops": ops, "valid": check.get("valid"), "applied": check.get("applied", False),
            "errors": check.get("errors"), "warnings": check.get("warnings"), "diff": check.get("diff")}


@router.get("/tools")
def get_ai_tools(db: Session = Depends(get_db)):
    """Tool-схемы для function-calling агента (AI_PLATFORM Ф1, read-only).
    Генерируются из каталога компонентов + ops DSL — единый источник правды."""
    ops_dsl = {"add_slide", "update_slide", "delete_slide", "set_slide_variant",
               "set_presentation_variant", "set_tokens", "apply_palette"}
    components = [{"slug": c.slug, "title": c.title, "manifest": c.manifest,
                   "payload_schema": c.payload_schema, "example": c.example}
                  for c in db.query(models.Component).order_by(models.Component.id).all()]
    return {
        "ops": sorted(ops_dsl),
        "components": components,
        "note": "ops применяются через POST /presentations/{id}/change-set (Ф2). "
                "Компоненты заполняются строго по payload_schema/example.",
    }


@router.get("/audio-duration")
def get_audio_duration(file_path: str):
    """Get duration of an audio file in milliseconds using ffprobe."""
    # Resolve /media/ → actual filesystem path
    if file_path.startswith("/media/"):
        abs_path = os.path.join(MEDIA_DIR, file_path[len("/media/"):])
    elif file_path.startswith("/uploads/"):
        abs_path = os.path.join("/app/uploads", file_path[len("/uploads/"):]) if os.path.exists("/app") else file_path
    else:
        abs_path = file_path

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"File not found: {abs_path}")

    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", abs_path],
            capture_output=True, text=True, timeout=15
        )
        info = json.loads(result.stdout)
        duration_sec = float(info["format"]["duration"])
        return {"file_path": file_path, "duration_ms": round(duration_sec * 1000, 1)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ffprobe error: {str(e)}")


class TranscribeRequest(BaseModel):
    file_path: str
    language: Optional[str] = "ru"
    model_size: Optional[str] = "base"


STT_URL = os.environ.get("STT_URL", "http://127.0.0.1:8788").rstrip("/")
STT_KEY = os.environ.get("STT_KEY", "local-whisper-key")
STT_TIMEOUT = float(os.environ.get("STT_TIMEOUT", "900"))


@router.post("/transcribe")
def transcribe_audio(request: TranscribeRequest):
    """Transcribe audio via the local OpenAI-compatible Whisper service (faster-whisper).

    STT_URL: http://127.0.0.1:8788 for local runs, http://host.docker.internal:8788 in Docker.
    """
    if request.file_path.startswith("/media/"):
        abs_path = os.path.join(MEDIA_DIR, request.file_path[len("/media/"):])
    else:
        abs_path = request.file_path

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"File not found: {abs_path}")

    headers = {"Authorization": f"Bearer {STT_KEY}"} if STT_KEY else {}
    try:
        with open(abs_path, "rb") as fh:
            resp = httpx.post(
                f"{STT_URL}/audio/transcriptions",
                headers=headers,
                files={"file": (os.path.basename(abs_path), fh, "application/octet-stream")},
                data={"model": "whisper-1", "response_format": "verbose_json",
                      **({"language": request.language} if request.language else {})},
                timeout=STT_TIMEOUT,
            )
        resp.raise_for_status()
        payload = resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"STT service unavailable at {STT_URL}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"STT error: {e.response.text[:300]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"STT error: {e}")

    words, segments = [], []
    for seg in payload.get("segments") or []:
        segments.append({
            "text": (seg.get("text") or "").strip(),
            "start": round(float(seg.get("start", 0)) * 1000, 1),
            "end": round(float(seg.get("end", 0)) * 1000, 1),
        })
        for w in seg.get("words") or []:
            words.append({
                "word": (w.get("word") or "").strip(),
                "start": round(float(w.get("start", 0)) * 1000, 1),
                "end": round(float(w.get("end", 0)) * 1000, 1),
            })

    return {
        "text": payload.get("text", ""),
        "language": payload.get("language", request.language),
        "words": words,
        "segments": segments,
    }
