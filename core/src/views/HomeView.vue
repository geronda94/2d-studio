<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProjectsSummary, fetchProjectColors, createProject } from '../services/api'
import AuthMenu from '../components/layout/AuthMenu.vue'
import StudioMenu from '../components/layout/StudioMenu.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const router = useRouter()
const projects = ref([])
const loading = ref(true)
const loadError = ref(false)
const projectColors = ref({}) // { [project.id]: string[] }
const colorsLoading = ref({}) // { [project.id]: boolean }

// Новый проект из шаблона палитры (UX-1)
const showCreateProject = ref(false)
const newProject = ref({ title: '', description: '', template: 'it2b' })
const templates = ref([])
const creatingProject = ref(false)
const createProjectError = ref('')
const showGuide = ref(localStorage.getItem('hideGuide') !== '1')
watch(showGuide, (v) => localStorage.setItem('hideGuide', v ? '0' : '1'))

const openCreateProject = async () => {
  createProjectError.value = ''
  newProject.value = { title: '', description: '', template: 'it2b' }
  showCreateProject.value = true
  try {
    const all = await fetchProjectsSummary()
    templates.value = all.filter(p => p.slug === 'it2b' || p.slug === 'history' || p.slug === 'derevnya')
    if (!templates.value.length) templates.value = all.slice(0, 3)
  } catch {
    templates.value = []
  }
}

const submitCreateProject = async () => {
  if (!newProject.value.title.trim() || creatingProject.value) return
  creatingProject.value = true
  createProjectError.value = ''
  try {
    const project = await createProject(newProject.value)
    showCreateProject.value = false
    router.push(`/project/${project.slug}`)
  } catch (e) {
    createProjectError.value = e.message
  } finally {
    creatingProject.value = false
  }
}

onMounted(async () => {
  try {
    projects.value = await fetchProjectsSummary()
    loading.value = false
    // Load colors for each project concurrently
    projects.value.forEach(project => {
      colorsLoading.value[project.id] = true
    })
    await Promise.all(
      projects.value.map(async (project) => {
        try {
          const colors = await fetchProjectColors(project.id)
          projectColors.value[project.id] = colors // Store the full array of color objects
        } catch (err) {
          console.error(`Failed to fetch colors for project ${project.id}:`, err)
          projectColors.value[project.id] = []
        } finally {
          colorsLoading.value[project.id] = false
        }
      })
    )
  } catch (err) {
    console.error('Failed to fetch projects:', err)
    loading.value = false
    loadError.value = true
  }
})

const getTheme = (projectId) => {
  const colors = projectColors.value[projectId] || []
  const getVal = (nameRegex) => {
    const c = colors.find(col => nameRegex.test(col.name))
    return c ? c.value : null
  }
  
  // Try to find semantic colors, fallback to defaults
  const bgBase = getVal(/^bg-base$/i) || '#ffffff'
  const bgSurface = getVal(/^bg-surface$/i) || '#f3f4f6'
  const textPrimary = getVal(/^text-primary$/i) || '#111827'
  const textSecondary = getVal(/^text-secondary$/i) || '#6b7280'
  const brand = getVal(/^brand-(blue|primary|accent|green|red|amber)$/i) || '#3b82f6'
  
  return { bgBase, bgSurface, textPrimary, textSecondary, brand }
}

const getDisplayColors = (projectId) => {
  const colors = projectColors.value[projectId]
  if (!colors) return []
  return colors
    .map(c => c.value)
    .filter(val => val && !val.startsWith('rgba') && !val.includes('gradient'))
    .slice(0, 5)
}
</script>

<template>
  <div class="min-h-dvh bg-[#f5f5f7] text-gray-900 p-4 md:p-12 font-sans">
    <div class="max-w-6xl mx-auto">

      <!-- Быстрая навигация -->
      <div class="flex justify-end items-center gap-3">
        <StudioMenu />
        <router-link
          to="/themes"
          class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors shadow-sm"
        >
          Темы
        </router-link>
        <AuthMenu />
      </div>

      <!-- Header -->
      <header class="flex flex-col items-center justify-center text-center mb-16 mt-8">
        <!-- Status badge -->
        <div class="inline-flex items-center gap-3 px-5 py-2 rounded-full bg-white border border-gray-200 shadow-sm mb-8">
          <span class="relative flex h-2.5 w-2.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
          </span>
          <span class="text-xs font-semibold tracking-[0.2em] uppercase text-gray-600">Engine Online</span>
        </div>

        <h1 class="text-4xl md:text-7xl font-bold tracking-tight mb-6 text-gray-900">
          YouTube Studio
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-500">Core</span>
        </h1>

        <p class="text-lg md:text-xl text-gray-600 max-w-2xl font-light leading-relaxed">
          Центральный пульт управления. Выберите проект, чтобы начать работу с папками и презентациями.
        </p>
      </header>

      <!-- Студии: новые инструменты -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <a href="/character-studio.html" target="_blank" rel="noopener"
           class="group bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
          <div class="text-[10px] font-bold tracking-[0.18em] text-blue-600 mb-2">2D CAST</div>
          <div class="font-bold text-gray-900 group-hover:text-blue-700">Paper Cast Studio</div>
          <div class="text-sm text-gray-500 mt-1">Canvas-персонажи: общий риг, 31 поза, 82 фонемы, липсинк и эмоции.</div>
        </a>
        <a href="/character-builder.html" target="_blank" rel="noopener"
           class="group bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
          <div class="text-[10px] font-bold tracking-[0.18em] text-blue-600 mb-2">BUILDER</div>
          <div class="font-bold text-gray-900 group-hover:text-blue-700">Конструктор персонажа</div>
          <div class="text-sm text-gray-500 mt-1">Пропорции, лицо, причёски, гардероб и животные: 10 видов скелетов.</div>
        </a>
        <a href="/pose-studio.html" target="_blank" rel="noopener"
           class="group bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
          <div class="text-[10px] font-bold tracking-[0.18em] text-blue-600 mb-2">POSES</div>
          <div class="font-bold text-gray-900 group-hover:text-blue-700">Pose Studio</div>
          <div class="text-sm text-gray-500 mt-1">Кости, лимиты, пресеты, A→B и библиотека жестов.</div>
        </a>
        <a href="/p/1" target="_blank" rel="noopener"
           class="group bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
          <div class="text-[10px] font-bold tracking-[0.18em] text-blue-600 mb-2">SCENES</div>
          <div class="font-bold text-gray-900 group-hover:text-blue-700">Демо-сцены</div>
          <div class="text-sm text-gray-500 mt-1">Движок презентаций и 2D/2.5D сцены в одном месте.</div>
        </a>
        <a href="/themes" target="_blank" rel="noopener"
           class="group bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
          <div class="text-[10px] font-bold tracking-[0.18em] text-blue-600 mb-2">THEMES</div>
          <div class="font-bold text-gray-900 group-hover:text-blue-700">Темы</div>
          <div class="text-sm text-gray-500 mt-1">Палитры и оформление проектов.</div>
        </a>
      </div>

      <!-- Онбординг: как начать -->
      <div class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-10">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-bold text-gray-900">С чего начать</h2>
          <button @click="showGuide = false" v-if="showGuide" class="text-gray-400 hover:text-gray-700 text-sm" title="Скрыть">✕</button>
        </div>
        <ol v-if="showGuide" class="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
          <li class="flex gap-2 items-start">
            <span class="w-6 h-6 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center shrink-0">1</span>
            <span class="text-gray-600">Задайте <router-link to="/themes" class="text-blue-600 hover:underline">тему</router-link> проекта: палитра и конфиг формы</span>
          </li>
          <li class="flex gap-2 items-start">
            <span class="w-6 h-6 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center shrink-0">2</span>
            <span class="text-gray-600">Заполните <b>бриф</b> в настройках проекта (⚙ → Бриф)</span>
          </li>
          <li class="flex gap-2 items-start">
            <span class="w-6 h-6 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center shrink-0">3</span>
            <span class="text-gray-600">Создайте презентацию и слайды (или через «✨ AI»)</span>
          </li>
          <li class="flex gap-2 items-start">
            <span class="w-6 h-6 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center shrink-0">4</span>
            <span class="text-gray-600">Озвучьте и экспортируйте (⚙ в плеере → Рендер)</span>
          </li>
        </ol>
        <p v-else class="text-sm text-gray-400">Скрыто. <button @click="showGuide = true" class="text-blue-600 hover:underline">Показать снова</button></p>
      </div>

      <!-- Горячие клавиши плеера -->
      <div class="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm mb-10 text-xs text-gray-500 flex flex-wrap gap-x-5 gap-y-2 items-center">
        <span class="font-bold text-gray-700 text-sm">Горячие клавиши в плеере:</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">P</kbd> пуск/пауза</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">M</kbd> мобильный</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">S</kbd> панель слайдов</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">E</kbd> редактировать</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">F</kbd> полный экран</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">R</kbd> экспорт</span>
        <span><kbd class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200 font-mono">D</kbd> отладка</span>
      </div>

      <!-- Projects Grid -->
      <h2 class="text-2xl font-bold text-gray-900 mb-5">Мои проекты</h2>

      <PageSkeleton v-if="loading" variant="cards" :count="4" />

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">

        <!-- New project card -->
        <button
          @click="openCreateProject"
          class="group flex flex-col items-center justify-center h-[28rem] rounded-3xl border-2 border-dashed border-gray-300 hover:border-blue-500 hover:bg-blue-50/50 transition-all duration-300 text-gray-600 hover:text-blue-700"
        >
          <span class="text-5xl font-light mb-3">+</span>
          <span class="font-bold">Новый проект</span>
          <span class="text-sm font-light mt-1">из шаблона палитры</span>
        </button>

        <router-link
          v-for="project in projects.filter(p => !p.is_template)"
          :key="project.slug"
          :to="`/project/${project.slug}`"
          class="group block bg-white border border-gray-200 rounded-3xl shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden cursor-pointer flex flex-col h-[28rem]"
        >
          <!-- Theme Preview Header (Top half) -->
          <div class="h-48 relative p-4 flex flex-col justify-end overflow-hidden transition-colors duration-500" :style="{ backgroundColor: getTheme(project.id).bgBase }">
             <!-- Skeleton overlay while loading -->
             <div v-if="colorsLoading[project.id]" class="absolute inset-0 bg-gray-100 animate-pulse z-20"></div>
             
             <!-- Mini UI Dashboard Preview -->
             <div class="absolute inset-x-6 top-6 bottom-0 rounded-t-2xl shadow-2xl p-5 flex flex-col gap-4 transform group-hover:translate-y-2 transition-transform duration-500 border-t border-l border-r border-white/10" 
                  :style="{ backgroundColor: getTheme(project.id).bgSurface }">
                <!-- Mock Header -->
                <div class="flex justify-between items-center">
                   <div class="w-1/3 h-3 rounded-full opacity-80" :style="{ backgroundColor: getTheme(project.id).brand }"></div>
                   <div class="flex gap-1">
                      <div class="w-2 h-2 rounded-full opacity-40" :style="{ backgroundColor: getTheme(project.id).textSecondary }"></div>
                      <div class="w-2 h-2 rounded-full opacity-40" :style="{ backgroundColor: getTheme(project.id).textSecondary }"></div>
                      <div class="w-2 h-2 rounded-full opacity-40" :style="{ backgroundColor: getTheme(project.id).textSecondary }"></div>
                   </div>
                </div>
                <!-- Mock Content -->
                <div class="space-y-2.5 mt-2" data-audit-ignore>
                   <div class="w-3/4 h-5 rounded-md opacity-90" :style="{ backgroundColor: getTheme(project.id).textPrimary }"></div>
                   <div class="w-1/2 h-3 rounded-md opacity-60" :style="{ backgroundColor: getTheme(project.id).textSecondary }"></div>
                </div>
                <!-- Mock Footer/Palette -->
                <div class="mt-auto flex justify-end items-end" data-audit-ignore>
                   <!-- Mock Button -->
                   <div class="px-4 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-wider text-gray-900 shadow-sm" :style="{ backgroundColor: getTheme(project.id).brand }">
                      View
                   </div>
                </div>
             </div>
          </div>

          <!-- Project Details (Bottom half) -->
          <div class="p-8 flex flex-col flex-1 bg-white relative z-10 border-t border-gray-100">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: getTheme(project.id).brand }"></div>
              <div class="text-xs font-bold uppercase tracking-[0.15em] text-gray-600">Проект</div>
            </div>
            <h2 class="text-2xl font-bold text-gray-900 mb-3">{{ project.title }}</h2>
            <p class="text-gray-600 text-sm mb-6 flex-1 font-light leading-relaxed line-clamp-2">{{ project.description }}</p>

            <div class="flex items-center justify-between pt-4 border-t border-gray-100">
               <div class="text-xs font-semibold text-gray-600">
                  <span v-if="getDisplayColors(project.id).length">{{ getDisplayColors(project.id).length }} Styles</span>
                  <span v-else>Default Theme</span>
               </div>
              <div class="flex items-center gap-1.5 text-gray-600 group-hover:text-blue-700 transition-colors font-medium text-sm">
                <span>Открыть</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transform group-hover:translate-x-1 transition-transform">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </div>
            </div>
          </div>
        </router-link>

      </div>

      <!-- Create project dialog -->
      <div
        v-if="showCreateProject"
        class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showCreateProject = false"
      >
        <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-md shadow-xl">
          <h3 class="text-xl font-bold text-gray-900 mb-4">Новый проект</h3>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Название</label>
          <input
            v-model="newProject.title"
            placeholder="Мой проект"
            class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 mb-4"
            @keyup.enter="submitCreateProject"
            autofocus
          >
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Описание</label>
          <input
            v-model="newProject.description"
            placeholder="О чём проект (необязательно)"
            class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 mb-4"
          >
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Палитра-шаблон</label>
          <select
            v-model="newProject.template"
            class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 mb-4"
          >
            <option v-for="t in templates" :key="t.slug" :value="t.slug">{{ t.title }}</option>
          </select>
          <p v-if="createProjectError" class="text-sm text-red-600 mb-4">{{ createProjectError }}</p>
          <div class="flex justify-end gap-3">
            <button @click="showCreateProject = false" class="px-4 py-2 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors">Отмена</button>
            <button
              @click="submitCreateProject"
              :disabled="!newProject.title.trim() || creatingProject"
              class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors font-medium"
            >
              {{ creatingProject ? 'Создание...' : 'Создать' }}
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
