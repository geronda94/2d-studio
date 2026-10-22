import os

# 1. ProductCard.vue
f1 = 'core/src/components/ui/ProductCard.vue'
lines = open(f1).readlines()
for i, line in enumerate(lines):
    if ':style="{ backgroundColor: item.highlight ? getColorAlpha(resolveColor(item.accent_color)' in line:
        lines[i] = "  :style=\"{ backgroundColor: item.highlight ? getColorAlpha(resolveColor(item.accent_color), 0.2) : getColorAlpha('var(--text-primary)', 0.05) }\">\n"
open(f1, 'w').writelines(lines)

# 2. Ecosystem.vue
f2 = 'core/src/components/ui/Ecosystem.vue'
lines = open(f2).readlines()
for i, line in enumerate(lines):
    if ':style="{ transform: "scale(${scaleFactor})`' in line:
        lines[i] = "  :style=\"{ transform: `scale(${scaleFactor})`, width: 0, height: 0 }\">\n"
    if ':style="node.color ? { borderColor: "${getColorAlpha' in line:
        lines[i] = "  :style=\"node.color ? { borderColor: getColorAlpha(`var(--${node.color}, ${node.color})`, 0.5), boxShadow: `0 8px 30px -5px ${getColorAlpha(`var(--${node.color}, ${node.color})`, 0.3)}` } : { borderColor: 'rgb(var(--text-primary-rgb) / 0.15)' }\">\n"
    if ':style="node.color ? { color: "var(--${node.color}' in line:
        lines[i] = "  :style=\"node.color ? { color: `var(--${node.color}, ${node.color})`, backgroundColor: getColorAlpha(`var(--${node.color}, ${node.color})`, 0.2) } : {}\">\n"
open(f2, 'w').writelines(lines)

# 3. Roadmap.vue
f3 = 'core/src/components/ui/Roadmap.vue'
lines = open(f3).readlines()
for i, line in enumerate(lines):
    if ':style="{ transform: "scale(${getScale(idx)})' in line:
        lines[i] = "  :style=\"{ transform: `scale(${getScale(idx)}) translateY(${getScale(idx) > 1 ? '-8px' : '0px'})` }\">\n"
open(f3, 'w').writelines(lines)

# 4. InteractiveArchitecture.vue
f4 = 'core/src/components/ui/InteractiveArchitecture.vue'
lines = open(f4).readlines()
for i, line in enumerate(lines):
    if ':style="{ transform: "translate(${translateX}px' in line:
        lines[i] = "  :style=\"{ transform: `translate(${translateX}px, ${translateY}px) scale(${scale})` }\">\n"
open(f4, 'w').writelines(lines)

# 5. InfographicCards.vue
f5 = 'core/src/components/ui/InfographicCards.vue'
lines = open(f5).readlines()
for i, line in enumerate(lines):
    if 'background: String(stat.trend).startsWith' in line:
        lines[i] = "  background: String(stat.trend).startsWith('+') ? getColorAlpha('var(--color-success)', 0.15) : getColorAlpha('var(--color-warning)', 0.15),\n"
    elif 'borderColor: String(stat.trend).startsWith' in line:
        lines[i] = "  borderColor: String(stat.trend).startsWith('+') ? getColorAlpha('var(--color-success)', 0.3) : getColorAlpha('var(--color-warning)', 0.3),\n"
open(f5, 'w').writelines(lines)

print('All 5 files manually fixed.')
