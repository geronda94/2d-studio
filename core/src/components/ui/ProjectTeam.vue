<script setup>
// AUTH_PLAN Ф2: команда проекта. Владелец приглашает помощников с ролями:
// editor — правит контент (слайды/данные/медиа/AI), viewer — только смотрит.
// Тема/палитра и управление командой — только у владельца.
import { ref, onMounted } from 'vue'
import {
  fetchProjectMembers, addProjectMember, updateProjectMember,
  removeProjectMember, transferProject, fetchProjectFolders,
} from '../../services/api'
import { useAuth } from '../../composables/useAuth'

const props = defineProps({
  projectId: { type: Number, required: true },
})

const { currentUser } = useAuth()
const loading = ref(true)
const error = ref('')
const owner = ref(null)
const members = ref([])
const newEmail = ref('')
const newRole = ref('editor')
const newScope = ref(null)
const folders = ref([])
const busy = ref(false)
const note = ref('')

const isOwner = () => {
  if (!currentUser.value) return false
  if (currentUser.value.is_superadmin) return true
  return owner.value && owner.value.user_id === currentUser.value.id
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const [data, fl] = await Promise.all([
      fetchProjectMembers(props.projectId),
      fetchProjectFolders(props.projectId),
    ])
    owner.value = data.owner
    members.value = data.members || []
    folders.value = fl || []
  } catch (e) {
    error.value = e.message || 'Не удалось загрузить команду'
  } finally {
    loading.value = false
  }
}

const add = async () => {
  if (!newEmail.value.trim() || busy.value) return
  busy.value = true
  note.value = ''
  try {
    await addProjectMember(props.projectId, newEmail.value.trim(), newRole.value, newScope.value)
    newEmail.value = ''
    await load()
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

const changeRole = async (m, role) => {
  if (busy.value) return
  busy.value = true
  try {
    await updateProjectMember(props.projectId, m.user_id, role, m.scope_folder_id)
    m.role = role
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

const changeScope = async (m, raw) => {
  if (busy.value) return
  const scope = raw === '' ? null : Number(raw)
  busy.value = true
  try {
    await updateProjectMember(props.projectId, m.user_id, m.role, scope)
    m.scope_folder_id = scope
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

const remove = async (m) => {
  if (busy.value) return
  busy.value = true
  try {
    await removeProjectMember(props.projectId, m.user_id)
    await load()
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

const transfer = async (m) => {
  if (busy.value) return
  if (!confirm(`Передать владение проектом пользователю ${m.email}? Вы потеряете права владельца.`)) return
  busy.value = true
  try {
    await transferProject(props.projectId, m.email)
    await load()
  } catch (e) {
    note.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="bg-white rounded-2xl border border-gray-200 p-5 md:p-6">
    <div class="flex items-center justify-between mb-1">
      <h2 class="text-lg font-bold text-gray-900">Команда</h2>
      <span v-if="isOwner()" class="text-[10px] uppercase font-bold text-blue-600">владелец</span>
    </div>
    <p class="text-sm text-gray-500 mb-4">
      Помощники с доступом к проекту. <b>Редактор</b> правит контент, <b>наблюдатель</b> — только смотрит.
      Тема и палитра доступны только владельцу.
    </p>

    <p v-if="loading" class="text-sm text-gray-400">Загружаю…</p>
    <p v-else-if="error" class="text-sm text-gray-400">{{ error }}</p>
    <template v-else>
      <div class="flex items-center gap-3 py-2 border-b border-gray-100">
        <span class="w-8 h-8 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
          {{ (owner?.display_name || owner?.email || 'S')[0].toUpperCase() }}
        </span>
        <div class="min-w-0 flex-1">
          <div class="text-sm font-semibold text-gray-900 truncate">{{ owner?.display_name || 'Системный проект' }}</div>
          <div class="text-xs text-gray-400 truncate">{{ owner?.email || 'владелец не назначен' }}</div>
        </div>
        <span class="text-[10px] uppercase font-bold text-gray-400">Владелец</span>
      </div>

      <div v-for="m in members" :key="m.user_id" class="flex items-center gap-3 py-2 border-b border-gray-100">
        <span class="w-8 h-8 rounded-full bg-gray-200 text-gray-600 text-xs font-bold flex items-center justify-center shrink-0">
          {{ (m.display_name || m.email || '?')[0].toUpperCase() }}
        </span>
        <div class="min-w-0 flex-1">
          <div class="text-sm text-gray-900 truncate">{{ m.display_name || m.email }}</div>
          <div class="text-xs text-gray-400 truncate">{{ m.email }}</div>
        </div>
        <template v-if="isOwner()">
          <select
            :value="m.role"
            @change="changeRole(m, $event.target.value)"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700"
          >
            <option value="editor">Редактор</option>
            <option value="viewer">Наблюдатель</option>
          </select>
          <select
            v-if="folders.length"
            :value="m.scope_folder_id ?? ''"
            @change="changeScope(m, $event.target.value)"
            class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700 max-w-[130px]"
            title="Ограничить доступ папкой"
          >
            <option value="">Все папки</option>
            <option v-for="f in folders" :key="f.id" :value="f.id">{{ f.title }}</option>
          </select>
          <button @click="transfer(m)" class="text-xs text-gray-400 hover:text-blue-600 px-1" title="Передать владение">⇪</button>
          <button @click="remove(m)" class="text-xs text-gray-400 hover:text-red-500 px-1" title="Удалить">✕</button>
        </template>
        <span v-else class="text-[10px] uppercase font-bold text-gray-400">{{ m.role }}</span>
      </div>

      <p v-if="!members.length" class="text-sm text-gray-400 py-3">Пока никого. Добавьте помощника по email.</p>

      <div v-if="isOwner()" class="flex flex-col sm:flex-row gap-2 mt-4">
        <input
          v-model="newEmail"
          type="email"
          placeholder="email помощника"
          class="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500"
        />
        <select v-model="newRole" class="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-white">
          <option value="editor">Редактор</option>
          <option value="viewer">Наблюдатель</option>
        </select>
        <select v-if="folders.length" v-model="newScope" class="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-white max-w-[150px]">
          <option :value="null">Все папки</option>
          <option v-for="f in folders" :key="f.id" :value="f.id">{{ f.title }}</option>
        </select>
        <button
          @click="add"
          :disabled="busy"
          class="px-4 py-2 rounded-xl font-bold text-white bg-blue-600 hover:opacity-90 disabled:opacity-50 text-sm"
        >
          Добавить
        </button>
      </div>
      <p v-if="note" class="text-sm text-red-500 mt-2">{{ note }}</p>
    </template>
  </section>
</template>
