<template>
 <div class="w-full h-full flex flex-col relative overflow-hidden px-4">
 <div class="flex-1 w-full h-full flex items-center justify-center relative z-10">
 <RoiCalculator v-bind="props" />
 </div>
 </div>
</template>

<script setup>
import RoiCalculator from '../ui/RoiCalculator.vue'

const props = defineProps({
 mobile: Boolean,
 title: String,
 variant: String,
 variables: Array,
 result_base: Number,
 result_label: String,
 result_suffix: String,
 result_description: String
})
</script>
