from sqlalchemy import create_engine, text
import json
import os

db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/presentation_db")
engine = create_engine(db_url)
with engine.connect() as conn:
    res = conn.execute(text("SELECT config FROM style_variants WHERE slug='classic'")).fetchone()
    if res:
        config = res[0]
        config['line']['animation'] = 'none'
        config['line']['style'] = 'solid'
        config['line']['width'] = 1
        config['line']['color'] = 'border-strong'
        
        conn.execute(
            text("UPDATE style_variants SET config = :config WHERE slug='classic'"),
            {"config": json.dumps(config)}
        )
        conn.commit()
        print("Reverted classic variant line animation in DB!")
