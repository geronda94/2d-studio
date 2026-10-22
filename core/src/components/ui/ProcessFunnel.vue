<script setup lang="ts">
import { getColorAlpha } from '../../utils/colors'
import { ref, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = withDefaults(defineProps<{
  steps?: Array<{
    label: string
    count: number
    icon: string
    start_time?: number
    color?: string
  }>
  layout?: 'horizontal' | 'vertical'
  mobile?: boolean
  variant?: string
  show_conversion?: boolean
}>(), {
  steps: () => [],
  layout: 'horizontal',
  mobile: false,
  show_conversion: true
})

const relativeTime = inject('relativeTime', ref(0))

const { itemVars } = useVariant(computed(() => props.variant), 'ProcessFunnel')

const isVisible = (idx: number) => {
  const t = props.steps[idx]?.start_time ?? (idx * 1000)
  return relativeTime.value >= t
}

const formatNumber = (num: number) => {
  if (num === undefined || num === null) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K'
  return num.toString()
}

// Конверсия текущей ступени относительно предыдущей.
const getConversion = (idx: number) => {
  if (idx <= 0) return null
  const prev = props.steps[idx - 1]?.count
  const curr = props.steps[idx]?.count
  if (!prev || !curr || prev === 0) return null
  return Math.round((curr / prev) * 100)
}

const getStepColor = (step: any, idx: number) => {
  return step?.color || `var(--chart-${(idx % 6) + 1})`
}

const stepCount = computed(() => (props.steps || []).length || 1)

// Насколько сужается воронка: ширина самой узкой грани (% от высоты кадра).
const MIN_EDGE = 38

// Высота вертикальной грани k (0..n): каждая следующая ступень уже предыдущей.
const edgeHeight = (k: number) => 100 - (k * (100 - MIN_EDGE)) / stepCount.value

// Трапеция ступени: левая грань выше правой → реальная горизонтальная воронка.
const clipFor = (idx: number) => {
  const hL = edgeHeight(idx)
  const hR = edgeHeight(idx + 1)
  const inset = 0.5
  const topL = ((100 - hL) / 2).toFixed(2)
  const topR = ((100 - hR) / 2).toFixed(2)
  const botL = ((100 + hL) / 2).toFixed(2)
  const botR = ((100 + hR) / 2).toFixed(2)
  return `polygon(${inset}% ${topL}%, ${100 - inset}% ${topR}%, ${100 - inset}% ${botR}%, ${inset}% ${botL}%)`
}

const stageStyle = (step: any, idx: number) => {
  const c = getStepColor(step, idx)
  return {
    background: `linear-gradient(160deg, ${getColorAlpha(c, 0.34)}, ${getColorAlpha(c, 0.06)}), var(--item-bg)`,
    backdropFilter: 'var(--item-backdrop)',
    clipPath: clipFor(idx),
  }
}

const revealStyle = (idx: number) => ({
  opacity: isVisible(idx) ? 1 : 0,
  transform: isVisible(idx) ? 'translateY(0) scale(1)' : 'translateY(18px) scale(0.97)',
  transition: 'opacity 500ms ease, transform 500ms ease',
})

// Полоса объёма в вертикальной (мобильной) раскладке.
const barRatio = (idx: number) => {
  const max = Math.max(1, ...(props.steps || []).map((s: any) => Number(s.count) || 0))
  const c = Number(props.steps[idx]?.count) || 0
  return Math.max(0.08, c / max).toFixed(3)
}
</script>

<template>
  <div class="w-full h-full flex items-center justify-center" :style="{ ...itemVars }">

    <!-- ВЕРТИКАЛЬНАЯ ВОРОНКА (мобильный / layout=vertical) -->
    <div v-if="mobile || layout === 'vertical'" class="w-full max-w-md h-full flex flex-col justify-evenly gap-3 px-1">
      <div
        v-for="(step, idx) in steps"
        :key="'v' + idx"
        class="flex items-center gap-3"
        :style="revealStyle(idx)"
      >
        <div
          class="w-11 h-11 shrink-0 flex items-center justify-center"
          :style="{
            background: getColorAlpha(getStepColor(step, idx), 0.16),
            borderRadius: 'var(--item-radius)',
            border: '1px solid ' + getColorAlpha(getStepColor(step, idx), 0.4),
          }"
        >
          <Icon :icon="step.icon || 'heroicons:check'" class="w-6 h-6" :style="{ color: getStepColor(step, idx) }" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-bold font-heading text-text-primary leading-none">{{ formatNumber(step.count) }}</span>
            <span class="text-[10px] font-medium uppercase tracking-widest text-text-secondary truncate">{{ step.label }}</span>
          </div>
          <div class="mt-1.5 h-1.5 w-full rounded-full overflow-hidden" :style="{ background: getColorAlpha(getStepColor(step, idx), 0.14) }">
            <div
              class="h-full w-full origin-left rounded-full"
              :style="{ background: getStepColor(step, idx), transform: `scaleX(${barRatio(idx)})` }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ГОРИЗОНТАЛЬНАЯ ВОРОНКА (desktop) -->
    <div v-else class="w-full h-full flex flex-col">
      <div class="flex-1 min-h-0 w-full flex items-stretch">
        <div
          v-for="(step, idx) in steps"
          :key="'h' + idx"
          class="relative flex-1 min-w-0 flex items-center justify-center"
          :style="[stageStyle(step, idx), revealStyle(idx)]"
        >
          <div class="flex flex-col items-center justify-center gap-1 px-2 text-center">
            <Icon :icon="step.icon || 'heroicons:check'" class="w-7 h-7" :style="{ color: getStepColor(step, idx) }" />
            <span class="font-heading font-bold text-text-primary leading-none text-3xl">{{ formatNumber(step.count) }}</span>
            <span class="text-[11px] font-medium uppercase tracking-[0.2em] text-text-secondary leading-tight">{{ step.label }}</span>
          </div>
        </div>
      </div>

      <!-- Конверсия между ступенями -->
      <div v-if="show_conversion" class="shrink-0 flex w-full pt-3">
        <div v-for="(step, idx) in steps" :key="'c' + idx" class="flex-1 flex justify-center">
          <div
            v-if="getConversion(idx) !== null"
            class="px-3 py-1 border font-sans text-xs font-bold flex items-center gap-1"
            :style="{
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              boxShadow: 'var(--item-shadow)',
              borderRadius: 'var(--item-radius)',
              borderColor: getColorAlpha(getStepColor(step, idx), 0.5),
              color: getStepColor(step, idx),
              opacity: isVisible(idx) ? 1 : 0,
              transition: 'opacity 400ms ease',
            }"
          >
            <Icon icon="heroicons:arrow-trending-down" class="w-3 h-3 opacity-70" />
            {{ getConversion(idx) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
