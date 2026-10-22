<script setup lang="ts">
import { inject, ref, computed } from 'vue'

const props = withDefaults(defineProps<{
 mode?: 'fixed' | 'absolute' | 'relative' | 'static'
 duration?: number
 variant?: string
}>(), {
 mode: 'relative',
 duration: 6000
})

import { useVariant } from '../../composables/useVariant'
const { line } = useVariant(computed(() => props.variant), 'VerticalDivider')

const relativeTime = inject('relativeTime', ref(0))

const sparkTop = computed(() => {
 const t = relativeTime.value % props.duration
 return (t / props.duration) * 100
})
</script>

<template>
 <div
 :class="[
 props.mode === 'relative' ? 'relative h-full' : (props.mode === 'absolute' ? 'absolute top-0 bottom-0' : ''),
 'w-[2px] pointer-events-none z-0 mx-4 overflow-hidden'
 ]"
 >
 <!-- Faded base line — gradient instead of mask-image (mask-image crashes SwiftShader) -->
 <div class="absolute inset-0 w-full h-full divider-fade" :style="{ '--line-color': line.color }"></div>
 <!-- Moving spark -->
 <div v-if="line.animation !== 'none'" class="absolute inset-0 w-full h-full animated-spark" :style="{ '--line-color': line.color, '--spark-top': sparkTop + '%' }"></div>
 </div>
</template>

<style scoped>
.divider-fade {
  background: linear-gradient(
    to bottom,
    transparent 0%,
    var(--line-color) 15%,
    var(--line-color) 85%,
    transparent 100%
  );
  opacity: 0.25;
}

.animated-spark {
  background: radial-gradient(
    ellipse 100% 12% at 50% var(--spark-top, 50%),
    var(--line-color) 0%,
    transparent 100%
  );
  opacity: 0.9;
}
</style>
