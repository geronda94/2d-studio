<script setup>
// Пустое состояние (UX kit).
defineProps({
  icon: { type: String, default: '✦' },
  title: { type: String, default: 'Пусто' },
  description: { type: String, default: '' },
  theme: { type: String, default: 'dark' },
})
</script>

<template>
  <div class="text-center py-12 px-6 rounded-2xl border border-dashed"
       :class="theme === 'light' ? 'border-gray-300 text-gray-500' : 'border-text-muted text-text-secondary'">
    <div class="text-4xl mb-3 opacity-70">{{ icon }}</div>
    <h3 class="text-lg font-bold mb-1" :class="theme === 'light' ? 'text-gray-800' : 'text-text-primary'">{{ title }}</h3>
    <p v-if="description" class="text-sm font-light max-w-md mx-auto mb-4">{{ description }}</p>
    <slot />
  </div>
</template>
