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
  points: { type: Array, default: () => [] },
  connections: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'MapVisualization')
const relativeTime = inject('relativeTime', ref(0))

const clampPct = (v) => Math.max(0, Math.min(100, Number(v) || 0))

// Растягиваем координаты на рабочую область, чтобы маркеры не сбивались в полосу.
const spread = (vals, lo, hi) => {
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  if (!isFinite(min) || !isFinite(max) || max - min < 0.001) {
    return vals.map(() => (lo + hi) / 2)
  }
  return vals.map((v) => lo + ((v - min) / (max - min)) * (hi - lo))
}

const layout = computed(() => {
  const list = props.points || []
  const map = {}
  if (!list.length) return map
  const xs = spread(list.map((p) => clampPct(p.x)), 14, 86)
  const ys = spread(list.map((p) => clampPct(p.y)), 18, 78)
  list.forEach((p, i) => (map[p.id] = { x: xs[i], y: ys[i] }))
  return map
})

const pointAt = (id) => layout.value[id] || { x: 50, y: 50 }

const pointReveal = (pt, idx) => {
  const t = pt.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.6 + 0.4 * e).toFixed(3)})` }
}

const connReveal = (cn) => {
  const t = cn.start_time ?? 0
  return Math.max(0, Math.min(1, (relativeTime.value - t) / 600))
}

// Детерминированная пульсация маркера (Math.sin, без infinite CSS).
const pulse = (pt, idx) => 1 + 0.12 * (0.5 + 0.5 * Math.sin((relativeTime.value / 1600 + idx) * Math.PI * 2))

const accent = (pt) => getHexColor(pt.color || 'var(--color-secondary)')
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="title" class="mb-3 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="relative w-full flex-1 min-h-[280px] overflow-hidden"
      :style="{
        background: 'var(--item-bg)',
        backdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)',
        boxShadow: 'var(--item-shadow)',
        padding: 'var(--item-padding)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)',
        borderColor: 'var(--item-border)',
      }"
    >
      <!-- Стилизованная «карта»: градиентная подложка, суша, река, широтная сетка -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient id="mv-sea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="getColorAlpha('var(--color-secondary)', 0.10)" />
            <stop offset="100%" :stop-color="getColorAlpha('var(--color-secondary)', 0.02)" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="100" height="100" fill="url(#mv-sea)" />
        <path
          d="M 6 64 C 12 42, 30 30, 45 37 C 55 42, 58 29, 71 28 C 86 27, 96 42, 91 58 C 86 74, 69 80, 55 75 C 43 71, 33 83, 21 79 C 11 76, 3 73, 6 64 Z"
          :fill="getColorAlpha('var(--text-muted)', 0.2)"
        />
        <g :stroke="getColorAlpha('var(--text-muted)', 0.28)" stroke-width="1" vector-effect="non-scaling-stroke">
          <line v-for="n in 9" :key="'vx' + n" :x1="n * 10" y1="0" :x2="n * 10" y2="100" />
          <line v-for="n in 5" :key="'hy' + n" x1="0" :y1="n * 16.6" x2="100" :y2="n * 16.6" />
        </g>
      </svg>

      <svg class="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
        <line
          v-for="(cn, idx) in connections"
          :key="'c' + idx"
          :x1="pointAt(cn.from).x + '%'"
          :y1="pointAt(cn.from).y + '%'"
          :x2="pointAt(cn.to).x + '%'"
          :y2="pointAt(cn.to).y + '%'"
          :stroke="getColorAlpha('var(--color-secondary)', 0.9)"
          stroke-width="2"
          stroke-dasharray="6 6"
          vector-effect="non-scaling-stroke"
          :style="{ opacity: connReveal(cn) }"
        />
      </svg>

      <div
        v-for="(pt, idx) in points"
        :key="pt.id ?? idx"
        class="absolute flex flex-col items-center w-[28%]"
        :style="[{ left: pointAt(pt.id).x + '%', top: pointAt(pt.id).y + '%', willChange: 'transform' }, pointReveal(pt, idx)]"
      >
        <span
          class="mb-1 px-2 py-0.5 rounded text-[10px] md:text-[11px] font-bold text-center leading-tight break-words max-w-full"
          :style="{ background: 'rgb(var(--bg-base-rgb) / 0.85)', color: accent(pt) }"
        >{{ pt.label }}</span>
        <div
          class="w-9 h-9 rounded-full flex items-center justify-center"
          :style="{
            background: getColorAlpha(accent(pt), 0.2),
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            border: '2px solid ' + accent(pt),
            transform: `scale(${pulse(pt, idx).toFixed(3)})`,
          }"
        >
          <Icon :icon="pt.icon || 'heroicons:map-pin'" class="w-4 h-4" :style="{ color: accent(pt) }" />
        </div>
      </div>
    </div>
  </div>
</template>
