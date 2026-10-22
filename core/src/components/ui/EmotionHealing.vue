<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  emotions: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'EmotionHealing')
const relativeTime = inject('relativeTime', ref(0))

const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const e = ease(clamp01((relativeTime.value - t) / (motion.value.appear_ms || 500)))
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const baseCard = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  // плотная сетка «эмоция→причина→исцеление»: компактные отступы карточек
  padding: 'calc(var(--item-padding) * 0.35) var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
}

const emotionStyle = (i) => ({ ...baseCard, borderColor: getColorAlpha(accent(i), 0.5) })
const causeStyle = { ...baseCard, borderColor: 'var(--item-border)' }
const remedyStyle = { ...baseCard, borderColor: getColorAlpha('var(--color-success)', 0.5) }
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!emotions.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative flex-1 min-h-0 flex flex-col justify-center gap-1.5 md:gap-2">
        <div
          v-for="(e, i) in emotions"
          :key="e.name + i"
          class="flex items-stretch"
          :class="mobile ? 'flex-col gap-0' : 'flex-row gap-2'"
          :style="reveal(e, i)"
        >
          <div class="flex-1 min-w-0 flex items-center gap-2" :style="emotionStyle(i)">
            <Icon :icon="e.icon || 'lucide:cloud-rain'" class="w-4 h-4 shrink-0" :style="{ color: getHexColor(accent(i)) }" />
            <span class="font-heading font-bold text-text-primary text-sm truncate">{{ e.name }}</span>
          </div>

          <Icon v-if="!mobile" icon="lucide:arrow-right" class="self-center w-4 h-4 shrink-0 text-text-muted" />

          <div class="flex-1 min-w-0 flex items-start gap-2" :style="causeStyle">
            <Icon icon="lucide:search" class="w-4 h-4 mt-0.5 shrink-0 text-text-muted" />
            <span class="text-[11px] leading-snug text-text-secondary">{{ e.cause }}</span>
          </div>

          <Icon v-if="!mobile" icon="lucide:arrow-right" class="self-center w-4 h-4 shrink-0 text-text-muted" />

          <div class="flex-1 min-w-0 flex items-start gap-2" :style="remedyStyle">
            <Icon icon="lucide:sprout" class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: getHexColor('var(--color-success)') }" />
            <span class="text-[11px] leading-snug text-text-secondary">{{ e.remedy }}</span>
          </div>
        </div>
      </div>

      <div v-if="source" class="mt-2 shrink-0 text-right text-[11px] font-mono text-text-muted">{{ source }}</div>
    </template>
  </div>
</template>
