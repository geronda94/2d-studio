<template>
  <div class="roi-calculator w-full max-w-[900px] mx-auto flex flex-col gap-2 md:gap-4"
  :style="{
  ...itemVars,
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  paddingTop: mobile ? 'calc(var(--item-padding) + 0.6rem)' : 'calc(var(--item-padding) + 1.5rem)',
  paddingBottom: mobile ? 'calc(var(--item-padding) + 0.4rem)' : 'calc(var(--item-padding) + 1rem)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
  }">
 
 <!-- Sliders Grid -->
 <div :class="['grid gap-x-6 gap-y-1 lg:gap-y-2', mobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2']">
      <div v-for="(v, idx) in localVariables" :key="idx" class="flex flex-col gap-1 py-1 md:py-1.5 px-3 hover:bg-bg-surface/[0.02]" :style="{ borderRadius: 'calc(var(--item-radius) - 4px)' }">
 
 <div class="flex justify-between items-end gap-3">
 <label class="text-[10px] sm:text-xs uppercase tracking-wider text-text-secondary font-semibold flex items-center gap-2 leading-tight flex-1">
 <Icon v-if="v.icon" :icon="v.icon" class="w-4 h-4 md:w-5 md:h-5 text-color-secondary opacity-90 shrink-0" />
 <span class="break-words">{{ v.label }}</span>
 </label>
 <div class="text-lg md:text-xl font-mono text-text-primary font-bold shrink-0">
 {{ formatNumber(v.current, v.step) }} <span class="text-[9px] md:text-[10px] text-color-secondary font-sans opacity-70 ml-0.5">{{ v.suffix }}</span>
 </div>
 </div>
 
 <div class="relative w-full flex items-center mt-1">
 <input 
 type="range" 
 :min="v.min" 
 :max="v.max" 
 :step="v.step || 1"
 v-model.number="v.current"
 @input="v.manualOverride = true"
 :style="{ '--progress': `${v.max > v.min ? ((v.current - v.min) / (v.max - v.min)) * 100 : 0}%` }"
 class="w-full h-1.5 rounded-full appearance-none cursor-pointer outline-none hover:opacity-90 bg-transparent"
 />
 </div>
 </div>
 </div>

 <!-- Accent Result Row (Minimalistic) -->
 <div class="mt-1 pt-2 pb-1 md:mt-2 md:pt-4 relative w-full flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-3 md:px-4 border-t border-text-muted">
 
 <div class="flex flex-col flex-1 pr-4">
 <div class="text-[10px] md:text-xs text-color-secondary uppercase tracking-[0.3em] font-bold mb-0.5 opacity-90">{{ result_label || 'Итого' }}</div>
 <div v-if="result_description" class="text-[9px] md:text-[10px] text-text-muted max-w-[300px]">
 {{ result_description }}
 </div>
 </div>
 
 <div class="flex items-baseline gap-1.5 sm:gap-2 shrink-0 whitespace-nowrap">
 <span :class="['font-heading font-black text-text-primary tracking-tight tabular-nums', mobile ? 'text-3xl sm:text-4xl' : 'text-4xl sm:text-5xl']">
 <AnimatedNumber :value="calculatedResult" />
 </span>
 <span v-if="result_suffix" :class="['text-color-secondary font-black', mobile ? 'text-xl sm:text-2xl' : 'text-2xl sm:text-3xl']">{{ result_suffix }}</span>
 </div>
 </div>
 </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 title: {
 type: String,
 default: ''
 },
 mobile: {
 type: Boolean,
 default: false
 },
 variant: String,
 variables: {
 type: Array,
 default: () => [] 
 },
 result_base: {
 type: Number,
 default: 0
 },
 result_label: {
 type: String,
 default: 'Итоговая выгода'
 },
 result_suffix: {
 type: String,
    default: '€'
 },
 result_description: {
 type: String,
 default: ''
 }
})

const relativeTime = inject('relativeTime', ref(0))
const { itemVars } = useVariant(computed(() => props.variant), 'RoiCalculator')
const localVariables = ref([])

const mapVariables = (vars) => {
 return vars.map(v => ({ 
 ...v, 
 current: v.min, // always start at min
 target: v.target !== undefined ? v.target : (v.current || 0), // fallback to current if target not set
 manualOverride: false 
 }))
}

onMounted(() => {
 if (props.variables && props.variables.length > 0) {
 localVariables.value = mapVariables(props.variables)
 }
})

watch(() => props.variables, (newVars) => {
 if (newVars && newVars.length > 0) {
 localVariables.value = mapVariables(newVars)
 } else {
 // Keep localVariables as is, or reset to mock if preferred, 
 // but better to just use what's there.
 }
}, { deep: true })

watch(relativeTime, (time) => {
 for (const v of localVariables.value) {
 if (v.manualOverride) continue;
 
 const start = v.start_time || 0
 const dur = v.duration || 500
 
 if (time >= start) {
 const progress = Math.min((time - start) / dur, 1)
 const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress) // easeOutExpo
 
 const rawValue = v.min + (v.target - v.min) * ease
 v.current = rawValue
 } else {
 v.current = v.min
 }
 }
})

const calculatedResult = computed(() => {
 let total = props.result_base
 for (const v of localVariables.value) {
 total += (v.current * (v.multiplier || 1))
 }
 return Math.max(0, total) // Prevent negative ROI for this simple calc
})

const formatNumber = (num, step = 1) => {
 const inv = 1.0 / step
 const rounded = Math.round(num * inv) / inv
 const isFloat = step % 1 !== 0
 const digits = isFloat ? 1 : 0
 return new Intl.NumberFormat('ru-RU', { 
 minimumFractionDigits: digits,
 maximumFractionDigits: digits 
 }).format(rounded)
}
</script>

<script>
// Inline AnimatedNumber component to keep it self-contained
import { defineComponent, h, Transition } from 'vue'

const AnimatedNumber = defineComponent({
 props: {
 value: { type: Number, required: true },
 duration: { type: Number, default: 500 }
 },
 setup(props) {
 const displayValue = ref(props.value)
 
 watch(() => props.value, (newVal) => {
 displayValue.value = newVal
 })
 
 return () => {
 return h('span', new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(Math.round(displayValue.value)))
 }
 }
})
</script>

<style scoped>
/* Custom range slider styling */
input[type=range]::-webkit-slider-thumb {
 -webkit-appearance: none;
 height: 14px;
 width: 14px;
 border-radius: 50%;
 background: var(--text-primary);
 cursor: pointer;
 margin-top: -4px;
}
input[type=range]::-moz-range-thumb {
 height: 14px;
 width: 14px;
 border-radius: 50%;
 background: var(--text-primary);
 cursor: pointer;
 border: none;
}
input[type=range]::-webkit-slider-runnable-track {
 width: 100%;
 height: 6px;
 cursor: pointer;
 background: linear-gradient(to right, var(--color-secondary) var(--progress, 0%), rgb(var(--text-primary-rgb) / 0.1) var(--progress, 0%));
 border-radius: 3px;
}
input[type=range]::-moz-range-track {
 width: 100%;
 height: 6px;
 cursor: pointer;
 background: linear-gradient(to right, var(--color-secondary) var(--progress, 0%), rgb(var(--text-primary-rgb) / 0.1) var(--progress, 0%));
 border-radius: 3px;
}
</style>
