<template>
 <div 
 class="advanced-video-player relative w-full h-full flex flex-col items-center justify-center group/player"
 :style="{ ...itemVars }"
 @mouseenter="isHovered = true"
 @mouseleave="isHovered = false"
 >
 <!-- Browser Frame -->
 <div v-if="frame === 'browser'" class="w-full max-w-5xl bg-bg-base/80 overflow-hidden flex flex-col mx-auto" :style="{ borderRadius: 'var(--item-radius)', borderWidth: 'var(--item-border-width)', borderStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' }">
 <WindowHeader :mobile="$attrs.mobile">
 <div class="mx-auto px-2 md:px-6 py-0.5 md:py-1 rounded bg-black/20 border border-text-muted text-[8px] md:text-xs text-text-muted font-mono flex items-center gap-1.5 md:gap-2">
 <svg xmlns="http://www.w3.org/2000/svg" class="w-2 h-2 md:w-2.5 md:h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
 {{ domain || 'app.startup.io' }}
 </div>
 </WindowHeader>
 <div class="relative w-full bg-black overflow-hidden flex items-center justify-center" :style="{ aspectRatio: videoAspect }">
 <div class="absolute inset-0 pointer-events-none" :style="videoWrapperStyle">
 <canvas v-if="isHeadless && hasVideo" ref="canvasEl" class="w-full h-full block"></canvas>
 <video v-else-if="hasVideo && !videoError" ref="videoEl" :src="video_url" class="w-full h-full object-cover" :style="videoElementStyle" @loadedmetadata="onVideoLoaded" @error="videoError = true" preload="auto" muted playsinline loop></video>
 <div v-else class="w-full h-full flex items-center justify-center text-text-muted text-sm">{{ videoError ? 'Видео недоступно' : 'Видео не задано' }}</div>
 </div>
 <div class="absolute inset-0 bg-black/40 flex flex-col justify-between z-50 pointer-events-auto" :class="isHovered && isAnimating ? 'opacity-100' : 'opacity-0'">
 <div class="flex-1 flex items-center justify-center">
 <button @click.stop="togglePlay" class="w-12 h-12 md:w-20 md:h-20 rounded-full bg-black/50  flex items-center justify-center text-white hover:scale-110 transition-transform">
 <svg v-if="!globalIsPlaying" xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 md:w-10 md:h-10 ml-1" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 md:w-10 md:h-10" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
 </button>
 </div>
 <div class="h-8 md:h-12 bg-gradient-to-t from-black/80 to-transparent flex items-end px-3 md:px-6 pb-2 md:pb-4">
 <div class="w-full flex items-center justify-between text-white font-mono text-[9px] md:text-sm shadow-sm">
 <span class="bg-black/50 px-1.5 md:px-2 py-0.5 md:py-1 rounded md:rounded-md ">{{ formatTime(currentTimeDisplay) }}</span>
 <span class="bg-black/50 px-1.5 md:px-2 py-0.5 md:py-1 rounded md:rounded-md ">{{ formatTime(durationDisplay) }}</span>
 </div>
 </div>
 </div>
 </div>
 </div>
 
 <!-- Mobile Frame -->
 <div v-else-if="frame === 'mobile'" 
 class="w-[320px] bg-bg-base border-4 border-text-secondary rounded-[2.5rem]  overflow-hidden relative mx-auto flex items-center justify-center"
 :style="{ aspectRatio: videoAspect > 1 ? 19/9 : 9/19 }"
 >
 <div class="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-black/50 rounded-b-xl z-20 "></div>
 <div class="relative w-full h-full bg-black overflow-hidden flex items-center justify-center">
 <div class="absolute inset-0 pointer-events-none" :style="videoWrapperStyle">
 <canvas v-if="isHeadless && hasVideo" ref="canvasEl" class="w-full h-full block"></canvas>
 <video v-else-if="hasVideo && !videoError" ref="videoEl" :src="video_url" class="w-full h-full object-cover" :style="videoElementStyle" @loadedmetadata="onVideoLoaded" @error="videoError = true" preload="auto" muted playsinline loop></video>
 <div v-else class="w-full h-full flex items-center justify-center text-text-muted text-sm">{{ videoError ? 'Видео недоступно' : 'Видео не задано' }}</div>
 </div>
 <div class="absolute inset-0 bg-black/40 flex flex-col justify-between z-50 pointer-events-auto" :class="isHovered && isAnimating ? 'opacity-100' : 'opacity-0'">
 <div class="flex-1 flex items-center justify-center">
 <button @click.stop="togglePlay" class="w-16 h-16 rounded-full bg-black/50  flex items-center justify-center text-white hover:scale-110 transition-transform">
 <svg v-if="!globalIsPlaying" xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 ml-1" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
 </button>
 </div>
 <div class="h-16 bg-gradient-to-t from-black/80 to-transparent flex items-end px-4 pb-6">
 <div class="w-full flex items-center justify-between text-white font-mono text-[10px] shadow-sm">
 <span class="bg-black/50 px-2 py-1 rounded-md ">{{ formatTime(currentTimeDisplay) }}</span>
 <span class="bg-black/50 px-2 py-1 rounded-md ">{{ formatTime(durationDisplay) }}</span>
 </div>
 </div>
 </div>
 </div>
 </div>
 
 <!-- No Frame -->
 <div v-else 
 class="w-full max-w-5xl rounded-[var(--item-radius)] overflow-hidden  bg-black relative flex items-center justify-center mx-auto"
 :style="{ aspectRatio: videoAspect }"
 >
 <div class="absolute inset-0 pointer-events-none" :style="videoWrapperStyle">
 <canvas v-if="isHeadless && hasVideo" ref="canvasEl" class="w-full h-full block"></canvas>
 <video v-else-if="hasVideo && !videoError" ref="videoEl" :src="video_url" class="w-full h-full object-cover" :style="videoElementStyle" @loadedmetadata="onVideoLoaded" @error="videoError = true" muted playsinline loop></video>
 <div v-else class="w-full h-full flex items-center justify-center text-text-muted text-sm">{{ videoError ? 'Видео недоступно' : 'Видео не задано' }}</div>
 </div>
 <div class="absolute inset-0 bg-black/40 flex flex-col justify-between z-50 pointer-events-auto" :class="isHovered && isAnimating ? 'opacity-100' : 'opacity-0'">
 <div class="flex-1 flex items-center justify-center">
 <button @click.stop="togglePlay" class="w-24 h-24 rounded-full bg-black/50  flex items-center justify-center text-white hover:scale-110 transition-transform">
 <svg v-if="!globalIsPlaying" xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 ml-1" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-12 h-12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
 </button>
 </div>
 <div class="h-16 bg-gradient-to-t from-black/80 to-transparent flex items-end px-8 pb-4">
 <div class="w-full flex items-center justify-between text-white font-mono text-sm shadow-sm">
 <span class="bg-black/50 px-2 py-1 rounded-md ">{{ formatTime(currentTimeDisplay) }}</span>
 <span class="bg-black/50 px-2 py-1 rounded-md ">{{ formatTime(durationDisplay) }}</span>
 </div>
 </div>
 </div>
 </div>
 </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject, onUnmounted } from 'vue'
import { useDirector } from '../../composables/useDirector'
import { useVariant } from '../../composables/useVariant'
import WindowHeader from './WindowHeader.vue'

const emit = defineEmits(['update:object_position'])

const props = defineProps({
 video_url: { type: String, required: true },
 frame: { type: String, default: 'browser' },
 domain: { type: String, default: 'app.startup.io' },
 trim_start: { type: Number, default: 0 },
 trim_end: { type: Number, default: 0 },
 object_position: { type: String, default: '50% 50%' },
 initial_scale: { type: [Number, String], default: 1.0 },
 target_scale: { type: [Number, String], default: 1.0 },
 start_time: { type: Number, default: 0 },
 variant: String
})

const { itemVars } = useVariant(computed(() => props.variant), 'AdvancedVideoPlayer')

// Гард: пустой video_url — не пытаемся играть (иначе play() reject каждый кадр).
const hasVideo = computed(() => !!(props.video_url && String(props.video_url).trim()))

const videoEl = ref(null)
const canvasEl = ref(null)
const videoError = ref(false)
const relativeTime = inject('relativeTime')
const { isPlaying: globalIsPlaying, play, pause } = useDirector()

// Headless (legacy frame-injection path) only when NOT under realtime x11grab.
// Realtime render passes ?engine=realtime → native <video> playback, no canvas.
const isRealtimeRender = typeof window !== 'undefined' &&
 new URLSearchParams(window.location.search).get('engine') === 'realtime'
const isHeadless = typeof window !== 'undefined' &&
 window.navigator.webdriver && !isRealtimeRender

const isHovered = ref(false)
const currentTimeDisplay = ref(0)
const durationDisplay = ref(0)
let timeUpdateInterval = null
const videoAspect = ref(16 / 9)


const onVideoLoaded = (e) => {
 const w = e.target.videoWidth
 const h = e.target.videoHeight
 if (w && h) videoAspect.value = w / h
 durationDisplay.value = e.target.duration || 0
}

const isAnimating = computed(() => relativeTime.value >= (props.start_time || 0))

const videoWrapperStyle = computed(() => {
 const tScale = parseFloat(props.target_scale)
 const iScale = parseFloat(props.initial_scale)
 const currentScale = isAnimating.value ? (isNaN(tScale) ? 1.0 : tScale) : (isNaN(iScale) ? 1.0 : iScale)
 return {
 transform: `scale(${currentScale})`,
 // Disable CSS transitions in headless: they delay VirtualTime budget expiry
 transition: isHeadless ? 'none' : 'transform 1.5s cubic-bezier(0.165, 0.84, 0.44, 1)',
 willChange: isHeadless ? 'auto' : 'transform'
 }
})

const videoElementStyle = computed(() => ({
 objectPosition: props.object_position || '50% 50%',
 willChange: 'object-position'
}))

onMounted(() => {
 if (isHeadless) {
 // In headless mode: Python's render_video.py pre-extracts video frames via ffmpeg
 // and injects them directly into this canvas via page.evaluate().
 // We don't need to do anything here — just expose the canvas element.
 if (canvasEl.value) {
 canvasEl.value.width = 1920
 canvasEl.value.height = 1080
 }
 return
 }

 // Normal mode: interval for time display updates
 timeUpdateInterval = setInterval(() => {
 if (videoEl.value) {
 currentTimeDisplay.value = videoEl.value.currentTime
 if (!durationDisplay.value && videoEl.value.duration) {
 durationDisplay.value = videoEl.value.duration
 }
 }
 }, 100)
})

onUnmounted(() => {
 if (timeUpdateInterval) clearInterval(timeUpdateInterval)
})

const togglePlay = () => {
 if (globalIsPlaying.value) pause()
 else play()
}

const formatTime = (seconds) => {
 if (isNaN(seconds) || seconds < 0) return '0:00'
 const m = Math.floor(seconds / 60)
 const s = Math.floor(seconds % 60)
 return `${m}:${s.toString().padStart(2, '0')}`
}

watch([relativeTime, globalIsPlaying], ([newTime, isPlaying]) => {
 // In headless mode, Python handles video frame injection — no JS needed
 if (isHeadless) return

 if (!videoEl.value) return
 if (!hasVideo.value) return
 if (videoError.value) return
 const playTriggerTime = props.start_time || 0

 if (newTime >= playTriggerTime) {
 const elapsed = (newTime - playTriggerTime) / 1000
 let expectedTime = props.trim_start + elapsed

 if (props.trim_end > 0) {
 const segDur = props.trim_end - props.trim_start
 if (segDur > 0) expectedTime = props.trim_start + (elapsed % segDur)
 } else if (videoEl.value.duration) {
 const segDur = videoEl.value.duration - props.trim_start
 if (segDur > 0) expectedTime = props.trim_start + (elapsed % segDur)
 }

 if (Math.abs(videoEl.value.currentTime - expectedTime) > 0.2) {
 videoEl.value.currentTime = Math.max(0, expectedTime)
 }

 if (isPlaying) {
 if (videoEl.value.readyState >= 2 && videoEl.value.paused) videoEl.value.play().catch(e => console.warn('Autoplay blocked:', e))
 } else {
 if (!videoEl.value.paused) videoEl.value.pause()
 }
 } else {
 if (!videoEl.value.paused) videoEl.value.pause()
 if (Math.abs(videoEl.value.currentTime - props.trim_start) > 0.2) {
 videoEl.value.currentTime = props.trim_start
 }
 }
}, { immediate: true })
</script>
