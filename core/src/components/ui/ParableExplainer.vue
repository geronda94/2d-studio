<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  image: { type: String, default: '' },
  title: { type: String, default: '' },
  symbols: { type: Array, default: () => [] },
  moral: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ParableExplainer')
const relativeTime = inject('relativeTime', ref(0))
const imgFailed = ref(false)

const symbols = computed(() => props.symbols || [])
const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)

const reveal = (item, i, y = 12) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const moralStart = computed(() => {
  let last = 0
  symbols.value.forEach((s, i) => {
    last = Math.max(last, s?.start_time ?? i * motion.value.stagger_ms)
  })
  return last + motion.value.stagger_ms
})

const cardStyle = {
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
    <div v-if="!title && !symbols.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex flex-col md:flex-row gap-3 md:gap-5">
      <div
        class="relative w-full md:w-[36%] shrink-0 overflow-hidden h-40 md:h-auto"
        :style="[cardStyle, reveal(null, 0, 14)]"
      >
        <img
          v-if="image && !imgFailed"
          :src="image"
          :alt="title"
          class="absolute inset-0 w-full h-full object-cover"
          @error="imgFailed = true"
        />
        <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-2 text-text-muted">
          <Icon icon="lucide:image" class="w-10 h-10" />
          <span class="text-[11px] font-mono">Образ притчи</span>
        </div>
      </div>

      <div class="flex-1 min-w-0 min-h-0 flex flex-col">
        <h3 v-if="title" class="shrink-0 font-heading font-bold text-text-primary text-xl md:text-2xl" :style="reveal(null, 0, 10)">{{ title }}</h3>

        <div class="flex-1 min-h-0 overflow-y-auto mt-3 flex flex-col gap-2.5">
          <div
            v-for="(s, i) in symbols"
            :key="i"
            class="flex items-start gap-3 py-2.5 px-3"
            :style="[
              {
                background: 'var(--item-primary-bg, var(--item-bg))',
                backdropFilter: 'var(--item-primary-backdrop, var(--item-backdrop))',
                borderRadius: 'var(--item-primary-radius, var(--item-radius))',
                borderWidth: 'var(--item-primary-border-width, var(--item-border-width))',
                borderStyle: 'var(--item-primary-border-style, var(--item-border-style))',
                borderColor: 'var(--item-primary-border, var(--item-border))',
              },
              reveal(s, i),
            ]"
          >
            <div
              class="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
              :style="{ background: getColorAlpha(accent(i), 0.16), color: accent(i), border: '1px solid ' + getColorAlpha(accent(i), 0.5) }"
            >
              <Icon :icon="s.icon || 'lucide:circle-dot'" class="w-4 h-4" />
            </div>
            <p class="font-sans text-text-primary leading-snug pt-1.5 min-w-0" :style="{ fontSize: mobile ? '0.9rem' : '0.98rem' }">{{ s.meaning }}</p>
          </div>
        </div>

        <div
          v-if="moral"
          class="shrink-0 mt-3 py-3 px-4"
          :style="[
            {
              background: getColorAlpha('var(--color-secondary)', 0.1),
              borderLeft: '3px solid ' + getHexColor('var(--color-secondary)'),
              borderRadius: 'var(--item-radius)',
            },
            reveal({ start_time: moralStart }, symbols.length, 10),
          ]"
        >
          <p class="font-sans text-text-primary italic leading-snug" :style="{ fontSize: mobile ? '0.9rem' : '1rem' }">{{ moral }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
