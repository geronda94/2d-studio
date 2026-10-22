import json
import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    svg_str = config['surface']['bg']['value']
    
    # Remove width="100%" and height="100%"
    svg_str = re.sub(r'\s+width="100%"', '', svg_str)
    svg_str = re.sub(r'\s+height="100%"', '', svg_str)
    
    # Also let's change preserveAspectRatio to none just to see if it helps, no wait, viewBox is enough.
    
    config['surface']['bg']['value'] = svg_str
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()
print("Removed width/height")
