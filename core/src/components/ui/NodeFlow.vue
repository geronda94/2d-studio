<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  flow_layout: { type: String, default: 'layered' }, // layered | radial | coords
  mobile_lo: { type: Number, default: 30 },
  mobile_hi: { type: Number, default: 70 },
  mobile_lo_y: { type: Number, default: null },
  mobile_hi_y: { type: Number, default: null },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'NodeFlow')
const relativeTime = inject('relativeTime', ref(0))

const STATUS_TOKEN = {
  ok: 'var(--color-success)', success: 'var(--color-success)',
  warn: 'var(--color-warning)', warning: 'var(--color-warning)',
  error: 'var(--color-danger)', danger: 'var(--color-danger)', risk: 'var(--color-danger)',
  info: 'var(--color-secondary)', active: 'var(--color-secondary)',
  muted: 'var(--text-muted)',
}
const statusColor = (n) => getHexColor(STATUS_TOKEN[n.status] || 'var(--color-secondary)')

const clamp = (v) => Math.max(0, Math.min(100, Number(v) || 0))
// Растягиваем набор координат на рабочий диапазон, чтобы диаграмма заполняла кадр
// (данные часто приходят скученными в узкой полосе).
const spread = (vals, lo, hi) => {
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  if (!isFinite(min) || !isFinite(max) || max - min < 0.001) {
    return vals.map(() => (lo + hi) / 2)
  }
  return vals.map((v) => lo + ((v - min) / (max - min)) * (hi - lo))
}

const positions = computed(() => {
  const list = props.nodes || []
  const map = {}
  if (!list.length) return map

  if (props.flow_layout === 'coords') {
    // Портрет: произвольные координаты (x/y) дают наложения широких подписей.
    // Раскладываем ноды в один столбец — читаемо и без пересечений.
    if (props.mobile) {
      const n = list.length
      list.forEach((node, i) => {
        const y = n <= 1 ? 50 : 12 + (i / (n - 1)) * 76
        map[node.id] = { x: 50, y }
      })
      return map
    }
    const loX = props.mobile ? props.mobile_lo : 10
    const hiX = props.mobile ? props.mobile_hi : 90
    const loY = props.mobile ? (props.mobile_lo_y ?? props.mobile_lo) : 14
    const hiY = props.mobile ? (props.mobile_hi_y ?? props.mobile_hi) : 86
    const xs = spread(list.map((n) => clamp(n.x ?? 50)), loX, hiX)
    const ys = spread(list.map((n) => clamp(n.y ?? 50)), loY, hiY)
    list.forEach((n, i) => (map[n.id] = { x: xs[i], y: ys[i] }))
    return map
  }

  if (props.flow_layout === 'radial') {
    list.forEach((n, i) => {
      if (i === 0) { map[n.id] = { x: 50, y: 50 }; return }
      const a = ((i - 1) / Math.max(1, list.length - 1)) * Math.PI * 2 - Math.PI / 2
      map[n.id] = { x: 50 + Math.cos(a) * 40, y: 50 + Math.sin(a) * 38 }
    })
    return map
  }

  // layered (BFS) → змеевидная сетка, чтобы этапы укладывались в кадр,
  // а не вытягивались в одну тонкую строку.
  const ids = new Set(list.map((n) => n.id))
  const indeg = {}
  list.forEach((n) => (indeg[n.id] = 0))
  ;(props.edges || []).forEach((e) => { if (ids.has(e.to)) indeg[e.to] = (indeg[e.to] || 0) + 1 })
  const level = {}
  const queue = list.filter((n) => !indeg[n.id]).map((n) => n.id)
  if (!queue.length && list.length) queue.push(list[0].id)
  queue.forEach((id) => (level[id] = 0))
  let guard = 0
  while (queue.length && guard < 1000) {
    guard++
    const id = queue.shift()
    ;(props.edges || []).filter((e) => e.from === id).forEach((e) => {
      if (!ids.has(e.to)) return
      const cand = level[id] + 1
      if (level[e.to] === undefined || cand > level[e.to]) { level[e.to] = cand; queue.push(e.to) }
    })
  }
  list.forEach((n) => { if (level[n.id] === undefined) level[n.id] = 0 })

  // Простая цепочка (у каждого узла ≤1 вход и ≤1 выход) → зигзаг по всей
  // площади кадра: узлы распределяются и по ширине, и по высоте, без пустой
  // полосы посередине (прошлый баг: 3 сверху + 2 снизу = ~60% кадра).
  const outDeg = {}
  const inDeg = {}
  list.forEach((n) => { outDeg[n.id] = 0; inDeg[n.id] = 0 })
  ;(props.edges || []).forEach((e) => {
    if (!ids.has(e.to) || !ids.has(e.from)) return
    outDeg[e.from] = (outDeg[e.from] || 0) + 1
    inDeg[e.to] = (inDeg[e.to] || 0) + 1
  })
  const isPath = list.length > 2 && list.every((n) => (outDeg[n.id] || 0) <= 1 && (inDeg[n.id] || 0) <= 1)
  if (isPath) {
    const start = list.find((n) => !inDeg[n.id]) || list[0]
    const order = []
    const seen = new Set()
    let cur = start
    let guard = 0
    while (cur && !seen.has(cur.id) && guard < 1000) {
      guard++
      seen.add(cur.id)
      order.push(cur)
      const e = (props.edges || []).find((x) => x.from === cur.id && ids.has(x.to))
      cur = e ? list.find((n) => n.id === e.to) : null
    }
    list.forEach((n) => { if (!seen.has(n.id)) order.push(n) })
    order.forEach((node, i) => {
      const t = order.length > 1 ? i / (order.length - 1) : 0.5
      const x = 9 + t * 82
      const y = i % 2 === 0 ? 16 : 84
      map[node.id] = props.mobile ? { x: y, y: x } : { x, y }
    })
    return map
  }

  const ordered = [...list].sort((a, b) => (level[a.id] - level[b.id]))
  const n = ordered.length
  const cols = props.mobile ? 2 : (n <= 3 ? n : n <= 8 ? 3 : 4)
  const rows = Math.max(1, Math.ceil(n / cols))
  ordered.forEach((node, i) => {
    const row = Math.floor(i / cols)
    let col = i % cols
    if (row % 2 === 1) col = cols - 1 - col
    const x = 10 + (cols === 1 ? 40 : (col / (cols - 1)) * 80)
    const y = rows === 1 ? 50 : 12 + (row / (rows - 1)) * 72
    map[node.id] = props.mobile ? { x: y, y: x } : { x, y }
  })
  return map
})

const posOf = (id) => positions.value[id] || { x: 50, y: 50 }

const nodeReveal = (n, i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (n.start_time ?? i * motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.7 + 0.3 * e).toFixed(3)})` }
}
const edgeReveal = (e) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (e.start_time ?? 0)) / 600))
  return { opacity: (0.25 + 0.6 * p).toFixed(3) }
}

// Подписи связей — на выделенном отступе от линии (перпендикуляр), с подложкой,
// чтобы не наезжать на ноды и не сливаться с пунктиром.
const labelPos = (e, idx = 0) => {
  const a = posOf(e.from)
  const b = posOf(e.to)
  const mx = (a.x + b.x) / 2
  const my = (a.y + b.y) / 2
  const dx = b.x - a.x
  const dy = b.y - a.y
  const len = Math.hypot(dx, dy) || 1
  // Знак отступа чередуем: соседние подписи уходят по разные стороны линий
  // и не сливаются в один ком (прошлый баг: «партия · 30 мин» поверх «партия · 90 мин»).
  const off = (props.mobile ? 6 : 5) * (idx % 2 === 0 ? 1 : -1)
  return { left: `${(mx - (dy / len) * off).toFixed(2)}%`, top: `${(my + (dx / len) * off).toFixed(2)}%` }
}

const compact = computed(() => props.density === 'compact' || props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!nodes.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0">
        <svg class="absolute inset-0 w-full h-full pointer-events-none">
          <defs>
            <marker :id="'nf-arrow-' + (variant || 'x')" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8" fill="none" stroke="var(--text-muted)" stroke-width="1" />
            </marker>
          </defs>
          <line
            v-for="(e, i) in edges"
            :key="'e' + i"
            :x1="posOf(e.from).x + '%'" :y1="posOf(e.from).y + '%'"
            :x2="posOf(e.to).x + '%'" :y2="posOf(e.to).y + '%'"
            stroke="var(--text-muted)"
            stroke-width="2.2"
            stroke-dasharray="7 7"
            vector-effect="non-scaling-stroke"
            :style="edgeReveal(e)"
          />
        </svg>

        <div
          v-for="(n, i) in nodes"
          :key="n.id ?? i"
          class="absolute z-10"
          :style="[{ left: posOf(n.id).x + '%', top: posOf(n.id).y + '%', willChange: 'transform' }, nodeReveal(n, i)]"
        >
          <div
            class="flex items-center whitespace-nowrap"
            :class="mobile ? 'gap-2 px-3.5 py-2 max-w-[190px]' : 'gap-3 px-6 py-3.5 max-w-[300px]'"
            :style="{
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              WebkitBackdropFilter: 'var(--item-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              padding: 'var(--item-padding)',
              border: '1.5px solid ' + getColorAlpha(statusColor(n), 0.55),
            }"
          >
            <Icon v-if="n.icon" :icon="n.icon" class="shrink-0" :class="mobile ? 'w-4 h-4' : 'w-6 h-6'" :style="{ color: statusColor(n) }" />
            <span class="text-text-primary font-bold truncate" :class="mobile ? 'text-sm' : 'text-lg'">{{ n.label }}</span>
          </div>
          <span
            v-if="n.meta && !compact"
            class="absolute left-1/2 -translate-x-1/2 top-full mt-1 px-1.5 py-0.5 text-[11px] font-mono text-text-secondary whitespace-nowrap rounded"
            :style="{ background: 'rgb(var(--bg-base-rgb) / 0.65)' }"
          >{{ n.meta }}</span>
        </div>

        <!-- подписи связей -->
        <span
          v-for="(e, i) in edges.filter((x) => x.label)"
          :key="'el' + i"
          class="absolute z-20 -translate-x-1/2 -translate-y-1/2 text-[11px] font-mono px-1.5 py-0.5 rounded whitespace-nowrap"
          :style="[labelPos(e, i), { background: 'rgb(var(--bg-base-rgb) / 0.8)', color: 'var(--text-secondary)' }, edgeReveal(e)]"
        >{{ e.label }}<template v-if="e.duration_label"> · {{ e.duration_label }}</template></span>
      </div>

      <div v-if="source_note" class="shrink-0 mt-2 text-center text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</div>
    </template>
  </div>
</template>
