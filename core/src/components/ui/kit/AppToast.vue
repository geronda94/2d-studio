<script setup>
import { useToast } from '../../../composables/useToast'
const { toasts, dismiss } = useToast()

const styles = {
  info: 'bg-bg-surface border-text-muted text-text-primary',
  success: 'bg-color-success/15 border-color-success/40 text-color-success',
  warning: 'bg-color-warning/15 border-color-warning/40 text-color-warning',
  error: 'bg-red-500/15 border-red-500/40 text-red-400',
}
</script>

<template>
  <div class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[600] flex flex-col gap-2 items-center pointer-events-none">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="pointer-events-auto flex items-center gap-3 px-4 py-2.5 rounded-xl border shadow-2xl text-sm font-medium max-w-md backdrop-blur"
      :class="styles[t.type] || styles.info"
    >
      <span class="flex-1">{{ t.message }}</span>
      <button class="opacity-60 hover:opacity-100 font-bold" @click="dismiss(t.id)">✕</button>
    </div>
  </div>
</template>
