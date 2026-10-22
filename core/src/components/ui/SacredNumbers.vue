<script setup>
// SacredNumbers — числа и символизм Писания (7, 40, 12, 3).
// Собственный макет: крупное число → значение → места употребления.
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  numbers: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'SacredNumbers')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => getHexColor(`var(--chart-${(i % 6) + 1})`)

const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}

const sourceReveal = computed(() => {
  const t = (props.numbers?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})

const itemStyle = {
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
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!numbers.length"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-y-auto flex flex-col justify-start gap-1.5 md:gap-2 pr-1">
      <div
        v-for="(n, i) in numbers"
        :key="n.value + i"
        class="flex items-center gap-3 md:gap-4 px-4 py-2 min-h-[68px]"
        :style="[itemStyle, reveal(n, i)]"
      >
        <span
          class="shrink-0 w-16 md:w-20 text-center font-heading font-black leading-none"
          :class="mobile ? 'text-5xl' : 'text-6xl'"
          :style="{ color: accent(i) }"
        >{{ n.value }}</span>

        <div class="flex-1 min-w-0 flex flex-col gap-1.5">
          <p class="text-text-primary font-heading leading-snug" :class="mobile ? 'text-sm' : 'text-base md:text-lg'">
            {{ n.meaning }}
          </p>
          <div v-if="(n.occurrences || []).length" class="flex flex-wrap gap-1.5">
            <span
              v-for="(o, oi) in n.occurrences"
              :key="oi"
              class="px-2 py-0.5 text-[10px] md:text-[11px] font-mono text-text-secondary"
              :style="{
                background: getColorAlpha(accent(i), 0.12),
                border: '1px solid ' + getColorAlpha(accent(i), 0.3),
                borderRadius: 'var(--item-radius)',
              }"
            >{{ o }}</span>
          </div>
        </div>

        <Icon
          v-if="n.icon"
          :icon="n.icon"
          class="hidden md:block shrink-0 w-5 h-5 mt-1 opacity-70"
          :style="{ color: accent(i) }"
        />
      </div>

      <p
        v-if="source"
        class="shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceReveal"
      >{{ source }}</p>
    </div>
  </div>
</template>
