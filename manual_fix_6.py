import os

f = 'core/src/components/ui/ArchitectureDiagram.vue'
content = open(f).read()
new_content = content.replace('getNodeColorAlpha', 'getColorAlpha')
open(f, 'w').write(new_content)
print('Fixed ArchitectureDiagram.vue imports')
