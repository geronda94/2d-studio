import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    conn.execute(
        text("UPDATE design_tokens SET value = '#FFF8EB' WHERE project_id = 3 AND token_key = 'bg-base'")
    )
    conn.execute(
        text("DELETE FROM design_tokens WHERE presentation_id = 13 AND token_key = 'bg-base'")
    )
    conn.commit()
print("Updated bg-base to #FFF8EB")
