<script setup>
import { ref } from 'vue'
import AppButton from '../components/ui/kit/AppButton.vue'
import AppModal from '../components/ui/kit/AppModal.vue'
import AppField from '../components/ui/kit/AppField.vue'
import AppEmptyState from '../components/ui/kit/AppEmptyState.vue'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'

const { push } = useToast()
const { ask } = useConfirm()
const showModal = ref(false)
const text = ref('')
</script>

<template>
  <div class="min-h-screen bg-[#f5f5f7] text-gray-900 p-8 font-sans">
    <div class="max-w-4xl mx-auto flex flex-col gap-8">
      <h1 class="text-3xl font-bold">UI Kit</h1>

      <section class="bg-white rounded-2xl p-6 border border-gray-200">
        <h2 class="font-bold mb-3">Кнопки</h2>
        <div class="flex flex-wrap gap-2 items-center">
          <AppButton theme="light">Primary</AppButton>
          <AppButton theme="light" variant="secondary">Secondary</AppButton>
          <AppButton theme="light" variant="ghost">Ghost</AppButton>
          <AppButton theme="light" variant="danger">Danger</AppButton>
          <AppButton theme="light" variant="success">Success</AppButton>
          <AppButton theme="light" loading>Loading</AppButton>
          <AppButton theme="light" disabled>Disabled</AppButton>
          <AppButton theme="light" size="sm">sm</AppButton>
          <AppButton theme="light" size="lg">lg</AppButton>
        </div>
      </section>

      <section class="bg-white rounded-2xl p-6 border border-gray-200">
        <h2 class="font-bold mb-3">Поля</h2>
        <div class="grid grid-cols-2 gap-4">
          <AppField theme="light" label="Название" hint="Подсказка под полем">
            <input v-model="text" class="bg-gray-50 border border-gray-300 rounded-lg px-3 py-2" />
          </AppField>
          <AppField theme="light" label="С ошибкой" error="Обязательное поле">
            <input class="bg-gray-50 border border-red-300 rounded-lg px-3 py-2" />
          </AppField>
        </div>
      </section>

      <section class="bg-white rounded-2xl p-6 border border-gray-200">
        <h2 class="font-bold mb-3">Модал / Confirm / Toast</h2>
        <div class="flex gap-2">
          <AppButton theme="light" @click="showModal = true">Открыть модал</AppButton>
          <AppButton theme="light" variant="danger" @click="ask({ title: 'Удалить?', text: 'Действие необратимо.', danger: true }).then(v => push('Ответ: ' + v, 'info'))">Confirm</AppButton>
          <AppButton theme="light" variant="secondary" @click="push('Сохранено', 'success')">Toast success</AppButton>
          <AppButton theme="light" variant="secondary" @click="push('Ошибка сети', 'error')">Toast error</AppButton>
        </div>
      </section>

      <section class="bg-white rounded-2xl p-6 border border-gray-200">
        <h2 class="font-bold mb-3">Empty state</h2>
        <AppEmptyState theme="light" icon="🗂" title="Нет проектов" description="Создайте первый проект, чтобы начать.">
          <AppButton theme="light">Создать</AppButton>
        </AppEmptyState>
      </section>
    </div>

    <AppModal :show="showModal" title="Пример модала" theme="light" @close="showModal = false">
      <p class="text-sm text-gray-600">Контент модала. Введено: «{{ text }}»</p>
      <template #footer>
        <AppButton theme="light" variant="secondary" @click="showModal = false">Отмена</AppButton>
        <AppButton theme="light" @click="showModal = false; push('Готово', 'success')">ОК</AppButton>
      </template>
    </AppModal>
  </div>
</template>
