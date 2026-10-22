<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  nodes: { type: Array, default: () => [] },
  layout: { type: String, default: 'vertical' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'OrgChart')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const flat = computed(() => {
  const out = []
  const walk = (list, depth, guides) => {
    ;(list || []).forEach((n, i) => {
      const isLast = i === (list.length - 1)
      out.push({ node: n, depth, isLast, guides: [...guides] })
      if (Array.isArray(n.children) && n.children.length) {
        walk(n.children, depth + 1, [...guides, !isLast])
      }
    })
  }
  walk(props.nodes, 0, [])
  return out
})

const roots = computed(() => (props.nodes || []).length)
const totalHead = computed(() => flat.value.reduce((acc, r) => acc + (Number(r.node.headcount) || 0), 0))

const plural = (n, one, few, many) => {
  const abs = Math.abs(n) % 100
  const d = abs % 10
  if (abs > 10 && abs < 20) return many
  if (d === 1) return one
  if (d >= 2 && d <= 4) return few
  return many
}
const functionsLabel = computed(() => plural(roots.value, 'функция', 'функции', 'функций'))
const peopleLabel = computed(() => plural(totalHead.value, 'человек', 'человека', 'человек'))

const initials = (name) =>
  String(name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()

// Каскад появления: для крупных деревьев шаг сжимается, чтобы все строки
// успели проявиться за время слайда (иначе нижние уровни остаются невидимыми).
const step = computed(() => Math.min(motion.value.stagger_ms, Math.max(120, 2500 / Math.max(1, flat.value.length - 1))))

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * step.value) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateX(${((1 - e) * -10).toFixed(2)}px)` }
}

const showBars = computed(() => props.layout === 'horizontal' || props.layout === 'board')
const compact = computed(() => props.mobile)

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  padding: '4px 10px',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!flat.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between mb-2 gap-2">
        <span class="text-[10px] font-mono uppercase tracking-widest text-text-muted">Оргструктура</span>
        <div class="flex items-center gap-4 text-[10px] font-mono text-text-secondary">
          <span class="flex items-center gap-1.5">
            <Icon icon="lucide:network" class="w-3.5 h-3.5" :style="{ color: 'var(--color-secondary)' }" />
            {{ roots }} {{ functionsLabel }}
          </span>
          <span class="flex items-center gap-1.5">
            <Icon icon="lucide:users" class="w-3.5 h-3.5" :style="{ color: 'var(--item-accent-2)' }" />
            {{ totalHead }} {{ peopleLabel }}
          </span>
        </div>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden">
        <div class="w-full py-0.5">
          <div v-for="(row, i) in flat" :key="row.node.id || row.node.name + i" class="flex items-stretch" :class="compact ? 'min-h-[36px]' : 'min-h-[38px]'">
            <template v-for="(g, L) in row.guides" :key="'g' + i + '-' + L">
              <div class="relative shrink-0" :class="compact ? 'w-4' : 'w-6'">
                <template v-if="L < row.depth - 1">
                  <div
                    v-if="g"
                    class="absolute left-1/2 top-0 bottom-0 w-px"
                    :style="{ background: 'var(--item-border)' }"
                  ></div>
                </template>
                <template v-else>
                  <div
                    class="absolute left-1/2 top-0 bottom-1/2 w-px"
                    :style="{ background: 'var(--item-border)' }"
                  ></div>
                  <div
                    v-if="g"
                    class="absolute left-1/2 top-1/2 bottom-0 w-px"
                    :style="{ background: 'var(--item-border)' }"
                  ></div>
                  <div
                    class="absolute left-1/2 top-1/2 h-px"
                    :style="{ width: '50%', background: 'var(--item-border)' }"
                  ></div>
                </template>
              </div>
            </template>

            <div class="flex items-center gap-2.5 my-0 flex-1 min-w-0" :style="[cardStyle, reveal(i)]">
              <div
                class="flex items-center justify-center shrink-0 rounded-full font-bold"
                :class="compact ? 'w-6 h-6 text-[9px]' : 'w-7 h-7 text-[10px]'"
                :style="{
                  background: getColorAlpha(accent(row.depth), 0.16),
                  color: accent(row.depth),
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderColor: getColorAlpha(accent(row.depth), 0.5),
                }"
              >{{ initials(row.node.name) }}</div>

              <div class="min-w-0 flex-1">
                <div class="text-[13px] font-bold text-text-primary leading-tight truncate">{{ row.node.name }}</div>
                <div class="text-[10px] text-text-muted leading-tight truncate">{{ row.node.title }}</div>
                <div
                  v-if="showBars"
                  class="mt-1 h-1 w-full overflow-hidden"
                  :style="{ background: getColorAlpha('var(--text-primary)', 0.08), borderRadius: '999px' }"
                >
                  <div
                    class="h-full w-full origin-left"
                    :style="{ background: accent(row.depth), transform: `scaleX(${Math.min(1, (Number(row.node.headcount) || 0) / 8)})` }"
                  ></div>
                </div>
              </div>

              <div
                class="ml-auto flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 shrink-0"
                :style="{
                  color: accent(row.depth),
                  background: getColorAlpha(accent(row.depth), 0.12),
                  borderRadius: 'calc(var(--item-radius) * 0.5)',
                }"
              >
                <Icon icon="lucide:users" class="w-3 h-3" />
                {{ row.node.headcount }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
