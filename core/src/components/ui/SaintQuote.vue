<script setup>
import { computed, inject, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  quote: { type: String, default: '' },
  author: { type: String, default: '' },
  author_title: { type: String, default: '' },
  image: { type: String, default: '' },
  source: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'SaintQuote')
const relativeTime = inject('relativeTime', ref(0))

// Битый URL портрета → фолбэк на инициалы (без «сломанной» картинки).
const imageBroken = ref(false)
watch(() => props.image, () => { imageBroken.value = false })

const accent = getHexColor('var(--color-secondary)')

const initials = (name) =>
  String(name || '')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0] || '')
    .join('')
    .toUpperCase() || '?'

const reveal = (t, y = 16) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (t ?? 0)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      class="flex-1 min-h-0 overflow-hidden flex items-center justify-center"
      :style="reveal(0, 12)"
    >
      <div class="w-full max-w-4xl mx-auto">
        <div
          class="relative overflow-hidden"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          }"
        >
          <Icon
            icon="heroicons:chat-bubble-bottom-center-text"
            class="absolute -top-2 -left-1 w-24 h-24 opacity-[0.06] pointer-events-none"
            :style="{ color: accent }"
          />

          <div class="relative flex flex-col items-center text-center py-2">
            <div class="font-heading leading-none mb-1" :style="{ color: accent, fontSize: mobile ? '2.5rem' : '3.5rem' }">&ldquo;</div>
            <p
              class="font-heading text-text-primary leading-snug italic max-w-3xl"
              :style="{ fontSize: mobile ? '1.35rem' : 'clamp(1.75rem, 3vw, 2.75rem)' }"
            >{{ quote }}</p>

            <div class="flex items-center gap-3 mt-6" :style="reveal(motion.appear_ms, 10)">
              <div
                class="w-14 h-14 rounded-full overflow-hidden flex items-center justify-center shrink-0"
                :style="{ border: '2px solid ' + accent, background: 'var(--item-primary-bg)' }"
              >
                <img v-if="image && !imageBroken" :src="image" class="w-full h-full object-cover" @error="imageBroken = true" />
                <span v-else class="font-heading font-bold text-lg" :style="{ color: accent }">{{ initials(author) }}</span>
              </div>
              <div class="text-left">
                <p class="font-heading font-bold text-text-primary text-base">{{ author }}</p>
                <p v-if="author_title" class="text-xs font-mono uppercase tracking-wider" :style="{ color: accent }">{{ author_title }}</p>
              </div>
            </div>

            <p v-if="source" class="text-text-muted text-xs mt-3 font-mono" :style="reveal(motion.appear_ms * 2, 8)">— {{ source }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
