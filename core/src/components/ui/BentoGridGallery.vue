<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 mobile: { type: Boolean, default: false },
 variant: String,
 defaultDelay: { type: Number, default: 150 },
 items: {
 type: Array,
 default: () => [
 { id: 1, title: 'Элемент 1', image: '', size: '2x2' },
 { id: 2, title: 'Элемент 2', image: '', size: '1x1' },
 { id: 3, title: 'Элемент 3', image: '', size: '1x1' }
 ]
 }
})

const { itemVars } = useVariant(computed(() => props.variant), 'BentoGridGallery')

const relativeTime = inject('relativeTime', ref(0))

// Return only items that have spawned
const visibleItems = computed(() => {
 return props.items.filter((item, idx) => {
 const threshold = item.start_time ?? (idx * props.defaultDelay)
 return relativeTime.value >= threshold
 })
})

const visibleCount = computed(() => visibleItems.value.length)

const getGridClasses = (item, idx) => {
 const vCount = visibleCount.value
 
 let size = item.size || '1x1'
 if (!item.size && item.span === 2) size = '2x2'
 if (!item.size && item.span === 1) size = '1x1'

 if (props.mobile) {
 if (vCount === 1) return 'col-span-2 row-span-4'
 if (vCount === 2) return 'col-span-2 row-span-2'
 if (size === '2x2') return 'col-span-2 row-span-2'
 if (size === '2x1') return 'col-span-2 row-span-1'
 if (size === '1x2') return 'col-span-1 row-span-2'
 if (size === '4x2') return 'col-span-2 row-span-2'
 if (size === '3x2') return 'col-span-2 row-span-2'
 return 'col-span-1 row-span-1'
 }

 // Desktop — dynamic cols based on item sizes
 const cols = visibleItems.value.reduce((sum, item) => {
  const s = item.size || '1x1'
  if (s === '2x2' || s === '2x1') return sum + 2
  if (s === '3x2') return sum + 3
  if (s === '4x2') return sum + 4
  return sum + 1
 }, 0)
 const isSmallGrid = vCount === 3 && cols <= 3

 if (vCount === 1) return 'col-span-4 row-span-3'
 if (vCount === 2) return 'col-span-2 row-span-3'
 
 if (size === '2x2') return `col-span-2 row-span-2`
 if (size === '2x1') return `col-span-2 row-span-1`
 if (size === '1x2') return 'col-span-1 row-span-2'
 if (size === '3x2') return 'col-span-3 row-span-2'
 if (size === '4x2') return 'col-span-4 row-span-2'
 return 'col-span-1 row-span-1' // default 1x1
}

const getDynamicStyles = (item, idx) => {
 const threshold = item.start_time ?? (idx * props.defaultDelay)
 const duration = 400
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 0) return { opacity: 0, transform: 'scale(0.85)', willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 1, transform: 'scale(1)', willChange: 'auto' }
 
 const ease = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2
 
 return {
 opacity: ease.toFixed(4),
 transform: `scale(${(0.85 + (0.15 * ease)).toFixed(4)})`,
 willChange: 'opacity, transform'
 }
}

const getSizeCategory = (item, idx) => {
 const vCount = visibleCount.value
 
 let size = item.size || '1x1'
 if (!item.size && item.span === 2) size = '2x2'
 if (!item.size && item.span === 1) size = '1x1'

 if (props.mobile) {
 if (vCount === 1) return 'large'
 if (vCount === 2) return 'medium'
 if (['2x2', '3x2', '4x2'].includes(size)) return 'medium'
 return 'small'
 }

 // Desktop
 if (vCount === 1) return 'large'
 if (vCount === 2) return 'large'
 
 if (['2x2', '3x2', '4x2'].includes(size)) return 'large'
 if (['2x1', '1x2'].includes(size)) return 'medium'
 return 'small'
}
const gridClasses = computed(() => {
 if (props.mobile) return 'grid-cols-2 grid-rows-4'
 const vCount = visibleCount.value
 if (vCount <= 1) return 'grid-cols-4 grid-rows-3'
 if (vCount === 2) return 'grid-cols-4 grid-rows-3'

// 3+ items: ширина колонок от самой широкой плитки; высота рядов — auto-rows-fr,
// чтобы сетка равномерно заполняла кадр и не оставляла дыру снизу.
const colSpans = visibleItems.value.map(item => {
 const s = item.size || '1x1'
 if (s === '2x2' || s === '2x1') return 2
 if (s === '3x2') return 3
 if (s === '4x2') return 4
 return 1
})
const maxSingle = Math.max(...colSpans)
const baseCols = [3, 4].find(c => c >= maxSingle) || 4
// 4+ плиток: 4 колонки заполняют сетку без дыр (2x2 + 1x2 + 1x1 + 1x1 + 2x1 + 2x1).
const cols = visibleCount.value >= 4 ? Math.max(baseCols, 4) : baseCols

return `grid-cols-${cols} auto-rows-fr`
})
</script>

<template>
  <div class="w-full h-full relative grid grid-flow-row-dense gap-4" 
  :class="gridClasses"
 :style="{ ...itemVars }">
 
  <div v-for="(item, idx) in visibleItems" :key="item.id || idx" 
  class="relative overflow-hidden group flex flex-col"
  :class="getGridClasses(item, idx)"
  :style="{
  ...getDynamicStyles(item, idx),
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
  }">
 
 <!-- Background Image -->
 <div v-if="item.image" class="absolute inset-0 bg-cover bg-center" :style="{ backgroundImage: `url('${item.image}')` }"></div>
 
 <!-- Text Content (градиент — плотный снизу, чтобы белый текст не терялся на светлых фото) -->
 <div v-if="item.title || item.desc" class="mt-auto relative z-10"
 :style="{
   padding: getSizeCategory(item, idx) === 'small' ? 'var(--item-padding)' : `calc(var(--item-padding) * 1.4)`,
   paddingTop: item.image ? 'calc(var(--item-padding) * 2)' : undefined,
   paddingBottom: item.image ? 'calc(var(--item-padding) * 1.5)' : undefined,
   backdropFilter: item.image ? 'var(--item-backdrop)' : undefined,
   WebkitBackdropFilter: item.image ? 'var(--item-backdrop)' : undefined,
   background: item.image ? `linear-gradient(to top, rgb(var(--bg-surface-rgb) / 0.95) 0%, rgb(var(--bg-surface-rgb) / 0.82) 55%, rgb(var(--bg-surface-rgb) / 0.25) 82%, transparent 100%)` : 'transparent'
 }">
 <h3 v-if="item.title" class="font-bold text-text-primary"
 :class="getSizeCategory(item, idx) === 'small' ? 'text-sm md:text-base leading-tight' : (getSizeCategory(item, idx) === 'medium' ? 'text-xl md:text-2xl' : 'text-2xl md:text-3xl')">{{ item.title }}</h3>
 <p v-if="item.desc" class="text-text-primary"
 :class="getSizeCategory(item, idx) === 'small' ? 'text-[11px] mt-0.5 line-clamp-1' : (getSizeCategory(item, idx) === 'medium' ? 'text-sm mt-1.5 line-clamp-2' : 'text-sm md:text-base mt-2')">{{ item.desc }}</p>
 </div>

 </div>
 </div>
</template>
