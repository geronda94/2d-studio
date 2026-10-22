import os, glob, re

files = glob.glob("core/src/components/**/*.vue", recursive=True)
for filepath in files:
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    
    # Fix HTML attributes that got outer backticks: :style=`{...}` -> :style="{...}"
    def fix_html_attr(m):
        attr = m.group(1)
        inner = m.group(2)
        return f'{attr}="{inner}"'

    content = re.sub(r'([a-zA-Z0-9_-]+)=\`(.*?)\`', fix_html_attr, content)
    
    # Fix the inner string interpolation: '${getColorAlpha(...)}' -> getColorAlpha(...)
    content = re.sub(r'[\'"]\$\{getColorAlpha\((.*?)\)\}[\'"]', r'getColorAlpha(\1)', content)
    
    # Also fix backticks around it: `${getColorAlpha(...)}` -> getColorAlpha(...)
    content = re.sub(r'\`\$\{getColorAlpha\((.*?)\)\}\`', r'getColorAlpha(\1)', content)
    
    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Repaired {filepath}")
