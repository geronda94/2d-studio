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
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  color_scheme: { type: String, default: 'neutral' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ValuesTable')
const relativeTime = inject('relativeTime', ref(0))

const cols = computed(() =>
  props.columns && props.columns.length >= 3 ? props.columns.slice(0, 3) : ['Ценность', 'Практика', 'Результат'],
)

const rowStyle = (row, idx) => {
  const t = row.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 16).toFixed(2)}px)` }
}

const schemeColor = (idx) => {
  const map = { warm: ['var(--color-warning)', 'var(--color-accent)', 'var(--color-error)'], cool: ['var(--color-secondary)', 'var(--color-primary)', 'var(--color-success)'] }
  const palette = map[props.color_scheme] || [`var(--item-accent-${(idx % 4) + 1})`]
  return getHexColor(palette[idx % palette.length])
}

const accent = (row, idx) => getHexColor(row.color || schemeColor(idx))
</script>

<template>
  <div class="w-full max-w-5xl mx-auto h-full flex flex-col justify-center" :style="{ ...itemVars }">
    <div v-if="title" class="mb-5 text-center">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="overflow-hidden"
      :style="{
        background: 'var(--item-bg)',
        backdropFilter: 'var(--item-backdrop)',
        WebkitBackdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)',
        boxShadow: 'var(--item-shadow)',
        // плотная таблица: горизонталь из токена, вертикаль — доля
        padding: 'calc(var(--item-padding) * 0.6) var(--item-padding)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)',
        borderColor: 'var(--item-border)',
      }"
    >
      <div v-if="!mobile" class="grid" :style="{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }">
        <div
          v-for="(c, ci) in cols"
          :key="'h' + ci"
          class="px-5 py-3 text-[11px] uppercase tracking-widest font-mono text-text-muted"
          :style="{ borderBottom: '1px solid var(--item-border)' }"
        >
          {{ c }}
        </div>
      </div>

      <div
        v-for="(row, idx) in rows"
        :key="row.id ?? idx"
        :class="mobile ? 'flex flex-col gap-2' : 'grid items-center min-h-[104px]'"
        :style="[
          rowStyle(row, idx),
          mobile
            ? { padding: '10px 16px', borderBottom: '1px solid var(--item-border)', borderLeft: '3px solid ' + accent(row, idx) }
            : { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', borderBottom: '1px solid var(--item-border)' },
        ]"
      >
        <div class="px-4 md:px-5 py-2 md:py-3.5 flex items-center gap-2.5 min-w-0">
          <span class="w-8 h-8 flex items-center justify-center shrink-0" :style="{ background: getColorAlpha(accent(row, idx), 0.15), borderRadius: 'calc(var(--item-radius) - 4px)' }">
            <Icon :icon="row.icon || 'heroicons:heart'" class="w-5 h-5" :style="{ color: accent(row, idx) }" />
          </span>
          <span class="font-heading font-bold text-text-primary text-base">{{ row.value }}</span>
        </div>
        <div class="px-4 md:px-5 py-2 md:py-3.5 text-text-secondary text-[15px] leading-snug">{{ row.practice }}</div>
        <div class="px-4 md:px-5 py-2 md:py-3.5 text-[15px] leading-snug" :style="{ color: accent(row, idx) }">{{ row.result }}</div>
      </div>
    </div>
  </div>
</template>
