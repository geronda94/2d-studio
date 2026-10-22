<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import BloomLadder from './BloomLadder.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  levels: { type: Array, default: () => [] },
  active: { type: [Number, String], default: null },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'LadderOfVirtues')
const relativeTime = inject('relativeTime', ref(0))

const mapped = computed(() => (props.levels || []).map((l, i) => ({
  name: l.name,
  task: l.description,
  icon: l.icon,
  color: l.color || `var(--item-accent-${(i % 4) + 1})`,
  start_time: l.start_time ?? i * motion.value.stagger_ms,
})))

const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const sourceReveal = computed(() => {
  const levels = props.levels || []
  const last = levels[levels.length - 1]
  const lastT = last ? (last.start_time ?? (levels.length - 1) * motion.value.stagger_ms) : 0
  const t = lastT + (motion.value.appear_ms || 500)
  const e = 1 - Math.pow(1 - clamp01((relativeTime.value - t) / (motion.value.appear_ms || 500)), 3)
  return e.toFixed(3)
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!levels.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div
        class="relative flex-1 min-h-0 overflow-hidden [&_.min-h-\[320px\]]:min-h-[220px] [&_.mb-3]:hidden [&_.truncate]:!whitespace-normal [&_.truncate]:!overflow-visible"
        :class="mobile ? 'px-2' : ''"
      >
        <BloomLadder
          :variant="variant"
          :mobile="mobile"
          :levels="mapped"
          :active_level="active"
        />
      </div>

      <div v-if="source" class="mt-2 shrink-0 text-right text-[11px] font-mono text-text-muted" :style="{ opacity: sourceReveal }">{{ source }}</div>
    </template>
  </div>
</template>
