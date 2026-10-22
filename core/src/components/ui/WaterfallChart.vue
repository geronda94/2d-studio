<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  start_label: { type: String, default: 'Было' },
  start_value: { type: Number, default: 0 },
  steps: { type: Array, default: () => [] },
  end_label: { type: String, default: 'Стало' },
  value_prefix: { type: String, default: '' },
  value_suffix: { type: String, default: '' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'WaterfallChart')
const relativeTime = inject('relativeTime', ref(0))

// Полоса: {label, kind:'total'|'pos'|'neg', from, to, value}
const bars = computed(() => {
  const out = []
  let running = Number(props.start_value) || 0
  out.push({ label: props.start_label, kind: 'total', from: 0, to: running, value: running })
  for (const s of props.steps || []) {
    const delta = Number(s.delta) || 0
    const next = running + delta
    out.push({ label: s.label, kind: s.kind || (delta >= 0 ? 'pos' : 'neg'), from: running, to: next, value: delta })
    running = next
  }
  out.push({ label: props.end_label, kind: 'total', from: 0, to: running, value: running })
  return out
})

const bounds = computed(() => {
  const vals = [0, ...bars.value.flatMap((b) => [b.from, b.to])]
  const rawMin = Math.min(...vals)
  const rawMax = Math.max(...vals)
  const min = Math.min(0, rawMin)
  const span = Math.max(1, rawMax - min)
  return { min, max: rawMax + span * 0.14 }
})

const toPct = (v) => ((v - bounds.value.min) / (bounds.value.max - bounds.value.min)) * 100

const barGeom = (b) => {
  const bottom = toPct(Math.min(b.from, b.to))
  const top = toPct(Math.max(b.from, b.to))
  const height = Math.max(1.5, top - bottom)
  return { bottom: `${bottom}%`, height: `${height}%` }
}

// Подпись крепится к ВЕРХНЕМУ краю полосы (top% считается от верха полотна,
// поэтому 100 - toPct). Итоговые полосы держат значение внутри, дельты — над полосой.
const labelTop = (b) => {
  const topPct = 100 - toPct(Math.max(b.from, b.to))
  if (b.kind === 'total') {
    const h = toPct(Math.max(b.from, b.to)) - toPct(Math.min(b.from, b.to))
    // Нулевая/почти нулевая итоговая полоса: подпись уходит под базлайн и
    // наезжает на подпись категории — поднимаем её над базлайном.
    return h < 6 ? `calc(${topPct.toFixed(2)}% - 18px)` : `calc(${topPct.toFixed(2)}% + 8px)`
  }
  return `calc(${topPct.toFixed(2)}% - 18px)`
}

const barColor = (b) =>
  b.kind === 'pos' ? 'var(--color-success)' : b.kind === 'neg' ? 'var(--color-danger)' : 'var(--color-secondary)'

const revealStep = computed(() => {
  const n = (bars.value?.length || 1) - 1
  return n > 0 ? Math.min(motion.value.stagger_ms, 4000 / n) : 0
})
const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * revealStep.value) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const ticks = computed(() => {
  const { min, max } = bounds.value
  const mid = min + (max - min) / 2
  return [max, mid, min].map((v) => Math.round(v))
})

const fmt = (v) => `${props.value_prefix}${Math.round(v).toLocaleString('ru-RU')}${props.value_suffix}`
const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars }"
  >
    <div v-if="!bars.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex-1 min-h-0 flex gap-2 md:gap-3 pt-3">
        <!-- Ось значений -->
        <div class="w-10 md:w-14 shrink-0 flex flex-col justify-between items-end pr-1 text-[9px] md:text-[10px] font-mono text-text-muted">
          <span v-for="(t, i) in ticks" :key="'y' + i" class="-translate-y-1/2">{{ t }}</span>
        </div>

        <!-- Полотно -->
        <div class="flex-1 min-w-0 flex flex-col">
          <div class="relative flex-1 min-h-0">
            <!-- сетка -->
            <div class="absolute inset-0 pointer-events-none">
              <div v-for="n in 3" :key="'grid' + n" class="absolute left-0 right-0 border-t"
                   :style="{ top: ((n - 1) / 2 * 100) + '%', borderColor: 'var(--item-border)', opacity: 0.45 }"></div>
            </div>

            <!-- коннекторы -->
            <svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
              <line
                v-for="(b, i) in bars.slice(0, -1)"
                :key="'c' + i"
                :x1="((i + 0.5) / bars.length) * 100"
                :y1="100 - toPct(b.to)"
                :x2="((i + 1.5) / bars.length) * 100"
                :y2="100 - toPct(b.to)"
                stroke="var(--text-muted)"
                stroke-width="1"
                stroke-dasharray="3 3"
                vector-effect="non-scaling-stroke"
                :style="{ opacity: 0.5 }"
              />
            </svg>

            <div class="absolute inset-0 flex items-stretch gap-1.5 md:gap-3">
              <div v-for="(b, i) in bars" :key="b.label + i" class="flex-1 h-full relative min-w-0">
                <div
                  class="absolute left-0 right-0 rounded-[var(--item-radius)]"
                  :style="[
                    barGeom(b),
                    { background: b.kind === 'total' ? getHexColor(barColor(b)) : getColorAlpha(barColor(b), 0.75) },
                    reveal(i),
                  ]"
                ></div>
                <span
                  class="absolute left-0 right-0 text-center text-[10px] md:text-xs font-mono"
                  :style="[{ top: labelTop(b) }, reveal(i)]"
                  :class="b.kind === 'neg' ? 'text-color-danger' : 'text-text-primary'"
                >{{ b.kind === 'total' ? fmt(b.to) : (b.value >= 0 ? '+' : '−') + Math.abs(b.value).toLocaleString('ru-RU') }}</span>
              </div>
            </div>

            <!-- базлайн -->
            <div class="absolute left-0 right-0 bottom-0 border-t" :style="{ borderColor: 'var(--text-muted)', opacity: 0.7 }"></div>
          </div>

          <!-- подписи категорий -->
          <div class="h-6 flex gap-1.5 md:gap-3 shrink-0">
            <span
              v-for="(b, i) in bars"
              :key="'l' + i"
              class="flex-1 min-w-0 text-center truncate"
              :class="compact ? 'text-[9px]' : 'text-[11px]'"
              :style="{ color: b.kind === 'total' ? 'var(--text-secondary)' : 'var(--text-muted)' }"
            >{{ b.label }}</span>
          </div>
        </div>

        <!-- правая пустая ось для симметрии -->
        <div class="w-0 md:w-2 shrink-0"></div>
      </div>

      <div v-if="source_note" class="shrink-0 mt-2 text-[11px] font-mono text-text-muted opacity-80">{{ source_note }}</div>
    </template>
  </div>
</template>
