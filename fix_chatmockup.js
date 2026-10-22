const fs = require('fs')
let content = fs.readFileSync('core/src/components/ui/ChatMockup.vue', 'utf8')

// Fix borderColor
content = content.replace("borderColor: 'var(--text-muted)'", "borderColor: 'var(--item-border-color)'")

// Fix header background
content = content.replace("style=\"background-color: var(--bg-hover);\"", "style=\"background-color: var(--item-primary-bg);\"")

// Fix avatar color (use color-primary instead of brand-blue)
content = content.replace("background: getColorAlpha(getHexColor('brand-blue'), 0.1), color: getHexColor('brand-blue')", "background: getColorAlpha(getHexColor('color-primary') || getHexColor('brand-blue'), 0.1), color: getHexColor('color-primary') || getHexColor('brand-blue')")

// Also fix message bubbles which might be hardcoded! Let's check them first!
fs.writeFileSync('core/src/components/ui/ChatMockup.vue', content)
console.log("ChatMockup fixed!")
