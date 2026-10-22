<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  stations: { type: Array, default: () => [] },
  takt_sec: { type: Number, default: 0 },
  bottleneck: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, line, motion } = useVariant(computed(() => props.variant), 'YamazumiBalance')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))

const stationTotal = (s) => (s.elements || []).reduce((a, e) => a + num(e.sec), 0)
const totals = computed(() => (props.stations || []).map(stationTotal))
const maxTotal = computed(() => Math.max(1, num(props.takt_sec), ...totals.value))
const bottleneckIndex = computed(() => {
  const list = props.stations || []
  const byName = list.findIndex((s) => s.name === props.bottleneck)
  if (byName >= 0) return byName
  let idx = -1
  let max = -1
  totals.value.forEach((t, i) => { if (t > max) { max = t; idx = i } })
  return idx
})
const taktY = computed(() => 100 - clamp01(num(props.takt_sec) / maxTotal.value) * 100)
const overTakt = (i) => totals.value[i] - num(props.takt_sec)
const barHeight = (i) => (totals.value[i] / maxTotal.value) * 100
const segmentHeight = (sec, total) => (num(sec) / Math.max(1, total)) * 100
const taktToken = 'var(--color-warning)'
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!stations.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <span class="text-[11px] font-mono uppercase tracking-wider text-text-muted">Балансировка линии · ямадзуми</span>
        <span class="flex items-center gap-2 text-[11px] font-mono px-2.5 py-1 rounded-full"
              :style="{ background: getColorAlpha(taktToken, 0.14), border: '1px solid ' + getColorAlpha(taktToken, 0.4), color: getHexColor(taktToken) }">
          <Icon icon="lucide:align-horizontal-justify-start" class="w-3.5 h-3.5" />
          такт {{ num(takt_sec) }} с
        </span>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden">
        <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <line v-for="n in [25, 50, 75]" :key="'g' + n" x1="0" :y1="n" x2="100" :y2="n"
                stroke="var(--item-border)" stroke-width="0.4" vector-effect="non-scaling-stroke" />
          <line x1="0" :y1="taktY" x2="100" :y2="taktY"
                :stroke="getHexColor(taktToken)" :stroke-width="line.width"
                :stroke-dasharray="line.dash === 'none' ? '6 5' : line.dash" vector-effect="non-scaling-stroke" />
        </svg>

        <div class="absolute inset-0 flex items-end gap-2 md:gap-3 pb-7">
          <div v-for="(s, i) in stations" :key="s.name + i" class="flex-1 h-full flex flex-col justify-end items-center min-w-0">
            <span class="text-[10px] font-mono px-1.5 rounded-full relative z-10 -mb-10"
                  :style="{ color: i === bottleneckIndex ? getHexColor(taktToken) : 'var(--text-primary)', background: 'rgb(var(--bg-base-rgb) / 0.85)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', opacity: progress(s.start_time ?? i * motion.stagger_ms).toFixed(3) }">
              {{ totals[i] }} с
            </span>
            <div
              class="w-full max-w-[76px] flex flex-col-reverse overflow-hidden"
              :style="{
                height: barHeight(i) + '%',
                transformOrigin: 'bottom',
                transform: `scaleY(${progress(s.start_time ?? i * motion.stagger_ms).toFixed(3)})`,
                borderRadius: 'var(--item-radius)',
                boxShadow: i === bottleneckIndex ? 'var(--item-shadow)' : 'none',
                background: i === bottleneckIndex ? 'var(--item-primary-bg)' : 'var(--item-bg)',
                backdropFilter: i === bottleneckIndex ? 'var(--item-primary-backdrop)' : 'var(--item-backdrop)',
                WebkitBackdropFilter: i === bottleneckIndex ? 'var(--item-primary-backdrop)' : 'var(--item-backdrop)',
                border: i === bottleneckIndex ? '2px solid ' + getHexColor(taktToken) : '1px solid var(--item-border)',
              }"
            >
              <div v-for="(e, k) in (s.elements || [])" :key="k"
                   :style="{ height: segmentHeight(e.sec, totals[i]) + '%', background: getHexColor('var(--item-accent-' + ((k % 4) + 1) + ')') }"></div>
            </div>
          </div>
        </div>

        <span class="absolute right-3 text-[10px] font-mono -translate-y-1/2 px-1.5 rounded"
              :style="{ bottom: (100 - taktY) + '%', color: getHexColor(taktToken), background: 'rgb(var(--bg-base-rgb) / 0.8)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }">такт</span>

        <div class="absolute left-0 right-0 border-t" :style="{ bottom: '1.75rem', borderColor: 'var(--item-border)' }"></div>

        <div class="absolute inset-x-0 bottom-0 flex gap-2 md:gap-3">
          <div v-for="(s, i) in stations" :key="'n' + i" class="flex-1 min-w-0 text-center">
            <span class="inline-flex items-center gap-1 text-[10px] md:text-[11px] truncate max-w-full"
                  :style="{ color: i === bottleneckIndex ? getHexColor(taktToken) : 'var(--text-secondary)' }">
              <Icon v-if="i === bottleneckIndex" icon="lucide:triangle-alert" class="w-3 h-3 shrink-0" />
              {{ s.name }}
            </span>
          </div>
        </div>
      </div>

      <div class="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] font-mono text-text-muted">
        <span>Такт {{ num(takt_sec) }} с</span>
        <span v-if="bottleneckIndex >= 0" :style="{ color: getHexColor(taktToken) }">
          Бутылочное горло: {{ stations[bottleneckIndex].name }} (+{{ overTakt(bottleneckIndex) }} с)
        </span>
        <span>Станций: {{ stations.length }}</span>
        <span v-if="!mobile" class="text-text-primary">Элементы работ — цветные сегменты станции</span>
        <span class="text-text-secondary">Δ к такту: <span :style="{ color: getHexColor(taktToken) }">+</span> перегруз / <span class="text-text-secondary">−</span> резерв</span>
      </div>

      <div class="mt-2 flex gap-2 md:gap-3">
        <div v-for="(s, i) in stations" :key="'o' + i" class="flex-1 min-w-0 text-center text-[10px] font-mono px-1 py-1 rounded-[var(--item-radius)] truncate"
             :style="{ background: overTakt(i) > 0 ? getColorAlpha(taktToken, 0.16) : getColorAlpha('var(--color-secondary)', 0.14), color: overTakt(i) > 0 ? getHexColor(taktToken) : 'var(--text-secondary)', border: '1px solid ' + getColorAlpha(overTakt(i) > 0 ? taktToken : 'var(--color-secondary)', 0.35) }">
          {{ overTakt(i) > 0 ? '+' : '' }}{{ overTakt(i) }} с
        </div>
      </div>
    </template>
  </div>
</template>
