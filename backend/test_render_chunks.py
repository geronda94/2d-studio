import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--js-flags=--max-old-space-size=2048'])
        page = await browser.new_page()
        print("Goto page...")
        await page.goto("http://frontend:5173/p/11")
        print("Page loaded. Sending virtual time policy...")
        await page.evaluate("window.__VUE_APP_RELATIVE_TIME__ = 0")
        client = await page.context.new_cdp_session(page)
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'pause'})
        budget_expired_event = asyncio.Event()
        client.on("Emulation.virtualTimeBudgetExpired", lambda *args: budget_expired_event.set())
        
        print("Advancing to 15.8s in one chunk...")
        budget_expired_event.clear()
        await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 15800})
        await asyncio.wait_for(budget_expired_event.wait(), timeout=10.0)
        
        print("Advancing in 16.6ms chunks past 16.0s...")
        for i in range(20):
            budget_expired_event.clear()
            await client.send('Emulation.setVirtualTimePolicy', {'policy': 'advance', 'budget': 16.666})
            await asyncio.wait_for(budget_expired_event.wait(), timeout=10.0)
            print(f"Frame {i} done")
            
        print("Success! No freeze!")
        await browser.close()

asyncio.run(main())
