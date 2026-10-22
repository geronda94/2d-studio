<template>
  <div ref="hostEl" class="scene-host absolute inset-0 w-full h-full overflow-hidden">
    <iframe
      :key="frameKey"
      ref="frameEl"
      :srcdoc="doc"
      sandbox="allow-scripts"
      class="absolute inset-0 w-full h-full border-0 block"
      style="background: transparent"
      title="scene"
    ></iframe>

    <div
      v-if="showErrors && error"
      class="absolute left-3 right-3 bottom-3 z-30 rounded-lg border border-red-400/60 bg-red-950/90 px-3 py-2 text-[11px] leading-snug text-red-100 font-mono whitespace-pre-wrap pointer-events-none"
    >
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useDirector } from '../composables/useDirector'
import { buildSceneDoc, collectThemeVars, loadGsapSource, loadKitSource } from './runtime'

const props = defineProps({
  code: { type: Object, default: () => ({}) },
  sceneProps: { type: Object, default: () => ({}) },
  cues: { type: Array, default: () => [] },
  startTime: { type: Number, default: 0 },
  duration: { type: Number, default: 0 },
  // Manual time for the editor preview. When set, the global director is ignored.
  time: { type: Number, default: null },
  format: { type: String, default: '' },
  view: { type: String, default: '' },
  showErrors: { type: Boolean, default: false },
  // Preview hosts (editor) must not own the global render handshake.
  preview: { type: Boolean, default: false },
})

const emit = defineEmits(['ready', 'error'])

const { currentTime } = useDirector()

const hostEl = ref(null)
const frameEl = ref(null)
const frameKey = ref(0)
const doc = ref('')
const ready = ref(false)
const error = ref('')
const format = ref(props.format || 'landscape')

let gsapSource = ''
let kitSource = ''
let pendingSeekId = 0
let lastTime = 0
let rafId = null
let rebuildTimer = null
const waiters = new Map()

const effectiveTime = computed(() => {
  let t
  if (props.time !== null && props.time !== undefined) t = Number(props.time) || 0
  else t = (Number(currentTime.value) || 0) - (Number(props.startTime) || 0)
  if (t < 0) t = 0
  if (props.duration > 0 && t > props.duration) t = props.duration
  return t
})

const docKey = computed(() =>
  JSON.stringify({
    code: props.code || {},
    sceneProps: props.sceneProps || {},
    cues: props.cues || [],
    format: format.value,
  }),
)

function updateFormat() {
  const el = hostEl.value
  if (!el) return
  const w = el.clientWidth || 0
  const h = el.clientHeight || 0
  const next = props.format || (h > w ? 'portrait' : 'landscape')
  if (next !== format.value) format.value = next
}

async function rebuild() {
  if (!hostEl.value) return
  ready.value = false
  error.value = ''
  if (typeof window !== 'undefined' && !props.preview) window.__sceneReady = false
  if (!gsapSource) gsapSource = await loadGsapSource()
  if (!kitSource) kitSource = await loadKitSource()
  doc.value = buildSceneDoc({
    code: props.code || {},
    sceneProps: props.sceneProps || {},
    cues: props.cues || [],
    themeCss: collectThemeVars(hostEl.value),
    format: format.value,
    view: props.view,
    gsapSource,
    kitSource,
  })
  frameKey.value += 1
}

function postSeek(t, { force = false } = {}) {
  const win = frameEl.value?.contentWindow
  if (!win) return
  if (!ready.value && !force) {
    lastTime = t
    return
  }
  pendingSeekId += 1
  win.postMessage({ type: 'seek', t, id: pendingSeekId }, '*')
}

function scheduleSeek(t) {
  lastTime = t
  if (rafId !== null) return
  rafId = requestAnimationFrame(() => {
    rafId = null
    postSeek(lastTime)
  })
}

// Public: awaitable seek for the future frame-by-frame renderer.
function patchObject(id, styles) {
  const win = frameEl.value?.contentWindow
  if (!win || !id) return
  win.postMessage({ type: 'patch-style', id, styles: styles || {} }, '*')
}

function seek(t) {
  const id = ++pendingSeekId
  const win = frameEl.value?.contentWindow
  if (!win) return Promise.resolve()
  return new Promise((resolve) => {
    waiters.set(id, resolve)
    win.postMessage({ type: 'seek', t: Number(t) || 0, id }, '*')
    setTimeout(() => {
      if (waiters.has(id)) {
        waiters.delete(id)
        resolve()
      }
    }, 1500)
  })
}

function onMessage(e) {
  if (!frameEl.value || e.source !== frameEl.value.contentWindow) return
  const msg = e.data || {}
  if (!msg.__scene) return
  if (msg.type === 'scene-ready') {
    ready.value = true
    if (typeof window !== 'undefined' && !props.preview) {
      window.__sceneReady = true
      window.__sceneSeek = seek
    }
    emit('ready')
    postSeek(lastTime || effectiveTime.value, { force: true })
  } else if (msg.type === 'scene-error') {
    error.value = msg.message || 'Scene error'
    emit('error', error.value)
  } else if (msg.type === 'seek-done') {
    const resolve = waiters.get(msg.id)
    if (resolve) {
      waiters.delete(msg.id)
      resolve()
    }
  }
}

watch(docKey, () => {
  clearTimeout(rebuildTimer)
  rebuildTimer = setTimeout(rebuild, 180)
})
watch(effectiveTime, (t) => scheduleSeek(t))

let resizeObserver = null
onMounted(() => {
  updateFormat()
  rebuild()
  window.addEventListener('message', onMessage)
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(updateFormat)
    if (hostEl.value) resizeObserver.observe(hostEl.value)
  }
})
onUnmounted(() => {
  window.removeEventListener('message', onMessage)
  if (typeof window !== 'undefined' && !props.preview) {
    window.__sceneReady = false
    if (window.__sceneSeek === seek) delete window.__sceneSeek
  }
  if (resizeObserver) resizeObserver.disconnect()
  if (rafId !== null) cancelAnimationFrame(rafId)
  clearTimeout(rebuildTimer)
  waiters.clear()
})

defineExpose({ seek, rebuild, patchObject })
</script>

<style scoped>
.scene-host {
  contain: layout paint;
}
</style>
