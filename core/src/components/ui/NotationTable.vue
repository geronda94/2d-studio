<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  columns: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] }, // [{label, rows:[{cells:[...],bold?,note?}], subtotal?}]
  rows: { type: Array, default: () => [] },   // плоский вариант без групп
  unit: { type: String, default: '' },
  highlight_rows: { type: Array, default: () => [] }, // индексы плоских rows
  source_note: { type: String, default: '' },
  fill: { type: Boolean, default: false }, // растянуть строки на всю доступную высоту (без скролла)
  col_weights: { type: Array, default: () => [] }, // доли колонок, напр. [2.4, 1, 1, 1]
  subtotal_col: { type: Number, default: -1 }, // индекс колонки для «Итого» (-1 = последняя)
  wrap_cols: { type: Array, default: () => [] }, // индексы колонок, где разрешён перенос строки вместо обрезки
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'NotationTable')
const relativeTime = inject('relativeTime', ref(0))

const cols = computed(() => (props.columns.length ? props.columns : ['Наименование', 'Значение']))

const normalized = computed(() => {
  const groups = props.groups && props.groups.length
    ? props.groups.map((g) => ({ label: g.label, subtotal: g.subtotal, rows: g.rows || [] }))
    : [{ label: '', subtotal: '', rows: props.rows || [] }]
  let i = 0
  groups.forEach((g) => g.rows.forEach((r) => { r._i = i++ }))
  return groups
})

const isNumeric = (cell) => /^[-+]?[\d\s.,]+%?$/.test(String(cell ?? '').trim()) && /\d/.test(String(cell))

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * Math.min(400, motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  // В режиме fill (без скролла) не сдвигаем строки: transform раздувает
  // scrollHeight контейнера и даёт ложный «скролл» на мобильном.
  if (props.fill) return { opacity: e.toFixed(4) }
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}

const isHighlight = (row) => row.highlight === true || (props.highlight_rows || []).includes(row._i)
const compact = computed(() => props.density === 'compact' || props.mobile)
const dense = computed(() => props.density === 'dense')

const gridTemplate = computed(() => {
  const n = cols.value.length
  const weights = (props.col_weights && props.col_weights.length === n)
    ? props.col_weights
    : [1.6, ...Array(Math.max(0, n - 1)).fill(1)]
  return weights.map((w) => `minmax(0, ${w}fr)`).join(' ')
})

const subtotalCol = computed(() =>
  props.subtotal_col >= 0 && props.subtotal_col < cols.value.length
    ? props.subtotal_col
    : cols.value.length - 1,
)
const rowPad = computed(() => (dense.value ? 'py-1' : compact.value ? 'py-1.5' : 'py-2.5'))
const headPad = computed(() => (dense.value ? 'py-1.5' : 'py-3'))
const groupPad = computed(() => (dense.value ? 'py-1' : 'py-2'))
const rowText = computed(() => (dense.value ? 'text-[11px]' : compact.value ? 'text-xs' : 'text-sm'))
// На мобильном горизонтальные отступы клеток минимальны — иначе длинные
// значения (суммы, наименования) обрезаются многоточием.
const cellPad = computed(() => (props.mobile ? 'px-1.5' : 'px-4'))
</script>

<template>
  <div
    class="w-full max-w-5xl mx-auto"
    :class="fill ? 'h-full min-h-0 flex flex-col' : 'overflow-hidden'"
    :style="{ ...itemVars }"
  >
    <div v-if="!rows.length && !groups.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <div
      v-else
      :class="fill ? 'flex-1 min-h-0 flex flex-col' : ''"
      :style="{
        background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)',
        borderWidth: 'var(--item-border-width)', borderStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)',
        overflow: fill ? 'hidden' : undefined,
      }"
    >
      <div class="grid shrink-0" :style="{ gridTemplateColumns: gridTemplate }">
        <div
          v-for="(c, ci) in cols"
          :key="'h' + ci"
          class="text-[10px] uppercase tracking-widest font-mono text-text-muted"
          :class="[headPad, cellPad]"
          :style="{ borderBottom: '1px solid var(--item-border)', textAlign: ci === 0 ? 'left' : 'right' }"
        >{{ c }}</div>
      </div>

      <template v-for="(g, gi) in normalized" :key="'g' + gi">
        <div v-if="g.label" class="shrink-0 flex items-center gap-2" :class="[groupPad, cellPad]" :style="{ background: 'var(--item-primary-bg)', borderBottom: '1px solid var(--item-border)' }">
          <Icon icon="heroicons:folder" class="w-3.5 h-3.5" :style="{ color: getHexColor('var(--color-secondary)') }" />
          <span class="text-xs font-bold text-text-primary">{{ g.label }}</span>
        </div>

        <div
          v-for="(row, ri) in g.rows"
          :key="'r' + gi + '-' + ri"
          class="grid items-center"
          :class="fill ? 'flex-1 min-h-0' : ''"
          :style="[
            { gridTemplateColumns: gridTemplate, borderBottom: '1px solid var(--item-border)' },
            reveal(row._i || 0),
            isHighlight(row) ? { background: 'color-mix(in srgb, var(--color-secondary) 10%, transparent)' } : {},
          ]"
        >
          <div
            v-for="(cell, ci) in row.cells || []"
            :key="'c' + ci"
            class="min-w-0"
            :class="[wrap_cols.includes(ci) ? cellPad + ' whitespace-normal break-words leading-snug' : cellPad + ' truncate', fill ? 'py-0.5' : rowPad, rowText, [1, 2, 3, 4, 5, 6, 7].includes(ci) ? 'font-mono' : 'font-medium', ci === 0 ? 'text-text-primary' : 'text-text-secondary', row.bold ? 'font-bold text-text-primary' : '']"
            :style="{ textAlign: ci === 0 ? 'left' : 'right', color: ci === 0 && isHighlight(row) ? getHexColor('var(--color-secondary)') : undefined }"
          >{{ cell }}</div>
        </div>

        <div
          v-if="g.subtotal"
          class="grid items-center"
          :class="fill ? 'flex-1 min-h-0' : ''"
          :style="{ gridTemplateColumns: gridTemplate, borderBottom: '1px solid var(--item-border)', background: 'var(--item-primary-bg)' }"
        >
          <span class="truncate text-xs font-bold text-text-primary" :class="[fill ? 'py-0.5' : rowPad, cellPad]">Итого{{ g.label ? ' · ' + g.label : '' }}</span>
          <span
            v-for="n in cols.length - 1"
            :key="'st' + n"
            class="truncate text-sm font-mono font-bold text-right"
            :class="[fill ? 'py-0.5' : rowPad, cellPad]"
            :style="{ color: n === subtotalCol ? getHexColor('var(--color-secondary)') : 'var(--text-primary)' }"
          >{{ n === subtotalCol ? g.subtotal : '' }}</span>
        </div>
      </template>

      <div v-if="!fill" class="h-1 md:h-1.5" aria-hidden="true"></div>
    </div>

    <div v-if="unit || source_note" class="mt-0.5 md:mt-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-0.5 text-[11px] font-mono text-text-muted">
      <span>{{ unit ? 'Ед.: ' + unit : '' }}</span>
      <span v-if="source_note" class="opacity-70">{{ source_note }}</span>
    </div>
  </div>
</template>
