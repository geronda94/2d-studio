<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  types: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'LoveTypes')
const relativeTime = inject('relativeTime', ref(0))

const accent = (t, i) => getHexColor(`var(--chart-${(i % 6) + 1})`)

const reveal = (t, i) => {
  const start = t.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}

const panelStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
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
    <div class="flex-1 min-h-0 overflow-hidden" :style="panelStyle">
      <div class="h-full min-h-0" :class="mobile ? 'flex flex-col' : 'grid grid-cols-4'">
        <div
          v-for="(t, i) in types"
          :key="t.greek || t.name || i"
          class="relative flex flex-col min-h-0 overflow-hidden px-4 py-4 md:px-5"
          :class="[
            !mobile && i > 0 ? 'border-l' : '',
            mobile && i > 0 ? 'border-t' : '',
            mobile ? 'flex-1' : '',
          ]"
          :style="[{ borderColor: 'var(--item-border)' }, reveal(t, i)]"
        >
          <span class="block w-10 h-[3px] rounded-full shrink-0" :style="{ background: accent(t, i) }"></span>

          <div class="flex-1 min-h-0 flex flex-col justify-center">
            <div class="mt-3 flex items-baseline gap-2 flex-wrap">
              <span class="font-heading font-bold text-xl md:text-2xl text-text-primary">{{ t.name }}</span>
              <span class="font-mono text-xs text-text-muted">{{ t.greek }}</span>
            </div>

            <p class="mt-2 text-text-secondary leading-relaxed" :class="mobile ? 'text-xs' : 'text-sm'">{{ t.meaning }}</p>

            <div class="mt-4 pt-3 flex items-start gap-2" :style="{ borderTop: '1px solid var(--item-border)' }">
              <Icon icon="lucide:book-open" class="w-3.5 h-3.5 mt-0.5 shrink-0" :style="{ color: accent(t, i) }" />
              <p class="font-sans italic leading-snug text-text-muted" :class="mobile ? 'text-[11px]' : 'text-xs'">{{ t.example }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
