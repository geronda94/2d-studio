export const getHexColor = (colorId?: string) => {
  if (!colorId) return 'var(--color-secondary)'
  
  const legacyMap: Record<string, string> = {
    'brand-blue': 'color-primary',
    'brand-light-blue': 'color-secondary',
    'brand-lightBlue': 'color-secondary',
    'brand-green': 'color-success',
    'brand-amber': 'color-warning',
    'brand-orange': 'color-accent',
    'brand-accent': 'color-accent',
    'blue': 'color-secondary', // from ArchitectureDiagram
    'green': 'color-success',
    'amber': 'color-warning',
    'default': 'color-secondary',
    'core': 'color-secondary',
  }
  
  const mapped = legacyMap[colorId] || colorId
  
  if (mapped.startsWith('#') || mapped.startsWith('rgb') || mapped.startsWith('var')) {
    return mapped
  }
  return `var(--${mapped})`
}

/**
 * Возвращает цвет с прозрачностью через rgb(var(--X-rgb) / alpha).
 * Совместим с любым браузером (в т.ч. SwiftShader/software renderer).
 * useTheme.js автоматически создаёт --X-rgb для каждого hex-токена.
 *
 * Для hex-цвет (#D87B22) напрямую: rgba(r, g, b, alpha).
 */
export const getColorAlpha = (colorId: string | undefined, alpha: number): string => {
  const hex = getHexColor(colorId)

  // Если это var(--X) → используем var(--X-rgb) с modern rgb() синтаксисом
  if (hex.startsWith('var(--') && hex.endsWith(')')) {
    const key = hex.slice(4, -1) // '--color-secondary'
    return `rgb(var(${key}-rgb) / ${alpha})`
  }

  // Если это прямой hex → парсим и возвращаем rgba()
  if (hex.startsWith('#')) {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    if (!isNaN(r) && !isNaN(g) && !isNaN(b)) {
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
  }

  // Fallback
  return `rgb(var(--color-secondary-rgb) / ${alpha})`
}
