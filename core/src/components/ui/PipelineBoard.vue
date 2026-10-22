<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  stages: { type: Array, default: () => [] },
  coverage: { type: Number, default: 0 },
  currency: { type: String, default: '€' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'PipelineBoard')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => `var(--item-accent-${(i % 4) + 1})`

const fmtMoney = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M'
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return String(Math.round(n))
}
const fmtNum = (v) => Number(v || 0).toLocaleString('ru-RU')

const totalValue = computed(() => (props.stages || []).reduce((s, x) => s + (Number(x.value) || 0), 0))
const maxCount = computed(() => Math.max(1, ...(props.stages || []).map((s) => Number(s.count) || 0)))

const ratioFor = (s) => {
  const r = (Number(s.count) || 0) / maxCount.value
  return (0.35 + r * 0.65).toFixed(3)
}

const reveal = (i, st) => {
  const t = st?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}

const compact = computed(() => props.mobile)
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!stages.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="flex items-center justify-between mb-3 gap-2">
        <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">Пайплайн по стадиям</span>
        <div
          class="flex items-center gap-2"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'calc(var(--item-padding) * 0.5) var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: getColorAlpha('var(--color-success)', 0.4),
          }"
        >
          <Icon icon="lucide:shield-check" class="w-3.5 h-3.5" :style="{ color: 'var(--color-success)' }" />
          <span class="text-xs text-text-secondary">Покрытие</span>
          <span class="text-sm font-bold font-mono text-text-primary">{{ Number(coverage || 0).toFixed(1) }}×</span>
        </div>
      </div>

      <div class="relative w-full flex-1 min-h-0 overflow-hidden">
        <div class="flex h-full items-stretch gap-2 md:gap-3" :class="compact ? 'flex-col' : 'flex-row'">
          <div
            v-for="(s, i) in stages"
            :key="s.name + i"
            class="flex min-w-0 flex-1"
            :class="compact ? 'flex-row items-center gap-3' : 'flex-col'"
            :style="reveal(i, s)"
          >
            <div
              class="relative flex flex-1 flex-col overflow-hidden"
              :style="{
                background: 'var(--item-bg)',
                backdropFilter: 'var(--item-backdrop)',
                borderRadius: 'var(--item-radius)',
                boxShadow: 'var(--item-shadow)',
                padding: 'calc(var(--item-padding) * 0.6) var(--item-padding)',
                borderWidth: 'var(--item-border-width)',
                borderStyle: 'var(--item-border-style)',
                borderColor: 'var(--item-border)',
              }"
            >
              <div class="absolute left-0 top-0 bottom-0 w-1" :style="{ background: accent(i) }"></div>

              <div class="flex items-center justify-between gap-2 mb-2 pl-2">
                <span class="text-[11px] font-semibold tracking-wide text-text-secondary min-w-0 flex-1 truncate">{{ s.name }}</span>
                <span
                  class="text-[10px] font-mono px-1.5 py-0.5 shrink-0"
                  :style="{ color: accent(i), background: getColorAlpha(accent(i), 0.12), borderRadius: 'calc(var(--item-radius) * 0.5)' }"
                >{{ Number(s.conversion ?? 100).toFixed(0) }}%</span>
              </div>

              <div class="pl-2 flex flex-1 flex-col justify-center gap-3">
                <div class="font-heading font-bold text-text-primary leading-none" :class="compact ? 'text-2xl' : 'text-4xl md:text-5xl'">
                  {{ fmtNum(s.count) }}
                </div>
                <div class="flex flex-col gap-2">
                  <div class="text-sm font-mono" :style="{ color: accent(i) }">
                    {{ currency }}{{ fmtMoney(s.value) }}
                  </div>
                  <div v-if="!compact" class="flex items-center gap-1.5 text-[11px] text-text-muted">
                    <Icon icon="lucide:clock" class="w-3 h-3" />
                    <span>{{ Number(s.aging || 0).toFixed(0) }} дн. в стадии</span>
                  </div>
                  <div
                    v-if="!compact"
                    class="mt-1 h-1.5 w-full overflow-hidden"
                    :style="{ background: getColorAlpha('var(--text-primary)', 0.08), borderRadius: '999px' }"
                  >
                    <div
                      class="h-full w-full origin-left"
                      :style="{ background: getColorAlpha(accent(i), 0.7), transform: `scaleX(${ratioFor(s)})` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-2 flex items-center justify-between text-[11px] font-mono text-text-muted">
        <span>Всего в пайплайне: {{ currency }}{{ fmtMoney(totalValue) }}</span>
        <span>Покрытие цели: {{ Number(coverage || 0).toFixed(1) }}×</span>
      </div>
    </template>
  </div>
</template>
