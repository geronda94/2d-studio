<script setup lang="ts">
import { getColorAlpha } from '../../utils/colors'
import { ref, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = withDefaults(defineProps<{
 columns?: Array<{ key: string, label: string, type?: 'text'|'icon'|'boolean'|'trend'|'status', align?: 'left'|'center'|'right' }>
 rows?: Array<Record<string, any>>
 fullWidth?: boolean
 mobile?: boolean
 defaultDelay?: number
 focus?: { start_time?: number }
 variant?: string
 dense?: boolean
}>(), {
 columns: () => [],
 rows: () => [],
 fullWidth: true,
 mobile: false,
 defaultDelay: 100,
 focus: () => ({ start_time: 0 }),
 dense: false
})

const relativeTime = inject('relativeTime', ref(0))

const { itemVars } = useVariant(computed(() => props.variant), 'ModernTable')

const getAnimProgress = (row: Record<string, any>, idx: number) => {
 const threshold = row.start_time ?? (idx * props.defaultDelay)
 const elapsed = Math.max(0, relativeTime.value - threshold)
 const p = Math.min(1, elapsed / 400)
 return 1 - Math.pow(1 - p, 3)
}

// Проп `focus` оставлен в контракте для совместимости схемы полезной нагрузки,
// но визуального эффекта фокусировки у таблицы нет: все строки выглядят одинаково.

// Smart columns for mobile layout
const iconCol = computed(() => props.columns.find(c => c.type === 'icon'))
const textCol = computed(() => props.columns.find(c => c.type === 'text' || !c.type))
const boolCol = computed(() => props.columns.find(c => c.type === 'boolean' || c.type === 'status'))
const gridCols = computed(() => props.columns.filter(c => c !== iconCol.value && c !== textCol.value && c !== boolCol.value))

</script>

<template>
 <!-- Мобильный карточный интерфейс -->
  <div v-if="mobile" class="flex flex-col w-full pb-1" :style="{ ...itemVars, gap: 'var(--item-gap)' }">
  <div v-for="(row, idx) in rows" :key="idx"
  :style="{
  background: 'var(--item-bg)',
  backdropFilter: 'var(--item-backdrop)',
  borderRadius: 'var(--item-radius)',
  boxShadow: 'var(--item-shadow)',
  padding: 'var(--item-padding)',
  padding: 'var(--item-padding)',
  opacity: getAnimProgress(row, idx)
  }">
  
 <!-- Шапка карточки -->
 <div class="flex justify-between items-start mb-1">
 <div class="flex items-center gap-2">
 <!-- Icon -->
 <div v-if="iconCol && row[iconCol.key]" class="w-6 h-6 flex items-center justify-center bg-color-secondary/10 text-color-secondary" :style="{ borderRadius: 'calc(var(--item-radius) - 4px)' }">
 <Icon :icon="row[iconCol.key]" class="w-3.5 h-3.5" />
 </div>
 <!-- Title -->
 <div v-if="textCol" class="text-text-primary font-bold text-[13px] leading-tight">{{ row[textCol.key] }}</div>
 </div>
 
 <!-- Status / Boolean -->
 <div v-if="boolCol">
 <div v-if="typeof row[boolCol.key] === 'boolean'">
 <div v-if="row[boolCol.key]" class="w-6 h-6 rounded-full border flex items-center justify-center"
 :style="{ background: getColorAlpha('var(--color-success)', 0.2), color: 'var(--color-success)', borderColor: getColorAlpha('var(--color-success)', 0.4) }">
 <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
 </div>
 <div v-else class="w-6 h-6 rounded-full border flex items-center justify-center"
 :style="{ background: getColorAlpha('var(--color-error)', 0.2), color: 'var(--color-error)', borderColor: getColorAlpha('var(--color-error)', 0.4) }">
 <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
 </div>
 </div>
 <span v-else class="px-2 py-1 rounded-full text-[9px] font-bold font-mono border uppercase tracking-wider"
 :style="{
  background: ['Active','Success'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-success)', 0.2) : ['Pending','Warning'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-warning)', 0.2) : ['Error','Failed'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-error)', 0.2) : 'var(--item-bg)',
 color: ['Active','Success'].includes(row[boolCol.key]) ? 'var(--color-success)' : ['Pending','Warning'].includes(row[boolCol.key]) ? 'var(--color-warning)' : ['Error','Failed'].includes(row[boolCol.key]) ? 'var(--color-error)' : 'var(--text-primary)',
  borderColor: ['Active','Success'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-success)', 0.4) : ['Pending','Warning'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-warning)', 0.4) : ['Error','Failed'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-error)', 0.4) : 'var(--text-secondary)'
 }">
 {{ row[boolCol.key] }}
 </span>
 </div>
 </div>
 
  <!-- Сетка метрик (все остальные колонки). На мобильном всегда 2 колонки:
       значения переносятся, а не обрезаются многоточием. -->
  <div v-if="gridCols.length > 0" class="grid grid-cols-2 gap-1.5">
  <div v-for="col in gridCols" :key="col.key"
   class="flex flex-col items-center justify-center border"
   :style="{ background: 'var(--item-bg)', borderRadius: 'calc(var(--item-radius) - 2px)', padding: 'calc(var(--item-padding) * 0.4)', borderWidth: 'var(--item-border-width)', borderStyle: 'var(--item-border-style)', borderColor: 'var(--item-border)' }">
   <div class="text-[8px] text-text-muted mb-0.5 uppercase tracking-wider font-medium text-center">{{ col.label }}</div>
 
 <template v-if="col.type === 'trend'">
 <div class="flex items-center gap-0.5 font-bold text-sm" :style="{ color: Number(row[col.key]) > 0 ? 'var(--color-success)' : 'var(--color-error)' }">
 <svg v-if="Number(row[col.key]) > 0" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
 {{ Math.abs(Number(row[col.key]) || 0) }}%
 </div>
 </template>
 <template v-else-if="col.type === 'icon'">
 <Icon v-if="row[col.key]" :icon="row[col.key]" class="w-4 h-4 text-text-secondary" />
 </template>
 <template v-else>
  <div class="font-bold text-[11px] text-center break-words leading-tight w-full text-text-primary font-sans line-clamp-3">{{ row[col.key] }}</div>
 </template>
 </div>
 </div>
 </div>
 </div>

  <!-- Десктопная таблица. Контейнер прозрачный: строки — отдельные
       «плавающие» карточки (фон/радиус/тень из варианта), разделение —
       просвет фона слайда. Никаких обводок. -->
  <div v-else class="relative overflow-x-auto"
  :class="fullWidth ? 'w-full' : 'w-max mx-auto'"
   :style="{ ...itemVars }">
  <table class="text-left border-separate"
  :class="fullWidth ? 'w-full' : 'w-max whitespace-nowrap'"
  :style="{ borderSpacing: '0px var(--item-gap)' }">
 <thead>
 <tr class="text-sm tracking-wider text-text-secondary font-sans font-bold uppercase">
  <th v-for="col in columns" :key="col.key" 
  :class="{
  'px-2 py-2 text-xs': mobile,
  'px-6 py-5': !mobile && !dense,
  'px-4 py-2 text-[11px]': !mobile && dense,
  'text-center': col.align === 'center' || col.type === 'icon' || col.type === 'boolean' || col.type === 'trend',
  'text-right': col.align === 'right'
  }">
 {{ col.label }}
 </th>
 </tr>
 </thead>
  <tbody>
    <tr v-for="(row, idx) in rows" :key="idx" :style="{ opacity: getAnimProgress(row, idx) }">
 
  <td v-for="(col, colIdx) in columns" :key="col.key"
  class="text-text-primary relative"
  style="background-clip: padding-box;"
    :style="{
   background: 'var(--item-bg, var(--bg-surface))',
   backdropFilter: 'var(--item-backdrop)',
   boxShadow: 'var(--item-shadow)',
  ...(dense && !mobile ? { height: '54px' } : {}),
  ...(colIdx === 0 ? { borderTopLeftRadius: 'var(--item-radius)', borderBottomLeftRadius: 'var(--item-radius)' } : {}),
  ...(colIdx === columns.length - 1 ? { borderTopRightRadius: 'var(--item-radius)', borderBottomRightRadius: 'var(--item-radius)' } : {})
  }"
  :class="{
  'px-6 py-8 text-[15px]': !dense,
  'px-4 py-2 text-xs': dense,
  'text-center': col.align === 'center' || col.type === 'icon' || col.type === 'boolean' || col.type === 'trend',
  'text-right': col.align === 'right'
  }">
 
 <template v-if="col.type === 'status' || col.type === 'boolean'">
 <!-- Boolean check/cross -->
  <div v-if="typeof row[col.key] === 'boolean'" class="flex justify-center">
 <div v-if="row[col.key]" class="w-6 h-6 rounded-full border flex items-center justify-center"
 :style="{ background: getColorAlpha('var(--color-success)', 0.2), color: 'var(--color-success)', borderColor: getColorAlpha('var(--color-success)', 0.4) }">
 <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
 </div>
 <div v-else class="w-6 h-6 rounded-full border flex items-center justify-center"
 :style="{ background: getColorAlpha('var(--color-error)', 0.2), color: 'var(--color-error)', borderColor: getColorAlpha('var(--color-error)', 0.4) }">
 <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
 </div>
 </div>
 <!-- Text Pill -->
  <span v-else class="rounded-full font-bold inline-block border font-sans px-3 py-1.5 text-xs"
 :style="{
  background: ['Active','Success'].includes(row[col.key]) ? getColorAlpha('var(--color-success)', 0.2) : ['Pending','Warning'].includes(row[col.key]) ? getColorAlpha('var(--color-warning)', 0.2) : ['Error','Failed'].includes(row[col.key]) ? getColorAlpha('var(--color-error)', 0.2) : 'var(--item-bg)',
 color: ['Active','Success'].includes(row[col.key]) ? 'var(--color-success)' : ['Pending','Warning'].includes(row[col.key]) ? 'var(--color-warning)' : ['Error','Failed'].includes(row[col.key]) ? 'var(--color-error)' : 'var(--text-primary)',
  borderColor: ['Active','Success'].includes(row[col.key]) ? getColorAlpha('var(--color-success)', 0.4) : ['Pending','Warning'].includes(row[col.key]) ? getColorAlpha('var(--color-warning)', 0.4) : ['Error','Failed'].includes(row[col.key]) ? getColorAlpha('var(--color-error)', 0.4) : 'var(--text-secondary)'
 }">
 {{ row[col.key] }}
 </span>
 </template>
 
 <template v-else-if="col.type === 'trend'">
  <div class="flex items-center gap-1 font-bold justify-center"
  :style="{ color: Number(row[col.key]) > 0 ? 'var(--color-success)' : 'var(--color-error)' }">
 <svg v-if="Number(row[col.key]) > 0" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
 {{ Math.abs(Number(row[col.key]) || 0) }}%
 </div>
 </template>

 <template v-else-if="col.type === 'icon'">
  <div class="flex items-center justify-center text-text-secondary">
 <Icon v-if="row[col.key]" :icon="row[col.key]" class="w-5 h-5" />
 </div>
 </template>
 
 <template v-else>
  <div class="flex items-center gap-3"
  :class="{
  'justify-center': col.align === 'center',
  'justify-end': col.align === 'right'
  }">
  <span class="inline-block"
  :class="[
  typeof row[col.key] === 'number' ? 'text-text-primary font-sans font-bold text-base' : '',
  dense ? 'line-clamp-2 leading-snug' : ''
  ]">{{ row[col.key] }}</span>
 </div>
 </template>
 
 </td>
 </tr>
 </tbody>
 </table>
 </div>
</template>
