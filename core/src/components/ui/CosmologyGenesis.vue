<script setup>
// CosmologyGenesis — Большой взрыв ↔ Дни творения (этапы).
// Композиция примитива ProcessFunnel: этап → иконка, день, библейский образ; ниже — пара «эпоха · время».
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import ProcessFunnel from './ProcessFunnel.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  stages: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'CosmologyGenesis')
const relativeTime = inject('relativeTime', ref(0))

const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}

const sourceReveal = computed(() => {
  const t = (props.stages?.length || 0) * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(4) }
})

const accent = (i) => `var(--chart-${(i % 6) + 1})`

const steps = computed(() => (props.stages || []).map((s, i) => ({
  label: s.biblical,
  count: i + 1,
  icon: s.icon || 'lucide:sparkles',
  color: s.color || accent(i),
  start_time: s.start_time ?? i * motion.value.stagger_ms,
})))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!stages.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div
        class="relative flex-1 min-h-0 overflow-hidden flex flex-col gap-3"
        :class="mobile ? '[&_.h-16]:h-11 [&_.w-16]:w-11 [&_.w-8]:w-6 [&_.h-8]:h-6 [&_.py-8]:py-3 [&_.text-2xl]:text-lg' : ''"
      >
        <div class="flex-1 min-h-0">
          <ProcessFunnel :variant="variant" :mobile="mobile" layout="horizontal" :steps="steps" />
        </div>

        <div
          class="shrink-0 grid gap-x-3 gap-y-1.5 px-2"
          :class="mobile ? 'grid-cols-2' : ''"
          :style="!mobile ? { gridTemplateColumns: `repeat(${stages.length}, minmax(0, 1fr))` } : {}"
        >
          <div
            v-for="(s, i) in stages"
            :key="'e' + i"
            class="text-center min-w-0"
            :style="reveal(s, i)"
          >
            <div class="text-[11px] md:text-xs font-mono" :style="{ color: accent(i) }">{{ s.epoch }}</div>
            <div class="text-[11px] md:text-xs text-text-secondary leading-tight truncate">{{ s.cosmic }}</div>
          </div>
        </div>

        <p
          v-if="source"
          class="shrink-0 text-center text-[11px] font-mono text-text-muted opacity-70"
          :style="sourceReveal"
        >{{ source }}</p>
      </div>
    </template>
  </div>
</template>
