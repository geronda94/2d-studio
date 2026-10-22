import re

with open('core/src/composables/useVariant.js', 'r') as f:
    content = f.read()

# Use regex to replace
pattern = r"if \(type === 'svg'\) \{\s*return \{ background: [^}]+ backdropFilter: 'none' \}\s*\}"
replacement = """if (type === 'svg') {
    const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor ? (tok(bg.fallbackColor) || bg.fallbackColor) : 'transparent'
    return { background: `url("data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}") ${pos} / ${size} no-repeat, ${fallback}`, backdropFilter: 'none' }
  }"""

content = re.sub(pattern, replacement, content)

with open('core/src/composables/useVariant.js', 'w') as f:
    f.write(content)

print("Updated useVariant.js again")
