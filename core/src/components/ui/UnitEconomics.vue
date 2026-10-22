<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  metrics: { type: Array, default: () => [] },
  payback_months: { type: Number, default: 0 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'UnitEconomics')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const payback = computed(() => Math.max(1, Math.round(Number(props.payback_months) || 0)))
// Горизонт шкалы шире окупаемости, чтобы маркер не упирался в 100% и был заметен.
const horizon = computed(() => Math.max(payback.value + 4, Math.ceil(payback.value * 1.4)))
const paybackFrac = computed(() => Math.min(1, payback.value / horizon.value))
const tickCount = computed(() => Math.min(24, horizon.value))

const fmtValue = (v) => {
  if (v === null || v === undefined || v === '') return '—'
  if (typeof v === 'number') return v.toLocaleString('ru-RU', { maximumFractionDigits: 2 })
  const n = Number(v)
  return Number.isNaN(n) ? String(v) : n.toLocaleString('ru-RU', { maximumFractionDigits: 2 })
}

const reveal = (i, m) => {
  const t = m?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const fillScale = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - 300) / motion.value.count_ms))
  return ((1 - Math.pow(1 - p, 3)) * paybackFrac.value).toFixed(4)
})

const markerReveal = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - 300 - motion.value.count_ms) / motion.value.appear_ms))
  return { opacity: p.toFixed(3), transform: `scale(${(0.7 + 0.3 * p).toFixed(3)})` }
})

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!metrics.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col gap-4">
        <div class="flex-1 min-h-0 grid gap-3 auto-rows-fr" :style="{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }">
          <div
            v-for="(m, i) in metrics"
            :key="m.label + i"
            class="flex flex-col justify-center gap-1.5"
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
                padding: 'var(--item-padding)',
              },
              reveal(i, m),
            ]"
          >
            <div class="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-text-muted">
              <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ background: accent(i) }"></span>
              <span class="truncate">{{ m.label }}</span>
            </div>
            <div class="flex items-baseline gap-1.5">
              <span class="font-heading font-bold text-text-primary" :class="compact ? 'text-3xl' : 'text-4xl'">
                {{ fmtValue(m.value) }}
              </span>
              <span v-if="m.unit" class="text-base font-sans" :style="{ color: accent(i) }">{{ m.unit }}</span>
            </div>
            <div v-if="m.target !== undefined && m.target !== null" class="flex items-center gap-1 text-[11px] font-mono text-text-muted">
              <Icon icon="lucide:target" class="w-3 h-3" />
              <span>цель {{ fmtValue(m.target) }}{{ m.unit || '' }}</span>
            </div>
          </div>
        </div>

        <div
          class="flex-1 min-h-0 flex flex-col justify-center"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
            padding: 'var(--item-padding)',
          }"
        >
          <div class="flex items-center justify-between mb-5">
            <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Окупаемость привлечения</span>
            <div class="flex items-center gap-1.5">
              <Icon icon="lucide:timer" class="w-4 h-4" :style="{ color: 'var(--color-success)' }" />
              <span class="text-base font-bold font-sans text-text-primary">{{ payback }} мес</span>
            </div>
          </div>

          <div class="relative h-16">
            <div
              class="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-3 rounded-full"
              :style="{ background: getColorAlpha('var(--text-primary)', 0.08) }"
            ></div>
            <div
              class="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-3 origin-left rounded-full"
              :style="{ background: getColorAlpha('var(--color-success)', 0.85), transform: `scaleX(${fillScale})` }"
            ></div>

            <div
              v-for="m in tickCount"
              :key="'t' + m"
              class="absolute top-1/2 w-px h-3 -translate-y-1/2"
              :style="{ left: `${(m / tickCount) * 100}%`, background: getColorAlpha('var(--text-primary)', 0.22) }"
            ></div>

            <div
              class="absolute top-0 bottom-0 flex flex-col items-center"
              :style="[{ left: `${paybackFrac * 100}%` }, { transform: 'translateX(-50%)' }, markerReveal]"
            >
              <Icon icon="lucide:flag" class="w-5 h-5" :style="{ color: 'var(--color-success)' }" />
              <span class="mt-1 text-[11px] font-sans font-bold whitespace-nowrap" :style="{ color: 'var(--color-success)' }">{{ payback }} мес</span>
            </div>
          </div>

          <div class="flex justify-between text-[10px] font-mono text-text-muted mt-1">
            <span>0 мес</span>
            <span>{{ horizon }} мес</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
