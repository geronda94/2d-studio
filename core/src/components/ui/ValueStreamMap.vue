<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import NodeFlow from './NodeFlow.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  processes: { type: Array, default: () => [] },
  flows: { type: Array, default: () => [] },
  va_time: { type: Number, default: 0 },
  lead_time: { type: Number, default: 0 },
})

const { itemVars, line, motion } = useVariant(computed(() => props.variant), 'ValueStreamMap')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))

const cardStyle = {
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

const idOf = (name) => {
  const i = (props.processes || []).findIndex((p) => p.name === name)
  return i < 0 ? null : 'p' + i
}
const nodes = computed(() => (props.processes || []).map((p, i) => ({
  id: 'p' + i,
  label: p.name,
  // meta не отдаём: подписи нод и подписи связей в NodeFlow идут на одной высоте
  // и наезжают друг на друга (прошлый баг). Детали ЦТ/ожид. есть в нижней легенде.
  status: num(p.wait_time) > num(p.cycle_time) ? 'warning' : 'ok',
  start_time: p.start_time,
})))
const edges = computed(() => {
  const mapped = (props.flows || []).map((f) => ({
    from: idOf(f.from) || f.from,
    to: idOf(f.to) || f.to,
    label: f.label || '',
    duration_label: f.duration_label || '',
  }))
  if (mapped.length) return mapped
  return nodes.value.slice(0, -1).map((n, i) => ({ from: n.id, to: nodes.value[i + 1].id, label: '', duration_label: '' }))
})

const total = computed(() => num(props.lead_time) || (props.processes || []).reduce((s, p) => s + num(p.cycle_time) + num(p.wait_time), 0) || 1)
const vaTotal = computed(() => num(props.va_time) || (props.processes || []).reduce((s, p) => s + num(p.cycle_time), 0) || 1)
const nvaTime = computed(() => Math.max(0, total.value - num(props.va_time)))
const vaRatio = computed(() => (num(props.va_time) / total.value) * 100)

const segments = computed(() => {
  const t = total.value
  const out = []
  ;(props.processes || []).forEach((p) => {
    out.push({ kind: 'cycle', sec: num(p.cycle_time), w: (num(p.cycle_time) / t) * 100 })
    out.push({ kind: 'wait', sec: num(p.wait_time), w: (num(p.wait_time) / t) * 100 })
  })
  return out
})

// Классическая лестница VSM: процесс — подъём, ожидание — горизонталь.
const stairPoints = computed(() => {
  const x = (v) => (v / total.value) * 100
  const y = (v) => 100 - clamp01(v / vaTotal.value) * 100
  const pts = [`0.00,${y(0).toFixed(2)}`]
  let xAcc = 0
  let yAcc = 0
  ;(props.processes || []).forEach((p) => {
    const cyc = num(p.cycle_time)
    const wait = num(p.wait_time)
    pts.push(`${x(xAcc).toFixed(2)},${y(yAcc + cyc).toFixed(2)}`)
    xAcc += cyc
    pts.push(`${x(xAcc).toFixed(2)},${y(yAcc + cyc).toFixed(2)}`)
    yAcc += cyc
    xAcc += wait
    pts.push(`${x(xAcc).toFixed(2)},${y(yAcc).toFixed(2)}`)
  })
  return pts.join(' ')
})

const reveal = (i, t0) => {
  const e = progress(t0 ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}
const fmt = (v) => Math.round(num(v))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!processes.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="mb-3 flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-text-muted">
        <span>Поток создания ценности · VA / NVA</span>
        <span :style="{ color: getHexColor('var(--color-success)') }">VA {{ vaRatio.toFixed(0) }}%</span>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden [&_.min-h-\[260px\]]:min-h-[220px]">
        <NodeFlow :nodes="nodes" :edges="edges" :variant="variant" :mobile="mobile" flow-layout="layered" />
      </div>

      <div class="mt-3 p-3" :style="cardStyle">
        <div class="flex flex-wrap items-center gap-x-6 gap-y-2 mb-3 text-[13px] font-mono">
          <span class="flex items-center gap-1.5 text-text-secondary">
            <span class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getHexColor('var(--color-success)') }"></span>VA {{ fmt(va_time) }} с
          </span>
          <span class="flex items-center gap-1.5 text-text-secondary">
            <span class="w-3 h-3 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getColorAlpha('var(--text-muted)', 0.5) }"></span>NVA {{ fmt(nvaTime) }} с
          </span>
          <span class="text-text-primary font-bold">Lead time {{ fmt(total) }} с</span>
          <span class="ml-auto font-bold" :style="{ color: getHexColor('var(--color-success)') }">Доля ценности {{ vaRatio.toFixed(0) }}%</span>
        </div>

        <div class="relative w-full h-[110px]">
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline :points="stairPoints" fill="none" :stroke="line.color" :stroke-width="line.width"
                      :stroke-dasharray="line.dash === 'none' ? undefined : line.dash"
                      vector-effect="non-scaling-stroke" :style="{ opacity: progress(0, motion.appear_ms * 1.8).toFixed(3) }" />
          </svg>
          <div class="absolute inset-x-0 bottom-0 h-3 flex overflow-hidden origin-left"
               :style="{ borderRadius: 'var(--item-radius)', transform: `scaleX(${progress(0).toFixed(3)})` }">
            <div v-for="(s, i) in segments" :key="i"
                 :style="{ width: s.w.toFixed(2) + '%', background: s.kind === 'cycle' ? getHexColor('var(--color-success)') : getColorAlpha('var(--text-muted)', 0.5) }"></div>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap gap-x-4 gap-y-2">
          <span v-for="(p, i) in processes" :key="p.name + i" class="flex items-center gap-1.5 text-xs" :style="reveal(i, p.start_time)">
            <span class="w-2.5 h-2.5 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getHexColor('var(--item-accent-' + ((i % 4) + 1) + ')') }"></span>
            <span class="text-text-primary font-bold">{{ p.name }}</span>
            <span class="text-text-secondary font-mono">ЦТ {{ num(p.cycle_time) }} / ожид. {{ num(p.wait_time) }} с</span>
          </span>
        </div>
      </div>
    </template>
  </div>
</template>
