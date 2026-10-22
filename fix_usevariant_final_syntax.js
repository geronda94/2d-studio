const fs = require('fs')
let content = fs.readFileSync('core/src/composables/useVariant.js', 'utf8')

content = content.replace(
  "return { background: `linear-gradient(${angle}deg, ${from}, ${to})`, backdropFilter: 'none' }\n\n  if (type === 'blur')",
  "return { background: `linear-gradient(${angle}deg, ${from}, ${to})`, backdropFilter: 'none' }\n  }\n\n  if (type === 'blur')"
)

content = content.replace(
  "return { background: 'transparent', backdropFilter: 'none' }\n\n  if (type === 'svg')",
  "return { background: 'transparent', backdropFilter: 'none' }\n  }\n\n  if (type === 'svg')"
)

fs.writeFileSync('core/src/composables/useVariant.js', content)
console.log("Syntax fixed completely!")
