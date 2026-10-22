<script setup>
import { computed, inject, ref } from 'vue'
import EcosystemSlide from '../slides/EcosystemSlide.vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  center: { type: Object, default: () => ({ label: '', icon: '' }) },
  nodes: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ChurchAsBody')
const relativeTime = inject('relativeTime', ref(0))

const mappedNodes = computed(() =>
  (props.nodes || []).map((n, i) => ({
    ...n,
    label: n.label ?? n.name ?? '',
    start_time: n.start_time ?? (i + 1) * motion.value.stagger_ms,
  })),
)

const noteReveal = computed(() => {
  const starts = (props.nodes || []).map((n, i) => Number(n.start_time ?? (i + 1) * motion.value.stagger_ms))
  const last = starts.length ? Math.max(...starts) : 0
  const start = last + motion.value.appear_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div class="flex-1 min-h-0 overflow-hidden">
      <EcosystemSlide
        :variant="variant"
        :mobile="mobile"
        :center="center"
        :nodes="mappedNodes"
      />
    </div>
    <p
      v-if="source_note"
      class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-muted"
      :style="noteReveal"
    >{{ source_note }}</p>
  </div>
</template>
