<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  orders: { type: Array, default: () => [] },
  overdue: { type: Number, default: 0 },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'MaintenanceBoard')
const relativeTime = inject('relativeTime', ref(0))

const num = (v) => Number(v) || 0
const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0))
const ease = (p) => 1 - Math.pow(1 - p, 3)
const progress = (t = 0, dur) => ease(clamp01((relativeTime.value - t) / (dur || motion.value.appear_ms)))

const cardStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  // плотная доска: горизонталь из токена, вертикаль — доля
  padding: 'calc(var(--item-padding) * 0.5) var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}

const STATUS = {
  overdue: { label: 'Просрочено', token: 'var(--color-danger)' },
  in_progress: { label: 'В работе', token: 'var(--color-warning)' },
  planned: { label: 'Запланировано', token: 'var(--color-secondary)' },
  done: { label: 'Выполнено', token: 'var(--color-success)' },
}
const COLUMNS = ['overdue', 'in_progress', 'planned', 'done']
const TYPE = {
  pm: { label: 'ППР', icon: 'lucide:calendar-check' },
  request: { label: 'Заявка', icon: 'lucide:alert-circle' },
  calibration: { label: 'Калибровка', icon: 'lucide:ruler' },
  spare: { label: 'Запчасти', icon: 'lucide:package' },
}
const typeOf = (o) => TYPE[o.type] || { label: o.type || '—', icon: 'lucide:wrench' }

const grouped = computed(() => {
  const cols = {}
  COLUMNS.forEach((k) => (cols[k] = []))
  ;(props.orders || []).forEach((o) => { if (cols[o.status]) cols[o.status].push(o) })
  return cols
})
const overdueCount = computed(() => {
  const derived = (props.orders || []).filter((o) => o.status === 'overdue').length
  return Math.max(num(props.overdue), derived)
})
const typeCounts = computed(() => {
  const c = {}
  Object.keys(TYPE).forEach((k) => (c[k] = 0))
  ;(props.orders || []).forEach((o) => { if (c[o.type] != null) c[o.type]++ })
  return c
})
const totalOrders = computed(() => (props.orders || []).length)
const statusTotals = computed(() => COLUMNS.map((k) => ({ key: k, count: grouped.value[k].length })))
const cardReveal = (o, i) => {
  const e = progress(o.start_time ?? i * motion.value.stagger_ms)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 14).toFixed(2)}px)` }
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div class="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2">
      <span class="text-[11px] font-mono uppercase tracking-wider text-text-muted">ППР и заявки</span>
      <span class="flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-bold"
            :style="{ background: getColorAlpha(overdueCount ? 'var(--color-danger)' : 'var(--color-success)', 0.14), border: '1px solid ' + getColorAlpha(overdueCount ? 'var(--color-danger)' : 'var(--color-success)', 0.4), color: getHexColor(overdueCount ? 'var(--color-danger)' : 'var(--color-success)') }">
        <Icon :icon="overdueCount ? 'lucide:triangle-alert' : 'lucide:circle-check'" class="w-3.5 h-3.5" />
        Просрочено: {{ overdueCount }}
      </span>
      <div class="flex flex-wrap items-center gap-2">
        <span v-for="(t, k) in TYPE" :key="k" class="flex items-center gap-1.5 text-[11px] font-mono text-text-muted">
          <Icon :icon="t.icon" class="w-3.5 h-3.5" :style="{ color: getHexColor('var(--item-accent-' + (Object.keys(TYPE).indexOf(k) % 4 + 1) + ')') }" />
          {{ t.label }} <span class="text-text-primary">{{ typeCounts[k] }}</span>
        </span>
      </div>
    </div>

    <div v-if="!orders.length" class="py-10 text-center text-text-muted text-sm">Нет заявок</div>

    <div v-else class="relative w-full flex-1 min-h-0" :class="mobile ? 'overflow-hidden' : 'min-h-[320px] overflow-x-auto'">
      <div class="grid gap-2 md:gap-4 h-full content-center" :class="mobile ? 'grid-cols-1' : 'grid-cols-4 min-w-[720px]'">
        <div v-for="(col, ci) in COLUMNS" :key="col" class="flex flex-col gap-1.5 md:gap-2.5">
          <div class="flex items-center justify-between px-1 pb-1 md:pb-2 border-b text-[11px] font-mono uppercase tracking-wider"
               :style="{ borderColor: 'var(--item-border)', color: getHexColor(STATUS[col].token) }">
            <span class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full" :style="{ background: getHexColor(STATUS[col].token) }"></span>{{ STATUS[col].label }}
            </span>
            <span class="text-text-muted">{{ grouped[col].length }}</span>
          </div>
          <div v-for="(o, i) in grouped[col]" :key="o.id ?? i" class="flex flex-col gap-1 md:gap-2"
               :style="[cardStyle, { borderLeftWidth: '3px', borderLeftStyle: 'solid', borderLeftColor: getHexColor(STATUS[col].token) }, cardReveal(o, ci * 3 + i)]">
            <div class="flex items-start justify-between gap-2">
              <span class="text-text-primary text-xs font-bold leading-tight">{{ o.asset }}</span>
              <Icon :icon="typeOf(o).icon" class="w-3.5 h-3.5 shrink-0" :style="{ color: getHexColor('var(--color-secondary)') }" />
            </div>
            <div class="flex items-center justify-between text-[10px] font-mono text-text-muted">
              <span>{{ typeOf(o).label }} · {{ o.id }}</span>
              <span :style="{ color: o.status === 'overdue' ? getHexColor('var(--color-danger)') : 'var(--text-secondary)' }">{{ o.due }}</span>
            </div>
            <div class="flex items-center gap-1.5 text-[11px] text-text-secondary pt-1.5 border-t" :style="{ borderColor: 'var(--item-border)' }">
              <Icon icon="lucide:user" class="w-3 h-3 shrink-0" />
              <span class="truncate">{{ o.assignee }}</span>
            </div>
          </div>
          <div v-if="!grouped[col].length" class="text-[11px] text-text-muted px-1">—</div>
        </div>
      </div>
    </div>

    <div v-if="orders.length" class="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] font-mono text-text-muted">
      <span>Всего заявок: <span class="text-text-primary font-bold">{{ totalOrders }}</span></span>
      <span v-for="s in statusTotals" :key="s.key" class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full" :style="{ background: getHexColor(STATUS[s.key].token) }"></span>
        {{ STATUS[s.key].label }} <span class="text-text-primary">{{ s.count }}</span>
      </span>
    </div>
  </div>
</template>
