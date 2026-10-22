<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'
import ProcessFunnel from './ProcessFunnel.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  stages: { type: Array, default: () => [] },
  source: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'StagesOfSin')
const relativeTime = inject('relativeTime', ref(0))

const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const reveal = (item, i) => {
  const t = item.start_time ?? i * motion.value.stagger_ms
  const e = ease(clamp01((relativeTime.value - t) / (motion.value.appear_ms || 500)))
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}

const STAGE_COLORS = ['var(--color-warning)', 'var(--color-accent)', 'var(--color-danger)', 'var(--color-error)']
const accent = (i) => STAGE_COLORS[Math.min(i, STAGE_COLORS.length - 1)]

const steps = computed(() => (props.stages || []).map((s, i) => ({
  label: s.name,
  count: i + 1,
  icon: s.icon || 'lucide:circle-dot',
  color: s.color || accent(i),
  start_time: s.start_time ?? i * motion.value.stagger_ms,
})))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!stages.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div
        class="relative flex-1 min-h-0 overflow-hidden flex items-center"
        :class="mobile ? '[&_.h-16]:h-11 [&_.w-16]:w-11 [&_.w-8]:w-6 [&_.h-8]:h-6 [&_.py-8]:py-3 [&_.text-2xl]:text-lg' : ''"
      >
        <ProcessFunnel :variant="variant" :mobile="mobile" layout="horizontal" :show_conversion="false" :steps="steps" />
      </div>

      <div class="shrink-0 grid gap-2 auto-rows-fr" :class="mobile ? 'grid-cols-1' : 'grid-cols-2'">
        <div
          v-for="(s, i) in stages"
          :key="'d' + i"
          class="flex items-start gap-2"
          :style="reveal(s, i)"
        >
          <span
            class="mt-0.5 w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-[10px] font-mono font-bold"
            :style="{ background: getColorAlpha(accent(i), 0.16), border: '1px solid ' + accent(i), color: accent(i) }"
          >{{ i + 1 }}</span>
          <span class="text-[11px] leading-snug text-text-secondary">
            <span class="font-bold text-text-primary">{{ s.name }}</span>
            <template v-if="s.description"> — {{ s.description }}</template>
          </span>
        </div>
      </div>

      <div v-if="source" class="mt-2 shrink-0 text-right text-[11px] font-mono text-text-muted">{{ source }}</div>
    </template>
  </div>
</template>
