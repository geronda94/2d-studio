<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  columns: { type: Array, default: () => [] },
  reference: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ScriptureParallel')
const relativeTime = inject('relativeTime', ref(0))

const cols = computed(() => props.columns || [])
const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)

const gridTemplate = computed(() => {
  const n = Math.max(1, Math.min(cols.value.length || 1, 3))
  return props.mobile ? '1fr' : `repeat(${n}, minmax(0, 1fr))`
})

const reveal = (item, i, y = 14) => {
  const start = item?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
}

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
  padding: 'var(--item-padding)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars, ...itemPrimaryVars }">
    <div v-if="!cols.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="shrink-0 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 mb-3">
        <Icon icon="lucide:layers" class="w-4 h-4 shrink-0" :style="{ color: getHexColor('var(--color-secondary)') }" />
        <span
          v-if="reference"
          class="px-2.5 py-0.5 text-[11px] md:text-xs font-mono font-bold"
          :style="{
            color: getHexColor('var(--color-secondary)'),
            background: getColorAlpha('var(--color-secondary)', 0.14),
            borderRadius: '999px',
            border: '1px solid ' + getColorAlpha('var(--color-secondary)', 0.4),
          }"
        >{{ reference }}</span>
      </div>

      <div class="flex-1 min-h-0 overflow-auto">
        <div class="grid gap-3 md:gap-4 h-full" :style="{ gridTemplateColumns: gridTemplate }">
          <div
            v-for="(col, i) in cols"
            :key="col.label ?? i"
            class="flex flex-col min-w-0 min-h-0"
            :style="[cardStyle, reveal(col, i)]"
          >
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="w-2.5 h-2.5 rounded-full shrink-0"
                :style="{ background: accent(i), boxShadow: '0 0 0 3px ' + getColorAlpha(accent(i), 0.18) }"
              ></span>
              <p class="font-mono text-[11px] md:text-xs font-bold uppercase tracking-wider truncate" :style="{ color: accent(i) }">{{ col.label }}</p>
            </div>
            <div class="flex-1 min-h-0 flex items-center">
              <p
                class="mt-3 font-sans text-text-primary leading-relaxed"
                :style="{ fontSize: mobile ? '1rem' : '1.5rem' }"
              >{{ col.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
