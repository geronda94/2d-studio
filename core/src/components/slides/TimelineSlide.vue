<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// TimelineSlide — «Линия времени»: горизонтальная шкала с событиями, активное
// событие раскрывается в контентной панели. Перенос элемента Diademas
// (TimelineIndex + TimeLinePanel) в движок.
//
// Канон:
//  • Данные только из props (payload.events), тайминги — локальные start_time.
//  • Появление/активация — детерминированно от relativeTime (§11): активное
//    событие = последнее, чей start_time наступил. Смена панели — one-time CSS
//    transition (разрешено §11, паттерн 3). Без rAF/infinite/<animate>.
//  • Стили/цвета — токены палитры + useVariant.
// ─────────────────────────────────────────────────────────────────────────────
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: Boolean,
  clicks: { type: Number, default: 0 },
  slideStartTime: { type: Number, default: 0 },

  variant: { type: String, default: undefined },
  events: { type: Array, default: () => [] },
  show_images: { type: Boolean, default: true },
})

const { itemVars } = useVariant(computed(() => props.variant), 'TimelineSlide')
const relativeTime = inject('relativeTime', ref(0))

const items = computed(() => props.events || [])

// Дробный прогресс вдоль шкалы (0..len-1): между точкой i и i+1 растёт
// линейно по времени — за счёт этого линия анимированно «доезжает» до следующей.
const exactProgress = computed(() => {
  const len = items.value.length
  if (len <= 1) return 0
  let cur = 0
  for (let i = 0; i < len - 1; i++) {
    const t0 = Number(items.value[i].start_time ?? 0)
    const t1 = Number(items.value[i + 1].start_time ?? t0 + 1000)
    if (relativeTime.value >= t1) {
      cur = i + 1
    } else if (relativeTime.value > t0) {
      const dur = Math.max(1, t1 - t0)
      cur = i + (relativeTime.value - t0) / dur
      break
    }
  }
  return cur
})

const activeIndex = computed(() =>
  Math.min(Math.max(0, items.value.length - 1), Math.floor(exactProgress.value)),
)
const active = computed(() => items.value[activeIndex.value] || null)

const reached = (i) => relativeTime.value >= (items.value[i]?.start_time ?? 0)
const imageRight = computed(() => activeIndex.value % 2 === 1)
const hasImage = computed(() => props.show_images && !!active.value?.image)

// Заполнение линии: доля 0..1 от первой до последней точки. Анимируем через
// transform: scaleX (композитор), а НЕ width — иначе перерисовка каждый кадр,
// что в софтверном рендере (--disable-gpu) даёт дёрганье.
const fillScale = computed(() => {
  const len = items.value.length
  if (len <= 1) return 0
  return Math.min(1, Math.max(0, exactProgress.value / (len - 1)))
})
// Позиция точки на шкале (равномерно, с учётом отступов трека).
const dotPos = (i) => {
  const len = items.value.length
  if (len <= 1) return '50%'
  return `${(i / (len - 1)) * 100}%`
}
</script>

<template>
  <div class="w-full h-full flex flex-col gap-4" :style="{ ...itemVars }">
    <!-- Контентная панель активного события -->
    <div class="flex-1 min-h-0 flex items-center justify-center">
    <Transition name="tl" mode="out-in">
      <div
        v-if="active"
        :key="activeIndex"
        class="flex w-full"
        :class="[
          mobile ? 'flex-col items-center text-center gap-4' : (hasImage ? (imageRight ? 'flex-row-reverse items-center gap-10' : 'flex-row items-center gap-10') : 'flex-col items-center text-center'),
        ]"
      >
        <div
          v-if="hasImage"
          class="overflow-hidden"
          :class="mobile ? 'w-[92%] aspect-[5/4]' : 'shrink-0 w-[36%] h-[360px]'"
          :style="{ borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }"
        >
          <img :src="active.image" alt="" class="w-full h-full object-cover" />
        </div>

        <div class="flex flex-col min-w-0" :class="mobile || !hasImage ? 'items-center text-center' : 'items-start'">
          <div
            class="font-heading font-bold leading-none mb-3"
            :style="{ color: 'var(--color-primary)', fontSize: mobile ? '3rem' : '4.6rem' }"
          >
            {{ active.year }}
          </div>
          <h3 class="font-heading font-bold text-text-primary mb-3" :style="{ fontSize: mobile ? '1.7rem' : '2.4rem' }">
            {{ active.title }}
          </h3>
          <p
            v-if="active.description"
            class="font-sans leading-relaxed"
            :style="{ color: 'var(--text-secondary)', fontSize: mobile ? '1.15rem' : '1.35rem' }"
          >
            {{ active.description }}
          </p>
        </div>
      </div>
    </Transition>
    </div>

    <!-- Шкала: все точки видны сразу, годы — по достижении; линия «доезжает»
         от текущей точки к следующей (анимация в духе Roadmap). -->
    <div class="relative w-full shrink-0 mb-3" :class="mobile ? 'h-16' : 'h-24'">
      <div class="absolute left-10 right-10 top-1/2 -translate-y-1/2">
        <div class="relative h-px" :style="{ background: 'var(--border-strong)' }">
          <!-- Прогресс от первой точки к текущей позиции -->
          <div
            class="tl-fill absolute left-0 top-1/2 h-[2px] w-full rounded-full origin-left"
            :style="{
              background: 'var(--color-secondary)',
              transform: `translateY(-50%) scaleX(${fillScale})`,
              willChange: 'transform',
            }"
          ></div>

          <!-- Все точки (не скрываем нерешённые) + подпись по достижении -->
          <div
            v-for="(e, i) in items"
            :key="e.id ?? i"
            class="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
            :style="{ left: dotPos(i) }"
          >
            <div
              class="tl-dot rounded-full w-3 h-3 transition-[transform,opacity] duration-500"
              :style="{
                transform: `scale(${i === activeIndex ? 1.5 : 1})`,
                background: i === activeIndex
                  ? 'var(--color-primary)'
                  : (reached(i) ? 'var(--color-secondary)' : 'var(--text-muted)'),
                opacity: reached(i) ? 1 : 0.6,
                boxShadow: i === activeIndex ? 'var(--glow-primary)' : 'none',
              }"
            ></div>
            <div
              class="tl-year absolute left-1/2 -translate-x-1/2 whitespace-nowrap font-heading text-sm transition-opacity duration-500"
              :class="i % 2 === 0 ? 'bottom-6' : 'top-6'"
              :style="{
                color: i === activeIndex ? 'var(--color-primary)' : 'var(--text-secondary)',
                opacity: reached(i) ? 1 : 0.35,
              }"
            >
              {{ e.year }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tl-enter-active,
.tl-leave-active {
  transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.tl-enter-from {
  transform: translateX(40px);
}
.tl-leave-to {
  transform: translateX(-40px);
}
</style>
