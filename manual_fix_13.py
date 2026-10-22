import os

f = 'core/src/components/ui/HorizontalDivider.vue'
content = open(f).read()

# Replace the template to include BOTH the static track and the spark
old_template = """<template>
 <div 
 :class="[
 props.mode === 'relative' ? 'relative w-full' : (props.mode === 'absolute' ? 'absolute left-0 right-0' : ''),
 'h-[2px] pointer-events-none z-0'
 ]"
 >
 <div v-if="line.animation !== 'none'" class="w-full h-full animated-bg-gradient horizontal-mask" :style="{ 'background-position': bgPositionX, '--line-color': line.color }"></div>
 <div v-else class="w-full h-full horizontal-mask" :style="{ background: line.color, opacity: 0.3 }"></div>
 </div>
</template>"""

new_template = """<template>
 <div 
 :class="[
 props.mode === 'relative' ? 'relative w-full' : (props.mode === 'absolute' ? 'absolute left-0 right-0' : ''),
 'h-[2px] pointer-events-none z-0 overflow-hidden horizontal-mask'
 ]"
 >
 <!-- Static background track (always visible) -->
 <div class="absolute inset-0 w-full h-full" :style="{ background: line.color, opacity: 0.2 }"></div>
 <!-- Animated spark -->
 <div v-if="line.animation !== 'none'" class="absolute inset-0 w-full h-full animated-bg-gradient" :style="{ 'background-position': bgPositionX, '--line-color': line.color }"></div>
 </div>
</template>"""

content = content.replace(old_template, new_template)

# Fix the percent logic so it slides smoothly from -100% to 200%
# Actually, background-position with % is tricky. Let's use pixels or just rely on a simple % sweep.
# With background-size 200%, position 0% = left aligned, 100% = right aligned.
# To sweep across entirely, position should go from -50% to 150% or something.
# Let's fix the computed property.
old_script = """const bgPositionX = computed(() => {
 const t = relativeTime.value % props.duration
 const percent = -(t / props.duration) * 200
 return `${percent}% 0%`
})"""

new_script = """const bgPositionX = computed(() => {
 const t = relativeTime.value % props.duration
 // Sweep from left to right. 
 // With size 200%, 0% means image's left edge touches container's left edge.
 // 100% means image's right edge touches container's right edge.
 // We want the spark (in the middle) to move from 0 to width.
 const percent = 100 - (t / props.duration) * 100
 return `${percent}% 0%`
})"""

content = content.replace(old_script, new_script)

open(f, 'w').write(content)
print("HorizontalDivider fixed")
