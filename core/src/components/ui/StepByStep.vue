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
  layout: { type: String, default: 'vertical' },
  steps: { type: Array, default: () => [] },
  // Компактный вертикальный режим (опт-ин): плотнее шаг, чтобы длинный список
  // не переполнял кадр на мобильном. По умолчанию выключен — прочие слайды не затронуты.
  compact: { type: Boolean, default: false },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'StepByStep')
const relativeTime = inject('relativeTime', ref(0))

const vertical = computed(() => props.layout !== 'horizontal' || props.mobile)

const stepProgress = (s, idx) => {
  const t = s.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const stepStyle = (s, idx) => {
  const e = stepProgress(s, idx)
  return { opacity: e.toFixed(4), transform: vertical.value ? `translateX(${((1 - e) * -24).toFixed(2)}px)` : `translateY(${((1 - e) * 20).toFixed(2)}px)` }
}

const accent = (s, idx) => getHexColor(s.color || `var(--item-accent-${(idx % 4) + 1})`)

const lineScale = computed(() => {
  const n = (props.steps || []).length
  if (n <= 1) return 1
  let filled = 0
  props.steps.forEach((s, idx) => {
    if (idx < n - 1 && stepProgress(s, idx) >= 1) filled = idx + 1
    else if (stepProgress(s, idx) > 0 && filled < idx) filled = idx + stepProgress(s, idx)
  })
  return Math.min(1, Math.max(0, filled / (n - 1)))
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col justify-center" :style="{ ...itemVars }">
    <div v-if="title" class="mb-6 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <!-- VERTICAL -->
    <div v-if="vertical" class="relative pl-2">
      <div class="absolute left-[27px] top-4 bottom-4 w-[2px]" :style="{ background: 'var(--item-border)' }"></div>
      <div class="absolute left-[27px] top-4 bottom-4 w-[2px] origin-top" :style="{ background: getHexColor('var(--color-secondary)'), transform: `scaleY(${lineScale})`, height: 'calc(100% - 32px)' }"></div>

      <div v-for="(s, idx) in steps" :key="s.id ?? idx" class="relative flex" :class="compact ? 'gap-3 pb-3 last:pb-0' : 'gap-4 pb-6 last:pb-0'" :style="stepStyle(s, idx)">
        <div class="relative z-10 rounded-full flex items-center justify-center shrink-0 font-heading font-bold" :class="compact ? 'w-10 h-10' : 'w-12 h-12'" :style="{ background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', border: '2px solid ' + accent(s, idx), color: accent(s, idx) }">
          <Icon v-if="s.icon" :icon="s.icon" :class="compact ? 'w-4 h-4' : 'w-5 h-5'" />
          <span v-else>{{ s.number ?? idx + 1 }}</span>
        </div>
        <div
          class="flex-1 min-w-0"
          :class="compact ? 'pt-2 pb-2 px-3' : 'pt-2.5 pb-3 px-4'"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          }"
        >
          <h4 class="font-heading font-bold text-text-primary" :class="compact ? 'text-sm' : 'text-base'">{{ s.title }}</h4>
          <p v-if="s.description" class="text-text-secondary leading-relaxed" :class="compact ? 'text-xs mt-0.5' : 'text-sm mt-1'">{{ s.description }}</p>
        </div>
      </div>
    </div>

    <!-- HORIZONTAL -->
    <div v-else class="relative">
      <div class="absolute top-12 left-[10%] right-[10%] h-[2px]" :style="{ background: 'var(--item-border)' }"></div>
      <div class="absolute top-12 left-[10%] right-[10%] h-[2px] origin-left" :style="{ background: getHexColor('var(--color-secondary)'), transform: `scaleX(${lineScale})` }"></div>
      <div class="grid" :style="{ gridTemplateColumns: `repeat(${(steps || []).length || 1}, minmax(0, 1fr))` }">
        <div v-for="(s, idx) in steps" :key="s.id ?? idx" class="flex flex-col items-center text-center px-3" :style="stepStyle(s, idx)">
          <div class="w-24 h-24 rounded-full flex items-center justify-center z-10 font-heading font-bold mb-6" :style="{ background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', border: '2px solid ' + accent(s, idx), color: accent(s, idx) }">
            <Icon v-if="s.icon" :icon="s.icon" class="w-11 h-11" />
            <span v-else>{{ s.number ?? idx + 1 }}</span>
          </div>
          <h4 class="font-heading font-bold text-text-primary text-xl md:text-2xl leading-tight">{{ s.title }}</h4>
          <p v-if="s.description" class="text-text-muted text-sm md:text-base mt-2 leading-snug min-h-[2.5rem]">{{ s.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
