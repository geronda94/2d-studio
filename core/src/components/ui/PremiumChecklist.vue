<script setup lang="ts">
import { ref, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { getHexColor , getColorAlpha} from '../../utils/colors'

const props = withDefaults(defineProps<{
 items?: Array<{
 label?: string
 title?: string
 text?: string
 desc?: string
 subtitle?: string
 icon?: string
 color?: string
 start_time?: number
 }>
 mobile?: boolean
 variant?: string
}>(), {
 items: () => [],
 mobile: false
})

const { itemVars, motion } = useVariant(computed(() => props.variant), 'PremiumChecklist')

const relativeTime = inject('relativeTime', ref(0))

const getItemProgress = (idx: number) => {
 const itemsList = props.items || []
 if (!itemsList.length || !itemsList[idx]) return 0
 const t = itemsList[idx].start_time ?? (idx * motion.value.stagger_ms)

  if (relativeTime.value < t) return 0
  const elapsed = relativeTime.value - t
  const progress = Math.min(elapsed / motion.value.appear_ms, 1)
  return 1 - Math.pow(1 - progress, 3) // easeOutCubic
}

const getActiveProgress = (idx: number) => {
 const itemsList = props.items || []
 if (!itemsList.length || !itemsList[idx]) return 0
 const t = itemsList[idx].start_time ?? (idx * motion.value.stagger_ms)
 const nextT = idx < itemsList.length - 1 ? (itemsList[idx+1].start_time ?? ((idx+1) * motion.value.stagger_ms)) : Infinity

  if (relativeTime.value < t) return 0

  if (relativeTime.value < nextT) {
 const elapsed = relativeTime.value - t
 const progress = Math.min(elapsed / motion.value.appear_ms, 1)
  return 1 - Math.pow(1 - progress, 3)
  } else {
 const elapsed = relativeTime.value - nextT
 const progress = Math.max(0, 1 - (elapsed / motion.value.appear_ms))
 return 1 - Math.pow(1 - progress, 3)
 }
}

const getDescProgress = (idx: number) => {
 return getItemProgress(idx)
}

const formatTitle = (title?: string) => {
 if (!title) return ''
 return title.replace(/\(([^)]+)\)/g, '<span class="font-mono text-color-secondary/80 text-[17px] font-normal ml-1">($1)</span>')
}
</script>

<template>
 <div ref="el" class="w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col"
 :style="{ ...itemVars }">
 <div class="grid"
 :class="[
   mobile ? 'items-start' : 'flex-1 min-h-0 items-stretch',
   (items?.length || 0) > 4 ? 'grid-cols-2' : 'grid-cols-1',
   mobile ? 'gap-x-3 gap-y-3' : ((items?.length || 0) > 4 ? 'grid-rows-3 gap-x-6 gap-y-3' : 'gap-y-3'),
 ]">
 <div v-for="(item, idx) in (items || [])" :key="idx" 
 class="group relative overflow-hidden flex items-center"
  :style="{
  opacity: getItemProgress(idx),
  transform: `translateX(${-48 * (1 - getItemProgress(idx))}px)`,
   background: 'var(--item-bg)',
   backdropFilter: 'var(--item-backdrop)',
  boxShadow: 'var(--item-shadow)',
  borderRadius: 'var(--item-radius)',
  gap: 'var(--item-gap)',
  padding: 'var(--item-padding)',
  borderWidth: 'var(--item-border-width)',
  borderStyle: 'var(--item-border-style)',
  borderColor: 'var(--item-border)'
 }">
 
 <!-- Декоративный левый край (теперь постоянный) -->
 <div class="absolute left-0 top-0 bottom-0 w-1"
 :style="{ backgroundColor: getHexColor(item.color) }"></div>

 <!-- Иконка -->
 <div class="shrink-0 w-10 h-10 md:w-14 md:h-14 ml-2 md:ml-3 border flex items-center justify-center relative z-10"
 :style="{
 borderRadius: 'var(--item-radius)',
 color: getHexColor(item.color),
 backgroundColor: getColorAlpha(getHexColor(item.color), 0.15),
 borderColor: getColorAlpha(getHexColor(item.color), 0.4),
 transform: `scale(${1 + 0.1 * getActiveProgress(idx)}) rotate(${3 * getActiveProgress(idx)}deg)`
 }">
 <Icon :icon="item.icon || 'heroicons:check'" class="w-5 h-5 md:w-7 md:h-7" />
 </div>

 <!-- Текст -->
 <div class="flex-1 flex flex-col justify-center min-h-[48px] relative z-10">
 <h4 class="font-bold text-[16px] md:text-[20px] tracking-wide font-heading leading-tight" 
  :style="{ color: getColorAlpha('var(--text-primary)', (70 + 30 * getActiveProgress(idx)) / 100) }"
  v-html="formatTitle(item.label || item.title || item.text)"></h4>
 
 <template v-if="item.desc || item.subtitle">
 <div
 :style="{
 opacity: getDescProgress(idx),
 marginTop: `${4 + 8 * getDescProgress(idx)}px`
 }">
 <div class="w-full h-[1px] mb-2" :style="{ backgroundColor: getColorAlpha('var(--text-primary)', 0.05) }"></div>
 <p class="text-[13.5px] md:text-[15.5px] font-sans leading-relaxed pb-0.5 text-text-secondary">{{ item.desc || item.subtitle }}</p>
 </div>
 </template>
 </div>
 </div>
 </div>
 </div>
</template>
