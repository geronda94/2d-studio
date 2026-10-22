<script setup>
import { ref, computed, onMounted } from 'vue'
import RenderManagerModal from '../components/ui/RenderManagerModal.vue'
import AppShell from '../components/layout/AppShell.vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchProjectSummary, createFolder, updateFolder, deleteFolder, fetchProjectColors } from '../services/api'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const folders = ref([])
const loading = ref(true)
const projectColors = ref([])

const showRenderManagerModal = ref(false)
const selectedRenderFolderId = ref(null)

const openRenderManager = (folder) => {
  selectedRenderFolderId.value = folder.id
  showRenderManagerModal.value = true
}

const showCreateFolderModal = ref(false)
const newFolderName = ref('')
const createFolderLoading = ref(false)

const showConfirmDeleteModal = ref(false)
const folderToDelete = ref(null)

const renamingFolder = ref(null)
const renamingFolderName = ref('')

onMounted(async () => {
  try {
    const slug = route.params.slug
    project.value = await fetchProjectSummary(slug)
    folders.value = project.value.folders

    // Fetch project colors
    try {
      projectColors.value = await fetchProjectColors(project.value.id)
    } catch (e) {
      console.error('Failed to fetch project colors', e)
    }
  } catch (err) {
    console.error('Failed to fetch project:', err)
    router.push('/')
  } finally {
    loading.value = false
  }
})

const headerGradient = computed(() => {
  if (projectColors.value.length === 0) return 'linear-gradient(to right, #2563EB, #6366F1)'
  
  const getVal = (name) => projectColors.value.find(c => c.name === name)?.value
  
  const brandLight = getVal('brand-light-blue') || getVal('brand-lightBlue') || '#38bdf8'
  const brandDark = getVal('brand-blue') || getVal('text-primary') || '#2563eb'
  
  return `linear-gradient(to right, ${brandLight}, ${brandDark})`
})

const handleCreateFolder = async () => {
  if (!newFolderName.value.trim()) return
  createFolderLoading.value = true
  try {
    const newFolder = await createFolder(project.value.id, {
      title: newFolderName.value.trim(),
      slug: '' // Backend will generate
    })
    folders.value.push(newFolder)
    showCreateFolderModal.value = false
    newFolderName.value = ''
  } catch (err) {
    console.error('Failed to create folder:', err)
  } finally {
    createFolderLoading.value = false
  }
}

const confirmDelete = (folder) => {
  folderToDelete.value = folder
  showConfirmDeleteModal.value = true
}

const executeDelete = async () => {
  if (!folderToDelete.value) return
  try {
    await deleteFolder(folderToDelete.value.id)
    folders.value = folders.value.filter(f => f.id !== folderToDelete.value.id)
    showConfirmDeleteModal.value = false
    folderToDelete.value = null
  } catch (err) {
    console.error('Failed to delete folder:', err)
  }
}

const startRenaming = (folder) => {
  renamingFolder.value = folder
  renamingFolderName.value = folder.title
}

const handleRename = async () => {
  if (!renamingFolderName.value.trim() || !renamingFolder.value) return
  try {
    const updated = await updateFolder(renamingFolder.value.id, {
      title: renamingFolderName.value.trim()
    })
    const index = folders.value.findIndex(f => f.id === updated.id)
    if (index !== -1) {
      folders.value[index].title = updated.title
    }
    renamingFolder.value = null
  } catch (err) {
    console.error('Failed to rename folder:', err)
  }
}
</script>

<template>
  <AppShell
    :crumbs="[{ label: 'Проекты', to: '/' }, { label: project?.title || 'Загрузка…' }]"
  >
    <template #title>
      Проект:
      <span v-if="loading" class="inline-block h-8 w-56 rounded-lg bg-gray-200 animate-pulse align-middle"></span>
      <span v-else class="text-transparent bg-clip-text" :style="{ backgroundImage: headerGradient }">{{ project.title }}</span>
    </template>
    <template #actions>
      <router-link
        v-if="!loading"
        :to="`/project/${project.slug}/settings`"
        class="px-6 py-3 bg-white hover:bg-gray-100 text-gray-700 border border-gray-200 rounded-xl font-medium transition-colors shadow-sm"
        title="Все настройки проекта: общее, стили, палитра"
      >
        ⚙️ Настройки
      </router-link>
      <button
        v-if="!loading"
        @click="showCreateFolderModal = true"
        class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-sm"
      >
        + Создать папку
      </button>
    </template>

      <PageSkeleton v-if="loading" variant="folders" :count="6" />

      <template v-else>
      <!-- Folders Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div
          v-for="folder in folders"
          :key="folder.id"
          class="group relative rounded-xl bg-white border border-gray-200 p-6 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 flex flex-col justify-between h-48"
        >

          <!-- Action buttons (visible on hover) -->
          <div class="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click="openRenderManager(folder)"
              class="p-1.5 bg-white border border-gray-200 hover:border-green-400 hover:text-green-600 text-gray-500 rounded-md transition-colors shadow-sm"
              title="Рендер-ферма"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            </button>
            <button
              @click="startRenaming(folder)"
              class="p-1.5 bg-white border border-gray-200 hover:border-blue-400 hover:text-blue-600 text-gray-500 rounded-md transition-colors shadow-sm"
              title="Переименовать"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
            </button>
            <button
              @click="confirmDelete(folder)"
              class="p-1.5 bg-white border border-gray-200 hover:border-red-400 hover:text-red-500 text-gray-500 rounded-md transition-colors shadow-sm"
              title="Удалить"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>

          <!-- Folder content -->
          <div class="flex-1 cursor-pointer" @click="router.push(`/folder/${folder.slug}`)">
            <div class="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            </div>

            <template v-if="renamingFolder?.id === folder.id">
              <input
                type="text"
                v-model="renamingFolderName"
                @blur="handleRename"
                @keyup.enter="handleRename"
                class="w-full bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 text-xl font-bold mb-2 focus:outline-none focus:border-blue-500"
                @click.stop
                autofocus
              >
            </template>
            <template v-else>
              <h3 class="text-xl font-bold text-gray-800 mb-2 line-clamp-1" :title="folder.title">{{ folder.title }}</h3>
            </template>
          </div>

          <div class="text-sm text-gray-400 mt-2">
            Презентаций: {{ folder.presentations_count ?? folder.presentations?.length ?? 0 }}
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="folders.length === 0" class="text-center py-20 bg-white rounded-2xl border border-gray-200 shadow-sm mt-8">
        <div class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4 text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
        </div>
        <h3 class="text-xl font-medium text-gray-800 mb-2">Нет папок</h3>
        <p class="text-gray-500 mb-6 max-w-md mx-auto">В этом проекте пока нет ни одной папки. Создайте первую, чтобы начать работу.</p>
        <button @click="showCreateFolderModal = true" class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
          Создать папку
        </button>
      </div>
      </template>

    <!-- Create Folder Modal -->
    <div v-if="showCreateFolderModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h3 class="text-xl font-bold text-gray-900 mb-4">Создать папку</h3>
        <input
          type="text"
          v-model="newFolderName"
          placeholder="Название папки"
          class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 mb-6"
          @keyup.enter="handleCreateFolder"
          autofocus
        >
        <div class="flex justify-end gap-3">
          <button @click="showCreateFolderModal = false" class="px-4 py-2 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors">Отмена</button>
          <button
            @click="handleCreateFolder"
            :disabled="!newFolderName.trim() || createFolderLoading"
            class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors font-medium"
          >
            {{ createFolderLoading ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <div v-if="showConfirmDeleteModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white border border-gray-200 rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Архивировать папку?</h3>
        <p class="text-gray-500 mb-6">Папка "<span class="text-gray-900 font-medium">{{ folderToDelete?.title }}</span>" больше не будет отображаться. Вы уверены?</p>
        <div class="flex justify-end gap-3">
          <button @click="showConfirmDeleteModal = false" class="px-4 py-2 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors">Отмена</button>
          <button @click="executeDelete" class="px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors font-medium">
            В архив
          </button>
        </div>
      </div>
    </div>
  </AppShell>

  <RenderManagerModal
    :isOpen="showRenderManagerModal"
    :presentationId="selectedRenderFolderId"
    @close="showRenderManagerModal = false"
  />
</template>
