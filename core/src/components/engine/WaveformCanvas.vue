<template>
  <canvas
    ref="canvasRef"
    class="absolute inset-0 w-full h-full pointer-events-none"
    :style="{ opacity: peaksData ? 1 : 0 }"
  />
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { loadPeaks, drawWaveform, slicePeaksWindow } from '../../composables/useWaveform'

const props = defineProps({
  /** Full URL or path to the audio file */
  src: {
    type: String,
    default: null
  },
  /** Waveform bar color */
  color: {
    type: String,
    default: 'rgba(255,255,255,0.55)'
  },
  /** Bar width in px */
  barWidth: {
    type: Number,
    default: 2
  },
  /** Gap between bars */
  gap: {
    type: Number,
    default: 1
  },
  /** media_offset клипа: смещение внутрь файла (мс) — левая граница окна волны */
  offset: {
    type: Number,
    default: 0
  },
  /** Длительность клипа на таймлайне (мс) — ширина окна волны */
  duration: {
    type: Number,
    default: 0
  }
})

const canvasRef = ref(null)
const peaksData = ref(null)
let resizeObserver = null

// Волна рисуется только для видимого окна клипа, иначе после обрезки
// разворачивалась волна всего файла, сжатая в новую ширину.
const visiblePeaks = computed(() => {
  if (!peaksData.value) return null
  return slicePeaksWindow(
    peaksData.value.peaks,
    peaksData.value.duration,
    props.offset,
    props.duration,
  )
})

const render = () => {
  if (!canvasRef.value || !visiblePeaks.value) return
  drawWaveform(canvasRef.value, visiblePeaks.value, {
    color: props.color,
    barWidth: props.barWidth,
    gap: props.gap
  })
}

const load = async (src) => {
  if (!src) {
    peaksData.value = null
    return
  }
  // Resolve relative paths (e.g. /audio/file.mp3 -> absolute)
  const url = src.startsWith('http') ? src : `${window.location.origin}${src}`
  peaksData.value = await loadPeaks(url, 300)
  await nextTick()
  render()
}

onMounted(async () => {
  await load(props.src)

  // Re-draw on resize
  resizeObserver = new ResizeObserver(() => {
    render()
  })
  if (canvasRef.value) {
    resizeObserver.observe(canvasRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

watch(() => props.src, (newSrc) => {
  load(newSrc)
})

watch(() => props.color, () => {
  render()
})

// Перерисовка при изменении окна клипа (трим слева/справа, сплит) —
// ширина canvas меняется не всегда, поэтому слушаем явно.
watch([() => props.offset, () => props.duration], async () => {
  await nextTick()
  render()
})
</script>
