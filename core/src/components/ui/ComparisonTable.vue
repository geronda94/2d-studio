<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

export interface FeatureRow {
 id?: string
 name?: string
 label?: string
 us?: boolean | string
 them?: boolean | string
 values?: (boolean | string)[]
 start_time?: number
}

const props = defineProps<{
 items?: FeatureRow[]
 rows?: FeatureRow[]
 headers?: string[]
 mobile?: boolean
 variant?: string
}>()

const { itemVars, itemPrimaryVars } = useVariant(computed(() => props.variant), 'ComparisonTable')

// Очищаем от пустой строки в начале — это placeholder для Features-колонки,
// который не рендерится в хедере
const cleanedHeaders = computed(() => {
 const h = props.headers || ['Наша платформа', 'Конкуренты']
 if (h.length > 0 && h[0] === '') return h.slice(1)
 return h
})

const normalizedHeaders = cleanedHeaders

// На мобиле заголовки для значений — те же cleaned headers
const mobileHeaders = cleanedHeaders

const normalizedItems = computed(() => {
 const arr = props.items || props.rows || []
 return arr.map(item => {
  let vals = item.values
  if (!vals) {
   vals = [item.us ?? true, item.them ?? false]
  }
  return { ...item, values: vals }
 })
})

const relativeTime = inject('relativeTime', ref(0))

const getActiveProgress = (idx: number) => {
 const arr = normalizedItems.value
 const t = arr[idx].start_time
 if (t === undefined) return 0
 if (relativeTime.value < t) return 0
 let nextT = Infinity
 for (let i = idx + 1; i < arr.length; i++) {
  if (arr[i].start_time !== undefined) { nextT = arr[i].start_time; break }
 }
 if (relativeTime.value < nextT) {
  const p = Math.min((relativeTime.value - t) / 500, 1)
  return 1 - Math.pow(1 - p, 3)
 } else {
  const p = Math.max(0, 1 - ((relativeTime.value - nextT) / 500))
  return 1 - Math.pow(1 - p, 3)
 }
}

const getRowStyles = (idx: number) => {
 const p = getActiveProgress(idx)
 const active = p > 0.5
 return {
  background: active ? 'var(--item-primary-bg, var(--item-bg))' : 'var(--item-bg)',
  backdropFilter: active ? 'var(--item-primary-backdrop, var(--item-backdrop))' : 'var(--item-backdrop)',
  borderRadius: active ? 'var(--item-primary-radius, var(--item-radius))' : 'var(--item-radius)',
  boxShadow: active ? 'var(--item-primary-shadow, var(--item-shadow))' : 'var(--item-shadow)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: p > 0 ? getColorAlpha('var(--color-primary)', Math.max(p, 0.35)) : 'var(--item-border)',
  zIndex: active ? 10 : 1
 }
}

const getDotStyles = (idx: number) => {
 const p = getActiveProgress(idx)
 return { backgroundColor: p > 0 ? getColorAlpha('var(--color-primary)', p * 0.5) : 'rgb(var(--text-muted-rgb) / 0.5)' }
}

const checkSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
const xSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
</script>

<template>
 <div class="w-full max-w-5xl mx-auto flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
 
  <!-- MOBILE -->
  <div v-if="mobile" class="w-full flex flex-col gap-2 px-1 pb-1 pt-1">
   <div v-for="(row, idx) in normalizedItems" :key="row.id || idx"
    class="relative overflow-hidden border"
    :style="[{ borderRadius: 'var(--item-radius)' }, getRowStyles(idx)]">
    
    <!-- Feature Name -->
    <div class="px-3 py-1.5 flex items-center gap-2">
     <div class="w-1.5 h-1.5 shrink-0 rounded-full" :style="getDotStyles(idx)"></div>
     <div class="text-text-primary font-bold text-xs leading-tight">{{ row.label || row.name }}</div>
    </div>
    
    <!-- Comparison с заголовками -->
    <div class="px-3 pb-2 flex gap-2">
     <div v-for="(val, vIdx) in row.values" :key="vIdx"
      class="flex-1 flex flex-col items-center gap-1 py-1.5 px-1"
      :style="[{ borderRadius: 'calc(var(--item-radius) - 4px)' }, vIdx === 0 ? {} : { background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }]"
      :class="vIdx === 0 ? 'bg-color-primary/10 border border-color-primary/20' : 'border border-text-muted/20'">
      
      <!-- Заголовок колонки -->
      <span class="text-[9px] font-sans font-bold uppercase tracking-wider text-center leading-tight"
       :class="vIdx === 0 ? 'text-color-primary' : 'text-text-muted'">{{ mobileHeaders[vIdx] || normalizedHeaders[vIdx] }}</span>
      
      <!-- Значение -->
      <template v-if="typeof val === 'boolean'">
       <div v-if="val" class="w-6 h-6 rounded-full bg-color-success/20 text-color-success flex items-center justify-center border border-color-success/30">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
       </div>
       <div v-else class="w-6 h-6 rounded-full bg-color-danger/15 text-color-danger flex items-center justify-center border border-color-danger/30">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
       </div>
      </template>
      <span v-else class="font-sans font-bold text-xs text-center leading-snug" :class="vIdx === 0 ? 'text-color-primary' : 'text-text-muted'">{{ val }}</span>
     </div>
    </div>
   </div>
  </div>

  <!-- DESKTOP -->
  <div v-else class="w-full">
   
   <!-- Header -->
   <div class="grid items-center py-3 px-6 text-xs font-sans font-bold uppercase tracking-[0.15em] text-text-secondary border-b"
    :style="{ gridTemplateColumns: `2fr repeat(${normalizedHeaders.length}, 1fr)`, borderBottomWidth: 'var(--item-border-width)', borderBottomStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' }">
    <div>Features</div>
    <div v-for="(head, hIdx) in normalizedHeaders" :key="hIdx"
     class="text-center"
     :class="hIdx === 0 ? 'text-color-primary' : 'opacity-60'">
     {{ head }}
    </div>
   </div>
   
   <!-- Body -->
   <div class="flex flex-col" :style="{ gap: 'var(--item-gap)' }">
    <div v-for="(row, idx) in normalizedItems" :key="row.id || idx"
     class="grid items-center px-6 py-4 relative border transition-all duration-300"
     :style="{ gridTemplateColumns: `2fr repeat(${row.values.length}, 1fr)`, ...getRowStyles(idx) }">
     
     <div class="flex items-center gap-3 min-w-0">
      <div class="w-1.5 h-1.5 shrink-0 rounded-full" :style="getDotStyles(idx)"></div>
      <span class="text-text-primary font-medium text-[17px] truncate">{{ row.label || row.name }}</span>
     </div>
     
     <div v-for="(val, vIdx) in row.values" :key="vIdx" class="flex justify-center min-w-0">
      <template v-if="typeof val === 'boolean'">
       <div v-if="val" class="w-9 h-9 rounded-full bg-color-success/20 text-color-success flex items-center justify-center border border-color-success/30">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
       </div>
       <div v-else class="w-9 h-9 rounded-full bg-color-danger/15 text-color-danger flex items-center justify-center border border-color-danger/30">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
       </div>
      </template>
      <span v-else class="font-sans font-bold tracking-wide text-center" :class="vIdx === 0 ? 'text-color-primary' : 'text-text-muted'">{{ val }}</span>
     </div>
    </div>
   </div>
  </div>
 </div>
</template>
