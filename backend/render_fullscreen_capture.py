#!/usr/bin/env python3
"""Render via x11grab realtime capture.

Starts Xvfb, openbox (WM), launches headful Chromium in --app mode,
ffmpeg captures the X11 display with minimal crop to remove browser chrome.
~1x realtime, no screenshots.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def _internal_headers(extra: dict = None) -> dict:
    """Внутренний токен для worker→API (см. permissions._is_internal)."""
    h = dict(extra or {})
    tok = os.environ.get("INTERNAL_API_TOKEN")
    if tok:
        h["X-Internal-Token"] = tok
    return h


def _api_patch(job_id: int, **kw):
    try:
        data = json.dumps(kw).encode()
        req = urllib.request.Request(
            f"http://localhost:8000/renders/{job_id}",
            data=data,
            headers=_internal_headers({"Content-Type": "application/json"}),
            method="PATCH",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def _api_get(path: str):
    try:
        req = urllib.request.Request(f"http://localhost:8000{path}",
                                     headers=_internal_headers())
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception:
        return None


def _collect_audio_clips(presentation_id: int) -> list:
    pres = _api_get(f"/presentations/{presentation_id}")
    if not pres:
        return []
    audio_timeline = pres.get("audio_timeline")
    if not audio_timeline or "tracks" not in audio_timeline:
        return []
    clips = []
    for track in audio_timeline["tracks"]:
        for clip in track.get("clips", []):
            if clip.get("muted"):
                continue
            src = clip.get("src", "")
            if not src:
                continue
            if src.startswith("/media/"):
                local = src.replace("/media/", "/app/backend/media/")
            elif src.startswith("/uploads/"):
                local = src.replace("/uploads/", "/app/uploads/")
            else:
                continue
            if os.path.exists(local):
                clips.append({
                    "local_src": local,
                    "start_time": float(clip.get("start_time", 0)),
                    "end_time": float(clip.get("end_time", 0)),
                    # Смещение внутрь аудиофайла (трим слева / правая половина сплита).
                    # Без него обрезанный клип в готовом mp4 играет с начала файла.
                    "media_offset": float(clip.get("media_offset", 0) or 0),
                    "volume": float(clip.get("volume", 1.0)),
                })
    return clips


def _build_audio_filter(clips: list) -> str:
    if not clips:
        return ""
    parts = []
    for i, c in enumerate(clips):
        start_ms = int(c["start_time"])
        vol = c["volume"]
        # Обрезаем хвост клипа по end_time, иначе файл играет дальше своего конца.
        dur_s = (c["end_time"] - c["start_time"]) / 1000.0 if c["end_time"] > c["start_time"] else 0
        trim = f"atrim=0:{dur_s:.3f},asetpts=PTS-STARTPTS," if dur_s > 0 else ""
        parts.append(f"[{i+1}:a]{trim}adelay={start_ms}|{start_ms},volume={vol}[a{i}]")
    if len(clips) > 1:
        mix = "".join(f"[a{i}]" for i in range(len(clips)))
        parts.append(f"{mix}amix=inputs={len(clips)}:normalize=0[aout]")
    else:
        parts.append("[a0]anull[aout]")
    return "; ".join(parts)


def _require_tools():
    import shutil
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found.")
    if shutil.which("Xvfb") is None:
        raise RuntimeError("Xvfb not found.")
    try:
        import playwright  # noqa: F401
    except Exception as exc:
        raise RuntimeError("playwright not installed.") from exc


def _start_xvfb(width: int, height: int, base_display: int, tries: int = 6) -> subprocess.Popen:
    """Start Xvfb on a free display. Retries consecutive display numbers so
    parallel renders (each with its own display) don't collide."""
    import shutil
    if shutil.which("Xvfb") is None:
        raise RuntimeError("Xvfb not found.")
    for i in range(tries):
        disp = base_display + i
        proc = subprocess.Popen(
            ["Xvfb", f":{disp}", "-screen", "0", f"{width}x{height}x24",
             "-ac", "+extension", "GLX", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)
        if proc.poll() is None:
            os.environ["DISPLAY"] = f":{disp}"
            return proc
    raise RuntimeError("Xvfb failed to start: no free display slot")


def _record(url: str, seconds: float, width: int, height: int,
            fps: int, output: Path, job_id: int,
            presentation_id: int,
            portrait_safe: dict = None) -> None:
    from playwright.sync_api import sync_playwright

    # Длительность контента (с) + небольшой предролл до старта Director.
    # ffmpeg запускается раньше play(), чтобы поймать самый первый кадр.
    PREROLL = 0.4
    capture_window = float(seconds) + PREROLL
    ffmpeg_proc = None

    if "render=true" not in url:
        url = f"{url}?render=true" if "?" not in url else f"{url}&render=true"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}w={width}&h={height}&engine=realtime"
    if portrait_safe:
        # Шортсы (портрет): safe-zone — сжать контентный слой (.slides-safebox)
        # и чуть сдвинуть. Фон контейнера остаётся на весь кадр.
        # Ландшафт не трогаем.
        sep = "&" if "?" in url else "?"
        url = (f"{url}{sep}safe={portrait_safe['scale']}"
               f"&safeshift={portrait_safe['shift_frac']}")

    _api_patch(job_id, status="rendering", progress=5)

    audio_clips = _collect_audio_clips(presentation_id)
    has_audio = len(audio_clips) > 0

    # No overscan: Xvfb = exact target, page fills it, no crop/scale needed.
    # Each render gets its own Xvfb display to enable parallel renders.
    xvfb_display = 99 + (job_id % 80)
    xvfb_proc = _start_xvfb(width, height, xvfb_display)

    # Openbox with window decorations disabled via native config.
    # (xprop is NOT installed in the container, so no _MOTIF_WM_HINTS hacks.)
    rc_path = "/tmp/openbox-render-rc.xml"
    try:
        with open(rc_path, "w") as f:
            f.write(OPENBOX_RC)
    except Exception:
        rc_path = None
    ob_cmd = ["openbox", "--config-file", rc_path] if rc_path else ["openbox"]
    ob_proc = subprocess.Popen(
        ob_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--kiosk",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    f"--window-size={width},{height}",
                    f"--window-position=0,0",
                ],
            )
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            page = context.new_page()
            _api_patch(job_id, progress=8)

            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            try:
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector('.slides-container');
                        return el && el.children.length > 2;
                    }""",
                    timeout=30000,
                )
            except Exception:
                pass
            page.wait_for_load_state("networkidle", timeout=120000)
            _api_patch(job_id, progress=15)

            # Hide UI chrome
            try:
                page.evaluate(
                    "() => { const s = document.createElement('style'); "
                    "s.id='__pw_css'; s.textContent=" + repr(INJECT_CSS) + "; "
                    "document.head.appendChild(s); }"
                )
            except Exception:
                pass

            # Fullscreen the browser window.
            # NOTE: --kiosk is ignored when Chromium is driven via Playwright/CDP,
            # so toggle fullscreen with F11 via xdotool instead. This hides
            # Chromium's own tab strip + address bar. The openbox rc.xml above
            # already removes the OS window title bar. Then enforce exact geometry.
            try:
                wids = []
                for cls in ["Chromium", "chromium", "Chrome", "chrome"]:
                    result = subprocess.run(
                        ["xdotool", "search", "--class", cls],
                        timeout=3, capture_output=True, text=True,
                    )
                    wids = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]
                    if wids:
                        break
                if not wids:
                    print("xdotool: no chromium window found!",
                          flush=True, file=sys.stderr)
                for wid in wids:
                    subprocess.run(
                        ["xdotool", "windowactivate", wid],
                        timeout=5,
                    )
                    time.sleep(0.3)
                    # Send F11 directly to the window (no focus race)
                    subprocess.run(
                        ["xdotool", "key", "--window", wid, "F11"],
                        timeout=5,
                    )
                    time.sleep(1.0)
                    subprocess.run(
                        ["xdotool", "windowsize", wid, str(width), str(height),
                         "windowmove", wid, "0", "0"],
                        timeout=5,
                    )
                    geo = subprocess.run(
                        ["xdotool", "getwindowgeometry", wid],
                        timeout=5, capture_output=True, text=True,
                    )
                    print(f"xdotool: wid={wid} "
                          f"{geo.stdout.strip().replace(chr(10), ' ')}",
                          flush=True, file=sys.stderr)
                    break
            except Exception as e:
                print(f"xdotool warning: {e}", flush=True, file=sys.stderr)

            # Wait for fonts
            try:
                page.evaluate(
                    "document.fonts ? document.fonts.ready : Promise.resolve()"
                )
            except Exception:
                pass

            # Wait for Shiki
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    pending = page.evaluate(
                        "document.querySelectorAll('[data-code-pending]').length"
                    )
                    if pending == 0:
                        break
                except Exception:
                    break
                time.sleep(0.3)
            _api_patch(job_id, progress=18)

            # Wait for Director
            try:
                page.wait_for_function(
                    "window.useDirectorInstance !== undefined", timeout=30000
                )
            except Exception:
                print("Warning: Director not found", flush=True)

            time.sleep(0.5)
            _api_patch(job_id, progress=22)

            # Director at t=0, paused
            try:
                page.evaluate("""() => {
                    const d = window.useDirectorInstance;
                    if (d) { d.seek(0); d.pause(); }
                }""")
            except Exception:
                pass
            time.sleep(0.3)

            # --- Start ffmpeg (after page loaded, no loading screens captured) ---
            # Direct capture, then trim the 1-2px window-edge borders left by
            # openbox/Chromium: symmetric micro-crop TRIM px per side + scale
            # back to the exact target resolution (stretch ~0.2%, invisible).
            TRIM = 2
            trim_w = width - 2 * TRIM
            trim_h = height - 2 * TRIM
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "x11grab",
                "-video_size", f"{width}x{height}",
                "-framerate", str(fps),
                "-draw_mouse", "0",
                "-i", f"{os.environ['DISPLAY']}+0,0",
            ]
            if has_audio:
                audio_filter = _build_audio_filter(audio_clips)
                full_filter = (
                    f"[0:v]crop={trim_w}:{trim_h}:{TRIM}:{TRIM},"
                    f"scale={width}:{height}[v]; "
                    + audio_filter
                )
                for clip in audio_clips:
                    # Входной seek: клип звучит с media_offset, а не с начала файла.
                    if clip.get("media_offset", 0) > 0:
                        ffmpeg_cmd.extend(["-ss", f"{clip['media_offset'] / 1000.0:.3f}"])
                    ffmpeg_cmd.extend(["-i", clip["local_src"]])
                ffmpeg_cmd.extend([
                    "-filter_complex", full_filter,
                    "-map", "[v]", "-map", "[aout]",
                    "-c:a", "aac", "-b:a", "192k",
                ])
            else:
                ffmpeg_cmd.extend([
                    "-vf", f"crop={trim_w}:{trim_h}:{TRIM}:{TRIM},"
                           f"scale={width}:{height}",
                ])
            ffmpeg_cmd.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-color_range", "pc",
                "-colorspace", "bt709",
                "-color_trc", "bt709",
                "-color_primaries", "bt709",
                # Жёсткий предел вывода: ffmpeg сам завершится на capture_window,
                # даже если основной цикл притормозит. Без этого длительность
                # уезжала на несколько секунд из-за неточной остановки.
                "-t", f"{capture_window:.3f}",
                "-movflags", "+faststart",
                str(output),
            ])
            ffmpeg_proc = subprocess.Popen(
                ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            _api_patch(job_id, progress=25)
            time.sleep(PREROLL)

            # --- Start Director ---
            capture_t0 = time.monotonic()
            try:
                page.evaluate("""() => {
                    const d = window.useDirectorInstance;
                    if (d) { d.play(); }
                }""")
            except Exception:
                pass
            _api_patch(job_id, progress=28)

            # Wait for playback: монотонный таймер вместо посекундного цикла —
            # иначе лишний хвост до полной секунды.
            while True:
                elapsed = time.monotonic() - capture_t0
                if elapsed >= seconds:
                    break
                time.sleep(0.1)
                pct = 28 + (elapsed / seconds) * 55
                _api_patch(job_id, progress=min(83, pct))

            # Stop: замораживаем кадр и СРАЗУ гасим захват — до закрытия
            # браузера, чтобы в видео не попали кадры teardown.
            try:
                page.evaluate(
                    "window.useDirectorInstance && window.useDirectorInstance.pause()"
                )
            except Exception:
                pass
            if ffmpeg_proc.poll() is None:
                ffmpeg_proc.send_signal(signal.SIGINT)
                try:
                    ffmpeg_proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    ffmpeg_proc.kill()
                    ffmpeg_proc.wait(timeout=10)
            browser.close()

        # Stop ffmpeg (страховка, если основной поток упал до остановки)
        if ffmpeg_proc is not None and ffmpeg_proc.poll() is None:
            ffmpeg_proc.send_signal(signal.SIGINT)
            try:
                ffmpeg_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                ffmpeg_proc.kill()
                ffmpeg_proc.wait(timeout=10)

        _api_patch(job_id, progress=95)
        if output.exists():
            out_mb = output.stat().st_size / (1024 * 1024)
            print(f"Output: {output} ({out_mb:.1f} MB)", flush=True)
        else:
            raise RuntimeError("ffmpeg did not produce output")

    finally:
        ob_proc.terminate()
        try:
            ob_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ob_proc.kill()
        xvfb_proc.terminate()
        try:
            xvfb_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            xvfb_proc.kill()


# Openbox config: no window decorations (no title bar, no border) for any window.
OPENBOX_RC = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <applications>
    <application class="*">
      <decor>no</decor>
      <layer>above</layer>
      <skip_pager>yes</skip_pager>
      <skip_taskbar>yes</skip_taskbar>
    </application>
  </applications>
</openbox_config>
"""


INJECT_CSS = """
.group\\/panel, [class*="sidebar"], [class*="toolbar"],
[class*="controls"], [class*="bottom-"] { display: none !important; }
html, body { margin: 0 !important; padding: 0 !important; overflow: hidden !important;
             height: 100% !important; background: #0B1322 !important; }
::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }
* { scrollbar-width: none !important; }
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Realtime x11grab render.")
    parser.add_argument("--job-id", type=int, required=True)
    parser.add_argument("--presentation-id", type=int, required=True)
    parser.add_argument("--url", default="http://localhost:5174/p/11")
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--output", default="render_realtime.mp4")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--preset", choices=["landscape", "portrait"], default="landscape")
    parser.add_argument("--safe-scale", type=float, default=float(os.environ.get("RENDER_SAFE_SCALE", "0.85")),
                        help="Safe-zone для шортс (портрет): масштаб контентного слоя 0.5-1.0 (env RENDER_SAFE_SCALE)")
    parser.add_argument("--safe-shift", type=float, default=-0.02,
                        help="Safe-zone для шортс: вертикальный сдвиг долей высоты слайда (минус = вверх)")
    args = parser.parse_args()

    _require_tools()

    if args.preset == "portrait":
        target_w, target_h = 1080, 1920
    else:
        target_w, target_h = args.width, args.height

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    portrait_safe = None
    if target_h > target_w:
        portrait_safe = {
            "scale": min(1.0, max(0.5, args.safe_scale)),
            "shift_frac": args.safe_shift,
        }

    _record(args.url, args.seconds, target_w, target_h, args.fps, output,
            args.job_id, args.presentation_id, portrait_safe)
    print(f"Render finished: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyboardInterrupt) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
