<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  before: { type: Object, default: () => ({}) },
  after: { type: Object, default: () => ({}) },
  transition_style: { type: String, default: 'slide' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'HistoricalCompare')
const relativeTime = inject('relativeTime', ref(0))

const imgFailed = ref({})

const reveal = (t, dur) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (t ?? 0)) / dur))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 22).toFixed(2)}px)` }
}

const beforeTime = computed(() => props.before?.start_time ?? 0)
const afterTime = computed(() => props.after?.start_time ?? 1200)

const panelOffset = (side) => {
  if (props.transition_style !== 'slide' || props.mobile) return '0px'
  if (side === 'before') {
    const p = Math.max(0, Math.min(1, relativeTime.value / motion.value.appear_ms))
    return `${((1 - p) * -40).toFixed(2)}px`
  }
  const p = Math.max(0, Math.min(1, (relativeTime.value - afterTime.value) / motion.value.appear_ms))
  return `${((1 - p) * 40).toFixed(2)}px`
}

const arrowReveal = computed(() => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - afterTime.value) / motion.value.appear_ms))
  return { opacity: (1 - Math.pow(1 - p, 3)).toFixed(3) }
})

const sideData = (side) => (side === 'before' ? props.before : props.after) || {}
const showImage = (side) => !!sideData(side).image && !imgFailed.value[side]

// Токен-акцент стороны: «Раньше» — предупреждение, «Теперь» — успех.
const sideToken = (side) => (side === 'before' ? 'var(--color-warning)' : 'var(--color-success)')
const sideIcon = (side) => (side === 'before' ? 'lucide:hourglass' : 'lucide:rocket')
</script>

<template>
  <div
    class="w-full h-full min-h-0 grid items-stretch gap-4 md:gap-5"
    :style="{ ...itemVars, gridTemplateColumns: mobile ? '1fr' : '1fr auto 1fr' }"
  >
    <template v-for="side in ['before', 'after']" :key="side">
      <div
        v-if="side === 'after' && !mobile"
        class="flex items-center justify-center"
        :style="arrowReveal"
      >
        <div class="w-10 h-10 rounded-full flex items-center justify-center" :style="{ background: getHexColor('var(--color-secondary)'), color: 'var(--text-on-color)' }">
          <Icon icon="heroicons:arrow-right" class="w-5 h-5" />
        </div>
      </div>

      <div
        class="flex flex-col overflow-hidden min-h-0"
        :style="[
          reveal(side === 'before' ? beforeTime : afterTime, motion.appear_ms),
          {
            transform: `translateX(${panelOffset(side)})`,
            height: mobile ? '100%' : undefined,
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          },
        ]"
      >
        <div class="relative w-full flex-1 min-h-0 overflow-hidden" :style="{ background: 'var(--item-primary-bg)', backdropFilter: 'var(--item-primary-backdrop)', WebkitBackdropFilter: 'var(--item-primary-backdrop)' }">
          <img
            v-if="showImage(side)"
            :src="sideData(side).image"
            class="absolute inset-0 w-full h-full object-cover"
            @error="imgFailed[side] = true"
          />
          <div
            v-else
            class="absolute inset-0 flex items-center justify-center overflow-hidden"
            :style="{ background: `linear-gradient(155deg, ${getColorAlpha(sideToken(side), 0.22)}, transparent 62%), var(--item-primary-bg)` }"
          >
            <span
              class="absolute rounded-full pointer-events-none"
              :style="{ width: '220px', height: '220px', border: '1px solid ' + getColorAlpha('var(--text-primary)', 0.05) }"
            ></span>
            <span
              class="absolute rounded-full pointer-events-none"
              :style="{ width: '150px', height: '150px', border: '1px solid ' + getColorAlpha('var(--text-primary)', 0.07) }"
            ></span>
            <span
              class="relative w-20 h-20 flex items-center justify-center"
              :style="{ borderRadius: 'calc(var(--item-radius) + 8px)', background: getColorAlpha(sideToken(side), 0.14), border: '1px solid ' + getColorAlpha(sideToken(side), 0.4), boxShadow: 'var(--item-shadow)' }"
            >
              <Icon :icon="sideIcon(side)" class="w-10 h-10" :style="{ color: getHexColor(sideToken(side)) }" />
            </span>
          </div>
          <div
            class="absolute top-3 left-3 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest"
            :style="side === 'before'
              ? { background: getColorAlpha('var(--color-warning)', 0.9), color: 'var(--text-on-color)' }
              : { background: getHexColor('var(--color-success)'), color: 'var(--text-on-color)' }"
          >
            {{ sideData(side).label || (side === 'before' ? 'До' : 'После') }}
          </div>
        </div>
        <div class="shrink-0 flex items-center p-4 md:p-5">
          <p class="text-text-primary text-sm md:text-lg leading-relaxed">{{ sideData(side).caption }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
