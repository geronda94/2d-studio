import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT default_payload FROM components WHERE slug = 'InteractiveArchitecture'")).fetchone()
    payload = row[0]
    
    # Fix start times to be monotonic
    current_time = 0
    for node in payload['nodes']:
        node['start_time'] = current_time
        current_time += 500
        
    conn.execute(
        text("UPDATE components SET default_payload = :payload WHERE slug = 'InteractiveArchitecture'"),
        {"payload": json.dumps(payload)}
    )
    conn.commit()
print("InteractiveArchitecture payload fixed!")
