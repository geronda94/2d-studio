import os

f = 'core/src/components/ui/ChatMockup.vue'
content = open(f).read()

# Replace var(--color-primary) and var(--text-on-primary) with concrete values
content = content.replace("'var(--color-primary)'", "getHexColor('brand-blue')")
content = content.replace("'var(--text-on-primary)'", "'#ffffff'")
# Ensure getHexColor is imported if not
if 'getHexColor' not in content[:content.find('</script>')]:
    content = content.replace("import { getColorAlpha } from '../../utils/colors'", "import { getColorAlpha, getHexColor } from '../../utils/colors'")

open(f, 'w').write(content)
print("ChatMockup styles adjusted")
