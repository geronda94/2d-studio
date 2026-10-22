<script setup lang="ts">
import { ref, inject, watch, nextTick, computed } from 'vue'
import type { Ref } from 'vue'
import { codeToHtml } from 'shiki'
import { useVariant } from '../../composables/useVariant'
import WindowHeader from './WindowHeader.vue'

const props = withDefaults(defineProps<{
 language?: string
 blocks?: Array<{ code: string, start_time: number }>
 mobile?: boolean
 variant?: string
}>(), {
 language: 'javascript',
 blocks: () => [],
 mobile: false
})

// Резолвим variant: payload → provide из презентации → дефолт 'tech'
const defaultVariant = inject<Ref<string | null>>('defaultVariant', ref(null))
const resolvedVariant = computed(() => {
 const v = (typeof props.variant === 'object' ? props.variant?.value : props.variant)
 return v || defaultVariant.value || 'tech'
})

const { itemVars } = useVariant(resolvedVariant, 'CodeExplain')

// Shiki theme — dark для тёмных вариантов, light для светлых
const shikiTheme = computed(() => {
 return ['derevnya', 'classic'].includes(resolvedVariant.value) ? 'github-light-high-contrast' : 'vitesse-dark'
})

const isLightTheme = computed(() => {
 return ['derevnya', 'classic'].includes(resolvedVariant.value)
})

const relativeTime = inject<Ref<number>>('relativeTime', ref(0))
const highlightedHtml = ref('')
const containerRef = ref<HTMLElement | null>(null)
// Сырой текст для фолбэка, пока Shiki грузится (иначе окно пустое)
const rawCode = computed(() => (props.blocks || []).map((b) => b.code).join(''))

const detectLanguage = (code: string) => {
 if (!code) return 'typescript'
 if (/^\s*[\{\[]\s*"/.test(code) || (/^\s*\{[\s\S]*\}\s*$/.test(code) && /"\w+"\s*:/.test(code))) return 'json'
 if (/<\/?\w+[^>]*>/.test(code)) return 'html'
 if (/\bdef \w+\s*\(/.test(code) || /\bimport \w+/.test(code) || /\bprint\s*\(/.test(code) || /:\n\s+/.test(code) || /\bclass \w+(:|\()/.test(code) || /^\s*#/m.test(code) || /\bfor\b.*\bin\b/.test(code)) return 'python'
 if (/[\w-]+\s*:\s*[^;]+;/.test(code) && /\{[\s\S]*\}/.test(code)) return 'css'
 return 'typescript'
}

const addTypingSpans = (html: string, blocks: Array<{ code: string, start_time: number }>) => {
 const div = document.createElement('div')
 div.innerHTML = html
 
 let globalCharIndex = 0
 
 const walk = (node: Node) => {
 if (node.nodeType === 3) {
 const text = node.textContent || ''
 const fragment = document.createDocumentFragment()
 
 for(let i = 0; i < text.length; i++) {
 let currentLen = 0
 let blockIdx = 0
 let charIndexInBlock = 0
 
 for (let b = 0; b < blocks.length; b++) {
 const bLen = blocks[b].code.length
 if (globalCharIndex >= currentLen && globalCharIndex < currentLen + bLen) {
 blockIdx = b
 charIndexInBlock = globalCharIndex - currentLen
 break
 }
 currentLen += bLen
 }
 
 const block = blocks[blockIdx] || blocks[blocks.length - 1]
 const startTime = block ? block.start_time : 0
  // Typing speed: 8ms per character (approx 125 chars/sec) — код успевает
  // пропечататься в пределах окна слайда (иначе хвост остаётся невидимым).
  const charTime = startTime + (charIndexInBlock * 8) 
 
 const span = document.createElement('span')
 span.className = 'code-char'
 span.style.opacity = '0'
 span.dataset.time = charTime.toString()
 span.textContent = text[i]
 
 fragment.appendChild(span)
 globalCharIndex++
 }
 if (node.parentNode) node.parentNode.replaceChild(fragment, node)
 } else if (node.nodeType === 1) {
 Array.from(node.childNodes).forEach(walk)
 }
 }
 
 Array.from(div.childNodes).forEach(walk)
 return div.innerHTML
}

 watch([() => props.blocks, () => props.language, shikiTheme], async ([newBlocks, newLang]) => {
 if (!newBlocks || newBlocks.length === 0) {
  highlightedHtml.value = ''
  return
 }
 
 const fullCode = newBlocks.map(b => b.code).join('')
 const activeLang = newLang || detectLanguage(fullCode)

 try {
 const rawHtml = await codeToHtml(fullCode, {
  lang: activeLang,
  theme: shikiTheme.value
 })
 // На светлых темах — без анимации печати, весь код сразу виден
 highlightedHtml.value = addTypingSpans(rawHtml, newBlocks)
 } catch (e) {
 console.error('Shiki highlight error:', e)
 highlightedHtml.value = addTypingSpans(`<pre><code>${fullCode}</code></pre>`, newBlocks)
 }
}, { immediate: true, deep: true })

let cachedChars: HTMLElement[] | null = null
let lastCodeBlocks = ''

watch([() => props.blocks, () => props.language], () => {
  cachedChars = null // reset cache when blocks change
  const currentCode = (props.blocks || []).map(b => b.code).join('')
  if (currentCode !== lastCodeBlocks) {
      lastCodeBlocks = currentCode
  }
})

const updateOpacity = () => {
 if (!containerRef.value) return
 
 if (!cachedChars) {
     cachedChars = Array.from(containerRef.value.querySelectorAll('.code-char'))
 }
 
 const currentRelTime = relativeTime.value
 let lastVisibleChar: HTMLElement | null = null
 
 for (let i = 0; i < cachedChars.length; i++) {
   const el = cachedChars[i]
   const time = parseFloat(el.dataset.time || '0')
   const shouldBeVisible = currentRelTime >= time
   const currentlyVisible = el.style.opacity === '1'
   
   if (shouldBeVisible && !currentlyVisible) {
     el.style.opacity = '1'
     lastVisibleChar = el
   } else if (!shouldBeVisible && currentlyVisible) {
     el.style.opacity = '0'
   } else if (shouldBeVisible) {
     lastVisibleChar = el
   }
 }
 
 if (lastVisibleChar && containerRef.value) {
   const container = containerRef.value
   const charTop = lastVisibleChar.offsetTop
   const charHeight = lastVisibleChar.offsetHeight
   
   if (charTop + charHeight > container.scrollTop + container.clientHeight) {
     container.scrollTop = charTop + charHeight - container.clientHeight + 40
   } else if (charTop < container.scrollTop) {
     container.scrollTop = charTop - 40
   }
 }
}

watch(relativeTime, updateOpacity)
watch(highlightedHtml, () => {
  cachedChars = null
  nextTick(updateOpacity)
})

</script>

<template>
   <div class="code-explain relative w-full text-left font-mono flex flex-col overflow-hidden"
   :style="{ ...itemVars }"
   :class="[ mobile ? 'h-full min-h-[500px] flex-1' : 'h-full min-h-0' ]">

  <WindowHeader title="code" :mobile="mobile" />

  <!-- Code Content Slot — тёмный хром внутри -->
  <div ref="containerRef" class="content relative w-full flex-1 min-h-0 overflow-auto custom-scrollbar"
  :data-theme="isLightTheme ? 'light' : 'dark'"
   :class="[
     mobile ? 'p-3 text-[11px] leading-[18px] wrap-code' : 'p-4 text-[12px] leading-[20px]',
     'bg-[var(--item-bg)] variant-item'
   ]"
  :style="{ backdropFilter: 'var(--item-backdrop)', WebkitBackdropFilter: 'var(--item-backdrop)', borderRadius: '0 0 calc(var(--item-radius) - 4px) calc(var(--item-radius) - 4px)' }">
  <div v-if="highlightedHtml" v-html="highlightedHtml"></div>
  </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
 height: 6px;
 width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
 background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
 background: rgb(var(--text-primary-rgb) / 0.1);
 border-radius: 10px;
}
.content :deep(pre) {
 margin: 0;
}
.wrap-code :deep(pre),
.wrap-code :deep(code) {
 white-space: pre-wrap;
 word-break: break-word;
 overflow-wrap: anywhere;
}
.content[data-theme="dark"] :deep(pre) {
 background: transparent !important;
}
</style>
