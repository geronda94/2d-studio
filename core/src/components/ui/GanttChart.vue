<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  tasks: { type: Array, default: () => [] },
  milestones: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'GanttChart')
const relativeTime = inject('relativeTime', ref(0))

const clampPct = (v) => Math.max(0, Math.min(100, Number(v) || 0))

const barProgress = (t, idx) => {
  const ts = t.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - ts) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

// Позиция/ширина считаются внутри трека (flex-1), поэтому одинаково верны
// на desktop и mobile — без отрицательных отступов под подписи.
const barGeometry = (t) => {
  const s = clampPct(t.start)
  const e = clampPct(t.end)
  return { left: `${s}%`, width: `${Math.max(3, e - s)}%` }
}

const fillStyle = (t, idx) => ({
  transform: `scaleX(${(clampPct(t.progress) / 100) * barProgress(t, idx)})`,
  transformOrigin: 'left center',
  background: getHexColor(t.color || 'var(--color-secondary)'),
})

// Трек задачи — пунктирный контур, заливка = прогресс. При 0% полоса явно пустая,
// а не «полная» (прошлый баг: полупрозрачный трек читался как выполненный бар).
const trackStyle = (t) => ({
  background: 'transparent',
  borderWidth: '1px',
  borderStyle: 'dashed',
  borderColor: getColorAlpha(getHexColor(t.color || 'var(--color-secondary)'), 0.45),
})

const pctLabelStyle = (t) => {
  const end = clampPct(t.end)
  return end > 86
    ? { right: `calc(${(100 - end).toFixed(2)}% + 6px)` }
    : { left: `calc(${end.toFixed(2)}% + 6px)` }
}

const milestoneReveal = (m, idx) => {
  const ts = m.start_time ?? (props.tasks.length * motion.value.stagger_ms) + idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - ts) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(3), transform: `translateX(-50%) translateY(-50%) scale(${(0.6 + 0.4 * p).toFixed(3)})` }
}
</script>

<template>
  <div class="w-full max-w-5xl mx-auto h-full min-h-0 overflow-hidden flex flex-col justify-center" :style="{ ...itemVars }">
    <div v-if="title" class="mb-5 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="relative"
      :class="mobile ? 'flex-1 min-h-0 flex flex-col justify-center' : 'shrink-0'"
      :style="{
        background: 'var(--item-bg)',
        backdropFilter: 'var(--item-backdrop)',
        WebkitBackdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)',
        boxShadow: 'var(--item-shadow)',
        padding: 'var(--item-padding)',
        padding: 'var(--item-padding)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)',
        borderColor: 'var(--item-border)',
      }"
    >
      <div
        v-for="(t, idx) in tasks"
        :key="t.id ?? idx"
        class="flex items-center gap-2 md:gap-3"
        :style="{ height: mobile ? undefined : '52px', flex: mobile ? 1 : undefined, minHeight: mobile ? '44px' : undefined, opacity: barProgress(t, idx) }"
      >
        <div
          class="shrink-0 flex items-center gap-1.5 text-text-secondary text-[10px] md:text-xs font-medium min-w-0"
          :style="{ width: mobile ? '124px' : '150px' }"
        >
          <Icon v-if="t.icon" :icon="t.icon" class="w-3.5 h-3.5 shrink-0" :style="{ color: getHexColor(t.color || 'var(--color-secondary)') }" />
          <span class="truncate">{{ t.name }}</span>
        </div>

        <div class="relative flex-1 h-7">
          <div
            class="absolute inset-y-0 rounded-full overflow-hidden"
            :style="[barGeometry(t), trackStyle(t)]"
          >
            <div class="absolute inset-y-0 left-0 right-0 rounded-full" :style="fillStyle(t, idx)"></div>
          </div>
          <span
            v-if="t.progress != null"
            class="absolute top-1/2 -translate-y-1/2 text-[11px] font-mono font-bold text-text-secondary whitespace-nowrap"
            :style="pctLabelStyle(t)"
          >{{ clampPct(t.progress) }}%</span>
        </div>
      </div>

      <div class="relative h-12 mt-1 shrink-0" :style="{ marginLeft: mobile ? '132px' : '162px' }">
        <div
          class="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-px"
          :style="{ background: 'var(--item-border)' }"
        ></div>
        <div
          v-for="(m, idx) in milestones"
          :key="m.id ?? idx"
          class="absolute top-1/2"
          :style="[{ left: `${clampPct(m.at)}%` }, milestoneReveal(m, idx)]"
        >
          <div class="w-3 h-3 rotate-45" :style="{ background: getHexColor(m.color || 'var(--color-warning)'), boxShadow: '0 0 0 2px var(--item-bg)' }"></div>
          <span class="absolute left-1/2 top-3.5 whitespace-nowrap text-[10px] font-mono text-text-secondary" :class="m.at > 80 ? '-translate-x-full' : '-translate-x-1/2'">{{ m.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
