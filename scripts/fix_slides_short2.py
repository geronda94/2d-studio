#!/usr/bin/env python3
"""Исправляет payload слайдов презентации 14 (шортс 2) по example из БД."""
import requests, json

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8000"
PRES_ID = 14

def update_slide(slide_id, payload):
    r = requests.get(f"{BASE}/presentations/{PRES_ID}")
    pres = r.json()
    for s in pres['slides']:
        if s['slide_id'] == slide_id:
            internal_id = s['id']
            r2 = requests.put(f"{BASE}/presentations/slides/{internal_id}", json={
                "slide_id": slide_id,
                "component": s['component'],
                "start_time": s['start_time'],
                "order_index": s['order_index'],
                "title": s.get('title', ''),
                "subtitle": s.get('subtitle', ''),
                "layout": s.get('layout', 'col'),
                "data": {"payload": payload}
            })
            if r2.status_code == 200:
                print(f"  ✓ {slide_id}")
            else:
                print(f"  ✗ {slide_id}: {r2.status_code} {r2.text[:120]}")
            return
    print(f"  ✗ {slide_id}: not found")

# ─── HOOK: ChatMockupSlide — role вместо sender ────────────────────────
update_slide("s2_hook_1", {
    "bot_name": "AI Support Bot",
    "bot_subtitle": "Автоматическая поддержка",
    "bot_avatar": "AI",
    "messages": [
        {"role": "user", "text": "Можно скидку на оптовый заказ?", "start_time": 500},
        {"role": "assistant", "text": "Конечно! Персональная скиdка 30% 🎉", "start_time": 2000},
    ]
})

# ─── МОСТ: AnimatedStatsSlide — +icon ──────────────────────────────────
update_slide("s2_most_1", {
    "stats": [
        {"value": 0, "label": "Рост продаж", "icon": "lucide:trending-down", "color": "#EF4444", "start_time": 500},
        {"value": 30, "label": "Потери на скидках", "suffix": "%", "icon": "lucide:percent", "color": "#EF4444", "start_time": 1500},
        {"value": 15000, "label": "Потерянная сделка", "suffix": "€", "icon": "lucide:euro", "color": "#EF4444", "start_time": 2500},
    ]
})

# ─── PROOF 1: PremiumChecklist — label+desc+icon+color ─────────────────
update_slide("s2_proof_1", {
    "items": [
        {"label": "Ответы на вопросы", "desc": "Агент обрабатывает частые запросы", "icon": "heroicons:check-circle", "color": "brand-green", "start_time": 300},
        {"label": "Поддержка разгружена", "desc": "Наполовину меньше обращений к менеджерам", "icon": "heroicons:check-circle", "color": "brand-green", "start_time": 1000},
        {"label": "Клиенты довольны", "desc": "Скорость ответа выросла в 3 раза", "icon": "heroicons:check-circle", "color": "brand-green", "start_time": 1700},
    ]
})

# ─── PROOF 3: ComparisonTable — +id в items ────────────────────────────
update_slide("s2_proof_3", {
    "headers": ["", "Ожидание", "Факт"],
    "items": [
        {"id": "r1", "label": "Ответы клиентам", "values": [True, True], "start_time": 300},
        {"id": "r2", "label": "Скидки только менеджер", "values": [True, False], "start_time": 1000},
        {"id": "r3", "label": "Контроль сделок", "values": [True, False], "start_time": 1700},
    ]
})

# ─── PROOF 4: ReceiptCard — name/price + footer_text ────────────────────
update_slide("s2_proof_4", {
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

# ─── PROOF 5: NetworkWaterfall — start_ms/duration_ms + method/icon ─────
update_slide("s2_proof_5", {
    "total_ms": 5000,
    "requests": [
        {"name": "Клиент → Бот", "method": "MSG", "type": "api", "start_ms": 0, "duration_ms": 1000, "start_time": 200, "color": "#38BDF8", "icon": "heroicons:chat-bubble-left"},
        {"name": "Бот → Скидка 30%", "method": "DISCOUNT", "type": "api", "start_ms": 1000, "duration_ms": 1500, "start_time": 600, "color": "#10B981", "icon": "heroicons:percentage-badge"},
        {"name": "Менеджер (не знает)", "method": "NONE", "type": "api", "start_ms": 2500, "duration_ms": 1500, "start_time": 1200, "color": "#EF4444", "icon": "heroicons:x-circle"},
        {"name": "Сделка заморожена", "method": "BLOCK", "type": "api", "start_ms": 3500, "duration_ms": 1500, "start_time": 2000, "color": "#EF4444", "icon": "heroicons:lock-closed"},
    ]
})

# ─── PROOF 6: InteractiveArchitecture — label/desc + details ────────────
update_slide("s2_proof_6", {
    "nodes": [
        {"id": "n1", "label": "Клиент", "desc": "Ждёт скидку", "icon": "heroicons:users", "color": "chart-1", "details": "Оптовый заказчик запрашивает персональные условия", "x": 10, "y": 20, "start_time": 300},
        {"id": "n2", "label": "ИИ-агент", "desc": "Выдал 30%", "icon": "heroicons:cpu-chip", "color": "color-error", "details": "Нейросеть自主 выдала скидку без разрешения", "x": 50, "y": 20, "start_time": 800},
        {"id": "n3", "label": "Менеджер", "desc": "Узнаёт последним", "icon": "heroicons:user", "color": "brand-amber", "details": "Не контролирует действия бота", "x": 90, "y": 20, "start_time": 1400},
        {"id": "n4", "label": "Сделка", "desc": "Заморожена", "icon": "heroicons:lock-closed", "color": "color-error", "details": "15 000€ в статусе ожидания", "x": 50, "y": 70, "start_time": 2000},
    ]
})

# ─── PROOF 8: ProcessFunnel — label/count ──────────────────────────────
update_slide("s2_proof_8", {
    "layout": "vertical",
    "steps": [
        {"label": "Частые вопросы", "count": 100, "icon": "heroicons:chat-bubble-left-right", "start_time": 300, "color": "#10B981"},
        {"label": "Сложный запрос", "count": 30, "icon": "heroicons:question-mark-circle", "start_time": 1200, "color": "#F59E0B"},
        {"label": "Скидки / суммы", "count": 5, "icon": "heroicons:stop-circle", "start_time": 2100, "color": "#EF4444"},
    ]
})

# ─── PAYOFF 1: InfographicCards — +id +trend ───────────────────────────
update_slide("s2_payoff_1", {
    "items": [
        {"id": 1, "label": "Контроль сумм", "value": "0", "trend": "Нет лимитов", "icon": "heroicons:shield-exclamation", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "Право на скидки", "value": "∞", "trend": "Без ограничений", "icon": "heroicons:gift", "color": "#EF4444", "start_time": 1000},
        {"id": 3, "label": "Эскалация", "value": "!", "trend": "Не работает", "icon": "heroicons:exclamation-triangle", "color": "#F59E0B", "start_time": 1700},
    ]
})

# ─── PAYOFF 2: MetricScales — percentage + gradient color ──────────────
update_slide("s2_payoff_2", {
    "metrics": [
        {"id": 1, "label": "Без границ", "percentage": 15, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 300},
        {"id": 2, "label": "С коридором", "percentage": 95, "color": "linear-gradient(to right, #10B981, #34D399)", "start_time": 1200},
    ],
    "title": "Прописывай границы",
    "subtitle": "Жёсткий коридор решает"
})

# ─── OUTRO: OutroSlide — с реальным qr_code ────────────────────────────
update_slide("s2_hookout_1", {
    "logo": "",
    "qr_code": "",
    "handle": "@it2b",
    "headline": "Пришли инструкцию своего бота — я покажу, где он может слить сделку",
})

print("\n✓ Шортс 2 исправлен!")
