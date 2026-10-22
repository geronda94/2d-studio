#!/usr/bin/env python3
"""Build visual slides for presentation 16 (shorts 02 v2, 99.4s, 14 audio chunks).
Validates every payload before creating. Run: docker compose exec backend python scripts/build_shorts16_slides.py
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
PRES_ID = 16
VARIANT = "tech"

SLIDES = [
 # 1. HOOK 0-8179 — agent promises discount
 dict(sid="s16_01", comp="ChatMockupSlide", t=0, oi=1, title="ИИ-агент врёт клиентам",
      sub="реальный диалог", payload={
   "bot_name": "AI-агент", "bot_subtitle": "поддержка 24/7", "bot_avatar": "AI",
   "messages": [
     {"role": "user", "text": "А если возьму партию на полгода?", "start_time": 0},
     {"role": "assistant", "text": "Сделаем персональную скидку 30%!", "start_time": 1500},
     {"role": "user", "text": "Скриню. Жду свои условия.", "start_time": 3000},
   ]}),
 # 2. HOOK cont — fake discount numbers
 dict(sid="s16_02", comp="AnimatedStatsSlide", t=4100, oi=2, title="Скидка из воздуха",
      sub="которой не существует", payload={
   "stats": [
     {"label": "Скидка от агента", "value": 30, "suffix": "%", "color": "#EF4444", "icon": "lucide:trending-down", "start_time": 0},
     {"label": "Сделка под угрозой", "value": 15, "suffix": "k €", "color": "#F59E0B", "icon": "lucide:alert-triangle", "start_time": 400},
     {"label": "Скидка реальная", "value": 1, "suffix": "%", "color": "#10B981", "icon": "lucide:check", "start_time": 800},
   ]}),
 # 3. MOST 8379 — money burning receipt
 dict(sid="s16_03", comp="ReceiptCard", t=8379, oi=3, title="",
      sub="", payload={
   "title": "ТВОЙ БЮДЖЕТ", "subtitle": "ИИ-агент раздаёт", "currency": "€",
   "total_text": "ПОТЕРЯНО", "footer_text": "НЕЙРОСЕТЬ РАЗДАЁТ ТВОИ ДЕНЬГИ",
   "total_start_time": 2000,
   "items": [
     {"name": "Выдуманная скидка", "price": 4500, "start_time": 300},
     {"name": "Сорванная сделка", "price": 15000, "start_time": 900},
     {"name": "Репутация", "price": 9999, "start_time": 1500},
   ]}),
 # 4. MOST cont — money stats cards
 dict(sid="s16_04", comp="InfographicCards", t=12200, oi=4, title="Цена галлюцинации",
      sub="в цифрах", payload={
   "items": [
     {"id": 1, "label": "Скидка", "value": "30%", "trend": "выдумана", "color": "#EF4444", "icon": "heroicons:exclamation-triangle", "start_time": 0},
     {"id": 2, "label": "Сделка", "value": "€15k", "trend": "висит", "color": "#F59E0B", "icon": "heroicons:pause", "start_time": 500},
     {"id": 3, "label": "Доверие", "value": "-100%", "trend": "потеряно", "color": "#38BDF8", "icon": "heroicons:chat-bubble-bottom-center-text", "start_time": 1000},
   ]}),
 # 5. PROOF narrative 16257 — ideal architecture
 dict(sid="s16_05", comp="ArchitectureDiagram", t=16257, oi=5, title="Как всё работало",
      sub="первый месяц — идеально", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Клиент", "subtitle": "вопрос", "icon": "user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "ИИ-агент", "subtitle": "база знаний", "icon": "cpu", "color": "chart-2", "start_time": 700, "is_main": True, "to": ["out1"]},
     {"id": "out1", "title": "Менеджер", "subtitle": "разгружен", "icon": "check", "color": "chart-3", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 # 6. PROOF narrative cont — funnel
 dict(sid="s16_06", comp="ProcessFunnel", t=20500, oi=6, title="Поддержка разгружена",
      sub="наполовину", payload={
   "layout": "horizontal",
   "steps": [
     {"label": "Вопросы", "count": 100, "icon": "heroicons:chat-bubble-left", "color": "#38BDF8", "start_time": 0},
     {"label": "Агент", "count": 50, "icon": "heroicons:cpu-chip", "color": "#F59E0B", "start_time": 800},
     {"label": "Закрыто", "count": 48, "icon": "heroicons:check-circle", "color": "#10B981", "start_time": 1600},
   ]}),
 # 7. PROOF narrative cont — scales
 dict(sid="s16_07", comp="MetricScales", t=24800, oi=7, title="Первый месяц",
      sub="всё выглядит отлично", payload={
   "title": "Первый месяц", "subtitle": "всё выглядит отлично",
   "metrics": [
     {"id": 1, "label": "Ответы агента", "percentage": 95, "color": "linear-gradient(to right, #34D399, #2DD4BF)", "start_time": 0},
     {"id": 2, "label": "Довольных клиентов", "percentage": 90, "color": "linear-gradient(to right, #38BDF8, #60A5FA)", "start_time": 500},
     {"id": 3, "label": "Нагрузка на поддержку", "percentage": 45, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 1000},
   ]}),
 # 8. PUNCH 28993 «не замолчал» — chat
 dict(sid="s16_08", comp="ChatMockupSlide", t=28993, oi=8, title="Агент не замолчал",
      sub="а должен был", payload={
   "bot_name": "AI-агент", "bot_subtitle": "должен молчать", "bot_avatar": "AI",
   "messages": [
     {"role": "user", "text": "Какие допуски по DIN?", "start_time": 0},
     {"role": "assistant", "text": "Конечно! Три стандарта...", "start_time": 1200},
   ]}),
 # 9. PUNCH 31943 «он угадал» — confidence
 dict(sid="s16_09", comp="AnimatedStatsSlide", t=31943, oi=9, title="Он угадал",
      sub="а не знал", payload={
   "stats": [
     {"label": "Уверенность", "value": 60, "suffix": "%", "color": "#EF4444", "icon": "lucide:help-circle", "start_time": 0},
     {"label": "Нужно для ответа", "value": 95, "suffix": "%", "color": "#10B981", "icon": "lucide:shield-check", "start_time": 400},
   ]}),
 # 10. PUNCH 34572 «скидка 30%» — promised vs real
 dict(sid="s16_10", comp="ComparisonTable", t=34572, oi=10, title="Обещано и реальность",
      sub="скидка 30%", payload={
   "headers": ["", "Агент пообещал", "На самом деле"],
   "items": [
     {"id": "r1", "label": "Скидка 30%", "values": [True, False], "start_time": 0},
     {"id": "r2", "label": "Согласовано", "values": [True, False], "start_time": 700},
     {"id": "r3", "label": "Существует", "values": [True, False], "start_time": 1400},
   ]}),
 # 11. cont — numbers
 dict(sid="s16_11", comp="StatsBarChart", t=38500, oi=11, title="Сделка встаёт",
      sub="€15 000", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Сделка встаёт", "subtitle": "€15 000 намертво",
   "data": [
     {"label": "Пн", "value": 90, "start_time": 0},
     {"label": "Вт", "value": 70, "start_time": 300},
     {"label": "Ср", "value": 30, "start_time": 600},
     {"label": "Чт", "value": 5, "highlight": True, "start_time": 900},
   ]}),
 # 12. PUNCH 42557 «сделка встала» — receipt
 dict(sid="s16_12", comp="ReceiptCard", t=42557, oi=12, title="", sub="", payload={
   "title": "СДЕЛКА", "subtitle": "€15 000 — статус", "currency": "€",
   "total_text": "ЗАВИСЛО", "footer_text": "КЛИЕНТ ЖДЁТ НЕСУЩЕСТВУЮЩИЕ УСЛОВИЯ",
   "total_start_time": 2000,
   "items": [
     {"name": "Партия на полгода", "price": 15000, "start_time": 300},
     {"name": "Выдуманная скидка", "price": 4500, "start_time": 900},
     {"name": "Ответ менеджера", "price": 0.01, "start_time": 1500},
   ]}),
 # 13. cont — browser chat screenshot
 dict(sid="s16_13", comp="BrowserMockup", t=46500, oi=13, title="", sub="", payload={
   "items": [{
     "id": "b1", "url": "chat.company.io", "type": "html", "start_time": 0,
     "content": "<div class='flex flex-col gap-3 p-6'><div class='bg-white/5 p-4 rounded-xl border border-white/10'><p class='text-white/50 text-xs'>КЛИЕНТ</p><p class='text-white text-lg'>Какие допуски по DIN?</p></div><div class='bg-red-500/10 p-4 rounded-xl border border-red-500/30'><p class='text-red-400 text-xs'>АГЕНТ</p><p class='text-white text-lg'>Три стандарта: DIN-UNDER, DIN-OVER...</p></div><p class='text-white/40 text-sm'>Клиент скринит переписку</p></div>",
   }]}),
 # 14. PUNCH 51079 «клиент скринит» — terminal log
 dict(sid="s16_14", comp="TerminalMockup", t=51079, oi=14, title="", sub="", payload={
   "commands": [
     {"cmd": "$ agent --reply DIN-99", "output": "confidence: 0.61 < 0.95\nWARNING: guessing — no KB hit", "start_time": 300},
     {"cmd": "$ client --screenshot", "output": "saved: proof.png\ntrust: DESTROYED", "start_time": 2000},
   ]}),
 # 15. PUNCH 54600 «ждёт условия» — waiting chat
 dict(sid="s16_15", comp="ChatMockupSlide", t=54600, oi=15, title="Клиент ждёт",
      sub="свои условия", payload={
   "bot_name": "AI-агент", "bot_subtitle": "молчит", "bot_avatar": "AI",
   "messages": [
     {"role": "user", "text": "Ну? Где мои 30%?", "start_time": 0},
     {"role": "user", "text": "Вы там вообще работаете?", "start_time": 1800},
   ]}),
 # 16. PUNCH 57871 «самое страшное» — broken architecture
 dict(sid="s16_16", comp="ArchitectureDiagram", t=57871, oi=16, title="Архитектурная ошибка",
      sub="свободный диалог", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Клиент", "subtitle": "сложный вопрос", "icon": "user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "LLM угадывает", "subtitle": "без коридора", "icon": "cpu", "color": "chart-4", "start_time": 700, "is_main": True, "to": ["out1"]},
     {"id": "out1", "title": "Провал", "subtitle": "€15 000", "icon": "alert", "color": "chart-4", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 # 17. cont — guardrail code
 dict(sid="s16_17", comp="CodeExplain", t=62000, oi=17, title="Жёсткий коридор",
      sub="вместо свободного диалога", payload={
   "language": "python",
   "blocks": [
     {"code": "if confidence < 0.95:\n    escalate_to_engineer()\n    return  # молчи, зови человека\n", "start_time": 0},
     {"code": "if topic not in ALLOWED:\n    say(\"Передал инженеру, подключится за 15 минут\")\n", "start_time": 1500},
   ]}),
 # 18. cont — 3 boundaries checklist
 dict(sid="s16_18", comp="PremiumChecklist", t=66200, oi=18, title="Три вопроса",
      sub="до внедрения", payload={
   "items": [
     {"label": "Где граница?", "desc": "Квалификация — да, закрытие — нет", "icon": "heroicons:fence", "color": "brand-blue", "start_time": 0},
     {"label": "Не знает — что делает?", "desc": "Молчит и зовёт человека", "icon": "heroicons:bell-alert", "color": "brand-amber", "start_time": 800},
     {"label": "Какой регламент?", "desc": "Сначала порядок, потом инструмент", "icon": "heroicons:clipboard-document-check", "color": "brand-green", "start_time": 1600},
   ]}),
 # 19. PUNCH cont 70893 — ecosystem fixed
 dict(sid="s16_19", comp="EcosystemSlide", t=70893, oi=19, title="Правильная схема",
      sub="агент в коридоре", payload={
   "center": {"label": "Агент", "logo": "cpu"},
   "nodes": [
     {"label": "Склад API", "icon": "lucide:database"},
     {"label": "Менеджер", "icon": "lucide:user-check"},
     {"label": "Инженер", "icon": "lucide:wrench"},
     {"label": "CRM", "icon": "logos:hubspot"},
   ]}),
 # 20. cont — fixed funnel
 dict(sid="s16_20", comp="ProcessFunnel", t=75200, oi=20, title="Ночь держит агент",
      sub="день разгружен", payload={
   "layout": "horizontal",
   "steps": [
     {"label": "Ночной лид", "count": 30, "icon": "heroicons:moon", "color": "#38BDF8", "start_time": 0},
     {"label": "Агент", "count": 28, "icon": "heroicons:cpu-chip", "color": "#F59E0B", "start_time": 800},
     {"label": "Менеджер", "count": 25, "icon": "heroicons:user", "color": "#10B981", "start_time": 1600},
   ]}),
 # 21. 79628 «зови менеджера» — escalate terminal
 dict(sid="s16_21", comp="TerminalMockup", t=79628, oi=21, title="", sub="", payload={
   "commands": [
     {"cmd": "$ agent --confidence 0.61", "output": "below threshold 0.95\nescalating to human...", "start_time": 300},
     {"cmd": "$ handoff --to engineer", "output": "engineer joins in 15 min\ndeal SAVED", "start_time": 2200},
   ]}),
 # 22. PAYOFF 83364 — thesis tiles
 dict(sid="s16_22", comp="BentoGridGallery", t=83364, oi=22, title="Вывод",
      sub="фантазёр с доступом к кошельку", payload={
   "items": [
     {"id": "g1", "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800", "title": "Границы", "desc": "Без них агент сливает", "size": "2x1", "start_time": 0},
     {"id": "g2", "image": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=800", "title": "Коридор", "desc": "Шаг в сторону — человек", "size": "1x1", "start_time": 800},
     {"id": "g3", "image": "https://images.unsplash.com/photo-1526374965328-7f61d42e8f71?auto=format&fit=crop&q=80&w=800", "title": "Порядок", "desc": "Сначала процесс", "size": "1x1", "start_time": 1600},
   ]}),
 # 23. PAYOFF cont — result bars
 dict(sid="s16_23", comp="StatsBarChart", t=88000, oi=23, title="Результат",
      sub="ночная конверсия +40%", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Результат", "subtitle": "ночная конверсия +40%",
   "data": [
     {"label": "До", "value": 40, "start_time": 0},
     {"label": "После", "value": 85, "highlight": True, "start_time": 500},
   ]}),
 # 24. CTA 93278 — outro
 dict(sid="s16_24", comp="OutroSlide", t=93278, oi=24, title="", sub="", payload={
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
