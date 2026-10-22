<script setup>
import { ref, inject } from 'vue'
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 title: { type: String, default: '' },
 subtitle: { type: String, default: '' },
 variant: String,
 base_color: { type: String, default: 'var(--color-primary)' },
 metrics: {
 type: Array,
 default: () => [
 { label: 'CPU Efficiency', percentage: 92, color: 'linear-gradient(to right, var(--color-secondary), var(--chart-1))', icon: 'lucide:cpu' },
 { label: 'Memory Usage', percentage: 68, color: 'linear-gradient(to right, var(--chart-2), var(--chart-3))', icon: 'lucide:memory-stick' },
 { label: 'Network Speed', percentage: 85, color: 'linear-gradient(to right, var(--color-success), var(--chart-4))', icon: 'lucide:network' },
 { label: 'Storage I/O', percentage: 74, color: 'linear-gradient(to right, var(--color-warning), var(--color-error))', icon: 'lucide:hard-drive' }
 ]
 }
})

const { itemVars } = useVariant(computed(() => props.variant), 'MetricScales')

const relativeTime = inject('relativeTime', ref(0))
const ANIM_DURATION = 1000

const dense = computed(() => (props.metrics || []).length > 3)

const getMetricProgress = (metric, index) => {
 const t = metric.start_time ?? (index * 300)
 if (relativeTime.value < t) return 0
 const elapsed = relativeTime.value - t
 const raw = Math.min(elapsed / ANIM_DURATION, 1)
 // quartic
 return 1 - Math.pow(1 - raw, 4)
}

const getPercentage = (metric) => {
 if (metric.percentage !== undefined) return metric.percentage
 if (metric.value !== undefined && metric.max) return Math.round((metric.value / metric.max) * 100)
 if (metric.value !== undefined) return metric.value // Assume out of 100
 return 0
}

const getDisplayedPercentage = (metric, index) => {
 return Math.floor(getPercentage(metric) * getMetricProgress(metric, index))
}

const getFillScale = (metric, index) => {
 const ratio = Math.max(0, Math.min(100, getPercentage(metric))) / 100
 return (ratio * getMetricProgress(metric, index)).toFixed(4)
}

const getShimmerTransform = () => {
 const progress = (relativeTime.value % 2000) / 2000
 const x = -100 + progress * 200
 return `translateX(${x.toFixed(2)}%)`
}
</script>

<template>
  <!-- Карточка по контенту (без h-full): иначе внутри карточки — пустые полосы,
       а подписи «отрываются» от своих шкал. Центрирование даёт Slide.vue. -->
  <div class="w-full max-w-6xl mx-auto overflow-hidden relative group"
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
  <!-- Background Glow (clipped so it never overflows the root) -->
  <div class="absolute inset-0 overflow-hidden pointer-events-none">
  <div class="absolute -bottom-32 -right-32 w-64 h-64 bg-color-secondary/10 rounded-full blur-[60px] opacity-0 group-hover:opacity-100"></div>
  </div>
 
 <!-- Header -->
 <div v-if="title || subtitle" class="shrink-0 mb-5 md:mb-6 relative z-10">
 <h3 v-if="title" class="text-2xl md:text-3xl font-heading font-bold text-text-primary mb-1">{{ title }}</h3>
 <p v-if="subtitle" class="text-text-muted text-sm">{{ subtitle }}</p>
 </div>
 
 <!-- Metrics List: внутренний отступ метки↔шкалы (gap-2) МЕНЬШЕ отступа между
      группами (gap-5/6) — по близости однозначно ясно, какой текст к какой шкале. -->
 <div class="flex flex-col gap-5 md:gap-6 relative z-10">
 <div v-for="(metric, index) in metrics" :key="index" class="w-full">
 
 <!-- Label & Value -->
 <div class="flex justify-between items-center mb-2">
 <div class="flex items-center gap-2" :class="dense ? 'md:gap-2.5' : 'md:gap-3'">
 <Icon v-if="metric.icon" :icon="metric.icon" class="text-text-secondary" :class="dense ? 'w-4 h-4 md:w-5 md:h-5' : 'w-5 h-5 md:w-6 md:h-6'" />
 <span class="text-text-primary font-bold tracking-wide" :class="dense ? 'text-sm md:text-base' : 'text-base md:text-lg'">{{ metric.label }}</span>
 </div>
 <span class="text-text-primary font-black tabular-nums" :class="dense ? 'text-sm md:text-base' : 'text-lg md:text-2xl'">{{ getDisplayedPercentage(metric, index) }}%</span>
 </div>
  
  <!-- Track: тонкая шкала (не «брусок») -->
  <div class="w-full rounded-full overflow-hidden relative border" :class="dense ? 'h-2 md:h-2.5' : 'h-2.5 md:h-3.5'" style="background: var(--item-bg); border-color: var(--item-border)">
 <!-- Animated Fill -->
 <div class="h-full w-full rounded-full relative origin-left"
 :style="{ 
 transform: `scaleX(${getFillScale(metric, index)})`,
 background: metric.color || `var(--chart-${(index % 6) + 1})`,
 willChange: 'transform'
 }">
 
 <!-- Animated shimmer effect -->
 <div class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent" 
 :style="{ transform: getShimmerTransform() }"></div>
 </div>
 </div>
  
 </div>
 </div>
 </div>
</template>
