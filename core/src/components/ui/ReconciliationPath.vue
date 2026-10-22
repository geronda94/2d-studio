<script setup>
import { computed } from 'vue'
import StepByStep from './StepByStep.vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  steps: { type: Array, default: () => [] },
  layout: { type: String, default: 'vertical' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ReconciliationPath')

const mappedSteps = computed(() =>
  (props.steps || []).map((s, i) => ({
    id: s.id ?? `step-${i}`,
    title: s.name ?? s.title ?? '',
    description: s.description ?? '',
    icon: s.icon,
    color: s.color,
    start_time: s.start_time ?? i * motion.value.stagger_ms,
  })),
)

// Две колонки на десктопе: карточки больше не растягиваются на всю ширину,
// текст не занимает левые 40% широкой карточки.
const twoCol = computed(
  () => !props.mobile && props.layout !== 'horizontal' && mappedSteps.value.length >= 5,
)

const columns = computed(() => {
  if (!twoCol.value) return [mappedSteps.value]
  const half = Math.ceil(mappedSteps.value.length / 2)
  return [mappedSteps.value.slice(0, half), mappedSteps.value.slice(half)]
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="twoCol" class="grid grid-cols-2 gap-x-10 h-full min-h-0 content-center">
      <StepByStep
        v-for="(col, ci) in columns"
        :key="ci"
        :variant="variant"
        :mobile="mobile"
        layout="vertical"
        :steps="col"
      />
    </div>
    <div v-else class="flex-1 min-h-0 overflow-hidden flex items-center justify-center">
      <StepByStep
        class="w-full"
        :variant="variant"
        :mobile="mobile"
        :compact="mobile"
        :layout="layout"
        :steps="mappedSteps"
      />
    </div>
  </div>
</template>
