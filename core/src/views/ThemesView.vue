<script setup>
import { ref, onMounted } from 'vue'
import AppShell from '../components/layout/AppShell.vue'
import { fetchPalettesSummary, fetchProjectsSummary, copyPalette, forkProject } from '../services/api'

const palettes = ref([])
const projects = ref([])
const loading = ref(true)
const target = ref({})     // slug палитры -> id проекта
const busy = ref({})
const msg = ref({})

const load = async () => {
  loading.value = true
  try {
    const [pal, proj] = await Promise.all([fetchPalettesSummary(), fetchProjectsSummary()])
    palettes.value = pal || []
    projects.value = (proj || []).filter((p) => !p.is_template)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
onMounted(load)

const isTemplate = (p) => p.is_template === true

const applyTo = async (p) => {
  const pid = target.value[p.slug]
  if (!pid || busy.value[p.slug]) return
  if (pid === p.id) {
    msg.value[p.slug] = 'Это тот же проект — выбери другой'
    return
  }
  busy.value[p.slug] = true
  msg.value[p.slug] = ''
  try {
    const res = await copyPalette(pid, p.slug)
    msg.value[p.slug] = `Применено: ${res.copied} токенов`
  } catch (e) { msg.value[p.slug] = e.message }
  finally { busy.value[p.slug] = false }
}

const fork = async (p) => {
  if (busy.value[p.slug]) return
  const title = prompt(`Название моей темы (копия «${p.title}»):`, `${p.title} (моя)`)
  if (title === null) return
  busy.value[p.slug] = true
  try {
    const created = await forkProject(p.id, title || undefined)
    msg.value[p.slug] = `Создана тема «${created.title}»`
    palettes.value = (await fetchPalettesSummary()) || []
  } catch (e) { msg.value[p.slug] = e.message }
  finally { busy.value[p.slug] = false }
}
</script>

<template>
  <AppShell
    :crumbs="[{ label: 'Проекты', to: '/' }, { label: 'Темы' }]"
    title="Темы"
    subtitle="Готовые палитры и ваши фирменные темы. Возьмите тему в проект или сохраните себе копию."
  >
    <div v-if="loading" class="text-gray-500 py-12 text-center">Загрузка…</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <div v-for="p in palettes" :key="p.slug" class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                :class="isTemplate(p) ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'">
            {{ isTemplate(p) ? 'Библиотека' : 'Моя тема' }}
          </span>
          <h3 class="font-bold text-gray-900 leading-tight">{{ p.title }}</h3>
        </div>
        <p class="text-xs text-gray-500 font-light line-clamp-2 flex-1">{{ p.description }}</p>

        <select v-model="target[p.slug]" class="w-full bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option :value="undefined" disabled>Применить в проект…</option>
          <option v-for="pr in projects.filter((x) => x.id !== p.id)" :key="pr.id" :value="pr.id">{{ pr.title }}</option>
        </select>
        <div class="flex gap-2">
          <button
            @click="applyTo(p)"
            :disabled="!target[p.slug] || busy[p.slug]"
            class="flex-1 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-bold transition-colors"
          >
            {{ busy[p.slug] ? '…' : 'Применить' }}
          </button>
          <button
            @click="fork(p)"
            :disabled="busy[p.slug]"
            class="px-3 py-2 bg-white hover:bg-gray-100 disabled:opacity-50 text-gray-700 border border-gray-200 rounded-lg text-sm font-medium transition-colors"
            title="Сохранить как мою тему"
          >
            ⧉ Форк
          </button>
        </div>
        <p v-if="msg[p.slug]" class="text-xs text-gray-500">{{ msg[p.slug] }}</p>
      </div>
    </div>
  </AppShell>
</template>
