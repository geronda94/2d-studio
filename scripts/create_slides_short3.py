#!/usr/bin/env python3
"""Создаёт слайды для презентации шортс 3 (id=15)."""
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
        print(f"  ✗ {component}: {r.status_code} {r.text[:120]}")

# ─── HOOK (0–5.4s): Менеджер уволился, унёс базу ──────────────────────
slide("s3_hook_1", "BrowserMockupSlide", 0, 0,
    "База ушла с менеджером",
    "WhatsApp вместо CRM",
    payload={
        "items": [
            {"type": "html", "content": "<div style='padding:40px;text-align:center;font-family:Inter,sans-serif;'><div style='font-size:48px;margin-bottom:16px;'>📱</div><div style='font-size:20px;font-weight:700;color:#2C2724;margin-bottom:8px;'>База клиентов</div><div style='font-size:14px;color:#8A8179;'>В личном WhatsApp у менеджера</div><div style='margin-top:24px;padding:12px 24px;background:#FEE2E2;border-radius:8px;color:#DC2626;font-weight:600;'>Уволился · Унёс · 0 контактов в CRM</div></div>", "start_time": 500}
        ]
    })

# ─── МОСТ (5.6–12.1s): CRM фиксирует хаос ─────────────────────────────
slide("s3_most_1", "AnimatedStatsSlide", 5640, 1,
    "Дорогая CRM",
    "Фиксирует хаос за твои деньги",
    payload={
        "stats": [
            {"value": 0, "label": "Контактов в CRM", "start_time": 500},
            {"value": 100, "label": "Стоимость подписки €", "suffix": "€/год", "start_time": 1500},
            {"value": 0, "label": "Порядка в процессах", "start_time": 2500},
        ]
    })

# ─── PROOF (12.3–41.2s): Разбор ситуации ───────────────────────────────
slide("s3_proof_1", "TechStackSlide", 12320, 2,
    "Покупаешь HubSpot",
    "Нанимаешь интегратора",
    payload={
        "technologies": [
            {"name": "HubSpot", "icon": "logos:hubspot", "color": "#FF7A59", "start_time": 300},
            {"name": "Интегратор", "icon": "lucide:settings", "color": "#6366f1", "start_time": 800},
            {"name": "Обучение", "icon": "lucide:book-open", "color": "#10B981", "start_time": 1300},
        ]
    })

slide("s3_proof_2", "ArchitectureDiagram", 16000, 3,
    "Схема интеграции",
    "Поначалу всё работает",
    payload={
        "nodes": [
            {"id": "site", "title": "Сайт", "subtitle": "Заявки", "icon": "globe", "color": "blue", "start_time": 300, "is_main": False, "to": ["crm"]},
            {"id": "crm", "title": "HubSpot", "subtitle": "CRM", "icon": "database", "color": "amber", "start_time": 800, "is_main": True, "to": ["mgr"]},
            {"id": "mgr", "title": "Менеджер", "subtitle": "Обработка", "icon": "user", "color": "green", "start_time": 1400, "is_main": False},
        ],
        "show_data_flow": True,
    })

slide("s3_proof_3", "ComparisonTable", 19500, 4,
    "Три месяца vs Реальность",
    "Ожидание не совпадает с фактом",
    payload={
        "headers": ["", "Месяц 1", "Месяц 3"],
        "items": [
            {"feature": "Данные в CRM", "values": [True, False], "start_time": 300},
            {"feature": "Воронка актуальна", "values": [True, False], "start_time": 1000},
            {"feature": "Сделки закрыты", "values": [True, False], "start_time": 1700},
        ]
    })

slide("s3_proof_4", "ReceiptCard", 23500, 5,
    "Сделка на 30 000€",
    "Висит «в работе» — клиент у конкурента",
    payload={
        "title": "Потерянная сделка",
        "subtitle": "Клиент уже купил",
        "currency": "€",
        "total_text": "30 000",
        "items": [
            {"label": "Статус в CRM", "value": "В работе", "start_time": 300},
            {"label": "Реальность", "value": "У конкурента", "start_time": 800},
            {"label": "Данные обновлены", "value": "Никогда", "start_time": 1300},
        ]
    })

slide("s3_proof_5", "StatsBarChart", 29500, 6,
    "Данные для галочки",
    "Заносят в пятницу вечером",
    payload={
        "data": [
            {"label": "Пн", "value": 85, "start_time": 200},
            {"label": "Вт", "value": 72, "start_time": 400},
            {"label": "Ср", "value": 60, "start_time": 600},
            {"label": "Чт", "value": 45, "start_time": 800},
            {"label": "Пт", "value": 15, "start_time": 1000},
            {"label": "Сб", "value": 0, "start_time": 1200},
        ],
        "title": "Активность занесения данных",
        "subtitle": "% от реальных сделок",
    })

slide("s3_proof_6", "PremiumChecklist", 35000, 7,
    "Никто не прописал регламент",
    "Софт натянули поверх бардака",
    payload={
        "items": [
            {"text": "Регламент работы с заявками", "icon": "x", "start_time": 300},
            {"text": "Правила занесения данных", "icon": "x", "start_time": 1000},
            {"text": "Обязательность CRM", "icon": "x", "start_time": 1700},
        ]
    })

# ─── PAYOFF (41.4–49.1s): Вывод ────────────────────────────────────────
slide("s3_payoff_1", "InfographicCards", 41400, 8,
    "CRM = зеркало",
    "Что покажешь, то и отразит",
    payload={
        "items": [
            {"value": "0", "label": "Без порядка", "icon": "alert", "color": "red", "start_time": 300},
            {"value": "100", "label": "С порядком %", "icon": "check", "color": "green", "start_time": 1200},
            {"value": "!", "label": "Сначала бумага", "icon": "file", "color": "amber", "start_time": 2100},
        ]
    })

slide("s3_payoff_2", "ProcessFunnel", 45400, 9,
    "Порядок сначала",
    "Инструмент потом",
    payload={
        "layout": "vertical",
        "steps": [
            {"title": "Регламент на бумаге", "subtitle": "Процессы, роли, правила", "icon": "file", "color": "green", "start_time": 300},
            {"title": "Обучение команды", "subtitle": "Все понимают зачем", "icon": "users", "color": "blue", "start_time": 1200},
            {"title": "Только потом CRM", "subtitle": "Инструмент автоматизирует порядок", "icon": "database", "color": "amber", "start_time": 2100},
        ]
    })

# ─── HOOK OUT (49.3–55.8s): CTA ────────────────────────────────────────
slide("s3_hookout_1", "OutroSlide", 49320, 10,
    "Пришли скриншот воронки",
    "Telegram: @it2b",
    payload={
        "logo": "",
        "qr_code": "",
        "handle": "@it2b",
        "headline": "Скинь скриншот воронки продаж — покажу, где теряешь деньги",
    })

# ─── END MARKER ─────────────────────────────────────────────────────────
slide("s3_end", "EndMarkerSlide", 56960, 11)

print("\n✓ Все слайды шортс 3 созданы!")
