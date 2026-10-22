import re

with open('core/src/components/ui/ArchitectureDiagram.vue', 'r') as f:
    content = f.read()

# Fix mobile paths
old_mobile_paths = """    if (props.mobile) {
      const sy = startNode.y;
      const ey = endNode.y;
      let sx, ex;
      if (startNode.x <= endNode.x) {
        sx = startNode.x + 70;
        ex = endNode.x - 70;
      } else {
        sx = startNode.x - 70;
        ex = endNode.x + 70;
      }
      const cx = (sx + ex) / 2;
      d = `M ${sx} ${sy} C ${cx} ${sy}, ${cx} ${ey}, ${ex} ${ey}`;
      length = Math.abs(ex - sx) + Math.abs(ey - sy) + 100;
    }"""

new_mobile_paths = """    if (props.mobile) {
      const sx = startNode.x;
      const ex = endNode.x;
      let sy, ey;
      if (startNode.y <= endNode.y) {
        sy = startNode.y + 40;
        ey = endNode.y - 40;
      } else {
        sy = startNode.y - 40;
        ey = endNode.y + 40;
      }
      const cy = (sy + ey) / 2;
      d = `M ${sx} ${sy} C ${sx} ${cy}, ${ex} ${cy}, ${ex} ${ey}`;
      length = Math.abs(ex - sx) + Math.abs(ey - sy) + 100;
    }"""

if old_mobile_paths in content:
    content = content.replace(old_mobile_paths, new_mobile_paths)
    print("Fixed mobile paths")
else:
    print("Mobile paths not found")

# Fix missing drop-shadow on node appear
old_css = """  }
  50% {
    opacity: 1;
  }
}
</style>"""

new_css = """  }
  50% {
    opacity: 1;
    filter: drop-shadow(0 0 8px currentColor);
  }
}
</style>"""

if old_css in content:
    content = content.replace(old_css, new_css)
    print("Fixed CSS drop-shadow")
else:
    print("CSS drop-shadow not found")

with open('core/src/components/ui/ArchitectureDiagram.vue', 'w') as f:
    f.write(content)
