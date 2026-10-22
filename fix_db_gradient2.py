import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')
with engine.connect() as conn:
    # REVERT GRADIENT TO ORIGINAL SUBTLE VERSION
    original_gradient = "radial-gradient(circle at 15% 0%, rgba(255, 209, 102, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(162, 212, 144, 0.12) 0%, transparent 60%), radial-gradient(circle at 80% 40%, rgba(255, 140, 0, 0.05) 0%, transparent 50%), radial-gradient(circle at 0% 100%, rgba(255, 179, 71, 0.10) 0%, transparent 60%)"
    
    conn.execute(
        text("UPDATE design_tokens SET value = :val WHERE project_id = 3 AND token_key = 'bg-image'"),
        {"val": original_gradient}
    )
    
    # REVERT BG-BASE TO #FFFFFF
    conn.execute(
        text("UPDATE design_tokens SET value = '#FFFFFF' WHERE project_id = 3 AND token_key = 'bg-base'")
    )
    
    conn.execute(text("DELETE FROM design_tokens WHERE presentation_id = 13 AND token_key IN ('bg-image', 'bg-base')"))
    
    conn.commit()
print("Gradient reverted to beautiful subtle version!")
