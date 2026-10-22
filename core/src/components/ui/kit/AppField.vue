<script setup>
// Поле формы: label + control(slot) + hint/error (UX kit).
const props = defineProps({
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  theme: { type: String, default: 'dark' },
})
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-xs font-bold uppercase tracking-wider"
           :class="theme === 'light' ? 'text-gray-500' : 'text-text-secondary'">{{ label }}</label>
    <slot />
    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
    <p v-else-if="hint" class="text-xs" :class="theme === 'light' ? 'text-gray-400' : 'text-text-muted'">{{ hint }}</p>
  </div>
</template>
