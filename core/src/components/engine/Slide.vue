<template>
  <Transition name="brand-blur" :css="!isHeadless">
    <div v-show="isActive" class="slide absolute inset-0 w-full h-full flex"
         :class="[
           `variant-${variantSlug}`,
           effectiveLayout === 'row' ? 'flex-row items-center' : 'flex-col',
           bare ? 'p-0' : (isMobile ? 'pt-5 px-4 pb-6' : 'px-12 py-8')
         ]"
          :style="[surfaceVars, slideBgStyle]">
      
      <!-- УНИФИЦИРОВАННЫЙ ЗАГОЛОВОК -->
      <!-- ВАРИАНТ 1: COL LAYOUT (Горизонтально сверху) -->
      <div v-if="!bare && (title || subtitle || $slots.header) && effectiveLayout === 'col'" 
           class="w-full flex flex-col shrink-0 z-10 relative"
           :class="isMobile ? 'text-left px-2 items-start mb-3 mt-1' : 'text-center items-center mb-4'">
        <div class="mb-2 w-full">
          <slot name="header">
            <div v-if="title" class="overflow-hidden">
              <h1 class="text-4xl font-heading mb-1 leading-tight inline" :style="{ fontSize: 'var(--type-h1, 2.25rem)' }" v-html="title"></h1>
            </div>
            <div v-if="subtitle" class="overflow-hidden">
              <p class="text-text-secondary text-lg" :style="{ fontSize: 'var(--type-body, 1.125rem)' }" v-html="subtitle"></p>
            </div>
          </slot>
        </div>
        <div v-if="isMobile" class="w-full mt-2 mb-2">
          <slot name="left-content" :clicks="currentClick"></slot>
        </div>
        <HorizontalDivider v-if="hasHeadline" class="w-full mt-2" />
      </div>

      <!-- ВАРИАНТ 2: ROW LAYOUT (Вертикально слева) -->
      <div v-if="!bare && (title || subtitle || $slots.header) && effectiveLayout === 'row'" 
           class="flex-1 flex flex-col justify-center text-left px-8 z-10 h-full relative">
        <slot name="header">
            <div v-if="title" class="overflow-hidden">
              <h1 class="text-4xl font-heading mb-2 leading-tight inline" :style="{ fontSize: 'var(--type-h1, 2.25rem)' }" v-html="title"></h1>
            </div>
            <div v-if="subtitle" class="overflow-hidden">
              <p class="text-text-secondary text-lg mb-4" :style="{ fontSize: 'var(--type-body, 1.125rem)' }" v-html="subtitle"></p>
            </div>
        </slot>
        <slot name="left-content" :clicks="currentClick"></slot>
      </div>

      <VerticalDivider v-if="!bare && effectiveLayout === 'row' && hasHeadline" class="h-3/4" />

      <!-- FULL-BLEED (сцена): сцена рисует весь кадр сама -->
      <div v-if="bare" class="absolute inset-0 z-0">
        <slot v-if="isActive" :clicks="currentClick"></slot>
      </div>

      <!-- УНИФИЦИРОВАННЫЙ КОНТЕНТ (строго по центру оставшегося места) -->
      <div v-else class="flex-1 min-h-0 w-full flex items-center justify-center relative z-0" 
           :class="effectiveLayout === 'row' ? 'px-8' : ''">
        <slot :clicks="currentClick"></slot>
      </div>
      
    </div>
  </Transition>
</template>

<script setup>
import { inject, computed, onMounted, ref, provide, onUnmounted } from 'vue'
import HorizontalDivider from '../ui/HorizontalDivider.vue'
import VerticalDivider from '../ui/VerticalDivider.vue'
import { useDirector } from '../../composables/useDirector'
import { useVariant } from '../../composables/useVariant'

const isHeadless = typeof window !== 'undefined' && window.navigator.webdriver

const { slug: variantSlug, surfaceVars } = useVariant()

// Фон слайда. По умолчанию ПРОЗРАЧНЫЙ: цвет/градиент/иллюстрация/шум рисует контейнер
// (.slides-container) СЛОЯМИ, и слои сцены (bg-image → bg-decorations → bg-overlay)
// должны быть видны, а не перекрываться непрозрачной «стеной» слайда (STYLE-ENFORCEMENT R2).
// Шахматка — явный opt-in override поверх сцены.
const slideChessboard = inject('slideChessboard', ref(false))
const slideBgStyle = computed(() => slideChessboard.value
  ? { background: `var(--slide-bg-${(Number(props.index) % 4) + 1})` }
  : { background: 'transparent' })

const props = defineProps({
  index: {
    type: Number,
    required: true
  },
  clicks: {
    type: Number,
    default: 0
  },
  layout: {
    type: String,
    default: 'col',
    // effectiveLayout нормализует любое значение → 'col' | 'row'
    // валидатор не ограничиваем: layout:'default' в БД — легаси-значение
  },
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  folder: {
    type: String,
    default: 'main'
  },
  startTime: {
    type: Number,
    default: 0
  },
  // Сцена рисует весь кадр сама: без заголовка, паддингов и стандартного контентного слоя.
  bare: {
    type: Boolean,
    default: false
  }
})

const currentSlide = inject('currentSlide')
const currentClick = inject('currentClick')
const currentFolder = inject('currentFolder', ref('main'))
const registerClicks = inject('registerClicks', () => {})
const isMobile = inject('isMobile', ref(false))

const { currentTime } = useDirector()

// Поддержка динамического изменения лейаута из дочерних компонентов
const dynamicLayout = ref(null)
const setSlideLayout = (layout) => {
  dynamicLayout.value = layout
}
provide('setSlideLayout', setSlideLayout)

// Главная унификация анимаций: относительное время слайда (с момента его начала)
const relativeTime = computed(() => {
  if (currentTime.value < props.startTime) return 0
  return currentTime.value - props.startTime
})
provide('relativeTime', relativeTime)

onMounted(() => {
  // Регистрируем клики только если слайд относится к текущей папке
  if (props.folder === currentFolder.value) {
    registerClicks(props.index, props.clicks)
  }
})

const isActive = computed(() => currentSlide.value === props.index && currentFolder.value === props.folder)

// Разделители показываем только когда есть видимый title/subtitle (без HTML-тегов и пробелов).
const hasHeadline = computed(() => {
  const titleText = String(props.title || '').replace(/<[^>]*>/g, '').trim()
  const subtitleText = String(props.subtitle || '').replace(/<[^>]*>/g, '').trim()
  return titleText.length > 0 || subtitleText.length > 0
})

// Заголовок и подзаголовок — статичные, без анимаций (печатание убрано).
// Анимированной остаётся только градиентная полоса-разделитель (HorizontalDivider).

const effectiveLayout = computed(() => {
  if (isMobile.value) return 'col'
  if (dynamicLayout.value) return dynamicLayout.value // Динамический приоритет
  if (['col', 'row'].includes(props.layout)) return props.layout
  return 'col'
})
</script>
