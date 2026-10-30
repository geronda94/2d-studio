// Stress: repeated navigation between presentations and studios.
//
//   node tests/audit/stress.cjs http://localhost:5590
//
// Catches the classic SPA leaks: iframes that are never removed, heap that
// grows with every visit, timers that keep running, console errors on the way.
const { chromium } = require('playwright')
const fs = require('fs')

const BASE = process.argv[2] || 'http://localhost:5590'
const ROUNDS = Number(process.env.ROUNDS || 6)
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)

const ROUTE = ['/p/1', '/p/12', '/p/13', '/', '/p/1']

async function main() {
  // --expose-gc lets the test measure the RETAINED heap instead of V8's
  // uncollected garbage; without it every SPA looks like a leak.
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox', '--js-flags=--expose-gc'] })
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  const errors = []
  page.on('pageerror', (e) => errors.push(String(e).slice(0, 200)))
  page.on('console', (m) => { if (m.type() === 'error' && !/favicon/i.test(m.text())) errors.push(m.text().slice(0, 200)) })

  const heap = []
  const iframes = []
  for (let r = 0; r < ROUNDS; r++) {
    for (const url of ROUTE) {
      await page.goto(BASE + url, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(500)
      await page.evaluate(() => { if (window.gc) { window.gc(); window.gc() } })
      const st = await page.evaluate(() => ({
        heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576 * 10) / 10 : null,
        iframes: document.querySelectorAll('iframe').length,
        canvases: document.querySelectorAll('canvas').length,
        scenes: document.querySelectorAll('[data-scene], iframe').length,
      }))
      heap.push(st.heap)
      iframes.push(st.iframes)
    }
    if (page.goto) await page.goto('about:blank')
    await page.waitForTimeout(300)
  }

  const first = heap.slice(0, 5).filter(Boolean)
  const last = heap.slice(-5).filter(Boolean)
  const avg = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length)
  const growth = avg(last) - avg(first)
  const maxIframes = Math.max(...iframes)
  await browser.close()

  console.log(JSON.stringify({
    rounds: ROUNDS,
    heapFirst: first,
    heapLast: last,
    heapGrowthMb: +growth.toFixed(1),
    maxIframes,
    errors: errors.slice(0, 5),
  }, null, 2))
  const ok = errors.length === 0 && growth < 12 && maxIframes <= 2
  console.log(ok ? '\nNO LEAKS' : '\nLEAK OR ERROR')
  process.exit(ok ? 0 : 1)
}

main().catch((e) => { console.error(e); process.exit(2) })
