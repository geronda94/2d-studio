<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  parts: { type: Array, default: () => [] },
  center_label: { type: String, default: '' },
  center_icon: { type: String, default: 'lucide:heart' },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'SoulStructure')
const relativeTime = inject('relativeTime', ref(0))

const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const e = ease(clamp01((relativeTime.value - t) / (motion.value.appear_ms || 500)))
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const placed = computed(() => {
  const list = props.parts || []
  const n = list.length
  const rx = props.mobile ? 24 : 37
  const ry = props.mobile ? 34 : 33
  return list.map((p, i) => {
    const ang = (i / Math.max(1, n)) * Math.PI * 2 - Math.PI / 2
    return { ...p, _i: i, x: 50 + Math.cos(ang) * rx, y: 50 + Math.sin(ang) * ry }
  })
})

// Точка выхода линии на КРАЮ карточки (а не в её центре/углу).
const edgePoint = (p) => {
  const dx = 50 - p.x
  const dy = 50 - p.y
  const hw = props.mobile ? 20 : 15
  const hh = props.mobile ? 15 : 12
  const tx = dx !== 0 ? hw / Math.abs(dx) : Infinity
  const ty = dy !== 0 ? hh / Math.abs(dy) : Infinity
  const t = Math.min(tx, ty)
  return { x: (p.x + dx * t).toFixed(2), y: (p.y + dy * t).toFixed(2) }
}

const lineOpacity = (i) => {
  const t = (props.parts[i]?.start_time ?? i * motion.value.stagger_ms) + motion.value.appear_ms * 0.4
  return ease(clamp01((relativeTime.value - t) / (motion.value.appear_ms || 500))).toFixed(3)
}

const cardStyle = (i) => ({
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: getColorAlpha(accent(i), 0.5),
})

const hubStyle = {
  background: 'var(--item-primary-bg)',
  backdropFilter: 'var(--item-primary-backdrop)',
  WebkitBackdropFilter: 'var(--item-primary-backdrop)',
  borderRadius: '9999px',
  borderWidth: 'var(--item-primary-border-width)',
  borderStyle: 'var(--item-primary-border-style)',
  borderColor: getColorAlpha('var(--color-secondary)', 0.55),
  boxShadow: 'var(--item-primary-shadow)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!parts.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative flex-1 min-h-0 overflow-hidden">
        <svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
          <line
            v-for="p in placed"
            :key="'ln' + p._i"
            x1="50" y1="50" :x2="edgePoint(p).x" :y2="edgePoint(p).y"
            :stroke="getColorAlpha(accent(p._i), 0.45)"
            stroke-width="1.2"
            vector-effect="non-scaling-stroke"
            :style="{ opacity: lineOpacity(p._i) }"
          />
        </svg>

        <div
          class="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-2"
          :class="mobile ? 'top-[40%]' : 'top-1/2'"
        >
          <div
            class="flex items-center justify-center"
            :class="mobile ? 'w-16 h-16' : 'w-24 h-24'"
            :style="hubStyle"
          >
            <Icon :icon="center_icon" :class="mobile ? 'w-7 h-7' : 'w-11 h-11'" :style="{ color: getHexColor('var(--color-secondary)') }" />
          </div>
          <span v-if="center_label" class="text-base font-heading font-bold text-text-primary">{{ center_label }}</span>
        </div>

        <div
          v-for="p in placed"
          :key="p.name + p._i"
          class="absolute"
          :style="{ left: p.x + '%', top: p.y + '%', transform: 'translate(-50%, -50%)', width: mobile ? '42%' : '30%' }"
        >
          <div class="flex flex-col items-center text-center px-3 py-3" :style="[cardStyle(p._i), reveal(p, p._i)]">
            <div
              class="w-10 h-10 flex items-center justify-center mb-2 rounded-full"
              :style="{ background: getColorAlpha(accent(p._i), 0.16), border: '1px solid ' + getHexColor(accent(p._i)) }"
            >
              <Icon :icon="p.icon || 'lucide:circle-dot'" class="w-5 h-5" :style="{ color: getHexColor(accent(p._i)) }" />
            </div>
            <p class="font-heading font-bold text-text-primary" :class="mobile ? 'text-sm' : 'text-base'">{{ p.name }}</p>
            <p class="text-[11px] text-text-secondary leading-snug mt-1">{{ p.function }}</p>
          </div>
        </div>
      </div>

      <div v-if="source" class="mt-2 shrink-0 text-right text-[11px] font-mono text-text-muted">{{ source }}</div>
    </template>
  </div>
</template>
