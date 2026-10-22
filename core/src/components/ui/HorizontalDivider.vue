<script setup lang="ts">
import { inject, ref, computed } from 'vue'

const props = withDefaults(defineProps<{
 mode?: 'fixed' | 'absolute' | 'relative' | 'static'
 duration?: number
 variant?: string
}>(), {
 mode: 'relative',
 duration: 3000
})

import { useVariant } from '../../composables/useVariant'
const { line } = useVariant(computed(() => props.variant), 'HorizontalDivider')

const relativeTime = inject('relativeTime', ref(0))

// Spark position: sweeps 0→100% across the line
const sparkLeft = computed(() => {
 const t = relativeTime.value % props.duration
 return (t / props.duration) * 100
})
</script>

<template>
 <div
 :class="[
 props.mode === 'relative' ? 'relative w-full' : (props.mode === 'absolute' ? 'absolute left-0 right-0' : ''),
 'h-[2px] pointer-events-none z-0 relative overflow-hidden'
 ]"
 >
 <!-- Fade edges via gradient background — no mask-image (unsafe in SwiftShader) -->
 <div class="absolute inset-0 w-full h-full divider-fade" :style="{ '--line-color': line.color }"></div>
 <!-- Animated spark overlay -->
 <div v-if="line.animation !== 'none'" class="absolute inset-0 w-full h-full animated-spark" :style="{ '--line-color': line.color, '--spark-left': sparkLeft + '%' }"></div>
 </div>
</template>

<style scoped>
/* Base line with faded edges — using background gradient instead of mask-image
   mask-image crashes SwiftShader (Playwright software renderer) */
.divider-fade {
  background: linear-gradient(
    to right,
    transparent 0%,
    var(--line-color) 50%,
    transparent 100%
  );
  opacity: 0.25;
}

/* Moving spark — a small bright segment that travels left→right */
.animated-spark {
  background: radial-gradient(
    ellipse 15% 100% at var(--spark-left, 50%) 50%,
    var(--line-color) 0%,
    transparent 100%
  );
  opacity: 0.9;
}
</style>
