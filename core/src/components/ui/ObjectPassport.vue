<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  image: { type: String, default: '' },
  name: { type: String, default: '' },
  address: { type: String, default: '' },
  status: { type: String, default: '' },
  specs: { type: Array, default: () => [] },
  energy_class: { type: String, default: '' },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'ObjectPassport')
const relativeTime = inject('relativeTime', ref(0))
const imgFailed = ref(false)

const STATUS_TOKEN = {
  ok: 'var(--color-success)', success: 'var(--color-success)',
  'в эксплуатации': 'var(--color-success)', 'сдан': 'var(--color-success)', 'готов': 'var(--color-success)',
  info: 'var(--color-secondary)', 'строится': 'var(--color-secondary)', 'в работе': 'var(--color-secondary)',
  warn: 'var(--color-warning)', 'заморожен': 'var(--color-warning)', 'проект': 'var(--color-warning)',
  danger: 'var(--color-danger)', 'просрочен': 'var(--color-danger)', 'аварийный': 'var(--color-danger)',
}
const statusToken = computed(() => STATUS_TOKEN[String(props.status).toLowerCase()] || 'var(--color-secondary)')

const energyToken = computed(() => {
  const c = String(props.energy_class).toUpperCase().charAt(0)
  if (c === 'A') return 'var(--color-success)'
  if (c === 'B') return 'var(--color-secondary)'
  if (c === 'C') return 'var(--color-warning)'
  return 'var(--color-danger)'
})

const compact = computed(() => props.density === 'compact' || props.mobile)

const reveal = (i) => {
  const start = props.specs[i]?.start_time ?? i * motion.value.stagger_ms
  const p = Math.max(0, Math.min(1, (relativeTime.value - start) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 10).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div v-if="!name" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <div
      v-else
      class="flex flex-col md:flex-row overflow-hidden flex-1 min-h-0 max-h-[620px] my-auto w-full"
      :style="{
        background: 'var(--item-bg)',
        backdropFilter: 'var(--item-backdrop)',
        borderRadius: 'var(--item-radius)',
        boxShadow: 'var(--item-shadow)',
        padding: 'var(--item-padding)',
        borderWidth: 'var(--item-border-width)',
        borderStyle: 'var(--item-border-style)',
        borderColor: 'var(--item-border)',
      }"
    >
      <div
        class="relative md:w-72 shrink-0 aspect-[16/9] md:aspect-auto overflow-hidden"
        :style="{ background: 'var(--item-primary-bg)' }"
      >
        <img
          v-if="image && !imgFailed"
          :src="image"
          :alt="name"
          class="absolute inset-0 w-full h-full object-cover"
          @error="imgFailed = true"
        />
        <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-text-muted">
          <span
            class="w-20 h-20 flex items-center justify-center"
            :style="{ background: getColorAlpha('var(--text-primary)', 0.06), border: '1px dashed ' + getColorAlpha('var(--text-primary)', 0.18), borderRadius: 'calc(var(--item-radius) - 4px)' }"
          >
            <Icon icon="lucide:building-2" class="w-9 h-9" />
          </span>
          <span class="text-[11px] font-mono uppercase tracking-widest">Фото объекта</span>
        </div>
        <span
          v-if="energy_class"
          class="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 text-sm font-mono font-bold"
          :style="{
            background: getColorAlpha(energyToken, 0.2),
            color: getHexColor(energyToken),
            borderRadius: 'var(--item-radius)',
            border: '1px solid ' + getHexColor(energyToken),
          }"
        >
          <Icon icon="lucide:zap" class="w-3.5 h-3.5" />{{ energy_class }}
        </span>
      </div>

      <div class="flex-1 min-w-0 min-h-0 p-4 flex flex-col gap-3">
        <div class="flex flex-wrap items-start justify-between gap-3 shrink-0">
          <div class="min-w-0 flex-1">
            <h3 class="text-2xl font-bold text-text-primary leading-snug line-clamp-2">{{ name }}</h3>
            <p class="mt-1 flex items-center gap-1.5 text-sm text-text-secondary">
              <Icon icon="lucide:map-pin" class="w-4 h-4 shrink-0" />
              <span class="truncate">{{ address }}</span>
            </p>
          </div>
          <span
            class="px-3 py-1 text-xs font-bold uppercase tracking-wider shrink-0"
            :style="{
              background: getColorAlpha(statusToken, 0.18),
              color: getHexColor(statusToken),
              borderRadius: '999px',
              border: '1px solid ' + getColorAlpha(statusToken, 0.5),
            }"
          >{{ status }}</span>
        </div>

        <div class="flex-1 min-h-0 flex">
          <div class="grid gap-2 w-full h-full grid-cols-2 md:grid-cols-3 md:grid-rows-2 auto-rows-fr">
            <div
              v-for="(s, i) in specs"
              :key="s.label + i"
              class="px-3 py-2.5 flex flex-col justify-center"
              :style="[
                {
                  background: 'var(--item-primary-bg)',
                  backdropFilter: 'var(--item-primary-backdrop)',
                  borderRadius: 'var(--item-primary-radius)',
                  borderWidth: 'var(--item-primary-border-width)',
                  borderStyle: 'var(--item-primary-border-style)',
                  borderColor: 'var(--item-primary-border)',
                },
                reveal(i),
              ]"
            >
              <div class="text-[11px] uppercase tracking-widest font-mono text-text-muted truncate">{{ s.label }}</div>
              <div class="mt-1 font-mono text-text-primary">
                <span class="text-xl md:text-2xl font-bold">{{ s.value }}</span>
                <span v-if="s.unit" class="ml-1 text-sm text-text-secondary">{{ s.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="source_note" class="shrink-0 text-[11px] font-mono text-text-muted opacity-70">{{ source_note }}</div>
      </div>
    </div>
  </div>
</template>
