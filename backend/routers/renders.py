from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..permissions import enforce_write, idempotency_guard
from .. import models, schemas
import os
import sys
import datetime
import signal
import threading
import subprocess

router = APIRouter(
    prefix="/renders",
    tags=["renders"],
    dependencies=[Depends(enforce_write)],
)

UPLOAD_DIR = "/app/uploads" if os.path.exists("/app") else "uploads"

# Track running render subprocesses so we can kill them on delete and
# prevent concurrent renders from exhausting memory/CPU.
_render_lock = threading.Lock()
ACTIVE_RENDERS = {}  # job_id -> subprocess.Popen

# Hard cap on parallel renders (CPU safety). Override via MAX_CONCURRENT_RENDERS env.
MAX_CONCURRENT_RENDERS = int(os.environ.get("MAX_CONCURRENT_RENDERS", "2"))


def _screen_size_for_format(format_type: str):
    if format_type == "mobile":
        return (1080, 1920)
    if format_type == "square":
        return (1080, 1080)
    if format_type == "landscape":
        return (1920, 1280)
    if format_type == "portrait":
        return (1280, 1920)
    return (1920, 1080)


def _presentation_duration_seconds(presentation) -> float:
    if presentation is None or not getattr(presentation, "slides", None):
        return 20.0

    slides = sorted(presentation.slides, key=lambda s: float(s.start_time or 0))
    if not slides:
        return 20.0

    # EndMarkerSlide — единственная точка истины конца видео.
    # Пользователь двигает его вручную; фронт уже так делает
    # (RenderManagerModal.getPresentationEndTime + useScreenRecorder +300мс).
    # Возвращаем длительность контента + 0.5с запаса. Хвост ПОСТОЯННЫЙ
    # (0.5с запас + ~0.4с предролл ffmpeg) и НЕ растёт с длительностью:
    # остановку ведёт монотонный таймер + ffmpeg -t в
    # render_fullscreen_capture.py, а не посекундный цикл со счётчиком.
    for s in slides:
        if getattr(s, "component", "") == "EndMarkerSlide":
            end_marker_ms = float(getattr(s, "start_time", 0) or 0)
            if end_marker_ms > 0:
                return max(5.0, end_marker_ms / 1000.0 + 0.5)

    # Fallback (маркера нет): слайды + аудио + 1.5с
    # Duration from slides
    last_slide_time = max(float(getattr(s, "start_time", 0) or 0) for s in slides)

    # Duration from audio timeline (may be longer than slide start_time)
    last_audio_time = 0
    audio_timeline = getattr(presentation, "audio_timeline", None)
    if audio_timeline and isinstance(audio_timeline, dict):
        for track in audio_timeline.get("tracks", []):
            for clip in track.get("clips", []):
                end = float(clip.get("end_time", 0) or 0)
                if end > last_audio_time:
                    last_audio_time = end

    last_time = max(last_slide_time, last_audio_time)
    if last_time <= 0:
        return 20.0
    return max(5.0, last_time / 1000.0 + 1.5)


def _kill_process_tree(proc: subprocess.Popen):
    """Terminate a render subprocess and its whole process group (ffmpeg, chromium)."""
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def _reap_finished():
    with _render_lock:
        for job_id in list(ACTIVE_RENDERS.keys()):
            if ACTIVE_RENDERS[job_id].poll() is not None:
                ACTIVE_RENDERS.pop(job_id, None)


def _update_render_job_status(job_id: int, *, status: str = None, progress: float = None, file_url: str = None, error_log: str = None):
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
        if not job:
            return
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = float(progress)
        if file_url is not None:
            job.file_url = file_url
        if error_log is not None:
            job.error_log = error_log
        job.updated_at = datetime.datetime.utcnow()
        db.commit()
    finally:
        db.close()

@router.post("/realtime", response_model=schemas.RenderJob, dependencies=[Depends(idempotency_guard)])
def create_realtime_render(job: schemas.RenderJobBase, db: Session = Depends(get_db)):
    """Real-time render: Playwright headless video recording.
    1 min video ≈ 1 min wall clock. No DISPLAY required."""
    _reap_finished()

    with _render_lock:
        if len(ACTIVE_RENDERS) >= MAX_CONCURRENT_RENDERS:
            raise HTTPException(
                status_code=429,
                detail=f"Рендер запущен ({len(ACTIVE_RENDERS)}/{MAX_CONCURRENT_RENDERS}). "
                       f"Дождитесь завершения текущего или поднимите лимит "
                       f"через переменную MAX_CONCURRENT_RENDERS.",
            )
        active_count = len(ACTIVE_RENDERS)

    settings = job.settings or {}
    fps = settings.get("fps", 60)
    format_type = settings.get("format", "desktop")
    quality = settings.get("quality", "standard")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    presentation = db.query(models.Presentation).filter(models.Presentation.id == job.presentation_id).first()
    title_slug = "video"
    if presentation and presentation.title:
        clean_title = "".join([c if c.isalnum() or c.isspace() or c in "-_" else "" for c in presentation.title]).strip()
        title_slug = "_".join(clean_title.split())
        if not title_slug:
            title_slug = "video"

    format_labels = {
        "portrait": "шортс",
        "mobile": "шортс",
        "desktop": "широкий_формат",
        "landscape": "широкий_формат",
        "square": "квадрат",
    }
    format_label = format_labels.get(format_type, format_type)

    output_filename = f"{title_slug}_{format_label}_realtime_{fps}fps_{timestamp}.mp4"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    db_job = models.RenderJob(
        presentation_id=job.presentation_id,
        settings={"fps": fps, "format": format_type, "quality": quality, "engine": "realtime"},
        status="pending",
        progress=0.0,
        file_url=f"/uploads/{output_filename}"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Duration from presentation timeline (slides + audio)
    duration_seconds = _presentation_duration_seconds(presentation)

    # Inside Docker, backend reaches frontend via service name
    presentation_url = f"http://frontend:5173/p/{job.presentation_id}"

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "render_fullscreen_capture.py")
    proc = subprocess.Popen([
        sys.executable,
        script_path,
        "--job-id", str(db_job.id),
        "--presentation-id", str(job.presentation_id),
        "--url", presentation_url,
        "--seconds", str(duration_seconds),
        "--output", output_path,
        "--fps", str(fps),
        "--preset", format_type if format_type in ("landscape", "portrait") else "landscape",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, start_new_session=True)

    with _render_lock:
        ACTIVE_RENDERS[db_job.id] = proc

    _update_render_job_status(db_job.id, status="rendering", progress=1.0)

    def _reaper():
        exit_code = proc.wait()
        with _render_lock:
            ACTIVE_RENDERS.pop(db_job.id, None)

        output_exists = os.path.exists(output_path)
        if exit_code == 0 and output_exists:
            _update_render_job_status(db_job.id, status="completed", progress=100.0, file_url=f"/uploads/{os.path.basename(output_path)}")
        else:
            error_message = "Realtime render process exited without producing video."
            if proc.stderr is not None:
                try:
                    err_text = proc.stderr.read()
                    if err_text:
                        error_message = err_text.strip()[:2000]
                except Exception:
                    pass
            if not output_exists and exit_code == 0:
                error_message = "Render process exited successfully but no output file was created."
            _update_render_job_status(db_job.id, status="failed", progress=max(0.0, min(99.0, float(db_job.progress or 0))), error_log=error_message)
    threading.Thread(target=_reaper, daemon=True).start()

    return db_job


@router.get("/presentation/{presentation_id}", response_model=List[schemas.RenderJob])
def get_render_jobs_by_presentation(presentation_id: int, db: Session = Depends(get_db)):
    jobs = db.query(models.RenderJob).filter(models.RenderJob.presentation_id == presentation_id).order_by(models.RenderJob.created_at.desc()).all()
    return jobs

@router.patch("/{job_id}")
def update_render_job(job_id: int, payload: dict, db: Session = Depends(get_db)):
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if "status" in payload:
        job.status = payload["status"]
    if "progress" in payload:
        job.progress = payload["progress"]
    if "error_log" in payload:
        job.error_log = payload["error_log"]
    if "eta" in payload:
        settings = dict(job.settings or {})
        settings["eta"] = payload["eta"]
        job.settings = settings
        
    db.commit()
    return {"status": "ok"}

@router.delete("/{job_id}")
def delete_render_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Kill the running render process tree if it's still active
    with _render_lock:
        proc = ACTIVE_RENDERS.pop(job_id, None)
    if proc is not None:
        _kill_process_tree(proc)
        
    # Delete the physical file if it exists
    if job.file_url:
        filename = job.file_url.split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")
                
    db.delete(job)
    db.commit()
    return {"status": "ok"}
