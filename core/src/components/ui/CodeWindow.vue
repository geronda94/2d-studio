<script setup lang="ts">
import { ref, watch, nextTick, computed, inject } from 'vue'
import type { Ref } from 'vue'
import { codeToHtml } from 'shiki'
import { useVariant } from '../../composables/useVariant'
import WindowHeader from './WindowHeader.vue'

const props = defineProps<{
 title?: string
 code?: string
 lang?: string
 mobile?: boolean
 typing?: boolean
 startTyping?: boolean
 typingStart?: number
 variant?: string
}>()

const defaultVariant = inject<Ref<string | null>>('defaultVariant', ref(null))
const resolvedVariant = computed(() => {
 const v = (typeof props.variant === 'object' ? props.variant?.value : props.variant)
 return v || defaultVariant.value || 'tech'
})

const { itemVars } = useVariant(resolvedVariant, 'CodeWindow')

const shikiTheme = computed(() => {
 return ['derevnya', 'classic'].includes(resolvedVariant.value) ? 'github-light-high-contrast' : 'vitesse-dark'
})

const isLightTheme = computed(() => {
 return ['derevnya', 'classic'].includes(resolvedVariant.value)
})

const highlightedHtml = ref('')
const containerRef = ref<HTMLElement | null>(null)
const relativeTime = inject<Ref<number>>('relativeTime', ref(0))

// Детерминированная «печать»: символы проявляются по relativeTime (§11), без setInterval.
const charDelay = computed(() => {
 const len = (props.code || '').length || 1
 return Math.max(4, Math.min(15, 3000 / len))
})

const addTypingSpans = (html: string) => {
 const div = document.createElement('div')
 div.innerHTML = html
 let idx = 0
 const start = Number(props.typingStart || 0)
 const delay = charDelay.value
 
 const walk = (node: Node) => {
 if (node.nodeType === 3) {
 const text = node.textContent || ''
 const fragment = document.createDocumentFragment()
 for(let i=0; i<text.length; i++) {
 if (text[i].trim() === '') {
 fragment.appendChild(document.createTextNode(text[i]))
 } else {
 const span = document.createElement('span')
 span.className = 'code-char'
 span.style.opacity = '0'
 span.dataset.time = String(start + idx * delay)
 span.textContent = text[i]
 fragment.appendChild(span)
 idx++
 }
 }
 if (node.parentNode) node.parentNode.replaceChild(fragment, node)
 } else if (node.nodeType === 1) {
 Array.from(node.childNodes).forEach(walk)
 }
 }
 
 Array.from(div.childNodes).forEach(walk)
 return div.innerHTML
}

const detectLanguage = (code: string) => {
 if (!code) return 'typescript'
 
 // JSON
 if (/^\s*[\{\[]\s*"/.test(code) || (/^\s*\{[\s\S]*\}\s*$/.test(code) && /"\w+"\s*:/.test(code))) return 'json'
 
 // HTML / Vue / XML
 if (/<\/?\w+[^>]*>/.test(code)) return 'html'
 
 // Python
 if (/\bdef \w+\s*\(/.test(code) || /\bimport \w+/.test(code) || /\bprint\s*\(/.test(code) || /:\n\s+/.test(code) || /\bclass \w+(:|\()/.test(code) || /^\s*#/m.test(code) || /\bfor\b.*\bin\b/.test(code)) return 'python'
 
 // CSS
 if (/[\w-]+\s*:\s*[^;]+;/.test(code) && /\{[\s\S]*\}/.test(code)) return 'css'
 
 // Default to typescript (perfect for JS/TS)
 return 'typescript'
}

watch([() => props.code, () => props.lang, () => props.typing, shikiTheme], async ([newCode, newLang, isTyping]) => {
 if (newCode) {
 const activeLang = newLang || detectLanguage(newCode)

 try {
 const rawHtml = await codeToHtml(newCode, {
 lang: activeLang,
 theme: shikiTheme.value
 })
 highlightedHtml.value = isTyping ? addTypingSpans(rawHtml) : rawHtml
 } catch (e) {
 console.error('Shiki highlight error:', e)
 highlightedHtml.value = isTyping ? addTypingSpans(newCode) : newCode
 }
 }
}, { immediate: true })

const updateChars = () => {
 if (!props.typing || !containerRef.value) return
 const chars = containerRef.value.querySelectorAll('.code-char')
 const t = relativeTime.value
 chars.forEach((c) => {
 const el = c as HTMLElement
 const ct = parseFloat(el.dataset.time || '0')
 el.style.opacity = t >= ct ? '1' : '0'
 })
}

watch(relativeTime, updateChars)
watch([() => props.startTyping, highlightedHtml], () => nextTick(updateChars), { flush: 'post', immediate: true })
</script>

<template>
   <div class="code-window overflow-hidden w-full max-w-full text-left my-2"
   :style="{ ...itemVars }">
   <div class="overflow-hidden" :class="isLightTheme ? 'bg-[#FEFEFE]' : ''" :style="{ borderRadius: 'calc(var(--item-radius) - 4px)', background: isLightTheme ? '#FEFEFE' : 'var(--item-bg)' }">
   <WindowHeader :title="title" :mobile="mobile" />

  <!-- Code Content Slot -->
  <div ref="containerRef" class="content font-mono overflow-auto max-h-[300px] scrollbar-thin scrollbar-thumb-white/10"
  :data-theme="isLightTheme ? 'light' : 'dark'"
  :class="mobile ? 'p-4 text-[10px] leading-relaxed' : 'p-4 text-xs leading-relaxed'"
  :data-code-pending="code && !highlightedHtml ? '1' : null">
  <div v-if="code && highlightedHtml" v-html="highlightedHtml"></div>
  <pre v-else-if="code" class="whitespace-pre-wrap text-text-primary">{{ code }}</pre>
  <slot v-else />
  </div>
  </div>
  </div>
</template>

<style scoped>
.content :deep(pre) {
 margin: 0;
}
.content[data-theme="dark"] :deep(pre) {
 background: transparent !important;
}
</style>
