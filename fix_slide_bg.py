import re

with open('core/src/components/engine/Slide.vue', 'r') as f:
    content = f.read()

# Update script to extract surfaceVars
content = content.replace("const { slug: variantSlug } = useVariant()", "const { slug: variantSlug, surfaceVars } = useVariant()")

# Update template to inject style
old_template = """    <div v-show="isActive" class="slide absolute inset-0 w-full h-full flex"
         :class="[
           `variant-${variantSlug}`,
           effectiveLayout === 'row' ? 'flex-row items-center' : 'flex-col',
           isMobile ? 'pt-3 px-4 pb-4' : 'px-12 py-8'
         ]">"""

new_template = """    <div v-show="isActive" class="slide absolute inset-0 w-full h-full flex"
         :class="[
           `variant-${variantSlug}`,
           effectiveLayout === 'row' ? 'flex-row items-center' : 'flex-col',
           isMobile ? 'pt-3 px-4 pb-4' : 'px-12 py-8'
         ]"
         :style="[surfaceVars, surfaceVars['--surface-bg'] !== 'transparent' ? { background: 'var(--surface-bg)' } : {}]">"""

content = content.replace(old_template, new_template)

with open('core/src/components/engine/Slide.vue', 'w') as f:
    f.write(content)
print("Updated Slide.vue")
