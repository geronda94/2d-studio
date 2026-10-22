import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    row = conn.execute(text("SELECT example FROM components WHERE slug = 'InteractiveArchitecture'")).fetchone()
    if row and row[0]:
        payload = row[0]
        if 'nodes' in payload:
            current_time = 0
            for node in payload['nodes']:
                node['start_time'] = current_time
                current_time += 500
            
            conn.execute(
                text("UPDATE components SET example = :payload WHERE slug = 'InteractiveArchitecture'"),
                {"payload": json.dumps(payload)}
            )
            conn.commit()
            print("InteractiveArchitecture example fixed!")
