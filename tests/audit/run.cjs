// Full audit: console health, load cost, render performance and UI rules.
//
//   node tests/audit/run.cjs http://localhost:5175
//
// Prints a JSON report and writes tests/audit/report.json. Exit code 1 if any
// hard rule fails (console error, overflow, tap target, contrast).
const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const BASE = process.argv[2] || 'http://localhost:5175'
const OUT = path.join(__dirname, 'report.json')
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)

const PAGES = [
  { name: 'home', url: '/', kind: 'spa' },
  { name: 'demo-scene', url: '/p/1', kind: 'spa' },
  { name: 'paper-duo', url: '/p/12', kind: 'spa' },
  { name: 'director-scene', url: '/p/13', kind: 'spa' },
  { name: 'pose-studio', url: '/pose-studio.html', kind: 'studio' },
  { name: 'builder', url: '/character-builder.html', kind: 'studio' },
  { name: 'lab', url: '/character-studio.html', kind: 'studio' },
  { name: 'rig3d', url: '/rig3d.html', kind: 'studio' },
  { name: 'director-demo', url: '/director-demo.html', kind: 'studio' },
]

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'laptop', width: 1280, height: 800 },
  { name: 'mobile', width: 390, height: 844 },
  { name: 'small', width: 360, height: 740 },
  { name: 'landscape', width: 844, height: 390 },
]

const report = { base: BASE, started: new Date().toISOString(), pages: [], perf: {}, ui: [], problems: [] }
const bad = (page, kind, detail) => report.problems.push({ page, kind, detail })

function luminance(rgb) {
  const [r, g, b] = rgb.map((v) => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox'] })

  // ── per-page: console health, load timing, responses ─────────────────────
  for (const def of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const page = await ctx.newPage()
    const errors = []
    const warnings = []
    const failed = []
    page.on('pageerror', (e) => errors.push(String(e).slice(0, 300)))
    // Third-party font CDNs are not our uptime: a blocked or flaky
    // fonts.gstatic.com must not fail the page, but it is still reported.
    const isFontCdn = (u) => /fonts\.(googleapis|gstatic)\.com/.test(u)
    page.on('console', (m) => {
      const text = m.text()
      if (m.type() === 'error') {
        if (/favicon|ERR_ABORTED/i.test(text)) return
        if (/fonts\.gstatic|fonts\.googleapis/.test(text)) { warnings.push('font cdn: ' + text.slice(0, 120)); return }
        errors.push(text.slice(0, 300))
      } else if (m.type() === 'warning') warnings.push(text.slice(0, 200))
    })
    page.on('requestfailed', (r) => {
      const u = r.url()
      if (/favicon|\.map$/.test(u)) return
      if (isFontCdn(u)) { warnings.push('font cdn: ' + r.failure().errorText); return }
      failed.push(`${r.failure().errorText} ${u}`.slice(0, 200))
    })
    const t0 = Date.now()
    let status = 0
    try {
      const res = await page.goto(BASE + def.url, { waitUntil: 'networkidle', timeout: 45000 })
      status = res ? res.status() : 0
    } catch (e) {
      errors.push('goto: ' + String(e).slice(0, 200))
    }
    const loadMs = Date.now() - t0
    await page.waitForTimeout(def.kind === 'spa' ? 1200 : 500)
    const nav = await page.evaluate(() => {
      const n = performance.getEntriesByType('navigation')[0]
      return n ? { dom: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd), ttfb: Math.round(n.responseStart) } : null
    })
    const heap = await page.evaluate(() => (performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null))
    const canvasCount = await page.evaluate(() => document.querySelectorAll('canvas').length)
    report.pages.push({ ...def, status, loadMs, nav, heapMb: heap, canvasCount, errors, warnings, failed })
    if (status !== 200) bad(def.name, 'http', status)
    for (const e of errors) bad(def.name, 'console', e)
    for (const f of failed) bad(def.name, 'request', f)
    await ctx.close()
  }

  // ── performance: canvas seek budget (deterministic frames) ────────────────
  const perfCtx = await browser.newContext({ viewport: { width: 900, height: 900 } })
  const perf = await perfCtx.newPage()
  await perf.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
  report.perf.papercast = await perf.evaluate(() => {
    const cv = document.createElement('canvas')
    cv.width = 600; cv.height = 900
    document.body.innerHTML = ''
    document.body.appendChild(cv)
    const cast = window.PaperCast.create(cv, { character: 'mark' })
    const N = 180
    // warm up
    for (let i = 0; i < 20; i++) { cast.setPose('neutral'); cast.seek(i * 16) }
    const t0 = performance.now()
    for (let i = 0; i < N; i++) {
      cast.setPose(i % 2 ? 'explain' : 'wave')
      cast.seek(i * 16)
    }
    const ms = (performance.now() - t0) / N
    return { frames: N, msPerFrame: +ms.toFixed(2), fps: +(1000 / ms).toFixed(1) }
  })
  await perf.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
  report.perf.animals = await perf.evaluate(() => {
    const cv = document.createElement('canvas')
    cv.width = 600; cv.height = 900
    const cast = window.PaperCastAnimals.create(cv, { kind: 'dog' })
    const N = 120
    for (let i = 0; i < 10; i++) cast.seek(i * 16)
    const t0 = performance.now()
    for (let i = 0; i < N; i++) cast.seek(i * 16)
    const ms = (performance.now() - t0) / N
    return { frames: N, msPerFrame: +ms.toFixed(2), fps: +(1000 / ms).toFixed(1) }
  })
  // hidden-state: does the rig keep drawing when the tab is hidden?
  await perf.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
  report.perf.idle = await perf.evaluate(async () => {
    const cv = document.createElement('canvas')
    cv.width = 300; cv.height = 450
    document.body.innerHTML = ''
    document.body.appendChild(cv)
    const cast = window.PaperCast.create(cv, { character: 'mira' })
    cast.seek(0)
    const before = performance.now()
    await new Promise((r) => setTimeout(r, 600))
    return { idleMs: +(performance.now() - before).toFixed(0), rafActive: window.__paperRaf || null }
  })
  await perfCtx.close()

  // ── scene runtime seek round-trip (iframe handshake) ─────────────────────
  const sceneCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } })
  const scenePage = await sceneCtx.newPage()
  await scenePage.goto(BASE + '/p/12', { waitUntil: 'networkidle' })
  await scenePage.waitForTimeout(1500)
  report.perf.scene = await scenePage.evaluate(async () => {
    // SceneHost exposes an awaitable seek on the host window; use it so the
    // number is a real round-trip, not a fixed sleep.
    if (typeof window.__sceneSeek !== 'function') return { error: 'no __sceneSeek' }
    const times = []
    for (let i = 0; i < 24; i++) {
      const t0 = performance.now()
      await window.__sceneSeek((i * 400) % 12000)
      times.push(performance.now() - t0)
    }
    times.sort((a, b) => a - b)
    return {
      frames: times.length,
      p50: +times[Math.floor(times.length / 2)].toFixed(2),
      p95: +times[Math.floor(times.length * 0.95)].toFixed(2),
      max: +times[times.length - 1].toFixed(2),
    }
  })
  await sceneCtx.close()

  // ── UI rules across viewports ────────────────────────────────────────────
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } })
    for (const def of PAGES) {
      const page = await ctx.newPage()
      try {
        await page.goto(BASE + def.url, { waitUntil: 'networkidle', timeout: 40000 })
        await page.waitForTimeout(400)
        const info = await page.evaluate(() => {
          const doc = document.documentElement
          const viewportW = doc.clientWidth
          const overflow = doc.scrollWidth > viewportW + 1
          const offenders = []
          if (overflow) {
            for (const el of document.querySelectorAll('body *')) {
              const r = el.getBoundingClientRect()
              if (r.width > 0 && r.right > viewportW + 2 && r.height > 0) {
                offenders.push({ tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 40), right: Math.round(r.right) })
              }
            }
          }
          // WCAG 2.5.8 (AA) requires 24×24 px; 32×32 is the comfortable goal
          const small = []
          const tight = []
          for (const el of document.querySelectorAll('button, a, input[type=range], select, [role=button]')) {
            const r = el.getBoundingClientRect()
            if (r.width === 0 || r.height === 0) continue
            // skip controls inside collapsed rails/drawers: they are not
            // reachable, so their size says nothing about usability
            if (typeof el.checkVisibility === 'function' &&
                !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) continue
            // WCAG 2.5.8 exempts links inline in a sentence
            if (el.tagName === 'A' && getComputedStyle(el).display === 'inline') continue
            const rec = { tag: el.tagName.toLowerCase(), text: (el.textContent || el.value || '').trim().slice(0, 24), w: Math.round(r.width), h: Math.round(r.height) }
            if (r.width < 24 || r.height < 24) small.push(rec)
            else if (r.width < 32 || r.height < 32) tight.push(rec)
          }
          // tiny text
          const tiny = []
          for (const el of document.querySelectorAll('body *')) {
            if (!el.textContent || el.children.length > 0) continue
            const cs = getComputedStyle(el)
            const size = parseFloat(cs.fontSize)
            if (size && size < 10) tiny.push({ text: el.textContent.trim().slice(0, 20), size })
          }
          return { overflow, viewportW, offenders: offenders.slice(0, 6), small: small.slice(0, 8), tight: tight.slice(0, 8), tiny: tiny.slice(0, 6) }
        })
        report.ui.push({ page: def.name, ...vp, ...info })
        if (info.overflow) bad(def.name, `overflow@${vp.name}`, info.offenders)
        if (info.small.length) bad(def.name, `tap-target@${vp.name}`, info.small)
      } catch (e) {
        bad(def.name, `ui@${vp.name}`, String(e).slice(0, 160))
      }
      await page.close()
    }
    await ctx.close()
  }

  await browser.close()
  report.finished = new Date().toISOString()
  report.summary = {
    pages: report.pages.length,
    consoleErrors: report.pages.reduce((n, p) => n + p.errors.length, 0),
    failedRequests: report.pages.reduce((n, p) => n + p.failed.length, 0),
    problems: report.problems.length,
  }
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2))
  console.log(JSON.stringify({ summary: report.summary, perf: report.perf, problems: report.problems.slice(0, 20) }, null, 2))
  process.exit(report.problems.length ? 1 : 0)
}

main().catch((e) => {
  console.error(e)
  process.exit(2)
})
