<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// ШАБЛОН НОВОГО КОМПОНЕНТА (копируй и заполняй содержимое).
// Это каноническая заготовка «список айтемов с последовательным появлением»
// (самый частый паттерн: карточки, списки, чеклисты, статистика).
//
// ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА (см. AGENTS.md):
//  1. Данные — только из props (payload), НИКАКОГО хардкода текста/медиа.
//  2. Анимации — детерминированы от relativeTime (без rAF / CSS infinite / <animate>).
//  3. Стили — через токены (var(--...)) и вариант (useVariant), не хардкод цветов.
//  4. Регистрация: добавить slug в core/src/config/componentsRegistry.js
//     и запись в scripts/seed_components.py, затем перегенерировать схемы.
// ─────────────────────────────────────────────────────────────────────────────
import { computed, inject, ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
const props = defineProps({
  // Системные пропсы (передаются движком, НЕ из payload):
  mobile: Boolean,
  clicks: { type: Number, default: 0 },
  slideStartTime: { type: Number, default: 0 },

  // ── Поля payload (объявляй под ключи из default_payload) ──
  items: { type: Array, default: () => [] },
  // variant: String,   // раскомментируй, если компонент поддерживает варианты отрисовки
})

// Вариант отрисовки (форма/материал айтемов). Даёт CSS-переменные --item-* / --item-primary-*.
// Если компонент не имеет variant — удали эти строки и задай стили токенами напрямую.
const { itemVars, itemPrimaryVars } = useVariant(computed(() => props.variant))

// Локальное время слайда (мс от его старта). Все появления/анимации — от него.
const relativeTime = inject('relativeTime', ref(0))

// Показываем только те айтемы, чей start_time уже наступил.
const visibleItems = computed(() =>
  (props.items || []).filter(it => relativeTime.value >= (it.start_time ?? 0))
)
</script>

<template>
  <!-- Корень: применяем CSS-переменные варианта на весь сабтри компонента -->
  <div class="w-full h-full flex items-center justify-center" :style="{ ...itemVars, ...itemPrimaryVars }">
    <TransitionGroup
      name="fade-slide"
      tag="div"
      class="flex flex-wrap items-center justify-center gap-4 w-full"
    >
      <div
        v-for="(item, i) in visibleItems"
        :key="item.id ?? i"
        class="transition-all duration-base"
        :style="{
          background: 'var(--item-bg)',
          backdropFilter: 'var(--item-backdrop)',
          borderRadius: 'var(--item-radius)',
          boxShadow: 'var(--item-shadow)',
          padding: 'var(--item-padding)',
          gap: 'var(--item-gap)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
        }"
      >
        <!-- Здесь — контент айтема из props (title/subtitle/icon/...), без хардкода -->
        <div class="font-heading font-bold text-text-primary leading-tight">{{ item.title }}</div>
        <div v-if="item.subtitle" class="text-text-secondary text-sm">{{ item.subtitle }}</div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Анимация появления/перестановки (обязательно .fade-slide-move для плавного сдвига соседей) */
.fade-slide-move,
.fade-slide-enter-active {
  transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.fade-slide-leave-active {
  position: absolute;
}
</style>
