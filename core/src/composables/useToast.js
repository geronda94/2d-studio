import { ref } from 'vue'

// Единая toast-система (UX kit). Использование:
//   import { useToast } from '@/composables/useToast'
//   const { push } = useToast()
//   push('Сохранено', 'success')
const toasts = ref([])
let seq = 0

export function useToast() {
  const push = (message, type = 'info', timeout = 4000) => {
    const id = ++seq
    toasts.value.push({ id, message, type })
    if (timeout > 0) setTimeout(() => dismiss(id), timeout)
    return id
  }
  const dismiss = (id) => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }
  return { toasts, push, dismiss }
}

export const toast = {
  info: (m, t) => useToast().push(m, 'info', t),
  success: (m, t) => useToast().push(m, 'success', t),
  error: (m, t) => useToast().push(m, 'error', t),
  warn: (m, t) => useToast().push(m, 'warning', t),
}
