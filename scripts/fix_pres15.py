#!/usr/bin/env python3
"""Полное исправление презентации 15 — все слайды по example из БД."""
import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8000"
PRES_ID = 15

def get_slides():
    r = requests.get(f"{BASE}/presentations/{PRES_ID}")
    return {s['slide_id']: s for s in r.json()['slides']}

def update(slide_id, payload):
    slides = get_slides()
    s = slides[slide_id]
    r = requests.put(f"{BASE}/presentations/slides/{s['id']}", json={
        "slide_id": slide_id,
        "component": s['component'],
        "start_time": s['start_time'],
        "order_index": s['order_index'],
        "title": s.get('title', ''),
        "subtitle": s.get('subtitle', ''),
        "layout": s.get('layout', 'col'),
        "data": {"payload": payload}
    })
    status = "✓" if r.status_code == 200 else f"✗ {r.status_code}"
    print(f"  {status} {slide_id}")

# 1. BrowserMockupSlide — type: "html" вместо "image" (надёжнее)
update("s3_hook_1", {
    "items": [
        {"id": "b1", "url": "crm.example.com/contacts", "type": "html",
         "content": "<div style='display:flex;flex-direction:column;height:100%;background:#0B1322;color:#F8FAFC;font-family:Inter,sans-serif;'><div style='padding:16px 24px;border-bottom:1px solid #1E293B;display:flex;align-items:center;gap:12px;'><div style='width:36px;height:36px;background:#EF4444;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;'>CRM</div><div><div style='font-size:16px;font-weight:600;'>Контакты</div><div style='font-size:12px;color:#64748B;'>0 записей</div></div></div><div style='flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;'><div style='font-size:64px;margin-bottom:16px;'>📱</div><div style='font-size:18px;font-weight:600;margin-bottom:8px;'>Пустая база</div><div style='font-size:14px;color:#64748B;text-align:center;'>Все контакты в WhatsApp<br>у бывшего менеджера</div><div style='margin-top:24px;padding:10px 20px;background:#FEE2E2;border-radius:8px;color:#DC2626;font-weight:600;font-size:13px;'>0 контактов · CRM не используется</div></div></div>",
         "scroll": False, "start_time": 0}
    ]
})

# 2. AnimatedStatsSlide — без value=0, разные цвета
update("s3_most_1", {
    "stats": [
        {"value": 100, "label": "Контактов потеряно", "suffix": "%", "color": "#EF4444", "icon": "lucide:users-x", "start_time": 500},
        {"value": 50, "label": "Подписка CRM", "suffix": "€/год", "color": "#F59E0B", "icon": "lucide:credit-card", "start_time": 1500},
        {"value": 0, "label": "Порядка в данных", "suffix": "", "color": "#8B5CF6", "icon": "lucide:database-x", "start_time": 2500},
    ]
})

# 4. ArchitectureDiagram — color: chart-N
update("s3_proof_2", {
    "nodes": [
        {"id": "site", "title": "Сайт", "subtitle": "Заявки", "icon": "globe", "color": "chart-1", "start_time": 300, "is_main": False, "to": ["crm"]},
        {"id": "crm", "title": "HubSpot", "subtitle": "CRM", "icon": "database", "color": "color-primary", "start_time": 800, "is_main": True, "to": ["mgr"]},
        {"id": "mgr", "title": "Менеджер", "subtitle": "Обработка", "icon": "user", "color": "chart-3", "start_time": 1400, "is_main": False},
    ],
    "show_data_flow": True,
})

# 5. ComparisonTable — +id
update("s3_proof_3", {
    "headers": ["", "Месяц 1", "Месяц 3"],
    "items": [
        {"id": "r1", "label": "Данные в CRM", "values": [True, False], "start_time": 300},
        {"id": "r2", "label": "Воронка актуальна", "values": [True, False], "start_time": 1000},
        {"id": "r3", "label": "Сделки закрыты", "values": [True, False], "start_time": 1700},
    ]
})

# 6. ReceiptCard — total_text словами, price не 0
update("s3_proof_4", {
    "title": "CORPORATE CARD",
    "subtitle": "Потерянная сделка",
    "currency": "€",
    "total_text": "ПОТЕРЯНО",
    "footer_text": "Клиент уже купил у конкурента",
    "total_start_time": 1500,
    "items": [
        {"name": "Сделка в CRM", "price": 30000, "start_time": 300},
        {"name": "Статус в системе", "price": 0, "start_time": 800},
        {"name": "Реальность", "price": 0, "start_time": 1300},
    ]
})

# 7. StatsBarChart — заголовок и подзаголовок
update("s3_proof_5", {
    "base_color": "var(--brand-blue)",
    "peak_color": "var(--brand-amber)",
    "data": [
        {"label": "Пн", "value": 85, "start_time": 200},
        {"label": "Вт", "value": 72, "start_time": 400},
        {"label": "Ср", "value": 60, "start_time": 600},
        {"label": "Чт", "value": 45, "start_time": 800},
        {"label": "Пт", "value": 15, "start_time": 1000},
        {"label": "Сб", "value": 0, "start_time": 1200},
    ],
    "title": "Активность занесения",
    "subtitle": "% от реальных сделок",
})

# 8. PremiumChecklist — РАЗНЫЕ иконки и цвета
update("s3_proof_6", {
    "items": [
        {"label": "Регламент заявок", "desc": "Не прописан до сих пор", "icon": "heroicons:document-text", "color": "brand-blue", "start_time": 300},
        {"label": "Правила данных", "desc": "Менеджеры игнорируют", "icon": "heroicons:pencil-square", "color": "brand-amber", "start_time": 1000},
        {"label": "Обязательность CRM", "desc": "Никто не контролирует", "icon": "heroicons:lock-closed", "color": "brand-purple", "start_time": 1700},
    ]
})

# 9. InfographicCards — разные цвета
update("s3_payoff_1", {
    "items": [
        {"id": 1, "label": "Без порядка", "value": "0%", "trend": "Потери", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "С порядком", "value": "100%", "trend": "Контроль", "icon": "heroicons:check-badge", "color": "#10B981", "start_time": 1200},
        {"id": 3, "label": "Сначала бумага", "value": "!", "trend": "Правильно", "icon": "heroicons:clipboard-document-check", "color": "#F59E0B", "start_time": 2100},
    ]
})

# 10. ProcessFunnel — label БЕЗ числа
update("s3_payoff_2", {
    "layout": "horizontal",
    "steps": [
        {"label": "Регламент", "count": 100, "icon": "heroicons:document-text", "start_time": 300, "color": "#10B981"},
        {"label": "Обучение", "count": 80, "icon": "heroicons:academic-cap", "start_time": 1200, "color": "#38BDF8"},
        {"label": "CRM", "count": 60, "icon": "heroicons:server-stack", "start_time": 2100, "color": "#F59E0B"},
    ]
})

print("\n✓ Презентация 15 полностью исправлена!")
