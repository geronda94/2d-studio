import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT config FROM style_variants WHERE slug = 'derevnya'")).fetchone()
    config = row[0]
    
    config['surface']['bg']['fallbackColor'] = 'transparent'
    
    conn.execute(
        text("UPDATE style_variants SET config = :config WHERE slug = 'derevnya'"),
        {"config": json.dumps(config)}
    )
    conn.commit()
print("Set fallbackColor to transparent")
