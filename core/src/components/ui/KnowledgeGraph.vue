<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  concepts: { type: Array, default: () => [] },
  connections: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'KnowledgeGraph')
const relativeTime = inject('relativeTime', ref(0))

// Радиальная авто-раскладка: центральные концепции (is_main) в центре,
// остальные по кругу. x/y в нормализованных координатах 0..100.
const layout = computed(() => {
  const list = props.concepts || []
  const n = list.length
  const map = {}
  const center = list.filter((c) => c.is_main)
  const ring = list.filter((c) => !c.is_main)
  center.forEach((c, i) => {
    map[c.id] = { x: 50 + (i - (center.length - 1) / 2) * 10, y: 50 }
  })
  const rx = props.mobile ? 30 : 40
  const ry = props.mobile ? 32 : 38
  ring.forEach((c, i) => {
    const angle = (i / Math.max(1, ring.length)) * Math.PI * 2 - Math.PI / 2
    map[c.id] = { x: 50 + Math.cos(angle) * rx, y: 50 + Math.sin(angle) * ry }
  })
  if (!center.length && n) {
    list.forEach((c, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2
      map[c.id] = { x: 50 + Math.cos(angle) * rx, y: 50 + Math.sin(angle) * ry }
    })
  }
  return map
})

const pos = (id) => layout.value[id] || { x: 50, y: 50 }

// Человекочитаемая подпись для id (легенда не должна печатать «kg0 → kg1»).
const labelOf = (id) => {
  const c = (props.concepts || []).find((x) => x.id === id)
  return c?.label || id
}

const mobileOrder = computed(() => {
  const list = props.concepts || []
  return [...list.filter((c) => c.is_main), ...list.filter((c) => !c.is_main)]
})

const edgeNote = (id) => {
  const outs = (props.connections || []).filter((cn) => cn.from === id)
  if (!outs.length) return ''
  return outs.map((cn) => `→ ${labelOf(cn.to)}${cn.label ? ' · ' + cn.label : ''}`).join('   ')
}

// На mobile — вертикальный список (как GenealogyTree): радиальная раскладка
// с длинными подписями наезжает узлами друг на друга.
const listReveal = (c, idx) => {
  const t = c.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const nodeReveal = (c, idx) => {
  const t = c.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.7 + 0.3 * e).toFixed(3)})` }
}

const connReveal = (cn, idx) => {
  const t = cn.start_time ?? (idx + 1) * 400
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / 600))
  return p
}

const lineCoords = (cn) => {
  const a = pos(cn.from)
  const b = pos(cn.to)
  return {
    x1: `${a.x}%`,
    y1: `${a.y}%`,
    x2: `${b.x}%`,
    y2: `${b.y}%`,
    opacity: connReveal(cn, props.connections.indexOf(cn)),
  }
}

const accent = (c) => getHexColor(c.color || 'var(--color-secondary)')
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col self-stretch" :style="{ ...itemVars }">
    <div v-if="mobile" class="flex-1 min-h-0 overflow-hidden flex flex-col py-1" :style="{ gap: 'var(--item-gap)' }">
      <div
        v-for="(c, idx) in mobileOrder"
        :key="(c.id ?? idx) + '-m'"
        class="flex flex-col"
        :style="listReveal(c, idx)"
      >
        <div
          class="flex items-center gap-2"
          :style="{ paddingLeft: c.is_main ? '0px' : '18px' }"
        >
          <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: accent(c) }"></span>
          <div class="min-w-0 flex-1 py-1.5 px-3" :style="cardStyle">
            <div class="flex items-center gap-2 min-w-0">
              <Icon v-if="c.icon" :icon="c.icon" class="w-4 h-4 shrink-0" :style="{ color: accent(c) }" />
              <span class="font-bold text-text-primary truncate" :class="c.is_main ? 'text-base' : 'text-sm'">{{ c.label }}</span>
            </div>
          </div>
        </div>
        <!-- Связь видна прямо под узлом: «↑ влияет на …» — иначе на мобиле граф нечитаем -->
        <div
          v-for="(cn, ci) in (connections || []).filter((x) => x.from === c.id)"
          :key="'me' + idx + ci"
          class="flex items-center gap-1.5 text-[10px] font-mono text-text-muted"
          :style="{ paddingLeft: (c.is_main ? '0px' : '18px'), marginLeft: 'inherit' }"
        >
          <Icon icon="lucide:corner-down-right" class="w-3 h-3 shrink-0" :style="{ color: accent(c) }" />
          <span>{{ cn.label || 'влияет' }} → </span>
          <span class="text-text-secondary">{{ labelOf(cn.to) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="relative w-full flex-1 min-h-[300px]">
      <svg class="absolute inset-0 w-full h-full" preserveAspectRatio="none">
        <line
          v-for="(cn, idx) in connections"
          :key="'l' + idx"
          v-bind="lineCoords(cn)"
          :stroke="getHexColor('var(--color-secondary)')"
          stroke-width="1.5"
          stroke-dasharray="6 8"
          vector-effect="non-scaling-stroke"
        />
      </svg>

      <div
        v-for="(c, idx) in concepts"
        :key="c.id ?? idx"
        class="absolute flex flex-col items-center"
        :style="[{ left: pos(c.id).x + '%', top: pos(c.id).y + '%', willChange: 'transform' }, nodeReveal(c, idx)]"
      >
        <div
          class="flex items-center rounded-full whitespace-nowrap"
          :class="c.is_main
            ? (mobile ? 'gap-2 px-4 py-2.5' : 'gap-2.5 px-6 py-3.5')
            : (mobile ? 'gap-1.5 px-3 py-1.5' : 'gap-2 px-4 py-2.5')"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            border: (c.is_main ? '2px solid ' : '1.5px solid ') + getColorAlpha(accent(c), 0.5),
          }"
        >
          <Icon
            v-if="c.icon"
            :icon="c.icon"
            :class="c.is_main
              ? (mobile ? 'w-4 h-4' : 'w-6 h-6')
              : (mobile ? 'w-3.5 h-3.5' : 'w-5 h-5')"
            :style="{ color: accent(c) }"
          />
          <span
            class="text-text-primary font-bold"
            :class="c.is_main
              ? (mobile ? 'text-sm' : 'text-lg')
              : (mobile ? 'text-xs' : 'text-base')"
          >{{ c.label }}</span>
        </div>
      </div>
    </div>

    <div v-if="!mobile && (connections || []).length" class="mt-4 flex flex-wrap gap-x-4 gap-y-1 justify-center">
      <span v-for="(cn, idx) in connections" :key="'cl' + idx" class="text-[11px] font-mono text-text-muted">
        {{ labelOf(cn.from) }} → {{ labelOf(cn.to) }}<span v-if="cn.label"> · {{ cn.label }}</span>
      </span>
    </div>
  </div>
</template>
