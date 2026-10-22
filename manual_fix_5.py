import os

f1 = 'core/src/components/ui/AnimatedStats.vue'
lines = open(f1).readlines()
for i, line in enumerate(lines):
    if '""0,40 ${sparklinePoints} 80,40``' in line:
        lines[i] = "  <polygon :points=\"`0,40 ${sparklinePoints} 80,40`\" :fill=\"`url(#${gradientId})`\" :style=\"{ opacity: Math.max(0, progress * 1) }\" />\n"
open(f1, 'w').writelines(lines)
print("Fixed AnimatedStats.vue")
