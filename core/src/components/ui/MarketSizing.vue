<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  layers: { type: Array, default: () => [] },
  currency: { type: String, default: '€' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'MarketSizing')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const ordered = computed(() =>
  (props.layers || [])
    .map((l, i) => ({ ...l, _i: i }))
    .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0)),
)

const maxVal = computed(() => Math.max(1, ...ordered.value.map((l) => Number(l.value) || 0)))
const side = (l) => Math.sqrt(Math.max(0, (Number(l.value) || 0) / maxVal.value))

const fmt = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, '') + 'B'
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M'
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return String(Math.round(n))
}

const reveal = (i, l) => {
  const t = l?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `scale(${(0.94 + 0.06 * e).toFixed(4)})` }
}

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!ordered.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between mb-3">
        <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Объём рынка</span>
        <span class="text-[11px] font-mono text-text-muted">TAM · SAM · SOM</span>
      </div>

      <div class="flex flex-col gap-3 flex-1 min-h-0" :class="compact ? '' : 'md:flex-row md:items-stretch'">
        <div class="relative w-full flex-1 min-h-0 overflow-hidden">
          <div
            v-for="(l, idx) in ordered"
            :key="'box' + l.name"
            class="absolute"
            :style="[
              {
                width: `${(side(l) * 100).toFixed(2)}%`,
                height: `${(side(l) * 100).toFixed(2)}%`,
                left: `${((1 - side(l)) * 50).toFixed(2)}%`,
                bottom: `${((1 - side(l)) * 50).toFixed(2)}%`,
                background: getColorAlpha(accent(l._i), 0.1 + idx * 0.05),
                borderWidth: '1px',
                borderStyle: 'solid',
                borderColor: getColorAlpha(accent(l._i), 0.55),
                borderRadius: 'var(--item-radius)',
              },
              reveal(idx, l),
            ]"
          >
            <span
              class="absolute top-1.5 left-2 text-[10px] font-mono font-bold uppercase tracking-widest"
              :style="{ color: accent(l._i) }"
            >{{ l.name }}</span>
          </div>
        </div>

        <div class="w-full shrink-0 flex flex-col gap-2" :class="compact ? '' : 'md:w-72'">
          <div
            v-for="(l, idx) in ordered"
            :key="'leg' + l.name"
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
              reveal(idx, l),
            ]"
          >
            <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: accent(l._i) }"></span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-bold text-text-primary truncate">{{ l.name }}</div>
              <div class="text-[11px] font-mono text-text-muted">{{ currency }}{{ fmt(l.value) }}</div>
            </div>
            <div
              class="flex items-center gap-1 text-[11px] font-mono shrink-0"
              :style="{ color: (Number(l.growth) || 0) >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }"
            >
              <Icon :icon="(Number(l.growth) || 0) >= 0 ? 'lucide:trending-up' : 'lucide:trending-down'" class="w-3 h-3" />
              <span>{{ (Number(l.growth) || 0) >= 0 ? '+' : '' }}{{ Number(l.growth || 0).toFixed(0) }}%</span>
            </div>
          </div>

          <div v-if="source_note" class="text-[11px] font-mono text-text-secondary opacity-90">{{ source_note }}</div>
        </div>
      </div>
    </template>
  </div>
</template>
