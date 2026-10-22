<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  shift: { type: String, default: '' },
  output: { type: Object, default: () => ({}) },
  downtime: { type: Array, default: () => [] },
  quality: { type: Object, default: () => ({}) },
  labor: { type: Object, default: () => ({}) },
  issues: { type: Array, default: () => [] },
  signoff: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'ShiftHandover')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))
const reveal = (i, t0) => {
  const e = progress(t0 ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  // плотная матрица сдачи: горизонталь из токена, вертикаль — доля
  padding: 'calc(var(--item-padding) * 0.5) var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const plan = computed(() => num(props.output.plan))
const actual = computed(() => num(props.output.actual))
const unit = computed(() => props.output.unit || 'шт')
const completion = computed(() => (plan.value ? (actual.value / plan.value) * 100 : 0))
const downtimeTotal = computed(() => (props.downtime || []).reduce((s, d) => s + num(d.minutes), 0))
const downtimeMax = computed(() => Math.max(1, ...(props.downtime || []).map((d) => num(d.minutes))))
const laborPct = computed(() => {
  const req = num(props.labor.required)
  return req ? (num(props.labor.present) / req) * 100 : 0
})
const fpy = computed(() => num(props.quality.fpy))
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div class="mb-2 md:mb-3 flex flex-wrap items-center gap-x-4 gap-y-1">
      <span class="text-[11px] font-mono uppercase tracking-wider text-text-muted">Сменный отчёт</span>
      <span class="font-heading font-bold text-text-primary text-base md:text-lg">{{ shift }}</span>
      <span class="ml-auto text-[11px] font-mono text-text-muted">
        Выпуск <span class="text-text-primary font-bold">{{ actual }} / {{ plan }} {{ unit }}</span>
        · <span :style="{ color: getHexColor(completion >= 100 ? 'var(--color-success)' : 'var(--color-warning)') }">{{ Math.round(completion) }}%</span>
      </span>
    </div>

    <div class="relative w-full flex-1 min-h-0 overflow-hidden grid gap-2 md:gap-4 lg:grid-cols-3">
      <!-- Выпуск / качество / персонал -->
      <div class="flex flex-col gap-1.5 md:gap-2.5 min-h-0">
        <div class="flex-1 flex flex-col justify-center" :style="[cardStyle, reveal(0)]">
          <div class="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <Icon icon="lucide:package" class="w-3.5 h-3.5" />Выпуск
          </div>
          <div class="flex items-end gap-2">
            <span class="font-black text-2xl text-text-primary leading-none">{{ actual }}</span>
            <span class="text-sm text-text-muted mb-0.5">/ {{ plan }} {{ unit }}</span>
          </div>
          <div class="relative h-2.5 mt-3 rounded-full overflow-hidden" :style="{ background: 'var(--item-border)' }">
            <div class="absolute inset-0 origin-left rounded-full"
                 :style="{ transform: `scaleX(${clamp01(completion / 100).toFixed(3)})`, background: getHexColor(completion >= 100 ? 'var(--color-success)' : 'var(--color-secondary)') }"></div>
          </div>
        </div>

        <div class="flex-1 flex flex-col justify-center" :style="[cardStyle, reveal(1)]">
          <div class="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <Icon icon="lucide:badge-check" class="w-3.5 h-3.5" />Качество
          </div>
          <div class="flex items-end gap-2">
            <span class="font-black text-2xl leading-none" :style="{ color: getHexColor(fpy >= 95 ? 'var(--color-success)' : 'var(--color-warning)') }">{{ fpy }}<span class="text-base">%</span></span>
            <span class="text-[11px] text-text-muted mb-1">FPY</span>
          </div>
          <div class="mt-2 flex flex-col gap-1 text-xs text-text-secondary">
            <div class="flex items-center justify-between">
              <span>Брак</span><span class="font-mono" :style="{ color: getHexColor('var(--color-danger)') }">{{ num(quality.scrap_pct) }}%</span>
            </div>
            <div class="flex items-center justify-between">
              <span>Доработка</span><span class="font-mono text-text-primary">{{ num(quality.rework) }}</span>
            </div>
          </div>
        </div>

        <div class="flex-1 flex flex-col justify-center" :style="[cardStyle, reveal(2)]">
          <div class="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <Icon icon="lucide:users" class="w-3.5 h-3.5" />Персонал
          </div>
          <div class="flex items-end gap-2">
            <span class="font-black text-2xl text-text-primary leading-none">{{ num(labor.present) }}</span>
            <span class="text-sm text-text-muted mb-0.5">/ {{ num(labor.required) }}</span>
          </div>
          <div class="mt-2 flex items-center justify-between text-xs">
            <span class="text-text-secondary">Явка</span>
            <span class="font-mono" :style="{ color: getHexColor(laborPct >= 100 ? 'var(--color-success)' : 'var(--color-warning)') }">{{ Math.round(laborPct) }}%</span>
          </div>
          <div class="mt-1 flex items-center justify-between text-xs">
            <span class="text-text-secondary">Сверхурочные</span>
            <span class="font-mono text-text-primary">{{ num(labor.overtime_h) }} ч</span>
          </div>
        </div>
      </div>

      <!-- Простои -->
      <div class="p-2 md:p-3 flex flex-col" :style="[cardStyle, reveal(0, 200)]">
        <div class="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
          <span class="flex items-center gap-2"><Icon icon="lucide:clock-alert" class="w-3.5 h-3.5" />Простои</span>
          <span class="text-text-primary">{{ downtimeTotal }} мин</span>
        </div>
        <div v-if="!downtime.length" class="flex-1 flex items-center justify-center text-text-muted text-sm">Простоев нет</div>
        <div v-else class="flex-1 flex flex-col justify-around gap-3">
          <div v-for="(d, i) in downtime" :key="d.reason + i" class="text-xs" :style="reveal(i, (d.start_time ?? i * motion.stagger_ms) + 300)">
            <div class="flex items-center justify-between mb-1">
              <span class="text-text-primary truncate pr-2">{{ d.reason }}</span>
              <span class="font-mono text-text-secondary shrink-0">{{ num(d.minutes) }} мин</span>
            </div>
            <div class="relative h-2 rounded-full overflow-hidden" :style="{ background: 'var(--item-border)' }">
              <div class="absolute inset-y-0 left-0 origin-left rounded-full"
                   :style="{ width: (num(d.minutes) / downtimeMax) * 100 + '%', transform: `scaleX(${progress(i * motion.stagger_ms + 300).toFixed(3)})`, background: getHexColor('var(--color-danger)') }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Вопросы + подписи -->
      <div class="flex flex-col gap-1.5 md:gap-2.5 min-h-0">
        <div class="p-2 md:p-3 flex-1 flex flex-col" :style="[cardStyle, reveal(1, 200)]">
          <div class="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <Icon icon="lucide:circle-help" class="w-3.5 h-3.5" />Открытые вопросы
          </div>
          <div v-if="!issues.length" class="text-text-muted text-sm">Вопросов нет</div>
          <div v-else class="flex-1 flex flex-col justify-around gap-2.5">
            <div v-for="(it, i) in issues" :key="i" class="flex items-start gap-2 text-xs" :style="reveal(i, (it.start_time ?? i * motion.stagger_ms) + 300)">
              <Icon icon="lucide:chevron-right" class="w-3.5 h-3.5 mt-0.5 shrink-0" :style="{ color: getHexColor('var(--color-warning)') }" />
              <span class="text-text-primary leading-snug">{{ it.text }}
                <span v-if="it.owner" class="text-text-muted">· {{ it.owner }}</span>
              </span>
            </div>
          </div>
        </div>

        <div class="p-2 md:p-3" :style="[cardStyle, reveal(2, 200)]">
          <div class="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <Icon icon="lucide:signature" class="w-3.5 h-3.5" />Подписи
          </div>
          <div class="flex flex-wrap gap-x-4 gap-y-2">
            <div v-for="(s, i) in signoff" :key="i" class="text-xs" :style="reveal(i, (s.start_time ?? i * motion.stagger_ms) + 300)">
              <div class="text-text-primary font-medium">{{ s.name }}</div>
              <div class="text-text-muted">{{ s.position }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
