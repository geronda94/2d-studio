<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  machines: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'MachineStatusBoard')
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

// ran / idle / setup / down → success / muted / warning / danger
const STATES = {
  ran: { label: 'Работа', token: 'var(--color-success)', icon: 'lucide:play' },
  idle: { label: 'Ожидание', token: 'var(--text-muted)', icon: 'lucide:pause' },
  setup: { label: 'Наладка', token: 'var(--color-warning)', icon: 'lucide:wrench' },
  down: { label: 'Простой', token: 'var(--color-danger)', icon: 'lucide:octagon-x' },
}
const STATE_ORDER = ['ran', 'idle', 'setup', 'down']
const stateOf = (m) => STATES[m.state] || { label: m.state || '—', token: 'var(--color-secondary)', icon: 'lucide:activity' }

const counts = computed(() => {
  const c = {}
  STATE_ORDER.forEach((k) => (c[k] = 0))
  ;(props.machines || []).forEach((m) => { if (c[m.state] != null) c[m.state]++ })
  return c
})
const avgOf = (key) => {
  const list = props.machines || []
  if (!list.length) return 0
  return list.reduce((s, m) => s + num(m[key]), 0) / list.length
}
const avgMtbf = computed(() => avgOf('mtbf'))
const avgMttr = computed(() => avgOf('mttr'))
const distribution = computed(() => STATE_ORDER.map((k) => ({
  key: k,
  count: counts.value[k],
  pct: (counts.value[k] / (props.machines.length || 1)) * 100,
})))
const attention = computed(() => (props.machines || []).filter((m) => m.state === 'down' || m.state === 'setup'))
const tileReveal = (i, t0) => {
  const e = progress(t0 ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 16).toFixed(2)}px) scale(${(0.97 + 0.03 * e).toFixed(3)})` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col pt-0 md:pt-3" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!machines.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="mb-2 md:mb-4 flex flex-wrap items-center gap-2 md:gap-3">
        <span class="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-text-muted">
          <Icon icon="lucide:factory" class="w-3.5 h-3.5" />Статусы оборудования
        </span>
        <div class="flex flex-wrap items-center gap-2">
          <span v-for="k in STATE_ORDER" :key="k" class="flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-mono"
                :style="{ background: getColorAlpha(STATES[k].token, 0.12), border: '1px solid ' + getColorAlpha(STATES[k].token, 0.35) }">
            <span class="w-2 h-2 rounded-full" :style="{ background: getHexColor(STATES[k].token) }"></span>
            <span :style="{ color: getHexColor(STATES[k].token) }">{{ STATES[k].label }}</span>
            <span class="text-text-primary font-bold">{{ counts[k] }}</span>
          </span>
        </div>
        <div class="ml-auto flex items-center gap-4 text-[11px] font-mono text-text-muted">
          <span>MTBF <span class="text-text-primary">{{ avgMtbf.toFixed(1) }} ч</span></span>
          <span>MTTR <span class="text-text-primary">{{ avgMttr.toFixed(1) }} ч</span></span>
        </div>
      </div>

      <div class="mb-2 md:mb-4">
        <div class="flex h-2.5 w-full overflow-hidden origin-left"
             :style="{ borderRadius: 'var(--item-radius)', transform: `scaleX(${progress(0).toFixed(3)})` }">
          <div v-for="d in distribution" :key="d.key" :style="{ width: d.pct + '%', background: getHexColor(STATES[d.key].token) }"></div>
        </div>
      </div>

      <div class="relative w-full flex-1 min-h-0 grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-3 content-start" :class="mobile ? 'overflow-hidden' : 'overflow-hidden'">
        <div v-for="(m, i) in machines" :key="m.name + i" class="p-2.5 md:p-3 flex flex-col gap-1.5 md:gap-2"
             :style="[cardStyle, tileReveal(i, m.start_time)]">
          <div class="flex items-start justify-between gap-2">
            <span class="text-text-primary text-sm font-bold leading-tight">{{ m.name }}</span>
            <span class="w-2.5 h-2.5 rounded-full shrink-0 mt-1" :style="{ background: getHexColor(stateOf(m).token), boxShadow: '0 0 8px ' + getColorAlpha(stateOf(m).token, 0.7) }"></span>
          </div>

          <div class="flex items-center gap-2 px-2 py-1"
               :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: getColorAlpha(stateOf(m).token, 0.12), border: '1px solid ' + getColorAlpha(stateOf(m).token, 0.3) }">
            <Icon :icon="stateOf(m).icon" class="w-3.5 h-3.5 shrink-0" :style="{ color: getHexColor(stateOf(m).token) }" />
            <span class="text-xs font-bold truncate" :style="{ color: getHexColor(stateOf(m).token) }">{{ stateOf(m).label }}</span>
          </div>

          <div class="flex items-center justify-between text-[11px] font-mono text-text-muted">
            <span>с {{ m.since || '—' }}</span>
          </div>
          <div class="flex items-center justify-between text-[10px] font-mono pt-1.5 border-t" :style="{ borderColor: 'var(--item-border)' }">
            <span class="text-text-muted">MTBF <span class="text-text-secondary">{{ num(m.mtbf) }} ч</span></span>
            <span class="text-text-muted">MTTR <span class="text-text-secondary">{{ num(m.mttr) }} ч</span></span>
          </div>
        </div>
      </div>

      <div v-if="attention.length" class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-text-muted">
        <span class="flex items-center gap-1.5" :style="{ color: getHexColor('var(--color-warning)') }">
          <Icon icon="lucide:bell" class="w-3.5 h-3.5" />Требуют внимания
        </span>
        <span v-for="(m, i) in attention" :key="i" :style="{ color: getHexColor(stateOf(m).token) }">
          {{ m.name }} · {{ stateOf(m).label }}
        </span>
      </div>
    </template>
  </div>
</template>
