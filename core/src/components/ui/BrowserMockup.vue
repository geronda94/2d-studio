<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { useVariant } from '../../composables/useVariant'
import WindowHeader from './WindowHeader.vue'

export interface BrowserItem {
 id?: string
 url: string
 type: 'image' | 'html'
 content: string
 scroll?: boolean
 scroll_duration?: number
 scroll_amount?: number
 image_position?: string
 start_time?: number
}

const props = defineProps<{
 items?: BrowserItem[]
 url?: string // fallback
 mobile?: boolean
 variant?: string
}>()

const { itemVars } = useVariant(computed(() => props.variant), 'BrowserMockup')

const relativeTime = inject('relativeTime', ref(0))

// Default fallback items if none provided
const actualItems = computed(() => {
 if (props.items && props.items.length > 0) return props.items
 return [{
 url: props.url || 'https://example.com',
 type: 'html',
 content: '<div class="text-center text-text-muted font-mono border-2 border-dashed border-text-muted rounded-2xl p-10 w-full max-w-md mx-auto mt-20"><p>Web Application Content Here</p></div>',
 start_time: 0
 }] as BrowserItem[]
})

// Find active item index based on relativeTime
const activeIndex = computed(() => {
 let activeIdx = 0
 for (let i = 0; i < actualItems.value.length; i++) {
 const t = actualItems.value[i].start_time || 0
 if (relativeTime.value >= t) {
 activeIdx = i
 }
 }
 return activeIdx
})

const activeItem = computed(() => actualItems.value[activeIndex.value])

const currentStartTime = computed(() => {
 return activeItem.value.start_time || 0
})

const isRenderMode = typeof window !== 'undefined' && window.location.search.includes('render=true')

// Loading simulation (400ms) — skipped in render mode
const loadProgress = computed(() => {
 if (isRenderMode) return 1
 if (relativeTime.value < currentStartTime.value) return 0
 const elapsed = relativeTime.value - currentStartTime.value
 return Math.min(elapsed / 400, 1)
})

const isLoading = computed(() => loadProgress.value < 1)

// Fade in progress (200ms after load) — instant in render mode
const fadeProgress = computed(() => {
 if (isRenderMode) return 1
 if (isLoading.value) return 0
 const elapsed = relativeTime.value - (currentStartTime.value + 400)
 return Math.min(elapsed / 200, 1)
})

// Scroll progress for the content (starts 200ms after load finishes)
const scrollProgress = computed(() => {
 if (isLoading.value) return 0
 const delay = 200
 const dur = activeItem.value.scroll_duration || 8000
 const actualDur = dur < 100 ? dur * 1000 : dur
 
 const startTime = currentStartTime.value + 400 + delay
 if (relativeTime.value < startTime) return 0
 const elapsed = relativeTime.value - startTime
 const p = Math.min(elapsed / actualDur, 1)
 
 // easeInOutQuad
 return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
})

const imageTransform = computed(() => {
 let progress = 0
 if (!activeItem.value.scroll) {
 if (activeItem.value.image_position === 'center') progress = 0.5
 else if (activeItem.value.image_position === 'bottom') progress = 1
 else progress = 0
 } else {
 const amt = (activeItem.value.scroll_amount !== undefined ? activeItem.value.scroll_amount : 100) / 100
 progress = scrollProgress.value * amt
 }
 
 // Using toFixed to avoid precision issues that might crash the browser layout engine
 return `translateY(calc(min(0px, calc(-100% + 100cqh)) * ${progress.toFixed(4)}))`
})

const loadBarWidth = computed(() => {
 if (loadProgress.value < 0.8) {
 return (loadProgress.value / 0.8) * 90
 } else {
 return 90 + ((loadProgress.value - 0.8) / 0.2) * 10
 }
})

const loadBarOpacity = computed(() => {
 if (loadProgress.value < 0.8) return 1
 return 1 - ((loadProgress.value - 0.8) / 0.2)
})
</script>

<template>
   <div class="w-full h-full flex flex-col overflow-hidden relative"
   :style="{ ...itemVars }">
   <div class="flex-1 min-h-0 flex flex-col overflow-hidden" style="border-radius: calc(var(--item-radius) - 4px)">
 <WindowHeader :mobile="mobile">
 <!-- URL Bar (default slot) -->
 <div class="flex-1 max-w-xl bg-[var(--item-bg)] h-7 flex items-center px-3 text-[13px] text-text-secondary mx-auto font-mono border border-text-muted relative overflow-hidden"
 :style="{ opacity: isLoading ? 0.5 : 1, borderRadius: 'var(--item-radius)' }">
 <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 mr-2 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
 </svg>
 <span class="truncate">{{ activeItem.url }}</span>
 <div v-if="isLoading" class="absolute bottom-0 left-0 h-[2px] bg-color-secondary"
 :style="{ width: `${loadBarWidth}%`, opacity: loadBarOpacity }"></div>
 </div>
 <template #right>
 <div class="flex items-center justify-end shrink-0 text-text-muted" :class="mobile ? 'w-6' : 'w-10'">
 <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 hover:text-text-primary cursor-pointer" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
 <circle cx="12" cy="12" r="10"/>
 <line x1="2" y1="12" x2="22" y2="12"/>
 <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
 </svg>
 </div>
 </template>
 </WindowHeader>

 <!-- Browser Content -->
 <div class="flex-1 relative overflow-hidden bg-[var(--item-bg)] variant-item" style="backdrop-filter: var(--item-backdrop); -webkit-backdrop-filter: var(--item-backdrop)">

 <!-- Loading State -->
 <div v-if="fadeProgress < 1" class="absolute inset-0 w-full h-full bg-[var(--item-bg)] flex flex-col items-center justify-center z-10"
 :style="{ opacity: 1 - fadeProgress }">
 <div class="w-8 h-8 border-4 border-text-muted/30 border-t-color-secondary rounded-full"
 :style="{ transform: `rotate(${ ((relativeTime % 1000) / 1000 * 360).toFixed(1) }deg)` }"></div>
 </div>

 <!-- Content -->
 <div v-if="!isLoading" class="absolute inset-0 w-full h-full bg-[var(--item-bg)] z-0"
 :style="{ opacity: fadeProgress }">

 <!-- Image Type -->
 <template v-if="activeItem.type === 'image'">
 <div class="w-full h-full overflow-hidden bg-[var(--item-bg)] relative" style="container-type: size">
 <img :src="activeItem.content"
 class="w-full h-auto block origin-top"
 :style="{
 transform: imageTransform,
 willChange: 'transform'
 }" />
 </div>
 </template>

 <!-- HTML Type -->
 <template v-else-if="activeItem.type === 'html'">
 <div class="w-full h-full bg-[var(--item-bg)] relative" :class="activeItem.scroll ? 'overflow-hidden' : 'overflow-y-auto'" style="container-type: size">
 <div class="p-4 md:p-8 text-text-primary prose prose-invert max-w-none min-h-full"
 :style="{
 '--scroll-progress': scrollProgress.toFixed(4),
 '--scroll-amount': ((activeItem.scroll_amount !== undefined ? activeItem.scroll_amount : 100) / 100).toFixed(4),
 transform: activeItem.scroll ? 'translateY(calc(min(0px, calc(-100% + 100cqh)) * var(--scroll-amount) * var(--scroll-progress)))' : 'none',
 willChange: activeItem.scroll ? 'transform' : 'auto'
 }"
 v-html="activeItem.content">
 </div>
 </div>
  </template>

   </div>
   </div>
   </div>
   </div>
  </template>
