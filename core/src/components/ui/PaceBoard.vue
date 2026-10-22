<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  plan: { type: Number, default: 0 },
  actual: { type: Number, default: 0 },
  takt: { type: Number, default: 0 },
  hourly: { type: Array, default: () => [] },
  stoppage_sec: { type: Number, default: 0 },
  status: { type: String, default: '' },
})

const { itemVars, line, motion } = useVariant(computed(() => props.variant), 'PaceBoard')
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

const STATUS = {
  run: { label: 'В норме', token: 'var(--color-success)', icon: 'lucide:circle-check' },
  running: { label: 'В норме', token: 'var(--color-success)', icon: 'lucide:circle-check' },
  on_track: { label: 'В норме', token: 'var(--color-success)', icon: 'lucide:circle-check' },
  warning: { label: 'Отставание', token: 'var(--color-warning)', icon: 'lucide:triangle-alert' },
  behind: { label: 'Отставание', token: 'var(--color-warning)', icon: 'lucide:triangle-alert' },
  stopped: { label: 'Останов', token: 'var(--color-danger)', icon: 'lucide:octagon-x' },
  critical: { label: 'Останов', token: 'var(--color-danger)', icon: 'lucide:octagon-x' },
}
const state = computed(() => STATUS[props.status] || { label: props.status || 'Статус', token: 'var(--color-secondary)', icon: 'lucide:activity' })
const completion = computed(() => (num(props.plan) ? (num(props.actual) / num(props.plan)) * 100 : 0))

const series = computed(() => (props.hourly || []).map((h, i) => ({
  label: h.hour ?? h.label ?? String(i + 1),
  plan: num(h.plan),
  actual: num(h.actual),
  start_time: h.start_time,
})))
const maxVal = computed(() => {
  const vals = [num(props.plan), num(props.actual)]
  series.value.forEach((p) => { vals.push(p.plan, p.actual) })
  return Math.max(1, ...vals) * 1.12
})
const yTicks = computed(() => {
  const max = maxVal.value
  return [max, max * 0.5, 0].map((v) => Math.round(v))
})
const xPct = (i) => ((i + 0.5) / Math.max(1, series.value.length)) * 100
const yPct = (v) => 100 - clamp01(num(v) / maxVal.value) * 100
const poly = (key) => series.value.map((p, i) => `${xPct(i).toFixed(2)},${yPct(p[key]).toFixed(2)}`).join(' ')
const lineGrow = computed(() => progress(0, motion.value.appear_ms * 1.6))

const stoppageShown = computed(() => Math.round(num(props.stoppage_sec) * progress(motion.value.appear_ms, motion.value.count_ms)))
const fmtTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`

const stats = computed(() => [
  { label: 'План', value: num(props.plan), suffix: '', tone: 'var(--text-primary)' },
  { label: 'Факт', value: num(props.actual), suffix: '', tone: 'var(--text-primary)' },
  { label: 'Выполнение', value: Math.round(completion.value), suffix: '%', tone: completion.value >= 100 ? 'var(--color-success)' : 'var(--color-warning)' },
  { label: 'Такт', value: num(props.takt), suffix: 'с', tone: 'var(--text-primary)' },
])
const pointReveal = (p, i) => {
  const e = progress(p.start_time ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translate(-50%, -50%) scale(${(0.6 + 0.4 * e).toFixed(3)})` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div class="mb-3 flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2 px-3 py-2 rounded-full"
           :style="{ background: getColorAlpha(state.token, 0.14), border: '1px solid ' + getColorAlpha(state.token, 0.4) }">
        <Icon :icon="state.icon" class="w-4 h-4" :style="{ color: getHexColor(state.token) }" />
        <span class="text-xs font-bold" :style="{ color: getHexColor(state.token) }">{{ state.label }}</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-2 rounded-full text-xs font-mono"
           :style="{ background: 'var(--item-bg)', border: '1px solid var(--item-border)' }">
        <Icon icon="lucide:timer" class="w-4 h-4 text-text-muted" />
        <span class="text-text-secondary">Простой</span>
        <span class="font-bold" :style="{ color: num(stoppage_sec) > 0 ? getHexColor('var(--color-danger)') : 'var(--text-primary)' }">{{ fmtTime(stoppageShown) }}</span>
      </div>
      <span class="ml-auto text-[11px] font-mono uppercase tracking-wider text-text-muted">Андон · темп линии</span>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-3">
      <div v-for="s in stats" :key="s.label" class="p-3" :style="cardStyle">
        <div class="text-[10px] font-mono uppercase tracking-wider text-text-muted">{{ s.label }}</div>
        <div class="mt-1 text-2xl font-black leading-none" :style="{ color: s.tone }">
          {{ s.value }}<span class="text-xs text-text-muted ml-0.5">{{ s.suffix }}</span>
        </div>
      </div>
    </div>

    <div class="relative w-full flex-1 min-h-0 overflow-hidden" :style="cardStyle">
      <div v-if="!series.length" class="h-full flex items-center justify-center text-text-muted text-sm py-16">Нет почасовых данных</div>
      <template v-else>
        <!-- Y ось -->
        <div class="absolute top-0 bottom-6 left-0 w-10 md:w-12 flex flex-col justify-between items-end pr-2 text-[9px] md:text-[10px] font-mono text-text-muted z-10">
          <span v-for="(t, i) in yTicks" :key="'y' + i" :class="i === 0 ? '' : '-translate-y-1/2'">{{ t }}</span>
        </div>
        <div class="absolute inset-0 left-10 md:left-12">
        <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <line v-for="n in [25, 50, 75]" :key="'g' + n" x1="0" :y1="n" x2="100" :y2="n"
                stroke="var(--item-border)" stroke-width="0.4" vector-effect="non-scaling-stroke" />
          <polyline :points="poly('plan')" fill="none" :stroke="line.color" :stroke-dasharray="line.dash === 'none' ? undefined : line.dash"
                    stroke-width="2" vector-effect="non-scaling-stroke" :style="{ opacity: (0.45 + 0.55 * lineGrow).toFixed(3) }" />
          <polyline :points="poly('actual')" fill="none" :stroke="getHexColor(state.token)"
                    stroke-width="2.5" vector-effect="non-scaling-stroke" :style="{ opacity: lineGrow.toFixed(3) }" />
        </svg>

        <div class="absolute inset-0">
          <span
            v-for="(p, i) in series"
            :key="p.label + i"
            class="absolute w-2 h-2 rounded-full"
            :style="[{ left: xPct(i) + '%', top: yPct(p.actual) + '%', background: getHexColor(state.token) }, pointReveal(p, i)]"
          ></span>
        </div>

        <div class="absolute inset-x-0 bottom-0 flex">
          <span v-for="(p, i) in series" :key="'x' + i" class="flex-1 text-center text-[10px] font-mono text-text-muted truncate px-0.5 pb-1">{{ p.label }}</span>
        </div>
        </div>
      </template>
    </div>

    <div class="mt-3 flex items-center justify-between text-[11px] font-mono text-text-muted">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1.5">
          <span class="w-4 h-0.5" :style="{ background: getHexColor(line.color) }"></span>План (накопл.)
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-4 h-0.5" :style="{ background: getHexColor(state.token) }"></span>Факт (накопл.)
        </span>
      </div>
      <span v-if="!mobile">такт {{ num(takt) }} с/шт</span>
    </div>
  </div>
</template>
