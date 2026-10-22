<script setup>
// FineTuningScales — антропный принцип: тонкая настройка физических констант.
// Композиция примитива MetricScales: константа → степень точной настройки (шкала),
// ниже — измеренное значение, допуск и пояснение.
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'
import MetricScales from './MetricScales.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  constants: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'FineTuningScales')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const metrics = computed(() => (props.constants || []).map((c, i) => ({
  label: c.name,
  percentage: Math.round(Math.max(1, Math.min(100, Number(c.precision) || 1))),
  icon: c.icon || 'lucide:sliders-horizontal',
  color: c.color || `linear-gradient(to right, ${getColorAlpha(accent(i), 0.3)}, ${accent(i)})`,
  start_time: c.start_time ?? i * motion.value.stagger_ms,
})))

const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
}

const sourceReveal = computed(() => {
  const t = (props.constants?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!constants.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative flex-1 min-h-0 overflow-y-auto pr-1">
        <MetricScales :variant="variant" :mobile="mobile" :metrics="metrics" />
      </div>

      <div class="shrink-0 grid grid-cols-2 gap-x-4 gap-y-1 px-3 pt-2">
        <div
          v-for="(c, i) in constants"
          :key="'d' + i"
          class="flex items-baseline gap-1.5 text-[11px] md:text-xs font-mono min-w-0"
          :style="reveal(c, i)"
        >
          <Icon icon="lucide:ruler" class="w-3.5 h-3.5 shrink-0 self-center" :style="{ color: accent(i) }" />
          <span class="text-text-secondary shrink-0">{{ c.value }}</span>
          <span v-if="c.tolerance" class="text-text-muted shrink-0">±{{ c.tolerance }}</span>
          <span v-if="c.note" class="text-text-muted opacity-70 min-w-0 truncate">{{ c.note }}</span>
        </div>
      </div>

      <p
        v-if="source_note"
        class="mt-1.5 shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceReveal"
      >{{ source_note }}</p>
    </template>
  </div>
</template>
