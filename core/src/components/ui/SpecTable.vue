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
  highlight_rows: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'SpecTable')
const relativeTime = inject('relativeTime', ref(0))

const cols = computed(() =>
  props.columns && props.columns.length >= 2 ? props.columns.slice(0, 2) : ['Параметр', 'Значение'],
)

const rowStyle = (row, idx) => {
  const t = row.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const ease = 1 - Math.pow(1 - p, 3)
  return { opacity: ease.toFixed(4), transform: `translateY(${((1 - ease) * 14).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-5xl mx-auto h-full flex flex-col" :class="mobile ? 'justify-start' : 'justify-center'" :style="{ ...itemVars }">
    <div v-if="title" class="mb-5 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="overflow-hidden"
      :class="mobile ? 'flex-1 min-h-0 flex flex-col' : ''"
      :style="{
        background: 'var(--item-bg)',
        backdropFilter: 'var(--item-backdrop)',
        WebkitBackdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)',
        boxShadow: 'var(--item-shadow)',
        padding: 'var(--item-padding)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)',
        borderColor: 'var(--item-border)',
      }"
    >
      <div class="grid shrink-0" :style="{ gridTemplateColumns: mobile ? '1.2fr 1fr' : '1.4fr 1fr' }">
        <div
          v-for="(c, ci) in cols"
          :key="'h' + ci"
          class="px-4 md:px-5 py-3 text-[10px] md:text-[11px] uppercase tracking-widest font-mono text-text-muted"
          :style="{ borderBottom: '1px solid var(--item-border)', textAlign: ci === 1 ? 'right' : 'left' }"
        >
          {{ c }}
        </div>
      </div>

      <div
        v-for="(row, idx) in rows"
        :key="row.id ?? idx"
        class="grid items-center min-h-[68px]"
        :class="mobile ? 'flex-1' : ''"
        :style="[
          { gridTemplateColumns: mobile ? '1.2fr 1fr' : '1.4fr 1fr', borderBottom: '1px solid var(--item-border)' },
          rowStyle(row, idx),
        ]"
      >
        <div class="px-4 md:px-5 py-4 flex items-center gap-3 min-w-0">
          <span
            v-if="row.icon"
            class="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
            :style="{
              background: getColorAlpha(getHexColor(row.color || 'var(--color-secondary)'), 0.15),
              color: getHexColor(row.color || 'var(--color-secondary)'),
            }"
          >
            <Icon :icon="row.icon" class="w-4 h-4" />
          </span>
          <span class="text-text-primary text-sm font-medium truncate">{{ row.label }}</span>
        </div>
        <div
          class="px-4 md:px-5 py-4 text-right font-mono text-sm truncate text-text-primary"
        >
          {{ row.value }}
        </div>
      </div>
    </div>
  </div>
</template>
