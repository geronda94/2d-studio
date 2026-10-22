<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  nodes: { type: Array, default: () => [] },
  orientation: { type: String, default: 'generations' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'GenealogyTree')
const relativeTime = inject('relativeTime', ref(0))

const generations = computed(() => {
  const gens = []
  const walk = (list, depth, parentKey) => {
    ;(list || []).forEach((n) => {
      const key = n.id ?? n.name
      gens[depth] = gens[depth] || []
      gens[depth].push({ node: n, key, parent: parentKey, depth, idx: gens[depth].length })
      if (Array.isArray(n.children) && n.children.length) walk(n.children, depth + 1, key)
    })
  }
  walk(props.nodes, 0, null)
  return gens
})

const maxGen = computed(() => Math.max(1, ...generations.value.map((g) => g.length)))

// Раскладываем каждое поколение по общей сетке maxGen колонок и центрируем
// группу — так карточки во всех рядах одинаковой ширины (прошлый баг:
// ряд из одной ноды растягивался на всю ширину).
const layout = computed(() =>
  generations.value.map((gen) => {
    const offset = Math.floor((maxGen.value - gen.length) / 2)
    return gen.map((e, idx) => ({ ...e, col: offset + idx }))
  }),
)

const colOf = computed(() => {
  const m = {}
  layout.value.forEach((gen) => gen.forEach((e) => { m[e.key] = e.col }))
  return m
})

const gapLines = computed(() => {
  const res = []
  for (let g = 1; g < layout.value.length; g++) {
    res[g] = layout.value[g].map((e) => {
      const pc = colOf.value[e.parent]
      return {
        key: e.key,
        x1: pc === undefined ? 50 : ((pc + 0.5) / maxGen.value) * 100,
        x2: ((e.col + 0.5) / maxGen.value) * 100,
      }
    })
  }
  return res
})

const flatList = computed(() => generations.value.flat())

const isList = computed(() => props.orientation === 'list' || props.mobile)
const accent = (depth) => getHexColor(`var(--item-accent-${(depth % 4) + 1})`)

const progress = (start) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (start ?? 0)) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const nodeReveal = (entry, gi) => {
  const start = entry.node.start_time ?? gi * motion.value.stagger_ms
  const e = progress(start)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const lineReveal = (gi) => {
  const e = progress(gi * motion.value.stagger_ms)
  return { opacity: (0.25 + 0.65 * e).toFixed(3) }
}

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
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!flatList.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else-if="isList" class="flex-1 min-h-0 flex flex-col" :class="mobile ? 'overflow-hidden' : 'overflow-auto'" :style="{ gap: 'var(--item-gap)' }">
      <div
        v-for="entry in flatList"
        :key="entry.key"
        class="flex items-center gap-2"
        :style="[{ paddingLeft: (entry.depth * (mobile ? 12 : 18)) + 'px' }, nodeReveal(entry, entry.depth)]"
      >
        <span class="w-2 h-2 rounded-full shrink-0" :style="{ background: accent(entry.depth) }"></span>
        <div class="min-w-0 flex-1" :style="cardStyle">
          <p class="font-heading font-bold text-text-primary text-sm truncate">{{ entry.node.name }}</p>
          <p v-if="entry.node.note" class="text-[11px] text-text-muted truncate">{{ entry.node.note }}</p>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex flex-col">
      <template v-for="(gen, gi) in layout" :key="gi">
        <div class="grid gap-2 md:gap-3 w-full flex-1 min-h-0" :style="{ gridTemplateColumns: `repeat(${maxGen}, minmax(0, 1fr))` }">
          <div
            v-for="entry in gen"
            :key="entry.key"
            class="min-h-0"
            :style="[{ gridColumn: entry.col + 1 }, nodeReveal(entry, gi)]"
          >
            <div class="h-full overflow-hidden" :style="cardStyle">
              <div class="flex items-center gap-2 min-w-0">
                <span
                  class="w-2.5 h-2.5 rounded-full shrink-0"
                  :style="{ background: accent(gi), boxShadow: '0 0 0 3px ' + getColorAlpha(accent(gi), 0.18) }"
                ></span>
                <p class="font-heading font-bold text-text-primary text-sm truncate">{{ entry.node.name }}</p>
              </div>
              <p v-if="entry.node.note" class="mt-0.5 text-[10px] text-text-muted leading-snug">{{ entry.node.note }}</p>
            </div>
          </div>
        </div>

        <div v-if="gi < layout.length - 1" class="relative w-full shrink-0" :style="{ height: mobile ? '16px' : '22px' }">
          <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <line
              v-for="line in gapLines[gi + 1]"
              :key="line.key"
              :x1="line.x1" y1="0" :x2="line.x2" y2="100"
              stroke="var(--color-secondary)"
              stroke-width="1.5"
              stroke-dasharray="4 4"
              vector-effect="non-scaling-stroke"
              :style="lineReveal(gi + 1)"
            />
          </svg>
        </div>
      </template>
    </div>
  </div>
</template>
