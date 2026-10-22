<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  periods: { type: Array, default: () => [] },
  pv: { type: Array, default: () => [] },
  ev: { type: Array, default: () => [] },
  ac: { type: Array, default: () => [] },
  show_index: { type: Boolean, default: true },
  numeric_x: { type: Boolean, default: false },
  unit_prefix: { type: String, default: '' },
  value_suffix: { type: String, default: '' },
  y_label: { type: String, default: '' },
  source_note: { type: String, default: '' },
  // opt-in: «круглые» деления оси Y (0/25/50/75/100) вместо дробных от max*1.08
  nice_ticks: { type: Boolean, default: false },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'SCurve')
const relativeTime = inject('relativeTime', ref(0))

const N = computed(() => Math.max(1, props.periods.length))
const rawMax = computed(() => {
  const all = [...props.pv, ...props.ev, ...props.ac].map(Number).filter((n) => !Number.isNaN(n))
  return Math.max(1, ...all)
})
// «Круглый» шаг оси: 1/2/2.5/5 × 10^n.
const niceStep = (x) => {
  if (!(x > 0)) return 1
  const pow = Math.pow(10, Math.floor(Math.log10(x)))
  for (const m of [1, 2, 2.5, 5, 10]) if (x <= m * pow) return m * pow
  return 10 * pow
}
const niceInfo = computed(() => {
  if (!props.nice_ticks) return null
  const step = niceStep(rawMax.value / 4)
  const max = Math.ceil(rawMax.value / step) * step
  const ticks = []
  for (let v = max; v >= 0; v -= step) ticks.push(Math.round(v))
  return { max, ticks }
})
const bounds = computed(() =>
  niceInfo.value ? { max: niceInfo.value.max } : { max: rawMax.value * 1.08 },
)

const maxTick = computed(() => Math.round(bounds.value.max))
const yTicks = computed(() => {
  if (niceInfo.value) return niceInfo.value.ticks
  const m = maxTick.value
  return [m, Math.round((m * 3) / 4), Math.round(m / 2), Math.round(m / 4), 0]
})

const series = computed(() => [
  { key: 'pv', label: 'PV (план)', color: 'var(--color-secondary)', values: props.pv },
  { key: 'ev', label: 'EV (освоено)', color: 'var(--color-success)', values: props.ev },
  { key: 'ac', label: 'AC (факт)', color: 'var(--color-warning)', values: props.ac },
].filter((s) => (s.values || []).length > 0))

// x от 2% до 98%: линии не касаются краёв и не режутся.
// numeric_x: позиции по реальным числовым значениям periods (неравные интервалы лет).
const numericPeriods = computed(() => props.periods.map((p) => Number(String(p).replace(/[^\d.-]/g, ''))))
const numericRange = computed(() => {
  const nums = numericPeriods.value.filter((n) => !Number.isNaN(n))
  if (nums.length < 2) return null
  const min = Math.min(...nums)
  const max = Math.max(...nums)
  return max > min ? { min, max } : null
})
const useNumericX = computed(() => props.numeric_x && numericRange.value !== null)
const fracOf = (i) => {
  if (useNumericX.value) {
    const v = numericPeriods.value[i]
    if (!Number.isNaN(v)) return (v - numericRange.value.min) / (numericRange.value.max - numericRange.value.min)
  }
  return i / Math.max(1, N.value - 1)
}
const xOf = (i) => 2 + fracOf(i) * 96
const yOf = (v) => 100 - (Number(v) / bounds.value.max) * 100
const points = (values) =>
  values.map((v, i) => `${xOf(i).toFixed(2)},${yOf(v).toFixed(2)}`).join(' ')

const draw = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * 250) / (motion.value.appear_ms * 1.8)))
  return { opacity: p.toFixed(3) }
}

const last = (arr) => (arr && arr.length ? Number(arr[arr.length - 1]) : 0)
const spi = computed(() => (last(props.pv) ? last(props.ev) / last(props.pv) : 0))
const cpi = computed(() => (last(props.ac) ? last(props.ev) / last(props.ac) : 0))
const fmtIdx = (v) => v.toFixed(2)
const compact = computed(() => props.density === 'compact' || props.mobile)
const fmtVal = (v) => `${props.unit_prefix}${v}${props.value_suffix}`
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="!periods.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex gap-2 md:gap-3">
        <!-- Y ось -->
        <div class="w-10 md:w-14 shrink-0 flex flex-col justify-between items-end pr-1 text-[9px] md:text-[10px] font-mono text-text-muted pb-6">
          <span v-for="(t, i) in yTicks" :key="'y' + i" class="-translate-y-1/2">{{ t }}</span>
        </div>

        <!-- полотно -->
        <div class="flex-1 min-w-0 relative flex flex-col">
          <div class="relative flex-1 min-h-0">
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <line v-for="g in 4" :key="'g' + g" x1="0" :x2="100" :y1="(g / 4) * 100" :y2="(g / 4) * 100"
                    stroke="var(--text-muted)" stroke-width="0.5" vector-effect="non-scaling-stroke" opacity="0.18" />
              <polyline
                v-for="(s, i) in series"
                :key="s.key"
                :points="points(s.values)"
                fill="none"
                :stroke="getHexColor(s.color)"
                stroke-width="2"
                vector-effect="non-scaling-stroke"
                :style="draw(i)"
              />
            </svg>
            <span v-if="y_label" class="absolute top-0 left-1 text-[10px] font-mono text-text-muted">{{ y_label }}</span>
          </div>

          <div class="h-6 relative shrink-0">
            <template v-if="useNumericX">
              <span v-for="(p, i) in periods" :key="'p' + i"
                    class="absolute -translate-x-1/2 whitespace-nowrap"
                    :class="compact ? 'text-[8px]' : 'text-[10px]'"
                    :style="{ left: xOf(i) + '%', color: 'var(--text-muted)' }">{{ p }}</span>
            </template>
            <div v-else class="flex gap-1.5 h-full">
              <span v-for="(p, i) in periods" :key="'p' + i" class="flex-1 text-center truncate"
                    :class="compact ? 'text-[8px]' : 'text-[10px]'" style="color: var(--text-muted)">{{ p }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div class="flex flex-wrap gap-4">
          <span v-for="s in series" :key="'lg' + s.key" class="flex items-center gap-2 text-xs text-text-secondary">
            <span class="w-3 h-3 rounded-full" :style="{ background: getHexColor(s.color) }"></span>{{ s.label }}
          </span>
        </div>
        <div v-if="show_index" class="flex gap-3">
          <div class="px-3 py-1.5 rounded-[var(--item-radius)]" :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)', border: '1px solid var(--item-border)' }">
            <span class="text-[10px] font-mono text-text-muted mr-2">SPI</span>
            <span class="font-bold" :style="{ color: getHexColor(spi >= 1 ? 'var(--color-success)' : 'var(--color-danger)') }">{{ fmtIdx(spi) }}</span>
          </div>
          <div class="px-3 py-1.5 rounded-[var(--item-radius)]" :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)', border: '1px solid var(--item-border)' }">
            <span class="text-[10px] font-mono text-text-muted mr-2">CPI</span>
            <span class="font-bold" :style="{ color: getHexColor(cpi >= 1 ? 'var(--color-success)' : 'var(--color-danger)') }">{{ fmtIdx(cpi) }}</span>
          </div>
        </div>
      </div>

      <div v-if="source_note" class="mt-2 text-[11px] font-mono text-text-muted shrink-0">{{ source_note }}</div>
    </template>
  </div>
</template>
