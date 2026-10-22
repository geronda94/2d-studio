#!/usr/bin/env python3
"""Build visual slides for presentation 19 (shorts 01 reworked, 77.4s).
Bounds: HOOK 0-6280 | MOST 6480-15480 | PROOF 15680-55520 | PAYOFF 55720-67280 | CTA 67480-77240.
16 slides ~4.8s each. Run: docker compose exec backend python scripts/build_shorts19_slides.py
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
PRES_ID = 19
VARIANT = "tech"

SLIDES = [
 dict(sid="s19_01", comp="ChatMockupSlide", t=0, oi=1, title="Заявки идут — ответов нет",
      sub="никто не понимает почему", payload={
   "bot_name": "Клиент", "bot_subtitle": "ждёт ответ", "bot_avatar": "K",
   "messages": [
     {"role": "user", "text": "Заявку отправил вчера. Где ответ?", "start_time": 0},
     {"role": "assistant", "text": "Тишина. Ответы не уходят.", "start_time": 1500},
     {"role": "user", "text": "И никто внутри не понимает почему", "start_time": 3000},
   ]}),
 dict(sid="s19_02", comp="AnimatedStatsSlide", t=3200, oi=2, title="Реклама крутится впустую",
      sub="ответы не уходят", payload={
   "stats": [
     {"label": "Заявки идут", "value": 100, "suffix": "%", "color": "#38BDF8", "icon": "lucide:trending-up", "start_time": 0},
     {"label": "Ответов уходит", "value": 3, "suffix": "%", "color": "#EF4444", "icon": "lucide:trending-down", "start_time": 400},
   ]}),
 dict(sid="s19_03", comp="InfographicCards", t=6480, oi=3, title="Классический сбой",
      sub="каждый второй бизнес", payload={
   "items": [
     {"id": 1, "label": "Бизнесов", "value": "50%", "trend": "через это проходят", "color": "#F59E0B", "icon": "heroicons:exclamation-triangle", "start_time": 0},
     {"id": 2, "label": "Настройка", "value": "1 раз", "trend": "и забыли", "color": "#38BDF8", "icon": "heroicons:cog", "start_time": 500},
     {"id": 3, "label": "Контроль", "value": "0%", "trend": "никто не смотрит", "color": "#EF4444", "icon": "heroicons:eye-slash", "start_time": 1000},
   ]}),
 dict(sid="s19_04", comp="ArchitectureDiagram", t=10000, oi=4, title="Как всё работало",
      sub="три месяца идеально", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Сайт", "subtitle": "заявка", "icon": "globe", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "CRM", "subtitle": "маршрут", "icon": "db", "color": "chart-2", "start_time": 700, "is_main": True, "to": ["mid1"]},
     {"id": "mid1", "title": "WhatsApp", "subtitle": "ответ", "icon": "chat", "color": "chart-3", "start_time": 1400, "is_main": False, "to": ["out1"]},
     {"id": "out1", "title": "Таблица", "subtitle": "данные", "icon": "table", "color": "chart-4", "start_time": 2100, "is_main": False, "to": []},
   ]}),
 dict(sid="s19_05", comp="ProcessFunnel", t=15680, oi=5, title="Путь заявки",
      sub="визуальные блоки", payload={
   "layout": "horizontal",
   "steps": [
     {"label": "Сайт", "count": 100, "icon": "heroicons:globe-alt", "color": "#38BDF8", "start_time": 0},
     {"label": "CRM", "count": 95, "icon": "heroicons:circle-stack", "color": "#F59E0B", "start_time": 800},
     {"label": "WhatsApp", "count": 90, "icon": "heroicons:chat-bubble-left", "color": "#F59E0B", "start_time": 1600},
     {"label": "Ответ", "count": 12, "icon": "heroicons:check-circle", "color": "#EF4444", "start_time": 2400},
   ]}),
 dict(sid="s19_06", comp="MetricScales", t=20000, oi=6, title="Три месяца",
      sub="всё идеально", payload={
   "title": "Три месяца", "subtitle": "всё идеально",
   "metrics": [
     {"id": 1, "label": "Аптайм", "percentage": 99, "color": "linear-gradient(to right, #34D399, #2DD4BF)", "start_time": 0},
     {"id": 2, "label": "Ответы уходят", "percentage": 95, "color": "linear-gradient(to right, #38BDF8, #60A5FA)", "start_time": 500},
     {"id": 3, "label": "Контроль", "percentage": 10, "color": "linear-gradient(to right, #F59E0B, #FB923C)", "start_time": 1000},
   ]}),
 dict(sid="s19_07", comp="TerminalMockup", t=24500, oi=7, title="", sub="", payload={
   "commands": [
     {"cmd": "$ crm-api --check permissions", "output": "403: access rules changed\nWARNING: integration DOWN", "start_time": 300},
     {"cmd": "$ leads --last-week", "output": "received: 132\nanswered: 4\nstatus: FAILING", "start_time": 2000},
   ]}),
 dict(sid="s19_08", comp="ReceiptCard", t=29000, oi=8, title="", sub="", payload={
   "title": "СДЕЛКА", "subtitle": "€15 000 — итог недели молчания", "currency": "€",
   "total_text": "СОРВАНА", "footer_text": "КЛИЕНТУ ПРОСТО НИКТО НЕ ОТВЕТИЛ",
   "total_start_time": 2000,
   "items": [
     {"name": "Сделка на €15 000", "price": 15000, "start_time": 300},
     {"name": "Неделя молчания", "price": 7000, "start_time": 900},
     {"name": "Ответ клиенту", "price": 0.01, "start_time": 1500},
   ]}),
 dict(sid="s19_09", comp="BrowserMockup", t=33500, oi=9, title="", sub="", payload={
   "items": [{
     "id": "b1", "url": "automation.editor", "type": "html", "start_time": 0,
     "content": "<div class='flex flex-col gap-3 p-6'><p class='text-white/50 text-xs'>РЕДАКТОР ПОДРЯДЧИКА</p><div class='grid grid-cols-4 gap-2'><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 1</div><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 7</div><div class='bg-red-500/10 p-3 rounded-lg border border-red-500/30 text-white text-xs'>блок 13 ⚠</div><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 22</div><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 28</div><div class='bg-red-500/10 p-3 rounded-lg border border-red-500/30 text-white text-xs'>блок 31 ⚠</div><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 36</div><div class='bg-white/5 p-3 rounded-lg border border-white/10 text-white text-xs'>блок 40</div></div><p class='text-red-400 text-sm'>40 блоков. Стрелки в разные стороны. Подрядчик исчез.</p></div>",
   }]}),
 dict(sid="s19_10", comp="ChatMockupSlide", t=38000, oi=10, title="Менеджеры боятся",
      sub="нажать не ту кнопку", payload={
   "bot_name": "Менеджер", "bot_subtitle": "боится трогать", "bot_avatar": "M",
   "messages": [
     {"role": "user", "text": "Почини интеграцию, заявки висят", "start_time": 0},
     {"role": "assistant", "text": "Боюсь нажать не ту кнопку. Там 40 блоков...", "start_time": 1500},
   ]}),
 dict(sid="s19_11", comp="CodeExplain", t=42500, oi=11, title="Жёсткая линейная архитектура",
      sub="вместо 40 блоков", payload={
   "language": "python",
   "blocks": [
     {"code": "steps = ['site', 'crm', 'whatsapp']\nfor step in steps:\n    process(step, timeout=30)\n", "start_time": 0},
     {"code": "on_failure(step):\n    alert_owner(step)\n    fallback_to_manual()\n", "start_time": 1500},
   ]}),
 dict(sid="s19_12", comp="ArchitectureDiagram", t=47000, oi=12, title="После перестройки",
      sub="каждый шаг прозрачен", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Заявка", "subtitle": "сайт", "icon": "globe", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "Линия", "subtitle": "шаг за шагом", "icon": "cpu", "color": "chart-2", "start_time": 700, "is_main": True, "to": ["out1"]},
     {"id": "out1", "title": "Алерт", "subtitle": "при сбое", "icon": "bell", "color": "chart-3", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 dict(sid="s19_13", comp="PremiumChecklist", t=51000, oi=13, title="Регламент на сбой",
      sub="в каждом проекте", payload={
   "items": [
     {"label": "Жёсткие лимиты", "desc": "Таймаут на каждый шаг", "icon": "heroicons:clock", "color": "brand-blue", "start_time": 0},
     {"label": "Алерты владельцу", "desc": "Узнаёшь первым, не через неделю", "icon": "heroicons:bell-alert", "color": "brand-amber", "start_time": 800},
     {"label": "Ручной фолбэк", "desc": "Заявка не теряется никогда", "icon": "heroicons:shield-check", "color": "brand-green", "start_time": 1600},
   ]}),
 dict(sid="s19_14", comp="BentoGridGallery", t=55720, oi=14, title="Вывод",
      sub="бомба замедленного действия", payload={
   "items": [
     {"id": "g1", "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800", "title": "Без правил", "desc": "Автоматизация — бомба", "size": "2x1", "start_time": 0},
     {"id": "g2", "image": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=800", "title": "Регламент", "desc": "Сначала порядок", "size": "1x1", "start_time": 800},
     {"id": "g3", "image": "https://images.unsplash.com/photo-1526374965328-7f61d42e8f71?auto=format&fit=crop&q=80&w=800", "title": "Контроль", "desc": "Каждый шаг виден", "size": "1x1", "start_time": 1600},
   ]}),
 dict(sid="s19_15", comp="StatsBarChart", t=61000, oi=15, title="Результат",
      sub="потери заявок падают", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Результат", "subtitle": "потери заявок падают",
   "data": [
     {"label": "До", "value": 85, "start_time": 0},
     {"label": "После", "value": 12, "highlight": True, "start_time": 500},
   ]}),
 dict(sid="s19_16", comp="OutroSlide", t=67480, oi=16, title="", sub="", payload={
   "logo": "/media/f5ebf358c1e441739ebb498871c46855.png",
   "qr_code": "/media/b6e033ba29ce4fcd8c6ad48ba918721f.png",
   "handle": "@it00101",
   "headline": "Пришли схему автоматизации — найду точку отказа",
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
