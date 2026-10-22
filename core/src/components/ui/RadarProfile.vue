<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  axes: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  max: { type: Number, default: 100 },
  unit: { type: String, default: '' },
  source_note: { type: String, default: '' },
  fill_opacity: { type: Number, default: 0.14 },
  show_legend: { type: Boolean, default: true },
  radius: { type: Number, default: 39 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'RadarProfile')
const relativeTime = inject('relativeTime', ref(0))

const N = computed(() => Math.max(1, props.axes.length))
const cx = 50
const cy = 50
const R = computed(() => Math.max(20, Math.min(46, props.radius || 39)))
// Отступ подписей осей: сжимается при большом радиусе, чтобы текст не вылезал за viewBox.
const labelGap = computed(() => Math.min(7.5, 49 - R.value))

const axisPoint = (i, r) => {
  const a = (i / N.value) * Math.PI * 2 - Math.PI / 2
  return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]
}
const labelPoint = (i) => {
  const a = (i / N.value) * Math.PI * 2 - Math.PI / 2
  return [cx + Math.cos(a) * (R.value + labelGap.value), cy + Math.sin(a) * (R.value + labelGap.value)]
}

const polygonPoints = (values, progress = 1) =>
  values
    .map((v, i) => {
      const r = (Math.min(1, (Number(v) || 0) / (props.max || 1)) * R.value) * progress
      const [x, y] = axisPoint(i, r)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')

const ringPoints = (frac) =>
  Array.from({ length: N.value }, (_, i) => axisPoint(i, R.value * frac).map((n) => n.toFixed(2)).join(',')).join(' ')

const seriesProgress = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / (motion.value.appear_ms * 1.6)))
  return 1 - Math.pow(1 - p, 3)
}

const color = (s) => getHexColor(s.color || 'var(--color-secondary)')
const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div
    class="w-full max-w-5xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars }"
  >
    <div v-if="!axes.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0">
        <svg class="absolute inset-0 w-full h-full" :viewBox="compact ? '-10 -6 120 112' : '0 0 100 100'" preserveAspectRatio="xMidYMid meet">
          <!-- кольца -->
          <polygon v-for="f in [0.25, 0.5, 0.75, 1]" :key="'r' + f" :points="ringPoints(f)" fill="none" stroke="var(--text-muted)" stroke-width="0.35" opacity="0.35" />
          <!-- спицы -->
          <line v-for="(a, i) in axes" :key="'s' + i" :x1="cx" :y1="cy" :x2="axisPoint(i, R)[0]" :y2="axisPoint(i, R)[1]" stroke="var(--text-muted)" stroke-width="0.35" opacity="0.35" />
          <!-- полигоны -->
          <polygon
            v-for="(s, i) in series"
            :key="'p' + i"
            :points="polygonPoints(s.values || [], seriesProgress(i))"
            :fill="getColorAlpha(color(s), fill_opacity)"
            :stroke="color(s)"
            stroke-width="2.2"
            stroke-linejoin="round"
            vector-effect="non-scaling-stroke"
          />
          <!-- подписи осей -->
          <text
            v-for="(a, i) in axes"
            :key="'t' + i"
            :x="labelPoint(i)[0]"
            :y="labelPoint(i)[1]"
            text-anchor="middle"
            dominant-baseline="middle"
            :style="{ fontSize: compact ? '3.4px' : '4.4px', fontWeight: 600, fill: 'var(--text-primary)' }"
          >{{ a }}</text>
        </svg>
      </div>

      <div v-if="show_legend && series.length" class="shrink-0 mt-2 flex flex-wrap items-center justify-center gap-4">
        <span v-for="s in series" :key="'lg' + s.label" class="flex items-center gap-2 text-xs text-text-secondary">
          <span class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: color(s) }"></span>{{ s.label }}
        </span>
      </div>

      <div v-if="source_note" class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-secondary opacity-90">{{ source_note }}</div>
    </template>
  </div>
</template>
