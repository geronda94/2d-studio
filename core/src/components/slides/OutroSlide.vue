<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <!-- mobile-ветка строится ТОЛЬКО от пропа `mobile`, без Tailwind `md:`:
         в портретном рендере viewport 1080×1920 → media-query «md» активна, хотя
         логический холст 450×800, и md:h-full ломал высоту (аутро не вмещалось). -->
    <div
      class="flex-1 min-h-0 w-full"
      :class="mobile ? 'flex flex-col items-center justify-center gap-5' : 'flex flex-row items-center justify-around gap-8'"
    >

    <!-- Лого (SVG / PNG) — без крупной пустой рамки, только свечение под логотипом -->
    <div
      class="flex items-center justify-center relative min-h-0 min-w-0"
      :class="mobile ? 'w-full shrink-0 h-[210px]' : 'flex-1 h-full'"
      :style="logoStyle"
    >
      <div
        class="absolute inset-0 pointer-events-none"
        :style="{
          background: 'radial-gradient(circle at 50% 50%, rgb(var(--color-secondary-rgb) / 0.22), transparent 68%)',
          filter: 'blur(8px)',
        }"
      ></div>
      <img
        v-if="logo"
        :src="logo"
        alt="logo"
        class="relative w-auto max-w-full max-h-full object-contain drop-shadow-[0_0_30px_rgb(var(--color-secondary-rgb) / 0.45)]"
      />
      <div
        v-else
        class="flex items-center justify-center text-text-muted font-bold"
        :class="mobile ? 'w-24 h-24' : 'w-40 h-40'"
        :style="{
          background: 'var(--item-bg)',
          backdropFilter: 'var(--item-backdrop)',
          borderRadius: 'var(--item-radius)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-border)',
        }"
      >Лого</div>
    </div>

    <!-- Контактный блок (чистая картинка QR-кода без лишних рамок) -->
    <div
      v-if="qr_code || headline || handle"
      class="flex flex-col items-center justify-center relative min-h-0 min-w-0"
      :class="mobile ? 'w-full shrink-0 gap-4' : 'flex-1 h-full gap-4'"
      :style="contactStyle"
    >

      <div v-if="headline" class="text-text-primary font-heading font-bold shrink-0 text-center" :class="mobile ? 'text-xl' : 'text-2xl'">{{ headline }}</div>

      <!-- Чистый QR-код (как загрузили, так и показываем) -->
      <div
        v-if="qr_code"
        class="relative min-h-0 flex items-center justify-center overflow-hidden"
        :class="mobile ? 'h-[280px] w-auto max-w-[80%]' : 'flex-1 max-w-full'"
        :style="{ borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }"
      >
        <img :src="qr_code" alt="QR" class="w-auto max-w-full max-h-full object-contain" />
      </div>

      <!-- Контакт (handle) — только если QR не содержит его сам -->
      <div v-if="handle && !qr_code" class="flex items-center gap-2 text-transparent bg-clip-text bg-gradient-to-r from-color-primary to-color-secondary font-bold shrink-0" :class="mobile ? 'text-xl' : 'text-2xl'">
        <Icon icon="heroicons:at-symbol" class="w-7 h-7 text-color-primary" />
        {{ handle }}
      </div>

    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: Boolean,
  variant: String,
  logo: { type: String, default: '' },
  qr_code: { type: String, default: '' },
  handle: { type: String, default: '' },
  headline: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'OutroSlide')
const relativeTime = inject('relativeTime', ref(0))

const ease = (p) => 1 - Math.pow(1 - Math.max(0, Math.min(1, p)), 3)
const reveal = (delay) => ease((relativeTime.value - delay) / (motion.value.appear_ms || 500))

const logoStyle = computed(() => ({
  opacity: reveal(0).toFixed(3),
  transform: `translateY(${((1 - reveal(0)) * 18).toFixed(1)}px)`,
}))
const contactStyle = computed(() => ({
  opacity: reveal(250).toFixed(3),
  transform: `translateY(${((1 - reveal(250)) * 18).toFixed(1)}px)`,
}))
</script>
