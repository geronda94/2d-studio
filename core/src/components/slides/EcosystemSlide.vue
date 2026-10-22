<template>
 <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col relative overflow-visible">
 <div class="flex-1 w-full min-h-0 h-full flex items-center justify-center relative z-10 pt-1 pb-2">
  <Ecosystem
    v-bind="props"
     :base_width="mobile ? undefined : 1240"
     :base_height="mobile ? undefined : 560"
     :orbit_dx="mobile ? 108 : 420"
     :orbit_dy="mobile ? 300 : 195"
  />
 </div>
 </div>
</template>

<script setup>
import Ecosystem from '../ui/Ecosystem.vue'

const props = defineProps({
 mobile: Boolean,
 title: String,
 variant: String,
 clicks: { type: Number, default: 0 },
 center: Object,
 nodes: Array
})
</script>
