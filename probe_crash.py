"""Быстрый пробник краша рендера: повторяет протокол render_video.py
(virtual time + seek) и замеряет, на скольких кадрах captureScreenshot встаёт.

Использование: docker compose exec -T backend python /app/probe_crash.py [slide_ms ...]
"""
import asyncio
import sys
import time
from playwright.async_api import async_playwright

PRES = int(sys.argv[1]) if len(sys.argv) > 1 else 11
FPS = 60
TIMES = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [16000]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
            '--js-flags=--max-old-space-size=2048', '--expose-gc',
        ])
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(f'http://frontend:5173/p/{PRES}?render=true&mobile=0', wait_until='load')
        await pg.wait_for_function('window.useDirectorInstance !== undefined', timeout=30000)
        client = await pg.context.new_cdp_session(pg)
        expired = asyncio.Event()
        client.on('Emulation.virtualTimeBudgetExpired', lambda *a: expired.set())

        for t in TIMES:
            await pg.evaluate(f'window.useDirectorInstance.seek({t})')
            expired.clear()
            await client.send('Emulation.setVirtualTimePolicy', {
                'policy': 'advance', 'budget': 1000 / FPS})
            t0 = time.time()
            try:
                await asyncio.wait_for(expired.wait(), timeout=8.0)
                budget_s = time.time() - t0
            except asyncio.TimeoutError:
                budget_s = None
            t1 = time.time()
            try:
                await asyncio.wait_for(
                    client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 95}),
                    timeout=12.0)
                shot_ms = (time.time() - t1) * 1000
            except asyncio.TimeoutError:
                shot_ms = None
            status = 'OK' if shot_ms is not None else 'HUNG'
            print(f"t={t:>6}ms  budget={budget_s if budget_s is None else round(budget_s,2)}s"
                  f"  screenshot={shot_ms if shot_ms is None else str(round(shot_ms))+'ms'}"
                  f"  -> {status}", flush=True)
        real = [e for e in errs if 'viewBox' not in e and 'favicon' not in e
                and 'ERR_FAILED' not in e and 'AudioEngine' not in e]
        if real:
            print('console errors:', real[:3])
        await b.close()

asyncio.run(main())
