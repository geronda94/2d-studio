import { ref, watch } from 'vue'

// Кэш HTMLAudioElement. Ключ — SRC, а не clipId: clip.id генерируются как
// block_0/block_1 и ПОВТОРЯЮТСЯ между презентациями. Если ключевать по clipId,
// для новой презентации возвращался элемент со СТАРЫМ src — и играла озвучка
// предыдущей презентации (баг «перешёл на другую — звучит та же озвучка»).
const audioInstances = new Map() // src -> HTMLAudioElement
const durationCache = new Map() // src -> duration ms

// Retrieve or create an Audio instance for a specific clip
export function getAudioInstanceForClip(clipId, src) {
  const key = src || `clip:${clipId}`
  if (!audioInstances.has(key)) {
    // Относительный URL (/media, /uploads) резолвится через vite-proxy к бэкенду —
    // работает и в браузере, и в headless-рендере (внутри docker-сети).
    const audio = new Audio(src)
    audio.preload = 'auto'
    
    // Preload duration
    audio.addEventListener('loadedmetadata', () => {
      durationCache.set(src, audio.duration * 1000)
    }, { once: true })
    
    // Handle error (e.g. file not found)
    audio.addEventListener('error', () => {
      console.warn(`[AudioEngine] Failed to load audio for clip ${clipId}: ${src}`)
      window.dispatchEvent(new CustomEvent('audio-clip-error', { detail: { clipId, src } }))
    }, { once: true })
    
    audioInstances.set(key, audio)
  }
  return audioInstances.get(key)
}

export function getAudioDuration(src) {
  return durationCache.get(src) || null
}

let isUnlocked = false
export function unlockAudioContext() {
  if (isUnlocked) return
  console.log('[AudioEngine] Unlocking audio context for iOS/Safari')
  
  // Removed audioInstances iteration because it causes immediate pauses 
  // that conflict with the actual playback loop in sync().
  // The dummy audio below is sufficient to unlock the context on iOS.
  
  // Also create a dummy audio element to ensure the context is unlocked
  // even if no instances were loaded yet
  const dummy = new Audio()
  dummy.src = 'data:audio/mp3;base64,//OkwAAAAAAAAAAAAAAAAAAAAAAAwQwKSAAAAP/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////'
  const dp = dummy.play()
  if (dp !== undefined) {
    dp.catch(() => {}).then(() => { dummy.pause() })
  }
  
  isUnlocked = true
}

// Ранний анлок: первый же пользователя (тап/клик/клавиша) снимает autoplay-политику
// браузера, из-за которой play() падал с NotAllowedError при старте без жеста
// (озвучка/BGM). Слушатели одноразовые и в capture-фазе.
if (typeof window !== 'undefined' && !window.__audioUnlockArmed) {
  window.__audioUnlockArmed = true
  const onFirstGesture = () => {
    unlockAudioContext()
    window.removeEventListener('pointerdown', onFirstGesture, true)
    window.removeEventListener('keydown', onFirstGesture, true)
    window.removeEventListener('touchstart', onFirstGesture, true)
  }
  window.addEventListener('pointerdown', onFirstGesture, true)
  window.addEventListener('keydown', onFirstGesture, true)
  window.addEventListener('touchstart', onFirstGesture, true)
}

// Active playing clips
let activeClips = new Map() // clipId -> { audio, config }

export function useAudioEngine() {
  const currentTimeline = ref({ tracks: [] })
  let engineIsPlaying = false
  let engineCurrentTime = 0
  let currentPlaybackRate = 1
  let engineIsMuted = false

  const setMuted = (muted) => {
    engineIsMuted = muted
    activeClips.forEach((state) => {
      state.audio.muted = engineIsMuted || state.config.muted || false
    })
  }

  let lastEngineTime = -1

  const loadTimeline = (timelineConfig, virtualClips = []) => {
    // Смена презентации/таймлайна: глушим всё, что звучало по прошлому таймлайну,
    // иначе старые клипы (с теми же clip.id) продолжают играть в новой презентации.
    stopAll()
    lastEngineTime = -1
    let clonedConfig = { tracks: [] }
    if (timelineConfig && timelineConfig.tracks) {
      clonedConfig = JSON.parse(JSON.stringify(timelineConfig))
    }
    
    if (virtualClips && virtualClips.length > 0) {
      let sfxTrack = clonedConfig.tracks.find(t => t.id === 'sfx')
      if (!sfxTrack) {
        sfxTrack = { id: 'sfx', type: 'sfx', clips: [] }
        clonedConfig.tracks.push(sfxTrack)
      }
      sfxTrack.clips.push(...virtualClips)
    }
    
    currentTimeline.value = clonedConfig
    
    // Pre-instantiate audio objects
    clonedConfig.tracks.forEach(track => {
      (track.clips || []).forEach(clip => {
        if (clip.src) {
          getAudioInstanceForClip(clip.id, clip.src)
        }
      })
    })
  }

  const sync = (timeMs, isPlaying, playbackRate = 1) => {
    const isJump = lastEngineTime !== -1 && Math.abs(timeMs - lastEngineTime) > 200
    lastEngineTime = timeMs
    
    engineIsPlaying = isPlaying
    engineCurrentTime = timeMs
    currentPlaybackRate = playbackRate
    
    if (!isPlaying) {
      // Pause all active
      activeClips.forEach((state) => {
        state.audio.pause()
      })
      activeClips.clear()
      return
    }

    // When playing, determine which clips should be active
    const clipsThatShouldPlay = new Set()

    currentTimeline.value.tracks.forEach(track => {
      (track.clips || []).forEach(clip => {
        if (clip.muted) return

        const start = clip.start_time
        const end = clip.end_time || start + 9999999 // If no end, play indefinitely
        
        if (timeMs >= start && timeMs < end) {
          clipsThatShouldPlay.add(clip.id)
          
          if (!activeClips.has(clip.id)) {
            console.log(`[AudioEngine] Starting clip: ${clip.name || clip.id} (src: ${clip.src})`)
            // Needs to start playing
            const audio = getAudioInstanceForClip(clip.id, clip.src)
            // Calculate where we should be in the audio file
            // media_offset is the starting offset inside the audio file itself (in ms)
            const offsetMs = clip.media_offset || 0
            const clipRate = clip.playbackRate || 1.0
            const relativeTimeMs = (timeMs - start) * clipRate
            const seekPos = (offsetMs + relativeTimeMs) / 1000
            
            // Avoid throwing errors if seek is slightly off
            try {
              if (audio.readyState >= 1) { // HAVE_METADATA
                if (Math.abs(audio.currentTime - seekPos) > 0.1) {
                  audio.currentTime = seekPos
                }
              } else {
                // Not loaded yet. Set up a one-time listener to seek once metadata loads.
                const onLoaded = () => {
                  if (!activeClips.has(clip.id)) return // Already stopped
                  if (Math.abs(audio.currentTime - seekPos) > 0.1) {
                    audio.currentTime = seekPos
                  }
                }
                audio.addEventListener('loadedmetadata', onLoaded, { once: true })
              }
              
              audio.volume = clip.volume !== undefined ? clip.volume : 1.0
              audio.playbackRate = playbackRate * (clip.playbackRate || 1.0)
              audio.muted = engineIsMuted || clip.muted || false
              
              const playPromise = audio.play()
              if (playPromise !== undefined) {
                playPromise.catch(err => {
                  // NotAllowedError — autoplay-политика до первого жеста; снимется
                  // сам при взаимодействии, это не ошибка (не засоряем консоль).
                  if (err && err.name === 'NotAllowedError') return
                  console.warn(`Audio play failed for clip ${clip.id} (src: ${clip.src}):`, err)
                })
              }
              
              activeClips.set(clip.id, { audio, config: clip })
            } catch (err) {
              console.warn(`Audio seek/play failed for clip ${clip.id} (src: ${clip.src}):`, err)
            }
          } else {
            // It's already playing, just update volume/rate if needed
            const state = activeClips.get(clip.id)
            
            // Check if user scrubbed the timeline (a jump occurred)
            if (isJump) {
              const offsetMs = clip.media_offset || 0
              const clipRate = clip.playbackRate || 1.0
              const relativeTimeMs = (timeMs - start) * clipRate
              const expectedSeekPos = (offsetMs + relativeTimeMs) / 1000
              
              if (state.audio.readyState >= 1) {
                state.audio.currentTime = expectedSeekPos
              }
            }

            if (state.audio.paused && isPlaying && !state.audio.ended) {
               // Soft retry in case it was rejected previously (e.g. AbortError on fast seek)
               const playPromise = state.audio.play()
               if (playPromise !== undefined) {
                 playPromise.catch(() => {})
               }
            }
            if (state.audio.playbackRate !== playbackRate) {
              state.audio.playbackRate = playbackRate * (clip.playbackRate || 1.0)
            }
            const targetVolume = clip.volume !== undefined ? clip.volume : 1.0
            if (state.audio.volume !== targetVolume) {
              state.audio.volume = targetVolume
            }
            state.audio.muted = engineIsMuted || clip.muted || false
          }
        }
      })
    })

    // Stop clips that are no longer in the time window
    activeClips.forEach((state, clipId) => {
      if (!clipsThatShouldPlay.has(clipId)) {
        state.audio.pause()
        activeClips.delete(clipId)
      }
    })
  }

  const stopAll = () => {
    activeClips.forEach((state) => state.audio.pause())
    activeClips.clear()
  }

  return {
    loadTimeline,
    sync,
    stopAll,
    setMuted
  }
}
