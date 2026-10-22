<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  question: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  explanation: { type: String, default: '' },
  reveal_time: { type: Number, default: 4000 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'QuizSlide')
const relativeTime = inject('relativeTime', ref(0))

const revealed = computed(() => relativeTime.value >= props.reveal_time)

const optionProgress = (opt, idx) => {
  const t = opt.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const optionStyle = (opt, idx) => {
  const e = optionProgress(opt, idx)
  const isCorrect = !!opt.correct
  const dim = revealed.value && !isCorrect
  return {
    opacity: (dim ? e * 0.45 : e).toFixed(4),
    transform: `translateX(${((1 - e) * 24).toFixed(2)}px)`,
    borderColor: revealed.value && isCorrect
      ? 'var(--color-success)'
      : revealed.value && !isCorrect
        ? 'var(--item-border)'
        : 'var(--item-border)',
    background: revealed.value && isCorrect
      ? getColorAlpha('var(--color-success)', 0.15)
      : 'var(--item-bg)',
  }
}

const letters = ['A', 'B', 'C', 'D', 'E', 'F']

const explanationStyle = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - props.reveal_time) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 16).toFixed(2)}px)` }
})
</script>

<template>
  <div class="w-full max-w-3xl mx-auto flex flex-col" :style="{ ...itemVars }">
    <div
      class="flex items-start gap-4"
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
      <span class="w-10 h-10 rounded-full flex items-center justify-center shrink-0" :style="{ background: getColorAlpha('var(--color-secondary)', 0.15), color: getHexColor('var(--color-secondary)') }">
        <Icon icon="heroicons:question-mark-circle" class="w-5 h-5" />
      </span>
      <h3 class="font-heading font-bold text-text-primary text-xl md:text-2xl leading-snug">{{ question }}</h3>
    </div>

    <div class="grid gap-2 mt-3" :class="mobile ? 'grid-cols-1' : 'grid-cols-1'">
      <div
        v-for="(opt, idx) in options"
        :key="opt.id ?? idx"
        class="flex items-center gap-3 px-4 py-2.5"
        :style="[
          optionStyle(opt, idx),
          {
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: '1.5px',
            borderStyle: 'solid',
          },
        ]"
      >
        <span
          class="w-7 h-7 flex items-center justify-center shrink-0 font-mono font-bold text-xs"
          :style="{
            background: revealed && opt.correct ? 'var(--color-success)' : getColorAlpha('var(--text-primary)', 0.06),
            color: revealed && opt.correct ? 'var(--text-on-color)' : 'var(--text-secondary)',
            borderRadius: 'calc(var(--item-radius) - 4px)',
          }"
        >{{ letters[idx] || idx + 1 }}</span>
        <span class="text-text-primary text-sm md:text-base flex-1">{{ opt.text }}</span>
        <Icon v-if="revealed && opt.correct" icon="heroicons:check-circle" class="w-5 h-5 shrink-0" :style="{ color: getHexColor('var(--color-success)') }" />
      </div>
    </div>

    <div
      v-if="explanation"
      class="mt-3 px-4 py-2.5 text-sm text-text-secondary"
      :style="[
        explanationStyle,
        {
          background: getColorAlpha('var(--color-secondary)', 0.08),
          borderLeft: '3px solid ' + getHexColor('var(--color-secondary)'),
          borderRadius: 'var(--item-radius)',
        },
      ]"
    >
      {{ explanation }}
    </div>
  </div>
</template>
