"""Пробник краша рендера (последовательный): повторяет протокол render_video.py
(virtual time + seek + captureScreenshot) кадр за кадром и печатает кадр,
на котором captureScreenshot встаёт.

Использование: docker compose exec -T backend python /app/probe_seq.py [pres] [start_frame] [end_frame] [step]
"""
import asyncio
import sys
import time
from playwright.async_api import async_playwright

PRES = int(sys.argv[1]) if len(sys.argv) > 1 else 11
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else 1100
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1
FPS = 60
SHOT_TIMEOUT = 8.0
BUDGET_TIMEOUT = 20.0


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
            '--js-flags=--max-old-space-size=2048', '--expose-gc',
        ])
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        await pg.goto(f'http://frontend:5173/p/{PRES}?render=true&mobile=0', wait_until='load')
        await pg.wait_for_function('window.useDirectorInstance !== undefined', timeout=30000)
        client = await pg.context.new_cdp_session(pg)
        expired = asyncio.Event()
        client.on('Emulation.virtualTimeBudgetExpired', lambda *a: expired.set())

        t_start = time.time()
        for frame in range(F0, F1 + 1, STEP):
            time_ms = (frame / FPS) * 1000
            try:
                await asyncio.wait_for(
                    pg.evaluate(f'window.useDirectorInstance.seek({time_ms})'), timeout=15.0)
            except Exception as e:
                print(f"frame {frame}: SEEK FAILED {type(e).__name__}", flush=True)
                break
            expired.clear()
            try:
                await asyncio.wait_for(client.send('Emulation.setVirtualTimePolicy', {
                    'policy': 'advance', 'budget': 1000 / FPS}), timeout=15.0)
                await asyncio.wait_for(expired.wait(), timeout=BUDGET_TIMEOUT)
            except asyncio.TimeoutError:
                print(f"frame {frame}: BUDGET TIMEOUT (seek_and_advance 20s)", flush=True)
                break
            except Exception as e:
                print(f"frame {frame}: BUDGET ERR {type(e).__name__}: {e}", flush=True)
                break
            try:
                await asyncio.wait_for(
                    client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 95}),
                    timeout=SHOT_TIMEOUT)
            except asyncio.TimeoutError:
                print(f"frame {frame}: SHOT HUNG >{SHOT_TIMEOUT}s  <-- CRASH POINT", flush=True)
                break
            except Exception as e:
                print(f"frame {frame}: SHOT ERR {type(e).__name__}", flush=True)
                break
            if frame % 50 == 0:
                el = time.time() - t_start
                print(f"frame {frame}: ok  ({el:.0f}s elapsed, {frame/el:.1f} fps)", flush=True)
        else:
            print(f"NO HANG in {F0}..{F1}", flush=True)
        await b.close()

asyncio.run(main())
