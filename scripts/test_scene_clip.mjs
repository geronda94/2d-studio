#!/usr/bin/env node
import assert from 'assert'
import '../core/public/vendor/scene-clip.js'
const Clip = globalThis.SceneClip

function near(a, b, eps = 1e-4) {
  assert.ok(Math.abs(a - b) <= eps, `${a} !~ ${b}`)
}

const q90 = Clip.qFromEuler(0, Math.PI / 2, 0)
near(q90[1], Math.SQRT1_2)
near(q90[3], Math.SQRT1_2)

const half = Clip.qSlerp([0, 0, 0, 1], q90, 0.5)
near(half[1], Math.sin(Math.PI / 8))
near(half[3], Math.cos(Math.PI / 8))

const track = [[0, 0, 0, 0, 1], [2, 0, Math.SQRT1_2, 0, Math.SQRT1_2]]
const before = Clip.trackValue(track, -1, true)
const mid = Clip.trackValue(track, 1, true)
const after = Clip.trackValue(track, 3, true)
near(before[3], 1)
near(mid[1], Math.sin(Math.PI / 8))
near(after[1], Math.SQRT1_2)

const clip = {
  format: 'sceneclip/1', name: 'test', fps: 30, duration: 2,
  tracks: { chest: { rotation: track } },
  face: { viseme_aa: [[0, 0], [1, 1], [2, 0]] },
}
const rest = { chest: [0, 0, 0, 1], head: [0, 0, 0, 1] }
const at0 = Clip.evaluate(clip, 0, rest)
assert.deepStrictEqual(at0.bones.chest.rotation, [0, 0, 0, 1])
assert.deepStrictEqual(at0.bones.head.rotation, [0, 0, 0, 1])
near(at0.face.viseme_aa, 0)
const at1 = Clip.evaluate(clip, 1, rest)
near(at1.bones.chest.rotation[1], Math.sin(Math.PI / 8))
near(at1.face.viseme_aa, 1)
const at15 = Clip.evaluate(clip, 1.5, rest)
near(at15.face.viseme_aa, 0.5)

const scalar = Clip.trackValue([[0, 0], [2, 1]], 0.5, false)
near(scalar[0], 0.25)
assert.strictEqual(Clip.duration(clip), 2)
console.log('scene-clip: 14 assertions OK')
