/* BabylonCharacter — deterministic 3D avatar for scenes.
 *
 * Ready Player Me GLB: 67-bone skeleton + 72 ARKit/Oculus morph targets.
 * Everything is a pure function of seek(t): no render loop, no wall clock.
 * seek(t) poses bones and morph weights, then draws exactly one frame.
 *
 * Body motion comes from retargeted mocap clips (Mixamo GLB, window.__avatarAnims).
 * The source rig is a T-pose Mixamo skeleton; the avatar is A-pose, so clips are
 * retargeted with world-space deltas: W_tgt(t) = D_world * W_tgt_rest.
 *
 * window.BabylonCharacter.create(canvas, opts) -> { ready, seek(t), ... }
 *   opts.src / opts.buffer   — .glb (URL or ArrayBuffer/File)
 *   opts.preset              — 'face' | 'bust' | 'full' | 'wide'
 *   opts.visemes             — [{ t, viseme }] engine visemes 0..9
 *   opts.mood                — neutral | joy | sad | surprise | anger
 *   opts.idleClip            — clip name (default 'Idle')
 *   opts.talkClip            — clip name (default 'Talking')
 *   opts.gestures            — [{ at, clip|type, duration }]
 */
(function () {
  const PI = Math.PI
  const IDENT = [0, 0, 0, 1]

  const PRESETS = {
    face: { targetY: 1.58, radius: 0.74, beta: 1.46, fov: 0.72, covW: 0.55, covH: 0.50 },
    bust: { targetY: 1.42, radius: 1.28, beta: 1.46, fov: 0.78, covW: 1.05, covH: 1.00 },
    full: { targetY: 0.95, radius: 2.60, beta: 1.50, fov: 0.78, covW: 1.10, covH: 1.95 },
    wide: { targetY: 0.92, radius: 3.80, beta: 1.50, fov: 0.80, covW: 1.50, covH: 2.20 },
  }

  // Engine visemes (0..9) -> Oculus viseme morph weights.
  const VISEME_OCULUS = {
    0: { viseme_sil: 1 },
    1: { viseme_aa: 1 },                       // А Э И Ы
    2: { viseme_PP: 1 },                       // Б М П
    3: { viseme_FF: 1 },                       // Ф В
    4: { viseme_DD: 0.85, viseme_kk: 0.15 },   // Д Т К Г С З Ц Р Н Й
    5: { viseme_U: 1 },                        // У Ю
    6: { viseme_CH: 1 },                       // Ч Ш Ж Щ
    7: { viseme_nn: 0.7, viseme_DD: 0.3 },     // Л
    8: { viseme_O: 1 },                        // О Ё
    9: { viseme_U: 0.6, viseme_O: 0.4 },       // QW
  }

  const MOODS = {
    neutral: {},
    joy: { mouthSmileLeft: 0.35, mouthSmileRight: 0.35, cheekSquintLeft: 0.18, cheekSquintRight: 0.18, browInnerUp: 0.10 },
    sad: { mouthFrownLeft: 0.6, mouthFrownRight: 0.6, browInnerUp: 0.45, eyeSquintLeft: 0.2, eyeSquintRight: 0.2 },
    surprise: { browOuterUpLeft: 0.8, browOuterUpRight: 0.8, browInnerUp: 0.7, eyeWideLeft: 0.6, eyeWideRight: 0.6, jawOpen: 0.18 },
    anger: { browDownLeft: 0.7, browDownRight: 0.7, mouthPressLeft: 0.4, mouthPressRight: 0.4, noseSneerLeft: 0.4, noseSneerRight: 0.4 },
  }

  const GESTURE_CLIP = {
    wave: 'Standing_Greeting',
    greeting: 'Standing_Greeting',
    point: 'Pointing',
    nod: 'Hard_Head_Nod',
    agree: 'Agreeing',
    shrug: 'Shrugging',
    think: 'Thinking',
    look: 'Look_Around',
    dismiss: 'Dismissing_Gesture',
    thumbs: 'Standing_Thumbs_Up',
    clap: 'Standing_Clap',
    strong: 'Strong_Gesture',
  }

  // ── quaternion helpers (arrays xyzw) ─────────────────────────────────────
  function qMul(a, b) {
    const ax = a[0], ay = a[1], az = a[2], aw = a[3]
    const bx = b[0], by = b[1], bz = b[2], bw = b[3]
    return [
      aw * bx + ax * bw + ay * bz - az * by,
      aw * by - ax * bz + ay * bw + az * bx,
      aw * bz + ax * by - ay * bx + az * bw,
      aw * bw - ax * bx - ay * by - az * bz,
    ]
  }
  function qInv(a) { return [-a[0], -a[1], -a[2], a[3]] }
  function qNorm(a) {
    const l = Math.hypot(a[0], a[1], a[2], a[3]) || 1
    return [a[0] / l, a[1] / l, a[2] / l, a[3] / l]
  }
  function qSlerp(a, b, t) {
    let bx = b[0], by = b[1], bz = b[2], bw = b[3]
    let d = a[0] * bx + a[1] * by + a[2] * bz + a[3] * bw
    if (d < 0) { bx = -bx; by = -by; bz = -bz; bw = -bw; d = -d }
    if (d > 0.9995) {
      return qNorm([a[0] + (bx - a[0]) * t, a[1] + (by - a[1]) * t,
                    a[2] + (bz - a[2]) * t, a[3] + (bw - a[3]) * t])
    }
    const th = Math.acos(Math.min(1, d))
    const s = Math.sin(th)
    const wa = Math.sin((1 - t) * th) / s
    const wb = Math.sin(t * th) / s
    return [a[0] * wa + bx * wb, a[1] * wa + by * wb, a[2] * wa + bz * wb, a[3] * wa + bw * wb]
  }
  function qEuler(x, y, z) {
    const cx = Math.cos(x / 2), sx = Math.sin(x / 2)
    const cy = Math.cos(y / 2), sy = Math.sin(y / 2)
    const cz = Math.cos(z / 2), sz = Math.sin(z / 2)
    return [
      sx * cy * cz + cx * sy * sz,
      cx * sy * cz - sx * cy * sz,
      cx * cy * sz + sx * sy * cz,
      cx * cy * cz - sx * sy * sz,
    ]
  }

  function qRotate(q, v) {
    const x = q[0], y = q[1], z = q[2], w = q[3]
    const vx = v[0], vy = v[1], vz = v[2]
    const tx = 2 * (y * vz - z * vy)
    const ty = 2 * (z * vx - x * vz)
    const tz = 2 * (x * vy - y * vx)
    return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)]
  }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x }
  function smooth(x) { const c = clamp(x, 0, 1); return c * c * (3 - 2 * c) }

  function visemePair(list, t) {
    let cur = 0, next = 0, at = null
    for (let i = 0; i < list.length; i++) {
      const it = list[i]
      const tt = it.t !== undefined ? it.t : it.timeMs
      const v = it.v !== undefined ? it.v : it.viseme
      if (tt <= t) { cur = v; next = 0; at = null } else { next = v; at = tt; break }
    }
    const k = at !== null ? smooth((t - (at - 80)) / 80) : 0
    return { cur, next, k }
  }

  function sampleKeys(times, keys, t, lerp) {
    if (!keys || !keys.length) return null
    if (t <= times[0]) return keys[0]
    const last = times.length - 1
    if (t >= times[last]) return keys[last]
    let i = 0
    while (i < last && times[i + 1] <= t) i++
    const t0 = times[i], t1 = times[i + 1]
    const k = t1 > t0 ? (t - t0) / (t1 - t0) : 0
    if (lerp) {
      const a = keys[i], b = keys[i + 1]
      return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]
    }
    return qSlerp(keys[i], keys[i + 1], k)
  }

  function create(canvas, opts) {
    const o = opts || {}
    const scene = new BABYLON.Scene(new BABYLON.Engine(canvas, true, {
      preserveDrawingBuffer: true, stencil: true, alpha: true,
      premultipliedAlpha: false, antialias: true,
    }, true))
    const engine = scene.getEngine()
    scene.clearColor = new BABYLON.Color4(0, 0, 0, 0)
    scene.ambientColor = new BABYLON.Color3(0.25, 0.26, 0.3)
    scene.imageProcessingConfiguration.toneMappingEnabled = false
    scene.imageProcessingConfiguration.exposure = 1.0
    scene.imageProcessingConfiguration.contrast = 1.04

    let presetName = o.preset || 'bust'
    let preset = PRESETS[presetName] || PRESETS.bust
    const camera = new BABYLON.ArcRotateCamera('cam', PI / 2, preset.beta, preset.radius,
      new BABYLON.Vector3(0, preset.targetY, 0), scene)
    camera.fov = preset.fov
    camera.minZ = 0.01
    camera.maxZ = 40
    scene.activeCamera = camera
    if (o.orbit) camera.attachControl(canvas, true)

    // ── lights: warm key, cool fill, cold rim ──────────────────────────────
    const hemi = new BABYLON.HemisphericLight('hemi', new BABYLON.Vector3(0, 1, 0), scene)
    hemi.intensity = 1.05
    hemi.diffuse = new BABYLON.Color3(1, 0.98, 0.95)
    hemi.groundColor = new BABYLON.Color3(0.16, 0.18, 0.24)

    const key = new BABYLON.DirectionalLight('key', new BABYLON.Vector3(-0.45, -0.75, -0.55), scene)
    key.position = new BABYLON.Vector3(2.6, 4.2, 3.0)
    key.intensity = 2.1
    key.diffuse = new BABYLON.Color3(1, 0.95, 0.88)

    const fill = new BABYLON.DirectionalLight('fill', new BABYLON.Vector3(0.55, -0.25, -0.55), scene)
    fill.position = new BABYLON.Vector3(-3.2, 2.2, 2.4)
    fill.intensity = 0.65
    fill.diffuse = new BABYLON.Color3(0.72, 0.82, 1)

    const rim = new BABYLON.DirectionalLight('rim', new BABYLON.Vector3(0.15, -0.35, 0.9), scene)
    rim.position = new BABYLON.Vector3(0.4, 3.0, -4.0)
    rim.intensity = 1.5
    rim.diffuse = new BABYLON.Color3(0.66, 0.78, 1)

    // ── contact shadow (no shadow maps: cheaper and deterministic) ─────────
    const shadowTex = new BABYLON.DynamicTexture('contact-shadow', { width: 256, height: 256 }, scene, false)
    {
      const ctx = shadowTex.getContext()
      const g = ctx.createRadialGradient(128, 128, 8, 128, 128, 126)
      g.addColorStop(0, 'rgba(0,0,0,0.62)')
      g.addColorStop(0.45, 'rgba(0,0,0,0.34)')
      g.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = g
      ctx.fillRect(0, 0, 256, 256)
      shadowTex.update()
      shadowTex.hasAlpha = true
    }
    const shadowMat = new BABYLON.StandardMaterial('contact-shadow-mat', scene)
    shadowMat.diffuseTexture = shadowTex
    shadowMat.opacityTexture = shadowTex
    shadowMat.useAlphaFromDiffuseTexture = true
    shadowMat.disableLighting = true
    shadowMat.emissiveColor = new BABYLON.Color3(0, 0, 0)
    shadowMat.diffuseColor = new BABYLON.Color3(0, 0, 0)
    shadowMat.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND
    shadowMat.backFaceCulling = false
    const shadowPlane = BABYLON.MeshBuilder.CreateGround('contact-shadow-plane', { width: 0.9, height: 0.55 }, scene)
    shadowPlane.material = shadowMat
    shadowPlane.position.y = 0.012
    shadowPlane.isPickable = false

    let root = null
    let armature = null
    let skeleton = null
    const bones = {}
    const boneObjs = {}
    const restQ = {}
    const restPos = {}
    const morphs = []
    const morphIndex = {}
    const weights = {}
    let visemes = []
    let lastT = Number(o.t0) || 0
    let readyResolve
    const ready = new Promise((res) => { readyResolve = res })
    const info = { bones: [], morphs: [], targets: [], clips: [], error: null }

    // ── animation data (retargeted mocap) ─────────────────────────────────
    const anims = window.__avatarAnims || null
    let srcOrder = []
    let srcParent = {}
    let srcKey = {}
    let srcRestQ = {}
    let srcRestPos = {}
    let srcHips = ''
    let srcScale = 1
    let targetOrder = []
    let targetParent = {}
    let targetRestQ = {}
    let targetRestPos = {}
    let retargetR = {}
    let targetHips = ''
    let lastPoseDebug = {}
    let IDLE = o.idleClip || 'Neutral_Idle'
    let TALK = o.talkClip || 'Talking'
    let TALK_W = o.talkWeight !== undefined ? Number(o.talkWeight) : 0.4
    let restFootY = 0

    function buildTargetRig() {
      const parentOf = {}
      const children = {}
      Object.keys(bones).forEach((name) => {
        // The glTF loader links every bone to a FLAT TransformNode (siblings
        // under the armature), so the node tree is useless for hierarchy.
        // Use the skeleton bones for the parent chain; animate the nodes.
        const b = boneObjs[name]
        const pb = b && b.getParent && b.getParent()
        const p = pb ? pb.name : ''
        parentOf[name] = p && bones[p] ? p : ''
        if (!children[parentOf[name]]) children[parentOf[name]] = []
        children[parentOf[name]].push(name)
      })
      targetParent = parentOf
      targetOrder = []
      const walk = (name) => {
        targetOrder.push(name)
        ;(children[name] || []).forEach(walk)
      }
      ;(children[''] || []).forEach(walk)
      targetOrder.forEach((name) => {
        const p = targetParent[name]
        targetRestQ[name] = p ? qMul(targetRestQ[p], restQ[name]) : restQ[name]
        targetRestPos[name] = p
          ? [targetRestPos[p][0] + restPos[name][0], targetRestPos[p][1] + restPos[name][1], targetRestPos[p][2] + restPos[name][2]]
          : restPos[name]
      })
      targetHips = bones.Hips ? 'Hips' : (targetOrder[0] || '')
      const rq = {}
      targetOrder.forEach((nm) => { rq[nm] = restQ[nm] })
      const feet = ['LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase']
        .filter((n) => bones[n])
        .map((n) => worldPosOf(n, rq, restPos[targetHips]))
      restFootY = feet.length ? Math.min.apply(null, feet.map((p) => p[1])) : 0
    }

    function worldPosOf(name, outQ, hipsPos) {
      const chain = []
      let n = name
      while (n) { chain.push(n); n = targetParent[n] }
      let q = IDENT
      let p = [0, 0, 0]
      for (let i = chain.length - 1; i >= 0; i--) {
        const nm = chain[i]
        const lq = outQ[nm] || restQ[nm]
        const lp = nm === targetHips ? hipsPos : restPos[nm]
        const off = qRotate(q, lp)
        p = [p[0] + off[0], p[1] + off[1], p[2] + off[2]]
        q = qMul(q, lq)
      }
      return p
    }

    function buildSourceRig() {
      if (!anims || !anims.rest) return
      const norm = (n) => String(n || '').replace(/^mixamorig:/, '')
      srcOrder = []
      srcParent = {}
      srcKey = {}
      ;(anims.order || []).forEach((orig) => {
        const nm = norm(orig)
        srcKey[nm] = orig
        srcOrder.push(nm)
        const pb = anims.parent[orig]
        srcParent[nm] = pb ? norm(pb) : ''
      })
      srcHips = norm(anims.hips)
      srcOrder.forEach((nm) => {
        const r = anims.rest[srcKey[nm]]
        if (!r) return
        const p = srcParent[nm]
        srcRestQ[nm] = p && srcRestQ[p] ? qMul(srcRestQ[p], r.q) : r.q
      })
      const h = anims.rest[srcKey[srcHips]]
      srcRestPos[srcHips] = h ? h.t.slice() : [0, 0, 0]
      if (targetRestPos[targetHips] && anims.height) {
        srcScale = targetRestPos[targetHips][1] / anims.height
      }
      // Absolute world retarget: map the source rest world orientation to the
      // target rest world orientation, then apply it to the animated source.
      retargetR = {}
      Object.keys(srcRestQ).forEach((nm) => {
        if (targetRestQ[nm]) retargetR[nm] = qMul(targetRestQ[nm], qInv(srcRestQ[nm]))
      })
      info.clips = Object.keys(anims.clips || {})
    }

    function evalClip(name, t, outQ, outHips) {
      const clip = anims && anims.clips && anims.clips[name]
      if (!clip) return false
      const dur = clip.duration || 0
      const tt = dur > 0 ? ((t % dur) + dur) % dur : 0
      // World-space delta retargeting. The source is T-pose, the avatar is
      // A-pose, so local deltas would twist elbows/shoulders. We compute the
      // source world rotation, take its delta from the source rest, apply it
      // to the target rest world, then convert back to a local rotation.
      const wq = {}
      for (let i = 0; i < srcOrder.length; i++) {
        const nm = srcOrder[i]
        const orig = srcKey[nm] || nm
        const tr = clip.tracks[orig]
        let q = (anims.rest[orig] && anims.rest[orig].q) || IDENT
        if (tr && tr.rot) {
          const smp = sampleKeys(tr.rt, tr.rot, tt, false)
          if (smp) q = smp
        }
        const p = srcParent[nm]
        wq[nm] = p ? qMul(wq[p] || IDENT, q) : q
      }
      const tw = {}
      for (let i = 0; i < targetOrder.length; i++) {
        const nm = targetOrder[i]
        const pw = tw[targetParent[nm]] || IDENT
        // Eye bones are driven by gaze, not by the body clips: the Mixamo eye
        // tracks retarget poorly and make the eyes roll away.
        if (nm === 'LeftEye' || nm === 'RightEye') {
          outQ[nm] = restQ[nm]
          tw[nm] = qMul(pw, restQ[nm])
          continue
        }
        if (!srcRestQ[nm]) {
          outQ[nm] = restQ[nm]
          tw[nm] = qMul(pw, restQ[nm])
          continue
        }
        const srcW = wq[nm] || srcRestQ[nm]
        const wt = qMul(retargetR[nm] || IDENT, srcW)
        outQ[nm] = qMul(qInv(pw), wt)
        tw[nm] = wt
      }
      const trH = clip.tracks[srcKey[srcHips] || srcHips]
      let hp = srcRestPos[srcHips] || [0, 0, 0]
      if (trH && trH.pos) {
        const smp = sampleKeys(trH.pt, trH.pos, tt, true)
        if (smp) hp = smp
      }
      const rp = srcRestPos[srcHips] || [0, 0, 0]
      outHips[0] = (hp[0] - rp[0]) * srcScale
      outHips[1] = (hp[1] - rp[1]) * srcScale
      outHips[2] = (hp[2] - rp[2]) * srcScale
      return true
    }

    function gestureAt(t) {
      const list = o.gestures || []
      for (let i = 0; i < list.length; i++) {
        const g = list[i]
        const at = g.at !== undefined ? g.at : 0
        const clipName = g.clip || GESTURE_CLIP[g.type] || g.type
        const clip = anims && anims.clips && anims.clips[clipName]
        const dur = Number(g.duration) || (clip ? clip.duration * 1000 : 1600)
        if (t >= at && t <= at + dur) {
          const fade = 260
          const w = smooth(Math.min(1, (t - at) / fade, (at + dur - t) / fade))
          let lt = (t - at) / 1000
          if (clip && clip.duration) lt = Math.min(lt, clip.duration - 1e-4)
          return { clip: clipName, type: g.type, localT: lt, w, at, dur }
        }
      }
      return null
    }

    function trackMorph(mesh) {
      const mtm = mesh.morphTargetManager
      if (!mtm) return
      for (let i = 0; i < mtm.numTargets; i++) {
        const tgt = mtm.getTarget(i)
        const rec = { mesh, index: i, name: tgt.name }
        morphs.push(rec)
        if (!morphIndex[tgt.name]) morphIndex[tgt.name] = []
        morphIndex[tgt.name].push(rec)
        if (!info.targets.includes(tgt.name)) info.targets.push(tgt.name)
      }
    }

    function setWeight(name, value) {
      const list = morphIndex[name]
      if (!list) return
      const w = clamp(value, 0, 1)
      for (let i = 0; i < list.length; i++) {
        const m = list[i].mesh.morphTargetManager.getTarget(list[i].index)
        m.influence = w
      }
    }

    function restOf(node) {
      if (node.rotationQuaternion) return node.rotationQuaternion
      return node.rotation
    }

    function resetBone(name) {
      const b = bones[name]
      if (!b) return
      const q = restQ[name]
      if (b.rotationQuaternion) b.rotationQuaternion.copyFromFloats(q[0], q[1], q[2], q[3])
      else b.rotation.set(q[0], q[1], q[2])
    }

    function boneDelta(name, x, y, z) {
      const b = bones[name]
      if (!b) return
      const q = qMul(restQ[name], qEuler(x, y, z))
      if (b.rotationQuaternion) b.rotationQuaternion.copyFromFloats(q[0], q[1], q[2], q[3])
      else b.rotation.set(q[0], q[1], q[2])
    }

    function poseMorphs(t, seed, mood) {
      const target = {}
      const pair = visemePair(visemes, t)
      const a = VISEME_OCULUS[pair.cur] || VISEME_OCULUS[0]
      const b = VISEME_OCULUS[pair.next] || VISEME_OCULUS[0]
      const k = pair.k
      Object.keys(a).forEach((n) => { target[n] = (target[n] || 0) + a[n] * (1 - k) })
      Object.keys(b).forEach((n) => { target[n] = (target[n] || 0) + b[n] * k })

      const m = MOODS[mood] || {}
      Object.keys(m).forEach((n) => { target[n] = (target[n] || 0) + m[n] })

      const period = 3600 + (seed % 5) * 130
      const phase = ((t + seed * 311) % period)
      let blink = 0
      if (phase < 170) blink = Math.sin((phase / 170) * PI)
      target.eyeBlinkLeft = Math.max(target.eyeBlinkLeft || 0, blink)
      target.eyeBlinkRight = Math.max(target.eyeBlinkRight || 0, blink)

      Object.keys(morphIndex).forEach((name) => {
        const want = target[name] || 0
        weights[name] = want
        setWeight(name, want)
      })
    }

    function poseProcedural(t, seed, intensity, gesture) {
      const s = t / 1000
      const breath = Math.sin(s * 1.35 + seed * 0.7)
      const sway = Math.sin(s * 0.62 + seed * 1.3)
      const micro = Math.sin(s * 0.27 + seed * 2.1)

      resetBone('Spine'); resetBone('Spine1'); resetBone('Spine2')
      resetBone('Neck'); resetBone('Head'); resetBone('Hips')
      resetBone('RightArm'); resetBone('RightForeArm')
      resetBone('LeftArm'); resetBone('LeftForeArm')

      boneDelta('Spine', breath * 0.010 * intensity, 0, sway * 0.008 * intensity)
      boneDelta('Spine1', breath * 0.008 * intensity, 0, 0)
      boneDelta('Spine2', breath * 0.006 * intensity, 0, 0)
      boneDelta('Hips', 0, 0, sway * 0.010 * intensity)

      let headX = Math.sin(s * 0.43 + seed) * 0.035 * intensity
      let headY = micro * 0.05 * intensity
      let headZ = sway * 0.02 * intensity
      if (gesture && gesture.type === 'nod') headX += 0.12 * gesture.k
      boneDelta('Neck', headX * 0.35, headY * 0.35, headZ * 0.35)
      boneDelta('Head', headX, headY, headZ)

      if (gesture && gesture.type === 'wave') {
        const wiggle = Math.sin(s * 9) * 0.16 * gesture.k
        boneDelta('RightArm', -0.9 * gesture.k, 0, -0.55 * gesture.k + wiggle)
        boneDelta('RightForeArm', -0.35 * gesture.k, 0, -0.7 * gesture.k + wiggle)
      } else if (gesture && gesture.type === 'point') {
        boneDelta('RightArm', -0.35 * gesture.k, 0.2 * gesture.k, -0.4 * gesture.k)
        boneDelta('RightForeArm', -0.1 * gesture.k, 0, -0.35 * gesture.k)
      } else if (gesture && gesture.type === 'shrug') {
        boneDelta('RightArm', 0, 0, 0.35 * gesture.k)
        boneDelta('LeftArm', 0, 0, -0.35 * gesture.k)
      }
      if (armature) armature.position.y = Math.sin(s * 1.35 + seed * 0.7) * 0.0035 * intensity
    }

    function effectivePose(t) {
      const out = {}
      const add = (bone, x, y, z) => {
        if (!out[bone]) out[bone] = [0, 0, 0]
        out[bone][0] += Number(x) || 0
        out[bone][1] += Number(y) || 0
        out[bone][2] += Number(z) || 0
      }
      const stat = o.pose || {}
      Object.keys(stat).forEach((bone) => {
        const v = stat[bone] || []
        add(bone, v[0], v[1], v[2])
      })
      const keys = (o.poseKeys || []).slice().sort((a, b) => (a.at || 0) - (b.at || 0))
      const perBone = {}
      keys.forEach((k) => {
        if (!k || !k.bone) return
        ;(perBone[k.bone] = perBone[k.bone] || []).push(k)
      })
      Object.keys(perBone).forEach((bone) => {
        let cur = null
        for (let i = 0; i < perBone[bone].length; i++) {
          const k = perBone[bone][i]
          if ((k.at || 0) <= t) cur = k
          else break
        }
        if (cur) add(bone, cur.x, cur.y, cur.z)
      })
      return out
    }

    function pose(t) {
      const seed = Number(o.seed) || 0
      const intensity = o.intensity !== undefined ? Number(o.intensity) : 1
      const mood = o.mood || 'neutral'
      const gesture = gestureAt(t)
      const hasAnims = !!(anims && anims.clips && anims.clips[IDLE] && srcRestQ[srcHips])
      lastPoseDebug = { gesture, hasAnims }

      if (hasAnims) {
        const idleQ = {}, talkQ = {}, gestQ = {}
        const idleH = [0, 0, 0], talkH = [0, 0, 0], gestH = [0, 0, 0]
        evalClip(IDLE, t, idleQ, idleH)
        const talkW = visemes.length && anims.clips[TALK] ? TALK_W : 0
        lastPoseDebug.talkW = talkW
        lastPoseDebug.gw = gesture ? gesture.w : 0
        if (talkW > 0) evalClip(TALK, t, talkQ, talkH)
        if (gesture && anims.clips[gesture.clip]) evalClip(gesture.clip, gesture.localT, gestQ, gestH)
        const gw = gesture ? gesture.w : 0

        // blend idle + talk + gesture for every bone first
        const finalQ = {}
        for (let i = 0; i < targetOrder.length; i++) {
          const nm = targetOrder[i]
          let q = idleQ[nm] || restQ[nm]
          if (talkW > 0 && talkQ[nm]) q = qSlerp(q, talkQ[nm], talkW)
          if (gw > 0 && gestQ[nm]) q = qSlerp(q, gestQ[nm], gw)
          finalQ[nm] = q
        }
        // manual pose overrides (editor sliders / pose keys), additive in the
        // bone's local frame
        const over = effectivePose(t)
        Object.keys(over).forEach((nm) => {
          if (!bones[nm]) return
          const v = over[nm]
          finalQ[nm] = qMul(finalQ[nm] || restQ[nm], qEuler(v[0] * PI / 180, v[1] * PI / 180, v[2] * PI / 180))
        })

        for (let i = 0; i < targetOrder.length; i++) {
          const nm = targetOrder[i]
          const q = finalQ[nm] || restQ[nm]
          const b = bones[nm]
          if (b.rotationQuaternion) b.rotationQuaternion.copyFromFloats(q[0], q[1], q[2], q[3])
          else b.rotation.set(q[0], q[1], q[2])
        }

        const hips = bones[targetHips]
        if (hips) {
          const dx = idleH[0] * (1 - talkW) + talkH[0] * talkW
          const dy = idleH[1] * (1 - talkW) + talkH[1] * talkW
          const dz = idleH[2] * (1 - talkW) + talkH[2] * talkW
          const gx = dx * (1 - gw) + gestH[0] * gw
          const gy = dy * (1 - gw) + gestH[1] * gw
          const gz = dz * (1 - gw) + gestH[2] * gw
          const rp = restPos[targetHips]
          const hp = [rp[0] + gx, rp[1] + gy, rp[2] + gz]
          // ground clamp: keep the lowest foot at its rest height
          const feet = ['LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase'].filter((n) => bones[n])
          if (feet.length) {
            let minY = Infinity
            feet.forEach((n) => { const p = worldPosOf(n, finalQ, hp); if (p[1] < minY) minY = p[1] })
            if (isFinite(minY)) hp[1] -= minY - restFootY
          }
          hips.position.set(hp[0], hp[1], hp[2])
        }
        if (armature) armature.position.y = 0
      } else {
        poseProcedural(t, seed, intensity, gesture)
      }

      // gaze on top of the clip (eyes are not animated by the mocap clips)
      const gaze = o.gaze || { x: 0, y: 0 }
      const gx = clamp(gaze.x || 0, -1, 1)
      const gy = clamp(gaze.y || 0, -1, 1)
      ;['LeftEye', 'RightEye'].forEach((nm) => {
        const b = bones[nm]
        if (!b) return
        const q = qMul(restQ[nm], qEuler(gy * 0.12, gx * 0.16, 0))
        if (b.rotationQuaternion) b.rotationQuaternion.copyFromFloats(q[0], q[1], q[2], q[3])
      })

      poseMorphs(t, seed, mood)
    }

    function applyPreset(name) {
      presetName = name || presetName
      preset = PRESETS[presetName] || PRESETS.bust
      camera.beta = preset.beta
      camera.fov = preset.fov
      camera.setTarget(new BABYLON.Vector3(0, preset.targetY, 0))
      fit()
    }

    function fit() {
      engine.resize()
      const aspect = engine.getRenderWidth() / Math.max(1, engine.getRenderHeight())
      const tan = Math.tan(camera.fov / 2)
      const covW = preset.covW * (aspect < 1 ? 0.8 : 1)
      const needV = preset.covH / (2 * tan)
      const needH = covW / (2 * tan * Math.max(0.2, aspect))
      camera.radius = Math.max(preset.radius, needV, needH) * 1.10
      pose(lastT)
      scene.render()
    }

    function seek(t) {
      lastT = Math.max(0, Number(t) || 0)
      pose(lastT)
      scene.render()
      return lastT
    }

    function load() {
      const done = (res) => {
        root = res.meshes[0]
        armature = root
        skeleton = res.skeletons[0]
        if (skeleton) {
          skeleton.bones.forEach((b) => {
            const node = (b.getTransformNode && b.getTransformNode()) || b
            bones[b.name] = node
            boneObjs[b.name] = b
            const r = restOf(node)
            restQ[b.name] = [r.x, r.y, r.z, r.w]
            restPos[b.name] = [node.position.x, node.position.y, node.position.z]
            info.bones.push(b.name)
          })
        }
        res.meshes.forEach((mesh) => {
          trackMorph(mesh)
          if (mesh.material && mesh.material.albedoTexture) {
            mesh.material.albedoTexture.anisotropicFilteringLevel = 4
          }
          // Skinned bounds do not follow the bones: without this the head or
          // an arm can be frustum-culled for a frame and "disappear".
          mesh.alwaysSelectAsActiveMesh = true
          if (mesh.name !== 'contact-shadow-plane') mesh.isPickable = false
        })
        info.morphs = Array.from(new Set(morphs.map((x) => x.mesh.name)))
        buildTargetRig()
        buildSourceRig()

        const warm = []
        res.meshes.forEach((mesh) => {
          if (mesh.material && mesh.material.forceCompilationAsync) {
            warm.push(mesh.material.forceCompilationAsync(mesh).catch(() => {}))
          }
        })
        Promise.all(warm).then(() => {
          seek(lastT)
          readyResolve(info)
          if (typeof o.onReady === 'function') o.onReady(info)
        })
      }
      const fail = (e) => {
        info.error = String(e && e.message ? e.message : e)
        readyResolve(info)
        if (typeof o.onError === 'function') o.onError(e)
      }
      if (o.buffer) {
        const file = o.buffer instanceof File ? o.buffer : new File([o.buffer], 'avatar.glb', { type: 'model/gltf-binary' })
        return BABYLON.SceneLoader.ImportMeshAsync('', '', file, scene, undefined, '.glb').then(done).catch(fail)
      }
      const src = o.src || '/models/brunette.glb'
      const slash = src.lastIndexOf('/')
      return BABYLON.SceneLoader.ImportMeshAsync('', src.slice(0, slash + 1), src.slice(slash + 1), scene, undefined, '.glb')
        .then(done).catch(fail)
    }

    function setVisemes(list) {
      visemes = Array.isArray(list) ? list.slice().sort((x, y) => (x.t || 0) - (y.t || 0)) : []
      if (visemes.length) {
        const last = visemes[visemes.length - 1]
        visemes.push({ t: (last.t || 0) + 180, viseme: 0 })
      }
    }
    setVisemes(o.visemes || [])

    window.addEventListener('resize', fit)
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(() => fit()).observe(canvas)
    }

    load()

    return {
      ready,
      info,
      seek,
      applyPreset,
      setPose(pose) { o.pose = pose || {}; seek(lastT); return o.pose },
      setPoseKeys(keys) { o.poseKeys = Array.isArray(keys) ? keys : []; seek(lastT); return o.poseKeys },
      setVisemes(list) {
        setVisemes(list)
        seek(lastT)
        return visemes
      },
      setMood(mood) { o.mood = mood || 'neutral'; seek(lastT) },
      setGaze(gaze) { o.gaze = gaze || { x: 0, y: 0 }; seek(lastT) },
      setGestures(list) { o.gestures = Array.isArray(list) ? list : []; seek(lastT) },
      setClips(c) {
        if (c && c.idle) IDLE = c.idle
        if (c && c.talk) TALK = c.talk
        if (c && c.talkWeight !== undefined) TALK_W = Number(c.talkWeight)
        seek(lastT)
      },
      resize: fit,
      scene,
      engine,
      debug: {
        bones, restQ, anims,
        get targetOrder() { return targetOrder },
        get targetParent() { return targetParent },
        get srcRestQ() { return srcRestQ },
        get lastPoseDebug() { return lastPoseDebug },
        get jointPos() {
          const out = {}
          ;['RightHand', 'LeftHand', 'Head', 'Hips', 'RightForeArm', 'LeftForeArm', 'LeftFoot', 'RightFoot', 'LeftUpLeg', 'RightUpLeg'].forEach((n) => {
            const b = bones[n]
            if (b) out[n] = b.getAbsolutePosition().asArray().map((x) => +x.toFixed(3))
          })
          return out
        },
      },
      get time() { return lastT },
      destroy() {
        window.removeEventListener('resize', fit)
        scene.dispose()
        engine.dispose()
      },
    }
  }

  window.BabylonCharacter = { create, PRESETS, VISEME_OCULUS, MOODS, GESTURE_CLIP }
})()
