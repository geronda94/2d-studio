<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'
import ParetoChart from './ParetoChart.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  days_without: { type: Number, default: 0 },
  leading: { type: Array, default: () => [] },
  lagging: { type: Array, default: () => [] },
  incidents_by_type: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'SafetyDashboard')
const relativeTime = inject('relativeTime', ref(0))

const hasData = computed(() =>
  !!props.days_without || props.leading.length || props.lagging.length || props.incidents_by_type.length,
)

const kpiProgress = computed(() => {
  const p = Math.max(0, Math.min(1, relativeTime.value / motion.value.count_ms))
  return 1 - Math.pow(1 - p, 3)
})
const kpiValue = computed(() => Math.round((Number(props.days_without) || 0) * kpiProgress.value))

const groups = computed(() => [
  { title: 'Проактивные меры', hint: 'Leading', token: 'var(--color-success)', icon: 'lucide:clipboard-check', items: props.leading || [] },
  { title: 'Инциденты и травмы', hint: 'Lagging', token: 'var(--color-danger)', icon: 'lucide:triangle-alert', items: props.lagging || [] },
])

const reveal = (i) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - i * motion.value.stagger_ms) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}
const fmt = (n) => Number(n || 0).toLocaleString('ru-RU', { maximumFractionDigits: 2 })
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-3 md:gap-4" :style="{ ...itemVars }">
    <div v-if="!hasData" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div
        class="flex flex-col sm:flex-row sm:items-center gap-3 px-4 py-2.5 shrink-0"
        :style="[
          {
            ...itemPrimaryVars,
            background: 'var(--item-primary-bg)',
            backdropFilter: 'var(--item-primary-backdrop)',
            borderRadius: 'var(--item-primary-radius)',
            boxShadow: 'var(--item-primary-shadow)',
            padding: 'var(--item-primary-padding)',
            borderWidth: 'var(--item-primary-border-width)',
            borderStyle: 'var(--item-primary-border-style)',
            borderColor: 'var(--item-primary-border)',
          },
          reveal(0),
        ]"
      >
        <Icon icon="lucide:shield-check" class="w-9 h-9 shrink-0" :style="{ color: getHexColor('var(--color-success)') }" />
        <div class="flex items-baseline gap-3">
          <span class="text-3xl font-mono font-bold text-text-primary tabular-nums">{{ kpiValue }}</span>
          <span class="text-sm text-text-secondary">дней без инцидентов</span>
        </div>
      </div>

      <div class="flex-1 min-h-0 flex flex-col md:flex-row gap-3 md:gap-4">
        <!-- Панели метрик -->
        <div class="flex flex-col gap-3 md:gap-4 min-h-0 md:w-[38%] md:shrink-0">
          <div
            v-for="(g, gi) in groups"
            :key="g.title"
            class="flex-1 min-h-0 flex flex-col gap-1.5 p-3 overflow-hidden justify-center"
            :style="{
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              padding: 'var(--item-padding)',
              borderWidth: 'var(--item-border-width)',
              borderStyle: 'var(--item-border-style)',
              borderColor: 'var(--item-border)',
            }"
          >
            <div class="flex items-center gap-2 shrink-0 min-w-0">
              <Icon :icon="g.icon" class="w-4 h-4 shrink-0" :style="{ color: getHexColor(g.token) }" />
              <span class="text-[11px] font-bold uppercase tracking-wider text-text-primary truncate">{{ g.title }}</span>
              <span class="text-[9px] font-mono uppercase text-text-muted shrink-0 whitespace-nowrap">{{ g.hint }}</span>
            </div>

            <div class="grid grid-cols-2 gap-1.5 flex-1 min-h-0 content-center overflow-hidden">
              <div
                v-for="(m, i) in g.items"
                :key="m.label + i"
                class="flex items-center gap-2 px-2.5 py-1.5 min-w-0"
                :style="[
                  {
                    background: 'var(--item-primary-bg)',
                    borderRadius: 'var(--item-primary-radius)',
                    borderWidth: 'var(--item-primary-border-width)',
                    borderStyle: 'var(--item-primary-border-style)',
                    borderColor: 'var(--item-primary-border)',
                  },
                  reveal(gi * g.items.length + i + 1),
                ]"
              >
                <Icon v-if="m.icon" :icon="m.icon" class="w-4 h-4 shrink-0" :style="{ color: getHexColor(g.token) }" />
                <div class="min-w-0">
                  <div class="text-[10px] uppercase tracking-wider font-mono text-text-muted truncate">{{ m.label }}</div>
                  <div class="font-mono text-text-primary">
                    <span class="text-base font-bold">{{ fmt(m.value) }}</span>
                    <span v-if="m.unit" class="ml-1 text-[11px] text-text-secondary">{{ m.unit }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- График инцидентов -->
        <div class="flex-1 min-h-0 overflow-hidden">
          <ParetoChart
            :variant="variant"
            :mobile="mobile"
            density="compact"
            :items="incidents_by_type"
            :threshold="80"
            :wrap_labels="true"
          />
        </div>
      </div>
    </template>
  </div>
</template>
