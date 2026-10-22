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

  window.SceneKit = { cues, mechanism, parallax, compose, views: applyViews }
})()
