<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  plan_image: { type: String, default: '' },
  zones: { type: Array, default: () => [] },
  legend: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'FloorPlanZones')
const relativeTime = inject('relativeTime', ref(0))
const imgFailed = ref(false)

const zoneColor = (z, i) => z.color || `var(--item-accent-${(i % 4) + 1})`
const fmt = (n) => Number(n || 0).toLocaleString('ru-RU', { maximumFractionDigits: 0 })
const compact = computed(() => props.density === 'compact' || props.mobile)

const totalArea = computed(() => (props.zones || []).reduce((a, z) => a + (Number(z.area) || 0), 0))
const totalValue = computed(() => (props.zones || []).reduce((a, z) => a + (Number(z.value) || 0), 0))

// Раскладываем зоны по плану без скучивания.
const spread = (vals, lo, hi) => {
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  if (!isFinite(min) || !isFinite(max) || max - min < 0.001) {
    return vals.map(() => (lo + hi) / 2)
  }
  return vals.map((v) => lo + ((v - min) / (max - min)) * (hi - lo))
}

const placedZones = computed(() => {
  const list = props.zones || []
  if (!list.length) return []
  const xs = spread(list.map((z) => Number(z.x) || 50), 14, 86)
  const ys = spread(list.map((z) => Number(z.y) || 50), 22, 80)
  return list.map((z, i) => ({ ...z, _x: xs[i], _y: ys[i], _i: i }))
})

const hotspotReveal = (i, start) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (start ?? i * motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translate(-50%, -50%) scale(${(0.7 + 0.3 * e).toFixed(3)})` }
}

const listReveal = (i, start) => {
  const p = Math.max(0, Math.min(1, (relativeTime.value - (start ?? i * motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col gap-4" :style="{ ...itemVars }">
    <div v-if="!zones.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-4 flex-1 min-h-0">
      <div
        class="relative w-full h-full min-h-[200px] lg:min-h-[320px] overflow-hidden"
        :style="{
          background: 'var(--item-primary-bg)',
          backdropFilter: 'var(--item-primary-backdrop)',
          WebkitBackdropFilter: 'var(--item-primary-backdrop)',
          borderRadius: 'var(--item-radius)',
          borderWidth: 'var(--item-border-width)',
          borderStyle: 'var(--item-border-style)',
          borderColor: 'var(--item-border)',
        }"
      >
        <img
          v-if="plan_image && !imgFailed"
          :src="plan_image"
          alt="План объекта"
          class="absolute inset-0 w-full h-full object-contain p-3 opacity-80"
          @error="imgFailed = true"
        />

        <!-- Стилизованная геометрия плана (стены и перегородки), если нет картинки -->
        <svg v-else class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
          <g
            fill="none"
            :stroke="getColorAlpha('var(--text-muted)', 0.45)"
            stroke-width="1.5"
            vector-effect="non-scaling-stroke"
          >
            <rect x="6" y="10" width="88" height="80" rx="2" />
            <line x1="6" y1="52" x2="94" y2="52" />
            <line x1="42" y1="10" x2="42" y2="52" />
            <line x1="64" y1="52" x2="64" y2="90" />
            <line x1="42" y1="72" x2="64" y2="72" />
            <line x1="20" y1="52" x2="20" y2="90" />
          </g>
        </svg>

        <div
          v-for="(z, i) in placedZones"
          :key="z.label + i"
          class="absolute flex flex-col items-center"
          :style="[{ left: z._x + '%', top: z._y + '%' }, hotspotReveal(i, z.start_time)]"
        >
          <span
            class="w-8 h-8 flex items-center justify-center text-xs font-mono font-bold"
            :style="{
              background: getColorAlpha(zoneColor(z, i), 0.85),
              color: getHexColor('var(--text-primary)'),
              borderRadius: '999px',
              border: '2px solid ' + getHexColor(zoneColor(z, i)),
            }"
          >{{ i + 1 }}</span>
          <span
            v-if="!compact"
            class="mt-1 px-1.5 py-0.5 text-[10px] font-mono whitespace-nowrap"
            :style="{ background: 'rgb(var(--bg-base-rgb) / 0.75)', color: 'var(--text-primary)', borderRadius: 'calc(var(--item-radius) - 4px)' }"
          >{{ z.label }}</span>
        </div>

        <div v-if="legend.length" class="absolute right-3 top-3 flex flex-wrap gap-2 max-w-[62%] justify-end">
          <span
            v-for="(l, i) in legend"
            :key="'lg' + i"
            class="flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-mono"
            :style="{ background: 'rgb(var(--bg-base-rgb) / 0.75)', color: 'var(--text-secondary)', borderRadius: 'calc(var(--item-radius) - 4px)' }"
          >
            <span class="w-2.5 h-2.5 rounded-[calc(var(--item-radius)-4px)]" :style="{ background: getColorAlpha(l.color || zoneColor({}, i), 0.85) }"></span>
            {{ l.label }}
          </span>
        </div>
      </div>

      <div class="flex flex-col gap-2 min-h-0">
        <div class="flex items-center justify-between text-[10px] uppercase tracking-widest font-mono text-text-muted">
          <span>Зоны</span><span>{{ zones.length }}</span>
        </div>

        <div
          v-for="(z, i) in zones"
          :key="'z' + i"
          class="flex items-center gap-3"
          :style="[
            {
              background: 'var(--item-bg)',
              backdropFilter: 'var(--item-backdrop)',
              WebkitBackdropFilter: 'var(--item-backdrop)',
              borderRadius: 'var(--item-radius)',
              boxShadow: 'var(--item-shadow)',
              // Плотный список зон: горизонталь из токена, вертикаль — доля токена
              padding: 'calc(var(--item-padding) * 0.6) var(--item-padding)',
              borderWidth: 'var(--item-border-width)',
              borderStyle: 'var(--item-border-style)',
              borderColor: 'var(--item-border)',
            },
            listReveal(i, z.start_time),
          ]"
        >
          <span
            class="w-6 h-6 shrink-0 flex items-center justify-center text-[11px] font-mono font-bold"
            :style="{ background: getColorAlpha(zoneColor(z, i), 0.85), color: getHexColor('var(--text-primary)'), borderRadius: '999px' }"
          >{{ i + 1 }}</span>
          <div class="min-w-0 flex-1">
            <div class="text-sm text-text-primary truncate">{{ z.label }}</div>
            <div class="text-[11px] font-mono text-text-muted">{{ fmt(z.area) }} м²</div>
          </div>
          <div class="text-sm font-mono font-bold shrink-0" :style="{ color: getHexColor(zoneColor(z, i)) }">
            {{ fmt(z.value) }} €
          </div>
        </div>

        <div class="flex items-center justify-between px-3 py-2 text-xs font-mono text-text-secondary">
          <span>Итого</span>
          <span>{{ fmt(totalArea) }} м² · {{ fmt(totalValue) }} €</span>
        </div>
        <div v-if="source_note" class="text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</div>
      </div>
    </div>
  </div>
</template>
