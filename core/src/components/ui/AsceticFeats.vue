<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  feats: { type: Array, default: () => [] },
  max_level: { type: Number, default: 5 },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'AsceticFeats')
const relativeTime = inject('relativeTime', ref(0))

const accent = (f, i) => getHexColor(f.color || `var(--item-accent-${(i % 4) + 1})`)

const progress = (f, i) => {
  const t = f.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const reveal = (f, i) => {
  const e = progress(f, i)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}

const levelPct = (f) => {
  const lv = Number(f.level) || 0
  return Math.max(0, Math.min(1, lv / (props.max_level || 1)))
}

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const noteStyle = computed(() => {
  const t = props.feats.length * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4) }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div class="flex-1 min-h-0 overflow-hidden flex flex-col justify-center" :style="{ gap: 'var(--item-gap)' }">
      <div
        v-for="(f, i) in feats"
        :key="f.name || i"
        class="flex items-center gap-3 md:gap-4"
        :style="[itemStyle, reveal(f, i)]"
      >
        <span
          class="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center shrink-0"
          :style="{ background: getColorAlpha(accent(f, i), 0.14), border: '1px solid ' + accent(f, i) }"
        >
          <Icon :icon="f.icon || 'lucide:flame'" class="w-5 h-5 md:w-6 md:h-6" :style="{ color: accent(f, i) }" />
        </span>

        <div class="flex-1 min-w-0">
          <div class="flex items-baseline gap-2 flex-wrap">
            <p class="font-heading font-bold text-text-primary leading-tight" :class="mobile ? 'text-sm' : 'text-base'">
              {{ f.name }}
            </p>
            <span v-if="f.note" class="text-[11px] md:text-xs text-text-secondary truncate">{{ f.note }}</span>
          </div>
          <div
            class="mt-2 h-2 rounded-full overflow-hidden"
            :style="{ background: getColorAlpha('var(--text-muted)', 0.18) }"
          >
            <div
              class="h-full rounded-full origin-left"
              :style="{
                background: accent(f, i),
                transform: `scaleX(${(progress(f, i) * levelPct(f)).toFixed(4)})`,
              }"
            ></div>
          </div>
        </div>

        <span class="shrink-0 font-mono text-xs md:text-sm" :style="{ color: accent(f, i) }">
          {{ f.level }}/{{ max_level }}
        </span>
      </div>
    </div>

    <p
      v-if="source_note"
      class="mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
      :style="noteStyle"
    >{{ source_note }}</p>
  </div>
</template>
