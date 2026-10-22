"""Диагностика зависания: находит кадр с HUNG и определяет характер зависания.
- Runtime.evaluate с таймаутом → если тоже виснет, main thread заблокирован (JS).
- Если evaluate отвечает → завис композитор/растеризация (GPU/SwiftShader).

Использование: docker compose exec -T backend python /app/probe_diag.py [pres] [f0] [f1]
"""
import asyncio
import sys
import time
from playwright.async_api import async_playwright

PRES = int(sys.argv[1]) if len(sys.argv) > 1 else 11
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 900
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else 1050
FPS = 60


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
            '--js-flags=--max-old-space-size=2048', '--expose-gc',
        ])
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        logs = []
        pg.on('console', lambda m: logs.append(f'[{m.type}] {m.text}'[:200]))
        pg.on('pageerror', lambda e: logs.append(f'[pageerror] {str(e)[:200]}'))
        await pg.goto(f'http://frontend:5173/p/{PRES}?render=true&mobile=0', wait_until='load')
        await pg.wait_for_function('window.useDirectorInstance !== undefined', timeout=30000)
        client = await pg.context.new_cdp_session(pg)
        expired = asyncio.Event()
        client.on('Emulation.virtualTimeBudgetExpired', lambda *a: expired.set())

        for frame in range(F0, F1 + 1):
            time_ms = (frame / FPS) * 1000
            await pg.evaluate(f'window.useDirectorInstance.seek({time_ms})')
            expired.clear()
            await client.send('Emulation.setVirtualTimePolicy', {
                'policy': 'advance', 'budget': 1000 / FPS})
            try:
                await asyncio.wait_for(expired.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                print(f"frame {frame}: BUDGET TIMEOUT")
                break
            try:
                await asyncio.wait_for(
                    client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 95}),
                    timeout=8.0)
            except asyncio.TimeoutError:
                print(f"frame {frame}: SHOT HUNG -> диагностика", flush=True)
                # 1) отвечает ли JS?
                t0 = time.time()
                try:
                    r = await asyncio.wait_for(pg.evaluate('1+1'), timeout=5.0)
                    print(f"  JS evaluate: ОТВЕЧАЕТ за {time.time()-t0:.1f}s -> {r}"
                          f"  => завис КОМПОЗИТОР (GPU/растеризация)", flush=True)
                except asyncio.TimeoutError:
                    print(f"  JS evaluate: ЗАВИС >5s => main thread ЗАБЛОКИРОВАН (JS-цикл)", flush=True)
                # 2) последние console-сообщения
                print("  последние console:", flush=True)
                for line in logs[-8:]:
                    print("   ", line, flush=True)
                # 3) что на слайде?
                try:
                    st = await asyncio.wait_for(pg.evaluate("""()=>{
                        const v=[...document.querySelectorAll('.slide, [data-slide], section')]
                            .filter(e=>e.getBoundingClientRect().width>0)
                            .map(e=>({cls:(e.className||'').toString().slice(0,60),
                                      w:Math.round(e.getBoundingClientRect().width)}));
                        return {visible:v.slice(0,6),
                                nodes:document.querySelectorAll('*').length,
                                scrollH:document.body.scrollHeight};
                    }"""), timeout=5.0)
                    print("  DOM:", st, flush=True)
                except asyncio.TimeoutError:
                    print("  DOM: тоже завис", flush=True)
                break
        await b.close()

asyncio.run(main())
