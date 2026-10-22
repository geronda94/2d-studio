#!/usr/bin/env python3
"""Слайды для широкоформатного Длинное_03 (presentation 68), 7 блоков.

Запуск с хоста: python3 scripts/build_long03_slides.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
PRES_ID = 68
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

BAD_SITE_HTML = '''<div style="display:flex;flex-direction:column;width:100%;min-height:100cqh;box-sizing:border-box;background:#0e1726;color:#f8fafc;font-family:Inter,system-ui,sans-serif;overflow:hidden;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:10px;padding:12px 16px;flex-shrink:0;">
    <span style="font-weight:800;letter-spacing:2px;font-size:13px;white-space:nowrap;flex-shrink:0;">ОЗЕРО <span style="color:#38bdf8;">РЕЗОРТ</span></span>
    <div style="display:flex;gap:12px;font-size:11px;color:rgba(255,255,255,0.6);white-space:nowrap;min-width:0;overflow:hidden;"><span>О нас</span><span>История</span><span>Миссия</span></div>
    <div style="font-size:18px;color:rgba(255,255,255,0.8);flex-shrink:0;">&#8801;</div>
  </div>
  <div style="position:relative;flex:1;min-height:0;display:flex;align-items:center;justify-content:center;text-align:center;background:url('https://images.unsplash.com/photo-1439066615861-d1af74d74000?auto=format&fit=crop&q=80&w=1600') center/cover no-repeat;">
    <div style="position:absolute;inset:0;background:rgba(11,19,34,0.6);"></div>
    <div style="position:relative;padding:24px;">
      <div style="font-size:34px;font-weight:800;line-height:1.1;">Единение с природой</div>
      <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:10px;max-width:520px;">Сорок домиков у озера. История основателей и наша миссия — вдохновлять.</div>
    </div>
  </div>
  <div style="padding:14px 18px;font-size:11px;color:rgba(255,255,255,0.4);border-top:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;gap:12px;">
    <span>Оставить заявку: форма — в подвале</span><span>5 полей, включая индекс</span>
  </div>
</div>'''

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L3_tez_1", "tezis", "InfographicCards", "Бюджет <em>сгорает</em>", "а заявок нет", {"variant": "tech", "items": [
        {"id": 1, "label": "Бюджет", "value": "€2000", "trend": "в месяц на рекламу", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "Трафик", "value": "Идёт", "trend": "на новый сайт", "color": A2, "icon": "heroicons:cursor-arrow-rays", "start_time": 800},
        {"id": 3, "label": "Внимание", "value": "3 сек", "trend": "и вкладка закрыта", "color": A3, "icon": "heroicons:clock", "start_time": 1600},
        {"id": 4, "label": "Винить", "value": "Рекламу?", "trend": "обычно зря", "color": A4, "icon": "heroicons:question-mark-circle", "start_time": 2400}]}),
    ("L3_tez_2", "tezis", "StatsBarChart", "Три <em>секунды</em>", "внимание по секундам", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Три секунды", "subtitle": "внимание по секундам", "data": [
        {"label": "0–1с", "value": 100, "highlight": True, "start_time": 0},
        {"label": "1–2с", "value": 70, "start_time": 800},
        {"label": "2–3с", "value": 40, "start_time": 1600},
        {"label": ">3с", "value": 10, "start_time": 2400}]}),
    ("L3_tez_3", "tezis", "ComparisonTable", "Ломается <em>путь</em>", "а не реклама", {"variant": "tech", "headers": ["", "Реклама", "Архитектура"], "items": [
        {"id": "r1", "label": "Трафик целевой", "values": [True, True], "start_time": 0},
        {"id": "r2", "label": "Оффер понятен", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Путь к покупке", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Заявка доходит", "values": [False, True], "start_time": 2400}]}),
    ("L3_tez_4", "tezis", "MetricScales", "Где <em>теряется</em> клиент", "на входе", {"variant": "tech", "title": "Где теряется клиент", "subtitle": "на входе", "metrics": [
        {"id": 1, "label": "Понял оффер за 3 сек", "percentage": 12, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Нашёл цену сразу", "percentage": 8, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Нашёл форму связи", "percentage": 15, "color": G2c, "start_time": 1600}]}),
    ("L3_tez_5", "tezis", "PremiumChecklist", "Что <em>сломано</em>", "при шаблонной сборке", {"variant": "tech", "items": [
        {"label": "Путь клиента", "desc": "логика решения", "icon": "heroicons:map", "color": "brand-blue", "start_time": 0},
        {"label": "Оффер", "desc": "не виден без скролла", "icon": "heroicons:magnifying-glass", "color": "brand-amber", "start_time": 800},
        {"label": "Передача лида", "desc": "падает в общую почту", "icon": "heroicons:paper-airplane", "color": "brand-green", "start_time": 1600}]}),
    ("L3_tez_6", "tezis", "ArchitectureDiagram", "Путь <em>B2B-решения</em>", "как надо", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клик", "subtitle": "реклама", "icon": "lucide:mouse-pointer-click", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["offer"]},
        {"id": "offer", "title": "Оффер", "subtitle": "3 секунды", "icon": "lucide:eye", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["contact"]},
        {"id": "contact", "title": "Контакт", "subtitle": "одна кнопка", "icon": "lucide:phone", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["crm"]},
        {"id": "crm", "title": "CRM", "subtitle": "лид у менеджера", "icon": "lucide:database", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L3_hyp_1", "hype", "InfographicCards", "Тёплый и <em>холодный</em>", "разный трафик", {"variant": "tech", "items": [
        {"id": 1, "label": "Тёплый", "value": "Работает", "trend": "из рекомендаций", "color": A2, "icon": "heroicons:heart", "start_time": 0},
        {"id": 2, "label": "Холодный", "value": "Уходит", "trend": "3 секунды", "color": A4, "icon": "heroicons:bolt", "start_time": 800},
        {"id": 3, "label": "Клик", "value": "Списан", "trend": "деньги ушли", "color": A3, "icon": "heroicons:banknotes", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Тишина", "trend": "нет заявок", "color": A1, "icon": "heroicons:bell-slash", "start_time": 2400}]}),
    ("L3_hyp_2", "hype", "ComparisonTable", "Тёплый <em>или холодный</em>", "разная логика", {"variant": "tech", "headers": ["", "Тёплый", "Холодный"], "items": [
        {"id": "r1", "label": "Уже знает вас", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Готов смотреть", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Прощает красоту", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Нужен оффер сразу", "values": [False, True], "start_time": 2400}]}),
    ("L3_hyp_3", "hype", "MetricScales", "Математика <em>холодного</em>", "три секунды", {"variant": "tech", "title": "Математика холодного", "subtitle": "три секунды", "metrics": [
        {"id": 1, "label": "Понял оффер", "percentage": 12, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Понял продукт", "percentage": 20, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Оставил заявку", "percentage": 5, "color": G3c, "start_time": 1600}]}),
    ("L3_hyp_4", "hype", "BrowserMockup", "Свежий сайт <em>на конструкторе</em>", "красиво, но не продаёт", {"variant": "tech", "items": [
        {"id": "b1", "url": "ozero-resort.com", "type": "html", "content": BAD_SITE_HTML, "scroll": False, "image_position": "top", "start_time": 0}]}),
    ("L3_hyp_5", "hype", "PremiumChecklist", "Что навязывает <em>шаблон</em>", "жёсткая структура", {"variant": "tech", "items": [
        {"label": "Блоки", "desc": "стандартные, не под процесс", "icon": "heroicons:squares-2x2", "color": "brand-blue", "start_time": 0},
        {"label": "Текст", "desc": "история вместо оффера", "icon": "heroicons:document-text", "color": "brand-amber", "start_time": 800},
        {"label": "Форма", "desc": "в подвале, лишние поля", "icon": "heroicons:inbox", "color": "brand-green", "start_time": 1600}]}),
    ("L3_hyp_6", "hype", "QuadrantMatrix", "Шаблон <em>или кастом</em>", "зависит от задачи", {"variant": "tech",
        "points": [
            {"label": "Визитка", "x": 80, "y": 25, "bubble": 22, "color": "var(--color-secondary)"},
            {"label": "Лендинг B2B", "x": 25, "y": 80, "bubble": 28, "color": "var(--color-success)"},
            {"label": "Сложный продукт", "x": 15, "y": 92, "bubble": 30, "color": "var(--color-accent)"}],
        "x_label": "Простота", "y_label": "Требования к конверсии",
        "quadrant_labels": ["Кастом", "Шаблон+", "Пересмотреть", "Шаблон ок"]}),
    ("L3_hyp_7", "hype", "AnimatedStatsSlide", "Три секунды <em>решают</em>", "или деньги ушли", {"variant": "tech", "stats": [
        {"label": "На оффер", "value": 3, "suffix": "сек", "color": A3, "icon": "lucide:clock", "start_time": 0},
        {"label": "Стоимость клика", "value": 2, "suffix": "€", "color": A1, "icon": "lucide:mouse-pointer-click", "start_time": 800},
        {"label": "Лишний текст", "value": 1, "suffix": "стена", "color": A4, "icon": "heroicons:no-symbol", "start_time": 1600}]}),
    ("L3_hyp_8", "hype", "WaterfallChart", "Бюджет <em>в никуда</em>", "вкладка закрыта", {"variant": "tech",
        "start_label": "Бюджет/мес", "start_value": 2000,
        "steps": [{"label": "Вкладка закрыта", "delta": -2000, "kind": "neg"}],
        "end_label": "Заявки", "value_prefix": "€", "value_suffix": ""}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L3_how_1", "how", "PremiumChecklist", "Три <em>проверки</em>", "до цветов и шрифтов", {"variant": "tech", "items": [
        {"label": "Оффер без скролла", "desc": "понятен сразу", "icon": "heroicons:eye", "color": "brand-blue", "start_time": 0},
        {"label": "Где берём контакт", "desc": "точка захвата", "icon": "heroicons:cursor-arrow-rays", "color": "brand-amber", "start_time": 800},
        {"label": "Куда летит заявка", "desc": "в CRM, а не на почту", "icon": "heroicons:paper-airplane", "color": "brand-green", "start_time": 1600}]}),
    ("L3_how_2", "how", "ArchitectureDiagram", "Путь <em>от клика</em>", "до CRM", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клик", "subtitle": "реклама", "icon": "lucide:mouse-pointer-click", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["offer"]},
        {"id": "offer", "title": "Оффер", "subtitle": "1 экран", "icon": "lucide:eye", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["pick"]},
        {"id": "pick", "title": "Выбор", "subtitle": "даты и домик", "icon": "lucide:calendar", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["crm"]},
        {"id": "crm", "title": "CRM", "subtitle": "пуш менеджеру", "icon": "lucide:database", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L3_how_3", "how", "StepByStep", "Порядок <em>проектирования</em>", "сначала логика", {"variant": "tech", "title": "", "subtitle": "", "layout": "horizontal", "steps": [
        {"id": "s1", "number": 1, "title": "Цель", "description": "продать сейчас?", "icon": "heroicons:flag", "color": "var(--color-secondary)", "start_time": 0},
        {"id": "s2", "number": 2, "title": "Оффер", "description": "на первый экран", "icon": "heroicons:bolt", "color": "var(--color-success)", "start_time": 800},
        {"id": "s3", "number": 3, "title": "Контакт", "description": "одна точка", "icon": "heroicons:cursor-arrow-rays", "color": "var(--color-warning)", "start_time": 1600},
        {"id": "s4", "number": 4, "title": "Интеграция", "description": "лид в CRM", "icon": "heroicons:circle-stack", "color": "var(--color-accent)", "start_time": 2400}]}),
    ("L3_how_4", "how", "ChatMockupSlide", "Один <em>вопрос</em>", "прежде чем рисовать", {"variant": "tech", "bot_name": "Игорь", "bot_subtitle": "архитектор", "bot_avatar": "И", "messages": [
        {"role": "user", "text": "Добавим раздел о команде?", "start_time": 0},
        {"role": "assistant", "text": "Сначала цель: продать сейчас или рассказать?", "start_time": 1500},
        {"role": "user", "text": "Продать.", "start_time": 3000}]}),
    ("L3_how_5", "how", "CrmCardSlide", "Заявка <em>в CRM</em>", "не на почту", {"variant": "tech", "customer": {"name": "База отдыха", "avatar_text": "БО", "id_text": "ID: #1500", "status": "новая"},
        "fields": [
            {"label": "ДАТЫ", "value": "12–14 июл", "field_icon": "heroicons:calendar-days", "field_color": "brand-green", "start_time": 300},
            {"label": "ДОМИК", "value": "Озеро, №7", "field_icon": "heroicons:home", "field_color": "brand-blue", "start_time": 1100},
            {"label": "ЦЕНА", "value": "€180/сутки", "field_icon": "heroicons:banknotes", "field_color": "brand-amber", "start_time": 1900},
            {"label": "ТЕЛЕФОН", "value": "+49 …", "field_icon": "heroicons:phone", "field_color": "brand-blue", "start_time": 2700}],
        "buttons": [
            {"text": "Позвонить", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Написать", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L3_how_6", "how", "MetricScales", "Судьба <em>лида</em>", "где он оказывается", {"variant": "tech", "title": "Судьба лида", "subtitle": "где он оказывается", "metrics": [
        {"id": 1, "label": "В CRM с параметрами", "percentage": 100, "color": G1c, "start_time": 0},
        {"id": 2, "label": "На общей почте", "percentage": 10, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Ждёт ответа сутки", "percentage": 5, "color": G3c, "start_time": 1600}]}),
    ("L3_how_7", "how", "InfographicCards", "Три <em>вещи</em>", "и всё", {"variant": "tech", "items": [
        {"id": 1, "label": "Оффер", "value": "1 экран", "trend": "без скролла", "color": A1, "icon": "heroicons:eye", "start_time": 0},
        {"id": 2, "label": "Контакт", "value": "Точка", "trend": "где берём", "color": A2, "icon": "heroicons:cursor-arrow-rays", "start_time": 800},
        {"id": 3, "label": "Данные", "value": "CRM", "trend": "куда летит", "color": A3, "icon": "heroicons:circle-stack", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Логика", "trend": "а не декор", "color": A4, "icon": "heroicons:map", "start_time": 2400}]}),
    ("L3_how_8", "how", "ComparisonTable", "Текст <em>против</em> оффера", "на первом экране", {"variant": "tech", "headers": ["", "История", "Оффер"], "items": [
        {"id": "r1", "label": "Понятно за 3 сек", "values": [False, True], "start_time": 0},
        {"id": "r2", "label": "Ведёт к заявке", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Не отвлекает", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Экономит бюджет", "values": [False, True], "start_time": 2400}]}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L3_prj_1", "project", "AnimatedStatsSlide", "База <em>отдыха</em>", "сорок домиков", {"variant": "tech", "stats": [
        {"label": "Домиков", "value": 40, "suffix": "", "color": A2, "icon": "lucide:home", "start_time": 0},
        {"label": "Бюджет трафика", "value": 1500, "suffix": "€", "color": A1, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Заявок", "value": 7, "suffix": "", "color": A4, "icon": "lucide:inbox", "start_time": 1600}]}),
    ("L3_prj_2", "project", "ReceiptCard", "", "", {"variant": "tech", "title": "БЮДЖЕТ НА РЕКЛАМУ", "subtitle": "Google Ads", "currency": "€", "total_text": "ПОТРАЧЕНО", "footer_text": "ЗА МЕСЯЦ", "total_start_time": 2600, "items": [
        {"name": "Кампании", "price": 1000, "start_time": 300},
        {"name": "Ведение", "price": 300, "start_time": 1100},
        {"name": "Креативы", "price": 200, "start_time": 1900}]}),
    ("L3_prj_3", "project", "InfographicCards", "Семь <em>заявок</em>", "что внутри", {"variant": "tech", "items": [
        {"id": 1, "label": "Всего", "value": "7", "trend": "за месяц", "color": A1, "icon": "heroicons:inbox", "start_time": 0},
        {"id": 2, "label": "«Шашлык»", "value": "5", "trend": "не по делу", "color": A4, "icon": "heroicons:fire", "start_time": 800},
        {"id": 3, "label": "Целевые", "value": "2", "trend": "брони", "color": A2, "icon": "heroicons:check-badge", "start_time": 1600},
        {"id": 4, "label": "Трафик", "value": "Целевой", "trend": "дело не в рекламе", "color": A3, "icon": "heroicons:chart-bar", "start_time": 2400}]}),
    ("L3_prj_4", "project", "PremiumChecklist", "Что мешало <em>купить</em>", "на главной", {"variant": "tech", "items": [
        {"label": "Баннер с озером", "desc": "красиво, но не оффер", "icon": "heroicons:photo", "color": "brand-blue", "start_time": 0},
        {"label": "История и миссия", "desc": "лишний текст сверху", "icon": "heroicons:document-text", "color": "brand-amber", "start_time": 800},
        {"label": "Форма в подвале", "desc": "5 полей с индексом", "icon": "heroicons:inbox", "color": "brand-green", "start_time": 1600}]}),
    ("L3_prj_5", "project", "ArchitectureDiagram", "Новая <em>архитектура</em>", "первый экран — оффер", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Первый экран", "subtitle": "даты · домик · цена", "icon": "lucide:mouse-pointer-click", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["pick"]},
        {"id": "pick", "title": "Выбор", "subtitle": "даты и домик", "icon": "lucide:calendar", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["phone"]},
        {"id": "phone", "title": "Телефон", "subtitle": "одна точка", "icon": "lucide:phone", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["push"]},
        {"id": "push", "title": "Пуш", "subtitle": "менеджеру сразу", "icon": "lucide:bell", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L3_prj_6", "project", "ProcessFunnel", "Воронка <em>брони</em>", "от визита до продажи", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Визиты", "count": 1000, "icon": "heroicons:cursor-arrow-rays", "color": A1, "start_time": 0},
        {"label": "Выбрали домик", "count": 120, "icon": "heroicons:home", "color": A2, "start_time": 800},
        {"label": "Оставили телефон", "count": 42, "icon": "heroicons:phone", "color": A3, "start_time": 1600},
        {"label": "Бронь", "count": 20, "icon": "heroicons:check-circle", "color": A4, "start_time": 2400}]}),
    ("L3_prj_7", "project", "StatsBarChart", "Было <em>7</em>", "стало 42", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Было 7", "subtitle": "стало 42", "data": [
        {"label": "Было", "value": 7, "start_time": 0},
        {"label": "Нед 1", "value": 8, "start_time": 800},
        {"label": "Нед 2", "value": 12, "start_time": 1600},
        {"label": "Итог", "value": 42, "highlight": True, "start_time": 2400}]}),
    ("L3_prj_8", "project", "AnimatedStatsSlide", "Результат <em>месяца</em>", "тот же бюджет", {"variant": "tech", "stats": [
        {"label": "Целевые заявки", "value": 42, "suffix": "", "color": A2, "icon": "lucide:inbox", "start_time": 0},
        {"label": "Стоимость лида", "value": 36, "suffix": "€", "color": A1, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Бюджет", "value": 1500, "suffix": "€", "color": A3, "icon": "lucide:wallet", "start_time": 1600}]}),
    ("L3_prj_9", "project", "ChatMockupSlide", "Пуш <em>менеджеру</em>", "в ту же секунду", {"variant": "tech", "bot_name": "Пуш", "bot_subtitle": "новая бронь", "bot_avatar": "N", "messages": [
        {"role": "assistant", "text": "Бронь: 12–14 июля, домик №7, €180/сутки.", "start_time": 0},
        {"role": "assistant", "text": "Телефон: +49 … Уточнять не нужно.", "start_time": 1500}]}),
    ("L3_prj_10", "project", "CrmCardSlide", "Карточка <em>брони</em>", "всё уже собрано", {"variant": "tech", "customer": {"name": "Семья К.", "avatar_text": "К", "id_text": "ID: #4210", "status": "горячая"},
        "fields": [
            {"label": "ДАТЫ", "value": "12–14 июл", "field_icon": "heroicons:calendar-days", "field_color": "brand-green", "start_time": 300},
            {"label": "ДОМИК", "value": "Озеро, №7", "field_icon": "heroicons:home", "field_color": "brand-blue", "start_time": 1100},
            {"label": "СУММА", "value": "€540", "field_icon": "heroicons:banknotes", "field_color": "brand-amber", "start_time": 1900},
            {"label": "КАНАЛ", "value": "Сайт", "field_icon": "heroicons:globe-alt", "field_color": "brand-blue", "start_time": 2700}],
        "buttons": [
            {"text": "Подтвердить", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Позвонить", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L3_prj_11", "project", "WaterfallChart", "7 → <em>42</em>", "без смены рекламы", {"variant": "tech",
        "start_label": "Было", "start_value": 7,
        "steps": [{"label": "Новая архитектура", "delta": 35, "kind": "pos"}],
        "end_label": "Стало", "value_prefix": "", "value_suffix": ""}),
    ("L3_prj_12", "project", "KpiDashboard", "Результат <em>кейса</em>", "метрики", {"variant": "tech", "title": "", "subtitle": "", "metrics": [
        {"id": "k1", "label": "Заявки", "value": "42", "unit": "/мес", "trend": "+500%", "color": "var(--color-success)", "icon": "heroicons:inbox", "sparkline": [7, 8, 12, 20, 30, 38, 42], "start_time": 0},
        {"id": "k2", "label": "Стоимость лида", "value": "36", "unit": "€", "trend": "-70%", "color": "var(--color-secondary)", "icon": "heroicons:banknotes", "sparkline": [214, 180, 120, 80, 55, 40, 36], "start_time": 900},
        {"id": "k3", "label": "Конверсия", "value": "4.2", "unit": "%", "trend": "+3.5 пт", "color": "var(--color-accent)", "icon": "heroicons:arrow-trending-up", "sparkline": [0.7, 0.9, 1.4, 2.1, 2.9, 3.6, 4.2], "start_time": 1800},
        {"id": "k4", "label": "Доля броней", "value": "48", "unit": "%", "trend": "+31 пт", "color": "var(--color-warning)", "icon": "heroicons:home", "sparkline": [17, 22, 28, 34, 39, 44, 48], "start_time": 2700}]}),
    ("L3_prj_13", "project", "PremiumChecklist", "Что убрал <em>и добавил</em>", "по итогу", {"variant": "tech", "items": [
        {"label": "Убрал баннер", "desc": "оффер вместо озера", "icon": "heroicons:no-symbol", "color": "brand-blue", "start_time": 0},
        {"label": "Убрал мёртвую форму", "desc": "5 полей с индексом", "icon": "heroicons:x-circle", "color": "brand-amber", "start_time": 800},
        {"label": "Добавил выбор", "desc": "даты, домик, цена", "icon": "heroicons:calendar-days", "color": "brand-green", "start_time": 1600}]}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L3_whr_1", "where", "ComparisonTable", "Когда <em>конструктор</em>", "и когда кастом", {"variant": "tech", "headers": ["", "Конструктор", "Кастом"], "items": [
        {"id": "r1", "label": "Простая задача", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Тёплый трафик", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Сложный B2B", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Логика пути клиента", "values": [False, True], "start_time": 2400}]}),
    ("L3_whr_2", "where", "PremiumChecklist", "Кастом <em>не нужен</em>", "честно", {"variant": "tech", "items": [
        {"label": "Простая задача", "desc": "базовый блок справится", "icon": "heroicons:squares-2x2", "color": "brand-blue", "start_time": 0},
        {"label": "Тёплый трафик", "desc": "рекомендации, сарафан", "icon": "heroicons:heart", "color": "brand-amber", "start_time": 800},
        {"label": "Нет отдела продаж", "desc": "сайт не спасёт", "icon": "heroicons:user-group", "color": "brand-green", "start_time": 1600}]}),
    ("L3_whr_3", "where", "QuadrantMatrix", "Трафик и <em>сложность</em>", "что выбрать", {"variant": "tech",
        "points": [
            {"label": "Визитка", "x": 80, "y": 20, "bubble": 22, "color": "var(--color-secondary)"},
            {"label": "Лендинг услуги", "x": 70, "y": 60, "bubble": 24, "color": "var(--color-success)"},
            {"label": "Сложный B2B", "x": 20, "y": 85, "bubble": 30, "color": "var(--color-accent)"}],
        "x_label": "Простота", "y_label": "Зависимость от конверсии",
        "quadrant_labels": ["Кастом", "Шаблон+", "Пересмотреть", "Шаблон ок"]}),
    ("L3_whr_4", "where", "AnimatedStatsSlide", "Без <em>продаж</em>", "архитектура не поможет", {"variant": "tech", "stats": [
        {"label": "Влияет сайт", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:globe", "start_time": 0},
        {"label": "Нужен отдел продаж", "value": 100, "suffix": "%", "color": A1, "icon": "lucide:users", "start_time": 800},
        {"label": "Сайт сам не продаст", "value": 1, "suffix": "", "color": A4, "icon": "lucide:alert-triangle", "start_time": 1600}]}),

    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L3_cnc_1", "conclusion", "DefinitionBlock", "Лендинг — <em>инструмент</em>", "не визитка", {"variant": "tech",
        "term": "Лендинг",
        "definition": "Инструмент продаж: показывает оффер, ведёт к заявке и передаёт лид менеджеру.",
        "examples": [
            {"id": "d1", "text": "Первый экран отвечает на «что вы продаёте».", "start_time": 1000},
            {"id": "d2", "text": "Вместо формы — понятный путь и одна кнопка.", "start_time": 2000}],
        "related_terms": ["Оффер", "Конверсия", "CRM"]}),
    ("L3_cnc_2", "conclusion", "ArchitectureDiagram", "Красота <em>без логики</em>", "дыра в бюджете", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Красивый сайт", "subtitle": "без архитектуры", "icon": "lucide:sparkles", "color": "chart-4", "start_time": 0, "is_main": False, "to": ["hole"]},
        {"id": "hole", "title": "Бюджет", "subtitle": "утекает", "icon": "heroicons:banknotes", "color": "chart-5", "start_time": 800, "is_main": True, "to": []},
        {"id": "ok", "title": "Логика пути", "subtitle": "лид в CRM", "icon": "lucide:check-circle", "color": "chart-3", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L3_cnc_3", "conclusion", "PremiumChecklist", "Итог <em>без воды</em>", "одна мысль", {"variant": "tech", "items": [
        {"label": "Сайт", "desc": "инструмент продаж", "icon": "heroicons:globe-alt", "color": "brand-blue", "start_time": 0},
        {"label": "Архитектура", "desc": "путь клиента, а не декор", "icon": "heroicons:map", "color": "brand-amber", "start_time": 800},
        {"label": "Иначе", "desc": "чёрная дыра в рекламном бюджете", "icon": "heroicons:banknotes", "color": "brand-green", "start_time": 1600}]}),

    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L3_cta_1", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
]


def validate(comp, payload):
    r = requests.post(f"{BASE}/components/{comp}/validate", json={"payload": payload})
    r.raise_for_status()
    return r.json()


def compute_times():
    d = requests.get(f"{BASE}/presentations/{PRES_ID}").json()
    clips = sorted([c for t in d["audio_timeline"]["tracks"] if t["id"] == "main" for c in t["clips"]],
                   key=lambda c: c["start_time"])
    bounds = {SECTIONS[i]: (clips[i]["start_time"], clips[i]["end_time"]) for i in range(len(SECTIONS))}
    counts = {}
    for _, sec, *_ in SLIDES:
        counts[sec] = counts.get(sec, 0) + 1
    starts = {}
    for sec, (s, e) in bounds.items():
        n = counts.get(sec, 0)
        if not n:
            continue
        step = max(2000, min(8000, int((e - s) / n)))
        idx = 0
        for sid, sc, *_ in SLIDES:
            if sc == sec:
                starts[sid] = s + idx * step
                idx += 1
    ordered = [x[0] for x in SLIDES]
    for i in range(1, len(ordered)):
        starts[ordered[i]] = max(starts[ordered[i]], starts[ordered[i - 1]] + 2000)
    return starts


def main():
    starts = compute_times()
    print("--- Creating slides ---")
    ok, fail = 0, []
    for i, (sid, sec, comp, title, sub, payload) in enumerate(SLIDES, start=1):
        res = validate(comp, payload)
        if not res.get("valid"):
            print(f"INVALID {sid} {comp}: {res.get('errors')}")
            fail.append(sid)
            continue
        for w in res.get("warnings", []):
            print(f"  warn {sid}: {w.get('type')} @ {w.get('path')}")
        gs.create_slide(PRES_ID, sid, comp, starts[sid], i, title=title, subtitle=sub, payload=payload)
        print(f"  OK {sid:<10} {starts[sid]:>7.0f}ms  {comp}")
        ok += 1
    normalize_bgm_track(PRES_ID)
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5175/p/{PRES_ID}")


if __name__ == "__main__":
    main()
