import os

files = [
    'core/src/components/ui/InteractiveArchitecture.vue',
    'core/src/components/ui/ArchitectureDiagram.vue',
    'core/src/components/ui/ProcessFunnel.vue'
]

for f in files:
    content = open(f).read()
    
    # We will just remove the `animation: ... infinite;` lines.
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'animation:' in line and 'infinite' in line:
            # Skip this line
            continue
        new_lines.append(line)
        
    open(f, 'w').write('\n'.join(new_lines))

print("Removed all infinite CSS animations from components.")
