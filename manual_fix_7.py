import os

f = 'core/src/components/ui/TerminalMockup.vue'
lines = open(f).readlines()
for i, line in enumerate(lines):
    if 'animate-pulse' in line:
        # replace 'animate-pulse' with ''
        lines[i] = line.replace('animate-pulse', '')
        # add the style
        lines[i] = lines[i].replace('class="', ':style="{ opacity: (relativeTime % 1000) < 500 ? 1 : 0 }" class="')
open(f, 'w').writelines(lines)
print('Fixed TerminalMockup.vue')
