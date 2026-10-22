"""Диагностика зависания композитора: в момент HUNG снимает метрики
процессов Chromium (RSS/CPU) и состояние страницы.

Использование: docker compose exec -T backend python /app/probe_mem.py [pres] [f0] [f1]
"""
import asyncio
import os
import subprocess
import sys
import time
from playwright.async_api import async_playwright

PRES = int(sys.argv[1]) if len(sys.argv) > 1 else 11
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 900
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else 1050
FPS = 60


def chrome_procs():
    out = []
    try:
        ps = subprocess.run(['ps', '-eo', 'pid,rss,pcpu,etime,args'],
                            capture_output=True, text=True).stdout
        for line in ps.splitlines():
            if 'chrome' in line and 'grep' not in line:
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    out.append((parts[0], int(parts[1]) // 1024, parts[2], parts[4][:70]))
    except Exception as e:
        print('ps error', e)
    return out


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
                print(f'frame {frame}: SHOT HUNG — профили Chromium:', flush=True)
                for pid, rss, cpu, args in chrome_procs():
                    print(f'  pid={pid} rss={rss}MB cpu={cpu}%  {args}', flush=True)
                tot = sum(r for _, r, _, _ in chrome_procs())
                print(f'  СУММА RSS chrome = {tot} MB', flush=True)
                # память JS-кучи
                try:
                    m = await asyncio.wait_for(pg.evaluate("""()=>performance.memory ? {
                        used: Math.round(performance.memory.usedJSHeapSize/1048576),
                        limit: Math.round(performance.memory.jsHeapSizeLimit/1048576)} : null"""),
                        timeout=5.0)
                    print('  JS heap:', m, flush=True)
                except asyncio.TimeoutError:
                    print('  JS heap: недоступно (main thread занят)', flush=True)
                # счётчик мутаций DOM во время зависания
                try:
                    n = await asyncio.wait_for(pg.evaluate("""async ()=>{
                        let n=0; const mo=new MutationObserver(()=>n++);
                        mo.observe(document.body,{childList:true,subtree:true,attributes:true});
                        await new Promise(r=>setTimeout(r,1500)); mo.disconnect(); return n;
                    }"""), timeout=6.0)
                    print('  мутаций DOM за 1.5с во время зависания:', n, flush=True)
                except asyncio.TimeoutError:
                    print('  мутации DOM: evaluate завис → main thread занят', flush=True)
                break
            if frame % 100 == 0:
                tot = sum(r for _, r, _, _ in chrome_procs())
                print(f'frame {frame}: ok, RSS chrome = {tot} MB', flush=True)
        await b.close()

asyncio.run(main())
