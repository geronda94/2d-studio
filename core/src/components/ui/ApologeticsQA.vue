<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  items: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ApologeticsQA')
const relativeTime = inject('relativeTime', ref(0))

const accent = getHexColor('var(--color-secondary)')
const success = getHexColor('var(--color-success)')

const reveal = (t, y = 12) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * y).toFixed(2)}px)` }
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
</script>

<template>
  <div
    class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-2"
    :style="{ ...itemVars, ...itemPrimaryVars }"
  >
    <div
      v-if="!items.length"
      class="flex-1 flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div
      v-else
      class="flex-1 min-h-0 overflow-hidden grid gap-2 md:gap-3 content-start"
      :class="mobile ? 'grid-cols-1' : 'grid-cols-2'"
    >
      <article
        v-for="(it, i) in items"
        :key="'qa' + i"
        class="min-h-0 px-3 py-2.5 flex flex-col gap-1.5"
        :style="[itemStyle, reveal(it.start_time ?? i * motion.stagger_ms, 10)]"
      >
        <div class="flex items-start gap-2">
          <span
            class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
            :style="{ background: getColorAlpha(accent, 0.16) }"
          >
            <Icon icon="lucide:message-circle-question" class="w-3 h-3" :style="{ color: accent }" />
          </span>
          <div class="min-w-0">
            <span class="block text-[9px] font-mono uppercase tracking-widest text-text-muted">Возражение</span>
            <span class="block text-text-primary text-xs md:text-sm font-medium leading-snug">{{ it.objection }}</span>
          </div>
        </div>

        <div class="h-px w-full" :style="{ background: 'var(--item-border)' }"></div>

        <div class="flex items-start gap-2">
          <span
            class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
            :style="{ background: getColorAlpha(success, 0.16) }"
          >
            <Icon icon="lucide:check-circle" class="w-3 h-3" :style="{ color: success }" />
          </span>
          <div class="min-w-0">
            <span class="block text-[9px] font-mono uppercase tracking-widest text-text-muted">Ответ</span>
            <span class="block text-text-secondary text-xs leading-snug">{{ it.answer }}</span>
            <span v-if="it.source" class="block text-[10px] font-mono text-text-muted mt-1">{{ it.source }}</span>
          </div>
        </div>
      </article>
    </div>

    <p
      v-if="source_note"
      class="shrink-0 text-center text-[10px] font-mono text-text-muted opacity-70"
    >{{ source_note }}</p>
  </div>
</template>
