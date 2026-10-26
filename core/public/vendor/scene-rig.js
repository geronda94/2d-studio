/* SceneRig — deterministic runtime for canonical SceneRig GLB characters.
 *
 * Everything visual is a pure function of seek(t):
 *   - body: procedural idle/talk from rest quaternions
 *   - face: Oculus-15 viseme morphs + deterministic blink + mood
 *   - appearance: material colours, accessory visibility, uniform scale
 *
 * No animation clocks. The optional interactive render loop is for editors
 * only; scenes call seek(t) and get exactly one frame.
 *
 * Requires: BABYLON, SceneClip (vendor/scene-clip.js).
 */
(function (root) {
  'use strict'

  const VISEME_MAP = {
    0: { viseme_sil: 1 },
    1: { viseme_aa: 1 },
    2: { viseme_PP: 1 },
    3: { viseme_FF: 1 },
    4: { viseme_DD: 0.85, viseme_kk: 0.15 },
    5: { viseme_U: 1 },
    6: { viseme_CH: 1 },
    7: { viseme_nn: 0.7, viseme_DD: 0.3 },
    8: { viseme_O: 1 },
    9: { viseme_U: 0.6, viseme_O: 0.4 },
  }
  const VISEME_MORPHS = [
    'viseme_sil', 'viseme_PP', 'viseme_FF', 'viseme_TH', 'viseme_DD',
    'viseme_kk', 'viseme_CH', 'viseme_SS', 'viseme_nn', 'viseme_RR',
    'viseme_aa', 'viseme_E', 'viseme_I', 'viseme_O', 'viseme_U',
  ]
  const MOOD_MORPHS = { joy: { mouthSmile: 0.7 }, sad: { mouthFrown: 0.7 } }
  const MATERIALS = {
    skin: 'Skin', hair: 'Hair', top: 'Top', bottom: 'Bottom', shoes: 'Shoes',
    eyes: 'Iris', lips: 'Lips', mouth: 'MouthDark', teeth: 'Teeth', tongue: 'Tongue',
  }
  const PRESETS = {
    face: { y: 1.60, r: 0.78, beta: 1.42 },
    bust: { y: 1.36, r: 1.55, beta: 1.44 },
    full: { y: 0.95, r: 2.70, beta: 1.48 },
    wide: { y: 0.95, r: 3.80, beta: 1.50 },
  }
  const IDENT = [0, 0, 0, 1]

  const EMOTION_MORPHS = {
    neutral: {},
    joy: { mouthSmile: 0.72, lipFull: 0.20 },
    sad: { mouthFrown: 0.62, lipFull: 0.10 },
    anger: { mouthPress: 0.55, mouthFrown: 0.20 },
    surprise: { jawOpen: 0.22, mouthStretch: 0.25, mouthPucker: 0.10 },
    fear: { mouthStretch: 0.45, mouthFrown: 0.18 },
    think: { mouthPress: 0.35, mouthPucker: 0.18 },
    disgust: { mouthFrown: 0.35, mouthPress: 0.22 },
  }
  const EMOTION_POSE = {
    neutral: {},
    joy: { head: [-0.025, 0, 0], chest: [0.025, 0, 0], neck: [-0.010, 0, 0] },
    sad: { head: [0.075, 0, 0], chest: [-0.020, 0, 0], neck: [0.030, 0, 0] },
    anger: { head: [0.035, 0, 0], chest: [0.020, 0, 0], neck: [0.020, 0, 0] },
    surprise: { head: [-0.055, 0, 0], chest: [0.020, 0, 0], neck: [-0.025, 0, 0] },
    fear: { head: [0.045, 0, 0], chest: [-0.030, 0, 0], neck: [0.020, 0, 0] },
    think: { head: [-0.020, 0.045, 0], chest: [0.010, 0.015, 0], neck: [0, 0.025, 0] },
    disgust: { head: [0.040, -0.025, 0], chest: [-0.010, -0.010, 0], neck: [0.010, -0.015, 0] },
  }

  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)) }

  function create(canvas, opts) {
    opts = opts || {}
    const engine = new BABYLON.Engine(canvas, true, { preserveDrawingBuffer: true, stencil: true, alpha: true })
    const scene = new BABYLON.Scene(engine)
    scene.clearColor = new BABYLON.Color4(0, 0, 0, 0)
    const camera = new BABYLON.ArcRotateCamera(
      'sceneRigCam', -Math.PI / 2 + 0.28, PRESETS[opts.preset]?.beta || 1.44,
      PRESETS[opts.preset]?.r || 1.5, new BABYLON.Vector3(0, 1.2, 0), scene
    )
    camera.fov = 0.78
    camera.minZ = 0.01
    if (opts.interactive) {
      camera.attachControl(canvas, true)
      camera.wheelPrecision = 40
      camera.lowerRadiusLimit = 0.4
      camera.upperRadiusLimit = 12
    }

    const hemi = new BABYLON.HemisphericLight('hemi', new BABYLON.Vector3(0.1, 1, 0.1), scene)
    hemi.intensity = 0.9
    hemi.groundColor = new BABYLON.Color3(0.12, 0.15, 0.20)
    const key = new BABYLON.DirectionalLight('key', new BABYLON.Vector3(-0.5, -1, -0.4), scene)
    key.position = new BABYLON.Vector3(2.6, 4.0, 3.2)
    key.intensity = 1.1
    const rim = new BABYLON.DirectionalLight('rim', new BABYLON.Vector3(0.6, -0.2, 0.8), scene)
    rim.position = new BABYLON.Vector3(-3, 2.5, -2.5)
    rim.intensity = 0.45
    rim.diffuse = new BABYLON.Color3(0.55, 0.75, 1.0)

    // Soft contact shadow under the feet.
    try {
      const tex = new BABYLON.DynamicTexture('sceneRigShadow', 256, scene, false)
      const ctx = tex.getContext()
      ctx.clearRect(0, 0, 256, 256)
      const g = ctx.createRadialGradient(128, 128, 8, 128, 128, 126)
      g.addColorStop(0, 'rgba(0,0,0,0.55)')
      g.addColorStop(0.55, 'rgba(0,0,0,0.24)')
      g.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.fillStyle = g
      ctx.fillRect(0, 0, 256, 256)
      tex.update()
      const disc = BABYLON.MeshBuilder.CreateDisc('sceneRigShadowDisc', { radius: 0.62, tessellation: 40 }, scene)
      disc.rotation.x = Math.PI / 2
      disc.position.y = 0.005
      disc.isPickable = false
      const sm = new BABYLON.StandardMaterial('sceneRigShadowMat', scene)
      sm.diffuseTexture = tex
      sm.opacityTexture = tex
      sm.disableLighting = true
      sm.useAlphaFromDiffuseTexture = true
      sm.backFaceCulling = false
      disc.material = sm
    } catch (e) { /* shadow is optional */ }

    let container = null
    let skeleton = null
    let rootNode = null
    let nodes = {}
    let restQ = {}
    let morphIndex = {}
    let materials = {}
    let accessories = { glasses: [], hood: [] }
    let visemes = []
    let appearance = opts.appearance || {}
    let mood = opts.mood || 'neutral'
    let motion = opts.motion === 'talk' ? 'talk' : 'idle'
    let gestureName = 'none'
    let emotion = opts.emotion || 'neutral'
    let emotionAmount = clamp(Number(opts.emotionAmount) || 1, 0, 1)
    let gaze = Object.assign({ x: 0, y: 0, head: true, auto: true }, opts.gaze || {})
    const GESTURES = {
      // additive local-Euler offsets on top of the idle/talk pose
      wave: {
        'upperArm.R': [0, 0, 1.35],
        'lowerArm.R': [0.65, 0, 0.80],
        'hand.R': [0, 0, 0.25],
      },
      point: {
        'upperArm.R': [0, 0, 1.45],
        'lowerArm.R': [-0.75, 0, 0.20],
        'hand.R': [0, 0, 0],
      },
      explain: {
        'upperArm.L': [0, 0, -0.95],
        'upperArm.R': [0, 0, 0.95],
        'lowerArm.L': [-0.85, 0, -0.80],
        'lowerArm.R': [-0.85, 0, 0.80],
      },
    }
    let gender = opts.gender === 'female' ? 'female' : 'male'
    let outfit = Object.assign({
      top: 'tee', bottom: 'pants', shoes: 'sneaker',
      hair: opts.hair || (gender === 'female' ? 'ponytail' : 'short'),
    }, opts.outfit || {})
    let parts = []
    let lastTime = 0
    let readyResolve, readyReject
    const info = { bones: [], morphs: [], clips: [], error: null }
    const ready = new Promise((res, rej) => { readyResolve = res; readyReject = rej })

    function hexColor(value) {
      try { return BABYLON.Color3.FromHexString(String(value)) } catch (e) { return null }
    }

    function morphsOf(mesh) {
      const mm = mesh.morphTargetManager
      if (!mm) return
      for (let i = 0; i < mm.numTargets; i++) {
        const t = mm.getTarget(i)
        if (!t || !t.name) continue
        if (!morphIndex[t.name]) morphIndex[t.name] = []
        morphIndex[t.name].push({ mesh, index: i, target: t })
        if (!info.morphs.includes(t.name)) info.morphs.push(t.name)
      }
    }

    function setMorph(name, weight) {
      const list = morphIndex[name]
      if (!list) return
      const w = clamp(Number(weight) || 0, 0, 1)
      for (let i = 0; i < list.length; i++) {
        const t = list[i].mesh.morphTargetManager.getTarget(list[i].index)
        if (t) t.influence = w
      }
    }

    function applyAppearance(app) {
      appearance = Object.assign({}, appearance, app || {})
      for (const key in MATERIALS) {
        if (appearance[key] && materials[MATERIALS[key]]) {
          const c = hexColor(appearance[key])
          if (c) materials[MATERIALS[key]].albedoColor = c
        }
      }
      if (rootNode && appearance.scale) {
        const s = clamp(Number(appearance.scale) || 1, 0.5, 1.8)
        rootNode.scaling.setAll(s)
      }
      applyOutfit()
      if (opts.interactive) scene.render()
    }

    function applyBody(t) {
      const talk = motion === 'talk' || opts.talk
      const walk = motion === 'walk'
      const s = t / 1000
      const heroRig = !!opts.boneMap
      const style = gender === 'female'
        ? { sway: 1.16, nod: 0.92, gesture: 0.88, breath: 1.10 }
        : { sway: 1.0, nod: 1.0, gesture: 1.0, breath: 1.0 }
      const autoGaze = gaze.auto
      const gx = autoGaze ? Math.sin(s * 0.37) * 0.55 + Math.sin(s * 1.13) * 0.18 : (Number(gaze.x) || 0)
      const gy = autoGaze ? Math.sin(s * 0.29 + 0.7) * 0.40 : (Number(gaze.y) || 0)
      const breath = Math.sin(s * Math.PI * 2 / 4.2)
      const sway = Math.sin(s * (talk ? 1.1 : 0.62))
      const nod = Math.sin(s * (talk ? 2.3 : 1.05))
      const gesture = Math.sin(s * (talk ? 1.35 : 0.62))
      const weight = Math.sin(s * (talk ? 0.8 : 0.45))

      const armBase = (opts.armRestY || opts.armRestZ) ? 0 : 0.35
      let pose = {
        hips: [0, sway * 0.025 * style.sway, weight * 0.015],
        spine: [breath * 0.015 * style.breath, sway * 0.03 * style.sway, -weight * 0.01],
        chest: [breath * (talk ? 0.05 : 0.035) * style.breath, sway * (talk ? 0.07 : 0.045) * style.sway, 0],
        neck: heroRig ? [0, 0, 0] : [nod * (talk ? 0.08 : 0.05) * style.nod, sway * 0.04 * style.sway + gx * 0.08, 0],
        head: heroRig ? [0, 0, 0] : [nod * (talk ? 0.12 : 0.07) * style.nod + gy * 0.08, sway * (talk ? 0.10 : 0.06) * style.sway + gx * 0.16, 0],
        'shoulder.L': [0, 0, breath * 0.015],
        'shoulder.R': [0, 0, -breath * 0.015],
        'upperArm.L': [0, 0, armBase + gesture * (talk ? 0.12 : 0.04)],
        'upperArm.R': [0, 0, -armBase - gesture * (talk ? 0.08 : 0.04)],
        // negative X bends the elbow FORWARD; positive folds it behind the back
        'lowerArm.L': [talk ? -0.26 - gesture * 0.12 : -0.05 - gesture * 0.03, 0, 0],
        'lowerArm.R': [talk ? -0.20 + gesture * 0.10 : -0.05 + gesture * 0.03, 0, 0],
        'hand.L': [0, 0, gesture * 0.06],
        'hand.R': [0, 0, -gesture * 0.06],
      }
      if (walk) {
        // walk in place, 1 s cycle: legs alternate, knees lift, arms counter-swing
        const p = s * Math.PI * 2
        const sin = Math.sin(p)
        pose = {
          hips: [0, 0.02 * sin, 0],
          spine: [0.01 * Math.sin(2 * p), 0.02 * sin, 0],
          chest: [0.02 * Math.sin(2 * p), 0.03 * sin, 0],
          neck: [0, 0.02 * sin, 0],
          head: [0, 0.03 * sin, 0],
          'upperLeg.L': [-0.30 * sin, 0, 0],
          'lowerLeg.L': [0.45 * Math.max(0, -sin), 0, 0],
          'upperLeg.R': [0.30 * sin, 0, 0],
          'lowerLeg.R': [0.45 * Math.max(0, sin), 0, 0],
          'upperArm.L': [0.14 * sin, 0, 0.03],
          'upperArm.R': [-0.14 * sin, 0, -0.03],
          'lowerArm.L': [-0.10, 0, 0],
          'lowerArm.R': [-0.10, 0, 0],
        }
      }
      const g = GESTURES[gestureName]
      if (g) {
        for (const name in g) {
          const p = pose[name] || [0, 0, 0]
          const o = g[name]
          pose[name] = [p[0] + o[0], p[1] + o[1], p[2] + o[2]]
        }
      }
      if (gestureName === 'wave') {
        const h = pose['hand.R'] || [0, 0, 0]
        pose['hand.R'] = [h[0], h[1], h[2] + Math.sin(s * 7) * 0.35]
      }
      const ep = EMOTION_POSE[emotion] || {}
      for (const name in ep) {
        const p = pose[name] || [0, 0, 0]
        const o = ep[name]
        const mul = heroRig && (name === 'head' || name === 'neck') ? 0 : 1
        pose[name] = [p[0] + o[0] * emotionAmount * mul, p[1] + o[1] * emotionAmount * mul, p[2] + o[2] * emotionAmount * mul]
      }
      for (const name in pose) {
        const node = nodes[name]
        if (!node) continue
        const rest = restQ[name] || IDENT
        const delta = SceneClip.qFromEuler(pose[name][0], pose[name][1], pose[name][2])
        const q = new BABYLON.Quaternion(rest[0], rest[1], rest[2], rest[3])
          .multiply(new BABYLON.Quaternion(delta[0], delta[1], delta[2], delta[3]))
        node.rotationQuaternion.copyFromFloats(q.x, q.y, q.z, q.w)
      }
      // Deterministic eye look: eyes lead the head, head follows with a delay.
      const eyeYaw = (autoGaze ? Math.sin(s * 0.37) * 0.55 : (Number(gaze.x) || 0)) * 0.42
      const eyePitch = (autoGaze ? Math.sin(s * 0.29 + 0.7) * 0.40 : (Number(gaze.y) || 0)) * 0.34
      for (const side of ['L', 'R']) {
        const node = nodes['eye.' + side]
        if (!node) continue
        const rest = restQ['eye.' + side] || IDENT
        const delta = SceneClip.qFromEuler(eyePitch, eyeYaw, 0)
        const q = new BABYLON.Quaternion(rest[0], rest[1], rest[2], rest[3])
          .multiply(new BABYLON.Quaternion(delta[0], delta[1], delta[2], delta[3]))
        node.rotationQuaternion.copyFromFloats(q.x, q.y, q.z, q.w)
      }
      if (skeleton) skeleton.prepare()
    }

    function visemeWeightsAt(time) {
      if (!visemes.length) return { viseme_sil: 1 }
      const list = visemes.slice().sort((a, b) => a.t - b.t)
      let i = -1
      for (let k = 0; k < list.length; k++) if (list[k].t <= time) i = k
      if (i < 0) i = 0
      const out = {}
      const cur = list[i]
      const fade = 80
      if (i > 0 && time - cur.t < fade) {
        const k = clamp((time - cur.t) / fade, 0, 1)
        addMap(out, VISEME_MAP[list[i - 1].viseme] || VISEME_MAP[0], 1 - k)
        addMap(out, VISEME_MAP[cur.viseme] || VISEME_MAP[0], k)
      } else {
        addMap(out, VISEME_MAP[cur.viseme] || VISEME_MAP[0], 1)
      }
      return out
    }

    function addMap(out, map, scale) {
      for (const k in map) out[k] = (out[k] || 0) + map[k] * scale
    }

    function applyFace(t) {
      for (const name of VISEME_MORPHS.concat(['eyeBlinkLeft', 'eyeBlinkRight', 'mouthSmile', 'mouthFrown'])) {
        setMorph(name, 0)
      }
      const weights = visemeWeightsAt(t)
      for (const name in weights) setMorph(name, weights[name])
      const phase = t % 4200
      if (phase > 3880 && phase < 4080) {
        const blink = Math.sin((phase - 3880) / 200 * Math.PI)
        setMorph('eyeBlinkLeft', blink)
        setMorph('eyeBlinkRight', blink)
      }
      const moodMap = MOOD_MORPHS[mood] || {}
      for (const name in moodMap) setMorph(name, Math.max(weights[name] || 0, moodMap[name]))
      const emo = EMOTION_MORPHS[emotion] || {}
      for (const name in emo) setMorph(name, Math.max(weights[name] || 0, emo[name] * emotionAmount))
    }

    function seek(ms) {
      const t = Math.max(0, Number(ms) || 0)
      lastTime = t
      if (!container) return t
      applyBody(t)
      applyFace(t)
      scene.render()
      return t
    }

    function setVisemes(list) {
      visemes = Array.isArray(list) ? list.filter((x) => x && typeof x.t === 'number').map((x) => ({ t: Number(x.t), viseme: Number(x.viseme) || 0 })) : []
      return seek(lastTime)
    }

    function setMotion(value) {
      motion = value === 'talk' ? 'talk' : value === 'walk' ? 'walk' : 'idle'
      return seek(lastTime)
    }

    function setMood(value) {
      mood = MOOD_MORPHS[value] ? value : 'neutral'
      return seek(lastTime)
    }

    function setGesture(value) {
      gestureName = GESTURES[value] ? value : 'none'
      return seek(lastTime)
    }

    function setEmotion(value, amount) {
      emotion = EMOTION_MORPHS[value] ? value : 'neutral'
      if (amount !== undefined) emotionAmount = clamp(Number(amount) || 0, 0, 1)
      return seek(lastTime)
    }

    function setGaze(x, y, options) {
      gaze = Object.assign({}, gaze, { x: clamp(Number(x) || 0, -1, 1), y: clamp(Number(y) || 0, -1, 1) }, options || {})
      return seek(lastTime)
    }

    function isOn(name, keys) {
      const n = String(name || '')
      return keys.some((k) => n === k || n.indexOf(k) === 0)
    }

    function applyOutfit() {
      const dress = outfit.top === 'dress'
      const showTop = (key) => !dress && outfit.top === key
      for (const mesh of parts) {
        const n = mesh.name || ''
        let on = true
        if (isOn(n, ['top_tee'])) on = showTop('tee')
        else if (isOn(n, ['top_shirt'])) on = showTop('shirt')
        else if (isOn(n, ['top_hoodie'])) on = showTop('hoodie')
        else if (isOn(n, ['dress'])) on = dress
        else if (isOn(n, ['bottom_pants'])) on = !dress && outfit.bottom === 'pants'
        else if (isOn(n, ['bottom_shorts'])) on = !dress && outfit.bottom === 'shorts'
        else if (isOn(n, ['bottom_skirt'])) on = !dress && outfit.bottom === 'skirt'
        else if (isOn(n, ['shoes_sneaker'])) on = outfit.shoes === 'sneaker'
        else if (isOn(n, ['shoes_boot'])) on = outfit.shoes === 'boot'
        else if (isOn(n, ['Sideburn'])) on = outfit.hair === 'short'
        else if (isOn(n, ['HairTail'])) on = outfit.hair === 'ponytail'
        else if (isOn(n, ['HairSide', 'HairBack'])) on = outfit.hair === 'bob' || outfit.hair === 'ponytail'
        else if (isOn(n, ['Collar.Tee'])) on = showTop('tee')
        else if (isOn(n, ['Collar.Shirt'])) on = showTop('shirt')
        else if (isOn(n, ['Collar.Hoodie'])) on = showTop('hoodie')
        else if (isOn(n, ['Button', 'Placket'])) on = showTop('shirt')
        else if (isOn(n, ['Drawstring'])) on = showTop('hoodie')
        else if (isOn(n, ['Belt', 'Buckle'])) on = !dress
        else if (isOn(n, ['HairBun'])) on = outfit.hair === 'bun'
        else if (isOn(n, ['Pocket'])) on = showTop('hoodie')
        else if (isOn(n, ['Hood'])) on = showTop('hoodie') && appearance.hood !== false
        else if (isOn(n, ['Glass'])) on = appearance.glasses !== false
        if (mesh.metadata) mesh.metadata.scenePart = on
        mesh.setEnabled(on)
      }
      if (scene) scene.render()
    }

    function setOutfit(next) {
      outfit = Object.assign({}, outfit, next || {})
      applyOutfit()
      return { gender, outfit }
    }

    function setAppearance(app) {
      applyAppearance(app)
      return seek(lastTime)
    }

    function setMorphValue(name, weight) {
      setMorph(name, weight)
      if (scene) scene.render()
      return weight
    }

    function setShape(shape) {
      if (shape && typeof shape === 'object') {
        for (const name in shape) setMorph(name, shape[name])
      }
      return seek(lastTime)
    }

    function load() {
      const done = (res) => {
        container = res
        res.addAllToScene()
        rootNode = res.meshes.find((m) => m.name === '__root__') || res.meshes[0]
        skeleton = (res.skeletons || [])[0] || null
        if (skeleton) {
          const boneMap = opts.boneMap || {}
          skeleton.bones.forEach((b) => {
            const node = (b.getTransformNode && b.getTransformNode()) || b
            if (!node) return
            const canon = boneMap[b.name] || b.name
            nodes[canon] = node
            let r = node.rotationQuaternion || BABYLON.Quaternion.FromEulerVector(node.rotation)
            if (opts.headPitch && (canon === 'head' || canon === 'neck')) {
              r = r.multiply(BABYLON.Quaternion.FromEulerAngles(opts.headPitch, 0, 0))
              node.rotationQuaternion = r.clone()
            }
            restQ[canon] = [r.x, r.y, r.z, r.w]
            if (!node.rotationQuaternion) node.rotationQuaternion = r.clone()
            info.bones.push(canon)
          })
          // T-pose hero rigs: lower the arms to a relaxed A-pose in world
          // space.  A local-Euler offset just twists/turns the limb, so the
          // world Z rotation is transformed into the bone's parent space.
          if (opts.armRestZ) {
            for (const canon of ['upperArm.L', 'upperArm.R']) {
              const node = nodes[canon]
              if (!node || !node.parent) continue
              const sign = canon === 'upperArm.L' ? 1 : -1
              node.parent.computeWorldMatrix(true)
              const piv = new BABYLON.Vector3(), sc = new BABYLON.Vector3(), pq = new BABYLON.Quaternion()
              node.parent.getWorldMatrix().decompose(sc, pq, piv)
              const rz = BABYLON.Quaternion.RotationAxis(new BABYLON.Vector3(0, 0, 1), opts.armRestZ * sign)
              const rest = restQ[canon] || IDENT
              const restQn = new BABYLON.Quaternion(rest[0], rest[1], rest[2], rest[3])
              const loc = pq.invert().multiply(rz).multiply(pq).multiply(restQn)
              restQ[canon] = [loc.x, loc.y, loc.z, loc.w]
              node.rotationQuaternion.copyFromFloats(loc.x, loc.y, loc.z, loc.w)
            }
          }
        }
        res.meshes.forEach((mesh) => {
          if (mesh.getTotalVertices && mesh.getTotalVertices() > 0) mesh.alwaysSelectAsActiveMesh = true
          mesh.isPickable = false
          parts.push(mesh)
          morphsOf(mesh)
          if (/glass/i.test(mesh.name)) accessories.glasses.push(mesh)
          if (/hood/i.test(mesh.name)) accessories.hood.push(mesh)
        })
        applyOutfit()
        res.materials.forEach((m) => { if (m && m.name) materials[m.name] = m })
        // GLB clips are data only: seek(t) must be the one time source. Babylon
        // starts the first animation group on load, which would fight seek().
        scene.animationGroups.slice().forEach((g) => { try { g.stop(); g.dispose() } catch (e) {} })
        const preset = PRESETS[opts.preset] || PRESETS.bust
        const h = opts.height || 1.8
        const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight)
        let targetY = preset.y * h / 1.8
        let radius = preset.r * h / 1.8
        if (preset === PRESETS.bust && aspect < 1.05) {
          targetY = 1.02 * h / 1.8
          radius = Math.max(radius, 2.32 * h / 1.8)
        }
        camera.setTarget(new BABYLON.Vector3(0, targetY, 0))
        camera.radius = radius
        applyAppearance(appearance)
        applyFace(0)
        applyBody(0)
        scene.render()
        readyResolve(info)
      }
      const fail = (e) => {
        info.error = String(e && e.message ? e.message : e)
        readyReject(info)
      }
      try {
        if (opts.buffer) {
          const bytes = opts.buffer instanceof ArrayBuffer ? new Uint8Array(opts.buffer) : opts.buffer
          const file = new File([bytes], opts.name || 'character.glb', { type: 'model/gltf-binary' })
          BABYLON.SceneLoader.LoadAssetContainerAsync('', file, scene).then(done).catch(fail)
        } else {
          const src = String(opts.src || '')
          const i = src.lastIndexOf('/')
          const rootUrl = i >= 0 ? src.slice(0, i + 1) : ''
          const file = i >= 0 ? src.slice(i + 1) : src
          BABYLON.SceneLoader.LoadAssetContainerAsync(rootUrl, file, scene).then(done).catch(fail)
        }
      } catch (e) { fail(e) }
    }

    function onResize() { engine.resize() }
    window.addEventListener('resize', onResize)
    if (opts.interactive) engine.runRenderLoop(() => scene.render())

    function destroy() {
      window.removeEventListener('resize', onResize)
      try { scene.dispose() } catch (e) {}
      try { engine.dispose() } catch (e) {}
    }

    load()
    return {
      ready,
      info,
      camera,
      scene,
      seek,
      setVisemes,
      setMotion,
      setMood,
      setGesture,
      setEmotion,
      setGaze,
      setOutfit,
      setAppearance,
      setMorph: setMorphValue,
      setShape,
      destroy,
    }
  }

  root.SceneRig = { create }
})(typeof globalThis !== 'undefined' ? globalThis : this)
