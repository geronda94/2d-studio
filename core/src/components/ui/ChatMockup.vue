<script setup lang="ts">
import { getColorAlpha } from '../../utils/colors'
import { ref, watch, nextTick, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

export interface Message {
 id?: string | number
 text: string
 sender?: 'bot' | 'user'
 role?: 'bot' | 'user' | 'assistant'
 isError?: boolean
 image?: string
 start_time?: number
}

const props = defineProps({
 title: { type: String, default: 'Chat' },
 botName: { type: String, default: 'Telegram Bot' },
 botSubtitle: { type: String, default: 'bot' },
 botAvatar: { type: String, default: 'T' },
 messages: {
 type: Array as () => Message[],
 default: () => []
 },
  mode: { type: String, default: 'auto' },
  clicks: { type: Number, default: 0 },
  mobile: { type: Boolean, default: false },
  variant: { type: String, default: undefined }
})

const { itemVars } = useVariant(computed(() => props.variant), 'ChatMockup')

const messagesContainer = ref<HTMLElement | null>(null)
const relativeTime = inject('relativeTime', ref(0))

// Сигнал родителю (Slide.vue): чат занимает половину экрана, поэтому слайд
// перестраивается в layout='row' (заголовок слева, чат справа). Без этого
// на десктопе чат растягивается на всю ширину и «плывёт» по центру.
const setSlideLayout = inject('setSlideLayout', null) as Function | null
if (setSlideLayout) {
 setSlideLayout('row')
}

watch(() => props.messages, async () => {
 await nextTick()
 if (messagesContainer.value) {
 messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
 }
}, { deep: true })

const getMessageStyle = (msg: Message, index: number) => {
 const threshold = msg.start_time ?? (index * 500)
 
 if (relativeTime.value < threshold) {
 return { opacity: 0, transform: 'translateY(20px) scale(0.95)', willChange: 'opacity, transform' }
 }
 
 const duration = 400
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 1) {
 return { opacity: 1, transform: 'translateY(0px) scale(1)', willChange: 'auto' }
 }
 
 // easeOutBack approximation
 const c1 = 1.70158
 const c3 = c1 + 1
 const p = progress - 1
 const ease = 1 + c3 * Math.pow(p, 3) + c1 * Math.pow(p, 2)
 
 return {
 opacity: Math.min(1, Math.max(0, progress * 1.5)).toFixed(4), // Opacity fades linearly faster
 transform: `translateY(${((1 - ease) * 20).toFixed(4)}px) scale(${(0.95 + 0.05 * ease).toFixed(4)})`,
 willChange: 'opacity, transform'
 }
}
</script>

<template>
  <div class="chat-mockup overflow-hidden flex flex-col relative mx-auto" 
  :class="mobile ? 'w-full h-full flex-1' : 'w-full max-w-[680px] h-full max-h-[560px] min-h-0 my-auto'"
  :style="{ 
    ...itemVars,
    background: 'var(--item-bg)',
    backdropFilter: 'var(--item-backdrop)',
    borderRadius: 'var(--item-radius)',
    boxShadow: 'var(--item-shadow)',
    padding: 'var(--item-padding)',
    borderWidth: 'var(--item-border-width)',
    borderStyle: 'var(--item-border-style)',
    borderColor: 'var(--item-border)'
  }">
 
  <!-- Header -->
  <div class="h-12 md:h-16 flex items-center px-3 md:px-4 gap-3 shrink-0 z-20" style="background: var(--item-bg); border-bottom: 1px solid var(--item-border);">
  <div class="w-8 h-8 md:w-10 md:h-10 flex flex-col items-center justify-center font-bold text-base md:text-lg overflow-hidden shrink-0"
 :style="{ borderRadius: 'var(--item-radius)', background: getColorAlpha('var(--color-primary)', 0.1), color: 'var(--color-primary)' }">
 <img v-if="botAvatar && (botAvatar.startsWith('http') || botAvatar.startsWith('/'))" :src="botAvatar" class="w-full h-full object-cover" />
 <template v-else>{{ botAvatar || 'T' }}</template>
 </div>
 <div class="flex-1 flex flex-col overflow-hidden">
 <span class="font-bold text-text-primary leading-tight truncate font-heading">{{ botName || title }}</span>
 <span class="text-xs uppercase tracking-wider font-mono truncate" :style="{ color: 'var(--text-secondary)' }">{{ botSubtitle }}</span>
 </div>
 <Icon icon="lucide:more-vertical" class="text-text-muted text-xl cursor-pointer hover:text-text-primary " />
 </div>

 <div class="relative flex-1 flex flex-col min-h-0">
 <!-- Background pattern -->
 <div class="absolute inset-0 z-0 opacity-10 pointer-events-none" style="background-image: url('data:image/svg+xml,%3Csvg width=\'20\' height=\'20\' viewBox=\'0 0 20 20\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'1\' fill-rule=\'evenodd\'%3E%3Ccircle cx=\'3\' cy=\'3\' r=\'1.5\'/%3E%3Ccircle cx=\'13\' cy=\'13\' r=\'1.5\'/%3E%3C/g%3E%3C/svg%3E'); background-size: 20px 20px;"></div>
 
  <div ref="messagesContainer" class="flex-1 overflow-y-auto p-2 gap-2 md:p-4 md:gap-4 flex flex-col custom-scrollbar scroll-smooth relative z-10 pb-2 md:pb-4">
 <div class="mt-auto"></div>
 <div v-for="(msg, i) in messages" :key="msg.id || i" 
 class="flex items-end max-w-[85%]"
 :class="(msg.sender === 'user' || msg.role === 'user') ? 'self-end' : 'self-start'"
 :style="getMessageStyle(msg, i)">
 
   <div class="px-3 py-2 text-xs md:px-4 md:py-3 md:text-sm leading-relaxed whitespace-pre-wrap break-words"
  :class="[
   (msg.sender === 'user' || msg.role === 'user') 
   ? '' 
   : (msg.isError ? 'bg-red-500/20 text-red-100' : 'text-text-primary')
   ]"
   :style="{ 
   background: (msg.sender === 'user' || msg.role === 'user') ? 'var(--color-primary)' : (msg.isError ? undefined : getColorAlpha('var(--text-primary)', 0.1)),
   color: (msg.sender === 'user' || msg.role === 'user') ? 'var(--text-on-color)' : undefined,
   borderRadius: 'var(--item-radius)'
   }">
   <img v-if="msg.image" :src="msg.image" class="max-w-full max-h-28 md:max-h-48 object-cover mb-2" :style="{ borderRadius: 'var(--item-radius)' }" />
 <span class="font-sans">{{ msg.text }}</span>
 </div>
 </div>
 </div>
 </div>
 
 <!-- Chat Input Mockup -->
  <div class="h-12 md:h-16 flex items-center px-3 md:px-4 gap-3 shrink-0 relative z-20" style="background: var(--item-bg); border-top: 1px solid var(--item-border);">
  <Icon icon="lucide:paperclip" class="w-5 h-5 text-text-muted hover:text-text-primary cursor-pointer transition-colors shrink-0" />
  <div class="flex-1 h-8 md:h-10 flex items-center px-4"
  :style="{ borderRadius: 'var(--item-radius)', background: 'rgb(var(--bg-base-rgb) / 0.45)' }">
  <span class="text-text-muted text-[13px]">Сообщение...</span>
  </div>
   <div class="w-9 h-9 flex items-center justify-center shrink-0 cursor-pointer"
   :style="{ borderRadius: 'var(--item-radius)', background: 'var(--color-primary)', color: 'var(--text-on-color)' }">
 <Icon icon="lucide:send" class="w-4 h-4" />
 </div>
 </div>
 </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
 width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
 background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
 background: rgb(var(--text-primary-rgb) / 0.1);
 border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
 background: rgb(var(--color-secondary-rgb) / 0.5);
}
.scroll-smooth {
 scroll-behavior: smooth;
}
</style>
