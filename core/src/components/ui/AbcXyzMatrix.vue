<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'
import QuadrantMatrix from './QuadrantMatrix.vue'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  items: { type: Array, default: () => [] },
  thresholds: { type: Object, default: () => ({ a: 80, b: 95, x: 10, y: 25 }) },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'AbcXyzMatrix')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))

const abcColor = {
  A: 'var(--color-success)',
  B: 'var(--color-secondary)',
  C: 'var(--text-muted)',
}

const rows = computed(() => {
  const list = [...(props.items || [])].sort((a, b) => num(b.value) - num(a.value))
  const totalValue = list.reduce((s, it) => s + num(it.value), 0) || 1
  let acc = 0
  return list.map((it) => {
    acc += num(it.value)
    const share = (acc / totalValue) * 100
    const abc = it.class
      ? String(it.class).charAt(0).toUpperCase()
      : share <= num(props.thresholds.a) ? 'A' : share <= num(props.thresholds.b) ? 'B' : 'C'
    return { ...it, cumulative: share, abc }
  })
})

const maxVariability = computed(() => Math.max(1, ...(props.items || []).map((it) => num(it.variability))))
// Шкала Y: 10% запаса над максимумом (минимум 30%), чтобы все пузыри — включая
// Z-выбросы — попадали в поле, а не липли к верхнему краю.
const Y_MAX = computed(() => Math.max(30, maxVariability.value * 1.1))
const points = computed(() => rows.value.map((it) => ({
  label: it.sku,
  x: clamp01(it.cumulative / 100) * 100,
  y: clamp01(num(it.variability) / Y_MAX.value) * 100,
  bubble: 16 + Math.sqrt(clamp01(num(it.value) / (rows.value.reduce((s, r) => s + num(r.value), 0) || 1))) * 34,
  color: abcColor[it.abc] || abcColor.C,
})))

const classCounts = computed(() => {
  const c = { A: 0, B: 0, C: 0 }
  rows.value.forEach((r) => { if (c[r.abc] != null) c[r.abc]++ })
  return c
})
const xyzCounts = computed(() => {
  const c = { X: 0, Y: 0, Z: 0 }
  ;(props.items || []).forEach((it) => {
    const v = num(it.variability)
    const xyz = v <= num(props.thresholds.x) ? 'X' : v <= num(props.thresholds.y) ? 'Y' : 'Z'
    c[xyz]++
  })
  return c
})
const xyzOf = (v) => (num(v) <= num(props.thresholds.x) ? 'X' : num(v) <= num(props.thresholds.y) ? 'Y' : 'Z')
const topRows = computed(() => rows.value.map((r) => ({ ...r, xyz: xyzOf(r.variability) })))
const legendReveal = (i) => {
  const e = progress(i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col" :style="{ ...itemVars }">
    <div v-if="!items.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <div class="shrink-0 mb-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[11px] font-mono uppercase tracking-wider text-text-muted">
        <span>ABC / XYZ · ценность × вариабельность</span>
        <span>A ≤ {{ num(thresholds.a) }}% · B ≤ {{ num(thresholds.b) }}% · X ≤ {{ num(thresholds.x) }}% · Y ≤ {{ num(thresholds.y) }}%</span>
      </div>

      <div class="relative w-full flex-1 min-h-[120px] flex flex-col py-1 px-2">
        <QuadrantMatrix
          :points="points"
          x-label="Накопленная ценность, %"
          y-label="Вариабельность, %"
          :quadrant-labels="['CZ', 'AZ', 'CX', 'AX']"
          :variant="variant"
          :mobile="mobile"
        />
      </div>

      <div class="shrink-0 mt-2 flex flex-wrap items-center gap-x-6 gap-y-2">
        <div class="flex flex-wrap items-center gap-3">
          <span v-for="(token, key, i) in abcColor" :key="key" class="flex items-center gap-2 px-2.5 py-1 rounded-full text-[11px] font-mono"
                :style="[{ background: getColorAlpha(token, 0.12), border: '1px solid ' + getColorAlpha(token, 0.35) }, legendReveal(i)]">
            <span class="w-2 h-2 rounded-full" :style="{ background: getHexColor(token) }"></span>
            <span :style="{ color: getHexColor(token) }">Класс {{ key }}</span>
            <span class="text-text-primary font-bold">{{ classCounts[key] }}</span>
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] font-mono text-text-muted">
          <span v-for="(count, key) in xyzCounts" :key="key">XYZ {{ key }} <span class="text-text-primary">{{ count }}</span></span>
        </div>
        <span v-if="!mobile" class="ml-auto flex items-center gap-1.5 text-[11px] font-mono text-text-muted">
          <Icon icon="lucide:info" class="w-3.5 h-3.5" />Размер пузыря — доля в ценности
        </span>
      </div>

      <div class="shrink-0 mt-1.5 p-2 md:p-2.5" :class="mobile ? 'overflow-hidden' : 'overflow-x-auto'"
           :style="{ background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)', borderWidth: 'var(--item-border-width)', borderStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' }">
        <div class="grid gap-x-1.5 md:gap-x-3 text-[10px] font-mono uppercase tracking-wider text-text-muted pb-1 border-b"
             :class="mobile ? 'grid-cols-[minmax(56px,1fr)_repeat(3,minmax(46px,1fr))_36px_30px]' : 'grid-cols-[minmax(90px,1fr)_repeat(3,minmax(80px,110px))_56px_48px]'"
             :style="{ borderColor: 'var(--item-border)' }">
          <span>SKU</span>
          <span class="text-right">Ценность</span>
          <span class="text-right">Накопл.</span>
          <span class="text-right">Вариабельн.</span>
          <span class="text-center">ABC</span>
          <span class="text-center">XYZ</span>
        </div>
        <div v-for="(r, i) in topRows" :key="r.sku + i"
             class="grid gap-x-1.5 md:gap-x-3 items-center py-1 border-b last:border-0"
             :class="mobile ? 'grid-cols-[minmax(56px,1fr)_repeat(3,minmax(46px,1fr))_36px_30px]' : 'grid-cols-[minmax(90px,1fr)_repeat(3,minmax(80px,110px))_56px_48px]'"
             :style="[{ borderColor: 'var(--item-border)' }, legendReveal(i)]">
          <span class="text-text-primary text-[11px] font-medium truncate">{{ r.sku }}</span>
          <span class="text-right text-[11px] font-mono text-text-secondary">{{ num(r.value).toLocaleString('ru-RU') }} €</span>
          <span class="text-right text-[11px] font-mono text-text-secondary">{{ r.cumulative.toFixed(0) }}%</span>
          <span class="text-right text-[11px] font-mono text-text-secondary">{{ num(r.variability) }}%</span>
          <span class="text-center text-[11px] font-bold" :style="{ color: getHexColor(abcColor[r.abc] || abcColor.C) }">{{ r.abc }}</span>
          <span class="text-center text-[11px] font-mono text-text-muted">{{ r.xyz }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
