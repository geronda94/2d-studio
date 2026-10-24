/* CharacterRig — риг персонажа на canvas.
 *
 * Полностью детерминированный: кадр — чистая функция от t.
 * Настоящий скелет: таз, шея, голова, плечо/локоть/запястье, бедро/колено/лопасть.
 * Всё рисуется градиентами и мягкими тенями — не плоские заливки.
 *
 * window.CharacterRig.create(canvas, opts) -> { seek(t) }
 */
(function () {
  const TAU = Math.PI * 2

  const PALETTE = {
    skin: '#F2CBA4',
    skinLight: '#FBE0C4',
    skinDark: '#C68C60',
    hair: '#3B2C24',
    hairLight: '#6B4C3C',
    shirt: '#2F6FB3',
    shirtLight: '#5E9BD8',
    shirtDark: '#1E4A7C',
    pants: '#2A3444',
    pantsLight: '#3D4A5E',
    shoe: '#1B2230',
    shoeLight: '#39465C',
    line: '#161E2A',
    mouth: '#3A1A1C',
    tongue: '#C7606A',
    teeth: '#F4F7FA',
    iris: '#4A7FB5',
    irisDark: '#1E3E63',
    lip: '#C2726B',
  }

  // ── форма рта: [ширина, высота, зубы, язык, уголок] ──────────────────────
  const MOUTHS = [
    { w: 1.00, h: 0.05, teeth: 0, tongue: 0, corner: 0.55 },  // 0 neutral
    { w: 1.05, h: 0.80, teeth: 1, tongue: 0, corner: 0.10 },  // 1 AEI
    { w: 0.48, h: 0.06, teeth: 0, tongue: 0, corner: 0.20 },  // 2 BMP
    { w: 0.92, h: 0.24, teeth: 0, tongue: 0, corner: 0.35 },  // 3 FV
    { w: 0.98, h: 0.48, teeth: 0, tongue: 0, corner: 0.25 },  // 4 CDGKNRST
    { w: 0.48, h: 0.32, teeth: 0, tongue: 0, corner: 0.15 },  // 5 U
    { w: 0.64, h: 0.40, teeth: 0, tongue: 0, corner: 0.20 },  // 6 ChJSh
    { w: 0.72, h: 0.62, teeth: 0, tongue: 1, corner: 0.20 },  // 7 L
    { w: 0.56, h: 0.58, teeth: 0, tongue: 0, corner: 0.12 },  // 8 O
    { w: 0.42, h: 0.24, teeth: 0, tongue: 0, corner: 0.18 },  // 9 QW
  ]

  function create(canvas, opts) {
    const o = opts || {}
    const ctx = canvas.getContext('2d')
    const C = Object.assign({}, PALETTE, o.palette || {})
    const VW = 600 // виртуальная ширина
    const VH = Math.round(VW * (canvas.height / canvas.width))
    const K = canvas.width / VW // масштаб виртуальных единиц в пиксели

    // ── скелет ───────────────────────────────────────────────────────────
    const B = {
      hips: { x: 300, y: 520 },
      neck: { x: 300, y: 236 },
      head: { x: 300, y: 138 },
      shL: { x: 190, y: 316 }, elL: { x: 176, y: 450 }, wrL: { x: 174, y: 576 },
      shR: { x: 410, y: 316 }, elR: { x: 424, y: 450 }, wrR: { x: 426, y: 576 },
      hipL: { x: 262, y: 520 }, knL: { x: 254, y: 692 }, anL: { x: 250, y: 848 },
      hipR: { x: 338, y: 520 }, knR: { x: 346, y: 692 }, anR: { x: 350, y: 848 },
    }
    const S = { headTilt: 0, headBob: 0, armL: 0, armR: 0, foreL: 0, foreR: 0, legL: 0, legR: 0, kneeL: 0, kneeR: 0, blink: 0, gx: 0, gy: 0, brow: 0, browTilt: 0, mouth: 0, mouthK: 0, open: 0 }

    // ── утилиты ──────────────────────────────────────────────────────────
    const lerp = (a, b, t) => a + (b - a) * t
    const clamp = (x, a, b) => (x < a ? a : x > b ? b : x)
    const ease = (x) => { const c = clamp(x, 0, 1); return c * c * (3 - 2 * c) }

    function rot(px, py, cx, cy, a) {
      const s = Math.sin(a), c = Math.cos(a)
      const dx = px - cx, dy = py - cy
      return [cx + dx * c - dy * s, cy + dx * s + dy * c]
    }
    // Конечность-капсула: заливка — градиент ПЕРПЕНДИКУЛЯРНО оси (объём),
    // плюс круг в суставе, чтобы не было разрывов.
    function limb(ctx, x1, y1, x2, y2, w1, w2, cLight, cMid, cDark) {
      const a = Math.atan2(y2 - y1, x2 - x1)
      const nx = -Math.sin(a), ny = Math.cos(a)
      const g = ctx.createLinearGradient(x1 + nx * w1, y1 + ny * w1, x1 - nx * w1, y1 - ny * w1)
      g.addColorStop(0, cDark)
      g.addColorStop(0.42, cMid)
      g.addColorStop(0.72, cLight)
      g.addColorStop(1, cDark)
      ctx.beginPath()
      ctx.moveTo(x1 + nx * w1, y1 + ny * w1)
      ctx.lineTo(x2 + nx * w2, y2 + ny * w2)
      ctx.arc(x2, y2, w2, a + Math.PI / 2, a - Math.PI / 2, true)
      ctx.lineTo(x1 - nx * w1, y1 - ny * w1)
      ctx.arc(x1, y1, w1, a - Math.PI / 2, a + Math.PI / 2, true)
      ctx.closePath()
      ctx.fillStyle = g
      ctx.fill()
    }
    function joint(ctx, x, y, r, cLight, cMid, cDark) {
      const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r)
      g.addColorStop(0, cLight)
      g.addColorStop(0.6, cMid)
      g.addColorStop(1, cDark)
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(x, y, r, 0, TAU)
      ctx.fill()
    }
    function softEllipse(ctx, x, y, rx, ry, color, alpha) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, Math.max(rx, ry))
      g.addColorStop(0, color)
      g.addColorStop(1, 'rgba(0,0,0,0)')
      ctx.save()
      ctx.globalAlpha = alpha
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.ellipse(x, y, rx, ry, 0, 0, TAU)
      ctx.fill()
      ctx.restore()
    }

    // ── голова ───────────────────────────────────────────────────────────
    function drawHead(t) {
      const hx = B.head.x, hy = B.head.y
      ctx.save()
      ctx.translate(hx, hy)
      ctx.rotate(S.headTilt)
      ctx.translate(0, S.headBob)
      ctx.scale(1.14, 1.14)

      // шея
      const neckGrad = ctx.createLinearGradient(-26, 0, 26, 0)
      neckGrad.addColorStop(0, C.skinDark)
      neckGrad.addColorStop(0.45, C.skin)
      neckGrad.addColorStop(1, C.skinDark)
      ctx.fillStyle = neckGrad
      ctx.beginPath()
      ctx.moveTo(-26, 66)
      ctx.quadraticCurveTo(-28, 92, -30, 108)
      ctx.lineTo(30, 108)
      ctx.quadraticCurveTo(28, 92, 26, 66)
      ctx.closePath()
      ctx.fill()
      // тень под подбородком
      softEllipse(ctx, 0, 72, 40, 22, '#3A2418', 0.5)

      // череп + лицо
      const facePath = new Path2D()
      facePath.moveTo(0, -74)
      facePath.bezierCurveTo(48, -74, 72, -38, 72, 2)
      facePath.bezierCurveTo(72, 42, 56, 74, 30, 92)
      facePath.bezierCurveTo(18, 100, 10, 102, 0, 102)
      facePath.bezierCurveTo(-10, 102, -18, 100, -30, 92)
      facePath.bezierCurveTo(-56, 74, -72, 42, -72, 2)
      facePath.bezierCurveTo(-72, -38, -48, -74, 0, -74)
      facePath.closePath()
      const skin = ctx.createRadialGradient(-26, -34, 10, 6, 10, 132)
      skin.addColorStop(0, C.skinLight)
      skin.addColorStop(0.45, C.skin)
      skin.addColorStop(1, C.skinDark)
      ctx.fillStyle = skin
      ctx.fill(facePath)
      ctx.strokeStyle = 'rgba(92,56,34,.32)'
      ctx.lineWidth = 2
      ctx.stroke(facePath)

      // объём лица: свет слева, тень справа
      ctx.save()
      ctx.clip(facePath)
      softEllipse(ctx, 34, 6, 62, 78, '#7A4A2C', 0.30)
      softEllipse(ctx, -30, -40, 44, 30, '#FFFFFF', 0.16)
      softEllipse(ctx, -46, 46, 26, 18, '#E8736B', 0.16)
      softEllipse(ctx, 46, 46, 26, 18, '#E8736B', 0.13)
      softEllipse(ctx, 0, 92, 34, 12, '#8A5A3A', 0.22)
      ctx.restore()

      // уши
      for (const s of [-1, 1]) {
        ctx.fillStyle = C.skin
        ctx.beginPath()
        ctx.ellipse(s * 70, 6, 12, 20, 0, 0, TAU)
        ctx.fill()
        ctx.fillStyle = 'rgba(120,74,44,.45)'
        ctx.beginPath()
        ctx.ellipse(s * 71, 8, 6, 11, 0, 0, TAU)
        ctx.fill()
      }

      drawEye(-32, 12, t)
      drawEye(32, 12, t)
      drawNose()
      drawMouth(t)
      drawHair()
      ctx.restore()
    }

    function drawEye(ex, ey) {
      const closed = S.blink
      const w = 19, h = 10.5
      ctx.save()
      ctx.translate(ex, ey)
      // тень глазницы
      softEllipse(ctx, 0, -2, 24, 15, '#8A5A3A', 0.22)
      if (closed > 0.92) {
        // закрытый: дуга века
        ctx.strokeStyle = C.line
        ctx.lineWidth = 3.4
        ctx.lineCap = 'round'
        ctx.beginPath()
        ctx.moveTo(-w * 0.92, 1)
        ctx.quadraticCurveTo(0, -6, w * 0.92, 1)
        ctx.stroke()
        ctx.restore()
        return
      }
      // склера
      const sc = ctx.createLinearGradient(0, -h, 0, h)
      sc.addColorStop(0, '#E4EAF2')
      sc.addColorStop(1, '#FBFDFF')
      ctx.fillStyle = sc
      ctx.beginPath()
      ctx.ellipse(0, 0, w, h, 0, 0, TAU)
      ctx.fill()
      // радужка + зрачок + блик
      ctx.save()
      ctx.beginPath()
      ctx.ellipse(0, 0, w, h, 0, 0, TAU)
      ctx.clip()
      const ix = S.gx * 5, iy = S.gy * 3
      const iris = ctx.createRadialGradient(ix - 2, iy - 2, 1, ix, iy, 9)
      iris.addColorStop(0, C.iris)
      iris.addColorStop(0.7, C.irisDark)
      iris.addColorStop(1, '#101A28')
      ctx.fillStyle = iris
      ctx.beginPath()
      ctx.arc(ix, iy, 8.4, 0, TAU)
      ctx.fill()
      ctx.fillStyle = '#0A0E14'
      ctx.beginPath()
      ctx.arc(ix, iy, 3.6, 0, TAU)
      ctx.fill()
      ctx.fillStyle = 'rgba(255,255,255,.92)'
      ctx.beginPath()
      ctx.arc(ix - 3, iy - 3, 2.4, 0, TAU)
      ctx.fill()
      ctx.fillStyle = 'rgba(255,255,255,.5)'
      ctx.beginPath()
      ctx.arc(ix + 2.6, iy + 2.4, 1.3, 0, TAU)
      ctx.fill()
      // веко (при моргании)
      if (closed > 0) {
        ctx.fillStyle = C.skin
        ctx.beginPath()
        ctx.moveTo(-w, -h)
        ctx.lineTo(w, -h)
        ctx.lineTo(w, -h + 2 * h * closed)
        ctx.quadraticCurveTo(0, -h + 2 * h * closed + 6 * closed, -w, -h + 2 * h * closed)
        ctx.closePath()
        ctx.fill()
      }
      ctx.restore()
      // верхнее веко с ресницами
      ctx.strokeStyle = C.line
      ctx.lineWidth = 3.2
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(-w, 0.5)
      ctx.quadraticCurveTo(0, -h - 4.5, w, 0.5)
      ctx.stroke()
      ctx.lineWidth = 1.4
      ctx.strokeStyle = 'rgba(22,30,42,.55)'
      ctx.beginPath()
      ctx.moveTo(-w * 0.8, h * 0.7)
      ctx.quadraticCurveTo(0, h + 2.5, w * 0.8, h * 0.7)
      ctx.stroke()
      ctx.restore()
    }

    function drawNose() {
      ctx.save()
      ctx.strokeStyle = 'rgba(120,74,44,.55)'
      ctx.lineWidth = 3
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(2, 24)
      ctx.quadraticCurveTo(9, 40, 2, 45)
      ctx.stroke()
      ctx.fillStyle = 'rgba(120,74,44,.5)'
      ctx.beginPath()
      ctx.ellipse(-4, 46, 2.6, 1.7, -0.3, 0, TAU)
      ctx.fill()
      ctx.beginPath()
      ctx.ellipse(6, 46, 2.6, 1.7, 0.3, 0, TAU)
      ctx.fill()
      softEllipse(ctx, -2, 40, 9, 6, '#FFFFFF', 0.20)
      ctx.restore()
      // складки от носа к углам рта
      ctx.strokeStyle = 'rgba(120,74,44,.22)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(-10, 50)
      ctx.quadraticCurveTo(-18, 60, -22, 66)
      ctx.moveTo(10, 50)
      ctx.quadraticCurveTo(18, 60, 22, 66)
      ctx.stroke()
      // блик на подбородке
      softEllipse(ctx, 0, 92, 16, 8, '#FFFFFF', 0.16)
    }

    function drawMouth(t) {
      const m = MOUTHS[S.mouth] || MOUTHS[0]
      const nx = MOUTHS[S.mouthNext] || MOUTHS[0]
      const k = S.mouthK
      const mw = 30 * lerp(m.w, nx.w, k)
      const mh = 26 * lerp(m.h, nx.h, k)
      const corner = lerp(m.corner, nx.corner, k)
      const teeth = lerp(m.teeth, nx.teeth, k)
      const tongue = lerp(m.tongue, nx.tongue, k)
      const cy = 68
      ctx.save()
      ctx.translate(0, cy)
      // внутренняя полость рта
      if (mh > 3) {
        const g = ctx.createRadialGradient(0, 0, 1, 0, 0, mw)
        g.addColorStop(0, '#160A0C')
        g.addColorStop(1, C.mouth)
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.moveTo(-mw, -mh * 0.18)
        ctx.quadraticCurveTo(0, -mh * 0.62, mw, -mh * 0.18)
        ctx.quadraticCurveTo(mw * 0.86, mh * 0.82, 0, mh * 0.92)
        ctx.quadraticCurveTo(-mw * 0.86, mh * 0.82, -mw, -mh * 0.18)
        ctx.closePath()
        ctx.fill()
        if (teeth > 0.05) {
          ctx.save()
          ctx.globalAlpha = teeth
          ctx.fillStyle = C.teeth
          ctx.beginPath()
          ctx.moveTo(-mw * 0.86, -mh * 0.24)
          ctx.quadraticCurveTo(0, -mh * 0.5, mw * 0.86, -mh * 0.24)
          ctx.lineTo(mw * 0.82, -mh * 0.02)
          ctx.quadraticCurveTo(0, -mh * 0.28, -mw * 0.82, -mh * 0.02)
          ctx.closePath()
          ctx.fill()
          ctx.restore()
        }
        if (tongue > 0.05) {
          ctx.save()
          ctx.globalAlpha = tongue * 0.95
          ctx.fillStyle = C.tongue
          ctx.beginPath()
          ctx.ellipse(0, mh * 0.5, mw * 0.5, mh * 0.34, 0, 0, TAU)
          ctx.fill()
          ctx.restore()
        }
      }
      // верхняя губа
      ctx.fillStyle = C.lip
      ctx.beginPath()
      ctx.moveTo(-mw, -mh * 0.1 - corner * 2)
      ctx.quadraticCurveTo(-mw * 0.5, -mh * 0.34 - corner * 3, 0, -mh * 0.3 - corner * 2)
      ctx.quadraticCurveTo(mw * 0.5, -mh * 0.34 - corner * 3, mw, -mh * 0.1 - corner * 2)
      ctx.quadraticCurveTo(0, mh * 0.1, -mw, -mh * 0.1 - corner * 2)
      ctx.closePath()
      ctx.fill()
      // нижняя губа
      const lg = ctx.createLinearGradient(0, 0, 0, mh * 0.5 + 6)
      lg.addColorStop(0, C.lip)
      lg.addColorStop(1, '#9C534E')
      ctx.fillStyle = lg
      ctx.beginPath()
      ctx.moveTo(-mw * 0.94, -mh * 0.06 - corner)
      ctx.quadraticCurveTo(0, mh * 0.42, mw * 0.94, -mh * 0.06 - corner)
      ctx.quadraticCurveTo(0, mh * 0.3 + 4, -mw * 0.94, -mh * 0.06 - corner)
      ctx.closePath()
      ctx.fill()
      // блик на нижней губе
      ctx.strokeStyle = 'rgba(255,255,255,.30)'
      ctx.lineWidth = 2.4
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(-mw * 0.4, mh * 0.24)
      ctx.quadraticCurveTo(0, mh * 0.34, mw * 0.36, mh * 0.2)
      ctx.stroke()
      ctx.restore()
    }

    function drawHair() {
      // шапка волос
      const hp = new Path2D()
      hp.moveTo(-74, 10)
      hp.bezierCurveTo(-80, -60, -46, -96, 0, -96)
      hp.bezierCurveTo(46, -96, 80, -60, 74, 10)
      hp.bezierCurveTo(66, -22, 52, -40, 30, -48)
      hp.bezierCurveTo(8, -56, -16, -54, -34, -46)
      hp.bezierCurveTo(-54, -37, -70, -14, -74, 10)
      hp.closePath()
      const hg = ctx.createLinearGradient(-60, -90, 60, 20)
      hg.addColorStop(0, C.hairLight)
      hg.addColorStop(0.45, C.hair)
      hg.addColorStop(1, '#241A15')
      ctx.fillStyle = hg
      ctx.fill(hp)
      // блики и пряди
      ctx.save()
      ctx.clip(hp)
      ctx.strokeStyle = 'rgba(255,225,190,.22)'
      ctx.lineWidth = 3
      ctx.lineCap = 'round'
      for (let i = 0; i < 7; i++) {
        const x = -58 + i * 19
        ctx.beginPath()
        ctx.moveTo(x, -70)
        ctx.quadraticCurveTo(x + 10, -30, x + 4, 6)
        ctx.stroke()
      }
      softEllipse(ctx, -26, -66, 44, 16, '#FFFFFF', 0.12)
      ctx.restore()
      // чёлка
      // пробор и чёлка
      ctx.fillStyle = C.hair
      ctx.beginPath()
      ctx.moveTo(-40, -50)
      ctx.quadraticCurveTo(-4, -70, 40, -48)
      ctx.quadraticCurveTo(18, -46, 2, -34)
      ctx.quadraticCurveTo(-18, -28, -34, -34)
      ctx.quadraticCurveTo(-42, -38, -40, -50)
      ctx.closePath()
      ctx.fill()
      // выбивающиеся пряди
      ctx.strokeStyle = 'rgba(28,20,16,.9)'
      ctx.lineWidth = 2.4
      ctx.lineCap = 'round'
      for (const [x1, y1, x2, y2] of [[-62, -46, -76, -18], [58, -48, 74, -22], [-44, -62, -30, -74]]) {
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.quadraticCurveTo((x1 + x2) / 2, (y1 + y2) / 2 - 6, x2, y2)
        ctx.stroke()
      }
      // блик на макушке
      softEllipse(ctx, -14, -74, 46, 14, '#FFFFFF', 0.14)
    }

    // ── тело ─────────────────────────────────────────────────────────────
    function drawBody(t) {
      const hipY = B.hips.y
      const shY = B.shL.y
      const neckY = B.neck.y
      const w = 104

      // ноги
      drawLeg(B.hipL, B.knL, B.anL, S.legL, S.kneeL, 'L')
      drawLeg(B.hipR, B.knR, B.anR, S.legR, S.kneeR, 'R')

      // торс: трапеция плеч → талия
      const tg = ctx.createLinearGradient(B.hips.x - w, 0, B.hips.x + w, 0)
      tg.addColorStop(0, C.shirtLight)
      tg.addColorStop(0.38, C.shirt)
      tg.addColorStop(1, C.shirtDark)
      ctx.fillStyle = tg
      ctx.beginPath()
      ctx.moveTo(B.hips.x - 40, neckY - 4)
      ctx.quadraticCurveTo(B.hips.x - w + 6, shY - 16, B.hips.x - w - 2, shY + 58)
      ctx.quadraticCurveTo(B.hips.x - 108, hipY - 104, B.hips.x - 96, hipY + 14)
      ctx.quadraticCurveTo(B.hips.x, hipY + 30, B.hips.x + 96, hipY + 14)
      ctx.quadraticCurveTo(B.hips.x + 108, hipY - 104, B.hips.x + 96, hipY + 14)
      ctx.quadraticCurveTo(B.hips.x + w - 6, shY - 16, B.hips.x + 40, neckY - 4)
      ctx.closePath()
      ctx.fill()
      ctx.strokeStyle = 'rgba(10,22,38,.30)'
      ctx.lineWidth = 3
      ctx.stroke()
      // объём: свет слева, тень справа, складки
      ctx.save()
      ctx.clip()
      softEllipse(ctx, B.hips.x - 74, shY + 44, 46, 76, '#FFFFFF', 0.11)
      softEllipse(ctx, B.hips.x + 92, hipY - 56, 44, 96, '#0A1E33', 0.26)
      softEllipse(ctx, B.hips.x - 20, hipY - 20, 70, 40, '#0A1E33', 0.10)
      ctx.strokeStyle = 'rgba(18,38,64,.26)'
      ctx.lineWidth = 3
      for (let i = 0; i < 3; i++) {
        ctx.beginPath()
        ctx.moveTo(B.hips.x - 72 + i * 30, hipY - 74 + i * 10)
        ctx.quadraticCurveTo(B.hips.x - 64 + i * 30, hipY - 36, B.hips.x - 76 + i * 30, hipY - 8)
        ctx.stroke()
      }
      ctx.restore()
      // тень от головы на грудь
      softEllipse(ctx, B.hips.x, neckY + 16, 62, 26, '#08182C', 0.30)
      // контровой свет по правому краю (тонкий, без артефактов)
      ctx.save()
      ctx.clip()
      const rim = ctx.createLinearGradient(B.hips.x + w - 26, 0, B.hips.x + w + 6, 0)
      rim.addColorStop(0, 'rgba(187,216,255,0)')
      rim.addColorStop(1, 'rgba(187,216,255,.22)')
      ctx.fillStyle = rim
      ctx.fillRect(B.hips.x, shY - 40, w + 20, hipY - shY + 90)
      ctx.restore()
      // воротник: две стойки + засечка
      ctx.fillStyle = C.shirtDark
      ctx.beginPath()
      ctx.moveTo(B.hips.x - 50, neckY - 14)
      ctx.lineTo(B.hips.x - 30, neckY + 18)
      ctx.lineTo(B.hips.x - 12, neckY - 10)
      ctx.closePath()
      ctx.moveTo(B.hips.x + 50, neckY - 14)
      ctx.lineTo(B.hips.x + 30, neckY + 18)
      ctx.lineTo(B.hips.x + 12, neckY - 10)
      ctx.closePath()
      ctx.fill()
      ctx.strokeStyle = 'rgba(255,255,255,.18)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(B.hips.x - 48, neckY - 12)
      ctx.lineTo(B.hips.x - 30, neckY + 16)
      ctx.moveTo(B.hips.x + 48, neckY - 12)
      ctx.lineTo(B.hips.x + 30, neckY + 16)
      ctx.stroke()
      // нагрудный карман
      ctx.strokeStyle = 'rgba(16,34,56,.42)'
      ctx.lineWidth = 2.4
      ctx.beginPath()
      ctx.roundRect(B.hips.x - 78, shY + 44, 42, 40, 3)
      ctx.stroke()
      // строчка по боку
      ctx.strokeStyle = 'rgba(255,255,255,.10)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(B.hips.x - w + 18, shY + 70)
      ctx.quadraticCurveTo(B.hips.x - w + 24, hipY - 60, B.hips.x - 92, hipY - 6)
      ctx.stroke()
      // пуговицы
      for (let i = 0; i < 3; i++) {
        const by = shY + 52 + i * 58
        ctx.fillStyle = '#EAF0F7'
        ctx.beginPath()
        ctx.arc(B.hips.x, by, 4.4, 0, TAU)
        ctx.fill()
        ctx.fillStyle = 'rgba(20,40,66,.45)'
        ctx.beginPath()
        ctx.arc(B.hips.x + 1.4, by + 1.4, 1.6, 0, TAU)
        ctx.fill()
      }
      // ремень с пряжкой
      ctx.fillStyle = '#1E2635'
      ctx.beginPath()
      ctx.roundRect(B.hips.x - 100, hipY + 2, 200, 19, 5)
      ctx.fill()
      ctx.fillStyle = 'rgba(255,255,255,.10)'
      ctx.fillRect(B.hips.x - 98, hipY + 3, 196, 4)
      ctx.fillStyle = '#C8D2E0'
      ctx.beginPath()
      ctx.roundRect(B.hips.x - 15, hipY + 3, 30, 17, 3)
      ctx.fill()
      ctx.strokeStyle = '#7C8AA0'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.roundRect(B.hips.x - 15, hipY + 3, 30, 17, 3)
      ctx.stroke()

      // руки (ближняя поверх торса)
      drawArm(B.shL, B.elL, B.wrL, S.armL, S.foreL, 'L')
      drawArm(B.shR, B.elR, B.wrR, S.armR, S.foreR, 'R')
    }

    function drawArm(sh, el, wr, upper, fore, side) {
      const dir = side === 'L' ? -1 : 1
      // a=0 — рука висит вниз; положительный угол уводит локоть наружу
      const a1 = dir * (0.10 + upper)
      const ex = sh.x + Math.sin(a1) * 148, ey = sh.y + Math.cos(a1) * 148
      const a2 = a1 - dir * (0.14 + fore)
      const wx = ex + Math.sin(a2) * 128, wy = ey + Math.cos(a2) * 128
      el.x = ex; el.y = ey; wr.x = wx; wr.y = wy

      const A_L = '#3E7CBE', A_M = '#2A63A0', A_D = '#1B4370'
      joint(ctx, sh.x, sh.y, 38, A_L, A_M, A_D)
      limb(ctx, sh.x, sh.y, ex, ey, 40, 30, A_L, A_M, A_D)
      joint(ctx, ex, ey, 30, A_L, A_M, A_D)
      limb(ctx, ex, ey, wx, wy, 30, 21, A_L, A_M, A_D)
      // тень от руки на корпусе
      softEllipse(ctx, sh.x - dir * 26, sh.y + 60, 22, 90, '#0A1E33', 0.18)
      // манжета
      ctx.save()
      ctx.translate(wx, wy)
      ctx.rotate(a2)
      ctx.fillStyle = C.shirtDark
      ctx.beginPath()
      ctx.roundRect(-25, -21, 13, 42, 4)
      ctx.fill()
      ctx.restore()
      // кисть
      ctx.save()
      ctx.translate(wx, wy)
      ctx.rotate(a2)
      const hg = ctx.createRadialGradient(-8, 26, 3, 2, 30, 40)
      hg.addColorStop(0, C.skinLight)
      hg.addColorStop(0.6, C.skin)
      hg.addColorStop(1, C.skinDark)
      ctx.fillStyle = hg
      ctx.beginPath()
      ctx.moveTo(-15, 8)
      ctx.quadraticCurveTo(-19, 44, -6, 54)
      ctx.quadraticCurveTo(10, 60, 18, 46)
      ctx.quadraticCurveTo(22, 22, 14, 8)
      ctx.closePath()
      ctx.fill()
      // большой палец
      ctx.beginPath()
      ctx.ellipse(-11, 22, 6, 11, -0.5, 0, TAU)
      ctx.fill()
      ctx.strokeStyle = 'rgba(120,74,44,.45)'
      ctx.lineWidth = 1.8
      for (let i = 0; i < 3; i++) {
        ctx.beginPath()
        ctx.moveTo(0 + i * 6, 16)
        ctx.lineTo(-1 + i * 6, 48)
        ctx.stroke()
      }
      ctx.restore()
    }

    function drawLeg(hip, kn, an, swing, knee, side) {
      const dir = side === 'L' ? -1 : 1
      const a1 = dir * swing
      const kx = hip.x + Math.sin(a1) * 172, ky = hip.y + Math.cos(a1) * 172
      const a2 = a1 + dir * knee
      const ax = kx + Math.sin(a2) * 158, ay = ky + Math.cos(a2) * 158
      kn.x = kx; kn.y = ky; an.x = ax; an.y = ay
      joint(ctx, hip.x, hip.y, 46, C.pantsLight, C.pants, '#1E2634')
      limb(ctx, hip.x, hip.y, kx, ky, 45, 33, C.pantsLight, C.pants, '#1E2634')
      joint(ctx, kx, ky, 33, C.pantsLight, C.pants, '#1E2634')
      limb(ctx, kx, ky, ax, ay, 33, 23, C.pantsLight, C.pants, '#1E2634')
      // ботинок
      ctx.save()
      ctx.translate(ax, ay)
      ctx.rotate(a2)
      const bg = ctx.createLinearGradient(-20, -20, 30, 46)
      bg.addColorStop(0, C.shoeLight)
      bg.addColorStop(0.45, C.shoe)
      bg.addColorStop(1, '#0E131C')
      ctx.fillStyle = bg
      ctx.beginPath()
      ctx.moveTo(-25, -12)
      ctx.quadraticCurveTo(-29, 30, -25, 44)
      ctx.quadraticCurveTo(-8, 52, 32, 50)
      ctx.quadraticCurveTo(45, 48, 43, 34)
      ctx.quadraticCurveTo(40, 6, 22, -10)
      ctx.closePath()
      ctx.fill()
      ctx.fillStyle = '#DCE3EC'
      ctx.beginPath()
      ctx.moveTo(-25, 36)
      ctx.lineTo(43, 36)
      ctx.quadraticCurveTo(45, 50, 32, 52)
      ctx.lineTo(-24, 50)
      ctx.closePath()
      ctx.fill()
      ctx.strokeStyle = 'rgba(20,28,40,.5)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(-16, 18)
      ctx.lineTo(14, 14)
      ctx.moveTo(-18, 26)
      ctx.lineTo(16, 22)
      ctx.stroke()
      ctx.restore()
    }

    // ── поза ─────────────────────────────────────────────────────────────
    function pose(t) {
      const s = t / 1000
      const vis = o.visemes || []
      // виземы
      let cur = 0, next = 0, nextAt = null
      for (const it of vis) {
        const at = it.t !== undefined ? it.t : it.timeMs
        const v = it.v !== undefined ? it.v : it.viseme
        if (at <= t) { cur = v; next = 0; nextAt = null } else { next = v; nextAt = at; break }
      }
      let k = 0
      const blend = o.blend !== undefined ? o.blend : 70
      if (nextAt !== null && blend > 0 && t > nextAt - blend) k = clamp((t - (nextAt - blend)) / blend, 0, 1)
      S.mouth = cur; S.mouthNext = next; S.mouthK = k
      const OPEN = [0.06, 0.9, 0.04, 0.3, 0.7, 0.4, 0.55, 0.8, 0.75, 0.25]
      S.open = lerp(OPEN[cur] || 0, OPEN[next] || 0, k)

      // дыхание
      const breath = Math.sin(s * 1.5)
      // моргание
      const period = o.blinkPeriod || 3800
      const bt = (t + (o.seed || 0)) % period
      S.blink = bt < 170 ? Math.sin((bt / 170) * Math.PI) : 0
      // взгляд
      S.gx = Math.sin(s * 0.7) * 1.1 + Math.sin(s * 2.3) * 0.35
      S.gy = Math.cos(s * 0.5) * 0.7 + Math.sin(s * 1.9) * 0.25
      // голова
      S.headTilt = (1.4 * Math.sin(s * 0.8) + (o.lookAt || 0)) * 0.0175
      S.headBob = breath * 1.6
      // жест
      let g = 0
      if (o.gestureAt !== undefined && o.gestureAt !== null) {
        const dur = o.gestureDur || 1500
        g = Math.min(ease((t - o.gestureAt) / 300), 1 - ease((t - (o.gestureAt + dur)) / 300))
      }
      S.armR = 0.30 * g          // локоть чуть в сторону
      S.foreR = 1.25 * g         // предплечье поднимается вверх — жест ведущего
      S.armL = -0.10 * Math.sin(s * 0.9)
      S.foreL = 0.30 + 0.08 * Math.sin(s * 0.6)
      // ходьба
      if (o.walk) {
        const sw = Math.sin(s * 6.2)
        S.legL = sw * 0.36; S.legR = -sw * 0.36
        S.kneeL = Math.max(0, -sw) * 0.5; S.kneeR = Math.max(0, sw) * 0.5
        S.armL = sw * 0.24; S.foreL = 0.3
      } else {
        S.legL = 0.04; S.legR = -0.04; S.kneeL = 0.03; S.kneeR = 0.03
      }
      // настроение → брови
      const MOODS = {
        neutral: [0, 0], joy: [-2.6, 0.09], anger: [2.6, -0.1], sad: [-1.4, -0.07], surprise: [-5, 0.12],
      }
      const m = MOODS[o.mood] || MOODS.neutral
      S.brow = m[0]; S.browTilt = m[1]
    }

    function draw(t) {
      ctx.setTransform(K, 0, 0, K, 0, 0)
      ctx.clearRect(0, 0, VW, VH)
      pose(t)
      drawBody(t)
      drawHead(t)
      // брови поверх головы
      ctx.save()
      ctx.translate(B.head.x, B.head.y)
      ctx.rotate(S.headTilt)
      ctx.translate(0, S.headBob)
      ctx.scale(1.14, 1.14)
      ctx.strokeStyle = C.hair
      ctx.lineCap = 'round'
      for (const s of [-1, 1]) {
        ctx.lineWidth = 6
        ctx.beginPath()
        ctx.moveTo(s * 16, 0 + S.brow)
        ctx.quadraticCurveTo(s * 32, -9 + S.brow, s * 50, -3 + S.brow)
        ctx.stroke()
      }
      ctx.restore()
    }

    return {
      seek(t) { draw(t) },
      palette: C,
    }
  }

  window.CharacterRig = { create, palette: PALETTE, mouths: MOUTHS }
})()
