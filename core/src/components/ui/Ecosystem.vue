<template>
 <div ref="containerRef" class="ecosystem-container relative w-full h-full min-h-[300px] flex items-center justify-center overflow-visible" :style="{ ...itemVars }">

 <div class="ecosystem-scale-wrapper absolute flex items-center justify-center"
  :style="{ transform: `scale(${scaleFactor})`, width: 0, height: 0 }">

 <!-- Radial connectors center → nodes -->
 <svg
  class="absolute pointer-events-none"
  style="left: -900px; top: -900px"
  width="1800"
  height="1800"
  viewBox="-900 -900 1800 1800"
 >
   <line
   v-for="(node, index) in positionedNodes"
   :key="'ln' + index"
   :x1="lineStart(node).x"
   :y1="lineStart(node).y"
   :x2="node.x"
   :y2="node.y + floatOffset(index).y"
   :stroke="getHexColor(node.color || 'var(--color-secondary)')"
   :stroke-width="line.width"
   :stroke-dasharray="line.dash === 'none' ? undefined : line.dash"
   stroke-linecap="round"
   vector-effect="non-scaling-stroke"
   :style="{ opacity: nodeLineOpacity(node, index) }"
   />
 </svg>

 <!-- Center Main Product -->
 <div class="absolute z-20 -translate-x-1/2 -translate-y-1/2" style="left: 0; top: 0;">
 <div class="flex flex-col items-center justify-center origin-center"
 :style="getCenterStyles()">

 <!-- IT2B brand wordmark (logo === 'it2b') -->
 <div
  v-if="center.logo === 'it2b'"
  class="w-40 h-40 rounded-[var(--item-radius)] border-2 flex items-center justify-center p-4"
  :style="{
   background: 'var(--item-primary-bg)',
   backdropFilter: 'var(--item-primary-backdrop)',
   WebkitBackdropFilter: 'var(--item-primary-backdrop)',
   borderColor: getColorAlpha('var(--color-secondary)', 0.5),
   boxShadow: 'var(--item-primary-shadow)',
  }"
 >
  <span class="font-heading font-black text-4xl tracking-tight text-text-primary">{{ center.label }}</span>
 </div>

 <!-- Generic center card -->
 <div v-else class="relative w-40 h-40 rounded-[var(--item-radius)] border-2 flex flex-col items-center justify-center p-4"
  :style="{
   background: 'var(--item-primary-bg)',
   backdropFilter: 'var(--item-primary-backdrop)',
   WebkitBackdropFilter: 'var(--item-primary-backdrop)',
   borderColor: getColorAlpha('var(--color-secondary)', 0.5),
   boxShadow: 'var(--item-primary-shadow)',
  }">
  <img v-if="center.logo" :src="center.logo" class="w-16 h-16 object-contain mb-2" />
  <div v-else class="w-20 h-20 mb-2 flex items-center justify-center"
   :style="{ background: getColorAlpha('var(--color-secondary)', 0.12), color: getHexColor('var(--color-secondary)'), borderRadius: 'calc(var(--item-radius) - 4px)' }">
   <Icon v-if="center.icon" :icon="center.icon" class="w-10 h-10" />
   <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
  </div>
  <span class="text-text-primary font-heading font-bold text-center text-base">{{ center.label }}</span>
 </div>
 </div>
 </div>

 <!-- Nodes -->
 <template v-for="(node, index) in positionedNodes" :key="index">
 <!-- 1. Orbit Position Wrapper -->
 <div
  class="absolute z-20 w-0 h-0"
  :style="getNodeStyles(node)"
  >
 <!-- 2. Centering Wrapper -->
 <div class="-translate-x-1/2 -translate-y-1/2">
 <!-- 3. Floating Animation Wrapper -->
 <div :style="getFloatingStyles(node, index)">

 <!-- Node Content -->
 <div class="relative flex items-center hover:scale-105"
  :class="mobile ? 'w-[152px] h-[48px] p-1.5 gap-1.5' : 'min-w-[200px] max-w-[280px] w-auto h-[60px] p-2.5 gap-2.5'"
  :style="{
   background: 'var(--item-bg)',
   backdropFilter: 'var(--item-backdrop)',
   WebkitBackdropFilter: 'var(--item-backdrop)',
   borderRadius: 'var(--item-radius)',
   borderWidth: 'var(--item-border-width)',
   borderStyle: 'var(--item-border-style)',
   borderColor: node.color ? getColorAlpha(node.color, 0.5) : 'var(--item-border)',
   boxShadow: node.color ? `0 8px 30px -5px ${getColorAlpha(node.color, 0.3)}` : 'var(--item-shadow)',
  }">

 <div class="flex items-center justify-center shrink-0"
 :class="[
 node.color ? '' : 'bg-color-secondary/10 text-color-secondary',
 mobile ? 'w-8 h-8' : 'w-10 h-10'
 ]"
  :style="[{ borderRadius: 'calc(var(--item-radius) - 4px)' }, node.color ? { color: getHexColor(node.color), backgroundColor: getColorAlpha(node.color, 0.2) } : {}]">
 <img v-if="node.logo" :src="node.logo" class="object-contain" :class="mobile ? 'w-5 h-5' : 'w-6 h-6'" />
 <Icon v-else-if="node.icon" :icon="node.icon" class="" :class="mobile ? 'text-lg' : 'text-xl'" />
 <span v-else class="font-bold uppercase" :class="mobile ? 'text-xs' : 'text-sm'">{{ node.label ? node.label.substring(0,2) : 'APP' }}</span>
 </div>

 <div class="flex flex-col overflow-hidden min-w-0 pr-0.5">
 <span class="text-text-primary font-heading font-bold leading-tight tracking-wide break-words"
 :class="mobile ? 'text-[12px] tracking-normal line-clamp-2' : 'text-base line-clamp-2'">{{ node.label }}</span>
 </div>
 </div>

 </div>
 </div>
 </div>
 </template>
 </div>
 </div>
</template>


<script setup>
import { getColorAlpha, getHexColor } from '../../utils/colors'
import { computed, inject, ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'

const props = defineProps({
 mobile: { type: Boolean, default: false },
 clicks: { type: Number, default: 0 },
 variant: String,
 center: {
 type: Object,
 default: () => ({ label: 'Core Platform', logo: null })
 },
  nodes: {
  type: Array,
  default: () => []
  },
  base_width: { type: Number, default: 0 },
  base_height: { type: Number, default: 0 },
  orbit_dx: { type: Number, default: 0 },
  orbit_dy: { type: Number, default: 0 }
})

const { itemVars, line } = useVariant(computed(() => props.variant), 'Ecosystem')

const containerRef = ref(null)
const scaleFactor = ref(1)
let resizeObserver = null

onMounted(() => {
 resizeObserver = new ResizeObserver((entries) => {
 for (let entry of entries) {
 const { width, height } = entry.contentRect
 // Base layout size depends on mobile mode (elliptical vs circular).
 // Wider base → орбита растягивается по ширине кадра, а не жмётся к центру.
  const baseW = props.base_width || (props.mobile ? 520 : 1220)
  const baseH = props.base_height || (props.mobile ? 660 : 760)
 const scaleW = width / baseW
 const scaleH = height / baseH
 // Apply dynamic scale to perfectly fit container
 scaleFactor.value = Math.min(scaleW, scaleH)
 }
 })

 if (containerRef.value) {
 resizeObserver.observe(containerRef.value)
 }
})

onUnmounted(() => {
 if (resizeObserver) {
 resizeObserver.disconnect()
 }
})

const relativeTime = inject('relativeTime', { value: 0 })

// The center node animates in at 300ms with a 700ms duration
const getCenterStyles = () => {
 const threshold = 300 // equivalent
 const duration = 700
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))

 const targetScale = props.mobile ? 1 : 1.15

 if (progress === 0) return { opacity: 0, transform: 'scale(0.5)', willChange: 'opacity, transform' }
 if (progress === 1) return { opacity: 1, transform: `scale(${targetScale})`, willChange: 'auto' }

 // easeOutQuart approximate
 const ease = 1 - Math.pow(1 - progress, 4)
 return {
 opacity: ease.toFixed(4),
 transform: `scale(${(0.5 + (targetScale - 0.5) * ease).toFixed(4)})`,
 willChange: 'opacity, transform'
 }
}

// Automatically position nodes in an orbit
const positionedNodes = computed(() => {
 const total = props.nodes.length
 if (total === 0) return []

 return props.nodes.map((node, index) => {
 // Distribute evenly around 360 degrees
 const angleBase = (360 / total) * index
 // -90 so it starts from the top
 const angleRad = (angleBase - 90) * (Math.PI / 180)

  // Perfectly symmetrical orbits (elliptical on mobile, wide ellipse on desktop)
  const distanceX = props.orbit_dx || (props.mobile ? 134 : 500)
  const distanceY = props.orbit_dy || (props.mobile ? 205 : 300)

 return {
 ...node,
 x: node.x !== undefined ? node.x : Math.cos(angleRad) * distanceX,
 y: node.y !== undefined ? node.y : Math.sin(angleRad) * distanceY
 }
 })
})

// Линии начинаются у края центральной карточки, а не в её центре — иначе под
// стеклом (blur) они просвечивают сквозь полупрозрачный центр.
const centerHalf = 88
const lineStart = (node) => {
 const len = Math.hypot(node.x, node.y) || 1
 return { x: (node.x / len) * centerHalf, y: (node.y / len) * centerHalf }
}

// Линия растёт от центра к узлу синхронно с его появлением: пока узел не начал
// появляться — линия полностью скрыта (раньше базовая 0.15 делала её видимой сразу).
const nodeLineOpacity = (node, index) => {
 const threshold = Number(node.start_time) || index * 200
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / 500))
 return (0.65 * (1 - Math.pow(1 - progress, 3))).toFixed(3)
}

const getNodeStyles = (node) => {
 const threshold = Number(node.start_time) || 0
 const duration = 700
 const progress = Math.max(0, Math.min(1, (relativeTime.value - threshold) / duration))

 const targetX = node.x
 const targetY = node.y

  if (progress === 0) return { left: '0px', top: '0px', opacity: 0, transform: `translate(${(targetX * 0.5).toFixed(4)}px, ${(targetY * 0.5).toFixed(4)}px)`, willChange: 'opacity, transform' }
  if (progress === 1) return { left: '0px', top: '0px', opacity: 1, transform: `translate(${targetX.toFixed(4)}px, ${targetY.toFixed(4)}px)`, willChange: 'auto' }

 // easeOutQuart approximate
 const ease = 1 - Math.pow(1 - progress, 4)
 const currentX = (targetX * 0.5) + (targetX * 0.5 * ease)
 const currentY = (targetY * 0.5) + (targetY * 0.5 * ease)

 return {
 left: '0px', top: '0px',
 opacity: ease.toFixed(4),
 transform: `translate(${currentX.toFixed(4)}px, ${currentY.toFixed(4)}px)`,
 willChange: 'opacity, transform'
 }
}

// Те же смещения плавания, что и у узла (getFloatingStyles): линия должна
// касаться карточки, а не висеть статично, пока узел качается по Y.
const floatOffset = (index) => {
  const yOffset = (Math.sin((relativeTime.value + index * 1200) / 4000 * Math.PI * 2) * -8) - 8
  return { y: yOffset }
}

const getFloatingStyles = (node, index) => {
 const threshold = Number(node.start_time) || 0
 if (relativeTime.value < threshold) return {}

 const yOffset = (Math.sin((relativeTime.value + index * 1200) / 4000 * Math.PI * 2) * -8) - 8
 return {
 transform: `translateY(${yOffset.toFixed(4)}px)`,
 willChange: 'transform'
 }
}
</script>
