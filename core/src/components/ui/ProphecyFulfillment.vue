<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  prophecies: { type: Array, default: () => [] },
  fulfillments: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ProphecyFulfillment')
const relativeTime = inject('relativeTime', ref(0))

const rows = computed(() => {
  const p = props.prophecies || []
  const f = props.fulfillments || []
  const pairs = props.links && props.links.length ? props.links : p.map((_, i) => ({ from: i, to: i }))
  return pairs
    .map((l, i) => {
      const pr = p[l.from]
      const fu = f[l.to]
      if (!pr || !fu) return null
      return { i, p: pr, f: fu, start: pr.start_time ?? i * motion.value.stagger_ms }
    })
    .filter(Boolean)
})

const prophecyAccent = getHexColor('var(--color-warning)')
const fulfillmentAccent = getHexColor('var(--color-success)')

const reveal = (start, dir, dist = 14) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (start ?? 0)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return {
    opacity: e.toFixed(4),
    transform: `translateX(${((1 - e) * dist * dir).toFixed(2)}px)`,
  }
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
    <div v-if="!rows.length" class="flex-1 min-h-0 flex items-center justify-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="flex-1 min-h-0 flex flex-col gap-2" :class="mobile ? 'overflow-hidden' : 'overflow-y-auto'">
      <div
        v-for="r in rows"
        :key="r.i"
        class="flex-1 min-h-0"
        :class="mobile ? 'flex flex-col gap-2' : 'grid items-stretch gap-2'"
        :style="mobile ? {} : { gridTemplateColumns: '1fr 44px 1fr' }"
      >
        <!-- MOBILE: единая компактная карточка -->
        <div
          v-if="mobile"
          class="min-w-0 flex flex-col gap-1 px-3 py-2"
          :style="[cardStyle, { padding: '8px 10px', borderLeftWidth: '3px', borderLeftColor: prophecyAccent, borderLeftStyle: 'solid' }, reveal(r.start, -1, 0)]"
        >
          <div class="flex items-center gap-1.5">
            <Icon icon="lucide:scroll-text" class="w-3.5 h-3.5 shrink-0" :style="{ color: prophecyAccent }" />
            <span class="font-mono text-[10px] font-bold" :style="{ color: prophecyAccent }">{{ r.p.year }}</span>
            <span class="ml-auto font-mono text-[9px] px-1.5 py-0.5" :style="{ color: prophecyAccent, background: getColorAlpha(prophecyAccent, 0.12), borderRadius: '999px' }">{{ r.p.ref }}</span>
          </div>
          <p class="font-sans text-text-primary leading-snug text-xs">{{ r.p.text }}</p>
          <div class="flex items-center gap-1.5 pt-1 mt-0.5" :style="{ borderTop: '1px solid var(--item-border)' }">
            <Icon icon="lucide:circle-check" class="w-3.5 h-3.5 shrink-0" :style="{ color: fulfillmentAccent }" />
            <span class="font-mono text-[10px] font-bold" :style="{ color: fulfillmentAccent }">{{ r.f.year }}</span>
            <span class="ml-auto font-mono text-[9px] px-1.5 py-0.5" :style="{ color: fulfillmentAccent, background: getColorAlpha(fulfillmentAccent, 0.12), borderRadius: '999px' }">{{ r.f.ref }}</span>
          </div>
          <p class="font-sans text-text-primary leading-snug text-xs">{{ r.f.text }}</p>
        </div>

        <template v-else>
        <div class="min-w-0 min-h-0 overflow-hidden flex flex-col justify-center" :style="[cardStyle, { padding: '8px 12px', borderLeftWidth: '3px', borderLeftColor: prophecyAccent, borderLeftStyle: 'solid' }, reveal(r.start, -1)]">
          <div class="flex items-center gap-2 shrink-0">
            <Icon icon="lucide:scroll-text" class="w-4 h-4 shrink-0" :style="{ color: prophecyAccent }" />
            <span class="font-mono text-[11px] font-bold truncate" :style="{ color: prophecyAccent }">{{ r.p.year }}</span>
          </div>
          <p class="mt-1 font-sans text-text-primary leading-snug" style="font-size: 0.82rem">{{ r.p.text }}</p>
          <span
            class="mt-1 self-start font-mono text-[10px] px-2 py-0.5"
            :style="{ color: prophecyAccent, background: getColorAlpha(prophecyAccent, 0.12), borderRadius: '999px' }"
          >{{ r.p.ref }}</span>
        </div>

        <div class="flex items-center justify-center">
          <div
            class="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
            :style="{ background: getColorAlpha(getHexColor('var(--color-secondary)'), 0.14), color: getHexColor('var(--color-secondary)') }"
          >
            <Icon icon="lucide:arrow-right" class="w-4 h-4" />
          </div>
        </div>

        <div class="min-w-0 min-h-0 overflow-hidden flex flex-col justify-center" :style="[cardStyle, { padding: '8px 12px', borderLeftWidth: '3px', borderLeftColor: fulfillmentAccent, borderLeftStyle: 'solid' }, reveal(r.start, 1)]">
          <div class="flex items-center gap-2 shrink-0">
            <Icon icon="lucide:circle-check" class="w-4 h-4 shrink-0" :style="{ color: fulfillmentAccent }" />
            <span class="font-mono text-[11px] font-bold truncate" :style="{ color: fulfillmentAccent }">{{ r.f.year }}</span>
          </div>
          <p class="mt-1 font-sans text-text-primary leading-snug" style="font-size: 0.82rem">{{ r.f.text }}</p>
          <span
            class="mt-1 self-start font-mono text-[10px] px-2 py-0.5"
            :style="{ color: fulfillmentAccent, background: getColorAlpha(fulfillmentAccent, 0.12), borderRadius: '999px' }"
          >{{ r.f.ref }}</span>
        </div>
        </template>
      </div>
    </div>
  </div>
</template>
