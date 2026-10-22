import sys
sys.path.append('backend')
from sqlalchemy import create_engine, text
from core.database import SessionLocal
import json

db = SessionLocal()
try:
    slides = db.execute(text("SELECT id, data FROM slides WHERE component = 'StatsBarChart'")).fetchall()
    for slide in slides:
        slide_id, data = slide
        if isinstance(data, str):
            data = json.loads(data)
        
        updated = False
        if "payload" in data:
            if data["payload"].get("base_color") == "#3b82f6":
                data["payload"]["base_color"] = "var(--brand-blue)"
                updated = True
            if data["payload"].get("peak_color") == "#f97316":
                data["payload"]["peak_color"] = "var(--brand-accent)"
                updated = True
                
        if updated:
            db.execute(text("UPDATE slides SET data = :data WHERE id = :id"), {"data": json.dumps(data), "id": slide_id})
            db.commit()
            print(f"Fixed slide {slide_id}")
finally:
    db.close()
