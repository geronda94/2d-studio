<template>
  <div ref="host" class="h-full w-full overflow-hidden rounded-lg border border-text-muted/30"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { basicSetup, EditorView } from 'codemirror'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'html' },
})
const emit = defineEmits(['update:modelValue'])

const host = ref(null)
let view = null

function languageExt() {
  if (props.language === 'css') return css()
  if (props.language === 'js') return javascript()
  return html()
}

function build() {
  if (!host.value) return
  view = new EditorView({
    doc: props.modelValue || '',
    extensions: [
      basicSetup,
      languageExt(),
      oneDark,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
      }),
    ],
    parent: host.value,
  })
}

onMounted(build)

watch(
  () => props.modelValue,
  (value) => {
    if (!view) return
    const current = view.state.doc.toString()
    if ((value || '') !== current) {
      view.dispatch({ changes: { from: 0, to: current.length, insert: value || '' } })
    }
  },
)

watch(
  () => props.language,
  () => {
    if (view) {
      view.destroy()
      view = null
      build()
    }
  },
)

onUnmounted(() => {
  if (view) view.destroy()
  view = null
})
</script>

<style scoped>
:deep(.cm-editor) {
  height: 100%;
  font-size: 12px;
}
:deep(.cm-scroller) {
  font-family: var(--font-mono), monospace;
  line-height: 1.6;
}
:deep(.cm-editor.cm-focused) {
  outline: none;
}
</style>
