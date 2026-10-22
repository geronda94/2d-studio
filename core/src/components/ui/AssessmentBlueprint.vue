<script setup>
import { computed, inject, ref } from 'vue'
import NotationTable from './NotationTable.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  rows: { type: Array, default: () => [] },
  totals: { type: Object, default: () => ({}) },
  rigor_dist: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'AssessmentBlueprint')
const relativeTime = inject('relativeTime', ref(0))

const columns = ['Стандарт', 'Навык', 'DOK', 'Заданий', 'Баллов', '%']

const pctOf = (r) => {
  const total = Number(props.totals && props.totals.points)
  if (!total) return ''
  return Math.round((Number(r.points) / total) * 100) + '%'
}

const tableRows = computed(() =>
  props.rows.map((r) => ({
    cells: [r.standard, r.skill, 'DOK ' + r.dok, String(r.items), String(r.points), pctOf(r)],
    highlight: Number(r.dok) >= 3,
  })),
)

const highlightRows = computed(() =>
  tableRows.value.map((r, i) => (r.highlight ? i : -1)).filter((i) => i >= 0),
)

const groups = computed(() => [
  { label: '', rows: tableRows.value, subtotal: String((props.totals && props.totals.points) ?? '') },
])

const DOK_COLORS = [
  'var(--text-muted)',
  'var(--color-secondary)',
  'var(--color-warning)',
  'var(--color-danger)',
]

const rigorTotal = computed(
  () => props.rigor_dist.reduce((s, d) => s + (Number(d.pct) || 0), 0) || 1,
)

const rigorStyle = (d) => ({ width: (((Number(d.pct) || 0) / rigorTotal.value) * 100).toFixed(2) + '%' })
const dokColor = (i) => getHexColor(DOK_COLORS[i % DOK_COLORS.length])

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * 120) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
}

const itemStyle = {
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
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div
      v-if="!rows.length"
      class="relative w-full flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 flex flex-col gap-3">
      <div class="flex-1 min-h-0">
        <NotationTable
          :mobile="mobile"
          :variant="variant"
          :fill="true"
          density="compact"
          :columns="columns"
          :groups="groups"
          :highlight_rows="highlightRows"
          :col_weights="[1.2, 2.2, 0.8, 1, 1, 0.8]"
          :subtotal_col="4"
          :unit="'Всего заданий: ' + (totals && totals.items ? totals.items : 0)"
          source_note="Blueprint теста · спецификация и вес заданий"
        />
      </div>

      <div v-if="rigor_dist.length" class="w-full max-w-5xl mx-auto shrink-0">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-text-muted">
          <span>Распределение по строгости (DOK)</span>
          <span>Итог: {{ (totals && totals.points) || 0 }} баллов</span>
        </div>

        <div class="flex h-3 rounded-full overflow-hidden" :style="itemStyle">
          <div
            v-for="(d, i) in rigor_dist"
            :key="'bar' + i"
            class="h-full"
            :style="[{ background: dokColor(i) }, rigorStyle(d), reveal(i)]"
          ></div>
        </div>

        <div class="mt-2 flex flex-wrap gap-3">
          <span
            v-for="(d, i) in rigor_dist"
            :key="'lg' + i"
            class="flex items-center gap-1.5 text-[11px] text-text-secondary"
          >
            <span
              class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]"
              :style="{ background: getColorAlpha(DOK_COLORS[i % DOK_COLORS.length], 0.5), border: '1px solid ' + dokColor(i) }"
            ></span>
            {{ d.label }} · {{ d.pct }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
