<script setup lang="ts">
import { computed, inject, ref } from 'vue'

interface Charge {
 name: string
 price: number
 start_time?: number
}

const props = withDefaults(defineProps<{
 title?: string
 subtitle?: string
 currency?: string
 total_text?: string
 footer_text?: string
 total_start_time?: number
 items?: Charge[]
}>(), {
 title: 'CORPORATE CARD',
 subtitle: 'August 2026',
 currency: '€',
 total_text: 'TOTAL DUE',
 footer_text: 'THANK YOU FOR YOUR MONEY',
 total_start_time: 2500,
 items: () => []
})

const relativeTime = inject('relativeTime', ref(0))

// Слайд с чеком перестраивается в layout='row' (заголовок слева, чек справа) —
// наш отлаженный тюнинг. Без этого чек «плывёт» под заголовком.
const setSlideLayout = inject('setSlideLayout', null)
if (setSlideLayout) setSlideLayout('row')

const getAnimProgress = (start_time: number = 0, duration = 300) => {
 const elapsed = Math.max(0, relativeTime.value - start_time)
 const p = Math.min(1, elapsed / duration)
 return 1 - Math.pow(1 - p, 3)
}

const getElasticProgress = (start_time: number = 0, duration = 800) => {
 const elapsed = Math.max(0, relativeTime.value - start_time)
 let t = Math.min(1, Math.max(0, elapsed / duration))
 if (t === 0) return 0
 if (t === 1) return 1
 const c1 = 1.70158
 const c3 = c1 + 1
 return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
}

const getDelayedProgress = (start_time: number = 0, delay = 500, duration = 500) => {
 const elapsed = Math.max(0, relativeTime.value - start_time - delay)
 const p = Math.min(1, Math.max(0, elapsed / duration))
 return 1 - Math.pow(1 - p, 3)
}

const totalSum = computed(() => {
 return (props.items || []).reduce((sum, item) => sum + (Number(item.price) || 0), 0)
})

</script>

<template>
  <div class="receipt-card bg-[#F8FAFC] rounded-xl w-80 md:w-[25rem] shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative rotate-0 md:rotate-1 origin-center h-full max-h-full mx-auto flex flex-col">
 
 <!-- Зубчатый край сверху -->
 <div class="h-2 w-full bg-[radial-gradient(circle,transparent_4px,#F8FAFC_4px)] bg-[length:16px_16px] -mt-1 relative z-10 shrink-0" style="background-position: -4px -8px"></div>

 <div class="p-5 text-slate-800 font-mono flex flex-col overflow-hidden h-full min-h-0 flex-1">
 <!-- Шапка чека -->
  <div v-if="props.title || props.subtitle" class="text-center border-b-2 border-dashed border-slate-300 pb-3 mb-3 shrink-0">
  <h3 v-if="props.title" class="font-bold text-xl uppercase tracking-widest text-slate-900">{{ props.title }}</h3>
  <p v-if="props.subtitle" class="text-xs text-slate-500 mt-1 font-sans">{{ props.subtitle }}</p>
  </div>

 <!-- Список списаний -->
 <div class="space-y-2 overflow-y-auto scrollbar-hide flex-1 min-h-0 py-1 relative">
 <div v-for="(charge, idx) in props.items" :key="idx" 
 class="flex justify-between text-sm items-center"
 :style="{
 opacity: getAnimProgress(charge.start_time),
 transform: `translateX(${(1 - getAnimProgress(charge.start_time)) * -15}px)`
 }">
 <span class="text-slate-600 line-clamp-1 font-semibold pr-2">{{ charge.name }}</span>
 <span class="font-bold tabular-nums whitespace-nowrap" :style="{ color: 'var(--color-error, #DC2626)' }">-{{ props.currency }}{{ Number(charge.price).toFixed(2) }}</span>
 </div>
 </div>

 <!-- Итого -->
 <div class="mt-4 pt-3 border-t-2 border-dashed border-slate-300 flex justify-between items-end shrink-0 overflow-visible pb-1">
 <span class="text-sm font-bold uppercase tracking-wider text-slate-900 mb-1">{{ props.total_text }}</span>
 
 <div class="relative">
 <span class="inline-block text-3xl font-bold font-heading tabular-nums origin-center"
 :style="{
 color: 'var(--color-error, #DC2626)',
 opacity: Math.min(1, Math.max(0, getElasticProgress(props.total_start_time))),
 transform: `scale(${2.5 - 1.5 * getElasticProgress(props.total_start_time)}) translateY(${(1 - getElasticProgress(props.total_start_time)) * -24}px)`,
 filter: `blur(${(1 - Math.min(1, Math.max(0, getElasticProgress(props.total_start_time)))) * 8}px)`
 }">
 {{ props.currency }}{{ totalSum.toFixed(2) }}
 </span>
 <div class="absolute -bottom-1 left-0 h-[3px] origin-left rounded-full"
 :style="{
 background: 'var(--color-error, #DC2626)',
 transform: `scaleX(${getDelayedProgress(props.total_start_time)})`,
 width: '100%'
 }"></div>
 </div>
 </div>

 <!-- Футер (Штрихкод) -->
 <div class="mt-5 text-center shrink-0">
 <svg class="mx-auto h-10 w-full opacity-60 text-slate-900" viewBox="0 0 100 30" preserveAspectRatio="none">
 <rect x="5" y="0" width="2" height="30" fill="currentColor"/>
 <rect x="10" y="0" width="4" height="30" fill="currentColor"/>
 <rect x="18" y="0" width="1" height="30" fill="currentColor"/>
 <rect x="22" y="0" width="6" height="30" fill="currentColor"/>
 <rect x="31" y="0" width="2" height="30" fill="currentColor"/>
 <rect x="37" y="0" width="4" height="30" fill="currentColor"/>
 <rect x="44" y="0" width="1" height="30" fill="currentColor"/>
 <rect x="48" y="0" width="5" height="30" fill="currentColor"/>
 <rect x="57" y="0" width="2" height="30" fill="currentColor"/>
 <rect x="62" y="0" width="4" height="30" fill="currentColor"/>
 <rect x="70" y="0" width="1" height="30" fill="currentColor"/>
 <rect x="74" y="0" width="7" height="30" fill="currentColor"/>
 <rect x="85" y="0" width="2" height="30" fill="currentColor"/>
 <rect x="91" y="0" width="4" height="30" fill="currentColor"/>
 </svg>
 <p class="text-[9px] font-sans text-slate-500 mt-3 tracking-[0.2em] uppercase font-bold">{{ props.footer_text }}</p>
 </div>
 </div>

 <!-- Зубчатый край снизу -->
 <div class="h-2 w-full bg-[radial-gradient(circle,transparent_4px,#F8FAFC_4px)] bg-[length:16px_16px] mb-0 md:-mb-1 relative z-10 rotate-180 shrink-0" style="background-position: -4px -8px"></div>
 </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
 display: none;
}
.scrollbar-hide {
 -ms-overflow-style: none;
 scrollbar-width: none;
}
</style>
