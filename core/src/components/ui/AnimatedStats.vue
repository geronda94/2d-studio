<script setup lang="ts">
import { getColorAlpha } from '../../utils/colors'
import { ref, computed, inject } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps<{
 label?: string
 title?: string
 value: number
 prefix?: string
 suffix?: string
 color?: string
 icon?: string
 mobile?: boolean
 delay?: number
 start_time?: number
 variant?: string
}>()

const { itemVars, motion } = useVariant(computed(() => props.variant), 'AnimatedStats')

const relativeTime = inject('relativeTime', ref(0))

const progress = computed(() => {
 const t = props.start_time ?? props.delay ?? 0
 if (relativeTime.value < t) return 0
 const duration = motion.value.count_ms
 const p = Math.min((relativeTime.value - t) / duration, 1)
 return 1 - Math.pow(1 - p, 4) // easeOutQuart
})

const displayValue = computed(() => Math.floor(props.value * progress.value))

const customColor = computed(() => props.color || 'var(--color-secondary)')

const gradientId = 'grad-animated-stat'

const sparklinePoints = computed(() => {
 return props.value < 0 
 ? '0,4 10,12 20,6 30,22 40,16 50,29 60,26 70,36 80,40'
 : '0,40 10,32 20,38 30,22 40,28 50,15 60,18 70,8 80,4'
})

const numberSizeClass = computed(() => {
 const strLen = displayValue.value.toLocaleString('ru-RU').length
 if (props.mobile) {
 if (strLen > 8) return 'text-2xl'
 if (strLen > 5) return 'text-3xl'
 return 'text-4xl'
 }
 if (strLen > 8) return 'text-3xl sm:text-5xl'
 if (strLen > 5) return 'text-4xl sm:text-6xl'
 return 'text-6xl sm:text-8xl'
})
</script>

<template>
  <div ref="el" 
  class="relative flex flex-col justify-center gap-3 sm:gap-6 overflow-hidden w-full min-h-[150px] sm:min-h-[180px]"
 :class="mobile ? 'min-w-0 max-w-none' : 'min-w-0 max-w-none'"
 :style="{
 ...itemVars,
 background: 'var(--item-bg)',
 backdropFilter: 'var(--item-backdrop)',
 WebkitBackdropFilter: 'var(--item-backdrop)',
 boxShadow: 'var(--item-shadow)',
 borderRadius: 'var(--item-radius)',
 padding: 'var(--item-padding)',
 borderWidth: 'var(--item-border-width)',
 borderStyle: 'var(--item-border-style)',
 borderColor: getColorAlpha(customColor, 0.4)
 }">
 
 <!-- Sparkline background -->
 <svg class="absolute bottom-0 left-0 w-full h-[46%] opacity-40 pointer-events-none" viewBox="0 0 80 40" preserveAspectRatio="none">
 <defs>
 <linearGradient :id="gradientId" x1="0%" y1="0%" x2="0%" y2="100%">
 <stop offset="0%" :stop-color="customColor" stop-opacity="0.15" />
 <stop offset="100%" :stop-color="customColor" stop-opacity="0" />
 </linearGradient>
 </defs>
 
  <polygon :points="`0,40 ${sparklinePoints} 80,40`" :fill="`url(#${gradientId})`" :style="{ opacity: progress }" />
 <!-- Sharp Line -->
 <polyline :points="sparklinePoints" fill="none" :stroke="customColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="200" :style="{ strokeDashoffset: 200 * (1 - progress) }" />
 </svg>

 <!-- Backing: приглушает спарклайн под цифрами, чтобы линия не «резала» значение -->
 <div class="absolute inset-x-0 bottom-0 h-[52%] pointer-events-none"
 :style="{ background: 'linear-gradient(to top, var(--item-bg) 34%, transparent 100%)' }"></div>

 <div class="text-[10px] sm:text-xs font-bold mb-1.5 sm:mb-4 z-10 uppercase tracking-[0.2em] flex items-center gap-2" :style="{ color: customColor }">
 <Icon v-if="icon" :icon="icon" class="w-3 h-3 sm:w-4 sm:h-4" />
 <span v-else class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: customColor }"></span>
 <span>{{ label || title }}</span>
 </div>
 
  <div class="flex items-baseline gap-1.5 sm:gap-2 z-10 flex-wrap">
 <span v-if="prefix" class="text-2xl sm:text-3xl font-semibold text-text-secondary">{{ prefix }}</span>
 <span class="font-extrabold tracking-tighter text-text-primary leading-none" :class="numberSizeClass"
 :style="{ textShadow: '0 2px 10px rgb(var(--bg-base-rgb) / 0.6), 0 1px 3px rgb(var(--bg-base-rgb) / 0.6)' }">
 {{ displayValue.toLocaleString('ru-RU') }}
 </span>
 <span v-if="suffix" class="text-xl sm:text-2xl font-bold text-text-primary">{{ suffix }}</span>
 </div>
 </div>
</template>

