import os
import sys
import json
sys.path.append('/app')
from backend.database import SessionLocal
from backend import models
from sqlalchemy.orm.attributes import flag_modified

db = SessionLocal()

# 1. Update Presentation 12 to project 3 (Derevnya)
pres = db.query(models.Presentation).filter(models.Presentation.id == 12).first()
if pres:
    print(f"Old folders: {[f.id for f in pres.folders]}")
    derevnya_folder = db.query(models.Folder).filter(models.Folder.project_id == 3).first()
    if not derevnya_folder:
        derevnya_folder = models.Folder(title="Черновики (Эко)", slug="derevnya-drafts", project_id=3)
        db.add(derevnya_folder)
        db.flush()
    pres.folders = [derevnya_folder]
    print("Moved presentation to Derevnya project folder!")

# 2. Update the slide payload
slide = db.query(models.Slide).filter(models.Slide.presentation_id == 12, models.Slide.component == 'ArchitectureDiagram').first()
if slide and slide.data:
    payload = slide.data.payload
    if 'nodes' in payload:
        for node in payload['nodes']:
            if node['id'] == 'in1': node['color'] = 'chart-2'
            if node['id'] == 'core1': node['color'] = 'color-primary'
            if node['id'] == 'out1': node['color'] = 'chart-3'
            if node['id'] == 'out2': node['color'] = 'chart-4'
    payload['variant'] = 'derevnya'
    slide.data.payload = payload
    flag_modified(slide.data, "payload")
    print("Updated slide payload to use dynamic tokens and derevnya variant!")
    
db.commit()
db.close()
