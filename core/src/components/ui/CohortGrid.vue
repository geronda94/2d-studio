<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  cohorts: { type: Array, default: () => [] },
  periods: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  metric: { type: String, default: '%' },
  suffix: { type: String, default: '%' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CohortGrid')
const relativeTime = inject('relativeTime', ref(0))

const maxVal = computed(() => {
  const nums = (props.values || []).flat().map(Number).filter((n) => !Number.isNaN(n))
  return Math.max(1, ...nums)
})

const cellStyle = (v) => {
  if (v === null || v === undefined || v === '') return { background: 'transparent', color: 'var(--text-muted)' }
  const num = Number(v)
  const ratio = Number.isNaN(num) ? 0.5 : Math.max(0, Math.min(1, num / maxVal.value))
  return {
    background: getColorAlpha('var(--color-secondary)', 0.08 + ratio * 0.62),
    color: ratio > 0.6 ? 'var(--text-primary)' : 'var(--text-secondary)',
  }
}

const reveal = (r, c) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (r + c) * 60) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(3) }
}

const fmt = (v) => (v === null || v === undefined || v === '' ? '' : `${v}${props.suffix}`)
const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!cohorts.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex flex-col">
        <div
          class="grid gap-1.5 md:gap-2 flex-1 min-h-0"
          :style="{
            gridTemplateColumns: `minmax(72px, 1.2fr) repeat(${periods.length}, minmax(0, 1fr))`,
            gridTemplateRows: `auto repeat(${cohorts.length}, minmax(0, 1fr))`,
          }"
        >
          <div class="text-[10px] md:text-xs font-mono text-text-muted flex items-end pb-1">Когорта</div>
          <div v-for="(p, pi) in periods" :key="'p' + pi" class="text-center text-[10px] md:text-xs font-mono text-text-muted pb-1 truncate">{{ p }}</div>

          <template v-for="(co, ri) in cohorts" :key="'r' + ri">
            <div class="flex items-center text-xs md:text-sm text-text-secondary pr-2 truncate">{{ co }}</div>
            <div
              v-for="(p, ci) in periods"
              :key="'c' + ri + '-' + ci"
              class="h-full min-h-[2rem] rounded-[calc(var(--item-radius)*0.5)] flex items-center justify-center text-[11px] md:text-sm font-mono"
              :style="[cellStyle((values[ri] || [])[ci]), reveal(ri, ci)]"
            >
              {{ fmt((values[ri] || [])[ci]) }}
            </div>
          </template>
        </div>

        <div class="mt-2 md:mt-3 shrink-0 flex items-center justify-between">
          <span class="text-[11px] md:text-xs font-mono text-text-secondary">Метрика: {{ metric }}</span>
          <span v-if="source_note" class="text-[11px] md:text-xs font-mono text-text-secondary opacity-90">{{ source_note }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
