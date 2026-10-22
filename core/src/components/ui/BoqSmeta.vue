<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import NotationTable from './NotationTable.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  currency: { type: String, default: '€' },
  sections: { type: Array, default: () => [] },
  subtotal: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'BoqSmeta')
const relativeTime = inject('relativeTime', ref(0))

const columns = ['Наименование', 'Ед.', 'Кол-во', 'Цена', 'Сумма']

const fmt = (n) => Number(n || 0).toLocaleString('ru-RU', { maximumFractionDigits: 2 })
const money = (n) => `${fmt(n)} ${props.currency}`

const rowAmount = (r) => Number(r.qty || 0) * Number(r.rate || 0)
const sectionSum = (s) => (s.rows || []).reduce((acc, r) => acc + rowAmount(r), 0)

const positionCount = computed(() =>
  (props.sections || []).reduce((acc, s) => acc + (s.rows || []).length, 0),
)

const groups = computed(() =>
  (props.sections || []).map((s) => ({
    label: s.code ? `${s.code} · ${s.name}` : s.name,
    rows: (s.rows || []).map((r) => ({
      cells: [r.name, r.unit || '', fmt(r.qty), fmt(r.rate), fmt(rowAmount(r))],
    })),
    subtotal: fmt(sectionSum(s)),
  })),
)

const shares = computed(() => {
  const sum = (props.sections || []).reduce((acc, s) => acc + sectionSum(s), 0) || 1
  return (props.sections || []).map((s, i) => ({
    label: s.name,
    pct: (sectionSum(s) / sum) * 100,
    color: `var(--item-accent-${(i % 4) + 1})`,
  }))
})

const barReveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / motion.value.appear_ms))
  return { transform: `scaleX(${(1 - Math.pow(1 - p, 3)).toFixed(4)})` }
}

const totalsDelay = computed(() => (props.sections || []).length * motion.value.stagger_ms)
const totalsReveal = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - totalsDelay.value) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  // Только opacity: transform на нижнем блоке даёт ложный overflow/скролл.
  return { opacity: e.toFixed(4) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-0.5 md:gap-2" :style="{ ...itemVars }">
    <div v-if="!sections.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between">
        <span class="flex items-center gap-2 text-[11px] font-mono text-text-muted">
          <Icon icon="lucide:layers" class="w-3.5 h-3.5" />
          {{ sections.length }} разделов · {{ positionCount }} позиций
        </span>
        <span class="text-[11px] font-mono text-text-muted">Единица: {{ currency }}</span>
      </div>

      <div class="flex-1 min-h-0 overflow-hidden pr-1">
        <NotationTable
          :variant="variant"
          :mobile="mobile"
          :fill="true"
          density="dense"
          :columns="columns"
          :groups="groups"
          :col_weights="mobile ? [1.5, 0.6, 0.9, 1.0, 1.15] : [1.6, 1, 1, 1, 1]"
          :unit="currency"
        />
      </div>

      <div v-if="positionCount <= 4" class="flex flex-col gap-1.5">
        <span class="text-[10px] uppercase tracking-widest font-mono text-text-muted">Структура затрат</span>
        <div class="flex w-full h-3 overflow-hidden rounded-full" :style="{ background: 'var(--item-primary-bg)' }">
          <div
            v-for="(s, i) in shares"
            :key="s.label + i"
            class="h-full origin-left"
            :style="[{ width: s.pct.toFixed(2) + '%', background: getColorAlpha(s.color, 0.85) }, barReveal(i)]"
          ></div>
        </div>
        <div class="flex flex-wrap gap-x-4 gap-y-1">
          <span v-for="(s, i) in shares" :key="'l' + i" class="flex items-center gap-1.5 text-[11px] text-text-secondary">
            <span class="w-2.5 h-2.5 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getColorAlpha(s.color, 0.85) }"></span>
            {{ s.label }} · {{ s.pct.toFixed(0) }}%
          </span>
        </div>
      </div>

      <div
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-0.5 sm:gap-2 px-3 py-0.5 md:py-2"
        :style="[
          {
            ...itemPrimaryVars,
            background: 'var(--item-primary-bg)',
            backdropFilter: 'var(--item-primary-backdrop)',
            borderRadius: 'var(--item-primary-radius)',
            boxShadow: 'var(--item-primary-shadow)',
            padding: 'var(--item-primary-padding)',
            border: 'var(--item-primary-border-width) var(--item-primary-border-style) var(--item-primary-border)',
          },
          totalsReveal,
        ]"
      >
        <div class="flex items-center gap-2">
          <Icon icon="lucide:clipboard-list" class="w-4 h-4" :style="{ color: getHexColor('var(--color-secondary)') }" />
          <span class="text-xs uppercase tracking-widest font-mono text-text-secondary">Итого по разделам</span>
          <span class="text-base font-mono font-bold text-text-primary">{{ money(subtotal) }}</span>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-xs uppercase tracking-widest font-mono text-text-secondary">Всего</span>
          <span class="text-xl sm:text-2xl font-mono font-bold" :style="{ color: getHexColor('var(--color-secondary)') }">{{ money(total) }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
