const fs = require('fs')
let content = fs.readFileSync('backend/validation.py', 'utf8')

// We need to remove the start_time checking logic for arrays.
const lines = content.split('\n')
const newLines = []
let skip = false
for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('prev = None')) {
        skip = true
        continue
    }
    if (skip && lines[i].includes('return errors')) {
        skip = false
        newLines.push(lines[i])
        continue
    }
    if (!skip) {
        newLines.push(lines[i])
    }
}
fs.writeFileSync('backend/validation.py', newLines.join('\n'))
