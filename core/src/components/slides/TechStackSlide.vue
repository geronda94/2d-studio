<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col">
    <div class="flex-1 min-h-0 w-full flex items-center justify-center">
      <div :class="containerClass">
        <TechCard v-for="(tech, idx) in technologies.slice(0, 8)" :key="idx" v-bind="tech" :compact="technologies.length > 4 || mobile" :variant="variant" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TechCard from '../ui/TechCard.vue'

const props = defineProps({ mobile: Boolean, variant: String, technologies: { type: Array, default: () => [] } })

const containerClass = computed(() => {
  const n = props.technologies.length
  if (props.mobile) {
    if (n > 4) {
      return 'grid grid-cols-2 gap-4 w-full px-2'
    }
    return 'flex flex-col gap-4 w-full px-4 max-w-[400px] mx-auto'
  }

  if (n === 4) {
    return 'grid grid-cols-2 gap-6 w-full max-w-3xl mx-auto h-full items-stretch'
  }

  if (n <= 3) {
    return 'grid grid-cols-3 gap-6 w-full max-w-5xl mx-auto h-full items-stretch'
  }

  return 'flex flex-wrap justify-center gap-6 w-full max-w-[1300px] mx-auto items-stretch content-center'
})
</script>
