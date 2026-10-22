<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'
import NotationTable from './NotationTable.vue'
import WaterfallChart from './WaterfallChart.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  currency: { type: String, default: '€' },
  orders: { type: Array, default: () => [] },
  cumulative: { type: Object, default: () => ({}) },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ChangeOrderLog')
const relativeTime = inject('relativeTime', ref(0))

const columns = ['Изменение', 'Статус', 'Бюджет', 'Срок']
const fmt = (n) => Number(n || 0).toLocaleString('ru-RU', { maximumFractionDigits: 0 })
const signed = (n) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${fmt(Math.abs(n))}`

const groups = computed(() => [
  {
    label: '',
    rows: (props.orders || []).map((o) => ({
      cells: [
        o.title,
        o.status,
        signed(Number(o.cost_delta) || 0) + ' ' + props.currency,
        signed(Number(o.days_delta) || 0) + ' дн.',
      ],
    })),
    subtotal: signed(Number(props.cumulative?.cost_delta) || 0) + ' ' + props.currency,
  },
])

const steps = computed(() =>
  (props.orders || [])
    .filter((o) => Number(o.cost_delta))
    .map((o) => ({
      label: o.id,
      delta: Number(o.cost_delta) || 0,
      kind: (Number(o.cost_delta) || 0) >= 0 ? 'pos' : 'neg',
    })),
)

const approved = computed(() => (props.orders || []).filter((o) => /утвержд|согласов|approved/i.test(o.status || '')).length)

const chips = computed(() => [
  { label: 'Изменений', value: String((props.orders || []).length), icon: 'lucide:file-diff', token: 'var(--color-secondary)' },
  { label: 'Утверждено', value: String(approved.value), icon: 'lucide:check-circle', token: 'var(--color-success)' },
  {
    label: 'Бюджет',
    value: signed(Number(props.cumulative?.cost_delta) || 0) + ' ' + props.currency,
    icon: 'lucide:banknote',
    token: (Number(props.cumulative?.cost_delta) || 0) > 0 ? 'var(--color-danger)' : 'var(--color-success)',
  },
  {
    label: 'Срок',
    value: signed(Number(props.cumulative?.days_delta) || 0) + ' дн.',
    icon: 'lucide:calendar-plus',
    token: 'var(--color-warning)',
  },
])

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col gap-2 md:gap-3" :style="{ ...itemVars }">
    <div v-if="!orders.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
        <div
          v-for="(c, i) in chips"
          :key="c.label"
          class="flex items-center gap-2 md:gap-3 px-2.5 py-1.5 md:px-3 md:py-2"
          :style="[
            {
              ...itemPrimaryVars,
              background: 'var(--item-primary-bg)',
              backdropFilter: 'var(--item-primary-backdrop)',
              borderRadius: 'var(--item-primary-radius)',
              boxShadow: 'var(--item-primary-shadow)',
              padding: 'var(--item-primary-padding)',
              borderWidth: 'var(--item-primary-border-width)',
              borderStyle: 'var(--item-primary-border-style)',
              borderColor: 'var(--item-primary-border)',
            },
            reveal(i),
          ]"
        >
          <Icon :icon="c.icon" class="w-4 h-4 md:w-5 md:h-5 shrink-0" :style="{ color: getHexColor(c.token) }" />
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-widest font-mono text-text-muted truncate">{{ c.label }}</div>
            <div class="font-mono text-base md:text-lg font-bold truncate" :style="{ color: getHexColor(c.token) }">{{ c.value }}</div>
          </div>
        </div>
      </div>

      <div class="flex-1 min-h-0 flex flex-col gap-2 md:gap-3">
        <div class="flex-1 min-h-0 flex">
          <NotationTable
            :variant="variant"
            :mobile="mobile"
            :fill="!mobile"
            :col_weights="mobile ? [2.3, 1.5, 1.2, 1.0] : [2.8, 1, 1.1, 1]"
            :density="mobile ? 'dense' : 'compact'"
            :columns="columns"
            :groups="groups"
            :unit="currency"
          />
        </div>

        <div class="shrink-0 flex flex-col gap-1 overflow-hidden" :class="mobile ? 'h-[220px]' : 'h-[36%]'">
          <span class="text-[10px] uppercase tracking-widest font-mono text-text-muted">Накопленный эффект, {{ currency }}</span>
          <div class="flex-1 min-h-0 [&>div]:h-full [&_.min-h-\[280px\]]:min-h-0 [&_.min-h-\[150px\]]:min-h-0">
            <WaterfallChart
              :variant="variant"
              :mobile="mobile"
              density="compact"
              start_label="Старт"
              :start_value="0"
              :steps="steps"
              end_label="Итог"
              :value_prefix="currency"
            />
          </div>
        </div>
      </div>

      <div v-if="source_note" class="text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</div>
    </template>
  </div>
</template>
