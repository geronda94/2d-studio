<script setup lang="ts">
import { ref, computed, inject } from 'vue'

import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor , getColorAlpha} from '../../utils/colors'

interface RoadmapStep {
 label?: string
 title?: string
 desc?: string
 date?: string
 icon?: string
 color?: string
 start_time?: number
}

const props = withDefaults(defineProps<{
 steps?: RoadmapStep[]
 items?: RoadmapStep[]
 mobile?: boolean
 variant?: string
}>(), {
 mobile: false
})

const { itemVars } = useVariant(computed(() => props.variant), 'Roadmap')

const isVisible = ref(true) // Always true since we use relativeTime
const relativeTime = inject('relativeTime', ref(0))

const normalizedSteps = computed(() => props.steps || props.items || [])

const exactProgress = computed(() => {
 const len = normalizedSteps.value.length
 if (len <= 1) return 0
 
 let current = 0
 for (let i = 0; i < len - 1; i++) {
 const t0 = normalizedSteps.value[i].start_time !== undefined ? Number(normalizedSteps.value[i].start_time) : (i * 1000)
 const t1 = normalizedSteps.value[i+1].start_time !== undefined ? Number(normalizedSteps.value[i+1].start_time) : ((i + 1) * 1000)
 
 if (relativeTime.value >= t1) {
 current = i + 1
 } else if (relativeTime.value > t0) {
 const duration = Math.max(1, t1 - t0)
 const p = (relativeTime.value - t0) / duration
 current = i + p
 break
 }
 }
 return current
})

const activeIndex = computed(() => Math.floor(exactProgress.value))

// Прогресс линии 0..1. Анимируем transform'ом (композитор), не width/height:
// в софтверном рендере (--disable-gpu) смена ширины/высоты = перерисовка каждый кадр.
const progressScale = computed(() => {
 const len = normalizedSteps.value.length
 if (len <= 1) return 1
 return Math.min(1, Math.max(0, exactProgress.value / (len - 1)))
})

const mobileLineScale = (idx: number) => {
 if (exactProgress.value >= idx + 1) return 1
 if (exactProgress.value <= idx) return 0
 return exactProgress.value - idx
}

const pulseOpacity = computed(() => {
 const p = (Math.sin(relativeTime.value / 1000 * Math.PI * 2) + 1) / 2
 return 0.1 + p * 0.2 
})



const getStepStatus = (idx: number) => {
 if (idx < activeIndex.value) return 'done'
 if (idx === activeIndex.value) return 'active'
 return 'upcoming'
}

const getScale = (idx: number) => {
 if (idx < 0 || idx >= normalizedSteps.value.length) return 1
 const step = normalizedSteps.value[idx]
 const elapsed = relativeTime.value - step.startTime
 
 if (elapsed >= 0 && elapsed < 700) {
 // curve
 const x = elapsed / 700
 const p = 1 - (1 - x) * (1 - x)
 return 1 + 0.1 * p // 1.0 to 1.1
 }
 
 if (elapsed >= 700 && getStepStatus(idx) === 'active') {
 return 1.1
 }
 
 return 1
 }
</script>

<template>
  <div ref="el" class="w-full mx-auto flex flex-col"
  :class="mobile ? 'max-w-md gap-4' : 'max-w-5xl gap-8 h-full min-h-0 justify-center'"
  :style="{
  ...itemVars,
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
  }">
 
 <!-- DESKTOP LAYOUT -->
 <div v-if="!mobile" class="flex items-start justify-between relative mt-4">
 
  <!-- Линия заднего фона (строго от центра первой до центра последней ноды) -->
  <div class="absolute top-24 left-[112px] right-[112px] h-[2px] z-0" style="background-color: var(--item-border);"></div>
  
  <div class="absolute top-24 left-[112px] right-[112px] z-0">
 <div class="h-[2px] w-full origin-left"
 :style="{ backgroundColor: 'var(--color-secondary)', transform: `scaleX(${progressScale})`, willChange: 'transform' }"></div>
 </div>
 
 <div v-for="(step, idx) in normalizedSteps" :key="'desk-'+idx"
 class="relative z-10 flex flex-col items-center group w-56"
  :style="{ transform: `scale(${getScale(idx)}) translateY(${getScale(idx) > 1 ? '-8px' : '0px'})` }">
 
  <div class="relative w-48 h-48 rounded-[var(--item-radius)] flex items-center justify-center mb-6 z-10"
 :class="{
 'border text-text-primary': getStepStatus(idx) === 'done',
 'border text-text-primary': getStepStatus(idx) === 'active',
 'border border-text-muted text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{
 borderColor: getStepStatus(idx) !== 'upcoming' ? getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')) : undefined
 }">
 
 <div class="absolute inset-0 rounded-[var(--item-radius)] -z-10" style="background: var(--item-bg); backdrop-filter: var(--item-backdrop); -webkit-backdrop-filter: var(--item-backdrop);"></div>
 <div class="absolute inset-0 rounded-[var(--item-radius)] -z-10"
 :style="{
  backgroundColor: getStepStatus(idx) !== 'upcoming' ? getColorAlpha(getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')), 0.2) : 'rgb(var(--text-primary-rgb) / 0.05)'
 }"></div>
 
  <Icon v-if="step.icon" :icon="step.icon" class="text-6xl" :style="{ color: getStepStatus(idx) !== 'upcoming' ? getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')) : undefined }" />
 <template v-else>
 <svg v-if="getStepStatus(idx) === 'done'" xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ color: getHexColor(step.color || 'var(--color-success)') }"><path d="M20 6 9 17l-5-5"/></svg>
 <svg v-else-if="getStepStatus(idx) === 'active'" xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ color: getHexColor(step.color || 'var(--color-secondary)') }"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
 </template>
 </div>
 
  <h3 class="text-xl font-sans font-bold mb-1.5 tracking-wide text-center leading-tight"
 :class="{
 'text-text-primary': getStepStatus(idx) === 'active',
 'text-text-primary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) !== 'upcoming' ? getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')) : undefined }">{{ step.label || step.title }}</h3>
 <p class="text-sm text-center font-mono leading-relaxed"
 :class="{
 'text-text-secondary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) === 'active' ? getHexColor(step.color || 'var(--color-secondary)') : undefined }">{{ step.desc || step.date }}</p>
 
 </div>
 </div>
 
 <!-- MOBILE LAYOUT (Snake Grid) -->
 <div v-else class="grid grid-cols-2 gap-y-20 gap-x-0 relative mt-4 mx-auto w-full px-2" style="grid-auto-rows: min-content;">
 <div v-for="(step, idx) in normalizedSteps" :key="'mob-'+idx" 
 class="relative z-10 flex flex-col group w-full h-full"
 :class="(Math.floor(idx / 2) % 2 === 0) ? 'justify-end' : 'justify-start'"
 :style="{ 
 gridColumn: (Math.floor(idx / 2) % 2 === 0) ? (idx % 2) + 1 : 2 - (idx % 2),
 gridRow: Math.floor(idx / 2) + 1 
 }">
 
 <!-- Text Above (Even Rows: 0, 2, 4...) -->
 <div v-if="Math.floor(idx / 2) % 2 === 0" class="flex flex-col items-center mb-4">
 <h3 class="text-[15px] font-sans font-bold mb-1 tracking-wide text-center leading-tight"
 :class="{
 'text-text-primary': getStepStatus(idx) === 'active',
 'text-text-primary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) === 'done' ? getHexColor(step.color || 'var(--color-success)') : undefined }">{{ step.label || step.title }}</h3>
 <p class="text-[12px] text-center font-mono leading-relaxed px-2"
 :class="{
 'text-text-secondary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) === 'active' ? getHexColor(step.color || 'var(--color-secondary)') : undefined }">{{ step.desc || step.date }}</p>
 </div>

 <!-- Circle Container -->
 <div class="relative w-full flex items-center justify-center">
 
 <!-- Lines -->
 <template v-if="idx < normalizedSteps.length - 1">
 <!-- Horizontal Line (idx % 2 === 0) -->
 <template v-if="idx % 2 === 0">
 <!-- Go Right (Even Rows) -->
 <template v-if="Math.floor(idx / 2) % 2 === 0">
 <div class="absolute top-[50%] -translate-y-1/2 left-[50%] w-[100%] h-[2px] z-0" style="background-color: var(--item-border);"></div>
 <div class="absolute top-[50%] -translate-y-1/2 left-[50%] w-[100%] h-[2px] z-0 origin-left"
 :style="{ backgroundColor: 'var(--color-secondary)', transform: `scaleX(${mobileLineScale(idx)})`, willChange: 'transform' }"></div>
 </template>
 <!-- Go Left (Odd Rows) -->
 <template v-else>
 <div class="absolute top-[50%] -translate-y-1/2 right-[50%] w-[100%] h-[2px] z-0" style="background-color: var(--item-border);"></div>
 <div class="absolute top-[50%] -translate-y-1/2 right-[50%] w-[100%] h-[2px] z-0 origin-right"
 :style="{ backgroundColor: 'var(--color-secondary)', transform: `scaleX(${mobileLineScale(idx)})`, willChange: 'transform' }"></div>
 </template>
 </template>
 
 <!-- Vertical Line (idx % 2 === 1) -->
 <template v-else>
 <div class="absolute top-[50%] left-[50%] -translate-x-1/2 w-[2px] z-0" style="height: 144px; background-color: var(--item-border);"></div>
 <div class="absolute top-[50%] left-[50%] -translate-x-1/2 w-[2px] h-[144px] z-0 origin-top"
 :style="{ backgroundColor: 'var(--color-secondary)', transform: `scaleY(${mobileLineScale(idx)})`, willChange: 'transform' }"></div>
 </template>
 </template>

 <!-- Кружок -->
 <div class="relative w-14 h-14 rounded-[var(--item-radius)] flex items-center justify-center mb-3 z-10"
 :class="{
 'border text-text-primary': getStepStatus(idx) === 'done',
 'border text-text-primary': getStepStatus(idx) === 'active',
 'border border-text-muted text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{
 borderColor: getStepStatus(idx) !== 'upcoming' ? getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')) : undefined
 }">
 
 <!-- Glass background -->
 <div class="absolute inset-0 rounded-[var(--item-radius)] -z-10" style="background: var(--item-bg); backdrop-filter: var(--item-backdrop); -webkit-backdrop-filter: var(--item-backdrop);"></div>
 <div class="absolute inset-0 rounded-[var(--item-radius)] -z-10"
 :style="{
  backgroundColor: getStepStatus(idx) !== 'upcoming' ? getColorAlpha(getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')), 0.2) : 'rgb(var(--text-primary-rgb) / 0.05)'
 }"></div>
 
 <Icon v-if="step.icon" :icon="step.icon" class="text-xl" :style="{ color: getStepStatus(idx) !== 'upcoming' ? getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')) : undefined }" />
 <template v-else>
 <svg v-if="getStepStatus(idx) === 'done'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ color: getHexColor(step.color || 'var(--color-success)') }"><path d="M20 6 9 17l-5-5"/></svg>
 <svg v-else-if="getStepStatus(idx) === 'active'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ color: getHexColor(step.color || 'var(--color-secondary)') }"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
 </template>
 </div>
 </div>

 <!-- Text Below (Odd Rows: 1, 3, 5...) -->
 <div v-if="Math.floor(idx / 2) % 2 !== 0" class="flex flex-col items-center mt-4">
 <h3 class="text-[15px] font-sans font-bold mb-1 tracking-wide text-center leading-tight"
 :class="{
 'text-text-primary': getStepStatus(idx) === 'active',
 'text-text-primary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) === 'done' ? getHexColor(step.color || 'var(--color-success)') : undefined }">{{ step.label || step.title }}</h3>
 <p class="text-[12px] text-center font-mono leading-relaxed px-2"
 :class="{
 'text-text-secondary': getStepStatus(idx) === 'done',
 'text-text-muted': getStepStatus(idx) === 'upcoming'
 }"
 :style="{ color: getStepStatus(idx) === 'active' ? getHexColor(step.color || 'var(--color-secondary)') : undefined }">{{ step.desc || step.date }}</p>
 </div>
 </div>
 </div>

 </div>
</template>
