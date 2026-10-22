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
  plans: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'PricingTable')
const relativeTime = inject('relativeTime', ref(0))

const planStyle = (plan, idx) => {
  const t = plan.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 26).toFixed(2)}px)` }
}

const accent = (plan) => getHexColor(plan.color || 'var(--color-secondary)')
</script>

<template>
  <div class="w-full mx-auto max-w-5xl" :style="{ ...itemVars }">
    <div v-if="title" class="mb-6 text-center">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="grid items-stretch"
      :class="[
        mobile ? 'grid-cols-2 gap-3' : 'gap-4 md:gap-6',
        !mobile && ((plans || []).length >= 3 ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2'),
      ]"
    >
      <div
        v-for="(plan, idx) in plans"
        :key="plan.id ?? idx"
        class="relative flex flex-col"
        :style="[
          planStyle(plan, idx),
          {
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: plan.highlighted ? 'var(--item-shadow)' : 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: plan.highlighted ? '2px' : 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: plan.highlighted ? accent(plan) : 'var(--item-border)',
          },
        ]"
      >
        <div class="min-h-[26px] mb-3">
          <span
            v-if="plan.badge"
            class="inline-block rounded-full font-bold uppercase tracking-wider text-[9px] px-2.5 py-1"
            :style="{ color: accent(plan), border: '1px solid ' + getColorAlpha(accent(plan), 0.3), background: getColorAlpha(accent(plan), 0.1) }"
          >
            {{ plan.badge }}
          </span>
        </div>

        <h4 class="font-heading font-bold text-text-primary" :class="mobile ? 'text-base' : 'text-lg'">{{ plan.name }}</h4>
        <p v-if="plan.description && !mobile" class="text-text-muted text-xs mt-1 min-h-[32px]">{{ plan.description }}</p>

        <div class="flex items-baseline gap-1 mt-3">
          <span class="font-black text-text-primary" :class="mobile ? 'text-2xl' : 'text-4xl'">{{ plan.price }}</span>
          <span v-if="plan.period" class="text-text-muted text-xs">{{ plan.period }}</span>
        </div>

        <div class="h-px w-full my-4" :style="{ background: 'var(--item-border)' }"></div>

        <ul class="flex-1 space-y-2.5">
          <li v-for="(f, fi) in (plan.features || []).slice(0, mobile ? 2 : 99)" :key="fi" class="flex items-start gap-2.5">
            <span class="w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5" :style="{ background: getColorAlpha(accent(plan), plan.highlighted ? 0.2 : 0.12) }">
              <Icon icon="heroicons:check" class="w-2.5 h-2.5" :style="{ color: accent(plan) }" />
            </span>
            <span class="text-text-primary text-[13px] leading-snug">{{ f }}</span>
          </li>
        </ul>

        <button
          v-if="plan.cta"
          class="w-full mt-5 py-3 text-sm font-bold"
          :style="[{ borderRadius: 'var(--item-radius)' }, plan.highlighted
            ? { background: plan.cta_color || accent(plan), color: 'var(--text-on-color)' }
            : { background: getColorAlpha('var(--text-primary)', 0.05), color: 'var(--text-primary)', border: '1px solid var(--item-border)' } ]"
        >
          {{ plan.cta }}
        </button>
      </div>
    </div>
  </div>
</template>
