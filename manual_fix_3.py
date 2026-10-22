import os

# 1. InteractiveArchitecture.vue
f1 = 'core/src/components/ui/InteractiveArchitecture.vue'
lines = open(f1).readlines()
for i, line in enumerate(lines):
    if ':style="{ left: "${node.x}px`, top: `${node.y}px` }`' in line:
        lines[i] = "  :style=\"{ left: `${node.x}px`, top: `${node.y}px` }\"\n"
open(f1, 'w').writelines(lines)

# 2. ModernTable.vue
f2 = 'core/src/components/ui/ModernTable.vue'
lines = open(f2).readlines()
for i, line in enumerate(lines):
    if 'background: [`Active\',\'Success\'].includes(row[boolCol.key])' in line:
        lines[i] = "  background: ['Active','Success'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-success)', 0.2) : ['Pending','Warning'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-warning)', 0.2) : ['Error','Failed'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-error, #EF4444)', 0.2) : 'var(--bg-surface)',\n"
    if 'borderColor: [`Active\',\'Success\'].includes(row[boolCol.key])' in line:
        lines[i] = "  borderColor: ['Active','Success'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-success)', 0.4) : ['Pending','Warning'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-warning)', 0.4) : ['Error','Failed'].includes(row[boolCol.key]) ? getColorAlpha('var(--color-error, #EF4444)', 0.4) : 'var(--text-secondary)'\n"
    if 'background: [`Active\',\'Success\'].includes(row[col.key])' in line:
        lines[i] = "  background: ['Active','Success'].includes(row[col.key]) ? getColorAlpha('var(--color-success)', 0.2) : ['Pending','Warning'].includes(row[col.key]) ? getColorAlpha('var(--color-warning)', 0.2) : ['Error','Failed'].includes(row[col.key]) ? getColorAlpha('var(--color-error, #EF4444)', 0.2) : 'var(--bg-surface)',\n"
    if 'borderColor: [`Active\',\'Success\'].includes(row[col.key])' in line:
        lines[i] = "  borderColor: ['Active','Success'].includes(row[col.key]) ? getColorAlpha('var(--color-success)', 0.4) : ['Pending','Warning'].includes(row[col.key]) ? getColorAlpha('var(--color-warning)', 0.4) : ['Error','Failed'].includes(row[col.key]) ? getColorAlpha('var(--color-error, #EF4444)', 0.4) : 'var(--text-secondary)'\n"
open(f2, 'w').writelines(lines)

# 3. NetworkWaterfall.vue
f3 = 'core/src/components/ui/NetworkWaterfall.vue'
lines = open(f3).readlines()
for i, line in enumerate(lines):
    if 'background: req.color ? getColorAlpha' in line and 'req.method === `POST\'' in line:
        lines[i] = "  background: req.color ? getColorAlpha(req.color, 0.2) : (req.method === 'POST' ? getColorAlpha('var(--chart-5)', 0.2) : 'var(--bg-surface)'), \n"
open(f3, 'w').writelines(lines)

# 4. Roadmap.vue
f4 = 'core/src/components/ui/Roadmap.vue'
lines = open(f4).readlines()
for i, line in enumerate(lines):
    if 'backgroundColor: getStepStatus(idx) !== `upcoming\'' in line:
        lines[i] = "  backgroundColor: getStepStatus(idx) !== 'upcoming' ? getColorAlpha(getHexColor(step.color || (getStepStatus(idx) === 'done' ? 'var(--color-success)' : 'var(--color-secondary)')), 0.2) : 'rgb(var(--text-primary-rgb) / 0.05)'\n"
open(f4, 'w').writelines(lines)

print("Syntax errors manually fixed.")
