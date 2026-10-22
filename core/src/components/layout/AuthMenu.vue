<script setup>
// AUTH_PLAN Ф1: компактное меню пользователя в админ-рамке.
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const router = useRouter()
const { currentUser, authMode, ensureLoaded, logout } = useAuth()
const open = ref(false)

onMounted(() => ensureLoaded())
const close = () => { open.value = false }
onMounted(() => window.addEventListener('click', close))
onUnmounted(() => window.removeEventListener('click', close))

const initials = computed(() => {
  const n = currentUser.value?.display_name || currentUser.value?.email || '?'
  return n.trim().charAt(0).toUpperCase()
})

const doLogout = async () => {
  open.value = false
  await logout()
  router.push('/login')
}
</script>

<template>
  <div class="relative" @click.stop>
    <button
      v-if="currentUser"
      @click="open = !open"
      class="flex items-center gap-2 rounded-full border border-gray-200 bg-white/80 hover:bg-white px-2 py-1.5 transition-colors"
      :title="currentUser.email"
    >
      <span class="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">{{ initials }}</span>
      <span class="hidden sm:block text-sm text-gray-700 max-w-[140px] truncate">{{ currentUser.display_name || currentUser.email }}</span>
    </button>

    <router-link
      v-else
      to="/login"
      class="rounded-full bg-blue-600 text-white text-sm font-semibold px-4 py-2 hover:opacity-90 transition-opacity"
    >
      Войти
    </router-link>

    <div
      v-if="open && currentUser"
      class="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-xl py-1 z-50"
    >
      <div class="px-3 py-2 border-b border-gray-100">
        <div class="text-sm font-semibold text-gray-900 truncate">{{ currentUser.display_name || 'Без имени' }}</div>
        <div class="text-xs text-gray-400 truncate">{{ currentUser.email }}</div>
        <div v-if="currentUser.is_superadmin" class="text-[10px] uppercase font-bold text-blue-600 mt-1">Администратор</div>
      </div>
      <router-link to="/" @click="close" class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">Мои проекты</router-link>
      <router-link to="/account" @click="close" class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">Аккаунт</router-link>
      <router-link v-if="currentUser.is_superadmin" to="/admin/users" @click="close" class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">Пользователи</router-link>
      <button @click="doLogout" class="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-gray-50">Выйти</button>
      <div v-if="authMode !== 'on'" class="px-3 py-2 text-[10px] text-gray-400 border-t border-gray-100">
        Режим прав: {{ authMode }}
      </div>
    </div>
  </div>
</template>
