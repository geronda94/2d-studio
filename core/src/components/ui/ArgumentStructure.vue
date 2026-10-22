<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  thesis: { type: String, default: '' },
  premises: { type: Array, default: () => [] },
  conclusion: { type: String, default: '' },
  objection: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ArgumentStructure')
const relativeTime = inject('relativeTime', ref(0))

const accent = getHexColor('var(--color-secondary)')
const success = getHexColor('var(--color-success)')
const warn = getHexColor('var(--color-warning)')

const reveal = (t, y = 14) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const premiseList = computed(() =>
  (props.premises || []).map((p) => (typeof p === 'string' ? { text: p, source: '' } : p)),
)

const premiseTime = (p, i) => p.start_time ?? (i + 1) * motion.value.stagger_ms
const conclusionTime = computed(() => (premiseList.value.length + 1) * motion.value.stagger_ms)
const objectionTime = computed(() => (premiseList.value.length + 2) * motion.value.stagger_ms)

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const primaryStyle = {
  background: 'var(--item-primary-bg)',
  backdropFilter: 'var(--item-primary-backdrop)',
  borderRadius: 'var(--item-primary-radius)',
  boxShadow: 'var(--item-primary-shadow)',
  padding: 'var(--item-primary-padding)',
  padding: 'var(--item-primary-padding)',
  borderWidth: 'var(--item-primary-border-width)',
  borderStyle: 'var(--item-primary-border-style)',
  borderColor: 'var(--item-primary-border)',
}
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!thesis && !premiseList.length"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex flex-col" :style="{ gap: 'var(--item-gap)' }">
      <div class="shrink-0 relative overflow-hidden" :style="[primaryStyle, reveal(0)]">
        <span class="absolute left-0 top-0 bottom-0 w-1" :style="{ background: accent, borderRadius: '2px' }"></span>
        <div class="flex items-center gap-2 mb-1">
          <Icon icon="lucide:flag" class="w-3.5 h-3.5" :style="{ color: accent }" />
          <span class="text-[10px] font-mono uppercase tracking-widest text-text-muted">Тезис</span>
        </div>
        <p class="text-text-primary text-sm md:text-lg font-medium leading-snug">{{ thesis }}</p>
      </div>

      <div class="flex-1 min-h-0 flex flex-col" :style="{ gap: 'var(--item-gap)' }">
        <div
          v-for="(p, i) in premiseList"
          :key="'p' + i"
          class="flex-1 min-h-0 flex items-center gap-3 md:gap-4 min-w-0"
          :style="[itemStyle, reveal(premiseTime(p, i), 10)]"
        >
          <span
            class="w-7 h-7 md:w-9 md:h-9 rounded-full flex items-center justify-center shrink-0 text-xs md:text-sm font-bold"
            :style="{ background: getColorAlpha(accent, 0.16), color: accent, border: '1px solid ' + getColorAlpha(accent, 0.35) }"
          >{{ i + 1 }}</span>
          <span class="min-w-0 flex-1">
            <span class="block text-text-primary text-sm md:text-base leading-snug">{{ p.text }}</span>
            <span v-if="p.source" class="block text-[10px] md:text-xs font-mono text-text-muted mt-0.5">{{ p.source }}</span>
          </span>
        </div>
      </div>

      <div class="shrink-0 grid" :class="mobile ? 'grid-cols-1' : 'grid-cols-2'" :style="{ gap: 'var(--item-gap)' }">
        <div
          class=""
          :style="[itemStyle, reveal(conclusionTime), { borderColor: getColorAlpha(success, 0.5) }]"
        >
          <div class="flex items-center gap-2 mb-1">
            <Icon icon="lucide:check-circle" class="w-3.5 h-3.5" :style="{ color: success }" />
            <span class="text-[10px] font-mono uppercase tracking-widest text-text-muted">Вывод</span>
          </div>
          <p class="text-text-primary text-xs md:text-sm leading-snug">{{ conclusion }}</p>
        </div>

        <div
          class=""
          :style="[itemStyle, reveal(objectionTime), { borderStyle: 'dashed', borderColor: getColorAlpha(warn, 0.5) }]"
        >
          <div class="flex items-center gap-2 mb-1">
            <Icon icon="lucide:message-circle-question" class="w-3.5 h-3.5" :style="{ color: warn }" />
            <span class="text-[10px] font-mono uppercase tracking-widest text-text-muted">Возражение</span>
          </div>
          <p class="text-text-secondary text-xs md:text-sm leading-snug">{{ objection }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
