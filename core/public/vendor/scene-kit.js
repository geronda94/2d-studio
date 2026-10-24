/* SceneKit — маленький детерминированный helper для 2D-сцен.
 *
 * Идея: сцена — это чистые HTML/CSS/JS. SceneKit даёт три вещи:
 *   cues(list)         — ключи на локальном таймлайне (stateAt / integrate)
 *   mechanism(spec)    — механизм с фазой (колёса, качание, пар)
 *   parallax(layers)   — параллакс фоновых слоёв
 *   characterRig(el)   — управляемый персонаж: виземы, моргание, взгляд, жесты
 *
 * Ничего не запускает само: всё считается от seek(t).
 */
(function () {
  // настроение → положение бровей (px вверх, поворот наружу в градусах)
  const MOOD_BROW = {
    neutral: { brow: 0, tilt: 0 },
    joy: { brow: -1.5, tilt: 6 },
    anger: { brow: 1.5, tilt: -8 },
    sad: { brow: -1, tilt: -5 },
    surprise: { brow: -3.5, tilt: 10 },
  }
  function cues(list, opts) {
    const points = (Array.isArray(list) ? list : [])
      .filter((c) => c && Number.isFinite(Number(c.at)))
      .map((c) => ({ ...c, at: Number(c.at) }))
      .sort((a, b) => a.at - b.at)
    // smooth: значение между ключами плавно интерполируется (smoothstep),
    // иначе скорость прыгает ступенчаткой и движение «дёргается».
    const smooth = !!(opts && opts.smooth)

    function stateAt(t) {
      const out = {}
      for (const c of points) {
        if (c.at > t) break
        if (c.set) Object.assign(out, c.set)
      }
      return out
    }

    // Текущее (сглаженное) значение ключа в момент t.
    function valueAt(key, t, fallback = 0) {
      let v0 = fallback
      let t0 = 0
      for (const c of points) {
        if (!c.set || c.set[key] === undefined) continue
        const v1 = Number(c.set[key]) || 0
        if (c.at <= t) { v0 = v1; t0 = c.at; continue }
        if (!smooth) return v0
        const span = c.at - t0
        const k = span > 0 ? Math.min(1, Math.max(0, (t - t0) / span)) : 1
        return v0 + (v1 - v0) * (k * k * (3 - 2 * k))
      }
      return v0
    }

    // Интеграл значения ключа по времени. Нужен, чтобы скорость можно было
    // менять ключами без скачков фазы (колесо не «прыгает»).
    function integrate(key, t, fallback = 0) {
      if (smooth) {
        let acc = 0
        let v0 = fallback
        let t0 = 0
        for (const c of points) {
          if (!c.set || c.set[key] === undefined) continue
          const v1 = Number(c.set[key]) || 0
          const dt = Math.max(0, Math.min(t, c.at) - t0)
          // среднее по сегменту: симметричный smoothstep даёт ровно (v0+v1)/2
          if (dt > 0) acc += (dt / 1000) * ((v0 + v1) / 2)
          if (c.at > t) return acc
          t0 = c.at
          v0 = v1
        }
        acc += (Math.max(0, t - t0) / 1000) * v0
        return acc
      }
      let value = fallback
      let acc = 0
      for (let i = 0; i < points.length; i++) {
        const c = points[i]
        if (c.at > t) break
        if (value) {
          const nextAt = points[i + 1] ? Math.min(t, points[i + 1].at) : t
          if (nextAt > c.at) acc += ((nextAt - c.at) / 1000) * value
        }
        if (c.set && c.set[key] !== undefined) value = Number(c.set[key]) || 0
      }
      return acc
    }

    return { points, stateAt, integrate, valueAt }
  }

  function mechanism(spec) {
    const start = Number(spec.start) || 0
    const speed = Number(spec.speed) || 1
    const loop = spec.loop !== false
    return {
      seek(t) {
        if (t < start) return
        let phase = ((t - start) / 1000) * speed
        phase = loop ? phase % 1 : Math.min(1, phase)
        if (typeof spec.update === 'function') spec.update(phase, t)
      },
    }
  }

  function parallax(layers, opts) {
    const speed = (opts && Number(opts.speed)) || 1
    return {
      seek(t) {
        const x = -((t / 1000) * speed * 100)
        for (const l of layers) {
          const depth = Number(l.depth) || 1
          l.el.style.transform = `translate3d(${(x * depth).toFixed(2)}px,0,0)`
        }
      },
    }
  }

  // 2.5D camera: move depth layers by a deterministic path.
  // path(t) -> { x, y, z, zoom, rot } (pixels / multiplier / degrees).
  function camera(layers, opts) {
    const path = (opts && opts.path) || function () { return {} }
    return {
      seek(t) {
        const c = path(t) || {}
        for (const l of layers) {
          const d = Number(l.depth) || 1
          const x = (Number(c.x) || 0) * d
          const y = (Number(c.y) || 0) * d
          const z = (Number(c.z) || 0) * d
          const zoom = 1 + (Number(c.zoom) || 0) * d
          const rot = (Number(c.rot) || 0) * d
          l.el.style.transform = 'translate3d(' + x.toFixed(2) + 'px,' + y.toFixed(2) + 'px,' + z.toFixed(2) + 'px) scale(' + zoom.toFixed(4) + ') rotate(' + rot.toFixed(3) + 'deg)'
        }
      },
    }
  }

  // Deterministic scatter: clone an object N times with seeded positions/scales.
  // Solves "100 identical trees" without hand-duplicating layers.
  function mulberry32(seed) {
    let a = seed >>> 0
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0
      let t = Math.imul(a ^ (a >>> 15), 1 | a)
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
  }

  function scatter(root, opts) {
    if (!root || !root.parentNode) return []
    const o = opts || {}
    const count = Math.max(1, Number(o.count) || 1)
    const x = o.x || [0.05, 0.95]
    const y = o.y || [0.1, 0.35]
    const scale = o.scale || [0.7, 1.3]
    const rotate = o.rotate || [-4, 4]
    const rand = mulberry32(Number(o.seed) || 1)
    const out = []
    for (let i = 0; i < count; i++) {
      const el = i === 0 ? root : root.cloneNode(true)
      if (i > 0) root.parentNode.appendChild(el)
      const xv = x[0] + (x[1] - x[0]) * rand()
      const yv = y[0] + (y[1] - y[0]) * rand()
      const sv = scale[0] + (scale[1] - scale[0]) * rand()
      const rv = rotate[0] + (rotate[1] - rotate[0]) * rand()
      el.style.left = (xv * 100).toFixed(2) + '%'
      el.style.bottom = (yv * 100).toFixed(2) + '%'
      el.style.transform = 'scale(' + sv.toFixed(3) + ') rotate(' + rv.toFixed(1) + 'deg)'
      out.push(el)
    }
    return out
  }

  // Lip-sync: viseme timeline is data, the renderer only asks "which viseme at t".
  // visemes: [{ t: 0, viseme: 0 }, { t: 120, viseme: 1 }, ...] or [{ timeMs, viseme }]
  function visemeAt(visemes, t) {
    let v = 0
    const list = visemes || []
    for (const item of list) {
      const at = item.t !== undefined ? item.t : item.timeMs
      if (at <= t) v = item.v !== undefined ? item.v : item.viseme
      else break
    }
    return v
  }

  // { cur, next, k } на момент t: k растёт 0→1 за последние `blend` мс текущего
  // визема, чтобы рот перетекал между формами, а не щёлкал. Детерминированно.
  function visemeBlend(visemes, t, blend) {
    const list = (Array.isArray(visemes) ? visemes : [])
      .map((x) => ({ t: Number(x.t !== undefined ? x.t : x.timeMs) || 0, v: Number(x.v !== undefined ? x.v : x.viseme) || 0 }))
      .sort((a, b) => a.t - b.t)
    const b = Number(blend) >= 0 ? Number(blend) : 60
    let cur = 0
    let next = 0
    let nextAt = null
    for (const item of list) {
      if (item.t <= t) { cur = item.v; next = 0; nextAt = null } else { next = item.v; nextAt = item.t; break }
    }
    let k = 0
    if (nextAt !== null && b > 0 && t > nextAt - b) k = Math.min(1, (t - (nextAt - b)) / b)
    return { cur, next, k }
  }

  function lipsync(opts) {
    const list = (opts && opts.visemes) || []
    const blend = opts ? opts.blend : 60
    return {
      seek(t) {
        if (typeof opts.onViseme === 'function') opts.onViseme(visemeAt(list, t), t)
        if (typeof opts.onVisemePair === 'function') {
          const b = visemeBlend(list, t, blend)
          opts.onVisemePair(b.cur, b.next, b.k, t)
        }
      },
    }
  }

  // Полностью управляемый персонаж: привязывает SVG-риг (.obj-character с
  // data-rig-частями и 10 path-виземами рта) к seek(t).
  // opts: { visemes, mood, blend, gestureAt, gestureDur, walk, blinkPeriod, blinkMs, seed }
  function characterRig(el, opts) {
    if (!el) return { seek() {} }
    const o = opts || {}
    const q = (s) => el.querySelector(s)
    const parts = {
      root: q('[data-rig="root"]'),
      head: q('[data-rig="head"]'),
      hair: q('[data-rig="hair"]'),
      torso: q('[data-rig="torso"]'),
      armL: q('[data-rig="arm-left"]'),
      armR: q('[data-rig="arm-right"]'),
      legL: q('[data-rig="leg-left"]'),
      legR: q('[data-rig="leg-right"]'),
      browL: q('[data-rig="brow-left"]'),
      browR: q('[data-rig="brow-right"]'),
      lidL: q('[data-rig="lid-left"]'),
      lidR: q('[data-rig="lid-right"]'),
      gaze: q('[data-rig="gaze"]'),
      mouth: q('[data-rig="mouth"]'),
    }
    const visPaths = parts.mouth ? Array.from(parts.mouth.querySelectorAll('[data-viseme]')) : []
    // mood → { brow: подъём бровей (px, отрицательный = вверх), tilt: поворот наружу (deg) }
    const mood = MOOD_BROW[o.mood] || MOOD_BROW.neutral
    const blend = o.blend !== undefined ? o.blend : 70
    const blinkPeriod = Number(o.blinkPeriod) || 3400
    const blinkMs = Number(o.blinkMs) || 170
    const blinkOffset = Number(o.seed) || 0
    const clamp01 = (x) => Math.max(0, Math.min(1, x))
    const ease = (x) => { const c = clamp01(x); return c * c * (3 - 2 * c) }

    function setT(el2, tr) { if (el2) el2.style.transform = tr }

    function seek(t) {
      const s = t / 1000
      // жест: подъём правой руки в окне [gestureAt, gestureAt+gestureDur]
      let gesture = 0
      if (o.gestureAt !== undefined && o.gestureAt !== null) {
        const dur = Number(o.gestureDur) || 1400
        const up = ease((t - o.gestureAt) / 320)
        const down = 1 - ease((t - (o.gestureAt + dur)) / 320)
        gesture = Math.min(up, down)
      }
      // дыхание / покачивание / микродвижения головы — чистая математика от t
      const breath = Math.sin(s * 1.5)
      setT(parts.torso, `scaleY(${(1 + 0.012 * breath).toFixed(4)})`)
      setT(parts.root, `translate(0, ${(0.8 * breath).toFixed(3)})`)
      const headA = 1.3 * Math.sin(s * 0.8) + 3.2 * gesture
      setT(parts.head, `rotate(${headA.toFixed(3)}deg)`)
      // волосы отстают от поворота головы (вторичное движение)
      if (parts.hair) {
        const lag = -headA * 0.45 + 0.55 * Math.sin(s * 1.7 + 0.6)
        setT(parts.hair, `rotate(${lag.toFixed(3)}deg)`)
      }
      // взгляд: медленный дрейф + быстрый саккадический шум
      if (parts.gaze) {
        const gx = 1.6 * Math.sin(s * 0.7) + 0.5 * Math.sin(s * 2.3)
        const gy = 0.8 * Math.cos(s * 0.5) + 0.3 * Math.sin(s * 1.9)
        parts.gaze.style.transform = `translate(${gx.toFixed(2)}px, ${gy.toFixed(2)}px)`
      }
      // моргание: период + seed offset; triangle-curve 0→1→0 внутри blinkMs
      const bt = (t + blinkOffset) % blinkPeriod
      const closed = bt < blinkMs ? Math.sin((bt / blinkMs) * Math.PI) : 0
      setT(parts.lidL, `scaleY(${closed.toFixed(3)})`)
      setT(parts.lidR, `scaleY(${closed.toFixed(3)})`)
      // настроение: брови
      if (parts.browL) setT(parts.browL, `translate(${-mood.tilt * 0.2}px, ${mood.brow}px) rotate(${mood.tilt}deg)`)
      if (parts.browR) setT(parts.browR, `translate(${mood.tilt * 0.2}px, ${mood.brow}px) rotate(${-mood.tilt}deg)`)
      // жест: подъём правой руки в окне [gestureAt, gestureAt+gestureDur]
      if (parts.armR) setT(parts.armR, `rotate(${(-88 * gesture).toFixed(2)}deg)`)
      // ходьба: махи ног/рук от фазы
      if (o.walk) {
        const swing = Math.sin(s * 7) * 18
        setT(parts.legL, `rotate(${swing.toFixed(2)}deg)`)
        setT(parts.legR, `rotate(${(-swing).toFixed(2)}deg)`)
        setT(parts.armL, `rotate(${(-swing * 0.6).toFixed(2)}deg)`)
        if (!o.gestureAt) setT(parts.armR, `rotate(${(swing * 0.6).toFixed(2)}deg)`)
      }
      // виземы: кроссфейд двух форм рта + язык/челюсть по «открытости»
      if (visPaths.length) {
        const v = visemeBlend(o.visemes || [], t, blend)
        // openness по виземам 0..9 (0 — закрыт)
        const OPEN = [0.06, 0.9, 0.04, 0.3, 0.7, 0.4, 0.55, 0.8, 0.75, 0.25]
        const tongue = parts.mouth.querySelector('[data-viseme="t"]')
        for (const path of visPaths) {
          const idx = path.getAttribute('data-viseme')
          if (idx === 't') continue
          const n = Number(idx)
          path.style.opacity = n === v.cur ? (1 - v.k).toFixed(3) : n === v.next ? v.k.toFixed(3) : '0'
        }
        const open = (OPEN[v.cur] || 0) * (1 - v.k) + (OPEN[v.next] || 0) * v.k
        if (tongue) tongue.style.opacity = open > 0.5 ? ((open - 0.5) * 2).toFixed(3) : '0'
        setT(parts.mouth, `translate(0, ${(2.6 * open).toFixed(2)}px)`)
      }
    }
    return { seek }
  }


  // Per-object view switching: { car: 'front', building: 'corner' }.
  // Objects opt in with CSS classes like .obj-car.view-front.
  function applyViews(root, map) {
    const entries = Object.entries(map || {})
    for (const [slug, view] of entries) {
      const nodes = root.querySelectorAll('.obj-' + slug)
      nodes.forEach((el) => {
        Array.from(el.classList)
          .filter((c) => c.indexOf('view-') === 0)
          .forEach((c) => el.classList.remove(c))
        if (view) el.classList.add('view-' + view)
      })
    }
  }

  // Композиция механизмов: удобно отдавать в window.scene.seek.
  function compose(...items) {
    return {
      seek(t) {
        for (const item of items) {
          if (item && typeof item.seek === 'function') item.seek(t)
        }
      },
    }
  }

  // ── Атмосфера: детерминированные частицы на canvas ───────────────────────
  // Позиция частицы — чистая функция от t, поэтому кадр воспроизводим.
  function particles(canvas, opts) {
    const o = opts || {}
    if (!canvas || !canvas.getContext) return { seek() {} }
    const ctx = canvas.getContext('2d')
    const w = canvas.width || 1920
    const h = canvas.height || 1080
    const count = Math.max(0, Number(o.count) || 50)
    const color = o.color || '255,220,150'
    const rand = mulberry32(Number(o.seed) || 42)
    const speedX = Number(o.speedX) || 0
    const speedY = Number(o.speedY) || 0
    const sizeMin = Number(o.sizeMin) || 1
    const sizeMax = Number(o.sizeMax) || 3
    const alphaMin = Number(o.alphaMin) || 0.08
    const alphaMax = Number(o.alphaMax) || 0.35
    const driftX = Number(o.driftX) || 0
    const driftFreq = Number(o.driftFreq) || 0.6
    const blink = o.blink !== false

    const ps = []
    for (let i = 0; i < count; i++) {
      ps.push({
        x0: rand() * w,
        y0: rand() * h,
        vx: (rand() - 0.5) * 2 * speedX,
        vy: -speedY - rand() * speedY,
        size: sizeMin + rand() * (sizeMax - sizeMin),
        phase: rand() * Math.PI * 2,
        freq: 0.4 + rand() * 1.3,
        amp: driftX * (0.6 + rand() * 0.8),
        alpha: alphaMin + rand() * (alphaMax - alphaMin),
      })
    }

    return {
      seek(t) {
        const s = t / 1000
        ctx.clearRect(0, 0, w, h)
        for (const p of ps) {
          let x = p.x0 + p.vx * s + Math.sin(s * p.freq + p.phase) * p.amp
          let y = p.y0 + p.vy * s
          x = ((x % w) + w) % w
          y = ((y % h) + h) % h
          const pulse = blink ? 0.65 + 0.35 * Math.sin(s * 2.4 + p.phase) : 1
          ctx.globalAlpha = Math.max(0, Math.min(1, p.alpha * pulse))
          ctx.fillStyle = 'rgb(' + color + ')'
          ctx.beginPath()
          ctx.arc(x, y, p.size, 0, Math.PI * 2)
          ctx.fill()
        }
        ctx.globalAlpha = 1
      },
    }
  }

  // ── Микро-анимация персонажа: дыхание, покачивание, моргание ─────────────
  // Работает и с портретом (.portrait-img), и с SVG-ригом (data-rig).
  function idle(root, opts) {
    if (!root) return { seek() {} }
    const o = opts || {}
    const idx = Number(o.index) || 0
    const portrait = root.querySelector('.portrait-img')
    const head = root.querySelector('[data-rig="head"]')
    const torso = root.querySelector('[data-rig="torso"]')
    const eyes = Array.from(root.querySelectorAll('[data-rig="eye"], [data-rig="eyes"]'))
    const blinkPeriod = Number(o.blinkPeriod) || 3800
    const blinkMs = Number(o.blinkMs) || 150

    return {
      seek(t) {
        const s = t / 1000
        if (portrait) {
          const breath = Math.sin(s * 1.9 + idx * 1.3) * 1.4
          const sway = Math.sin(s * 0.7 + idx) * 0.6
          const sc = 1 + Math.sin(s * 1.1 + idx) * 0.004
          const driftX = Math.sin(s * 0.45 + idx * 2.1) * 2
          portrait.style.transform =
            'translate3d(' + driftX.toFixed(2) + 'px,' + breath.toFixed(2) + 'px,0) rotate(' +
            sway.toFixed(3) + 'deg) scale(' + sc.toFixed(4) + ')'
          return
        }
        if (torso) {
          const b = Math.sin(s * 1.9 + idx)
          torso.style.transform = 'scale(' + (1 - b * 0.005).toFixed(4) + ',' + (1 + b * 0.02).toFixed(4) + ')'
          torso.style.transformOrigin = 'bottom center'
        }
        if (head) {
          const dip = Math.sin(s * 1.9 - 0.4) * 2
          const tilt = Math.sin(s * 0.95) * 1.2
          head.style.transform = 'translate3d(0,' + dip.toFixed(2) + 'px,0) rotate(' + tilt.toFixed(3) + 'deg)'
        }
        if (eyes.length) {
          const cycle = ((t + idx * 640) % blinkPeriod + blinkPeriod) % blinkPeriod
          const closed = cycle > blinkPeriod - blinkMs
            ? 1 - Math.abs(((cycle - (blinkPeriod - blinkMs)) / blinkMs) - 0.5) * 2
            : 1
          for (const e of eyes) e.style.transform = 'scale(1,' + closed.toFixed(3) + ')'
        }
      },
    }
  }

  // ── Пост-обработка кадра: зерно + виньетка + цветовая коррекция ──────────
  // Один вызов поднимает «цифровой» кадр до «кинематографичного».
  function grain(root, opts) {
    if (!root) return null
    const o = opts || {}
    let fx = root.querySelector('.layer-fx')
    if (!fx) {
      fx = document.createElement('div')
      fx.className = 'layer layer-fx'
      fx.setAttribute('data-layer', 'fx')
      const overlay = root.querySelector('.layer-overlay')
      if (overlay && overlay.parentNode) overlay.parentNode.insertBefore(fx, overlay)
      else root.appendChild(fx)
    }
    const noise = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E"
    const wrap = document.createElement('div')
    wrap.className = 'post-fx'
    wrap.style.cssText = 'position:absolute;inset:0;pointer-events:none;z-index:40'
    const layer = (cls, css) => {
      const d = document.createElement('div')
      d.className = cls
      d.style.cssText = 'position:absolute;inset:0;pointer-events:none;' + css
      wrap.appendChild(d)
      return d
    }
    if (o.grain !== false) {
      layer('post-grain', 'background-image:url(' + noise + ');background-size:160px 160px;opacity:' +
        (o.grainOpacity !== undefined ? o.grainOpacity : 0.12) + ';mix-blend-mode:overlay')
    }
    if (o.vignette !== false) {
      layer('post-vignette', 'background:radial-gradient(ellipse at 50% 45%, transparent 40%, rgba(0,0,0,' +
        (o.vignetteStrength || 0.42) + ') 100%)')
    }
    if (o.grade !== false) {
      layer('post-grade', 'background:linear-gradient(180deg, rgba(255,205,130,.05) 0%, transparent 38%, transparent 68%, rgba(8,16,34,.16) 100%);mix-blend-mode:soft-light')
    }
    fx.appendChild(wrap)
    return wrap
  }

  // ── Контактная тень: «приземляет» объект ────────────────────────────────
  function shadow(el, opts) {
    if (!el) return null
    const o = opts || {}
    const s = document.createElement('div')
    s.className = 'obj-shadow'
    s.style.cssText = [
      'position:absolute', 'left:' + (o.left !== undefined ? o.left : 8) + '%',
      'right:' + (o.right !== undefined ? o.right : 8) + '%',
      'bottom:' + (o.bottom !== undefined ? o.bottom : -2) + '%',
      'height:' + (o.height !== undefined ? o.height : 9) + '%',
      'background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,' + (o.opacity || 0.4) + ') 0%, transparent 70%)',
      'filter:blur(' + (o.blur || 3) + 'px)', 'pointer-events:none',
    ].join(';')
    // тень должна лежать ПОД объектом, а не поверх
    if (el.firstChild) el.insertBefore(s, el.firstChild)
    else el.appendChild(s)
    return s
  }

  // ── Формы рта (локальная система: центр 0,0, номинальная ширина 10) ─────
  // Используются и в SVG-риге, и в оверлее поверх нарисованного портрета.
  const VISEME_SHAPES = [
    'M-4.6 -0.4 Q0 1.7 4.6 -0.4 Q0 0.3 -4.6 -0.4 Z',            // 0 neutral/closed
    'M-4.8 -1.2 Q0 -3.3 4.8 -1.2 Q3 4.2 0 4.2 Q-3 4.2 -4.8 -1.2 Z', // 1 AEI
    'M-2.6 0 Q0 1.3 2.6 0 Q0 0.4 -2.6 0 Z',                      // 2 BMP
    'M-3.8 -0.8 Q0 -2.1 3.8 -0.8 Q2.6 1.9 0 1.9 Q-2.6 1.9 -3.8 -0.8 Z', // 3 FV
    'M-4.4 -1 Q0 -2.7 4.4 -1 Q3 3.4 0 3.4 Q-3 3.4 -4.4 -1 Z',    // 4 CDGKNRST
    'M-2.4 -0.8 Q0 -1.7 2.4 -0.8 Q1.9 2.1 0 2.1 Q-1.9 2.1 -2.4 -0.8 Z', // 5 U
    'M-3.2 -1 Q0 -2.3 3.2 -1 Q2.6 3.1 0 3.1 Q-2.6 3.1 -3.2 -1 Z', // 6 ChJSh
    'M-3.6 -1 Q0 -2.9 3.6 -1 Q2.8 3.8 0 3.8 Q-2.8 3.8 -3.6 -1 Z', // 7 L
    'M-3 -1 Q0 -2.1 3 -1 Q3 2.7 0 2.7 Q-3 2.7 -3 -1 Z',        // 8 O
    'M-2.2 -0.6 Q0 -1.3 2.2 -0.6 Q1.8 1.5 0 1.5 Q-1.8 1.5 -2.2 -0.6 Z', // 9 QW
  ]
  const TONGUE_SHAPE = 'M-2.6 1.6 Q0 0.9 2.6 1.6 Q1.8 3.3 0 3.3 Q-1.8 3.3 -2.6 1.6 Z'

  // Слой рта поверх нарисованного портрета: 10 форм + язык + веки.
  // opts: { x, y, w } — центр рта и ширина в % картинки; lip/skin — цвета.
  function mouthLayer(host, opts) {
    if (!host) return null
    const o = opts || {}
    const cx = Number(o.x) || 50
    const cy = Number(o.y) || 46
    const w = Number(o.w) || 7
    const scale = w / 10
    const ns = 'http://www.w3.org/2000/svg'
    const svg = document.createElementNS(ns, 'svg')
    svg.setAttribute('class', 'mouth-layer')
    svg.setAttribute('viewBox', '0 0 100 100')
    svg.setAttribute('preserveAspectRatio', 'none')
    const g = document.createElementNS(ns, 'g')
    g.setAttribute('class', 'mouth')
    g.setAttribute('transform', 'translate(' + cx + ',' + cy + ') scale(' + scale.toFixed(4) + ')')
    const mk = (d, cls, viseme) => {
      const p = document.createElementNS(ns, 'path')
      p.setAttribute('d', d)
      p.setAttribute('class', cls)
      p.setAttribute('data-viseme', String(viseme))
      g.appendChild(p)
      return p
    }
    VISEME_SHAPES.forEach((d, i) => mk(d, 'vis' + (i === 0 ? ' vis-base' : ''), i))
    mk(TONGUE_SHAPE, 'vis tongue', 't')
    svg.appendChild(g)
    host.appendChild(svg)
    // веки для моргания (только если заданы глаза)
    const eyes = o.eyes || []
    eyes.forEach((e, i) => {
      const lid = document.createElementNS(ns, 'ellipse')
      lid.setAttribute('class', 'lid')
      lid.setAttribute('data-rig', i === 0 ? 'lid-left' : 'lid-right')
      lid.setAttribute('cx', e[0])
      lid.setAttribute('cy', e[1])
      lid.setAttribute('rx', e[2] || 3.4)
      lid.setAttribute('ry', e[3] || 2.6)
      svg.appendChild(lid)
    })
    return svg
  }

  // ── Персонаж-портрет: нарисованный кадр + оверлей рта/век ───────────────
  // opts: { image, mouth:{x,y,w}, lip, skin, eyes, visemes, mood, breath }
  function portraitRig(el, opts) {
    if (!el) return { seek() {} }
    const o = opts || {}
    const img = el.querySelector('.portrait-img')
    const mouth = o.mouth || { x: 50, y: 46, w: 7 }
    if (img && o.image) img.src = o.image
    const layer = mouthLayer(el, {
      x: mouth.x, y: mouth.y, w: mouth.w, eyes: o.eyes,
    })
    const visPaths = layer ? Array.from(layer.querySelectorAll('.vis')) : []
    const lids = el.querySelectorAll('.lid')
    const blinkPeriod = Number(o.blinkPeriod) || 4200
    const blinkMs = Number(o.blinkMs) || 160
    const mood = MOOD_BROW[o.mood] || MOOD_BROW.neutral

    function seek(t) {
      const s = t / 1000
      if (img) {
        const breath = Math.sin(s * 1.35)
        const sway = Math.sin(s * 0.62) * 0.45
        const drift = Math.sin(s * 0.38) * 0.8
        img.style.transform = 'translate3d(' + drift.toFixed(2) + 'px,' + (breath * 1.3).toFixed(2) +
          'px,0) rotate(' + sway.toFixed(3) + 'deg) scale(' + (1 + breath * 0.004).toFixed(4) + ')'
      }
      // веки: моргание
      if (lids.length) {
        const bt = (t + Number(o.seed || 0)) % blinkPeriod
        const closed = bt < blinkMs ? Math.sin((bt / blinkMs) * Math.PI) : 0
        for (const l of lids) l.style.transform = 'scaleY(' + closed.toFixed(3) + ')'
      }
      // рот: кроссфейд форм
      if (visPaths.length) {
        const v = visemeBlend(o.visemes || [], t, o.blend !== undefined ? o.blend : 70)
        for (const p of visPaths) {
          const idx = p.getAttribute('data-viseme')
          if (idx === 't') {
            const OPEN = [0.06, 0.9, 0.04, 0.3, 0.7, 0.4, 0.55, 0.8, 0.75, 0.25]
            const open = (OPEN[v.cur] || 0) * (1 - v.k) + (OPEN[v.next] || 0) * v.k
            p.style.opacity = open > 0.55 ? ((open - 0.55) / 0.45).toFixed(3) : '0'
            continue
          }
          const n = Number(idx)
          p.style.opacity = n === v.cur ? (1 - v.k).toFixed(3) : n === v.next ? v.k.toFixed(3) : '0'
        }
      }
    }
    return { seek }
  }

  // ── Rive: детерминированный кадр через scrub ───────────────────────────
  // Контракт тот же: кадр = чистая функция от t.
  // scrub() ставит время анимаций/стейт-машины и СИНХРОННО рисует кадр,
  // поэтому ни rAF, ни wall-clock не участвуют.
  function rive(canvas, opts) {
    const o = opts || {}
    const userReady = o.onReady
    const userError = o.onError
    if (!canvas || typeof window.rive === 'undefined') return { seek() {}, ready: Promise.resolve(null) }
    let r = null
    let inputs = null
    let lastT = null
    let lastViseme = null
    let visemeProp = null
    let poseProp = null
    let moodProp = null
    let resolveReady = null
    const readyPromise = new Promise((res) => { resolveReady = res })

    let loaded = false
    const instance = new window.rive.Rive({
      src: o.src,
      canvas,
      autoplay: false,
      autoBind: true,
      stateMachine: o.stateMachine || undefined,
      autoBind: true,
      layout: o.layout || new window.rive.Layout({ fit: window.rive.Fit.Contain }),
      onLoad() {
        r = instance
        loaded = true
        try { r.resizeDrawingSurfaceToCanvas() } catch (e) {}
        try { inputs = o.stateMachine ? r.stateMachineInputs(o.stateMachine) : null } catch (e) { inputs = null }
        // Стейт-машина ДОЛЖНА играть: виземы — это её состояния.
        // Время задаёт сам runtime (переходы плавные), мы лишь ставим входы.
        if (o.stateMachine) { try { r.play(o.stateMachine) } catch (e) {} }
        // Data binding: enum-свойства view model
        try {
          const vm = r.viewModelInstance
          if (vm) {
            visemeProp = vm.enum(o.visemeProperty || 'mouthVisemeCode')
            poseProp = vm.enum(o.poseProperty || 'pose')
            if (o.mood && o.moodProperty) moodProp = vm.enum(o.moodProperty)
          }
        } catch (e) { visemeProp = null }
        if (resolveReady) resolveReady(r)
        if (typeof userReady === 'function') userReady(r, inputs)
        seek(o.t0 || 0)
      },
      onLoadError(e) { if (typeof userError === 'function') userError(e) },
    })

    function applyInputs(t) {
      if (!inputs) return
      const viseme = visemeAt(o.visemes || [], t)
      for (const inp of inputs) {
        const n = String(inp.name || '')
        if (o.inputMap && o.inputMap[n]) {
          const v = o.inputMap[n](t, viseme, inp)
          if (v !== undefined && v !== null) inp.value = v
        } else if (o.phonemeInput && n === o.phonemeInput) {
          inp.value = viseme
        }
      }
      if (o.gazeInput) {
        const gx = o.gaze ? o.gaze(t) : { x: 0, y: 0 }
        for (const inp of inputs) {
          if (inp.name === o.gazeInput.x) inp.value = gx.x
          if (inp.name === o.gazeInput.y) inp.value = gx.y
        }
      }
      lastViseme = viseme
    }

    function seek(t) {
      if (!r && !loaded) return
      const viseme = visemeAt(o.visemes || [], t)
      // 1) view model: главный путь для Rive 2.x (enum виземов/позы)
      if (visemeProp) {
        const code = (o.visemeCodes && o.visemeCodes[viseme]) || viseme
        try { visemeProp.value = code } catch (e) {}
        if (poseProp) { try { poseProp.value = o.pose || 'idle' } catch (e) {} }
        if (moodProp && o.mood) { try { moodProp.value = o.mood } catch (e) {} }
        lastViseme = viseme
        lastT = t
        return
      }
      // 2) fallback: state machine inputs + scrub (старые ассеты)
      applyInputs(t)
      try { r.scrub(o.stateMachine || undefined, t / 1000) } catch (e) { try { r.scrub(undefined, t / 1000) } catch (e2) {} }
      try { r.drawFrame() } catch (e) {}
      lastT = t
    }

    return {
      instance,
      seek,
      get lastTime() { return lastT },
      get viseme() { return lastViseme },
      destroy() { try { instance.cleanup() } catch (e) {} },
      ready: readyPromise,
    }
  }

  // Ready-made Rive character (linear animations): scrubbed from seek(t).
  function riveActor(canvas, opts) {
    if (window.RiveActor && typeof window.RiveActor.create === 'function') {
      return window.RiveActor.create(canvas, opts)
    }
    return { ready: Promise.resolve(null), seek() {}, setViseme() {}, setExpression() {} }
  }

  // 3D avatar (Ready Player Me GLB): Babylon renders one deterministic frame
  // per seek(t). Bones + ARKit/Oculus morph targets, no render loop.
  function babylonCharacter(canvas, opts) {
    if (window.BabylonCharacter && typeof window.BabylonCharacter.create === 'function') {
      return window.BabylonCharacter.create(canvas, opts)
    }
    return { ready: Promise.resolve(null), seek() {}, applyPreset() {}, resize() {} }
  }

  // Rive-backed character: the hand-built .riv rig is driven by view-model
  // numbers from seek(t). Falls back to a no-op if the Rive bundle is absent.
  function riveCharacter(canvas, opts) {
    if (window.RiveCharacter && typeof window.RiveCharacter.create === 'function') {
      return window.RiveCharacter.create(canvas, opts)
    }
    return { ready: Promise.resolve(null), seek() {}, setPreset() {}, setVisemes() {} }
  }

  window.SceneKit = { cues, mechanism, parallax, camera, compose, views: applyViews, scatter, mulberry32, visemeAt, visemeBlend, lipsync, characterRig, portraitRig, riveCharacter, riveActor, babylonCharacter, particles, idle, grain, shadow, visemePaths: VISEME_SHAPES, mouthLayer, rive }
})()
