<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  left: { type: Object, default: () => ({}) },
  right: { type: Object, default: () => ({}) },
  note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ConceptDiptych')
const relativeTime = inject('relativeTime', ref(0))

const leftAccent = getHexColor('var(--color-secondary)')
const rightAccent = getHexColor('var(--color-accent)')

const reveal = (t, y = 14) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const leftPoints = computed(() => props.left?.points || [])
const rightPoints = computed(() => props.right?.points || [])

const sides = computed(() => [
  {
    key: 'left',
    title: props.left?.title || '',
    points: leftPoints.value,
    accent: leftAccent,
    icon: 'lucide:heart-handshake',
    offset: 0,
  },
  {
    key: 'right',
    title: props.right?.title || '',
    points: rightPoints.value,
    accent: rightAccent,
    icon: 'lucide:book-open',
    offset: leftPoints.value.length,
  },
])

const noteTime = computed(() => {
  const all = [...leftPoints.value, ...rightPoints.value]
  const starts = all.map((p, i) => p.start_time ?? (i + 1) * motion.value.stagger_ms)
  const maxStart = starts.length ? Math.max(...starts) : 0
  // Заметка появляется вместе с последним пунктом, а не на целый шаг позже —
  // иначе на кадре конца слайда она ещё невидима.
  return Math.max(0, Math.max(maxStart, all.length * motion.value.stagger_ms) - motion.value.appear_ms)
})

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const pointStyle = {
  background: 'var(--item-primary-bg)',
  backdropFilter: 'var(--item-primary-backdrop)',
  WebkitBackdropFilter: 'var(--item-primary-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!left?.title && !right?.title"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="flex-1 min-h-0 overflow-hidden flex flex-col gap-3">
      <div
        class="flex-1 min-h-0 overflow-hidden grid gap-3"
        :class="mobile ? 'grid-cols-1 grid-rows-2' : 'grid-cols-2 auto-rows-fr'"
      >
        <section
          v-for="(side, si) in sides"
          :key="side.key"
          class="min-h-0 flex flex-col gap-2"
          :style="reveal(si * motion.stagger_ms)"
        >
          <div class="flex items-center gap-2 shrink-0">
            <span
              class="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
              :style="{ background: getColorAlpha(side.accent, 0.16), border: '1px solid ' + getColorAlpha(side.accent, 0.4) }"
            >
              <Icon :icon="side.icon" class="w-4 h-4" :style="{ color: side.accent }" />
            </span>
            <h3 class="font-heading font-bold text-lg md:text-2xl text-text-primary leading-tight">
              {{ side.title }}
            </h3>
          </div>

          <ul class="flex-1 min-h-0 overflow-hidden flex flex-col gap-1.5">
            <li
              v-for="(pt, i) in side.points"
              :key="side.key + i"
              class="flex-1 min-h-0 flex items-center gap-2.5 px-3.5 py-1.5"
              :style="[pointStyle, reveal(pt.start_time ?? (side.offset + i + 1) * motion.value.stagger_ms)]"
            >
              <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ background: side.accent }"></span>
              <span class="min-w-0">
                <span class="block text-text-primary text-sm md:text-base leading-snug">{{ pt.text }}</span>
                <span v-if="pt.source" class="block text-[10px] md:text-[11px] font-mono text-text-muted mt-0.5">{{ pt.source }}</span>
              </span>
            </li>
          </ul>
        </section>
      </div>

      <p
        v-if="note"
        class="shrink-0 px-3 py-2 text-center text-[11px] md:text-xs italic text-text-secondary"
        :style="[itemStyle, reveal(noteTime)]"
      >
        {{ note }}
      </p>
    </div>
  </div>
</template>
