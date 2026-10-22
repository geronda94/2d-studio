import json
from sqlalchemy import create_engine, text

# 1. Read PostMaker.html
with open('/home/goga/Рабочий стол/Derevnya_Final_Deliverables./Derevnya_Deliverables/PostMaker.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 2. Extract <defs>
defs_lines = lines[489:532] # 490 to 532 are defs
defs_str = ''.join(defs_lines)

# 3. Extract SVG content
# SVG starts at 598 (0-indexed 598) and ends at 680 (0-indexed 680)
svg_start = 598
svg_end = 680
svg_lines = lines[svg_start:svg_end+1]

# Insert defs right after the <svg> opening tag
svg_str = svg_lines[0] + defs_str + ''.join(svg_lines[1:])

# Convert to single line to avoid issues (optional but good practice)
svg_str = svg_str.replace('\n', ' ')
# Ensure we don't have multiple spaces
import re
svg_str = re.sub(r'\s+', ' ', svg_str)

# 4. Update the DB
engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    # Ensure surface bg type is SVG
    if 'surface' not in config:
        config['surface'] = {}
    
    config['surface']['bg'] = {
        'type': 'svg',
        'value': svg_str
    }
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()

print("Derevnya config updated successfully in DB.")
