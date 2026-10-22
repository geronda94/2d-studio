<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const { register } = useAuth()

const email = ref('')
const displayName = ref('')
const password = ref('')
const password2 = ref('')
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  if (password.value.length < 8) {
    error.value = 'Пароль минимум 8 символов'
    return
  }
  if (password.value !== password2.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  loading.value = true
  try {
    await register(email.value, password.value, displayName.value)
    router.replace(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message || 'Не удалось зарегистрироваться'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-dvh bg-[#f5f5f7] flex items-center justify-center p-4 font-sans">
    <div class="w-full max-w-sm">
      <div class="bg-white rounded-2xl shadow-xl border border-gray-200 p-6 md:p-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Регистрация</h1>
        <p class="text-sm text-gray-500 mb-6">Аккаунт нужен для создания и редактирования презентаций</p>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Email</label>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-900 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Имя</label>
            <input
              v-model="displayName"
              type="text"
              autocomplete="name"
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-900 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Пароль</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="new-password"
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-900 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Повторите пароль</label>
            <input
              v-model="password2"
              type="password"
              required
              autocomplete="new-password"
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-900 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 rounded-xl font-bold text-white bg-blue-600 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {{ loading ? 'Создаю…' : 'Создать аккаунт' }}
          </button>
        </form>

        <p class="text-sm text-gray-500 mt-5 text-center">
          Уже есть аккаунт?
          <router-link to="/login" class="text-blue-600 font-semibold hover:underline">Войти</router-link>
        </p>
      </div>
    </div>
  </div>
</template>
