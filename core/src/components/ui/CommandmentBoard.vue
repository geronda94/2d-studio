<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  items: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'CommandmentBoard')
const relativeTime = inject('relativeTime', ref(0))

const items = computed(() => props.items || [])
const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)

const reveal = (item, i, y = 12) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  padding: 'var(--item-padding)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!items.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-3 content-start" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
      <div
        v-for="(item, i) in items"
        :key="item.no ?? i"
        class="flex items-start gap-2 md:gap-3"
        :style="[cardStyle, mobile ? { padding: '8px 10px' } : {}, reveal(item, i)]"
      >
        <span
          class="rounded-full flex items-center justify-center shrink-0 font-heading font-bold text-lg"
          :class="mobile ? 'w-9 h-9 text-base' : 'w-11 h-11'"
          :style="{ background: getColorAlpha(accent(i), 0.16), color: accent(i), border: '1px solid ' + getColorAlpha(accent(i), 0.5) }"
        >{{ item.no }}</span>

        <div class="min-w-0 flex-1">
          <div class="flex items-start gap-2">
            <Icon :icon="item.icon || 'lucide:book-open'" class="w-4 h-4 mt-0.5 shrink-0" :style="{ color: accent(i) }" />
            <p class="font-sans text-text-primary font-medium leading-snug min-w-0" :style="{ fontSize: mobile ? '0.95rem' : '1.05rem' }">{{ item.text }}</p>
          </div>
          <p v-if="item.meaning" class="mt-1.5 text-text-secondary leading-snug" :style="{ fontSize: mobile ? '0.8rem' : '0.88rem' }">{{ item.meaning }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
