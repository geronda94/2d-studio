<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import ComparisonTable from './ComparisonTable.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  rows: { type: Array, default: () => [] },
  headers: { type: Array, default: () => ['Физический закон', 'Духовный принцип'] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'LawParallel')
const relativeTime = inject('relativeTime', ref(0))

const items = computed(() =>
  props.rows.map((r, i) => ({
    id: `r${i + 1}`,
    label: r.principle,
    values: [r.physical, r.spiritual],
    start_time: r.start_time ?? i * motion.value.stagger_ms,
  })),
)

const noteStyle = computed(() => {
  const t = props.rows.length * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4) }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div class="flex-1 min-h-0 flex flex-col justify-start [&_.py-4]:!py-2 [&_.py-3]:!py-2" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
      <ComparisonTable
        :variant="variant"
        :mobile="mobile"
        :headers="headers"
        :items="items"
      />
    </div>

    <p
      v-if="source_note"
      class="mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
      :style="noteStyle"
    >{{ source_note }}</p>
  </div>
</template>
