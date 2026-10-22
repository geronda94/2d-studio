<script setup>
// CivilizationCycle — цикл подъёма и упадка цивилизации: фазы и их признаки.
// Собственный макет: кольцо фаз (SVG) + панель фаз со знаками. Данные из props.
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  phases: { type: Array, default: () => [] },
  center_label: { type: String, default: '' },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CivilizationCycle')
const relativeTime = inject('relativeTime', ref(0))

const n = computed(() => Math.max(1, props.phases.length))
const phaseTime = (p, i) => p.start_time ?? i * motion.value.stagger_ms

const activeIndex = computed(() => {
  let idx = 0
  props.phases.forEach((p, i) => {
    if (relativeTime.value >= phaseTime(p, i)) idx = i
  })
  return idx
})

const reveal = (p, i) => {
  const prog = Math.max(0, Math.min(1, (relativeTime.value - phaseTime(p, i)) / motion.value.appear_ms))
  return 1 - Math.pow(1 - prog, 3)
}

const accent = (p, i) => getHexColor(p.color || `var(--item-accent-${(i % 4) + 1})`)
const badgeBg = (p, i) => getColorAlpha(accent(p, i), 0.15)

const nodes = computed(() =>
  props.phases.map((_phase, i) => {
    const angle = ((-90 + (i + 0.5) * (360 / n.value)) * Math.PI) / 180
    return { x: 100 + 70 * Math.cos(angle), y: 100 + 70 * Math.sin(angle) }
  }),
)

const rowStyle = (p, i) => {
  const e = reveal(p, i)
  return {
    opacity: e.toFixed(4),
    transform: `translateX(${((1 - e) * 12).toFixed(2)}px)`,
    borderColor: i === activeIndex.value ? accent(p, i) : 'var(--item-border)',
  }
}

const arcDash = computed(() => {
  const seg = (100 / n.value) * 0.78
  return `${seg.toFixed(3)} ${(100 - seg).toFixed(3)}`
})
const arcOffset = (i) => `${(-(i * (100 / n.value))).toFixed(3)}`

const lastTime = computed(() =>
  props.phases.length ? phaseTime(props.phases[props.phases.length - 1], props.phases.length - 1) : 0,
)
const sourceStyle = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - lastTime.value) / motion.value.appear_ms))
  return { opacity: p.toFixed(3) }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!phases.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden">
        <div
          class="w-full h-full"
          :class="mobile ? 'flex flex-col justify-between gap-2' : 'flex items-center gap-6'"
        >
          <div v-if="!mobile" class="min-w-0 flex-1 h-full relative">
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 200 200" preserveAspectRatio="xMidYMid meet">
              <circle
                cx="100" cy="100" r="70" fill="none" stroke-width="1.5"
                :style="{ stroke: 'var(--item-border)', opacity: 0.35 }"
              />

              <circle
                v-for="(p, i) in phases"
                :key="'arc' + (p.id ?? i)"
                cx="100" cy="100" r="70" fill="none" pathLength="100"
                stroke-width="5" stroke-linecap="round" transform="rotate(-90 100 100)"
                :stroke-dasharray="arcDash"
                :stroke-dashoffset="arcOffset(i)"
                :style="{ stroke: i <= activeIndex ? accent(p, i) : 'var(--item-border)', opacity: reveal(p, i).toFixed(4) }"
              />

              <g v-for="(nd, i) in nodes" :key="'nd' + i" :style="{ opacity: reveal(phases[i], i).toFixed(4) }">
                <circle
                  :cx="nd.x" :cy="nd.y" r="13"
                  :style="{
                    fill: 'var(--item-bg)',
                    stroke: i <= activeIndex ? accent(phases[i], i) : 'var(--item-border)',
                  }"
                  stroke-width="2"
                />
                <text
                  :x="nd.x" :y="nd.y + 1" text-anchor="middle" dominant-baseline="central"
                  font-size="13" font-weight="700"
                  :style="{ fill: i <= activeIndex ? accent(phases[i], i) : 'var(--text-muted)' }"
                >{{ i + 1 }}</text>
              </g>

              <g>
                <circle cx="100" cy="100" r="34" stroke-width="1" :style="{ fill: 'var(--item-bg)', stroke: 'var(--item-border)' }" />
                <text x="100" y="94" text-anchor="middle" dominant-baseline="central" font-size="8" :style="{ fill: 'var(--text-muted)' }">{{ center_label }}</text>
                <text x="100" y="108" text-anchor="middle" dominant-baseline="central" font-size="11" font-weight="700" :style="{ fill: 'var(--text-primary)' }">{{ activeIndex + 1 }} / {{ n }}</text>
              </g>
            </svg>
          </div>

          <div
            class="min-h-0 overflow-hidden flex flex-col gap-2"
            :class="mobile ? 'w-full flex-1 justify-between' : 'w-[44%] shrink-0 justify-center'"
          >
            <div
              v-for="(p, i) in phases"
              :key="p.id ?? i"
              class="min-w-0 px-3 py-2"
              :style="[
                rowStyle(p, i),
                {
                  background: 'var(--item-bg)',
                  backdropFilter: 'var(--item-backdrop)',
                  borderRadius: 'var(--item-radius)',
                  boxShadow: 'var(--item-shadow)',
                  padding: 'var(--item-padding)',
                  borderWidth: 'var(--item-border-width)',
                  borderStyle: 'var(--item-border-style)',
                  borderLeftWidth: '3px',
                  borderLeftColor: accent(p, i),
                },
              ]"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span
                  class="w-5 h-5 shrink-0 rounded-full flex items-center justify-center font-mono text-[10px] font-bold"
                  :style="{ background: badgeBg(p, i), color: accent(p, i) }"
                >{{ i + 1 }}</span>
                <span class="font-heading font-bold text-text-primary text-sm truncate">{{ p.name }}</span>
                <span class="ml-auto shrink-0 font-mono text-[11px] text-text-muted">{{ p.span }}</span>
              </div>
              <div class="flex flex-wrap gap-1.5 mt-1.5">
                <span
                  v-for="(sign, j) in p.signs" :key="j"
                  class="text-[11px] px-2 py-0.5 rounded-full text-text-secondary"
                  :style="{ background: 'var(--item-primary-bg)', border: '1px solid var(--item-border)' }"
                >{{ sign }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="source_note"
        class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
        :style="sourceStyle"
      >
        {{ source_note }}
      </div>
    </template>
  </div>
</template>
