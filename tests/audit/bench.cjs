// Performance benchmark with medians (single warm-up, interleaved runs).
//
//   node tests/audit/bench.cjs http://localhost:5590            # report
//   node tests/audit/bench.cjs http://localhost:5590 --check    # vs baseline
//   node tests/audit/bench.cjs http://localhost:5590 --save     # new baseline
//
// Metrics are milliseconds per frame. `--check` fails when a metric is more
// than 2.5× slower than the stored baseline (a regression, not machine noise).
const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const BASE = process.argv[2] || 'http://localhost:5590'
const MODE = process.argv.includes('--save') ? 'save' : process.argv.includes('--check') ? 'check' : 'report'
const BASELINE = path.join(__dirname, 'baseline.json')
const TOLERANCE = 2.5
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)

function median(values) {
  const s = values.slice().sort((a, b) => a - b)
  return s[Math.floor(s.length / 2)]
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox'] })
  const out = {}

  // PaperCast: one character, the classic 600×900 studio canvas
  const p1 = await browser.newPage({ viewport: { width: 900, height: 950 } })
  await p1.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
  out['papercast-600x900'] = await p1.evaluate(() => {
    const cv = document.createElement('canvas')
    cv.width = 600; cv.height = 900
    document.body.innerHTML = ''
    document.body.appendChild(cv)
    const cast = window.PaperCast.create(cv, { character: 'mark' })
    const N = 90
    for (let i = 0; i < 20; i++) { cast.setPose('wave'); cast.seek(i * 16) }
    const runs = []
    for (let r = 0; r < 5; r++) {
      const t0 = performance.now()
      for (let i = 0; i < N; i++) { cast.setPose(i % 2 ? 'explain' : 'wave'); cast.seek(i * 16) }
      runs.push((performance.now() - t0) / N)
    }
    runs.sort((a, b) => a - b)
    return +runs[2].toFixed(2)
  })

  // Animals: one dog
  await p1.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
  out['animals-dog'] = await p1.evaluate(() => {
    const cv = document.createElement('canvas')
    cv.width = 600; cv.height = 900
    document.body.innerHTML = ''
    document.body.appendChild(cv)
    const cast = window.PaperCastAnimals.create(cv, { kind: 'dog' })
    const N = 90
    for (let i = 0; i < 20; i++) cast.seek(i * 16)
    const runs = []
    for (let r = 0; r < 5; r++) {
      const t0 = performance.now()
      for (let i = 0; i < N; i++) cast.seek(i * 16)
      runs.push((performance.now() - t0) / N)
    }
    runs.sort((a, b) => a - b)
    return +runs[2].toFixed(2)
  })
  await p1.close()

  // PaperCastStage: two actors + room + captions
  const p2 = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  await p2.goto(BASE + '/director-demo.html', { waitUntil: 'networkidle' })
  await p2.waitForTimeout(600)
  out['stage-2-actors'] = await p2.evaluate(() => {
    const med = (v) => { const s = v.slice().sort((a, b) => a - b); return s[Math.floor(s.length / 2)] }
    const d = window.__director
    for (let i = 0; i < 15; i++) d.seek(i * 60)
    const runs = []
    for (let r = 0; r < 5; r++) {
      const t = []
      for (let i = 0; i < 60; i++) {
        const t0 = performance.now()
        d.seek((i * 41) % 12000)
        t.push(performance.now() - t0)
      }
      runs.push(med(t))
    }
    runs.sort((a, b) => a - b)
    return +runs[2].toFixed(2)
  })
  await p2.close()

  // Scene runtime: awaitable seek round-trip (includes the iframe hop)
  const p3 = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  await p3.goto(BASE + '/p/12', { waitUntil: 'networkidle' })
  await p3.waitForFunction(() => window.__sceneReady === true, { timeout: 30000 }).catch(() => {})
  out['scene-seek-p50'] = await p3.evaluate(async () => {
    if (!window.__sceneSeek) return null
    const med = (v) => { const s = v.slice().sort((a, b) => a - b); return s[Math.floor(s.length / 2)] }
    const t = []
    for (let i = 0; i < 24; i++) {
      const t0 = performance.now()
      await window.__sceneSeek((i * 400) % 12000)
      t.push(performance.now() - t0)
    }
    return +med(t).toFixed(2)
  })
  await p3.close()
  await browser.close()

  // ── report / compare ─────────────────────────────────────────────────────
  const keys = Object.keys(out).filter((k) => typeof out[k] === 'number')
  console.log('metric                 ms/frame')
  for (const k of keys) console.log(k.padEnd(22), String(out[k]).padStart(8))

  if (MODE === 'save') {
    fs.writeFileSync(BASELINE, JSON.stringify({ saved: new Date().toISOString(), metrics: out }, null, 2) + '\n')
    console.log(`\nbaseline saved to ${path.relative(process.cwd(), BASELINE)}`)
    return
  }
  if (MODE === 'check') {
    if (!fs.existsSync(BASELINE)) {
      console.log('\nno baseline yet — run with --save first')
      process.exit(0)
    }
    const base = JSON.parse(fs.readFileSync(BASELINE, 'utf8')).metrics || {}
    let bad = 0
    for (const k of keys) {
      if (!(k in base)) continue
      const ratio = out[k] / base[k]
      const ok = ratio <= TOLERANCE
      if (!ok) bad++
      console.log(`${ok ? 'ok  ' : 'FAIL'}  ${k}: ${out[k]} ms vs ${base[k]} ms (${ratio.toFixed(1)}×)`)
    }
    console.log(`\n${bad ? 'PERF REGRESSION' : 'within budget'} (tolerance ${TOLERANCE}×)`)
    process.exit(bad ? 1 : 0)
  }
}

main().catch((e) => { console.error(e); process.exit(2) })
