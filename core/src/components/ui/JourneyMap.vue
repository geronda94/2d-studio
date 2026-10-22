<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  stages: { type: Array, default: () => [] },
})

const { itemVars, line, motion } = useVariant(computed(() => props.variant), 'JourneyMap')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const reveal = (i, s) => {
  const t = s?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!stages.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="relative w-full flex-1 min-h-0 overflow-hidden flex flex-col justify-center">
        <div v-if="!compact" class="relative flex items-center mb-3 h-6 shrink-0">
          <div
            class="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-px"
            :style="{ background: line.color, opacity: 0.5 }"
          ></div>
          <div
            v-for="(s, i) in stages"
            :key="'dot' + i"
            class="relative flex-1 flex justify-center"
            :style="reveal(i, s)"
          >
            <span
              class="w-4 h-4 rounded-full"
              :style="{
                background: 'var(--item-bg)',
                borderWidth: '2px',
                borderStyle: 'solid',
                borderColor: accent(i),
                boxShadow: 'var(--item-shadow)',
              }"
            ></span>
          </div>
        </div>

        <div class="flex gap-2" :class="compact ? 'flex-col' : 'flex-row'">
          <div
            v-for="(s, i) in stages"
            :key="'st' + i"
            class="flex-1 min-w-0 flex flex-col"
            :style="[
              {
                background: 'var(--item-bg)',
                backdropFilter: 'var(--item-backdrop)',
                WebkitBackdropFilter: 'var(--item-backdrop)',
                borderRadius: 'var(--item-radius)',
                boxShadow: 'var(--item-shadow)',
                padding: 'var(--item-padding)',
                borderWidth: 'var(--item-border-width)',
                borderStyle: 'var(--item-border-style)',
                borderColor: 'var(--item-border)',
                padding: compact ? '8px 10px' : 'var(--item-padding)',
              },
              reveal(i + 1, s),
            ]"
          >
            <div class="flex items-center gap-2 mb-3">
              <span
                class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                :style="{ background: getColorAlpha(accent(i), 0.18), color: accent(i) }"
              >{{ i + 1 }}</span>
              <span class="text-base font-bold text-text-primary truncate">{{ s.name }}</span>
            </div>

            <div
              v-if="s.kpi"
              class="mb-2 inline-flex self-start items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono"
              :style="{
                color: 'var(--color-success)',
                background: getColorAlpha('var(--color-success)', 0.12),
                borderRadius: 'calc(var(--item-radius) * 0.5)',
              }"
            >
              <Icon icon="lucide:activity" class="w-3 h-3" />
              {{ s.kpi }}
            </div>

            <div v-if="!compact" class="mb-2">
              <div class="text-[10px] uppercase tracking-widest text-text-muted mb-1.5">Точки контакта</div>
              <div
                v-for="(t, ti) in (s.touchpoints || [])"
                :key="'t' + ti"
                class="flex items-start gap-1.5 mb-1.5 text-[13px] text-text-secondary"
              >
                <Icon icon="lucide:mouse-pointer-click" class="w-3 h-3 mt-0.5 shrink-0" :style="{ color: accent(i) }" />
                <span>{{ t }}</span>
              </div>
            </div>

            <div v-if="!compact">
              <div class="text-[10px] uppercase tracking-widest text-text-muted mb-1.5">Боли</div>
              <div
                v-for="(p, pi) in (s.pains || [])"
                :key="'p' + pi"
                class="flex items-start gap-1.5 mb-1.5 text-[13px] text-text-secondary"
              >
                <Icon icon="lucide:triangle-alert" class="w-3 h-3 mt-0.5 shrink-0" :style="{ color: 'var(--color-warning)' }" />
                <span>{{ p }}</span>
              </div>
            </div>

            <div v-if="compact" class="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-text-muted">
              <span v-for="(t, ti) in (s.touchpoints || [])" :key="'mt' + ti" class="truncate">· {{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
