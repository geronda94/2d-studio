<script setup lang="ts">
import { ref, inject, computed, nextTick, watch } from 'vue'
import type { Ref } from 'vue'
import { useVariant } from '../../composables/useVariant'
import WindowHeader from './WindowHeader.vue'

const props = withDefaults(defineProps<{
 mobile?: boolean
 variant?: string
 commands?: Array<{
 cmd: string
 output?: string
 start_time?: number
 }>
}>(), {
 mobile: false,
 commands: () => []
})

const { itemVars } = useVariant(computed(() => props.variant), 'TerminalMockup')

const relativeTime = inject<Ref<number>>('relativeTime', ref(0))

const el = ref<HTMLElement | null>(null)

// Character delay for typewriter (ms per char)
const CHAR_DELAY = 40

const escapeHtml = (str: string) => (str || '').replace(/</g, "&lt;").replace(/>/g, "&gt;")

const highlightCommand = (cmdStr: string) => {
 if (!cmdStr) return ''
 let html = escapeHtml(cmdStr)
 
 // 1. Strings (yellow)
 html = html.replace(/('.*?'|".*?")/g, '<span class="text-[#EAB308]">$1</span>')
 // 2. Flags (slate/gray)
 html = html.replace(/(\s--?[a-zA-Z0-9-]+)/g, '<span class="text-[#94A3B8]">$1</span>')
 // 3. Known Commands (green)
 const commands = ['npm', 'yarn', 'node', 'python', 'python3', 'git', 'docker', 'docker-compose', 'sudo', 'apt', 'apt-get', 'brew', 'pip', 'pip3', 'ls', 'cd', 'rm', 'mkdir', 'touch', 'cat', 'echo', 'curl', 'wget', 'npx', 'pnpm', 'bun', 'sh', 'bash', 'make']
 const cmdRegex = new RegExp(`(^|&&\\s*|\\|\\|\\s*|;\\s*)(${commands.join('|')})\\b`, 'g')
 html = html.replace(cmdRegex, '$1<span class="text-[#27C93F]">$2</span>')
 
 return html
}

const highlightOutput = (outputStr: string) => {
 if (!outputStr) return ''
 const lines = outputStr.split('\n')
 const highlightedLines = lines.map(line => {
 let escapedLine = escapeHtml(line)
 const lowerLine = escapedLine.toLowerCase()
 
 // Status-based coloring for the whole line
 if (lowerLine.includes('error:') || lowerLine.includes('error ') || lowerLine.includes('failed ') || lowerLine.includes('exception:')) {
 return `<span class="text-[#EF4444]">${escapedLine}</span>`
 }
 if (lowerLine.includes('warn:') || lowerLine.includes('warning:')) {
 return `<span class="text-[#FBBF24]">${escapedLine}</span>`
 }
 if (lowerLine.includes('success') || lowerLine.includes('done') || lowerLine.includes('ready in') || lowerLine.includes('built in') || lowerLine.includes('ok') || lowerLine.includes('finished')) {
 return `<span class="text-[#27C93F]">${escapedLine}</span>`
 }
 
 // URLs
 escapedLine = escapedLine.replace(/(https?:\/\/[^\s]+|localhost:\d+)/g, '<span class="text-color-secondary underline cursor-pointer hover:text-white ">$1</span>')
 
 return escapedLine
 })
 
 return highlightedLines.join('\n')
}

const processedSteps = computed(() => {
 if (!props.commands) return []
 return props.commands.map((step, index) => {
 const startTime = step.start_time || 0
 const nextStep = props.commands![index + 1]
 const nextStartTime = nextStep ? (nextStep.start_time || 0) : Infinity
 
 const cmd = step.cmd || ''
 const lines = (step.output || '').split('\n')
 
 // Mandatory pause before the next command starts
 const PAUSE_BEFORE_NEXT = 300
 // Maximum time allowed for typing a command
 const MAX_TYPING_DURATION = 1000
 
 const NORMAL_CHAR_DELAY = 40
 const NORMAL_OUTPUT_START = 100
 const NORMAL_LINE_DELAY = 30
 
 const normalTypingDuration = cmd.length * NORMAL_CHAR_DELAY
 const normalOutputDuration = NORMAL_OUTPUT_START + Math.max(0, lines.length - 1) * NORMAL_LINE_DELAY
 
 const availableTime = nextStartTime - startTime - PAUSE_BEFORE_NEXT
 
 let typingDuration = 0
 let outputStartDelay = NORMAL_OUTPUT_START
 let lineDelay = NORMAL_LINE_DELAY
 
 if (availableTime <= 0) {
 typingDuration = 0
 outputStartDelay = 0
 lineDelay = 0
 } else if (availableTime < normalOutputDuration) {
 typingDuration = 0
 outputStartDelay = availableTime * 0.3 // 30% of available time for the initial pause
 const remainingForLines = availableTime - outputStartDelay
 lineDelay = lines.length > 1 ? remainingForLines / (lines.length - 1) : 0
 } else {
 const allowedTyping = availableTime - normalOutputDuration
 typingDuration = Math.min(normalTypingDuration, allowedTyping, MAX_TYPING_DURATION)
 }
 
 const charDelay = typingDuration > 0 ? typingDuration / (cmd.length || 1) : 0
 
 const elapsed = relativeTime.value - startTime
 
 let cmdChars = cmd.length
 if (charDelay > 0) {
 cmdChars = Math.max(0, Math.floor(elapsed / charDelay))
 }
 const displayedCmd = cmd.substring(0, cmdChars)
 const highlightedCmd = highlightCommand(displayedCmd)
 
 const isTyping = elapsed >= 0 && displayedCmd.length < cmd.length
 
 const timeSinceOutputStarted = elapsed - typingDuration - outputStartDelay
 let visibleLinesCount = 0
 
 if (timeSinceOutputStarted >= 0) {
 if (lineDelay > 0) {
 visibleLinesCount = 1 + Math.floor(timeSinceOutputStarted / lineDelay)
 } else {
 visibleLinesCount = lines.length
 }
 }
 visibleLinesCount = Math.min(visibleLinesCount, lines.length)
 
 const visibleLines = lines.slice(0, visibleLinesCount).join('\n')
 const highlightedOut = visibleLinesCount > 0 ? highlightOutput(visibleLines) : ''
 const outputVisible = visibleLinesCount > 0
 
 return {
 ...step,
 highlightedCmd,
 highlightedOut,
 isTyping,
 outputVisible,
 started: elapsed >= 0
 }
 })
})

// Auto-scroll when new steps or output appear
watch(processedSteps, () => {
 nextTick(() => {
 const container = el.value?.querySelector('.custom-scrollbar')
 if (container) {
 container.scrollTop = container.scrollHeight
 }
 })
}, { deep: true })

</script>

<template>
   <div ref="el"
   class="mx-auto overflow-hidden flex flex-col flex-1 min-h-0 w-full"
   :style="[{ ...itemVars }, mobile ? 'height: 100%; min-height: 0;' : 'max-width: 850px; height: 100%; min-height: 0;', 'font-family: \'JetBrains Mono\', Menlo, Consolas, monospace;', mobile ? 'line-height: 1.3;' : 'line-height: 1.5;']"
   :class="mobile ? 'text-[11px]' : 'text-[13px]'"
   >
   <div class="flex-1 min-h-0 flex flex-col overflow-hidden bg-[var(--item-bg)] variant-item" style="border-radius: calc(var(--item-radius) - 4px)">
   <WindowHeader centered title="root@server — bash — 80x24" :mobile="mobile" />

  <!-- Terminal Body -->
  <div class="flex-1 bg-[var(--item-bg)] overflow-hidden flex flex-col text-left min-h-0"
  :class="mobile ? 'p-2 pt-2' : 'p-4 pt-5'">

  <!-- Steps -->
  <template v-for="(step, idx) in processedSteps" :key="idx">
  <div v-if="step.started" class="whitespace-pre-wrap break-all text-left" :class="mobile ? 'mb-1' : 'mb-2'">
   <span class="text-[#27C93F] font-bold mr-2">root@server<span class="text-text-primary">:</span><span class="text-[#3A96DD]">~/app</span><span class="text-text-primary">#</span></span><span class="text-text-primary" v-html="step.highlightedCmd"></span><span v-if="step.isTyping" :style="{ opacity: (relativeTime % 1000) < 500 ? 1 : 0 }" class="bg-text-muted inline-block align-middle ml-1" :class="mobile ? 'w-[6px] h-[12px]' : 'w-[8px] h-[15px]'"></span>
  </div>
  <div v-if="step.outputVisible && step.output" class="break-words text-text-secondary whitespace-pre-wrap" :class="mobile ? 'mb-2' : 'mb-4'" v-html="step.highlightedOut"></div>
  </template>

  <!-- Prompt after execution -->
  <div v-if="processedSteps.length === 0 || (!processedSteps[processedSteps.length - 1].isTyping && processedSteps[processedSteps.length - 1].outputVisible)" class="mt-4 text-left">
   <span class="text-[#27C93F] font-bold mr-2">root@server<span class="text-text-primary">:</span><span class="text-[#3A96DD]">~/app</span><span class="text-text-primary">#</span></span><span :style="{ opacity: (relativeTime % 1000) < 500 ? 1 : 0 }" class="bg-text-muted inline-block align-middle" :class="mobile ? 'w-[6px] h-[12px]' : 'w-[8px] h-[15px]'"></span>
  </div>

  <!-- Safe bottom padding to prevent sticking -->
  <div class="shrink-0 w-full" :class="mobile ? 'h-3' : 'h-8'"></div>
  </div>
  </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
 width: 10px;
}
.custom-scrollbar::-webkit-scrollbar-track {
 background: var(--item-bg, var(--bg-base, #1C1C1E));
}
.custom-scrollbar::-webkit-scrollbar-thumb {
 background: var(--text-muted, #4B4B4D);
 border: 2px solid var(--item-bg, var(--bg-base, #1C1C1E));
 border-radius: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
 background: var(--text-secondary, #636366);
}
</style>
