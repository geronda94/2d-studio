#!/usr/bin/env python3
"""Исправляет payload слайдов презентаций 14 и 15 — все ошибки по feedback."""
import requests, json

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

# 2. AnimatedStatsSlide — разноцветные метрики, value > 0
update(14, "s2_most_1", {
    "stats": [
        {"value": 100, "label": "Потери на скидках", "suffix": "%", "color": "#EF4444", "icon": "lucide:trending-down", "start_time": 500},
        {"value": 15, "label": "Сделок слито", "suffix": "шт", "color": "#F59E0B", "icon": "lucide:alert-triangle", "start_time": 1500},
        {"value": 42, "label": "Средний чек просел", "suffix": "%", "color": "#8B5CF6", "icon": "lucide:arrow-down-right", "start_time": 2500},
    ]
})

# 7. ReceiptCard — разноцветные строки
update(14, "s2_proof_4", {
    "title": "CORPORATE CARD",
    "subtitle": "Оптовая сделка",
    "currency": "€",
    "total_text": "15 000",
    "footer_text": "Потерянная сделка из-за несанкционированной скидки",
    "total_start_time": 1500,
    "items": [
        {"name": "Партия товаров (6 мес.)", "price": 15000, "start_time": 300},
        {"name": "Выданная скидка ботом", "price": -4500, "start_time": 800},
        {"name": "Итого к оплате", "price": 10500, "start_time": 1300},
    ]
})

# 8. InteractiveArchitecture — УБРАЛ x/y, компонент сам считает позиции
update(14, "s2_proof_6", {
    "nodes": [
        {"id": "n1", "label": "Клиент", "desc": "Оптовый заказчик", "icon": "heroicons:users", "color": "chart-1", "details": "Запрашивает персональные условия", "to": ["n2"], "start_time": 300},
        {"id": "n2", "label": "ИИ-агент", "desc": "Выдал 30% без разрешения", "icon": "heroicons:cpu-chip", "color": "chart-2", "details": "Нейросеть自主 выдала скидку", "to": ["n3", "n4"], "start_time": 800},
        {"id": "n3", "label": "Менеджер", "desc": "Узнаёт последним", "icon": "heroicons:user", "color": "chart-3", "details": "Не контролирует действия бота", "to": [], "start_time": 1400},
        {"id": "n4", "label": "Сделка", "desc": "Заморожена 15к€", "icon": "heroicons:lock-closed", "color": "chart-4", "details": "Клиент уже у конкурента", "to": [], "start_time": 2000},
    ]
})

# 10. ProcessFunnel — horizontal, 3 items, разные цвета
update(14, "s2_proof_8", {
    "layout": "horizontal",
    "steps": [
        {"label": "Частые вопросы", "count": 100, "icon": "heroicons:chat-bubble-left-right", "start_time": 300, "color": "#10B981"},
        {"label": "Сложный запрос", "count": 30, "icon": "heroicons:question-mark-circle", "start_time": 1200, "color": "#F59E0B"},
        {"label": "Скидки / суммы", "count": 5, "icon": "heroicons:stop-circle", "start_time": 2100, "color": "#EF4444"},
    ]
})

# 11. MetricScales — percentage + gradient colors
update(14, "s2_payoff_2", {
    "metrics": [
        {"id": 1, "label": "Без границ", "percentage": 15, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 300},
        {"id": 2, "label": "С коридором", "percentage": 95, "color": "linear-gradient(to right, #10B981, #34D399)", "start_time": 1200},
    ],
    "title": "Прописывай границы",
    "subtitle": "Жёсткий коридор решает"
})

# ═══════════════════════════════════════════════════════════════════════
# ШОРТС 3 (id=15)
# ═══════════════════════════════════════════════════════════════════════
print("\n=== Шортс 3 (id=15) ===")

# 1. BrowserMockupSlide — type: "image" + реальный URL картинки
update(15, "s3_hook_1", {
    "items": [
        {"id": "b1", "url": "crm.example.com/contacts", "type": "image", "content": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800", "scroll": False, "start_time": 500}
    ]
})

# 2. InfographicCards — разноцветные, value = текст, не пустые
update(15, "s3_payoff_1", {
    "items": [
        {"id": 1, "label": "Без порядка", "value": "0% данных", "trend": "Потери", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "С порядком", "value": "100% картина", "trend": "Контроль", "icon": "heroicons:check-circle", "color": "#10B981", "start_time": 1200},
        {"id": 3, "label": "Сначала бумага", "value": "Порядок → CRM", "trend": "Правильно", "icon": "heroicons:document-text", "color": "#F59E0B", "start_time": 2100},
    ]
})

# 10. ProcessFunnel — horizontal, 3 items
update(15, "s3_payoff_2", {
    "layout": "horizontal",
    "steps": [
        {"label": "Регламент", "count": 100, "icon": "heroicons:document-text", "start_time": 300, "color": "#10B981"},
        {"label": "Обучение", "count": 80, "icon": "heroicons:users", "start_time": 1200, "color": "#38BDF8"},
        {"label": "CRM", "count": 60, "icon": "heroicons:server-stack", "start_time": 2100, "color": "#F59E0B"},
    ]
})

print("\n✓ Все исправления применены!")
