import re

with open('core/src/composables/useVariant.js', 'r') as f:
    content = f.read()

# Replace the hardcoded background for type === 'svg'
old_svg_code = "return { background: `url(\\\"data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}\\\") center/cover no-repeat`, backdropFilter: 'none' }"
new_svg_code = """const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor ? (tok(bg.fallbackColor) || bg.fallbackColor) : 'transparent'
    return { background: `url("data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}") ${pos} / ${size} no-repeat, ${fallback}`, backdropFilter: 'none' }"""

content = content.replace(old_svg_code, new_svg_code)

with open('core/src/composables/useVariant.js', 'w') as f:
    f.write(content)

print("Updated useVariant.js")
