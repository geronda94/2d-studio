"""Профилирование роста ресурсов по кадрам рендера: снимает DOM-узлы,
JS-heap, число audio/video/canvas и стили — чтобы найти утечку.

Использование: docker compose exec -T backend python /app/probe_growth.py [pres] [f0] [f1] [step]
"""
import asyncio
import subprocess
import sys
import time
from playwright.async_api import async_playwright

PRES = int(sys.argv[1]) if len(sys.argv) > 1 else 11
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 850
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else 1900
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 100
FPS = 60


def chrome_rss():
    tot = 0
    try:
        ps = subprocess.run(['ps', '-eo', 'rss,args'], capture_output=True, text=True).stdout
        for line in ps.splitlines():
            if 'chrome' in line and 'grep' not in line:
                try:
                    tot += int(line.split()[0]) // 1024
                except Exception:
                    pass
    except Exception:
        pass
    return tot


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
        for frame in range(F0, F1 + 1):
            time_ms = (frame / FPS) * 1000
            await pg.evaluate(f'window.useDirectorInstance.seek({time_ms})')
            expired.clear()
            await client.send('Emulation.setVirtualTimePolicy', {
                'policy': 'advance', 'budget': 1000 / FPS})
            try:
                await asyncio.wait_for(expired.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                print(f'frame {frame}: BUDGET TIMEOUT')
                break
            try:
                await asyncio.wait_for(
                    client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 95}),
                    timeout=8.0)
            except asyncio.TimeoutError:
                print(f'frame {frame}: SHOT HUNG', flush=True)
                break
            if frame % STEP == 0:
                el = time.time() - t_start
                m = await pg.evaluate("""()=>{
                    const q=(s)=>document.querySelectorAll(s).length;
                    return {
                        dom: q('*'),
                        audio: q('audio'),
                        video: q('video'),
                        canvas: q('canvas'),
                        img: q('img'),
                        styleTags: q('style'),
                        heap: performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):-1,
                        heapLimit: performance.memory?Math.round(performance.memory.jsHeapSizeLimit/1048576):-1,
                        listeners: (window.__listeners||0),
                    };
                }""")
                print(f"f={frame:>5} {el:>6.1f}s {frame/el:>6.1f}fps  "
                      f"dom={m['dom']:<6} audio={m['audio']:<4} video={m['video']:<4} "
                      f"canvas={m['canvas']:<3} img={m['img']:<5} style={m['styleTags']:<4} "
                      f"heap={m['heap']}MB/{m['heapLimit']}MB  chromeRSS={chrome_rss()}MB", flush=True)
        await b.close()

asyncio.run(main())
