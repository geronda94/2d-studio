<script setup>
// AUTH_PLAN Ф5: админка пользователей (только супер-админ).
import { ref, onMounted } from 'vue'
import AppShell from '../components/layout/AppShell.vue'
import { useAuth } from '../composables/useAuth'
import { fetchAdminUsers, updateAdminUser, resetUserPassword } from '../services/api'

const { currentUser, ensureLoaded } = useAuth()
const users = ref([])
const loading = ref(true)
const error = ref('')
const note = ref('')
const busyId = ref(null)

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    users.value = await fetchAdminUsers()
  } catch (e) {
    error.value = e.message || 'Нет доступа'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await ensureLoaded()
  if (currentUser.value?.is_superadmin) await load()
  else loading.value = false
})

const toggleActive = async (u) => {
  busyId.value = u.id
  note.value = ''
  try {
    const upd = await updateAdminUser(u.id, { is_active: !u.is_active })
    u.is_active = upd.is_active
  } catch (e) { note.value = e.message } finally { busyId.value = null }
}

const toggleAdmin = async (u) => {
  busyId.value = u.id
  note.value = ''
  try {
    const upd = await updateAdminUser(u.id, { is_superadmin: !u.is_superadmin })
    u.is_superadmin = upd.is_superadmin
  } catch (e) { note.value = e.message } finally { busyId.value = null }
}

const doReset = async (u) => {
  const pw = prompt(`Новый пароль для ${u.email} (мин. 8 символов):`)
  if (!pw) return
  busyId.value = u.id
  note.value = ''
  try {
    await resetUserPassword(u.id, pw)
    note.value = `Пароль для ${u.email} изменён, все его сессии завершены.`
  } catch (e) { note.value = e.message } finally { busyId.value = null }
}

const fmt = (s) => (s ? new Date(s).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' }) : '—')
</script>

<template>
  <AppShell :crumbs="[{ label: 'Проекты', to: '/' }, { label: 'Пользователи' }]" title="Пользователи" max-width="max-w-4xl">
    <div v-if="!currentUser?.is_superadmin" class="bg-white rounded-2xl border border-gray-200 p-6 text-gray-500">
      Доступ только у администратора.
    </div>

    <section v-else class="bg-white rounded-2xl border border-gray-200 p-5 md:p-6">
      <p v-if="loading" class="text-sm text-gray-400">Загружаю…</p>
      <p v-else-if="error" class="text-sm text-red-500">{{ error }}</p>
      <template v-else>
        <!-- Мобильные карточки (таблица ниже — только md+) -->
        <div class="md:hidden divide-y divide-gray-100">
          <div v-for="u in users" :key="'m'+u.id" class="py-3">
            <div class="font-medium text-gray-900 truncate">{{ u.display_name || '—' }}</div>
            <div class="text-xs text-gray-400 truncate mb-2">{{ u.email }}</div>
            <div class="flex items-center gap-2 flex-wrap">
              <button @click="toggleAdmin(u)" :disabled="busyId === u.id"
                class="text-[10px] uppercase font-bold px-2 py-1 rounded-lg"
                :class="u.is_superadmin ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'">
                {{ u.is_superadmin ? 'Админ' : 'Пользователь' }}
              </button>
              <button @click="toggleActive(u)" :disabled="busyId === u.id"
                class="text-[10px] uppercase font-bold px-2 py-1 rounded-lg"
                :class="u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'">
                {{ u.is_active ? 'Активен' : 'Заблокирован' }}
              </button>
              <span class="text-[11px] text-gray-400">{{ fmt(u.last_login_at) }}</span>
              <button @click="doReset(u)" :disabled="busyId === u.id"
                class="ml-auto text-xs text-gray-500 hover:text-blue-600 font-semibold">Сменить пароль</button>
            </div>
          </div>
        </div>

        <div class="overflow-x-auto hidden md:block">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs uppercase tracking-wider text-gray-400 border-b border-gray-100">
                <th class="py-2 pr-3">Пользователь</th>
                <th class="py-2 px-3">Роль</th>
                <th class="py-2 px-3">Статус</th>
                <th class="py-2 px-3">Последний вход</th>
                <th class="py-2 pl-3"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" class="border-b border-gray-50">
                <td class="py-3 pr-3">
                  <div class="font-medium text-gray-900 truncate max-w-[240px]">{{ u.display_name || '—' }}</div>
                  <div class="text-xs text-gray-400 truncate max-w-[240px]">{{ u.email }}</div>
                </td>
                <td class="py-3 px-3">
                  <button
                    @click="toggleAdmin(u)"
                    :disabled="busyId === u.id"
                    class="text-[10px] uppercase font-bold px-2 py-1 rounded-lg transition-colors"
                    :class="u.is_superadmin ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
                  >{{ u.is_superadmin ? 'Админ' : 'Пользователь' }}</button>
                </td>
                <td class="py-3 px-3">
                  <button
                    @click="toggleActive(u)"
                    :disabled="busyId === u.id"
                    class="text-[10px] uppercase font-bold px-2 py-1 rounded-lg transition-colors"
                    :class="u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
                  >{{ u.is_active ? 'Активен' : 'Заблокирован' }}</button>
                </td>
                <td class="py-3 px-3 text-xs text-gray-400">{{ fmt(u.last_login_at) }}</td>
                <td class="py-3 pl-3 text-right">
                  <button @click="doReset(u)" :disabled="busyId === u.id" class="text-xs text-gray-500 hover:text-blue-600 font-semibold">Сменить пароль</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="note" class="text-sm text-blue-600 mt-3">{{ note }}</p>
      </template>
    </section>
  </AppShell>
</template>
