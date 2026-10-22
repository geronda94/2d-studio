const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

const correctBlock = `    return { 
      background: \`\${fallback} url("data:image/svg+xml;utf8,\${encodeURIComponent(bg.value)}") \${pos} / \${size} no-repeat\`,
      backdropFilter: 'none' 
    }
  }

  // solid`

content = content.replace(/return \{\s*background: `\$\{fallback\}.*?\s*backdropFilter: 'none'\s*[\s\}]*\/\/ solid/ms, correctBlock)
fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Fixed!")
