<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import NodeFlow from './NodeFlow.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  site_image: { type: String, default: '' },
  objects: { type: Array, default: () => [] },
  flows: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'SiteLogisticsMap')
const relativeTime = inject('relativeTime', ref(0))
const imgFailed = ref(false)

const TYPE_META = {
  crane: { icon: 'lucide:construction', status: 'warn', label: 'Кран' },
  warehouse: { icon: 'lucide:warehouse', status: 'ok', label: 'Склад' },
  road: { icon: 'lucide:route', status: 'muted', label: 'Дорога' },
  gate: { icon: 'lucide:door-open', status: 'info', label: 'КПП' },
  office: { icon: 'lucide:hard-hat', status: 'info', label: 'Бытовка' },
  zone: { icon: 'lucide:square-dashed', status: 'muted', label: 'Зона работ' },
}
const metaOf = (t) => TYPE_META[t] || TYPE_META.zone

const nodes = computed(() =>
  (props.objects || []).map((o, i) => ({
    id: o.id || `o${i}`,
    label: o.label,
    x: Number(o.x) || 50,
    y: Number(o.y) || 50,
    icon: metaOf(o.type).icon,
    status: metaOf(o.type).status,
    meta: metaOf(o.type).label,
    start_time: o.start_time ?? i * motion.value.stagger_ms,
  })),
)

const edges = computed(() => (props.flows || []).map((f) => ({ from: f.from, to: f.to, label: f.label })))

const legend = computed(() => {
  const types = [...new Set((props.objects || []).map((o) => o.type).filter(Boolean))]
  return types.map((t) => ({ type: t, ...metaOf(t) }))
})

const flowList = computed(() =>
  (props.flows || []).map((f) => {
    const from = (props.objects || []).find((o) => o.id === f.from)
    const to = (props.objects || []).find((o) => o.id === f.to)
    return { label: f.label, from: from?.label || f.from, to: to?.label || f.to }
  }),
)

const lastStart = computed(() =>
  nodes.value.length ? Math.max(...nodes.value.map((n) => Number(n.start_time) || 0)) : 0,
)

const flowReveal = (i) => {
  const start = lastStart.value + 100 + i * 120
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
}

const summaryReveal = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - lastStart.value - 100) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-3" :style="{ ...itemVars }">
    <div v-if="!objects.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between">
        <span class="flex items-center gap-2 text-[11px] font-mono text-text-muted">
          <Icon icon="lucide:traffic-cone" class="w-3.5 h-3.5" />
          {{ objects.length }} объектов · {{ flows.length }} потоков
        </span>
        <span class="text-[10px] uppercase tracking-widest font-mono text-text-muted">Стройгенплан</span>
      </div>

      <div
        class="relative w-full flex-1 min-h-0 overflow-hidden"
        :style="{
          background: 'var(--item-primary-bg)',
          backdropFilter: 'var(--item-primary-backdrop)',
          WebkitBackdropFilter: 'var(--item-primary-backdrop)',
          borderRadius: 'var(--item-radius)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-border)',
        }"
      >
        <img
          v-if="site_image && !imgFailed"
          :src="site_image"
          alt="Стройгенплан"
          class="absolute inset-0 w-full h-full object-cover"
          @error="imgFailed = true"
        />
        <div
          v-if="site_image && !imgFailed"
          class="absolute inset-0 pointer-events-none"
          :style="{ background: 'rgb(var(--bg-base-rgb) / 0.55)' }"
        ></div>

        <!-- Стилизованная подложка стройгенплана -->
        <svg v-if="!site_image || imgFailed" class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
          <g :stroke="getColorAlpha('var(--text-muted)', 0.22)" stroke-width="1" vector-effect="non-scaling-stroke">
            <line v-for="n in 9" :key="'gx' + n" :x1="n * 10" y1="0" :x2="n * 10" y2="100" />
            <line v-for="n in 5" :key="'gy' + n" x1="0" :y1="n * 16.6" x2="100" :y2="n * 16.6" />
          </g>
          <g fill="none" :stroke="getColorAlpha('var(--text-muted)', 0.4)" stroke-width="1.5" vector-effect="non-scaling-stroke">
            <rect x="8" y="12" width="84" height="76" rx="2" />
          </g>
        </svg>

        <NodeFlow
          class="relative z-10 h-full px-8 md:px-14"
          :variant="variant"
          :mobile="mobile"
          :density="density"
          :nodes="nodes"
          :edges="edges"
          flow_layout="coords"
        />
      </div>

      <div class="shrink-0 flex flex-wrap items-center gap-x-4 gap-y-1" :style="summaryReveal">
        <span v-for="(l, i) in legend" :key="l.type + i" class="flex items-center gap-1.5 text-[11px] text-text-secondary">
          <Icon :icon="l.icon" class="w-3.5 h-3.5" />{{ l.label }}
        </span>
        <span v-if="source_note" class="ml-auto text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</span>
      </div>

      <div v-if="flowList.length" class="shrink-0 flex flex-wrap gap-x-4 gap-y-1">
        <span
          v-for="(f, i) in flowList"
          :key="'fl' + i"
          class="flex items-center gap-1.5 text-[11px] text-text-secondary"
          :style="flowReveal(i)"
        >
          <Icon icon="lucide:move-right" class="w-3.5 h-3.5 shrink-0" :style="{ color: getHexColor('var(--color-secondary)') }" />
          <span class="truncate">{{ f.from }}</span>
          <Icon icon="lucide:arrow-right" class="w-3 h-3 shrink-0 text-text-muted" />
          <span class="truncate">{{ f.to }}</span>
          <span v-if="f.label" class="font-mono text-text-muted truncate">{{ f.label }}</span>
        </span>
      </div>
    </template>
  </div>
</template>
