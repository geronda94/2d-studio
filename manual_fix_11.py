import os

f = 'core/src/components/ui/ChatMockup.vue'
lines = open(f).readlines()
for i, line in enumerate(lines):
    if 'getColorAlpha(' in line and '`)' in line:
        lines[i] = line.replace('`)', ')')

open(f, 'w').writelines(lines)
print("Fixed ChatMockup stray backtick")
