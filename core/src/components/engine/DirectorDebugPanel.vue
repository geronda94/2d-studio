<template>
  <Transition name="timeline-sheet">
  <div 
    v-if="isOpen"
    ref="panelRef"
    class="fixed bottom-0 left-0 w-full flex flex-col z-[300] font-mono select-none"
    :class="showControls ? 'rounded-t-2xl shadow-2xl overflow-y-auto max-h-[45dvh]' : ''"
  >
    <!-- Мобильный хедер-грабер: явный тоглер сворачивания таймлайна -->
    <div
      v-if="showControls"
      class="flex items-center justify-between px-3 h-8 bg-white border-t border-gray-200"
    >
      <span class="text-[11px] font-bold uppercase tracking-wider text-gray-500">Таймлайн</span>
      <div class="flex items-center gap-1">
        <button
          @click="fitTimeline"
          class="text-gray-500 hover:text-gray-800 p-1"
          title="Вписать (сбросить зум)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"></path><path d="M21 8V5a2 2 0 0 0-2-2h-3"></path><path d="M3 16v3a2 2 0 0 0 2 2h3"></path><path d="M16 21h3a2 2 0 0 0 2-2v-3"></path></svg>
        </button>
        <button
          @click="$emit('collapse')"
          class="text-gray-500 hover:text-gray-800 p-1 -mr-1"
          title="Свернуть таймлайн"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </button>
      </div>
    </div>
    <!-- Скроллер + зум таймлайна (телефон и десктоп): ползунок прокрутки слева,
         ползунок масштаба справа. Скролл-ползунок появляется при зуме >1. -->
    <div
      v-if="showControls"
      class="flex items-center gap-3 px-3 py-1 bg-white border-t border-gray-200"
    >
      <input
        v-if="timelineScrollMax > 0"
        type="range"
        min="0"
        :max="timelineScrollMax"
        step="1"
        :value="globalScrollLeft"
        @input="onTimelinePan($event.target.value)"
        class="flex-1 min-w-0 h-4 accent-brand-blue"
        aria-label="Прокрутка таймлайна"
      />
      <div v-else class="flex-1 min-w-0"></div>

      <div class="flex items-center gap-1 shrink-0 w-[46%] min-w-[130px]" title="Масштаб таймлайна">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 shrink-0"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
        <input
          type="range"
          min="0"
          max="100"
          step="1"
          :value="zoomSliderValue"
          @input="onTimelineZoom($event.target.value)"
          class="flex-1 min-w-0 h-4 accent-brand-orange"
          aria-label="Масштаб таймлайна"
        />
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400 shrink-0"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
      </div>
    </div>
    <!-- LOCAL TIMELINE ROW -->
    <div class="flex w-full">
      <!-- LEFT INFO BLOCK LOCAL -->
      <div class="w-[90px] shrink-0 border-r border-gray-200 flex flex-col z-[60] transition-all bg-white">
        <!-- Local Info Row -->
        <div class="border-t border-gray-200 flex flex-col justify-center items-center transition-all h-[40px] text-[11px] text-gray-500">
          <div class="text-brand-orange font-bold text-sm">{{ formatTime(Math.max(0, currentTime - (currentParsedSlide?.startTime || 0))) }}</div>
          <div class="text-[8px] opacity-60" v-if="true">{{ formatTime(currentParsedSlide?.duration || 0) }}</div>
        </div>
      </div>
      
      <!-- RIGHT TIMELINES COLUMN LOCAL -->
      <div class="flex-1 min-w-0 flex flex-col relative">
        <!-- LOCAL TIMELINE WRAPPER --> 
        <div class="w-full overflow-x-auto overflow-y-hidden hide-scrollbar" 
        ref="localScrollContainer"
        @wheel.prevent="handleLocalWheel"
      >
        <!-- LOCAL TIMELINE INNER -->
        <div 
          class="relative cursor-crosshair overflow-visible group h-[40px] bg-gray-50 border-t border-gray-200 touch-none" 
          :style="{ width: `${100 * zoomLevelLocal}%` }"
          @mousedown="startDragLocal"
          @mousemove="updateHoverLocal"
          @mouseleave="hoverPercentLocal = null"
          @touchstart="onTrackTouchStart($event, 'local')"
          @touchmove="onTrackTouchMove($event, 'local')"
          @touchend="onTrackTouchEnd($event, 'local')"
          @touchcancel="onTrackTouchEnd($event, 'local')"
          ref="localTrack"
        >
          <div class="absolute inset-0 pointer-events-none"></div>
          
          <!-- Event Markers -->
          <div v-for="(event, i) in currentParsedSlide?.events || []" :key="i"
               class="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full transition-all z-20 -translate-x-1/2 ring-2 ring-white"
               :class="[
                 draggedLocalIndex === i ? 'bg-orange-600 scale-125' : 'bg-brand-orange',
                 isEditorOpen ? 'cursor-ew-resize hover:scale-125 hover:bg-orange-600' : 'pointer-events-none'
               ]"
               :style="{ left: (event.time / (currentParsedSlide?.duration || 1)) * 100 + '%' }"
               @mousedown.stop="startDragLocalPoint($event, i)"
          >
            <!-- Tooltip -->
            <div class="absolute top-3 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-gray-800 backdrop-blur text-[9px] rounded border border-gray-600 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
              <span class="text-brand-orange">{{ event.target || event.payload?.target || currentParsedSlide?.componentName || 'Sys' }}</span>.{{ event.action || event.payload?.action || event.type }}
              <span class="text-gray-400 ml-1">[{{ formatTime(event.time) }}]</span>
            </div>
            
            <div v-if="draggedLocalIndex === i" class="absolute top-3 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-brand-orange backdrop-blur text-[10px] font-bold text-white rounded whitespace-nowrap pointer-events-none shadow-lg z-50">
              {{ formatTime(event.time) }}
            </div>
          </div>
          
          <!-- Local Playhead Background -->
          <div class="absolute top-0 bottom-0 bg-brand-orange/20 pointer-events-none transition-transform duration-75"
               :style="{ width: localProgressPercent + '%' }">
          </div>
          <!-- Local Playhead Line -->
          <div class="absolute top-0 bottom-0 w-0.5 bg-brand-orange pointer-events-none transition-transform duration-75 z-10 -translate-x-1/2"
               :style="{ left: localProgressPercent + '%' }">
          </div>

          <!-- Cursor Hover Tooltip & Line -->
          <template v-if="hoverPercentLocal !== null">
            <div class="absolute top-0 bottom-0 w-px bg-brand-orange/40 pointer-events-none z-10"
                 :style="{ left: hoverPercentLocal + '%' }">
            </div>
            <div class="absolute top-1 left-0 px-2 py-0.5 bg-gray-800 backdrop-blur text-[10px] font-bold text-brand-orange rounded border border-brand-orange/20 whitespace-nowrap pointer-events-none z-30 shadow-lg -translate-x-1/2"
                 :style="{ left: hoverPercentLocal + '%' }">
              {{ formatTime(hoverPercentLocal / 100 * (currentParsedSlide?.duration || 0)) }}
            </div>
          </template>
        </div>
        </div>
      </div>
    </div>
    
    <!-- GLOBAL TIMELINE ROW -->
    <div class="flex w-full">
      <!-- LEFT INFO BLOCK GLOBAL -->
      <div class="w-[90px] shrink-0 border-r border-gray-200 flex flex-col z-[60] transition-all bg-white">
        <!-- Global Info Row -->
        <div class="border-t border-gray-200 flex flex-col justify-center items-center transition-all h-[40px] text-[11px] text-gray-500">
          <div class="text-gray-800 font-bold text-sm">{{ formatTime(currentTime) }}</div>
          <div class="text-[8px] opacity-60" v-if="true">{{ formatTime(totalDuration) }}</div>
        </div>
      </div>
  
      <!-- RIGHT TIMELINES COLUMN GLOBAL -->
      <div class="flex-1 min-w-0 flex flex-col relative">
        <!-- GLOBAL TIMELINE WRAPPER -->
      <div 
        class="w-full overflow-x-auto overflow-y-hidden hide-scrollbar" 
        ref="globalScrollContainer"
        @wheel="handleGlobalWheel"
        @scroll="(e) => { globalScrollLeft = e.target.scrollLeft }"
      >
        <!-- GLOBAL TIMELINE INNER -->
        <div 
          class="relative border-t border-gray-200 cursor-crosshair overflow-visible group h-[40px] bg-gray-50 touch-none" 
          :style="{ width: `${100 * zoomLevel}%` }"
          @mousedown="startDragGlobal"
          @mousemove="updateHoverGlobal"
          @mouseleave="hoverPercentGlobal = null"
          @touchstart="onTrackTouchStart($event, 'global')"
          @touchmove="onTrackTouchMove($event, 'global')"
          @touchend="onTrackTouchEnd($event, 'global')"
          @touchcancel="onTrackTouchEnd($event, 'global')"
          ref="globalTrack"
        >
        <div class="absolute inset-0 pointer-events-none"></div>
        
        <!-- Slide Markers (Vertical Lines) -->
        <div v-for="slide in computedSlides" :key="slide.index"
             class="absolute top-0 bottom-0 border-l border-gray-300 pointer-events-none"
             :style="{ left: slide.leftPercent + '%', width: slide.widthPercent + '%' }"
        ></div>

        <!-- Slide Draggable Points -->
        <div v-for="slide in computedSlides" :key="'marker-'+slide.index"
              class="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full z-30 -translate-x-1/2 transition-all duration-200 ring-2 ring-white"
             :class="[
               slide.componentName === 'EndMarkerSlide' ? 
                 (slide.index === currentSlide ? 'bg-red-600 scale-125' : 'bg-red-500') :
                 (slide.index === currentSlide ? 'bg-gray-800 scale-125' : 'bg-gray-500'),
               (isEditorOpen && slide.index > 0) ? (slide.componentName === 'EndMarkerSlide' ? 'cursor-ew-resize hover:bg-red-600 hover:scale-125' : 'cursor-ew-resize hover:bg-gray-700 hover:scale-125') : 'pointer-events-none'
             ]"
             :style="{ left: slide.leftPercent + '%' }"
             @mousedown.stop="startDragSlidePoint($event, slide.index)"
        >
          <div v-if="draggedSlideIndex === slide.index" class="absolute top-4 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-gray-900 text-[10px] font-bold text-white rounded whitespace-nowrap pointer-events-none z-50">
            {{ formatTime(slide.startTime) }}
          </div>
        </div>
        
        <!-- Playhead Background - soft blue fill shows progress in light mode -->
        <div class="absolute top-0 bottom-0 bg-brand-blue/10 pointer-events-none transition-transform duration-75"
             :style="{ width: globalProgressPercent + '%' }">
        </div>
        <!-- Playhead Line (unified with audio) -->
        <div class="absolute top-0 bottom-0 w-[1px] bg-red-500 pointer-events-none z-40"
             :style="{ left: globalProgressPercent + '%' }">
             <!-- Triangle on top -->
             <div class="absolute -top-1 -left-1.5 w-3 h-3 bg-red-500 rounded-sm" style="clip-path: polygon(0 0, 100% 0, 50% 100%)"></div>
        </div>

        <!-- Cursor Hover Tooltip & Line -->
        <template v-if="hoverPercentGlobal !== null">
          <div class="absolute top-0 bottom-0 w-px bg-text-muted pointer-events-none z-10"
               :style="{ left: hoverPercentGlobal + '%' }">
          </div>
          <div class="absolute top-1 left-0 px-2 py-0.5 bg-gray-800 backdrop-blur text-[10px] font-bold text-white rounded border border-gray-600 whitespace-nowrap pointer-events-none z-50 shadow-lg -translate-x-1/2"
               :style="{ left: hoverPercentGlobal + '%' }">
            {{ formatTime(hoverPercentGlobal / 100 * totalDuration) }}
          </div>
        </template>
        </div>
      </div>
    </div>
  </div>
    
  <!-- AUDIO TIMELINE WRAPPER -->
    <AudioTimeline
      class="w-full shrink-0"
      :audioTimeline="audioTimeline"
      :zoomLevel="zoomLevelGlobalForAudio"
      :totalDuration="totalDuration"
      :snapPoints="snapPoints"
      :currentTime="currentTime"
      :recordingTrackId="recordingTrackId"
      :isFullscreen="isFullscreen"
      :isEditorOpen="isEditorOpen"
      :syncScrollLeft="globalScrollLeft"
      :trackWidthPx="globalTrackWidthPx"
      @scroll-request="handleAudioWheel"
      @update-audio-timeline="handleUpdateAudioTimeline"
      @request-add-audio="(trackId) => emit('request-add-audio', trackId)"
      @toggle-record="$emit('toggle-record', $event)"
      @request-generate-voice="$emit('request-generate-voice',
  'edit-clip', $event)"
      @seek="(t) => { emit('seek', t); syncStateToTime(t); }"
    />
    

  </div>
  </Transition>
</template>

<script setup>
import { computed, inject, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDirector } from '../../composables/useDirector'
import AudioTimeline from './AudioTimeline.vue'
import { useMobile } from '../../composables/useMobile'

const { isMobile, isTouch } = useMobile()
const showControls = computed(() => isMobile.value || isTouch.value)

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  slidesData: {
    type: Array,
    default: () => []
  },
  isEditorOpen: {
    type: Boolean,
    default: false
  },
  isFullscreen: {
    type: Boolean,
    default: false
  },
  currentSlide: Number,
  timeline: Object,
  audioTimeline: Object,
  recordingTrackId: {
    type: String,
    default: null
  }
})
const emit = defineEmits([
  'update-timing', 
  'update-local-timing', 
  'dragging-local-timing', 
  'update-audio-timeline',
  'request-add-audio',
  'seek',
  'toggle-record',
  'request-generate-voice',
  'edit-clip',
  'collapse',
  'height'
])

const currentSlide = inject('currentSlide')
const goTo = inject('goTo')

const { currentTime, timelineEvents, seek, isPlaying } = useDirector()

// Высота панели — единый источник правды для --timeline-height.
// От неё зависят: padding плеера (desktop), нижняя граница nav-drawer и ужим слайда (mobile).
const panelRef = ref(null)
let panelObserver = null

const syncTimelineHeight = () => {
  const open = props.isOpen && !props.isFullscreen
  const h = open && panelRef.value
    ? Math.round(panelRef.value.getBoundingClientRect().height)
    : 0
  document.documentElement.style.setProperty('--timeline-height', h + 'px')
  emit('height', h)
}

watch(() => [props.isOpen, props.isFullscreen], async () => {
  await nextTick()
  if (panelRef.value && panelObserver) {
    panelObserver.disconnect()
    panelObserver.observe(panelRef.value)
  }
  syncTimelineHeight()
}, { immediate: true })

onMounted(() => {
  panelObserver = new ResizeObserver(() => syncTimelineHeight())
})

onUnmounted(() => {
  panelObserver?.disconnect()
  document.documentElement.style.setProperty('--timeline-height', '0px')
})

const globalTrack = ref(null)
const localTrack = ref(null)

const hoverPercentGlobal = ref(null)
const hoverPercentLocal = ref(null)

let isDraggingGlobal = false
let isDraggingLocal = false

const zoomLevel = ref(1)
const zoomLevelLocal = ref(1)
const hasAutoZoomed = ref(false)


const globalScrollContainer = ref(null)
const localScrollContainer = ref(null)
const isAutoScrollPaused = ref(false)

const globalScrollLeft = ref(0)
const globalTrackWidthPx = ref(0)
const zoomLevelGlobalForAudio = computed(() => zoomLevel.value)

// Keep globalTrackWidthPx in sync so AudioTimeline inner tracks are pixel-perfect
let globalTrackResizeObserver = null
watch(globalTrack, (el) => {
  if (globalTrackResizeObserver) globalTrackResizeObserver.disconnect()
  if (!el) return
  globalTrackResizeObserver = new ResizeObserver(() => {
    globalTrackWidthPx.value = el.offsetWidth
  })
  globalTrackResizeObserver.observe(el)
  globalTrackWidthPx.value = el.offsetWidth
})

// Горизонтальный скроллбар таймлайна (телефон): диапазон = прокручиваемый «хвост».
const scrollViewportW = ref(0)
const timelineScrollMax = computed(() =>
  Math.max(0, Math.round((globalTrackWidthPx.value || 0) - (scrollViewportW.value || 0))),
)

let scrollViewportObserver = null
watch(globalScrollContainer, (el) => {
  if (scrollViewportObserver) scrollViewportObserver.disconnect()
  if (!el) return
  scrollViewportObserver = new ResizeObserver(() => {
    scrollViewportW.value = el.clientWidth
  })
  scrollViewportObserver.observe(el)
  scrollViewportW.value = el.clientWidth
})

const onTimelinePan = (v) => {
  const c = globalScrollContainer.value
  if (!c) return
  c.scrollLeft = Number(v) || 0
  globalScrollLeft.value = c.scrollLeft
  isAutoScrollPaused.value = true
}

// Зум-слайдер рядом со скроллером (телефон/десктоп): экспоненциальная шкала
// 1x..50x, чтобы и мелкий, и крупный зум были удобны. Якорь — центр вьюпорта.
const zoomSliderValue = computed(() => {
  const z = Math.max(1, Number(zoomLevel.value) || 1)
  return Math.round((Math.log(z) / Math.log(50)) * 100)
})

const onTimelineZoom = (v) => {
  const z = clampZoom(Math.pow(50, (Number(v) || 0) / 100))
  const container = globalScrollContainer.value
  if (!container) {
    zoomLevel.value = z
    return
  }
  const cRect = container.getBoundingClientRect()
  applyZoomAnchored("global", z, cRect.left + container.clientWidth / 2)
  isAutoScrollPaused.value = true
}

const handleGlobalWheel = (e) => {
  e.preventDefault()
  if (e.shiftKey) {
    // Browsers convert Shift+Wheel to deltaX
    const delta = e.deltaY !== 0 ? e.deltaY : e.deltaX
    const zoomFactor = delta > 0 ? 0.9 : 1.1
    if (!globalScrollContainer.value || !globalTrack.value) return
    const container = globalScrollContainer.value
    const scrollLeft = container.scrollLeft
    
    let anchorRatio = 0
    let anchorScreenX = 0
    
    if (totalDuration.value > 0) {
      anchorRatio = currentTime.value / totalDuration.value
      anchorScreenX = (anchorRatio * globalTrack.value.clientWidth) - scrollLeft
    } else {
      const rect = container.getBoundingClientRect()
      anchorScreenX = e.clientX - rect.left
      anchorRatio = (scrollLeft + anchorScreenX) / globalTrack.value.clientWidth
    }
    
    zoomLevel.value = Math.max(1, Math.min(50, zoomLevel.value * zoomFactor))
    
    nextTick(() => {
      if (!globalTrack.value) return
      const newScrollLeft = anchorRatio * globalTrack.value.clientWidth - anchorScreenX
      container.scrollLeft = newScrollLeft
      globalScrollLeft.value = newScrollLeft
      isAutoScrollPaused.value = true
    })
  } else {
    if (globalScrollContainer.value) {
      globalScrollContainer.value.scrollLeft += (e.deltaX !== 0 ? e.deltaX : e.deltaY)
      globalScrollLeft.value = globalScrollContainer.value.scrollLeft
      isAutoScrollPaused.value = true
    }
  }
}

const handleAudioWheel = (e) => {
  // If audio track sends a direct scrollLeft (from its own scroll event), apply it
  if (e._scrollLeft !== undefined) {
    if (globalScrollContainer.value) {
      globalScrollContainer.value.scrollLeft = e._scrollLeft
      globalScrollLeft.value = e._scrollLeft
    }
    return
  }
  // Otherwise delegate to global wheel handler (for zoom/scroll from audio row)
  handleGlobalWheel(e)
}

const handleUpdateAudioTimeline = (data) => {
  emit('update-audio-timeline', data)
}

const handleLocalWheel = (e) => {
  e.preventDefault()
  if (e.shiftKey) {
    const delta = e.deltaY !== 0 ? e.deltaY : e.deltaX
    const zoomFactor = delta > 0 ? 0.9 : 1.1
    if (!localScrollContainer.value || !localTrack.value) return
    const container = localScrollContainer.value
    const scrollLeft = container.scrollLeft
    
    let anchorRatio = 0
    let anchorScreenX = 0
    
    const localTotal = currentParsedSlide.value?.duration || 0
    
    if (localTotal > 0) {
      const localTime = Math.max(0, Math.min(localTotal, currentTime.value - (currentParsedSlide.value?.startTime || 0)))
      anchorRatio = localTime / localTotal
      anchorScreenX = (anchorRatio * localTrack.value.clientWidth) - scrollLeft
    } else {
      const rect = container.getBoundingClientRect()
      anchorScreenX = e.clientX - rect.left
      anchorRatio = (scrollLeft + anchorScreenX) / localTrack.value.clientWidth
    }
    
    zoomLevelLocal.value = Math.max(1, Math.min(50, zoomLevelLocal.value * zoomFactor))
    
    nextTick(() => {
      if (!localTrack.value) return
      const newScrollLeft = anchorRatio * localTrack.value.clientWidth - anchorScreenX
      container.scrollLeft = newScrollLeft
    })
  } else {
    if (localScrollContainer.value) {
      localScrollContainer.value.scrollLeft += (e.deltaX !== 0 ? e.deltaX : e.deltaY)
    }
  }
}

watch(() => isPlaying.value, (newVal) => {
  if (newVal) isAutoScrollPaused.value = false
})

// Format ms to MM:SS.d (e.g. 01:23.5)
const formatTime = (ms) => {
  if (ms === undefined || ms === null || isNaN(ms)) return '00:00.0'
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  const deciseconds = Math.floor((ms % 1000) / 100)
  
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${deciseconds}`
}

const computedSlides = computed(() => {
  const slides = props.slidesData || []
  if (slides.length === 0) return []
  
  let lastEventTime = 0
  if (timelineEvents.value.length > 0) {
    lastEventTime = timelineEvents.value[timelineEvents.value.length - 1].time
  }
  
  const parsed = slides.map((slide, index) => {
    const startTime = slide.start_time || slide.startTime || 0
    let nextTime = 0
    if (index < slides.length - 1) {
      nextTime = slides[index + 1].start_time || slides[index + 1].startTime || 0
    } else {
      nextTime = Math.max(startTime + 5000, lastEventTime)
    }
    if (nextTime < startTime) nextTime = startTime // prevent negative duration
    
    let events = [...(slide.data?.director || slide.events || [])]
    
    // Extract implicit events recursively from inner arrays that have start_time or time
    if (slide.data) {
      const extractEvents = (obj, prefix = '') => {
        if (!obj || typeof obj !== 'object') return
        
        if (prefix !== '' && obj.start_time !== undefined && !Array.isArray(obj)) {
           const t = Number(obj.start_time)
           if (!isNaN(t)) {
             events.push({
               time: t,
               target: prefix.split('.').pop().toUpperCase(),
               action: 'Start',
               type: 'implicit_root',
               propPath: prefix,
               timeProp: 'start_time'
             })
           }
        }
        
        Object.keys(obj).forEach(key => {
          const val = obj[key]
          if (Array.isArray(val)) {
            val.forEach((item, itemIdx) => {
              const tVal = item.start_time !== undefined ? item.start_time : item.time
              if (tVal !== undefined && tVal !== null) {
                const t = Number(tVal)
                if (!isNaN(t)) {
                  events.push({
                    time: t,
                    target: (prefix ? prefix + '.' + key : key).toUpperCase(),
                    action: `Item ${itemIdx + 1}`,
                    type: 'implicit',
                    arrayPath: prefix ? `${prefix}.${key}` : key,
                    itemIndex: itemIdx,
                    timeProp: item.start_time !== undefined ? 'start_time' : 'time'
                  })
                }
              }
            })
          } else if (typeof val === 'object' && val !== null) {
            extractEvents(val, prefix ? prefix + '.' + key : key)
          }
        })
      }
      
      extractEvents(slide.data)
      // Sort events by time just in case
      events.sort((a, b) => a.time - b.time)
    }

    return {
      index,
      startTime,
      endTime: nextTime,
      duration: nextTime - startTime,
      events: events,
      componentName: slide.component || 'Slide'
    }
  })
  
  const total = parsed[parsed.length - 1].endTime
  
  let totalDur = total
  if (props.audioTimeline && props.audioTimeline.tracks) {
    props.audioTimeline.tracks.forEach(t => {
      if (t.clips) {
        t.clips.forEach(c => {
          if (c.end_time > totalDur) totalDur = c.end_time
        })
      }
    })
  }
  
  return parsed.map(slide => ({
    ...slide,
    leftPercent: totalDur > 0 ? (slide.startTime / totalDur) * 100 : 0,
    widthPercent: totalDur > 0 ? (slide.duration / totalDur) * 100 : 0
  }))
})

const totalDuration = computed(() => {
  let dur = 0
  if (computedSlides.value.length > 0) {
    dur = computedSlides.value[computedSlides.value.length - 1].endTime
  }
  if (props.audioTimeline && props.audioTimeline.tracks) {
    props.audioTimeline.tracks.forEach(t => {
      if (t.clips) {
        t.clips.forEach(c => {
          if (c.end_time > dur) dur = c.end_time
        })
      }
    })
  }
  return dur
})

watch([
  () => totalDuration.value, 
  () => computedSlides.value.length > 0 ? computedSlides.value[computedSlides.value.length - 1].endTime : 0
], ([newTotal, newSlides]) => {
  // На телефоне «комфортный» дефолт — вписать всю дорожку (1x), дальше пинч-зум.
  if (isMobile.value) {
    zoomLevel.value = 1
    zoomLevelLocal.value = 1
    hasAutoZoomed.value = true
    return
  }
  if (!hasAutoZoomed.value && newSlides > 0 && newTotal > newSlides) {
    zoomLevel.value = Math.max(1, newTotal / (newSlides * 1.05))
    hasAutoZoomed.value = true
  }
}, { immediate: true })

const snapPoints = computed(() => {
  const points = new Set([0, totalDuration.value])
  
  computedSlides.value.forEach(slide => {
    points.add(slide.startTime)
    points.add(slide.endTime)
  })

  timelineEvents.value.forEach(ev => {
    points.add(ev.time)
  })
  
  if (props.audioTimeline && props.audioTimeline.tracks) {
    props.audioTimeline.tracks.forEach(t => {
      if (t.clips) {
        t.clips.forEach(c => {
          points.add(c.start_time)
          points.add(c.end_time)
        })
      }
    })
  }

  return Array.from(points).sort((a, b) => a - b)
})

const globalProgressPercent = computed(() => {
  if (totalDuration.value === 0) return 0
  return Math.min(100, Math.max(0, (currentTime.value / totalDuration.value) * 100))
})

// watch(globalProgressPercent, () => {
//   if (zoomLevel.value > 1 && globalScrollContainer.value && globalTrack.value) {
//     if (isAutoScrollPaused.value) return
//     
//     const trackWidth = globalTrack.value.clientWidth
//     const playheadX = (globalProgressPercent.value / 100) * trackWidth
//     const containerWidth = globalScrollContainer.value.clientWidth
//     const targetScrollLeft = playheadX - containerWidth / 2
//     
//     globalScrollContainer.value.scrollLeft = targetScrollLeft
//     globalScrollLeft.value = targetScrollLeft
//   }
// })

const currentParsedSlide = computed(() => {
  if (computedSlides.value.length === 0) return null
  return computedSlides.value[currentSlide.value] || null
})

const localTime = computed(() => {
  if (!currentParsedSlide.value) return 0
  return Math.max(0, currentTime.value - currentParsedSlide.value.startTime)
})

const localProgressPercent = computed(() => {
  if (!currentParsedSlide.value || currentParsedSlide.value.duration === 0) return 0
  return Math.min(100, Math.max(0, (localTime.value / currentParsedSlide.value.duration) * 100))
})

const syncStateToTime = (timeMs) => {
  if (computedSlides.value.length === 0) return
  let targetIndex = computedSlides.value.length - 1
  for (const slide of computedSlides.value) {
    if (timeMs >= slide.startTime && timeMs < slide.endTime) {
      targetIndex = slide.index
      break
    }
  }
  
  if (currentSlide.value !== targetIndex && typeof goTo === 'function') {
    goTo(targetIndex, true)
  }
}

const draggedSlideIndex = ref(-1)
const draggedLocalIndex = ref(-1)
let dragStartTotalDuration = 0

const startDragSlidePoint = (e, index) => {
  if (typeof goTo === 'function') {
    goTo(index, true)
  }
  
  if (!props.isEditorOpen || index === 0) return
  isDraggingGlobal = true // Reuse global drag state to capture mousemove
  draggedSlideIndex.value = index
  dragStartTotalDuration = totalDuration.value
  e.stopPropagation()
}

// Drag & Scrubbing Logic
const updateHoverGlobal = (e) => {
  if (!globalTrack.value) return
  const rect = globalTrack.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
  hoverPercentGlobal.value = (x / rect.width) * 100
  
  if (isDraggingGlobal && draggedSlideIndex.value > 0) {
    const timeMs = (hoverPercentGlobal.value / 100) * (dragStartTotalDuration || totalDuration.value)
    let newTime = timeMs
    
    // Snapping logic for slide points
    if (globalTrack.value) {
      const rect = globalTrack.value.getBoundingClientRect()
      const msPerPixel = (dragStartTotalDuration || totalDuration.value) / rect.width
      const snapPixels = Math.max(8, 25 / zoomLevel.value)
      const snapThresholdMs = snapPixels * msPerPixel
      
      const currentOldTime = props.slidesData[draggedSlideIndex.value].start_time || props.slidesData[draggedSlideIndex.value].startTime || 0
      
      let bestPt = newTime
      let minDiff = snapThresholdMs
      for (const pt of snapPoints.value) {
        if (Math.abs(pt - currentOldTime) < 1) continue // Skip self
        const diff = Math.abs(newTime - pt)
        if (diff < minDiff) {
          minDiff = diff
          bestPt = pt
        }
      }
      newTime = bestPt
    }
    
    const prevSlide = computedSlides.value[draggedSlideIndex.value - 1]
    const minTime = prevSlide ? prevSlide.startTime + 2000 : 0
    
    if (newTime < minTime) newTime = minTime
    
    const currentTimeInProps = props.slidesData[draggedSlideIndex.value].start_time || props.slidesData[draggedSlideIndex.value].startTime || 0
    const delta = newTime - currentTimeInProps
    
    if (delta !== 0) {
      for (let i = draggedSlideIndex.value; i < props.slidesData.length; i++) {
        const slide = props.slidesData[i]
        const oldTime = slide.start_time || slide.startTime || 0
        slide.start_time = oldTime + delta
        if (slide.startTime !== undefined) {
           slide.startTime = oldTime + delta
        }
      }
    }
  }
}

const updateHoverLocal = (e) => {
  if (!localTrack.value) return
  const rect = localTrack.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
  hoverPercentLocal.value = (x / rect.width) * 100
  
  if (isDraggingLocal && draggedLocalIndex.value >= 0 && currentParsedSlide.value) {
    const percent = hoverPercentLocal.value / 100
    let newTime = Math.round(percent * currentParsedSlide.value.duration)
    
    const event = currentParsedSlide.value.events[draggedLocalIndex.value]
    
    if (event && event.type === 'implicit_root' && event.propPath) {
      if (newTime < 0) newTime = 0
      
      const slideData = props.slidesData[currentParsedSlide.value.index].data
      
      const pathParts = event.propPath.split('.')
      let obj = slideData
      for (const part of pathParts) {
        if (obj && obj[part] !== undefined) {
          obj = obj[part]
        } else {
          obj = null
          break
        }
      }
      
      if (obj) {
        obj[event.timeProp] = newTime
      }
      
      emit('dragging-local-timing', currentParsedSlide.value.index, slideData)
    }
    else if (event && event.type === 'implicit' && event.arrayPath) {
      // Find previous element in the same array
      let prevTime = 0
      for (let i = draggedLocalIndex.value - 1; i >= 0; i--) {
        const prevEvent = currentParsedSlide.value.events[i]
        if (prevEvent.type === 'implicit' && prevEvent.arrayPath === event.arrayPath && prevEvent.itemIndex === event.itemIndex - 1) {
          prevTime = prevEvent.time + 100
          break
        }
      }
      
      if (newTime < prevTime) newTime = prevTime
      
      // Update data reactively
      const slideData = props.slidesData[currentParsedSlide.value.index].data
      
      // Get array
      const pathParts = event.arrayPath.split('.')
      let arr = slideData
      for (const part of pathParts) {
        if (arr && arr[part]) {
          arr = arr[part]
        } else {
          arr = null
          break
        }
      }
      
      if (Array.isArray(arr) && arr[event.itemIndex]) {
        const item = arr[event.itemIndex]
        const oldTime = item[event.timeProp] !== undefined ? item[event.timeProp] : item.time
        const delta = newTime - oldTime
        
        if (delta !== 0) {
          // Cascade shift all subsequent items in the array
          for (let i = event.itemIndex; i < arr.length; i++) {
            const subsequentItem = arr[i]
            const t = subsequentItem[event.timeProp] !== undefined ? subsequentItem[event.timeProp] : subsequentItem.time
            subsequentItem[event.timeProp !== undefined ? event.timeProp : 'time'] = t + delta
          }
        }
      }
      
      emit('dragging-local-timing', currentParsedSlide.value.index, slideData)
    }
  }
}

const startDragLocalPoint = (e, index) => {
  isDraggingLocal = true
  draggedLocalIndex.value = index
}

const doSeekGlobal = (clientX) => {
  if (!globalTrack.value || totalDuration.value === 0) return
  if (draggedSlideIndex.value > 0) return // Don't seek if we are dragging a point!
  const rect = globalTrack.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(clientX - rect.left, rect.width))
  const percent = x / rect.width
  let timeMs = percent * totalDuration.value
  
  // Snap
  const msPerPixel = totalDuration.value / rect.width
  const snapPixels = Math.max(8, 25 / zoomLevel.value)
  const snapThresholdMs = snapPixels * msPerPixel
  for (const pt of snapPoints.value) {
    if (Math.abs(timeMs - pt) < snapThresholdMs) {
      timeMs = pt
      break
    }
  }
  
  seek(timeMs)
  syncStateToTime(timeMs)
}

const doSeekLocal = (clientX) => {
  if (!localTrack.value || !currentParsedSlide.value || currentParsedSlide.value.duration === 0) return
  const rect = localTrack.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(clientX - rect.left, rect.width))
  const percent = x / rect.width
  let timeMs = currentParsedSlide.value.startTime + (percent * currentParsedSlide.value.duration)
  
  // Snap
  const msPerPixel = currentParsedSlide.value.duration / rect.width
  const snapPixels = Math.max(8, 25 / zoomLevelLocal.value)
  const snapThresholdMs = snapPixels * msPerPixel
  for (const pt of snapPoints.value) {
    if (Math.abs(timeMs - pt) < snapThresholdMs) {
      timeMs = pt
      break
    }
  }

  seek(timeMs)
  syncStateToTime(timeMs)
}

const startDragGlobal = (e) => {
  isAutoScrollPaused.value = false
  isDraggingGlobal = true
  document.body.classList.add('is-seeking')
  doSeekGlobal(e.clientX)
}

const startDragLocal = (e) => {
  isDraggingLocal = true
  document.body.classList.add('is-seeking')
  doSeekLocal(e.clientX)
}

const onMouseMove = (e) => {
  if (isDraggingGlobal) {
    if (draggedSlideIndex.value > 0) {
      updateHoverGlobal(e) // Handled differently if dragging a point
    } else {
      doSeekGlobal(e.clientX)
      updateHoverGlobal(e)
    }
  }
  if (isDraggingLocal) {
    if (draggedLocalIndex.value >= 0) {
      updateHoverLocal(e)
    } else {
      doSeekLocal(e.clientX)
      updateHoverLocal(e)
    }
  }
}

const onMouseUp = () => {
  if (isDraggingGlobal && draggedSlideIndex.value > 0) {
    const finalTime = props.slidesData[draggedSlideIndex.value].start_time || props.slidesData[draggedSlideIndex.value].startTime || 0
    emit('update-timing', draggedSlideIndex.value, finalTime)
  }
  
  if (isDraggingLocal && draggedLocalIndex.value >= 0 && currentParsedSlide.value) {
    emit('update-local-timing', currentParsedSlide.value.index)
  }
  
  isDraggingGlobal = false
  isDraggingLocal = false
  draggedSlideIndex.value = -1
  draggedLocalIndex.value = -1
  document.body.classList.remove('is-seeking')
}

const seekToEvent = (event) => {
  if (!currentParsedSlide.value) return
  const timeMs = currentParsedSlide.value.startTime + event.time
  seek(timeMs)
  syncStateToTime(timeMs)
}

// === MOBILE GESTURES ===
// Одним пальцем — скраб (seek), двумя — пинч-зум с якорем под пальцами и панорама.
let pinchStartDist = 0
let pinchStartZoom = 1

const touchDist = (t) =>
  Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY)
const touchMidX = (t) => (t[0].clientX + t[1].clientX) / 2
const clampZoom = (z) => Math.max(1, Math.min(50, z))

// Меняем зум так, чтобы точка под пальцем (anchorClientX) оставалась на месте.
const applyZoomAnchored = (kind, newZoom, anchorClientX) => {
  const isGlobal = kind === "global"
  const container = isGlobal ? globalScrollContainer.value : localScrollContainer.value
  const track = isGlobal ? globalTrack.value : localTrack.value
  const zoomRef = isGlobal ? zoomLevel : zoomLevelLocal
  if (!container || !track) {
    zoomRef.value = newZoom
    return
  }
  const cRect = container.getBoundingClientRect()
  const anchorScreenX = anchorClientX - cRect.left
  const contentX = container.scrollLeft + anchorScreenX
  const ratio = contentX / track.clientWidth
  zoomRef.value = newZoom
  nextTick(() => {
    container.scrollLeft = ratio * track.clientWidth - anchorScreenX
    if (isGlobal) globalScrollLeft.value = container.scrollLeft
  })
}

const onTrackTouchStart = (e, kind) => {
  if (e.touches.length === 1) {
    if (kind === "global") {
      isAutoScrollPaused.value = false
      isDraggingGlobal = true
      doSeekGlobal(e.touches[0].clientX)
    } else {
      isDraggingLocal = true
      doSeekLocal(e.touches[0].clientX)
    }
  } else if (e.touches.length === 2) {
    isDraggingGlobal = false
    isDraggingLocal = false
    pinchStartDist = touchDist(e.touches) || 1
    pinchStartZoom = kind === "global" ? zoomLevel.value : zoomLevelLocal.value
    e.preventDefault()
  }
}

const onTrackTouchMove = (e, kind) => {
  if (e.touches.length === 1) {
    if (kind === "global" && isDraggingGlobal) {
      doSeekGlobal(e.touches[0].clientX)
      e.preventDefault()
    } else if (kind === "local" && isDraggingLocal) {
      doSeekLocal(e.touches[0].clientX)
      e.preventDefault()
    }
  } else if (e.touches.length === 2) {
    e.preventDefault()
    const d = touchDist(e.touches) || 1
    const newZoom = clampZoom(pinchStartZoom * (d / pinchStartDist))
    applyZoomAnchored(kind, newZoom, touchMidX(e.touches))
  }
}

const onTrackTouchEnd = (e, kind) => {
  if (e.touches.length === 0) {
    if (kind === "global") isDraggingGlobal = false
    else isDraggingLocal = false
  }
}

// «Вписать»: сбросить зум к 1x (вся дорожка видна) и показать текущее время
const fitTimeline = () => {
  zoomLevel.value = 1
  zoomLevelLocal.value = 1
  nextTick(() => {
    const c = globalScrollContainer.value
    const t = globalTrack.value
    if (c && t && totalDuration.value > 0) {
      const ratio = currentTime.value / totalDuration.value
      c.scrollLeft = Math.max(0, ratio * t.clientWidth - c.clientWidth / 2)
      globalScrollLeft.value = c.scrollLeft
    }
  })
}
// "в стандартном режиме мы видели на таймлайне в каком месте находится текущий слайд"
watch(currentSlide, (newIndex) => {
  if (!isPlaying.value && computedSlides.value[newIndex]) {
    seek(computedSlides.value[newIndex].startTime)
  }
})
onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
/* Выезд таймлайна снизу (desktop и mobile) */
.timeline-sheet-enter-active,
.timeline-sheet-leave-active {
  transition: transform 0.25s ease-out;
}
.timeline-sheet-enter-from,
.timeline-sheet-leave-to {
  transform: translateY(100%);
}
</style>
