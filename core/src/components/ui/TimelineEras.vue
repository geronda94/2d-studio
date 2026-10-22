<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  eras: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'TimelineEras')
const relativeTime = inject('relativeTime', ref(0))

const times = computed(() => (props.eras || []).map((e, i) => e.start_time ?? i * motion.value.stagger_ms))

const activeIndex = computed(() => {
  let idx = 0
  times.value.forEach((t, i) => { if (relativeTime.value >= t) idx = i })
  return idx
})

const eraProgress = (idx) => {
  const t = times.value[idx] ?? 0
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const accent = (e, idx) => getHexColor(e.color || `var(--item-accent-${(idx % 4) + 1})`)

// Цветные сегменты коннектора: каждый отрезок между нодами окрашен в акцент
// своей (левой) ноды и «доезжает» при появлении следующей — вместо одной синей
// линии на всю шкалу (прошлый баг: один цвет при разноцветных нодах).
const lineSegments = computed(() => {
  const n = (props.eras || []).length
  if (n <= 1) return []
  return Array.from({ length: n - 1 }).map((_, i) => ({
    i,
    left: `${((i + 0.5) / n) * 100}%`,
    width: `${(1 / n) * 100}%`,
    color: accent(props.eras[i], i),
  }))
})

// Линия идёт строго от центра первой ноды до центра последней — не вылезает
// за крайние точки (прошлый баг: линия торчала за последнюю ноду).
const lineInset = computed(() => {
  const n = (props.eras || []).length
  if (n <= 1) return '50%'
  return `${((0.5 / n) * 100).toFixed(2)}%`
})

const eraStyle = (idx) => {
  const e = eraProgress(idx)
  const active = idx === activeIndex.value
  return {
    opacity: e.toFixed(4),
    transform: `translateY(${((1 - e) * 20).toFixed(2)}px) scale(${active && !props.mobile ? 1.04 : 1})`,
    borderColor: active ? accent(props.eras[idx], idx) : 'var(--item-border)',
  }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :class="mobile ? 'justify-start' : 'justify-center'" :style="{ ...itemVars }">
    <div v-if="title" class="mb-6 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <!-- MOBILE: вертикальная шкала — широкие названия не наезжают друг на друга -->
    <div v-if="mobile" class="relative flex-1 min-h-0 flex flex-col justify-between">
      <div class="absolute left-[22px] top-4 bottom-4 w-[2px]" :style="{ background: 'var(--item-border)' }"></div>
      <div
        v-for="(era, idx) in eras"
        :key="era.id ?? idx"
        class="relative flex-1 min-h-0 flex items-center pl-14"
        :style="eraStyle(idx)"
      >
        <div
          class="absolute left-0 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full flex items-center justify-center z-10"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            border: '2px solid ' + (idx <= activeIndex ? accent(era, idx) : 'var(--item-border)'),
            color: idx <= activeIndex ? accent(era, idx) : 'var(--text-muted)',
          }"
        >
          <Icon :icon="era.icon || 'heroicons:clock'" class="w-5 h-5" />
        </div>
        <div
          class="w-full min-w-0 px-4 py-3 flex items-center gap-3"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          }"
        >
          <span class="font-mono text-xs font-bold shrink-0" :style="{ color: accent(era, idx) }">{{ era.period }}</span>
          <h4 class="font-heading font-bold text-text-primary text-base leading-tight min-w-0 truncate">{{ era.name }}</h4>
        </div>
      </div>
    </div>

    <div v-else class="relative shrink-0">
      <div class="absolute top-12 h-[2px]" :style="{ left: lineInset, right: lineInset, background: 'var(--item-border)' }"></div>
      <div
        v-for="seg in lineSegments"
        :key="'seg' + seg.i"
        class="absolute top-12 h-[2px] origin-left"
        :style="{
          left: seg.left,
          width: seg.width,
          background: seg.color,
          transform: `scaleX(${eraProgress(seg.i + 1)})`,
          willChange: 'transform',
        }"
      ></div>

      <div class="relative grid gap-3 md:gap-4" :style="{ gridTemplateColumns: `repeat(${(eras || []).length || 1}, minmax(0, 1fr))` }">
        <div v-for="(era, idx) in eras" :key="era.id ?? idx" class="flex flex-col items-center text-center px-1 h-full">
          <div
            class="w-24 h-24 rounded-full flex items-center justify-center z-10 mb-4"
            :style="{
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              WebkitBackdropFilter: 'var(--item-backdrop)',
              border: '2px solid ' + (idx <= activeIndex ? accent(era, idx) : 'var(--item-border)'),
              color: idx <= activeIndex ? accent(era, idx) : 'var(--text-muted)',
            }"
          >
            <Icon :icon="era.icon || 'heroicons:clock'" class="w-11 h-11" />
          </div>
          <p class="font-mono text-sm md:text-base font-bold mb-2 min-h-[2.75rem] flex items-center justify-center" :style="{ color: accent(era, idx) }">{{ era.period }}</p>
          <div
            class="w-full px-5 py-5 flex-1"
            :style="[
              eraStyle(idx),
              {
                background: 'var(--item-bg)',
                backdropFilter: 'var(--item-backdrop)',
                WebkitBackdropFilter: 'var(--item-backdrop)',
                borderRadius: 'var(--item-radius)',
                boxShadow: 'var(--item-shadow)',
                padding: 'var(--item-padding)',
                borderWidth: 'var(--item-border-width)',
                borderStyle: 'var(--item-border-style)',
              },
            ]"
          >
            <h4 class="font-heading font-bold text-text-primary text-lg leading-tight">{{ era.name }}</h4>
            <p v-if="era.description && !mobile" class="text-text-secondary text-sm mt-2 leading-snug">{{ era.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
