<template>
 <div class="flex flex-col items-center justify-center text-text-muted h-full w-full">
 <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-4">
 <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
 <line x1="4" y1="22" x2="4" y2="15"></line>
 </svg>
 <h2 class="text-2xl font-mono uppercase tracking-[0.3em]">End of Presentation</h2>
 </div>
</template>

<script setup>
// Technical slide acting as an Out Point / End Marker for the timeline
defineProps({
 mobile: Boolean,
 clicks: { type: Number, default: 0 }
})
</script>
