const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

const target = /if \(type === 'svg'\) \{[\s\S]*?backdropFilter: 'none' \}\n  \}/;

const newCode = `if (type === 'svg') {
    const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor || 'transparent'
    return { 
      backgroundImage: \`url("data:image/svg+xml;utf8,\${encodeURIComponent(bg.value)}")\`,
      backgroundPosition: pos,
      backgroundSize: size,
      backgroundRepeat: 'no-repeat',
      backgroundColor: fallback,
      backdropFilter: 'none' 
    }
  }`

content = content.replace(target, newCode)
fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Fixed CSS properties!")
