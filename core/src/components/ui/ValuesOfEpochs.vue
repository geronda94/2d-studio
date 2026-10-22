<script setup>
// ValuesOfEpochs — ценности эпох и цивилизаций по оси времени.
// Композиция примитива TimelineEras: эпоха → период, ядро ценностей, артефакт.
import { computed, inject, ref } from 'vue'
import TimelineEras from './TimelineEras.vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  epochs: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ValuesOfEpochs')
const relativeTime = inject('relativeTime', ref(0))

const eras = computed(() =>
  (props.epochs || []).map((e, i) => {
    const core = Array.isArray(e.core_values) ? e.core_values.join(' · ') : e.core_values || ''
    const artifact = e.artifact ? `«${e.artifact}»` : ''
    return {
      id: e.id ?? `epoch${i}`,
      name: e.name,
      period: e.period ?? '',
      icon: e.icon || 'lucide:hourglass',
      color: e.color || `var(--item-accent-${(i % 4) + 1})`,
      description: [core, artifact].filter(Boolean).join(' — '),
      start_time: e.start_time ?? i * motion.value.stagger_ms,
    }
  }),
)

const lastTime = computed(() =>
  eras.value.length ? (eras.value[eras.value.length - 1].start_time || 0) : 0,
)

const sourceStyle = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - lastTime.value) / motion.value.appear_ms))
  return { opacity: p.toFixed(3) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!eras.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col justify-center gap-4">
        <div class="w-full" :class="mobile ? 'flex-1 min-h-0 flex flex-col' : 'shrink-0'">
          <TimelineEras :variant="variant" :mobile="mobile" :eras="eras" />
        </div>

        <p
          v-if="source_note"
          class="shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
          :style="sourceStyle"
        >
          {{ source_note }}
        </p>
      </div>
    </template>
  </div>
</template>
