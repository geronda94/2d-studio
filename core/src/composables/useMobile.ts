import { ref, computed, onMounted, onUnmounted } from 'vue'

const forceMobile = ref(false)
const windowIsMobile = ref(false)
// Тач-устройство (в т.ч. телефон в ландшафте, где windowIsMobile=false).
// Нужно, чтобы показывать контролы там, где нет hover (мышь-hover на тач недоступен).
const isTouch = ref(false)

const checkWindowSize = () => {
  windowIsMobile.value = window.innerHeight > window.innerWidth
}

if (typeof window !== 'undefined') {
  window.addEventListener('resize', checkWindowSize)
  // Init
  checkWindowSize()
  isTouch.value =
    'ontouchstart' in window ||
    (typeof navigator !== 'undefined' && navigator.maxTouchPoints > 0) ||
    (typeof window.matchMedia === 'function' &&
      window.matchMedia('(pointer: coarse)').matches)
}

export function useMobile() {
  const isMobile = computed(() => forceMobile.value || windowIsMobile.value)
  
  const toggleForceMobile = () => {
    forceMobile.value = !forceMobile.value
  }

  return {
    isMobile,
    isTouch,
    forceMobile,
    toggleForceMobile,
    checkWindowSize
  }
}
