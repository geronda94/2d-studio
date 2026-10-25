/* SceneClip — pure evaluation of authored *.sclip.json clips.
 *
 * Deterministic: value(t) depends only on the clip data. No clocks, no DOM.
 * Used by the browser Clip Editor and (next) by the canonical runtime driver.
 *
 * Quaternions are arrays [x, y, z, w]; keys are [time, ...value].
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory()
  else root.SceneClip = factory()
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict'

  function qMul(a, b) {
    var ax = a[0], ay = a[1], az = a[2], aw = a[3]
    var bx = b[0], by = b[1], bz = b[2], bw = b[3]
    return [
      aw * bx + ax * bw + ay * bz - az * by,
      aw * by - ax * bz + ay * bw + az * bx,
      aw * bz + ax * by - ay * bx + az * bw,
      aw * bw - ax * bx - ay * by - az * bz,
    ]
  }

  function qNorm(a) {
    var l = Math.hypot(a[0], a[1], a[2], a[3]) || 1
    return [a[0] / l, a[1] / l, a[2] / l, a[3] / l]
  }

  function qSlerp(a, b, t) {
    var bx = b[0], by = b[1], bz = b[2], bw = b[3]
    var d = a[0] * bx + a[1] * by + a[2] * bz + a[3] * bw
    if (d < 0) { bx = -bx; by = -by; bz = -bz; bw = -bw; d = -d }
    if (d > 0.9995) {
      return qNorm([
        a[0] + (bx - a[0]) * t,
        a[1] + (by - a[1]) * t,
        a[2] + (bz - a[2]) * t,
        a[3] + (bw - a[3]) * t,
      ])
    }
    var theta0 = Math.acos(Math.max(-1, Math.min(1, d)))
    var theta = theta0 * t
    var sin0 = Math.sin(theta0)
    var s0 = Math.sin(theta0 - theta) / sin0
    var s1 = Math.sin(theta) / sin0
    return qNorm([
      a[0] * s0 + bx * s1,
      a[1] * s0 + by * s1,
      a[2] * s0 + bz * s1,
      a[3] * s0 + bw * s1,
    ])
  }

  function qFromEuler(x, y, z) {
    var qx = [Math.sin(x / 2), 0, 0, Math.cos(x / 2)]
    var qy = [0, Math.sin(y / 2), 0, Math.cos(y / 2)]
    var qz = [0, 0, Math.sin(z / 2), Math.cos(z / 2)]
    return qNorm(qMul(qMul(qy, qx), qz))
  }

  function lerp(a, b, t) {
    var out = new Array(a.length)
    for (var i = 0; i < a.length; i++) out[i] = a[i] + (b[i] - a[i]) * t
    return out
  }

  function sorted(keys) {
    return keys.slice().sort(function (a, b) { return a[0] - b[0] })
  }

  function trackValue(keys, time, isQuat) {
    if (!keys || !keys.length) return null
    var list = sorted(keys)
    if (time <= list[0][0]) return list[0].slice(1)
    if (time >= list[list.length - 1][0]) return list[list.length - 1].slice(1)
    for (var i = 0; i < list.length - 1; i++) {
      var t0 = list[i][0], t1 = list[i + 1][0]
      if (time >= t0 && time <= t1) {
        var a = list[i].slice(1), b = list[i + 1].slice(1)
        if (t1 - t0 < 1e-9) return a
        var u = (time - t0) / (t1 - t0)
        return isQuat ? qSlerp(a, b, u) : lerp(a, b, u)
      }
    }
    return list[list.length - 1].slice(1)
  }

  /**
   * Evaluate a clip at time (seconds).
   * rest: { bone: [x,y,z,w] } used for bones without rotation keys.
   * Returns { bones: { name: { rotation, translation?, scale? } }, face: { morph: weight } }.
   */
  function evaluate(clip, time, rest) {
    var out = { bones: {}, face: {} }
    var tracks = (clip && clip.tracks) || {}
    for (var bone in tracks) {
      if (!Object.prototype.hasOwnProperty.call(tracks, bone)) continue
      var chans = tracks[bone] || {}
      var rec = {}
      var rot = trackValue(chans.rotation, time, true)
      if (rot) rec.rotation = rot
      else if (rest && rest[bone]) rec.rotation = rest[bone].slice()
      var tr = trackValue(chans.translation, time, false)
      if (tr) rec.translation = tr
      var sc = trackValue(chans.scale, time, false)
      if (sc) rec.scale = sc
      out.bones[bone] = rec
    }
    if (rest) {
      for (var name in rest) {
        if (!Object.prototype.hasOwnProperty.call(rest, name)) continue
        if (!out.bones[name]) out.bones[name] = { rotation: rest[name].slice() }
      }
    }
    var face = (clip && clip.face) || {}
    for (var morph in face) {
      if (!Object.prototype.hasOwnProperty.call(face, morph)) continue
      var v = trackValue(face[morph], time, false)
      if (v) out.face[morph] = v[0]
    }
    return out
  }

  function eventsAt(clip, time) {
    var out = []
    var list = (clip && clip.events) || []
    for (var i = 0; i < list.length; i++) {
      if (list[i] && typeof list[i].t === 'number' && list[i].t <= time + 1e-9) {
        if (!list[i].fired) out.push(list[i])
      }
    }
    return out
  }

  function duration(clip) {
    return Math.max(0, Number(clip && clip.duration) || 0)
  }

  return {
    qMul: qMul,
    qNorm: qNorm,
    qSlerp: qSlerp,
    qFromEuler: qFromEuler,
    lerp: lerp,
    trackValue: trackValue,
    evaluate: evaluate,
    eventsAt: eventsAt,
    duration: duration,
  }
})
