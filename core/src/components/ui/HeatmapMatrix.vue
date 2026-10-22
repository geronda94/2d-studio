<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  rows: { type: Array, default: () => [] },
  cols: { type: Array, default: () => [] },
  cells: { type: Array, default: () => [] },
  scale: { type: String, default: 'rag' }, // rag | irms | bloom | custom
  row_label: { type: String, default: '' },
  col_label: { type: String, default: '' },
  source_note: { type: String, default: '' },
  lean: { type: Boolean, default: false },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'HeatmapMatrix')
const relativeTime = inject('relativeTime', ref(0))

const PRESETS = {
  rag: {
    L: { token: 'var(--color-success)', label: 'Низко' },
    M: { token: 'var(--color-warning)', label: 'Средне' },
    H: { token: 'var(--color-danger)', label: 'Высоко' },
  },
  irms: {
    I: { token: 'var(--text-muted)', label: 'Introduced' },
    R: { token: 'var(--color-secondary)', label: 'Reinforced' },
    M: { token: 'var(--color-warning)', label: 'Mastered' },
    A: { token: 'var(--color-success)', label: 'Assessed' },
  },
}

const numericMax = computed(() => {
  const nums = (props.cells || []).flat().map(Number).filter((n) => !Number.isNaN(n))
  return Math.max(1, ...nums)
})

const cellStyle = (cell) => {
  const s = String(cell ?? '').trim()
  if (s === '') return { background: 'transparent', color: 'var(--text-muted)' }
  const preset = PRESETS[props.scale]
  if (preset && preset[s]) {
    const t = preset[s].token
    return { background: getColorAlpha(t, 0.22), color: getHexColor(t) }
  }
  const num = Number(cell)
  if (!Number.isNaN(num)) {
    const ratio = Math.max(0, Math.min(1, num / numericMax.value))
    // custom/numeric: один акцент, интенсивность = уровень
    return { background: getColorAlpha('var(--color-secondary)', 0.10 + ratio * 0.55), color: ratio > 0.55 ? 'var(--text-primary)' : 'var(--text-secondary)' }
  }
  // bloom/произвольная строка — шахматка акцентов по индексу
  const idx = (s.charCodeAt(0) || 0) % 4
  const t = `var(--item-accent-${idx + 1})`
  return { background: getColorAlpha(t, 0.22), color: getHexColor(t) }
}

const reveal = (r, c) => {
  const t = (r + c) * 60
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(3) }
}

const legend = computed(() => {
  const preset = PRESETS[props.scale]
  if (preset) return Object.values(preset)
  return []
})
const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col justify-center" :class="mobile ? 'overflow-hidden' : 'overflow-x-auto'" :style="{ ...itemVars }">
    <div v-if="!rows.length || !cols.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="grid gap-1.5 md:gap-2 flex-1 min-h-0" :style="{ gridTemplateColumns: mobile ? `minmax(64px, 1fr) repeat(${cols.length}, minmax(0, 1fr))` : `minmax(150px, 1.5fr) repeat(${cols.length}, minmax(0, 1fr))`, gridTemplateRows: `auto repeat(${rows.length}, minmax(0, 1fr))` }">
        <div></div>
        <div v-for="(c, ci) in cols" :key="'c' + ci" class="text-center text-[11px] md:text-xs font-mono text-text-muted pb-1 truncate">{{ c }}</div>

        <template v-for="(r, ri) in rows" :key="'r' + ri">
          <div class="flex items-center text-sm text-text-secondary pr-2 leading-tight min-w-0">{{ r }}</div>
          <div
            v-for="(c, ci) in cols"
            :key="'cell' + ri + '-' + ci"
            class="h-full min-h-[34px] rounded-[calc(var(--item-radius)*0.5)] flex items-center justify-center overflow-hidden"
            :class="mobile ? 'text-[10px] leading-tight font-bold text-center px-0.5 break-words' : 'text-sm md:text-base font-bold'"
            :style="[cellStyle((cells[ri] || [])[ci]), reveal(ri, ci)]"
          >
            {{ (cells[ri] || [])[ci] || '—' }}
          </div>
        </template>
      </div>

      <div class="mt-3 shrink-0 flex flex-wrap items-center justify-between gap-3">
        <div v-if="!lean && legend.length" class="flex flex-wrap gap-3">
          <span v-for="(l, i) in legend" :key="'lg' + i" class="flex items-center gap-1.5 text-xs text-text-secondary">
            <span class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getColorAlpha(l.token, 0.5), border: '1px solid ' + getHexColor(l.token) }"></span>{{ l.label }}
          </span>
        </div>
        <span v-if="!lean && source_note" class="text-xs font-mono text-text-secondary">{{ source_note }}</span>
      </div>
    </template>
  </div>
</template>
