<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  items: { type: Array, default: () => [] },
  threshold: { type: Number, default: 80 },
  value_suffix: { type: String, default: '' },
  bar_color: { type: String, default: 'var(--color-secondary)' },
  cumulative_color: { type: String, default: 'var(--color-warning)' },
  value_label: { type: String, default: '' },
  source_note: { type: String, default: '' },
  // opt-in: скрыть левую числовую ось (когда столбцы — проценты, а справа уже % шкала)
  show_value_axis: { type: Boolean, default: true },
  // opt-in: держать подпись значения у вершины столбца, а не в верхней полосе графика,
  // чтобы кумулятивная линия не перечёркивала короткие подписи.
  anchor_labels: { type: Boolean, default: false },
  // opt-in: переносить длинные подписи категорий вместо обрезки «…» (для узких панелей/мобилы).
  wrap_labels: { type: Boolean, default: false },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ParetoChart')
const relativeTime = inject('relativeTime', ref(0))

const sorted = computed(() =>
  [...(props.items || [])]
    .map((it) => ({ label: it.label, value: Number(it.value) || 0 }))
    .sort((a, b) => b.value - a.value),
)

const total = computed(() => sorted.value.reduce((s, it) => s + it.value, 0) || 1)
const maxValue = computed(() => Math.max(1, ...sorted.value.map((it) => it.value)))

const cumulative = computed(() => {
  let acc = 0
  return sorted.value.map((it) => {
    acc += it.value
    return (acc / total.value) * 100
  })
})

const vitalIndex = computed(() => {
  const idx = cumulative.value.findIndex((c) => c >= props.threshold)
  return idx === -1 ? sorted.value.length - 1 : idx
})

// Кумулятивная линия в SVG поверх столбцов (координаты в %).
const linePoints = computed(() =>
  cumulative.value
    .map((c, i) => `${(((i + 0.5) / Math.max(1, sorted.value.length)) * 100).toFixed(2)},${(100 - c).toFixed(2)}`)
    .join(' '),
)
const lineDraw = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - 200) / (motion.value.appear_ms * 1.6)))
  return { opacity: p.toFixed(3) }
})

const barReveal = (i) => {
  const t = i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return (1 - Math.pow(1 - p, 3)).toFixed(4)
}
const isVital = (i) => i <= vitalIndex.value
const barHeight = (it) => `${((it.value / maxValue.value) * 100).toFixed(2)}%`

// Левая числовая ось: 0, 1/2 и max — круглые значения.
const leftTicks = computed(() => {
  const max = maxValue.value
  return [max, max / 2, 0].map((v) => Math.round(v))
})

// Правая % ось: 0 / 25 / 50 / 75 / 100 (линейная).
const pctTicks = [100, 75, 50, 25, 0]
const compact = computed(() => props.density === 'compact' || props.mobile)
const tickTop = (i, len) => `${(i / Math.max(1, len - 1) * 100).toFixed(2)}%`
// Полоса значений сверху занимает 20px; сетка/оси живут в той же зоне, что и столбцы.
// В режиме anchor_labels подпись стоит у вершины столбца, поэтому оставляем небольшой
// верхний отступ — иначе подпись самого высокого столбца обрезается.
const plotZone = computed(() => (props.anchor_labels ? 'top-4 bottom-0' : 'top-5 bottom-0'))
const padL = computed(() => (props.show_value_axis ? 'pl-12 md:pl-[68px]' : 'pl-0'))
const padR = 'pr-11 md:pr-14'
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!sorted.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="relative flex-1 min-h-0 flex flex-col">
      <!-- Значения столбцов (отдельная полоса над графиком — линия их не задевает) -->
      <div v-if="!anchor_labels" class="flex gap-1.5 md:gap-3 h-5 shrink-0" :class="[padL, padR]">
        <span
          v-for="(it, i) in sorted"
          :key="'v' + i"
          class="flex-1 text-center text-[9px] md:text-[10px] font-mono whitespace-nowrap"
          :style="{ opacity: barReveal(i), color: 'var(--text-secondary)' }"
        >{{ Math.round(it.value) }}{{ value_suffix }}</span>
      </div>

      <!-- Оси + полотно (общая высота → подписи осей совпадают с сеткой) -->
      <div class="flex-1 min-h-0 flex gap-2 md:gap-3">
        <!-- Левая ось (значения) -->
        <div v-if="show_value_axis" class="relative w-10 md:w-14 shrink-0 text-[9px] md:text-[10px] font-mono text-text-muted">
          <div class="absolute inset-x-0" :class="plotZone">
            <span
              v-for="(t, i) in leftTicks"
              :key="'yl' + i"
              class="absolute right-1 -translate-y-1/2"
              :style="{ top: tickTop(i, leftTicks.length) }"
            >{{ t }}</span>
          </div>
        </div>

        <!-- Полотно -->
        <div class="relative flex-1 min-w-0">
          <div class="absolute left-0 right-0" :class="plotZone">
            <!-- горизонтальная сетка -->
            <div class="absolute inset-0 pointer-events-none">
              <div
                v-for="n in 5"
                :key="'grid' + n"
                class="absolute left-0 right-0 border-t"
                :style="{ top: ((n - 1) / 4 * 100) + '%', borderColor: 'var(--item-border)', opacity: 0.5 }"
              ></div>
            </div>

            <!-- столбцы -->
            <div class="absolute inset-0 flex items-end gap-1.5 md:gap-3">
              <div v-for="(it, i) in sorted" :key="it.label + i" class="relative flex-1 h-full min-w-0">
                <div
                  class="absolute bottom-0 left-[12%] right-[12%] origin-bottom"
                  :style="{
                    height: barHeight(it),
                    transform: `scaleY(${barReveal(i)})`,
                    background: isVital(i) ? getHexColor(bar_color) : getColorAlpha(bar_color, 0.35),
                    borderRadius: 'var(--item-radius)',
                  }"
                ></div>
                <span
                  v-if="anchor_labels"
                  class="absolute inset-x-0 text-center text-[9px] md:text-[10px] font-mono whitespace-nowrap pointer-events-none"
                  :style="{ bottom: `calc(${barHeight(it)} + 3px)`, opacity: barReveal(i), color: 'var(--text-secondary)' }"
                >{{ Math.round(it.value) }}{{ value_suffix }}</span>
              </div>
            </div>

            <!-- кумулятивная линия -->
            <svg class="absolute inset-0 w-full h-full pointer-events-none z-10" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline
                :points="linePoints"
                fill="none"
                :stroke="getHexColor(cumulative_color)"
                stroke-width="2"
                vector-effect="non-scaling-stroke"
                :style="lineDraw"
              />
            </svg>
          </div>
        </div>

        <!-- Правая % ось -->
        <div class="relative w-9 md:w-11 shrink-0 text-[9px] md:text-[10px] font-mono text-text-muted">
          <div class="absolute inset-x-0" :class="plotZone">
            <span
              v-for="(t, i) in pctTicks"
              :key="'pr' + t"
              class="absolute left-1 -translate-y-1/2"
              :style="{ top: tickTop(i, pctTicks.length) }"
            >{{ t }}%</span>
          </div>
        </div>
      </div>

      <!-- подписи категорий -->
      <div class="shrink-0 flex gap-1.5 md:gap-3" :class="[padL, padR, wrap_labels ? 'min-h-6 items-start pt-1' : 'h-6']">
        <span
          v-for="(it, i) in sorted"
          :key="'l' + i"
          class="flex-1 text-center"
          :class="[compact ? 'text-[9px]' : 'text-[11px]', wrap_labels ? 'leading-tight break-words' : 'truncate']"
          :style="{ color: isVital(i) ? getHexColor(bar_color) : 'var(--text-muted)' }"
        >{{ it.label }}</span>
      </div>

      <div v-if="sorted.length" class="mt-3 flex items-center justify-between text-[11px] font-mono text-text-muted shrink-0">
        <span>Витальное меньшинство: {{ vitalIndex + 1 }} из {{ sorted.length }} → {{ cumulative[vitalIndex].toFixed(0) }}%</span>
        <span v-if="source_note" class="opacity-80">{{ source_note }}</span>
      </div>
    </div>
  </div>
</template>
