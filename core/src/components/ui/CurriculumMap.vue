<script setup>
import { computed, inject, ref } from 'vue'
import HeatmapMatrix from './HeatmapMatrix.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  courses: { type: Array, default: () => [] },
  outcomes: { type: Array, default: () => [] },
  map: { type: Array, default: () => [] },
  notation: { type: String, default: 'irms' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CurriculumMap')
const relativeTime = inject('relativeTime', ref(0))

const scale = computed(() =>
  ['rag', 'irms', 'bloom', 'custom'].includes(props.notation) ? props.notation : 'irms',
)

const NOTATION = [
  { code: 'I', label: 'Знакомство', token: 'var(--text-muted)' },
  { code: 'R', label: 'Закрепление', token: 'var(--color-secondary)' },
  { code: 'M', label: 'Мастерство', token: 'var(--color-warning)' },
  { code: 'A', label: 'Оценка', token: 'var(--color-success)' },
]

const coverage = computed(() =>
  props.courses.map((c, ri) => {
    const row = props.map[ri] || []
    const filled = row.filter((x) => String(x ?? '').trim() !== '').length
    const mastered = row.filter((x) => ['M', 'A'].includes(String(x ?? '').trim().toUpperCase())).length
    const total = props.outcomes.length || 1
    return { name: c, filled, mastered, pct: Math.round((mastered / total) * 100) }
  }),
)

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * 90) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(3) }
}

const fillRate = computed(() => {
  const total = props.courses.length * (props.outcomes.length || 1)
  const filled = (props.map || []).reduce(
    (s, row) => s + (row || []).filter((x) => String(x ?? '').trim() !== '').length,
    0,
  )
  return total ? Math.round((filled / total) * 100) : 0
})

const itemStyle = {
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
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div
      v-if="!courses.length || !outcomes.length"
      class="relative w-full flex-1 min-h-[320px] flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col gap-3">
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Карта курсов и результатов</span>
        <span
          v-for="t in NOTATION"
          :key="t.code"
          class="flex items-center gap-1.5 text-[11px] text-text-secondary"
        >
          <span
            class="w-4 h-4 rounded-[calc(var(--item-radius)-4px)] flex items-center justify-center text-[9px] font-mono font-bold"
            :style="{ background: getColorAlpha(t.token, 0.22), border: '1px solid ' + getHexColor(t.token), color: getHexColor(t.token) }"
          >{{ t.code }}</span>
          {{ t.label }}
        </span>
        <span class="ml-auto text-[11px] font-mono text-text-muted">
          {{ courses.length }} курсов · {{ outcomes.length }} результатов · заполнено {{ fillRate }}%
        </span>
      </div>

      <HeatmapMatrix
        :mobile="mobile"
        :variant="variant"
        :rows="courses"
        :cols="outcomes"
        :cells="map"
        :scale="scale"
        :lean="true"
        row_label="Курс"
        col_label="Результат"
      />

      <div class="w-full flex flex-col" :style="{ gap: 'var(--item-gap)' }">
        <span class="text-[11px] font-mono text-text-muted">Доля результатов уровня «мастерство / оценка» по курсам</span>
        <div
          v-for="(c, i) in coverage"
          :key="'cov' + i"
          class="flex items-center gap-3"
          :style="[itemStyle, reveal(i)]"
        >
          <span class="w-40 shrink-0 text-xs text-text-secondary leading-tight truncate">{{ c.name }}</span>
          <div class="flex-1 h-2 rounded-full overflow-hidden" :style="{ background: getColorAlpha('var(--color-secondary)', 0.14) }">
            <div
              class="h-full origin-left"
              :style="{ width: c.pct + '%', background: getHexColor('var(--color-secondary)'), borderRadius: 'inherit' }"
            ></div>
          </div>
          <span class="w-20 shrink-0 text-right text-[11px] font-mono text-text-muted">
            {{ c.mastered }} / {{ c.filled }} · {{ c.pct }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
