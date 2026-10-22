import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
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
        page = await browser.new_page()
        await page.goto("http://frontend:5173/p/11?is_render=true")
        await page.wait_for_function('window.useDirectorInstance !== undefined', timeout=30000)
        
        client = await page.context.new_cdp_session(page)
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'pause'})
        
        budget_expired_event = asyncio.Event()
        client.on("Emulation.virtualTimeBudgetExpired", lambda *args: budget_expired_event.set())
        
        await page.evaluate('window.useDirectorInstance.seek(14000)')
        budget_expired_event.clear()
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 14000})
        await asyncio.wait_for(budget_expired_event.wait(), timeout=15.0)
        
        print("At 14s - starting frame-by-frame test 840-990")
        
        crashed = False
        for frame in range(840, 990):
            time_ms = frame * (1000 / 60)
            await page.evaluate(f'window.useDirectorInstance.seek({time_ms})')
            
            budget_expired_event.clear()
            await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 16.666})
            try:
                await asyncio.wait_for(budget_expired_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print(f"TIMEOUT (deadlock) at frame {frame} ({time_ms:.0f}ms)")
                crashed = True
                break
            
            try:
                data = await client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 50})
                if frame % 20 == 0:
                    print(f"  Frame {frame} ({time_ms:.0f}ms) OK: {len(data['data'])} bytes")
            except Exception as e:
                print(f"SCREENSHOT CRASH at frame {frame}: {e}")
                crashed = True
                break
        
        if not crashed:
            print("SUCCESS: All frames rendered without crash!")
        
        await browser.close()

asyncio.run(main())
