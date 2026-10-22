<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import HeatmapMatrix from './HeatmapMatrix.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  rows: { type: Array, default: () => [] },
  cols: { type: Array, default: () => [] },
  cells: { type: Array, default: () => [] },
  states: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'HandoverMatrix')
const relativeTime = inject('relativeTime', ref(0))

const stateColor = (code) => {
  const idx = (String(code || '').charCodeAt(0) || 0) % 4
  return `var(--item-accent-${idx + 1})`
}

const flat = computed(() => (props.cells || []).flat().filter((c) => String(c ?? '').trim() !== ''))
const total = computed(() => flat.value.length || 1)
const doneCode = computed(() => {
  const done = (props.states || []).find((s) => /сдано|готово|done/i.test(s.label || ''))
  return done ? done.code : (props.states?.[props.states.length - 1]?.code ?? '')
})
const done = computed(() => flat.value.filter((c) => String(c) === doneCode.value).length)
const progress = computed(() => Math.round((done.value / total.value) * 100))

const stateCounts = computed(() =>
  (props.states || []).map((s) => ({ ...s, count: flat.value.filter((c) => String(c) === s.code).length })),
)

const issuesCount = computed(() => {
  const issue = (props.states || []).find((s) => /замеч|issue|snag/i.test(s.label || ''))
  return issue ? flat.value.filter((c) => String(c) === issue.code).length : 0
})

const rowStats = computed(() =>
  (props.rows || []).map((label, ri) => {
    const row = (props.cells || [])[ri] || []
    const filled = row.filter((c) => String(c ?? '').trim() !== '').length || 1
    const ready = row.filter((c) => String(c) === doneCode.value).length
    return { label, ready, filled, pct: Math.round((ready / filled) * 100) }
  }),
)

const legendReveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col gap-3" :style="{ ...itemVars }">
    <div v-if="!rows.length || !cols.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-[10px] uppercase tracking-widest font-mono text-text-muted">Матрица сдачи</span>
        <div class="h-2 flex-1 min-w-[160px] overflow-hidden rounded-full" :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)' }">
          <div
            class="h-full origin-left"
            :style="{
              width: progress + '%',
              background: getHexColor('var(--color-success)'),
              transform: `scaleX(${Math.min(1, relativeTime / motion.count_ms).toFixed(3)})`,
            }"
          ></div>
        </div>
        <span class="text-[11px] font-mono text-text-muted">
          Сдано <span class="text-sm font-bold" :style="{ color: getHexColor('var(--color-success)') }">{{ progress }}%</span>
          · {{ done }} из {{ total }}
        </span>
        <span v-if="issuesCount" class="flex items-center gap-1.5 text-[11px] font-mono text-text-muted">
          <span class="w-2 h-2 rounded-full" :style="{ background: getHexColor('var(--color-warning)') }"></span>
          замечаний: {{ issuesCount }}
        </span>
      </div>

      <div class="flex-1 min-h-0 overflow-hidden">
        <HeatmapMatrix
          :variant="variant"
          :mobile="mobile"
          density="compact"
          :rows="rows"
          :cols="cols"
          :cells="cells"
          scale="custom"
        />
      </div>

      <div class="flex flex-wrap gap-3">
        <span
          v-for="(s, i) in stateCounts"
          :key="s.code + i"
          class="flex items-center gap-1.5 text-[11px] text-text-secondary"
          :style="legendReveal(i)"
        >
          <span
            class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]"
            :style="{ background: getColorAlpha(stateColor(s.code), 0.5), border: '1px solid ' + getHexColor(stateColor(s.code)) }"
          ></span>
          {{ s.label }} · {{ s.count }}
        </span>
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-[10px] uppercase tracking-widest font-mono text-text-muted">Готовность по этажам</span>
        <div class="flex flex-col gap-1.5">
          <div v-for="(r, i) in rowStats" :key="'rs' + i" class="flex items-center gap-2">
            <span class="w-24 shrink-0 text-[11px] text-text-secondary truncate">{{ r.label }}</span>
            <span class="flex-1 h-2 overflow-hidden rounded-full" :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)' }">
              <span
                class="block h-full origin-left"
                :style="{
                  width: r.pct + '%',
                  background: getHexColor('var(--color-success)'),
                  transform: `scaleX(${Math.min(1, relativeTime / motion.count_ms).toFixed(3)})`,
                }"
              ></span>
            </span>
            <span class="w-16 shrink-0 text-right text-[10px] font-mono text-text-muted">{{ r.ready }}/{{ r.filled }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
