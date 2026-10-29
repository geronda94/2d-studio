// Golden frames: visual regression of the character art.
//
//   node tests/qa/golden.cjs http://localhost:5590           # check
//   node tests/qa/golden.cjs http://localhost:5590 --update  # rewrite goldens
//
// Each frame is rendered deterministically into a 200×300 canvas (dpr 1). The
// comparison decodes the stored PNG in the browser and counts pixels that
// differ by more than 12/255 in any channel: up to 1.5 % of the frame may
// change (antialiasing, a moved hair strand), anything more fails.
const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const BASE = process.argv[2] || 'http://localhost:5590'
const UPDATE = process.argv.includes('--update')
const DIR = path.join(__dirname, 'golden')
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)

const W = 200
const H = 300
const DIFF_LIMIT = 0.015

// A spread of what people actually look at: both skins, dress, profile, beard,
// animals, gestures and the 3/4 turn.
const FRAMES = [
  { name: 'mark-front', opts: { character: 'mark' } },
  { name: 'mark-wave', opts: { character: 'mark', pose: 'wave' } },
  { name: 'mark-explain', opts: { character: 'mark', pose: 'explain' } },
  { name: 'mark-beard-long', opts: { character: 'mark', appearance: { beardStyle: 'long', faceShape: 'square' } } },
  { name: 'mark-jacket', opts: { character: 'mark', appearance: { outfit: 'jacket' } } },
  { name: 'mira-front', opts: { character: 'mira' } },
  { name: 'mira-dress', opts: { character: 'mira', appearance: { outfit: 'dress' } } },
  { name: 'mira-3q', opts: { character: 'mira', yaw: 0.55 } },
  { name: 'mira-profile-left', opts: { character: 'mira', yaw: -1 } },
  { name: 'mark-spine', opts: { character: 'mark', pose: { fk: { spine: 16 } } } },
  { name: 'mark-knee-bend', opts: { character: 'mark', pose: { fk: { kneeL: -70, elbowR: -60 } } } },
]

async function renderAll(page) {
  return page.evaluate(({ frames, W, H }) => {
    const cv = document.createElement('canvas')
    cv.width = W
    cv.height = H
    document.body.innerHTML = ''
    document.body.style.cssText = 'margin:0;background:#e9e4d8'
    document.body.appendChild(cv)
    const out = {}
    for (const f of frames) {
      const cast = window.PaperCast.create(cv, Object.assign({ yaw: 0 }, f.opts))
      cast.setYaw(f.opts.yaw || 0)
      cast.seek(0)
      out[f.name] = cv.toDataURL('image/png')
    }
    return out
  }, { frames: FRAMES, W, H })
}

async function compare(page, rendered) {
  return page.evaluate(async ({ rendered, W, H }) => {
    const load = (src) => new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = src
    })
    const dataOf = (img) => {
      const c = document.createElement('canvas')
      c.width = W; c.height = H
      const g = c.getContext('2d')
      g.drawImage(img, 0, 0, W, H)
      return g.getImageData(0, 0, W, H).data
    }
    const res = {}
    for (const [name, png] of Object.entries(rendered)) {
      const img = await load(png)
      res[name] = dataOf(img)
    }
    return res
  }, { rendered, W, H })
}

function diffRatio(a, b) {
  let bad = 0
  const n = Math.min(a.length, b.length) / 4
  for (let i = 0; i < a.length; i += 4) {
    if (Math.abs(a[i] - b[i]) > 12 || Math.abs(a[i + 1] - b[i + 1]) > 12 || Math.abs(a[i + 2] - b[i + 2]) > 12) bad++
  }
  return bad / n
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 900, height: 900 } })
  await page.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
  const rendered = await renderAll(page)
  fs.mkdirSync(DIR, { recursive: true })

  let failed = 0
  if (UPDATE) {
    for (const [name, png] of Object.entries(rendered)) {
      fs.writeFileSync(path.join(DIR, `${name}.png`), Buffer.from(png.split(',')[1], 'base64'))
    }
    console.log(`updated ${Object.keys(rendered).length} golden frames → ${path.relative(process.cwd(), DIR)}`)
    await browser.close()
    return
  }

  // current renders as data URLs → compare against the stored PNGs
  for (const f of FRAMES) {
    const file = path.join(DIR, `${f.name}.png`)
    if (!fs.existsSync(file)) {
      console.log(`FAIL  ${f.name}: no golden (run --update)`)
      failed++
      continue
    }
    const golden = 'data:image/png;base64,' + fs.readFileSync(file).toString('base64')
    const cmp = await compare(page, { [f.name]: rendered[f.name] })
    const gold = await compare(page, { [f.name]: golden })
    const ratio = diffRatio(cmp[f.name], gold[f.name])
    const ok = ratio <= DIFF_LIMIT
    if (!ok) failed++
    console.log(`${ok ? 'ok  ' : 'FAIL'}  ${f.name}  changed ${(ratio * 100).toFixed(2)}%`)
  }
  await browser.close()
  console.log(`\n${failed ? 'VISUAL REGRESSION' : 'golden frames match'} — ${FRAMES.length - failed}/${FRAMES.length}`)
  process.exit(failed ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(2) })
