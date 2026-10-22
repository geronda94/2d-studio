<template>
 <div v-if="hasError" class="w-full h-full flex items-center justify-center text-center p-4 bg-red-900/20 text-red-400 border border-red-500/30">
 <div>
 <Icon icon="heroicons:exclamation-triangle" class="w-8 h-8 mx-auto mb-2 opacity-50" />
 <p class="text-sm font-bold">{{ componentName }}</p>
 <p class="text-[10px] mt-1 opacity-70">Превью недоступно (ошибка рендера)</p>
 </div>
 </div>
 <div v-else class="w-full h-full relative">
 <Slide 
 :index="0"
 folder="preview"
 :title="slideTitle"
 :subtitle="slideSubtitle"
 layout="col"
 >
 <template #default>
 <component 
 :is="componentInstance" 
 v-bind="payload" 
 />
 </template>
 </Slide>
 </div>
</template>

<script setup>
import { ref, onErrorCaptured, provide, computed } from 'vue'
import { Icon } from '@iconify/vue'
import Slide from '../engine/Slide.vue'

const props = defineProps({
 componentInstance: {
 type: Object,
 required: true
 },
 componentName: {
 type: String,
 default: 'Unknown Component'
 },
 payload: {
 type: Object,
 default: () => ({})
 }
})

const hasError = ref(false)

// Provide mock engine state so Slide.vue can render normally
provide('currentSlide', ref(0))
provide('currentClick', ref(0))
provide('currentFolder', ref('preview'))
provide('registerClicks', () => {})
provide('isMobile', ref(false))

// Extract title/subtitle if they exist in the payload for preview purposes
const slideTitle = computed(() => props.payload?.title || props.componentName)
const slideSubtitle = computed(() => props.payload?.subtitle || '')

onErrorCaptured((err, instance, info) => {
 console.warn(`[SafeComponentPreview] Error rendering ${props.componentName}:`, err, info)
 hasError.value = true
 return false // Prevent error from propagating further up!
})
</script>
