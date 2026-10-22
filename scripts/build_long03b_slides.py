#!/usr/bin/env python3
"""Слайды для Длинное_03 (переписанный сценарий, presentation 69), 7 блоков.

Запуск с хоста: python3 scripts/build_long03b_slides.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402
from build_long03_slides import BAD_SITE_HTML  # noqa: E402

BASE = gs.BASE
PRES_ID = 70
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]
A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

GOOD_SITE_HTML = '''<div style="display:flex;flex-direction:column;width:100%;min-height:100cqh;box-sizing:border-box;background:#0b1322;color:#f8fafc;font-family:Inter,system-ui,sans-serif;overflow:hidden;">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;flex-shrink:0;">
    <span style="font-weight:800;letter-spacing:2px;font-size:13px;white-space:nowrap;">ОЗЕРО <span style="color:#38bdf8;">РЕЗОРТ</span></span>
    <span style="font-size:11px;color:rgba(255,255,255,0.55);white-space:nowrap;">Бронирование онлайн</span>
  </div>
  <div style="flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:14px;padding:10px 18px;background:url('https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&q=80&w=1600') center/cover no-repeat;position:relative;">
    <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,19,34,0.35),rgba(11,19,34,0.9));"></div>
    <div style="position:relative;">
      <div style="font-size:11px;letter-spacing:4px;color:#7dd3fc;">ДОМИКИ У ОЗЕРА · СУТКИ</div>
      <div style="font-size:30px;font-weight:800;line-height:1.1;margin-top:8px;">Выберите даты — остальное соберём сами</div>
    </div>
    <div style="position:relative;display:flex;flex-wrap:wrap;gap:10px;">
      <div style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);border-radius:10px;padding:10px 14px;font-size:13px;">12–14 июля</div>
      <div style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);border-radius:10px;padding:10px 14px;font-size:13px;">Домик «Озеро»</div>
      <div style="background:rgba(56,189,248,0.2);border:1px solid rgba(56,189,248,0.5);border-radius:10px;padding:10px 14px;font-size:13px;font-weight:700;">€180 / сутки</div>
      <div style="background:#38bdf8;color:#04121f;border-radius:10px;padding:10px 18px;font-size:13px;font-weight:800;">Забронировать</div>
    </div>
  </div>
  <div style="padding:10px 18px;font-size:10px;color:rgba(255,255,255,0.4);border-top:1px solid rgba(255,255,255,0.06);">Телефон — один шаг. Менеджер получает бронь сразу.</div>
</div>'''

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L3c_tez_1", "tezis", "InfographicCards", "Привет из <em>2010</em>", "первый экран", {"variant": "tech", "items": [
        {"id": 1, "label": "Стоковые улыбки", "value": "Штамп", "trend": "узнаётся мгновенно", "color": A1, "icon": "heroicons:face-smile", "start_time": 0},
        {"id": 2, "label": "Серый текст", "value": "Стена", "trend": "оффер не читают", "color": A4, "icon": "heroicons:document-text", "start_time": 800},
        {"id": 3, "label": "Баннер", "value": "Ни о чём", "trend": "красиво и пусто", "color": A3, "icon": "heroicons:photo", "start_time": 1600},
        {"id": 4, "label": "Вывод клиента", "value": "Старые", "trend": "до первого слова", "color": A2, "icon": "heroicons:clock", "start_time": 2400}]}),
    ("L3c_tez_2", "tezis", "AnimatedStatsSlide", "Решение за <em>секунду</em>", "до оффера", {"variant": "tech", "stats": [
        {"label": "На оценку", "value": 1, "suffix": "сек", "color": A3, "icon": "lucide:eye", "start_time": 0},
        {"label": "Вид сайта", "value": 2010, "suffix": "", "color": A4, "icon": "lucide:clock", "start_time": 800},
        {"label": "Оффер", "value": 1, "suffix": "не прочитан", "color": A1, "icon": "lucide:file-x", "start_time": 1600}]}),
    ("L3c_tez_3", "tezis", "ComparisonTable", "2010 <em>против</em> живого", "что видит клиент", {"variant": "tech", "headers": ["", "Шаблон 2010", "Живой сайт"], "items": [
        {"id": "r1", "label": "Стоковые фото", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Оффер на первом экране", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Человеческий язык", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Ощущение надёжности", "values": [False, True], "start_time": 2400}]}),
    ("L3c_tez_4", "tezis", "MetricScales", "Что теряешь <em>сразу</em>", "до первого экрана", {"variant": "tech", "title": "Что теряешь сразу", "subtitle": "до первого экрана", "metrics": [
        {"id": 1, "label": "Доверие", "percentage": 10, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Оффер прочитан", "percentage": 15, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Дошёл до заявки", "percentage": 5, "color": G2c, "start_time": 1600}]}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L3c_hyp_1", "hype", "ComparisonTable", "Раньше <em>и сейчас</em>", "правила изменились", {"variant": "tech", "headers": ["", "Раньше", "Сейчас"], "items": [
        {"id": "r1", "label": "Все одинаковые", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Хватало картинки", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Глаз отличает живое", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Платят за ощущение", "values": [False, True], "start_time": 2400}]}),
    ("L3c_hyp_2", "hype", "AnimatedStatsSlide", "Клиент видел <em>сотни</em>", "сайтов", {"variant": "tech", "stats": [
        {"label": "Современных сайтов", "value": 100, "suffix": "+", "color": A2, "icon": "lucide:layout-grid", "start_time": 0},
        {"label": "Отличает живое", "value": 1, "suffix": "сек", "color": A3, "icon": "lucide:eye", "start_time": 800},
        {"label": "Решает ощущение", "value": 100, "suffix": "%", "color": A1, "icon": "lucide:heart", "start_time": 1600}]}),
    ("L3c_hyp_3", "hype", "QuoteCard", "Голос <em>клиента</em>", "пока он смотрит", {"variant": "tech",
        "quote": "Сайт как из 2010. Они что, давно этим не занимаются? А может, компании уже нет.",
        "author": "Клиент", "author_title": "читает первый экран", "source": "до первого слова продавца"}),
    ("L3c_hyp_4", "hype", "PremiumChecklist", "Что он <em>достраивает</em>", "по сайту", {"variant": "tech", "items": [
        {"label": "«Здесь не меняется»", "desc": "устаревший вид", "icon": "heroicons:clock", "color": "brand-blue", "start_time": 0},
        {"label": "«Компании уже нет»", "desc": "мёртвый сайт", "icon": "heroicons:face-frown", "color": "brand-amber", "start_time": 800},
        {"label": "«Сервис такой же»", "desc": "по аналогии", "icon": "heroicons:exclamation-triangle", "color": "brand-green", "start_time": 1600}]}),
    ("L3c_hyp_5", "hype", "InfographicCards", "Сигналы <em>о компании</em>", "читает везде", {"variant": "tech", "items": [
        {"id": 1, "label": "Нет онлайн-записи", "value": "Старинка", "trend": "только телефон", "color": A1, "icon": "heroicons:phone", "start_time": 0},
        {"id": 2, "label": "Бот выдумывает", "value": "Нет контроля", "trend": "сервис не держат", "color": A4, "icon": "heroicons:cpu-chip", "start_time": 800},
        {"id": 3, "label": "Данные в голове", "value": "Потеряют", "trend": "как всех до меня", "color": A3, "icon": "heroicons:user", "start_time": 1600},
        {"id": 4, "label": "Сайт-шаблон", "value": "Старые", "trend": "сигнал обо всей", "color": A2, "icon": "heroicons:globe-alt", "start_time": 2400}]}),
    ("L3c_hyp_6", "hype", "ArchitectureDiagram", "Сигнал <em>обо всей</em>", "компании", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Первый экран", "subtitle": "сайт-шаблон", "icon": "lucide:monitor", "color": "chart-4", "start_time": 0, "is_main": False, "to": ["trust"]},
        {"id": "trust", "title": "Доверие", "subtitle": "падает", "icon": "lucide:shield", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["deal"]},
        {"id": "deal", "title": "Заявка", "subtitle": "не приходит", "icon": "lucide:inbox", "color": "chart-6", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L3c_hyp_7", "hype", "MetricScales", "Решает <em>первый экран</em>", "а не сервис внутри", {"variant": "tech", "title": "Решает первый экран", "subtitle": "а не сервис внутри", "metrics": [
        {"id": 1, "label": "Впечатление за 1 сек", "percentage": 100, "color": G1c, "start_time": 0},
        {"id": 2, "label": "Дочитал оффер", "percentage": 20, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Написал/позвонил", "percentage": 8, "color": G3c, "start_time": 1600}]}),
    ("L3c_hyp_8", "hype", "StatsBarChart", "Доверие <em>тает</em>", "по экранам", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Доверие тает", "subtitle": "по экранам", "data": [
        {"label": "1 экран", "value": 100, "highlight": True, "start_time": 0},
        {"label": "2 экран", "value": 45, "start_time": 800},
        {"label": "3 экран", "value": 18, "start_time": 1600},
        {"label": "Форма", "value": 6, "start_time": 2400}]}),
    ("L3c_hyp_9", "hype", "DefinitionBlock", "Живой <em>сайт</em>", "термин", {"variant": "tech",
        "term": "Живой сайт",
        "definition": "Сайт, который клиент читает как «здесь работают люди, которым можно доверить деньги».",
        "examples": [
            {"id": "d1", "text": "Настоящие фото и формулировки вместо стока.", "start_time": 1000},
            {"id": "d2", "text": "Быстро, понятно и без поиска кнопки.", "start_time": 2000}],
        "related_terms": ["Оффер", "Доверие", "Скорость"]}),
    ("L3c_hyp_10", "hype", "QuadrantMatrix", "Шаблон <em>или живой</em>", "что решает", {"variant": "tech",
        "points": [
            {"label": "Шаблон 2010", "x": 20, "y": 20, "bubble": 26, "color": "var(--color-danger)"},
            {"label": "Свежий, но безликий", "x": 55, "y": 45, "bubble": 22, "color": "var(--color-warning)"},
            {"label": "Живой + оффер", "x": 85, "y": 90, "bubble": 30, "color": "var(--color-success)"}],
        "x_label": "Современность", "y_label": "Доверие и заявки",
        "quadrant_labels": ["Старый", "Живой", "Пересмотреть", "Безликий"]}),
    ("L3c_hyp_11", "hype", "WaterfallChart", "Бюджет <em>в никуда</em>", "до первого экрана", {"variant": "tech",
        "start_label": "Бюджет/мес", "start_value": 2000,
        "steps": [{"label": "Ушёл до оффера", "delta": -2000, "kind": "neg"}],
        "end_label": "Заявки", "value_prefix": "€", "value_suffix": ""}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L3c_how_1", "how", "QuoteCard", "Про <em>ощущение</em>", "а не про «красиво»", {"variant": "tech",
        "quote": "Я думаю не про «красиво», а про ощущение, которое человек забирает с собой.",
        "author": "Игорь", "author_title": "IT2B", "source": "принцип работы"}),
    ("L3c_how_2", "how", "PremiumChecklist", "Из чего <em>собирается</em>", "по отдельности не видно", {"variant": "tech", "items": [
        {"label": "Живые детали", "desc": "настоящие фото вместо стока", "icon": "heroicons:camera", "color": "brand-blue", "start_time": 0},
        {"label": "Язык человека", "desc": "коротко и понятно", "icon": "heroicons:chat-bubble-left", "color": "brand-amber", "start_time": 800},
        {"label": "Ритм и воздух", "desc": "сайт дышит, а не кричит", "icon": "heroicons:sparkles", "color": "brand-green", "start_time": 1600}]}),
    ("L3c_how_3", "how", "StepByStep", "Как я <em>собираю</em>", "живой сайт", {"variant": "tech", "title": "", "subtitle": "", "layout": "horizontal", "steps": [
        {"id": "s1", "number": 1, "title": "Детали", "description": "настоящие фото", "icon": "heroicons:camera", "color": "var(--color-secondary)", "start_time": 0},
        {"id": "s2", "number": 2, "title": "Язык", "description": "человеческие фразы", "icon": "heroicons:chat-bubble-left", "color": "var(--color-success)", "start_time": 800},
        {"id": "s3", "number": 3, "title": "Ритм", "description": "порядок и воздух", "icon": "heroicons:sparkles", "color": "var(--color-warning)", "start_time": 1600},
        {"id": "s4", "number": 4, "title": "Скорость", "description": "и понятный путь", "icon": "heroicons:bolt", "color": "var(--color-accent)", "start_time": 2400}]}),
    ("L3c_how_4", "how", "MetricScales", "Мёртвый <em>даже красивый</em>", "если медленный", {"variant": "tech", "title": "Мёртвый даже красивый", "subtitle": "если медленный", "metrics": [
        {"id": 1, "label": "Грузится за 6 сек", "percentage": 100, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Кнопка в подвале", "percentage": 100, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Живой: быстро и ясно", "percentage": 15, "color": G2c, "start_time": 1600}]}),
    ("L3c_how_5", "how", "BrowserMockup", "Живой <em>первый экран</em>", "даты · домик · цена", {"variant": "tech", "items": [
        {"id": "g1", "url": "ozero-resort.com", "type": "html", "content": GOOD_SITE_HTML, "scroll": False, "image_position": "top", "start_time": 0}]}),
    ("L3c_how_6", "how", "AnimatedStatsSlide", "Скорость <em>и путь</em>", "входят в ощущение", {"variant": "tech", "stats": [
        {"label": "Загрузка", "value": 6, "suffix": "сек", "color": A4, "icon": "lucide:timer", "start_time": 0},
        {"label": "Кнопка", "value": 1, "suffix": "шаг", "color": A1, "icon": "lucide:mouse-pointer-click", "start_time": 800},
        {"label": "Понятный путь", "value": 1, "suffix": "", "color": A2, "icon": "lucide:route", "start_time": 1600}]}),
    ("L3c_how_7", "how", "ComparisonTable", "Мёртвый <em>или живой</em>", "разница в деталях", {"variant": "tech", "headers": ["", "Мёртвый", "Живой"], "items": [
        {"id": "r1", "label": "Сток вместо фото", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Канцелярит", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Шумно и тесно", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Быстро и ясно", "values": [False, True], "start_time": 2400}]}),
    ("L3c_how_8", "how", "InfographicCards", "Что делает <em>живым</em>", "четыре вещи", {"variant": "tech", "items": [
        {"id": 1, "label": "Фото", "value": "Свои", "trend": "не сток", "color": A1, "icon": "heroicons:camera", "start_time": 0},
        {"id": 2, "label": "Текст", "value": "Живой", "trend": "без штампов", "color": A2, "icon": "heroicons:chat-bubble-left", "start_time": 800},
        {"id": 3, "label": "Ритм", "value": "Воздух", "trend": "порядок", "color": A3, "icon": "heroicons:sparkles", "start_time": 1600},
        {"id": 4, "label": "Скорость", "value": "Быстро", "trend": "и путь ясен", "color": A4, "icon": "heroicons:bolt", "start_time": 2400}]}),
    ("L3c_how_9", "how", "ProcessFunnel", "Путь <em>без квеста</em>", "от экрана до заявки", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Первый экран", "count": 100, "icon": "heroicons:eye", "color": A1, "start_time": 0},
        {"label": "Выбор дат", "count": 60, "icon": "heroicons:calendar-days", "color": A2, "start_time": 800},
        {"label": "Выбор домика", "count": 40, "icon": "heroicons:home", "color": A3, "start_time": 1600},
        {"label": "Телефон", "count": 30, "icon": "heroicons:phone", "color": A4, "start_time": 2400}]}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L3c_prj_1", "project", "AnimatedStatsSlide", "База <em>отдыха</em>", "сорок домиков", {"variant": "tech", "stats": [
        {"label": "Домиков", "value": 40, "suffix": "", "color": A2, "icon": "lucide:home", "start_time": 0},
        {"label": "Бюджет трафика", "value": 1500, "suffix": "€", "color": A1, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Заявок", "value": 7, "suffix": "", "color": A4, "icon": "lucide:inbox", "start_time": 1600}]}),
    ("L3c_prj_2", "project", "ReceiptCard", "", "", {"variant": "tech", "title": "БЮДЖЕТ НА ТРАФИК", "subtitle": "Google Ads", "currency": "€", "total_text": "ПОТРАЧЕНО", "footer_text": "ЗА МЕСЯЦ", "total_start_time": 2600, "items": [
        {"name": "Кампании", "price": 1000, "start_time": 300},
        {"name": "Ведение", "price": 300, "start_time": 1100},
        {"name": "Креативы", "price": 200, "start_time": 1900}]}),
    ("L3c_prj_3", "project", "InfographicCards", "Семь <em>заявок</em>", "что внутри", {"variant": "tech", "items": [
        {"id": 1, "label": "Всего", "value": "7", "trend": "за месяц", "color": A1, "icon": "heroicons:inbox", "start_time": 0},
        {"id": 2, "label": "«Шашлык»", "value": "5", "trend": "не по делу", "color": A4, "icon": "heroicons:fire", "start_time": 800},
        {"id": 3, "label": "Целевые", "value": "2", "trend": "брони", "color": A2, "icon": "heroicons:check-badge", "start_time": 1600},
        {"id": 4, "label": "Сайт", "value": "Свежий", "trend": "но безликий", "color": A3, "icon": "heroicons:globe-alt", "start_time": 2400}]}),
    ("L3c_prj_4", "project", "BrowserMockup", "Свежий, но <em>безликий</em>", "сток и миссия", {"variant": "tech", "items": [
        {"id": "b1", "url": "ozero-resort.com", "type": "html", "content": BAD_SITE_HTML, "scroll": False, "image_position": "top", "start_time": 0}]}),
    ("L3c_prj_5", "project", "PremiumChecklist", "Что мешало <em>доверять</em>", "на главной", {"variant": "tech", "items": [
        {"label": "Баннер с озером", "desc": "стоковое фото", "icon": "heroicons:photo", "color": "brand-blue", "start_time": 0},
        {"label": "История и миссия", "desc": "текст вместо оффера", "icon": "heroicons:document-text", "color": "brand-amber", "start_time": 800},
        {"label": "Форма в подвале", "desc": "5 полей с индексом", "icon": "heroicons:inbox", "color": "brand-green", "start_time": 1600}]}),
    ("L3c_prj_6", "project", "ArchitectureDiagram", "Переписал <em>ощущение</em>", "новая логика", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Первый экран", "subtitle": "даты · домик · цена", "icon": "lucide:eye", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["pick"]},
        {"id": "pick", "title": "Выбор", "subtitle": "даты и домик", "icon": "lucide:calendar", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["phone"]},
        {"id": "phone", "title": "Телефон", "subtitle": "один шаг", "icon": "lucide:phone", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["push"]},
        {"id": "push", "title": "Пуш", "subtitle": "менеджеру сразу", "icon": "lucide:bell", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L3c_prj_7", "project", "StatsBarChart", "Было <em>7</em>", "стало 42", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Было 7", "subtitle": "стало 42", "data": [
        {"label": "Было", "value": 7, "start_time": 0},
        {"label": "Нед 1", "value": 9, "start_time": 800},
        {"label": "Нед 2", "value": 14, "start_time": 1600},
        {"label": "Итог", "value": 42, "highlight": True, "start_time": 2400}]}),
    ("L3c_prj_8", "project", "AnimatedStatsSlide", "Результат <em>месяца</em>", "тот же бюджет", {"variant": "tech", "stats": [
        {"label": "Целевые заявки", "value": 42, "suffix": "", "color": A2, "icon": "lucide:inbox", "start_time": 0},
        {"label": "Стоимость лида", "value": 36, "suffix": "€", "color": A1, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Бюджет", "value": 1500, "suffix": "€", "color": A3, "icon": "lucide:wallet", "start_time": 1600}]}),
    ("L3c_prj_9", "project", "ChatMockupSlide", "Пуш <em>менеджеру</em>", "в ту же секунду", {"variant": "tech", "bot_name": "Пуш", "bot_subtitle": "новая бронь", "bot_avatar": "N", "messages": [
        {"role": "assistant", "text": "Бронь: 12–14 июля, домик «Озеро», €180/сутки.", "start_time": 0},
        {"role": "assistant", "text": "Телефон: +49 … Уточнять не нужно.", "start_time": 1500}]}),
    ("L3c_prj_10", "project", "CrmCardSlide", "Карточка <em>брони</em>", "всё собрано", {"variant": "tech", "customer": {"name": "Семья К.", "avatar_text": "К", "id_text": "ID: #4210", "status": "горячая"},
        "fields": [
            {"label": "ДАТЫ", "value": "12–14 июл", "field_icon": "heroicons:calendar-days", "field_color": "brand-green", "start_time": 300},
            {"label": "ДОМИК", "value": "Озеро, №7", "field_icon": "heroicons:home", "field_color": "brand-blue", "start_time": 1100},
            {"label": "СУММА", "value": "€540", "field_icon": "heroicons:banknotes", "field_color": "brand-amber", "start_time": 1900},
            {"label": "КАНАЛ", "value": "Сайт", "field_icon": "heroicons:globe-alt", "field_color": "brand-blue", "start_time": 2700}],
        "buttons": [
            {"text": "Подтвердить", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Позвонить", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L3c_prj_11", "project", "WaterfallChart", "7 → <em>42</em>", "без смены рекламы", {"variant": "tech",
        "start_label": "Было", "start_value": 7,
        "steps": [{"label": "Живой сайт", "delta": 35, "kind": "pos"}],
        "end_label": "Стало", "value_prefix": "", "value_suffix": ""}),
    ("L3c_prj_12", "project", "KpiDashboard", "Результат <em>кейса</em>", "метрики", {"variant": "tech", "title": "", "subtitle": "", "metrics": [
        {"id": "k1", "label": "Заявки", "value": "42", "unit": "/мес", "trend": "+500%", "color": "var(--color-success)", "icon": "heroicons:inbox", "sparkline": [7, 9, 14, 20, 30, 38, 42], "start_time": 0},
        {"id": "k2", "label": "Стоимость лида", "value": "36", "unit": "€", "trend": "-70%", "color": "var(--color-secondary)", "icon": "heroicons:banknotes", "sparkline": [214, 180, 120, 80, 55, 40, 36], "start_time": 900},
        {"id": "k3", "label": "Конверсия", "value": "4.2", "unit": "%", "trend": "+3.5 пт", "color": "var(--color-accent)", "icon": "heroicons:arrow-trending-up", "sparkline": [0.7, 0.9, 1.4, 2.1, 2.9, 3.6, 4.2], "start_time": 1800},
        {"id": "k4", "label": "Доля броней", "value": "48", "unit": "%", "trend": "+31 пт", "color": "var(--color-warning)", "icon": "heroicons:home", "sparkline": [17, 22, 28, 34, 39, 44, 48], "start_time": 2700}]}),
    ("L3c_prj_13", "project", "PremiumChecklist", "Что убрал <em>и добавил</em>", "по итогу", {"variant": "tech", "items": [
        {"label": "Убрал сток", "desc": "настоящие фото домиков", "icon": "heroicons:camera", "color": "brand-blue", "start_time": 0},
        {"label": "Убрал мёртвую форму", "desc": "5 полей с индексом", "icon": "heroicons:x-circle", "color": "brand-amber", "start_time": 800},
        {"label": "Добавил выбор", "desc": "даты, домик, цена", "icon": "heroicons:calendar-days", "color": "brand-green", "start_time": 1600}]}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L3c_whr_1", "where", "InfographicCards", "Что <em>не спасёт</em>", "по отдельности", {"variant": "tech", "items": [
        {"id": 1, "label": "Вид без оффера", "value": "Нет", "trend": "картинка не вытянет", "color": A4, "icon": "heroicons:photo", "start_time": 0},
        {"id": 2, "label": "Сток вместо смысла", "value": "Нет", "trend": "читается как обман", "color": A3, "icon": "heroicons:face-smile", "start_time": 800},
        {"id": 3, "label": "Медленная загрузка", "value": "Нет", "trend": "до красоты дожить", "color": A2, "icon": "heroicons:clock", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Вместе", "trend": "вид + оффер + скорость", "color": A1, "icon": "heroicons:check-badge", "start_time": 2400}]}),
    ("L3c_whr_2", "where", "PremiumChecklist", "Где ломается", "честно", {"variant": "tech", "items": [
        {"label": "Красота без оффера", "desc": "непонятно, что продаёшь", "icon": "heroicons:eye", "color": "brand-blue", "start_time": 0},
        {"label": "Сток без конкретики", "desc": "глянец = недоверие", "icon": "heroicons:camera", "color": "brand-amber", "start_time": 800},
        {"label": "Долгая загрузка", "desc": "клиент не доживает", "icon": "heroicons:clock", "color": "brand-green", "start_time": 1600}]}),
    ("L3c_whr_3", "where", "ComparisonTable", "Вид <em>и смысл</em>", "только вместе", {"variant": "tech", "headers": ["", "По отдельности", "Вместе"], "items": [
        {"id": "r1", "label": "Доверие", "values": [False, True], "start_time": 0},
        {"id": "r2", "label": "Понятный оффер", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Скорость", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Заявка", "values": [False, True], "start_time": 2400}]}),
    ("L3c_whr_4", "where", "AnimatedStatsSlide", "Работает <em>вместе</em>", "три условия", {"variant": "tech", "stats": [
        {"label": "Вид", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:eye", "start_time": 0},
        {"label": "Оффер", "value": 100, "suffix": "%", "color": A1, "icon": "lucide:target", "start_time": 800},
        {"label": "Скорость", "value": 100, "suffix": "%", "color": A3, "icon": "lucide:bolt", "start_time": 1600}]}),

    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L3c_cnc_1", "conclusion", "DefinitionBlock", "Доверие", "современный вид", {"variant": "tech",
        "term": "Современный вид",
        "definition": "Ощущение, что за сайтом стоят живые люди, которым можно доверить деньги.",
        "examples": [
            {"id": "d1", "text": "Живые фото и человеческий язык.", "start_time": 1000},
            {"id": "d2", "text": "Быстро и понятно, куда нажать.", "start_time": 2000}],
        "related_terms": ["Доверие", "Оффер", "Скорость"]}),
    ("L3c_cnc_2", "conclusion", "QuoteCard", "Одна <em>мысль</em>", "забрать с собой", {"variant": "tech",
        "quote": "Доверие видно за секунду. Это и есть современный вид.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод"}),

    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L3c_cta_1", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
        print(f"  OK {sid:<11} {starts[sid]:>7.0f}ms  {comp}")
        ok += 1
    normalize_bgm_track(PRES_ID)
    print(f"\nDone: {ok}/{len(SLIDES)}. Failed: {fail}")
    print(f"Preview: http://localhost:5175/p/{PRES_ID}")


if __name__ == "__main__":
    main()
