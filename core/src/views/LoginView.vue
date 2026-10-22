<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const { login } = useAuth()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  loading.value = true
  try {
    await login(email.value, password.value)
    router.replace(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message || 'Не удалось войти'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-dvh bg-[#f5f5f7] flex items-center justify-center p-4 font-sans">
    <div class="w-full max-w-sm">
      <div class="bg-white rounded-2xl shadow-xl border border-gray-200 p-6 md:p-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Вход</h1>
        <p class="text-sm text-gray-500 mb-6">Войдите, чтобы создавать и редактировать презентации</p>

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
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Пароль</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-900 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 rounded-xl font-bold text-white bg-blue-600 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {{ loading ? 'Вхожу…' : 'Войти' }}
          </button>
        </form>

        <p class="text-sm text-gray-500 mt-5 text-center">
          Нет аккаунта?
          <router-link to="/register" class="text-blue-600 font-semibold hover:underline">Зарегистрироваться</router-link>
        </p>
      </div>

      <p class="text-xs text-gray-400 text-center mt-4">
        Просмотр презентаций по ссылке доступен без входа.
      </p>
    </div>
  </div>
</template>
