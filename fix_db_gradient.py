import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    # 1. Update project 3 token
    new_gradient = "radial-gradient(circle at 15% 0%, rgba(255, 209, 102, 0.4) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(162, 212, 144, 0.5) 0%, transparent 60%), radial-gradient(circle at 80% 40%, rgba(255, 140, 0, 0.3) 0%, transparent 50%), radial-gradient(circle at 0% 100%, rgba(255, 179, 71, 0.4) 0%, transparent 60%)"
    
    conn.execute(
        text("UPDATE design_tokens SET value = :val WHERE project_id = 3 AND token_key = 'bg-image'"),
        {"val": new_gradient}
    )
    
    # Also update presentation 13 if it exists, or insert it just to be safe
    # Wait, presentation 13 tokens override project tokens if they exist.
    # Let's just delete presentation 13 bg-image so it falls back to project 3.
    conn.execute(
        text("DELETE FROM design_tokens WHERE presentation_id = 13 AND token_key = 'bg-image'")
    )
    
    conn.commit()
print("Gradient opacities boosted!")
