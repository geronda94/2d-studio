<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  buckets: { type: Array, default: () => [] },
  milestones: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'UseOfFunds')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const RADIUS = 40
const CIRC = 2 * Math.PI * RADIUS

const sumAmounts = computed(() => (props.buckets || []).reduce((acc, b) => acc + (Number(b.amount) || 0), 0))
const totalValue = computed(() => Number(props.total) || sumAmounts.value)

const segments = computed(() => {
  let acc = 0
  return (props.buckets || []).map((b, i) => {
    const amount = Number(b.amount) || 0
    const frac = totalValue.value ? amount / totalValue.value : 0
    const len = frac * CIRC
    const seg = {
      label: b.label,
      amount,
      frac,
      i,
      color: getHexColor(b.color || accent(i)),
      dash: `${len.toFixed(3)} ${(CIRC - len).toFixed(3)}`,
      offset: (-acc * CIRC).toFixed(3),
    }
    acc += frac
    return seg
  })
})

const milestoneList = computed(() =>
  (props.milestones || []).map((m) => (typeof m === 'string' ? { label: m } : m)),
)

const fmt = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e9) return '€' + (n / 1e9).toFixed(1).replace(/\.0$/, '') + 'B'
  if (Math.abs(n) >= 1e6) return '€' + (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M'
  if (Math.abs(n) >= 1e3) return '€' + (n / 1e3).toFixed(0) + 'K'
  return '€' + n.toLocaleString('ru-RU')
}

const reveal = (i, item) => {
  const t = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!segments.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col gap-1.5 md:gap-3">
        <div class="flex-1 min-h-0 flex flex-col gap-1.5 md:gap-3 md:flex-row md:items-stretch">
          <div class="relative mx-auto shrink-0 aspect-square w-full max-w-[180px] md:max-w-[300px] self-center">
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" :style="reveal(0)">
              <circle
                cx="50"
                cy="50"
                :r="RADIUS"
                fill="none"
                :stroke="getColorAlpha('var(--text-primary)', 0.08)"
                stroke-width="12"
              />
              <g transform="rotate(-90 50 50)">
                <circle
                  v-for="s in segments"
                  :key="'seg' + s.i"
                  cx="50"
                  cy="50"
                  :r="RADIUS"
                  fill="none"
                  :stroke="s.color"
                  stroke-width="12"
                  :stroke-dasharray="s.dash"
                  :stroke-dashoffset="s.offset"
                />
              </g>
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-[10px] uppercase tracking-widest text-text-muted">Всего</span>
              <span class="mt-1 text-3xl leading-none font-heading font-bold text-text-primary">{{ fmt(totalValue) }}</span>
            </div>
          </div>

          <div class="min-w-0 grid grid-cols-2 gap-2 flex-1 auto-rows-fr md:flex md:flex-col md:gap-2">
            <div
              v-for="s in segments"
              :key="'leg' + s.i"
              class="flex flex-col justify-center gap-1.5 md:flex-1 md:gap-2"
              :style="[
                {
                  background: 'var(--item-bg)',
                  backdropFilter: 'var(--item-backdrop)',
                  WebkitBackdropFilter: 'var(--item-backdrop)',
                  borderRadius: 'var(--item-radius)',
                  boxShadow: 'var(--item-shadow)',
                  padding: 'var(--item-padding)',
                  borderWidth: 'var(--item-border-width)',
                  borderStyle: 'var(--item-border-style)',
                  borderColor: 'var(--item-border)',
                  padding: compact ? '8px 10px' : 'var(--item-padding)',
                },
                reveal(s.i + 1, buckets[s.i]),
              ]"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: s.color }"></span>
                  <span class="text-sm font-bold text-text-primary truncate">{{ s.label }}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0 font-mono text-[11px]">
                  <span class="text-text-muted">{{ (s.frac * 100).toFixed(0) }}%</span>
                  <span class="text-text-primary font-bold">{{ fmt(s.amount) }}</span>
                </div>
              </div>
              <div
                class="h-1.5 w-full overflow-hidden"
                :style="{ background: getColorAlpha('var(--text-primary)', 0.08), borderRadius: '999px' }"
              >
                <div
                  class="h-full w-full origin-left"
                  :style="{ background: s.color, transform: `scaleX(${s.frac.toFixed(4)})` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="milestoneList.length" class="shrink-0 grid grid-cols-1 sm:grid-cols-3 gap-2 pb-3">
          <div
            v-for="(m, i) in milestoneList"
            :key="'ms' + i"
            class="flex items-center justify-center gap-2 px-3 py-1.5 md:py-2.5"
            :style="[
              {
                background: 'var(--item-bg)',
                backdropFilter: 'var(--item-backdrop)',
                WebkitBackdropFilter: 'var(--item-backdrop)',
                borderRadius: 'var(--item-radius)',
                boxShadow: 'var(--item-shadow)',
                padding: 'var(--item-padding)',
                borderWidth: 'var(--item-border-width)',
                borderStyle: 'var(--item-border-style)',
                borderColor: getColorAlpha(accent(i), 0.4),
              },
              reveal(segments.length + i, m),
            ]"
          >
            <Icon icon="lucide:milestone" class="w-4 h-4 shrink-0" :style="{ color: accent(i) }" />
            <span class="text-xs text-text-primary">{{ m.label }}</span>
            <span v-if="m.period" class="text-[10px] font-mono text-text-muted">{{ m.period }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
