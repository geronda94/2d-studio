import re

with open('core/src/components/ui/InteractiveArchitecture.vue', 'r') as f:
    content = f.read()

old_path = """ <path v-for="(edge, i) in computedEdges" :key="'fg'+i"
 :d="calculatePath(edge.from, edge.to)" 
 fill="none" 
 :stroke="getEdgeColor(edge.to)" 
 :stroke-width="line.width" 
 stroke-linecap="round"
 :style="{ strokeDasharray: line.dash }" />"""

new_path = """ <path v-for="(edge, i) in computedEdges" :key="'fg'+i"
 :d="calculatePath(edge.from, edge.to)" 
 fill="none" 
 :stroke="getEdgeColor(edge.to)" 
 :stroke-width="line.width" 
 stroke-linecap="round"
 :style="{ 
   strokeDasharray: line.animation === 'none' ? line.dash : '10 30',
   strokeDashoffset: line.animation === 'none' ? 0 : 40 - ((relativeTime % 2000) / 2000 * 40)
 }" />"""

if old_path in content:
    content = content.replace(old_path, new_path)
    print("Fixed InteractiveArchitecture line animation!")
else:
    print("Could not find the path block")

with open('core/src/components/ui/InteractiveArchitecture.vue', 'w') as f:
    f.write(content)
