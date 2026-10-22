/**
 * useWaveform.js
 * 
 * Composable for loading and caching audio waveform peak data.
 * Uses the Web Audio API to decode audio files and extract
 * amplitude peaks for rendering in a canvas element.
 * 
 * Cache is module-level so it persists across component instances.
 */

// Module-level cache: url -> { peaks: Float32Array, duration: seconds }
const peakCache = new Map()
// Track in-flight requests to avoid duplicate fetches
const pendingFetches = new Map()

// Ограничиваем параллелизм: одновременная загрузка+декодирование десятков WAV
// перегружает сеть и CPU (и рвётся при смене сети: ERR_NETWORK_CHANGED).
const MAX_CONCURRENT = 2
let activeLoads = 0
const loadQueue = []

function withSlot(task) {
  return new Promise((resolve, reject) => {
    const run = () => {
      activeLoads++
      Promise.resolve()
        .then(task)
        .then(resolve, reject)
        .finally(() => {
          activeLoads--
          const next = loadQueue.shift()
          if (next) next()
        })
    }
    if (activeLoads < MAX_CONCURRENT) run()
    else loadQueue.push(run)
  })
}

// Транзиентные сетевые сбои (ERR_NETWORK_CHANGED, Failed to fetch) — повторяем.
async function fetchWithRetry(url, tries = 3) {
  let lastErr
  for (let attempt = 0; attempt < tries; attempt++) {
    try {
      const response = await fetch(url)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response
    } catch (err) {
      lastErr = err
      if (attempt < tries - 1) {
        await new Promise((r) => setTimeout(r, 400 * (attempt + 1)))
      }
    }
  }
  throw lastErr
}

/**
 * Returns `{ peaks, duration }` for the given audio URL.
 * `peaks` — Float32Array of `numSamples` amplitude peaks, normalized to [0, 1];
 * `duration` — длительность файла в секундах (для оконной нарезки волны по media_offset).
 */
async function loadPeaks(url, numSamples = 200) {
  if (peakCache.has(url)) {
    return peakCache.get(url)
  }

  // If already loading, wait for it
  if (pendingFetches.has(url)) {
    return pendingFetches.get(url)
  }

  const promise = withSlot(async () => {
    try {
      const response = await fetchWithRetry(url)
      const arrayBuffer = await response.arrayBuffer()

      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer)
      const duration = audioBuffer.duration
      ctx.close()

      // Mix all channels down to mono
      const numChannels = audioBuffer.numberOfChannels
      const length = audioBuffer.length
      const mono = new Float32Array(length)
      for (let c = 0; c < numChannels; c++) {
        const channelData = audioBuffer.getChannelData(c)
        for (let i = 0; i < length; i++) {
          mono[i] += channelData[i] / numChannels
        }
      }

      // Downsample to numSamples peaks
      const blockSize = Math.floor(length / numSamples)
      const peaks = new Float32Array(numSamples)
      let maxPeak = 0

      for (let i = 0; i < numSamples; i++) {
        const start = i * blockSize
        let max = 0
        for (let j = 0; j < blockSize; j++) {
          const abs = Math.abs(mono[start + j] || 0)
          if (abs > max) max = abs
        }
        peaks[i] = max
        if (max > maxPeak) maxPeak = max
      }

      // Normalize
      if (maxPeak > 0) {
        for (let i = 0; i < numSamples; i++) {
          peaks[i] /= maxPeak
        }
      }

      const result = { peaks, duration }
      peakCache.set(url, result)
      return result
    } catch (err) {
      console.warn('[useWaveform] Failed to load peaks for', url, err)
      return null
    } finally {
      pendingFetches.delete(url)
    }
  })

  pendingFetches.set(url, promise)
  return promise
}

/**
 * Draws a waveform from peaks onto a canvas element.
 * 
 * @param {HTMLCanvasElement} canvas
 * @param {Float32Array} peaks
 * @param {object} opts - { color, backgroundColor, barWidth, gap }
 */
function drawWaveform(canvas, peaks, opts = {}) {
  if (!canvas || !peaks) return

  const {
    color = 'rgba(255,255,255,0.7)',
    backgroundColor = 'transparent',
    barWidth = 2,
    gap = 1
  } = opts

  const dpr = window.devicePixelRatio || 1
  const width = canvas.offsetWidth
  const height = canvas.offsetHeight

  if (width === 0 || height === 0) return

  canvas.width = width * dpr
  canvas.height = height * dpr

  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  // Background
  if (backgroundColor !== 'transparent') {
    ctx.fillStyle = backgroundColor
    ctx.fillRect(0, 0, width, height)
  } else {
    ctx.clearRect(0, 0, width, height)
  }

  const step = barWidth + gap
  const numBars = Math.floor(width / step)
  const peaksPerBar = peaks.length / numBars
  const centerY = height / 2

  ctx.fillStyle = color

  for (let i = 0; i < numBars; i++) {
    // Average the peaks for this bar
    const startPeak = Math.floor(i * peaksPerBar)
    const endPeak = Math.floor((i + 1) * peaksPerBar)
    let sum = 0
    let count = 0
    for (let p = startPeak; p < endPeak && p < peaks.length; p++) {
      sum += peaks[p]
      count++
    }
    const amplitude = count > 0 ? sum / count : 0
    const barHeight = Math.max(1, amplitude * (height * 0.85))

    const x = i * step
    ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight)
  }
}

/**
 * Вырезает из полных peaks аудиофайла окно, соответствующее видимой части клипа.
 * Без этого обрезанный клип показывал волну всего файла, сжатую в новую ширину.
 *
 * @param {Float32Array} peaks       полные пики файла (нормированы 0..1)
 * @param {number} fileDuration      длительность файла в секундах
 * @param {number} offsetMs          media_offset клипа (мс от начала файла)
 * @param {number} durationMs        длительность клипа на таймлайне (мс)
 * @returns {Float32Array} срез пиков (тот же массив, если окно покрывает файл целиком)
 */
function slicePeaksWindow(peaks, fileDuration, offsetMs = 0, durationMs = 0) {
  if (!peaks || !fileDuration || fileDuration <= 0) return peaks
  const totalMs = fileDuration * 1000
  const startMs = Math.max(0, Math.min(totalMs, Number(offsetMs) || 0))
  const endMs = durationMs > 0
    ? Math.min(totalMs, startMs + durationMs)
    : totalMs
  if (startMs <= 0 && endMs >= totalMs) return peaks

  const startIdx = Math.max(0, Math.floor((startMs / totalMs) * peaks.length))
  const endIdx = Math.max(startIdx + 1, Math.ceil((endMs / totalMs) * peaks.length))
  return peaks.slice(startIdx, Math.min(peaks.length, endIdx))
}

export { loadPeaks, drawWaveform, slicePeaksWindow }
