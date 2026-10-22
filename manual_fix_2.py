import os

# 1. PremiumChecklist.vue
f1 = 'core/src/components/ui/PremiumChecklist.vue'
lines = open(f1).readlines()
for i, line in enumerate(lines):
    if 'borderColor: `color-mix(in srgb, var(--text-primary)' in line:
        lines[i] = "  borderColor: getColorAlpha('var(--text-primary)', (5 + 15 * getActiveProgress(idx)) / 100)\n"
    if ':style="{ color: "color-mix(' in line:
        lines[i] = "  :style=\"{ color: getColorAlpha('var(--text-primary)', (70 + 30 * getActiveProgress(idx)) / 100) }\">\n"
open(f1, 'w').writelines(lines)

# 2. HorizontalDivider.vue
f2 = 'core/src/components/ui/HorizontalDivider.vue'
new_f2 = open(f2).read().replace(
'''  background: linear-gradient(
  90deg, 
  color-mix(in srgb, var(--line-color) 30%, transparent) 0%, 
  color-mix(in srgb, var(--line-color) 30%, transparent) 35%, 
  var(--line-color) 45%,
  color-mix(in srgb, var(--text-primary) 30%, var(--line-color)) 50%, 
  var(--line-color) 55%,
  color-mix(in srgb, var(--line-color) 30%, transparent) 65%, 
  color-mix(in srgb, var(--line-color) 30%, transparent) 100%
  );
  background-size: 200% 100%;
  box-shadow: 0 0 8px color-mix(in srgb, var(--line-color) 30%, transparent);''', 
'''  background: linear-gradient(
  90deg, 
  transparent 0%, 
  transparent 35%, 
  var(--line-color) 45%,
  var(--text-primary) 50%, 
  var(--line-color) 55%,
  transparent 65%, 
  transparent 100%
  );
  background-size: 200% 100%;'''
)
open(f2, 'w').write(new_f2)

# 3. ComparisonTable.vue
f3 = 'core/src/components/ui/ComparisonTable.vue'
lines = open(f3).readlines()
for i, line in enumerate(lines):
    if 'borderColor: p > 0 ? `color-mix' in line:
        lines[i] = "  borderColor: p > 0 ? getColorAlpha('var(--color-accent)', p) : 'rgb(var(--text-muted-rgb) / 0.3)',\n"
    if 'backgroundColor: p > 0 ? `color-mix' in line:
        lines[i] = "  backgroundColor: p > 0 ? getColorAlpha('var(--color-accent)', p * 0.5) : 'rgb(var(--text-muted-rgb) / 0.5)',\n"
open(f3, 'w').writelines(lines)

print("Done")
