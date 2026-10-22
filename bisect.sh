#!/usr/bin/env bash
# Бисект-обёртка: применяет патч, гоняет пробник, откатывает.
# usage: ./bisect.sh "<описание>" "<python-код патча>"
set -u
cd "/home/goga/Рабочий стол/Projects/Presentation"
DESC="$1"; PATCH="$2"
cp /tmp/AD.pulled.vue core/src/components/ui/ArchitectureDiagram.vue
python3 -c "
f='core/src/components/ui/ArchitectureDiagram.vue'
s=open(f).read()
$PATCH
open(f,'w').write(s)
" || { echo "[$DESC] PATCH ERROR"; cp /tmp/AD.pulled.vue core/src/components/ui/ArchitectureDiagram.vue; exit 1; }
sleep 2
docker compose exec -T backend sh -c "pkill -f chrome-linux/chrome" 2>/dev/null
sleep 1
OUT=$(docker compose exec -T backend python /app/probe_seq.py 11 850 1100 1 2>&1 | grep -E "SHOT HUNG|NO HANG|BUDGET TIMEOUT|SHOT ERR" | head -2)
echo "[$DESC] -> $OUT"
cp /tmp/AD.pulled.vue core/src/components/ui/ArchitectureDiagram.vue
