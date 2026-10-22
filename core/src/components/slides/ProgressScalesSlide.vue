<template>
  <div :class="mobile ? 'flex flex-col gap-4 w-full h-full min-h-0' : 'w-full max-w-5xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-5 md:gap-7'">
 <ProgressScale v-for="(scale, idx) in scales" :key="idx" v-bind="scale" :color="scale.color" :variant="props.variant" class="flex-1 min-h-0" />
 </div>
</template>
<script setup>
import ProgressScale from '../ui/ProgressScale.vue'
const props = defineProps({ mobile: Boolean, variant: String, scales: { type: Array, default: () => [] } })
</script>