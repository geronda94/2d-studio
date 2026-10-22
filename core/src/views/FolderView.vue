<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchFolderSummary, createPresentation, deletePresentation, updatePresentation, fetchProjectColors, restorePresentation } from '../services/api'
import AppShell from '../components/layout/AppShell.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const route = useRoute()
const router = useRouter()

const folderId = computed(() => route.params.id)
const folder = ref(null)
const loading = ref(true)
const loadError = ref(false)
const projectColors = ref([])

const showCreateModal = ref(false)
const newPresentationTitle = ref('')
const createLoading = ref(false)
const createError = ref('')

const showConfirmDeleteModal = ref(false)
const presentationToDelete = ref(null)

const renamingPresentation = ref(null)
const renamingTitle = ref('')

const showArchived = ref(false)
const projectBackLink = computed(() => folder.value?.project_slug ? `/project/${folder.value.project_slug}` : '/')

const restoreFromArchive = async (p, e) => {
  e.stopPropagation()
  try {
    await restorePresentation(p.id)
    await loadFolder()
  } catch (err) {
    console.error('Failed to restore presentation:', err)
  }
}

const loadFolder = async () => {
  loading.value = true
  try {
    folder.value = await fetchFolderSummary(folderId.value, showArchived.value)
    loadError.value = false
    if (folder.value?.project_id) {
      projectColors.value = await fetchProjectColors(folder.value.project_id)
    }
  } catch (err) {
    console.error('Failed to fetch folder:', err)
    loadError.value = true
    folder.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadFolder)

watch(showArchived, loadFolder)
watch(folderId, loadFolder)

watch(showCreateModal, (open) => {
  if (open) createError.value = ''
})

const handleCreatePresentation = async () => {
  if (!folder.value || !newPresentationTitle.value.trim()) return
  createLoading.value = true
  try {
    const newPres = await createPresentation({
      title: newPresentationTitle.value.trim(),
      folder_id: folder.value.id
    })
    showCreateModal.value = false
    newPresentationTitle.value = ''
    router.push(`/p/${newPres.id}`)
  } catch (e) {
    createError.value = 'Ошибка при создании презентации'
  } finally {
    createLoading.value = false
  }
}

const confirmDelete = (presentation) => {
  presentationToDelete.value = presentation
  showConfirmDeleteModal.value = true
}

const executeDelete = async () => {
  if (!presentationToDelete.value) return
  try {
    await deletePresentation(presentationToDelete.value.id)
    await loadFolder()
    showConfirmDeleteModal.value = false
    presentationToDelete.value = null
  } catch (err) {
    console.error('Failed to delete presentation:', err)
  }
}

const startRenaming = (presentation) => {
  renamingPresentation.value = presentation
  renamingTitle.value = presentation.title
}

const handleRename = async () => {
  if (!renamingTitle.value.trim() || !renamingPresentation.value) return
  try {
    await updatePresentation(renamingPresentation.value.id, {
      title: renamingTitle.value.trim()
    })
    await loadFolder()
    renamingPresentation.value = null
  } catch (err) {
    console.error('Failed to rename presentation:', err)
  }
}

const goBack = () => {
  router.push(projectBackLink.value)
}

const getColorVal = (name) => projectColors.value.find(c => c.name === name)?.value

const headerGradient = computed(() => {
  if (projectColors.value.length === 0) return 'linear-gradient(to right, #2563EB, #6366F1)'

  const brandLight = getColorVal('brand-light-blue') || getColorVal('brand-lightBlue') || '#38bdf8'
  const brandDark = getColorVal('brand-blue') || getColorVal('text-primary') || '#2563eb'

  return `linear-gradient(to right, ${brandLight}, ${brandDark})`
})

const dotColor = computed(() =>
  getColorVal('bg-surface') || getColorVal('brand-blue') || '#2563eb'
)
</script>

<template>
  <!-- Ошибка загрузки -->
  <div v-if="!loading && loadError" class="min-h-screen bg-[#f5f5f7] flex items-center justify-center text-gray-900">
    <div class="text-center">
      <h2 class="text-2xl font-bold mb-4 text-gray-800">Не удалось загрузить папку</h2>
      <button @click="loadFolder" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">Повторить</button>
      <div class="mt-3"><button @click="router.push('/')" class="text-gray-500 hover:underline text-sm">На главную</button></div>
    </div>
  </div>

  <!-- Not found state -->
  <div v-else-if="!loading && !folder" class="min-h-screen bg-[#f5f5f7] flex items-center justify-center text-gray-900">
    <div class="text-center">
      <h2 class="text-2xl font-bold mb-4 text-gray-800">Папка не найдена</h2>
      <button @click="router.push('/')" class="text-blue-600 hover:underline">На главную</button>
    </div>
  </div>

  <!-- Main content: рамка видна сразу, контент подменяется скелетоном -->
  <AppShell
    v-else
    :crumbs="[{ label: 'Проекты', to: '/' }, { label: 'Папки', to: projectBackLink }, { label: folder?.title || 'Загрузка…' }]"
  >
    <template #title>
      <span v-if="loading" class="inline-block h-8 w-56 rounded-lg bg-gray-200 animate-pulse align-middle"></span>
      <span v-else class="text-transparent bg-clip-text" :style="{ backgroundImage: headerGradient }">{{ folder.title }}</span>
    </template>
    <template #subtitle>{{ folder?.desc || '' }}</template>
    <template #actions>
      <button
        @click="showArchived = !showArchived"
        :disabled="loading"
        class="flex-shrink-0 px-4 py-3 rounded-xl font-medium transition-colors shadow-sm border disabled:opacity-50"
        :class="showArchived ? 'bg-gray-800 text-white border-gray-800' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100'"
        :title="showArchived ? 'Скрыть архив' : 'Показать архивные презентации'"
      >
        🗄 Архив
      </button>
      <button
        @click="showCreateModal = true"
        :disabled="loading"
        class="flex-shrink-0 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-sm disabled:opacity-50"
      >
        + Создать презентацию
      </button>
    </template>

      <PageSkeleton v-if="loading" variant="cards" :count="8" />

      <template v-else>
      <!-- Presentations Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">

        <div
          v-for="presentation in folder.presentations"
          :key="presentation.id"
          class="group relative rounded-xl border p-5 shadow-sm transition-all duration-300 flex flex-col h-48 justify-between"
          :class="presentation.is_archived ? 'bg-gray-100 border-gray-200 opacity-80' : 'bg-white border-gray-200 hover:shadow-md hover:-translate-y-0.5'"
        >

          <!-- Archived badge -->
          <span v-if="presentation.is_archived" class="absolute top-3 left-3 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-gray-300 text-gray-700">архив</span>

          <!-- Action buttons -->
          <div class="absolute top-3 right-3 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              v-if="presentation.is_archived"
              @click="restoreFromArchive(presentation, $event)"
              class="p-1.5 bg-white border border-gray-200 hover:border-green-400 hover:text-green-600 text-gray-500 rounded-md transition-colors shadow-sm"
              title="Восстановить из архива"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
            </button>
            <button
              @click="startRenaming(presentation)"
              class="p-1.5 bg-white border border-gray-200 hover:border-blue-400 hover:text-blue-600 text-gray-400 rounded-md transition-colors shadow-sm"
              title="Переименовать"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
            </button>
            <button
              @click="confirmDelete(presentation)"
              class="p-1.5 bg-white border border-gray-200 hover:border-red-400 hover:text-red-500 text-gray-400 rounded-md transition-colors shadow-sm"
              title="Удалить"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>

          <!-- Presentation content -->
          <div class="flex-1 cursor-pointer" @click="router.push(`/p/${presentation.id}`)">
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
              :class="folder.theme === 'blue' ? 'bg-blue-50 text-blue-600' : 'bg-indigo-50 text-indigo-500'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            </div>

            <template v-if="renamingPresentation?.id === presentation.id">
              <input
                type="text"
                v-model="renamingTitle"
                @blur="handleRename"
                @keyup.enter="handleRename"
                class="w-full bg-gray-50 border border-gray-300 rounded px-2 py-1 text-gray-900 font-bold focus:outline-none focus:border-blue-500"
                @click.stop
                autofocus
              >
            </template>
            <template v-else>
              <h3 class="text-base font-bold text-gray-800 mb-1 line-clamp-2 leading-tight" :title="presentation.title">{{ presentation.title }}</h3>
            </template>
          </div>

          <div class="text-xs text-gray-400">
            Слайдов: {{ presentation.slides_count ?? presentation.slides?.length ?? 0 }}
            <span v-if="presentation.is_archived" class="ml-2 text-gray-500">· в архиве</span>
          </div>
        </div>

      </div>

      <!-- Empty state -->
      <div v-if="!folder.presentations?.length" class="text-center py-20 bg-white rounded-2xl border border-gray-200 shadow-sm mt-8">
        <div class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4 text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
        </div>
        <h3 class="text-xl font-medium text-gray-800 mb-2">Нет презентаций</h3>
        <p class="text-gray-500 mb-6 max-w-md mx-auto">В этой папке пока нет презентаций. Создайте первую, чтобы начать работу.</p>
        <button @click="showCreateModal = true" class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
          Создать презентацию
        </button>
      </div>
      </template>

    <!-- Create Presentation Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h3 class="text-xl font-bold text-gray-900 mb-4">Создать презентацию</h3>
        <p v-if="createError" class="text-sm text-red-600 mb-4">{{ createError }}</p>
        <input
          type="text"
          v-model="newPresentationTitle"
          placeholder="Название презентации"
          class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 mb-6"
          @keyup.enter="handleCreatePresentation"
          autofocus
        >
        <div class="flex justify-end gap-3">
          <button @click="showCreateModal = false" class="px-4 py-2 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors">Отмена</button>
          <button
            @click="handleCreatePresentation"
            :disabled="!newPresentationTitle.trim() || createLoading"
            class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors font-medium"
          >
            {{ createLoading ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <div v-if="showConfirmDeleteModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Удалить презентацию?</h3>
        <p class="text-gray-500 mb-6">Презентация "<span class="text-gray-900 font-medium">{{ presentationToDelete?.title }}</span>" будет перемещена в архив. Вы уверены?</p>
        <div class="flex justify-end gap-3">
          <button @click="showConfirmDeleteModal = false" class="px-4 py-2 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors">Отмена</button>
          <button @click="executeDelete" class="px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors font-medium">
            В архив
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
