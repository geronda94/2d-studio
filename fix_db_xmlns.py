import json
import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    svg_str = config['surface']['bg']['value']
    
    if 'xmlns="http://www.w3.org/2000/svg"' not in svg_str:
        svg_str = svg_str.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        
    config['surface']['bg']['value'] = svg_str
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()
print("Added xmlns")
