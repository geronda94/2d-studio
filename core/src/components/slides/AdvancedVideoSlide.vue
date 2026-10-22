<script setup>
import AdvancedVideoPlayer from '../ui/AdvancedVideoPlayer.vue'
import { useVariant } from '../../composables/useVariant'
import { computed } from 'vue'

const props = defineProps({
 mobile: Boolean,
 title: String,
 video_url: String,
 frame: String,
 domain: String,
 zoom: Number,
 pan_x: Number,
 pan_y: Number,
 trim_start: Number,
 trim_end: Number,
 initial_scale: [Number, String],
 target_scale: [Number, String],
 object_position: String,
 start_time: Number,
 variant: String
})

const { itemVars } = useVariant(computed(() => props.variant), 'AdvancedVideoSlide')

import { useAttrs } from 'vue'
const attrs = useAttrs()
const resolvedVideoUrl = computed(() => {
 return props.video_url || attrs.VIDEO_URL || attrs.media_url || attrs.MEDIA_URL || ''
})
</script>

<template>
 <div class="w-full h-full flex flex-col relative overflow-hidden"
 :style="{ ...itemVars }">
 <div class="flex-1 w-full h-full flex flex-col items-center justify-center relative z-10 p-4">
 <AdvancedVideoPlayer v-bind="props" :video_url="resolvedVideoUrl" class="w-full max-h-full" />
 </div>
 </div>
</template>
