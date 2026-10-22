import re
import os

files = [
    'core/src/components/ui/RenderManagerModal.vue',
    'core/src/views/MainPresentation.vue'
]

for file in files:
    if os.path.exists(file):
        with open(file, 'r') as f:
            content = f.read()
        
        # Remove alert(`Live capture запущен...`)
        content = re.sub(r'alert\(`Live capture запущен:.*?\);\n?', '', content)
        
        with open(file, 'w') as f:
            f.write(content)
        print(f"Fixed alerts in {file}")
