<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  phases: { type: Array, default: () => [] },
})

const { itemVars, line, motion } = useVariant(computed(() => props.variant), 'LessonArc')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)
const n = computed(() => props.phases.length || 1)
const totalMinutes = computed(() => props.phases.reduce((s, p) => s + (Number(p.minutes) || 0), 0))

const xPct = (i) => ((i + 0.5) / n.value) * 100
const yPct = (i) => {
  const t = (i + 0.5) / n.value
  return 50 + (0.5 - Math.sin(Math.PI * t)) * 60
}
const arcPoints = computed(() =>
  props.phases.map((_, i) => `${xPct(i).toFixed(2)},${yPct(i).toFixed(2)}`).join(' '),
)

const reveal = (p, i) => {
  const t = p.start_time ?? i * motion.value.stagger_ms
  const prog = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - prog, 3)
}
const dotStyle = (p, i) => {
  const e = reveal(p, i)
  return { opacity: e.toFixed(4), transform: `scale(${(0.6 + 0.4 * e).toFixed(3)})` }
}
const cardStyle = (p, i) => {
  const e = reveal(p, i)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
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
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col justify-center" :style="{ ...itemVars }">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-text-muted shrink-0">
      <span class="uppercase tracking-widest">Ход урока · фазы и время</span>
      <span v-if="totalMinutes">Всего: {{ totalMinutes }} мин</span>
    </div>

    <div
      v-if="!phases.length"
      class="relative w-full flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 flex flex-col">
      <!-- DESKTOP -->
      <div v-if="!mobile" class="flex flex-col gap-4 h-full">
        <div class="relative w-full shrink-0" style="height: 120px">
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline
              :points="arcPoints"
              fill="none"
              :stroke="line.color"
              :stroke-width="line.width"
              :stroke-dasharray="line.dash"
              vector-effect="non-scaling-stroke"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          <div
            v-for="(p, i) in phases"
            :key="'d' + i"
            class="absolute"
            :style="{ left: xPct(i) + '%', top: yPct(i) + '%', transform: 'translate(-50%, -50%)' }"
          >
            <span
              class="w-11 h-11 rounded-full flex items-center justify-center"
              :style="[{ background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', border: '2px solid ' + accent(i), color: accent(i) }, dotStyle(p, i)]"
            >
              <Icon :icon="p.icon || 'lucide:circle-dot'" class="w-5 h-5" />
            </span>
          </div>
        </div>

        <div class="grid gap-3 flex-1 min-h-0" :style="{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }">
          <div
            v-for="(p, i) in phases"
            :key="'c' + i"
            class="flex flex-col gap-2 p-4 justify-center"
            :style="[itemStyle, cardStyle(p, i)]"
          >
            <div class="flex flex-col items-start gap-1.5 min-w-0 w-full">
              <p class="font-heading font-bold text-base leading-tight break-words" :style="{ color: accent(i) }">{{ p.name }}</p>
              <span
                class="text-[10px] font-mono px-1.5 py-0.5 rounded-full shrink-0"
                :style="{ background: getColorAlpha(accent(i), 0.14), color: accent(i) }"
              >{{ p.minutes }} мин</span>
            </div>
            <p class="text-sm text-text-secondary leading-snug">{{ p.activity }}</p>
          </div>
        </div>
      </div>

      <!-- MOBILE -->
      <div v-else class="relative pl-2">
        <div class="absolute left-[23px] top-3 bottom-3 w-[2px]" :style="{ background: 'var(--item-border)' }"></div>
        <div
          v-for="(p, i) in phases"
          :key="'m' + i"
          class="relative flex gap-3 pb-4 last:pb-0"
          :style="cardStyle(p, i)"
        >
          <span
            class="relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0"
            :style="{ background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', border: '2px solid ' + accent(i), color: accent(i) }"
          >
            <Icon :icon="p.icon || 'lucide:circle-dot'" class="w-5 h-5" />
          </span>
          <div class="flex-1 p-3" :style="itemStyle">
            <div class="flex items-start justify-between gap-2 min-w-0 w-full">
              <p class="font-heading font-bold text-sm min-w-0 break-words" :style="{ color: accent(i) }">{{ p.name }}</p>
              <span
                class="text-[10px] font-mono px-1.5 py-0.5 rounded-full shrink-0"
                :style="{ background: getColorAlpha(accent(i), 0.14), color: accent(i) }"
              >{{ p.minutes }} мин</span>
            </div>
            <p class="text-xs text-text-secondary leading-snug mt-1">{{ p.activity }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
