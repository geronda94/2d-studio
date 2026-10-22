<script setup>
// ScienceFaithParallel — открытие ↔ Писание: две колонки со связью.
// Собственный макет (в реестре примитивов нет аналога «пара с линией связи»).
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  pairs: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ScienceFaithParallel')
const relativeTime = inject('relativeTime', ref(0))

const SCIENCE = 'var(--color-secondary)'
const SCRIPTURE = 'var(--color-accent)'

const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const sourceReveal = computed(() => {
  const t = (props.pairs?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})

const panelStyle = (token) => ({
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: getColorAlpha(token, 0.45),
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!pairs.length"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="flex-1 min-h-0 flex flex-col justify-start gap-1 pr-1" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
      <div
        v-for="(pair, i) in pairs"
        :key="i"
        class="flex-1 min-h-0 flex flex-col"
        :style="reveal(pair, i)"
      >
        <div class="grid items-stretch gap-1.5 md:gap-2 flex-1 min-h-0" :class="mobile ? 'grid-cols-1' : 'grid-cols-[1fr_2.5rem_1fr]'">
          <div class="flex flex-col gap-0.5 px-3 py-0.5 md:px-4 md:py-1 min-h-0 justify-center" :style="panelStyle(SCIENCE)">
            <span
              class="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest"
              :style="{ color: getHexColor(SCIENCE) }"
            >
              <Icon icon="lucide:microscope" class="w-3.5 h-3.5" /> Наука
            </span>
            <p class="text-sm md:text-base font-semibold text-text-primary leading-snug">{{ pair.science }}</p>
          </div>

          <div class="flex items-center justify-center">
            <span
              class="flex items-center justify-center rounded-full shrink-0"
              :class="mobile ? 'w-5 h-5' : 'w-7 h-7'"
              :style="{
                background: getColorAlpha('var(--color-primary)', 0.12),
                border: '1px solid ' + getColorAlpha('var(--color-primary)', 0.4),
                color: getHexColor('var(--color-primary)'),
              }"
            >
              <Icon :icon="mobile ? 'lucide:arrow-down' : 'lucide:arrow-right-left'" :class="mobile ? 'w-3 h-3' : 'w-3.5 h-3.5'" />
            </span>
          </div>

          <div class="flex flex-col gap-0.5 px-3 py-0.5 md:px-4 md:py-1 min-h-0 justify-center" :style="panelStyle(SCRIPTURE)">
            <span
              class="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest"
              :style="{ color: getHexColor(SCRIPTURE) }"
            >
              <Icon icon="lucide:book-open" class="w-3.5 h-3.5" /> Писание
            </span>
            <p class="text-sm md:text-base font-heading text-text-primary leading-snug">{{ pair.scripture }}</p>
          </div>
        </div>

        <p
          v-if="pair.note"
          class="mt-0.5 flex items-start gap-1.5 text-[10px] md:text-[11px] text-text-muted"
        >
          <Icon icon="lucide:link" class="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span class="min-w-0">{{ pair.note }}</span>
        </p>
      </div>

      <p
        v-if="source"
        class="shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceReveal"
      >{{ source }}</p>
    </div>
  </div>
</template>
