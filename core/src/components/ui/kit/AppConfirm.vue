<script setup>
import { useConfirm } from '../../../composables/useConfirm'
import AppModal from './AppModal.vue'
import AppButton from './AppButton.vue'
const { state, resolve } = useConfirm()
</script>

<template>
  <AppModal :show="state.open" :title="state.title" theme="dark" max-width="max-w-sm" @close="resolve(false)">
    <p v-if="state.text" class="text-sm text-text-secondary">{{ state.text }}</p>
    <template #footer>
      <AppButton variant="secondary" @click="resolve(false)">{{ state.cancelText }}</AppButton>
      <AppButton :variant="state.danger ? 'danger' : 'primary'" @click="resolve(true)">{{ state.okText }}</AppButton>
    </template>
  </AppModal>
</template>
