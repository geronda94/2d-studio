#!/usr/bin/env python3
"""Исправляет payload слайдов презентации 15 (шортс 3) по example из БД."""
import requests, json

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8000"
PRES_ID = 15

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

# ─── HOOK: BrowserMockupSlide — items[].content (html) ──────────────────
update_slide("s3_hook_1", {
    "items": [
        {"type": "html", "content": "<div style='padding:40px;text-align:center;font-family:Inter,sans-serif;'><div style='font-size:48px;margin-bottom:16px;'>📱</div><div style='font-size:20px;font-weight:700;color:#2C2724;margin-bottom:8px;'>База клиентов</div><div style='font-size:14px;color:#8A8179;'>В личном WhatsApp у менеджера</div><div style='margin-top:24px;padding:12px 24px;background:#FEE2E2;border-radius:8px;color:#DC2626;font-weight:600;'>Уволился · Унёс · 0 контактов в CRM</div></div>", "start_time": 500}
    ]
})

# ─── МОСТ: AnimatedStatsSlide — +icon +color ───────────────────────────
update_slide("s3_most_1", {
    "stats": [
        {"value": 0, "label": "Контактов в CRM", "icon": "lucide:users", "color": "#EF4444", "start_time": 500},
        {"value": 100, "label": "Стоимость подписки €", "suffix": "€/год", "icon": "lucide:credit-card", "color": "#F59E0B", "start_time": 1500},
        {"value": 0, "label": "Порядка в процессах", "icon": "lucide:alert-triangle", "color": "#EF4444", "start_time": 2500},
    ]
})

# ─── PROOF 1: TechStackSlide — +desc ──────────────────────────────────
update_slide("s3_proof_1", {
    "technologies": [
        {"name": "HubSpot", "icon": "logos:hubspot", "desc": "CRM система", "color": "#FF7A59", "start_time": 300},
        {"name": "Интегратор", "icon": "lucide:settings", "desc": "Настройка подключения", "color": "#6366f1", "start_time": 800},
        {"name": "Обучение", "icon": "lucide:book-open", "desc": "Обучение сотрудников", "color": "#10B981", "start_time": 1300},
    ]
})

# ─── PROOF 2: ArchitectureDiagram — color: chart-N/color-N ──────────────
update_slide("s3_proof_2", {
    "nodes": [
        {"id": "site", "title": "Сайт", "subtitle": "Заявки", "icon": "globe", "color": "chart-1", "start_time": 300, "is_main": False, "to": ["crm"]},
        {"id": "crm", "title": "HubSpot", "subtitle": "CRM", "icon": "database", "color": "color-primary", "start_time": 800, "is_main": True, "to": ["mgr"]},
        {"id": "mgr", "title": "Менеджер", "subtitle": "Обработка", "icon": "user", "color": "chart-2", "start_time": 1400, "is_main": False},
    ],
    "show_data_flow": True,
})

# ─── PROOF 3: ComparisonTable — +id ────────────────────────────────────
update_slide("s3_proof_3", {
    "headers": ["", "Месяц 1", "Месяц 3"],
    "items": [
        {"id": "r1", "label": "Данные в CRM", "values": [True, False], "start_time": 300},
        {"id": "r2", "label": "Воронка актуальна", "values": [True, False], "start_time": 1000},
        {"id": "r3", "label": "Сделки закрыты", "values": [True, False], "start_time": 1700},
    ]
})

# ─── PROOF 4: ReceiptCard — name/price + footer_text ────────────────────
update_slide("s3_proof_4", {
    "title": "CORPORATE CARD",
    "subtitle": "Потерянная сделка",
    "currency": "€",
    "total_text": "30 000",
    "footer_text": "Клиент уже купил у конкурента",
    "total_start_time": 1500,
    "items": [
        {"name": "Сделка в CRM", "price": 30000, "start_time": 300},
        {"name": "Статус", "price": 0, "start_time": 800},
        {"name": "Реальность", "price": 0, "start_time": 1300},
    ]
})

# ─── PROOF 5: StatsBarChart — +base_color/peak_color ───────────────────
update_slide("s3_proof_5", {
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
    "title": "Активность занесения данных",
    "subtitle": "% от реальных сделок",
})

# ─── PROOF 6: PremiumChecklist — label+desc+icon+color ─────────────────
update_slide("s3_proof_6", {
    "items": [
        {"label": "Регламент работы с заявками", "desc": "Не прописан до сих пор", "icon": "heroicons:x-circle", "color": "brand-red", "start_time": 300},
        {"label": "Правила занесения данных", "desc": "Менеджеры игнорируют", "icon": "heroicons:x-circle", "color": "brand-red", "start_time": 1000},
        {"label": "Обязательность CRM", "desc": "Никто не контролирует", "icon": "heroicons:x-circle", "color": "brand-red", "start_time": 1700},
    ]
})

# ─── PAYOFF 1: InfographicCards — +id +trend ───────────────────────────
update_slide("s3_payoff_1", {
    "items": [
        {"id": 1, "label": "Без порядка", "value": "0", "trend": "Нет данных", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300},
        {"id": 2, "label": "С порядком", "value": "100", "trend": "Полная картина", "icon": "heroicons:check-circle", "color": "#10B981", "start_time": 1200},
        {"id": 3, "label": "Сначала бумага", "value": "!", "trend": "Инструмент потом", "icon": "heroicons:document-text", "color": "#F59E0B", "start_time": 2100},
    ]
})

# ─── PAYOFF 2: ProcessFunnel — label/count ──────────────────────────────
update_slide("s3_payoff_2", {
    "layout": "vertical",
    "steps": [
        {"label": "Регламент на бумаге", "count": 100, "icon": "heroicons:document-text", "start_time": 300, "color": "#10B981"},
        {"label": "Обучение команды", "count": 80, "icon": "heroicons:users", "start_time": 1200, "color": "#38BDF8"},
        {"label": "Только потом CRM", "count": 60, "icon": "heroicons:server-stack", "start_time": 2100, "color": "#F59E0B"},
    ]
})

# ─── OUTRO: OutroSlide ──────────────────────────────────────────────────
update_slide("s3_hookout_1", {
    "logo": "",
    "qr_code": "",
    "handle": "@it2b",
    "headline": "Скинь скриншот воронки продаж — покажу, где теряешь деньги",
})

print("\n✓ Шортс 3 исправлен!")
