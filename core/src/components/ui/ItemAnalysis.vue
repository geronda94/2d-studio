<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import ParetoChart from './ParetoChart.vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  items: { type: Array, default: () => [] },
  flags: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ItemAnalysis')
const relativeTime = inject('relativeTime', ref(0))

const bars = computed(() =>
  [...props.items]
    .sort((a, b) => (Number(b.pct) || 0) - (Number(a.pct) || 0))
    .map((it) => ({ label: '№' + it.no, value: Number(it.pct) || 0 })),
)

// Порядок карточек = порядок на диаграмме (по убыванию %): подписи идут последовательно.
const chartOrder = computed(() =>
  [...props.items].sort((a, b) => (Number(b.pct) || 0) - (Number(a.pct) || 0)),
)

const flagFor = (it) => props.flags.find((f) => String(f.no) === String(it.no))

const discColor = (v) => {
  const n = Number(v)
  if (n >= 0.3) return getHexColor('var(--color-success)')
  if (n >= 0.15) return getHexColor('var(--color-warning)')
  return getHexColor('var(--color-danger)')
}

const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)

const avgPct = computed(() => {
  if (!props.items.length) return 0
  return Math.round(props.items.reduce((s, it) => s + (Number(it.pct) || 0), 0) / props.items.length)
})

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * 140) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}

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
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div
      v-if="!items.length"
      class="relative w-full flex-1 min-h-[320px] flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 flex flex-col gap-2 md:gap-3">
      <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-text-muted shrink-0">
        <span class="uppercase tracking-widest">Анализ заданий · % верных и дискриминация</span>
        <span>Средний результат: {{ avgPct }}% · флагов: {{ flags.length }}</span>
      </div>

      <ParetoChart
        :mobile="mobile"
        :variant="variant"
        :items="bars"
        :threshold="80"
        value_suffix="%"
        value_label="% верных"
        source_note="% верных ответов · правило 80/20"
        :show_value_axis="false"
        :anchor_labels="true"
      />

      <div class="grid grid-cols-3 lg:grid-cols-5 gap-2 md:gap-3">
        <div class="contents">
          <div
            v-for="(it, i) in chartOrder"
            :key="it.no + '-' + i"
            class="min-w-0 flex flex-col gap-1 md:gap-2 p-2 md:p-3"
            :style="[itemStyle, reveal(i)]"
          >
            <div class="flex items-center justify-between gap-2">
              <span
                class="px-2 py-0.5 rounded text-[11px] font-mono font-bold"
                :style="{ background: getColorAlpha(accent(i), 0.16), color: accent(i) }"
              >№{{ it.no }}</span>
              <span class="text-xs font-mono text-text-secondary">{{ it.pct }}%</span>
            </div>

            <div class="flex items-center justify-between text-[11px]">
              <span class="text-text-muted">Сложность</span>
              <span class="font-mono text-text-secondary">{{ it.difficulty }}</span>
            </div>
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-text-muted">Дискриминация</span>
              <span class="font-mono font-bold" :style="{ color: discColor(it.discrimination) }">{{ it.discrimination }}</span>
            </div>

            <div class="flex flex-wrap gap-1 pt-1" :style="{ borderTop: '1px solid var(--item-border)' }">
              <span
                v-for="(d, di) in (it.distractors || [])"
                :key="'d' + di"
                class="px-1.5 py-0.5 rounded text-[10px] font-mono"
                :style="{ background: getColorAlpha(accent(i), 0.10), color: 'var(--text-muted)' }"
              >{{ d.label }} · {{ d.pct }}%</span>
            </div>

            <div
              v-if="flagFor(it)"
              class="flex items-start gap-1.5 text-[10px] leading-snug"
              :style="{ color: getHexColor('var(--color-warning)') }"
            >
              <Icon icon="lucide:flag" class="w-3 h-3 mt-0.5 shrink-0" />
              <span>{{ flagFor(it).text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
