<script setup>
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  points: { type: Array, default: () => [] },
  x_label: { type: String, default: '' },
  y_label: { type: String, default: '' },
  quadrant_labels: { type: Array, default: () => [] }, // [tl, tr, bl, br]
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'QuadrantMatrix')
const relativeTime = inject('relativeTime', ref(0))

const clamp = (v) => Math.max(0, Math.min(100, Number(v) || 0))
// Пузырь позиционируем в диапазоне 4..92% и поджимаем к краям через clamp(),
// чтобы крупные круги и подписи не резались границами квадрантов.
const pos = (p) => {
  const lx = 4 + clamp(p.x) * 0.88
  const ty = 4 + (100 - clamp(p.y)) * 0.88
  return {
    left: `clamp(28px, ${lx.toFixed(2)}%, calc(100% - 28px))`,
    top: `clamp(26px, ${ty.toFixed(2)}%, calc(100% - 26px))`,
  }
}

const labelFor = (i) => (props.quadrant_labels || [])[i] || ''

const reveal = (p, i) => {
  const t = i * motion.value.stagger_ms
  const prog = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - prog, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.7 + 0.3 * e).toFixed(3)})` }
}

const accent = (p) => getHexColor(p.color || 'var(--color-secondary)')
const maxBubble = computed(() => {
  const arr = (props.points || []).map((p) => Number(p.bubble) || 0)
  return Math.max(1, ...arr)
})
// Пузыри крупнее и пропорциональны данным — заполняют квадранты. На мобильном
// (узкий/высокий кадр) масштаб выше, иначе 3 точки в большом поле читаются как
// «неполный» компонент.
const bubbleSize = (p) => {
  const raw = Number(p.bubble) || 22
  const rel = raw / maxBubble.value
  const base = props.mobile ? 26 : 18
  const span = props.mobile ? 30 : 22
  return Math.round(base + rel * span)
}
const compact = computed(() => props.density === 'compact' || props.mobile)

// Подпись выносим рядом с пузырём (под кругом, у нижней границы — над кругом):
// внутри кластера тексты не помещаются и перекрывают друг друга.
const labelAbove = (p) => clamp(p.y) < 18
const labelStyle = (p) => {
  const x = clamp(p.x)
  const v = labelAbove(p) ? { bottom: '100%', marginBottom: '2px' } : { top: '100%', marginTop: '2px' }
  if (x > 72) return { ...v, right: '0%' }
  if (x < 28) return { ...v, left: '0%' }
  return { ...v, left: '50%', transform: 'translateX(-50%)' }
}
</script>

<template>
  <div class="w-full max-w-5xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="!points.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0">
        <!-- квадрантные подписи (без фоновых панелей — иначе пустые ячейки читаются
             как сломанная верстка; оси-разделители дают структуру) -->
        <div v-if="quadrant_labels && quadrant_labels.length" class="absolute inset-0 pointer-events-none">
          <span v-for="i in 4" :key="'q' + i"
                class="absolute font-mono uppercase tracking-wider text-text-muted"
                :class="[
                  mobile ? 'text-[10px]' : 'text-[11px]',
                  i === 1 || i === 2 ? 'top-1' : 'bottom-1',
                  i === 1 || i === 3 ? 'left-2' : 'right-2',
                ]">{{ labelFor(i - 1) }}</span>
        </div>
        <!-- оси -->
        <div class="absolute inset-0 pointer-events-none">
          <div class="absolute left-1/2 top-0 bottom-0 w-px" :style="{ background: 'var(--item-border)' }"></div>
          <div class="absolute top-1/2 left-0 right-0 h-px" :style="{ background: 'var(--item-border)' }"></div>
        </div>

        <!-- пузыри -->
        <div
          v-for="(p, i) in points"
          :key="p.label + i"
          class="absolute flex items-center justify-center"
          :style="[pos(p), reveal(p, i)]"
        >
          <span
            class="rounded-full block"
            :style="{
              width: bubbleSize(p) + 'px',
              height: bubbleSize(p) + 'px',
              background: getColorAlpha(accent(p), 0.28),
              border: '2px solid ' + accent(p),
              boxShadow: '0 0 0 3px ' + getColorAlpha(accent(p), 0.10),
            }"
          ></span>
          <span
            class="absolute whitespace-nowrap text-[10px] font-mono font-semibold text-text-primary"
            :style="labelStyle(p)"
          >{{ p.label }}</span>
        </div>

        <!-- подписи осей -->
        <span v-if="x_label" class="absolute left-1/2 -translate-x-1/2 font-mono text-text-secondary" :class="mobile ? 'bottom-1 text-[11px]' : '-bottom-7 text-xs'">{{ x_label }} →</span>
        <span v-if="y_label" class="absolute top-1/2 -translate-y-1/2 -rotate-90 font-mono text-text-secondary" :class="mobile ? 'left-1 text-[11px]' : '-left-8 text-xs'">{{ y_label }} →</span>
      </div>

      <div v-if="source_note" class="mt-8 text-center text-[11px] font-mono text-text-muted">{{ source_note }}</div>
    </template>
  </div>
</template>
