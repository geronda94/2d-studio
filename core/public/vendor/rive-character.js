/* RiveCharacter — deterministic controller for the hand-built Rive rig.
 *
 * The .riv file contains the skeleton, vector art and a 10-shape mouth.
 * Every bone rotation / face control is a view-model number; this controller
 * writes those numbers from seek(t) and draws one frame. No wall clock, no rAF.
 *
 * window.RiveCharacter.create(canvas, opts) -> { ready, seek(t), setPreset, ... }
 */
(function () {
  const PI = Math.PI
  const TAU = PI * 2

  const PRESETS = {
    host: {
      label: 'Ведущий',
      colors: {
        skin: 0xFFF2CBA4, skinLight: 0xFFFBE0C4, skinDark: 0xFFC68C60,
        hair: 0xFF3B2C24, hairLight: 0xFF6B4C3C,
        shirt: 0xFF2F6FB3, shirtLight: 0xFF5E9BD8, shirtDark: 0xFF1E4A7C,
        pants: 0xFF2A3444, pantsLight: 0xFF3D4A5E, shoe: 0xFF1B2230, shoeLight: 0xFF39465C,
        lip: 0xFFC2726B, iris: 0xFF4A7FB5, scarf: 0xFFB23A48, skirt: 0xFF35405A, cassock: 0xFF23242B,
      },
      flags: { beard: 1, glasses: 0, scarfOn: 0, skirtOn: 0, cassockOn: 0, blazerOn: 0, longHair: 0 },
    },
    cohost: {
      label: 'Соведущая',
      colors: {
        skin: 0xFFF7D3B4, skinLight: 0xFFFFE7CF, skinDark: 0xFFCE9A73,
        hair: 0xFF4A3328, hairLight: 0xFF704C3A,
        shirt: 0xFF6B4A5A, shirtLight: 0xFF8F6578, shirtDark: 0xFF4A303E,
        pants: 0xFF3A2F45, pantsLight: 0xFF54435F, shoe: 0xFF2A2130, shoeLight: 0xFF4A3B53,
        lip: 0xFFC96E72, iris: 0xFF4E8FA8, scarf: 0xFFB23A48, skirt: 0xFF3A2F45, cassock: 0xFF23242B,
      },
      flags: { beard: 0, glasses: 0, scarfOn: 1, skirtOn: 1, cassockOn: 0, blazerOn: 0, longHair: 1 },
    },
    priest: {
      label: 'Священник',
      colors: {
        skin: 0xFFEFC6A0, skinLight: 0xFFF9DBBE, skinDark: 0xFFBF845C,
        hair: 0xFF2E2620, hairLight: 0xFF514138,
        shirt: 0xFF23242B, shirtLight: 0xFF3A3C46, shirtDark: 0xFF15161B,
        pants: 0xFF1C1D22, pantsLight: 0xFF2B2D34, shoe: 0xFF111216, shoeLight: 0xFF2A2C33,
        lip: 0xFFB96A65, iris: 0xFF4A6B88, scarf: 0xFF23242B, skirt: 0xFF23242B, cassock: 0xFF23242B,
      },
      flags: { beard: 1, glasses: 0, scarfOn: 0, skirtOn: 0, cassockOn: 1, blazerOn: 0, longHair: 0 },
    },
    historian: {
      label: 'Историк',
      colors: {
        skin: 0xFFEFC9A8, skinLight: 0xFFFBE2C8, skinDark: 0xFFC08E68,
        hair: 0xFF8A8A86, hairLight: 0xFFB8B8B2,
        shirt: 0xFF4B3A2F, shirtLight: 0xFF6B5647, shirtDark: 0xFF33261E,
        pants: 0xFF2E3138, pantsLight: 0xFF454A54, shoe: 0xFF1A1C20, shoeLight: 0xFF34383F,
        lip: 0xFFB76D68, iris: 0xFF4E6F90, scarf: 0xFF4B3A2F, skirt: 0xFF2E3138, cassock: 0xFF23242B,
      },
      flags: { beard: 0, glasses: 1, scarfOn: 0, skirtOn: 0, cassockOn: 0, blazerOn: 1, longHair: 0 },
    },
    sociologist: {
      label: 'Социолог',
      colors: {
        skin: 0xFFF5D0B2, skinLight: 0xFFFFE6CE, skinDark: 0xFFCB9872,
        hair: 0xFF3B2A26, hairLight: 0xFF5E443A,
        shirt: 0xFF2F5D63, shirtLight: 0xFF4C838A, shirtDark: 0xFF1E3F44,
        pants: 0xFF2C3038, pantsLight: 0xFF444A55, shoe: 0xFF191B1F, shoeLight: 0xFF32363D,
        lip: 0xFFC77270, iris: 0xFF4D8A93, scarf: 0xFF2F5D63, skirt: 0xFF2C3038, cassock: 0xFF23242B,
      },
      flags: { beard: 0, glasses: 0, scarfOn: 0, skirtOn: 0, cassockOn: 0, blazerOn: 1, longHair: 1 },
    },
  }

  function clamp(x, a, b) { return x < a ? a : x > b ? b : x }
  function ease(x) { const c = clamp(x, 0, 1); return c * c * (3 - 2 * c) }
  function lerp(a, b, k) { return a + (b - a) * k }

  function visemePair(list, t) {
    let cur = 0, next = 0, at = null
    for (const it of list || []) {
      const tt = it.t !== undefined ? it.t : it.timeMs
      const v = it.v !== undefined ? it.v : it.viseme
      if (tt <= t) { cur = v; next = 0; at = null } else { next = v; at = tt; break }
    }
    let k = 0
    if (at !== null) k = clamp((t - (at - 70)) / 70, 0, 1)
    return { cur, next, k }
  }

  function create(canvas, opts) {
    const o = opts || {}
    let presetName = o.character || 'host'
    let preset = PRESETS[presetName] || PRESETS.host
    let vm = null
    let riveInst = null
    let lastT = Number(o.t0) || 0
    let readyResolve
    const ready = new Promise((res) => { readyResolve = res })

    function num(name, value) {
      if (!vm) return
      const p = vm.number(name)
      if (p) p.value = value
    }
    function col(name, argb) {
      if (!vm) return
      const p = vm.color(name)
      if (p) p.value = argb
    }
    function applyPreset(name) {
      presetName = name || presetName
      preset = PRESETS[presetName] || PRESETS.host
      Object.keys(preset.colors).forEach((k) => col(k, preset.colors[k]))
      Object.keys(preset.flags).forEach((k) => num(k, preset.flags[k]))
    }

    const params = {
      canvas,
      autoplay: false,
      autoBind: true,
      stateMachine: o.stateMachine || 'State Machine 1',
      layout: o.layout || new window.rive.Layout({ fit: window.rive.Fit.Contain, alignment: window.rive.Alignment.Center }),
      onLoad() {
        if (!riveInst) riveInst = this
        // Binds only run while a state machine is running. The machine's only
        // animation is empty, so it cannot drift away from the values we write.
        try { riveInst.play(o.stateMachine || 'State Machine 1') } catch (e) {}
        vm = riveInst.viewModelInstance
        applyPreset(presetName)
        seek(lastT)
        readyResolve(riveInst)
        if (typeof o.onReady === 'function') o.onReady(riveInst)
      },
      onLoadError(e) {
        if (typeof o.onError === 'function') o.onError(e)
      },
    }
    if (o.buffer) params.buffer = o.buffer
    else params.src = o.src || '/rive/character.riv'
    riveInst = new window.rive.Rive(params)

    function pose(t) {
      const s = t / 1000
      const p = o.props || {}
      const vis = p.visemes || o.visemes || []
      const pair = visemePair(vis, t)
      const mood = p.mood || o.mood || 'neutral'
      const walk = !!(p.walk !== undefined ? p.walk : o.walk)
      const seed = Number(p.seed !== undefined ? p.seed : o.seed) || 0
      const intensity = Number(p.intensity !== undefined ? p.intensity : o.intensity) || 1
      const gestures = p.gestures || o.gestures || []
      const g = (p.gestureAt !== undefined || o.gestureAt !== undefined)
        ? [{ at: p.gestureAt !== undefined ? p.gestureAt : o.gestureAt, type: 'wave', hand: 'R' }]
        : gestures

      // ── idle: breathing, weight shift, head micro-motion ────────────────
      const breath = Math.sin(s * 1.5)
      const sway = Math.sin(s * 0.72)
      let rootX = 300 + sway * 2.2
      let rootY = 560 + breath * 0.9
      let spine = 0.014 * Math.sin(s * 0.61)
      let chest = -0.010 * Math.sin(s * 0.77)
      let neck = 0.008 * Math.sin(s * 0.9)
      let headRot = 0.022 * Math.sin(s * 0.83) + 0.012 * Math.sin(s * 2.1)
      let shoulderL = -PI / 2, shoulderR = PI / 2
      let upperArmL = -PI / 2 + 0.035 * Math.sin(s * 0.9)
      let upperArmR = PI / 2 - 0.035 * Math.sin(s * 0.9 + 0.6)
      let foreArmL = 0.08 + 0.03 * Math.sin(s * 0.7)
      let foreArmR = 0.08 + 0.03 * Math.sin(s * 0.7 + 0.4)
      let handL = 0.06, handR = -0.06
      let hipL = -PI / 2, hipR = PI / 2
      let thighL = -PI / 2, thighR = PI / 2
      let shinL = 0.03, shinR = 0.03
      let footL = 0, footR = 0

      // ── walk ───────────────────────────────────────────────────────────
      if (walk) {
        const phase = s * 5.4
        const sw = Math.sin(phase)
        rootX += (o.walkX !== false ? (t / 1000) * 22 : 0)
        rootY += Math.abs(Math.cos(phase)) * -3
        thighL += -sw * 0.46
        thighR += sw * 0.46
        shinL = Math.max(0, -sw) * 0.55
        shinR = Math.max(0, sw) * 0.55
        footL = -sw * 0.16
        footR = sw * 0.16
        upperArmL += sw * 0.28
        upperArmR -= sw * 0.28
        foreArmL = 0.18
        foreArmR = 0.18
        headRot += 0.015 * Math.sin(phase)
        spine += 0.01 * Math.cos(phase)
      }

      // ── talk: small nods + a hand gesture ──────────────────────────────
      if (p.talk !== false || vis.length) {
        const talking = pair.cur !== 0 || pair.next !== 0
        if (talking) {
          headRot += 0.015 * Math.sin(s * 7.2)
          chest += 0.007 * Math.sin(s * 5.4)
        }
      }
      for (const ev of g) {
        if (!ev || ev.at === undefined) continue
        const dur = Number(ev.dur) || 1500
        const a = Math.min(ease((t - ev.at) / 280), 1 - ease((t - (ev.at + dur)) / 280))
        if (a <= 0) continue
        const hand = ev.hand === 'L' ? 'L' : 'R'
        const kind = ev.type || 'wave'
        if (kind === 'wave') {
          if (hand === 'R') { upperArmR += -1.85 * a; foreArmR += 1.15 * a; handR += 0.25 * Math.sin(s * 9) * a }
          else { upperArmL += 1.85 * a; foreArmL += -1.15 * a; handL += -0.25 * Math.sin(s * 9) * a }
        } else if (kind === 'point') {
          if (hand === 'R') { upperArmR += -1.15 * a; foreArmR += 0.25 * a }
          else { upperArmL += 1.15 * a; foreArmL += -0.25 * a }
        } else if (kind === 'open') {
          if (hand === 'R') { upperArmR += -0.9 * a; foreArmR += 0.55 * a }
          else { upperArmL += 0.9 * a; foreArmL += -0.55 * a }
        } else if (kind === 'shrug') {
          shoulderR += 0.22 * a; shoulderL -= 0.22 * a
          upperArmR += 0.35 * a; upperArmL -= 0.35 * a
        }
      }

      // ── face ───────────────────────────────────────────────────────────
      const period = Number(p.blinkPeriod !== undefined ? p.blinkPeriod : o.blinkPeriod) || 3600
      const bt = (t + seed) % period
      const blink = bt < 170 ? Math.sin((bt / 170) * PI) : 0
      const gazeX = Math.sin(s * 0.7) * 1.6 + Math.sin(s * 2.3) * 0.5
      const gazeY = Math.cos(s * 0.5) * 0.9 + Math.sin(s * 1.9) * 0.35
      const MOOD_BROW = {
        neutral: [0, 0], joy: [-1.5, 6], anger: [1.5, -8], sad: [-1, -5], surprise: [-3.5, 10],
      }
      const mb = MOOD_BROW[mood] || MOOD_BROW.neutral
      const browY = mb[0] * intensity
      const browTilt = mb[1] * 0.0175 * intensity
      const jaw = (pair.cur === 1 || pair.cur === 4 || pair.cur === 7 || pair.cur === 8) ? 1 : 0

      // ── write view model ───────────────────────────────────────────────
      num('rootX', rootX); num('rootY', rootY); num('rootRot', -PI / 2)
      num('spine', spine); num('chest', chest); num('neck', neck); num('head', headRot)
      num('shoulderL', shoulderL); num('shoulderR', shoulderR)
      num('upperArmL', upperArmL); num('upperArmR', upperArmR)
      num('foreArmL', foreArmL); num('foreArmR', foreArmR)
      num('handL', handL); num('handR', handR)
      num('hipL', hipL); num('hipR', hipR)
      num('thighL', thighL); num('thighR', thighR)
      num('shinL', shinL); num('shinR', shinR)
      num('footL', footL); num('footR', footR)
      num('blink', blink)
      num('gazeX', gazeX); num('gazeY', gazeY)
      num('browYL', browY); num('browYR', browY)
      num('browTiltL', browTilt); num('browTiltR', -browTilt)
      num('headYaw', 0); num('headPitch', 0)
      for (let i = 0; i < 10; i++) {
        let v = 0
        if (i === pair.cur) v += 1 - pair.k
        if (i === pair.next) v += pair.k
        num('m' + i, v)
      }
      // mouth opening also nudges the head/jaw a little
      num('neck', neck + jaw * 0.004)

      if (riveInst) {
        try { riveInst.drawFrame() } catch (e) {}
      }
    }

    function seek(t) {
      lastT = Number(t) || 0
      if (!vm) return
      pose(lastT)
    }

    return {
      ready,
      seek,
      setPreset(name) { applyPreset(name); pose(lastT) },
      setVisemes(list) { o.visemes = list; pose(lastT) },
      get pose() { return pose },
      get rive() { return riveInst },
      presets: PRESETS,
    }
  }

  window.RiveCharacter = { create, presets: PRESETS }
})()
