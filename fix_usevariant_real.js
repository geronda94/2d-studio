const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

const target = /if \(type === 'svg'\) \{[\s\S]*?backdropFilter: 'none' \n    \}/;

const newCode = `if (type === 'svg') {
    const pos = bg.position || 'center'
    const size = bg.size || 'cover'
    const fallback = bg.fallbackColor || 'transparent'
    // Ensure we use the proper CSS background shorthand syntax. 
    // We can't easily put color on a separate layer if it's the only layer, so we just append it.
    return { 
      background: \`\${fallback} url("data:image/svg+xml;utf8,\${encodeURIComponent(bg.value)}") \${pos} / \${size} no-repeat\`,
      backdropFilter: 'none' 
    }
  }`

content = content.replace(target, newCode)
fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Fixed CSS shorthand!")
