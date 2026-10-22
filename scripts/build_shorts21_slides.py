#!/usr/bin/env python3
"""Build visual slides for presentation 21 (shorts 03 reworked, 66.2s).
Bounds: HOOK 0-4960 | MOST 5160-13720 | PROOF 13920-50600 | PAYOFF 50800-59200 | CTA 59400-66040.
16 slides ~4.1s each. Run: docker compose exec backend python scripts/build_shorts21_slides.py
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
PRES_ID = 21
VARIANT = "tech"

SLIDES = [
 dict(sid="s21_01", comp="ChatMockupSlide", t=0, oi=1, title="Менеджер уволился",
      sub="забрал базу с собой", payload={
   "bot_name": "Менеджер", "bot_subtitle": "ушёл с базой", "bot_avatar": "M",
   "messages": [
     {"role": "user", "text": "У меня все клиенты в личном WhatsApp", "start_time": 0},
     {"role": "assistant", "text": "И он унёс их с собой", "start_time": 1800},
   ]}),
 dict(sid="s21_02", comp="ReceiptCard", t=5160, oi=2, title="", sub="", payload={
   "title": "УБЫТКИ", "subtitle": "это дороже CRM", "currency": "€",
   "total_text": "ПОТЕРЯНО", "footer_text": "CRM НЕ СПАСЁТ ОТ ХАОСА",
   "total_start_time": 2000,
   "items": [
     {"name": "База клиентов", "price": 30000, "start_time": 300},
     {"name": "Доверие", "price": 15000, "start_time": 900},
     {"name": "Год подписки Hubspot", "price": 6000, "start_time": 1500},
   ]}),
 dict(sid="s21_03", comp="InfographicCards", t=9500, oi=3, title="Hubspot за €500/мес",
      sub="а воронка пуста", payload={
   "items": [
     {"id": 1, "label": "Подписка", "value": "€6k/год", "trend": "купили", "color": "#F59E0B", "icon": "heroicons:credit-card", "start_time": 0},
     {"id": 2, "label": "Интегратор", "value": "нанят", "trend": "ждём", "color": "#38BDF8", "icon": "heroicons:user-group", "start_time": 500},
     {"id": 3, "label": "Воронка", "value": "пусто", "trend": "3 месяца спустя", "color": "#EF4444", "icon": "heroicons:exclamation-triangle", "start_time": 1000},
   ]}),
 dict(sid="s21_04", comp="ArchitectureDiagram", t=13920, oi=4, title="Картина клиента",
      sub="годовая подписка + интегратор", payload={
   "variant": VARIANT, "show_data_flow": True,
   "nodes": [
     {"id": "in1", "title": "Hubspot", "subtitle": "CRM", "icon": "lucide:database", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core1"]},
     {"id": "core1", "title": "Интегратор", "subtitle": "настроен", "icon": "cpu", "color": "chart-2", "start_time": 700, "is_main": True, "to": ["out1", "out2"]},
     {"id": "out1", "title": "Воронка", "subtitle": "пуста", "icon": "lucide:inbox", "color": "chart-4", "start_time": 1400, "is_main": False, "to": []},
     {"id": "out2", "title": "Переписка", "subtitle": "в WhatsApp", "icon": "lucide:message-circle", "color": "chart-4", "start_time": 1400, "is_main": False, "to": []},
   ]}),
 dict(sid="s21_05", comp="MetricScales", t=18500, oi=5, title="Три месяца спустя",
      sub="открываем воронку", payload={
   "title": "Три месяца спустя", "subtitle": "открываем воронку",
   "metrics": [
     {"id": 1, "label": "Данные в CRM", "percentage": 25, "color": "linear-gradient(to right, #EF4444, #F87171)", "start_time": 0},
     {"id": 2, "label": "Переписка в CRM", "percentage": 8, "color": "linear-gradient(to right, #EF4444, #FB923C)", "start_time": 500},
     {"id": 3, "label": "Данные в WhatsApp", "percentage": 92, "color": "linear-gradient(to right, #38BDF8, #60A5FA)", "start_time": 1000},
   ]}),
 dict(sid="s21_06", comp="StatsBarChart", t=23000, oi=6, title="Сделка на €30 000",
      sub="висит «в работе»", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Сделка на €30 000", "subtitle": "клиент уже купил у конкурента",
   "data": [
     {"label": "Вт", "value": 80, "start_time": 0},
     {"label": "Ср", "value": 75, "start_time": 300},
     {"label": "Чт", "value": 10, "start_time": 600},
     {"label": "Пт", "value": 3, "highlight": True, "start_time": 900},
   ]}),
 dict(sid="s21_07", comp="ChatMockupSlide", t=27000, oi=7, title="Пятница, вечер",
      sub="данные для галочки", payload={
   "bot_name": "Менеджер", "bot_subtitle": "заносит для галочки", "bot_avatar": "M",
   "messages": [
     {"role": "assistant", "text": "Воронка обновлена. Данные внесены.", "start_time": 0},
     {"role": "user", "text": "А реальная переписка? В WhatsApp на личном телефоне", "start_time": 1800},
   ]}),
 dict(sid="s21_08", comp="BrowserMockup", t=32000, oi=8, title="", sub="", payload={
   "items": [{
     "id": "b1", "url": "hubspot.com/vorolk", "type": "html", "start_time": 0,
     "content": "<div class='flex flex-col gap-4 p-6'><p class='text-white/50 text-xs'>HUBSPOT ВОРОНКА</p><div class='grid grid-cols-3 gap-3'><div class='bg-white/5 p-4 rounded-xl border border-white/10 text-center'><p class='text-white/50 text-xs'>Новые</p><p class='text-2xl font-bold text-white'>12</p></div><div class='bg-white/5 p-4 rounded-xl border border-white/10 text-center'><p class='text-white/50 text-xs'>В работе</p><p class='text-2xl font-bold text-[#F59E0B]'>34</p></div><div class='bg-white/5 p-4 rounded-xl border border-red-500/30 text-center'><p class='text-white/50 text-xs'>Закрытые</p><p class='text-2xl font-bold text-[#EF4444]'>0</p></div></div><p class='text-red-400 text-sm'>Клиент купил у конкурента. Воронка пуста.</p></div>",
   }]}),
 dict(sid="s21_09", comp="TerminalMockup", t=36500, oi=9, title="", sub="", payload={
   "commands": [
     {"cmd": "$ crm --funnel --status 'в работе'", "output": "deals: 34\nclosed: 0\nbut: 12 already bought elsewhere", "start_time": 300},
     {"cmd": "$ whatsapp --personal-phones", "output": "ALL conversations there\nCRM: empty", "start_time": 2000},
   ]}),
 dict(sid="s21_10", comp="ChatMockupSlide", t=41000, oi=10, title="Софт натянули",
      sub="на хаос", payload={
   "bot_name": "Менеджер", "bot_subtitle": "боится трогать CRM", "bot_avatar": "M",
   "messages": [
     {"role": "user", "text": "Почему не заносишь в CRM?", "start_time": 0},
     {"role": "assistant", "text": "Боюсь сломать. А клиент ждать не будет.", "start_time": 1800},
   ]}),
 dict(sid="s21_11", comp="CodeExplain", t=45500, oi=11, title="Жёсткий регламент",
      sub="переписка только через API", payload={
   "language": "python",
   "blocks": [
     {"code": "def send_message(client_id, text, channel):\n    if channel != 'corporate_api':\n        raise Error('Personal channels banned')\n", "start_time": 0},
     {"code": "def sync_to_crm(client_id):\n    data = fetch_whatsapp_via_api(client_id)\n    crm.update(client_id, data)  # автоматически\n", "start_time": 1500},
   ]}),
 dict(sid="s21_12", comp="PremiumChecklist", t=50800, oi=12, title="CRM — зеркало",
      sub="автоматизация хаоса = автоматизированный хаос", payload={
   "items": [
     {"label": "Данные через API", "desc": "Только корпоративные каналы", "icon": "heroicons:globe-alt", "color": "brand-blue", "start_time": 0},
     {"label": "Авто-синхронизация", "desc": "WhatsApp → CRM автоматически", "icon": "heroicons:arrow-path", "color": "brand-green", "start_time": 800},
     {"label": "Контроль", "desc": "Воронка отражает реальность", "icon": "heroicons:eye", "color": "brand-amber", "start_time": 1600},
   ]}),
 dict(sid="s21_13", comp="StatsBarChart", t=55000, oi=13, title="Результат",
      sub="данные в CRM растут", payload={
   "base_color": "var(--brand-blue)", "peak_color": "var(--brand-accent)",
   "title": "Результат", "subtitle": "данные в CRM растут",
   "data": [
     {"label": "До", "value": 25, "start_time": 0},
     {"label": "После", "value": 94, "highlight": True, "start_time": 500},
   ]}),
 dict(sid="s21_14", comp="OutroSlide", t=59400, oi=14, title="", sub="", payload={
   "logo": "/media/f5ebf358c1e441739ebb498871c46855.png",
   "qr_code": "/media/b6e033ba29ce4fcd8c6ad48ba918721f.png",
   "handle": "@it00101",
   "headline": "Скинь скриншот воронки — покажу где теряете деньги",
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
