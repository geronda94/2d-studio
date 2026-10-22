import os
import sys
import json
import asyncio
import base64
import subprocess
import time
from playwright.async_api import async_playwright

# Usage: python render_video.py <job_id> <presentation_id> <format: mobile|desktop|square> <fps> <quality: draft|standard|premium> <output_path>

def get_presentation_data(presentation_id):
    import requests
    response = requests.get(f"http://localhost:8000/presentations/{presentation_id}")
    if response.status_code != 200:
        raise Exception(f"Failed to fetch presentation data: {response.status_code}")

    data = response.json()
    return data


FONT_PRELOAD_JS = '''() => {
    const style = document.createElement('style');
    style.innerHTML = `* { scroll-behavior: auto !important; }`;
    document.head.appendChild(style);

    const div = document.createElement('div');
    div.innerHTML = `
        <span style="font-family: 'Inter'; font-weight: 300;">A Абвгд</span>
        <span style="font-family: 'Inter'; font-weight: 400;">A Абвгд</span>
        <span style="font-family: 'Inter'; font-weight: 500;">A Абвгд</span>
        <span style="font-family: 'Inter'; font-weight: 600;">A Абвгд</span>
        <span style="font-family: 'Inter'; font-weight: 700;">A Абвгд</span>
        <span style="font-family: 'Space Grotesk'; font-weight: 400;">A Абвгд</span>
        <span style="font-family: 'Space Grotesk'; font-weight: 500;">A Абвгд</span>
        <span style="font-family: 'Space Grotesk'; font-weight: 600;">A Абвгд</span>
        <span style="font-family: 'Space Grotesk'; font-weight: 700;">A Абвгд</span>
        <span style="font-family: 'Space Mono'; font-weight: 400;">A Абвгд</span>
        <span style="font-family: 'Space Mono'; font-weight: 700;">A Абвгд</span>
        <span style="font-family: 'Fira Code'; font-weight: 400;">A Абвгд</span>
    `;
    div.style.position = 'absolute';
    div.style.opacity = '0';
    div.style.pointerEvents = 'none';
    document.body.appendChild(div);
    return document.fonts.ready;
}'''


async def render_video(job_id, presentation_id, format_type, fps, quality, output_path):
    print(f"Starting render for job {job_id} (presentation {presentation_id}) in {format_type} format, {fps} fps, {quality} quality...")

    def _do_update(payload):
        import requests
        try:
            response = requests.patch(f"http://localhost:8000/renders/{job_id}", json=payload)
            if response.status_code == 404:
                print("Job deleted from API, aborting render.", flush=True)
                os._exit(0)
        except Exception as e:
            print(f"Failed to update progress to API: {e}", flush=True)

    def update_progress(status, frame=0, total=0, error=None, eta=None):
        progress_val = (frame / total * 100) if total > 0 else 0
        payload = {
            "status": status,
            "progress": progress_val
        }
        if error:
            payload["error_log"] = str(error)
        if eta is not None:
            payload["eta"] = eta
            
        if status in ("completed", "failed"):
            _do_update(payload)
        else:
            import threading
            threading.Thread(target=_do_update, args=(payload,), daemon=True).start()

    tmp_frames_dir = None
    mixed_audio_path = None
    process = None

    try:
        update_progress("rendering")

        import tempfile
        import shutil
        tmp_frames_dir = tempfile.mkdtemp(prefix=f"render_{job_id}_frames_")

        # Determine format size
        if format_type == 'mobile':
            width, height = 1080, 1920
        elif format_type == 'square':
            width, height = 1080, 1080
        else:
            width, height = 1920, 1080

        data = get_presentation_data(presentation_id)
        slides = data.get('slides', [])

        # Calculate total frames (assuming 60fps)
        total_duration_ms = 10000  # default fallback
        for slide in slides:
            if slide.get('component') == 'EndMarkerSlide':
                total_duration_ms = slide.get('start_time', 10000)
                break

        print(f"Total duration: {total_duration_ms}ms")
        fps_int = int(fps)
        total_frames = int((total_duration_ms / 1000) * fps_int)

        # Parse audio clips and pre-mix if any
        mixed_audio_path = None
        audio_timeline = data.get('audio_timeline')
        clips = []

        # 1. Add normal timeline clips
        if audio_timeline and 'tracks' in audio_timeline:
            for track in audio_timeline.get('tracks', []):
                for clip in track.get('clips', []):
                    if clip.get('muted'):
                        continue
                    src = clip.get('src')
                    if src and src.startswith('/media/'):
                        src = src.replace('/media/', '/app/backend/media/')
                    elif src and src.startswith('/uploads/'):
                        src = src.replace('/uploads/', '/app/uploads/')

                    if src and os.path.exists(src):
                        clip['local_src'] = src
                        clips.append(clip)

        # 2. Add component-level virtual SFX
        for i, slide in enumerate(slides):
            slide_time = slide.get('start_time', slide.get('startTime', 0))
            if slide_time is None:
                slide_time = 0

            payload = slide.get('data', {})
            if isinstance(payload, dict) and 'payload' in payload:
                payload = payload['payload']
            if not isinstance(payload, dict):
                payload = {}

            def extract_sfx(obj):
                if not obj or not isinstance(obj, (dict, list)):
                    return

                if isinstance(obj, dict):
                    node_sfx = obj.get('sfx') if (isinstance(obj.get('sfx'), dict) and obj.get('sfx').get('src')) else None
                    parent_sfx = payload.get('item_sfx') if (obj != payload and isinstance(payload.get('item_sfx'), dict) and payload.get('item_sfx').get('src') and obj.get('start_time') is not None) else None
                    sfx_to_use = node_sfx or parent_sfx

                    item_time = obj.get('start_time', obj.get('time'))
                    if item_time is not None and sfx_to_use and not sfx_to_use.get('muted') and sfx_to_use.get('src'):
                        try:
                            item_time_val = float(item_time)
                            time_offset = float(sfx_to_use.get('time_offset', 0))
                            calc_start_time = float(slide_time) + item_time_val + time_offset

                            src = sfx_to_use.get('src')
                            if src and src.startswith('/media/'):
                                src = src.replace('/media/', '/app/backend/media/')
                            elif src and src.startswith('/uploads/'):
                                src = src.replace('/uploads/', '/app/uploads/')

                            if src and os.path.exists(src):
                                clips.append({
                                    'local_src': src,
                                    'start_time': calc_start_time,
                                    'volume': sfx_to_use.get('volume', 1.0)
                                })
                        except (ValueError, TypeError):
                            pass

                    for v in obj.values():
                        extract_sfx(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_sfx(item)

            extract_sfx(payload)
        
        # Audio clips are gathered, we will mix them on the fly in the final ffmpeg encode!
        audio_clips_list = clips

        import multiprocessing
        threads_to_use = str(max(1, multiprocessing.cpu_count() // 2))

        preset = 'fast'
        crf = '23'
        if quality == 'draft':
            preset = 'ultrafast'
            crf = '28'
        elif quality == 'premium':
            preset = 'fast'
            crf = '15'

        # === Pre-extract all video frames from AdvancedVideoSlide components ===
        # This avoids having the browser decode video during VirtualTime (which deadlocks)
        print("Scanning for video slides...", flush=True)
        video_slides = []
        for slide in slides:
            if slide.get('component') == 'AdvancedVideoSlide':
                slide_data = slide.get('data', {})
                if isinstance(slide_data, dict) and 'payload' in slide_data:
                    slide_data = slide_data['payload']
                if not isinstance(slide_data, dict):
                    slide_data = {}

                video_url = slide_data.get('video_url', '')
                if not video_url:
                    continue

                local_path = None
                if video_url.startswith('/media/'):
                    local_path = video_url.replace('/media/', '/app/backend/media/')
                elif video_url.startswith('/uploads/'):
                    local_path = video_url.replace('/uploads/', '/app/uploads/')

                if local_path and os.path.exists(local_path):
                    video_slides.append({
                        'slide': slide,
                        'local_path': local_path,
                        'video_url': video_url,
                        'trim_start': float(slide_data.get('trim_start', 0)),
                        'trim_end': float(slide_data.get('trim_end', 0)),
                        'slide_start_ms': float(slide.get('start_time', 0)),
                        'video_play_offset_ms': float(slide_data.get('start_time', 0)),
                    })
                    print(f"  Found video slide: {video_url} slide_start={slide.get('start_time')}ms video_play_offset={slide_data.get('start_time')}ms", flush=True)

        video_frames_cache = {}
        for vs in video_slides:
            local_path = vs['local_path']
            video_url = vs['video_url']
            trim_start = vs['trim_start']
            trim_end = vs['trim_end']
            slide_start_ms = vs['slide_start_ms']
            video_play_offset_ms = vs['video_play_offset_ms']
            video_abs_start_ms = slide_start_ms + video_play_offset_ms

            print(f"Extracting frames for {video_url}...", flush=True)

            try:
                probe = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', local_path],
                    capture_output=True, text=True, timeout=30
                )
                vid_duration = float(probe.stdout.strip())
            except Exception as e:
                print(f"  ffprobe failed: {e}", flush=True)
                vid_duration = 60.0

            if trim_end <= 0:
                trim_end = vid_duration

            seg_duration = trim_end - trim_start
            if seg_duration <= 0:
                seg_duration = vid_duration

            trim_duration = trim_end - trim_start
            
            # Cap the extraction duration to what's actually needed for the presentation
            max_needed_duration = (total_duration_ms - slide_start_ms) / 1000.0
            if max_needed_duration > 0 and trim_duration > max_needed_duration:
                trim_duration = max_needed_duration
                print(f"  Capped extraction duration to {trim_duration:.2f}s based on presentation length", flush=True)

            print(f"  Extracting {fps_int}fps frames from {trim_start:.2f}s for {trim_duration:.2f}s...", flush=True)

            import hashlib
            vid_hash = hashlib.md5(video_url.encode()).hexdigest()[:8]
            video_frames_dir = os.path.join(tmp_frames_dir, f"video_{vid_hash}")
            os.makedirs(video_frames_dir, exist_ok=True)

            frame_pattern = os.path.join(video_frames_dir, 'frame_%06d.jpg')
            try:
                result = subprocess.run(
                    ['ffmpeg', '-y',
                     '-ss', str(trim_start),
                     '-i', local_path,
                     '-t', str(trim_duration),
                     '-vf', f'fps={fps_int}',
                     '-q:v', '3',
                     '-f', 'image2',
                     frame_pattern],
                    capture_output=True, timeout=300
                )
                if result.returncode != 0:
                    print(f"  ffmpeg error: {result.stderr.decode('utf-8', errors='ignore')[-500:]}", flush=True)
            except Exception as e:
                print(f"  ffmpeg failed: {e}", flush=True)

            extracted_frames_count = 0
            while True:
                fpath = os.path.join(video_frames_dir, f'frame_{extracted_frames_count+1:06d}.jpg')
                if not os.path.exists(fpath):
                    break
                extracted_frames_count += 1

            print(f"  Extracted {extracted_frames_count} frames to disk", flush=True)

            video_frames_cache[video_url] = {}
            for frame_num in range(1, total_frames + 1):
                frame_ms = (frame_num / fps_int) * 1000
                if frame_ms < video_abs_start_ms:
                    vid_frame_idx = 1
                else:
                    elapsed_s = (frame_ms - video_abs_start_ms) / 1000.0
                    looped_elapsed = elapsed_s % seg_duration
                    vid_frame_idx = int(looped_elapsed * fps_int) + 1

                if extracted_frames_count > 0:
                    vid_frame_idx = min(vid_frame_idx, extracted_frames_count)
                    video_frames_cache[video_url][frame_num] = os.path.join(video_frames_dir, f'frame_{vid_frame_idx:06d}.jpg')

            print(f"  Done mapping {len(video_frames_cache[video_url])} render frames for {video_url}", flush=True)

        # === Preload ALL images from presentation data (avoids VirtualTime network deadlocks) ===
        image_urls = set()

        def extract_images(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        lower_v = v.lower()
                        if (v.startswith('http') or v.startswith('/')) and (lower_v.endswith('.png') or lower_v.endswith('.jpg') or lower_v.endswith('.jpeg') or lower_v.endswith('.svg') or lower_v.endswith('.webp') or lower_v.endswith('.gif')):
                            image_urls.add(v)
                        elif ('avatar' in k.lower() or 'image' in k.lower() or 'icon' in k.lower() or 'logo' in k.lower() or 'url' in k.lower()) and '/' in v:
                            if not lower_v.endswith('.mp4') and not lower_v.endswith('.webm'):
                                image_urls.add(v)
                    else:
                        extract_images(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_images(item)

        extract_images(data)

        preload_js = None
        if image_urls:
            print(f"Will preload {len(image_urls)} images to prevent VirtualTime deadlocks...", flush=True)
            preload_js = """() => {
                const promises = [];
                const container = document.createElement('div');
                container.style.position = 'absolute';
                container.style.opacity = '0.01';
                container.style.pointerEvents = 'none';
                container.style.width = '1px';
                container.style.height = '1px';
                container.style.overflow = 'hidden';
                document.body.appendChild(container);
            """
            for i_url in image_urls:
                safe_url = i_url.replace("'", "\\'")
                preload_js += f"""
                promises.push(new Promise((resolve) => {{
                    const img = document.createElement('img');
                    img.src = '{safe_url}';
                    img.decode().then(resolve).catch(resolve);
                    container.appendChild(img);
                }}));
                """
            preload_js += "return Promise.all(promises); }"

        async def open_render_browser(p):
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--js-flags=--expose-gc --max-old-space-size=2048'
                ]
            )
            page = await browser.new_page(
                viewport={'width': width, 'height': height},
                device_scale_factor=1
            )

            url = f"http://frontend:5173/p/{presentation_id}?render=true&mobile={1 if format_type == 'mobile' else 0}"
            print(f"Navigating to {url}", flush=True)

            page.on("console", lambda msg: print(f"Browser console: {msg.text}", flush=True))
            page.on("pageerror", lambda err: print(f"Browser error: {err}", flush=True))

            # Block all audio requests since we mix audio separately. 
            # Streaming audio requests cause Chromium's virtual time to deadlock and saturates the backend server.
            async def abort_media(route):
                await route.abort()
            await page.route("**/*.mp3", abort_media)
            await page.route("**/*.wav", abort_media)

            await page.goto(url, wait_until='load')

            # Disable backdrop-filter across the entire page.
            # backdrop-filter triggers GPU compositor layers which run in REAL time even
            # under VirtualTime — after ~900 frames the GPU compositor queue fills up and
            # the browser deadlocks. Removing it has zero visual impact on the final video.
            try:
                await asyncio.wait_for(page.evaluate("""() => {
                    const style = document.createElement('style');
                    style.id = '__render_fix';
                    style.textContent = '* { backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }';
                    document.head.appendChild(style);
                }"""), timeout=10.0)
                print("Render fix: backdrop-filter disabled.", flush=True)
            except Exception as e:
                print(f"Warning: could not inject render CSS fix: {e}", flush=True)

            # Preload fonts to avoid screenshot hangs on font loading during paused virtual time
            try:
                await asyncio.wait_for(page.evaluate(FONT_PRELOAD_JS), timeout=15.0)
            except Exception as e:
                print(f"Warning: font preload timed out: {e}", flush=True)

            # Preload all images
            if preload_js:
                try:
                    await asyncio.wait_for(page.evaluate(preload_js), timeout=30.0)
                    print("All images preloaded successfully.", flush=True)
                except Exception as e:
                    print(f"Warning: image preload timed out or failed: {e}", flush=True)

            client = await page.context.new_cdp_session(page)
            try:
                await asyncio.wait_for(page.wait_for_function('window.useDirectorInstance !== undefined'), timeout=60.0)
            except Exception as e:
                print(f"Warning: wait for useDirectorInstance failed: {e}", flush=True)

            # Register video slides URL mapping
            if video_slides:
                try:
                    await asyncio.wait_for(page.evaluate('''() => { window.__videoSlidesUrls = ''' +
                                        str([vs['video_url'] for vs in video_slides]).replace("'", '"') +
                                        '''; }'''), timeout=15.0)
                    print("Video slide URLs registered in browser", flush=True)
                except Exception as e:
                    print(f"Warning: video slides registration failed: {e}", flush=True)

            # Enable virtual time (paused) so we control each frame
            try:
                await asyncio.wait_for(client.send('Emulation.setVirtualTimePolicy', {'policy': 'pause'}), timeout=15.0)
            except Exception as e:
                pass
            budget_expired_event = asyncio.Event()
            client.on("Emulation.virtualTimeBudgetExpired", lambda *args: budget_expired_event.set())

            return browser, page, client, budget_expired_event

        async def inject_video_frames(page, frame):
            # Inject pre-extracted video frames as <img> into the video player canvas
            for vs in video_slides:
                video_url = vs['video_url']
                vpath = video_frames_cache.get(video_url, {}).get(frame)
                if not vpath or not os.path.exists(vpath):
                    continue
                try:
                    has_player = await asyncio.wait_for(
                        page.evaluate("() => document.querySelectorAll('.advanced-video-player').length > 0"), 
                        timeout=5.0
                    )
                except Exception:
                    has_player = False
                if not has_player:
                    continue
                with open(vpath, 'rb') as f:
                    frame_data = base64.b64encode(f.read()).decode()
                js_inject = f'''() => {{
                    const players = document.querySelectorAll('.advanced-video-player');
                    players.forEach(player => {{
                        const canvas = player.querySelector('canvas');
                        if (canvas) {{
                            const img = new Image();
                            img.onload = () => {{
                                if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {{
                                    canvas.width = img.naturalWidth || 1920;
                                    canvas.height = img.naturalHeight || 1080;
                                }}
                                canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                            }};
                            img.src = 'data:image/jpeg;base64,{frame_data}';
                        }}
                    }});
                }}'''
                try:
                    await asyncio.wait_for(page.evaluate(js_inject), timeout=15.0)
                except Exception as e:
                    raise Exception(f"Inject video frames failed: {e}")

        async def seek_and_advance(page, client, budget_expired_event, time_ms):
            try:
                await asyncio.wait_for(page.evaluate(f'window.useDirectorInstance.seek({time_ms})'), timeout=15.0)
                budget_expired_event.clear()
                await asyncio.wait_for(client.send('Emulation.setVirtualTimePolicy', {
                    'policy': 'advance',
                    'budget': 1000 / fps_int
                }), timeout=15.0)
                await asyncio.wait_for(budget_expired_event.wait(), timeout=120.0)
            except Exception as e:
                raise Exception(f"Seek failed: {e}")
            # Small real-time settle so the compositor finishes the DOM mutation
            # triggered by seek() before we ask for a screenshot.
            await asyncio.sleep(0.02)

        async def close_browser(browser):
            try:
                await asyncio.wait_for(browser.close(), timeout=20)
            except Exception:
                pass

        async def render_chunk(p, worker_id, start_frame, end_frame, total_frames, start_time_render, global_state, ffmpeg_proc):
            browser, page, client, budget_expired_event = await open_render_browser(p)

            for frame in range(start_frame, end_frame + 1):
                start_frame_time = time.time()
                time_ms = (frame / fps_int) * 1000

                captured = False
                jpeg_quality = 95 if quality == 'premium' else 85 if quality == 'standard' else 70

                for attempt in range(4):
                    try:
                        try:
                            await inject_video_frames(page, frame)
                        except Exception as e:
                            raise Exception(f"inject_video_frames failed: {e}")
                        
                        try:
                            await seek_and_advance(page, client, budget_expired_event, time_ms)
                        except Exception as e:
                            raise Exception(f"seek_and_advance failed: {e}")
                        
                        try:
                            screenshot_data = await asyncio.wait_for(
                                client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': jpeg_quality}),
                                timeout=30.0
                            )
                        except Exception as e:
                            raise Exception(f"captureScreenshot failed: {e}")

                        # Stream raw JPEG bytes directly to ffmpeg stdin
                        ffmpeg_proc.stdin.write(base64.b64decode(screenshot_data['data']))
                        captured = True
                        break
                    except Exception as e:
                        err_name = type(e).__name__
                        print(f"Frame {frame} failed: {e} (attempt {attempt+1}/4), restarting browser...", flush=True)
                        await close_browser(browser)
                        try:
                            browser, page, client, budget_expired_event = await open_render_browser(p)
                        except Exception as open_err:
                            print(f"Failed to restart browser: {open_err}", flush=True)

                if not captured:
                    print(f"FATAL: Frame {frame} hung or failed after 4 attempts!")
                    raise Exception(f"Frame {frame} hung after 4 attempts!")

                global_state['completed_frames'] += 1
                
                # Only log progress periodically
                if global_state['completed_frames'] % 15 == 0 or global_state['completed_frames'] == total_frames:
                    elapsed = time.time() - start_time_render
                    eta = None
                    rate = global_state['completed_frames'] / elapsed if elapsed > 0 else 0
                    if rate > 0:
                        eta = (total_frames - global_state['completed_frames']) / rate
                    print(f"Rendered {global_state['completed_frames']}/{total_frames} frames ({global_state['completed_frames']/total_frames*100:.1f}%) in {elapsed:.1f}s, ETA: {eta if eta else 0:.1f}s", flush=True)
                    update_progress("rendering", frame=global_state['completed_frames'], total=total_frames, eta=eta)
                    
                # Explicitly invoke garbage collection every 50 frames to avoid OOM
                if global_state['completed_frames'] % 50 == 0:
                    try:
                        await page.evaluate("if(window.gc) window.gc()")
                    except:
                        pass

            await close_browser(browser)

        # Start FFmpeg process first and wait for piped input
        print("Starting FFmpeg encoder stream...", flush=True)
        encode_cmd = [
            'ffmpeg', '-y',
            '-threads', threads_to_use,
            '-framerate', str(fps_int),
            '-f', 'image2pipe',
            '-i', '-'
        ]
        
        # Add audio inputs and filter_complex
        if audio_clips_list:
            for clip in audio_clips_list:
                encode_cmd.extend(['-i', clip['local_src']])
                
            filter_complex = ""
            for i, clip in enumerate(audio_clips_list):
                # i+1 because 0 is the video stream
                start_ms = int(float(clip.get('start_time', 0)))
                volume = float(clip.get('volume', 1.0))
                filter_complex += f"[{i+1}:a]adelay={start_ms}|{start_ms},volume={volume}[a{i}]; "
                
            if len(audio_clips_list) > 1:
                mix_inputs = "".join([f"[a{i}]" for i in range(len(audio_clips_list))])
                filter_complex += f"{mix_inputs}amix=inputs={len(audio_clips_list)}:normalize=0[aout]"
            else:
                filter_complex += "[a0]anull[aout]"
                
            encode_cmd.extend(['-filter_complex', filter_complex])

        encode_cmd.extend([
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', preset,
            '-crf', crf,
            '-t', str(total_duration_ms / 1000)
        ])

        if audio_clips_list:
            encode_cmd.extend(['-map', '0:v', '-map', '[aout]', '-c:a', 'aac', '-b:a', '192k'])

        encode_cmd.append(output_path)
        
        ffmpeg_proc = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE)

        async with async_playwright() as p:
            print("Starting linear frame capture to pipe...", flush=True)
            update_progress("rendering", frame=0, total=total_frames)
            start_time_render = time.time()
            
            global_state = {
                'completed_frames': 0
            }
            
            await render_chunk(p, 0, 1, total_frames, total_frames, start_time_render, global_state, ffmpeg_proc)

        # Close stdin to signal ffmpeg that no more frames are coming
        ffmpeg_proc.stdin.close()
        ffmpeg_proc.wait()
        if ffmpeg_proc.returncode != 0:
            raise Exception(f"FFmpeg encoding failed with exit code {ffmpeg_proc.returncode}")

        print("Render successful!", flush=True)
        update_progress("completed", frame=total_frames, total=total_frames)

    except Exception as e:
        import traceback
        err_msg = str(e)
        print(f"Render failed: {err_msg}", flush=True)
        traceback.print_exc()
        update_progress("failed", error=err_msg)

    finally:
        # Cleanup Subprocesses (if any leftover)
        if 'ffmpeg_proc' in locals() and ffmpeg_proc and ffmpeg_proc.returncode is None:
            try:
                ffmpeg_proc.terminate()
                ffmpeg_proc.wait(timeout=10)
            except Exception:
                try:
                    ffmpeg_proc.kill()
                    ffmpeg_proc.wait()
                except:
                    pass

        # Cleanup Temp Files
        if tmp_frames_dir and os.path.exists(tmp_frames_dir):
            try:
                import shutil
                shutil.rmtree(tmp_frames_dir)
                print(f"Cleaned up temporary frames directory: {tmp_frames_dir}")
            except Exception as e:
                print(f"Warning: failed to cleanup temp frames dir {tmp_frames_dir}: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 7:
        print("Usage: python render_video.py <job_id> <presentation_id> <format: mobile|desktop|square> <fps> <quality: draft|standard|premium> <output_path>")
        sys.exit(1)

    job_id = sys.argv[1]
    presentation_id = sys.argv[2]
    format_type = sys.argv[3]
    fps = sys.argv[4]
    quality = sys.argv[5]
    output_path = sys.argv[6]

    asyncio.run(render_video(job_id, presentation_id, format_type, fps, quality, output_path))
