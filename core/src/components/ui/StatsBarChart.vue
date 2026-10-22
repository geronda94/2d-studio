<script setup>
import { ref, computed, inject } from 'vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 mobile: { type: Boolean, default: false },
 variant: String,
 title: { type: String, default: '' },
 subtitle: { type: String, default: '' },
 items: {
 type: Array,
 default: () => []
 },
 data: {
 type: Array,
 default: () => []
 },
 defaultDelay: { type: Number, default: 150 },
 valuePrefix: { type: String, default: '' },
 valueSuffix: { type: String, default: '' },
 base_color: { type: String, default: 'var(--color-primary)' },
 peak_color: { type: String, default: 'var(--color-error)' }
})

const { itemVars } = useVariant(computed(() => props.variant), 'StatsBarChart')

const hoveredIndex = ref(null)
const relativeTime = inject('relativeTime', ref(0))

// Fallback to beautiful default data if nothing is provided
const defaultData = [
 { label: 'ЯНВ', value: 1200 },
 { label: 'ФЕВ', value: 1900 },
 { label: 'МАР', value: 1500 },
 { label: 'АПР', value: 2200 },
 { label: 'МАЙ', value: 2800 },
 { label: 'ИЮН', value: 3500, highlight: true },
 { label: 'ИЮЛ', value: 3100 }
]

const chartData = computed(() => {
 if (props.items && props.items.length > 0) return props.items
 if (props.data && Array.isArray(props.data) && props.data.length > 0) return props.data
 return defaultData
})

const rawMaxValue = computed(() => {
 return Math.max(...chartData.value.map(item => item.value))
})

const averageValue = computed(() => {
 const values = chartData.value.map(item => item.value).filter(v => v > 0)
 if (values.length === 0) return 0
 return values.reduce((a, b) => a + b, 0) / values.length
})

const maxValue = computed(() => {
  // «Круглый» шаг шкалы (1/1.5/2/2.5/3/4/5/6/8 × 10^n) так, чтобы 4 интервала
  // покрывали данные с небольшим запасом. Прошлый баг: norm 1.001 → шаг 2 → ось 200
  // при пике 91 (половина графика пустая).
  const raw = rawMaxValue.value > 0 ? rawMaxValue.value : 100
  const intervals = 4
  const rough = raw / intervals
  const mag = Math.pow(10, Math.floor(Math.log10(rough)))
  const norm = rough / mag
  const nice = norm <= 1 ? 1 : norm <= 1.5 ? 1.5 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 3 ? 3 : norm <= 4 ? 4 : norm <= 5 ? 5 : norm <= 6 ? 6 : norm <= 8 ? 8 : 10
  const step = nice * mag
  let max = step * intervals
  while (max < raw * 1.02) max += step
  return max
})

const barMaxWidth = computed(() => {
  const n = chartData.value.length
  if (n <= 4) return '150px'
  if (n <= 6) return '110px'
  return '72px'
})

const yAxisLabels = computed(() => {
  const steps = 5
  const max = maxValue.value
  // 5 «круглых» подписей (max, 3/4, 1/2, 1/4, 0).
  return Array.from({ length: steps }).map((_, i) => Math.round(max - (max / (steps - 1)) * i))
})

const formatValue = (val) => {
 if (val === 0) return `0${props.valueSuffix}`
 if (val >= 1000) return `${props.valuePrefix}${(val / 1000).toFixed(1).replace('.0', '')}k${props.valueSuffix}`
 return `${props.valuePrefix}${Math.round(val)}${props.valueSuffix}`
}

const getBarStyles = (item, index) => {
 const threshold = item.start_time ?? (index * props.defaultDelay)
 const duration = 1000
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 0) return { height: '0%', willChange: 'height' }
 if (progress === 1) return { height: `${((item.value / maxValue.value) * 100).toFixed(4)}%`, willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 return {
 height: `${(ease * (item.value / maxValue.value) * 100).toFixed(4)}%`,
 willChange: 'height'
 }
}

const getPeakHeaderStyles = () => {
 // Uses first item's start time for fade in
 const firstThreshold = chartData.value[0]?.start_time ?? 0
 const duration = 700
 const progress = Math.max(0, Math.min(1, (relativeTime.value - firstThreshold) / duration))
 
 if (progress === 0) return { opacity: 0, transform: 'translateY(16px)', willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 1, transform: 'translateY(0px)', willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 return {
 opacity: ease.toFixed(4),
 transform: `translateY(${((1 - ease) * 16).toFixed(4)}px)`,
 willChange: 'opacity, transform'
 }
}

const getBarLabelStyles = (item, index) => {
 const threshold = item.start_time ?? (index * props.defaultDelay)
 const duration = 1000
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 0 || item.value === 0) return { opacity: 0, willChange: 'opacity' }
 if (progress === 1) return { opacity: 1, willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 return { opacity: ease.toFixed(4), willChange: 'opacity' }
}

const getAxisLabelStyles = (item, index) => {
 // Starts 200ms after threshold
 const threshold = (item.start_time ?? (index * props.defaultDelay)) + 200
 const duration = 500
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 const barColor = item.value > averageValue.value ? props.peak_color : (item.highlight || hoveredIndex.value === index ? 'var(--text-primary)' : props.base_color)
 
 if (progress === 0) return { opacity: 0, transform: 'translateY(16px)', color: barColor, willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 0.8, transform: 'translateY(0px)', color: barColor, willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 return {
 opacity: (ease * 0.8).toFixed(4),
 transform: `translateY(${((1 - ease) * 16).toFixed(4)}px)`,
 color: barColor,
 willChange: 'opacity, transform'
 }
}
</script>

<template>
  <div class="w-full relative overflow-hidden group"
  :class="mobile ? 'h-full flex flex-col' : ''"
  :style="{
  ...itemVars,
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
  }">
 
 <!-- Header -->
 <div class="flex justify-between items-end mb-6 relative z-10 shrink-0">
 <div>
 <h3 class="text-xl md:text-2xl font-heading font-bold text-text-primary mb-1">{{ title }}</h3>
 <p class="text-text-muted text-xs md:text-sm">{{ subtitle }}</p>
 </div>
  <div class="text-right hidden sm:block" :style="getPeakHeaderStyles()">
  <p class="text-[10px] uppercase tracking-widest font-bold mb-1 opacity-70" :style="{ color: props.peak_color }">Peak Value</p>
  <p class="font-black text-lg md:text-xl" :style="{ color: props.peak_color }">{{ formatValue(rawMaxValue) }}</p>
  </div>
 </div>
 
 <!-- Chart Area -->
 <div class="relative w-full flex flex-col z-10 mt-2" :class="mobile ? 'flex-1 min-h-0' : 'h-40 md:h-60'">
 
 <!-- Y-Axis Labels Column -->
 <div class="absolute top-0 bottom-8 left-0 w-8 md:w-12 flex flex-col justify-between text-right pr-2 md:pr-4 z-0">
 <div v-for="(val, idx) in yAxisLabels" :key="idx" class="text-[9px] md:text-xs text-text-muted font-medium -translate-y-1/2">
 {{ formatValue(val) }}
 </div>
 </div>

 <!-- Grid Lines & Average Norm Line -->
 <div class="absolute top-0 bottom-8 left-8 md:left-12 right-0 pointer-events-none z-0">
 <!-- Y-axis lines -->
 <div class="absolute inset-0 flex flex-col justify-between">
 <div v-for="(val, idx) in yAxisLabels" :key="idx" class="w-full border-b border-text-muted/[0.04]"></div>
 </div>
 
 <!-- Average Line -->
 <div class="absolute left-0 right-0 border-b border-dashed z-20 pointer-events-none"
 :style="{ bottom: `${(averageValue / maxValue) * 100}%`, borderColor: props.peak_color }">
 <span v-if="!props.mobile" class="absolute right-0 -top-4 text-[8px] font-bold pl-2 uppercase tracking-widest opacity-90 z-20"
 :style="{ color: props.peak_color, background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }">Norm / {{ formatValue(averageValue) }}</span>
 </div>
 </div>
 
 <!-- Bars Container -->
 <div class="relative w-full h-full flex justify-around gap-2 md:gap-8 z-10 pl-8 md:pl-12">
  <div v-for="(item, index) in chartData" :key="index" 
  class="relative flex flex-col items-center flex-1 group/bar z-10 h-full cursor-pointer"
  :style="{ maxWidth: barMaxWidth }"
  @mouseenter="hoveredIndex = index"
  @mouseleave="hoveredIndex = null">
 
 <!-- Bar Track (Empty Space) -->
 <div class="w-full flex-1 flex items-end overflow-visible">
 
  <!-- Animated Fill -->
  <div class="w-full relative overflow-visible flex justify-center hover:brightness-110"
  :style="[getBarStyles(item, index), { borderTopLeftRadius: 'var(--item-radius)', borderTopRightRadius: 'var(--item-radius)' }]">
 
  <!-- Layers Wrapper to prevent gradient bleed while keeping label visible -->
  <div class="absolute inset-0 w-full h-full overflow-hidden" :style="{ borderTopLeftRadius: 'var(--item-radius)', borderTopRightRadius: 'var(--item-radius)' }">
 <!-- Base Layer -->
 <div class="absolute inset-0 w-full h-full" :style="{ background: props.base_color }"></div>
 
 <!-- Peak Layer -->
 <div v-if="item.value > averageValue"
 class="absolute top-0 left-0 right-0 w-full"
 :style="{ 
 height: `${((item.value - averageValue) / item.value) * 100}%`,
 background: props.peak_color
 }">
 </div>
 </div>
 
 <!-- Permanent Value Label (Top of bar) -->
 <div class="absolute -top-6 md:-top-7 w-full flex justify-center"
 :style="getBarLabelStyles(item, index)">
 <span class="font-semibold text-[9px] md:text-xs"
 :style="{ color: item.value > averageValue ? props.peak_color : (item.highlight || hoveredIndex === index ? 'var(--text-primary)' : props.base_color) }">
 {{ formatValue(item.value) }}
 </span>
 </div>
 </div>
 </div>
 
 <!-- X-axis Label -->
 <div class="mt-3 h-5 flex items-center justify-center overflow-hidden w-full border-t border-text-muted/[0.04]">
 <div class="text-[9px] md:text-xs font-medium uppercase tracking-wide mt-2"
 :style="getAxisLabelStyles(item, index)">
 {{ item.label }}
 </div>
 </div>
 
 </div>
 </div>
 </div>
 </div>
</template>
