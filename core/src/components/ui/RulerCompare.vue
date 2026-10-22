<script setup>
// RulerCompare — правители: вера / дела / наследие.
// Композиция примитива ComparisonTable: строка — правитель, колонки — критерии.
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import ComparisonTable from './ComparisonTable.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  rulers: { type: Array, default: () => [] },
  headers: { type: Array, default: () => ['Вера', 'Дела', 'Наследие'] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'RulerCompare')
const relativeTime = inject('relativeTime', ref(0))

const items = computed(() => (props.rulers || []).map((r, i) => ({
  id: r.id || `r${i + 1}`,
  label: r.years ? `${r.name} · ${r.years}` : r.name,
  values: [r.faith || '—', r.deeds || '—', r.legacy || '—'],
  start_time: r.start_time ?? i * motion.value.stagger_ms,
})))

const sourceReveal = computed(() => {
  const t = (props.rulers?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div v-if="!rulers.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex flex-col justify-start [&_.py-4]:!min-h-[84px]" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
        <ComparisonTable
          :variant="variant"
          :mobile="mobile"
          :headers="headers"
          :items="items"
        />
      </div>

      <p
        v-if="source_note"
        class="mt-2 shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceReveal"
      >{{ source_note }}</p>
    </template>
  </div>
</template>
