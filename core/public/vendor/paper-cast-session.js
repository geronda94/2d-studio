/* Paper Cast shared studio session.
 *
 * One character, one appearance and one pose across Character Lab,
 * Pose Studio, Builder and the 3D view. Pages read the session on load
 * and write it back on changes; `?char=` in the URL wins over storage.
 */
(function () {
  'use strict'
  const KEY = 'papercast.session.v1'
  const VERSION = 1
  const TAB = 'tab-' + Math.random().toString(36).slice(2, 10)

  function read() {
    try {
      const raw = localStorage.getItem(KEY)
      const data = raw ? JSON.parse(raw) : {}
      return data && typeof data === 'object' ? data : {}
    } catch (e) {
      return {}
    }
  }

  function clean(obj) {
    const o = Object.assign({}, obj || {})
    delete o.updated
    delete o._by
    return JSON.stringify(o)
  }

  function write(patch) {
    const cur = read()
    const next = Object.assign({}, cur, patch || {}, { v: VERSION, updated: Date.now(), _by: TAB })
    // identical payloads must not bounce between tabs
    if (clean(cur) === clean(next)) return cur
    try { localStorage.setItem(KEY, JSON.stringify(next)) } catch (e) { /* private mode */ }
    return next
  }

  function patchAppearance(patch) {
    const cur = read()
    return write({ appearance: Object.assign({}, cur.appearance || {}, patch || {}) })
  }

  function readSkin(char) {
    if (!char) return {}
    const s = read()
    if (s.skins && s.skins[char]) return Object.assign({}, s.skins[char])
    if (s.appearanceChar === char) return Object.assign({}, s.appearance || {})
    return {}
  }

  function writeSkin(char, appearance) {
    if (!char) return read()
    const s = read()
    const skins = Object.assign({}, s.skins || {})
    skins[char] = Object.assign({}, appearance || {})
    return write({ skins, appearance: skins[char], appearanceChar: char, active: char })
  }

  function clear() {
    try { localStorage.removeItem(KEY) } catch (e) { /* ignore */ }
  }

  function fromURL() {
    try {
      const name = new URL(location.href).searchParams.get('char')
      return name && /^[a-z0-9_]+$/i.test(name) ? name : null
    } catch (e) {
      return null
    }
  }

  function setChar(name) {
    if (!name) return read()
    write({ active: name })
    try {
      const u = new URL(location.href)
      u.searchParams.set('char', name)
      history.replaceState(null, '', u.pathname + u.search + u.hash)
    } catch (e) { /* ignore */ }
    return read()
  }

  function on(cb) {
    if (typeof cb !== 'function') return
    window.addEventListener('storage', (e) => {
      if (e.key !== KEY || !e.newValue) return
      const data = read()
      if (!data || data._by === TAB) return
      cb(data)
    })
  }

  window.PaperCastSession = { KEY, VERSION, read, write, readSkin, writeSkin, patchAppearance, clear, fromURL, setChar, on }
})()
