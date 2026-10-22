const fs = require('fs');
const path = require('path');
const { parse } = require('@vue/compiler-sfc');

const componentsDir = path.join(__dirname, 'core/src/components');

function walkDir(dir) {
    let files = [];
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        file = path.join(dir, file);
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) {
            files = files.concat(walkDir(file));
        } else if (file.endsWith('.vue')) {
            files.push(file);
        }
    });
    return files;
}

const vueFiles = walkDir(componentsDir);
let errors = 0;

for (const file of vueFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const { errors: parseErrors } = parse(content, { filename: file });
    if (parseErrors && parseErrors.length > 0) {
        console.error(`Syntax Error in ${file}:`);
        parseErrors.forEach(err => console.error('  ', err.message, `(Line: ${err.loc?.start?.line})`));
        errors++;
    }
}

if (errors === 0) {
    console.log('All .vue files passed syntax check!');
} else {
    console.error(`Found ${errors} files with syntax errors.`);
}
