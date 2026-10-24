/* RiveActor — deterministic playback of a ready-made Rive character.
 *
 * Bob (CC BY 4.0, emanuelcabezas): full-body rig with static viseme poses,
 * expression loops, head/pupil idle, breath, gesture poses.
 *
 * Unlike RiveCharacter (view-model driven), this controller scrubs named
 * linear animations and draws one frame. No state machine, no wall clock.
 *
 * window.RiveActor.create(canvas, opts) -> { ready, seek(t), ... }
 */
(function () {
  const PI = Math.PI
  try {
    const names = ['scrub', 'default-state-machine']
    if (window.rive) window.rive.suppressDeprecationWarnings = names
    if (window.rive && window.rive.Rive) window.rive.Rive.suppressDeprecationWarnings = names
  } catch (e) {}

  const BOB = {
    label: 'Bob (CC BY 4.0)',
    src: '/rive/ready/bob.riv',
    // Bob ships a state machine; linear scrubbing is ignored while it owns the
    // artboard. Stop it once, then drive the authored clips from seek(t).
    stopStateMachine: true,
    base: '[Pose] Idle',
    breath: '[Body] Breath Light',
    head: '[Head] Look Idle',
    pupils: '[Pupil] Idle',
    expressions: {
      neutral: '[Exp] Idle face',
      joy: '[Exp] Grin',
      smile: '[Exp] Smirk',
      sad: '[Exp] Skeptic',
      surprise: '[Exp] Surprise',
      thinking: '[Exp] Thinking',
      warm: '[Exp] Warm',
      proud: '[Exp] Proud',
      focus: '[Exp] Focus',
    },
    // our 10 visemes -> Bob's authored mouth animations
    visemes: ['Viseme X', 'Viseme A', 'Viseme B', 'Viseme C', 'Viseme D',
              'Viseme E', 'Viseme F', 'Viseme G', 'Viseme H', 'Viseme X 2'],
    poses: {
      idle: '[Pose] Idle',
      wave: '[Pose] R Hand Waving',
      wave2: '[Pose] R Hand Waving 2',
      point: '[Pose] Hands Showing',
      waist: '[Pose] Hands Waist',
      leanL: '[Pose] Lean L',
      leanR: '[Pose] Lean R',
      scratch: '[Pose] L Hand Scratch',
      up: '[Pose] R Hand Up 1',
    },
  }

  const OLDMAN = {
    label: 'Old Man (CC BY 4.0)',
    src: '/rive/ready/oldman.riv',
    // This asset ships a state machine + view model: the machine owns breathing,
    // cloth, rope, foot tap and blinking; the view model owns mouth/face/hand.
    // Scrubbing individual animations would cancel them one by one (that is why
    // only blinking survived in the old linear driver).
    mode: 'stateMachine',
    stateMachine: 'State Machine 1',
    viewModel: {
      mouth: 'mouth',
      face: 'face',
      hand: 'leftHand',
      // 10 engine visemes -> the three authored mouth states
      mouthMap: { 0: 'Default', 1: 'AAA', 2: 'Default', 3: 'Default', 4: 'AAA',
                  5: 'OO', 6: 'OO', 7: 'Default', 8: 'OO', 9: 'OO' },
      faceMap: { neutral: 'Normal', joy: 'Normal', surprise: 'wow', sad: 'Normal', anger: 'Normal' },
    },
    // gestures are view-model triggers, not scrubbed poses
    triggers: { point: 'leftHand', wave: 'leftHand', hand: 'leftHand' },
    base: null,
    breath: null,
    head: null,
    pupils: null,
    expressions: {},
    visemes: [],
    poses: {},
    // Visible secondary motion on top of the state machine: a real Rive rig
    // alone reads as a still image at small sizes, so the root sways/breathes.
    bodyMotion: { swayDeg: 1.2, bobPx: 5, shiftPx: 3, breathe: 0.01, period: 3200 },
    gestureEvery: 2600,
  }

  function clamp(x, a, b) { return x < a ? a : x > b ? b : x }
  function ease(x) { const c = clamp(x, 0, 1); return c * c * (3 - 2 * c) }

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
    const cfg = Object.assign({}, (o.character === 'oldman' ? OLDMAN : BOB), o.config || {})
    let riveInst = null
    let artboard = null
    let readyResolve
    const ready = new Promise((res) => { readyResolve = res })
    const durations = {}
    let lastT = Number(o.t0) || 0
    let visemeIndex = 0
    let forcedViseme = null
    let forcedExpression = null
    let gesture = null
    let gotLoad = false
    let smObj = null
    let lastDriveT = 0
    const firedGestures = new Set()
    let vmMouth = null
    let vmFace = null
    let vmHand = null

    function dur(name) {
      if (durations[name] !== undefined) return durations[name]
      try {
        const a = artboard && artboard.animationByName(name)
        const d = a ? a.duration / (a.fps || 60) : 1
        durations[name] = d > 0 ? d : 1
      } catch (e) { durations[name] = 1 }
      return durations[name]
    }

    function scrub(name, t) {
      if (!riveInst || !name) return
      try { riveInst.scrub(name, Math.max(0, t)) } catch (e) {}
    }

    function loop(name, t) {
      const d = dur(name)
      return d > 0 ? t % d : 0
    }

    const params = {
      canvas,
      autoplay: false,
      onLoad() {
        gotLoad = true
        artboard = riveInst.artboard
        if (cfg.mode === 'stateMachine' && cfg.stateMachine) bootStateMachine()
        else if (cfg.stopStateMachine) {
          try { riveInst.stop() } catch (e) {}
          try { if (riveInst.stopRendering) riveInst.stopRendering() } catch (e) {}
        }
        seek(lastT)
        readyResolve(riveInst)
        if (typeof o.onReady === 'function') o.onReady(riveInst)
      },
      onLoadError(e) {
        if (typeof o.onError === 'function') o.onError(e)
      },
    }
    if (o.buffer) params.buffer = o.buffer
    else params.src = o.src || cfg.src
    riveInst = new window.rive.Rive(params)

    function bindViewModel() {
      vmMouth = vmFace = vmHand = null
      if (!cfg.viewModel) return
      try {
        const vm = riveInst && riveInst.viewModelInstance
        if (!vm) return
        const m = cfg.viewModel.mouth && vm.enum ? vm.enum(cfg.viewModel.mouth) : null
        const f = cfg.viewModel.face && vm.enum ? vm.enum(cfg.viewModel.face) : null
        const h = cfg.viewModel.hand && vm.trigger ? vm.trigger(cfg.viewModel.hand) : null
        vmMouth = m || null
        vmFace = f || null
        vmHand = h || null
      } catch (e) {}
    }

    function bootStateMachine() {
      try { riveInst.play(cfg.stateMachine) } catch (e) {}
      // The clock belongs to seek(t): stop Rive's own rAF loop and advance the
      // state machine by hand.
      try { if (riveInst.stopRendering) riveInst.stopRendering() } catch (e) {}
      smObj = findStateMachine()
      lastDriveT = 0
      firedGestures.clear()
      bindViewModel()
    }

    function findStateMachine() {
      try {
        const list = (riveInst.animator && riveInst.animator.stateMachines) || []
        return list.find((m) => m.name === cfg.stateMachine) || list[0] || null
      } catch (e) { return null }
    }

    function resetStateMachine() {
      try { riveInst.stop() } catch (e) {}
      try { riveInst.play(cfg.stateMachine) } catch (e) {}
      try { if (riveInst.stopRendering) riveInst.stopRendering() } catch (e) {}
      smObj = findStateMachine()
      lastDriveT = 0
      firedGestures.clear()
      bindViewModel()
    }

    function advanceStateMachine(dt) {
      if (!smObj) return
      // Small steps keep transitions and looping clips honest; a single huge
      // step can skip triggers and blend states.
      let left = dt
      let guard = 0
      while (left > 1e-4 && guard++ < 2000) {
        const step = Math.min(left, 1 / 60)
        try { smObj.advanceAndApply(step) } catch (e) { break }
        left -= step
      }
    }

    function applyViewModel(mood, viseme, pair) {
      if (!cfg.viewModel) return
      try {
        if (vmMouth) {
          const map = cfg.viewModel.mouthMap || {}
          const v = pair && pair.next && pair.k > 0.5 ? pair.next : viseme
          vmMouth.value = map[v] || 'Default'
        }
      } catch (e) {}
      try {
        if (vmFace) {
          const fm = cfg.viewModel.faceMap || {}
          vmFace.value = fm[mood] || fm.neutral || 'Normal'
        }
      } catch (e) {}
    }

    function fireGesture(index) {
      if (!vmHand || firedGestures.has(index)) return
      firedGestures.add(index)
      try { vmHand.trigger() } catch (e) {}
    }

    function applyBodyMotion(t) {
      const m = cfg.bodyMotion
      if (!m || !canvas || !canvas.style) return
      const p = m.period || 2600
      const phase = (t % p) / p
      const sway = Math.sin(phase * Math.PI * 2) * (m.swayDeg || 0)
      const bob = Math.sin(phase * Math.PI * 4) * (m.bobPx || 0)
      const shift = Math.sin(phase * Math.PI * 2 + 0.8) * (m.shiftPx || 0)
      const br = 1 + Math.sin(phase * Math.PI * 2) * (m.breathe || 0)
      canvas.style.transformOrigin = '50% 100%'
      canvas.style.transform = 'translate(' + shift.toFixed(2) + 'px,' + bob.toFixed(2) + 'px) rotate(' + sway.toFixed(3) + 'deg) scaleY(' + br.toFixed(4) + ')'
    }

    function seek(t) {
      lastT = Number(t) || 0
      applyBodyMotion(lastT)
      if (!gotLoad) return
      const s = lastT / 1000
      const p = o.props || {}
      const vis = p.visemes || o.visemes || []
      const pair = forcedViseme !== null ? { cur: forcedViseme, next: 0, k: 0 } : visemePair(vis, lastT)
      const mood = p.mood || o.mood || 'neutral'
      const expr = (forcedExpression && cfg.expressions[forcedExpression]) || cfg.expressions[mood] || cfg.expressions[o.expression] || cfg.expressions.neutral
      const gestures = p.gestures || o.gestures || []

      if (cfg.mode === 'stateMachine') {
        const target = s
        if (target < lastDriveT - 1e-4) resetStateMachine()
        if (target > lastDriveT) {
          advanceStateMachine(target - lastDriveT)
          lastDriveT = target
        }
        applyViewModel(mood, pair.cur, pair)
        let gi = 0
        for (const ev of gestures) {
          if (ev && ev.at !== undefined) {
            const d = Number(ev.dur) || 1500
            if (lastT >= ev.at && lastT < ev.at + d) fireGesture(gi)
          }
          gi += 1
        }
        if (cfg.gestureEvery) {
          const slot = Math.floor(lastT / cfg.gestureEvery)
          const phase = lastT % cfg.gestureEvery
          if (phase < 90) fireGesture(10000 + slot)
        }
        try { riveInst.drawFrame() } catch (e) {}
        visemeIndex = pair.cur
        return
      }

      // pick the active gesture pose (if any)
      let gpose = null
      let gtime = 0
      for (const ev of gestures) {
        if (!ev || ev.at === undefined) continue
        const d = Number(ev.dur) || 1500
        if (lastT >= ev.at && lastT <= ev.at + d) {
          gpose = cfg.poses[ev.type] || cfg.poses.wave
          gtime = (lastT - ev.at) / 1000
          break
        }
      }

      // base / pose
      scrub(gpose || p.pose && cfg.poses[p.pose] || cfg.base, gpose ? gtime : 0)
      // secondary motion
      if (cfg.breath) scrub(cfg.breath, loop(cfg.breath, s))
      if (cfg.head) scrub(cfg.head, loop(cfg.head, s))
      if (cfg.pupils) scrub(cfg.pupils, loop(cfg.pupils, s))
      if (expr) scrub(expr, loop(expr, s))
      for (const n of cfg.extras || []) scrub(n, loop(n, s))
      // mouth: if the character has a talking loop, use it while speech is
      // active; otherwise fall back to static viseme poses.
      const speech = vis && vis.length && pair.cur !== 0 || pair.next !== 0
      if (cfg.talking && speech) scrub(cfg.talking, s * 1.3)
      else {
        const curAnim = cfg.visemes[pair.cur] || cfg.visemes[0]
        const nextAnim = cfg.visemes[pair.next] || null
        if (nextAnim && pair.k > 0.5) scrub(nextAnim, 0)
        else scrub(curAnim, 0)
      }
      try { riveInst.drawFrame() } catch (e) {}
      visemeIndex = pair.cur
    }

    return {
      ready,
      seek,
      setViseme(i) { forcedViseme = Number(i); seek(lastT) },
      setExpression(name) { forcedExpression = name; seek(lastT) },
      get rive() { return riveInst },
      config: cfg,
    }
  }

  window.RiveActor = { create, configs: { bob: BOB, oldman: OLDMAN } }
})()
