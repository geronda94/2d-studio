import os
lines = open('core/src/components/ui/Ecosystem.vue').readlines()
lines[172] = "  if (progress === 0) return { left: '0px', top: '0px', opacity: 0, transform: `translate(${(targetX * 0.5).toFixed(4)}px, ${(targetY * 0.5).toFixed(4)}px)`, willChange: 'opacity, transform' }\n"
lines[173] = "  if (progress === 1) return { left: '0px', top: '0px', opacity: 1, transform: `translate(${targetX.toFixed(4)}px, ${targetY.toFixed(4)}px)`, willChange: 'auto' }\n"
open('core/src/components/ui/Ecosystem.vue', 'w').writelines(lines)
