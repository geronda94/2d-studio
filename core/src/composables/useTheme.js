// Тема (Фаза 2): загрузка и применение дизайн-токенов проекта.
// Токены из БД применяются как CSS-переменные (--bg-base, --brand-blue, ...).
import { fetchPresentationTokens } from '../services/api'

function hexToRgb(hex) {
  const s = String(hex).trim();
  let m = s.replace('#', '').match(/^([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
  if (m) return `${parseInt(m[1], 16)} ${parseInt(m[2], 16)} ${parseInt(m[3], 16)}`;
  // rgb()/rgba() — запятая или пробельный синтаксис: из rgba(255,255,255,.92) → "255 255 255"
  m = s.match(/^rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})/i);
  if (m) return `${m[1]} ${m[2]} ${m[3]}`;
  return null;
}

// Нормализуем значение токена: из {key,type,value} или просто строки
function tokenValue(tok) {
  return (tok && typeof tok === 'object') ? tok.value : tok
}

function tokenType(tok) {
  return (tok && typeof tok === 'object') ? tok.type : 'color'
}

export function applyTheme(tokens, target = null) {
  const root = target || document.documentElement
  for (const [key, tok] of Object.entries(tokens || {})) {
    if (key === 'font_link') continue // не CSS-переменная — грузится через applyFontLink
    const val = tokenValue(tok)
    if (val === undefined || val === null) continue
    root.style.setProperty(`--${key}`, val)
    if (tokenType(tok) !== 'font_family') {
      const rgb = hexToRgb(val)
      if (rgb) {
        root.style.setProperty(`--${key}-rgb`, rgb)
      }
    }
  }
}

// Загружает Google Fonts из токена `font_link` (шрифты не хранятся в репозитории).
// Один <link> в <head>, href обновляется при смене темы.
export function applyFontLink(tokens) {
  const link = tokens && tokens['font_link']
  const url = tokenValue(link)
  if (!url || typeof url !== 'string' || url.indexOf('fonts.googleapis.com') === -1) return
  const id = 'theme-font-link'
  let el = document.getElementById(id)
  if (!el) {
    el = document.createElement('link')
    el.id = id
    el.rel = 'stylesheet'
    document.head.appendChild(el)
  }
  el.href = url
}

// Применяем тему ТОЛЬКО к контенту слайда (.slides-container),
// чтобы редактор/сайдбар/подложка оставались на фиксированном тёмном стиле (:root).
export function applyThemeToSlides(tokens, attempt = 0) {
  const container = document.querySelector('.slides-container')
  if (container) {
    applyTheme(tokens, container)
    return
  }
  if (attempt < 25) {
    setTimeout(() => applyThemeToSlides(tokens, attempt + 1), 200)
  }
}

export async function loadThemeForPresentation(presentationId) {
  try {
    const data = await fetchPresentationTokens(presentationId)
    if (data && data.tokens) {
      applyFontLink(data.tokens)
      applyThemeToSlides(data.tokens)
    }
    return data
  } catch (err) {
    console.warn('[Theme] не удалось загрузить токены:', err)
    return null
  }
}
