<script setup>
// ArchaeologyConfirms — археология подтверждает Писание.
// Композиция примитива ModernTable: находка → место, датировка, что подтверждает.
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import ModernTable from './ModernTable.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  finds: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ArchaeologyConfirms')
const relativeTime = inject('relativeTime', ref(0))

const columns = computed(() => {
  const base = [
    { key: 'icon', label: '', type: 'icon', align: 'center' },
    { key: 'artifact', label: 'Находка', type: 'text' },
    { key: 'place', label: 'Место', type: 'text' },
  ]
  // На мобиле датировку не выводим отдельной ячейкой — экономим высоту карточки
  if (!props.mobile) base.push({ key: 'year', label: 'Датировка', type: 'text', align: 'center' })
  base.push({ key: 'confirms', label: 'Подтверждает', type: 'text' })
  return base
})

const rows = computed(() => (props.finds || []).map((f, i) => ({
  icon: f.icon || 'lucide:landmark',
  artifact: f.artifact,
  place: f.place,
  year: f.year,
  confirms: f.confirms,
  start_time: f.start_time ?? i * motion.value.stagger_ms,
})))

const sourceReveal = computed(() => {
  const t = (props.finds?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div v-if="!finds.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex flex-col justify-start [&_.py-5]:!py-2 [&_.py-4]:!py-2 [&_.py-3]:!py-2" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
        <ModernTable
          :variant="variant"
          :mobile="mobile"
          :dense="!mobile"
          :columns="columns"
          :rows="rows"
          :full-width="true"
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
