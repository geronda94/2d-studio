<script setup>
// Единый модал (UX kit). theme: 'dark' (по умолчанию) | 'light'.
const props = defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  theme: { type: String, default: 'dark' },
  maxWidth: { type: String, default: 'max-w-lg' },
  closeOnBackdrop: { type: Boolean, default: true },
})
const emit = defineEmits(['close'])

const panel = () => props.theme === 'light'
  ? 'bg-white border-gray-200 text-gray-900'
  : 'bg-bg-surface border-text-muted text-text-primary'
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-[300] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeOnBackdrop && emit('close')"></div>
    <div class="relative border rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[88vh]" :class="[panel(), maxWidth]">
      <div v-if="title || $slots.header" class="flex items-center justify-between p-5 border-b"
           :class="theme === 'light' ? 'border-gray-200' : 'border-text-muted'">
        <slot name="header"><h2 class="text-lg font-bold">{{ title }}</h2></slot>
        <button class="text-xl leading-none px-1 opacity-70 hover:opacity-100" @click="emit('close')" title="Закрыть">✕</button>
      </div>
      <div class="p-5 overflow-y-auto">
        <slot />
      </div>
      <div v-if="$slots.footer" class="p-4 border-t flex justify-end gap-3"
           :class="theme === 'light' ? 'border-gray-200' : 'border-text-muted'">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
