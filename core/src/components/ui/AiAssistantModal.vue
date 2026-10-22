<script setup>
import { ref, computed, watch } from 'vue'
import { generateSlides, applyChangeSet } from '../../services/api'

const props = defineProps({
  show: Boolean,
  presentationId: { type: [Number, String], default: null },
})

const emit = defineEmits(['close', 'applied'])

const script = ref('')
const slideCount = ref(null)
const generating = ref(false)
const applying = ref(false)
const proposal = ref(null) // {ops, valid, errors, warnings, diff}
const message = ref('')

watch(() => props.show, (open) => {
  if (open) {
    script.value = ''
    slideCount.value = null
    proposal.value = null
    message.value = ''
  }
})

const canApply = computed(() => proposal.value?.valid && proposal.value?.ops?.length && !applying.value)

const propose = async () => {
  if (!props.presentationId || generating.value) return
  generating.value = true
  message.value = ''
  proposal.value = null
  try {
    proposal.value = await generateSlides(props.presentationId, {
      script: script.value.trim() || undefined,
      slideCount: slideCount.value || undefined,
      apply: false,
    })
    if (!proposal.value.ops?.length) message.value = 'ИИ не предложил изменений'
  } catch (e) {
    message.value = e.message
  } finally {
    generating.value = false
  }
}

const apply = async () => {
  if (!canApply.value) return
  if (!confirm(`Применить ${proposal.value.ops.length} операций к презентации?`)) return
  applying.value = true
  message.value = ''
  try {
    const res = await applyChangeSet(props.presentationId, proposal.value.ops, false)
    if (res.valid && res.applied) {
      emit('applied', res)
      emit('close')
    } else {
      message.value = 'Не удалось применить: ' + (res.errors?.[0]?.message || 'ошибка валидации')
    }
  } catch (e) {
    message.value = e.message
  } finally {
    applying.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-[320] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="emit('close')"></div>
    <div class="relative bg-bg-surface border border-text-muted rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh]">
      <div class="flex items-center justify-between p-5 border-b border-text-muted">
        <h2 class="text-lg font-bold text-text-primary">✨ AI-ассистент</h2>
        <button @click="emit('close')" class="text-text-secondary hover:text-text-primary text-xl leading-none px-1">✕</button>
      </div>

      <div class="p-5 flex flex-col gap-4 overflow-y-auto">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1.5">Команда / сценарий</label>
          <textarea
            v-model="script"
            rows="4"
            placeholder="Например: сделай 3 слайда — проблема, решение, результат. Тон энергичный, без воды."
            class="w-full bg-bg-base border border-text-muted rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:border-color-secondary"
          ></textarea>
        </div>
        <label class="flex items-center gap-2 text-sm text-text-secondary">
          Слайдов (необязательно):
          <input v-model.number="slideCount" type="number" min="1" max="30" class="w-20 bg-bg-base border border-text-muted rounded-lg px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-color-secondary">
        </label>

        <div class="flex items-center gap-3">
          <button
            @click="propose"
            :disabled="generating"
            class="px-4 py-2 bg-color-primary hover:opacity-90 disabled:opacity-50 text-white text-sm font-bold rounded-lg transition-all"
          >
            {{ generating ? 'Генерирую…' : 'Предложить' }}
          </button>
          <button
            @click="apply"
            :disabled="!canApply"
            class="px-4 py-2 bg-color-success hover:opacity-90 disabled:opacity-40 text-white text-sm font-bold rounded-lg transition-all"
          >
            {{ applying ? 'Применяю…' : 'Применить' }}
          </button>
          <span v-if="message" class="text-sm text-text-muted">{{ message }}</span>
        </div>

        <!-- Предложение: diff -->
        <div v-if="proposal" class="border-t border-text-muted pt-4">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-2 h-2 rounded-full" :class="proposal.valid ? 'bg-color-success' : 'bg-red-500'"></span>
            <span class="text-sm font-bold text-text-primary">
              {{ proposal.ops.length }} операций · {{ proposal.valid ? 'валидно' : 'есть ошибки' }}
            </span>
          </div>
          <ul class="space-y-1.5">
            <li
              v-for="(d, i) in proposal.diff"
              :key="i"
              class="text-xs font-mono text-text-secondary bg-bg-base rounded-lg px-3 py-2 border border-text-muted/40"
            >
              <span class="font-bold text-text-primary">{{ d.op }}</span>
              <span v-if="d.slide_id"> · {{ d.slide_id }}</span>
              <span v-if="d.component"> · {{ d.component }}</span>
              <span v-if="d.change"> · {{ d.change }}</span>
              <span v-if="d.title" class="text-text-muted"> — {{ String(d.title).replace(/<[^>]*>/g,'') }}</span>
            </li>
          </ul>
          <ul v-if="proposal.errors?.length" class="mt-3 space-y-1">
            <li v-for="(e, i) in proposal.errors" :key="'e'+i" class="text-xs text-red-400 font-mono">✕ {{ e.path }} — {{ e.message }}</li>
          </ul>
          <ul v-if="proposal.warnings?.length" class="mt-2 space-y-1">
            <li v-for="(w, i) in proposal.warnings" :key="'w'+i" class="text-xs text-amber-400 font-mono">! {{ w.path }} — {{ w.message }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
