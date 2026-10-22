import re

with open('core/src/components/ui/ArchitectureDiagram.vue', 'r') as f:
    content = f.read()

old_code = """                :style="{
                  strokeDashoffset:
                    line.dash === 'none' ? getDrawOffset(path) : undefined,
                }\""""

new_code = """                :style="{
                  strokeDashoffset:
                    line.dash === 'none' ? getDrawOffset(path) : (40 - ((relativeTime % 2000) / 2000 * 40)),
                }\""""

content = content.replace(old_code, new_code)

with open('core/src/components/ui/ArchitectureDiagram.vue', 'w') as f:
    f.write(content)
print("Updated static path dash offset!")
