<script setup lang="ts">
import { ref, inject, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps<{
 label: string
 value: number // Raw value
 max?: number // Defaults to 100 if not provided
 color?: string
 icon?: string
 start_time?: number
 tooltip?: string
 variant?: string
}>()

const { itemVars } = useVariant(computed(() => props.variant), 'ProgressScale')

const relativeTime = inject('relativeTime', ref(0))

const ANIM_DURATION = 1500

const animProgress = computed(() => {
 const threshold = props.start_time ?? 0
 if (relativeTime.value < threshold) return 0
 const elapsed = relativeTime.value - threshold
 const raw = Math.min(elapsed / ANIM_DURATION, 1)
 return 1 - Math.pow(1 - raw, 4)
})

const percentage = computed(() => {
 const m = props.max || 100
 return Math.min(100, Math.max(0, (props.value / m) * 100))
})

const displayValue = computed(() => Math.floor(props.value * animProgress.value))
// Анимация только через transform (compositor), без paint-свойства width (§11).
const scaleX = computed(() => (percentage.value / 100 * animProgress.value).toFixed(4))

const container = ref<HTMLElement | null>(null)
const mouseX = ref(0)
const isHovering = ref(false)

const onMouseMove = (e: MouseEvent) => {
 if (!container.value) return
 const rect = container.value.getBoundingClientRect()
 mouseX.value = e.clientX - rect.left
 isHovering.value = true
}

const getIconName = () => {
 return props.icon || 'lucide:activity'
}

const customColor = computed(() => props.color || 'var(--color-secondary)')

const getContainerStyles = computed(() => {
 const threshold = props.start_time ?? 0
 const duration = 500
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))
 
 if (progress === 0) return { opacity: 0, transform: 'translateY(16px)', willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 1, transform: 'translateY(0px)', willChange: 'auto' }
 
 const ease = 1 - Math.pow(1 - progress, 4)
 return {
 opacity: ease.toFixed(4),
 transform: `translateY(${((1 - ease) * 16).toFixed(4)}px)`,
 willChange: 'opacity, transform'
 }
})
</script>

<template>
 <div ref="container" class="w-full h-full group relative cursor-pointer hover:brightness-110 flex flex-col justify-center" 
 :style="[{
 ...itemVars,
 background: 'var(--item-bg)',
 backdropFilter: 'var(--item-backdrop)',
 borderRadius: 'var(--item-radius)',
 boxShadow: 'var(--item-shadow)',
 padding: 'var(--item-padding)',
 padding: 'var(--item-padding)',
 borderWidth: 'var(--item-border-width)',
 borderStyle: 'var(--item-border-style)',
 borderColor: 'var(--item-border)'
 }, getContainerStyles]"
 @mousemove="onMouseMove" 
 @mouseleave="isHovering = false">
 
 <!-- Всплывающая подсказка (Tooltip) -->
 <div v-if="tooltip" 
 class="absolute bottom-full mb-3 pointer-events-none z-50 "
 :style="{ 
 left: `${mouseX}px`, 
 transform: 'translateX(-50%)', 
 opacity: isHovering ? 1 : 0,
 visibility: isHovering ? 'visible' : 'hidden'
 }">
 <div class="border px-3 py-1.5 flex flex-col items-center"
 :style="{
 background: 'var(--item-bg)',
 borderRadius: 'calc(var(--item-radius) - 4px)',
 boxShadow: 'var(--item-shadow)',
 borderWidth: 'var(--item-border-width)',
 borderStyle: 'var(--item-border-style)',
 borderColor: 'var(--item-border)'
 }">
 <p class="text-xs text-text-primary whitespace-nowrap font-medium">{{ tooltip }}</p>
 <div class="w-2.5 h-2.5 border-b border-r rotate-45 absolute -bottom-[6px]"
 :style="{ background: 'var(--item-bg)', borderColor: 'var(--item-border)' }"></div>
 </div>
 </div>
 <div class="flex justify-between items-center mb-3 md:mb-4">
 <div class="flex items-center gap-3 group-hover:translate-x-1 w-2/3">
            <div class="w-10 h-10 md:w-12 md:h-12 border flex items-center justify-center group-hover:scale-110 shrink-0" :style="{ background: 'var(--item-bg)', color: customColor, borderColor: 'var(--item-border)', borderRadius: 'calc(var(--item-radius) - 4px)' }">
 <Icon :icon="getIconName()" class="w-6 h-6 md:w-7 md:h-7" />
 </div>
 <span class="text-text-primary font-bold text-base md:text-lg tracking-wide group-hover:text-text-primary leading-tight" style="word-break: break-word;">{{ label }}</span>
 </div>
 <div class="flex items-baseline gap-1 group-hover:drop-shadow-[0_0_8px_rgb(var(--text-primary-rgb) / 0.5)] group-hover:-translate-x-1">
 <span class="text-text-primary group-hover:text-text-primary font-mono font-bold text-2xl md:text-3xl leading-none">{{ displayValue }}</span>
 <span class="text-text-muted group-hover:text-text-secondary font-mono text-base leading-none">%</span>
 </div>
 </div>
 
 <div class="h-3 md:h-5 w-full rounded-full overflow-hidden relative"
 style="background: color-mix(in srgb, var(--text-muted) 15%, transparent)">
 <div class="h-full w-full rounded-full origin-left"
 :style="{ 
 transform: `scaleX(${scaleX})`, 
 backgroundColor: customColor,
 boxShadow: `0 0 10px ${customColor}`,
 willChange: 'transform'
 }">
 </div>
 </div>
 </div>
</template>
