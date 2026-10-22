#!/usr/bin/env python3
"""Исправления v4: PremiumChecklist иконки, ProcessFunnel подписи, InfographicCards value."""
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

# 3. PremiumChecklist — РАЗНЫЕ иконки и цвета
update(14, "s2_proof_1", {
    "items": [
        {"label": "Ответы на вопросы", "desc": "Агент обрабатывает частые запросы", "icon": "heroicons:chat-bubble-left-right", "color": "brand-blue", "start_time": 300},
        {"label": "Поддержка разгружена", "desc": "Наполовину меньше обращений к менеджерам", "icon": "heroicons:user-group", "color": "brand-green", "start_time": 1000},
        {"label": "Клиенты довольны", "desc": "Скорость ответа выросла в 3 раза", "icon": "heroicons:face-smile", "color": "brand-amber", "start_time": 1700},
    ]
})

# 10. ProcessFunnel — label БЕЗ числа (count уже показан)
update(14, "s2_proof_8", {
    "layout": "horizontal",
    "steps": [
        {"label": "Входящих", "count": 100, "icon": "heroicons:chat-bubble-left-right", "start_time": 300, "color": "#10B981"},
        {"label": "Сложных", "count": 30, "icon": "heroicons:question-mark-circle", "start_time": 1200, "color": "#F59E0B"},
        {"label": "О скидках", "count": 5, "icon": "heroicons:stop-circle", "start_time": 2100, "color": "#EF4444"},
    ]
})

# 11. InfographicCards — КОРОТКИЕ value чтобы влезали в карточку
update(14, "s2_payoff_1", {
    "items": [
        {"id": 1, "label": "Контроль сумм", "value": "Нет", "trend": "Риск", "icon": "heroicons:shield-exclamation", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "Право на скидки", "value": "∞", "trend": "Убыток", "icon": "heroicons:gift", "color": "#F59E0B", "start_time": 1000},
        {"id": 3, "label": "Эскалация", "value": "0", "trend": "Сбой", "icon": "heroicons:exclamation-triangle", "color": "#8B5CF6", "start_time": 1700},
    ]
})

# ═══════════════════════════════════════════════════════════════════════
# ШОРТС 3 (id=15)
# ═══════════════════════════════════════════════════════════════════════
print("\n=== Шортс 3 (id=15) ===")

# 2. InfographicCards — КОРОТКИЕ value
update(15, "s3_payoff_1", {
    "items": [
        {"id": 1, "label": "Без порядка", "value": "0%", "trend": "Потери", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "С порядком", "value": "100%", "trend": "Контроль", "icon": "heroicons:check-badge", "color": "#10B981", "start_time": 1200},
        {"id": 3, "label": "Сначала бумага", "value": "!", "trend": "Правильно", "icon": "heroicons:clipboard-document-check", "color": "#8B5CF6", "start_time": 2100},
    ]
})

# 10. ProcessFunnel — label БЕЗ числа
update(15, "s3_payoff_2", {
    "layout": "horizontal",
    "steps": [
        {"label": "Регламент", "count": 100, "icon": "heroicons:document-text", "start_time": 300, "color": "#10B981"},
        {"label": "Обучение", "count": 80, "icon": "heroicons:academic-cap", "start_time": 1200, "color": "#38BDF8"},
        {"label": "CRM", "count": 60, "icon": "heroicons:server-stack", "start_time": 2100, "color": "#F59E0B"},
    ]
})

print("\n✓ Все исправления v4 применены!")
