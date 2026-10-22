<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  cards: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'FlashCards')
const relativeTime = inject('relativeTime', ref(0))

// Детерминированный кроссфейд вопрос → ответ (без 3D preserve-3d/backface —
// они теряют фон карточки в софтверном рендере).
const flipProgress = (card, idx) => {
  const t = card.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / 500))
  return p
}

const cardProgress = (card, idx) => {
  const t = card.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const cardStyle = (card, idx) => {
  const e = cardProgress(card, idx)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 22).toFixed(2)}px)` }
}

const frontStyle = (card, idx) => ({ opacity: (1 - flipProgress(card, idx)).toFixed(3) })
const backStyle = (card, idx) => ({ opacity: flipProgress(card, idx).toFixed(3) })

const accent = (card) => getHexColor(card.color || 'var(--color-secondary)')

const colsClass = computed(() => {
  const n = (props.cards || []).length
  if (n <= 1) return 'grid-cols-1 max-w-md'
  if (n === 2) return 'grid-cols-1 md:grid-cols-2 max-w-3xl'
  return 'grid-cols-1 md:grid-cols-3 max-w-5xl'
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="title" class="mb-6 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div class="grid gap-4 md:gap-5 mx-auto w-full flex-1 min-h-0" :class="colsClass" style="grid-auto-rows: minmax(0, 1fr)">
      <div
        v-for="(card, idx) in cards"
        :key="card.id ?? idx"
        class="relative overflow-hidden h-full min-h-[150px]"
        :style="[
          cardStyle(card, idx),
          {
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
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
        <!-- FRONT: вопрос -->
        <div class="absolute inset-0 flex flex-col items-center justify-center text-center px-5" :style="frontStyle(card, idx)">
          <span
            v-if="card.icon"
            class="w-14 h-14 rounded-full flex items-center justify-center mb-4"
            :style="{ background: getColorAlpha(accent(card), 0.15), color: accent(card) }"
          >
            <Icon :icon="card.icon" class="w-7 h-7" />
          </span>
          <p class="font-heading font-bold text-text-primary text-xl md:text-2xl leading-tight">{{ card.front }}</p>
          <span class="absolute bottom-3 right-4 text-[10px] font-mono uppercase tracking-widest text-text-secondary">Вопрос</span>
        </div>

        <!-- BACK: ответ -->
        <div
          class="absolute inset-0 flex flex-col items-center justify-center text-center px-5"
          :style="[
            backStyle(card, idx),
            {
              background: 'var(--item-primary-bg)',
              backdropFilter: 'var(--item-primary-backdrop)',
              WebkitBackdropFilter: 'var(--item-primary-backdrop)',
              borderRadius: 'var(--item-radius)',
            },
          ]"
        >
          <p v-if="card.front" class="absolute top-3 left-0 right-0 px-5 text-[11px] font-mono uppercase tracking-wider text-text-secondary line-clamp-1">{{ card.front }}</p>
          <Icon icon="heroicons:sparkles" class="w-6 h-6 mb-3" :style="{ color: accent(card) }" />
          <p class="text-text-primary text-lg md:text-xl leading-snug">{{ card.back }}</p>
          <span class="absolute bottom-3 right-4 text-[10px] font-mono uppercase tracking-widest text-text-secondary">Ответ</span>
        </div>
      </div>
    </div>
  </div>
</template>
