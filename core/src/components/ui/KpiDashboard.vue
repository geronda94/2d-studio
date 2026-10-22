<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  metrics: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'KpiDashboard')
const relativeTime = inject('relativeTime', ref(0))

const cardProgress = (m, idx) => {
  const t = m.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const cardStyle = (m, idx) => {
  const e = cardProgress(m, idx)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 22).toFixed(2)}px) scale(${(0.96 + 0.04 * e).toFixed(4)})` }
}

// Детерминированный спарклайн: points из массива чисел, «прорисовка» через strokeDashoffset.
const sparkPoints = (arr) => {
  const vals = (arr || []).filter((v) => typeof v === 'number')
  if (vals.length < 2) return ''
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = Math.max(1e-6, max - min)
  return vals
    .map((v, i) => {
      const x = (i / (vals.length - 1)) * 100
      const y = 30 - ((v - min) / range) * 26 - 2
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

const sparkStyle = (m, idx) => {
  const t = m.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / (motion.value.appear_ms * 2)))
  return { strokeDasharray: '120 120', strokeDashoffset: (120 * (1 - p)).toFixed(2) }
}

const trendUp = (m) => String(m.trend || '').trim().startsWith('+')
</script>

<template>
  <div class="w-full max-w-5xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="title" class="mb-5 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div class="flex-1 min-h-0 grid items-stretch gap-4 md:gap-5" :class="(metrics || []).length >= 3 ? 'grid-cols-2 lg:grid-cols-4' : 'grid-cols-1 md:grid-cols-2'">
      <div
        v-for="(m, idx) in metrics"
        :key="m.id ?? idx"
        class="relative overflow-hidden flex flex-col justify-between min-h-[150px]"
        :style="[
          cardStyle(m, idx),
          {
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          },
        ]"
      >
        <div class="flex items-center gap-2 shrink-0">
          <span
            class="w-8 h-8 flex items-center justify-center shrink-0"
            :style="{ background: getColorAlpha(getHexColor(m.color || 'var(--color-secondary)'), 0.15), color: getHexColor(m.color || 'var(--color-secondary)'), borderRadius: 'calc(var(--item-radius) - 4px)' }"
          >
            <Icon :icon="m.icon || 'heroicons:chart-bar'" class="w-5 h-5" />
          </span>
          <p class="text-text-secondary text-[11px] md:text-xs font-mono uppercase tracking-wider truncate">{{ m.label }}</p>
        </div>

        <div class="flex-1 min-h-0 flex items-center">
          <div class="flex items-end gap-1">
            <span class="font-black text-5xl md:text-6xl text-text-primary leading-none">{{ m.value }}</span>
            <span v-if="m.unit" class="text-text-muted text-base md:text-lg mb-0.5">{{ m.unit }}</span>
          </div>
        </div>

        <div class="flex items-end justify-between gap-3 shrink-0">
          <svg viewBox="0 0 100 32" preserveAspectRatio="none" class="h-14 md:h-16 flex-1 min-w-0 mr-1" fill="none">
            <polyline
              v-if="sparkPoints(m.sparkline)"
              :points="sparkPoints(m.sparkline)"
              :style="sparkStyle(m, idx)"
              :stroke="getHexColor(m.color || 'var(--color-secondary)')"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <div
            v-if="m.trend"
            class="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold shrink-0"
            :style="{
              background: getColorAlpha(trendUp(m) ? 'var(--color-success)' : 'var(--color-warning)', 0.15),
              border: '1px solid',
              borderColor: getColorAlpha(trendUp(m) ? 'var(--color-success)' : 'var(--color-warning)', 0.3),
              color: trendUp(m) ? 'var(--color-success)' : 'var(--color-warning)',
            }"
          >
            <Icon :icon="trendUp(m) ? 'heroicons:arrow-trending-up' : 'heroicons:arrow-trending-down'" class="w-3 h-3" />
            {{ m.trend }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
