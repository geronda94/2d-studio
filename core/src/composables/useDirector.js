import { ref, reactive } from 'vue'
import { useAudioEngine, unlockAudioContext } from './useAudioEngine'

const isPlaying = ref(false)
const currentTime = ref(0)
const timelineEvents = ref([])
let lastEventIndex = -1
let animationFrameId = null
let startTime = 0
let pausedTime = 0

const globalBus = reactive({
  listeners: {}
})

// Create Audio Engine singleton
const audioEngine = useAudioEngine()

const isAudioMuted = ref(false)

const loadAudioTimeline = (timelineConfig, virtualClips = []) => {
  audioEngine.loadTimeline(timelineConfig, virtualClips)
}

const toggleAudioMute = () => {
  isAudioMuted.value = !isAudioMuted.value
  audioEngine.setMuted(isAudioMuted.value)
}
const setAudioMute = (muted) => {
  isAudioMuted.value = muted
  audioEngine.setMuted(muted)
}

export function useDirector(configOrNone, callbackOrNone) {
  // ВРЕМЕННЫЙ ФИКС: Для старых компонентов эмулируем локальный таймлайн
  if (configOrNone !== undefined || callbackOrNone !== undefined) {
    let timeoutIds = []
    return {
      start: () => {
        if (Array.isArray(configOrNone)) {
          configOrNone.forEach(event => {
            const id = setTimeout(() => {
              if (callbackOrNone) callbackOrNone(event)
            }, event.time || 0)
            timeoutIds.push(id)
          })
        }
      },
      stop: () => {
        timeoutIds.forEach(clearTimeout)
        timeoutIds = []
      },
      reset: () => {
        timeoutIds.forEach(clearTimeout)
        timeoutIds = []
      },
      isRunning: ref(false)
    }
  }

  const setTimeline = (events) => {
    timelineEvents.value = [...events].sort((a, b) => a.time - b.time)
    console.log('Director loaded timeline with', timelineEvents.value.length, 'events')
  }

  const playbackRate = ref(1)
  const playUntilTime = ref(null)
  
  let lastFrameTime = 0
  const isRenderMode = typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('render') === 'true'

  const play = (untilTime = null) => {
    // Unlock audio context on first user gesture
    unlockAudioContext()

    const targetUntilTime = untilTime !== null ? Number(untilTime) : null
    if (isPlaying.value && playUntilTime.value === targetUntilTime) return
    isPlaying.value = true
    playUntilTime.value = targetUntilTime
    
    if (animationFrameId) {
      if (isRenderMode) clearInterval(animationFrameId)
      else cancelAnimationFrame(animationFrameId)
    }

    // Recalculate lastEventIndex based on current time
    const nextIndex = timelineEvents.value.findIndex(e => e.time > currentTime.value)
    lastEventIndex = nextIndex === -1 ? timelineEvents.value.length - 1 : nextIndex - 1

    if (isRenderMode) {
      // Render mode: use setInterval with wall-clock (performance.now) for reliable timing
      const wallStart = performance.now() - currentTime.value
      animationFrameId = setInterval(() => {
        if (!isPlaying.value) return
        const now = performance.now()
        let newTime = (now - wallStart) * playbackRate.value
        const pUt = playUntilTime.value !== null ? Number(playUntilTime.value) : null
        if (pUt !== null && newTime >= pUt) newTime = pUt
        currentTime.value = newTime

        let nextIndex = lastEventIndex + 1
        while (nextIndex < timelineEvents.value.length && currentTime.value >= timelineEvents.value[nextIndex].time) {
          triggerEvent(timelineEvents.value[nextIndex])
          lastEventIndex = nextIndex
          nextIndex++
        }

        audioEngine.sync(currentTime.value, true, playbackRate.value)

        if (pUt !== null && newTime >= pUt) {
          pause()
          playUntilTime.value = null
        }
      }, 16)
      return
    }

    let firstTick = true
    const tick = (now) => {
      if (!isPlaying.value) return
      
      if (firstTick) {
        lastFrameTime = now
        firstTick = false
      }
      
      const delta = (now - lastFrameTime) * playbackRate.value
      lastFrameTime = now
      
      let newTime = currentTime.value + delta
      const pUt = playUntilTime.value !== null ? Number(playUntilTime.value) : null
      if (pUt !== null && newTime >= pUt) {
         newTime = pUt
      }
      
      currentTime.value = newTime

      // Process all events that should have fired by now
      let nextIndex = lastEventIndex + 1
      while (nextIndex < timelineEvents.value.length && currentTime.value >= timelineEvents.value[nextIndex].time) {
        triggerEvent(timelineEvents.value[nextIndex])
        lastEventIndex = nextIndex
        nextIndex++
      }
      
      // Sync audio engine with the new time
      audioEngine.sync(currentTime.value, isPlaying.value, playbackRate.value)

      if (pUt !== null && newTime >= pUt) {
         pause()
         playUntilTime.value = null
         return
      }

      animationFrameId = requestAnimationFrame(tick)
    }
    animationFrameId = requestAnimationFrame(tick)
  }

  const pause = () => {
    isPlaying.value = false
    pausedTime = currentTime.value
    if (animationFrameId) {
      if (isRenderMode) clearInterval(animationFrameId)
      else cancelAnimationFrame(animationFrameId)
    }
    
    // Pause Audio
    audioEngine.sync(currentTime.value, false, playbackRate.value)
  }

  const stop = () => {
    pause()
    currentTime.value = 0
    pausedTime = 0
    lastEventIndex = -1
    
    audioEngine.stopAll()
  }
  
  const seek = (timeMs) => {
    const targetTime = Number(timeMs) || 0
    currentTime.value = targetTime
    pausedTime = targetTime
    if (isPlaying.value) {
      startTime = performance.now() - targetTime
      // Also need to recalculate lastEventIndex
      const nextIndex = timelineEvents.value.findIndex(e => Number(e.time) > currentTime.value)
      lastEventIndex = nextIndex === -1 ? timelineEvents.value.length - 1 : nextIndex - 1
    }
    
    // Force sync if paused, so playhead moves correctly
    if (!isPlaying.value) {
      audioEngine.sync(targetTime, false, playbackRate.value)
    }
  }

  const triggerEvent = (event) => {
    if (globalBus.listeners[event.type]) {
      globalBus.listeners[event.type].forEach(cb => cb(event.payload))
    }
  }

  const onEvent = (type, callback) => {
    if (!globalBus.listeners[type]) {
      globalBus.listeners[type] = []
    }
    globalBus.listeners[type].push(callback)
    
    // Return unsubscribe function
    return () => {
      globalBus.listeners[type] = globalBus.listeners[type].filter(cb => cb !== callback)
    }
  }

  const clearListeners = (type = null) => {
    if (type) {
      globalBus.listeners[type] = []
    } else {
      globalBus.listeners = {}
    }
  }

  const instance = {
    isPlaying,
    currentTime,
    playUntilTime,
    playbackRate,
    timelineEvents,
    setTimeline,
    play,
    pause,
    stop,
    seek,
    onEvent,
    clearListeners,
    loadAudioTimeline,
    toggleAudioMute,
    setAudioMute,
    isAudioLoaded: ref(true),
    isAudioMuted
  }

  // Expose for headless rendering
  if (typeof window !== 'undefined') {
    window.useDirectorInstance = instance
  }

  return instance
}
