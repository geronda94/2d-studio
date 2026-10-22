import json
import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    svg_str = config['surface']['bg']['value']
    
    # Replace CSS variables
    svg_str = svg_str.replace('var(--color-forest)', '#4A6038')
    svg_str = svg_str.replace('var(--color-primary)', '#D87B22')
    svg_str = svg_str.replace('var(--color-text-main)', '#2C211A')
    svg_str = svg_str.replace('var(--color-text-muted)', '#6B5B50')
    svg_str = svg_str.replace('var(--color-bg-main)', '#FFF8EB')
    
    # Insert background rect
    if '<rect width="100%" height="100%" fill="#FFF8EB"' not in svg_str:
        svg_str = re.sub(r'(<svg[^>]*>)', r'\1<rect width="100%" height="100%" fill="#FFF8EB" />', svg_str, count=1)
        
    config['surface']['bg']['value'] = svg_str
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()

print("SVG colors fixed and background rect added in DB.")
