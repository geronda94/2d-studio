<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import CohortGrid from './CohortGrid.vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  cohorts: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  metric: { type: String, default: 'logo' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CohortRetention')
const relativeTime = inject('relativeTime', ref(0))

const isNrr = computed(() => String(props.metric).toLowerCase() === 'nrr')
const metricLabel = computed(() => (isNrr.value ? 'Net Revenue Retention' : 'Logo Retention'))

const periods = computed(() => {
  const n = Math.max(0, ...(props.values || []).map((r) => (Array.isArray(r) ? r.length : 0)))
  return Array.from({ length: n }, (_, i) => `M${i}`)
})

const avgAt = (idx) => {
  const nums = (props.values || [])
    .map((r) => Number((r || [])[idx]))
    .filter((n) => !Number.isNaN(n) && n !== 0)
  if (!nums.length) return null
  return nums.reduce((a, b) => a + b, 0) / nums.length
}

const lastValue = computed(() => {
  const first = props.values?.[0] || []
  const nums = first.map(Number).filter((n) => !Number.isNaN(n) && n !== 0)
  return nums.length ? nums[nums.length - 1] : null
})

const kpis = computed(() => {
  const defs = [
    { key: 'm1', label: 'Удержание M1', value: avgAt(1), color: 'var(--color-secondary)', icon: 'lucide:user-check' },
    { key: 'm3', label: 'Удержание M3', value: avgAt(3), color: 'var(--item-accent-2)', icon: 'lucide:users' },
    {
      key: 'last',
      label: isNrr.value ? 'NRR (последняя)' : 'Logo (последняя)',
      value: lastValue.value,
      color: 'var(--color-success)',
      icon: 'lucide:trending-up',
    },
  ]
  return defs.filter((d) => d.value !== null && d.value !== undefined)
})

const tailDelta = computed(() => {
  if (lastValue.value === null) return null
  return isNrr.value ? lastValue.value - 100 : 100 - lastValue.value
})

const fmtPct = (v) => (v === null || v === undefined ? '—' : `${Number(v).toFixed(0)}%`)

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!cohorts.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between mb-3 gap-2">
        <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">{{ metricLabel }}</span>
        <div
          v-if="tailDelta !== null"
          class="flex items-center gap-2 px-3 py-1"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: getColorAlpha(isNrr ? 'var(--color-success)' : 'var(--color-danger)', 0.4),
          }"
        >
          <Icon
            :icon="isNrr ? 'lucide:trending-up' : 'lucide:user-minus'"
            class="w-3.5 h-3.5"
            :style="{ color: isNrr ? 'var(--color-success)' : 'var(--color-danger)' }"
          />
          <span class="text-xs text-text-secondary">{{ isNrr ? 'Рост' : 'Churn' }}</span>
          <span class="text-sm font-bold font-mono text-text-primary">
            {{ tailDelta > 0 ? '+' : '' }}{{ fmtPct(tailDelta) }}
          </span>
        </div>
      </div>

      <div class="grid gap-2 mb-4" :class="compact ? 'grid-cols-1' : 'grid-cols-3'">
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
            reveal(i),
          ]"
        >
          <Icon :icon="k.icon" class="w-5 h-5 shrink-0" :style="{ color: k.color }" />
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-widest text-text-muted truncate">{{ k.label }}</div>
            <div class="text-base font-heading font-bold font-mono text-text-primary">{{ fmtPct(k.value) }}</div>
          </div>
        </div>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden">
        <CohortGrid
          :variant="variant"
          :mobile="mobile"
          :cohorts="cohorts"
          :periods="periods"
          :values="values"
          :metric="metricLabel"
          suffix="%"
        />
      </div>

      <div class="mt-2 text-[11px] font-mono text-text-muted">
        {{ isNrr ? 'Когорты по выручке с учётом расширения и сжатия' : 'Когорты по числу клиентов' }}
      </div>
    </template>
  </div>
</template>
