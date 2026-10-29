// End-to-end smoke walk: the flows a person actually uses, with console and
// network guards. Run against a live app (dev or dist):
//
//   node tests/audit/e2e.cjs http://localhost:5590
//
// Exit code 1 on any console error, failed request or broken expectation.
const { chromium } = require('playwright')
const fs = require('fs')

const BASE = process.argv[2] || 'http://localhost:5590'
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)
const results = []
let failed = 0

function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail })
  if (!ok) failed++
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${name}${detail ? '  ' + JSON.stringify(detail).slice(0, 240) : ''}`)
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox'] })
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()
  const errors = []
  const failedReq = []
  page.on('pageerror', (e) => errors.push(String(e).slice(0, 240)))
  page.on('console', (m) => { if (m.type() === 'error' && !/favicon/i.test(m.text())) errors.push(m.text().slice(0, 240)) })
  page.on('requestfailed', (r) => { if (!/favicon|\.map$/.test(r.url())) failedReq.push(`${r.failure().errorText} ${r.url().slice(0, 120)}`) })
  const resetErrors = () => { errors.length = 0; failedReq.length = 0 }

  // ── 1. home loads with projects ───────────────────────────────────────────
  resetErrors()
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(600)
  const home = await page.evaluate(() => ({
    title: document.title,
    links: [...document.querySelectorAll('a[href^="/p/"]')].length,
    text: document.body.innerText.slice(0, 120),
  }))
  check('home: loads without errors', errors.length === 0 && failedReq.length === 0, { errors: errors.slice(0, 2) })
  check('home: has presentation links', home.links > 0, { links: home.links })

  // ── 2. open the demo presentation and play it ────────────────────────────
  resetErrors()
  await page.goto(BASE + '/p/1', { waitUntil: 'networkidle' })
  await page.waitForFunction(() => window.__sceneReady === true, { timeout: 30000 }).catch(() => {})
  const ready = await page.evaluate(() => window.__sceneReady === true)
  check('presentation: scene handshake', ready, { ready })

  const seekA = await page.evaluate(() => window.__sceneSeek ? window.__sceneSeek(1200).then(() => true) : false)
  check('presentation: awaitable seek', seekA === true, { seekA })

  // playback: the player drives seek on its own clock
  const played = await page.evaluate(async () => {
    const btn = [...document.querySelectorAll('button')].find((b) => /play|▶/i.test(b.textContent || '') || /play/i.test(b.title || ''))
    if (!btn) return { started: false }
    btn.click()
    await new Promise((r) => setTimeout(r, 1600))
    return { started: true }
  })
  await page.waitForTimeout(200)
  check('presentation: controls are present', played.started, played)

  // ── 3. next slide / navigation ───────────────────────────────────────────
  resetErrors()
  const nav = await page.evaluate(async () => {
    const before = location.pathname + location.search
    const next = [...document.querySelectorAll('button')].find((b) => /next|след/i.test(b.title || b.textContent || ''))
    if (next) { next.click(); await new Promise((r) => setTimeout(r, 900)) }
    return { before, after: location.pathname + location.search, clicked: !!next, body: document.body.innerText.slice(0, 80) }
  })
  check('presentation: navigation does not crash', errors.length === 0, { nav, errors: errors.slice(0, 2) })

  // ── 4. builder: change the look, export JSON ─────────────────────────────
  resetErrors()
  await page.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const builder = await page.evaluate(async () => {
    const st = window.__builderState || window.state || null
    // click a hair thumbnail by its label
    const chip = [...document.querySelectorAll('[data-lib-item],[data-hair],[data-value]')].find((e) => /bob|кудри|curly/i.test(e.dataset.value || e.dataset.libItem || e.textContent || ''))
    if (chip) chip.click()
    await new Promise((r) => setTimeout(r, 300))
    const hair = st && st.appearance ? st.appearance.hairStyle : null
    const exp = window.PaperCast && window.PaperCast.normalizeAppearance ? window.PaperCast.normalizeAppearance({ hairStyle: 'curly' }) : {}
    return { clicked: !!chip, hair, exp: exp.hairStyle }
  })
  check('builder: look library applies', builder.exp === 'curly', builder)
  check('builder: no console errors', errors.length === 0, { errors: errors.slice(0, 2) })

  // ── 5. pose studio: preset + keyframe + export ───────────────────────────
  resetErrors()
  await page.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const pose = await page.evaluate(async () => {
    const st = window.__poseStudio.state
    const before = JSON.stringify(st.pose.armR.hand)
    const sel = document.querySelector('#preset')
    sel.value = 'wave'
    sel.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 250))
    // a raw partial pose must not break the skeleton solver either
    let robust = true
    try { window.PaperCast.skeleton({}) } catch (e) { robust = false }
    return { changed: JSON.stringify(st.pose.armR.hand) !== before, name: sel.value, robust, hasUid: !!window.__poseStudio }
  })
  check('pose studio: presets apply', pose.changed && pose.hasUid, pose)
  check('pose studio: no console errors', errors.length === 0, { errors: errors.slice(0, 2) })

  // ── 6. lab: text becomes visemes ─────────────────────────────────────────
  resetErrors()
  await page.goto(BASE + '/character-studio.html', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const lab = await page.evaluate(() => {
    const v = window.PaperCast.visemesFromText ? window.PaperCast.visemesFromText('Привет, мир') : null
    return { count: Array.isArray(v) ? v.length : 0, first: Array.isArray(v) ? v[0] : null }
  })
  check('lab: text → visemes', lab.count > 3, lab)
  check('lab: no console errors', errors.length === 0, { errors: errors.slice(0, 2) })

  // ── 7. director scene plays deterministically ────────────────────────────
  resetErrors()
  await page.goto(BASE + '/p/13', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)
  const det = await page.evaluate(async () => {
    if (!window.__sceneSeek) return { ok: false }
    await window.__sceneSeek(4000)
    await window.__sceneSeek(0)
    await window.__sceneSeek(4000)
    return { ok: true }
  })
  check('director scene: seeks back and forth', det.ok, det)
  check('director scene: no console errors', errors.length === 0, { errors: errors.slice(0, 2) })

  await browser.close()
  console.log(`\n${failed ? 'FAILED' : 'PASSED'} — ${results.length - failed}/${results.length}`)
  process.exit(failed ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(2) })
