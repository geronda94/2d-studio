// Paper Cast QA — committed, repeatable checks.
//
//   npm i -D playwright && npx playwright install chromium
//   node tests/qa/run.mjs http://localhost:5175
//
// Exit code 1 on any failure. Prints a JSON report.

const { chromium } = require('playwright')
const fs = require('fs')

async function main() {
const BASE = process.argv[2] || 'http://localhost:5175'
const results = []
let failed = 0

function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail })
  if (!ok) failed++
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${name}${detail ? '  ' + JSON.stringify(detail).slice(0, 220) : ''}`)
}

const chromiumPath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium-browser') ? '/usr/bin/chromium-browser' : undefined)
const browser = await chromium.launch({
  headless: true,
  executablePath: chromiumPath,
  args: ['--no-sandbox'],
})

const page = await browser.newPage({ viewport: { width: 1400, height: 900 } })
const consoleErrors = []
page.on('pageerror', (e) => consoleErrors.push(String(e)))
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()) })

// ── pages load ─────────────────────────────────────────────────────────────
for (const path of ['/pose-studio.html', '/character-builder.html', '/character-studio.html', '/rig3d.html']) {
  consoleErrors.length = 0
  const res = await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 45000 })
  await page.waitForTimeout(500)
  const info = await page.evaluate(() => ({
    paper: !!window.PaperCast,
    canvas: !!document.querySelector('canvas'),
  }))
  check(`page ${path}`, res && res.ok() && info.paper && info.canvas && consoleErrors.length === 0, {
    status: res && res.status(), paper: info.paper, errors: consoleErrors.slice(0, 3),
  })
}

// ── version manifest ──────────────────────────────────────────────────────
await page.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
const versions = await page.evaluate(async () => ({
  manifest: await (await fetch('/vendor/versions.json')).json(),
  scripts: [...document.scripts].map((s) => s.getAttribute('src')).filter(Boolean),
}))
const scriptsJoin = versions.scripts.join(' ')
check('versions match manifest',
  scriptsJoin.includes(`paper-cast.js?v=${versions.manifest.paper}`) &&
  scriptsJoin.includes(`paper-cast-animals.js?v=${versions.manifest.animals}`),
  versions.manifest)

// ── rig determinism (poses, clips, animals) ───────────────────────────────
await page.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
const rig = await page.evaluate(async () => {
  const add = (src) => new Promise((ok, bad) => {
    const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = bad; document.head.appendChild(s)
  })
  if (!window.PaperCastAnimals) await add('/vendor/paper-cast-animals.js?v=5')
  const canvas = document.createElement('canvas')
  canvas.width = 600; canvas.height = 900
  canvas.style.cssText = 'position:fixed;left:-2000px;top:0;width:300px;height:450px'
  document.body.appendChild(canvas)

  const hash = () => canvas.toDataURL()
  const poses = Object.keys(PaperCast.POSES)
  let poseFail = []
  for (const name of poses) {
    const r = PaperCast.create(canvas, { character: 'mark', pose: name, life: false, autoGaze: false, blink: false })
    r.seek(700); const a = hash()
    r.seek(0); r.seek(700)
    if (hash() !== a) poseFail.push(name)
  }
  const clips = Object.keys(PaperCast.CLIPS)
  let clipFail = []
  for (const id of clips) {
    const r = PaperCast.create(canvas, { character: 'mark', life: false, autoGaze: false, blink: false })
    r.setClip(id, 0); r.seek(600); const a = hash()
    r.seek(0); r.seek(600)
    if (hash() !== a) clipFail.push(id)
  }
  const kinds = Object.keys(PaperCastAnimals.KINDS)
  let animalFail = []
  const cv2 = document.createElement('canvas')
  cv2.width = 600; cv2.height = 600
  cv2.style.cssText = 'position:fixed;left:-2000px;top:0;width:300px;height:300px'
  document.body.appendChild(cv2)
  for (const kind of kinds) {
    const posesA = PaperCastAnimals.POSES[kind] || ['stand']
    for (const pose of posesA) {
      const r = PaperCastAnimals.create(cv2, { kind, pose })
      r.seek(500); const a = cv2.toDataURL()
      r.seek(0); r.seek(500)
      if (cv2.toDataURL() !== a) animalFail.push(kind + ':' + pose)
    }
  }
  const norm = PaperCast.normalizePose({ body: { x: 5 } })
  return {
    poses: poses.length, poseFail,
    clips: clips.length, clipFail,
    kinds: kinds.length, animalFail,
    schema: PaperCast.POSE_SCHEMA,
    normalized: !!(norm && norm.fk && norm.legL && norm.armR),
    skeleton3D: (() => {
      const sk = PaperCast.skeleton3D('neutral', Math.PI / 2)
      const sk2 = PaperCast.skeleton3D('neutral', -Math.PI / 2)
      return !!(sk && sk.head && sk.head.length === 3 &&
        Math.abs(sk.shL[2]) > 1 && Math.sign(sk.shL[2]) !== Math.sign(sk2.shL[2]))
    })(),
    animalSkeleton: (() => {
      const sk = PaperCastAnimals.skeleton('dog', 'stand', 0, 'walk', 0, {})
      return !!(sk && sk.joints && sk.joints.head && sk.legs && sk.legs.fl && sk.legs.fl.knee)
    })(),
    profile: (() => {
      const r = PaperCast.create(cv2, { kind: 'human', character: 'mark', pose: 'neutral' })
      r.setYaw(1); r.seek(500)
      const a = cv2.toDataURL()
      r.seek(0); r.seek(500)
      const sk = PaperCast.skeleton('neutral', 1)
      return { deterministic: a === cv2.toDataURL(), profile: !!sk.profile, byName: !!sk.head }
    })(),
    insectFK: (() => {
      const a = PaperCastAnimals.skeleton('beetle', 'stand', 0, null, 0, {})
      const b = PaperCastAnimals.skeleton('beetle', 'stand', 0, null, 0, { l3Hip: 30 })
      const legs = a && a.legs ? Object.keys(a.legs).length : 0
      const moved = a.legs.l3 && b.legs.l3 && (a.legs.l3.foot[0] !== b.legs.l3.foot[0] || a.legs.l3.foot[1] !== b.legs.l3.foot[1])
      return { legs, moved: !!moved }
    })(),
  }
})
check('31 poses deterministic', rig.poses === 31 && rig.poseFail.length === 0, { count: rig.poses, failed: rig.poseFail })
check('9 clips deterministic', rig.clips === 9 && rig.clipFail.length === 0, { count: rig.clips, failed: rig.clipFail })
check('10 animals deterministic', rig.kinds === 10 && rig.animalFail.length === 0, { count: rig.kinds, failed: rig.animalFail })
check('pose schema + normalize', rig.schema === 2 && rig.normalized, { schema: rig.schema })
check('animal skeleton joints', rig.animalSkeleton, { animalSkeleton: rig.animalSkeleton })
check('3D skeleton projection', rig.skeleton3D, { skeleton3D: rig.skeleton3D })
check('insect FK (6 legs, hip moves foot)', rig.insectFK.legs === 6 && rig.insectFK.moved, rig.insectFK)
check('profile side view deterministic', rig.profile.deterministic && rig.profile.profile && rig.profile.byName, rig.profile)

// ── anatomy + look validators ─────────────────────────────────────────────
const viz = await page.evaluate(() => {
  const P = window.PaperCast
  const dress = P.normalizeAppearance({ outfit: 'dress', bottom: 'pants' })
  const report = P.validateAppearance({ outfit: 'dress', bottom: 'pants' })
  const neutral = P.normalizeAppearance({ outfit: 'shirt', bottom: 'pants' })
  const an = P.anatomyReport(P.POSES.neutral)
  return {
    dressBottom: dress.bottom,
    reportBlocked: report.ok === false && report.issues.some((i) => i.code === 'dress-bottom'),
    neutralHair: neutral.hairStyle,
    elbow: P.jointRange('elbow', 'flex'),
    kneeClamp: P.clampJoint('knee', 'flex', 200),
    wristClamp: P.clampJoint('wrist', 'flex', 120),
    neutralAnatomy: an.every((r) => r.ok),
    finger: P.fingerCurl(1),
    variety: {
      patterns: P.PATTERNS.length,
      accessories: P.ACCESSORIES.length,
      glasses: P.GLASSES_STYLES.length,
      afro: P.HAIR_STYLES.includes('afro'),
      longBeard: P.BEARD_STYLES.includes('long'),
      badPattern: P.normalizeAppearance({ pattern: 'nope' }).pattern,
      badAccessory: P.normalizeAppearance({ accessory: 'nope' }).accessory,
      sweater: P.OUTFITS.includes('sweater'),
      faces: P.FACE_SHAPES.length,
      badFace: P.normalizeAppearance({ faceShape: 'nope' }).faceShape,
    },
  }
})
check('look validators + anatomy ranges',
  viz.dressBottom === 'dress' && viz.reportBlocked && viz.neutralHair === undefined &&
  viz.elbow[0] === 0 && viz.elbow[1] === 150 && viz.kneeClamp === 135 && viz.wristClamp === 70 &&
  viz.neutralAnatomy && viz.finger.mcp === 90 && viz.finger.pip === 100 &&
  viz.variety.patterns === 4 && viz.variety.accessories === 5 && viz.variety.glasses === 3 &&
  viz.variety.faces === 4 && viz.variety.badFace === 'oval' &&
  viz.variety.afro && viz.variety.longBeard && viz.variety.sweater &&
  viz.variety.badPattern === 'solid' && viz.variety.badAccessory === 'none',
  viz)

// ── pose studio: all joints visible + foot/hand controls work ────────────
await page.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
await page.waitForTimeout(400)
const joints = await page.evaluate(() => ({
  bones: [...document.querySelectorAll('#bones .bone')].filter((e) => e.style.display !== 'none').length,
  hands: [...document.querySelectorAll('#handles .handle')].filter((e) => e.style.display !== 'none').length,
  rings: [...document.querySelectorAll('#handles .rot')].filter((e) => e.style.display !== 'none').length,
  fingers: document.querySelectorAll('#fingerbar [data-finger]').length,
}))
const foot = await page.evaluate(() => {
  const el = [...document.querySelectorAll('#bones .bone')].find((e) => e.dataset.label === 'стопа R')
  const r = el.getBoundingClientRect()
  return { x: r.x + r.width / 2, y: r.y + r.height / 2, swing: window.__poseStudio.state.pose.legR.swing }
})
await page.mouse.move(foot.x, foot.y)
await page.mouse.down()
await page.mouse.move(foot.x + 50, foot.y - 30, { steps: 6 })
await page.mouse.up()
await page.waitForTimeout(150)
const afterFoot = await page.evaluate(() => window.__poseStudio.state.pose.legR.swing)
await page.click('#fingerbar [data-hand="R"]')
await page.click('#fingerbar [data-finger="peace"]')
const afterFinger = await page.evaluate(() => window.__poseStudio.state.pose.armR.handPose)
check('pose studio: all joints + foot/fingers',
  joints.bones >= 12 && joints.hands === 2 && joints.rings === 2 && joints.fingers === 8 &&
  afterFoot !== foot.swing && afterFinger === 'peace',
  { joints, footSwing: [foot.swing, afterFoot], afterFinger })

// ── two axes per joint: swing the bone, then bend the joint ───────────────
const axis = await page.evaluate(() => {
  const st = window.__poseStudio.state
  const el = [...document.querySelectorAll('#bones .bone')].find((e) => e.dataset.label === 'колено L')
  const r = el.getBoundingClientRect()
  return { x: r.x + r.width / 2, y: r.y + r.height / 2, hip: st.pose.fk.hipL, knee: st.pose.fk.kneeL, sel: st.selJoint }
})
await page.mouse.move(axis.x, axis.y)
await page.mouse.down()
await page.mouse.move(axis.x + 60, axis.y - 10, { steps: 6 })
await page.mouse.up()
await page.waitForTimeout(120)
const afterSwing = await page.evaluate(() => ({ hip: window.__poseStudio.state.pose.fk.hipL, sel: window.__poseStudio.state.selJoint }))
const ring = await page.locator('#bones .axis-ring').boundingBox()
let afterBend = null
if (ring) {
  const rx = ring.x + ring.width / 2, ry = ring.y + ring.height / 2
  // the ring is a rotation handle: try both directions and keep the one that
  // moves the joint (a clamped direction is a no-op by design)
  for (const [dx, dy] of [[60, -20], [-60, 20], [-20, -70], [20, 70]]) {
    await page.mouse.move(rx, ry)
    await page.mouse.down()
    for (let i = 1; i <= 8; i++) await page.mouse.move(rx + (dx * i) / 8, ry + (dy * i) / 8)
    await page.mouse.up()
    await page.waitForTimeout(100)
    afterBend = await page.evaluate(() => window.__poseStudio.state.pose.fk.kneeL)
    if (afterBend !== axis.knee) break
  }
}
check('pose studio: two axes per joint',
  afterSwing.sel === 'kneeL' && afterSwing.hip !== axis.hip && !!ring && afterBend !== axis.knee,
  { swing: [axis.hip, afterSwing.hip], selected: afterSwing.sel, bend: [axis.knee, afterBend] })

// ── director (config timeline) ────────────────────────────────────────────
await page.goto(BASE + '/director-demo.html', { waitUntil: 'networkidle' })
await page.waitForTimeout(600)
const director = await page.evaluate(() => {
  const d = window.__director
  const cv = document.querySelector('#cv')
  d.seek(2000)
  const a = cv.toDataURL()
  d.seek(0); d.seek(2000)
  const b = cv.toDataURL()
  return {
    stage: !!window.PaperCastStage,
    duration: d.duration,
    deterministic: a === b && a.length > 1000,
    actors: d.config.cast.length,
    events: d.config.timeline.length,
    envs: window.PaperCastStage.ENVIRONMENTS.length,
    srt: (() => {
      const r = window.PaperCastStage.fromSRT('1\n00:00:01,000 --> 00:00:03,000\nmark: Привет\n\n2\n00:00:03,500 --> 00:00:06,000\nmira: Ответ', { tail: 500 })
      return r.timeline.length === 2 && r.captions.length === 2 && r.duration > 5000
    })(),
  }
})
check('director config timeline deterministic',
  director.stage && director.deterministic && director.duration === 12000 && director.actors === 2 && director.events > 5 && director.envs >= 3 && director.srt,
  director)

// ── mobile overflow ───────────────────────────────────────────────────────
const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
const mp = await mobile.newPage()
for (const path of ['/pose-studio.html', '/character-builder.html']) {
  await mp.goto(BASE + path, { waitUntil: 'networkidle' })
  await mp.waitForTimeout(400)
  const m = await mp.evaluate(() => ({
    sw: document.documentElement.scrollWidth,
    iw: window.innerWidth,
    handles: document.querySelectorAll('.handle, .bone').length,
  }))
  check(`mobile ${path} no h-scroll`, m.sw <= m.iw + 1, m)
}
await mobile.close()

// ── shared studio session (Lab / Pose / Builder / 3D) ─────────────────────
await page.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
await page.evaluate(() => localStorage.removeItem('papercast.session.v1'))
await page.reload({ waitUntil: 'networkidle' })
await page.selectOption('#base', 'mira')
await page.click('#hair-chips [data-hair="bob"]')
await page.selectOption('#pose', 'point')
await page.waitForTimeout(500)
const sessSaved = await page.evaluate(() => JSON.parse(localStorage.getItem('papercast.session.v1') || '{}'))
await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(300)
const sessRestored = await page.evaluate(() => ({
  base: document.querySelector('#base').value,
  hair: window.__builder.state.appearance.hairStyle,
  pose: document.querySelector('#pose').value,
  hairState: window.__builder.state.appearance.hairStyle,
}))
await page.goto(BASE + '/pose-studio.html?char=mira', { waitUntil: 'networkidle' })
const sessPose = await page.evaluate(() => ({
  char: document.querySelector('#char').value,
  name: window.__poseStudio.state.name,
}))
await page.goto(BASE + '/character-studio.html', { waitUntil: 'networkidle' })
const sessLab = await page.evaluate(() => ({
  active: window.__paperStudio.state.active,
  hairStyle: window.__paperStudio.state.appearance[window.__paperStudio.state.active].hairStyle,
}))
check('studio session shared across pages',
  sessSaved.active === 'mira' && sessSaved.pose === 'point' &&
  !!(sessSaved.skins && sessSaved.skins.mira && sessSaved.skins.mira.hairStyle === 'bob') &&
  sessRestored.base === 'mira' && sessRestored.hair === 'bob' &&
  sessRestored.pose === 'point' && sessRestored.hairState === 'bob' &&
  sessPose.char === 'mira' && sessPose.name === 'point' &&
  sessLab.active === 'mira' && sessLab.hairStyle === 'bob',
  { sessSaved: { active: sessSaved.active, pose: sessSaved.pose }, sessRestored, sessPose, sessLab })

await page.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
await page.evaluate(() => {
  document.querySelector('[data-tab=animal]').click()
  const k = document.querySelector('#kind')
  k.value = 'bee'
  k.dispatchEvent(new Event('change', { bubbles: true }))
  const s = document.querySelector('#a-skel')
  s.checked = true
  s.dispatchEvent(new Event('change', { bubbles: true }))
  const f = document.querySelector('#a-bones input[data-fk="l1Hip"]')
  f.value = '25'
  f.dispatchEvent(new Event('input', { bubbles: true }))
})
await page.waitForTimeout(600)
await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(300)
const sessAnimal = await page.evaluate(() => ({
  mode: window.__builder.state.mode,
  kind: window.__builder.state.animal.kind,
  fk: window.__builder.state.animal.fk.l1Hip,
  slider: document.querySelector('#a-bones input[data-fk="l1Hip"]').value,
  kindSelect: document.querySelector('#kind').value,
}))
check('studio session restores animal + FK',
  sessAnimal.mode === 'animal' && sessAnimal.kind === 'bee' && sessAnimal.fk === 25 &&
  sessAnimal.slider === '25' && sessAnimal.kindSelect === 'bee',
  sessAnimal)
await page.evaluate(() => localStorage.removeItem('papercast.session.v1'))

// ── visual library previews ───────────────────────────────────────────────
await page.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
await page.evaluate(() => { localStorage.removeItem('papercast.session.v1'); sessionStorage.clear() })
await page.reload({ waitUntil: 'networkidle' })
await page.waitForFunction(
  () => [...document.querySelectorAll('.libitem img')].filter((i) => i.src.startsWith('data:')).length >= 55,
  { timeout: 12000 },
).catch(() => {})
await page.waitForTimeout(300)
const lib = await page.evaluate(() => ({
  items: document.querySelectorAll('.libitem').length,
  thumbs: [...document.querySelectorAll('.libitem img')].filter((i) => i.src.startsWith('data:')).length,
}))
await page.click('#tabs [data-tab="outfit"]')
await page.click('#outfit-lib [data-outfit="dress"]')
await page.waitForTimeout(300)
const libState = await page.evaluate(() => ({
  outfit: window.__builder.state.appearance.outfit,
  bottom: window.__builder.state.appearance.bottom,
  on: document.querySelectorAll('#outfit-lib .libitem.on').length,
}))
check('visual library previews', lib.items >= 55 && lib.thumbs >= 55 && libState.outfit === 'dress' && libState.bottom === 'dress' && libState.on === 1, { lib, libState })
await page.evaluate(() => localStorage.removeItem('papercast.session.v1'))

// ── live sync between studio tabs ─────────────────────────────────────────
const syncCtx = await browser.newContext({ viewport: { width: 1200, height: 900 } })
const s1 = await syncCtx.newPage()
const s2 = await syncCtx.newPage()
await s1.goto(BASE + '/character-builder.html', { waitUntil: 'networkidle' })
await s1.evaluate(() => localStorage.removeItem('papercast.session.v1'))
await s1.reload({ waitUntil: 'networkidle' })
await s2.goto(BASE + '/pose-studio.html', { waitUntil: 'networkidle' })
await s1.waitForTimeout(400)
await s1.selectOption('#pose', 'wave')
await s1.waitForTimeout(700)
const synced = await s2.evaluate(() => ({ name: window.__poseStudio.state.name }))
check('live sync between tabs', synced.name === 'wave', synced)
await syncCtx.close()

await browser.close()
console.log(`\n${failed ? 'FAILED' : 'PASSED'} — ${results.length - failed}/${results.length}`)
process.exit(failed ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(1) })
