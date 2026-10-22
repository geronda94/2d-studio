<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useVariant } from '../composables/useVariant'
import AppShell from '../components/layout/AppShell.vue'
import ProjectTeam from '../components/ui/ProjectTeam.vue'
import ProjectBrand from '../components/ui/ProjectBrand.vue'
import ProjectHistory from '../components/ui/ProjectHistory.vue'
import { useAuth } from '../composables/useAuth'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchProjectBySlug, updateProject, fetchProjectColors,
  fetchTokenCoverage, repairTokens, fetchVariants, copyPalette,
  upsertProjectTokens, deleteProjectToken, deleteProject,
  applyProjectVariant, fetchPalettes, forkProject, fetchBrief, updateBrief,
} from '../services/api'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const { currentUser, ensureLoaded } = useAuth()
const canManageProject = computed(() =>
  !!currentUser.value &&
  (currentUser.value.is_superadmin || project.value?.owner_id === currentUser.value.id),
)
// Первая презентация проекта — для медиатеки в «Бренде проекта».
const firstPresentationId = computed(() => {
  for (const f of project.value?.folders || []) {
    for (const p of f.presentations || []) return p.id
  }
  return 0
})
const loading = ref(true)
const activeTab = ref('general')

// Общее
const formTitle = ref('')
const formDesc = ref('')
const savingGeneral = ref(false)
const generalMsg = ref('')
const deleteConfirm = ref('')
const deleting = ref(false)

const stylesLoaded = ref(false)

const loadProject = async () => {
  loading.value = true
  try {
    project.value = await fetchProjectBySlug(route.params.slug)
    formTitle.value = project.value.title || ''
    formDesc.value = project.value.description || ''
  } catch {
    project.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => { ensureLoaded(); loadProject() })

const saveGeneral = async () => {
  if (!project.value?.id || savingGeneral.value) return
  savingGeneral.value = true
  generalMsg.value = ''
  try {
    const updated = await updateProject(project.value.id, {
      title: formTitle.value.trim(),
      description: formDesc.value.trim(),
    })
    project.value.title = updated.title
    project.value.description = updated.description
    generalMsg.value = 'Сохранено'
  } catch (e) {
    generalMsg.value = e.message
  } finally {
    savingGeneral.value = false
  }
}

// ---- Таб Стили ----
const GROUP_DEFS = [
  { id: 'scene', name: 'Фон сцены', desc: 'Слои фона слайда снизу вверх: цвет → градиент → иллюстрация → шум. Слой с none выключен.', match: (k) => k === 'bg-image' || k.startsWith('bg-decorations') || k.startsWith('bg-overlay') || k.startsWith('pattern-') || k === 'glass-bg' },
  { id: 'surface', name: 'Поверхности', desc: 'Фоны карточек и слайдов.', match: (k) => (k.startsWith('bg-') || k.startsWith('slide-bg-')) && !GROUP_DEFS[0].match(k) },
  { id: 'text', name: 'Текст', desc: 'Цвета текста и палитра шрифтов — в Типографике.', match: (k) => k.startsWith('text-') },
  { id: 'accent', name: 'Акценты', desc: '4 цвета шахматки айтемов + главный акцент. Меняются вместе.', match: (k) => k.startsWith('item-accent-') || k === 'color-accent' || k === 'color-accent-2' },
  { id: 'role', name: 'Роли', desc: 'Семантика: успех, предупреждение, ошибка, инфо. Трогать только осознанно.', match: (k) => k.startsWith('color-') },
  { id: 'chart', name: 'Графики', desc: 'Цвета диаграмм и сетки.', match: (k) => k.startsWith('chart-') },
  { id: 'effect', name: 'Эффекты', desc: 'Градиенты, свечения, стекло, тени.', match: (k) => k.startsWith('gradient-') || k.startsWith('glow-') || k.startsWith('glass-') || k.startsWith('pattern-') || k.startsWith('shadow') },
  { id: 'border', name: 'Границы', desc: 'Рамки карточек.', match: (k) => k.startsWith('border-') },
  { id: 'type', name: 'Типографика', desc: 'Кегли шкалы и шрифты. Меняют весь проект сразу.', match: (k) => k.startsWith('type-') || k.startsWith('font') },
  { id: 'custom', name: 'Мои', desc: 'Токены, созданные вручную. Можно удалять.', match: null },
  { id: 'other', name: 'Прочее', desc: 'Всё остальное.', match: null },
]

const expandedKey = ref(null)
const isLong = (v) => typeof v === 'string' && v.length > 60

const tokensList = ref([]) // [{key, value, custom}]
const coverage = ref(null)
const variantsList = ref([])
const templatesList = ref([])
// Палитры для селекта: исключаем сам проект-получатель (нельзя применить к себе)
const paletteOptions = computed(() =>
  (templatesList.value || []).filter((t) => t.id !== (project.value?.id ?? -1)))
const defaultVariantSel = ref('')
const variantSaving = ref(false)
const copyFrom = ref('')
const copying = ref(false)
const reverting = ref(false)
const repairing = ref(false)
const panelMsg = ref('')
const activeGroup = ref('surface')
const groupSearch = ref('')
const editVals = ref({})
const showAddToken = ref(false)
const newTokenKey = ref('')
const newTokenVal = ref('#FF00FF')
const addingToken = ref(false)

const filteredGroups = computed(() => {
  const q = groupSearch.value.trim().toLowerCase()
  return GROUP_DEFS.map((g) => {
    let toks
    if (g.id === 'custom') {
      toks = tokensList.value.filter((t) => t.custom)
    } else if (g.id === 'other') {
      toks = tokensList.value.filter((t) => !GROUP_DEFS.some((gg) => gg.id !== 'custom' && gg.id !== 'other' && gg.match && gg.match(t.key)))
    } else {
      toks = tokensList.value.filter((t) => g.match(t.key))
    }
    if (q) toks = toks.filter((t) => t.key.toLowerCase().includes(q) || (t.value || '').toLowerCase().includes(q))
    return { ...g, tokens: toks }
  }).filter((g) => g.id === 'custom' || g.tokens.length || !groupSearch.value.trim())
})

const activeGroupMeta = computed(() => filteredGroups.value.find((g) => g.id === activeGroup.value) || filteredGroups.value[0])

const isColorish = (v) => typeof v === 'string' && (v.trim().startsWith('#') || v.trim().startsWith('rgb'))
const toHex = (v) => {
  const s = String(v || '').trim()
  if (s.startsWith('#')) return s.length === 4 ? '#' + s.slice(1).split('').map((c) => c + c).join('') : s.slice(0, 7)
  const m = s.match(/rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/i)
  if (m) return '#' + [m[1], m[2], m[3]].map((n) => Number(n).toString(16).padStart(2, '0')).join('').toUpperCase()
  return '#000000'
}

const previewVariant = ref('tech')

// Стенд реально читает конфиг варианта (иначе смена конфига визуально «ничего не делает»):
// форма (radius/shadow/border/padding), линия (style/width/color) и моушн (appear/stagger/count).
const {
  itemVars: previewItemVars,
  surfaceVars: previewVars,
  line: previewLine,
  motion: previewMotion,
} = useVariant(computed(() => previewVariant.value), 'Preview')

// Replay моушна: перемонтирует демо-блок, entrance идёт с длительностью appear_ms варианта
const motionReplayKey = ref(0)
const motionPlayed = ref(true)

// CSS-переменные варианта + перекрытие цветом из темы проекта (--pv-*)
const itemStyle = (extra = {}) => ({
  background: extra.bg || 'var(--item-bg, var(--pv-bg-surface))',
  color: extra.color || 'var(--pv-text-primary)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  padding: 'var(--item-padding)',
})

const activeVariantConfig = computed(() =>
  (variantsList.value.find((v) => v.slug === previewVariant.value) || {}).config || null
)

const hexToRgb = (v) => {
  const s = String(v || '').trim()
  let m = s.match(/^#([0-9a-f]{6})$/i)
  if (m) {
    const h = m[1]
    return `${parseInt(h.slice(0, 2), 16)} ${parseInt(h.slice(2, 4), 16)} ${parseInt(h.slice(4, 6), 16)}`
  }
  m = s.match(/^rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})/i)
  if (m) return `${m[1]} ${m[2]} ${m[3]}`
  return null
}

// Песочница темы: токены проекта под НАСТОЯЩИМИ именами (--bg-surface, --text-primary…).
// Без этого конфиг варианта (--item-bg → var(--bg-surface)) резолвится в светлую тему
// страницы настроек, и стенд врёт (белая плашка на тёмной теме). Переменные скоупированы
// корнем стенда — наружу не текут.
const themeVars = computed(() => {
  const out = {}
  for (const t of tokensList.value) {
    if (typeof t.value !== 'string' || !t.value) continue
    out[`--${t.key}`] = t.value
    const rgb = hexToRgb(t.value)
    if (rgb) out[`--${t.key}-rgb`] = rgb
  }
  return out
})

// Стенд читает тему проекта через --pv-* переменные: правишь токен — стенд
// перекрашивается мгновенно, без перезагрузки (чистый CSS, без рефлоу)
const previewStyle = computed(() => {
  const map = {}
  for (const t of tokensList.value) {
    if (typeof t.value === 'string' && !t.value.includes('url(')) {
      map[`--pv-${t.key}`] = t.value
    }
  }
  return {
    ...map,
    background: 'var(--pv-bg-base, #fff)',
    border: '1px solid var(--pv-border-main, #e5e7eb)',
  }
})

// Превью сцены: повторяет слои SlidePresentation (контейнер bg + image + decorations + overlay).
// Значения берутся из editVals (несохранённые правки видны сразу) с fallback на сохранённые.
const scenePreview = computed(() => {
  const val = (k) => {
    const ed = (editVals.value[k] ?? '').trim()
    if (ed) return ed
    return (tokensList.value.find((t) => t.key === k) || {}).value || 'none'
  }
  return {
    backgroundColor: val('bg-base'),
    backgroundImage: `${val('bg-decorations')}, ${val('bg-image')}, ${val('bg-overlay')}`,
    backgroundSize: `${val('bg-decorations-size')}, cover, auto`,
    backgroundPosition: 'bottom center, center, center',
    backgroundRepeat: 'no-repeat',
  }
})

const reloadTokens = async () => {
  if (!project.value?.id) return
  try {
    const colors = await fetchProjectColors(project.value.id)
    tokensList.value = (colors || []).map((c) => ({ key: c.name, value: c.value, custom: c.custom === true }))
    editVals.value = {}
  } catch { tokensList.value = [] }
  try {
    coverage.value = await fetchTokenCoverage(project.value.id)
  } catch { coverage.value = null }
}

const saveToken = async (t) => {
  const val = (editVals.value[t.key] ?? '').trim()
  if (!val || val === t.value) return
  try {
    await upsertProjectTokens(project.value.id, { [t.key]: val })
    panelMsg.value = `${t.key} сохранён`
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
}

const saveTokenColor = async (t, hex) => {
  editVals.value[t.key] = hex
  await saveToken(t)
}

const addToken = async () => {
  const key = newTokenKey.value.trim()
  if (!key || addingToken.value) return
  addingToken.value = true
  try {
    await upsertProjectTokens(project.value.id, { [key]: newTokenVal.value })
    newTokenKey.value = ''
    showAddToken.value = false
    panelMsg.value = `${key} создан`
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
  finally { addingToken.value = false }
}

const removeToken = async (t) => {
  if (!t.custom || !confirm(`Удалить токен «${t.key}»?`)) return
  try {
    await deleteProjectToken(project.value.id, t.key)
    panelMsg.value = `${t.key} удалён`
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
}

const applyDefaultVariant = async () => {
  // Настройки проекта = применяется ко всему проекту сразу: дефолт для новых
  // + все существующие презентации (слайды со своим variant не трогаем).
  if (!project.value?.id || variantSaving.value) return
  variantSaving.value = true
  try {
    const v = defaultVariantSel.value || null
    const updated = await updateProject(project.value.id, { default_variant: v })
    project.value.default_variant = updated.default_variant
    const res = await applyProjectVariant(project.value.id, v)
    // стенд следует за конфигом проекта
    previewVariant.value = v || 'tech'
    panelMsg.value = `Стиль применён ко всему проекту: ${res.updated} из ${res.total} през.`
  } catch (e) {
    panelMsg.value = e.message
    defaultVariantSel.value = project.value?.default_variant || ''
  } finally { variantSaving.value = false }
}

const runCopy = async () => {
  if (!project.value?.id || !copyFrom.value || copying.value) return
  if (!confirm(`Взять палитру «${copyFrom.value}»? Свои цвета не пострадают.`)) return
  copying.value = true
  try {
    const res = await copyPalette(project.value.id, copyFrom.value)
    const src = templatesList.value.find((t) => t.slug === copyFrom.value)
    if (src) project.value.palette_source = src.slug
    panelMsg.value = `Тема применена: ${res.copied} токенов` + (res.structural?.length ? ` (фон сцены: ${res.structural.join(', ')})` : '')
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
  finally { copying.value = false }
}

const runRevert = async () => {
  if (!project.value?.palette_source || reverting.value) return
  if (!confirm(`Вернуть палитру «${project.value.palette_source}»? Свои цвета не пострадают.`)) return
  reverting.value = true
  try {
    const res = await copyPalette(project.value.id, project.value.palette_source)
    panelMsg.value = `Тема возвращена к ${project.value.palette_source}: ${res.copied} токенов`
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
  finally { reverting.value = false }
}

const forking = ref(false)

const runFork = async () => {
  const src = templatesList.value.find((t) => t.slug === copyFrom.value)
  if (!src || forking.value) return
  const title = prompt(`Название моей темы (копия «${src.title}»):`, `${src.title} (моя)`)
  if (title === null) return
  forking.value = true
  try {
    const fork = await forkProject(src.id, title || undefined)
    panelMsg.value = `Создана моя тема «${fork.title}»`
    templatesList.value = (await fetchPalettes()) || []
  } catch (e) { panelMsg.value = e.message }
  finally { forking.value = false }
}

const runRepair = async () => {
  if (!project.value?.id || repairing.value) return
  repairing.value = true
  try {
    const res = await repairTokens(project.value.id)
    panelMsg.value = `Дотянуто: ${res.added.length}`
    await reloadTokens()
  } catch (e) { panelMsg.value = e.message }
  finally { repairing.value = false }
}

const loadStylesTab = async () => {
  if (!project.value?.id) return
  await reloadTokens()
  try {
    variantsList.value = (await fetchVariants()) || []
    // Палитры = общие шаблоны + личные темы текущего владельца
    templatesList.value = (await fetchPalettes()) || []
  } catch { variantsList.value = []; templatesList.value = [] }
  const cur = project.value?.default_variant || ''
  defaultVariantSel.value = cur
  // Предпросмотр стартует с текущего конфига проекта (не хардкод tech)
  previewVariant.value = cur || 'tech'
  // Текущий источник палитры показываем в селекте, только если он есть в списке.
  // Legacy-slug ('history') нормализуем к 'template-history'; иначе — пусто,
  // чтобы «Применить» не отправлял несуществующий/совпадающий источник.
  const src = project.value?.palette_source || ''
  const match = paletteOptions.value.find((t) => t.slug === src)
    || paletteOptions.value.find((t) => t.slug === `template-${src}`)
  copyFrom.value = match ? match.slug : ''
}

// ---- Бриф проекта (AI_PLATFORM, вкладка «Бриф») ----
const brief = ref({ about: '', audience: '', tone: '', voice: '' })
const briefMust = ref('')
const briefForbidden = ref('')
const briefSaving = ref(false)
const briefMsg = ref('')
const briefLoaded = ref(false)

const loadBrief = async () => {
  if (!project.value?.id) return
  try {
    const data = await fetchBrief(project.value.id)
    const b = data.brief || {}
    brief.value = {
      about: b.about || '', audience: b.audience || '',
      tone: b.tone || '', voice: b.voice || '',
    }
    briefMust.value = (b.must || []).join('\n')
    briefForbidden.value = (b.forbidden || []).join('\n')
  } catch { /* нет брифа — пусто */ }
  briefLoaded.value = true
}

const saveBrief = async () => {
  if (!project.value?.id || briefSaving.value) return
  briefSaving.value = true
  briefMsg.value = ''
  try {
    await updateBrief(project.value.id, {
      ...brief.value,
      must: briefMust.value.split('\n').map(s => s.trim()).filter(Boolean),
      forbidden: briefForbidden.value.split('\n').map(s => s.trim()).filter(Boolean),
    })
    briefMsg.value = 'Бриф сохранён'
  } catch (e) { briefMsg.value = e.message }
  finally { briefSaving.value = false }
}

// Ленивая загрузка тяжёлых данных по требованию
watch(activeTab, async (tab) => {
  if (tab === 'styles' && !stylesLoaded.value && project.value) {
    await loadStylesTab()
    stylesLoaded.value = true
  }
  if (tab === 'brief' && !briefLoaded.value && project.value) {
    await loadBrief()
  }
})

const doDelete = async () => {
  if (!project.value?.id || deleting.value) return
  if (deleteConfirm.value.trim() !== (project.value.title || '').trim()) return
  deleting.value = true
  try {
    await deleteProject(project.value.id)
    router.push('/')
  } catch (e) {
    generalMsg.value = e.message
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <AppShell
    v-if="!loading && project"
    :crumbs="[{ label: 'Проекты', to: '/' }, { label: project.title, to: `/project/${project.slug}` }, { label: 'Настройки' }]"
    :title="`Настройки: ${project.title}`"
  >
    <template #subtitle>slug: <span class="font-mono text-sm">{{ project.slug }}</span></template>
    <div>
      <!-- Tabs -->
      <div class="flex gap-2 mb-8 border-b border-gray-200 pb-px">
        <button
          @click="activeTab = 'general'"
          class="px-5 py-2.5 text-sm font-bold border-b-2 -mb-px transition-colors"
          :class="activeTab === 'general' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Общее
        </button>
        <button
          @click="activeTab = 'styles'"
          class="px-5 py-2.5 text-sm font-bold border-b-2 -mb-px transition-colors"
          :class="activeTab === 'styles' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Стили
        </button>
        <button
          @click="activeTab = 'brief'"
          class="px-5 py-2.5 text-sm font-bold border-b-2 -mb-px transition-colors"
          :class="activeTab === 'brief' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-800'"
        >
          Бриф
        </button>
      </div>

      <!-- Tab: бриф (знание проекта для AI) -->
      <section v-if="activeTab === 'brief'" class="max-w-3xl flex flex-col gap-6">
        <div class="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col gap-4">
          <h2 class="text-lg font-bold">Бриф проекта</h2>
          <p class="text-sm text-gray-500 -mt-2">Знание проекта для ИИ-ассистента: о чём, для кого, тон, что обязательно и что запрещено.</p>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">О чём проект</label>
            <textarea v-model="brief.about" rows="3" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"></textarea>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Аудитория</label>
              <input v-model="brief.audience" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Tone of voice</label>
              <input v-model="brief.tone" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Голос озвучки</label>
              <input v-model="brief.voice" placeholder="Charon" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Обязательно (по строке)</label>
              <textarea v-model="briefMust" rows="3" placeholder="евро, не рубли" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"></textarea>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Запрещено (по строке)</label>
              <textarea v-model="briefForbidden" rows="3" placeholder="эмодзи&#10;слайд-слаоп" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"></textarea>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="saveBrief"
              :disabled="briefSaving"
              class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
            >
              {{ briefSaving ? 'Сохранение…' : 'Сохранить бриф' }}
            </button>
            <span v-if="briefMsg" class="text-sm text-gray-500">{{ briefMsg }}</span>
          </div>
        </div>
      </section>

      <!-- Tab: общее -->
      <section v-if="activeTab === 'general'" class="max-w-2xl flex flex-col gap-6">
        <div class="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col gap-4">
          <h2 class="text-lg font-bold">Основное</h2>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Название</label>
            <input
              v-model="formTitle"
              class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Описание</label>
            <textarea
              v-model="formDesc"
              rows="3"
              class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            ></textarea>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="saveGeneral"
              :disabled="savingGeneral || !formTitle.trim()"
              class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
            >
              {{ savingGeneral ? 'Сохранение…' : 'Сохранить' }}
            </button>
            <span v-if="generalMsg" class="text-sm text-gray-500">{{ generalMsg }}</span>
          </div>
        </div>

        <div class="bg-white border border-red-200 rounded-2xl p-6 shadow-sm flex flex-col gap-3">
          <h2 class="text-lg font-bold text-red-700">Опасная зона</h2>
          <p class="text-sm text-gray-500 font-light">Архивирование скрывает проект из списка. Шаблоны витрины удалить нельзя. Данные не удаляются физически.</p>
          <input
            v-model="deleteConfirm"
            :placeholder="`Введите «${project.title}» для подтверждения`"
            class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-100"
          >
          <button
            @click="doDelete"
            :disabled="deleting || deleteConfirm.trim() !== (project.title || '').trim()"
            class="self-start px-5 py-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
          >
            {{ deleting ? 'Архивирую…' : 'Архивировать проект' }}
          </button>
        </div>
      </section>

      <!-- Tab: стили. Две НЕЗАВИСИМЫЕ оси: СТИЛЬ (форма) и ТЕМА (цвета/сцена).
           Меняешь одну — вторая не трогается. Всё применяется ко всему проекту. -->
      <section v-if="activeTab === 'styles'" class="flex flex-col gap-5">
        <!-- Панель проекта -->
        <div class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col gap-4">
          <!-- Ось 1: стиль (форма) -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
            <span class="text-sm font-bold text-gray-800 w-32 shrink-0">Стиль (форма)</span>
            <select
              v-model="defaultVariantSel"
              @change="applyDefaultVariant"
              :disabled="variantSaving"
              class="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:border-blue-500 disabled:opacity-50"
              title="Радиусы, границы, тени, линии, моушн. Цвета не меняет."
            >
              <option value="">—</option>
              <option v-for="v in variantsList" :key="v.slug" :value="v.slug">{{ v.name || v.slug }}</option>
            </select>
            <span class="text-xs text-gray-400">радиусы · границы · тени · линии · моушн</span>
            <span v-if="variantSaving" class="text-xs text-gray-400">применяю…</span>
          </div>

          <!-- Ось 2: тема (цвета/сцена) -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-gray-100 pt-4">
            <span class="text-sm font-bold text-gray-800 w-32 shrink-0">Тема (цвета)</span>
            <select
              v-model="copyFrom"
              class="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:border-blue-500 max-w-56"
              title="Заменяет цвета и сцену (фон/градиент/иллюстрацию). Форму не меняет."
            >
              <option value="" disabled>Выбрать палитру…</option>
              <option v-for="t in paletteOptions" :key="t.slug" :value="t.slug">{{ t.title }}</option>
            </select>
            <button
              @click="runCopy"
              :disabled="!copyFrom || copying"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {{ copying ? '…' : 'Применить тему' }}
            </button>
            <button
              @click="runRevert"
              :disabled="reverting || !project.palette_source"
              class="px-3 py-2 bg-white hover:bg-gray-100 disabled:opacity-50 text-gray-700 border border-gray-200 rounded-lg text-sm font-medium transition-colors"
              :title="project.palette_source ? `Вернуть исходную палитру «${project.palette_source}»` : 'Источник палитры неизвестен'"
            >
              {{ reverting ? '…' : '↩ К источнику' }}
            </button>
            <button
              @click="runFork"
              :disabled="!copyFrom || forking"
              class="px-3 py-2 bg-white hover:bg-gray-100 disabled:opacity-50 text-gray-700 border border-gray-200 rounded-lg text-sm font-medium transition-colors"
              title="Сохранить выбранную палитру как МОЮ личную тему (шаблон не меняется)"
            >
              {{ forking ? '…' : '⧉ В мои темы' }}
            </button>
            <span class="text-xs text-gray-400">
              фон · градиент · иллюстрация · цвета<template v-if="project.palette_source"> · источник: {{ project.palette_source }}</template>
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-gray-100 pt-3">
            <span class="text-sm text-gray-500 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="coverage?.missing?.length ? 'bg-amber-500' : 'bg-green-500'"></span>
              Переменные {{ coverage?.covered ?? '–' }}/{{ coverage?.total ?? '–' }}
              <button
                v-if="coverage?.missing?.length"
                @click="runRepair"
                :disabled="repairing"
                class="text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
              >
                {{ repairing ? '…' : 'Дотянуть' }}
              </button>
            </span>
            <span v-if="panelMsg" class="text-sm text-gray-500">{{ panelMsg }}</span>
          </div>
        </div>

        <!-- Живой предпросмотр темы -->
        <div class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
          <div class="flex items-center justify-between mb-4 gap-3 flex-wrap">
            <div>
              <h2 class="text-lg font-bold">Предпросмотр</h2>
              <p class="text-xs text-gray-400">Песочница: примеряй без применения. Тема проекта + выбранный конфиг ниже.</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500">примеряю конфиг:</span>
              <select
                v-model="previewVariant"
                class="bg-gray-50 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                title="Какой конфиг показать в предпросмотре (не применяется)"
              >
                <option v-for="v in variantsList" :key="v.slug" :value="v.slug">{{ v.name || v.slug }}</option>
              </select>
              <button
                @click="defaultVariantSel = previewVariant; applyDefaultVariant()"
                :disabled="variantSaving || previewVariant === (project.default_variant || 'tech')"
                class="px-3 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg transition-colors"
                title="Применить этот конфиг ко всему проекту"
              >
                Применить
              </button>
            </div>
          </div>
          <div
            class="rounded-xl overflow-hidden p-6 flex flex-col gap-4 transition-all"
            :style="[previewStyle, themeVars, previewVars, previewItemVars]"
          >
            <h3 class="font-bold" :style="{ color: 'var(--pv-text-primary)', fontSize: 'var(--pv-type-h1, 1.75rem)' }">
              Заголовок <em :style="{ color: 'var(--pv-color-accent)' }">с акцентом</em>
            </h3>
            <div class="flex gap-2 flex-wrap">
              <span class="px-3 py-1 text-xs font-bold" :style="itemStyle({ bg: 'var(--pv-color-primary)', color: '#fff' })">Primary</span>
              <span class="px-3 py-1 text-xs font-bold" :style="itemStyle({ bg: 'var(--pv-color-success-soft)', color: 'var(--pv-color-success)' })">Успех</span>
              <span class="px-3 py-1 text-xs font-bold" :style="itemStyle({ bg: 'var(--pv-color-warning-soft)', color: 'var(--pv-color-warning)' })">Внимание</span>
              <span class="px-3 py-1 text-xs font-bold" :style="itemStyle({ bg: 'var(--pv-color-danger-soft)', color: 'var(--pv-color-danger)' })">Ошибка</span>
            </div>
            <div class="p-4 flex items-center gap-3" :style="itemStyle()">
              <span class="w-10 h-10 flex items-center justify-center font-bold" :style="{ background: 'var(--pv-color-secondary)', color: '#fff', borderRadius: 'var(--item-radius)' }">◆</span>
              <div class="flex-1">
                <p class="font-bold text-sm" :style="{ color: 'var(--pv-text-primary)' }">Карточка айтема</p>
                <p class="text-xs" :style="{ color: 'var(--pv-text-secondary)' }">Вторичный текст описания</p>
              </div>
            </div>
            <div class="h-2.5 overflow-hidden" :style="{ background: 'var(--pv-bg-surface)', borderRadius: 'var(--item-radius)' }">
              <div class="h-full w-2/3" :style="{ background: 'linear-gradient(90deg, var(--pv-color-secondary), var(--pv-chart-1))', borderRadius: 'var(--item-radius)' }"></div>
            </div>
            <button class="self-start px-5 py-2.5 text-sm font-bold text-white" :style="[itemStyle({ bg: 'var(--pv-color-accent)' })]">
              Кнопка действия
            </button>
          </div>
          <!-- Форма варианта: радиус/тень/рамка/линия/моушн — всё из конфига, видно сразу -->
          <div
            class="rounded-xl overflow-hidden p-4 flex flex-col gap-3"
            :style="[themeVars, previewVars, previewItemVars]"
          >
            <p class="text-xs font-bold uppercase tracking-wider" :style="{ color: 'var(--pv-text-secondary)' }">
              Форма конфига «{{ previewVariant }}»
            </p>
            <div class="flex gap-3 flex-wrap items-stretch">
              <div class="flex-1 min-w-28 p-3" :style="{ background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)', borderWidth: 'var(--item-border-width)', borderStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' }">
                <p class="text-xs font-mono" :style="{ color: 'var(--pv-text-secondary)' }">radius {{ activeVariantConfig?.item?.radius || '—' }}</p>
              </div>
              <div class="flex-1 min-w-28 p-3 flex flex-col justify-center gap-1" :style="{ background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }">
                <div :style="{ borderTop: `${previewLine.width || 2}px ${previewLine.style || 'solid'} ${previewLine.color || 'var(--pv-color-secondary)'}` }"></div>
                <p class="text-xs font-mono" :style="{ color: 'var(--pv-text-secondary)' }">{{ previewLine.style || 'solid' }} · {{ previewLine.width || 2 }}px</p>
              </div>
              <div class="flex-1 min-w-28 p-3" :style="{ background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }">
                <p class="text-xs font-mono" :style="{ color: 'var(--pv-text-secondary)' }">appear {{ previewMotion.appear_ms }}ms</p>
                <p class="text-xs font-mono" :style="{ color: 'var(--pv-text-secondary)' }">stagger {{ previewMotion.stagger_ms }}ms</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button
                @click="motionPlayed = false; motionReplayKey++; $nextTick(() => { motionPlayed = true })"
                class="px-3 py-1.5 text-xs font-bold rounded-lg text-white"
                :style="{ background: 'var(--pv-color-secondary)' }"
              >
                ▶ Replay появления ({{ previewMotion.appear_ms }}ms)
              </button>
              <div class="flex-1 h-9 flex items-center">
                <div
                  :key="motionReplayKey"
                  class="h-9 flex-1"
                  :style="{
                    background: 'var(--pv-color-accent)',
                    borderRadius: 'var(--item-radius)',
                    opacity: motionPlayed ? 1 : 0,
                    transform: motionPlayed ? 'translateX(0)' : 'translateX(24px)',
                    transitionProperty: 'opacity, transform',
                    transitionDuration: (previewMotion.appear_ms || 500) + 'ms',
                    transitionTimingFunction: 'cubic-bezier(0.22, 1, 0.36, 1)',
                  }"
                ></div>
              </div>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">
            Конфиг: radius {{ activeVariantConfig?.item?.radius || '—' }},
            shadow {{ (activeVariantConfig?.item?.shadow || 'none').slice(0, 24) }}
          </p>
        </div>

        <div class="flex gap-5 items-start">
          <!-- Группы -->
          <aside class="w-56 shrink-0 bg-white border border-gray-200 rounded-2xl p-3 shadow-sm sticky top-4">
            <input
              v-model="groupSearch"
              placeholder="Поиск токена…"
              class="w-full bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:border-blue-500"
            >
            <button
              v-for="g in filteredGroups"
              :key="g.id"
              @click="activeGroup = g.id"
              class="w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex justify-between items-center"
              :class="activeGroup === g.id ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'"
            >
              <span>{{ g.name }}</span>
              <span class="text-xs opacity-70">{{ g.tokens.length }}</span>
            </button>
          </aside>

          <!-- Редактор группы -->
          <div class="flex-1 min-w-0 bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-1">
              <h2 class="text-lg font-bold">{{ activeGroupMeta?.name }}</h2>
              <button
                @click="showAddToken = !showAddToken"
                class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
              >
                + Свой токен
              </button>
            </div>
            <p v-if="activeGroupMeta?.desc" class="text-xs text-gray-400 mb-4">{{ activeGroupMeta.desc }}</p>
            <!-- Превью сцены ПЕРВЫМ: сначала видно результат, потом строки -->
            <div v-if="activeGroup === 'scene'" class="mb-4">
              <div
                class="rounded-xl h-44 border border-gray-300 relative overflow-hidden"
                :style="scenePreview"
              >
                <div class="absolute inset-0 flex items-end justify-center pb-3 pointer-events-none">
                  <span class="px-3 py-1 rounded-lg text-xs font-bold bg-black/40 text-white backdrop-blur-sm">контент слайда поверх</span>
                </div>
              </div>
              <p class="text-xs text-gray-400 mt-1.5">Слои снизу вверх: цвет → градиент → иллюстрация → шум. Клик по строке разворачивает длинное значение.</p>
            </div>
            <div v-if="showAddToken" class="flex gap-2 mb-4">
              <input v-model="newTokenKey" placeholder="my-accent" class="flex-1 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500">
              <input v-model="newTokenVal" type="color" class="w-11 h-10 rounded-lg cursor-pointer bg-gray-50 border border-gray-300 p-1 shrink-0">
              <input v-model="newTokenVal" placeholder="#FF00FF" class="w-32 bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500">
              <button @click="addToken" :disabled="addingToken || !newTokenKey.trim()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium">OK</button>
            </div>
            <div class="flex flex-col gap-2">
              <div
                v-for="t in activeGroupMeta?.tokens || []"
                :key="t.key"
                class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-colors"
              >
                <span
                  class="w-9 h-9 rounded-lg border border-gray-300 shrink-0 shadow-inner"
                  :style="{ background: t.value }"
                  :title="t.value"
                ></span>
                <div class="flex-1 min-w-0">
                  <p class="font-mono text-sm font-bold truncate" :title="t.key">{{ t.key }}</p>
                  <p class="font-mono text-xs text-gray-400 truncate" :title="`var(--${t.key})`">var(--{{ t.key }})</p>
                </div>
                <span v-if="!t.custom" class="text-gray-300 shrink-0" title="Дефолт темы">🔒</span>
                <!-- Компактная строка: длинные значения свернуты, ▼ разворачивает в textarea -->
                <textarea
                  v-if="isLong(t.value) && expandedKey === t.key"
                  v-model="editVals[t.key]"
                  @change="saveToken(t)"
                  :placeholder="t.value"
                  rows="3"
                  class="flex-1 min-w-0 bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:border-blue-500 break-all"
                  :title="t.value"
                ></textarea>
                <input
                  v-else
                  v-model="editVals[t.key]"
                  @change="saveToken(t)"
                  :placeholder="t.value"
                  class="bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm font-mono focus:outline-none focus:border-blue-500"
                  :class="isLong(t.value) ? 'w-36 truncate' : 'flex-1 min-w-0'"
                  :title="t.value"
                >
                <button
                  v-if="isLong(t.value)"
                  @click="expandedKey = expandedKey === t.key ? null : t.key"
                  class="text-xs text-blue-600 hover:text-blue-800 shrink-0 px-1"
                  :title="expandedKey === t.key ? 'Свернуть' : 'Развернуть'"
                >
                  {{ expandedKey === t.key ? '▲' : '▼' }}
                </button>
                <input
                  v-if="isColorish(t.value)"
                  type="color"
                  :value="toHex(t.value)"
                  @change="saveTokenColor(t, $event.target.value)"
                  class="w-9 h-9 rounded-lg cursor-pointer bg-gray-50 border border-gray-300 p-0.5 shrink-0"
                  title="Пикер"
                >
                <button
                  v-if="t.custom"
                  @click="removeToken(t)"
                  class="text-gray-400 hover:text-red-500 p-1.5 shrink-0 transition-colors"
                  title="Удалить"
                >
                  🗑
                </button>
              </div>
              <p v-if="!(activeGroupMeta?.tokens || []).length" class="text-sm text-gray-400 py-6 text-center">Нет токенов в группе</p>
            </div>
          </div>
        </div>
      </section>

      <ProjectBrand v-if="project?.id" :project-id="project.id" :can-edit="canManageProject" :presentation-id="firstPresentationId" class="mt-6" />
      <ProjectHistory v-if="project?.id" :project-id="project.id" :can-edit="canManageProject" class="mt-6" />
      <ProjectTeam v-if="project?.id" :project-id="project.id" class="mt-6" />
    </div>
  </AppShell>
  <div v-else-if="!loading" class="min-h-screen bg-[#f5f5f7] flex items-center justify-center text-center p-8">
    <div>
      <h2 class="text-2xl font-bold mb-4 text-gray-900">Проект не найден</h2>
      <router-link to="/" class="text-blue-600 hover:underline">На главную</router-link>
    </div>
  </div>
</template>
