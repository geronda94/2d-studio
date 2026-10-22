#!/usr/bin/env python3
"""Исправления v3: разнообразие, тайминги, подписи."""
import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8000"

def get_slides(pres_id):
    r = requests.get(f"{BASE}/presentations/{pres_id}")
    return {s['slide_id']: s for s in r.json()['slides']}

def update(pres_id, slide_id, payload):
    slides = get_slides(pres_id)
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

# ═══════════════════════════════════════════════════════════════════════
# ШОРТС 2 (id=14)
# ═══════════════════════════════════════════════════════════════════════
print("=== Шортс 2 (id=14) ===")

# 3. InfographicCards — РАЗНЫЕ иконки и цвета
update(14, "s2_payoff_1", {
    "items": [
        {"id": 1, "label": "Контроль сумм", "value": "Нет лимитов", "trend": "Риск", "icon": "heroicons:shield-exclamation", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "Право на скидки", "value": "Без ограничений", "trend": "Убыток", "icon": "heroicons:gift", "color": "#F59E0B", "start_time": 1000},
        {"id": 3, "label": "Эскалация", "value": "Не работает", "trend": "Сбой", "icon": "heroicons:exclamation-triangle", "color": "#8B5CF6", "start_time": 1700},
    ]
})

# 8. InteractiveArchitecture — start_time ТОЛЬКО у одного ноды (фокус анимации)
update(14, "s2_proof_6", {
    "nodes": [
        {"id": "n1", "label": "Клиент", "desc": "Оптовый заказчик", "icon": "heroicons:users", "color": "chart-1", "details": "Запрашивает персональные условия", "to": ["n2"], "start_time": 0},
        {"id": "n2", "label": "ИИ-агент", "desc": "Выдал 30% без разрешения", "icon": "heroicons:cpu-chip", "color": "chart-2", "details": "Нейросеть自主 выдала скидку — критический сбой", "to": ["n3", "n4"], "start_time": 800},
        {"id": "n3", "label": "Менеджер", "desc": "Узнаёт последним", "icon": "heroicons:user", "color": "chart-3", "details": "Не контролирует действия бота", "to": []},
        {"id": "n4", "label": "Сделка", "desc": "Заморожена 15к€", "icon": "heroicons:lock-closed", "color": "chart-4", "details": "Клиент уже у конкурента", "to": []},
    ]
})

# 10. ProcessFunnel — подписи объясняют цифры
update(14, "s2_proof_8", {
    "layout": "horizontal",
    "steps": [
        {"label": "100 входящих", "count": 100, "icon": "heroicons:chat-bubble-left-right", "start_time": 300, "color": "#10B981"},
        {"label": "30 сложных", "count": 30, "icon": "heroicons:question-mark-circle", "start_time": 1200, "color": "#F59E0B"},
        {"label": "5 о скидках", "count": 5, "icon": "heroicons:stop-circle", "start_time": 2100, "color": "#EF4444"},
    ]
})

# 11. ReceiptCard — total_text словами
update(14, "s2_proof_4", {
    "title": "CORPORATE CARD",
    "subtitle": "Оптовая сделка",
    "currency": "€",
    "total_text": "ИТОГО",
    "footer_text": "Потерянная сделка из-за несанкционированной скидки",
    "total_start_time": 1500,
    "items": [
        {"name": "Партия товаров (6 мес.)", "price": 15000, "start_time": 300},
        {"name": "Выданная скидка ботом", "price": -4500, "start_time": 800},
        {"name": "Итого к оплате", "price": 10500, "start_time": 1300},
    ]
})

# ═══════════════════════════════════════════════════════════════════════
# ШОРТС 3 (id=15)
# ═══════════════════════════════════════════════════════════════════════
print("\n=== Шортс 3 (id=15) ===")

# 2. InfographicCards — РАЗНЫЕ иконки и цвета
update(15, "s3_payoff_1", {
    "items": [
        {"id": 1, "label": "Без порядка", "value": "0% данных", "trend": "Потери", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "С порядком", "value": "100% картина", "trend": "Контроль", "icon": "heroicons:check-badge", "color": "#10B981", "start_time": 1200},
        {"id": 3, "label": "Сначала бумага", "value": "Порядок → CRM", "trend": "Правильно", "icon": "heroicons:clipboard-document-check", "color": "#8B5CF6", "start_time": 2100},
    ]
})

# 10. ProcessFunnel — подписи объясняют цифры
update(15, "s3_payoff_2", {
    "layout": "horizontal",
    "steps": [
        {"label": "Регламент на бумаге", "count": 100, "icon": "heroicons:document-text", "start_time": 300, "color": "#10B981"},
        {"label": "Обучение команды", "count": 80, "icon": "heroicons:academic-cap", "start_time": 1200, "color": "#38BDF8"},
        {"label": "Только потом CRM", "count": 60, "icon": "heroicons:server-stack", "start_time": 2100, "color": "#F59E0B"},
    ]
})

# ReceiptCard шортс 3 — total_text словами
update(15, "s3_proof_4", {
    "title": "CORPORATE CARD",
    "subtitle": "Потерянная сделка",
    "currency": "€",
    "total_text": "ПОТЕРЯНО",
    "footer_text": "Клиент уже купил у конкурента",
    "total_start_time": 1500,
    "items": [
        {"name": "Сделка в CRM", "price": 30000, "start_time": 300},
        {"name": "Статус", "price": 0, "start_time": 800},
        {"name": "Реальность", "price": 0, "start_time": 1300},
    ]
})

print("\n✓ Все исправления v3 применены!")
