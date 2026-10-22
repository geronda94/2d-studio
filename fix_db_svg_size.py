import json
import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    svg_str = config['surface']['bg']['value']
    
    # Remove the <rect> tag
    svg_str = re.sub(r'<rect width="100%" height="100%" fill="#FFF8EB"\s*/>', '', svg_str)
    
    # Also let's change preserveAspectRatio to "xMidYMax meet" just in case, but actually "none" or just keeping it might be fine if we use 100% auto
    svg_str = svg_str.replace('preserveAspectRatio="xMidYMax slice"', 'preserveAspectRatio="xMidYMax meet"')
    
    config['surface']['bg']['value'] = svg_str
    config['surface']['bg']['position'] = 'bottom center'
    config['surface']['bg']['size'] = '100% auto'
    config['surface']['bg']['fallbackColor'] = '#FFF8EB'
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()

print("DB SVG config updated.")
