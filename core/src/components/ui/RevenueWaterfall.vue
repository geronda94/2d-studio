<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import WaterfallChart from './WaterfallChart.vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  start: { type: Number, default: 0 },
  steps: { type: Array, default: () => [] },
  end: { type: Number, default: 0 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'RevenueWaterfall')
const relativeTime = inject('relativeTime', ref(0))

const NEGATIVE_TYPES = ['churn', 'negative', 'neg', 'loss', 'отток', 'downgrade']

const normalized = computed(() =>
  (props.steps || []).map((s) => {
    const delta = Number(s.delta) || 0
    const type = String(s.type || '').toLowerCase()
    const kind = type === 'total' ? 'total' : NEGATIVE_TYPES.includes(type) || delta < 0 ? 'neg' : 'pos'
    return { label: s.label, delta, kind, start_time: s.start_time }
  }),
)

const deltaSum = computed(() => normalized.value.reduce((acc, s) => acc + (s.kind === 'total' ? 0 : s.delta), 0))
const resolvedEnd = computed(() => (Number(props.end) || Number(props.start) + deltaSum.value))
const netChange = computed(() => resolvedEnd.value - (Number(props.start) || 0))
const grossNew = computed(() =>
  normalized.value.filter((s) => s.kind === 'pos').reduce((acc, s) => acc + s.delta, 0),
)
const churn = computed(() =>
  normalized.value.filter((s) => s.kind === 'neg').reduce((acc, s) => acc + s.delta, 0),
)

const kpis = computed(() => [
  { key: 'start', label: 'Прошлый период', value: Number(props.start) || 0, color: 'var(--color-secondary)', icon: 'lucide:flag' },
  { key: 'new', label: 'Новая выручка', value: grossNew.value, color: 'var(--color-success)', icon: 'lucide:plus-circle' },
  { key: 'churn', label: 'Отток', value: churn.value, color: 'var(--color-danger)', icon: 'lucide:minus-circle' },
  { key: 'end', label: 'Текущий период', value: resolvedEnd.value, color: 'var(--color-secondary)', icon: 'lucide:target' },
])

const fmt = (v) => {
  const n = Number(v) || 0
  const sign = n > 0 ? '+' : n < 0 ? '−' : ''
  return `${sign}€${Math.abs(n).toLocaleString('ru-RU')}k`
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
    <div v-if="!normalized.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between mb-3">
        <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Мост выручки</span>
        <span class="text-[11px] font-mono text-text-muted">{{ normalized.length }} факторов</span>
      </div>

      <div class="grid grid-cols-2 gap-2 md:grid-cols-4 mb-3">
        <div
          v-for="(k, i) in kpis"
          :key="k.key"
          class="flex items-center gap-3"
          :style="[
            {
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              padding: 'var(--item-padding)',
              borderWidth: 'var(--item-border-width)',
              borderStyle: 'var(--item-border-style)',
              borderColor: 'var(--item-border)',
              padding: 'var(--item-padding)',
            },
            reveal(i, normalized[i]),
          ]"
        >
          <Icon :icon="k.icon" class="w-5 h-5 shrink-0" :style="{ color: k.color }" />
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-widest text-text-muted truncate">{{ k.label }}</div>
            <div class="text-lg font-heading font-bold font-mono text-text-primary truncate">{{ fmt(k.value) }}</div>
          </div>
        </div>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden [&_.min-h-\[280px\]]:min-h-[200px]">
        <WaterfallChart
          :variant="variant"
          :mobile="mobile"
          start_label="Прошлый"
          :start_value="Number(start) || 0"
          :steps="normalized"
          end_label="Текущий"
          value_prefix="€"
          value_suffix="k"
        />
      </div>

      <div class="mt-2 flex items-center justify-between text-[11px] font-mono text-text-muted">
        <span class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full" :style="{ background: 'var(--color-success)' }"></span> рост
          <span class="w-2 h-2 rounded-full ml-2" :style="{ background: 'var(--color-danger)' }"></span> отток
        </span>
        <span :style="{ color: netChange >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }">
          {{ compact ? 'Δ' : 'Чистое изменение' }}: {{ fmt(netChange) }}
        </span>
      </div>
    </template>
  </div>
</template>
