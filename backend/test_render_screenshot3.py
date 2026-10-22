import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://frontend:5173/p/11?is_render=true")
        await page.wait_for_function('window.useDirectorInstance !== undefined')
        
        client = await page.context.new_cdp_session(page)
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'pause'})
        budget_expired_event = asyncio.Event()
        client.on("Emulation.virtualTimeBudgetExpired", lambda *args: budget_expired_event.set())
        
        # Advance quickly to 15.5s
        await page.evaluate('window.useDirectorInstance.seek(15500)')
        budget_expired_event.clear()
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 15500})
        await asyncio.wait_for(budget_expired_event.wait(), timeout=10.0)

        for frame in range(930, 990): # 15.5s to 16.5s
            time_ms = frame * (1000 / 60)
            await page.evaluate(f'window.useDirectorInstance.seek({time_ms})')
            
            budget_expired_event.clear()
            await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 16.666})
            await asyncio.wait_for(budget_expired_event.wait(), timeout=5.0)
            
            try:
                data = await client.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 100})
                if frame % 10 == 0:
                    print(f"Frame {frame} ({time_ms}ms) screenshot: {len(data['data'])} bytes")
            except Exception as e:
                print(f"CRASH at frame {frame}: {e}")
                break
        
        await browser.close()
        print("Done!")

asyncio.run(main())
