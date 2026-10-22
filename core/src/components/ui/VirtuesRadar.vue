<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import RadarProfile from './RadarProfile.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  axes: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  max: { type: Number, default: 10 },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'VirtuesRadar')
const relativeTime = inject('relativeTime', ref(0))

const ACCENTS = ['var(--color-primary)', 'var(--color-secondary)', 'var(--color-success)']

const radarSeries = computed(() =>
  props.series.map((s, i) => ({
    label: s.name || '',
    values: s.values || [],
    color: s.color || ACCENTS[i % ACCENTS.length],
  })),
)

const noteStyle = computed(() => {
  const t = props.series.length * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div class="flex-1 min-h-0 overflow-hidden">
      <RadarProfile
        :variant="variant"
        :mobile="mobile"
        :axes="axes"
        :series="radarSeries"
        :max="max"
        :radius="mobile ? 34 : 45"
      />
    </div>

    <p
      v-if="source_note"
      class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-secondary opacity-90"
      :style="noteStyle"
    >{{ source_note }}</p>
  </div>
</template>
