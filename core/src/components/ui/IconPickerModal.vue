<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 backdrop-blur-md">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-bg-base/80" @click="$emit('close')"></div>
    
    <!-- Modal -->
    <div class="bg-bg-hover border border-text-muted rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl relative z-10 overflow-hidden transform transition-all">
      <!-- Header -->
      <div class="flex justify-between items-center p-6 border-b border-text-muted">
        <h2 class="text-xl font-bold text-text-primary flex items-center gap-2">
          <Icon icon="heroicons:sparkles" class="text-[#A78BFA]" /> 
          Icon Picker (Iconify)
        </h2>
        <button @click="$emit('close')" class="text-text-secondary hover:text-text-primary transition-colors bg-bg-surface hover:bg-bg-surface p-2 rounded-lg">
          <Icon icon="heroicons:x-mark" class="w-5 h-5" />
        </button>
      </div>

      <!-- Search -->
      <div class="p-6 border-b border-text-muted bg-bg-surface/50">
        <div class="relative">
          <Icon icon="heroicons:magnifying-glass" class="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted text-lg" />
          <input 
            v-model="searchQuery" 
            @keyup.enter="searchIcons"
            type="text" 
            placeholder="Search icons (e.g., arrow, check, user, star)..."
            class="w-full bg-bg-surface border border-text-muted rounded-xl pl-12 pr-4 py-3 text-text-primary focus:outline-none focus:border-[#A78BFA] transition-colors"
          >
          <button @click="searchIcons" class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-[#A78BFA] text-text-primary rounded-lg text-sm font-bold hover:bg-[#8B5CF6] transition-colors">
            Search
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto flex-1 min-h-[400px]">
        <div v-if="isLoading" class="flex flex-col items-center justify-center h-full text-text-secondary gap-4">
          <Icon icon="heroicons:arrow-path" class="w-8 h-8 animate-spin text-[#A78BFA]" />
          <p>Searching icons via API...</p>
        </div>
        
        <div v-else-if="icons.length === 0 && hasSearched" class="flex flex-col items-center justify-center h-full text-text-secondary">
          <Icon icon="heroicons:face-frown" class="w-12 h-12 mb-4 opacity-50" />
          <p>No icons found for "{{ searchQuery }}"</p>
        </div>
        
        <div v-else-if="icons.length === 0" class="flex flex-col items-center justify-center h-full text-text-muted">
          <Icon icon="heroicons:sparkles" class="w-16 h-16 mb-4 opacity-20" />
          <p>Type a keyword above and press Enter to search.</p>
        </div>
        
        <div v-else class="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-4">
          <div 
            v-for="icon in icons" 
            :key="icon"
            @click="selectIcon(icon)"
            class="aspect-square bg-bg-surface border border-text-muted rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-bg-surface hover:border-[#A78BFA]/50 transition-all group"
            :title="icon"
          >
            <Icon :icon="icon" class="text-3xl text-text-secondary group-hover:text-[#A78BFA] transition-colors" />
            <span class="text-[10px] text-text-muted truncate w-full px-2 text-center group-hover:text-text-primary transition-colors">{{ icon.split(':')[1] }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'select'])

const searchQuery = ref('')
const icons = ref([])
const isLoading = ref(false)
const hasSearched = ref(false)

const searchIcons = async () => {
  if (!searchQuery.value.trim()) return
  
  isLoading.value = true
  hasSearched.value = true
  icons.value = []
  
  try {
    const res = await fetch(`https://api.iconify.design/search?query=${encodeURIComponent(searchQuery.value)}&limit=104`)
    const data = await res.json()
    icons.value = data.icons || []
  } catch (err) {
    console.error("Failed to fetch icons:", err)
    alert("Failed to search icons. Please check network.")
  } finally {
    isLoading.value = false
  }
}

const selectIcon = (iconName) => {
  emit('select', iconName)
  emit('close')
}

watch(() => props.isOpen, (val) => {
  if (val && !hasSearched.value) {
    searchQuery.value = 'check'
    searchIcons()
  }
})
</script>
