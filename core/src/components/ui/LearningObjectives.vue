<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  objectives: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'LearningObjectives')
const relativeTime = inject('relativeTime', ref(0))

const accent = (i) => getHexColor(`var(--item-accent-${(i % 4) + 1})`)

const reveal = (o, i) => {
  const t = o.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - t) / motion.value.appear_ms))
  return 1 - Math.pow(1 - p, 3)
}

const cardStyle = (o, i) => {
  const e = reveal(o, i)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 18).toFixed(2)}px)` }
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

const criteria = [
  { key: 'condition', label: 'Условие', icon: 'lucide:settings-2' },
  { key: 'degree', label: 'Критерий', icon: 'lucide:target' },
]

const abcdLegend = ['Глагол', 'Действие', 'Условие', 'Критерий']

const BLOOM = ['знание', 'понимание', 'применение', 'анализ', 'оценка', 'создание']
const levelIndex = (lvl) => {
  const num = Number(lvl)
  if (!Number.isNaN(num) && num >= 1 && num <= 6) return num
  const idx = BLOOM.findIndex((b) => String(lvl).toLowerCase().includes(b))
  return idx >= 0 ? idx + 1 : 0
}

const levelStats = computed(() => {
  const map = {}
  props.objectives.forEach((o) => {
    const k = String(o.level || 'Без уровня')
    map[k] = (map[k] || 0) + 1
  })
  return Object.entries(map).map(([label, count], i) => ({
    label,
    count,
    token: `var(--item-accent-${(i % 4) + 1})`,
  }))
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <span class="text-[11px] font-mono uppercase tracking-widest text-text-muted">ABCD-структура цели</span>
      <span
        v-for="(l, i) in abcdLegend"
        :key="l"
        class="px-2 py-0.5 rounded-full text-[10px] font-mono"
        :style="{ background: getColorAlpha(accent(i), 0.12), color: accent(i) }"
      >{{ l }}</span>
      <span class="ml-auto text-[11px] font-mono text-text-muted">Целей: {{ objectives.length }}</span>
    </div>

    <div v-if="levelStats.length && !mobile" class="mb-4 flex flex-wrap items-center gap-2">
      <span class="text-[10px] font-mono uppercase tracking-widest text-text-muted">Уровни</span>
      <span
        v-for="s in levelStats"
        :key="s.label"
        class="px-2 py-0.5 rounded-full text-[10px] font-mono"
        :style="{ background: getColorAlpha(getHexColor(s.token), 0.12), color: getHexColor(s.token) }"
      >{{ s.label }} · {{ s.count }}</span>
    </div>

    <div
      v-if="!objectives.length"
      class="relative w-full flex-1 min-h-[320px] flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0 overflow-hidden">
      <div class="grid gap-2" :class="mobile ? 'grid-cols-2' : 'grid-cols-2 lg:grid-cols-4'">
        <div
          v-for="(o, i) in objectives"
          :key="i"
          class="flex flex-col"
          :class="mobile ? 'gap-1.5 p-2' : 'gap-2 p-3'"
          :style="[itemStyle, cardStyle(o, i)]"
        >
          <div class="flex items-center gap-2">
            <span
              class="rounded-full flex items-center justify-center font-mono font-bold shrink-0"
              :class="mobile ? 'w-5 h-5 text-[9px]' : 'w-7 h-7 text-xs'"
              :style="{ background: getColorAlpha(accent(i), 0.16), border: '1px solid ' + accent(i), color: accent(i) }"
            >{{ i + 1 }}</span>
            <span
              v-if="o.level"
              class="px-2 py-0.5 rounded-full font-mono uppercase tracking-widest"
              :class="mobile ? 'text-[8px] px-1.5' : 'text-[10px]'"
              :style="{ background: getColorAlpha(accent(i), 0.12), color: accent(i) }"
            >{{ o.level }}</span>
          </div>

          <p class="font-heading font-bold leading-tight" :class="mobile ? 'text-sm' : 'text-lg'" :style="{ color: accent(i) }">{{ o.verb }}</p>
          <p class="text-text-secondary" :class="mobile ? 'text-[10px] leading-snug' : 'text-sm leading-relaxed'">{{ o.behavior }}</p>

          <div v-if="!mobile && levelIndex(o.level) > 0" class="flex items-center gap-1">
            <span
              v-for="s in 6"
              :key="'lv' + s"
              class="h-1 flex-1 rounded-full"
              :style="{ background: s <= levelIndex(o.level) ? accent(i) : 'var(--item-border)' }"
            ></span>
          </div>

          <div class="mt-auto flex flex-col" :class="mobile ? 'gap-1 pt-2' : 'gap-2 pt-3'" :style="{ borderTop: '1px solid var(--item-border)' }">
            <div v-for="c in criteria" :key="c.key" class="flex items-start gap-1.5">
              <Icon :icon="c.icon" class="mt-0.5 shrink-0" :class="mobile ? 'w-3 h-3' : 'w-3.5 h-3.5'" :style="{ color: accent(i) }" />
              <p class="leading-snug text-text-muted" :class="mobile ? 'text-[10px]' : 'text-xs'">
                <span class="text-text-secondary">{{ c.label }}:</span> {{ o[c.key] }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p v-if="objectives.length && !mobile" class="mt-4 text-center text-[11px] font-mono text-text-muted">
      Каждая цель измерима: глагол действия + условие выполнения + критерий достижения.
    </p>
  </div>
</template>
