<script setup>
// FigureCard — карточка личности: портрет, эпоха, вклад, цитата.
// Портрет заполняет кадр по высоте; при отсутствии/ошибке картинки — стилизованный
// empty-state на токенах (градиент + иконка персоны), без «битой картинки».
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  image: { type: String, default: '' },
  name: { type: String, default: '' },
  years: { type: String, default: '' },
  office: { type: String, default: '' },
  contribution: { type: String, default: '' },
  quote: { type: String, default: '' },
  quote_source: { type: String, default: '' },
  facts: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'FigureCard')
const relativeTime = inject('relativeTime', ref(0))
const imgFailed = ref(false)

const specs = computed(() => {
  const list = []
  if (props.contribution) list.push({ label: 'Вклад', value: props.contribution })
  for (const f of props.facts || []) {
    list.push({ label: f.label, value: f.value, unit: f.unit })
  }
  return list
})

const reveal = (i) => {
  const start = i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const quoteReveal = computed(() => {
  const t = (specs.value.length + 1) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
})

const accent = getHexColor('var(--color-accent)')
const secondary = getHexColor('var(--color-secondary)')

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
}

const innerCardStyle = {
  background: 'var(--item-primary-bg)',
  backdropFilter: 'var(--item-primary-backdrop)',
  WebkitBackdropFilter: 'var(--item-primary-backdrop)',
  borderRadius: 'var(--item-primary-radius)',
  borderWidth: 'var(--item-primary-border-width)',
  borderStyle: 'var(--item-primary-border-style)',
  borderColor: 'var(--item-primary-border)',
}
</script>

<template>
  <div class="w-full h-full min-h-0 flex" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div
      class="w-full h-full min-h-0 overflow-hidden flex"
      :class="mobile ? 'flex-col' : 'flex-row'"
      :style="cardStyle"
    >
      <!-- ПОРТРЕТ / EMPTY-STATE -->
      <div
        class="relative shrink-0 overflow-hidden"
        :class="mobile ? 'w-full aspect-[16/9]' : 'h-full w-[300px] max-w-[40%]'"
        :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)' }"
      >
        <img
          v-if="image && !imgFailed"
          :src="image"
          :alt="name"
          class="absolute inset-0 w-full h-full object-cover object-top"
          @error="imgFailed = true"
        />
        <div
          v-else
          class="absolute inset-0 flex flex-col items-center justify-center gap-4 overflow-hidden"
          :style="{ background: `linear-gradient(165deg, ${getColorAlpha('var(--color-accent)', 0.18)}, transparent 62%), var(--item-primary-bg)` }"
        >
          <span
            class="absolute rounded-full pointer-events-none"
            :style="{ width: '200px', height: '200px', border: '1px solid ' + getColorAlpha('var(--text-primary)', 0.05) }"
          ></span>
          <span
            class="absolute rounded-full pointer-events-none"
            :style="{ width: '138px', height: '138px', border: '1px solid ' + getColorAlpha('var(--text-primary)', 0.07) }"
          ></span>
          <span
            class="relative w-24 h-24 rounded-full flex items-center justify-center"
            :style="{ background: getColorAlpha('var(--text-primary)', 0.06), border: '1px dashed ' + getColorAlpha('var(--text-primary)', 0.2) }"
          >
            <Icon icon="lucide:user-round" class="w-12 h-12" :style="{ color: getColorAlpha('var(--text-primary)', 0.55) }" />
          </span>
          <span v-if="name" class="relative px-4 text-center font-heading text-sm text-text-secondary leading-tight">{{ name }}</span>
        </div>
        <div
          class="absolute inset-x-0 bottom-0 h-20 pointer-events-none"
          :style="{ background: 'linear-gradient(to top, var(--item-primary-bg), transparent)' }"
        ></div>
      </div>

      <!-- КОНТЕНТ -->
      <div class="flex-1 min-w-0 min-h-0 flex flex-col" :class="mobile ? 'p-4 gap-2' : 'p-5 gap-3'">
        <div class="shrink-0 flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="font-heading font-bold text-text-primary leading-tight" :class="mobile ? 'text-xl' : 'text-3xl'">{{ name }}</h3>
            <p v-if="years" class="mt-1 flex items-center gap-1.5 text-text-secondary" :class="mobile ? 'text-xs' : 'text-sm'">
              <Icon icon="lucide:calendar-days" class="w-4 h-4 shrink-0" />
              <span class="truncate">{{ years }}</span>
            </p>
          </div>
          <span
            v-if="office"
            class="shrink-0 px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full"
            :style="{ background: getColorAlpha('var(--color-secondary)', 0.16), color: secondary, border: '1px solid ' + getColorAlpha('var(--color-secondary)', 0.4) }"
          >{{ office }}</span>
        </div>

        <div class="flex-1 min-h-0 flex items-center">
          <div class="grid w-full gap-2" :class="mobile ? 'grid-cols-2' : 'grid-cols-2 lg:grid-cols-3'">
            <div
              v-for="(s, i) in specs"
              :key="s.label + i"
              class="px-3 py-2.5 min-w-0"
              :style="[innerCardStyle, reveal(i)]"
            >
              <div class="text-[10px] uppercase tracking-widest font-mono text-text-muted truncate">{{ s.label }}</div>
              <div class="mt-1 font-heading text-text-primary">
                <span class="font-bold" :class="mobile ? 'text-sm' : 'text-lg'">{{ s.value }}</span>
                <span v-if="s.unit" class="ml-1 text-xs text-text-secondary">{{ s.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <blockquote
          v-if="quote"
          class="shrink-0 px-4 py-2.5 flex items-start gap-2.5"
          :style="[innerCardStyle, quoteReveal]"
        >
          <Icon icon="lucide:quote" class="w-4 h-4 shrink-0 mt-0.5" :style="{ color: accent }" />
          <div class="min-w-0">
            <p class="font-heading italic text-text-primary leading-snug" :class="mobile ? 'text-sm' : 'text-base'">
              «{{ quote }}»
            </p>
            <cite
              v-if="quote_source"
              class="mt-1 block not-italic text-[11px] font-mono"
              :style="{ color: secondary }"
            >— {{ quote_source }}</cite>
          </div>
        </blockquote>
      </div>
    </div>
  </div>
</template>
