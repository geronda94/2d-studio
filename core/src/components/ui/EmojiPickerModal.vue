<template>
  <div v-if="isOpen" class="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-bg-base border border-text-muted rounded-2xl w-full max-w-sm flex flex-col shadow-2xl relative" v-click-outside="() => $emit('close')">
      <!-- Header -->
      <div class="p-4 border-b border-text-muted flex justify-between items-center bg-bg-surface rounded-t-2xl">
        <h3 class="text-lg font-bold text-text-primary">Выбрать Эмодзи</h3>
        <button @click="$emit('close')" class="p-1 text-text-secondary hover:text-text-primary transition-colors">
          <Icon icon="heroicons:x-mark" class="text-xl" />
        </button>
      </div>

      <!-- Emojis Grid -->
      <div class="p-4 grid grid-cols-6 gap-2 max-h-[300px] overflow-y-auto custom-scrollbar">
        <button 
          v-for="(emoji, index) in emojis" 
          :key="index"
          @click="$emit('select', emoji)"
          class="text-2xl hover:bg-bg-surface rounded-lg p-2 transition-colors flex items-center justify-center"
        >
          {{ emoji }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Icon } from '@iconify/vue'

defineProps({
  isOpen: Boolean
})

defineEmits(['close', 'select'])

// Базовый набор популярных эмодзи
const emojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩',
  '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗',
  '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈',
  '👍', '👎', '👏', '🙌', '👐', '🤲', '🤝', '🤜', '🤛', '🤞', '✌️', '🤟', '🤘', '👌', '🤏', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐', '🖖', '👋', '🤙', '💪', '🦾', '🖕', '✍️',
  '🙏', '❤️', '🔥', '✨', '⭐', '🌟', '💥', '🚀', '💻', '📱', '✅', '❌', '💡', '🤖', '👾', '🎉', '🎊', '🎈', '💸', '💰'
]
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgb(var(--text-primary-rgb) / 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(var(--text-primary-rgb) / 0.1);
  border-radius: 4px;
}
</style>
