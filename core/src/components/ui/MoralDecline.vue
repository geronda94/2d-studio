<script setup>
// MoralDecline — деградация нравственного ориентира во времени.
// Композиция примитива SCurve (кривая) + строка маркеров-переломов.
// Данные только из props; время — relativeTime; движение — transform/opacity.
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import SCurve from './SCurve.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  periods: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  markers: { type: Array, default: () => [] },
  value_suffix: { type: String, default: '' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'MoralDecline')
const relativeTime = inject('relativeTime', ref(0))

const markerTime = (m, i) => m.start_time ?? i * motion.value.stagger_ms

const markerReveal = (m, i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - markerTime(m, i)) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const markerStyle = (m, i) => {
  const e = markerReveal(m, i)
  return {
    opacity: e.toFixed(4),
    transform: `translateY(${((1 - e) * 12).toFixed(2)}px)`,
  }
}

const markerAccent = (m, i) => getHexColor(m.color || `var(--item-accent-${(i % 4) + 1})`)
</script>

<template>
  <div class="moral-decline w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!periods.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col">
        <div class="shrink-0 mb-1 flex items-center justify-between text-[11px] font-mono text-text-muted">
          <span>Доля христиан, %</span>
        </div>
        <SCurve
          :variant="variant"
          :mobile="mobile"
          :periods="periods"
          :pv="values"
          :show_index="false"
          numeric_x
          nice_ticks
          :value_suffix="value_suffix"
          :source_note="source_note"
        />
      </div>

      <div
        v-if="markers.length"
        class="shrink-0 mt-3 grid gap-2"
        :class="mobile ? 'grid-cols-1' : 'grid-cols-2 md:grid-cols-4'"
      >
        <div
          v-for="(m, i) in markers"
          :key="m.id ?? i"
          class="min-w-0 px-3 py-2"
          :style="[
            markerStyle(m, i),
            {
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              padding: 'var(--item-padding)',
              borderWidth: 'var(--item-border-width)',
              borderStyle: 'var(--item-border-style)',
              borderColor: 'var(--item-border)',
              borderLeftWidth: '3px',
              borderLeftColor: markerAccent(m, i),
            },
          ]"
        >
          <div class="flex items-center gap-2 min-w-0">
            <Icon
              :icon="m.icon || 'lucide:corner-down-right'"
              class="w-4 h-4 shrink-0"
              :style="{ color: markerAccent(m, i) }"
            />
            <span class="font-mono text-[11px] font-bold truncate" :style="{ color: markerAccent(m, i) }">
              {{ m.label }}
            </span>
          </div>
          <p v-if="m.description" class="text-[11px] leading-snug text-text-muted mt-1">
            {{ m.description }}
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* В MoralDecline серия одна и легенда SCurve не нужна — прячем строку легенды/индексов. */
.moral-decline :deep(.max-w-6xl > .mt-3) {
  display: none;
}
</style>
