<script setup>
import { getColorAlpha } from '../../utils/colors'
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  items: { 
  type: Array, 
  default: () => [
  { id: 1, label: 'Active Users', value: '14.2M', trend: '+24%', color: 'var(--color-secondary)', icon: 'heroicons:users', start_time: 0 },
  { id: 2, label: 'Latency', value: '24ms', trend: '-12%', color: 'var(--color-success)', icon: 'heroicons:server', start_time: 500 },
  { id: 3, label: 'Error Rate', value: '0.01%', trend: '-0.05%', color: 'var(--color-warning)', icon: '', start_time: 1000 }
  ]
  }
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'InfographicCards')

const relativeTime = inject('relativeTime', ref(0))

const resolvedItems = computed(() => {
 return props.items
})

const visibleItems = computed(() => {
 return resolvedItems.value.filter(item => {
 const threshold = item.start_time ?? 0
 return relativeTime.value >= threshold
 })
})

const getGridColsClass = computed(() => {
 const len = resolvedItems.value.length
 if (len === 1) return 'grid-cols-1 max-w-md mx-auto'
 if (len === 2) return 'grid-cols-2 max-w-4xl mx-auto'
 if (len >= 4) return 'grid-cols-2 max-w-5xl mx-auto'
 return 'grid-cols-3'
})

const getDynamicStyles = (stat) => {
 const threshold = stat.start_time ?? 0
 const duration = motion.value.appear_ms
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 0) return { opacity: 0, transform: 'translateY(20px) scale(0.95)', willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 1, transform: 'translateY(0px) scale(1)', willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 
 return {
 opacity: ease.toFixed(4),
 transform: `translateY(${((1 - ease) * 20).toFixed(4)}px) scale(${(0.95 + (0.05 * ease)).toFixed(4)})`,
 willChange: 'opacity, transform'
 }
}
</script>

<template>
 <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
  <div class="flex-1 min-h-0 w-full h-full relative grid items-stretch auto-rows-fr"
  :class="[
  'grid w-full',
  mobile ? 'gap-4' : ['gap-4 md:gap-6', getGridColsClass]
  ]">
  
   <div v-for="(stat, idx) in visibleItems" :key="stat.id || idx" class="relative min-h-0">
   <div class="h-full relative overflow-hidden group min-h-[96px] md:min-h-[120px] flex flex-col justify-between gap-1.5 md:gap-2"
  :style="{
  ...getDynamicStyles(stat),
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  borderTopWidth: '4px',
  borderTopColor: stat.color || 'var(--color-secondary)'
  }">

 
  <div class="relative z-10 flex items-center gap-2.5">
  <span v-if="stat.icon" class="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center shrink-0"
  :style="{ background: getColorAlpha(stat.color || 'var(--color-secondary)', 0.15), color: stat.color || 'var(--color-secondary)', borderRadius: 'calc(var(--item-radius) - 4px)' }">
  <Icon :icon="stat.icon" class="w-5 h-5 md:w-6 md:h-6" />
  </span>
  <p class="text-text-secondary text-[11px] md:text-xs font-mono uppercase tracking-wider line-clamp-1">{{ stat.label || stat.title }}</p>
  </div>
 
  <div class="relative z-10 flex items-end justify-between gap-2">
  <h3 class="text-xl md:text-3xl font-black text-text-primary leading-tight break-words">{{ stat.value }}</h3>
 
  <div v-if="stat.trend" class="rounded flex items-center gap-1 mb-1" :style="{ 
  padding: '5px 10px', 
  background: String(stat.trend).startsWith('+') ? getColorAlpha('var(--color-success)', 0.15) : getColorAlpha('var(--color-warning)', 0.15),
  border: '1px solid',
  borderColor: String(stat.trend).startsWith('+') ? getColorAlpha('var(--color-success)', 0.3) : getColorAlpha('var(--color-warning)', 0.3),
  color: String(stat.trend).startsWith('+') ? 'var(--color-success)' : 'var(--color-warning)'
  }">
  <svg v-if="String(stat.trend).startsWith('+')" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
  <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
  </svg>
  <span class="text-sm font-bold">{{ stat.trend }}</span>
  </div>
  </div>
 
  <p v-if="stat.desc" class="relative z-10 text-xs md:text-sm text-text-muted">{{ stat.desc }}</p>
 
  <!-- Decorative background watermark -->
  <Icon v-if="stat.icon" :icon="stat.icon" class="absolute -bottom-5 -right-5 w-32 h-32 opacity-[0.06] pointer-events-none" 
  :style="{ color: stat.color || 'var(--text-primary)' }" />
  </div>
  </div>
 </div>
 </div>
</template>
