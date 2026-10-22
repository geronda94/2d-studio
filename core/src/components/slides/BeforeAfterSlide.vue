<template>
 <div :class="mobile ? 'mt-6 w-full' : 'w-full max-w-6xl h-full min-h-0 mx-auto'">
 <div class="w-full h-full">
 <BeforeAfter 
 :mobile="mobile"
 :variant="props.variant"
 :leftTitle="windows[0]?.title || 'До'" 
 :rightTitle="windows[1]?.title || 'После'"
 :leftTime="windows[0]?.start_time"
 :rightTime="windows[1]?.start_time"
 >
 <template #left>
 <img v-if="windows[0]?.image" :src="windows[0].image" class="w-full h-full object-cover" />
 <div v-else class="w-full h-full flex items-center justify-center text-text-muted" style="background: var(--item-bg)">Нет изображения (До)</div>
 </template>
 <template #right>
 <img v-if="windows[1]?.image" :src="windows[1].image" class="w-full h-full object-cover" />
 <div v-else class="w-full h-full flex items-center justify-center text-text-muted" style="background: var(--item-bg)">Нет изображения (После)</div>
 </template>
 </BeforeAfter>
 </div>
 </div>
</template>
<script setup>
import BeforeAfter from '../ui/BeforeAfter.vue'
const props = defineProps({ 
 mobile: Boolean, 
 variant: String,
 windows: { type: Array, default: () => [] }
})
</script>