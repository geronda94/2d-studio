import os

f = 'core/src/components/ui/ComparisonTable.vue'
content = open(f).read()
if 'getColorAlpha' not in content[:content.find('export interface')]:
    content = content.replace("import { useVariant } from '../../composables/useVariant'", "import { useVariant } from '../../composables/useVariant'\nimport { getColorAlpha } from '../../utils/colors'")
    open(f, 'w').write(content)
    print("Fixed ComparisonTable.vue import")
