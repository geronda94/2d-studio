<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import NodeFlow from './NodeFlow.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  loop: { type: Array, default: () => [] },
  source: { type: String, default: '' },
  center_label: { type: String, default: 'Цикл' },
  center_icon: { type: String, default: 'lucide:rotate-cw' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'HabitLoop')
const relativeTime = inject('relativeTime', ref(0))

const nodes = computed(() => {
  const list = props.loop || []
  const n = Math.max(1, list.length)
  const r = props.mobile ? 15 : 32
  return list.map((it, i) => {
    const ang = (i / n) * Math.PI * 2 - Math.PI / 2 + Math.PI / n
    return {
      id: 'h' + i,
      label: it.stage,
      meta: it.spiritual,
      icon: it.icon || 'lucide:refresh-cw',
      status: it.status || (i % 2 ? 'info' : 'warn'),
      x: +(50 + Math.cos(ang) * r).toFixed(2),
      y: +(50 + Math.sin(ang) * r).toFixed(2),
      start_time: it.start_time ?? i * motion.value.stagger_ms,
    }
  })
})

const edges = computed(() => {
  const n = (props.loop || []).length
  return (props.loop || []).map((_, i) => ({ from: 'h' + i, to: 'h' + ((i + 1) % n) }))
})

const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const centerReveal = computed(() => {
  const p = clamp01((relativeTime.value - (motion.value.appear_ms || 500)) / (motion.value.appear_ms || 500))
  return (1 - Math.pow(1 - p, 3)).toFixed(3)
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!loop.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative flex-1 min-h-0 overflow-hidden [&_.min-h-\[260px\]]:min-h-[220px]" :class="mobile ? '[&_.max-w-\[240px\]]:max-w-[132px]' : ''">
        <NodeFlow
          class="h-full"
          :nodes="nodes"
          :edges="edges"
          :variant="variant"
          :mobile="mobile"
          :mobile_lo="18"
          :mobile_hi="82"
          :mobile_lo_y="6"
          :mobile_hi_y="94"
          flow_layout="coords"
          :source_note="source"
        />

        <div class="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 flex flex-col items-center gap-2">
          <div
            class="flex items-center justify-center"
            :class="mobile ? 'w-16 h-16' : 'w-44 h-44'"
            :style="{
              background: 'var(--item-primary-bg)',
              backdropFilter: 'var(--item-primary-backdrop)',
              WebkitBackdropFilter: 'var(--item-primary-backdrop)',
              borderRadius: '9999px',
              borderWidth: 'var(--item-primary-border-width)',
              borderStyle: 'var(--item-primary-border-style)',
              borderColor: getColorAlpha('var(--color-secondary)', 0.5),
              boxShadow: 'var(--item-primary-shadow)',
              opacity: centerReveal,
            }"
          >
            <Icon
              :icon="center_icon"
              :class="mobile ? 'w-8 h-8' : 'w-20 h-20'"
              :style="{ color: getHexColor('var(--color-secondary)') }"
            />
          </div>
          <span
            v-if="center_label"
            class="text-sm font-heading font-bold uppercase tracking-widest text-text-secondary"
            :style="{ opacity: centerReveal }"
          >{{ center_label }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
