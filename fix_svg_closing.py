import json
import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    svg_str = config['surface']['bg']['value']
    
    # Remove trailing </div>
    svg_str = svg_str.replace('</div>', '')
    
    # Just to be absolutely safe, let's also remove any leading <div>
    svg_str = svg_str.replace('<div class="forest-background">', '')
    
    config['surface']['bg']['value'] = svg_str.strip()
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()

print("SVG closing tags fixed in DB.")
