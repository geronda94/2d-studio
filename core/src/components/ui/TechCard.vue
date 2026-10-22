<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps<{
  name: string
  icon?: string
  desc?: string
  color?: string
  delay?: number
  start_time?: number
  compact?: boolean
  variant?: string
}>()

const { itemVars } = useVariant(computed(() => props.variant), 'TechCard')

const relativeTime = inject('relativeTime', ref(0))
const customColor = computed(() => props.color || 'var(--color-secondary)')

const progress = computed(() => {
  const t = props.start_time ?? props.delay ?? 0
  return Math.min(1, Math.max(0, (relativeTime.value - t) / 700))
})
</script>

<template>
  <div
    class="relative flex w-full group overflow-hidden"
    :class="compact ? 'flex-row items-center gap-3 flex-1' : 'flex-col items-center justify-center text-center h-full gap-7'"
    :style="{
      ...itemVars,
      background: 'var(--item-bg)',
      backdropFilter: 'var(--item-backdrop)',
      borderRadius: 'var(--item-radius)',
      boxShadow: 'var(--item-shadow)',
      padding: 'var(--item-padding)',
      padding: compact ? '1rem' : '1.5rem',
      borderWidth: 'var(--item-border-width)',
      borderStyle: 'var(--item-border-style)',
      borderColor: 'var(--item-border)',
      opacity: progress,
      transform: `translateY(${32 - progress * 32}px) scale(${0.95 + progress * 0.05})`,
    }"
  >
    <div
      class="flex items-center justify-center shrink-0"
      :class="compact ? 'w-8 h-8 sm:w-10 sm:h-10' : 'w-32 h-32 md:w-44 md:h-44'"
    >
      <Icon v-if="icon" :icon="icon" class="w-full h-full" :style="{ color: customColor }" />
      <span v-else class="w-full h-full rounded-full" :style="{ backgroundColor: customColor }"></span>
    </div>

    <div class="flex flex-col min-w-0" :class="compact ? 'flex-1 items-start text-left' : 'items-center'">
      <h3
        class="font-bold tracking-tight leading-tight text-text-primary"
        :class="compact ? 'text-sm sm:text-base text-left' : 'text-2xl md:text-3xl'"
      >
        {{ name }}
      </h3>
      <p
        v-if="desc"
        class="text-text-secondary leading-relaxed mt-2"
        :class="compact ? 'text-xs sm:text-sm text-left' : 'text-base md:text-lg'"
      >
        {{ desc }}
      </p>
    </div>
  </div>
</template>
