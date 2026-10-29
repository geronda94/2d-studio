/* Paper Cast visual library — thumbnail previews for appearance/wardrobe.
 *
 * One offscreen rig renders every variant once; results are cropped and
 * cached (memory + sessionStorage). Builder asks for a thumb and gets a
 * dataURL when it is ready.
 */
(function () {
  'use strict'
  const BASE = {
    hairStyle: 'short', beardStyle: 'none', faceShape: 'oval',
    noseStyle: 'straight', eyeStyle: 'round', browStyle: 'soft', lipStyle: 'full',
    glasses: false, glassesStyle: 'round',
    outfit: 'shirt', bottom: 'pants', sleeves: 'auto', pattern: 'solid', accessory: 'none',
  }
  const KEYS = {
    hair: 'hairStyle', beard: 'beardStyle', face: 'faceShape', nose: 'noseStyle',
    eye: 'eyeStyle', brow: 'browStyle', lip: 'lipStyle', glasses: 'glassesStyle',
    outfit: 'outfit', bottom: 'bottom', pattern: 'pattern', accessory: 'accessory',
  }
  const CROPS = {
    head: [0.23, 0.05, 0.54, 0.31],
    body: [0.24, 0.30, 0.52, 0.50],
    torso: [0.24, 0.30, 0.52, 0.30],
  }

  const mem = new Map()
  let storage = null
  try { storage = window.sessionStorage } catch (e) { storage = null }
  let storeKey = 'papercast.lib.v1'
  let loaded = false
  let cv = null
  let rig = null
  let out = null
  const queue = []
  let timer = 0

  function version() {
    const s = document.querySelector('script[src*="paper-cast.js?v="]')
    const m = s && s.getAttribute('src').match(/[?&]v=(\d+)/)
    return m ? m[1] : '0'
  }

  function loadStore() {
    if (loaded) return
    loaded = true
    storeKey = 'papercast.lib.v' + version()
    if (!storage) return
    try {
      const raw = storage.getItem(storeKey)
      if (!raw) return
      const data = JSON.parse(raw)
      for (const k of Object.keys(data)) if (typeof data[k] === 'string') mem.set(k, data[k])
    } catch (e) { /* ignore */ }
  }

  function saveStore() {
    if (!storage) return
    try {
      const data = {}
      for (const [k, v] of mem) data[k] = v
      storage.setItem(storeKey, JSON.stringify(data))
    } catch (e) { /* quota */ }
  }

  function ensure() {
    if (rig) return
    cv = document.createElement('canvas')
    cv.width = 600; cv.height = 900
    cv.style.cssText = 'position:fixed;left:-12000px;top:0;width:600px;height:900px'
    document.body.appendChild(cv)
    out = document.createElement('canvas')
    out.width = 160; out.height = 200
    rig = window.PaperCast.create(cv, { character: 'mark', pose: 'neutral', autoGaze: false, life: false, blink: false })
  }

  function appFor(kind, id) {
    const a = Object.assign({}, BASE)
    const key = KEYS[kind]
    if (!key) return a
    a[key] = id
    if (kind === 'beard') a.beard = id !== 'none'
    if (kind === 'glasses') a.glasses = true
    if (kind === 'outfit' && id === 'dress') a.bottom = 'dress'
    if (kind === 'bottom' && id === 'dress') a.outfit = 'dress'
    return a
  }

  function render(kind, id) {
    ensure()
    rig.setAppearance(appFor(kind, id))
    rig.setYaw(0)
    rig.setPose('neutral')
    rig.seek(900)
    const crop = kind === 'outfit' || kind === 'bottom' ? CROPS.body : kind === 'pattern' || kind === 'accessory' ? CROPS.torso : CROPS.head
    const c = out.getContext('2d')
    c.clearRect(0, 0, out.width, out.height)
    c.drawImage(cv,
      Math.round(cv.width * crop[0]), Math.round(cv.height * crop[1]),
      Math.round(cv.width * crop[2]), Math.round(cv.height * crop[3]),
      0, 0, out.width, out.height)
    return out.toDataURL('image/png')
  }

  function work() {
    timer = 0
    const item = queue.shift()
    if (!item) return
    const key = item.kind + ':' + item.id
    let url = mem.get(key)
    if (!url) {
      try { url = render(item.kind, item.id) } catch (e) { url = '' }
      if (url) mem.set(key, url)
    }
    if (url && item.cb) item.cb(url)
    if (queue.length) timer = setTimeout(work, 8)
    else setTimeout(saveStore, 400)
  }

  function thumb(kind, id, cb) {
    loadStore()
    const key = kind + ':' + id
    const cached = mem.get(key)
    if (cached) { if (cb) cb(cached); return cached }
    queue.push({ kind, id, cb })
    if (!timer) timer = setTimeout(work, 0)
    return null
  }

  window.PaperCastLibrary = { thumb, clear() { mem.clear(); if (storage) try { storage.removeItem(storeKey) } catch (e) {} } }
})()
