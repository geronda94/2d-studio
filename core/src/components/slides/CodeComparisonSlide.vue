<script setup>
import { computed, inject, ref } from 'vue'
import CodeWindow from '../ui/CodeWindow.vue'

const props = defineProps({
 mobile: Boolean,
 variant: String,
 windows: { type: Array, default: () => [] }
})

const relativeTime = inject('relativeTime', ref(0))

const isVisible = (windowObj) => {
 return relativeTime.value >= (windowObj.start_time || 0)
}
</script>

<template>
 <div :class="mobile ? 'flex flex-col gap-6 mt-4 w-full text-left relative py-2' : 'flex justify-center gap-12 w-full h-full max-w-[1400px] px-4 mx-auto'">
 <div 
 v-for="(win, idx) in windows" 
 :key="idx"
 :class="mobile ? 'text-center px-4 min-w-0 flex flex-col' : 'text-center px-4 min-w-0 flex flex-col flex-1 max-w-[600px] h-full'" 
 :style="{
 opacity: isVisible(win) ? Math.min(1, (relativeTime - (win.start_time || 0)) / 700) : 0,
 transform: isVisible(win) ? `translateY(${Math.max(0, 32 - (relativeTime - (win.start_time || 0)) / 700 * 32)}px)` : 'translateY(32px)'
 }"
 >
 <h3 class="truncate font-bold shrink-0" :style="{ color: win.color }" :class="mobile ? '!text-base mb-2' : 'mb-3 font-heading text-xl'">{{ win.title }}</h3>
 <div class="min-h-0 flex-1" :class="mobile ? '' : 'cc-window'">
 <CodeWindow 
 :mobile="mobile" 
 :variant="variant"
 :title="win.file" 
 :code="win.code" 
 :lang="win.language || win.lang"
 :typing="win.typing"
 :typing-start="win.start_time || 0"
 :startTyping="isVisible(win)"
 />
 </div>
 </div>
 </div>
</template>

<style scoped>
/* Оба окна одинаковой высоты во всю доступную область — у короткого кода
   не остаётся «огрызка», у длинного нет переполнения. */
.cc-window :deep(.code-window) {
 height: 100%;
 display: flex;
 flex-direction: column;
}
.cc-window :deep(.code-window > div) {
 height: 100%;
 display: flex;
 flex-direction: column;
}
.cc-window :deep(.content) {
 max-height: none;
 flex: 1 1 auto;
}
</style>
