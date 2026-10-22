from sqlalchemy import create_engine, text
import json

engine = create_engine("postgresql://postgres:postgres@localhost:5435/presentation_db")
with engine.connect() as conn:
    res = conn.execute(text("SELECT config FROM style_variants WHERE slug='classic'")).fetchone()
    if res:
        config = res[0]
        config['line']['animation'] = 'particles'
        config['line']['style'] = 'dashed'
        config['line']['width'] = 2
        config['line']['color'] = 'brand-light-blue'
        
        conn.execute(
            text("UPDATE style_variants SET config = :config WHERE slug='classic'"),
            {"config": json.dumps(config)}
        )
        conn.commit()
        print("Updated classic variant line animation in DB!")
