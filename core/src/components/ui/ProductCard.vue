<script setup>
import { getColorAlpha } from '../../utils/colors'
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  defaultDelay: { type: Number, default: 200 },
  items: {
    type: Array,
    default: () => [
      {
        id: 'pc1',
        variant: 'pricing',
        title: 'Starter AI',
        price: '49 €',
        period: '/мес',
        features: ['1 Агент', 'Базовые API', 'Поддержка email'],
        btn_text: 'Начать',
        start_time: 0
      },
      {
        id: 'pc2',
        variant: 'pricing',
        badge: 'Популярно',
        title: 'Pro Team',
        price: '199 €',
        period: '/мес',
        features: ['10 Агентов', 'Доступ к GPT-5', 'Выделенный сервер'],
        btn_text: 'Купить',
        btn_icon: 'heroicons:rocket-launch',
        accent_color: 'var(--color-secondary)',
        border_color: 'rgb(var(--color-secondary-rgb) / 0.3)',
        highlight: true,
        start_time: 1000
      },
      {
        id: 'pc3',
        variant: 'photo',
        image: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=800',
        badge: 'UI/UX',
        title: 'Умный Дашборд',
        desc: 'Следите за всеми агентами в реальном времени',
        btn_text: 'Смотреть демо',
        btn_icon: 'heroicons:play',
        accent_color: 'var(--color-primary)',
        start_time: 2000
      },
      {
        id: 'pc4',
        variant: 'photo',
        image: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&q=80&w=800',
        title: 'API Доступ',
        desc: 'Интегрируйте нейросети в любой продукт за 5 минут',
        btn_text: 'Документация',
        btn_icon: 'heroicons:document-text',
        accent_color: 'var(--color-success)',
        start_time: 3000
      }
    ]
  }
})

const relativeTime = inject('relativeTime', ref(0))

const { itemVars } = useVariant(computed(() => props.variant), 'ProductCard')

const imgFailed = ref({})

// Return only items that have spawned
const visibleItems = computed(() => {
  return props.items.filter((item, idx) => {
    const threshold = item.start_time ?? (idx * props.defaultDelay)
    return relativeTime.value >= threshold
  })
})

const resolveColor = (c) => {
  if (!c) return 'var(--color-primary)'
  const lower = c.toLowerCase()
  // Маппим старые захардкоженные HEX-цвета из seed_components на токены темы,
  // чтобы карточки автоматически адаптировались под исторический/светлый стиль.
  if (lower === '#38bdf8' || lower === 'var(--color-secondary)') return 'var(--color-secondary)'
  if (lower === '#ec4899') return 'var(--color-accent-2)'
  if (lower === '#10b981') return 'var(--color-success)'
  return c
}

const isCompact = computed(() => {
  const count = visibleItems.value.length;
  if (props.mobile && count >= 2) return true;
  if (!props.mobile && count >= 4) return true;
  return false;
})

const getDesktopItemWidth = (count) => {
  if (count === 1) return 'max-w-md' // 448px
  if (count === 2) return 'max-w-[360px]'
  if (count === 3) return 'max-w-[300px]'
  return 'max-w-[260px]' // 4 cards
}

const getMobileGridClass = (count) => {
  if (count <= 2) return 'grid-cols-1 max-w-sm mx-auto'
  return 'grid-cols-2'
}

// Кнопка залита акцентом у выделенных тарифов и у медиа-карточек.
const isFilled = (item) => item.highlight || item.variant === 'photo' || !!item.btn_bg_color

const getDynamicStyles = (item, idx) => {
  const threshold = item.start_time ?? (idx * props.defaultDelay)
  const duration = 500
  const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))

  if (progress === 0) return { opacity: 0, transform: 'scale(0.9) translateY(20px)', willChange: 'opacity, transform' }
  if (progress === 1) {
    return {
      opacity: 1,
      transform: 'scale(1) translateY(0px)',
      willChange: 'auto',
      backgroundColor: item.bg_color || 'var(--item-bg)',
      backdropFilter: 'var(--item-backdrop)',
      boxShadow: 'var(--item-shadow)',
      borderColor: item.border_color || (item.highlight ? resolveColor(item.accent_color) : 'var(--item-border)')
    }
  }

  // easeOutQuart approximate
  const ease = 1 - Math.pow(1 - progress, 4)

  return {
    opacity: ease.toFixed(4),
    transform: `scale(${(0.9 + (0.1 * ease)).toFixed(4)}) translateY(${((1 - ease) * 20).toFixed(4)}px)`,
    willChange: 'opacity, transform',
    backgroundColor: item.bg_color || 'var(--item-bg)',
    backdropFilter: 'var(--item-backdrop)',
    boxShadow: 'var(--item-shadow)',
    borderColor: item.border_color || (item.highlight ? resolveColor(item.accent_color) : 'var(--item-border)')
  }
}
</script>

<template>
  <div class="w-full relative"
    :class="[
      mobile
        ? `grid gap-3 w-full content-center ${getMobileGridClass(visibleItems.length)}`
        : 'flex flex-row items-stretch justify-center gap-5 w-full h-full'
    ]"
    :style="{ ...itemVars }">

    <div v-for="(item, idx) in visibleItems" :key="item.id || idx"
      class="relative group flex flex-col origin-center overflow-hidden"
      :class="[
        mobile ? '' : `flex-1 min-w-0 ${getDesktopItemWidth(visibleItems.length)}`
      ]"
      :style="{
        ...getDynamicStyles(item, idx),
        borderRadius: 'var(--item-radius)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)'
      }">

      <!-- ЕДИНЫЙ МЕДИА-ЗАГОЛОВОК (картинка или стилизованный плейсхолдер) -->
      <div class="relative w-full shrink-0 overflow-hidden" :class="mobile ? 'h-16' : 'h-28'">
        <img
          v-if="item.image && !imgFailed[item.id || idx]"
          :src="item.image"
          class="absolute inset-0 w-full h-full object-cover"
          @error="imgFailed[item.id || idx] = true"
        />
        <div
          v-else
          class="absolute inset-0 flex items-center justify-center"
          :style="{ background: `linear-gradient(150deg, ${getColorAlpha(resolveColor(item.accent_color), 0.3)}, transparent 70%), var(--item-primary-bg)` }"
        >
          <div
            class="flex items-center justify-center"
            :class="mobile ? 'w-9 h-9' : 'w-12 h-12'"
            :style="{
              borderRadius: 'var(--item-radius)',
              background: getColorAlpha(resolveColor(item.accent_color), 0.16),
              border: '1px solid ' + getColorAlpha(resolveColor(item.accent_color), 0.4),
            }"
          >
            <Icon
              :icon="item.icon || (item.variant === 'photo' ? 'heroicons:photo' : 'heroicons:sparkles')"
              :class="mobile ? 'w-4 h-4' : 'w-6 h-6'"
              :style="{ color: resolveColor(item.accent_color) }"
            />
          </div>
        </div>
        <div
          class="absolute inset-x-0 top-0 h-10 pointer-events-none"
          :style="{ background: 'linear-gradient(to bottom, rgb(var(--bg-base-rgb) / 0.45), transparent)' }"
        ></div>
        <div
          v-if="item.badge"
          class="absolute top-2.5 left-2.5 rounded-full font-bold uppercase tracking-wider px-2.5 py-1 text-[9px]"
          :style="{ color: 'var(--text-primary)', backgroundColor: 'rgb(var(--bg-base-rgb) / 0.7)' }"
        >
          {{ item.badge }}
        </div>
      </div>

      <!-- ТЕЛО КАРТОЧКИ -->
      <div class="relative z-10 flex flex-col flex-1 min-h-0" :style="{ padding: 'var(--item-padding)' }">
        <h3 class="font-heading font-bold text-text-primary leading-tight" :class="isCompact ? 'text-sm mb-1' : 'text-lg mb-1'">
          {{ item.title }}
        </h3>

        <div v-if="item.price" class="flex items-baseline gap-1" :class="isCompact ? 'mb-2' : 'mb-3'">
          <span class="font-black text-text-primary" :class="isCompact ? 'text-2xl' : 'text-4xl'">{{ item.price }}</span>
          <span v-if="item.period" class="text-text-muted" :class="isCompact ? 'text-[9px]' : 'text-xs'">{{ item.period }}</span>
        </div>

        <div class="h-[1px] w-full shrink-0" :class="isCompact ? 'mb-2' : 'mb-3'" :style="{ backgroundColor: 'var(--item-border)' }"></div>

        <div class="flex-1 min-h-0 flex flex-col justify-center">
          <ul v-if="item.features && item.features.length" :class="isCompact ? 'space-y-1.5' : 'space-y-2'">
            <li v-for="(feat, i) in item.features" :key="i" class="flex items-start gap-2">
              <div
                class="rounded-full flex items-center justify-center shrink-0 mt-0.5"
                :class="isCompact ? 'w-3.5 h-3.5' : 'w-5 h-5'"
                :style="{ backgroundColor: item.highlight ? getColorAlpha(resolveColor(item.accent_color), 0.2) : getColorAlpha('var(--text-primary)', 0.05) }"
              >
                <Icon
                  icon="heroicons:check"
                  :class="isCompact ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'"
                  :style="{ color: item.highlight ? resolveColor(item.accent_color) : getColorAlpha('var(--text-primary)', 0.4) }"
                />
              </div>
              <span class="text-text-primary leading-tight" :class="isCompact ? 'text-[10px]' : 'text-[13px]'">{{ feat }}</span>
            </li>
          </ul>
          <p
            v-else
            class="text-text-secondary leading-snug line-clamp-3"
            :class="isCompact ? 'text-[10px]' : 'text-sm'"
          >{{ item.desc }}</p>
        </div>

        <button
          v-if="item.btn_text || item.btn_icon"
          class="w-full shrink-0 font-bold mt-3 flex items-center justify-center gap-2"
          :class="isCompact ? 'py-2 text-[11px]' : 'py-3 text-sm'"
          :style="[ { borderRadius: 'calc(var(--item-radius) - 2px)' }, isFilled(item)
            ? { backgroundColor: item.btn_bg_color || resolveColor(item.accent_color), color: item.btn_text_color || 'var(--text-on-color)' }
            : { backgroundColor: getColorAlpha('var(--text-primary)', 0.05), color: item.btn_text_color || 'var(--text-primary)', borderColor: 'var(--item-border)', borderWidth: '1px' } ]"
        >
          <Icon v-if="item.btn_icon" :icon="item.btn_icon" :class="isCompact ? 'w-3 h-3' : 'w-4 h-4'" />
          {{ item.btn_text }}
        </button>
      </div>
    </div>
  </div>
</template>
