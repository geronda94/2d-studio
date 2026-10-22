import { ref } from 'vue'

// Promise-based подтверждение (UX kit):
//   const confirm = useConfirm()
//   if (await confirm({ title: 'Удалить?', text: '...' })) { ... }
const state = ref({ open: false, title: '', text: '', okText: 'Подтвердить', cancelText: 'Отмена', danger: false })
let resolver = null

export function useConfirm() {
  const ask = (opts = {}) => {
    state.value = {
      open: true,
      title: opts.title || 'Подтвердите действие',
      text: opts.text || '',
      okText: opts.okText || 'Подтвердить',
      cancelText: opts.cancelText || 'Отмена',
      danger: !!opts.danger,
    }
    return new Promise((resolve) => { resolver = resolve })
  }
  const resolve = (val) => {
    state.value = { ...state.value, open: false }
    if (resolver) { resolver(val); resolver = null }
  }
  return { state, ask, resolve }
}
