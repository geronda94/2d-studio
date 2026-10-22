<template>
  <div v-if="isOpen" class="fixed inset-0 z-[300] bg-bg-base text-text-primary flex flex-col" :style="editorTheme">
    <header class="shrink-0 border-b border-text-muted/40 bg-bg-surface/70 px-4 py-3 flex items-center gap-3">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <span class="text-[10px] uppercase tracking-[0.22em] text-text-muted">Сцена</span>
          <span class="text-[10px] font-mono text-text-muted/70 truncate">{{ scene?.slide_id }}</span>
        </div>
        <input
          v-model="form.title"
          class="mt-1 w-full max-w-xl bg-transparent text-lg font-bold outline-none border-b border-transparent focus:border-brand-blue/60"
          placeholder="Название сцены"
        />
      </div>

      <label class="hidden md:flex items-center gap-2 text-[10px] uppercase tracking-wide text-text-muted">
        Старт, мс
        <input v-model.number="form.start_time" type="number" step="100"
          class="w-24 rounded-md border border-text-muted/40 bg-bg-base px-2 py-1.5 text-xs text-text-primary outline-none focus:border-brand-blue" />
      </label>
      <label class="hidden md:flex items-center gap-2 text-[10px] uppercase tracking-wide text-text-muted">
        Длительность, мс
        <input v-model.number="form.duration" type="number" step="100"
          class="w-24 rounded-md border border-text-muted/40 bg-bg-base px-2 py-1.5 text-xs text-text-primary outline-none focus:border-brand-blue" />
      </label>

      <button class="rounded-lg bg-brand-blue px-4 py-2 text-xs font-bold text-white hover:opacity-90" @click="save">Сохранить</button>
      <button class="rounded-lg border border-red-400/40 px-3 py-2 text-xs font-bold text-red-300 hover:bg-red-500/10" @click="$emit('delete', scene)">Удалить</button>
      <button class="rounded-lg border border-text-muted/40 px-3 py-2 text-xs text-text-secondary hover:bg-bg-surface" @click="$emit('close')">Закрыть</button>
    </header>

    <div class="flex-1 min-h-0 flex flex-col lg:flex-row">
      <section class="flex-1 min-h-0 flex flex-col bg-black/40">
        <div class="flex-1 min-h-0 flex items-center justify-center p-4">
          <div class="relative w-full max-w-[1100px] aspect-video overflow-hidden rounded-xl border border-white/10 bg-black shadow-2xl">
            <SceneHost
              :code="form.code"
              :scene-props="parsedProps"
              :start-time="0"
              :duration="form.duration"
              :time="previewTime"
              :show-errors="true"
              preview
              @error="previewError = $event"
            />
          </div>
        </div>

        <div class="shrink-0 border-t border-text-muted/30 bg-bg-surface/50 px-4 py-3 flex items-center gap-3">
          <button class="h-9 w-9 rounded-full bg-brand-blue text-white flex items-center justify-center text-sm" @click="togglePreview">
            {{ previewPlaying ? '❚❚' : '▶' }}
          </button>
          <input v-model.number="previewTime" type="range" min="0" :max="Math.max(1, form.duration)" step="10" class="flex-1 accent-brand-blue" />
          <span class="w-28 text-right text-xs font-mono text-text-secondary">
            {{ (previewTime / 1000).toFixed(2) }}s / {{ (form.duration / 1000).toFixed(2) }}s
          </span>
          <button class="rounded-md border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" @click="previewTime = 0">0</button>
        </div>

        <div v-if="jsonError" class="shrink-0 bg-red-950/80 px-4 py-2 text-xs text-red-200 font-mono">Props JSON: {{ jsonError }}</div>
        <div v-else-if="previewError" class="shrink-0 bg-red-950/60 px-4 py-2 text-xs text-red-200 font-mono">{{ previewError }}</div>
      </section>

      <aside class="w-full lg:w-[46%] xl:w-[42%] shrink-0 border-t lg:border-t-0 lg:border-l border-text-muted/30 bg-bg-surface/40 flex flex-col min-h-0">
        <div class="shrink-0 flex items-center gap-1 px-3 pt-3">
          <button v-for="tab in tabs" :key="tab.id"
            class="rounded-md px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide transition-colors"
            :class="activeTab === tab.id ? 'bg-brand-blue text-white' : 'text-text-secondary hover:bg-bg-surface'"
            @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
          <div class="flex-1"></div>
          <button class="rounded-md border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" title="Загрузить демо-сцену" @click="loadDemo">Demo</button>
        </div>

        <div class="flex-1 min-h-0 p-3">
          <div v-if="activeTab === 'templates'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <button
              v-for="t in templates" :key="t.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-blue/60 transition-colors"
              @click="applyTemplate(t)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-bold text-text-primary">{{ t.title }}</span>
                <span class="text-[10px] font-mono text-text-muted">{{ t.duration }} ms</span>
              </div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ t.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ (t.tags || []).join(' · ') }}
              </div>
            </button>
            <p v-if="!templates.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'environments'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <button
              v-for="e in environments" :key="e.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-light-blue/60 transition-colors"
              @click="applyEnvironment(e)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-bold text-text-primary">{{ e.title }}</span>
                <span class="text-[10px] font-mono text-text-muted">{{ e.slug }}</span>
              </div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ e.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ (e.tags || []).join(' · ') }}
              </div>
            </button>
            <p v-if="!environments.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'objects'" class="h-full overflow-y-auto space-y-2 pr-1">
            <p v-if="libraryError" class="text-xs text-red-300">{{ libraryError }}</p>
            <button
              v-for="o in objects" :key="o.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-green/60 transition-colors"
              @click="insertObject(o)"
            >
              <div class="text-sm font-bold text-text-primary">{{ o.title }}</div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ o.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-green">
                + {{ (o.tags || []).join(' · ') }}
              </div>
            </button>
            <p v-if="!objects.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <textarea v-else-if="activeTab === 'html'" v-model="form.code.html" spellcheck="false"
            class="h-full w-full resize-none rounded-lg border border-text-muted/30 bg-bg-base p-3 font-mono text-[12px] leading-relaxed text-text-primary outline-none focus:border-brand-blue"
            placeholder="<div class='scene'>...</div>"></textarea>

          <textarea v-else-if="activeTab === 'css'" v-model="form.code.css" spellcheck="false"
            class="h-full w-full resize-none rounded-lg border border-text-muted/30 bg-bg-base p-3 font-mono text-[12px] leading-relaxed text-text-primary outline-none focus:border-brand-blue"
            placeholder=".scene { position:absolute; inset:0; }"></textarea>

          <textarea v-else-if="activeTab === 'js'" v-model="form.code.js" spellcheck="false"
            class="h-full w-full resize-none rounded-lg border border-text-muted/30 bg-bg-base p-3 font-mono text-[12px] leading-relaxed text-text-primary outline-none focus:border-brand-blue"
            placeholder="const tl = gsap.timeline({ paused: true });&#10;window.scene = { seek(t) { tl.seek(t / 1000) } };"></textarea>

          <div v-else-if="activeTab === 'props'" class="h-full flex flex-col gap-2">
            <textarea v-model="propsText" spellcheck="false"
              class="flex-1 w-full resize-none rounded-lg border border-text-muted/30 bg-bg-base p-3 font-mono text-[12px] leading-relaxed text-text-primary outline-none focus:border-brand-blue"
              placeholder="{&#10;  &quot;title&quot;: &quot;Привет&quot;&#10;}"></textarea>
            <p class="text-[10px] text-text-muted">Параметры сцены. Доступны в коде как <code class="text-brand-light-blue">window.__sceneProps</code>.</p>
          </div>

          <div v-else class="h-full overflow-y-auto rounded-lg border border-text-muted/30 bg-bg-base p-3 text-xs text-text-secondary space-y-2">
            <div><span class="text-text-muted">ID:</span> {{ scene?.slide_id }}</div>
            <div><span class="text-text-muted">Компонент:</span> __scene__</div>
            <div><span class="text-text-muted">Порядок:</span> {{ scene?.order_index }}</div>
            <div><span class="text-text-muted">Старт:</span> {{ form.start_time }} мс</div>
            <div><span class="text-text-muted">Длительность:</span> {{ form.duration }} мс</div>
            <div class="pt-2 text-[10px] leading-relaxed text-text-muted">
              Контракт: <code class="text-brand-light-blue">window.scene.seek(t)</code>.
              Никаких requestAnimationFrame, Date.now и бесконечных CSS-анимаций.
              Время приходит только из таймлайна.
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import SceneHost from './SceneHost.vue'
import { DEMO_SCENE, normalizeScenePayload } from './demoScene'
import { fetchSceneEnvironments, fetchSceneObjects, fetchSceneTemplates, fetchSceneTemplate } from '../services/api'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  scene: { type: Object, default: null },
})

const emit = defineEmits(['close', 'save', 'delete'])

const editorTheme = {
  '--bg-base': '#0B1322',
  '--bg-base-rgb': '11 19 34',
  '--bg-surface': '#152033',
  '--bg-surface-rgb': '21 32 51',
  '--bg-surface-hover': '#1F2D44',
  '--bg-hover': '#152033',
  '--bg-hover-rgb': '31 45 68',
  '--text-primary': '#F8FAFC',
  '--text-primary-rgb': '248 250 252',
  '--text-secondary': '#94A3B8',
  '--text-secondary-rgb': '148 163 184',
  '--text-muted': '#64748B',
  '--text-muted-rgb': '100 116 139',
  '--brand-blue': '#2563EB',
  '--brand-blue-rgb': '37 99 235',
  '--brand-light-blue': '#38BDF8',
  '--brand-light-blue-rgb': '56 189 248',
  '--brand-green': '#10B981',
  '--brand-green-rgb': '16 185 129',
  '--color-primary': '#2563EB',
  '--color-primary-rgb': '37 99 235',
  '--color-secondary': '#38BDF8',
  '--color-secondary-rgb': '56 189 248',
}

const tabs = [
  { id: 'templates', label: 'Scenes' },
  { id: 'environments', label: 'Worlds' },
  { id: 'objects', label: 'Objects' },
  { id: 'html', label: 'HTML' },
  { id: 'css', label: 'CSS' },
  { id: 'js', label: 'JS' },
  { id: 'props', label: 'Props' },
  { id: 'info', label: 'Info' },
]

const activeTab = ref('html')
const previewTime = ref(0)
const previewPlaying = ref(false)
const previewError = ref('')
const propsText = ref('{}')
const jsonError = ref('')
const templates = ref([])
const environments = ref([])
const objects = ref([])
const libraryError = ref('')

const form = ref({
  title: '',
  start_time: 0,
  duration: 5000,
  code: { html: '', css: '', js: '' },
  props_schema: {},
})

let previewTimer = null

function resetFromScene(scene) {
  const raw = scene?.data?.payload || {}
  const p = normalizeScenePayload({
    code: scene?.code || raw.code || {},
    props: scene?.props || raw.props || {},
    props_schema: scene?.props_schema || raw.props_schema || {},
    duration: scene?.duration ?? raw.duration,
  })
  form.value = {
    title: scene?.title || 'Новая сцена',
    start_time: Number(scene?.start_time) || 0,
    duration: Number(p.duration) || DEMO_SCENE.duration,
    code: { ...p.code },
    props_schema: scene?.props_schema || p.props_schema || {},
  }
  propsText.value = JSON.stringify(p.props || {}, null, 2)
  previewTime.value = Math.min(1200, form.value.duration)
  previewPlaying.value = false
  previewError.value = ''
  jsonError.value = ''
  activeTab.value = 'html'
  stopPreview()
}

watch(() => props.scene, (s) => { if (s) resetFromScene(s) }, { immediate: true })
watch(() => props.isOpen, (open) => {
  if (!open) { stopPreview(); previewPlaying.value = false }
  else if (!templates.value.length || libraryError.value) loadLibrary()
})

const parsedProps = computed(() => {
  try {
    const v = JSON.parse(propsText.value || '{}')
    jsonError.value = ''
    return v && typeof v === 'object' ? v : {}
  } catch (e) {
    jsonError.value = e.message
    return {}
  }
})

function togglePreview() {
  if (previewPlaying.value) stopPreview()
  else startPreview()
}

function startPreview() {
  stopPreview()
  previewPlaying.value = true
  if (previewTime.value >= form.value.duration) previewTime.value = 0
  let last = performance.now()
  previewTimer = setInterval(() => {
    const now = performance.now()
    const dt = now - last
    last = now
    previewTime.value = Math.min(form.value.duration, previewTime.value + dt)
    if (previewTime.value >= form.value.duration) {
      previewTime.value = form.value.duration
      stopPreview()
    }
  }, 16)
}

function stopPreview() {
  if (previewTimer) clearInterval(previewTimer)
  previewTimer = null
  previewPlaying.value = false
}

function applyTemplate(t) {
  if (!t) return
  form.value.code = { ...(t.code || {}) }
  form.value.duration = Number(t.duration) || form.value.duration
  form.value.props_schema = t.props_schema || {}
  propsText.value = JSON.stringify(t.default_props || {}, null, 2)
  previewTime.value = Math.min(1200, form.value.duration)
  previewError.value = ''
}

function applyEnvironment(e) {
  if (!e) return
  form.value.code = {
    html: `<div class="scene">\n${e.html || ''}\n</div>`,
    css: e.css || '',
    js: 'window.scene = { seek(t) {} };',
  }
  form.value.duration = 5000
  form.value.props_schema = {}
  propsText.value = '{}'
  previewTime.value = 1200
  previewError.value = ''
  activeTab.value = 'html'
}

function insertObject(o) {
  if (!o) return
  form.value.code.html = (form.value.code.html || '') + '\n' + (o.html || '')
  form.value.code.css = (form.value.code.css || '') + '\n' + (o.css || '')
  form.value.code.js = (form.value.code.js || '') + '\n' + (o.js || '')
  activeTab.value = 'html'
}

async function loadLibrary() {
  try {
    const [t, e, o] = await Promise.all([
      fetchSceneTemplates(),
      fetchSceneEnvironments(),
      fetchSceneObjects(),
    ])
    templates.value = Array.isArray(t) ? t : []
    environments.value = Array.isArray(e) ? e : []
    objects.value = Array.isArray(o) ? o : []
  } catch (e) {
    libraryError.value = e?.message || 'Не удалось загрузить библиотеку'
  }
}

onMounted(loadLibrary)

async function loadDemo() {
  try {
    const t = await fetchSceneTemplate('forest-drive')
    if (t) { applyTemplate(t); return }
  } catch (e) { /* fallback below */ }
  const local = templates.value.find((x) => x.slug === 'forest-drive')
  if (local) { applyTemplate(local); return }
  form.value.code = { ...DEMO_SCENE.code }
  form.value.props_schema = {}
  propsText.value = JSON.stringify(DEMO_SCENE.props || {}, null, 2)
  previewTime.value = Math.min(1200, form.value.duration)
  previewError.value = ''
}

function save() {
  if (!props.scene) return
  let p = {}
  try { p = JSON.parse(propsText.value || '{}') } catch (e) { jsonError.value = e.message; return }
  emit('save', {
    slide_id: props.scene.slide_id,
    component: '__scene__',
    start_time: Number(form.value.start_time) || 0,
    title: form.value.title || '',
    subtitle: '',
    layout: 'col',
    order_index: props.scene.order_index || 0,
    kind: 'scene',
    duration: Number(form.value.duration) || 5000,
    code: { ...form.value.code },
    props: p,
    props_schema: form.value.props_schema || {},
    track: props.scene.track || 'main',
    z_index: props.scene.z_index ?? 0,
    data: {
      payload: {
        kind: 'scene',
        code: { ...form.value.code },
        props: p,
        props_schema: form.value.props_schema || {},
        duration: Number(form.value.duration) || 5000,
      },
    },
    events: [],
  })
}

onUnmounted(stopPreview)
</script>
