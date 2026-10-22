<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useVariant } from '../../composables/useVariant'
import { useDirector } from '../../composables/useDirector'
import { getHexColor , getColorAlpha} from '../../utils/colors'

const props = defineProps<{
 nodes?: any[]
 mobile?: boolean
 variant?: string
}>()

const { itemVars, line } = useVariant(computed(() => props.variant), 'InteractiveArchitecture')
const { isPlaying } = useDirector()
 
 function nodeStyleFor(prefix) {
 return {
 background: `var(--${prefix}-bg)`,
 backdropFilter: `var(--${prefix}-backdrop)`,
 WebkitBackdropFilter: `var(--${prefix}-backdrop)`,
 borderRadius: `var(--${prefix}-radius)`,
 boxShadow: `var(--${prefix}-shadow)`,
 borderWidth: `var(--${prefix}-border-width)`,
 borderStyle: `var(--${prefix}-border-style)`,
 }
 }
 const nodeStyle = computed(() => nodeStyleFor('item'))

const relativeTime = ref(0)
const injectedTime = typeof window !== 'undefined' ? (window as any).__VUE_APP_RELATIVE_TIME__ : null
// In reality, we use inject, but to be safe and compatible with Slide.vue:
import { inject } from 'vue'
const relTime = inject<any>('relativeTime', ref(0))
watch(relTime, (v) => relativeTime.value = v)

const containerRef = ref<HTMLElement | null>(null)
const minimap = ref<HTMLElement | null>(null)

// Размеры контейнера измеряются ResizeObserver'ом — раскладка и «домашний» вид
// считаются от реальной площади, поэтому граф центрируется и не липнет к низу.
const cw = ref(props.mobile ? 390 : 940)
const ch = ref(props.mobile ? 620 : 400)

const scale = ref(0.65)
const translateX = ref(0)
const translateY = ref(0)

// Состояние перетаскивания канваса (Pan)
const isDragging = ref(false)
const dragDistance = ref(0)
const startX = ref(0)
const startY = ref(0)

// Состояние перетаскивания миникарты
const isMinimapDragging = ref(false)

// Состояние перетаскивания узлов (Node Drag)
const draggingNodeId = ref<string | null>(null)
const nodeDragStartMouse = { x: 0, y: 0 }
const nodeDragStartPos = { x: 0, y: 0 }

const mousePos = ref({ x: 0, y: 0 })
const hoveredNodeId = ref<string | null>(null)
const selectedNode = ref<any | null>(null)
const activeNodeId = ref<string | null>(null)

let animationState = ref<any>(null)

const animateCamera = (targetTx: number, targetTy: number, targetScale: number, duration = 1500) => {
 animationState.value = {
 startTx: translateX.value,
 startTy: translateY.value,
 startScale: scale.value,
 targetTx,
 targetTy,
 targetScale,
 duration,
 startTime: relativeTime.value
 }
}

watch(relativeTime, (time) => {
 if (animationState.value) {
 const { startTx, startTy, startScale, targetTx, targetTy, targetScale, duration, startTime } = animationState.value
 const progress = Math.min((time - startTime) / duration, 1)
 const ease = 1 - Math.pow(1 - progress, 4) // easeOutQuart
 
 translateX.value = startTx + (targetTx - startTx) * ease
 translateY.value = startTy + (targetTy - startTy) * ease
 
 const zoomDip = Math.sin(progress * Math.PI) * -0.12
 scale.value = startScale + (targetScale - startScale) * ease + zoomDip
 
 if (progress >= 1) {
 animationState.value = null
 }
 }
})

// Auto-layout logic
const processedNodes = computed(() => {
 const rawNodes = props.nodes && props.nodes.length > 0 ? JSON.parse(JSON.stringify(props.nodes)) : []
 
 // Implicitly build edges
 const edges: {from: string, to: string}[] = []
 rawNodes.forEach((n: any) => {
 if (n.to && Array.isArray(n.to)) {
 n.to.forEach((t: string) => edges.push({ from: n.id, to: t }))
 }
 })
 
 // Calculate layers (Topological-ish BFS)
 const nodeMap = new Map<string, any>()
 const inDegree = new Map<string, number>()
 const layers = new Map<string, number>()
 
 rawNodes.forEach((n: any) => {
 nodeMap.set(n.id, n)
 inDegree.set(n.id, 0)
 layers.set(n.id, 0)
 })
 
 edges.forEach(e => {
 if (inDegree.has(e.to)) {
 inDegree.set(e.to, inDegree.get(e.to)! + 1)
 }
 })
 
 let queue = rawNodes.filter((n: any) => inDegree.get(n.id) === 0).map((n: any) => n.id)
 
 while (queue.length > 0) {
 const currentId = queue.shift()!
 const currentLayer = layers.get(currentId)!
 
 edges.filter(e => e.from === currentId).forEach(e => {
 const nextLayer = Math.max(layers.get(e.to)!, currentLayer + 1)
 layers.set(e.to, nextLayer)
 const indeg = inDegree.get(e.to)! - 1
 inDegree.set(e.to, indeg)
 if (indeg === 0) queue.push(e.to)
 })
 }
 
 // Assign coordinates based on layers
 const layerGroups = new Map<number, string[]>()
 layers.forEach((layer, id) => {
 if (!layerGroups.has(layer)) layerGroups.set(layer, [])
 layerGroups.get(layer)!.push(id)
 })
 
 const colSpacing = props.mobile ? 200 : 220
 const rowSpacing = props.mobile ? 140 : 180
 
 const maxLayer = Math.max(...Array.from(layerGroups.keys()), 0)
 const centerCol = maxLayer / 2
 
 layerGroups.forEach((nodeIds, layer) => {
 const layerSize = nodeIds.length
 // In mobile, vertical layout; in desktop, horizontal layout
 nodeIds.forEach((id, index) => {
 const node = nodeMap.get(id)
 if (node.x === undefined || node.y === undefined) {
 if (props.mobile) {
 node.x = (index - (layerSize - 1) / 2) * colSpacing * 0.95 // Увеличили отступ (190px при 200)
 node.y = (layer - centerCol) * rowSpacing
 } else {
 node.x = (layer - centerCol) * colSpacing
 node.y = (index - (layerSize - 1) / 2) * rowSpacing
 }
 }
 })
 })
 
 return { nodes: Array.from(nodeMap.values()), edges }
})

const nodes = computed(() => processedNodes.value.nodes)
const computedEdges = computed(() => processedNodes.value.edges)

// Границы графа (с учётом размера ноды 180×64) → масштаб «по размеру» и центр.
const NODE_HALF_W = 100
const NODE_HALF_H = 34
const bounds = computed(() => {
  const ns = nodes.value
  if (!ns.length) return { cx: 0, cy: 0, w: 200, h: 80, minX: -100, maxX: 100, minY: -40, maxY: 40 }
  const xs = ns.map((n) => Number(n.x) || 0)
  const ys = ns.map((n) => Number(n.y) || 0)
  const minX = Math.min(...xs) - NODE_HALF_W
  const maxX = Math.max(...xs) + NODE_HALF_W
  const minY = Math.min(...ys) - NODE_HALF_H
  const maxY = Math.max(...ys) + NODE_HALF_H
  return { cx: (minX + maxX) / 2, cy: (minY + maxY) / 2, w: maxX - minX, h: maxY - minY, minX, maxX, minY, maxY }
})

const fitScale = computed(() => {
  const b = bounds.value
  const sx = (cw.value * 0.82) / Math.max(1, b.w)
  const sy = (ch.value * 0.78) / Math.max(1, b.h)
  return Math.min(1.5, Math.max(0.25, Math.min(sx, sy)))
})

const home = computed(() => ({
  scale: fitScale.value,
  tx: cw.value / 2 - bounds.value.cx * fitScale.value,
  ty: ch.value / 2 - bounds.value.cy * fitScale.value,
}))

const snapHome = () => {
  scale.value = home.value.scale
  translateX.value = home.value.tx
  translateY.value = home.value.ty
}

// Надёжный замер контейнера (offsetWidth/Height = layout-размер, не зависит от
// масштаба сцены). Дублирует ResizeObserver — RO может не сработать при
// переключении v-show-слайда.
const measure = () => {
  const el = containerRef.value
  if (!el) return
  if (el.offsetWidth > 0) cw.value = el.offsetWidth
  if (el.offsetHeight > 0) ch.value = el.offsetHeight
}

// Не даём камере увести граф за границы контейнера (ноды не должны обрезаться).
const clampCamera = (tx, ty, s) => {
  const b = bounds.value
  const pad = 16
  const minTx = pad - b.minX * s
  const maxTx = cw.value - pad - b.maxX * s
  const minTy = pad - b.minY * s
  const maxTy = ch.value - pad - b.maxY * s
  const outTx = minTx > maxTx ? cw.value / 2 - b.cx * s : Math.min(Math.max(tx, minTx), maxTx)
  const outTy = minTy > maxTy ? ch.value / 2 - b.cy * s : Math.min(Math.max(ty, minTy), maxTy)
  return { tx: outTx, ty: outTy }
}

// Focus logic based on start_time
watch(relativeTime, (time) => {
 if (isDragging.value || selectedNode.value || draggingNodeId.value) return // User is interacting

 measure()
 // Вне реального воспроизведения (пауза/seek/редактор) держим общий вид —
 // кадр всегда показывает весь граф без обрезки.
 if (!isPlaying.value) {
  activeNodeId.value = null
  snapHome()
  return
 }
 
 let targetNode = null
 let maxTime = -1
 
 nodes.value.forEach(node => {
 if (node.start_time !== undefined && node.start_time !== null && Number(node.start_time) > 0) {
 if (time >= node.start_time && node.start_time > maxTime) {
 targetNode = node
 maxTime = node.start_time
 }
 }
 })
 
 const targetId = targetNode ? (targetNode as any).id : null
 
 if (targetId !== activeNodeId.value) {
 activeNodeId.value = targetId
 if (targetNode) {
 const targetScale = Math.min(1.5, Math.max(fitScale.value, fitScale.value * 1.12))
 const rawTx = cw.value / 2 - (targetNode as any).x * targetScale
 const rawTy = ch.value / 2 - (targetNode as any).y * targetScale
 const cam = clampCamera(rawTx, rawTy, targetScale)
 animateCamera(cam.tx, cam.ty, targetScale, 1500)
 } else {
 animateCamera(home.value.tx, home.value.ty, home.value.scale, 1500)
 }
 }
})

// --- Intersection Observer (to reset view when out of screen) ---
// Intersect logic is combined with containerRef above
let observer: IntersectionObserver | null = null
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
 window.addEventListener('mouseup', handleMouseUp)
 window.addEventListener('mousemove', handleMouseMove)
 window.addEventListener('keydown', handleKeyDown)

 if (typeof ResizeObserver !== 'undefined' && containerRef.value) {
  resizeObserver = new ResizeObserver((entries) => {
   const rect = entries[0]?.contentRect
   if (!rect) return
   if (rect.width > 0) cw.value = rect.width
   if (rect.height > 0) ch.value = rect.height
   if (!animationState.value && !selectedNode.value) snapHome()
  })
  resizeObserver.observe(containerRef.value)
 }

 measure()
 snapHome()

 observer = new IntersectionObserver((entries) => {
 if (!entries[0].isIntersecting) {
 animateCamera(home.value.tx, home.value.ty, home.value.scale, 0)
 activeNodeId.value = null
 }
 }, { threshold: 0.1 })
 
 if (containerRef.value) observer.observe(containerRef.value)
})

onUnmounted(() => {
 window.removeEventListener('mouseup', handleMouseUp)
 window.removeEventListener('mousemove', handleMouseMove)
 window.removeEventListener('keydown', handleKeyDown)
 if (observer) observer.disconnect()
 if (resizeObserver) resizeObserver.disconnect()
})

const handleWheel = (e: WheelEvent) => {
 e.preventDefault() 
 if (selectedNode.value) return 
 if (!containerRef.value) return
 
 const rect = containerRef.value.getBoundingClientRect()
 const logicalWidth = props.mobile ? 390 : cw.value
 const logicalHeight = props.mobile ? 620 : ch.value
 // Учитываем глобальный масштаб Core
 const mouseX = (e.clientX - rect.left) * (logicalWidth / rect.width)
 const mouseY = (e.clientY - rect.top) * (logicalHeight / rect.height)
 
 const zoomSensitivity = 0.0015
 const zoomDelta = Math.exp(-e.deltaY * zoomSensitivity)
 const newScale = Math.min(Math.max(scale.value * zoomDelta, 0.2), 3)
 
 translateX.value = mouseX - (mouseX - translateX.value) * (newScale / scale.value)
 translateY.value = mouseY - (mouseY - translateY.value) * (newScale / scale.value)
 scale.value = newScale
}

const handleMouseDown = (e: MouseEvent) => {
 if (e.button !== 0 || selectedNode.value) return
 isDragging.value = true
 dragDistance.value = 0
 startX.value = e.clientX - translateX.value
 startY.value = e.clientY - translateY.value
 document.body.style.cursor = 'grabbing'
}

const startNodeDrag = (e: MouseEvent, node: any) => {
 if (e.button !== 0 || selectedNode.value) return
 e.stopPropagation() // Блокируем перетаскивание холста
 
 draggingNodeId.value = node.id
 nodeDragStartMouse.x = e.clientX
 nodeDragStartMouse.y = e.clientY
 nodeDragStartPos.x = node.x
 nodeDragStartPos.y = node.y
 document.body.style.cursor = 'grabbing'
}

const handleMinimapMove = (e: MouseEvent) => {
 if (!isMinimapDragging.value || !minimap.value) return
 const rect = minimap.value.getBoundingClientRect()
 const nx = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1))
 const ny = Math.max(0, Math.min((e.clientY - rect.top) / rect.height, 1))
 
 // Миникарта 160x96, центр в 80x48, масштаб 0.08
 const logicalX = (nx * 160 - 80) / 0.08
 const logicalY = (ny * 96 - 48) / 0.08
 
 // Центрируем основную карту на этой логической точке
 translateX.value = home.value.tx - logicalX * scale.value
 translateY.value = home.value.ty - logicalY * scale.value
}

const handleMinimapMouseDown = (e: MouseEvent) => {
 if (e.button !== 0 || selectedNode.value) return
 e.stopPropagation()
 isMinimapDragging.value = true
 handleMinimapMove(e)
}

const handleMinimapWheel = (e: WheelEvent) => {
 e.preventDefault()
 if (selectedNode.value || !minimap.value) return
 
 const rect = minimap.value.getBoundingClientRect()
 const nx = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1))
 const ny = Math.max(0, Math.min((e.clientY - rect.top) / rect.height, 1))
 
 const logicalX = (nx * 160 - 80) / 0.08
 const logicalY = (ny * 96 - 48) / 0.08
 
 const zoomSensitivity = 0.0015
 const zoomDelta = Math.exp(-e.deltaY * zoomSensitivity)
 scale.value = Math.min(Math.max(scale.value * zoomDelta, 0.2), 3)
 
 // Центрируем вид на точке под курсором миникарты
 translateX.value = home.value.tx - logicalX * scale.value
 translateY.value = home.value.ty - logicalY * scale.value
}

const handleMouseMove = (e: MouseEvent) => {
 mousePos.value = { x: e.clientX, y: e.clientY }
 
 if (isMinimapDragging.value) {
 handleMinimapMove(e)
 return
 }
 
 // Если тянем ноду
 if (draggingNodeId.value) {
 const node = nodes.value.find(n => n.id === draggingNodeId.value)
 if (node) {
 const dx = (e.clientX - nodeDragStartMouse.x) / scale.value
 const dy = (e.clientY - nodeDragStartMouse.y) / scale.value
 
 const targetX = nodeDragStartPos.x + dx
 const targetY = nodeDragStartPos.y + dy
 
 // Collision detection (Узлы имеют размер 180x64. Возьмем margin безопасности 200x84)
 const isColliding = nodes.value.some(n => {
 if (n.id === node.id) return false
 return Math.abs(n.x - targetX) < 200 && Math.abs(n.y - targetY) < 84
 })
 
 if (!isColliding) {
 node.x = targetX
 node.y = targetY
 }
 }
 return
 }
 
 // Если тянем холст
 if (isDragging.value) {
 const newTx = e.clientX - startX.value
 const newTy = e.clientY - startY.value
 dragDistance.value += Math.abs(newTx - translateX.value) + Math.abs(newTy - translateY.value)
 translateX.value = newTx
 translateY.value = newTy
 }
}

const handleMouseUp = () => {
 isDragging.value = false
 isMinimapDragging.value = false
 draggingNodeId.value = null
 document.body.style.cursor = 'default'
}

const handleKeyDown = (e: KeyboardEvent) => {
 if (e.key === 'Escape' && selectedNode.value) {
 selectedNode.value = null
 }
}

const zoomIn = () => { if(!selectedNode.value) setScale(scale.value * 1.2) }
const zoomOut = () => { if(!selectedNode.value) setScale(scale.value / 1.2) }
const resetZoom = () => {
 if (selectedNode.value) return
 snapHome()
}

const setScale = (newScale: number) => {
 if (!containerRef.value) return
 newScale = Math.min(Math.max(newScale, 0.2), 3)
 const rect = containerRef.value.getBoundingClientRect()
 const centerX = rect.width / 2
 const centerY = rect.height / 2
 
 translateX.value = centerX - (centerX - translateX.value) * (newScale / scale.value)
 translateY.value = centerY - (centerY - translateY.value) * (newScale / scale.value)
 scale.value = newScale
}

const bgPosition = computed(() => `${translateX.value}px ${translateY.value}px`)
const bgSize = computed(() => `${20 * scale.value}px ${20 * scale.value}px`)

const tooltipStyle = computed(() => {
 const x = mousePos.value.x + 20
 const y = mousePos.value.y + 20
 const maxW = typeof window !== 'undefined' ? window.innerWidth : 1200
 const maxH = typeof window !== 'undefined' ? window.innerHeight : 800
 return {
 left: `${Math.min(x, maxW - 300)}px`,
 top: `${Math.min(y, maxH - 150)}px`
 }
})

const hasInputs = (id: string) => computedEdges.value.some(e => e.to === id)
const hasOutputs = (id: string) => computedEdges.value.some(e => e.from === id)

const getEdgeColor = (toId: string) => {
 const to = nodes.value.find(n => n.id === toId)
 return getHexColor(to?.color || 'color-secondary')
}

const calculatePath = (fromId: string, toId: string) => {
 const from = nodes.value.find(n => n.id === fromId)
 const to = nodes.value.find(n => n.id === toId)
 if (!from || !to) return ''
 
 if (props.mobile) {
 const x1 = Number(from.x)
 const y1 = Number(from.y) + 32
 const x2 = Number(to.x)
 const y2 = Number(to.y) - 32
 
 const sy1 = y1 + 25
 const sy2 = y2 - 25
 const midY = (sy1 + sy2) / 2
 
 return `M ${x1} ${y1} L ${x1} ${sy1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${sy2} L ${x2} ${y2}`
 } else {
 const x1 = Number(from.x) + 90
 const y1 = Number(from.y)
 const x2 = Number(to.x) - 90
 const y2 = Number(to.y)
 
 const sx1 = x1 + 25
 const sx2 = x2 - 25
 const midX = (sx1 + sx2) / 2
 
 return `M ${x1} ${y1} L ${sx1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${sx2} ${y2} L ${x2} ${y2}`
 }
}

const hoveredNode = computed(() => {
 return nodes.value.find(n => n.id === hoveredNodeId.value)
})

const handleNodeClick = (node: any) => {
 // Игнорируем клик, если ноду перетаскивали
 if (Math.abs(node.x - nodeDragStartPos.x) > 5 || Math.abs(node.y - nodeDragStartPos.y) > 5) return 
 selectedNode.value = node
}
</script>

<template>
  <div ref="containerRef"
  class="interactive-architecture-container variant-item relative mx-auto overflow-hidden cursor-grab active:cursor-grabbing w-full max-w-6xl h-full min-h-0"
  @wheel="handleWheel"
  @mousedown="handleMouseDown"
   :style="{
   ...itemVars,
   background: 'var(--item-bg)',
   backdropFilter: 'var(--item-backdrop)',
   WebkitBackdropFilter: 'var(--item-backdrop)',
   borderRadius: 'var(--item-radius)',
   boxShadow: 'var(--item-shadow)',
   padding: 'var(--item-padding)',
   borderWidth: 'var(--item-border-width)',
   borderStyle: 'var(--item-border-style)',
   borderColor: 'var(--item-border)',
   overflow: 'hidden',
   cursor: isDragging ? 'grabbing' : 'grab'
   }">
 
  <!-- Трансформируемый холст -->
  <div class="absolute inset-0 overflow-hidden pointer-events-none">
  <div class="absolute inset-0 origin-top-left pointer-events-none"
   :style="{ transform: `translate(${translateX}px, ${translateY}px) scale(${scale})` }">
 
 <!-- Линии -->
      <svg class="absolute inset-0 overflow-hidden pointer-events-none">
 <path v-for="(edge, i) in computedEdges" :key="'bg'+i"
 :d="calculatePath(edge.from, edge.to)" 
 fill="none" 
 stroke="rgb(var(--text-primary-rgb) / 0.1)" 
 :stroke-width="line.width" />
 
 <path v-for="(edge, i) in computedEdges" :key="'fg'+i"
 :d="calculatePath(edge.from, edge.to)" 
 fill="none" 
 :stroke="getEdgeColor(edge.to)" 
 :stroke-width="line.width" 
 stroke-linecap="round"
 :style="{ 
    strokeDasharray: line.dash !== 'none' ? line.dash : undefined,
    strokeDashoffset: line.dash !== 'none' ? 40 - ((relativeTime % 2000) / 2000 * 40) : 0
 }" />
 </svg>

 <!-- Узлы -->
 <div v-for="node in nodes" :key="node.id"
 class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-auto group"
  :style="{ left: `${node.x}px`, top: `${node.y}px` }"
 @mousedown="startNodeDrag($event, node)">
 
  <div class="relative w-[200px] h-[64px] flex items-center gap-3 p-3 transition-transform"
  :style="{ 
  ...nodeStyle,
  borderColor: 'var(--item-border)',
  borderLeftColor: getHexColor(node.color), 
  borderLeftWidth: 'max(3px, var(--item-border-width))',
  cursor: draggingNodeId === node.id ? 'grabbing' : 'pointer'
  }"
 @mouseenter="hoveredNodeId = node.id"
 @mouseleave="hoveredNodeId = null"
 @click="handleNodeClick(node)">
 
 <div v-if="hasOutputs(node.id)" 
 class="absolute w-2 h-2 rounded-full border border-text-secondary"
 :style="[mobile ? { bottom: '-4px', left: '50%', transform: 'translateX(-50%)' } : { right: '-4px', top: '50%', transform: 'translateY(-50%)' }, { background: 'var(--item-bg)' }]">
</div>
 <div v-if="hasInputs(node.id)" 
 class="absolute w-2 h-2 rounded-full border border-text-secondary"
 :style="[mobile ? { top: '-4px', left: '50%', transform: 'translateX(-50%)' } : { left: '-4px', top: '50%', transform: 'translateY(-50%)' }, { background: 'var(--item-bg)' }]">
</div>
 
 <div class="w-10 h-10 flex items-center justify-center shrink-0"
 :style="{
 borderRadius: 'calc(var(--item-radius) - 4px)',
 backgroundColor: getColorAlpha(node.color, 0.15),
 color: getHexColor(node.color)
 }">
 <Icon v-if="node.icon && node.icon.includes(':')" :icon="node.icon" class="text-xl" />
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
 <template v-if="node.icon && node.icon.includes('ellipse')">
 <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>
 </template>
 <path v-else-if="node.icon" :d="node.icon"/>
 </svg>
 </div>
 
 <div class="flex flex-col overflow-hidden">
 <span class="text-text-primary font-heading font-bold text-sm leading-tight truncate pointer-events-none">{{ node.label }}</span>
 <span class="text-[10px] font-mono text-text-secondary uppercase tracking-wider truncate pointer-events-none">{{ node.desc }}</span>
 </div>
 </div>
 </div>
 
 </div>
 </div>

 <!-- UI Overlay: Масштаб -->
 <div class="absolute top-4 left-4 flex items-center gap-2 p-1.5 border border-text-muted select-none z-50"
  :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }">
 <button @click.stop="zoomOut" class="w-7 h-7 flex items-center justify-center rounded text-text-secondary hover:text-text-primary hover:bg-[rgb(var(--text-primary-rgb)/0.08)]">-</button>
 <span class="text-xs font-mono w-12 text-center text-text-primary cursor-pointer hover:text-color-secondary" @click.stop="resetZoom">{{ Math.round(scale * 100) }}%</span>
 <button @click.stop="zoomIn" class="w-7 h-7 flex items-center justify-center rounded text-text-secondary hover:text-text-primary hover:bg-[rgb(var(--text-primary-rgb)/0.08)]">+</button>
 </div>

 <!-- UI Overlay: Четкая миникарта без замыливания -->
 <div v-if="!mobile" class="absolute top-4 right-4 w-40 h-24 border border-text-muted overflow-hidden z-50 cursor-crosshair"
 ref="minimap"
 :style="{ borderRadius: 'var(--item-radius)', background: 'var(--item-bg)', backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)' }"
 @mousedown="handleMinimapMouseDown"
 @wheel="handleMinimapWheel">
 <div class="absolute inset-0 opacity-100 pointer-events-none">
 <div v-for="node in nodes" :key="'mini'+node.id"
 class="absolute rounded-[calc(var(--item-radius)-4px)]"
 :style="{ 
 backgroundColor: getHexColor(node.color),
 left: `${Math.round(80 + node.x * 0.08 - 7)}px`, 
 top: `${Math.round(48 + node.y * 0.08 - 2)}px`,
 width: '14px',
 height: '6px'
 }">
 </div>
 </div>
 
 <!-- Вьюпорт -->
 <div class="absolute border border-color-secondary bg-color-secondary/10"
 :style="{
 left: `${Math.round(80 + (-translateX / scale) * 0.08)}px`,
 top: `${Math.round(48 + (-translateY / scale) * 0.08)}px`,
 width: `${Math.round(cw / scale * 0.08)}px`,
 height: `${Math.round(ch / scale * 0.08)}px`
 }">
 </div>
 </div>

 <!-- Модальное окно при клике -->
 <div v-if="selectedNode" 
 class="absolute inset-0 bg-bg-base/70  z-[200] flex items-center justify-center p-8 "
 @click="selectedNode = null">
 <div class="border border-color-secondary/30 p-6 w-full max-w-md relative" 
 :style="{ background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }"
 @click.stop>
 <button @click="selectedNode = null" class="absolute top-4 right-4 text-text-muted hover:text-text-primary ">
 <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
 </button>
 
 <div class="flex items-center gap-4 mb-4">
 <div class="w-12 h-12 flex items-center justify-center shrink-0"
 :style="{
 borderRadius: 'calc(var(--item-radius) - 2px)',
 backgroundColor: getColorAlpha(selectedNode.color, 0.2),
 color: getHexColor(selectedNode.color)
 }">
 <Icon v-if="selectedNode.icon && selectedNode.icon.includes(':')" :icon="selectedNode.icon" class="text-2xl" />
 <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
 <template v-if="selectedNode.icon && selectedNode.icon.includes('ellipse')">
 <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>
 </template>
 <path v-else-if="selectedNode.icon" :d="selectedNode.icon"/>
 </svg>
 </div>
 <div>
 <h3 class="text-xl font-heading font-bold text-text-primary">{{ selectedNode.label }}</h3>
 <div class="text-xs font-mono text-text-secondary uppercase tracking-wider">{{ selectedNode.desc }}</div>
 </div>
 </div>
 
  <div class="text-text-secondary leading-relaxed text-sm border-t border-text-muted pt-4" v-html="selectedNode.details">
 </div>
  </div>
  </div>
  
  <!-- Всплывающий тултип (вне канваса, фиксирован к мышке) -->
 <Teleport to="body">
 <div v-if="hoveredNode && !selectedNode && !draggingNodeId && !isDragging" 
 class="fixed z-[1000]  border border-text-secondary px-4 py-3 pointer-events-none w-[260px]"
 :style="isPlaying ? { left: '50%', top: '50%', transform: 'translate(-50%, -50%)', background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' } : { ...tooltipStyle, background: 'var(--item-bg)', borderRadius: 'var(--item-radius)', boxShadow: 'var(--item-shadow)' }">
 <div class="font-bold text-text-primary mb-1.5 flex items-center gap-2 text-sm">
 <div class="w-2 h-2 rounded-full" 
 :style="{ backgroundColor: getHexColor(hoveredNode.color) }"></div>
 {{ hoveredNode.label }}
 </div>
  <div class="text-xs text-text-secondary leading-relaxed" v-html="hoveredNode.details"></div>
  </div>
  </Teleport>
 </div>
</template>
