// Contrast audit (WCAG 2.1 AA): text vs its effective background.
//
//   node tests/audit/contrast.cjs http://localhost:5590
//
// Report-only by default; `--fail` exits 1 when a real violation is found.
// Elements over gradients/images are skipped (the effective background is not
// computable without a screenshot sample), so this never flags false positives
// from decorative layers.
const { chromium } = require('playwright')
const fs = require('fs')

const BASE = process.argv[2] || 'http://localhost:5590'
const FAIL = process.argv.includes('--fail')
const CHROME = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)

const PAGES = ['/', '/p/1', '/p/12', '/pose-studio.html', '/character-builder.html', '/character-studio.html', '/rig3d.html', '/director-demo.html']

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME, args: ['--no-sandbox'] })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const report = []
  for (const url of PAGES) {
    await page.goto(BASE + url, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.waitForTimeout(1500)
    const rows = await page.evaluate(() => {
      const parse = (c) => {
        const m = c.match(/rgba?\(([^)]+)\)/)
        if (!m) return null
        const p = m[1].split(',').map((v) => parseFloat(v))
        return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }
      }
      const lum = ({ r, g, b }) => {
        const f = (v) => {
          const c = v / 255
          return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
      }
      const ratio = (a, b) => {
        const la = lum(a), lb = lum(b)
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
      }
      const mix = (fg, bg) => ({
        r: fg.r * fg.a + bg.r * (1 - fg.a),
        g: fg.g * fg.a + bg.g * (1 - fg.a),
        b: fg.b * fg.a + bg.b * (1 - fg.a),
        a: 1,
      })
      const out = []
      for (const el of document.querySelectorAll('body *')) {
        if (el.children.length > 0) continue
        const text = (el.textContent || '').trim()
        if (!text || text.length < 2) continue
        const cs = getComputedStyle(el)
        if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.1) continue
        if (typeof el.checkVisibility === 'function' && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) continue
        // decorative thumbnails (a mock UI inside a project card) are not text
        if (el.closest('[data-audit-ignore]')) continue
        const fg = parse(cs.color)
        if (!fg) continue
        // walk up for the first opaque background
        let bg = null
        let node = el
        let guard = 0
        while (node && guard++ < 12) {
          const bs = getComputedStyle(node)
          if (bs.backgroundImage && bs.backgroundImage !== 'none') { bg = null; break }
          const c = parse(bs.backgroundColor)
          if (c && c.a > 0.6) { bg = c; break }
          node = node.parentElement
        }
        if (!bg) continue
        const fgM = fg.a < 1 ? mix(fg, bg) : fg
        const r = ratio(fgM, bg)
        const size = parseFloat(cs.fontSize)
        const weight = parseInt(cs.fontWeight, 10) || 400
        const large = size >= 24 || (size >= 18.66 && weight >= 700)
        const need = large ? 3 : 4.5
        if (r < need) {
          out.push({
            text: text.slice(0, 40),
            cls: (el.className || '').toString().slice(0, 30),
            tag: el.tagName.toLowerCase(),
            ratio: +r.toFixed(2),
            need,
            size: Math.round(size),
            color: cs.color,
            bg: `rgb(${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)})`,
          })
        }
      }
      return out
    })
    report.push({ url, violations: rows })
  }
  await browser.close()

  let total = 0
  for (const r of report) {
    total += r.violations.length
    console.log(`${r.violations.length ? 'FAIL' : 'ok  '}  ${r.url.padEnd(26)} ${r.violations.length} violations`)
    for (const v of r.violations.slice(0, 8)) {
      console.log(`      ${v.ratio}:1 (need ${v.need}) ${v.size}px ${v.tag}.${v.cls} "${v.text}" ${v.color} on ${v.bg}`)
    }
  }
  console.log(`\n${total} contrast violations`)
  if (FAIL && total) process.exit(1)
}

main().catch((e) => { console.error(e); process.exit(2) })
