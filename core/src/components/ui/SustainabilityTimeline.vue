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
  milestones: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'SustainabilityTimeline')
const relativeTime = inject('relativeTime', ref(0))

const itemProgress = (m, idx) => {
  const t = m.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const itemStyle = (m, idx) => {
  const e = itemProgress(m, idx)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 20).toFixed(2)}px)` }
}

const accent = (m, idx) => getHexColor(m.color || `var(--item-accent-${(idx % 4) + 1})`)
</script>

<template>
  <div class="w-full max-w-3xl mx-auto" :style="{ ...itemVars }">
    <div v-if="title" class="mb-6 text-center">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div class="relative pl-16">
      <div class="absolute left-[35px] top-3 bottom-3 w-[2px]" :style="{ background: 'var(--item-border)' }"></div>

      <div v-for="(m, idx) in milestones" :key="m.id ?? idx" class="relative pb-6 last:pb-0" :style="itemStyle(m, idx)">
        <!-- Связка ведёт от центра этой ноды к центру следующей и окрашена
             в цвет текущей ноды (прошлый баг: линия всегда была success-зелёной). -->
        <div
          v-if="idx < milestones.length - 1"
          class="absolute left-[35px] w-[2px] origin-top z-0"
          :style="{ top: '34px', bottom: '-34px', background: accent(m, idx), opacity: itemProgress(m, idx).toFixed(3), transform: `scaleY(${Math.max(0, Math.min(1, itemProgress(m, idx))).toFixed(3)})` }"
        ></div>
        <div class="absolute -left-16 top-3 w-16 flex justify-center">
          <div class="w-11 h-11 rounded-full flex items-center justify-center z-10" :style="{ background: 'var(--item-bg)', border: '2px solid ' + accent(m, idx) }">
            <Icon :icon="m.icon || 'heroicons:leaf'" class="w-5 h-5" :style="{ color: accent(m, idx) }" />
          </div>
        </div>
        <div
          class="ml-2 flex flex-col md:flex-row md:items-center gap-2 md:gap-4 px-4 py-3"
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
          <span class="font-mono font-bold text-sm shrink-0" :style="{ color: accent(m, idx) }">{{ m.year }}</span>
          <div class="flex-1 min-w-0">
            <h4 class="font-heading font-bold text-text-primary text-base leading-tight">{{ m.event }}</h4>
            <p v-if="m.impact" class="text-text-secondary text-sm mt-0.5">{{ m.impact }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
