<script setup>
// AUTH_PLAN Ф3: аккаунт — смена пароля.
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/layout/AppShell.vue'
import { useAuth } from '../composables/useAuth'
import {
  changePassword, fetchApiKeys, createApiKey, revokeApiKey,
  fetchDelegations, requestDelegation, approveDelegation, revokeDelegation,
} from '../services/api'

const router = useRouter()
const { currentUser } = useAuth()

const current = ref('')
const next = ref('')
const next2 = ref('')
const error = ref('')
const ok = ref('')
const busy = ref(false)

// --- API-ключи ---
const keys = ref([])
const keysError = ref('')
const newKeyLabel = ref('')
const newKeyScopes = ref('read,write')
const createdKey = ref('')
const keyBusy = ref(false)

const loadKeys = async () => {
  keysError.value = ''
  try {
    keys.value = await fetchApiKeys()
  } catch (e) {
    keysError.value = e.message || 'Ошибка'
  }
}
onMounted(loadKeys)

const makeKey = async () => {
  keyBusy.value = true
  createdKey.value = ''
  keysError.value = ''
  try {
    const scopes = newKeyScopes.value.split(',').map((s) => s.trim()).filter(Boolean)
    const res = await createApiKey(newKeyLabel.value || 'agent', scopes)
    createdKey.value = res.key
    newKeyLabel.value = ''
    await loadKeys()
  } catch (e) {
    keysError.value = e.message || 'Ошибка'
  } finally {
    keyBusy.value = false
  }
}

const revoke = async (k) => {
  keyBusy.value = true
  try {
    await revokeApiKey(k.id)
    await loadKeys()
  } catch (e) {
    keysError.value = e.message || 'Ошибка'
  } finally {
    keyBusy.value = false
  }
}

// --- ENTERPRISE Ф3: боты и делегирования ---
const delegations = ref([])
const delegError = ref('')
const botName = ref('')
const botDelegate = ref(true)
const subjectEmail = ref('')
const selectedBotId = ref('')
const bots = computed(() => (keys.value || []).filter((k) => k.kind === 'service'))

const loadDelegations = async () => {
  try { delegations.value = await fetchDelegations() } catch (e) { delegError.value = e.message }
}
onMounted(loadDelegations)

const makeBot = async () => {
  keyBusy.value = true
  createdKey.value = ''
  keysError.value = ''
  try {
    const res = await createApiKey(botName.value || 'bot', ['read', 'write'], {
      kind: 'service', bot_name: botName.value || 'bot', can_delegate: botDelegate.value,
    })
    createdKey.value = res.key
    botName.value = ''
    await loadKeys()
    await loadDelegations()
  } catch (e) {
    keysError.value = e.message || 'Ошибка'
  } finally {
    keyBusy.value = false
  }
}

const reqDelegation = async () => {
  delegError.value = ''
  if (!selectedBotId.value || !subjectEmail.value.trim()) return
  try {
    await requestDelegation(Number(selectedBotId.value), subjectEmail.value.trim())
    subjectEmail.value = ''
    await loadDelegations()
  } catch (e) { delegError.value = e.message }
}

const approve = async (d) => {
  try { await approveDelegation(d.id); await loadDelegations() } catch (e) { delegError.value = e.message }
}
const revokeDeleg = async (d) => {
  try { await revokeDelegation(d.id); await loadDelegations() } catch (e) { delegError.value = e.message }
}

const submit = async () => {
  error.value = ''
  ok.value = ''
  if (next.value.length < 8) { error.value = 'Новый пароль минимум 8 символов'; return }
  if (next.value !== next2.value) { error.value = 'Пароли не совпадают'; return }
  busy.value = true
  try {
    await changePassword(current.value, next.value)
    ok.value = 'Пароль изменён. Другие сессии завершены.'
    current.value = next.value = next2.value = ''
  } catch (e) {
    error.value = e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AppShell :crumbs="[{ label: 'Проекты', to: '/' }, { label: 'Аккаунт' }]" title="Аккаунт" max-width="max-w-2xl">
    <section class="bg-white rounded-2xl border border-gray-200 p-5 md:p-6">
      <h2 class="text-lg font-bold text-gray-900 mb-1">Профиль</h2>
      <p class="text-sm text-gray-500 mb-4">
        {{ currentUser?.display_name || 'Без имени' }} · {{ currentUser?.email }}
      </p>

      <h3 class="text-sm font-bold text-gray-700 mb-3 mt-6">Смена пароля</h3>
      <form @submit.prevent="submit" class="space-y-3 max-w-md">
        <input v-model="current" type="password" required autocomplete="current-password" placeholder="Текущий пароль"
          class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-500" />
        <input v-model="next" type="password" required autocomplete="new-password" placeholder="Новый пароль"
          class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-500" />
        <input v-model="next2" type="password" required autocomplete="new-password" placeholder="Повторите новый пароль"
          class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:border-blue-500" />
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <p v-if="ok" class="text-sm text-green-600">{{ ok }}</p>
        <button type="submit" :disabled="busy"
          class="px-4 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:opacity-90 disabled:opacity-50 text-sm">
          {{ busy ? 'Сохраняю…' : 'Сменить пароль' }}
        </button>
      </form>

      <h3 class="text-sm font-bold text-gray-700 mb-2 mt-8">API-ключи</h3>
      <p class="text-xs text-gray-400 mb-3">Для агентов/скриптов. Ключ показывается один раз при создании.</p>
      <div class="flex flex-col sm:flex-row gap-2 max-w-lg">
        <input v-model="newKeyLabel" placeholder="метка (напр. agent)"
          class="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <input v-model="newKeyScopes" placeholder="read,write"
          class="w-32 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <button @click="makeKey" :disabled="keyBusy"
          class="px-4 py-2 rounded-xl font-bold text-white bg-gray-900 hover:opacity-90 disabled:opacity-50 text-sm">Создать</button>
      </div>
      <div v-if="createdKey" class="mt-3 p-3 rounded-xl bg-green-50 border border-green-200 text-xs break-all">
        <div class="font-bold text-green-800 mb-1">Скопируй ключ — он больше не покажется:</div>
        <code>{{ createdKey }}</code>
      </div>
      <p v-if="keysError" class="text-sm text-red-500 mt-2">{{ keysError }}</p>

      <ul class="mt-3 divide-y divide-gray-100 max-w-lg">
        <li v-for="k in keys" :key="k.id" class="flex items-center gap-3 py-2">
          <div class="min-w-0 flex-1">
            <div class="text-sm text-gray-900 truncate">{{ k.label || 'без метки' }}</div>
            <div class="text-xs text-gray-400">{{ (k.scopes || []).join(', ') }} · {{ k.is_active ? 'активен' : 'отозван' }}</div>
          </div>
          <button v-if="k.is_active" @click="revoke(k)" :disabled="keyBusy"
            class="text-xs text-red-500 hover:text-red-700 font-semibold">Отозвать</button>
        </li>
      </ul>
      <p v-if="!keys.length" class="text-sm text-gray-400 mt-2">Ключей пока нет.</p>

      <h3 class="text-sm font-bold text-gray-700 mb-2 mt-10">Боты и делегирования</h3>
      <p class="text-xs text-gray-400 mb-3">
        Бот — технический аккаунт. Действует от имени пользователя только после его одобрения.
        Боту запрещены owner-операции (стиль, команда, передача владения).
      </p>

      <div class="flex flex-col sm:flex-row gap-2 max-w-lg items-center">
        <input v-model="botName" placeholder="имя бота (напр. AI-редактор)"
          class="flex-1 min-w-0 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
        <label class="flex items-center gap-2 text-xs text-gray-600 shrink-0">
          <input type="checkbox" v-model="botDelegate" /> может действовать от имени
        </label>
        <button @click="makeBot" :disabled="keyBusy"
          class="px-4 py-2 rounded-xl font-bold text-white bg-indigo-600 hover:opacity-90 disabled:opacity-50 text-sm shrink-0">Создать бота</button>
      </div>

      <div v-if="bots.length" class="mt-4 max-w-lg">
        <div class="text-xs uppercase font-bold text-gray-400 mb-2">Запросить делегирование</div>
        <div class="flex flex-col sm:flex-row gap-2">
          <select v-model="selectedBotId" class="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-white">
            <option value="">— бот —</option>
            <option v-for="b in bots" :key="b.id" :value="b.owner_id">{{ b.label || ('bot #' + b.owner_id) }}</option>
          </select>
          <input v-model="subjectEmail" type="email" placeholder="email пользователя"
            class="flex-1 min-w-0 border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
          <button @click="reqDelegation" class="px-4 py-2 rounded-xl font-bold text-white bg-gray-900 hover:opacity-90 text-sm">Запросить</button>
        </div>
      </div>

      <p v-if="delegError" class="text-sm text-red-500 mt-2">{{ delegError }}</p>

      <ul class="mt-4 divide-y divide-gray-100 max-w-lg">
        <li v-for="d in delegations" :key="d.id" class="flex items-center gap-3 py-2">
          <div class="min-w-0 flex-1">
            <div class="text-sm text-gray-900">Бот #{{ d.bot_user_id }} → пользователь #{{ d.subject_user_id }}</div>
            <div class="text-xs" :class="d.revoked ? 'text-gray-400' : (d.approved ? 'text-green-600' : 'text-amber-600')">
              {{ d.revoked ? 'отозвано' : (d.approved ? 'одобрено' : 'ожидает одобрения') }}
              <span v-if="d.project_id"> · проект #{{ d.project_id }}</span>
            </div>
          </div>
          <button v-if="!d.approved && !d.revoked && currentUser?.id === d.subject_user_id"
            @click="approve(d)" class="text-xs text-green-600 font-semibold px-2">Одобрить</button>
          <button v-if="!d.revoked" @click="revokeDeleg(d)"
            class="text-xs text-red-500 font-semibold px-2">Отозвать</button>
        </li>
      </ul>
      <p v-if="!delegations.length" class="text-sm text-gray-400 mt-2">Делегирований пока нет.</p>
    </section>
  </AppShell>
</template>
