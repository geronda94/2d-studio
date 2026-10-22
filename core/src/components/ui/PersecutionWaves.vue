<script setup>
// PersecutionWaves — волны гонений на христиан: период, масштаб, место.
// Собственная раскладка (без внешнего TimelineEras): тянется на всю высоту
// кадра — круги сверху, карточки занимают остаток, без пустой полосы.
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  waves: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'PersecutionWaves')
const relativeTime = inject('relativeTime', ref(0))

const times = computed(() => (props.waves || []).map((w, i) => w.start_time ?? i * motion.value.stagger_ms))

const activeIndex = computed(() => {
  let idx = 0
  times.value.forEach((t, i) => { if (relativeTime.value >= t) idx = i })
  return idx
})

const progress = (i) => {
  const t = times.value[i] ?? 0
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const progressScale = computed(() => {
  const n = props.waves.length
  if (n <= 1) return 1
  let filled = 0
  props.waves.forEach((w, idx) => {
    const e = progress(idx)
    if (e >= 1) filled = idx
    else if (e > 0 && filled < idx) filled = idx - 1 + e
  })
  return Math.min(1, Math.max(0, filled / (n - 1)))
})

const accent = (w, idx) => getHexColor(w.color || `var(--item-accent-${(idx % 4) + 1})`)
const lineInset = computed(() => {
  const n = (props.waves || []).length
  if (n <= 1) return '50%'
  return `${((0.5 / n) * 100).toFixed(2)}%`
})

const circleStyle = (w, idx) => {
  const e = progress(idx)
  const active = idx <= activeIndex.value
  return {
    opacity: e.toFixed(4),
    transform: `translateY(${((1 - e) * 18).toFixed(2)}px) scale(${active && !props.mobile ? 1.05 : 1})`,
    background: 'var(--item-bg)',
    backdropFilter: 'var(--item-backdrop)',
    WebkitBackdropFilter: 'var(--item-backdrop)',
    border: '2px solid ' + (active ? accent(w, idx) : 'var(--item-border)'),
    color: active ? accent(w, idx) : 'var(--text-muted)',
    boxShadow: active ? `0 0 24px ${getColorAlpha(accent(w, idx), 0.35)}` : 'none',
  }
}
const cardStyle = (w, idx) => {
  const e = progress(idx)
  return {
    opacity: e.toFixed(4),
    transform: `translateY(${((1 - e) * 18).toFixed(2)}px)`,
    background: 'var(--item-bg)',
    backdropFilter: 'var(--item-backdrop)',
    WebkitBackdropFilter: 'var(--item-backdrop)',
    borderRadius: 'var(--item-radius)',
    boxShadow: 'var(--item-shadow)',
    padding: 'var(--item-padding)',
    borderWidth: 'var(--item-border-width)',
    borderStyle: 'var(--item-border-style)',
    borderColor: idx === activeIndex.value ? getColorAlpha(accent(w, idx), 0.55) : 'var(--item-border)',
  }
}
const sourceReveal = computed(() => progress(Math.max(0, (props.waves?.length || 1) - 1)))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!waves.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <!-- DESKTOP: одна строка, круги сверху, карточки на всю оставшуюся высоту -->
      <div v-if="!mobile" class="relative flex-1 min-h-0">
        <!-- Линия связи (базовая + прогресс) -->
        <div class="absolute h-[2px]" :style="{ left: lineInset, right: lineInset, top: '48px', background: 'var(--item-border)' }"></div>
        <div class="absolute h-[2px] origin-left" :style="{ left: lineInset, right: lineInset, top: '48px', background: getHexColor('var(--color-secondary)'), transform: `scaleX(${progressScale})`, willChange: 'transform' }"></div>

        <div class="grid h-full gap-3 md:gap-4" :style="{ gridTemplateColumns: `repeat(${waves.length}, minmax(0, 1fr))` }">
          <div v-for="(w, idx) in waves" :key="w.id ?? idx" class="flex flex-col items-center h-full text-center px-1">
            <div
              class="w-20 h-20 md:w-24 md:h-24 rounded-full flex items-center justify-center shrink-0 z-10"
              :style="circleStyle(w, idx)"
            >
              <Icon :icon="w.icon || 'heroicons:clock'" class="w-8 h-8 md:w-9 md:h-9" />
            </div>

            <p class="font-mono text-xs md:text-sm font-bold mt-3 mb-3 shrink-0" :style="{ color: accent(w, idx) }">{{ w.period }}</p>

            <div
              class="w-full flex-1 min-h-0 flex flex-col items-center justify-center gap-1.5 px-3 py-3"
              :style="cardStyle(w, idx)"
            >
              <h4 class="font-heading font-bold text-text-primary text-base leading-tight">{{ w.scope }}</h4>
              <p v-if="w.place && !mobile" class="text-text-secondary text-xs leading-snug">{{ w.place }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- MOBILE: вертикальный список — круг слева, карточка справа -->
      <div v-else class="flex flex-col gap-2 min-h-0 flex-1">
        <div
          v-for="(w, idx) in waves"
          :key="'m' + (w.id ?? idx)"
          class="flex items-stretch gap-2.5 min-h-0 flex-1"
        >
          <div class="flex flex-col items-center shrink-0">
            <div class="w-11 h-11 rounded-full flex items-center justify-center" :style="circleStyle(w, idx)">
              <Icon :icon="w.icon || 'heroicons:clock'" class="w-5 h-5" />
            </div>
            <div v-if="idx < waves.length - 1" class="flex-1 w-[2px] my-1" :style="{ background: 'var(--item-border)' }"></div>
          </div>
          <div
            class="flex-1 min-h-0 flex flex-col justify-center gap-0.5 px-3 py-2"
            :style="cardStyle(w, idx)"
          >
            <span class="font-mono text-[11px] font-bold" :style="{ color: accent(w, idx) }">{{ w.period }}</span>
            <h4 class="font-heading font-bold text-text-primary text-sm leading-tight">{{ w.scope }}</h4>
            <p v-if="w.place" class="text-text-secondary text-[11px] leading-snug">{{ w.place }}</p>
          </div>
        </div>
      </div>

      <div
        v-if="source_note"
        class="shrink-0 mt-3 text-center text-[11px] font-mono text-text-secondary"
        :style="{ opacity: Math.max(0.55, sourceReveal) }"
      >{{ source_note }}</div>
    </template>
  </div>
</template>
