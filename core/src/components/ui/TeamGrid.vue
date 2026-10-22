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
  members: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'TeamGrid')
const relativeTime = inject('relativeTime', ref(0))

const memberStyle = (m, idx) => {
  const t = m.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 24).toFixed(2)}px)` }
}

const initials = (name) => {
  const parts = String(name || '').trim().split(/\s+/).slice(0, 2)
  return parts.map((p) => p[0] || '').join('').toUpperCase() || '?'
}

const colsClass = computed(() => {
  const n = (props.members || []).length
  if (n <= 1) return 'grid-cols-1 max-w-sm'
  if (n === 2) return 'grid-cols-1 md:grid-cols-2 max-w-2xl'
  if (n === 3) return 'grid-cols-1 md:grid-cols-3 max-w-4xl'
  return 'grid-cols-2 lg:grid-cols-4 max-w-6xl'
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="title" class="shrink-0 mb-4 md:mb-6 text-center">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div class="flex-1 min-h-0 w-full grid gap-3 md:gap-5 content-center mx-auto" :class="colsClass">
      <div
        v-for="(m, idx) in members"
        :key="m.id ?? idx"
        class="flex flex-col items-center justify-center text-center md:min-h-[360px]"
        :style="[
          memberStyle(m, idx),
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
        <div
          class="w-20 h-20 md:w-32 md:h-32 rounded-full overflow-hidden flex items-center justify-center shrink-0 mb-3 md:mb-4"
          :style="{ border: '2px solid ' + getColorAlpha(getHexColor(m.color || 'var(--color-secondary)'), 0.5), background: getColorAlpha(getHexColor(m.color || 'var(--color-secondary)'), 0.15) }"
        >
          <img v-if="m.photo" :src="m.photo" class="w-full h-full object-cover" />
          <span v-else class="font-heading font-bold text-2xl md:text-4xl" :style="{ color: getHexColor(m.color || 'var(--color-secondary)') }">{{ initials(m.name) }}</span>
        </div>

        <h4 class="font-heading font-bold text-text-primary text-lg md:text-xl leading-tight">{{ m.name }}</h4>
        <p class="text-xs md:text-sm font-mono uppercase tracking-wider mt-1.5" :style="{ color: getHexColor(m.color || 'var(--color-secondary)') }">{{ m.title }}</p>

        <div v-if="(m.contacts || []).length" class="mt-4 flex flex-col gap-1.5 w-full">
          <div v-for="(c, ci) in m.contacts" :key="ci" class="flex items-center justify-center gap-2 text-text-secondary text-xs md:text-sm">
            <Icon v-if="c.icon" :icon="c.icon" class="w-4 h-4 shrink-0" />
            <span class="truncate">{{ c.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
