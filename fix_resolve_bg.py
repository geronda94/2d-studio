import re

with open('core/src/composables/useVariant.js', 'r') as f:
    content = f.read()

old_bg = """  if (type === 'transparent') {
    return { background: 'transparent', backdropFilter: 'none' }
  }"""

new_bg = """  if (type === 'transparent') {
    return { background: 'transparent', backdropFilter: 'none' }
  }
  if (type === 'svg') {
    return { background: `url("data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}") center/cover no-repeat`, backdropFilter: 'none' }
  }"""

content = content.replace(old_bg, new_bg)

with open('core/src/composables/useVariant.js', 'w') as f:
    f.write(content)
print("Updated resolveBg in useVariant.js")
