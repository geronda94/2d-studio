<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  soils: { type: Array, default: () => [] },
  reference: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'SeedAndSoil')
const relativeTime = inject('relativeTime', ref(0))

const accent = (s, i) => getHexColor(s.color || `var(--item-accent-${(i % 4) + 1})`)

const maxLevel = computed(() => {
  const vals = (props.soils || []).map((s) => Number(s.level) || 0)
  return Math.max(0.0001, ...vals)
})

const progress = (s, i) => {
  const t = s.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

// Нормируем высоту столбика к максимальному level и держим нижнюю границу —
// иначе «при дороге» (0.15) выглядит почти невидимой чёрточкой.
// sqrt-кривая растягивает низ шкалы, чтобы малые уровни читались.
const grow = (s, i) => {
  const lvl = Math.min(1, Math.max(0, (Number(s.level) || 0) / maxLevel.value))
  return progress(s, i) * Math.max(0.28, Math.pow(lvl, 0.6))
}

// «—» в yield не показываем: это не значение, а заглушка (иначе «бесхозные чёрточки»).
const hasYield = (s) => {
  const y = String(s.yield ?? '').trim()
  return y.length > 0 && y !== '—' && y !== '-'
}

const reveal = (s, i) => {
  const e = progress(s, i)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const referenceStyle = computed(() => {
  const t = props.soils.length * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4) }
})
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div class="flex-1 min-h-0 overflow-hidden">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-2.5 md:gap-3 h-full min-h-0">
        <div
          v-for="(s, i) in soils"
          :key="s.type || i"
          class="relative flex flex-col items-center px-2.5 md:px-3 pt-3 pb-3.5 h-full min-h-0 overflow-hidden"
          :style="[itemStyle, reveal(s, i)]"
        >
          <span v-if="hasYield(s)" class="text-[10px] md:text-xs font-mono mb-2" :style="{ color: accent(s, i) }">
            {{ s.yield }}
          </span>

          <div class="relative flex-1 min-h-0 w-8 md:w-10 flex flex-col justify-end">
            <div
              class="w-full rounded-t-full origin-bottom"
              :style="{
                height: '100%',
                transform: `scaleY(${grow(s, i).toFixed(4)})`,
                background: `linear-gradient(to top, ${getColorAlpha(accent(s, i), 0.25)}, ${getColorAlpha(accent(s, i), 0.9)})`,
              }"
            ></div>
          </div>

          <span
            class="mt-2 w-9 h-9 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0"
            :style="{ background: getColorAlpha(accent(s, i), 0.14), border: '1px solid ' + accent(s, i) }"
          >
            <Icon :icon="s.icon || 'lucide:sprout'" class="w-4 h-4 md:w-5 md:h-5" :style="{ color: accent(s, i) }" />
          </span>

          <p
            class="mt-1.5 font-heading font-bold text-text-primary text-center leading-tight"
            :class="mobile ? 'text-xs' : 'text-sm'"
          >{{ s.type }}</p>
          <p v-if="s.outcome" class="mt-1 text-[10px] md:text-[11px] text-text-secondary text-center leading-snug">
            {{ s.outcome }}
          </p>
        </div>
      </div>
    </div>

    <p
      v-if="reference"
      class="mt-2 text-center text-[11px] font-mono text-text-muted opacity-70"
      :style="referenceStyle"
    >{{ reference }}</p>
  </div>
</template>
