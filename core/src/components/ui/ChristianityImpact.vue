<script setup>
// ChristianityImpact — влияние христианства: область → было → стало.
// Композиция примитива InfographicCards: крупно «стало», подпись «было».
import { computed, inject, ref } from 'vue'
import InfographicCards from './InfographicCards.vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  areas: { type: Array, default: () => [] },
  before_label: { type: String, default: 'Было' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ChristianityImpact')
const relativeTime = inject('relativeTime', ref(0))

const items = computed(() =>
  (props.areas || []).map((a, i) => ({
    id: a.id ?? `area${i}`,
    label: a.domain,
    value: a.after,
    trend: a.trend || '',
    desc: a.before ? `${props.before_label}: ${a.before}` : '',
    color: a.color || `var(--item-accent-${(i % 4) + 1})`,
    icon: a.icon || 'lucide:sparkles',
    start_time: a.start_time ?? i * motion.value.stagger_ms,
  })),
)

const lastTime = computed(() =>
  items.value.length ? (items.value[items.value.length - 1].start_time || 0) : 0,
)

const sourceStyle = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - lastTime.value) / motion.value.appear_ms))
  return { opacity: p.toFixed(3) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!items.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex items-center">
        <InfographicCards :variant="variant" :mobile="mobile" :items="items" />
      </div>

      <div
        v-if="source_note"
        class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceStyle"
      >
        {{ source_note }}
      </div>
    </template>
  </div>
</template>
