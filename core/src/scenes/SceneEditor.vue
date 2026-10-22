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
              ref="sceneHostRef"
              :code="form.code"
              :scene-props="parsedProps"
              :cues="form.cues"
              :start-time="0"
              :duration="form.duration"
              :time="previewTime"
              :view="form.view"
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
            <div class="flex items-center justify-between gap-2">
              <p class="text-[10px] uppercase tracking-wide text-text-muted">
                Мир: {{ activeEnvData?.title || 'не выбран' }}
              </p>
              <label class="flex items-center gap-1 text-[10px] text-text-muted">
                <input v-model="showAllObjects" type="checkbox" class="accent-brand-blue" />
                все
              </label>
            </div>
            <p v-if="compatWarning" class="rounded-md border border-amber-400/40 bg-amber-950/40 px-2 py-1.5 text-[10px] text-amber-200">
              {{ compatWarning }}
            </p>
            <button
              v-for="o in visibleObjects" :key="o.slug"
              class="w-full text-left rounded-lg border border-text-muted/30 bg-bg-base px-3 py-2.5 hover:border-brand-green/60 transition-colors"
              @click="insertObject(o)"
            >
              <div class="text-sm font-bold text-text-primary">{{ o.title }}</div>
              <div class="mt-0.5 text-[11px] leading-snug text-text-secondary">{{ o.description }}</div>
              <div class="mt-1 text-[9px] font-mono uppercase tracking-wide text-brand-green">
                + {{ (o.domain || []).join(' · ') }}{{ o.surface ? ' / ' + o.surface : '' }}
              </div>
              <div v-if="(o.views || []).length > 1" class="mt-0.5 text-[9px] font-mono text-text-muted">
                views: {{ o.views.join(' / ') }}
              </div>
            </button>
            <p v-if="!objects.length && !libraryError" class="text-xs text-text-muted">Загрузка…</p>
          </div>

          <div v-else-if="activeTab === 'layers'" class="h-full flex flex-col gap-2">
            <div class="flex-1 min-h-0 overflow-y-auto space-y-1 pr-1">
              <button
                v-for="l in layerList" :key="l.index"
                class="w-full text-left rounded-md border px-2.5 py-2 text-xs transition-colors"
                :class="selectedLayer === l.index
                  ? 'border-brand-blue bg-brand-blue/15 text-text-primary'
                  : 'border-text-muted/30 bg-bg-base text-text-secondary hover:border-brand-blue/40'"
                @click="selectedLayer = l.index"
              >
                <div class="flex items-center justify-between">
                  <span class="font-mono">{{ l.slug }}</span>
                  <span class="text-[9px] text-text-muted">#{{ l.index }}</span>
                </div>
                <div v-if="l.view" class="text-[9px] font-mono text-brand-light-blue">view: {{ l.view }}</div>
              </button>
              <p v-if="!layerList.length" class="text-xs text-text-muted py-4">
                В сцене нет объектов. Добавь мир и объект во вкладках Worlds / Objects.
              </p>
            </div>

            <div v-if="selectedLayerMeta" class="shrink-0 rounded-lg border border-text-muted/30 bg-bg-base p-2.5 space-y-2">
              <div class="text-[10px] font-mono uppercase tracking-wide text-brand-light-blue">
                {{ selectedLayerMeta.slug }} #{{ selectedLayerMeta.index }}
              </div>
              <div class="space-y-2">
                <label class="block">
                  <div class="flex justify-between text-[9px] text-text-muted"><span>X</span><span>{{ layerNum('left', 12, '%') }}{{ layerUnit('left', '%') }}</span></div>
                  <input type="range" min="-20" max="100" step="0.5" :value="layerNum('left', 12, '%')"
                    @input="setLayerNum('left', $event.target.value, '%')" class="w-full accent-brand-blue" />
                </label>
                <label class="block">
                  <div class="flex justify-between text-[9px] text-text-muted"><span>Y / bottom</span><span>{{ layerNum('bottom', 18, '%') }}{{ layerUnit('bottom', '%') }}</span></div>
                  <input type="range" min="-20" max="100" step="0.5" :value="layerNum('bottom', 18, '%')"
                    @input="setLayerNum('bottom', $event.target.value, '%')" class="w-full accent-brand-blue" />
                </label>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Ширина</span><span>{{ layerNum('width', 38, 'vmin') }}{{ layerUnit('width', 'vmin') }}</span></div>
                    <input type="range" min="2" max="100" step="1" :value="layerNum('width', 38, 'vmin')"
                      @input="setLayerNum('width', $event.target.value, 'vmin')" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Высота</span><span>{{ layerNum('height', 16, 'vmin') }}{{ layerUnit('height', 'vmin') }}</span></div>
                    <input type="range" min="2" max="100" step="1" :value="layerNum('height', 16, 'vmin')"
                      @input="setLayerNum('height', $event.target.value, 'vmin')" class="w-full accent-brand-blue" />
                  </label>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Масштаб</span><span>{{ layerScale.toFixed(2) }}</span></div>
                    <input type="range" min="0.2" max="3" step="0.05" :value="layerScale"
                      @input="setLayerScale($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Поворот</span><span>{{ layerRotate }}°</span></div>
                    <input type="range" min="-180" max="180" step="1" :value="layerRotate"
                      @input="setLayerRotate($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Прозрачность</span><span>{{ Number(styleValue(selectedLayerMeta.style, 'opacity') || 1).toFixed(2) }}</span></div>
                    <input type="range" min="0" max="1" step="0.01" :value="Number(styleValue(selectedLayerMeta.style, 'opacity') || 1)"
                      @input="setLayerOpacity($event.target.value)" class="w-full accent-brand-blue" />
                  </label>
                  <label class="block">
                    <div class="flex justify-between text-[9px] text-text-muted"><span>Z-index</span><span>{{ layerNum('z-index', 10, '') }}</span></div>
                    <input type="range" min="0" max="100" step="1" :value="layerNum('z-index', 10, '')"
                      @input="setLayerNum('z-index', $event.target.value, '')" class="w-full accent-brand-blue" />
                  </label>
                </div>
              </div>
              <label v-if="(selectedLayerObject?.views || []).length > 1" class="block text-[9px] text-text-muted">
                view
                <select :value="selectedLayerMeta.view" @change="updateLayerView($event.target.value)"
                  class="mt-0.5 w-full rounded border border-text-muted/30 bg-bg-surface px-2 py-1 text-xs text-text-primary">
                  <option value="">default</option>
                  <option v-for="v in selectedLayerObject.views" :key="v" :value="v">{{ v }}</option>
                </select>
              </label>
              <div class="flex gap-2 pt-1">
                <button class="flex-1 rounded border border-text-muted/40 px-2 py-1 text-[10px] text-text-secondary hover:bg-bg-surface" @click="duplicateLayer">Дублировать</button>
                <button class="flex-1 rounded border border-red-400/40 px-2 py-1 text-[10px] text-red-300 hover:bg-red-500/10" @click="removeLayer">Удалить</button>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'cues'" class="h-full flex flex-col gap-2">
            <div class="relative h-10 shrink-0 rounded-md border border-text-muted/30 bg-bg-base cursor-crosshair" @click="seekFromCueBar">
              <div class="absolute top-0 bottom-0 w-px bg-white/50" :style="{ left: previewPercent + '%' }"></div>
              <div
                v-for="(c, i) in form.cues" :key="i"
                class="absolute top-1 bottom-1 w-1.5 -translate-x-1/2 rounded-full cursor-pointer"
                :class="selectedCue === i ? 'bg-brand-light-blue' : 'bg-brand-blue/70'"
                :style="{ left: cuePercent(c) + '%' }"
                @click.stop="selectedCue = i"
              ></div>
            </div>

            <div class="flex items-center justify-between shrink-0">
              <p class="text-[10px] text-text-muted">Ключей: {{ form.cues.length }} · время сцены {{ form.duration }} мс</p>
              <button class="rounded-md bg-brand-blue px-2.5 py-1 text-[10px] font-bold text-white" @click="addCue">+ ключ</button>
            </div>

            <div class="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1">
              <div
                v-for="(c, i) in form.cues" :key="i"
                class="rounded-lg border bg-bg-base p-2 space-y-1.5"
                :class="selectedCue === i ? 'border-brand-blue/60' : 'border-text-muted/30'"
                @click="selectedCue = i"
              >
                <div class="flex items-center justify-between text-[10px]">
                  <span class="font-mono text-text-muted">#{{ i + 1 }}</span>
                  <span class="font-mono text-brand-light-blue">{{ c.at }} ms</span>
                  <button class="text-red-300 hover:text-red-200 px-1" @click.stop="removeCue(i)">×</button>
                </div>
                <input type="range" min="0" :max="Math.max(1, form.duration)" step="50" :value="c.at"
                  @input="setCueTime(i, $event.target.value)" class="w-full accent-brand-blue" />
                <input :value="cueSetText(c)" @input="setCueSet(i, $event.target.value)"
                  placeholder="speed=3, brake=true"
                  class="w-full rounded border border-text-muted/30 bg-bg-surface px-2 py-1 font-mono text-[11px] text-text-primary" />
              </div>
              <p v-if="!form.cues.length" class="text-xs text-text-muted py-4">
                Нет ключей. Сцена использует значения по умолчанию из своего JS.
                Добавь ключ, чтобы включить/ускорить/остановить механизм.
              </p>
            </div>
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
            <div class="space-y-1">
              <div class="flex justify-between text-[10px]"><span class="text-text-muted">Старт сцены</span><span>{{ form.start_time }} мс</span></div>
              <input type="range" min="0" max="120000" step="100" v-model.number="form.start_time" class="w-full accent-brand-blue" />
            </div>
            <div class="space-y-1">
              <div class="flex justify-between text-[10px]"><span class="text-text-muted">Длительность</span><span>{{ form.duration }} мс</span></div>
              <input type="range" min="500" max="20000" step="100" v-model.number="form.duration" class="w-full accent-brand-blue" />
            </div>
            <div v-if="(activeEnvData?.views || []).length" class="flex items-center gap-2 pt-1">
              <span class="text-text-muted">Вид мира:</span>
              <select v-model="form.view" class="rounded-md border border-text-muted/40 bg-bg-base px-2 py-1 text-xs text-text-primary">
                <option v-for="v in activeEnvData.views" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
            <div><span class="text-text-muted">Мир:</span> {{ activeEnvData?.title || '—' }}</div>
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
  { id: 'layers', label: 'Layers' },
  { id: 'cues', label: 'Cues' },
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
const activeEnvironment = ref('')
const showAllObjects = ref(false)
const compatWarning = ref('')
const selectedLayer = ref(0)
const selectedCue = ref(0)
const sceneHostRef = ref(null)

const form = ref({
  title: '',
  start_time: 0,
  duration: 5000,
  code: { html: '', css: '', js: '' },
  props_schema: {},
  view: '',
  cues: [],
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
    view: scene?.view || p.view || '',
    cues: Array.isArray(p.cues) ? p.cues.map((c) => ({ at: Number(c.at) || 0, set: { ...(c.set || {}) } })) : [],
  }
  form.value.code.html = ensureLayerIds(form.value.code.html)
  propsText.value = JSON.stringify(p.props || {}, null, 2)
  const envMatch = String(p.code.html || '').match(/env-([a-z-]+)/)
  activeEnvironment.value = envMatch ? envMatch[1] : ''
  previewTime.value = Math.min(1200, form.value.duration)
  previewPlaying.value = false
  previewError.value = ''
  jsonError.value = ''
  activeTab.value = 'html'
  selectedLayer.value = 0
  selectedCue.value = 0
  stopPreview()
}

watch(() => props.scene, (s) => { if (s) resetFromScene(s) }, { immediate: true })
watch(() => props.isOpen, (open) => {
  if (!open) { stopPreview(); previewPlaying.value = false }
  else if (!templates.value.length || libraryError.value) loadLibrary()
})

const activeEnvData = computed(() =>
  environments.value.find((e) => e.slug === activeEnvironment.value) || null,
)

const compatibleObjects = computed(() => {
  if (!activeEnvironment.value) return objects.value
  const domain = activeEnvData.value?.domain
  return objects.value.filter((o) => {
    if (Array.isArray(o.environments) && o.environments.length) {
      return o.environments.includes(activeEnvironment.value)
    }
    return Array.isArray(o.domain) && domain ? o.domain.includes(domain) : true
  })
})

const visibleObjects = computed(() =>
  showAllObjects.value ? objects.value : compatibleObjects.value,
)

function sceneObjects() {
  try {
    const doc = new DOMParser().parseFromString(form.value.code.html || '', 'text/html')
    return Array.from(doc.body.querySelectorAll('*')).filter((el) =>
      Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
    )
  } catch (e) {
    return []
  }
}

const layerList = computed(() => {
  const els = sceneObjects()
  return els.map((el, i) => {
    const cls = Array.from(el.classList || [])
    return {
      index: i,
      id: el.dataset.layerId || `layer-${i}`,
      slug: (cls.find((c) => c.startsWith('obj-')) || 'obj').replace('obj-', ''),
      view: (cls.find((c) => c.startsWith('view-')) || '').replace('view-', ''),
      style: el.getAttribute('style') || '',
    }
  })
})

const selectedLayerMeta = computed(() => layerList.value[selectedLayer.value] || null)

const selectedLayerObject = computed(() =>
  selectedLayerMeta.value ? objects.value.find((o) => o.slug === selectedLayerMeta.value.slug) : null,
)

function styleValue(style, key) {
  const m = String(style || '').match(new RegExp('(?:^|;)\\s*' + key + '\\s*:\\s*([^;]+)'))
  return m ? m[1].trim() : ''
}

function ensureLayerIds(html) {
  try {
    const doc = new DOMParser().parseFromString(html || '', 'text/html')
    const els = Array.from(doc.body.querySelectorAll('*')).filter((el) =>
      Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
    )
    els.forEach((el, i) => {
      if (!el.dataset.layerId) el.dataset.layerId = `layer-${i}`
    })
    return doc.body.innerHTML
  } catch (e) {
    return html
  }
}

function mutateLayer(fn) {
  const doc = new DOMParser().parseFromString(form.value.code.html || '', 'text/html')
  const els = Array.from(doc.body.querySelectorAll('*')).filter((el) =>
    Array.from(el.classList || []).some((c) => c.startsWith('obj-')),
  )
  const el = els[selectedLayer.value]
  if (!el) return
  fn(el, doc)
  els.forEach((item, i) => {
    if (!item.dataset.layerId) item.dataset.layerId = `layer-${i}`
  })
  form.value.code.html = doc.body.innerHTML
}

function patchLayer(styles) {
  const id = selectedLayerMeta.value?.id
  mutateLayer((el) => {
    for (const [key, value] of Object.entries(styles || {})) {
      if (value === '' || value === null || value === undefined) el.style.removeProperty(key)
      else el.style.setProperty(key, String(value))
    }
  })
  if (id && sceneHostRef.value?.patchObject) sceneHostRef.value.patchObject(id, styles)
}

function updateLayerStyle(key, value) {
  patchLayer({ [key]: value })
}

function styleParts(style, key, fallback, defaultUnit) {
  const raw = styleValue(style, key)
  const m = raw.match(/^(-?[\d.]+)\s*([a-z%]*)$/i)
  return {
    num: m ? Number(m[1]) : fallback,
    unit: m ? (m[2] || defaultUnit || '') : (defaultUnit || ''),
  }
}

function layerNum(key, fallback, unit) {
  return styleParts(selectedLayerMeta.value?.style, key, fallback, unit).num
}

function layerUnit(key, unit) {
  return styleParts(selectedLayerMeta.value?.style, key, 0, unit).unit || unit
}

function setLayerNum(key, value, unit) {
  const suffix = unit === '%' || unit === 'vmin' ? (layerUnit(key, unit) || unit) : ''
  patchLayer({ [key]: `${value}${suffix}` })
}

const layerTransform = computed(() => styleValue(selectedLayerMeta.value?.style, 'transform'))
const layerScale = computed(() => {
  const m = layerTransform.value.match(/scale\(([^)]+)\)/)
  return m ? Number(m[1]) || 1 : 1
})
const layerRotate = computed(() => {
  const m = layerTransform.value.match(/rotate\(([-\d.]+)deg\)/)
  return m ? Number(m[1]) || 0 : 0
})

function setLayerScale(value) {
  patchLayer({ transform: `scale(${Number(value) || 1}) rotate(${layerRotate.value}deg)` })
}

function setLayerRotate(value) {
  patchLayer({ transform: `scale(${layerScale.value}) rotate(${Number(value) || 0}deg)` })
}

function setLayerOpacity(value) {
  patchLayer({ opacity: String(value) })
}

function updateLayerView(view) {
  mutateLayer((el) => {
    Array.from(el.classList || [])
      .filter((c) => c.startsWith('view-'))
      .forEach((c) => el.classList.remove(c))
    if (view) el.classList.add(`view-${view}`)
  })
}

function removeLayer() {
  mutateLayer((el) => el.remove())
  selectedLayer.value = Math.max(0, Math.min(selectedLayer.value, layerList.value.length - 1))
}

function duplicateLayer() {
  mutateLayer((el) => {
    const clone = el.cloneNode(true)
    if (el.parentNode) el.parentNode.appendChild(clone)
  })
}

const previewPercent = computed(() =>
  Math.max(0, Math.min(100, (previewTime.value / Math.max(1, form.value.duration)) * 100)),
)

function cuePercent(cue) {
  return Math.max(0, Math.min(100, (Number(cue.at) || 0) / Math.max(1, form.value.duration) * 100))
}

function cueSetText(cue) {
  return Object.entries(cue.set || {})
    .map(([k, v]) => `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join(', ')
}

function parseSet(text) {
  const out = {}
  String(text || '').split(',').forEach((part) => {
    const idx = part.indexOf('=')
    if (idx <= 0) return
    const key = part.slice(0, idx).trim()
    let value = part.slice(idx + 1).trim()
    try { value = JSON.parse(value) } catch (e) { /* keep string */ }
    if (key) out[key] = value
  })
  return out
}

function setCueSet(index, text) {
  if (form.value.cues[index]) form.value.cues[index].set = parseSet(text)
}

function setCueTime(index, value) {
  if (form.value.cues[index]) form.value.cues[index].at = Number(value) || 0
}

function addCue() {
  form.value.cues.push({ at: Math.round(previewTime.value), set: { speed: 1 } })
  form.value.cues.sort((a, b) => (a.at || 0) - (b.at || 0))
  selectedCue.value = form.value.cues.length - 1
}

function removeCue(index) {
  form.value.cues.splice(index, 1)
  selectedCue.value = Math.max(0, Math.min(selectedCue.value, form.value.cues.length - 1))
}

function seekFromCueBar(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)))
  previewTime.value = Math.round(ratio * form.value.duration)
}

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
  form.value.code.html = ensureLayerIds(form.value.code.html)
  form.value.duration = Number(t.duration) || form.value.duration
  form.value.props_schema = t.props_schema || {}
  activeEnvironment.value = t.environment || ''
  form.value.view = t.view || activeEnvData.value?.default_view || ''
  form.value.cues = Array.isArray(t.cues) ? t.cues.map((c) => ({ at: Number(c.at) || 0, set: { ...(c.set || {}) } })) : []
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
  form.value.code.html = ensureLayerIds(form.value.code.html)
  form.value.duration = 5000
  form.value.props_schema = {}
  activeEnvironment.value = e.slug || ''
  form.value.view = e.default_view || ''
  form.value.cues = []
  compatWarning.value = ''
  propsText.value = '{}'
  previewTime.value = 1200
  previewError.value = ''
  activeTab.value = 'html'
}

function insertObject(o) {
  if (!o) return
  compatWarning.value = ''
  if (activeEnvironment.value && !compatibleObjects.value.some((x) => x.slug === o.slug)) {
    compatWarning.value = `${o.title} не предназначен для мира «${activeEnvData.value?.title || activeEnvironment.value}». Вставлено принудительно.`
  }
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
    view: form.value.view || '',
    cues: form.value.cues,
    track: props.scene.track || 'main',
    z_index: props.scene.z_index ?? 0,
    data: {
      payload: {
        kind: 'scene',
        code: { ...form.value.code },
        props: p,
        props_schema: form.value.props_schema || {},
        view: form.value.view || '',
        cues: form.value.cues,
        duration: Number(form.value.duration) || 5000,
      },
    },
    events: [],
  })
}

onUnmounted(stopPreview)
</script>
