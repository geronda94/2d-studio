<template>
  <div v-if="isOpen" class="fixed inset-0 z-[400] flex items-center justify-center">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')"></div>

    <div class="relative bg-bg-surface w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-text-muted flex flex-col">
      <!-- Header -->
      <div class="p-5 border-b border-text-muted flex justify-between items-center bg-bg-hover">
        <h2 class="text-xl font-bold text-text-primary flex items-center gap-2">
          <span class="text-2xl">🤖</span> Сгенерировать ИИ Голос (Gemini)
        </h2>
        <button @click="$emit('close')" class="text-text-secondary hover:text-text-primary transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 overflow-y-auto max-h-[70vh] flex flex-col gap-5">
        <!-- Text Input -->
        <div v-if="!isEditing">
          <div class="flex justify-between items-center mb-2">
            <label class="block text-sm font-medium text-text-secondary">Текст для озвучки</label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="isBatchMode" class="accent-color-primary" />
              <span class="text-xs font-medium text-text-secondary hover:text-text-primary">Пакетный режим</span>
            </label>
          </div>
          
          <template v-if="!isBatchMode || batchBlocks.length === 0">
            <textarea v-model="formData.text" rows="5" class="w-full bg-bg-surface border border-text-muted rounded-xl p-4 text-text-primary placeholder-white/30 focus:outline-none focus:border-color-primary resize-none" placeholder="Введите текст, который нужно озвучить..."></textarea>
            <button v-if="isBatchMode" @click="splitText" class="mt-2 w-full py-2 bg-bg-surface hover:bg-bg-surface text-text-primary rounded-lg text-sm font-bold transition-colors">Разбить на фрагменты (по абзацам)</button>
          </template>
          
          <template v-else>
            <div class="space-y-3 max-h-64 overflow-y-auto pr-2">
              <div v-for="(block, idx) in batchBlocks" :key="idx" class="relative group">
                <textarea v-model="batchBlocks[idx]" rows="2" class="w-full bg-bg-surface border border-text-muted rounded-xl p-3 text-text-primary text-sm focus:outline-none focus:border-color-primary resize-none"></textarea>
                <button @click="batchBlocks.splice(idx, 1)" class="absolute top-2 right-2 p-1 bg-red-500/20 text-red-400 rounded opacity-0 group-hover:opacity-100 transition-opacity">X</button>
              </div>
            </div>
            <div class="flex gap-2 mt-2">
              <button @click="batchBlocks.push('')" class="flex-1 py-2 bg-bg-surface hover:bg-bg-surface text-text-primary rounded-lg text-sm transition-colors">+ Добавить блок</button>
              <button @click="batchBlocks = []; isBatchMode = false" class="flex-1 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm transition-colors">Отмена</button>
            </div>
          </template>
        </div>
        <div v-else>
          <label class="block text-sm font-medium text-text-secondary mb-2">Оригинальный текст</label>
          <div class="w-full bg-bg-surface border border-text-muted rounded-xl p-4 text-text-secondary text-sm italic">{{ formData.text }}</div>
          <p class="text-xs text-color-primary mt-2">В режиме редактирования вы можете изменить только настройки воспроизведения (скорость). Чтобы изменить текст, сгенерируйте новый клип.</p>
        </div>

        <!-- Playback Settings (Prominent in Editing) -->
        <div v-if="isEditing" class="bg-color-success/10 border border-color-success/30 p-4 rounded-xl">
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-bold text-text-primary">Playback Speed (Скорость)</label>
            <span class="text-sm font-bold text-color-success">{{ formData.playbackRate }}x</span>
          </div>
          <input type="range" v-model.number="formData.playbackRate" min="0.5" max="2.0" step="0.05" class="w-full accent-color-success" />
          <p class="text-xs text-text-secondary mt-2">Изменение скорости повлияет только на воспроизведение клипа на таймлайне.</p>
        </div>

        <div v-if="!isEditing">
          <div class="flex justify-between items-center mb-2">
            <label class="block text-sm font-medium text-text-secondary">Temperature (Эмоциональность/Случайность)</label>
            <span class="text-sm font-bold text-color-primary">{{ formData.temperature }}</span>
          </div>
          <input type="range" v-model.number="formData.temperature" min="0.0" max="2.0" step="0.1" class="w-full accent-color-primary" />
        </div>

        <!-- Voice Selection -->
        <div v-if="!isEditing">
          <label class="block text-sm font-medium text-text-secondary mb-2">Голос диктора</label>
          <select v-model="formData.voice" class="w-full bg-bg-surface border border-text-muted rounded-xl p-3 text-text-primary focus:outline-none focus:border-color-primary">
            <option value="Charon">Charon (Низкий, уверенный, мужской)</option>
            <option value="Aoede">Aoede (Мягкий, женский)</option>
            <option value="Fenrir">Fenrir (Мужской, энергичный)</option>
            <option value="Kore">Kore (Спокойный, женский)</option>
            <option value="Puck">Puck (Высокий, веселый)</option>
          </select>
        </div>

        <!-- Advanced Settings -->
        <details v-if="!isEditing" class="group bg-bg-surface rounded-xl border border-text-muted overflow-hidden">
          <summary class="p-4 cursor-pointer text-text-primary font-medium flex items-center justify-between select-none hover:bg-bg-surface transition-colors">
            Расширенные настройки (Режиссура)
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transform group-open:rotate-180 transition-transform"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </summary>
          <div class="p-4 border-t border-text-muted flex flex-col gap-4 bg-black/20">
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1">Audio Profile (Профиль аудио)</label>
              <input type="text" v-model="formData.audio_profile" class="w-full bg-bg-surface border border-text-muted rounded-lg p-2 text-sm text-text-primary focus:outline-none focus:border-color-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1">Style (Стиль)</label>
              <input type="text" v-model="formData.style" class="w-full bg-bg-surface border border-text-muted rounded-lg p-2 text-sm text-text-primary focus:outline-none focus:border-color-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1">Pace (Темп)</label>
              <input type="text" v-model="formData.pace" class="w-full bg-bg-surface border border-text-muted rounded-lg p-2 text-sm text-text-primary focus:outline-none focus:border-color-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1">Tone (Тон)</label>
              <input type="text" v-model="formData.tone" class="w-full bg-bg-surface border border-text-muted rounded-lg p-2 text-sm text-text-primary focus:outline-none focus:border-color-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-secondary mb-1">Scene (Сцена)</label>
              <input type="text" v-model="formData.scene" class="w-full bg-bg-surface border border-text-muted rounded-lg p-2 text-sm text-text-primary focus:outline-none focus:border-color-primary" />
            </div>
          </div>
        </details>
      </div>

      <!-- Footer Actions -->
      <div class="p-5 border-t border-text-muted bg-bg-hover flex justify-end gap-3">
        <button @click="$emit('close')" class="px-5 py-2.5 rounded-xl font-medium text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors">Отмена</button>
        <button v-if="!isEditing" @click="handleGenerate" :disabled="isGenerating || (!isBatchMode && !formData.text.trim()) || (isBatchMode && batchBlocks.length === 0)" class="px-5 py-2.5 rounded-xl font-bold text-white bg-color-primary hover:bg-color-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shadow-lg shadow-color-primary/30">
          <svg v-if="isGenerating" class="animate-spin -ml-1 mr-2 h-4 w-4 text-text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <span v-if="isGenerating">Генерация...</span>
          <span v-else>{{ isBatchMode && batchBlocks.length > 0 ? 'Сгенерировать пакет (' + batchBlocks.length + ')' : 'Сгенерировать' }}</span>
        </button>
        <button v-else @click="handleUpdate" class="px-5 py-2.5 rounded-xl font-bold text-white bg-color-success hover:bg-color-success/80 transition-colors flex items-center gap-2 shadow-lg shadow-color-success/30">
          Сохранить изменения
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { generateAIVoice } from '../../services/api'

const props = defineProps({
  isOpen: Boolean,
  presentationId: {
    type: Number,
    required: true
  },
  initialData: {
    type: Object,
    default: null
  },
  // BRAND KIT: дефолты голоса проекта (voice/temperature/style/pace/tone/scene/audio_profile)
  defaults: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'generated', 'updated'])

const isGenerating = ref(false)
const isBatchMode = ref(false)
const batchBlocks = ref([])
const isEditing = ref(false)

const splitText = () => {
  batchBlocks.value = formData.text.split(/\n+/).map(t => t.trim()).filter(t => t.length > 0)
}

const getDefaultFormData = () => ({
  text: '',
  voice: 'Charon',
  audio_profile: 'A confident and dynamic tech expert with a deep, resonant voice.',
  style: 'Engaging and professional.',
  pace: 'Fast, continuous, and energetic, with absolutely no long pauses.',
  tone: 'Authoritative, convincing, and lively.',
  scene: 'A high-end tech YouTube channel.',
  temperature: 0.9,
  playbackRate: 1.0
})

const formData = reactive(getDefaultFormData())

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    isBatchMode.value = false
    batchBlocks.value = []
    
    if (props.initialData && props.initialData.isEditing) {
      isEditing.value = true
      Object.assign(formData, getDefaultFormData())
      if (props.defaults) Object.assign(formData, props.defaults)
      formData.text = props.initialData.text || ''
      if (props.initialData.settings) {
        Object.assign(formData, props.initialData.settings)
      }
      formData.playbackRate = props.initialData.playbackRate || 1.0
    } else if (props.initialData) {
      isEditing.value = false
      Object.assign(formData, getDefaultFormData())
      if (props.defaults) Object.assign(formData, props.defaults)
      formData.text = props.initialData.text || ''
      if (props.initialData.settings) {
        Object.assign(formData, props.initialData.settings)
      }
    } else {
      isEditing.value = false
      Object.assign(formData, getDefaultFormData())
      if (props.defaults) Object.assign(formData, props.defaults)
    }
  }
})

const handleGenerate = async () => {
  isGenerating.value = true
  try {
    let textsToGenerate = []
    let batchId = null
    
    if (isBatchMode.value && batchBlocks.value.length > 0) {
      textsToGenerate = batchBlocks.value.filter(t => t.trim().length > 0)
      batchId = "batch_" + Math.random().toString(36).substring(2, 9)
    } else {
      if (!formData.text.trim()) return
      textsToGenerate = [formData.text.trim()]
    }
    
    const results = []
    
    // Sequential generation
    for (const txt of textsToGenerate) {
      const payload = {
        text: txt,
        voice: formData.voice,
        audio_profile: formData.audio_profile,
        style: formData.style,
        pace: formData.pace,
        tone: formData.tone,
        scene: formData.scene,
        temperature: formData.temperature,
        batch_id: batchId
      }
      const mediaFile = await generateAIVoice(props.presentationId, payload)
      results.push(mediaFile)
    }
    
    emit('generated', results)
  } catch (error) {
    console.error('Failed to generate AI voice:', error)
    alert(error.message || 'Ошибка при генерации аудио')
  } finally {
    isGenerating.value = false
  }
}

const handleUpdate = () => {
  emit('updated', {
    ...props.initialData,
    playbackRate: formData.playbackRate,
    settings: {
      ...props.initialData.settings,
      temperature: formData.temperature,
      voice: formData.voice,
      audio_profile: formData.audio_profile,
      style: formData.style,
      pace: formData.pace,
      tone: formData.tone,
      scene: formData.scene
    }
  })
}
</script>
