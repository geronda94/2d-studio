<template>
  <div v-if="isOpen" class="fixed inset-0 z-[200] flex items-center justify-center p-2 md:p-0">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')"></div>
    
    <div class="relative bg-bg-base w-full max-w-[95vw] md:max-w-4xl h-[80dvh] rounded-2xl border border-text-muted shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Header -->
      <div class="p-6 border-b border-text-muted bg-bg-surface flex justify-between items-center shrink-0">
        <div>
          <h2 class="text-xl font-bold text-text-primary">Выбор компонента</h2>
          <p class="text-text-secondary text-sm mt-1">Выберите компонент для нового слайда</p>
        </div>
        <button @click="$emit('close')" class="p-2 text-text-secondary hover:text-text-primary transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
      
      <!-- Body -->
      <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
        <!-- Фильтры: desktop — сайдбар, mobile — горизонтальные чипы -->
        <div class="w-full md:w-64 shrink-0 border-b md:border-b-0 md:border-r border-text-muted bg-bg-hover p-2 md:p-4 flex flex-row md:flex-col gap-2 md:gap-6 overflow-x-auto md:overflow-y-auto hide-scrollbar">
          <div class="shrink-0">
            <h3 class="hidden md:block text-xs font-bold text-text-muted uppercase tracking-wider mb-3">По типу</h3>
            <div class="flex flex-row md:flex-col gap-1 md:gap-0 md:space-y-1">
              <button 
                class="w-auto md:w-full shrink-0 whitespace-nowrap text-left px-3 py-2 rounded-lg text-sm transition-colors"
                :class="!selectedType ? 'bg-color-primary text-white font-bold' : 'text-text-secondary hover:bg-bg-surface'"
                @click="selectedType = null"
              >
                Все типы
              </button>
              <button 
                v-for="t in types" :key="t.id"
                class="w-auto md:w-full shrink-0 whitespace-nowrap text-left px-3 py-2 rounded-lg text-sm transition-colors"
                :class="selectedType === t.id ? 'bg-color-primary text-white font-bold' : 'text-text-secondary hover:bg-bg-surface'"
                @click="selectedType = t.id"
              >
                {{ t.name }}
              </button>
            </div>
          </div>
          
          <div class="shrink-0">
            <h3 class="hidden md:block text-xs font-bold text-text-muted uppercase tracking-wider mb-3">По категории</h3>
            <div class="flex flex-row md:flex-col gap-1 md:gap-0 md:space-y-1">
              <button 
                class="w-auto md:w-full shrink-0 whitespace-nowrap text-left px-3 py-2 rounded-lg text-sm transition-colors"
                :class="!selectedCategory ? 'bg-color-success text-white font-bold' : 'text-text-secondary hover:bg-bg-surface'"
                @click="selectedCategory = null"
              >
                Все категории
              </button>
              <button 
                v-for="c in categories" :key="c.id"
                class="w-auto md:w-full shrink-0 whitespace-nowrap text-left px-3 py-2 rounded-lg text-sm transition-colors"
                :class="selectedCategory === c.id ? 'bg-color-success text-white font-bold' : 'text-text-secondary hover:bg-bg-surface'"
                @click="selectedCategory = c.id"
              >
                {{ c.name }}
              </button>
            </div>
          </div>
        </div>
        
        <!-- Component Grid -->
        <div class="flex-1 p-3 md:p-6 overflow-y-auto bg-bg-base">
          <div v-if="loading" class="flex justify-center py-10">
            <div class="animate-pulse text-color-primary">Загрузка компонентов...</div>
          </div>
          <div v-else-if="filteredComponents.length === 0" class="text-center py-10 text-text-secondary">
            Компоненты не найдены по заданным фильтрам.
          </div>
          <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-3 md:gap-4">
            <div 
              v-for="comp in filteredComponents" :key="comp.id"
              @click="selectComponent(comp)"
              class="bg-bg-hover border border-text-muted rounded-xl hover:border-color-primary hover:bg-bg-hover/80 transition-all cursor-pointer group flex flex-col overflow-hidden"
            >
              <!-- Live Preview Area -->
              <div class="h-40 bg-bg-base border-b border-text-muted relative overflow-hidden flex items-center justify-center">
                <div 
                  class="absolute flex items-center justify-center overflow-hidden" 
                  style="width: 1280px; height: 720px; transform: scale(0.28); transform-origin: center; pointer-events: none; background-color: var(--bg-base);"
                >
                  <div class="w-full h-full flex flex-col items-center justify-center">
                    <SafeComponentPreview 
                      v-if="componentsMap && componentsMap[comp.slug]" 
                      :componentInstance="componentsMap[comp.slug]"
                      :componentName="comp.slug"
                      :payload="getPayload(comp)" 
                    />
                    <div v-else class="w-full h-full flex items-center justify-center text-4xl text-text-muted">
                      No Preview
                    </div>
                  </div>
                </div>
                <!-- Hover Overlay -->
                <div class="absolute inset-0 bg-color-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              </div>
              
              <!-- Info Area -->
              <div class="p-5 flex flex-col flex-1">
                <div class="flex justify-between items-start mb-2">
                  <h3 class="text-text-primary font-bold text-lg group-hover:text-color-primary transition-colors">{{ comp.title }}</h3>
                  <span v-if="comp.type" class="px-2 py-1 rounded bg-black/30 text-[10px] text-text-secondary font-mono">{{ comp.type.slug }}</span>
                </div>
                <p class="text-text-secondary text-sm mb-4 flex-1">{{ comp.description || 'Нет описания' }}</p>
                
                <div class="flex flex-wrap gap-2 mt-auto">
                  <span v-for="cat in comp.categories" :key="cat.id" class="px-2 py-0.5 rounded-full bg-color-success/10 text-color-success text-xs">
                    {{ cat.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { componentsMap } from '../../config/componentsRegistry.js'
import SafeComponentPreview from './SafeComponentPreview.vue'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'select'])

// Close on escape key
const handleKeydown = (e) => {
  if (props.isOpen && e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const components = ref([])
const categories = ref([])
const types = ref([])
const loading = ref(false)

const getPayload = (comp) => {
  if (!comp.default_payload) return {}
  if (typeof comp.default_payload === 'string') {
    try {
      return JSON.parse(comp.default_payload)
    } catch (e) {
      return {}
    }
  }
  return comp.default_payload
}

const selectedType = ref(null)
const selectedCategory = ref(null)

const API_BASE_URL = '/api'

const fetchData = async () => {
  if (components.value.length > 0) return // Already loaded
  loading.value = true
  try {
    const [compsRes, catsRes, typesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/components/`),
      fetch(`${API_BASE_URL}/components/categories`),
      fetch(`${API_BASE_URL}/components/types`)
    ])
    
    if (compsRes.ok) components.value = await compsRes.json()
    if (catsRes.ok) categories.value = await catsRes.json()
    if (typesRes.ok) types.value = await typesRes.json()
  } catch (err) {
    console.error("Failed to fetch component data:", err)
  } finally {
    loading.value = false
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchData()
  }
})

const filteredComponents = computed(() => {
  return components.value.filter(c => {
    const matchType = selectedType.value ? c.type_id === selectedType.value : true
    const matchCat = selectedCategory.value ? c.categories.some(cat => cat.id === selectedCategory.value) : true
    return matchType && matchCat
  })
})

const selectComponent = (comp) => {
  emit('select', comp)
}
</script>
