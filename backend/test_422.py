import requests

payload = {
    "slide_id": "slide-1789246800001",
    "component": "ArchitectureDiagram",
    "start_time": 1000.0,
    "title": "Архитектура",
    "subtitle": "",
    "layout": "col",
    "order_index": 1,
    "data": {
        "payload": {
            "nodes": [
                {
                    "id": "in1",
                    "title": "Telegram Bot",
                    "subtitle": "Frontend",
                    "icon": "telegram",
                    "color": "chart-2",
                    "start_time": 500,
                    "is_main": False,
                    "to": ["core1"]
                }
            ],
            "show_data_flow": True,
            "variant": "tech"
        }
    }
}

import os

# Базовый URL настраиваемый: с хоста http://localhost:8001, из контейнера http://backend:8000
BASE = os.environ.get("API_BASE_URL", "http://localhost:8001")
PRES = os.environ.get("TEST_PRESENTATION_ID", "13")

response = requests.post(f"{BASE}/presentations/{PRES}/slides", json=payload)
print(response.status_code)
print(response.text)

# Не оставляем мусор: удаляем проб-слайд, если он создан
try:
    created = response.json()
    if response.status_code == 200 and created.get("id"):
        requests.delete(f"{BASE}/presentations/slides/{created['id']}")
        print(f"cleaned up slide id={created['id']}")
except Exception:
    pass
