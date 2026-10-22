import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { Icon } from '@iconify/vue'

const app = createApp(App)

// Режим рендера (?render=true): headless-Chromium рендерит софтверно (SwiftShader),
// а backdrop-filter (стекло/blur) в таком режиме очень медленный и жрёт память (OOM).
// Отключаем его только во время рендера — живой просмотр не затрагивается.
if (new URLSearchParams(window.location.search).get('render') === 'true') {
  const style = document.createElement('style')
  style.textContent = '*, *::before, *::after { backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }'
  document.head.appendChild(style)
}

app.use(router)
app.component('Icon', Icon)

// v-click-outside — закрытие по клику вне элемента. Используется в
// EmojiPickerModal (и потенциально других оверлеях). Раньше директива не была
// зарегистрирована → Vue warn «Failed to resolve directive» и клик снаружи не работал.
app.directive('click-outside', {
  mounted(el, binding) {
    el.__clickOutside__ = (event) => {
      if (el === event.target || el.contains(event.target)) return
      if (typeof binding.value === 'function') binding.value(event)
    }
    // mousedown в capture-фазе: срабатывает до click и не конфликтует с
    // обработчиками кнопок/ссылок внутри элемента.
    document.addEventListener('mousedown', el.__clickOutside__, true)
  },
  beforeUnmount(el) {
    if (el.__clickOutside__) {
      document.removeEventListener('mousedown', el.__clickOutside__, true)
      delete el.__clickOutside__
    }
  },
})

app.mount('#app')
