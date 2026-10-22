#!/usr/bin/env python3
"""Build visual slides for presentation 20 (shorts 02 reworked, 72.0s).
Bounds: HOOK 0-3960 | MOST 4160-12360 | PROOF 12560-54560 | PAYOFF 54760-63480 | CTA 63680-71840.
16 slides ~4.5s each. Run: docker compose exec backend python scripts/build_shorts20_slides.py
"""
import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8000"
PRES_ID = 20
VARIANT = "tech"

SLIDES = [
 dict(sid="s20_01", comp="ChatMockupSlide", t=0, oi=1, title="ИИ пообещал скидку",
      sub="которой нет", payload={
   "bot_name": "AI-агент", "bot_subtitle": "поддержка 24/7", "bot_avatar": "AI",
   "messages": [
     {"role": "user", "text": "А если возьму партию на полгода?", "start_time": 0},
     {"role": "assistant", "text": "Сделаем персональную скидку 30%!", "start_time": 1500},
     {"role": "user", "text": "Скриню. Жду свои условия.", "start_time": 3000},
   ]}),
 dict(sid="s20_02", comp="ReceiptCard", t=4160, oi=2, title="", sub="", payload={
   "title": "ТВОЙ БЮДЖЕТ", "subtitle": "ИИ раздаёт твои деньги", "currency": "€",
   "total_text": "ПОТЕРЯНО", "footer_text": "УЗНАЁШЬ ОБ ЭТОМ ПОСЛЕДНИМ",
   "total_start_time": 2000,
   "items": [
     {"name": "Выдуманная скидка", "price": 4500, "start_time": 300},
     {"name": "Сорванная сделка", "price": 15000, "start_time": 900},
     {"name": "Доверие клиента", "price": 9999, "start_time": 1500},
   ]}),
 dict(sid="s20_03", comp="InfographicCards", t=8000, oi=3, title="Цена галлюцинации",
      sub="в цифрах", payload={
   "items": [
     {"id": 1, "label": "Скидка", "value": "30%", "trend": "выдумана", "color": "#EF4444", "icon": "heroicons:exclamation-triangle", "start_time": 0},
     {"id": 2, "label": "Сделка", "value": "€15k", "trend": "встала", "color": "#F59E0B", "icon": "heroicons:pause", "start_time": 500},
     {"id": 3, "label": "Узнаёшь", "value": "последним", "trend": "неделя спустя", "color": "#38BDF8", "icon": "heroicons:clock", "start_time": 1000},
   ]}),
 dict(sid="s20_04", comp="ArchitectureDiagram", t=12560, oi=4, title="Первый месяц — идеально",
      sub="бот разгрузил поддержку", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Клиент", "subtitle": "вопрос", "icon": "lucide:user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "ИИ-агент", "subtitle": "база знаний", "icon": "cpu", "color": "chart-2", "start_time": 700, "is_main": True, "to": ["out1"]},
     {"id": "out1", "title": "Ответ", "subtitle": "мгновенно", "icon": "lucide:check", "color": "chart-3", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 dict(sid="s20_05", comp="ProcessFunnel", t=16500, oi=5, title="Поддержка разгружена",
      sub="наполовину", payload={
   "layout": "horizontal",
   "steps": [
     {"label": "Вопросы", "count": 100, "icon": "heroicons:chat-bubble-left", "color": "#38BDF8", "start_time": 0},
     {"label": "Бот", "count": 50, "icon": "heroicons:cpu-chip", "color": "#F59E0B", "start_time": 800},
     {"label": "Закрыто", "count": 48, "icon": "heroicons:check-circle", "color": "#10B981", "start_time": 1600},
   ]}),
 dict(sid="s20_06", comp="MetricScales", t=20500, oi=6, title="Ты выдыхаешь",
      sub="всё под контролем", payload={
   "title": "Ты выдыхаешь", "subtitle": "всё под контролем",
   "metrics": [
     {"id": 1, "label": "Ответы бота", "percentage": 98, "color": "linear-gradient(to right, #34D399, #2DD4BF)", "start_time": 0},
     {"id": 2, "label": "Клиенты довольны", "percentage": 92, "color": "linear-gradient(to right, #38BDF8, #60A5FA)", "start_time": 500},
     {"id": 3, "label": "Контроль галлюцинаций", "percentage": 15, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 1000},
   ]}),
 dict(sid="s20_07", comp="ChatMockupSlide", t=25000, oi=7, title="Оптовик спрашивает",
      sub="партия на полгода", payload={
   "bot_name": "Оптовик", "bot_subtitle": "крупная партия", "bot_avatar": "O",
   "messages": [
     {"role": "user", "text": "А какие условия на партию на полгода?", "start_time": 0},
     {"role": "assistant", "text": "Должен замолчать и позвать менеджера", "start_time": 1500},
   ]}),
 dict(sid="s20_08", comp="AnimatedStatsSlide", t=29500, oi=8, title="Бот должен был замолчать",
      sub="а он угадал", payload={
   "stats": [
     {"label": "Нужно для ответа", "value": 95, "suffix": "%", "color": "#10B981", "icon": "lucide:shield-check", "start_time": 0},
     {"label": "Уверенность бота", "value": 60, "suffix": "%", "color": "#EF4444", "icon": "lucide:help-circle", "start_time": 400},
   ]}),
 dict(sid="s20_09", comp="ComparisonTable", t=33500, oi=9, title="Обещано и реальность",
      sub="скидка 30%", payload={
   "headers": ["", "Бот пообещал", "На самом деле"],
   "items": [
     {"id": "r1", "label": "Скидка 30%", "values": [True, False], "start_time": 0},
     {"id": "r2", "label": "Согласовано с тобой", "values": [True, False], "start_time": 700},
     {"id": "r3", "label": "Существует", "values": [True, False], "start_time": 1400},
   ]}),
 dict(sid="s20_10", comp="StatsBarChart", t=37500, oi=10, title="Сделка встала",
      sub="€15 000 намертво", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Сделка встала", "subtitle": "€15 000 намертво",
   "data": [
     {"label": "Пн", "value": 90, "start_time": 0},
     {"label": "Вт", "value": 60, "start_time": 300},
     {"label": "Ср", "value": 20, "start_time": 600},
     {"label": "Чт", "value": 5, "highlight": True, "start_time": 900},
   ]}),
 dict(sid="s20_11", comp="TerminalMockup", t=41500, oi=11, title="", sub="", payload={
   "commands": [
     {"cmd": "$ agent --reply 'скидка 30%'", "output": "confidence: 0.61 < 0.95\nWARNING: guessing — no KB hit", "start_time": 300},
     {"cmd": "$ client --screenshot", "output": "saved: proof.png\ntrust: DESTROYED", "start_time": 2000},
   ]}),
 dict(sid="s20_12", comp="ArchitectureDiagram", t=45500, oi=12, title="Архитектурная ошибка",
      sub="свободный диалог", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Запрос", "subtitle": "вне базы", "icon": "lucide:message-circle", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "LLM угадывает", "subtitle": "без коридора", "icon": "cpu", "color": "chart-4", "start_time": 700, "is_main": True, "to": ["out1"]},
     {"id": "out1", "title": "Провал", "subtitle": "€15 000", "icon": "lucide:alert-triangle", "color": "chart-4", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 dict(sid="s20_13", comp="CodeExplain", t=50000, oi=13, title="Жёсткий коридор",
      sub="вместо свободного диалога", payload={
   "language": "python",
   "blocks": [
     {"code": "if confidence < 0.95:\n    escalate_to_human()\n    return  # молчи, зови человека\n", "start_time": 0},
     {"code": "if topic not in KNOWLEDGE_BASE:\n    say(\"Передал менеджеру, подключится за 5 минут\")\n", "start_time": 1500},
   ]}),
 dict(sid="s20_14", comp="PremiumChecklist", t=54760, oi=14, title="Без границ — фантазёр",
      sub="с доступом к кошельку", payload={
   "items": [
     {"label": "Чёткие границы", "desc": "Где бот отвечает, где молчит", "icon": "heroicons:fence", "color": "brand-blue", "start_time": 0},
     {"label": "Шаг в сторону — стоп", "desc": "Вне базы → сразу к человеку", "icon": "heroicons:bell-alert", "color": "brand-amber", "start_time": 800},
     {"label": "Сначала регламент", "desc": "Потом инструмент", "icon": "heroicons:clipboard-document-check", "color": "brand-green", "start_time": 1600},
   ]}),
 dict(sid="s20_15", comp="BentoGridGallery", t=59000, oi=15, title="Фантазёр с кошельком",
      sub="или управляемый агент", payload={
   "items": [
     {"id": "g1", "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800", "title": "Без границ", "desc": "Сливает сделки", "size": "2x1", "start_time": 0},
     {"id": "g2", "image": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=800", "title": "Коридор", "desc": "Шаг в сторону — стоп", "size": "1x1", "start_time": 800},
     {"id": "g3", "image": "https://images.unsplash.com/photo-1526374965328-7f61d42e8f71?auto=format&fit=crop&q=80&w=800", "title": "Контроль", "desc": "Деньги целы", "size": "1x1", "start_time": 1600},
   ]}),
 dict(sid="s20_16", comp="OutroSlide", t=63680, oi=16, title="", sub="", payload={
   "logo": "/media/f5ebf358c1e441739ebb498871c46855.png",
   "qr_code": "/media/b6e033ba29ce4fcd8c6ad48ba918721f.png",
   "handle": "@it00101",
   "headline": "Скинь инструкцию бота — покажу где сольёт сделку",
 }),
]


def main():
    ok, fail = 0, []
    for s in SLIDES:
        v = requests.post(f"{BASE}/components/{s['comp']}/validate", json={"payload": s["payload"]})
        res = v.json()
        if not res.get("valid"):
            print(f"INVALID {s['sid']} {s['comp']}: {res.get('errors')}")
            fail.append(s["sid"])
            continue
        body = {"slide_id": s["sid"], "component": s["comp"], "start_time": s["t"],
                "order_index": s["oi"], "title": s.get("title", ""), "subtitle": s.get("sub", ""),
                "layout": "col", "data": {"payload": s["payload"]}}
        r = requests.post(f"{BASE}/presentations/{PRES_ID}/slides", json=body)
        if r.status_code in (200, 201):
            ok += 1
            print(f"OK {s['sid']} @ {s['t']}ms")
        else:
            print(f"CREATE FAIL {s['sid']}: {r.status_code} {r.text[:300]}")
            fail.append(s["sid"])
    print(f"\nDone: {ok}/{len(SLIDES)} created. Failed: {fail}")


if __name__ == "__main__":
    main()
