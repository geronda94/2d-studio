<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  points: { type: Array, default: () => [] },
  mean: { type: Number, default: 0 },
  ucl: { type: Number, default: 0 },
  lcl: { type: Number, default: 0 },
  unit: { type: String, default: '' },
  violations: { type: Array, default: () => [] },
  target: { type: Number, default: null },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ControlChart')
const relativeTime = inject('relativeTime', ref(0))

const bounds = computed(() => {
  const vals = [props.mean, props.ucl, props.lcl, ...(props.points || [])].map(Number)
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const pad = (max - min) * 0.15 || 1
  return { min: min - pad, max: max + pad }
})
const toY = (v) => 100 - ((Number(v) - bounds.value.min) / (bounds.value.max - bounds.value.min)) * 100
const toX = (i) => 1 + (i / Math.max(1, (props.points.length || 1) - 1)) * 97

const linePoints = computed(() => (props.points || []).map((v, i) => `${toX(i).toFixed(2)},${toY(v).toFixed(2)}`).join(' '))
const violationSet = computed(() => new Set(props.violations || []))

const draw = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - 150) / (motion.value.appear_ms * 2)))
  return { opacity: p.toFixed(3) }
})
const dotReveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * 60) / motion.value.appear_ms))
  return (1 - Math.pow(1 - p, 3)).toFixed(3)
}
const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div class="w-full max-w-5xl mx-auto flex flex-col overflow-hidden" :style="{ ...itemVars }">
    <div v-if="!points.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-[300px] flex gap-2">
        <div class="w-10 flex flex-col justify-between text-right text-[9px] font-mono text-text-muted shrink-0">
          <span>{{ Math.round(bounds.max) }}</span>
          <span>{{ Math.round(mean) }}</span>
          <span>{{ Math.round(bounds.min) }}</span>
        </div>
        <div class="relative flex-1 min-h-[300px] pr-1">
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <line x1="0" x2="100" :y1="toY(ucl)" :y2="toY(ucl)" stroke="var(--color-danger)" stroke-width="1" stroke-dasharray="5 4" vector-effect="non-scaling-stroke" />
            <line x1="0" x2="100" :y1="toY(mean)" :y2="toY(mean)" stroke="var(--color-secondary)" stroke-width="1" vector-effect="non-scaling-stroke" />
            <line x1="0" x2="100" :y1="toY(lcl)" :y2="toY(lcl)" stroke="var(--color-danger)" stroke-width="1" stroke-dasharray="5 4" vector-effect="non-scaling-stroke" />
            <polyline :points="linePoints" fill="none" :stroke="getHexColor('var(--color-secondary)')" stroke-width="2" vector-effect="non-scaling-stroke" :style="draw" />
            <circle
              v-for="(v, i) in points"
              :key="'pt' + i"
              :cx="toX(i)"
              :cy="toY(v)"
              :r="violationSet.has(i) ? 1.6 : 1"
              :fill="violationSet.has(i) ? getHexColor('var(--color-danger)') : getHexColor('var(--color-secondary)')"
              :style="{ opacity: dotReveal(i) }"
            />
          </svg>
          <span class="absolute right-0 text-[9px] font-mono text-color-danger" :style="{ top: `${toY(ucl)}%` }">UCL {{ ucl }}{{ unit }}</span>
          <span class="absolute right-0 text-[9px] font-mono text-color-danger" :style="{ top: `${toY(lcl)}%` }">LCL {{ lcl }}{{ unit }}</span>
        </div>
      </div>

      <div class="flex items-center justify-between mt-3 text-xs text-text-secondary">
        <span>X̄-карта · {{ points.length }} точек</span>
        <span v-if="violationSet.size" class="text-color-danger font-medium">Выход за контроль: {{ violationSet.size }}</span>
        <span v-else class="text-color-success font-medium">Процесс стабилен</span>
      </div>

      <div v-if="source_note" class="mt-2 text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</div>
    </template>
  </div>
</template>
