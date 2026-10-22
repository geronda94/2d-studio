import { ref, onUnmounted } from 'vue'

export interface DirectorEvent<T = string> {
  time: number
  action: T
  [key: string]: any
}

export function useDirector<T = string>(
  events: DirectorEvent<T>[], 
  actionHandler: (event: DirectorEvent<T>) => void,
  options: { delay?: number } = {}
) {
  const isRunning = ref(false)
  const currentTime = ref(0)
  let startTime = 0
  let animationFrameId: number | null = null
  let nextEventIndex = 0

  const start = () => {
    if (isRunning.value) return
    isRunning.value = true
    nextEventIndex = 0
    
    // Sort events by time to ensure chronological order
    const sortedEvents = [...events].sort((a, b) => a.time - b.time)
    
    const loop = (timestamp: number) => {
      if (!isRunning.value) return
      currentTime.value = timestamp - startTime

      // Process all events that should have fired by now
      while (nextEventIndex < sortedEvents.length && currentTime.value >= sortedEvents[nextEventIndex].time) {
        actionHandler(sortedEvents[nextEventIndex])
        nextEventIndex++
      }

      if (nextEventIndex < sortedEvents.length) {
        animationFrameId = requestAnimationFrame(loop)
      } else {
        isRunning.value = false // Finished
      }
    }

    if (options.delay) {
      setTimeout(() => {
        startTime = performance.now()
        animationFrameId = requestAnimationFrame(loop)
      }, options.delay)
    } else {
      startTime = performance.now()
      animationFrameId = requestAnimationFrame(loop)
    }
  }

  const stop = () => {
    isRunning.value = false
    if (animationFrameId) cancelAnimationFrame(animationFrameId)
  }

  const reset = () => {
    stop()
    currentTime.value = 0
    nextEventIndex = 0
  }

  onUnmounted(stop)

  return {
    start, stop, reset, isRunning, currentTime
  }
}
