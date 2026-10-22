<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'
import MapVisualization from './MapVisualization.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  points: { type: Array, default: () => [] },
  legend: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'RelicsMap')
const relativeTime = inject('relativeTime', ref(0))

const legendFor = (type) =>
  (props.legend || []).find((l) => l.type === type || l.label === type) || {}

const mapPoints = computed(() =>
  props.points.map((p, i) => {
    const lg = legendFor(p.type)
    return {
      id: p.id ?? `pt-${i}`,
      x: p.x,
      y: p.y,
      label: p.label,
      icon: p.icon || lg.icon || 'heroicons:map-pin',
      color: p.color || lg.color || 'var(--color-secondary)',
      start_time: p.start_time ?? i * motion.value.stagger_ms,
    }
  }),
)

const noteStyle = computed(() => {
  const t = props.points.length * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4) }
})

const legendColor = (l) => getHexColor(l.color || 'var(--color-secondary)')
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div class="flex-1 min-h-0 overflow-hidden">
      <MapVisualization
        :variant="variant"
        :mobile="mobile"
        :points="mapPoints"
      />
    </div>

    <div v-if="legend.length" class="mt-3 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5">
      <span
        v-for="(l, i) in legend"
        :key="l.type || l.label || i"
        class="flex items-center gap-1.5 text-[11px] md:text-xs text-text-secondary"
      >
        <Icon :icon="l.icon || 'heroicons:map-pin'" class="w-3.5 h-3.5" :style="{ color: legendColor(l) }" />
        {{ l.label }}
      </span>
    </div>

    <p
      v-if="source_note"
      class="mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
      :style="noteStyle"
    >{{ source_note }}</p>
  </div>
</template>
