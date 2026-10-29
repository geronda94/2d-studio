/* PaperCast Animals v2 — deterministic paper-cut animals on Canvas 2D.
 *
 * Side-view skeletons: quadruped (dog, cat), bird (chicken, dove).
 * Flat fills, ink outlines, one continuous tube per limb; seek(t) is pure.
 *
 *   const pet = PaperCastAnimals.create(canvas, { kind: 'dog', pose: 'sit' })
 *   pet.setGait('walk'); pet.seek(1200)
 */
(function () {
  'use strict'

  const TAU = Math.PI * 2
  const DEG = Math.PI / 180
  const INK = '#20232d'

  const KINDS = {
    dog: {
      family: 'quadruped', label: 'Пёс',
      fur: '#b9824f', dark: '#8a5a32', light: '#d8a873', belly: '#efd3ae',
      nose: '#241d19', eye: '#3a2a1e', collar: '#d86a3d',
      r: 50, chest: [252, 336], hip: [418, 346], head: [188, 248], headR: 33,
      snout: 1.05, ears: 'flop', tail: 'up', tailLen: 86, tailW: 17,
      legs: { front: [86, 86], back: [90, 90] }, slim: 1,
    },
    cat: {
      family: 'quadruped', label: 'Кот',
      fur: '#8f96a3', dark: '#6c7380', light: '#b6bdc9', belly: '#dde1e8',
      nose: '#241d19', eye: '#3f5b46', collar: '#2e7a78',
      r: 43, chest: [258, 338], hip: [410, 348], head: [198, 252], headR: 30,
      snout: 0.66, ears: 'point', tail: 'long', tailLen: 126, tailW: 13,
      legs: { front: [85, 85], back: [88, 88] }, slim: 0.93,
    },
    pig: {
      family: 'quadruped', label: 'Свинья',
      fur: '#e0a394', dark: '#c07f72', light: '#f2c3b5', belly: '#f7d9ce',
      nose: '#b06a62', eye: '#3a2a1e', collar: null,
      r: 48, chest: [252, 340], hip: [414, 350], head: [196, 258], headR: 31,
      snout: 1.15, ears: 'flop', tail: 'curl', tailLen: 42, tailW: 12,
      legs: { front: [84, 84], back: [88, 88] }, slim: 1.06, pigNose: true,
    },
    cow: {
      family: 'quadruped', label: 'Корова',
      fur: '#efe7db', dark: '#cfc4b4', light: '#f8f3ea', belly: '#fbf7f0',
      nose: '#c98f86', eye: '#3a2a1e', collar: null, patch: '#2f2b2a',
      r: 58, chest: [246, 334], hip: [420, 344], head: [188, 244], headR: 34,
      snout: 0.96, ears: 'flop', tail: 'up', tailLen: 84, tailW: 14,
      legs: { front: [90, 90], back: [92, 92] }, slim: 1.04, horns: true, spots: true,
    },
    eagle: {
      family: 'avian', label: 'Орёл',
      body: '#8a6a4e', bodyDark: '#6d5139', wing: '#7b5c41', wingDark: '#5c412c',
      tail: '#6d5139', comb: null, wattle: null, beak: '#e0b23c',
      eye: '#241d19', leg: '#d7a63f', legDark: '#a57a28',
      bodyC: [316, 348], headC: [398, 266], bodyR: [92, 64], headColor: '#efe6d6',
      beakHook: true, wingScale: 1.16,
    },
    tit: {
      family: 'avian', label: 'Синица',
      body: '#e9c94f', bodyDark: '#c9a832', wing: '#d8b83e', wingDark: '#a8892a',
      tail: '#b39a3a', comb: null, wattle: null, beak: '#5b5348',
      eye: '#241d19', leg: '#8a8070', legDark: '#6b6154',
      bodyC: [316, 342], headC: [398, 262], bodyR: [76, 58], headColor: '#2b2b2f',
      beakHook: false, wingScale: 0.92,
    },
    beetle: {
      family: 'insectoid', label: 'Жук',
      shell: '#4a3a2c', shellLight: '#6b5540', body: '#2e2620', leg: '#3a2f28',
      eye: '#1a1513', accent: '#8a6a4a', stripe: null,
      abdomenR: [70, 50], thoraxR: 38, headR: 26,
    },
    bee: {
      family: 'insectoid', label: 'Пчела',
      shell: '#e2b93f', shellLight: '#f2d06a', body: '#2a2320', leg: '#3a2f28',
      eye: '#1a1513', accent: '#f2d06a', stripe: '#2a2320', wing: '#d9ecf5',
      abdomenR: [62, 46], thoraxR: 36, headR: 25,
    },
    chicken: {
      family: 'avian', label: 'Курица',
      body: '#ecd9b3', bodyDark: '#cbb387', wing: '#dcc59b', wingDark: '#b39a6f',
      tail: '#b39a6f', comb: '#cf4a3a', wattle: '#c8402f', beak: '#e0a23c',
      eye: '#241d19', leg: '#d09a3f', legDark: '#a8762c',
      bodyC: [318, 352], headC: [392, 272], bodyR: [88, 64],
    },
    dove: {
      family: 'avian', label: 'Голубь',
      body: '#adb8c6', bodyDark: '#8d99aa', wing: '#9aa7b9', wingDark: '#78869b',
      tail: '#7f8c9e', comb: null, wattle: null, beak: '#c9a06a',
      eye: '#241d19', leg: '#c2746a', legDark: '#95534b',
      bodyC: [318, 344], headC: [402, 256], bodyR: [84, 60],
    },
  }

  // ── canvas helpers ───────────────────────────────────────────────────────
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
  // smooth tube through a polyline with round caps
  function tube(ctx, pts, radii, fill, lw) {
    const N = 12, samples = []
    for (let s = 0; s < pts.length - 1; s++) {
      const a = pts[s], b = pts[s + 1], ra = radii[s], rb = radii[s + 1]
      for (let i = 0; i < N; i++) {
        const k = i / N
        samples.push({ x: a[0] + (b[0] - a[0]) * k, y: a[1] + (b[1] - a[1]) * k, r: ra + (rb - ra) * k })
      }
    }
    const last = pts.length - 1
    samples.push({ x: pts[last][0], y: pts[last][1], r: radii[last] })
    const left = [], right = []
    for (let i = 0; i < samples.length; i++) {
      const a = samples[Math.max(0, i - 1)], b = samples[Math.min(samples.length - 1, i + 1)]
      let dx = b.x - a.x, dy = b.y - a.y
      const l = Math.hypot(dx, dy) || 1
      dx /= l; dy /= l
      const nx = -dy, ny = dx, s = samples[i]
      left.push([s.x + nx * s.r, s.y + ny * s.r])
      right.push([s.x - nx * s.r, s.y - ny * s.r])
    }
    const d0 = { x: samples[1].x - samples[0].x, y: samples[1].y - samples[0].y }
    const l0 = Math.hypot(d0.x, d0.y) || 1
    const dn = { x: samples[samples.length - 1].x - samples[samples.length - 2].x, y: samples[samples.length - 1].y - samples[samples.length - 2].y }
    const ln = Math.hypot(dn.x, dn.y) || 1
    const k = 0.5523, p0 = samples[0], pn = samples[samples.length - 1]

    ctx.beginPath()
    ctx.moveTo(left[0][0], left[0][1])
    for (let i = 1; i < left.length; i++) ctx.lineTo(left[i][0], left[i][1])
    const lE = left[left.length - 1], rE = right[right.length - 1]
    ctx.bezierCurveTo(
      lE[0] + (dn.x / ln) * pn.r * k, lE[1] + (dn.y / ln) * pn.r * k,
      rE[0] + (dn.x / ln) * pn.r * k, rE[1] + (dn.y / ln) * pn.r * k,
      rE[0], rE[1])
    for (let i = right.length - 2; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1])
    const lS = left[0], rS = right[0]
    ctx.bezierCurveTo(
      rS[0] - (d0.x / l0) * p0.r * k, rS[1] - (d0.y / l0) * p0.r * k,
      lS[0] - (d0.x / l0) * p0.r * k, lS[1] - (d0.y / l0) * p0.r * k,
      lS[0], lS[1])
    ctx.closePath()
    fillStroke(ctx, fill, INK, lw || 3)
  }
  // tapered curved tail (quadratic centreline)
  function taperedTail(ctx, a, c, b, w0, w1, fill) {
    const N = 14, left = [], right = []
    for (let i = 0; i <= N; i++) {
      const t = i / N
      const x = (1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0]
      const y = (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]
      const dx = 2 * (1 - t) * (c[0] - a[0]) + 2 * t * (b[0] - c[0])
      const dy = 2 * (1 - t) * (c[1] - a[1]) + 2 * t * (b[1] - c[1])
      const l = Math.hypot(dx, dy) || 1
      const w = (w0 + (w1 - w0) * t) / 2
      left.push([x - dy / l * w, y + dx / l * w])
      right.push([x + dy / l * w, y - dx / l * w])
    }
    ctx.beginPath()
    ctx.moveTo(left[0][0], left[0][1])
    for (let i = 1; i <= N; i++) ctx.lineTo(left[i][0], left[i][1])
    for (let i = N; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1])
    ctx.closePath()
    fillStroke(ctx, fill, INK, 3)
  }
  function rotPt(pt, c, a) {
    if (!a) return pt
    const ca = Math.cos(a), sa = Math.sin(a)
    const dx = pt[0] - c[0], dy = pt[1] - c[1]
    return [c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca]
  }

  function solve2(root, target, upper, lower, bend) {
    let dx = target[0] - root[0], dy = target[1] - root[1]
    let d = Math.hypot(dx, dy) || 0.001
    const max = (upper + lower) * 0.985
    const min = Math.abs(upper - lower) + 6
    if (d > max) { dx *= max / d; dy *= max / d; d = max }
    if (d < min) { const f = min / d; dx *= f; dy *= f; d = min }
    const ux = dx / d, uy = dy / d
    const a = (upper * upper - lower * lower + d * d) / (2 * d)
    const h = Math.sqrt(Math.max(0, upper * upper - a * a))
    return {
      joint: [root[0] + ux * a - uy * h * bend, root[1] + uy * a + ux * h * bend],
      end: [root[0] + dx, root[1] + dy],
    }
  }

  // ── quadruped ────────────────────────────────────────────────────────────
  const PAWS = { fl: [250, 540], fr: [270, 540], bl: [420, 540], br: [440, 540] }
  const GAIT_OFF = { fl: 0, fr: Math.PI, bl: Math.PI * 0.5, br: Math.PI * 1.5 }

  function quadJoints(kind, pose, t, gait, seed, fkIn) {
    const fk = fkIn || {}
    const k = KINDS[kind]
    const moving = gait === 'walk' || gait === 'run'
    const speed = gait === 'run' ? 1.8 : 1
    const phase = (t / 1000) * TAU * speed + seed
    const stride = gait === 'run' ? 56 : 38
    const lift = gait === 'run' ? 38 : 24

    let dy = 0, headDy = 0, headDx = 0
    if (pose === 'sit') { dy = 92; headDy = 12 }
    else if (pose === 'lie') { dy = 132; headDy = 54; headDx = 12 }
    else if (pose === 'bark') { headDy = -22; headDx = -6 }

    const bob = moving
      ? Math.sin(phase * 2) * (gait === 'run' ? 7 : 4)
      : Math.sin((t / 1000) * 1.7 + seed) * 1.8
    const bodyY = k.chest[1] + 6
    const chest = [k.chest[0], bodyY + dy + bob]
    const hip = [k.hip[0], k.hip[1] + 6 + dy * 1.06 + bob]
    let head = [k.head[0] + headDx, k.head[1] + (bodyY - (k.chest[1] - 50)) * 0.35 + dy * 0.78 + headDy + bob * 0.6]

    const targets = {
      fl: [PAWS.fl[0], PAWS.fl[1]], fr: [PAWS.fr[0], PAWS.fr[1]],
      bl: [PAWS.bl[0], PAWS.bl[1]], br: [PAWS.br[0], PAWS.br[1]],
    }
    if (pose === 'sit') {
      targets.fl = [238, 540]; targets.fr = [256, 540]
      targets.bl = [452, 540]; targets.br = [470, 540]
    } else if (pose === 'lie') {
      targets.fl = [206, 540]; targets.fr = [224, 540]
      targets.bl = [438, 540]; targets.br = [454, 540]
    }
    if (moving) {
      for (const key of Object.keys(targets)) {
        const p = phase + GAIT_OFF[key]
        targets[key][0] += Math.sin(p) * stride
        targets[key][1] -= Math.max(0, Math.sin(p)) * lift
      }
    }

    const legs = {}
    for (const key of ['fl', 'fr', 'bl', 'br']) {
      const front = key[0] === 'f'
      const far = key[1] === 'r'
      const root = front
        ? [chest[0] + (far ? -10 : 14), chest[1] + 22]
        : [hip[0] + (far ? -6 : 12), hip[1] + 8]
      const [up, lo] = front ? k.legs.front : k.legs.back
      const solved = solve2(root, targets[key], up, lo, front ? -1 : 1)
      legs[key] = { root, knee: solved.joint, paw: solved.end, far }
    }
    const neckA = (fk.neck || 0) * DEG
    if (neckA) head = rotPt(head, chest, neckA)
    for (const key of ['fl', 'fr', 'bl', 'br']) {
      const L = legs[key]
      const hipA = (fk[key + 'Hip'] || 0) * DEG
      if (hipA) {
        L.knee = rotPt(L.knee, L.root, hipA)
        L.paw = rotPt(L.paw, L.root, hipA)
      }
      const kneeA = (fk[key + 'Knee'] || 0) * DEG
      if (kneeA) L.paw = rotPt(L.paw, L.knee, kneeA)
    }
    return { k, chest, hip, head, dy, legs, phase, moving, gait, bob, fk, headRot: (fk.head || 0) }
  }

  function drawQuad(ctx, kind, pose, t, gait, seed, skeleton, fk) {
    const S = quadJoints(kind, pose, t, gait, seed, fk)
    const k = S.k
    const r = k.r * k.slim

    ctx.save()
    ctx.globalAlpha = 0.15
    ctx.beginPath()
    ctx.ellipse(340, 548, 150, 16, 0, 0, TAU)
    ctx.fillStyle = '#10121b'; ctx.filter = 'blur(3px)'; ctx.fill()
    ctx.restore()

    for (const key of ['fr', 'br']) drawQuadLeg(ctx, S.legs[key], k, true)
    drawTail(ctx, S, k, pose)
    // body: arched capsule + chest + haunch
    const mid = [(S.chest[0] + S.hip[0]) / 2, (S.chest[1] + S.hip[1]) / 2 - 12 * k.slim]
    tube(ctx, [S.chest, mid, S.hip], [r * 0.94, r, r * 1.02], k.fur, 3.2)
    ctx.beginPath()
    ctx.ellipse(S.chest[0] + 12, S.chest[1] + 10, r * 0.78, r * 0.72, -0.1, 0, TAU)
    ctx.fillStyle = k.fur; ctx.fill()
    ctx.beginPath()
    ctx.ellipse(S.hip[0] - 4, S.hip[1] + 6, r * 0.8, r * 0.74, 0.1, 0, TAU)
    ctx.fillStyle = k.fur; ctx.fill()
    // belly
    ctx.beginPath()
    ctx.ellipse((S.chest[0] + S.hip[0]) / 2 + 6, (S.chest[1] + S.hip[1]) / 2 + 26 * k.slim, 70 * k.slim, 22, 0, 0, TAU)
    ctx.fillStyle = k.belly; ctx.globalAlpha = 0.9; ctx.fill(); ctx.globalAlpha = 1
    // back highlight
    ctx.beginPath()
    ctx.moveTo(S.chest[0] - 10, S.chest[1] - r * 0.72)
    ctx.quadraticCurveTo(mid[0], mid[1] - r * 0.95, S.hip[0] + 14, S.hip[1] - r * 0.55)
    ctx.strokeStyle = k.light; ctx.lineWidth = 6; ctx.globalAlpha = 0.35; ctx.stroke(); ctx.globalAlpha = 1

    if (k.spots) {
      ctx.save()
      ctx.globalAlpha = 0.9
      ctx.beginPath()
      ctx.ellipse(S.chest[0] + 30, S.chest[1] - 16, 26, 17, -0.25, 0, TAU)
      ctx.ellipse(S.hip[0] - 20, S.hip[1] - 8, 30, 20, 0.2, 0, TAU)
      ctx.fillStyle = k.patch || k.dark
      ctx.fill()
      ctx.restore()
    }

    // neck + head
    const headBase = [S.head[0] + 26, S.head[1] + 40]
    tube(ctx, [[S.chest[0] - 6, S.chest[1] - 12], [S.chest[0] - 22, S.chest[1] - 38], headBase], [26, 22, 18], k.fur)
    drawQuadHead(ctx, S, k, pose)
    for (const key of ['fl', 'bl']) drawQuadLeg(ctx, S.legs[key], k, false)
    if (k.collar) drawCollar(ctx, S, k)
    if (skeleton) drawQuadSkeleton(ctx, S)
  }

  function drawQuadLeg(ctx, leg, k, far) {
    const fill = far ? k.dark : k.fur
    const r = leg.far ? 0.92 : 1
    tube(ctx, [leg.root, leg.knee, leg.paw], [16 * r, 10, 8], fill)
    ctx.beginPath()
    ctx.ellipse(leg.paw[0] + 6, leg.paw[1] + 2, 14, 7.5, 0, 0, TAU)
    fillStroke(ctx, far ? k.dark : k.light, INK, 2.6)
    ctx.beginPath()
    ctx.moveTo(leg.paw[0] + 12, leg.paw[1] + 2)
    ctx.lineTo(leg.paw[0] + 18, leg.paw[1] + 3)
    ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.stroke()
  }

  function drawTail(ctx, S, k, pose) {
    const base = [S.hip[0] + 30, S.hip[1] - 26]
    const tailA = (S.fk && S.fk.tail ? S.fk.tail : 0) * DEG
    const ctrl = (p) => rotPt(p, base, tailA)
    const wag = Math.sin(S.phase * 1.5) * 4 + (pose === 'wag' ? Math.sin(S.phase * 3) * 10 : 0)
    if (k.tail === 'curl') {
      ctx.beginPath()
      for (let a = 0; a < 5.4; a += 0.18) {
        const r = 17 * (1 - a / 6.4)
        const x = base[0] + 16 + Math.cos(a) * r
        const y = base[1] - 12 + Math.sin(a) * r
        if (a === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
      }
      ctx.strokeStyle = INK; ctx.lineWidth = 10; ctx.lineCap = 'round'; ctx.stroke()
      ctx.strokeStyle = k.fur; ctx.lineWidth = 6; ctx.stroke()
      return
    }
    if (k.tail === 'long') {
      taperedTail(ctx, base, ctrl([base[0] + 52, base[1] - 96 + wag]), ctrl([base[0] + 96, base[1] + 4 + wag]), k.tailW, 5, k.fur)
    } else {
      taperedTail(ctx, base, ctrl([base[0] + 2, base[1] - 66 + wag]), ctrl([base[0] + 52, base[1] - 86 + wag]), k.tailW, 6, k.fur)
    }
  }

  function drawQuadHead(ctx, S, k, pose) {
    const [hx, hy] = S.head
    const r = k.headR
    const tilt = (pose === 'bark' ? -12 : pose === 'sit' ? -4 : 0) + (S.headRot || 0)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate((tilt + S.dy * 0.02) * DEG)

    if (k.ears === 'flop') {
      for (const s of [-1, 1]) {
        ctx.save()
        ctx.translate(s * 16, -r + 8)
        ctx.rotate(s * 0.22)
        rr(ctx, -12, 0, 24, 54, 12)
        fillStroke(ctx, k.dark, INK, 3)
        ctx.restore()
      }
    } else {
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(s * 6, -r + 8)
        ctx.lineTo(s * 20, -r - 28)
        ctx.lineTo(s * 30, -r + 6)
        ctx.closePath()
        fillStroke(ctx, k.dark, INK, 3)
      }
    }

    if (k.horns) {
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(s * 14, -r + 2)
        ctx.quadraticCurveTo(s * 30, -r - 18, s * 12, -r - 22)
        ctx.quadraticCurveTo(s * 22, -r - 6, s * 6, -r + 2)
        ctx.closePath()
        fillStroke(ctx, '#e8dcc0', INK, 2.4)
      }
    }
    // skull
    ctx.beginPath()
    ctx.ellipse(0, 0, r + 5, r, -0.05, 0, TAU)
    fillStroke(ctx, k.fur, INK, 3.2)
    // cheek
    ctx.beginPath()
    ctx.ellipse(-4, 10, r * 0.8, r * 0.72, 0.1, 0, TAU)
    ctx.fillStyle = k.light; ctx.globalAlpha = 0.35; ctx.fill(); ctx.globalAlpha = 1
    // muzzle
    const sn = k.snout
    ctx.beginPath()
    ctx.ellipse(-r - 10 * sn, 10, 22 * sn, 13 * sn, -0.12, 0, TAU)
    fillStroke(ctx, k.light, INK, 2.8)
    // nose
    ctx.beginPath()
    ctx.ellipse(-r - 27 * sn, 6, 6.5, 5, -0.2, 0, TAU)
    ctx.fillStyle = k.nose; ctx.fill()
    if (k.pigNose) {
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.ellipse(-r - 30 * sn + s * 5, 7, 1.8, 3, 0, 0, TAU)
        ctx.fillStyle = 'rgba(60,30,30,.65)'; ctx.fill()
      }
    }
    // mouth
    ctx.beginPath()
    ctx.moveTo(-r - 8 * sn, 19)
    ctx.quadraticCurveTo(-r + 2, 26, -r + 12, 22)
    ctx.strokeStyle = INK; ctx.lineWidth = 2.4; ctx.stroke()
    // eye
    ctx.beginPath()
    ctx.ellipse(-2, -9, 8.5, 9.5, 0, 0, TAU)
    fillStroke(ctx, '#f8f1e2', INK, 2.4)
    ctx.beginPath()
    ctx.arc(-4, -8, 4.4, 0, TAU)
    ctx.fillStyle = k.eye; ctx.fill()
    ctx.beginPath()
    ctx.arc(-5.6, -10, 1.5, 0, TAU)
    ctx.fillStyle = '#fff'; ctx.fill()
    // brow
    ctx.beginPath()
    ctx.moveTo(-12, -20)
    ctx.quadraticCurveTo(-2, -25, 8, -19)
    ctx.strokeStyle = k.dark; ctx.lineWidth = 3.2; ctx.lineCap = 'round'; ctx.stroke()
    ctx.restore()
  }

  function drawCollar(ctx, S, k) {
    const p = [S.chest[0] - 16, S.chest[1] - 30]
    ctx.save()
    ctx.translate(p[0], p[1])
    ctx.rotate(-0.5)
    rr(ctx, -18, -7, 36, 14, 6)
    fillStroke(ctx, k.collar, INK, 2.4)
    ctx.beginPath()
    ctx.arc(14, 4, 4, 0, TAU)
    ctx.fillStyle = '#f3d27a'; ctx.fill()
    ctx.strokeStyle = INK; ctx.lineWidth = 1.6; ctx.stroke()
    ctx.restore()
  }

  function drawQuadSkeleton(ctx, S) {
    ctx.save()
    ctx.globalAlpha = 0.9
    ctx.strokeStyle = '#69d6ff'; ctx.fillStyle = '#69d6ff'; ctx.lineWidth = 2
    for (const key of Object.keys(S.legs)) {
      const L = S.legs[key]
      ctx.beginPath(); ctx.moveTo(L.root[0], L.root[1]); ctx.lineTo(L.knee[0], L.knee[1]); ctx.lineTo(L.paw[0], L.paw[1]); ctx.stroke()
      for (const p of [L.root, L.knee, L.paw]) { ctx.beginPath(); ctx.arc(p[0], p[1], 3.5, 0, TAU); ctx.fill() }
    }
    ctx.beginPath(); ctx.moveTo(S.chest[0], S.chest[1]); ctx.lineTo(S.hip[0], S.hip[1])
    ctx.moveTo(S.chest[0], S.chest[1]); ctx.lineTo(S.head[0], S.head[1]); ctx.stroke()
    for (const p of [S.chest, S.hip, S.head]) { ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, TAU); ctx.fill() }
    ctx.restore()
  }

  // ── bird ─────────────────────────────────────────────────────────────────
  function birdJoints(kind, pose, t, gait, seed, fkIn) {
    const k = KINDS[kind]
    const fk = fkIn || {}
    const phase = (t / 1000) * TAU + seed
    let body = (k.bodyC || [312, 326]).slice()
    let head = (k.headC || [416, 222]).slice()
    let headRot = -0.05
    let wing = 0
    let hop = 0
    let footLift = 0
    let neck = null

    if (pose === 'peck') {
      body = [k.bodyC ? k.bodyC[0] : 312, (k.bodyC ? k.bodyC[1] : 326) + 14]
      head = [head[0] + 44, head[1] + 140]
      headRot = 1.05
      neck = [[body[0] + 42, body[1] - 30], [head[0] - 26, head[1] - 40], [head[0] - 6, head[1] - 12]]
    } else if (pose === 'flap') {
      wing = 0.95 + Math.sin(phase * 5) * 0.45
      hop = Math.abs(Math.sin(phase * 5)) * 26
      footLift = Math.min(46, hop * 1.4)
      body = [body[0], body[1] - hop]
      head = [head[0], head[1] - hop * 0.7]
    }
    if (gait === 'walk' || gait === 'run') {
      const sp = gait === 'run' ? 1.9 : 1
      const step = Math.abs(Math.sin(phase * 2 * sp)) * (gait === 'run' ? 9 : 5)
      body = [body[0], body[1] - step]
      head = [head[0], head[1] - step]
    } else if (pose !== 'fly' && pose !== 'peck') {
      const idle = Math.sin((t / 1000) * 1.8 + seed) * 1.8
      body = [body[0], body[1] + idle]
      head = [head[0], head[1] + idle * 1.1]
    }
    if (fk.neck) head = rotPt(head, body, fk.neck * DEG)
    headRot += (fk.head || 0) * DEG
    wing += (fk.wing || 0) * DEG
    return { k, body, head, headRot, wing, hop, footLift, neck, phase, pose, gait, peck: pose === 'peck', fk }
  }

  function drawBird(ctx, kind, pose, t, gait, seed, skeleton, fk) {
    const S = birdJoints(kind, pose, t, gait, seed, fk)
    const k = S.k
    const [bx, by] = S.body
    const [hx, hy] = S.head

    ctx.save()
    ctx.globalAlpha = 0.14
    ctx.beginPath()
    ctx.ellipse(bx + 30, 548, 96, 12, 0, 0, TAU)
    ctx.fillStyle = '#10121b'; ctx.filter = 'blur(3px)'; ctx.fill()
    ctx.restore()

    // far leg
    drawBirdLeg(ctx, [bx - 28, by + 46], k, true, S, S.phase + Math.PI)

    // tail wedge
    ctx.beginPath()
    ctx.moveTo(bx - 58, by - 22)
    ctx.quadraticCurveTo(bx - 128, by - 58, bx - 158, by - 6)
    ctx.quadraticCurveTo(bx - 120, by + 34, bx - 62, by + 22)
    ctx.closePath()
    fillStroke(ctx, k.tail, INK, 3.2)
    ctx.beginPath()
    ctx.moveTo(bx - 72, by - 4); ctx.quadraticCurveTo(bx - 120, by - 18, bx - 146, by - 2)
    ctx.strokeStyle = k.wingDark; ctx.lineWidth = 3; ctx.stroke()

    // body
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(-0.14 + (S.peck ? 0.2 : 0))
    const br = k.bodyR || [84, 62]
    ctx.beginPath()
    ctx.ellipse(0, 0, br[0], br[1], 0, 0, TAU)
    fillStroke(ctx, k.body, INK, 3.4)
    ctx.beginPath()
    ctx.ellipse(16, 14, 62, 40, 0.1, 0, TAU)
    ctx.fillStyle = k.bodyDark; ctx.globalAlpha = 0.4; ctx.fill(); ctx.globalAlpha = 1
    ctx.restore()

    // neck
    if (S.neck) tube(ctx, S.neck, [22, 18, 14], k.body)
    else tube(ctx, [
      [bx + 44, by - 24],
      [(bx + hx) / 2 + 12, (by + hy) / 2],
      [hx - 16, hy + 14],
    ], [22, 18, 14], k.body)

    // wing (behind head, in front of body)
    drawBirdWing(ctx, S, k)

    // head
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(S.headRot)
    ctx.beginPath()
    ctx.ellipse(0, 0, 29, 27, 0, 0, TAU)
    fillStroke(ctx, k.headColor || k.body, INK, 3)
    // comb
    if (k.comb) {
      ctx.beginPath()
      ctx.moveTo(-14, -22)
      ctx.quadraticCurveTo(-18, -44, -5, -36)
      ctx.quadraticCurveTo(0, -50, 8, -36)
      ctx.quadraticCurveTo(18, -46, 17, -22)
      ctx.closePath()
      fillStroke(ctx, k.comb, INK, 2.6)
    }
    // beak
    ctx.beginPath()
    ctx.moveTo(24, -6)
    ctx.lineTo(56, 2)
    if (k.beakHook) {
      ctx.quadraticCurveTo(52, 14, 44, 12)
      ctx.lineTo(24, 11)
    } else {
      ctx.lineTo(24, 11)
    }
    ctx.closePath()
    fillStroke(ctx, k.beak, INK, 2.4)
    // wattle
    if (k.wattle) {
      ctx.beginPath()
      ctx.ellipse(26, 18, 8, 12, 0.15, 0, TAU)
      fillStroke(ctx, k.wattle, INK, 2.2)
    }
    // eye (light ring for dark/white heads)
    ctx.beginPath()
    ctx.arc(8, -8, k.headColor ? 7.2 : 5.2, 0, TAU)
    ctx.fillStyle = k.headColor ? '#f4ede0' : k.eye
    ctx.fill()
    ctx.beginPath()
    ctx.arc(8, -8, 5.2, 0, TAU)
    ctx.fillStyle = k.eye; ctx.fill()
    ctx.beginPath()
    ctx.arc(9.6, -9.6, 1.6, 0, TAU)
    ctx.fillStyle = '#fff'; ctx.fill()
    ctx.restore()

    // near leg
    drawBirdLeg(ctx, [bx + 2, by + 48], k, false, S, S.phase)
    if (skeleton) drawBirdSkeleton(ctx, S)
  }

  function drawBirdWing(ctx, S, k) {
    const [bx, by] = S.body
    ctx.save()
    ctx.translate(bx + 18, by - 10)
    const ws = k.wingScale || 1
    ctx.scale(ws, ws)
    ctx.rotate(S.wing + 0.08)
    // a wing points back towards the tail; in flap it swings up
    ctx.beginPath()
    ctx.moveTo(36, -10)
    ctx.quadraticCurveTo(4, -46, -46, -34)
    ctx.quadraticCurveTo(-92, -22, -112, 4)
    ctx.quadraticCurveTo(-68, 32, -10, 38)
    ctx.quadraticCurveTo(28, 32, 36, -10)
    ctx.closePath()
    fillStroke(ctx, k.wing, INK, 3.2)
    // feather tips
    ctx.beginPath()
    ctx.moveTo(-112, 4)
    ctx.quadraticCurveTo(-86, 12, -62, 18)
    ctx.moveTo(-104, -8)
    ctx.quadraticCurveTo(-78, -2, -56, 6)
    ctx.strokeStyle = k.wingDark
    ctx.lineWidth = 2.6
    ctx.globalAlpha = 0.8
    ctx.stroke()
    ctx.globalAlpha = 1
    // shoulder seam
    ctx.beginPath()
    ctx.moveTo(30, -6)
    ctx.quadraticCurveTo(-10, -20, -46, -20)
    ctx.strokeStyle = INK
    ctx.lineWidth = 2.2
    ctx.globalAlpha = 0.35
    ctx.stroke()
    ctx.globalAlpha = 1
    ctx.restore()
  }

  function drawBirdLeg(ctx, root, k, far, S, phase) {
    const sp = S.gait === 'run' ? 1.9 : 1
    const step = S.gait ? Math.sin(phase * sp) * (S.gait === 'run' ? 20 : 13) : 0
    const lift = S.gait && Math.sin(phase * sp) > 0 ? Math.sin(phase * sp) * (S.gait === 'run' ? 14 : 8) : 0
    const foot = [root[0] + 4 + step, 540 - lift - S.footLift]
    // bird ankle bends backwards: root -> hock -> foot
    const hock = [root[0] - 14 + step * 0.3, 452 - S.footLift * 0.55]
    tube(ctx, [root, hock, foot], [10, 7, 5.5], far ? k.legDark : k.leg, 2.6)
    // feathered thigh
    ctx.beginPath()
    ctx.ellipse(root[0] - 2, root[1] + 2, 15, 18, -0.2, 0, TAU)
    ctx.fillStyle = k.body
    ctx.fill()
    // toes
    const fy = foot[1] + 2
    ctx.beginPath()
    ctx.moveTo(foot[0] - 15, fy)
    ctx.quadraticCurveTo(foot[0], fy + 6, foot[0] + 17, fy)
    ctx.moveTo(foot[0], fy); ctx.lineTo(foot[0] - 5, fy + 8)
    ctx.moveTo(foot[0], fy); ctx.lineTo(foot[0] + 9, fy + 7)
    ctx.strokeStyle = INK
    ctx.lineWidth = 3.4
    ctx.lineCap = 'round'
    ctx.stroke()
  }

  function drawBirdSkeleton(ctx, S) {
    ctx.save()
    ctx.globalAlpha = 0.9
    ctx.strokeStyle = '#69d6ff'; ctx.fillStyle = '#69d6ff'; ctx.lineWidth = 2
    const [bx, by] = S.body
    for (const [a, b] of [[[bx, by], S.head], [[bx, by], [bx - 20, by + 52]], [[bx, by], [bx + 2, by + 48]]]) {
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke()
    }
    for (const p of [S.body, S.head]) { ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, TAU); ctx.fill() }
    ctx.restore()
  }

  // ── insects (6 legs, elytra/wings) ───────────────────────────────────────
  const INSECT_PHASE = [0, Math.PI, Math.PI * 0.5, Math.PI * 1.5, Math.PI, 0]

  function insectJoints(kind, pose, t, gait, seed, fkIn) {
    const k = KINDS[kind]
    const fk = fkIn || {}
    const phase = (t / 1000) * TAU + seed
    let body = [318, 352]
    let head = [228, 338]
    let lift = 0
    let wing = 0
    if (pose !== 'fly' && gait !== 'fly') {
      const idle = Math.sin((t / 1000) * 1.9 + seed) * 1.4
      body = [body[0], body[1] + idle]
      head = [head[0], head[1] + idle]
    }
    if (pose === 'fly') {
      lift = 44
      body = [body[0], body[1] - lift]
      head = [head[0], head[1] - lift]
      wing = Math.sin(phase * 12) * 0.7
    } else if (gait === 'fly') {
      lift = 36 + Math.sin(phase * 3) * 6
      body = [body[0], body[1] - lift]
      head = [head[0], head[1] - lift]
      wing = Math.sin(phase * 12) * 0.7
    }
    const walking = gait === 'walk' && pose !== 'fly'
    const legs = []
    for (let i = 0; i < 6; i++) {
      const far = i % 2 === 1
      const rootX = 262 + Math.floor(i / 2) * 38 + (far ? 8 : 0)
      const p = phase + INSECT_PHASE[i]
      const step = walking ? Math.sin(p) * 16 : 0
      const up = walking && Math.sin(p) > 0 ? Math.sin(p) * 14 : 0
      const root = [rootX, body[1] + 22]
      const foot = [rootX + 20 + step, 540 - up - lift * 0.55]
      legs.push({
        root,
        knee: [root[0] + 16, (root[1] + foot[1]) / 2],
        foot,
        far,
      })
    }
    const neckA = (fk.neck || 0) * DEG
    if (neckA) head = rotPt(head, body, neckA)
    for (let i = 0; i < legs.length; i++) {
      const L = legs[i]
      const hipA = (fk['l' + (i + 1) + 'Hip'] || 0) * DEG
      if (hipA) {
        L.knee = rotPt(L.knee, L.root, hipA)
        L.foot = rotPt(L.foot, L.root, hipA)
      }
      const kneeA = (fk['l' + (i + 1) + 'Knee'] || 0) * DEG
      if (kneeA) L.foot = rotPt(L.foot, L.knee, kneeA)
    }
    return { k, body, head, legs, phase, lift, wing, fk, headRot: (fk.head || 0), flying: pose === 'fly' || gait === 'fly' }
  }

  function drawInsect(ctx, kind, pose, t, gait, seed, skeleton, fk) {
    const S = insectJoints(kind, pose, t, gait, seed, fk)
    const k = S.k
    const [bx, by] = S.body
    const [hx, hy] = S.head
    const ar = k.abdomenR

    ctx.save()
    ctx.globalAlpha = 0.14
    ctx.beginPath()
    ctx.ellipse(bx + 30, 548, 110, 12, 0, 0, TAU)
    ctx.fillStyle = '#10121b'; ctx.filter = 'blur(3px)'; ctx.fill()
    ctx.restore()

    // far legs
    for (const L of S.legs) if (L.far) drawInsectLeg(ctx, L, k, true)
    // abdomen
    ctx.beginPath()
    ctx.ellipse(bx + 52, by + 6, ar[0], ar[1], -0.08, 0, TAU)
    fillStroke(ctx, k.shell, INK, 3.2)
    if (k.stripe) {
      ctx.save()
      ctx.beginPath()
      ctx.ellipse(bx + 52, by + 6, ar[0], ar[1], -0.08, 0, TAU)
      ctx.clip()
      for (let i = -2; i <= 2; i++) {
        ctx.beginPath()
        ctx.ellipse(bx + 52 + i * 26, by + 6, 7, ar[1], 0, 0, TAU)
        ctx.fillStyle = k.stripe
        ctx.fill()
      }
      ctx.restore()
    } else {
      // beetle elytra seam + shine
      ctx.beginPath()
      ctx.moveTo(bx + 18, by - 32)
      ctx.quadraticCurveTo(bx + 54, by - 44, bx + 92, by - 12)
      ctx.strokeStyle = k.shellLight
      ctx.lineWidth = 4
      ctx.globalAlpha = 0.6
      ctx.stroke()
      ctx.globalAlpha = 1
      ctx.beginPath()
      ctx.moveTo(bx + 34, by - 30)
      ctx.quadraticCurveTo(bx + 52, by - 6, bx + 46, by + 30)
      ctx.strokeStyle = 'rgba(0,0,0,.35)'
      ctx.lineWidth = 2.4
      ctx.stroke()
    }
    // thorax
    ctx.beginPath()
    ctx.ellipse(bx - 26, by - 2, k.thoraxR, k.thoraxR * 0.86, -0.1, 0, TAU)
    fillStroke(ctx, k.shell, INK, 3)
    // head
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate((S.headRot || 0) * DEG)
    ctx.beginPath()
    ctx.ellipse(0, 0, k.headR, k.headR * 0.92, 0, 0, TAU)
    fillStroke(ctx, k.body, INK, 3)
    for (const s of [-1, 1]) {
      ctx.beginPath()
      ctx.moveTo(14, -8 + s * 6)
      ctx.quadraticCurveTo(46, -26 + s * 10, 58, -34 + s * 12)
      ctx.strokeStyle = INK
      ctx.lineWidth = 3
      ctx.lineCap = 'round'
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(58, -34 + s * 12, 3, 0, TAU)
      ctx.fillStyle = k.accent
      ctx.fill()
    }
    ctx.beginPath()
    ctx.arc(4, -4, 7, 0, TAU)
    ctx.fillStyle = '#f4ede0'; ctx.fill()
    ctx.beginPath()
    ctx.arc(6, -4, 4.4, 0, TAU)
    ctx.fillStyle = k.eye; ctx.fill()
    ctx.restore()
    // wings / elytra
    if (k.stripe) {
      // bee: two translucent wings, flap with time
      ctx.save()
      ctx.translate(bx - 4, by - 20)
      ctx.rotate(-0.25 + S.wing)
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.ellipse(10, s * 14, 54, 20, s * 0.25, 0, TAU)
        ctx.fillStyle = k.wing
        ctx.globalAlpha = 0.55
        ctx.fill()
        ctx.globalAlpha = 1
        ctx.strokeStyle = INK
        ctx.lineWidth = 2
        ctx.stroke()
      }
      ctx.restore()
      // stinger
      ctx.beginPath()
      ctx.moveTo(bx + ar[0] + 30, by + 14)
      ctx.lineTo(bx + ar[0] + 52, by + 18)
      ctx.lineTo(bx + ar[0] + 30, by + 22)
      ctx.closePath()
      fillStroke(ctx, k.body, INK, 2)
    } else {
      // beetle: elytra slightly open in flight
      const open = S.flying ? 0.22 : 0
      for (const s of [-1, 1]) {
        ctx.save()
        ctx.translate(bx + 24, by - 8)
        ctx.rotate(-0.1 + s * open)
        ctx.beginPath()
        ctx.ellipse(30, 0, 58, 30, 0, 0, TAU)
        fillStroke(ctx, k.shell, INK, 2.6)
        ctx.restore()
      }
    }
    // near legs
    for (const L of S.legs) if (!L.far) drawInsectLeg(ctx, L, k, false)
    if (skeleton) drawInsectSkeleton(ctx, S)
  }

  function drawInsectLeg(ctx, L, k, far) {
    const root = L.root
    const foot = L.foot
    const knee = L.knee
    tube(ctx, [root, knee, foot], [8, 6, 4.5], far ? k.body : k.leg, 2.2)
    ctx.beginPath()
    ctx.moveTo(foot[0] - 9, foot[1] + 2)
    ctx.lineTo(foot[0] + 9, foot[1] + 2)
    ctx.strokeStyle = INK
    ctx.lineWidth = 2.6
    ctx.stroke()
  }

  function drawInsectSkeleton(ctx, S) {
    ctx.save()
    ctx.globalAlpha = 0.9
    ctx.strokeStyle = '#69d6ff'; ctx.fillStyle = '#69d6ff'; ctx.lineWidth = 2
    ctx.beginPath(); ctx.moveTo(S.body[0], S.body[1]); ctx.lineTo(S.head[0], S.head[1]); ctx.stroke()
    for (const L of S.legs) {
      ctx.beginPath(); ctx.moveTo(L.root[0], L.root[1]); ctx.lineTo(L.knee[0], L.knee[1]); ctx.lineTo(L.foot[0], L.foot[1]); ctx.stroke()
      for (const p of [L.root, L.knee, L.foot]) { ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, TAU); ctx.fill() }
    }
    for (const p of [S.body, S.head]) { ctx.beginPath(); ctx.arc(p[0], p[1], 5, 0, TAU); ctx.fill() }
    ctx.restore()
  }

  // Joint positions for authoring tools (no drawing side effects).
  function skeleton(kind, pose, t, gait, seed, fk) {
    const k = KINDS[kind]
    if (!k) return { family: null, joints: {}, legs: {} }
    if (k.family === 'quadruped') {
      const S = quadJoints(kind, pose, t, gait, seed || 0, fk || {})
      const neck = [(S.chest[0] + S.head[0]) / 2, (S.chest[1] + S.head[1]) / 2]
      return {
        family: 'quadruped',
        joints: { chest: S.chest, hip: S.hip, head: S.head, neck, tail: [S.hip[0] + 30, S.hip[1] - 26] },
        legs: S.legs,
      }
    }
    if (k.family === 'avian') {
      const S = birdJoints(kind, pose, t, gait, seed || 0, fk || {})
      return {
        family: 'avian',
        joints: {
          body: S.body, head: S.head,
          neck: [(S.body[0] + S.head[0]) / 2, (S.body[1] + S.head[1]) / 2],
          wing: [S.body[0] - 54, S.body[1] - 22],
        },
        legs: {},
      }
    }
    if (k.family === 'insectoid') {
      const S = insectJoints(kind, pose, t, gait, seed || 0, fk || {})
      const legs = {}
      S.legs.forEach((L, i) => { legs['l' + (i + 1)] = L })
      return {
        family: 'insectoid',
        joints: {
          body: S.body, head: S.head,
          neck: [(S.body[0] + S.head[0]) / 2, (S.body[1] + S.head[1]) / 2],
        },
        legs,
      }
    }
    return { family: null, joints: {}, legs: {} }
  }

  // ── factory ──────────────────────────────────────────────────────────────
  function create(canvas, opts) {
    const o = opts || {}
    const ctx = canvas.getContext('2d')
    const state = {
      kind: KINDS[o.kind] ? o.kind : 'dog',
      pose: o.pose || 'stand',
      gait: o.gait || null,
      time: 0,
      seed: Number(o.seed) || 0,
      palette: Object.assign({}, o.palette || {}),
      showSkeleton: !!o.showSkeleton,
      fk: Object.assign({}, o.fk || {}),
    }
    let lastFrame = null

    function kindCfg() {
      return Object.assign({}, KINDS[state.kind], state.palette)
    }

    function draw(t) {
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      const cw = Math.max(1, Math.round((rect.width || canvas.width) * dpr))
      const ch = Math.max(1, Math.round((rect.height || canvas.height) * dpr))
      if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch }
      const scale = Math.min(cw / 600, ch / 600)
      const ox = (cw - 600 * scale) / 2
      const oy = (ch - 600 * scale) / 2
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, cw, ch)
      ctx.setTransform(scale, 0, 0, scale, ox, oy)
      ctx.lineJoin = 'round'
      ctx.lineCap = 'round'
      const k = kindCfg()
      if (k.family === 'quadruped') drawQuad(ctx, state.kind, state.pose, t, state.gait, state.seed, state.showSkeleton, state.fk)
      else if (k.family === 'insectoid') drawInsect(ctx, state.kind, state.pose, t, state.gait, state.seed, state.showSkeleton, state.fk)
      else drawBird(ctx, state.kind, state.pose, t, state.gait, state.seed, state.showSkeleton, state.fk)
      lastFrame = t
    }

    function seek(t) { state.time = Number(t) || 0; draw(state.time) }
    function setKind(kind) { if (!KINDS[kind]) return false; state.kind = kind; draw(state.time); return true }
    function setPose(name) { state.pose = name; draw(state.time); return true }
    function setGait(name) { state.gait = name || null; draw(state.time); return state.gait }
    function setPalette(p) { Object.assign(state.palette, p || {}); draw(state.time) }
    function setSkeleton(on) { state.showSkeleton = !!on; draw(state.time) }
    function setFK(patch) { Object.assign(state.fk, patch || {}); draw(state.time) }
    function resetFK() { state.fk = {}; draw(state.time) }

    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => draw(state.time)) : null
    if (ro) ro.observe(canvas)
    draw(0)

    return {
      ready: Promise.resolve(true),
      seek, setKind, setPose, setGait, setPalette, setSkeleton, setFK, resetFK,
      getState: () => ({ kind: state.kind, pose: state.pose, gait: state.gait, time: state.time, fk: Object.assign({}, state.fk), lastFrame }),
      destroy() {
        if (ro) ro.disconnect()
        ctx.setTransform(1, 0, 0, 1, 0, 0)
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      },
    }
  }

  window.PaperCastAnimals = {
    create,
    skeleton,
    KINDS,
    POSES: {
      dog: ['stand', 'sit', 'lie', 'bark', 'wag'],
      cat: ['stand', 'sit', 'lie', 'bark', 'wag'],
      pig: ['stand', 'sit', 'lie', 'bark', 'wag'],
      cow: ['stand', 'sit', 'lie', 'bark', 'wag'],
      eagle: ['stand', 'peck', 'flap'],
      tit: ['stand', 'peck', 'flap'],
      beetle: ['stand', 'fly'],
      bee: ['stand', 'fly'],
      chicken: ['stand', 'peck', 'flap'],
      dove: ['stand', 'peck', 'flap'],
    },
    GAITS: ['walk', 'run', 'fly'],
    INK,
  }
})()
