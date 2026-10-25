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
      const s = t / 1000
      const breath = Math.sin(s * Math.PI * 2 / 4.2)
      const sway = Math.sin(s * (talk ? 1.1 : 0.62))
      const nod = Math.sin(s * (talk ? 2.3 : 1.05))
      const gesture = Math.sin(s * (talk ? 1.35 : 0.62))

      const pose = {
        chest: [breath * (talk ? 0.026 : 0.018), sway * (talk ? 0.05 : 0.04), 0],
        neck: [nod * (talk ? 0.055 : 0.035), sway * 0.03, 0],
        head: [nod * (talk ? 0.07 : 0.045), sway * (talk ? 0.06 : 0.05), 0],
        'upperArm.L': [0, 0, 0.65 + gesture * (talk ? 0.12 : 0.05)],
        'upperArm.R': [0, 0, -0.85 - gesture * (talk ? 0.10 : 0.05)],
        'lowerArm.L': [talk ? 0.16 + gesture * 0.12 : 0.04 + gesture * 0.03, 0, 0],
        'lowerArm.R': [talk ? 0.12 - gesture * 0.10 : 0.04 - gesture * 0.03, 0, 0],
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
      motion = value === 'talk' ? 'talk' : 'idle'
      return seek(lastTime)
    }

    function setMood(value) {
      mood = MOOD_MORPHS[value] ? value : 'neutral'
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
        else if (isOn(n, ['Collar.Shirt'])) on = showTop('shirt')
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

    function load() {
      const done = (res) => {
        container = res
        res.addAllToScene()
        rootNode = res.meshes.find((m) => m.name === '__root__') || res.meshes[0]
        skeleton = (res.skeletons || [])[0] || null
        if (skeleton) {
          skeleton.bones.forEach((b) => {
            const node = (b.getTransformNode && b.getTransformNode()) || b
            if (!node) return
            nodes[b.name] = node
            const r = node.rotationQuaternion || BABYLON.Quaternion.FromEulerVector(node.rotation)
            restQ[b.name] = [r.x, r.y, r.z, r.w]
            if (!node.rotationQuaternion) node.rotationQuaternion = r.clone()
            info.bones.push(b.name)
          })
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
      setOutfit,
      setAppearance,
      destroy,
    }
  }

  root.SceneRig = { create }
})(typeof globalThis !== 'undefined' ? globalThis : this)
