<template>
  <div class="flex items-center space-x-1 w-full bg-bg-surface border border-text-muted rounded-lg px-4 py-2 text-text-primary focus-within:border-color-secondary transition-colors font-mono select-none"
       :class="{'border-red-500/50 bg-red-500/5': hitLimit}"
       @mouseleave="hitLimit = false">
    
    <!-- Minutes -->
    <input 
      type="text" 
      v-model="localMinutes"
      @blur="applyInput"
      @keydown.enter="applyInput"
      class="w-10 bg-transparent text-center focus:outline-none focus:bg-bg-surface rounded cursor-ns-resize transition-colors"
      @wheel.prevent="handleWheel($event, 'minutes')"
      @mousedown.prevent="startDrag($event, 'minutes')"
      title="Минуты (скролл или тяните мышкой)"
    />
    
    <span class="text-text-secondary font-bold pb-1">:</span>
    
    <!-- Seconds -->
    <input 
      type="text" 
      v-model="localSeconds"
      @blur="applyInput"
      @keydown.enter="applyInput"
      class="w-10 bg-transparent text-center focus:outline-none focus:bg-bg-surface rounded cursor-ns-resize transition-colors"
      @wheel.prevent="handleWheel($event, 'seconds')"
      @mousedown.prevent="startDrag($event, 'seconds')"
      title="Секунды (скролл или тяните мышкой)"
    />
    
    <span class="text-text-secondary font-bold pb-1">.</span>
    
    <!-- Deciseconds -->
    <input 
      type="text" 
      v-model="localDeci"
      @blur="applyInput"
      @keydown.enter="applyInput"
      class="w-6 bg-transparent text-center focus:outline-none focus:bg-bg-surface rounded cursor-ns-resize transition-colors"
      @wheel.prevent="handleWheel($event, 'deciseconds')"
      @mousedown.prevent="startDrag($event, 'deciseconds')"
      title="Десятые (скролл или тяните мышкой)"
    />
    
    <div v-if="hitLimit" class="absolute -top-8 left-0 right-0 text-center text-xs text-red-400 font-sans pointer-events-none whitespace-nowrap">
      Достигнут лимит (соседние слайды)
    </div>

  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: Number, required: true },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 9999999 }
})
const emit = defineEmits(['update:modelValue'])

const hitLimit = ref(false)

const localMinutes = ref('00')
const localSeconds = ref('00')
const localDeci = ref('0')

const syncFromProps = () => {
  const ms = props.modelValue || 0
  localMinutes.value = Math.floor(ms / 60000).toString().padStart(2, '0')
  localSeconds.value = Math.floor((ms % 60000) / 1000).toString().padStart(2, '0')
  localDeci.value = Math.floor((ms % 1000) / 100).toString()
}

watch(() => props.modelValue, syncFromProps, { immediate: true })

const applyConstraints = (newMs) => {
  let clamped = newMs
  let limited = false
  if (clamped < props.min) { clamped = props.min; limited = true }
  if (clamped > props.max) { clamped = props.max; limited = true }
  
  if (limited && clamped === props.modelValue) {
    hitLimit.value = true
    setTimeout(() => { hitLimit.value = false }, 1500)
  } else {
    hitLimit.value = false
    emit('update:modelValue', clamped)
  }
}

const applyInput = () => {
  const m = parseInt(localMinutes.value) || 0
  const s = parseInt(localSeconds.value) || 0
  const d = parseInt(localDeci.value) || 0
  const newMs = (m * 60000) + (s * 1000) + (d * 100)
  applyConstraints(newMs)
  // Re-sync UI just in case it clamped
  setTimeout(syncFromProps, 0)
}

const increment = (unit, amount = 1) => {
  let ms = props.modelValue || 0
  if (unit === 'minutes') ms += 60000 * amount
  else if (unit === 'seconds') ms += 1000 * amount
  else if (unit === 'deciseconds') ms += 100 * amount
  applyConstraints(ms)
}

const decrement = (unit, amount = 1) => {
  let ms = props.modelValue || 0
  if (unit === 'minutes') ms -= 60000 * amount
  else if (unit === 'seconds') ms -= 1000 * amount
  else if (unit === 'deciseconds') ms -= 100 * amount
  applyConstraints(ms)
}

const handleWheel = (event, unit) => {
  if (event.deltaY < 0) increment(unit)
  else if (event.deltaY > 0) decrement(unit)
}

const activeDragUnit = ref(null)
let lastY = 0

const startDrag = (event, unit) => {
  activeDragUnit.value = unit
  lastY = event.clientY
  document.body.style.cursor = 'ns-resize'
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
  // Optional: focus the input so they can type immediately if they just clicked
  event.target.focus()
}

const onDrag = (event) => {
  if (!activeDragUnit.value) return
  const currentY = event.clientY
  const delta = lastY - currentY
  if (Math.abs(delta) >= 3) {
    if (delta > 0) increment(activeDragUnit.value)
    else decrement(activeDragUnit.value)
    lastY = currentY
  }
}

const stopDrag = () => {
  activeDragUnit.value = null
  document.body.style.cursor = ''
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
})
</script>
