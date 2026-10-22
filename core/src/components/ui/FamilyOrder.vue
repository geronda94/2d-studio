<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  roles: { type: Array, default: () => [] },
  foundation: { type: Object, default: () => null },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'FamilyOrder')
const relativeTime = inject('relativeTime', ref(0))

const accent = (r, i) => getHexColor(r.color || `var(--item-accent-${(i % 4) + 1})`)

const reveal = (item, i) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 18).toFixed(2)}px)` }
}

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div class="flex-1 min-h-0 overflow-hidden">
      <div
        class="h-full min-h-0 gap-3"
        :class="mobile ? 'flex flex-col' : 'grid'"
        :style="!mobile ? { gridTemplateColumns: `repeat(${Math.max(roles.length, 1)}, minmax(0, 1fr))` } : {}"
      >
        <div
          v-for="(r, i) in roles"
          :key="r.member || i"
          class="relative flex flex-col min-h-0 overflow-hidden"
          :class="mobile ? 'flex-1' : ''"
          :style="[itemStyle, reveal(r, i)]"
        >
          <span class="absolute left-0 top-3 bottom-3 w-[3px] rounded-full" :style="{ background: accent(r, i) }"></span>
          <div class="pl-3 flex flex-col h-full min-h-0">
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                :style="{
                  background: getColorAlpha(accent(r, i), 0.16),
                  color: accent(r, i),
                  border: '1px solid ' + getColorAlpha(accent(r, i), 0.35),
                }"
              >
                <Icon :icon="r.icon || 'lucide:user-round'" class="w-4 h-4" />
              </span>
              <span class="font-heading font-bold text-text-primary text-base md:text-lg leading-tight">{{ r.member }}</span>
            </div>

            <p class="mt-3 text-text-secondary leading-relaxed" :class="mobile ? 'text-xs' : 'text-sm'">{{ r.duty }}</p>

            <div class="mt-auto pt-3" :style="{ borderTop: '1px solid var(--item-border)' }">
              <span class="font-mono uppercase tracking-wider text-[10px] text-text-muted">{{ r.scripture }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="foundation"
      class="shrink-0 mt-3 relative overflow-hidden flex items-center gap-3"
      :style="[
        {
          background: 'var(--item-primary-bg)',
          backdropFilter: 'var(--item-primary-backdrop)',
          WebkitBackdropFilter: 'var(--item-primary-backdrop)',
          borderRadius: 'var(--item-radius)',
          boxShadow: 'var(--item-shadow)',
          padding: 'var(--item-padding)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-primary-border)',
        },
        reveal(foundation, roles.length),
      ]"
    >
      <span
        class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
        :style="{
          background: getColorAlpha('var(--color-accent)', 0.16),
          color: getHexColor('var(--color-accent)'),
          border: '1px solid ' + getColorAlpha('var(--color-accent)', 0.35),
        }"
      >
        <Icon :icon="foundation.icon || 'lucide:cross'" class="w-5 h-5" />
      </span>
      <div class="min-w-0">
        <p class="text-text-primary text-sm md:text-base leading-snug">{{ foundation.text }}</p>
        <p v-if="foundation.scripture" class="font-mono text-[10px] md:text-[11px] text-text-muted mt-1">{{ foundation.scripture }}</p>
      </div>
    </div>
  </div>
</template>
