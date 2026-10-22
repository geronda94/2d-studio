<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  density: { type: String, default: 'comfortable' },
  items: { type: Array, default: () => [] },
  source_note: { type: String, default: '' },
})

const { itemVars, itemPrimaryVars, motion } = useVariant(computed(() => props.variant), 'SnagBoard')
const relativeTime = inject('relativeTime', ref(0))
const imgFail = ref({})

const STATUS_ORDER = ['Новая', 'В работе', 'На проверке', 'Закрыта']
const SEVERITY = {
  'Критично': { token: 'var(--color-danger)', icon: 'lucide:alert-octagon' },
  'Высокая': { token: 'var(--color-warning)', icon: 'lucide:alert-triangle' },
  'Средняя': { token: 'var(--color-secondary)', icon: 'lucide:circle-alert' },
  'Низкая': { token: 'var(--text-muted)', icon: 'lucide:info' },
  danger: { token: 'var(--color-danger)', icon: 'lucide:alert-octagon' },
  warning: { token: 'var(--color-warning)', icon: 'lucide:alert-triangle' },
  info: { token: 'var(--color-secondary)', icon: 'lucide:circle-alert' },
  muted: { token: 'var(--text-muted)', icon: 'lucide:info' },
}
const sev = (s) => SEVERITY[s] || SEVERITY['Средняя']

const indexOf = computed(() => {
  const m = {}
  ;(props.items || []).forEach((it, i) => (m[it.id] = i))
  return m
})

const columns = computed(() => {
  const map = {}
  ;(props.items || []).forEach((it) => {
    const key = it.status || 'Без статуса'
    ;(map[key] = map[key] || []).push(it)
  })
  const keys = [...STATUS_ORDER.filter((k) => map[k]), ...Object.keys(map).filter((k) => !STATUS_ORDER.includes(k))]
  return keys.map((k) => ({ status: k, items: map[k] }))
})

const cardReveal = (it) => {
  const i = indexOf.value[it.id] ?? 0
  const p = Math.max(0, Math.min(1, (relativeTime.value - (it.start_time ?? i * motion.value.stagger_ms)) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(4), transform: `translateY(${((1 - e) * 12).toFixed(2)}px)` }
}

// Мобильный режим — плоский компактный список (колонки по статусам не влезают
// в портрет и дают клиппинг/скролл).
const flatItems = computed(() => {
  const order = (s) => {
    const i = STATUS_ORDER.indexOf(s)
    return i === -1 ? STATUS_ORDER.length : i
  }
  return [...(props.items || [])].sort((a, b) => order(a.status) - order(b.status))
})
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col gap-3" :style="{ ...itemVars }">
    <div v-if="!items.length" class="py-10 text-center text-text-muted text-sm">Нет данных</div>

    <template v-else>
      <!-- MOBILE: плоский список -->
      <div v-if="mobile" class="flex flex-col gap-1.5 flex-1 min-h-0 overflow-hidden">
        <div
          v-for="it in flatItems"
          :key="it.id"
          class="flex flex-col gap-1 p-2"
          :style="[
            {
              ...itemPrimaryVars,
              background: 'var(--item-primary-bg)',
              backdropFilter: 'var(--item-primary-backdrop)',
              WebkitBackdropFilter: 'var(--item-primary-backdrop)',
              borderRadius: 'var(--item-primary-radius)',
              boxShadow: 'var(--item-primary-shadow)',
              padding: 'var(--item-primary-padding)',
              borderWidth: 'var(--item-primary-border-width)',
              borderStyle: 'var(--item-primary-border-style)',
              borderColor: 'var(--item-primary-border)',
            },
            cardReveal(it),
          ]"
        >
          <div class="flex items-center justify-between gap-2">
            <span
              class="flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold"
              :style="{ background: getColorAlpha(sev(it.severity).token, 0.18), color: getHexColor(sev(it.severity).token), borderRadius: '4px' }"
            >
              <Icon :icon="sev(it.severity).icon" class="w-3 h-3" />{{ it.severity }}
            </span>
            <span class="text-[10px] font-mono text-text-muted truncate">{{ it.status }} · {{ it.id }}</span>
          </div>
          <div class="text-text-primary text-xs leading-snug line-clamp-2">{{ it.title }}</div>
          <div class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-text-secondary">
            <span class="flex items-center gap-1"><Icon icon="lucide:map-pin" class="w-3 h-3" />{{ it.location }}</span>
            <span class="flex items-center gap-1"><Icon icon="lucide:calendar-clock" class="w-3 h-3" />до {{ it.due }}</span>
          </div>
        </div>
      </div>

      <!-- DESKTOP: канбан-колонки -->
      <div
        v-else
        class="grid grid-cols-1 gap-2 md:gap-3 flex-1 min-h-0 overflow-hidden content-center"
        :style="{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }"
      >
        <div
          v-for="col in columns"
          :key="col.status"
          class="flex flex-col gap-1.5 p-2 min-h-0"
          :style="{
            background: 'var(--item-bg)',
            backdropFilter: 'var(--item-backdrop)',
            WebkitBackdropFilter: 'var(--item-backdrop)',
            borderRadius: 'var(--item-radius)',
            boxShadow: 'var(--item-shadow)',
            padding: 'var(--item-padding)',
            borderWidth: 'var(--item-border-width)',
            borderStyle: 'var(--item-border-style)',
            borderColor: 'var(--item-border)',
          }"
        >
          <div class="flex items-center justify-between px-1 pb-1 shrink-0" :style="{ borderBottom: '1px solid var(--item-border)' }">
            <span class="text-[11px] font-bold uppercase tracking-wider text-text-secondary">{{ col.status }}</span>
            <span class="text-[11px] font-mono text-text-muted">{{ col.items.length }}</span>
          </div>

          <div class="flex flex-col gap-1.5 my-auto min-h-0">
            <div
              v-for="it in col.items"
              :key="it.id"
              class="flex flex-col gap-1 p-2"
              :style="[
                {
                  ...itemPrimaryVars,
                  background: 'var(--item-primary-bg)',
                  backdropFilter: 'var(--item-primary-backdrop)',
                  WebkitBackdropFilter: 'var(--item-primary-backdrop)',
                  borderRadius: 'var(--item-primary-radius)',
                  boxShadow: 'var(--item-primary-shadow)',
                  padding: 'var(--item-primary-padding)',
                  borderWidth: 'var(--item-primary-border-width)',
                  borderStyle: 'var(--item-primary-border-style)',
                  borderColor: 'var(--item-primary-border)',
                },
                cardReveal(it),
              ]"
            >
              <div class="flex items-center justify-between gap-2">
                <span
                  class="flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold"
                  :style="{ background: getColorAlpha(sev(it.severity).token, 0.18), color: getHexColor(sev(it.severity).token), borderRadius: '4px' }"
                >
                  <Icon :icon="sev(it.severity).icon" class="w-3 h-3" />{{ it.severity }}
                </span>
                <span class="text-[10px] font-mono text-text-muted">{{ it.id }}</span>
              </div>

              <div class="text-text-primary leading-snug text-[13px] line-clamp-2">{{ it.title }}</div>

              <div v-if="it.photo && !imgFail[it.id]" class="relative w-full h-16 overflow-hidden" :style="{ borderRadius: 'var(--item-radius)' }">
                <img :src="it.photo" :alt="it.title" class="absolute inset-0 w-full h-full object-cover" @error="imgFail[it.id] = true" />
              </div>

              <div class="flex flex-col gap-0.5 text-[11px] text-text-secondary">
                <span class="flex items-center gap-1.5">
                  <Icon icon="lucide:hard-hat" class="w-3.5 h-3.5 shrink-0" /><span class="truncate">{{ it.trade }}</span>
                </span>
                <span class="flex items-center gap-1.5">
                  <Icon icon="lucide:map-pin" class="w-3.5 h-3.5 shrink-0" /><span class="truncate">{{ it.location }}</span>
                </span>
                <span class="flex items-center gap-1.5">
                  <Icon icon="lucide:calendar-clock" class="w-3.5 h-3.5 shrink-0" /><span class="truncate">до {{ it.due }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="source_note" class="text-[11px] font-mono text-text-muted opacity-70 shrink-0">{{ source_note }}</div>
    </template>
  </div>
</template>
