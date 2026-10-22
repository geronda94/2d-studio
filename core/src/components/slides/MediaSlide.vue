<template>
 <div class="w-full h-full flex flex-col p-2 sm:p-4 relative z-10" :style="backgroundStyle">
  <div class="relative w-full h-full overflow-hidden isolate"
  :style="{
  ...itemVars,
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
  }">
 
 <!-- Media Layer with Zoom -->
 <div 
 class="absolute inset-0 will-change-transform pointer-events-none"
 :style="{
 transform: `scale(${currentScale})`,
 objectPosition: currentPosition
 }"
 >
 <img v-if="showMedia && !isVideo" :src="resolvedUrl" class="w-full h-full object-cover" :style="{ objectPosition: 'inherit' }" @error="loadError = true" />
 <video v-else-if="showMedia && isVideo" :src="resolvedUrl" class="w-full h-full object-cover" :style="{ objectPosition: 'inherit' }" autoplay loop muted playsinline @error="loadError = true"></video>
 <div v-else class="w-full h-full flex flex-col items-center justify-center text-text-muted text-xl gap-4" style="background: var(--item-bg)">
 <Icon icon="heroicons:photo" class="text-6xl opacity-50" />
 {{ placeholder || 'Медиа заглушка' }}
 </div>
 </div>
 
 <!-- Overlay & Caption -->
 <div v-if="caption" class="absolute bottom-0 inset-x-0 flex flex-col justify-end pointer-events-none px-8 sm:px-12 pb-5 sm:pb-6 pt-4"
 :style="{ background: `linear-gradient(to top, rgb(var(--bg-surface-rgb) / 0.9) 0%, rgb(var(--bg-surface-rgb) / 0.6) 55%, transparent 100%)` }">
 <div class="text-text-primary text-3xl sm:text-5xl font-bold tracking-tight max-w-4xl leading-tight">
 {{ caption }}
 </div>
 </div>
 
 </div>
 </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 // Content Props
 MEDIA_URL: String,
 media_url: String,
 image: String,
 video: String,
 
 CAPTION: String,
 caption: String,
 
 placeholder: String,
 theme: String,
 variant: String,
 
 // Animation & Positioning Props
 object_position: { type: String, default: 'center' },
 target_position: { type: String, default: '' },
 initial_scale: { type: [Number, String], default: 1.0 },
 target_scale: { type: [Number, String], default: 1.0 },
 zoom_duration: { type: [Number, String], default: 8000 },
 start_time: { type: Number, default: 0 }
})

const { itemVars } = useVariant(computed(() => props.variant), 'MediaSlide')

// Normalize inputs
const resolvedUrl = computed(() => props.MEDIA_URL || props.media_url || props.image || props.video)
const isVideo = computed(() => resolvedUrl.value && resolvedUrl.value.toLowerCase().endsWith('.mp4'))
const caption = computed(() => props.CAPTION || props.caption)

// Если файл отсутствует/битый (404) — показываем заглушку, а не «сломанную» картинку.
const loadError = ref(false)
const showMedia = computed(() => !!resolvedUrl.value && !loadError.value)
watch(resolvedUrl, () => { loadError.value = false })

// Animation logic
const relativeTime = inject('relativeTime', ref(0))

const durationMs = computed(() => parseInt(props.zoom_duration) || 8000)

// Calculate progress 0..1 based on relative time
const progress = computed(() => {
 const elapsed = Math.max(0, relativeTime.value - (props.start_time || 0))
 if (durationMs.value <= 0) return elapsed > 0 ? 1 : 0
 return Math.min(1, Math.max(0, elapsed / durationMs.value))
})

// easeOutCubic to make it smooth and match the old cubic-bezier
const easedProgress = computed(() => {
 const t = progress.value
 return 1 - Math.pow(1 - t, 3)
})

const currentScale = computed(() => {
 const start = parseFloat(props.initial_scale) || 1.0
 const end = parseFloat(props.target_scale) || 1.0
 return start + (end - start) * easedProgress.value
})

// Helper to parse object-position strings (e.g. "center top", "20% 80%") into numeric x/y percentages
const parsePosition = (pos) => {
 if (!pos) return { x: 50, y: 50 }
 const parts = pos.trim().toLowerCase().split(/\s+/)
 let x = 50, y = 50
 
 const parsePart = (p) => {
 if (p === 'center') return 50
 if (p === 'left' || p === 'top') return 0
 if (p === 'right' || p === 'bottom') return 100
 if (p.endsWith('%')) return parseFloat(p)
 return parseFloat(p) || 0
 }

 if (parts.length === 1) {
 if (['top', 'bottom'].includes(parts[0])) { x = 50; y = parsePart(parts[0]) }
 else if (['left', 'right'].includes(parts[0])) { x = parsePart(parts[0]); y = 50 }
 else { x = parsePart(parts[0]); y = 50 }
 } else if (parts.length >= 2) {
 x = parsePart(parts[0])
 y = parsePart(parts[1])
 }
 return { x, y }
}

const currentPosition = computed(() => {
 const start = parsePosition(props.object_position || 'center')
 const end = parsePosition(props.target_position || props.object_position || 'center')
 
 const currentX = start.x + (end.x - start.x) * easedProgress.value
 const currentY = start.y + (end.y - start.y) * easedProgress.value
 
 return `${currentX}% ${currentY}%`
})

const backgroundStyle = computed(() => ({
 background: props.theme === 'dark' ? 'var(--surface-bg)' : 'transparent'
}))
</script>
