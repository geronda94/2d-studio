const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

const target = "if (type === 'svg') {\n    return { background: `url(\"data:image/svg+xml;utf8,${encodeURIComponent(bg.value)}\") center/cover no-repeat`, backdropFilter: 'none' }\n  }"
const newCode = `if (type === 'svg') {
    const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor || 'transparent'
    return { background: \`url("data:image/svg+xml;utf8,\${encodeURIComponent(bg.value)}") \${pos} / \${size} no-repeat, \${fallback}\`, backdropFilter: 'none' }
  }`

content = content.replace(target, newCode)
fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Replaced!")
