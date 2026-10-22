<script setup>
// ─────────────────────────────────────────────────────────────────────────────
// PortraitLampSlide — портрет в арочном окладе с подвесной лампадкой.
// Перенос элемента прототипа Diademas (HeaderIndex + LampAnimation) в движок.
//
// Канон:
//  • Данные только из props (payload), без хардкода текста/медиа.
//  • Анимации детерминированы от relativeTime (§11): «бегущий» градиент оклада —
//    позиция фона от времени; лампадка — во внутреннем Lampada.vue.
//  • Стили/цвета — токены палитры + useVariant (форма/материал оклада).
// ─────────────────────────────────────────────────────────────────────────────
import { computed, inject, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import Lampada from '../ui/Lampada.vue'

const props = defineProps({
  // Системные
  mobile: Boolean,
  clicks: { type: Number, default: 0 },
  slideStartTime: { type: Number, default: 0 },

  // Payload
  variant: { type: String, default: undefined },
  image: { type: String, default: '' },
  name: { type: String, default: '' },
  caption: { type: String, default: '' },
  description: { type: String, default: '' },
  lamp: { type: Boolean, default: true },
  lamp_color: { type: String, default: 'color-primary' },
  flame_color: { type: String, default: 'color-warning' },
  image_position: { type: String, default: 'center 20%' },
})

const { itemVars } = useVariant(computed(() => props.variant), 'PortraitLampSlide')
const relativeTime = inject('relativeTime', ref(0))

// Fallback на иконку, если портрет не задан или ссылка битая (без битых изображений).
const imageBroken = ref(false)
watch(() => props.image, () => { imageBroken.value = false })

// Осмысленный плейсхолдер вместо пустого оклада: инициалы из name (данные из props).
const initials = computed(() => {
  const parts = String(props.name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return ''
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
})

// «Бегущий» блик оклада — через transform (композитор), НЕ через background-position:
// в софтверном рендере (--disable-gpu) смена позиции фона = перерисовка каждый кадр.
const sheenX = computed(() => {
  const p = (relativeTime.value / 4500) % 1 // 0..1
  return (-120 + p * 240).toFixed(1)         // -120% .. 120%
})

const frameStyle = computed(() => ({
  background:
    'linear-gradient(var(--item-bg), var(--item-bg)) padding-box, var(--gradient-text) border-box',
  backgroundSize: '100% 100%',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  border: '6px solid transparent',
  boxShadow: 'var(--item-shadow)',
}))

</script>

<template>
  <div
    class="w-full h-full flex"
    :class="mobile ? 'flex-col items-center gap-2' : 'flex-row items-center justify-center gap-8'"
    :style="{ ...itemVars }"
  >
    <!-- Портрет в арочном окладе + лампадка (лампадка в потоке → группа центрируется целиком) -->
    <div
      class="relative flex flex-col items-center justify-center"
      :class="mobile ? 'w-full mt-2' : 'shrink-0'"
    >
      <div
        class="portrait-frame relative overflow-hidden"
        :class="mobile ? 'w-[220px] h-[293px]' : 'w-[225px] h-[300px]'"
        :style="frameStyle"
      >
        <img
          v-if="image && !imageBroken"
          :src="image"
          alt=""
          class="w-full h-full object-cover"
          :style="{ objectPosition: image_position }"
          @error="imageBroken = true"
        />
        <!-- Пустое состояние: инициалы из имени (данные) вместо битой картинки/текста-заглушки -->
        <div v-else class="portrait-empty absolute inset-0 flex items-center justify-center">
          <span
            v-if="initials"
            class="font-heading font-bold leading-none select-none"
            :style="{
              fontSize: mobile ? '4.5rem' : '7.5rem',
              background: 'var(--gradient-text)',
              backgroundSize: '100% 100%',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              color: 'transparent',
            }"
          >{{ initials }}</span>
          <Icon v-else icon="lucide:user-round" class="w-[42%] h-[42%]" :style="{ color: 'var(--item-border)' }" />
        </div>
        <!-- Блик: движется transform'ом (композитор), не трогает paint -->
        <div class="portrait-sheen" :style="{ transform: `translateX(${sheenX}%)` }"></div>
      </div>

      <!-- Лампадка по центру ПОД портретом (цепочки уходят под оклад) -->
      <div
        v-if="lamp"
        class="relative z-10 shrink-0"
        :class="mobile ? '-mt-6' : '-mt-20'"
      >
        <Lampada :color="lamp_color" :flame_color="flame_color" :scale="mobile ? 1 : 1.15" />
      </div>
    </div>

    <!-- Текст -->
    <div
      class="flex flex-col min-w-0 shrink-0"
      :class="mobile ? 'items-center text-center px-4 mt-1' : 'items-start text-left max-w-[440px]'"
    >
      <div
        v-if="caption"
        class="uppercase tracking-[0.28em] font-heading mb-1.5"
        :style="{ color: 'var(--color-secondary)', fontSize: mobile ? '0.8rem' : '0.75rem' }"
      >
        {{ caption }}
      </div>
      <h2
        v-if="name"
        class="font-heading font-bold leading-[1.08] mb-3"
        :style="{
          fontSize: mobile ? '1.9rem' : 'var(--type-display, 3.5rem)',
          background: 'var(--gradient-text)',
          backgroundSize: '100% 100%',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          color: 'transparent',
        }"
      >
        {{ name }}
      </h2>
      <p
        v-if="description"
        class="font-sans leading-relaxed"
        :style="{ color: 'var(--text-secondary)', fontSize: mobile ? '0.95rem' : 'var(--type-body, 1.125rem)' }"
      >
        {{ description }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.portrait-frame {
  border-radius: 50% 50% 10px 10px;
}
.portrait-empty {
  background: radial-gradient(circle at 50% 35%, color-mix(in srgb, var(--text-muted) 14%, transparent), transparent 70%);
}
.portrait-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 55%;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.12), transparent);
  will-change: transform;
}
</style>
