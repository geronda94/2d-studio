<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  quote: { type: String, default: '' },
  author: { type: String, default: '' },
  author_title: { type: String, default: '' },
  photo: { type: String, default: '' },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'QuoteCard')
const relativeTime = inject('relativeTime', ref(0))

const reveal = (t, dur) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (t ?? 0)) / dur))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 20).toFixed(2)}px)` }
}

const initials = (name) => String(name || '').trim().split(/\s+/).slice(0, 2).map((p) => p[0] || '').join('').toUpperCase() || '?'
const accent = getHexColor('var(--color-secondary)')
</script>

<template>
  <div class="w-full max-w-4xl mx-auto" :style="{ ...itemVars }">
    <div
      class="relative overflow-hidden"
      :style="[
        reveal(0, motion.appear_ms),
        {
          background: 'var(--item-bg)',
          backdropFilter: 'var(--item-backdrop)',
          borderRadius: 'var(--item-radius)',
          boxShadow: 'var(--item-shadow)',
          padding: 'var(--item-padding)',
          padding: 'var(--item-padding)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-border)',
        },
      ]"
    >
      <Icon
        icon="heroicons:chat-bubble-bottom-center-text"
        class="absolute -top-2 -left-1 w-24 h-24 opacity-[0.06] pointer-events-none"
        :style="{ color: accent }"
      />

      <div class="relative flex flex-col items-center text-center py-4">
        <div class="text-6xl font-heading leading-none mb-2" :style="{ color: accent }">&ldquo;</div>
        <p class="font-heading text-xl md:text-3xl text-text-primary leading-snug italic max-w-3xl">{{ quote }}</p>

        <div class="flex items-center gap-3 mt-7" :style="reveal(600, motion.appear_ms)">
          <div class="w-14 h-14 rounded-full overflow-hidden flex items-center justify-center shrink-0" :style="{ border: '2px solid ' + accent, background: 'var(--item-primary-bg)' }">
            <img v-if="photo" :src="photo" class="w-full h-full object-cover" />
            <span v-else class="font-heading font-bold" :style="{ color: accent }">{{ initials(author) }}</span>
          </div>
          <div class="text-left">
            <p class="font-heading font-bold text-text-primary text-base">{{ author }}</p>
            <p v-if="author_title" class="text-xs font-mono uppercase tracking-wider" :style="{ color: accent }">{{ author_title }}</p>
          </div>
        </div>

        <p v-if="source" class="text-text-muted text-xs mt-4 font-mono" :style="reveal(1000, motion.appear_ms)">— {{ source }}</p>
      </div>
    </div>
  </div>
</template>
