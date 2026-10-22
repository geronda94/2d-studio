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
  items: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'OrganicGrid')
const relativeTime = inject('relativeTime', ref(0))

const SPAN = {
  '1x1': { c: 1, r: 1 },
  '1x2': { c: 1, r: 2 },
  '2x1': { c: 2, r: 1 },
  '2x2': { c: 2, r: 2 },
  '3x2': { c: 3, r: 2 },
  '4x2': { c: 4, r: 2 },
}

const spanStyle = (item, idx) => {
  const s = SPAN[item.size] || (idx === 0 ? SPAN['2x2'] : SPAN['1x1'])
  if (props.mobile) return {}
  return { gridColumn: `span ${Math.min(s.c, 4)}`, gridRow: `span ${s.r}` }
}

const itemStyle = (item, idx) => {
  const t = item.start_time ?? idx * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  const s = SPAN[item.size] || {}
  const mod = (s.r || 1) >= 2 ? 1.03 : 1
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 22).toFixed(2)}px) scale(${(0.95 + 0.05 * e * mod).toFixed(4)})` }
}

const accent = (item, idx) => getHexColor(item.color || `var(--item-accent-${(idx % 4) + 1})`)

const big = (item) => ['2x2', '3x2', '4x2'].includes(item.size)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col pb-2" :style="{ ...itemVars }">
    <div v-if="title" class="mb-5 text-center shrink-0">
      <h3 class="font-heading font-bold text-2xl md:text-3xl text-text-primary">{{ title }}</h3>
      <p v-if="subtitle" class="text-text-muted text-sm mt-1">{{ subtitle }}</p>
    </div>

    <div
      class="grid gap-3 flex-1 min-h-0"
      :style="mobile
        ? { gridTemplateColumns: '1fr', gridAutoRows: 'minmax(110px, auto)' }
        : { gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gridAutoRows: 'minmax(0, 1fr)' }"
    >
      <div
        v-for="(item, idx) in items"
        :key="item.id ?? idx"
        class="relative overflow-hidden flex flex-col justify-center"
        :style="[
          spanStyle(item, idx),
          itemStyle(item, idx),
          {
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
            minHeight: mobile ? '110px' : undefined,
          },
        ]"
      >
        <div
          class="absolute inset-0 opacity-[0.16] pointer-events-none"
          :style="{ background: `radial-gradient(circle at 80% 20%, ${getColorAlpha(accent(item, idx), 0.6)}, transparent 70%)` }"
        ></div>

        <Icon
          v-if="item.icon"
          :icon="item.icon"
          class="absolute -bottom-3 -right-2 pointer-events-none opacity-[0.14]"
          :class="big(item) ? 'w-32 h-32' : 'w-20 h-20'"
          :style="{ color: accent(item, idx) }"
        />

        <div class="relative z-10">
          <div class="flex items-center gap-2 mb-1 md:mb-2">
            <span v-if="item.icon" class="flex items-center justify-center shrink-0" :class="big(item) ? 'w-9 h-9' : 'w-6 h-6'" :style="{ background: getColorAlpha(accent(item, idx), 0.15), borderRadius: 'calc(var(--item-radius) - 4px)' }">
              <Icon :icon="item.icon" :class="big(item) ? 'w-5 h-5' : 'w-3.5 h-3.5'" :style="{ color: accent(item, idx) }" />
            </span>
            <h4 class="font-heading font-bold text-text-primary" :class="big(item) ? 'text-2xl' : 'text-sm md:text-base'">{{ item.title }}</h4>
          </div>
          <p v-if="item.desc" class="text-text-secondary leading-snug" :class="big(item) ? 'text-base max-w-md' : 'text-xs md:text-sm'">{{ item.desc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
