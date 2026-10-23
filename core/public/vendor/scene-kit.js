/* SceneKit — маленький детерминированный helper для 2D-сцен.
 *
 * Идея: сцена — это чистые HTML/CSS/JS. SceneKit даёт три вещи:
 *   cues(list)         — ключи на локальном таймлайне (stateAt / integrate)
 *   mechanism(spec)    — механизм с фазой (колёса, качание, пар)
 *   parallax(layers)   — параллакс фоновых слоёв
 *
 * Ничего не запускает само: всё считается от seek(t).
 */
(function () {
  function cues(list) {
    const points = (Array.isArray(list) ? list : [])
      .filter((c) => c && Number.isFinite(Number(c.at)))
      .map((c) => ({ ...c, at: Number(c.at) }))
      .sort((a, b) => a.at - b.at)

    function stateAt(t) {
      const out = {}
      for (const c of points) {
        if (c.at > t) break
        if (c.set) Object.assign(out, c.set)
      }
      return out
    }

    // Интеграл значения ключа по времени. Нужен, чтобы скорость можно было
    // менять ключами без скачков фазы (колесо не «прыгает»).
    function integrate(key, t, fallback = 0) {
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

    return { points, stateAt, integrate }
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

  function lipsync(opts) {
    const list = (opts && opts.visemes) || []
    return {
      seek(t) {
        const v = visemeAt(list, t)
        if (opts && typeof opts.onViseme === 'function') opts.onViseme(v, t)
      },
    }
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

  window.SceneKit = { cues, mechanism, parallax, camera, compose, views: applyViews, scatter, mulberry32, visemeAt, lipsync }
})()
