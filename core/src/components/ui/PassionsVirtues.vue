<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  pairs: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'PassionsVirtues')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`
const pct = (p) => Math.round(Math.max(1, Math.min(100, Number(p.level) || 1)))

const progress = (i) => {
  const t = props.pairs[i]?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / (motion.value.appear_ms || 500)))
  return 1 - Math.pow(1 - p, 3)
}

const rowStyle = (i) => {
  const e = progress(i)
  return { opacity: e.toFixed(4), transform: `translateX(${((1 - e) * -14).toFixed(2)}px)` }
}
const fillStyle = (i) => {
  const e = progress(i)
  const color = accent(i)
  return {
    transform: `scaleX(${((pct(props.pairs[i]) / 100) * e).toFixed(4)})`,
    background: `linear-gradient(to right, ${getColorAlpha(color, 0.35)}, ${color})`,
  }
}
const sourceReveal = computed(() => progress(Math.max(0, (props.pairs?.length || 1) - 1)))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!pairs.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative flex-1 min-h-0 flex flex-col justify-center gap-3 md:gap-4">
        <div v-for="(p, i) in pairs" :key="i" class="w-full" :style="rowStyle(i)">
          <div class="flex justify-between items-center mb-1.5 gap-3">
            <div class="flex items-center gap-2 min-w-0">
              <Icon :icon="p.icon || 'lucide:scale'" class="w-4 h-4 shrink-0" :style="{ color: accent(i) }" />
              <span class="text-text-primary font-bold text-[13px] md:text-sm tracking-wide truncate">
                {{ [p.passion, p.virtue].filter(Boolean).join(' → ') }}
              </span>
            </div>
            <span class="text-text-primary font-black text-[13px] md:text-sm shrink-0">{{ pct(p) }}%</span>
          </div>
          <div
            class="w-full h-3 md:h-3.5 rounded-full overflow-hidden border"
            :style="{ borderColor: 'var(--item-border)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }"
          >
            <div class="h-full w-full rounded-full origin-left" :style="fillStyle(i)"></div>
          </div>
        </div>
      </div>

      <div
        v-if="source"
        class="mt-2 shrink-0 text-right text-[11px] font-mono text-text-secondary"
        :style="{ opacity: sourceReveal }"
      >{{ source }}</div>
    </template>
  </div>
</template>
