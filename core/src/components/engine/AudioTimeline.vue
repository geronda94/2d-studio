<template>
  <div class="flex flex-col w-full text-xs font-mono select-none relative overflow-hidden">
    <div class="flex flex-col w-full overflow-y-auto hide-scrollbar"
         :style="{ maxHeight: visibleTrackIds.length > 2 ? '96px' : 'none' }">
      <div v-for="trackId in visibleTrackIds" :key="trackId" 
           class="flex flex-row items-center border-t border-gray-200 group/track relative transition-all shrink-0 h-[48px] bg-white">
      
      <!-- Track Header (Left Info Block) -->
      <div class="w-[90px] shrink-0 border-r border-gray-200 h-full flex flex-col justify-center px-2 z-[60] bg-white">
        <div class="flex flex-row items-center justify-between w-full">
          <template v-if="selectedClips.some(sel => sel.trackId === trackId)">
            <button @click="splitSelectedClip" class="p-1 hover:bg-bg-surface rounded text-text-secondary hover:text-text-primary transition-colors" title="Разрезать (S, C, X)">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>
            </button>
            <button @click="duplicateSelectedClip" class="p-1 hover:bg-bg-surface rounded text-text-secondary hover:text-text-primary transition-colors" title="Дублировать (D)">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            </button>
            <button @click="deleteSelectedClip" class="p-1 hover:bg-red-500/20 rounded text-text-secondary hover:text-red-400 transition-colors" title="Удалить (Del)">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
            <button @click="selectedClips = []" class="p-1 text-text-muted hover:text-text-primary transition-colors" title="Отменить выделение">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </template>
          <template v-else>
            <span class="text-text-secondary text-[10px] uppercase font-bold tracking-wider"
                  :class="{ 'text-brand-orange': trackId === 'main', 'text-brand-light-blue': trackId === 'bgm', 'text-red-400': trackId === 'sfx' }">
              {{ trackId === 'main' ? '1' : trackId === 'overlay' ? '2' : trackId === 'bgm' ? '3' : '4' }}
            </span>
            <div class="flex gap-1">
              <button @click="emit('toggle-record', trackId)" 
                      class="p-0.5 rounded transition-colors" 
                      :class="recordingTrackId === trackId ? 'text-red-500 animate-pulse bg-red-500/20' : 'text-text-muted hover:text-red-400'" 
                      :title="recordingTrackId === trackId ? 'Остановить запись' : 'Записать голос (Микрофон)'">
                <svg v-if="recordingTrackId !== trackId" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
              </button>
              <button @click="emit('request-generate-voice', trackId)" class="text-text-muted hover:text-brand-blue p-0.5 rounded transition-colors" title="Сгенерировать ИИ голос (Gemini)">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path><path d="M12 8v4l3 3"></path></svg>
              </button>
              <button @click="emit('request-add-audio', trackId)" class="text-text-muted hover:text-text-primary p-0.5 rounded transition-colors" title="Добавить аудио">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              </button>
              <button class="text-text-muted hover:text-text-primary p-0.5 rounded transition-colors" title="Mute Track">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon></svg>
              </button>
              <button v-if="trackId !== visibleTrackIds[0]" @click="removeTrack(trackId)" class="text-text-muted hover:text-red-400 p-0.5 rounded transition-colors" title="Удалить дорожку">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </template>
        </div>
        <!-- Add New Track Button (Only on the first track) -->
        <button v-if="trackId === visibleTrackIds[0] && visibleTrackIds.length < 4" 
                @click="addNextTrack"
                class="mt-1 text-[8px] text-text-muted hover:text-text-primary text-left transition-colors flex items-center gap-0.5 w-full"
                title="Добавить новую аудио-дорожку">
          <svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          TRACK
        </button>
      </div>

      <!-- Track Timeline Body (Right Column) - Real overflow-x scroll, synced with global -->
      <div class="flex-1 min-w-0 h-full overflow-x-auto overflow-y-hidden hide-scrollbar relative"
           :ref="el => { if (el) trackScrollers[trackId] = el }"
           @wheel="handleWheel"
           @scroll.passive="onTrackScroll">
        
        <div class="relative h-full overflow-visible touch-none" 
             :style="{ width: trackWidthPx > 0 ? `${trackWidthPx}px` : `${100 * zoomLevel}%`, minWidth: '100%' }"
             @mousedown="startSeek($event, trackId); selectedClips = []"
             @touchstart="onTouchSeekStart($event, trackId)"
             @touchmove="onTouchSeekMove($event, trackId)"
             @touchend="onTouchSeekEnd"
             @touchcancel="onTouchSeekEnd"
             :ref="el => { if (el) trackInners[trackId] = el }"
              :class="'bg-gray-50'">
          
          <!-- Audio Clips -->
          <div v-for="(clip, idx) in getTrackClips(trackId)" :key="clip.id"
               class="absolute top-1 bottom-1 rounded border overflow-hidden cursor-move flex items-center px-1 group/clip transition-colors"
               :class="[getClipColors(trackId, clip.type), isClipSelected(trackId, clip.id) ? 'ring-1 ring-white z-20 shadow-md border-transparent' : 'border-transparent z-10', hoveredBatchId && clip.ai_settings?.batch_id === hoveredBatchId ? 'ring-1 ring-[#A78BFA] bg-[#A78BFA]/40 z-15' : '']"
               :style="{ left: getLeftPercent(clip) + '%', width: getWidthPercent(clip) + '%' }"
               @mouseenter="hoveredBatchId = clip.ai_settings?.batch_id || null"
               @mouseleave="hoveredBatchId = null"
               @mousedown.stop="selectClip($event, trackId, clip.id); startDragClip($event, trackId, idx)"
               @contextmenu.prevent="showContextMenu($event, trackId, clip.id, idx)">
            
            <!-- Waveform Canvas - drawn from decoded audio peaks -->
            <WaveformCanvas
              :src="clip.src || clip.file_path || null"
              :color="clip.type === 'ai_voice' ? 'rgba(139,92,246,0.65)' : 'rgba(22,163,74,0.65)'"
              :bar-width="1"
              :gap="1"
              :offset="clip.media_offset || 0"
              :duration="Math.max(0, (clip.end_time || 0) - (clip.start_time || 0))"
            />

            <!-- Volume tint overlay (subtle, shown on top of waveform) -->
            <div class="absolute left-0 right-0 bottom-0 opacity-20 pointer-events-none transition-all z-0"
                 :class="clip.type === 'ai_voice' ? 'bg-purple-500' : 'bg-green-600'"
                 :style="{ height: `${(clip.volume !== undefined ? clip.volume : 1) * 100}%` }"></div>

            <div class="truncate text-[9px] px-1 opacity-90 pointer-events-none relative z-10 flex items-center gap-1 font-semibold drop-shadow-sm">
              <svg v-if="clip.ai_settings && clip.ai_settings.batch_id" xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              {{ clip.name }}
            </div>
            

            
            <!-- Left & Right Resizers - transparent with subtle hover accent -->
            <div class="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize z-20 group/left flex items-center justify-start"
                 @mousedown.stop="startResizeClip($event, trackId, idx, 'left')">
              <div class="w-0.5 h-3/4 rounded-full bg-white/0 group-hover/left:bg-white/60 transition-all"></div>
            </div>
            <div class="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize z-20 group/right flex items-center justify-end"
                 @mousedown.stop="startResizeClip($event, trackId, idx, 'right')">
              <div class="w-0.5 h-3/4 rounded-full bg-white/0 group-hover/right:bg-white/60 transition-all"></div>
            </div>
          </div>
          
          <!-- Playhead line -->
          <div v-if="totalDuration > 0" class="absolute top-0 bottom-0 w-[1px] bg-red-500 z-40 pointer-events-none"
               :style="{ left: `${(currentTime / totalDuration) * 100}%` }">
          </div>
        </div>

              </div>
    </div>
    </div>
    
    
      
    
    <!-- Context Menu Modal (Volume) -->
    <div v-if="contextMenu.visible" 
         class="fixed bg-bg-surface border border-gray-200/30 rounded-md shadow-lg p-3 z-[200] w-48 pointer-events-auto"
         :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
         @mousedown.stop>
       <div class="text-[10px] text-text-secondary uppercase font-bold tracking-wider mb-2">Громкость</div>
       <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-secondary"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
          <input type="range" min="0" max="1" step="0.05" 
                 :value="contextMenu.clip?.volume !== undefined ? contextMenu.clip.volume : 1"
                 @input="handleContextMenuVolume"
                 @change="handleContextMenuVolumeCommit"
                 class="w-full accent-brand-orange h-1.5 bg-text-muted/30 rounded-full appearance-none outline-none cursor-pointer" />
          <span class="text-text-secondary text-[10px] w-8 text-right font-mono">{{ Math.round((contextMenu.clip?.volume !== undefined ? contextMenu.clip.volume : 1) * 100) }}%</span>
       </div>
       <hr class="border-gray-200 my-2" />
       <div class="text-[10px] text-text-secondary uppercase font-bold tracking-wider mb-2">Скорость</div>
       <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-secondary"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          <input type="range" min="0.5" max="2.0" step="0.05" 
                 :value="contextMenu.clip?.playbackRate || 1.0"
                 @input="handleContextMenuSpeed"
                 @change="handleContextMenuSpeedCommit"
                 class="w-full accent-brand-green h-1.5 bg-text-muted/30 rounded-full appearance-none outline-none cursor-pointer" />
          <span class="text-text-secondary text-[10px] w-8 text-right font-mono">{{ (contextMenu.clip?.playbackRate || 1.0).toFixed(2) }}x</span>
       </div>
       <hr class="border-gray-200 my-2" />
       <button v-if="contextMenu.clip?.type === 'ai_voice'" 
               @click="emit('edit-clip', {trackId: contextMenu.trackId, clip: contextMenu.clip, idx: contextMenu.idx}); contextMenu.visible = false"
               class="flex items-center justify-center gap-2 text-[10px] text-[#A78BFA] hover:text-[#C4B5FD] hover:bg-bg-surface p-1.5 rounded transition-colors uppercase font-bold tracking-wider w-full mb-1">
         <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
         Настроить ИИ
       </button>
       <button @click="deleteClip(contextMenu.trackId, contextMenu.idx); contextMenu.visible = false"
               class="flex items-center justify-center gap-2 text-[10px] text-red-400 hover:text-red-300 hover:bg-bg-surface p-1.5 rounded transition-colors uppercase font-bold tracking-wider w-full">
         <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
         Удалить клип
       </button>
    </div>
  </div>
</template>




<script setup>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import WaveformCanvas from './WaveformCanvas.vue'

const hoveredBatchId = ref(null)
import { getAudioDuration } from '../../composables/useAudioEngine'

const props = defineProps({
  audioTimeline: {
    type: Object,
    default: () => null
  },
  zoomLevel: {
    type: Number,
    default: 1
  },
  totalDuration: {
    type: Number,
    default: 0
  },
  snapPoints: {
    type: Array,
    default: () => []
  },
  currentTime: {
    type: Number,
    default: 0
  },
  isFullscreen: {
    type: Boolean,
    default: false
  },
  isEditorOpen: {
    type: Boolean,
    default: false
  },
  syncScrollLeft: {
    type: Number,
    default: 0
  },
  trackWidthPx: {
    type: Number,
    default: 0
  },
  recordingTrackId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update-audio-timeline', 'scroll-request', 'request-add-audio', 'seek', 'toggle-record', 'request-generate-voice', 'edit-clip'])

// Track refs
const trackScrollers = ref({}) // trackId -> scroll container DOM element
const trackInners = ref({})    // trackId -> inner track div DOM element

const localTimeline = ref({
  tracks: [
    { id: 'main', type: 'voiceover', clips: [] },
    { id: 'overlay', type: 'voiceover', clips: [] },
    { id: 'bgm', type: 'bgm', clips: [] },
    { id: 'sfx', type: 'sfx', clips: [] }
  ]
})

const visibleTrackIds = ref(['main'])

const addNextTrack = () => {
  const allTracks = ['main', 'overlay', 'bgm', 'sfx']
  for (const t of allTracks) {
    if (!visibleTrackIds.value.includes(t)) {
      visibleTrackIds.value.push(t)
      break
    }
  }
}

const removeTrack = (trackId) => {
  const idx = visibleTrackIds.value.indexOf(trackId)
  if (idx !== -1) {
    visibleTrackIds.value.splice(idx, 1)
    const t = localTimeline.value.tracks.find(x => x.id === trackId)
    if (t) {
      t.clips = []
      commitChange()
    }
  }
}

// ------------------------------------
// UNDO / REDO HISTORY
// ------------------------------------
const history = ref([])
const historyIndex = ref(-1)
const MAX_HISTORY = 30

const commitChange = () => {
  const snapshot = JSON.stringify(localTimeline.value)
  // Don't commit if it's identical to current state
  if (historyIndex.value >= 0 && history.value[historyIndex.value] === snapshot) return
  
  // Truncate redo history if we are in the middle of the stack
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  
  history.value.push(snapshot)
  if (history.value.length > MAX_HISTORY) {
    history.value.shift()
  } else {
    historyIndex.value++
  }
  
  emit('update-audio-timeline', JSON.parse(snapshot))
}

const undo = () => {
  if (historyIndex.value > 0) {
    historyIndex.value--
    localTimeline.value = JSON.parse(history.value[historyIndex.value])
    emit('update-audio-timeline', localTimeline.value)
  }
}

const redo = () => {
  if (historyIndex.value < history.value.length - 1) {
    historyIndex.value++
    localTimeline.value = JSON.parse(history.value[historyIndex.value])
    emit('update-audio-timeline', localTimeline.value)
  }
}

watch(() => props.audioTimeline, (newVal) => {
  if (newVal && newVal.tracks) {
    const stringified = JSON.stringify(newVal)
    
    // Ignore updates that match our current history step to prevent overwriting local state
    if (historyIndex.value >= 0 && history.value[historyIndex.value] === stringified) {
      return
    }
    
    localTimeline.value = JSON.parse(stringified)
    
    // Auto-show tracks that have clips
    localTimeline.value.tracks.forEach(t => {
      if (t.clips && t.clips.length > 0 && !visibleTrackIds.value.includes(t.id)) {
        visibleTrackIds.value.push(t.id)
      }
    })
    
    // Initialize history if empty
    if (history.value.length === 0) {
      history.value.push(stringified)
      historyIndex.value = 0
    }
  }
}, { immediate: true, deep: true })

// ==== CORE SYNC: when the global scroll changes, apply it to all audio track scrollers ====
let suppressScrollEvent = false
watch(() => props.syncScrollLeft, (newScrollLeft) => {
  suppressScrollEvent = true
  for (const el of Object.values(trackScrollers.value)) {
    if (el) {
      el.scrollLeft = newScrollLeft
    }
  }
  // Use rAF to reset flag after paint, not just Vue tick - prevents any drift
  requestAnimationFrame(() => { suppressScrollEvent = false })
}, { flush: 'sync' })

// When user scrolls an audio track, propagate upward to keep global in sync
const onTrackScroll = (e) => {
  if (suppressScrollEvent) return
  emit('scroll-request', { deltaX: e.target.scrollLeft - (props.syncScrollLeft || 0), deltaY: 0, _scrollLeft: e.target.scrollLeft })
}

const handleWheel = (e) => {
  if (e.shiftKey) {
    e.preventDefault()
    // DirectorDebugPanel already handles the deltaX fallback
    emit('scroll-request', e)
    return
  }
  if (e.altKey) return

  if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
    return
  }
  e.preventDefault()
  e.currentTarget.scrollLeft += e.deltaY
}

const getTrackClips = (trackId) => {
  if (Array.isArray(localTimeline.value.tracks)) {
    const t = localTimeline.value.tracks.find(x => x.id === trackId)
    return t ? (t.clips || []) : []
  }
  return localTimeline.value.tracks[trackId] || []
}

const getClipForMutation = (trackId, idx) => {
  const clips = getTrackClips(trackId)
  return { clips, clip: clips[idx] }
}

const getLeftPercent = (clip) => {
  if (props.totalDuration === 0) return 0
  return (clip.start_time / props.totalDuration) * 100
}

const getWidthPercent = (clip) => {
  if (props.totalDuration === 0) return 0
  const dur = clip.end_time - clip.start_time
  return (dur / props.totalDuration) * 100
}

const getClipColors = (trackId, clipType) => {
  if (clipType === 'ai_voice') {
    return 'bg-purple-100 border-purple-500 text-purple-700'
  }
  // All other non-AI sounds
  return 'bg-green-100 border-brand-green text-green-700'
}

// Drag logic
let isDragging = false
let dragType = null // 'move', 'resize-left', 'resize-right', 'seek'
let activeTrack = null
let activeIdx = -1
let startX = 0
let initialStart = 0
let initialEnd = 0
let initialDragState = []
let currentPixelsToTimeRatio = 10

const getActiveSnapPoints = (excludeClipId = null) => {
  const points = new Set(props.snapPoints || [])
  
  if (localTimeline.value && localTimeline.value.tracks) {
    localTimeline.value.tracks.forEach(t => {
      if (t.clips) {
        t.clips.forEach(c => {
          if (c.id !== excludeClipId) {
            points.add(c.start_time)
            points.add(c.end_time)
          }
        })
      }
    })
  }
  return Array.from(points).sort((a, b) => a - b)
}

const getSnappedTime = (time, snapPointsArr, innerWidth) => {
  if (!snapPointsArr.length || !innerWidth) return time
  const msPerPixel = props.totalDuration / innerWidth
  const snapPixels = Math.max(8, 25 / props.zoomLevel)
  const snapThresholdMs = snapPixels * msPerPixel
  
  for (const pt of snapPointsArr) {
    if (Math.abs(time - pt) < snapThresholdMs) {
      return pt
    }
  }
  return time
}

// === MOBILE: скраб по аудио-дорожке одним пальцем (без модалки редактора) ===
const touchSeekId = ref(null)

const doTouchSeek = (clientX, trackId) => {
  const inner = trackInners.value[trackId]
  if (!inner) return
  const rect = inner.getBoundingClientRect()
  let time = ((clientX - rect.left) / rect.width) * props.totalDuration
  time = getSnappedTime(time, getActiveSnapPoints(), rect.width)
  emit('seek', Math.max(0, Math.min(time, props.totalDuration)))
}

const onTouchSeekStart = (e, trackId) => {
  if (e.touches.length !== 1) return
  touchSeekId.value = trackId
  selectedClips.value = []
  doTouchSeek(e.touches[0].clientX, trackId)
}

const onTouchSeekMove = (e, trackId) => {
  if (touchSeekId.value === null || e.touches.length !== 1) return
  doTouchSeek(e.touches[0].clientX, trackId)
  e.preventDefault()
}

const onTouchSeekEnd = () => {
  touchSeekId.value = null
}

const startSeek = (e, trackId) => {
  if (!props.isEditorOpen) return
  const inner = trackInners.value[trackId]
  if (!inner) return
  const rect = inner.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  let time = (clickX / rect.width) * props.totalDuration
  
  // Snap on click
  const snapPointsArr = getActiveSnapPoints()
  time = getSnappedTime(time, snapPointsArr, rect.width)
  
  emit('seek', Math.max(0, time)) // can't seek to negative time

  isDragging = true
  dragType = 'seek'
  activeTrack = trackId
  document.body.classList.add('is-seeking')
}

const deleteClip = (trackId, idx) => {
  if (!props.isEditorOpen) return
  const { clips } = getClipForMutation(trackId, idx)
  clips.splice(idx, 1)
  commitChange()
}

const startDragClip = (e, trackId, idx) => {
  if (!props.isEditorOpen) return
  isDragging = true
  dragType = 'move'
  document.body.classList.add('is-seeking')
  activeTrack = trackId
  activeIdx = idx
  startX = e.clientX
  
  const inner = trackInners.value[trackId]
  if (inner) {
    currentPixelsToTimeRatio = props.totalDuration / inner.getBoundingClientRect().width
  }
  
  const { clip } = getClipForMutation(trackId, idx)
  initialStart = clip.start_time
  initialEnd = clip.end_time

  if (isClipSelected(trackId, clip.id)) {
    initialDragState = getSelectedClipsData().map(item => ({
      clipId: item.clip.id,
      trackId: item.trackId,
      start: item.clip.start_time,
      end: item.clip.end_time
    }))
  } else {
    initialDragState = [{
      clipId: clip.id,
      trackId,
      start: clip.start_time,
      end: clip.end_time
    }]
  }
}

const startResizeClip = (e, trackId, idx, edge) => {
  if (!props.isEditorOpen) return
  isDragging = true
  dragType = `resize-${edge}`
  document.body.classList.add('is-seeking')
  activeTrack = trackId
  activeIdx = idx
  startX = e.clientX
  
  const inner = trackInners.value[trackId]
  if (inner) {
    currentPixelsToTimeRatio = props.totalDuration / inner.getBoundingClientRect().width
  }
  
  const { clip } = getClipForMutation(trackId, idx)
  initialStart = clip.start_time
  initialEnd = clip.end_time
}

const onMouseMove = (e) => {
  if (!isDragging) return
  
  if (dragType === 'seek') {
    const inner = trackInners.value[activeTrack]
    if (!inner) return
    const rect = inner.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const time = (clickX / rect.width) * props.totalDuration
    emit('seek', Math.max(0, Math.min(time, props.totalDuration)))
    return
  }
  
  const deltaX = e.clientX - startX
  const timeDelta = deltaX * currentPixelsToTimeRatio

  const { clip } = getClipForMutation(activeTrack, activeIdx)
  const snapPointsArr = getActiveSnapPoints(clip.id)
  const innerWidth = trackInners.value[activeTrack]?.getBoundingClientRect().width || 0

  let maxLeftStart = -Infinity
  let minRightStart = Infinity
  const track = localTimeline.value.tracks.find(t => t.id === activeTrack)
  if (track && track.clips) {
    track.clips.forEach(c => {
      if (c.id === clip.id) return
      if (c.end_time <= initialStart + 1) {
        if (c.end_time > maxLeftStart) maxLeftStart = c.end_time
      }
      if (c.start_time >= initialEnd - 1) {
        if (c.start_time < minRightStart) minRightStart = c.start_time
      }
    })
  }

  if (dragType === 'move') {
    let newStart = initialStart + timeDelta
    let newEnd = initialEnd + timeDelta
    
    // Snapping for move
    const snappedStart = getSnappedTime(newStart, snapPointsArr, innerWidth)
    if (snappedStart !== newStart) {
      const diff = snappedStart - newStart
      newStart = snappedStart
      newEnd += diff
    } else {
      const snappedEnd = getSnappedTime(newEnd, snapPointsArr, innerWidth)
      if (snappedEnd !== newEnd) {
        const diff = snappedEnd - newEnd
        newEnd = snappedEnd
        newStart += diff
      }
    }
    
    const dur = newEnd - newStart
    if (newStart < maxLeftStart) {
      newStart = maxLeftStart
      newEnd = newStart + dur
    }
    if (newEnd > minRightStart) {
      newEnd = minRightStart
      newStart = newEnd - dur
    }
    
    const effectiveDelta = newStart - initialStart

    // Prevent any clip from going below time 0
    let minStart = Infinity
    for (const state of initialDragState) {
      if (state.start < minStart) minStart = state.start
    }
    let safeDelta = effectiveDelta
    if (minStart + safeDelta < 0) safeDelta = -minStart

    for (const state of initialDragState) {
      const t = localTimeline.value.tracks.find(x => x.id === state.trackId)
      if (t) {
        const c = t.clips.find(x => x.id === state.clipId)
        if (c) {
          const cDur = state.end - state.start
          c.start_time = state.start + safeDelta
          c.end_time = c.start_time + cDur
        }
      }
    }
  } else if (dragType === 'resize-left') {
    let newStart = initialStart + timeDelta
    newStart = getSnappedTime(newStart, snapPointsArr, innerWidth)
    
    if (newStart < maxLeftStart) newStart = maxLeftStart
    if (newStart > clip.end_time - 100) newStart = clip.end_time - 100 // min 100ms
    
    // We must adjust media_offset to keep audio in sync!
    const offsetDelta = newStart - initialStart
    let newMediaOffset = (clip.media_offset || 0) + offsetDelta
    
    // Prevent expanding left beyond the start of the audio file
    if (newMediaOffset < 0) {
      newStart -= newMediaOffset // shift back by negative amount
      newMediaOffset = 0
    }
    
    clip.media_offset = newMediaOffset
    clip.start_time = newStart
  } else if (dragType === 'resize-right') {
    let newEnd = initialEnd + timeDelta
    newEnd = getSnappedTime(newEnd, snapPointsArr, innerWidth)
    
    if (newEnd > minRightStart) newEnd = minRightStart
    if (newEnd < clip.start_time + 100) newEnd = clip.start_time + 100
    
    const maxDur = getAudioDuration(clip.src)
    if (maxDur !== null) {
      const maxEnd = clip.start_time + (maxDur - (clip.media_offset || 0))
      if (newEnd > maxEnd) newEnd = maxEnd
    }
    
    clip.end_time = newEnd
  }
}

const onMouseUp = () => {
  if (isDragging) {
    const wasSeek = dragType === 'seek'
    isDragging = false
    document.body.classList.remove('is-seeking')
    if (!wasSeek) {
      commitChange()
    }
  }
}

const splitClip = (trackId, idx) => {
  const { clips, clip } = getClipForMutation(trackId, idx)
  if (props.currentTime <= clip.start_time || props.currentTime >= clip.end_time) return
  
  // Split at currentTime
  const newClip1 = { ...clip, id: clip.id + '_a', end_time: props.currentTime }
  const newClip2 = { 
    ...clip, 
    id: clip.id + '_b', 
    start_time: props.currentTime,
    media_offset: (clip.media_offset || 0) + (props.currentTime - clip.start_time)
  }
  
  clips.splice(idx, 1, newClip1, newClip2)
  commitChange()
  
  if (isClipSelected(trackId, clip.id)) {
    // selectClip(e, trackId, clipId) — первым аргументом событие (null = программное выделение)
    selectClip(null, trackId, newClip2.id)
  }
}

// ------------------------------------
// HOTKEYS & SELECTION
// ------------------------------------
const selectedClips = ref([])
let lastClickedClip = null


const isClipSelected = (trackId, clipId) => {
  return selectedClips.value.some(sel => sel.trackId === trackId && sel.clipId === clipId)
}

const getSelectedClipsData = () => {
  const result = []
  for (const sel of selectedClips.value) {
    const t = Array.isArray(localTimeline.value.tracks) ? localTimeline.value.tracks.find(x => x.id === sel.trackId) : localTimeline.value.tracks[sel.trackId]
    if (t) {
      const clip = t.clips.find(c => c.id === sel.clipId)
      if (clip) result.push({ trackId: sel.trackId, clip, idx: t.clips.indexOf(clip) })
    }
  }
  return result
}


const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  clip: null,
  trackId: null,
  idx: -1
})

const showContextMenu = (e, trackId, clipId, idx) => {
  e.preventDefault()
  selectClip(e, trackId, clipId)
  
  const { clip } = getClipForMutation(trackId, idx)
  if (!clip) return
  
  contextMenu.value = {
    visible: true,
    x: Math.min(e.clientX, window.innerWidth - 200),
    y: Math.min(e.clientY, window.innerHeight - 180),
    clip,
    trackId,
    idx
  }
}

const handleContextMenuVolume = (e) => {
  if (!contextMenu.value.clip) return
  const vol = parseFloat(e.target.value)
  
  if (selectedClips.value.length > 0) {
    for (const item of getSelectedClipsData()) {
      item.clip.volume = vol
    }
  }
  contextMenu.value.clip.volume = vol
}

const handleContextMenuVolumeCommit = (e) => {
  commitChange()
}

const handleContextMenuSpeed = (e) => {
  if (!contextMenu.value.clip) return
  const spd = parseFloat(e.target.value)
  
  if (selectedClips.value.length > 0) {
    for (const item of getSelectedClipsData()) {
      item.clip.playbackRate = spd
    }
  }
  contextMenu.value.clip.playbackRate = spd
}

const handleContextMenuSpeedCommit = (e) => {
  if (!contextMenu.value.clip) return
  const spd = parseFloat(e.target.value)
  
  if (selectedClips.value.length > 0) {
    const tracksMap = {}
    for (const item of getSelectedClipsData()) {
      if (!tracksMap[item.trackId]) tracksMap[item.trackId] = []
      tracksMap[item.trackId].push(item.clip)
    }

    for (const trackId in tracksMap) {
      const clips = tracksMap[trackId]
      clips.sort((a, b) => a.start_time - b.start_time)
      const oldEndTimes = clips.map(c => c.end_time)

      for (let i = 0; i < clips.length; i++) {
        const clip = clips[i]
        const originalDur = clip.originalDuration || (clip.end_time - clip.start_time)
        if (!clip.originalDuration) clip.originalDuration = originalDur
        
        if (i > 0) {
          const prevClip = clips[i - 1]
          const prevOldEndTime = oldEndTimes[i - 1]
          const gap = clip.start_time - prevOldEndTime
          clip.start_time = prevClip.end_time + gap
        }
        
        clip.end_time = clip.start_time + (originalDur / spd)
      }
    }
  } else {
    const clip = contextMenu.value.clip
    const originalDur = clip.originalDuration || (clip.end_time - clip.start_time)
    if (!clip.originalDuration) clip.originalDuration = originalDur
    clip.end_time = clip.start_time + (originalDur / spd)
  }
  commitChange()
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

window.addEventListener('mousedown', closeContextMenu)
onUnmounted(() => {
  window.removeEventListener('mousedown', closeContextMenu)
})





const selectClip = (e, trackId, clipId) => {
  const existingIdx = selectedClips.value.findIndex(sel => sel.trackId === trackId && sel.clipId === clipId)
  
  if (e && e.shiftKey && lastClickedClip) {
    // Range selection
    const allClips = []
    localTimeline.value.tracks.forEach(t => {
      t.clips.forEach(c => allClips.push({ trackId: t.id, clip: c }))
    })
    allClips.sort((a, b) => a.clip.start_time - b.clip.start_time)
    
    const startIdx = allClips.findIndex(item => item.trackId === lastClickedClip.trackId && item.clip.id === lastClickedClip.clipId)
    const endIdx = allClips.findIndex(item => item.trackId === trackId && item.clip.id === clipId)
    
    if (startIdx !== -1 && endIdx !== -1) {
      const minIdx = Math.min(startIdx, endIdx)
      const maxIdx = Math.max(startIdx, endIdx)
      
      const newSelection = []
      for (let i = minIdx; i <= maxIdx; i++) {
        newSelection.push({ trackId: allClips[i].trackId, clipId: allClips[i].clip.id })
      }
      selectedClips.value = newSelection
    } else {
      // Fallback
      selectedClips.value = [{ trackId, clipId }]
      lastClickedClip = { trackId, clipId }
    }
  } else if (e && (e.ctrlKey || e.metaKey)) {
    // Toggle single selection
    if (existingIdx !== -1) {
      selectedClips.value.splice(existingIdx, 1)
    } else {
      selectedClips.value.push({ trackId, clipId })
    }
    lastClickedClip = { trackId, clipId }
  } else {
    // Single selection
    if (existingIdx === -1 || (e && e.type === 'mousedown' && selectedClips.value.length === 1)) {
      selectedClips.value = [{ trackId, clipId }]
    }
    lastClickedClip = { trackId, clipId }
  }
}

const deleteSelectedClip = () => {
  if (selectedClips.value.length === 0) return
  for (const sel of selectedClips.value) {
    const t = localTimeline.value.tracks.find(x => x.id === sel.trackId)
    if (t) {
      const idx = t.clips.findIndex(c => c.id === sel.clipId)
      if (idx !== -1) deleteClip(sel.trackId, idx)
    }
  }
  selectedClips.value = []
}

const splitSelectedClip = () => {
  if (selectedClips.value.length === 0) return
  const selectedData = getSelectedClipsData()
  for (const item of selectedData) {
    const t = localTimeline.value.tracks.find(x => x.id === item.trackId)
    if (t) {
      const idx = t.clips.findIndex(c => c.id === item.clip.id)
      if (idx !== -1) {
        splitClip(item.trackId, idx)
      }
    }
  }
}

const duplicateSelectedClip = () => {
  if (!selectedClip.value) return
  const { trackId, clipId } = selectedClip.value
  const t = localTimeline.value.tracks.find(x => x.id === trackId)
  if (!t) return
  const clip = t.clips.find(c => c.id === clipId)
  if (!clip) return
  
  const dur = clip.end_time - clip.start_time
  const newClip = JSON.parse(JSON.stringify(clip))
  newClip.id = Math.random().toString(36).substr(2, 9)
  newClip.start_time = clip.end_time
  newClip.end_time = newClip.start_time + dur
  
  t.clips.push(newClip)
  commitChange()
  selectClip(trackId, newClip.id)
}

const handleKeyDown = (e) => {
  if (!props.isEditorOpen) return
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

  if (e.code === 'Delete' || e.code === 'Backspace') {
    if (selectedClips.value.length > 0) deleteSelectedClip()
  } else if (e.code === 'KeyZ' && (e.ctrlKey || e.metaKey)) {
    if (e.shiftKey) {
      redo()
    } else {
      undo()
    }
  } else if (e.code === 'KeyY' && (e.ctrlKey || e.metaKey)) {
    redo()
  } else if (e.code === 'KeyS' || e.code === 'KeyC' || e.code === 'KeyX') {
    if (selectedClips.value.length > 0) splitSelectedClip()
  } else if (e.code === 'KeyD') {
    if (selectedClips.value.length > 0) {
      e.preventDefault()
      duplicateSelectedClip()
    }
  }
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('keydown', handleKeyDown)
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
</style>
