<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import RadarProfile from './RadarProfile.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  axes: { type: Array, default: () => [] },
  schools: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'TheologicalSchools')
const relativeTime = inject('relativeTime', ref(0))

const PALETTE = [
  'var(--color-secondary)',
  'var(--color-success)',
  'var(--color-warning)',
  'var(--color-accent)',
]

const series = computed(() =>
  (props.schools || []).map((s, i) => ({
    label: s.name,
    values: s.values || [],
    color: s.color || PALETTE[i % PALETTE.length],
  })),
)

const color = (i) => getHexColor(series.value[i]?.color || 'var(--color-secondary)')

const reveal = (t, y = 12) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const hasData = computed(() => (props.axes || []).length > 0 && (props.schools || []).length > 0)
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-2"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!hasData"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex flex-col md:flex-row gap-3 md:gap-4">
        <div class="flex-1 min-h-0 overflow-hidden">
          <RadarProfile
            class="h-full"
            :mobile="mobile"
            :variant="variant"
            :axes="axes"
            :series="series"
            :max="100"
            :fill_opacity="0.05"
            :radius="45"
            :source_note="source_note"
          />
        </div>

        <div class="flex flex-col gap-2 md:w-[42%] md:shrink-0 min-h-0 overflow-hidden">
          <div
            v-for="(s, i) in schools"
            :key="s.name + i"
            class="px-3 py-2 md:flex-1 md:min-h-0 flex flex-col justify-center"
            :style="[itemStyle, reveal(s.start_time ?? i * motion.stagger_ms)]"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="w-2 h-2 rounded-full shrink-0" :style="{ background: color(i) }"></span>
              <span class="text-text-primary text-xs md:text-sm font-bold truncate">{{ s.name }}</span>
            </div>
            <p class="text-text-secondary text-[11px] leading-snug">{{ s.emphasis }}</p>
            <p v-if="(s.representatives || []).length" class="text-text-muted text-[10px] font-mono mt-1 leading-snug">
              {{ (s.representatives || []).join(' · ') }}
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
