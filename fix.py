import os, glob, re

def replace_in_js(match):
    color = match.group(1).strip()
    pct = match.group(2).strip()
    alpha = float(pct) / 100.0
    if color.startswith("${") and color.endswith("}"):
        expr = color[2:-1]
        return f"${{getColorAlpha({expr}, {alpha})}}"
    elif color.startswith("var("):
        return f"${{getColorAlpha('{color}', {alpha})}}"
    elif color.startswith("#"):
        return f"${{getColorAlpha('{color}', {alpha})}}"
    else:
        return f"${{getColorAlpha('{color}', {alpha})}}"

files = glob.glob("core/src/components/**/*.vue", recursive=True)
for filepath in files:
    with open(filepath, "r") as f:
        content = f.read()
        
    if "color-mix" not in content:
        continue
        
    if "HorizontalDivider.vue" in filepath or "VerticalDivider.vue" in filepath:
        continue

    new_content = re.sub(
        r"color-mix\(\s*in srgb,\s*(.+?)\s+(\d+(?:\.\d+)?)%\s*,\s*transparent\s*\)",
        replace_in_js,
        content
    )
    
    def fix_quotes(m):
        quote = m.group(1)
        inner = m.group(2)
        if "${" in inner:
            return f"`{inner}`"
        return m.group(0)
    
    new_content = re.sub(r"(['\"])(.*?\$\{.*?\}.*?)\1", fix_quotes, new_content)
    
    if "getColorAlpha" in new_content and "getColorAlpha" not in content and "import" in new_content:
        if "utils/colors" in new_content:
            new_content = re.sub(r"import\s+\{(.*?)\}\s+from\s+['\"](?:.*?)utils/colors['\"]", lambda m: f"import {{{m.group(1)}, getColorAlpha}} from '../../utils/colors'", new_content)
        else:
            new_content = new_content.replace("<script setup lang=\"ts\">\n", "<script setup lang=\"ts\">\nimport { getColorAlpha } from '../../utils/colors'\n")
            new_content = new_content.replace("<script setup>\n", "<script setup>\nimport { getColorAlpha } from '../../utils/colors'\n")

    new_content = new_content.replace("getNodeColorAlpha", "getColorAlpha")
    
    with open(filepath, "w") as f:
        f.write(new_content)
    print(f"Fixed {filepath}")
