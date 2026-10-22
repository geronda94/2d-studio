<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  verse: { type: String, default: '' },
  reference: { type: String, default: '' },
  translation: { type: String, default: '' },
  original: { type: String, default: '' },
  highlight: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'VerseFocus')
const relativeTime = inject('relativeTime', ref(0))

const accent = 'var(--color-secondary)'

const reveal = (item, i, y = 14) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const clean = (w) => String(w || '').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '')

const tokens = computed(() => {
  const set = new Set((props.highlight || []).map(clean).filter(Boolean))
  return String(props.verse || '')
    .split(/(\s+)/)
    .map((word) => ({ text: word, on: set.has(clean(word)) }))
})

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  padding: 'var(--item-padding)',
  paddingTop: '3rem',
  paddingBottom: '3rem',
  paddingLeft: 'clamp(1.5rem, 6%, 4rem)',
  paddingRight: 'clamp(1.5rem, 6%, 4rem)',
}

const highlightStyle = {
  color: getHexColor(accent),
  background: getColorAlpha(accent, 0.16),
  borderRadius: '4px',
  padding: '0 4px',
  boxShadow: 'inset 0 -2px 0 ' + getColorAlpha(accent, 0.7),
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!verse" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex items-center justify-center">
      <div class="w-full max-w-5xl" :style="[cardStyle, reveal(null, 0, 18)]">
        <div class="flex flex-wrap items-center justify-center gap-x-3 gap-y-1.5">
          <Icon icon="lucide:book-open" class="w-5 h-5 shrink-0" :style="{ color: getHexColor(accent) }" />
          <span v-if="translation" class="text-[11px] md:text-xs font-mono uppercase tracking-widest text-text-muted">{{ translation }}</span>
          <span
            v-if="reference"
            class="px-2.5 py-0.5 text-[11px] md:text-xs font-mono font-bold"
            :style="{
              color: getHexColor(accent),
              background: getColorAlpha(accent, 0.14),
              borderRadius: '999px',
              border: '1px solid ' + getColorAlpha(accent, 0.4),
            }"
          >{{ reference }}</span>
        </div>

        <p
          class="mt-8 text-center font-sans text-text-primary leading-snug"
          :style="{ fontSize: mobile ? '1.5rem' : '2.5rem' }"
        >
          <template v-for="(t, i) in tokens" :key="i"><span v-if="t.on" :style="highlightStyle">{{ t.text }}</span><span v-else>{{ t.text }}</span></template>
        </p>

        <div
          v-if="original"
          class="mt-8 pt-6"
          :style="[
            { borderTopWidth: 'var(--item-border-width)', borderTopStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' },
            reveal({ start_time: Math.round(motion.appear_ms * 0.8) }, 1, 10),
          ]"
        >
          <p
            class="text-center font-sans italic text-text-secondary leading-relaxed"
            :style="{ fontSize: mobile ? '1rem' : '1.3rem' }"
          >{{ original }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
