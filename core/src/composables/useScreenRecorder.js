import { ref } from 'vue'

const BITRATE_MAP = {
  draft: 12_000_000,
  standard: 25_000_000,
  premium: 60_000_000,
}

export function useScreenRecorder() {
  const isRecording = ref(false)
  let mediaRecorder = null
  let recordedChunks = []
  let stream = null
  let autoStopTimer = null
  let recordingStartTime = 0
  let savedContainerStyles = null
  let captureTarget = null

  const ensureCaptureOverlay = () => {
    if (typeof document === 'undefined') return

    let overlay = document.getElementById('capture-overlay-blocker')
    if (!overlay) {
      overlay = document.createElement('div')
      overlay.id = 'capture-overlay-blocker'
      overlay.setAttribute('aria-hidden', 'true')
      overlay.style.position = 'fixed'
      overlay.style.inset = '0'
      overlay.style.zIndex = '2147483647'
      overlay.style.cursor = 'none'
      overlay.style.pointerEvents = 'auto'
      overlay.style.background = 'transparent'
      document.body.appendChild(overlay)
    }

    document.body.style.cursor = 'none'
    document.body.style.userSelect = 'none'
    document.body.style.pointerEvents = 'auto'
  }

  const removeCaptureOverlay = () => {
    if (typeof document === 'undefined') return

    const overlay = document.getElementById('capture-overlay-blocker')
    if (overlay) overlay.remove()

    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.body.style.pointerEvents = ''
  }

  const stopAllTracks = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      stream = null
    }
  }

  const clearAutoStop = () => {
    if (autoStopTimer) {
      clearTimeout(autoStopTimer)
      autoStopTimer = null
    }
  }

  const resolveEndTime = (endTimeMs = null) => {
    const explicit = Number(endTimeMs)
    if (Number.isFinite(explicit) && explicit > 0) {
      return explicit
    }

    if (typeof window === 'undefined' || !window.useDirectorInstance) {
      return null
    }

    const timeline = window.useDirectorInstance.timelineEvents || []
    if (!timeline.length) return null

    const lastTime = timeline.reduce((max, event) => Math.max(max, Number(event.time) || 0), 0)
    return lastTime > 0 ? lastTime + 1800 : null
  }

  const PRE_ROLL_MS = 800

  const startPlaybackAfterPreroll = (opts) => {
    const director = typeof window !== 'undefined' ? window.useDirectorInstance : null
    if (director) {
      director.pause()
      director.seek(0)
    }
    return new Promise((resolve) => {
      setTimeout(() => {
        if (isRecording.value) triggerPlayback(opts)
        resolve()
      }, PRE_ROLL_MS)
    })
  }

  const loadFixWebmDuration = () => {
    return new Promise((resolve) => {
      if (window.ysFixWebmDuration) return resolve(window.ysFixWebmDuration)
      const script = document.createElement('script')
      script.src = '/vendor-fix-webm-duration.js'
      script.onload = () => resolve(window.ysFixWebmDuration)
      script.onerror = () => resolve(null)
      document.head.appendChild(script)
    })
  }

  const clearSafeZone = () => {
    if (typeof window === 'undefined') return
    if (window.__safeZone) {
      window.__safeZone = null
      window.dispatchEvent(
        new CustomEvent('presentation:safezone', { detail: null }),
      )
    }
  }

  const setCaptureLock = (on) => {
    if (typeof window !== 'undefined') window.__presentationCapturing = !!on
    if (typeof document !== 'undefined') {
      if (on) document.body.dataset.capturing = '1'
      else delete document.body.dataset.capturing
    }
  }

  const triggerPlayback = ({ autoPlay = true, endTimeMs = null } = {}) => {
    if (!autoPlay || typeof window === 'undefined') return
    const director = window.useDirectorInstance
    if (!director) return

    const safeEndTime = resolveEndTime(endTimeMs)

    const startPlayback = () => {
      window.dispatchEvent(new CustomEvent('presentation:reset-timeline'))
      director.seek(0)

      if (safeEndTime !== null) {
        clearAutoStop()
        autoStopTimer = setTimeout(() => {
          if (isRecording.value) {
            stopRecording()
          }
        }, Math.max(1000, safeEndTime + 300))
        director.play(safeEndTime)
        return
      }

      director.play()
    }

    if (document.readyState === 'complete') {
      requestAnimationFrame(startPlayback)
      return
    }

    window.addEventListener('load', startPlayback, { once: true })
  }

  const restoreContainer = () => {
    if (captureTarget && savedContainerStyles) {
      Object.assign(captureTarget.style, savedContainerStyles)
      captureTarget = null
      savedContainerStyles = null
    }
  }

  const startRecording = async (targetElement = null, options = {}) => {
    try {
      const {
        width = 1920,
        height = 1280,
        fps = 60,
        quality = 'premium',
        autoPlay = true,
        endTimeMs = null,
        title = '',
        format = '',
      } = options

      ensureCaptureOverlay()
      setCaptureLock(true)

      // Safe-zone для шортс (портрет): SlidePresentation ужмёт внутренний
      // слой со слайдами (.slides-safebox), фон останется на весь кадр.
      // Применяется только к захвату, не к просмотру.
      // 0.85 — отлаженное значение safe-zone (контент чуть ужимается, чтобы
      // нижнее/боковое UI YouTube/TikTok не перекрывало важное).
      // (кнопки, рейл, подписи) не перекрывало важное.
      if (typeof window !== 'undefined') {
        const isPortraitSafe = format === 'portrait' || format === 'mobile'
        const safeScale = Number(import.meta?.env?.VITE_RENDER_SAFE_SCALE) || 0.85
        window.__safeZone = isPortraitSafe
          ? { scale: safeScale, shiftFrac: -0.02 }
          : null
        window.dispatchEvent(
          new CustomEvent('presentation:safezone', { detail: window.__safeZone }),
        )
      }

      const earlyDirector =
        typeof window !== 'undefined' ? window.useDirectorInstance : null
      if (earlyDirector) {
        earlyDirector.pause()
        earlyDirector.seek(0)
      }
      window.dispatchEvent(new CustomEvent('presentation:reset-timeline'))

      const directorPromise = new Promise((resolve, reject) => {
        const startedAt = Date.now()
        const check = () => {
          if (typeof window !== 'undefined' && window.useDirectorInstance) {
            resolve(window.useDirectorInstance)
            return
          }
          if (Date.now() - startedAt > 5000) {
            reject(new Error('Director is not ready for capture'))
            return
          }
          setTimeout(check, 100)
        }
        check()
      })

      await directorPromise

      captureTarget = targetElement || document.querySelector('.slides-container')

      // Один вызов getDisplayMedia — и аудио, и видео.
      // captureStream() доступен не везде, поэтому getDisplayMedia — основной путь.
      const displayMediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          frameRate: Number(fps) || 60,
          width: { ideal: Math.round(width) },
          height: { ideal: Math.round(height) },
          aspectRatio: width / Math.max(height, 1),
          displaySurface: 'browser',
        },
        preferCurrentTab: true,
        audio: true,
      })

      const displayVideoTracks = displayMediaStream.getVideoTracks()
      const displayAudioTracks = displayMediaStream.getAudioTracks()

      // Если доступен captureStream() — используем его видео (高质量 элемента),
      // а аудио берём из getDisplayMedia (табовое аудио).
      let elementVideoTrack = null
      if (captureTarget && typeof captureTarget.captureStream === 'function') {
        // После получения доступа — переключаем контейнер на разрешение захвата.
        // captureStream() захватывает в layout-размере (не визуальном).
        savedContainerStyles = {
          width: captureTarget.style.width,
          height: captureTarget.style.height,
          transform: captureTarget.style.transform,
          transition: captureTarget.style.transition,
        }
        captureTarget.style.width = `${Math.round(width)}px`
        captureTarget.style.height = `${Math.round(height)}px`
        // Safe-zone живёт на внутреннем .slides-safebox, трансформ контейнера
        // перетираем как раньше — конфликта нет.
        captureTarget.style.transform = 'translate(0px, 0px) scale(1)'
        captureTarget.style.transition = 'none'
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
        await new Promise(r => setTimeout(r, 150))

        try {
          const elementStream = captureTarget.captureStream(Math.max(30, Number(fps) || 60))
          elementVideoTrack = elementStream.getVideoTracks()[0] || null
        } catch (e) {
          console.warn('captureStream() failed, using getDisplayMedia video:', e)
        }
      }

      const videoTrack = elementVideoTrack || displayVideoTracks[0]
      stream = new MediaStream([
        ...(videoTrack ? [videoTrack] : []),
        ...displayAudioTracks,
      ])

      // Останавливаем лишний видео-трек от getDisplayMedia, если используем element
      if (elementVideoTrack) {
        displayVideoTracks.forEach(t => { if (t !== videoTrack) t.stop() })
      }

      if (captureTarget && window.CropTarget && !elementVideoTrack) {
        try {
          const cropTarget = await CropTarget.fromElement(captureTarget)
          const videoTrack = stream.getVideoTracks()[0]
          if (videoTrack?.cropTo) {
            await videoTrack.cropTo(cropTarget)
          }
        } catch (cropErr) {
          console.warn('Failed to apply CropTarget, falling back to full tab capture:', cropErr)
        }
      }

      // Ждём шрифты, layout, Shiki
      try {
        await Promise.race([
          (document.fonts ? document.fonts.ready : Promise.resolve()),
          new Promise((r) => setTimeout(r, 2000)),
        ])
      } catch {
        /* ignore */
      }
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
      await new Promise((r) => setTimeout(r, 300))
      const codeReadyDeadline = Date.now() + 8000
      while (
        typeof document !== 'undefined' &&
        document.querySelector('[data-code-pending]') &&
        Date.now() < codeReadyDeadline
      ) {
        await new Promise((r) => setTimeout(r, 150))
      }

      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9'
        : 'video/webm'

      mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        videoBitsPerSecond: BITRATE_MAP[quality] || BITRATE_MAP.premium,
      })
      recordedChunks = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunks.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        restoreContainer()
        clearAutoStop()
        setCaptureLock(false)
        clearSafeZone()
        removeCaptureOverlay()
        const durationMs = Date.now() - recordingStartTime
        const rawBlob = new Blob(recordedChunks, { type: mediaRecorder?.mimeType || 'video/webm' })

        const saveBlob = (blobToSave) => {
          const url = URL.createObjectURL(blobToSave)
          const a = document.createElement('a')
          document.body.appendChild(a)
          a.style = 'display: none'
          a.href = url
          const now = new Date()
          const date = now.toISOString().slice(0, 10)
          const time = now.toTimeString().slice(0, 5).replace(':', '-')
          const titleSlug = title
            ? title.replace(/[^a-zA-Zа-яА-Я0-9\s_-]/g, '').trim().replace(/\s+/g, '_') || 'video'
            : 'video'
          const formatLabel = format === 'portrait' ? 'shorts' : format === 'landscape' ? 'wide' : format || 'video'
          a.download = `${titleSlug}_${formatLabel}_${date}_${time}.webm`
          a.click()
          window.URL.revokeObjectURL(url)
          isRecording.value = false
          stopAllTracks()
        }

        try {
          const fixWebmDuration = await loadFixWebmDuration()
          if (!fixWebmDuration) throw new Error('fixer unavailable')
          fixWebmDuration(rawBlob, durationMs, (fixedBlob) => {
            saveBlob(fixedBlob)
          })
        } catch (e) {
          console.error('Webm duration fix failed, saving raw blob', e)
          saveBlob(rawBlob)
        }
      }

      stream.getVideoTracks()[0].onended = () => {
        if (isRecording.value) {
          stopRecording()
        }
      }

      recordingStartTime = Date.now()
      mediaRecorder.start(1000)
      isRecording.value = true
      await startPlaybackAfterPreroll({ autoPlay, endTimeMs })
    } catch (error) {
      console.error('Error starting browser capture:', error)
      restoreContainer()
      setCaptureLock(false)
      clearSafeZone()
      removeCaptureOverlay()
      clearAutoStop()
      isRecording.value = false
      stopAllTracks()
    }
  }

  const stopRecording = () => {
    setCaptureLock(false)
    clearSafeZone()
    if (mediaRecorder && isRecording.value) {
      const director = window.useDirectorInstance
      if (director) {
        director.pause()
      }
      mediaRecorder.stop()
      isRecording.value = false
      removeCaptureOverlay()
    }
  }

  const toggleRecording = (targetElement = null, options = {}) => {
    if (isRecording.value) {
      stopRecording()
    } else {
      startRecording(targetElement, options)
    }
  }

  return {
    isRecording,
    startRecording,
    stopRecording,
    toggleRecording,
  }
}
