import re

with open('core/src/components/engine/Slide.vue', 'r') as f:
    content = f.read()

old_style = """         ]"
         :style="[surfaceVars, surfaceVars['--surface-bg'] !== 'transparent' ? { background: 'var(--surface-bg)' } : {}]">"""

new_style = """         ]"
         :style="[surfaceVars, { background: 'var(--surface-bg)' }]">"""

content = content.replace(old_style, new_style)

with open('core/src/components/engine/Slide.vue', 'w') as f:
    f.write(content)
print("Simplified Slide.vue")
