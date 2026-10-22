<script setup>
// InfluenceMap — кто на кого повлиял (граф).
// Композиция примитива KnowledgeGraph: узлы-личности и направленные связи-влияния.
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import KnowledgeGraph from './KnowledgeGraph.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'InfluenceMap')
const relativeTime = inject('relativeTime', ref(0))

const concepts = computed(() => (props.nodes || []).map((n, i) => ({
  id: n.id ?? `n${i}`,
  label: n.label ?? n.name ?? '',
  icon: n.icon || 'lucide:user',
  color: n.color || `var(--item-accent-${(i % 4) + 1})`,
  is_main: !!n.is_main,
  start_time: n.start_time ?? i * motion.value.stagger_ms,
})))

const connections = computed(() => (props.edges || []).map((e, i) => ({
  from: e.from,
  to: e.to,
  label: e.label || '',
  start_time: e.start_time ?? i * motion.value.stagger_ms,
})))

const sourceReveal = computed(() => {
  const t = (props.edges?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!nodes.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 overflow-hidden flex flex-col [&_.min-h-\[300px\]]:min-h-[200px]">
        <KnowledgeGraph
          :variant="variant"
          :mobile="mobile"
          :concepts="concepts"
          :connections="connections"
        />
      </div>

      <p
        v-if="source_note"
        class="shrink-0 mt-1 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceReveal"
      >{{ source_note }}</p>
    </template>
  </div>
</template>
