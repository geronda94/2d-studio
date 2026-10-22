<script setup>
// ENTERPRISE Ф2: история версий проекта — список, diff, откат, чекпоинт.
import { ref, onMounted } from 'vue'
import {
  fetchProjectRevisions, getProjectRevision, createProjectCheckpoint, restoreProjectRevision,
} from '../../services/api'

const props = defineProps({
  projectId: { type: Number, required: true },
  canEdit: { type: Boolean, default: false },
})

const revisions = ref([])
const selectedN = ref(null)
const diff = ref(null)
const loading = ref(true)
const busy = ref(false)
const note = ref('')
const error = ref('')

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    revisions.value = await fetchProjectRevisions(props.projectId)
  } catch (e) {
    error.value = e.message || 'Ошибка'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const select = async (n) => {
  selectedN.value = n
  diff.value = null
  try {
    const r = await getProjectRevision(props.projectId, n)
    diff.value = r.diff_vs_current
  } catch (e) {
    error.value = e.message || 'Ошибка'
  }
}

const checkpoint = async () => {
  const label = prompt('Название точки (необязательно):') ?? ''
  busy.value = true
  note.value = ''
  try {
    await createProjectCheckpoint(props.projectId, label || 'checkpoint')
    await load()
    note.value = 'Точка сохранена'
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

const doRestore = async () => {
  if (selectedN.value == null || busy.value) return
  busy.value = true
  note.value = ''
  try {
    const dry = await restoreProjectRevision(props.projectId, selectedN.value, true)
    const d = dry.diff || {}
    const s = d.slides || {}
    const summary = `Слайды: +${s.added || 0} / −${s.removed || 0} / ~${s.changed || 0}. Продолжить откат?`
    if (!confirm(summary)) return
    await restoreProjectRevision(props.projectId, selectedN.value, false)
    await load()
    note.value = 'Проект откачен. Создана новая ревизия.'
  } catch (e) {
    note.value = e.message || 'Ошибка отката'
  } finally {
    busy.value = false
  }
}

const fmt = (s) => (s ? new Date(s).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' }) : '—')
const kb = (n) => (n ? `${Math.round(n / 1024)} КБ` : '')
const sourceLabel = (src) => ({
  manual: 'вручную', autosave: 'автосейв', ai: 'ИИ', restore: 'откат', import: 'импорт',
}[src] || src)
</script>

<template>
  <section class="bg-white rounded-2xl border border-gray-200 p-5 md:p-6">
    <div class="flex items-center justify-between mb-1">
      <h2 class="text-lg font-bold text-gray-900">История версий</h2>
      <button v-if="canEdit" @click="checkpoint" :disabled="busy"
        class="text-xs font-bold px-3 py-1.5 rounded-lg bg-gray-900 text-white hover:opacity-90 disabled:opacity-50">
        Сохранить точку
      </button>
    </div>
    <p class="text-sm text-gray-500 mb-4">
      Снимки контента проекта. Можно посмотреть изменения и откатить. Участники и ключи не затрагиваются.
    </p>

    <p v-if="loading" class="text-sm text-gray-400">Загружаю…</p>
    <p v-else-if="error" class="text-sm text-red-500">{{ error }}</p>
    <template v-else>
      <div v-if="!revisions.length" class="text-sm text-gray-400 py-3">
        Пока нет версий. Точки создаются вручную и автоматически перед правками ИИ.
      </div>
      <ul v-else class="divide-y divide-gray-100">
        <li v-for="r in revisions" :key="r.n"
            class="flex items-center gap-3 py-2 cursor-pointer"
            :class="selectedN === r.n ? 'bg-gray-50 rounded-lg px-2' : ''"
            @click="select(r.n)">
          <span class="w-8 text-center text-xs font-mono text-gray-400 shrink-0">#{{ r.n }}</span>
          <div class="min-w-0 flex-1">
            <div class="text-sm text-gray-900 truncate">
              {{ r.label || sourceLabel(r.source) }}
              <span class="text-[10px] uppercase font-bold text-gray-400 ml-1">{{ sourceLabel(r.source) }}</span>
            </div>
            <div class="text-xs text-gray-400">{{ fmt(r.created_at) }} · {{ kb(r.size_bytes) }}</div>
          </div>
        </li>
      </ul>

      <div v-if="selectedN != null" class="mt-4 border-t border-gray-100 pt-3">
        <div v-if="!diff" class="text-sm text-gray-400">Считаю изменения…</div>
        <div v-else class="text-sm text-gray-700 space-y-1">
          <div>Слайды: <b>+{{ diff.slides?.added || 0 }}</b> / <b>−{{ diff.slides?.removed || 0 }}</b> / <b>~{{ diff.slides?.changed || 0 }}</b></div>
          <div>Презентации: +{{ (diff.presentations?.added || []).length }} / −{{ (diff.presentations?.removed || []).length }} / ~{{ (diff.presentations?.changed || []).length }}</div>
          <div>Папки: +{{ (diff.folders?.added || []).length }} / −{{ (diff.folders?.removed || []).length }} / ~{{ (diff.folders?.changed || []).length }}</div>
        </div>
        <button v-if="canEdit" @click="doRestore" :disabled="busy || !diff"
          class="mt-3 px-4 py-2 rounded-xl font-bold text-white bg-amber-600 hover:opacity-90 disabled:opacity-50 text-sm">
          Откатить к #{{ selectedN }}
        </button>
      </div>

      <p v-if="note" class="text-sm text-blue-600 mt-3">{{ note }}</p>
    </template>
  </section>
</template>
