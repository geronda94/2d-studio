<script setup lang="ts">
import { getColorAlpha } from '../../utils/colors'
import { ref, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import type { Ref } from 'vue'
import { useVariant } from '../../composables/useVariant'

interface Request {
 name: string
 method: string
 type: 'html' | 'js' | 'api' | 'image'
 start_ms: number 
 duration_ms: number 
 start_time?: number
 color?: string
 icon?: string
}

interface LegendItem {
 label: string
 color: string
}

const props = withDefaults(defineProps<{
 requests?: Request[]
 legend?: LegendItem[]
 total_ms?: number
 mobile?: boolean
 start_time?: number
 defaultDelay?: number
 variant?: string
}>(), {
 requests: () => [],
 legend: () => [],
 total_ms: 1000,
 mobile: false,
 start_time: 0,
 defaultDelay: 150
})

const relativeTime = inject<Ref<number>>('relativeTime', ref(0))

const { itemVars } = useVariant(computed(() => props.variant), 'NetworkWaterfall')

// A request is visible when relativeTime passes its threshold
const isRequestVisible = computed(() => {
 return props.requests.map((req, idx) => {
 const threshold = req.start_time ?? (props.start_time + idx * props.defaultDelay)
 return relativeTime.value >= threshold
 })
})

const getBarProgress = (req: Request, idx: number) => {
 const threshold = req.start_time ?? (props.start_time + idx * props.defaultDelay)
 const elapsed = Math.max(0, relativeTime.value - threshold)
 const p = Math.min(1, elapsed / 800)
 return 1 - Math.pow(1 - p, 3)
}

const getTextOpacity = (req: Request, idx: number) => {
 const threshold = req.start_time ?? (props.start_time + idx * props.defaultDelay)
 const elapsed = Math.max(0, relativeTime.value - threshold - 800)
 return Math.min(1, Math.max(0, elapsed / 500))
}

const getBarColor = (req: Request) => {
 if (req.color) return req.color
 if (req.type === 'html') return 'var(--chart-1)'
 if (req.type === 'js') return 'var(--chart-2)'
 if (req.type === 'api') return 'var(--chart-3)'
 return 'var(--chart-4)'
 }

const getBarInlineStyles = (req: Request, idx: number) => {
 const progress = getBarProgress(req, idx)
 const targetWidth = Math.min(100, Math.max(0, (req.duration_ms / props.total_ms) * 100))
 const color = getBarColor(req)
 return {
 left: `${Math.min(100, Math.max(0, (req.start_ms / props.total_ms) * 100))}%`, 
 width: `${targetWidth * progress}%`,
 background: getColorAlpha(color, 0.8),
 borderColor: color
 }
 }
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
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

 <!-- Timeline Header -->
 <div class="flex text-chart-axis font-mono border-b border-chart-grid relative z-10 shrink-0"
 :class="mobile ? 'flex-col text-[9px] mb-3 pb-2' : 'flex-row items-center text-xs mb-3 pb-2'">
 <div class="font-bold" :class="mobile ? 'hidden' : 'w-1/3 pl-2'">Resource Name</div>
 <div class="relative h-4" :class="mobile ? 'w-full' : 'w-2/3'">
 <span class="absolute left-0">0ms</span>
 <span class="absolute left-1/4 -translate-x-1/2" v-if="!mobile">{{ Math.round(total_ms * 0.25) }}ms</span>
 <span class="absolute left-1/2 -translate-x-1/2">{{ Math.round(total_ms * 0.5) }}ms</span>
 <span class="absolute left-3/4 -translate-x-1/2" v-if="!mobile">{{ Math.round(total_ms * 0.75) }}ms</span>
 <span class="absolute right-0">{{ total_ms }}ms</span>
 </div>
 </div>

 <!-- Requests -->
 <div class="flex-1 min-h-0 flex flex-col relative z-10 justify-evenly" :class="mobile ? 'gap-3' : 'gap-2'">

 <!-- Вертикальные линии сетки -->
 <div class="absolute top-0 bottom-0 pointer-events-none z-0"
 :class="mobile ? 'left-0 w-full' : 'left-1/3 w-2/3'">
 <div class="absolute left-0 top-0 bottom-0 w-[1px]" style="background: var(--item-border)"></div>
 <div class="absolute left-1/4 top-0 bottom-0 w-[1px]" style="background: var(--item-border)"></div>
 <div class="absolute left-1/2 top-0 bottom-0 w-[1px] border-l border-dashed" style="border-color: var(--chart-grid)"></div>
 <div class="absolute left-3/4 top-0 bottom-0 w-[1px]" style="background: var(--item-border)"></div>
 <div class="absolute right-0 top-0 bottom-0 w-[1px]" style="background: var(--item-border)"></div>
 </div>

 <div v-for="(req, idx) in requests" :key="idx" class="group z-10"
 :class="mobile ? 'flex flex-col gap-1.5' : 'flex items-center'">
 <div class="flex items-center truncate"
 :class="mobile ? 'w-full gap-1.5' : 'w-1/3 gap-3 pr-4 pl-2'">
 <span class="font-bold rounded uppercase font-mono tracking-widest shrink-0"
 :class="[mobile ? 'text-[7px] px-1 py-0.5' : 'text-[9px] px-1.5 py-0.5']"
 :style="{ 
  background: req.color ? getColorAlpha(req.color, 0.2) : (req.method === 'POST' ? getColorAlpha('var(--chart-5)', 0.2) : 'var(--item-bg)'), 
  color: req.color ? req.color : (req.method === 'POST' ? 'var(--chart-5)' : 'var(--text-primary)') 
 }">{{ req.method }}</span>
 <span class="font-mono truncate group-hover:brightness-125 flex items-center gap-1.5"
 :class="mobile ? 'text-[11px]' : 'text-sm'"
 :style="req.color ? { color: req.color } : { color: 'var(--text-muted)' }">
 <Icon v-if="req.icon" :icon="req.icon" class="shrink-0" />
 {{ req.name }}
 </span>
 </div>

  <div class="relative overflow-hidden border shrink-0"
  :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', borderColor: 'var(--item-border)' }"
  :class="mobile ? 'w-full h-8' : 'w-2/3 h-9'">
  <div class="absolute h-full border-r border-t border-b border-l-0 flex items-center justify-end pr-2 overflow-hidden"
  :style="[ { borderRadius: 'calc(var(--item-radius) - 4px)' }, getBarInlineStyles(req, idx) ]">
  <span v-if="isRequestVisible[idx]" class="font-bold text-text-primary whitespace-nowrap"
  :class="mobile ? 'text-[11px]' : 'text-[10px]'"
  :style="{ opacity: getTextOpacity(req, idx) }">{{ req.duration_ms }}ms</span>
  </div>
 </div>
 </div>

 </div>

 <!-- Легенда -->
 <div v-if="legend && legend.length > 0" class="flex items-center font-mono text-text-secondary justify-center flex-wrap shrink-0"
 :class="mobile ? 'gap-3 mt-3 pt-3 border-t border-chart-grid text-[9px]' : 'gap-6 mt-3 pt-3 border-t border-chart-grid text-[11px]'">
 <div v-for="(item, idx) in legend" :key="idx" class="flex items-center gap-1.5">
 <div class="rounded-full" :class="mobile ? 'w-2 h-2' : 'w-3 h-3'"
 :style="{ backgroundColor: item.color }"></div> 
 {{ item.label }}
 </div>
 </div>
 </div>
</template>
