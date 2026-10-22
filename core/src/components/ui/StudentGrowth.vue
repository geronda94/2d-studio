<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  points: { type: Array, default: () => [] },
  target: { type: [Number, String], default: null },
  bands: { type: Array, default: () => [] },
  growth: { type: String, default: '' },
})

const { itemVars, line, motion } = useVariant(computed(() => props.variant), 'StudentGrowth')
const relativeTime = inject('relativeTime', ref(0))

const pointsList = computed(() => props.points || [])
const n = computed(() => pointsList.value.length || 1)
const last = computed(() => pointsList.value.length - 1)

const allValues = computed(() => {
  const arr = pointsList.value.map((p) => Number(p.value) || 0)
  props.bands.forEach((b) => arr.push(Number(b.from) || 0, Number(b.to) || 0))
  if (props.target !== null && props.target !== '' && props.target !== undefined) arr.push(Number(props.target))
  return arr
})
const minV = computed(() => (allValues.value.length ? Math.min(...allValues.value) : 0))
const maxV = computed(() => (allValues.value.length ? Math.max(...allValues.value) : 100))
const span = computed(() => Math.max(1, maxV.value - minV.value))

const y = (v) => 100 - ((Number(v) - minV.value) / span.value) * 100
const x = (i) => ((i + 0.5) / n.value) * 100

const linePoints = computed(() =>
  pointsList.value.map((p, i) => `${x(i).toFixed(2)},${y(p.value).toFixed(2)}`).join(' '),
)

const bandTop = (b) => Math.min(y(b.from), y(b.to))
const bandHeight = (b) => Math.abs(y(b.to) - y(b.from))

const pointReveal = (p, i) => {
  const t = p.start_time ?? i * motion.value.stagger_ms
  const prog = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - prog, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.6 + 0.4 * e).toFixed(3)})` }
}

const lineOpacity = computed(() => {
  if (last.value < 0) return 0
  const t = pointsList.value[last.value].start_time ?? last.value * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return (1 - Math.pow(1 - p, 3)).toFixed(3)
})

const targetY = computed(() => y(props.target))
// Точка рядом с линией цели: подпись под ней перечёркнута — переносим наверх.
const labelAbove = (p) =>
  props.target !== null && props.target !== '' && props.target !== undefined &&
  Math.abs(y(p.value) - targetY.value) < 10

const ticks = computed(() =>
  [0, 1, 2, 3, 4].map((i) => Math.round(maxV.value - (i * span.value) / 4)),
)
const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div class="shrink-0 mb-3 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-text-muted">
      <span class="uppercase tracking-widest">Динамика обучения · baseline → target</span>
      <span v-if="growth" class="flex items-center gap-1" :style="{ color: getHexColor('var(--color-success)') }">
        <Icon icon="lucide:trending-up" class="w-3.5 h-3.5" />Рост {{ growth }}
      </span>
    </div>

    <div
      v-if="!points.length"
      class="relative w-full flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0">
      <div class="absolute inset-0 pb-7 pl-9 pr-2">
        <div class="relative w-full h-full">
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <rect
              v-for="(b, bi) in bands"
              :key="'band' + bi"
              x="0"
              width="100"
              :y="bandTop(b)"
              :height="bandHeight(b)"
              :fill="getColorAlpha(b.color || 'var(--color-secondary)', 0.12)"
            />
            <line
              v-for="(t, ti) in ticks"
              :key="'g' + ti"
              x1="0"
              x2="100"
              :y1="y(t)"
              :y2="y(t)"
              stroke="var(--item-border)"
              stroke-width="1"
              vector-effect="non-scaling-stroke"
              :style="{ opacity: 0.5 }"
            />
            <line
              v-if="target !== null && target !== ''"
              x1="0"
              x2="100"
              :y1="targetY"
              :y2="targetY"
              :stroke="getHexColor('var(--color-warning)')"
              stroke-width="2"
              stroke-dasharray="5 5"
              vector-effect="non-scaling-stroke"
            />
            <polyline
              :points="linePoints"
              fill="none"
              :stroke="line.color"
              :stroke-width="line.width"
              vector-effect="non-scaling-stroke"
              stroke-linecap="round"
              stroke-linejoin="round"
              :style="{ opacity: lineOpacity }"
            />
            <line
              v-if="last > 0"
              :x1="x(0)"
              :y1="y(pointsList[0].value)"
              :x2="x(last)"
              :y2="y(pointsList[last].value)"
              :stroke="getHexColor('var(--color-success)')"
              stroke-width="1.5"
              stroke-dasharray="3 4"
              vector-effect="non-scaling-stroke"
              :style="{ opacity: lineOpacity }"
            />
          </svg>

          <span
            v-for="(b, bi) in bands"
            :key="'bl' + bi"
            class="absolute left-1 text-[9px] font-mono px-1 rounded"
            :style="{ top: (bandTop(b) + bandHeight(b) / 2) + '%', transform: 'translateY(-50%)', background: getColorAlpha(b.color || 'var(--color-secondary)', 0.18), color: 'var(--text-primary)' }"
          >{{ b.label }}</span>

          <div
            v-for="(p, i) in pointsList"
            :key="'p' + i"
            class="absolute flex items-center gap-1 whitespace-nowrap"
            :class="labelAbove(p) ? 'flex-col-reverse' : 'flex-col'"
            :style="[{ left: x(i) + '%', top: y(p.value) + '%' }, pointReveal(p, i)]"
          >
            <span
              class="w-3 h-3 rounded-full"
              :style="{ background: line.color, boxShadow: '0 0 0 3px ' + getColorAlpha('var(--color-secondary)', 0.22) }"
            ></span>
            <span class="text-[10px] font-mono text-text-primary px-1 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: 'rgb(var(--bg-base-rgb) / 0.5)' }" :class="labelAbove(p) ? 'mb-2' : 'mt-1.5'">{{ p.value }}</span>
          </div>

          <div
            v-if="growth && last >= 0"
            class="absolute flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono"
            :style="{ left: x(last) + '%', top: y(pointsList[last].value) + '%', transform: 'translate(-50%, -240%)', background: getColorAlpha('var(--color-success)', 0.16), color: getHexColor('var(--color-success)'), opacity: lineOpacity }"
          >
            <Icon icon="lucide:trending-up" class="w-3 h-3" />{{ growth }}
          </div>
        </div>
      </div>

      <div
        class="absolute bottom-0 left-9 right-2 grid gap-1"
        :style="{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }"
      >
        <span v-for="(p, i) in pointsList" :key="'x' + i" class="text-center text-[10px] font-mono text-text-muted truncate">
          {{ p.label }}
        </span>
      </div>

      <div
        class="absolute top-0 bottom-7 left-0 w-9 flex flex-col justify-between items-end pr-1 text-[9px] font-mono text-text-muted"
      >
        <span v-for="(t, ti) in ticks" :key="'yt' + ti" class="-translate-y-1/2">{{ t }}</span>
      </div>
    </div>
  </div>
</template>
