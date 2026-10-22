// Варианты отрисовки (типизация, Фаза 2.3).
// Общий механизм: любой компонент вызывает useVariant(props.variant) и получает
// резолвнутые стили для своих частей (айтемы/ноды, линии, фон).
// Определения вариантов хранятся в БД (таблица style_variants) в едином JSON-формате,
// поэтому добавлять новые типы можно без правки кода компонентов.
import { ref, computed, inject } from 'vue'
import { fetchVariants } from '../services/api'

const variantsCache = ref(null)
const loading = ref(false)

export async function loadVariants() {
  if (variantsCache.value) return variantsCache.value
  if (loading.value) return null
  loading.value = true
  try {
    const list = await fetchVariants()
    const map = {}
    for (const v of list) map[v.slug] = v
    variantsCache.value = map
    return map
  } catch (err) {
    console.warn('[Variant] не удалось загрузить варианты:', err)
    return null
  } finally {
    loading.value = false
  }
}

// Резолв значения токена: если это ключ токена темы → var(--key), иначе как есть.
function tok(val) {
  if (!val) return null
  return String(val).startsWith('var(') ? val : `var(--${val})`
}

// Резолв фона части: solid | gradient | blur | transparent
function resolveBg(bg) {
  if (!bg) return { background: 'transparent', backdropFilter: 'none' }
  const type = bg.type || 'solid'
  if (type === 'gradient') {
    const angle = bg.angle ?? 135
    const from = tok(bg.from) || 'transparent'
    const to = tok(bg.to) || 'transparent'
    return { background: `linear-gradient(${angle}deg, ${from}, ${to})`, backdropFilter: 'none' }
  }

  if (type === 'blur') {
    const rgb = bg.value ? `var(--${bg.value}-rgb)` : '255 255 255'
    const opacity = bg.opacity ?? 0.5
    const blur = bg.blur ?? '12px'
    return { background: `rgb(${rgb} / ${opacity})`, backdropFilter: `blur(${blur})` }
  }
  if (type === 'transparent') {
    return { background: 'transparent', backdropFilter: 'none' }
  }

  if (type === 'svg') {
    const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor || 'transparent'
    // Ensure we use the proper CSS background shorthand syntax. 
    // We can't easily put color on a separate layer if it's the only layer, so we just append it.
        return { 
      background: `${fallback} url("data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}") ${pos} / ${size} no-repeat`,
      backdropFilter: 'none' 
    }
  }
  // solid
  return { background: tok(bg.value) || 'transparent', backdropFilter: 'none' }
}

function dashForStyle(style) {
  if (style === 'dashed') return '6 12'
  if (style === 'dotted') return '2 6'
  return 'none'
}

// Ритм по умолчанию = текущие хардкоды компонентов (P3: поведение не меняется):
// appear_ms 500 — появление айтема, stagger_ms 1000 — шаг §8.3, count_ms 2000 — счётчики.
const DEFAULT_MOTION = { appear_ms: 500, stagger_ms: 1000, count_ms: 2000 }

// Встроенный дефолт: БИТОВО совпадает с вариантом "tech" в БД — поддерживай
// синхронно со scripts/seed_variants.py! Используется до загрузки вариантов с БД
// и как запасной при ошибке сети. Любое расхождение с БД = видимый «щелчок»
// (сначала один материал, после ответа API — другой) при первом появлении слайда.
// tech = сплошные карточки, стекло только у ArchitectureDiagram (спека §10.1).
const FALLBACK_CONFIG = {
  motion: { ...DEFAULT_MOTION },
  item: {
    bg: { type: 'solid', value: 'bg-surface' },
    border: { width: 1, style: 'solid', color: 'border-main' },
    radius: '16px',
    shadow: '0 8px 24px rgb(0 0 0 / 0.25)',
    spacing: { padding: '12px', gap: '8px' },
  },
  item_primary: {
    bg: { type: 'solid', value: 'bg-surface' },
    border: { width: 1, style: 'solid', color: 'border-main' },
    radius: '16px',
    shadow: 'none',
    spacing: { padding: '16px', gap: '8px' },
  },
  line: { style: 'dashed', width: 2, animation: 'dash' },
  surface: { bg: { type: 'solid', value: 'bg-base' } },
  components: {
    ArchitectureDiagram: {
      item: { bg: { type: 'blur', value: 'bg-surface', opacity: 0.7, blur: '16px' } },
    },
    TerminalMockup: {
      item: { bg: { type: 'solid', value: 'bg-surface-hover' } },
    },
    CodeExplain: {
      item: { bg: { type: 'solid', value: 'bg-surface-hover' } },
    },
    BrowserMockup: {
      item: { bg: { type: 'solid', value: 'bg-surface-hover' } },
    },
  },
}

export function useVariant(variantSlug, componentSlug) {
  // Ленивая загрузка вариантов с БД (однократно, кэш в ref → реактивно).
  if (!variantsCache.value && !loading.value) {
    loadVariants()
  }

  // Дефолтный вариант презентации (provide из MainPresentation). Слайд переопределяет через payload.variant.
  const injectedDefault = inject('defaultVariant', null)

  const slug = computed(() => {
    const v = variantSlug && typeof variantSlug === 'object' ? variantSlug.value : variantSlug
    const d = injectedDefault && typeof injectedDefault === 'object' ? injectedDefault.value : injectedDefault
    return v || d || 'tech'
  })

  const component = computed(() => {
    const c = componentSlug && typeof componentSlug === 'object' ? componentSlug.value : componentSlug
    return c || null
  })

  const config = computed(() => {
    const map = variantsCache.value || {}
    const base = (map[slug.value] && map[slug.value].config) || (map.tech && map.tech.config) || FALLBACK_CONFIG
    // Точечное переопределение под конкретный компонент (секция `components.<slug>`).
    const over = (component.value && base.components && base.components[component.value]) || {}
    return {
      item: { ...(base.item || {}), ...(over.item || {}) },
      item_primary: { ...(base.item_primary || {}), ...(over.item_primary || {}) },
      line: { ...(base.line || {}), ...(over.line || {}) },
      surface: { ...(base.surface || {}), ...(over.surface || {}) },
      motion: { ...DEFAULT_MOTION, ...(base.motion || {}), ...(over.motion || {}) },
    }
  })

  // Ритм анимаций (P3): компонент читает длительности отсюда, а не из хардкода.
  // Мерж поверх дефолта — кастомным вариантам без motion ничего ломать не будет.
  const motion = computed(() => ({ ...config.value.motion }))

  // CSS-переменные для айтемов/нод (накладываются на корень компонента).
  // prefix "item" (обычные) и "item-primary" (акцентные/главные) — чтобы не конфликтовали.
  function resolveItemVars(item, prefix) {
    const bg = resolveBg(item && item.bg)
    const border = (item && item.border) || {}
    const spacing = (item && item.spacing) || {}
    const bw = border.width ?? 1
    const bs = border.style || 'solid'
    return {
      [`--${prefix}-bg`]: bg.background,
      [`--${prefix}-backdrop`]: bg.backdropFilter,
      [`--${prefix}-radius`]: (item && item.radius) || '0px',
      [`--${prefix}-shadow`]: (item && item.shadow) || 'none',
      [`--${prefix}-border-width`]: `${bw}px`,
      [`--${prefix}-border-style`]: bs,
      [`--${prefix}-border`]: border.color ? tok(border.color) : 'color-mix(in srgb, var(--text-primary) 15%, transparent)',
      [`--${prefix}-padding`]: spacing.padding || '0px',
      [`--${prefix}-gap`]: spacing.gap || '0px',
    }
  }

  const itemVars = computed(() => resolveItemVars(config.value.item, 'item'))
  // Акцентный айтем (главная нода/карточка) — при отсутствии item_primary наследует item.
  const itemPrimaryVars = computed(() =>
    resolveItemVars(config.value.item_primary || config.value.item, 'item-primary'),
  )

  // Резолвнутый объект линий (для SVG: stroke/dasharray/анимация).
  const line = computed(() => {
    const l = config.value.line || {}
    return {
      color: tok(l.color) || 'var(--brand-light-blue)',
      style: l.style || 'solid',
      dash: dashForStyle(l.style),
      width: l.width ?? 2,
      animation: l.animation || 'none',
    }
  })

  // CSS-переменные для фона контейнера.
  const surfaceVars = computed(() => {
    const bg = resolveBg(config.value.surface && config.value.surface.bg)
    return {
      '--surface-bg': bg.background,
      '--surface-backdrop': bg.backdropFilter,
    }
  })

  return {
    slug,
    config,
    itemVars,
    itemPrimaryVars,
    surfaceVars,
    line,
    motion,
  }
}
