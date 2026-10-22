<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  lines: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'OeeDashboard')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const avg = (key) => {
  const list = props.lines || []
  if (!list.length) return 0
  return list.reduce((s, l) => s + num(l[key]), 0) / list.length
}

const overall = computed(() => ({
  name: (props.lines[0] && props.lines[0].name) || 'Цех',
  availability: avg('availability'),
  performance: avg('performance'),
  quality: avg('quality'),
  oee: avg('oee'),
  target: avg('target'),
}))

const pillars = computed(() => [
  { label: 'Доступность', value: overall.value.availability, icon: 'lucide:timer-reset' },
  { label: 'Производительность', value: overall.value.performance, icon: 'lucide:gauge' },
  { label: 'Качество', value: overall.value.quality, icon: 'lucide:badge-check' },
])

// Мультипликативная декомпозиция: OEE = A × P × Q, потери считаются последовательно.
const losses = computed(() => {
  const a = clamp01(overall.value.availability / 100)
  const p = clamp01(overall.value.performance / 100)
  const q = clamp01(overall.value.quality / 100)
  return [
    { label: 'Доступность', value: (1 - a) * 100, color: 'var(--color-danger)' },
    { label: 'Темп', value: a * (1 - p) * 100, color: 'var(--color-warning)' },
    { label: 'Качество', value: a * p * (1 - q) * 100, color: 'var(--color-accent)' },
  ]
})

const CX = 110
const CY = 130
const R = 92
const point = (deg, r) => ({
  x: CX + r * Math.sin((deg * Math.PI) / 180),
  y: CY - r * Math.cos((deg * Math.PI) / 180),
})
const needleAngle = computed(() => -90 + 180 * clamp01(overall.value.oee / 100) * progress(0, motion.value.count_ms))
const targetTick = computed(() => {
  const a = -90 + 180 * clamp01(overall.value.target / 100)
  return { a: point(a, 80), b: point(a, R) }
})
const ticks = [0, 25, 50, 75, 100].map((v) => {
  const a = -90 + 180 * (v / 100)
  return { v, a: point(a, R - 12), b: point(a, R) }
})

const oeeToken = (l) => {
  const o = num(l.oee)
  const t = num(l.target)
  if (o >= t) return 'var(--color-success)'
  return o >= t - 5 ? 'var(--color-warning)' : 'var(--color-danger)'
}
const rowReveal = (i, t0) => {
  const e = progress(t0 ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!lines.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="mb-2 flex items-center justify-between gap-3 text-[11px] font-mono uppercase tracking-wider text-text-muted">
        <span>OEE = доступность × производительность × качество</span>
        <span class="truncate">{{ overall.name }}</span>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden grid gap-1.5 md:gap-3 lg:grid-cols-[300px_minmax(0,1fr)]">
        <!-- Гейдж + столпы -->
        <div class="flex flex-col gap-1.5 md:gap-2 p-2 md:p-2.5" :style="cardStyle">
          <div class="relative w-full max-w-[280px] h-[100px] mx-auto">
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 220 150" preserveAspectRatio="xMidYMax meet">
              <path d="M 18 130 A 92 92 0 0 1 202 130" fill="none"
                    :stroke="getColorAlpha(oeeToken(lines[0]), 0.22)" stroke-width="10" stroke-linecap="round" />
              <line v-for="t in ticks" :key="'t' + t.v" :x1="t.a.x" :y1="t.a.y" :x2="t.b.x" :y2="t.b.y"
                    stroke="var(--item-border)" stroke-width="1.5" />
              <line :x1="targetTick.a.x" :y1="targetTick.a.y" :x2="targetTick.b.x" :y2="targetTick.b.y"
                    stroke="var(--color-accent)" stroke-width="3" stroke-linecap="round" />
            </svg>
            <div
              class="absolute left-1/2 bottom-[14px] w-[3px] h-[60px] rounded-full"
              :style="{ marginLeft: '-1.5px', transformOrigin: 'bottom center', transform: `rotate(${needleAngle}deg)`, background: getHexColor(oeeToken(lines[0])) }"
            ></div>
          </div>

          <div class="text-center">
            <div class="font-black text-4xl text-text-primary leading-none">
              {{ Math.round(overall.oee) }}<span class="text-lg text-text-muted">%</span>
            </div>
            <div class="text-[10px] font-mono text-text-muted mt-1">план {{ Math.round(overall.target) }}%</div>
          </div>

          <div class="flex flex-col gap-2">
            <div v-for="(p, i) in pillars" :key="p.label" class="flex items-center gap-2">
              <Icon :icon="p.icon" class="w-4 h-4 shrink-0" :style="{ color: getHexColor('var(--item-accent-' + ((i % 4) + 1) + ')') }" />
              <span class="w-28 text-[11px] text-text-secondary truncate">{{ p.label }}</span>
              <div class="relative flex-1 h-2 rounded-full overflow-hidden" :style="{ background: 'var(--item-border)' }">
                <div class="absolute inset-0 origin-left rounded-full"
                     :style="{ transform: `scaleX(${(clamp01(p.value / 100) * progress(0)).toFixed(3)})`, background: getHexColor('var(--item-accent-' + ((i % 4) + 1) + ')') }"></div>
              </div>
              <span class="w-10 text-right text-[11px] font-mono text-text-primary">{{ Math.round(p.value) }}%</span>
            </div>
          </div>
        </div>

        <!-- Таблица линий -->
        <div class="p-2 md:p-2.5" :class="mobile ? 'overflow-hidden' : 'overflow-x-auto'" :style="cardStyle">
          <div class="grid gap-x-1.5 md:gap-x-2 text-[10px] font-mono uppercase tracking-wider text-text-muted pb-2 border-b"
               :class="mobile ? 'grid-cols-[minmax(88px,1fr)_repeat(4,minmax(36px,1fr))_minmax(46px,1fr)]' : 'grid-cols-[minmax(120px,1fr)_repeat(4,minmax(48px,64px))_minmax(60px,76px)]'"
               :style="{ borderColor: 'var(--item-border)' }">
            <span>Линия</span>
            <span class="text-right">Дост.</span>
            <span class="text-right">Темп</span>
            <span class="text-right">Кач.</span>
            <span class="text-right">OEE</span>
            <span class="text-right">План</span>
          </div>
          <div v-for="(l, i) in lines" :key="l.name + i"
               class="grid gap-x-1.5 md:gap-x-2 items-center py-1.5 border-b last:border-0"
               :class="mobile ? 'grid-cols-[minmax(88px,1fr)_repeat(4,minmax(36px,1fr))_minmax(46px,1fr)]' : 'grid-cols-[minmax(120px,1fr)_repeat(4,minmax(48px,64px))_minmax(60px,76px)]'"
               :style="[{ borderColor: 'var(--item-border)' }, rowReveal(i, l.start_time)]">
            <span class="text-text-primary text-xs font-medium truncate">{{ l.name }}</span>
            <span class="text-right text-xs font-mono text-text-secondary">{{ Math.round(num(l.availability)) }}%</span>
            <span class="text-right text-xs font-mono text-text-secondary">{{ Math.round(num(l.performance)) }}%</span>
            <span class="text-right text-xs font-mono text-text-secondary">{{ Math.round(num(l.quality)) }}%</span>
            <span class="text-right text-sm font-bold font-mono" :style="{ color: getHexColor(oeeToken(l)) }">{{ Math.round(num(l.oee)) }}%</span>
            <span class="text-right text-xs font-mono text-text-muted">{{ Math.round(num(l.target)) }}%</span>
          </div>
        </div>

        <!-- Разбивка потерь -->
        <div class="lg:col-span-2 p-2 md:p-2.5" :style="cardStyle">
          <div class="flex items-center justify-between mb-2 text-[11px] font-mono uppercase tracking-wider text-text-muted">
            <span>Разбивка потерь · 100% − OEE = {{ Math.round(100 - overall.oee) }}%</span>
            <span v-if="!mobile">A × P × Q</span>
          </div>
          <div class="h-5 w-full rounded-full overflow-hidden flex origin-left"
               :style="{ transform: `scaleX(${progress(0).toFixed(3)})` }">
            <div v-for="s in losses" :key="s.label" class="h-full" :style="{ width: s.value.toFixed(2) + '%', background: getHexColor(s.color) }"></div>
            <div class="h-full flex-1" :style="{ background: getColorAlpha('var(--color-success)', 0.85) }"></div>
          </div>
          <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-text-secondary">
            <span v-for="s in losses" :key="'l' + s.label" class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getHexColor(s.color) }"></span>{{ s.label }} {{ s.value.toFixed(1) }}%
            </span>
            <span class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getColorAlpha('var(--color-success)', 0.85) }"></span>OEE {{ Math.round(overall.oee) }}%
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
