<template>
 <div class="w-full h-full flex flex-col relative overflow-hidden">
 <!-- Chart Container -->
 <div class="flex-1 w-full min-h-0 flex items-center justify-center relative z-10 py-2">
 <div :class="containerClass" class="w-full">
 <AnimatedStats v-for="(stat, idx) in stats.slice(0, 4)" :key="idx" v-bind="stat" :variant="variant" :mobile="mobile" />
 </div>
 </div>
 </div>
</template>
<script setup>
import { computed } from 'vue'
import AnimatedStats from '../ui/AnimatedStats.vue'

const props = defineProps({ mobile: Boolean, variant: String, stats: { type: Array, default: () => [] } })

// Раскладка: 2 и 3 стата — одна строка (3-across), 4 — 2×2 на узких и 4-across на широких.
// Раньше 3-й стат уезжал один во вторую строку → разбалансированный кадр.
const containerClass = computed(() => {
 if (props.mobile) {
 return props.stats.length >= 4
 ? 'flex flex-col gap-2 w-full px-2'
 : 'flex flex-col gap-5 w-full px-2'
 }

 if (props.stats.length === 4) {
 return 'grid grid-cols-2 xl:grid-cols-4 gap-5 w-full max-h-[440px] max-w-[1500px] mx-auto px-4'
 }

 return 'grid grid-cols-1 md:grid-cols-3 gap-5 w-full max-h-[440px] max-w-[1500px] mx-auto px-4'
})
</script>
