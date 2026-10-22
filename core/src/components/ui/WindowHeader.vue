<script setup lang="ts">
withDefaults(defineProps<{
 title?: string
 mobile?: boolean
 centered?: boolean
}>(), {
 mobile: false,
 centered: false
})
</script>

<template>
 <div class="relative flex items-center border-b select-none shrink-0 gap-4"
 :style="{
   background: 'var(--item-bg, var(--bg-surface, #18181B))',
   backdropFilter: 'var(--item-backdrop, none)',
   borderColor: 'var(--item-border, #2D2D2F)',
   borderRadius: 'var(--item-radius, 0px) var(--item-radius, 0px) 0 0'
 }"
 :class="mobile ? 'h-7 px-3' : 'h-9 px-4'">
 <!-- macOS traffic-light dots -->
 <div class="flex shrink-0 z-10"
 :class="mobile ? 'gap-1.5' : 'gap-2'"
 :style="centered ? { position: 'absolute', left: mobile ? '12px' : '16px' } : {}">
 <div class="rounded-full bg-[#FF5F56] border border-[#E0443E]" :class="mobile ? 'w-2.5 h-2.5' : 'w-3 h-3'"></div>
 <div class="rounded-full bg-[#FFBD2E] border border-[#DEA123]" :class="mobile ? 'w-2.5 h-2.5' : 'w-3 h-3'"></div>
 <div class="rounded-full bg-[#27C93F] border border-[#1AAB29]" :class="mobile ? 'w-2.5 h-2.5' : 'w-3 h-3'"></div>
 </div>

 <!-- Centered title (terminal style) -->
 <template v-if="centered && title">
 <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
 <div class="font-sans font-semibold tracking-wide"
 :style="{ color: 'var(--text-secondary, #8E8E93)' }"
 :class="mobile ? 'text-[9px]' : 'text-[12px]'">
 {{ title }}
 </div>
 </div>
 </template>

 <!-- Default slot (URL bar, etc.) -->
 <slot v-if="!centered && $slots.default" />

 <!-- Title text (when no default slot) -->
 <div v-else-if="!centered && title && !$slots.default" class="flex-1 text-center font-mono tracking-wide pointer-events-none"
 :style="{ color: 'var(--text-secondary, #94A3B8)' }"
 :class="mobile ? 'text-[9px]' : 'text-[12px]'">
 {{ title }}
 </div>

 <!-- Empty flex-1 spacer (when no title, no slot) -->
 <div v-else-if="!centered && !$slots.default && !title" class="flex-1"></div>

 <!-- Right slot (globe icon, toolbar, etc.) -->
 <slot name="right" />
 </div>
</template>
