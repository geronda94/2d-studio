#!/usr/bin/env python3
"""Создаёт слайды для презентации шортс 2 (id=14)."""
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

def slide(sid, component, start, order, title="", subtitle="", layout="col", payload=None):
    body = {
        "slide_id": sid, "component": component, "start_time": start,
        "order_index": order, "title": title, "subtitle": subtitle,
        "layout": layout, "data": {"payload": payload or {}}
    }
    r = requests.post(f"{BASE}/presentations/{PRES_ID}/slides", json=body)
    if r.status_code == 200:
        print(f"  ✓ {component} at {start}ms — {title[:40]}")
    else:
        print(f"  ✗ {component}: {r.status_code} {r.text[:100]}")
    return r

# ─── HOOK (0–6s): ИИ-агент пообещал скидку ─────────────────────────────
slide("s2_hook_1", "ChatMockupSlide", 0, 0,
    "ИИ-агент пообещал скидку",
    "Клиенту — которой нет в природе",
    payload={
        "bot_name": "AI Support Bot",
        "bot_subtitle": "Автоматическая поддержка",
        "messages": [
            {"sender": "user", "text": "Можно скидку на оптовый заказ?", "start_time": 500},
            {"sender": "bot", "text": "Конечно! Персональная скидка 30% 🎉", "start_time": 2000},
        ]
    })

# ─── МОСТ (6.2–12s): Вместо роста — раздаёт деньги ────────────────────
slide("s2_most_1", "AnimatedStatsSlide", 6200, 1,
    "Вместо роста продаж",
    "Нейросеть раздаёт твои деньги",
    payload={
        "stats": [
            {"value": "0", "label": "Рост продаж", "trend": "down", "start_time": 500},
            {"value": "−30%", "label": "Потери на скидках", "trend": "down", "start_time": 1500},
            {"value": "15K€", "label": "Потерянная сделка", "trend": "down", "start_time": 2500},
        ]
    })

# ─── PROOF (12.2–45.3s): Разбор ситуации ───────────────────────────────
slide("s2_proof_1", "PremiumChecklist", 12200, 2,
    "Первый месяц",
    "Всё работает идеально",
    payload={
        "items": [
            {"text": "Агент отвечает на частые вопросы", "icon": "check", "start_time": 300},
            {"text": "Поддержка разгружена наполовину", "icon": "check", "start_time": 1000},
            {"text": "Клиенты довольны скоростью", "icon": "check", "start_time": 1700},
        ]
    })

slide("s2_proof_2", "ArchitectureDiagram", 16000, 3,
    "Агент разгрузил поддержку",
    "Идеальная архитектура",
    payload={
        "nodes": [
            {"id": "client", "title": "Клиент", "subtitle": "Запрос", "icon": "users", "color": "blue", "start_time": 300, "is_main": False, "to": ["agent"]},
            {"id": "agent", "title": "ИИ-агент", "subtitle": "Auto-reply", "icon": "bot", "color": "green", "start_time": 800, "is_main": True, "to": ["crm"]},
            {"id": "crm", "title": "CRM", "subtitle": "HubSpot", "icon": "database", "color": "amber", "start_time": 1400, "is_main": False},
        ],
        "show_data_flow": True,
    })

slide("s2_proof_3", "ComparisonTable", 19500, 4,
    "На первый взгляд",
    "Отлично vs Реальность",
    payload={
        "headers": ["", "Ожидание", "Факт"],
        "items": [
            {"feature": "Ответы клиентам", "values": [True, True], "start_time": 300},
            {"feature": "Скидки только менеджер", "values": [True, False], "start_time": 1000},
            {"feature": "Контроль сделок", "values": [True, False], "start_time": 1700},
        ]
    })

slide("s2_proof_4", "ReceiptCard", 23500, 5,
    "Оптовый заказчик",
    "Партия на полгода",
    payload={
        "title": "Заказ на полгода",
        "subtitle": "Оптовая сделка",
        "currency": "€",
        "total_text": "15 000",
        "items": [
            {"label": "Партия товаров", "value": "6 мес.", "start_time": 300},
            {"label": "Ожидаемая скидка", "value": "0%", "start_time": 800},
            {"label": "Выданная скидка", "value": "30%", "start_time": 1300},
        ]
    })

slide("s2_proof_5", "NetworkWaterfall", 27500, 6,
    "Сделка встала намертво",
    "Клиент ждёт условия",
    payload={
        "total_ms": 5000,
        "requests": [
            {"name": "Клиент → Бот", "start_pct": 0, "duration_pct": 20, "status": "ok", "start_time": 200},
            {"name": "Бот → Скидка 30%", "start_pct": 20, "duration_pct": 30, "status": "ok", "start_time": 600},
            {"name": "Менеджер (не знает)", "start_pct": 50, "duration_pct": 40, "status": "error", "start_time": 1200},
            {"name": "Сделка заблокирована", "start_pct": 70, "duration_pct": 30, "status": "error", "start_time": 2000},
        ],
        "legend": [
            {"label": "Успешно", "color": "green"},
            {"label": "Ошибка", "color": "red"},
            {"label": "Ожидание", "color": "amber"},
        ]
    })

slide("s2_proof_6", "InteractiveArchitecture", 31500, 7,
    "Ты узнаёшь последним",
    "Клиент уже скринит экран",
    payload={
        "nodes": [
            {"id": "n1", "title": "Клиент", "subtitle": "Ждёт скидку", "icon": "users", "color": "blue", "x": 10, "y": 20, "start_time": 300},
            {"id": "n2", "title": "ИИ-агент", "subtitle": "Выдал 30%", "icon": "bot", "color": "red", "x": 50, "y": 20, "start_time": 800},
            {"id": "n3", "title": "Менеджер", "subtitle": "Узнаёт последним", "icon": "user", "color": "amber", "x": 90, "y": 20, "start_time": 1400},
            {"id": "n4", "title": "Сделка", "subtitle": "Заморожена", "icon": "lock", "color": "red", "x": 50, "y": 70, "start_time": 2000},
        ]
    })

slide("s2_proof_7", "CodeExplain", 35500, 8,
    "Промпт нейросети",
    "Ей дали инструкцию «отвечай клиентам»",
    layout="col",
    payload={
        "language": "text",
        "blocks": [
            {"code": "# Инструкция для бота\nОтвечай клиентам на частые вопросы.\nПомогай с выбором товаров.\nПредлагай помощь менеджера при сложных вопросах.\n\n# Чего НЕТ в инструкции:\n- Запрет на скидки\n- Лимиты сумм сделок\n- Коридор для эскалации", "start_time": 0},
        ]
    })

slide("s2_proof_8", "ProcessFunnel", 39500, 9,
    "Жёсткий коридор",
    "Шаг в сторону — зови менеджера",
    payload={
        "layout": "vertical",
        "steps": [
            {"title": "Частые вопросы", "subtitle": "Бот отвечает сам", "icon": "bot", "color": "green", "start_time": 300},
            {"title": "Сложный запрос", "subtitle": "Эскалация менеджеру", "icon": "user", "color": "amber", "start_time": 1200},
            {"title": "Скидки / суммы", "subtitle": "Стоп. Только живой менеджер", "icon": "lock", "color": "red", "start_time": 2100},
        ]
    })

# ─── PAYOFF (45.5–54.6s): Вывод ────────────────────────────────────────
slide("s2_payoff_1", "InfographicCards", 45500, 10,
    "ИИ без границ",
    "Фантазёр с доступом к кошельку",
    payload={
        "items": [
            {"value": "0", "label": "Контроль сумм", "icon": "shield", "color": "red", "start_time": 300},
            {"value": "∞", "label": "Право на скидки", "icon": "gift", "color": "red", "start_time": 1000},
            {"value": "!", "label": "Эскалация", "icon": "alert", "color": "amber", "start_time": 1700},
        ]
    })

slide("s2_payoff_2", "MetricScales", 49000, 11,
    "Прописывай границы",
    "Жёсткий коридор решает",
    payload={
        "metrics": [
            {"label": "Без границ", "value": 15, "max_value": 100, "color": "red", "start_time": 300},
            {"label": "С коридором", "value": 95, "max_value": 100, "color": "green", "start_time": 1200},
        ]
    })

# ─── HOOK OUT (54.8–59.9s): CTA ────────────────────────────────────────
slide("s2_hookout_1", "OutroSlide", 54800, 12,
    "Пришли инструкцию бота",
    "Telegram: @it2b",
    payload={
        "logo": "",
        "qr_code": "",
        "handle": "@it2b",
        "headline": "Пришли инструкцию своего бота — я покажу, где он может слить сделку",
    })

# ─── END MARKER ─────────────────────────────────────────────────────────
slide("s2_end", "EndMarkerSlide", 61080, 13)

print("\n✓ Все слайды созданы!")
