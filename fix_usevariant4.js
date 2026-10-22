const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

// We had: url(...) ${pos} / ${size} no-repeat, ${fallback}
// Let's change it to: url(...) ${pos} / ${size} no-repeat ${fallback}  <-- NO COMMA!
content = content.replace(/no-repeat, \$\{fallback\}/g, 'no-repeat ${fallback}')
fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Removed comma!")
