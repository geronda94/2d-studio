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
  gauges: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CircularGauge')
const relativeTime = inject('relativeTime', ref(0))

const R = 54
const CIRC = 2 * Math.PI * R

const fillProgress = (g, idx) => {
  const t = g.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.count_ms))
  return 1 - Math.pow(1 - p, 3)
}

// Доля заполнения кольца. Всегда зажимается в [0, 1] — кольцо НЕ может «переполниться»
// и выглядеть как 100%, когда значение больше max (баг «118% = полное кольцо»).
const ratio = (g) => {
  const max = Number(g.max) || 100
  return Math.max(0, Math.min(1, (Number(g.value) || 0) / max))
}

const dashOffset = (g, idx) => (CIRC * (1 - ratio(g) * fillProgress(g, idx))).toFixed(2)

const revealed = (g, idx) => relativeTime.value >= (g.start_time ?? idx * motion.value.stagger_ms)

const displayValue = (g, idx) => {
  const target = Number(g.value) || 0
  return Math.round(target * fillProgress(g, idx))
}

// Перевыполнение плана (value > max) — показываем отдельным бейджем, чтобы не
// выдавать полное кольцо за «ровно 100%».
const overBy = (g) => Math.round((Number(g.value) || 0) - (Number(g.max) || 100))
const hasOver = (g) => (Number(g.value) || 0) > (Number(g.max) || 100)

// Маркер на конце дуги (в локальных координатах SVG; сам SVG повёрнут -90°).
const endPoint = (g, idx) => {
  const a = (360 * ratio(g) * fillProgress(g, idx)) * Math.PI / 180
  return { x: 64 + R * Math.cos(a), y: 64 + R * Math.sin(a) }
}

const cardReveal = (g, idx) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (g.start_time ?? idx * motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 20).toFixed(2)}px)` }
}

const accent = (g) => getHexColor(g.color || 'var(--color-secondary)')
const warn = getHexColor('var(--color-warning)')

const gridClass = computed(() => {
  const n = (props.gauges || []).length
  if (props.mobile) return n >= 3 ? 'grid-cols-2' : 'grid-cols-1'
  if (n <= 1) return 'grid-cols-1'
  if (n === 2) return 'grid-cols-2'
  if (n === 3) return 'grid-cols-3'
  return 'grid-cols-4'
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="title" class="shrink-0 mb-4 md:mb-6 text-center">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="flex-1 min-h-0 grid content-center justify-items-center gap-4 md:gap-6"
      :class="gridClass"
    >
      <div
        v-for="(g, idx) in gauges"
        :key="g.id ?? idx"
        class="flex flex-col items-center justify-center text-center w-full"
        :style="[
          cardReveal(g, idx),
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
        <div class="relative w-[clamp(130px,15vw,210px)] aspect-square">
          <svg viewBox="0 0 128 128" class="w-full h-full -rotate-90">
            <circle cx="64" cy="64" :r="R" fill="none" :stroke="getColorAlpha(accent(g), 0.15)" stroke-width="10" />
            <circle
              cx="64"
              cy="64"
              :r="R"
              fill="none"
              :stroke="accent(g)"
              stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="CIRC.toFixed(2)"
              :stroke-dashoffset="dashOffset(g, idx)"
            />
            <circle
              v-if="ratio(g) > 0"
              :cx="endPoint(g, idx).x"
              :cy="endPoint(g, idx).y"
              r="4.5"
              :fill="accent(g)"
              stroke="var(--item-bg)"
              stroke-width="2"
            />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <Icon v-if="g.icon" class="w-5 h-5 mb-1" :icon="g.icon" :style="{ color: accent(g) }" />
            <span class="font-black text-4xl text-text-primary leading-none">
              {{ displayValue(g, idx) }}<span v-if="g.unit" class="text-lg">{{ g.unit }}</span>
            </span>
          </div>
        </div>
        <p class="mt-3 text-text-primary text-sm md:text-base font-medium leading-tight">{{ g.label }}</p>
        <span
          v-if="hasOver(g)"
          class="mt-1.5 inline-flex items-center gap-1 text-[11px] font-mono font-bold px-2 py-0.5 rounded-full"
          :style="{ color: warn, background: getColorAlpha(warn, 0.12), border: '1px solid ' + getColorAlpha(warn, 0.3) }"
        >
          <Icon icon="lucide:trending-up" class="w-3 h-3" />
          +{{ overBy(g) }}{{ g.unit || '' }}
        </span>
      </div>
    </div>
  </div>
</template>
