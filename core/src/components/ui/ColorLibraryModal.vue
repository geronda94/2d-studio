<script setup>
import { ref, watch, computed } from 'vue'
import { fetchProjectsSummary, fetchProjectColors, fetchPresentationTokens, upsertProjectTokens, deleteProjectToken } from '../../services/api'

const props = defineProps({
  show: Boolean,
  projectId: [Number, String],
  presentationId: [Number, String],
  // adminMode = настройки проекта: дефолты можно править (но не удалять), custom — всё можно.
  // Обычный режим (из редактора слайда): дефолты locked, custom — правка + удаление.
  adminMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'select'])

const colors = ref([])
const activeCategory = ref('all')
const loading = ref(true)

const newColor = ref({
  name: '',
  value: '#FFFFFF',
  category: 'solid'
})

const transparentSettings = ref({
  baseColor: '#000000',
  opacity: 50
})

const gradientSettings = ref({
  type: 'linear',
  angle: 90,
  stops: [
    { id: 1, color: 'var(--color-secondary)', opacity: 100, position: 0 },
    { id: 2, color: 'var(--color-primary)', opacity: 100, position: 100 }
  ]
})

let stopIdCounter = 3
const addGradientStop = () => {
  gradientSettings.value.stops.push({
    id: stopIdCounter++,
    color: '#FFFFFF',
    opacity: 100,
    position: 50
  })
  gradientSettings.value.stops.sort((a, b) => a.position - b.position)
}

const removeGradientStop = (id) => {
  if (gradientSettings.value.stops.length > 2) {
    gradientSettings.value.stops = gradientSettings.value.stops.filter(s => s.id !== id)
  }
}

const hexToRgba = (hex, opacity) => {
  let h = hex.replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const r = parseInt(h.substring(0,2), 16) || 0;
  const g = parseInt(h.substring(2,4), 16) || 0;
  const b = parseInt(h.substring(4,6), 16) || 0;
  return `rgba(${r}, ${g}, ${b}, ${opacity / 100})`;
}

watch([transparentSettings, () => newColor.value.category], () => {
  if (newColor.value.category === 'transparent') {
    newColor.value.value = hexToRgba(transparentSettings.value.baseColor, transparentSettings.value.opacity)
  }
}, { deep: true })

watch([gradientSettings, () => newColor.value.category], () => {
  if (newColor.value.category === 'gradient') {
    const stopStrings = [...gradientSettings.value.stops]
      .sort((a, b) => a.position - b.position)
      .map(stop => {
        const rgba = hexToRgba(stop.color, stop.opacity)
        return `${rgba} ${stop.position}%`
      })
      .join(', ')
      
    if (gradientSettings.value.type === 'linear') {
      newColor.value.value = `linear-gradient(${gradientSettings.value.angle}deg, ${stopStrings})`
    } else if (gradientSettings.value.type === 'radial') {
      newColor.value.value = `radial-gradient(circle, ${stopStrings})`
    } else if (gradientSettings.value.type === 'conic') {
      newColor.value.value = `conic-gradient(from ${gradientSettings.value.angle}deg, ${stopStrings})`
    }
  }
}, { deep: true })

const categoryForKey = (key) => {
  if (key.startsWith('slide-bg-')) return 'slide-bg'
  if (key.startsWith('item-accent-')) return 'item-accent'
  if (key.startsWith('chart-')) return 'chart'
  if (key.startsWith('bg-')) return 'surface'
  if (key.startsWith('text-')) return 'text'
  if (key.startsWith('border-')) return 'border'
  if (key.startsWith('color-')) return 'role'
  if (key.startsWith('gradient-') || key.startsWith('glow-') || key.startsWith('glass-') || key.startsWith('pattern-')) return 'effect'
  return 'other'
}
const categories = [
  { id: 'all', name: 'Все' },
  { id: 'custom', name: 'Мои' },
  { id: 'surface', name: 'Поверхности' },
  { id: 'text', name: 'Текст' },
  { id: 'role', name: 'Роли' },
  { id: 'item-accent', name: 'Шахматка' },
  { id: 'slide-bg', name: 'Фоны слайдов' },
  { id: 'chart', name: 'Графики' },
  { id: 'effect', name: 'Эффекты' },
  { id: 'solid', name: 'Сплошные' },
  { id: 'gradient', name: 'Градиенты' },
  { id: 'transparent', name: 'Полупрозрачные' }
]

const resolveProjectId = async () => {
  if (props.projectId) return Number(props.projectId)
  if (props.presentationId) {
    try {
      const data = await fetchPresentationTokens(Number(props.presentationId))
      // presentation tokens already merged, but we need project id for save; fallback to fetchProjects
      if (data && data.project_id) return Number(data.project_id)
    } catch {}
  }
  // Fallback: try to infer from current URL /p/{id} or it2b
  const m = typeof window !== 'undefined' ? window.location.pathname.match(/\/p\/(\d+)/) : null
  if (m) {
    try {
      const data = await fetchPresentationTokens(Number(m[1]))
      if (data && data.project_id) return Number(data.project_id)
    } catch {}
  }
  const projects = await fetchProjectsSummary()
  const it2b = projects.find(p => p.slug === 'it2b')
  return it2b ? it2b.id : null
}

const loadColors = async () => {
  try {
    loading.value = true
    // Prefer presentation tokens (merged global→project) for realistic preview of current preso
    if (props.presentationId) {
      try {
        const data = await fetchPresentationTokens(Number(props.presentationId))
        if (data && data.tokens && Object.keys(data.tokens).length) {
          colors.value = Object.values(data.tokens).map(t => ({
            name: t.key,
            value: t.value,
            category: categoryForKey(t.key),
            custom: t.custom === true
          }))
          return
        }
      } catch {}
    }
    const pid = await resolveProjectId()
    if (pid) {
      const data = await fetchProjectColors(pid)
      colors.value = data.map(c => ({ ...c, category: categoryForKey(c.name), custom: c.custom === true }))
    }
  } catch (e) {
    console.error("Failed to load colors", e)
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadColors()
  }
}, { immediate: true })

const filteredColors = computed(() => {
  if (activeCategory.value === 'all') return colors.value
  if (activeCategory.value === 'custom') return colors.value.filter(c => c.custom === true)
  if (activeCategory.value === 'solid') return colors.value.filter(c => c.category === 'solid' || c.category === 'role' || c.category === 'item-accent' || c.category === 'slide-bg' || c.category === 'chart' || c.category === 'surface' || c.category === 'text')
  return colors.value.filter(c => c.category === activeCategory.value)
})

const selectColor = (color) => {
  // Вставляем ссылку на переменную, а не резолвленное значение —
  // правки токена на уровне проекта применятся автоматически (валидатор принимает var(...))
  emit('select', `var(--${color.name})`)
  emit('close')
}

const editMode = ref(false)
const editingColorId = ref(null)
const editingOriginalName = ref(null)
const editingIsCustom = computed(() => {
  if (!editMode.value || !editingOriginalName.value) return true
  const orig = colors.value.find(c => c.name === editingOriginalName.value)
  return orig ? orig.custom === true : true
})

const parseGradient = (cssValue) => {
  let type = 'linear'
  let angle = 90
  if (cssValue.startsWith('radial')) type = 'radial'
  if (cssValue.startsWith('conic')) type = 'conic'
  
  if (type === 'linear') {
    const m = cssValue.match(/linear-gradient\(([\d.]+)deg/)
    if (m) angle = parseFloat(m[1])
  } else if (type === 'conic') {
    const m = cssValue.match(/conic-gradient\(from ([\d.]+)deg/)
    if (m) angle = parseFloat(m[1])
  }
  
  const stops = []
  const stopRegex = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)\s+([\d.]+)%/g;
  let match;
  let id = 1;
  while ((match = stopRegex.exec(cssValue)) !== null) {
    const r = parseInt(match[1]), g = parseInt(match[2]), b = parseInt(match[3])
    const a = match[4] !== undefined ? parseFloat(match[4]) : 1
    const pos = parseFloat(match[5])
    const hex = "#" + (1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1).toUpperCase()
    stops.push({ id: id++, color: hex, opacity: Math.round(a * 100), position: pos })
  }
  
  return { type, angle, stops }
}

const parseTransparent = (cssValue) => {
  const m = cssValue.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/)
  if (m) {
    const r = parseInt(m[1]), g = parseInt(m[2]), b = parseInt(m[3])
    const a = m[4] !== undefined ? parseFloat(m[4]) : 1
    const hex = "#" + (1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1).toUpperCase()
    return { baseColor: hex, opacity: Math.round(a * 100) }
  }
  return { baseColor: '#000000', opacity: 50 }
}

const startEdit = (color, e) => {
  e.stopPropagation()
  // Дефолты правим только в настройках проекта (adminMode), в обычном режиме — locked
  if (!color.custom && !props.adminMode) return
  editMode.value = true
  editingColorId.value = color.id
  editingOriginalName.value = color.name

  newColor.value = {
    name: color.name,
    value: color.value,
    category: color.category
  }
  
  if (color.category === 'gradient') {
    const parsed = parseGradient(color.value)
    if (parsed.stops.length > 0) gradientSettings.value = parsed
  } else if (color.category === 'transparent') {
    transparentSettings.value = parseTransparent(color.value)
  }
}

const cancelEdit = () => {
  editMode.value = false
  editingColorId.value = null
  editingOriginalName.value = null
  newColor.value = { name: '', value: '#FFFFFF', category: 'solid' }
}

const handleSave = async () => {
  if (!newColor.value.name || !newColor.value.value) return
  try {
    const pid = await resolveProjectId()
    if (!pid) return
    const renamed = editMode.value && editingOriginalName.value && editingOriginalName.value !== newColor.value.name
    if (editMode.value) {
      const idx = colors.value.findIndex(c => c.name === editingOriginalName.value || c.name === newColor.value.name || c.id === editingColorId.value)
      if (idx !== -1) {
        // Дефолт переименовывать нельзя — имя зафиксировано, правится только значение
        if (!colors.value[idx].custom) newColor.value.name = editingOriginalName.value
        colors.value[idx] = { ...colors.value[idx], ...newColor.value, category: categoryForKey(newColor.value.name) }
      }
    } else {
      colors.value.push({ ...newColor.value, category: categoryForKey(newColor.value.name), custom: true })
    }

    // Single-key PUT: шлём ТОЛЬКО изменённый токен. Full-list PUT дублировал
    // всю палитру в скоуп проекта и теневым копированием замораживал её
    // (пересевы global переставали действовать на проект).
    const tokensObj = { [newColor.value.name]: newColor.value.value }

    // Send to current project (not hardcoded it2b)
    const res = await upsertProjectTokens(pid, tokensObj)

    // Переименование custom: старый ключ в БД orphan — удаляем.
    // Сверяем имена ПОСЛЕ гарда (дефолту имя сброшено → условие ложно → дефолт цел)
    if (renamed && newColor.value.name !== editingOriginalName.value) {
      try { await deleteProjectToken(pid, editingOriginalName.value) } catch {}
    }

      // Reload colors from API to ensure we have the exact saved representation
      if (res && res.tokens) {
         colors.value = Object.values(res.tokens).map(t => ({
          name: t.key,
          value: t.value,
          category: categoryForKey(t.key),
          custom: t.custom === true
        }))
      }

      cancelEdit()
  } catch (e) {
    console.error("Failed to save color", e)
  }
}

const deleteColor = async (color, e) => {
  e.stopPropagation()
  if (!color.custom) return  // дефолты удалять запрещено (403 и на бэкенде)
  try {
    const pid = await resolveProjectId()
    if (!pid) return
    await deleteProjectToken(pid, color.name)
    colors.value = colors.value.filter(c => c.name !== color.name)
    if (editMode.value && editingOriginalName.value === color.name) cancelEdit()
  } catch (err) {
    console.error("Failed to delete color", err)
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="emit('close')"></div>
    
    <!-- Modal -->
    <div class="relative bg-bg-base border border-text-muted rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-text-muted bg-bg-surface/50">
        <h2 class="text-2xl font-bold font-heading text-text-primary flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-color-secondary"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
          Библиотека цветов
        </h2>
        <button @click="emit('close')" class="text-text-secondary hover:text-text-primary transition-colors bg-bg-surface hover:bg-bg-surface p-2 rounded-xl">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
      
      <!-- Content -->
      <div class="flex flex-col md:flex-row flex-1 min-h-0">
        <!-- Main Area -->
        <div class="flex-1 p-6 overflow-y-auto">
          <!-- Tabs (на телефоне — горизонтальный скролл) -->
          <div class="mb-8 max-w-full overflow-x-auto hide-scrollbar">
            <div class="flex gap-2 bg-bg-surface p-1.5 rounded-xl w-max border border-text-muted">
              <button 
                v-for="cat in categories" :key="cat.id"
                @click="activeCategory = cat.id"
                class="px-5 py-2 rounded-lg text-sm font-bold transition-all whitespace-nowrap"
                :class="activeCategory === cat.id ? 'bg-color-secondary text-white shadow-lg' : 'text-text-secondary hover:text-text-primary hover:bg-bg-surface'"
              >
                {{ cat.name }}
              </button>
            </div>
          </div>
          
          <div v-if="loading" class="flex justify-center items-center h-40">
            <div class="animate-spin w-8 h-8 border-4 border-color-secondary border-t-transparent rounded-full"></div>
          </div>
          
          <div v-else-if="filteredColors.length === 0" class="text-center py-12 border-2 border-dashed border-text-muted rounded-xl">
            <p class="text-text-secondary font-medium">Нет цветов в этой категории</p>
          </div>
          
          <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div 
              v-for="color in filteredColors" :key="color.id"
              @click="selectColor(color)"
              class="group cursor-pointer flex flex-col"
            >
              <div 
                class="w-full aspect-square rounded-xl border border-text-muted hover:scale-105 transition-transform duration-300 shadow-md relative overflow-hidden"
                :style="{ background: color.value }"
              >
                <!-- Checkered background for transparent colors -->
                <div v-if="color.category === 'transparent'" class="absolute inset-0 -z-10 opacity-20" style="background-image: linear-gradient(45deg, #808080 25%, transparent 25%), linear-gradient(-45deg, #808080 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #808080 75%), linear-gradient(-45deg, transparent 75%, #808080 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;"></div>
                
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span class="text-text-primary font-bold text-sm bg-black/50 px-3 py-1 rounded-lg backdrop-blur-sm">Выбрать</span>
                </div>
              </div>
              <div class="mt-2 relative group/item pr-12">
                <p class="text-text-primary font-medium text-sm truncate flex items-center gap-1.5" :title="color.name">
                  {{ color.name }}
                  <svg v-if="!color.custom" xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-text-muted shrink-0" :title="adminMode ? 'Дефолт темы (удаление запрещено)' : 'Дефолт темы — правится в настройках проекта'"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                  <span v-else class="text-[9px] font-bold uppercase tracking-wider text-color-secondary bg-color-secondary/10 px-1.5 py-0.5 rounded">мой</span>
                </p>
                <button v-if="color.custom || adminMode" @click="startEdit(color, $event)" class="absolute right-6 top-0 text-text-muted hover:text-white bg-bg-surface hover:bg-color-secondary rounded p-1 opacity-0 group-hover/item:opacity-100 transition-all z-10" title="Редактировать">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                </button>
                <button v-if="color.custom" @click="deleteColor(color, $event)" class="absolute right-0 top-0 text-text-muted hover:text-red-400 hover:bg-red-500/20 rounded p-1 opacity-0 group-hover/item:opacity-100 transition-all z-10" title="Удалить">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
                <p class="text-text-muted text-xs truncate font-mono" :title="`var(--${color.name})`">var(--{{ color.name }})</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Sidebar: Add new color -->
        <div class="w-full md:w-80 border-l border-text-muted bg-bg-surface/30 p-6 flex flex-col gap-5 overflow-y-auto">
          <h3 class="text-lg font-bold text-text-primary mb-2">{{ editMode ? 'Редактировать цвет' : 'Добавить цвет' }}</h3>
          
          <div>
            <label class="block text-xs font-bold text-text-secondary mb-1.5 uppercase tracking-wider">Название</label>
            <input v-model="newColor.name" type="text" placeholder="e.g. primary-button" :disabled="editMode && !editingIsCustom" class="w-full bg-bg-base border border-text-muted rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-color-secondary disabled:opacity-50" :title="editMode && !editingIsCustom ? 'Имя дефолта зафиксировано' : ''" />
          </div>
          
          <div>
            <label class="block text-xs font-bold text-text-secondary mb-1.5 uppercase tracking-wider">Категория</label>
            <select v-model="newColor.category" class="w-full bg-bg-base border border-text-muted rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-color-secondary">
              <option value="solid">Сплошной (Solid)</option>
              <option value="gradient">Градиент (Gradient)</option>
              <option value="transparent">Полупрозрачный (Transparent)</option>
            </select>
          </div>
          
          <!-- Dynamic Settings based on Category -->
          <div v-if="newColor.category === 'transparent'" class="space-y-4 border border-text-muted rounded-xl p-4 bg-black/20">
            <div>
              <label class="block text-[10px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">Базовый цвет</label>
              <div class="flex gap-2">
                <input v-model="transparentSettings.baseColor" type="text" class="flex-1 bg-bg-base border border-text-muted rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-color-secondary font-mono text-sm min-w-0" />
                <input v-model="transparentSettings.baseColor" type="color" class="w-9 h-9 rounded-lg cursor-pointer bg-bg-base border border-text-muted p-0.5 shrink-0">
              </div>
            </div>
            <div>
              <label class="flex justify-between text-[10px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">
                <span>Непрозрачность</span>
                <span class="text-color-secondary">{{ transparentSettings.opacity }}%</span>
              </label>
              <input v-model="transparentSettings.opacity" type="range" min="0" max="100" class="w-full accent-color-secondary">
            </div>
          </div>

          <div v-else-if="newColor.category === 'gradient'" class="space-y-4 border border-text-muted rounded-xl p-4 bg-black/20">
            <div>
              <label class="block text-[10px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">Тип градиента</label>
              <select v-model="gradientSettings.type" class="w-full bg-bg-base border border-text-muted rounded-lg px-3 py-2 text-text-primary text-xs focus:outline-none focus:border-color-secondary">
                <option value="linear">Линейный (Linear)</option>
                <option value="radial">Радиальный (Radial)</option>
                <option value="conic">Конический (Conic)</option>
              </select>
            </div>
            
            <div v-if="gradientSettings.type !== 'radial'">
              <label class="flex justify-between text-[10px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">
                <span>Угол (градусы)</span>
                <span class="text-color-secondary">{{ gradientSettings.angle }}°</span>
              </label>
              <input v-model="gradientSettings.angle" type="range" min="0" max="360" class="w-full accent-color-secondary">
            </div>
            
            <div class="space-y-3">
              <label class="block text-[10px] font-bold text-text-secondary uppercase tracking-wider">Точки цвета (Stops)</label>
              <div v-for="(stop, index) in gradientSettings.stops" :key="stop.id" class="flex flex-col gap-2 p-3 bg-bg-base rounded-lg border border-text-muted relative group">
                <button v-if="gradientSettings.stops.length > 2" @click="removeGradientStop(stop.id)" class="absolute top-2 right-2 text-red-500 opacity-50 hover:opacity-100 hover:bg-red-500/20 p-1 rounded transition-all" title="Удалить">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
                <div class="flex gap-2 mr-6">
                  <input v-model="stop.color" type="text" class="w-20 bg-bg-surface border border-text-muted rounded-md px-2 py-1 text-text-primary focus:outline-none focus:border-color-secondary font-mono text-xs" />
                  <input v-model="stop.color" type="color" class="w-7 h-7 rounded cursor-pointer bg-bg-surface border border-text-muted p-0 shrink-0">
                </div>
                <div class="flex gap-4 text-[10px] text-text-secondary mt-1">
                  <div class="flex-1">
                    <div class="flex justify-between mb-1">
                      <span>Позиция</span>
                      <span class="text-color-secondary">{{ stop.position }}%</span>
                    </div>
                    <input 
                      v-model.number="stop.position" 
                      type="range" 
                      :min="index > 0 ? gradientSettings.stops[index - 1].position : 0" 
                      :max="index < gradientSettings.stops.length - 1 ? gradientSettings.stops[index + 1].position : 100" 
                      class="w-full accent-color-secondary"
                    >
                  </div>
                  <div class="flex-1">
                    <div class="flex justify-between mb-1">
                      <span>Непрозрачн.</span>
                      <span class="text-color-secondary">{{ stop.opacity }}%</span>
                    </div>
                    <input v-model.number="stop.opacity" type="range" min="0" max="100" class="w-full accent-color-secondary">
                  </div>
                </div>
              </div>
              
              <button @click="addGradientStop" class="w-full py-2 border border-dashed border-text-secondary rounded-lg text-text-secondary hover:text-text-primary hover:border-color-secondary hover:bg-color-secondary/10 transition-all text-xs flex items-center justify-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                Добавить точку
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-text-secondary mb-1.5 uppercase tracking-wider">Итоговое значение (CSS)</label>
            <div class="flex gap-2">
              <input v-model="newColor.value" type="text" placeholder="#FF0000 или linear-gradient(...)" class="flex-1 bg-bg-base border border-text-muted rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-color-secondary font-mono text-sm min-w-0" />
              <input v-if="newColor.category === 'solid'" v-model="newColor.value" type="color" class="w-11 h-11 rounded-lg cursor-pointer bg-bg-base border border-text-muted p-0.5 shrink-0" title="Выбрать цвет">
            </div>
          </div>
          
          <div class="mt-2 p-4 rounded-xl border border-text-muted h-24 flex items-center justify-center relative overflow-hidden" :style="{ background: newColor.value }">
            <div v-if="newColor.category === 'transparent'" class="absolute inset-0 -z-10 opacity-20" style="background-image: linear-gradient(45deg, #808080 25%, transparent 25%), linear-gradient(-45deg, #808080 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #808080 75%), linear-gradient(-45deg, transparent 75%, #808080 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;"></div>
            <span class="text-text-primary font-bold drop-shadow-md text-sm">Превью</span>
          </div>
          
          <div class="flex gap-2 mt-4">
            <button v-if="editMode" @click="cancelEdit" class="flex-1 bg-bg-surface hover:bg-bg-hover text-text-primary font-bold py-3 rounded-xl transition-all text-sm">
              Отмена
            </button>
            <button @click="handleSave" class="flex-[2] bg-gradient-to-r from-color-secondary to-color-primary hover:opacity-90 text-text-primary font-bold py-3 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 text-sm">
              <svg v-if="!editMode" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              {{ editMode ? 'Сохранить' : 'Добавить' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
