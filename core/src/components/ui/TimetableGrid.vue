<script setup>
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor, getColorAlpha } from '../../utils/colors'

const props = defineProps({
  mobile: { type: Boolean, default: false },
  variant: String,
  days: { type: Array, default: () => [] },
  periods: { type: Array, default: () => [] },
  cells: { type: Array, default: () => [] },
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'TimetableGrid')
const relativeTime = inject('relativeTime', ref(0))

const cellAt = (r, c) => (props.cells[r] || [])[c] || null

const accent = (cell, r, c) =>
  getHexColor((cell && cell.color) || `var(--item-accent-${((r * (props.days.length || 1) + c) % 4) + 1})`)

const reveal = (r, c) => {
  const step = Math.min(120, motion.value.stagger_ms)
  const p = Math.max(0, Math.min(1, (relativeTime.value - (r + c) * step) / motion.value.appear_ms))
  const e = 1 - Math.pow(1 - p, 3)
  return { opacity: e.toFixed(3), transform: `translateY(${((1 - e) * 8).toFixed(2)}px)` }
}

const hasConflicts = computed(() =>
  (props.cells || []).some((row) => (row || []).some((cell) => cell && cell.conflict)),
)

const totalLessons = computed(() =>
  (props.cells || []).reduce((s, row) => s + (row || []).filter((c) => c && c.subject).length, 0),
)

const itemStyle = {
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  WebkitBackdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)',
}
</script>

<template>
  <div class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col" :style="{ ...itemVars }">
    <div
      v-if="!days.length || !periods.length"
      class="relative w-full flex-1 min-h-[320px] flex items-center justify-center text-text-muted text-sm"
    >Нет данных</div>

    <div v-else class="relative w-full flex-1 min-h-0" :class="mobile ? 'overflow-hidden' : 'overflow-x-auto'">
      <div :class="mobile ? 'h-full flex flex-col' : 'min-w-[760px]'">
        <div class="mb-2 shrink-0 flex flex-col gap-0.5 md:flex-row md:flex-wrap md:items-center md:justify-between md:gap-2 text-[11px] font-mono text-text-muted">
          <span class="uppercase tracking-widest">Расписание · неделя × пары</span>
          <span>Занятий: {{ totalLessons }} · дней: {{ days.length }} · пар: {{ periods.length }}</span>
        </div>

        <div
          class="grid gap-1 md:gap-1.5"
          :class="mobile ? 'flex-1 min-h-0' : ''"
          :style="{ gridTemplateColumns: mobile ? `minmax(44px, 0.5fr) repeat(${days.length}, minmax(0, 1fr))` : `minmax(76px, 0.7fr) repeat(${days.length}, minmax(124px, 1fr))`, gridTemplateRows: mobile ? `auto repeat(${periods.length}, minmax(0, 1fr))` : undefined }"
        >
          <div></div>
          <div
            v-for="(d, ci) in days"
            :key="'h' + ci"
            class="text-center font-mono uppercase tracking-widest text-text-muted pb-1 truncate"
            :class="mobile ? 'text-[9px]' : 'text-[11px]'"
          >{{ d }}</div>

          <template v-for="(p, ri) in periods" :key="'r' + ri">
            <div class="flex items-center justify-center font-mono text-text-secondary" :class="mobile ? 'text-[9px]' : 'text-[11px]'">{{ p }}</div>

            <div
              v-for="(d, ci) in days"
              :key="'c' + ri + '-' + ci"
              class="flex flex-col"
              :class="mobile ? 'p-1 min-h-[42px] gap-0.5' : 'p-2 min-h-[64px] gap-1'"
              :style="[
                itemStyle,
                reveal(ri, ci),
                cellAt(ri, ci) ? { borderLeft: '3px solid ' + accent(cellAt(ri, ci), ri, ci) } : {},
                cellAt(ri, ci) && cellAt(ri, ci).conflict
                  ? { boxShadow: 'inset 0 0 0 1px ' + getHexColor('var(--color-danger)') }
                  : {},
              ]"
            >
              <template v-if="cellAt(ri, ci)">
                <div class="flex items-start justify-between gap-1">
                  <p
                    class="font-heading font-bold leading-tight break-words min-w-0"
                    :class="mobile ? 'text-[9px]' : 'text-xs'"
                    :style="{ color: accent(cellAt(ri, ci), ri, ci) }"
                  >{{ cellAt(ri, ci).subject }}</p>
                  <Icon
                    v-if="cellAt(ri, ci).conflict"
                    icon="lucide:alert-triangle"
                    :class="mobile ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'"
                    class="shrink-0"
                    :style="{ color: getHexColor('var(--color-danger)') }"
                  />
                </div>
                <p v-if="!mobile && cellAt(ri, ci).teacher" class="text-[10px] text-text-secondary truncate">
                  {{ cellAt(ri, ci).teacher }}
                </p>
                <p v-if="!mobile && cellAt(ri, ci).room" class="text-[10px] font-mono text-text-muted truncate">
                  {{ cellAt(ri, ci).room }}
                </p>
              </template>
            </div>
          </template>
        </div>

        <div class="mt-2 md:mt-3 shrink-0 flex flex-wrap items-center gap-3 md:gap-4 text-[11px] font-mono text-text-muted">
          <span class="flex items-center gap-1.5">
            <span class="w-1 h-3 rounded-full" :style="{ background: getHexColor('var(--color-secondary)') }"></span>
            Цвет полосы — предмет
          </span>
          <span v-if="hasConflicts" class="flex items-center gap-1.5">
            <Icon icon="lucide:alert-triangle" class="w-3.5 h-3.5" :style="{ color: getHexColor('var(--color-danger)') }" />
            Конфликт: двойная нагрузка преподавателя или аудитории
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
