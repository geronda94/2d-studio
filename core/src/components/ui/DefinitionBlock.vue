<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  term: { type: String, default: '' },
  definition: { type: String, default: '' },
  examples: { type: Array, default: () => [] },
  related_terms: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'DefinitionBlock')
const relativeTime = inject('relativeTime', ref(0))

const reveal = (t, dur) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (t ?? 0)) / dur))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 18).toFixed(2)}px)` }
}

const accent = getHexColor('var(--color-secondary)')
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col justify-center gap-4" :style="{ ...itemVars }">
    <div
      class="relative overflow-hidden w-full max-w-4xl mx-auto flex-1 min-h-0 flex flex-col justify-center"
      :style="[
        reveal(0, motion.appear_ms),
        {
          background: 'var(--item-bg)',
          backdropFilter: 'var(--item-backdrop)',
          WebkitBackdropFilter: 'var(--item-backdrop)',
          borderRadius: 'var(--item-radius)',
          boxShadow: 'var(--item-shadow)',
          padding: 'var(--item-padding)',
          padding: 'calc(var(--item-padding) * 2)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-border)',
        },
      ]"
    >
      <div class="absolute left-0 top-0 bottom-0 w-2" :style="{ background: accent }"></div>
      <div :class="mobile ? 'pl-5' : 'pl-8'">
        <div class="flex items-center gap-2 mb-3">
          <Icon icon="heroicons:book-open" class="w-5 h-5" :style="{ color: accent }" />
          <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Определение</span>
        </div>
        <h3 class="font-heading font-bold leading-tight text-text-primary" :class="mobile ? 'text-3xl' : 'text-5xl'">{{ term }}</h3>
        <p class="text-text-secondary mt-4 leading-relaxed max-w-3xl" :class="mobile ? 'text-base' : 'text-xl'">{{ definition }}</p>
      </div>
    </div>

    <div v-if="(examples || []).length" class="w-full max-w-4xl mx-auto shrink-0">
      <p class="text-[11px] font-mono uppercase tracking-widest text-text-muted mb-2">Примеры</p>
      <div class="grid gap-2.5" :class="mobile ? 'grid-cols-1' : 'grid-cols-2'">
        <div
          v-for="(ex, idx) in examples"
          :key="ex.id ?? idx"
          class="flex items-start gap-3 px-4 py-3.5"
          :style="[
            reveal(ex.start_time ?? (idx + 1) * motion.stagger_ms, motion.appear_ms),
            {
              background: 'var(--item-primary-bg)',
              backdropFilter: 'var(--item-primary-backdrop)',
              WebkitBackdropFilter: 'var(--item-primary-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              padding: 'var(--item-padding)',
              borderWidth: 'var(--item-border-width)',
              borderStyle: 'var(--item-border-style)',
              borderColor: 'var(--item-border)',
            },
          ]"
        >
          <span class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5" :style="{ background: getColorAlpha(accent, 0.15) }">
            <Icon icon="heroicons:arrow-small-right" class="w-4 h-4" :style="{ color: accent }" />
          </span>
          <span class="text-text-primary text-base leading-relaxed">{{ ex.text }}</span>
        </div>
      </div>
    </div>

    <div v-if="(related_terms || []).length" class="shrink-0 flex flex-wrap gap-2 justify-center">
      <span
        v-for="(rt, idx) in related_terms"
        :key="idx"
        class="px-4 py-2 rounded-full text-sm font-mono"
        :style="[
          reveal((examples.length + 1) * motion.stagger_ms + idx * 300, motion.appear_ms),
          { background: getColorAlpha(accent, 0.1), color: accent, border: '1px solid ' + getColorAlpha(accent, 0.3) },
        ]"
      >
        #{{ rt }}
      </span>
    </div>
  </div>
</template>
