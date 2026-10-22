<script setup>
import { getColorAlpha } from '../../utils/colors'
import { computed, inject, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 title: String,
 subtitle: String,
 variant: String,
 customer: Object,
 fields: Array,
 buttons: Array,
 slideStartTime: {
 type: Number,
 default: 0
 },
 mobile: Boolean
})

const { itemVars } = useVariant(computed(() => props.variant), 'CrmCardSlide')

const relativeTime = inject('relativeTime', ref(0))

const computedCustomer = computed(() => props.customer || {
 name: 'Иван Иванов',
 avatar_text: 'И',
 id_text: 'ID: #49281',
 status: 'горячий'
})

const computedFields = computed(() => props.fields || [])
const computedButtons = computed(() => props.buttons || [
 { text: "Взять в работу", btn_color: "", btn_text_color: "", start_time: 2500 },
 { text: "Отклонить", btn_color: "", btn_text_color: "", start_time: 2700 }
])

const getAnimProgress = (start_time, duration = 600) => {
 const elapsed = Math.max(0, relativeTime.value - (start_time || 0))
 const p = Math.min(1, elapsed / duration)
 return 1 - Math.pow(1 - p, 3)
}
</script>

<template>
 <div class="w-full h-full min-h-0 overflow-hidden flex flex-col items-center justify-center p-4 text-center text-text-primary relative">
 <!-- CRM Card -->
 <div :class="['relative w-full text-left z-10 flex flex-col overflow-hidden', mobile ? 'p-4 max-w-[95%] min-h-[92%]' : 'p-6 max-w-3xl min-h-[88%]']"
 :style="{
 ...itemVars,
 background: 'var(--item-bg)',
 backdropFilter: 'var(--item-backdrop)',
 WebkitBackdropFilter: 'var(--item-backdrop)',
 borderRadius: 'var(--item-radius)',
 boxShadow: 'var(--item-shadow)',
 padding: 'var(--item-padding)',
 padding: 'var(--item-padding)',
 borderWidth: 'var(--item-border-width)',
 borderStyle: 'var(--item-border-style)',
 borderColor: 'var(--item-border)'
 }">
 <!-- Glow effect -->
 <div class="absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl pointer-events-none z-0 opacity-10" :style="{ background: 'var(--color-primary)' }"></div>
 
 <!-- Card Header -->
 <div class="flex justify-between items-start mb-4 border-b pb-4 relative z-10" :style="{ borderColor: 'var(--item-border)' }">
 <div class="flex items-center gap-4 min-w-0">
 <div :class="['rounded-full flex items-center justify-center font-bold shrink-0', mobile ? 'w-10 h-10 text-lg' : 'w-14 h-14 text-xl']"
 :style="{ color: 'var(--color-primary)', background: getColorAlpha('var(--color-primary)', 0.15) }">
 {{ computedCustomer.avatar_text }}
 </div>
 <div class="min-w-0 pr-2">
 <h3 :class="['font-bold truncate text-text-primary', mobile ? 'text-base' : 'text-xl']">{{ computedCustomer.name }}</h3>
 <div class="text-text-secondary text-xs mt-0.5 truncate">{{ computedCustomer.id_text }}</div>
 </div>
 </div>
 <div :class="['text-color-success border rounded-full font-bold uppercase tracking-wider shrink-0 mt-1', mobile ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs']"
 :style="{ background: getColorAlpha('var(--color-success)', 0.15), borderColor: getColorAlpha('var(--color-success)', 0.3) }">
 {{ computedCustomer.status }}
 </div>
 </div>

 <!-- Fields Grid -->
 <div :class="['grid relative z-10 flex-1 content-center', mobile ? 'grid-cols-1 gap-3' : 'grid-cols-2 gap-4']">
 <div v-for="(field, idx) in computedFields" :key="idx" 
 class="p-3 border flex flex-col justify-center"
 :style="{ 
 opacity: getAnimProgress(field.start_time), 
 transform: `translateY(${(1 - getAnimProgress(field.start_time)) * 10}px)`,
 background: getColorAlpha('var(--text-primary)', 0.05),
 borderColor: 'var(--item-border)',
 borderRadius: 'calc(var(--item-radius) * 0.75)'
 }">
 <div class="flex items-center gap-2 mb-1 text-text-muted">
 <Icon v-if="field.field_icon" :icon="field.field_icon" class="text-sm shrink-0" :style="{ color: field.field_color || 'currentColor' }" />
 <div class="text-[10px] font-sans font-bold uppercase tracking-wider truncate">{{ field.label }}</div>
 </div>
 <div :class="['font-bold truncate', mobile ? 'text-sm' : 'text-base']" :style="{ color: field.field_color || 'var(--color-primary)' }">{{ field.value }}</div>
 </div>
 </div>
 
 <!-- Footer Actions -->
 <div :class="['mt-5 flex relative z-10', mobile ? 'flex-col gap-2' : 'flex-row gap-3']">
 <button v-for="(btn, i) in computedButtons" :key="i"
 class="flex-1 font-bold uppercase tracking-wider border text-center flex items-center justify-center transition-opacity"
 :class="[
 mobile ? 'py-2.5 text-[11px]' : 'py-3 px-5 text-xs',
 !btn.btn_color && i === 0 ? 'border-transparent opacity-90 hover:opacity-100' : (!btn.btn_color ? 'border-text-muted text-text-primary' : '')
 ]"
 :style="{
  ...(btn.btn_color ? { backgroundColor: btn.btn_color, color: btn.btn_text_color || 'var(--text-on-color)', borderColor: 'transparent' } : (i === 0 ? { backgroundColor: 'var(--color-primary)', color: 'var(--text-on-color)' } : { backgroundColor: getColorAlpha('var(--text-primary)', 0.05) })),
 borderRadius: 'calc(var(--item-radius) * 0.75)',
 opacity: getAnimProgress(btn.start_time),
 transform: `translateY(${(1 - getAnimProgress(btn.start_time)) * 10}px)`
 }">
 {{ btn.text }}
 </button>
 </div>
 </div>
 </div>
</template>
