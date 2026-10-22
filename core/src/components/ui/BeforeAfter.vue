<script setup lang="ts">
import { ref, inject, watch, onMounted, onUnmounted, computed } from 'vue'
import type { BeforeAfterEvent, BeforeAfterAction } from './schema'
import { useVariant } from '../../composables/useVariant'

const props = defineProps<{
 leftTitle?: string
 rightTitle?: string
 leftTime?: number
 rightTime?: number
 mobile?: boolean
 variant?: string
}>()

const { itemVars } = useVariant(computed(() => props.variant), 'BeforeAfter')

const relativeTime = inject('relativeTime', ref(0))

const sliderPosition = ref(50) // percentage
const isDragging = ref(false)
const container = ref<HTMLElement | null>(null)

let animationState = ref<any>(null)

const animateSlider = (target: number, duration = 1000) => {
 animationState.value = {
 startPos: sliderPosition.value,
 targetPos: target,
 duration,
 startTime: relativeTime.value
 }
}

watch(relativeTime, (time) => {
 if (animationState.value) {
 const { startPos, targetPos, duration, startTime } = animationState.value
 const progress = Math.min((time - startTime) / duration, 1)
 const ease = 1 - Math.pow(1 - progress, 3) // easeOutCubic
 sliderPosition.value = startPos + (targetPos - startPos) * ease
 
 if (progress >= 1) {
 animationState.value = null
 }
 }
})

const targetPosition = computed(() => {
 const events = [
 { time: -1, val: 50 },
 { time: props.leftTime !== undefined ? props.leftTime : Infinity, val: 85 },
 { time: props.rightTime !== undefined ? props.rightTime : Infinity, val: 15 }
 ].filter(e => e.time !== Infinity).sort((a,b) => a.time - b.time)
 
 let target = 50;
 for (let event of events) {
 if (relativeTime.value >= event.time) {
 target = event.val;
 }
 }
 return target;
})

watch(targetPosition, (newTarget) => {
 if (!isDragging.value) {
 animateSlider(newTarget, 1000)
 }
}, { immediate: true })

const handleMouseDown = (e: MouseEvent) => {
 if (e.button !== 0) return
 isDragging.value = true
 document.body.style.cursor = props.mobile ? 'ns-resize' : 'ew-resize'
 document.body.style.userSelect = 'none'
}

const handleMouseMove = (e: MouseEvent) => {
 if (!isDragging.value || !container.value) return
 const rect = container.value.getBoundingClientRect()
 if (props.mobile) {
 let y = e.clientY - rect.top
 y = Math.max(0, Math.min(y, rect.height))
 sliderPosition.value = (y / rect.height) * 100
 } else {
 let x = e.clientX - rect.left
 x = Math.max(0, Math.min(x, rect.width))
 sliderPosition.value = (x / rect.width) * 100
 }
}

const handleMouseUp = () => {
 isDragging.value = false
 document.body.style.cursor = 'default'
 document.body.style.userSelect = 'auto'
}

onMounted(() => {
 window.addEventListener('mousemove', handleMouseMove)
 window.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
 window.removeEventListener('mousemove', handleMouseMove)
 window.removeEventListener('mouseup', handleMouseUp)
})

const sparkTransform = computed(() => {
 const t = (relativeTime.value % 3000) / 3000
 const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
 const pos = -20 + ease * 140
 let opacity = 1
 if (t < 0.2) opacity = t / 0.2
 else if (t > 0.8) opacity = 1 - (t - 0.8) / 0.2
 return { pos, opacity }
})
</script>

<template>
  <div class="relative w-full bg-[var(--item-bg)] rounded-[var(--item-radius)] border border-text-muted overflow-hidden select-none"
  :style="{ ...itemVars, backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }"
  :class="mobile ? 'h-[550px]' : 'h-full min-h-0'"
 ref="container"
 @mousedown="handleMouseDown">
 
  <!-- Слой "После" (Right) - Базовый слой -->
  <div class="absolute inset-0 w-full h-full flex flex-col bg-[var(--item-bg)] z-0">
  <div class="flex-1 w-full h-full">
  <slot name="right"></slot>
  </div>
  </div>

  <!-- Слой "До" (Left) - Обрезанный слой -->
  <div class="absolute inset-0 h-full flex flex-col bg-[var(--item-bg)] z-20"
  :style="{ clipPath: mobile ? `inset(0 0 ${100 - sliderPosition}% 0)` : `inset(0 ${100 - sliderPosition}% 0 0)` }">
  <div class="flex-1 w-full h-full">
  <slot name="left"></slot>
  </div>
  </div>

  <!-- Подписи поверх слоёв (вне клипа) -->
  <div class="absolute px-6 py-2.5 text-text-primary border border-text-muted text-[10px] font-bold uppercase tracking-widest z-40 pointer-events-none" :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }"
  :class="mobile ? 'top-4 left-4' : 'top-6 left-6'">{{ leftTitle }}</div>
  <div class="absolute px-6 py-2.5 text-color-secondary border border-color-secondary/30 text-[10px] font-bold uppercase tracking-widest z-40 pointer-events-none" :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }"
  :class="mobile ? 'bottom-4 right-4' : 'top-6 right-6'">{{ rightTitle }}</div>

 <!-- Разделитель для мобильных (Вертикальный) -->
 <div v-if="mobile" class="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-color-secondary to-transparent -translate-y-1/2 cursor-ns-resize flex items-center justify-center group z-30"
 :style="{ top: `${sliderPosition}%` }">
 
 <div class="absolute top-1/2 -translate-y-1/2 h-[2px] w-[120px] bg-color-secondary shadow-[0_0_10px_var(--color-secondary)] rounded-full pointer-events-none"
 :style="{ left: `${sparkTransform.pos}%`, opacity: sparkTransform.opacity }"></div>

 <div class="w-8 h-8 border-2 border-color-secondary shadow-[0_0_15px_rgb(var(--color-secondary-rgb) / 0.5)] rounded-full flex items-center justify-center text-text-primary group-hover:scale-110 relative z-10" style="background: var(--item-bg)">
 <!-- Up Down Icon -->
 <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6 6-6-6"/><path d="m18 9-6-6-6 6"/></svg>
 </div>
 </div>

 <!-- Разделитель для десктопа (Горизонтальный) -->
 <div v-else class="absolute top-0 bottom-0 w-[2px] bg-gradient-to-b from-transparent via-color-secondary to-transparent -translate-x-1/2 cursor-ew-resize flex items-center justify-center group z-30"
 :style="{ left: `${sliderPosition}%` }">
 
 <!-- Бегающий огонек (искра) -->
 <div class="absolute left-1/2 -translate-x-1/2 w-[2px] h-[120px] bg-color-secondary shadow-[0_0_10px_var(--color-secondary)] rounded-full pointer-events-none"
 :style="{ top: `${sparkTransform.pos}%`, opacity: sparkTransform.opacity }"></div>

 <div class="w-8 h-8 border-2 border-color-secondary shadow-[0_0_15px_rgb(var(--color-secondary-rgb) / 0.5)] rounded-full flex items-center justify-center text-text-primary group-hover:scale-110 relative z-10" style="background: var(--item-bg)">
 <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18 6-6-6-6"/><path d="m9 18-6-6 6-6"/></svg>
 </div>
 </div>
 </div>
</template>
