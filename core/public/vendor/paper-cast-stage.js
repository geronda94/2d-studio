/* PaperCastStage — config-driven paper-cut scenes.
 *
 * One canvas, a paper environment, N characters and a timing config:
 *
 *   const stage = PaperCastStage.create(canvas, {
 *     duration: 12000,
 *     environment: { preset: 'room', props: { plant: true } },
 *     cast: [
 *       { id: 'mark', character: 'mark', x: .32, y: .94, facing: 1 },
 *       { id: 'mira', character: 'mira', x: .68, y: .94, facing: -1 },
 *     ],
 *     timeline: [
 *       { at: 0,    type: 'pose',   who: 'mark', pose: 'explain' },
 *       { at: 1200, type: 'clip',   who: 'mark', clip: 'wave' },
 *       { at: 2000, type: 'speak',  who: 'mira', text: 'Привет!', dur: 2600 },
 *       { at: 3000, type: 'emotion',who: 'mark', emotion: 'joy' },
 *       { at: 5000, type: 'turn',   who: 'mark', yaw: .5 },
 *     ],
 *     captions: [{ at: 2000, text: 'Привет!', dur: 2600 }],
 *   })
 *   stage.seek(t)
 *
 * Everything is a pure function of t: no clocks, no random without a seed.
 */
(function () {
  'use strict'

  const TAU = Math.PI * 2
  const INK = '#20232d'

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0
      let t = Math.imul(a ^ (a >>> 15), 1 | a)
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
  }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v }
  function rr(ctx, x, y, w, h, r) {
    const k = Math.min(r, w / 2, h / 2)
    ctx.beginPath()
    ctx.moveTo(x + k, y)
    ctx.arcTo(x + w, y, x + w, y + h, k)
    ctx.arcTo(x + w, y + h, x, y + h, k)
    ctx.arcTo(x, y + h, x, y, k)
    ctx.arcTo(x, y, x + w, y, k)
    ctx.closePath()
  }
  function fillStroke(ctx, fill, stroke, lw) {
    if (fill) { ctx.fillStyle = fill; ctx.fill() }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 3; ctx.stroke() }
  }

  // ── environments ────────────────────────────────────────────────────────
  function grain(ctx, W, H, seed) {
    const rnd = mulberry32(seed || 7)
    ctx.save()
    ctx.globalAlpha = 0.05
    for (let i = 0; i < 260; i++) {
      ctx.fillStyle = i % 2 ? '#20232d' : '#ffffff'
      const x = rnd() * W, y = rnd() * H, r = 0.6 + rnd() * 1.8
      ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill()
    }
    ctx.restore()
  }
  function vignette(ctx, W, H) {
    const g = ctx.createRadialGradient(W / 2, H * 0.46, H * 0.3, W / 2, H * 0.5, W * 0.72)
    g.addColorStop(0, 'rgba(0,0,0,0)')
    g.addColorStop(1, 'rgba(12,10,8,.28)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, W, H)
  }

  const ROOM_STYLES = {
    home: {
      wall: '#e9dfcc', floor: '#c8b394', trim: '#b49b7c', accent: '#d86a3d', lamp: '#d8b46f',
      furniture: ['sofa', 'table', 'plant', 'frames', 'lamp', 'rug'],
    },
    office: {
      wall: '#dfe4e6', floor: '#b9bfc4', trim: '#9aa3a8', accent: '#2e7a78', lamp: '#cfd8d4',
      furniture: ['desk', 'shelf', 'plant', 'lamp', 'frames'],
    },
    cafe: {
      wall: '#d9c3ad', floor: '#8d6b57', trim: '#6f5243', accent: '#cf7a3a', lamp: '#f0c47a',
      furniture: ['table', 'chairs', 'shelf', 'lamp', 'menu'],
    },
    loft: {
      wall: '#cbb9a4', floor: '#a98b6f', trim: '#8a6f58', accent: '#486f5b', lamp: '#d8b46f',
      furniture: ['sofa', 'shelf', 'plant', 'rug', 'frames'],
    },
  }

  function drawTable(ctx, x, baseY, w, h, color) {
    ctx.fillStyle = color
    rr(ctx, x - w / 2, baseY - h, w, 12, 5); ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(x - w / 2 + 10, baseY - h + 12); ctx.lineTo(x - w / 2 + 14, baseY)
    ctx.moveTo(x + w / 2 - 10, baseY - h + 12); ctx.lineTo(x + w / 2 - 14, baseY)
    ctx.stroke()
  }

  function drawSofa(ctx, x, baseY, w, color, light) {
    ctx.fillStyle = color
    rr(ctx, x - w / 2, baseY - 120, w, 88, 16); ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke()
    ctx.fillStyle = light
    rr(ctx, x - w / 2 + 12, baseY - 158, w - 24, 54, 14); ctx.fill(); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(x, baseY - 158); ctx.lineTo(x, baseY - 108)
    ctx.strokeStyle = 'rgba(0,0,0,.2)'; ctx.lineWidth = 3; ctx.stroke()
  }

  function drawShelf(ctx, x, baseY, h, color) {
    ctx.fillStyle = color
    rr(ctx, x - 42, baseY - h, 84, h, 4); ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke()
    const rnd = mulberry32(Number(x) | 0)
    for (let row = 0; row < 3; row++) {
      const y = baseY - h + 12 + row * (h / 3.2)
      ctx.beginPath(); ctx.moveTo(x - 38, y + 26); ctx.lineTo(x + 38, y + 26)
      ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 2; ctx.stroke()
      for (let i = 0; i < 4; i++) {
        ctx.fillStyle = ['#cf7a3a', '#5f8a58', '#2e7a78', '#d8b46f'][(row + i) % 4]
        ctx.fillRect(x - 32 + i * 16, y + 4, 10, 20)
      }
    }
  }

  function drawDesk(ctx, x, baseY, w, color) {
    drawTable(ctx, x, baseY, w, 60, color)
    // monitor
    ctx.fillStyle = '#20232d'
    rr(ctx, x - 42, baseY - 168, 84, 54, 4); ctx.fill()
    ctx.fillStyle = '#8fd0c8'
    rr(ctx, x - 36, baseY - 162, 72, 42, 3); ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 3
    ctx.beginPath(); ctx.moveTo(x, baseY - 114); ctx.lineTo(x, baseY - 92)
    ctx.moveTo(x - 20, baseY - 92); ctx.lineTo(x + 20, baseY - 92); ctx.stroke()
  }

  function drawRug(ctx, x, baseY, w, color) {
    ctx.fillStyle = color
    ctx.beginPath(); ctx.ellipse(x, baseY + 10, w / 2, 26, 0, 0, TAU); ctx.fill()
    ctx.strokeStyle = 'rgba(0,0,0,.18)'; ctx.lineWidth = 2; ctx.stroke()
  }

  function drawDoor(ctx, x, baseY, h, color) {
    ctx.fillStyle = color
    rr(ctx, x - 52, baseY - h, 104, h, 4); ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke()
    ctx.beginPath(); ctx.arc(x + 34, baseY - h / 2, 5, 0, TAU)
    ctx.fillStyle = '#d8b46f'; ctx.fill(); ctx.stroke()
  }

  function drawMenu(ctx, x, y) {
    ctx.fillStyle = '#2f2a26'
    rr(ctx, x - 90, y, 180, 112, 6); ctx.fill()
    ctx.strokeStyle = '#d8b46f'; ctx.lineWidth = 3; ctx.stroke()
    ctx.fillStyle = '#e8d9bf'
    ctx.font = '600 14px ui-sans-serif, sans-serif'
    ctx.fillText('MENU', x - 26, y + 28)
    ctx.fillStyle = 'rgba(232,217,191,.55)'
    for (let i = 0; i < 3; i++) ctx.fillRect(x - 64, y + 46 + i * 18, 128, 4)
  }

  function drawChairs(ctx, x, baseY) {
    for (const s of [-1, 1]) {
      const cx = x + s * 78
      ctx.fillStyle = '#8a5a3a'
      rr(ctx, cx - 26, baseY - 76, 52, 10, 4); ctx.fill()
      ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(cx - 18, baseY - 66); ctx.lineTo(cx - 20, baseY)
      ctx.moveTo(cx + 18, baseY - 66); ctx.lineTo(cx + 20, baseY)
      ctx.moveTo(cx - 18, baseY - 70); ctx.lineTo(cx - 22, baseY - 130)
      ctx.moveTo(cx + 18, baseY - 70); ctx.lineTo(cx + 22, baseY - 130)
      ctx.stroke()
    }
  }

  function envRoom(ctx, W, H, env, t) {
    const styleName = env.style || 'home'
    const st = ROOM_STYLES[styleName] || ROOM_STYLES.home
    const p = Object.assign({}, st, env.palette || {})
    const pr = env.props || {}
    const line = H * (pr.horizon !== undefined ? pr.horizon : 0.64)
    ctx.fillStyle = p.wall; ctx.fillRect(0, 0, W, line)
    ctx.fillStyle = p.floor; ctx.fillRect(0, line, W, H - line)
    ctx.fillStyle = p.trim; ctx.fillRect(0, line - 14, W, 14)
    ctx.strokeStyle = 'rgba(32,35,45,.25)'; ctx.lineWidth = 2
    ctx.beginPath(); ctx.moveTo(0, line); ctx.lineTo(W, line); ctx.stroke()
    ctx.strokeStyle = 'rgba(32,35,45,.12)'
    for (let i = 0; i < 8; i++) {
      const x = (i / 8) * W + 40
      ctx.beginPath(); ctx.moveTo(x, line); ctx.lineTo(x + 120, H); ctx.stroke()
    }

    const winCount = pr.windows !== undefined ? Math.max(0, Math.min(3, pr.windows)) : (styleName === 'office' || styleName === 'loft' ? 2 : 1)
    const winW = W * 0.22, winH = H * 0.34
    const span = winCount > 1 ? 0.62 : 0
    for (let i = 0; i < winCount; i++) {
      const wx = winCount === 1 ? W * 0.42 : W * (0.22 + (i * span) / Math.max(1, winCount - 1))
      const wy = H * 0.15
      ctx.fillStyle = p.trim; ctx.fillRect(wx - 14, wy - 14, winW + 28, winH + 28)
      const g = ctx.createLinearGradient(0, wy, 0, wy + winH)
      g.addColorStop(0, p.sky || '#bed9e6'); g.addColorStop(1, '#e7f0f2')
      ctx.fillStyle = g; ctx.fillRect(wx, wy, winW, winH)
      ctx.fillStyle = 'rgba(255,255,255,.75)'
      ctx.beginPath()
      ctx.ellipse(wx + winW * 0.32, wy + winH * 0.28, 40, 14, 0, 0, TAU)
      ctx.ellipse(wx + winW * 0.5, wy + winH * 0.26, 26, 10, 0, 0, TAU)
      ctx.fill()
      ctx.fillStyle = p.trim; ctx.fillRect(wx - 22, wy + winH + 14, winW + 44, 14)
      ctx.strokeStyle = p.trim; ctx.lineWidth = 8
      ctx.beginPath(); ctx.moveTo(wx + winW / 2, wy); ctx.lineTo(wx + winW / 2, wy + winH)
      ctx.moveTo(wx, wy + winH * 0.52); ctx.lineTo(wx + winW, wy + winH * 0.52); ctx.stroke()
      if (i === 0 && styleName !== 'office') {
        const sway = Math.sin(t / 1400) * 6
        ctx.fillStyle = p.accent; ctx.globalAlpha = 0.8
        ctx.beginPath()
        ctx.moveTo(wx - 54, wy - 18)
        ctx.quadraticCurveTo(wx - 66 + sway, wy + winH * 0.5, wx - 46 + sway, wy + winH + 24)
        ctx.lineTo(wx - 8, wy + winH + 24)
        ctx.quadraticCurveTo(wx - 26 + sway, wy + winH * 0.5, wx - 20, wy - 18)
        ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1
      }
    }

    const POS = { sofa: 0.16, table: 0.5, desk: 0.52, shelf: 0.86, plant: 0.93, rug: 0.42, door: 0.72, chairs: 0.5, menu: 0.3, lamp: 0.3, frames: 0.2 }
    const raw = pr.furniture || st.furniture || []
    const items = raw.map((it) => {
      if (typeof it === 'string') return { type: it, x: POS[it] !== undefined ? POS[it] : 0.5, scale: 1 }
      return { type: it.type, x: it.x !== undefined ? it.x : (POS[it.type] || 0.5), scale: it.scale || 1 }
    })
    if (pr.rug !== false && !items.some((i) => i.type === 'rug')) items.push({ type: 'rug', x: POS.rug, scale: 1 })
    if (pr.door) items.push({ type: 'door', x: POS.door, scale: 1 })

    // floor layer first
    for (const it of items) if (it.type === 'rug') drawRug(ctx, it.x * W, line, W * 0.34 * it.scale, 'rgba(120,86,64,.32)')
    for (const it of items) if (it.type === 'door') drawDoor(ctx, it.x * W, line, H * 0.42, p.trim)
    // back furniture
    for (const it of items) {
      if (it.type === 'shelf') drawShelf(ctx, it.x * W, line, H * 0.3 * it.scale, p.trim)
      if (it.type === 'desk') drawDesk(ctx, it.x * W, line - 2, W * 0.2 * it.scale, p.sofa || '#8d6b57')
    }
    for (const it of items) {
      if (it.type === 'table') drawTable(ctx, it.x * W, line - 2, W * 0.2 * it.scale, 66, p.sofa || '#8d6b57')
      if (it.type === 'chairs') drawChairs(ctx, it.x * W, line)
      if (it.type === 'sofa') drawSofa(ctx, it.x * W, line - 4, W * 0.22 * it.scale, p.sofa || '#8d6b57', p.sofaLight || '#a7836b')
      if (it.type === 'plant') drawPlant(ctx, it.x * W, line - 6, t, p.plant || '#5c8a5a')
      if (it.type === 'menu') drawMenu(ctx, it.x * W, H * 0.18)
      if (it.type === 'lamp') {
        const lx = it.x * W, ly = H * 0.06
        ctx.strokeStyle = INK; ctx.lineWidth = 3
        ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, ly + 30); ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(lx - 44, ly + 64)
        ctx.quadraticCurveTo(lx, ly + 14, lx + 44, ly + 64)
        ctx.closePath(); fillStroke(ctx, p.lamp || '#d8b46f', INK, 3)
        const glow = ctx.createRadialGradient(lx, ly + 90, 10, lx, ly + 90, 220)
        glow.addColorStop(0, 'rgba(255,220,150,.22)')
        glow.addColorStop(1, 'rgba(255,220,150,0)')
        ctx.fillStyle = glow; ctx.fillRect(lx - 260, ly, 520, 420)
      }
      if (it.type === 'frames') {
        const count = pr.frames !== undefined ? Math.max(0, Math.min(3, pr.frames)) : 2
        for (let i = 0; i < count; i++) {
          const fx = W * (0.12 + i * 0.13), fy = H * (0.2 + (i % 2) * 0.05)
          ctx.fillStyle = '#f7efe0'; ctx.strokeStyle = INK; ctx.lineWidth = 4
          rr(ctx, fx, fy, W * 0.09, H * 0.16, 4); ctx.fill(); ctx.stroke()
          ctx.strokeStyle = 'rgba(32,35,45,.25)'; ctx.lineWidth = 2
          ctx.beginPath(); ctx.moveTo(fx + 12, fy + 40); ctx.lineTo(fx + W * 0.09 - 12, fy + 40); ctx.stroke()
        }
      }
    }
    const rnd = mulberry32(11)
    ctx.fillStyle = 'rgba(255,255,255,.5)'
    for (let i = 0; i < 30; i++) {
      const x = rnd() * W
      const y = ((rnd() * H + t * (0.006 + rnd() * 0.01)) % H)
      ctx.globalAlpha = 0.1 + rnd() * 0.16
      ctx.beginPath(); ctx.arc(x, y, 1 + rnd() * 1.8, 0, TAU); ctx.fill()
    }
    ctx.globalAlpha = 1
    grain(ctx, W, H, 5)
    vignette(ctx, W, H)
  }

  function drawPlant(ctx, x, baseY, t, color) {
    const sway = Math.sin(t / 900) * 0.05
    ctx.save()
    ctx.translate(x, baseY)
    // pot
    ctx.beginPath()
    ctx.moveTo(-38, 0); ctx.lineTo(38, 0); ctx.lineTo(28, 60); ctx.lineTo(-28, 60)
    ctx.closePath(); fillStroke(ctx, '#c9794f', INK, 3)
    ctx.rotate(sway)
    for (let i = -2; i <= 2; i++) {
      const a = i * 0.32
      ctx.save(); ctx.rotate(a)
      ctx.beginPath()
      ctx.moveTo(0, 0)
      ctx.quadraticCurveTo(-26, -60, 0, -128)
      ctx.quadraticCurveTo(26, -60, 0, 0)
      ctx.closePath(); fillStroke(ctx, color, INK, 2.6)
      ctx.restore()
    }
    ctx.restore()
  }

  function envStreet(ctx, W, H, env, t) {
    const p = env.palette || {}
    const skyTop = p.skyTop || '#1d2a44'
    const skyBot = p.skyBottom || '#c96f5a'
    const road = p.road || '#2b2f38'
    const g = ctx.createLinearGradient(0, 0, 0, H * 0.7)
    g.addColorStop(0, skyTop); g.addColorStop(1, skyBot)
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H * 0.68)
    // moon
    ctx.fillStyle = 'rgba(247,236,205,.9)'
    ctx.beginPath(); ctx.arc(W * 0.78, H * 0.18, 42, 0, TAU); ctx.fill()
    // buildings
    const rnd = mulberry32(23)
    for (let layer = 0; layer < 2; layer++) {
      const dark = layer === 0 ? 'rgba(26,30,44,.55)' : 'rgba(18,21,32,.9)'
      ctx.fillStyle = dark
      let x = -60
      while (x < W + 60) {
        const bw = 120 + rnd() * 140
        const bh = H * (0.18 + rnd() * 0.3) * (layer === 0 ? 0.8 : 1)
        const by = H * 0.68 - bh
        ctx.fillRect(x, by, bw, bh)
        // windows
        ctx.fillStyle = 'rgba(255,214,140,.55)'
        for (let wy = by + 26; wy < H * 0.66 - 20; wy += 34) {
          for (let wx = x + 16; wx < x + bw - 20; wx += 30) {
            if (rnd() > 0.45) ctx.fillRect(wx, wy, 12, 16)
          }
        }
        ctx.fillStyle = dark
        x += bw + 14
      }
    }
    // road + sidewalk
    ctx.fillStyle = road; ctx.fillRect(0, H * 0.68, W, H * 0.32)
    ctx.fillStyle = p.sidewalk || '#4a4f5a'; ctx.fillRect(0, H * 0.68, W, H * 0.04)
    // lamps
    for (let i = 0; i < 3; i++) {
      const lx = W * (0.18 + i * 0.32)
      ctx.strokeStyle = INK; ctx.lineWidth = 4
      ctx.beginPath(); ctx.moveTo(lx, H * 0.68); ctx.lineTo(lx, H * 0.38); ctx.stroke()
      ctx.beginPath(); ctx.arc(lx, H * 0.38, 7, 0, TAU); ctx.fillStyle = 'rgba(255,220,150,.9)'; ctx.fill()
      const glow = ctx.createRadialGradient(lx, H * 0.4, 6, lx, H * 0.4, 120)
      glow.addColorStop(0, 'rgba(255,210,130,.22)')
      glow.addColorStop(1, 'rgba(255,210,130,0)')
      ctx.fillStyle = glow; ctx.fillRect(lx - 130, H * 0.3, 260, 220)
    }
    // rain
    ctx.strokeStyle = 'rgba(210,225,240,.25)'; ctx.lineWidth = 2
    const rnd2 = mulberry32(41)
    for (let i = 0; i < 90; i++) {
      const x = (rnd2() * W + t * 0.2) % W
      const y = (rnd2() * H + t * 0.6) % H
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 4, y + 18); ctx.stroke()
    }
    grain(ctx, W, H, 9)
    vignette(ctx, W, H)
  }

  function envStudio(ctx, W, H, env, t) {
    const p = env.palette || {}
    ctx.fillStyle = p.bg || '#11151d'; ctx.fillRect(0, 0, W, H)
    // floor
    ctx.fillStyle = p.floor || '#1b202b'
    ctx.beginPath(); ctx.ellipse(W / 2, H * 0.86, W * 0.62, H * 0.16, 0, 0, TAU); ctx.fill()
    // spotlights
    for (let i = 0; i < 3; i++) {
      const x = W * (0.28 + i * 0.22)
      const g = ctx.createLinearGradient(x, 0, x + 80, H * 0.8)
      g.addColorStop(0, 'rgba(255,225,170,.16)')
      g.addColorStop(1, 'rgba(255,225,170,0)')
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.moveTo(x - 30, 0); ctx.lineTo(x + 30, 0)
      ctx.lineTo(x + 210, H * 0.86); ctx.lineTo(x - 210, H * 0.86)
      ctx.closePath(); ctx.fill()
    }
    // dust
    const rnd = mulberry32(13)
    ctx.fillStyle = 'rgba(255,240,210,.6)'
    for (let i = 0; i < 60; i++) {
      const x = rnd() * W
      const y = (rnd() * H + Math.sin(t / 1800 + i) * 20) % H
      ctx.globalAlpha = 0.08 + rnd() * 0.16
      ctx.beginPath(); ctx.arc(x, y, 1 + rnd() * 2, 0, TAU); ctx.fill()
    }
    ctx.globalAlpha = 1
    grain(ctx, W, H, 3)
    vignette(ctx, W, H)
  }

  function envPark(ctx, W, H, env, t) {
    const p = env.palette || {}
    const g = ctx.createLinearGradient(0, 0, 0, H * 0.7)
    g.addColorStop(0, p.skyTop || '#bcd9e8'); g.addColorStop(1, p.skyBottom || '#f2e6d0')
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H * 0.72)
    // hills
    ctx.fillStyle = p.hill || '#9fb28a'
    ctx.beginPath(); ctx.ellipse(W * 0.25, H * 0.7, W * 0.4, H * 0.2, 0, Math.PI, TAU); ctx.fill()
    ctx.fillStyle = p.hill2 || '#7f9870'
    ctx.beginPath(); ctx.ellipse(W * 0.75, H * 0.72, W * 0.45, H * 0.22, 0, Math.PI, TAU); ctx.fill()
    // ground
    ctx.fillStyle = p.ground || '#c8b394'; ctx.fillRect(0, H * 0.7, W, H * 0.3)
    // trees
    const rnd = mulberry32(31)
    for (let i = 0; i < 5; i++) {
      const x = W * (0.08 + i * 0.21), y = H * 0.7
      const s = 0.7 + rnd() * 0.5
      ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
      ctx.fillStyle = '#6b4a33'; ctx.fillRect(-8, -70, 16, 70)
      ctx.fillStyle = p.leaf || '#5f8a58'
      ctx.beginPath(); ctx.arc(0, -96, 58, 0, TAU); ctx.arc(-36, -70, 40, 0, TAU); ctx.arc(40, -72, 42, 0, TAU); ctx.fill()
      ctx.restore()
    }
    // bench
    ctx.fillStyle = '#8a5a3a'; ctx.fillRect(W * 0.44, H * 0.72, 150, 14)
    ctx.fillRect(W * 0.45, H * 0.74, 10, 46); ctx.fillRect(W * 0.56, H * 0.74, 10, 46)
    grain(ctx, W, H, 17)
    vignette(ctx, W, H)
  }

  const ENVIRONMENTS = { room: envRoom, street: envStreet, studio: envStudio, park: envPark }

  // ── stage ───────────────────────────────────────────────────────────────
  function create(canvas, config) {
    const cfg = Object.assign({
      width: 1600, height: 900, duration: 10000, background: '#efe4d1',
      autoInteract: true, seed: 1,
      environment: { preset: 'room' }, cast: [], timeline: [], captions: [],
      title: '',
    }, config || {})
    cfg.environment = Object.assign({ preset: 'room', palette: {}, props: {} }, cfg.environment || {})
    const roomStyles = ['home', 'office', 'cafe', 'loft']
    if (roomStyles.indexOf(cfg.environment.preset) >= 0) {
      cfg.environment.style = cfg.environment.preset
      cfg.environment.preset = 'room'
    }
    cfg.cast = (cfg.cast || []).map((c, i) => Object.assign({
      id: 'c' + i, character: 'mark', x: 0.5, y: 0.94, scale: 1,
      facing: 1, pose: 'neutral', appearance: {}, emotion: 'neutral', yaw: 0,
    }, c))
    cfg.timeline = (cfg.timeline || []).slice().sort((a, b) => (a.at || 0) - (b.at || 0))
    cfg.captions = (cfg.captions || []).slice().sort((a, b) => (a.at || 0) - (b.at || 0))
    cfg.camera = Object.assign({ zoom: 1, x: 0, y: 0, follow: null }, cfg.camera || {})

    const W = cfg.width, H = cfg.height
    const ctx = canvas.getContext('2d')
    const duration = cfg.duration || Math.max(1000, ...cfg.timeline.map((e) => (e.at || 0) + 1200), ...cfg.captions.map((e) => (e.at || 0) + (e.dur || 2000)))

    // hidden hosts for character canvases
    const host = document.createElement('div')
    host.style.cssText = 'position:fixed;left:-12000px;top:0;width:600px;height:900px;overflow:hidden;pointer-events:none'
    document.body.appendChild(host)

    const actors = cfg.cast.map((c) => {
      const cv = document.createElement('canvas')
      cv.width = 600; cv.height = 900
      cv.style.cssText = 'width:600px;height:900px;display:block'
      host.appendChild(cv)
      const rig = window.PaperCast.create(cv, {
        character: c.character,
        appearance: c.appearance,
        pose: c.pose || 'neutral',
        yaw: c.yaw || 0,
        autoGaze: false,
        life: true,
      })
      return { cfg: c, canvas: cv, rig, applied: null }
    })

    function speakingAt(t) {
      let best = null
      for (const a of actors) {
        const evs = cfg.timeline.filter((e) => e.type === 'speak' && (e.who === a.cfg.id || e.who === 'all' || e.who === 'both') && e.at <= t)
        if (!evs.length) continue
        const e = evs[evs.length - 1]
        if (t < e.at + (e.dur || 2600) + 200) best = { id: a.cfg.id, char: a.cfg, at: e.at, dur: e.dur || 2600, text: e.text }
      }
      return best
    }

    function directiveAt(a, t) {
      const c = a.cfg
      const d = {
        pose: c.pose || 'neutral', clip: null, gesture: null, speak: null, fade: null,
        emotion: c.emotion || 'neutral', yaw: null, lookAt: null,
        visemes: null, blink: null,
      }
      const evs = cfg.timeline.filter((e) => e.who === c.id || e.who === 'all' || e.who === 'both')
      let prevPose = c.pose || 'neutral'
      for (const e of evs) {
        if ((e.at || 0) > t) break
        if (e.type === 'pose') {
          const fade = Number(e.fade) || 0
          if (fade && t < e.at + fade) d.fade = { from: prevPose, to: e.pose, at: e.at, dur: fade }
          else d.fade = null
          d.pose = e.pose
          d.clip = null
          prevPose = e.pose
        }
        else if (e.type === 'clip') { d.clip = { id: e.clip, at: e.at, obj: e.clipObj || null } }
        else if (e.type === 'gesture') { d.gesture = { pose: e.pose, at: e.at, dur: e.dur || 1200 } }
        else if (e.type === 'speak') { d.speak = { text: e.text, dur: e.dur || 2600, at: e.at } }
        else if (e.type === 'emotion') { d.emotion = e.emotion }
        else if (e.type === 'turn') { d.yaw = e.yaw }
        else if (e.type === 'lookAt') { d.lookAt = e.target }
        else if (e.type === 'visemes') { d.visemes = e.visemes }
        else if (e.type === 'blink') { d.blink = e.on }
      }
      if (d.clip) {
        const dur = (d.clip.obj && d.clip.obj.duration) || (window.PaperCast.CLIPS[d.clip.id] && window.PaperCast.CLIPS[d.clip.id].duration) || 1200
        if (t >= d.clip.at + dur) d.clip = null
      }
      if (d.gesture && t >= d.gesture.at + d.gesture.dur) d.gesture = null
      if (d.speak && t >= d.speak.at + d.speak.dur + 200) d.speak = null

      // auto interaction: turn and look at the one who speaks
      const other = cfg.cast.find((o) => o.id !== c.id)
      const speaker = speakingAt(t)
      if (cfg.autoInteract && other) {
        if (d.yaw === null) {
          if (speaker) d.yaw = Math.sign(other.x - c.x) * 0.3
          else d.yaw = (c.facing || 1) * 0.24
        }
        if (!d.lookAt) d.lookAt = speaker && speaker.id !== c.id ? other.id : (speaker && speaker.id === c.id ? other.id : null)
      }
      if (d.lookAt) {
        const target = cfg.cast.find((o) => o.id === d.lookAt)
        if (target) {
          const sx = c.x * W, sy = c.y * H - 620 * (c.scale || 1)
          const tx = target.x * W, ty = target.y * H - 620 * (target.scale || 1)
          d.gaze = [clamp((tx - sx) / 420, -1, 1), clamp((ty - sy) / 300, -1, 1)]
        }
      }
      if (cfg.autoInteract && speaker && speaker.id !== c.id && !d.gesture) {
        if (t >= speaker.at - 100 && t <= speaker.at + 320) d.gesture = { pose: 'nod', at: speaker.at, dur: 700 }
      }
      return d
    }

    function resolvePose(x) {
      return typeof x === 'string' ? (window.PaperCast.POSES[x] || window.PaperCast.POSES.neutral) : x
    }

    function apply(a, d, t) {
      const key = JSON.stringify(d)
      const changed = a.applied !== key
      if (changed) {
        if (d.clip) {
          if (d.clip.obj) a.rig.setClip(d.clip.obj, d.clip.at)
          else a.rig.setClip(d.clip.id, d.clip.at)
        } else if (!d.fade) {
          a.rig.setPose(d.pose)
          if (d.gesture) a.rig.playGesture(d.gesture.pose, d.gesture.at, d.gesture.dur)
          else a.rig.playGesture(null)
        }
        a.rig.setEmotion(d.emotion)
        if (d.speak) a.rig.speak(d.speak.text, d.speak.dur, d.speak.at)
        else a.rig.setVisemes([])
        if (d.visemes) a.rig.setVisemes(d.visemes)
        if (d.blink !== null) a.rig.setBlink(d.blink)
        a.rig.setYaw(d.yaw === null ? 0 : d.yaw)
        if (d.gaze) a.rig.setGaze(d.gaze[0], d.gaze[1])
        else a.rig.setGaze(0, 0)
        a.applied = key
      }
      if (d.fade && !d.clip) {
        const k = (t - d.fade.at) / d.fade.dur
        const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2
        const from = resolvePose(d.fade.from)
        const to = resolvePose(d.fade.to)
        a.rig.setPoseObject(window.PaperCast.blendPose(from, to, Math.max(0, Math.min(1, e))))
      }
      a.rig.seek(t)
    }

    function cameraAt(t, speaker) {
      const base = cfg.camera
      let cam = { zoom: base.zoom, x: base.x, y: base.y }
      let before = Object.assign({}, cam)
      const evs = cfg.timeline.filter((e) => e.type === 'camera')
      for (const e of evs) {
        if ((e.at || 0) > t) break
        before = Object.assign({}, cam)
        const target = {
          zoom: e.zoom !== undefined ? e.zoom : cam.zoom,
          x: e.x !== undefined ? e.x : cam.x,
          y: e.y !== undefined ? e.y : cam.y,
        }
        if (e.dur && t < e.at + e.dur) {
          const k = (t - e.at) / e.dur
          const e2 = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2
          cam = {
            zoom: before.zoom + (target.zoom - before.zoom) * e2,
            x: before.x + (target.x - before.x) * e2,
            y: before.y + (target.y - before.y) * e2,
          }
          break
        }
        cam = target
      }
      if (base.follow === 'speaker' && speaker && speaker.char) {
        cam.x += clamp((speaker.char.x - 0.5) * 0.35, -0.1, 0.1)
        cam.zoom = Math.max(cam.zoom, 1.04)
      }
      return cam
    }

    function drawEnvironment(t) {
      const preset = cfg.environment.preset || 'room'
      const fn = ENVIRONMENTS[preset] || ENVIRONMENTS.room
      ctx.fillStyle = cfg.background
      ctx.fillRect(0, 0, W, H)
      fn(ctx, W, H, cfg.environment, t)
    }

    function drawCaption(t) {
      let cap = null
      for (const c of cfg.captions) {
        if (c.at <= t && t < c.at + (c.dur || 2600)) cap = c
      }
      if (!cap) return
      const text = String(cap.text || '')
      if (!text) return
      ctx.save()
      ctx.font = '600 34px ui-sans-serif, system-ui, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const w = Math.min(W * 0.8, ctx.measureText(text).width + 56)
      const x = W / 2 - w / 2, y = H - 96
      ctx.fillStyle = 'rgba(248,242,230,.92)'
      ctx.strokeStyle = '#20232d'; ctx.lineWidth = 3
      rr(ctx, x, y, w, 56, 12); ctx.fill(); ctx.stroke()
      ctx.fillStyle = '#20232d'; ctx.fillText(text, W / 2, y + 29)
      ctx.restore()
    }

    function drawTitle() {
      if (!cfg.title) return
      ctx.save()
      ctx.font = '700 44px ui-sans-serif, system-ui, sans-serif'
      ctx.fillStyle = 'rgba(32,35,45,.9)'
      ctx.textAlign = 'left'; ctx.textBaseline = 'top'
      ctx.fillText(cfg.title, 56, 40)
      ctx.restore()
    }

    function draw(t) {
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      const cw = Math.max(1, Math.round((rect.width || canvas.width) * dpr))
      const ch = Math.max(1, Math.round((rect.height || canvas.height) * dpr))
      if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch }
      const s = Math.min(cw / W, ch / H)
      const ox = (cw - W * s) / 2, oy = (ch - H * s) / 2
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, cw, ch)
      ctx.setTransform(s, 0, 0, s, ox, oy)
      ctx.lineJoin = 'round'; ctx.lineCap = 'round'
      const speaker = speakingAt(t)
      const cam = cameraAt(t, speaker)
      ctx.save()
      const cx = W / 2 + cam.x * W, cy = H / 2 + cam.y * H
      ctx.translate(cx, cy); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cx, -cy)
      drawEnvironment(t)
      for (const a of actors) apply(a, directiveAt(a, t), t)
      const sorted = actors.slice().sort((a, b) => a.cfg.y - b.cfg.y || a.cfg.x - b.cfg.x)
      for (const a of sorted) {
        const c = a.cfg
        const px = c.x * W, py = c.y * H
        const sc = c.scale || 1
        const flip = c.flip !== undefined ? !!c.flip : (c.facing || 1) < 0
        // Render the actor at the size it actually occupies on screen: a
        // 600×900 canvas blitted down to 300 px was the single biggest cost
        // of a two-actor frame (77 % of the seek time was drawImage).
        const needW = Math.max(220, Math.min(900, Math.round(600 * sc * s)))
        const needH = Math.round(needW * 1.5)
        if (a.rig.setSize) a.rig.setSize(needW, needH)
        ctx.save()
        ctx.translate(px, py)
        if (flip) ctx.scale(-1, 1)
        ctx.scale((sc * 600) / needW, (sc * 900) / needH)
        ctx.drawImage(a.canvas, -needW / 2, -needH)
        ctx.restore()
      }
      ctx.restore()
      drawCaption(t)
      drawTitle()
    }

    function seek(t) {
      draw(Math.max(0, Math.min(duration, Number(t) || 0)))
    }

    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => seek(stateTime)) : null
    let stateTime = 0
    if (ro) ro.observe(canvas)
    seek(0)

    return {
      ready: Promise.resolve(true),
      seek(t) { stateTime = Math.max(0, Math.min(duration, Number(t) || 0)); draw(stateTime) },
      duration,
      getState: () => ({ time: stateTime, actors: cfg.cast.map((c) => c.id), duration }),
      destroy() {
        if (ro) ro.disconnect()
        for (const a of actors) { try { a.rig.destroy() } catch (e) {} }
        host.remove()
        ctx.setTransform(1, 0, 0, 1, 0, 0)
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      },
    }
  }

  function fromTranscript(segments, opts) {
    const o = opts || {}
    const list = Array.isArray(segments) ? segments : []
    const nums = list.map((s) => Number(s.start) || 0).concat(list.map((s) => Number(s.end) || 0))
    const seconds = o.unit === 's' || (nums.length && Math.max.apply(null, nums) < 120)
    const mul = seconds ? 1000 : 1
    const timeline = []
    const captions = []
    let end = 0
    for (const s of list) {
      const start = Math.max(0, (Number(s.start) || 0) * mul)
      const text = String(s.text || '')
      const stop = Number(s.end) ? Number(s.end) * mul : start + Math.max(900, text.length * 55)
      const dur = Math.max(400, stop - start)
      const who = s.speaker || s.who || o.speaker || 'mark'
      timeline.push({ at: Math.round(start), type: 'speak', who, text, dur: Math.round(dur) })
      captions.push({ at: Math.round(start), text, dur: Math.round(dur) })
      if (s.pose) timeline.push({ at: Math.round(start), type: 'pose', who, pose: s.pose })
      if (s.emotion) timeline.push({ at: Math.round(start), type: 'emotion', who, emotion: s.emotion })
      if (s.gesture) timeline.push({ at: Math.round(start + 200), type: 'gesture', who, pose: s.gesture, dur: 900 })
      end = Math.max(end, stop)
    }
    return {
      duration: Math.round(end + (o.tail !== undefined ? o.tail : 700)),
      timeline,
      captions,
    }
  }

  function srtTime(str) {
    const m = String(str || '').match(/(\d+):(\d+):(\d+)[,.](\d+)/)
    if (!m) return 0
    return ((Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3])) * 1000) + Number(m[4])
  }

  function fromSRT(srt, opts) {
    const o = opts || {}
    const blocks = String(srt || '').replace(/\r/g, '').split(/\n{2,}/)
    const segments = []
    for (const block of blocks) {
      const lines = block.split('\n').filter((l) => l.trim() !== '')
      if (!lines.length) continue
      const i = lines.findIndex((l) => l.indexOf('-->') >= 0)
      if (i < 0) continue
      const parts = lines[i].split('-->')
      const start = srtTime(parts[0])
      const end = srtTime(parts[1])
      let text = lines.slice(i + 1).join(' ').replace(/<[^>]+>/g, '').trim()
      if (!text) continue
      let speaker = o.speaker
      const tag = text.match(/^\[([^\]]+)\]\s*/) || text.match(/^([\wа-яА-ЯёЁ-]{2,18})\s*:\s*/)
      if (tag) {
        speaker = String(tag[1]).toLowerCase()
        text = text.slice(tag[0].length)
      }
      segments.push({ start, end, text, speaker })
    }
    const speakers = o.speakers || ['mark', 'mira']
    let k = 0
    for (const seg of segments) if (!seg.speaker) seg.speaker = speakers[k++ % speakers.length]
    return fromTranscript(segments, o)
  }

  window.PaperCastStage = {
    create,
    fromTranscript,
    fromSRT,
    ENVIRONMENTS: Object.keys(ENVIRONMENTS),
    STYLES: Object.keys(ROOM_STYLES),
    INK,
  }
})()
