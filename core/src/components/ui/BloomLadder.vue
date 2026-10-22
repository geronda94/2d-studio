<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  levels: { type: Array, default: () => [] },
  active_level: { type: [Number, String], default: null },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'BloomLadder')
const relativeTime = inject('relativeTime', ref(0))

const ordered = computed(() => props.levels.map((l, i) => ({ ...l, _i: i })).reverse())

const accent = (l) => getHexColor(l.color || `var(--item-accent-${(l._i % 4) + 1})`)

const isActive = (l) => {
  const a = props.active_level
  if (a === null || a === undefined || a === '') return false
  if (typeof a === 'number') return l._i + 1 === a
  return String(l.name) === String(a)
}

const widthPct = (d) => {
  const n = ordered.value.length
  if (n <= 1) return 100
  return 100 - d * (38 / (n - 1))
}

const reveal = (l) => {
  const t = l.start_time ?? l._i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const rowStyle = (l, d) => {
  const e = reveal(l)
  const active = isActive(l)
  return {
    width: `${widthPct(d)}%`,
    opacity: e.toFixed(4),
    // Плотный список уровней: горизонтальный отступ из токена, вертикальный — половина
    // (полный item-padding на 5-6 рядов переполняет кадр).
    padding: 'calc(var(--item-padding) * 0.5) var(--item-padding)',
    transform: `translateY(${((1 - e) * 16).toFixed(2)}px) scale(${active ? 1.02 : 1})`,
    ...(active
      ? { borderColor: accent(l), boxShadow: `0 0 0 2px ${getColorAlpha(accent(l), 0.35)}` }
      : {}),
  }
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

const activeName = computed(() => {
  const l = ordered.value.find((x) => isActive(x))
  return l ? l.name : ''
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-text-muted">
      <span class="uppercase tracking-widest">Таксономия Блума · уровни мышления</span>
      <span v-if="activeName" class="flex items-center gap-1" :style="{ color: getHexColor('var(--color-secondary)') }">
        <Icon icon="lucide:crosshair" class="w-3.5 h-3.5" />Цель урока: {{ activeName }}
      </span>
    </div>

    <div
      v-if="!levels.length"
      class="relative w-full flex-1 min-h-[320px] flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col gap-1" :class="mobile ? 'justify-between' : 'justify-end'">
      <div class="flex items-center justify-between px-1 text-[9px] font-mono text-text-muted">
        <span>базовые уровни</span>
        <span>продуктивное мышление</span>
      </div>
      <div
        v-for="(l, d) in ordered"
        :key="l._i"
        class="mx-auto flex items-center gap-3"
        :style="[itemStyle, rowStyle(l, d)]"
      >
        <span
          class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0"
          :style="{ background: getColorAlpha(accent(l), 0.16), border: '1px solid ' + accent(l), color: accent(l) }"
        >{{ l._i + 1 }}</span>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="font-heading font-bold leading-tight" :class="mobile ? 'text-xs' : 'text-sm'" :style="{ color: accent(l) }">
              {{ l.name }}
            </p>
            <Icon v-if="isActive(l)" icon="lucide:crosshair" class="w-3.5 h-3.5 shrink-0" :style="{ color: accent(l) }" />
          </div>
          <p v-if="l.task" class="text-[11px] text-text-secondary mt-0.5 leading-tight">{{ l.task }}</p>
        </div>

        <div v-if="!mobile" class="flex flex-nowrap gap-1 justify-end shrink-0">
          <span
            v-for="(v, vi) in (l.verbs || [])"
            :key="vi"
            class="px-1.5 py-0.5 rounded text-[10px] font-mono whitespace-nowrap"
            :style="{ background: getColorAlpha(accent(l), 0.12), color: accent(l) }"
          >{{ v }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
