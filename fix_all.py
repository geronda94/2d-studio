import re

with open('core/src/components/ui/InteractiveArchitecture.vue', 'r') as f:
    content = f.read()

# Fix InteractiveArchitecture
old_path_ia = """ :style="{ 
   strokeDasharray: line.animation === 'none' ? line.dash : '10 30',
   strokeDashoffset: line.animation === 'none' ? 0 : 40 - ((relativeTime % 2000) / 2000 * 40)
 }" />"""

new_path_ia = """ :style="{ 
   strokeDasharray: line.dash !== 'none' ? line.dash : '10 30',
   strokeDashoffset: 40 - ((relativeTime % 2000) / 2000 * 40)
 }" />"""

content = content.replace(old_path_ia, new_path_ia)
with open('core/src/components/ui/InteractiveArchitecture.vue', 'w') as f:
    f.write(content)
print("InteractiveArchitecture updated")

with open('core/src/components/ui/ArchitectureDiagram.vue', 'r') as f:
    content = f.read()

# Fix ArchitectureDiagram static path to animate if it has dashes
old_static = """              <path
                :id="'path-' + path.id"
                :d="path.d"
                fill="none"
                :stroke="line.color"
                :stroke-width="line.width"
                :stroke-dasharray="line.dash !== 'none' ? line.dash : undefined"
                :class="line.animation === 'none' ? 'opacity-100' : 'opacity-30'"
              />"""

new_static = """              <path
                :id="'path-' + path.id"
                :d="path.d"
                fill="none"
                :stroke="line.color"
                :stroke-width="line.width"
                :stroke-dasharray="line.dash !== 'none' ? line.dash : undefined"
                :class="line.animation === 'none' ? 'opacity-100' : 'opacity-30'"
                :style="{
                  strokeDashoffset: line.dash !== 'none' ? (40 - ((relativeTime % 2000) / 2000 * 40)) : undefined
                }"
              />"""

content = content.replace(old_static, new_static)

# Also fix the `dash` animation block which was missing strokeDashoffset entirely
old_dash = """                <path
                  v-else-if="line.animation === 'dash'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                  :stroke-dasharray="line.dash === 'none' ? '6 12' : line.dash"
                />"""

new_dash = """                <path
                  v-else-if="line.animation === 'dash'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                  :stroke-dasharray="line.dash === 'none' ? '6 12' : line.dash"
                  :style="{
                    strokeDashoffset: 40 - ((relativeTime % 2000) / 2000 * 40)
                  }"
                />"""

content = content.replace(old_dash, new_dash)

with open('core/src/components/ui/ArchitectureDiagram.vue', 'w') as f:
    f.write(content)
print("ArchitectureDiagram updated")

