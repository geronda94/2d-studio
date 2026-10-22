#!/usr/bin/env python3
"""Слайды для Длинное_04 «Как хаос в данных убивает продажи» (presentation 75), 7 блоков.

Запуск с хоста: python3 scripts/build_long04_slides.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
PRES_ID = 75
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]
A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L4_tez_1", "tezis", "InfographicCards", "Клиент на <em>$50 000</em>", "в личном телефоне", {"variant": "tech", "items": [
        {"id": 1, "label": "Клиент", "value": "$50 000", "trend": "ключевой", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "Канал", "value": "Телефон", "trend": "личный", "color": A4, "icon": "heroicons:device-phone-mobile", "start_time": 800},
        {"id": 3, "label": "Внезапно", "value": "Больничный", "trend": "менеджер выпал", "color": A3, "icon": "heroicons:clock", "start_time": 1600},
        {"id": 4, "label": "Знает детали", "value": "Только он", "trend": "офис не в курсе", "color": A2, "icon": "heroicons:user", "start_time": 2400}]}),
    ("L4_tez_2", "tezis", "AnimatedStatsSlide", "Отдел <em>замирает</em>", "никто не знает деталей", {"variant": "tech", "stats": [
        {"label": "Клиент", "value": 50000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Знает детали", "value": 1, "suffix": "человек", "color": A4, "icon": "heroicons:user", "start_time": 800},
        {"label": "Дней молчания", "value": 5, "suffix": "", "color": A1, "icon": "heroicons:clock", "start_time": 1600}]}),
    ("L4_tez_3", "tezis", "ComparisonTable", "Сделка <em>у компании</em>", "или у менеджера", {"variant": "tech", "headers": ["", "У компании", "У менеджера"], "items": [
        {"id": "r1", "label": "Доступ к истории", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Скидки и обещания", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Договоры и счета", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Риск ухода с клиентом", "values": [False, True], "start_time": 2400}]}),
    ("L4_tez_4", "tezis", "MetricScales", "База <em>не твоя</em>", "фактически", {"variant": "tech", "title": "База не твоя", "subtitle": "фактически", "metrics": [
        {"id": 1, "label": "Доступ компании", "percentage": 10, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Зависимость от менеджера", "percentage": 100, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Данные в системе", "percentage": 5, "color": G2c, "start_time": 1600}]}),
    ("L4_tez_5", "tezis", "QuoteCard", "Голос <em>клиента</em>", "пока менеджера нет", {"variant": "tech",
        "quote": "С ним договорились напрямую. Теперь его нет — и меня как будто тоже.",
        "author": "Клиент", "author_title": "звонит в офис", "source": "никто не может ответить"}),
    ("L4_tez_6", "tezis", "PremiumChecklist", "Что <em>теряется</em>", "вместе с телефоном", {"variant": "tech", "items": [
        {"label": "История переписки", "desc": "вся коммуникация", "icon": "heroicons:chat-bubble-left", "color": "brand-blue", "start_time": 0},
        {"label": "Обещанные скидки", "desc": "никто не помнит", "icon": "heroicons:tag", "color": "brand-amber", "start_time": 800},
        {"label": "Договоры и счета", "desc": "клиент не может оплатить", "icon": "heroicons:document-text", "color": "brand-green", "start_time": 1600}]}),
    ("L4_tez_7", "tezis", "ArchitectureDiagram", "Сделка <em>в телефоне</em>", "и уносится с ним", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клиент", "subtitle": "ключевой", "icon": "lucide:user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["phone"]},
        {"id": "phone", "title": "Личный телефон", "subtitle": "менеджера", "icon": "lucide:smartphone", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["sick"]},
        {"id": "sick", "title": "Больничный", "subtitle": "внезапно", "icon": "lucide:bed", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["dead"]},
        {"id": "dead", "title": "Отдел без ответа", "subtitle": "деталей нет", "icon": "lucide:phone-off", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L4_tez_8", "tezis", "AnimatedStatsSlide", "Ты купил <em>CRM</em>", "и оцифровал хаос", {"variant": "tech", "stats": [
        {"label": "Подписка", "value": 500, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Система пустая", "value": 3, "suffix": "мес", "color": A4, "icon": "heroicons:clock", "start_time": 800},
        {"label": "Хаос оцифрован", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:document-duplicate", "start_time": 1600}]}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L4_hyp_1", "hype", "QuoteCard", "Обещание <em>вендора</em>", "красивая картинка", {"variant": "tech",
        "quote": "Купите подписку. Наша система сама начнёт двигать ваши сделки.",
        "author": "Вендор", "author_title": "продаёт софт", "source": "обещание на сайте"}),
    ("L4_hyp_2", "hype", "ComparisonTable", "Ожидание <em>и реальность</em>", "через три месяца", {"variant": "tech", "headers": ["", "Ожидание", "Реальность"], "items": [
        {"id": "r1", "label": "Система сама продаёт", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Хаос переехал в облако", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Данные заполнены", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "В системе пусто", "values": [False, True], "start_time": 2400}]}),
    ("L4_hyp_3", "hype", "AnimatedStatsSlide", "Через <em>три месяца</em>", "заходишь — пусто", {"variant": "tech", "stats": [
        {"label": "Оплачено лицензий", "value": 12, "suffix": "мес", "color": A1, "icon": "heroicons:credit-card", "start_time": 0},
        {"label": "Настроили дашбордов", "value": 5, "suffix": "", "color": A2, "icon": "heroicons:chart-bar", "start_time": 800},
        {"label": "Заполненность системы", "value": 5, "suffix": "%", "color": A4, "icon": "heroicons:circle-stack", "start_time": 1600}]}),
    ("L4_hyp_4", "hype", "PremiumChecklist", "Почему <em>бегут</em>", "обратно в мессенджеры", {"variant": "tech", "items": [
        {"label": "Программа неудобная", "desc": "много лишнего", "icon": "heroicons:device-phone-mobile", "color": "brand-blue", "start_time": 0},
        {"label": "Прайс в WhatsApp", "desc": "привычнее и быстрее", "icon": "heroicons:chat-bubble-left", "color": "brand-amber", "start_time": 800},
        {"label": "Ты им уступаешь", "desc": "хаос продолжается", "icon": "heroicons:hand-thumb-down", "color": "brand-green", "start_time": 1600}]}),
    ("L4_hyp_5", "hype", "ArchitectureDiagram", "Хаос <em>переехал</em>", "в облако", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Личный WhatsApp", "subtitle": "прайс клиенту", "icon": "lucide:message-circle", "color": "chart-4", "start_time": 0, "is_main": False, "to": ["crm"]},
        {"id": "crm", "title": "CRM", "subtitle": "не заполняется", "icon": "lucide:database", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["hand"]},
        {"id": "hand", "title": "Передача сделки", "subtitle": "данных нет", "icon": "lucide:file-x", "color": "chart-6", "start_time": 1600, "is_main": False, "to": ["gone"]},
        {"id": "gone", "title": "Сделка потеряна", "subtitle": "клиент ушёл", "icon": "lucide:user-x", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L4_hyp_6", "hype", "DefinitionBlock", "Автоматизированный <em>хаос</em>", "термин", {"variant": "tech",
        "term": "Автоматизированный хаос",
        "definition": "Дорогая система, которая не наводит порядок, а только ускоряет ваш бардак.",
        "examples": [
            {"id": "d1", "text": "Импровизация каждого менеджера ускоряется софтом.", "start_time": 1000},
            {"id": "d2", "text": "Счёт $500 в месяц, порядка — нет.", "start_time": 2000}],
        "related_terms": ["CRM", "Процесс", "Дисциплина"]}),
    ("L4_hyp_7", "hype", "MetricScales", "Софт <em>бессилен</em>", "перед бардаком", {"variant": "tech", "title": "Софт бессилен", "subtitle": "перед бардаком", "metrics": [
        {"id": 1, "label": "Порядок в процессе", "percentage": 10, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Импровизация каждого", "percentage": 100, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Скорость хаоса", "percentage": 100, "color": G2c, "start_time": 1600}]}),
    ("L4_hyp_8", "hype", "QuoteCard", "Итог <em>хаоса</em>", "одна мысль", {"variant": "tech",
        "quote": "Систематизировать хаос невозможно — он только ускоряется.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод по хайпу"}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L4_how_1", "how", "QuoteCard", "Один <em>вопрос</em>", "до автоматизации", {"variant": "tech",
        "quote": "Какова истинная цель? Отчёты для галочки или исключить потери сделок при увольнении?",
        "author": "Игорь", "author_title": "IT2B", "source": "первый вопрос клиенту"}),
    ("L4_how_2", "how", "ComparisonTable", "Две <em>разные</em> задачи", "требуют разного подхода", {"variant": "tech", "headers": ["", "Отчёты для галочки", "Чтобы база не уходила"], "items": [
        {"id": "r1", "label": "Подходит коробка", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Нужна перестройка процесса", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Решает потерю сделок", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Это разные проекты", "values": [True, True], "start_time": 2400}]}),
    ("L4_how_3", "how", "DefinitionBlock", "Истинная <em>цель</em>", "термин", {"variant": "tech",
        "term": "Истинная цель",
        "definition": "Ответ на вопрос, зачем тебе система: красивые отчёты или сохранность клиентской базы.",
        "examples": [
            {"id": "d1", "text": "Отчёты для галочки — одна задача.", "start_time": 1000},
            {"id": "d2", "text": "База как актив — совсем другая.", "start_time": 2000}],
        "related_terms": ["Цель", "Актив", "Процесс"]}),
    ("L4_how_4", "how", "PremiumChecklist", "Два <em>критерия</em>", "смотрю только на них", {"variant": "tech", "items": [
        {"label": "Продажу описать шагами", "desc": "на листе бумаги", "icon": "heroicons:list-bullet", "color": "brand-blue", "start_time": 0},
        {"label": "Где хранится специфика", "desc": "истинное место сделки", "icon": "heroicons:map-pin", "color": "brand-amber", "start_time": 800}]}),
    ("L4_how_5", "how", "ProcessFunnel", "Путь <em>сделки</em>", "описать шагами", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Заявка", "count": 100, "icon": "heroicons:inbox", "color": A1, "start_time": 0},
        {"label": "Квалификация", "count": 70, "icon": "heroicons:chat-bubble-left", "color": A2, "start_time": 800},
        {"label": "Смета", "count": 45, "icon": "heroicons:document-text", "color": A3, "start_time": 1600},
        {"label": "Сделка", "count": 25, "icon": "heroicons:check-badge", "color": A4, "start_time": 2400}]}),
    ("L4_how_6", "how", "ArchitectureDiagram", "Двое <em>продавцов</em>", "под одной крышей", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "sen", "title": "Старший", "subtitle": "долгие созвоны", "icon": "lucide:phone", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["crm2"]},
        {"id": "jun", "title": "Младший", "subtitle": "сметы в мессенджер", "icon": "lucide:file-text", "color": "chart-3", "start_time": 800, "is_main": False, "to": ["crm2"]},
        {"id": "crm2", "title": "Одна CRM", "subtitle": "не объединит", "icon": "lucide:database", "color": "chart-5", "start_time": 1600, "is_main": True, "to": ["order"]},
        {"id": "order", "title": "Сначала порядок", "subtitle": "в процессе", "icon": "lucide:route", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L4_how_7", "how", "AnimatedStatsSlide", "Разные <em>процессы</em>", "в одном отделе", {"variant": "tech", "stats": [
        {"label": "Созвоны с клиентом", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:phone", "start_time": 0},
        {"label": "Сметы в мессенджер", "value": 100, "suffix": "%", "color": A4, "icon": "lucide:file-text", "start_time": 800},
        {"label": "Независимых продавцов", "value": 2, "suffix": "", "color": A1, "icon": "lucide:users", "start_time": 1600}]}),
    ("L4_how_8", "how", "ComparisonTable", "Простая <em>продажа</em>", "или сложная", {"variant": "tech", "headers": ["", "Консультации", "Оборудование"], "items": [
        {"id": "r1", "label": "Пара стандартных полей", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Десятки чертежей", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Стандартная CRM подойдёт", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Нужна своя структура", "values": [False, True], "start_time": 2400}]}),
    ("L4_how_9", "how", "PremiumChecklist", "Что <em>ломает</em> внедрение", "в сложной продаже", {"variant": "tech", "items": [
        {"label": "Стандартные поля", "desc": "для сложного товара", "icon": "heroicons:clipboard-document-list", "color": "brand-blue", "start_time": 0},
        {"label": "Игнор специфики", "desc": "чертежи и логистика", "icon": "heroicons:map-pin", "color": "brand-amber", "start_time": 800},
        {"label": "Саботаж людей", "desc": "и они будут правы", "icon": "heroicons:x-circle", "color": "brand-green", "start_time": 1600}]}),
    ("L4_how_10", "how", "QuoteCard", "Про <em>саботаж</em>", "это нормально", {"variant": "tech",
        "quote": "Запихивать специфику в стандартные поля бессмысленно — люди устроят саботаж, и будут правы.",
        "author": "Игорь", "author_title": "IT2B", "source": "второй критерий"}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L4_prj_1", "project", "AnimatedStatsSlide", "Оптовый <em>поставщик</em>", "строительной техники", {"variant": "tech", "stats": [
        {"label": "Зависло сделок", "value": 80000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Клиентов ждут", "value": 12, "suffix": "", "color": A4, "icon": "heroicons:users", "start_time": 800},
        {"label": "Простой", "value": 14, "suffix": "дней", "color": A1, "icon": "heroicons:clock", "start_time": 1600}]}),
    ("L4_prj_2", "project", "QuoteCard", "Запрос <em>клиента</em>", "дословно", {"variant": "tech",
        "quote": "Мы купили систему, но в ней никто не работает. Сделайте хоть что-нибудь.",
        "author": "Клиент", "author_title": "оптовый поставщик", "source": "запрос на старте"}),
    ("L4_prj_3", "project", "CrmCardSlide", "Кейс: <em>стройтехника</em>", "всё висело на одном", {"variant": "tech", "customer": {"name": "Оптовик, стройтехника", "avatar_text": "Э", "id_text": "ID: #case-04", "status": "простой"},
        "fields": [
            {"label": "СИСТЕМА", "value": "Куплена", "field_icon": "heroicons:rectangle-stack", "field_color": "brand-blue", "start_time": 300},
            {"label": "ЗАПОЛНЕНО", "value": "Никем", "field_icon": "heroicons:document-text", "field_color": "brand-amber", "start_time": 1100},
            {"label": "ЗАВИСЛО", "value": "$80 000", "field_icon": "heroicons:banknotes", "field_color": "brand-green", "start_time": 1900},
            {"label": "ДАННЫЕ", "value": "WhatsApp", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Снести настройки", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Привязать WhatsApp", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L4_prj_4", "project", "ArchitectureDiagram", "Вся связь <em>в WhatsApp</em>", "у менеджера", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клиенты", "subtitle": "хотят оплатить", "icon": "lucide:users", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["wa"]},
        {"id": "wa", "title": "Личный WhatsApp", "subtitle": "менеджера", "icon": "lucide:smartphone", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["sick2"]},
        {"id": "sick2", "title": "Больничный", "subtitle": "менеджер выпал", "icon": "lucide:bed", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["frozen"]},
        {"id": "frozen", "title": "Сделки заморожены", "subtitle": "договоры не найти", "icon": "lucide:ban", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L4_prj_5", "project", "ReceiptCard", "", "", {"variant": "tech", "title": "ПОТЕРИ", "subtitle": "поставщик техники", "currency": "$", "total_text": "ЗАВИСЛО", "footer_text": "ПОКА МЕНЕДЖЕР БОЛЕЛ", "total_start_time": 2600, "items": [
        {"name": "Экскаваторы", "price": 45000, "start_time": 300},
        {"name": "Договоры", "price": 20000, "start_time": 1100},
        {"name": "Счета", "price": 15000, "start_time": 1900}]}),
    ("L4_prj_6", "project", "PremiumChecklist", "Причина <em>простоя</em>", "честно", {"variant": "tech", "items": [
        {"label": "Договоры в WhatsApp", "desc": "личный телефон", "icon": "heroicons:chat-bubble-left", "color": "brand-blue", "start_time": 0},
        {"label": "Никто не знает деталей", "desc": "только менеджер", "icon": "heroicons:eye-slash", "color": "brand-amber", "start_time": 800},
        {"label": "Нет доступа к истории", "desc": "офис бессилен", "icon": "heroicons:key", "color": "brand-green", "start_time": 1600}]}),
    ("L4_prj_7", "project", "InfographicCards", "Что я <em>сделал</em>", "четыре шага", {"variant": "tech", "items": [
        {"id": 1, "label": "Снёс настройки", "value": "Всё", "trend": "до бизнес-сути", "color": A1, "icon": "heroicons:trash", "start_time": 0},
        {"id": 2, "label": "Перестроил", "value": "Архитектуру", "trend": "под отгрузку", "color": A2, "icon": "heroicons:wrench-screwdriver", "start_time": 800},
        {"id": 3, "label": "Убрал мусор", "value": "80%", "trend": "визуальный шум", "color": A3, "icon": "heroicons:sparkles", "start_time": 1600},
        {"id": 4, "label": "Привязал", "value": "WhatsApp", "trend": "к сделке", "color": A4, "icon": "heroicons:link", "start_time": 2400}]}),
    ("L4_prj_8", "project", "MetricScales", "Мусор <em>убрал</em>", "оставил суть", {"variant": "tech", "title": "Мусор убрал", "subtitle": "оставил суть", "metrics": [
        {"id": 1, "label": "Визуальный мусор", "percentage": 80, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Оставил нужные поля", "percentage": 20, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Параметры для отгрузки", "percentage": 100, "color": G1c, "start_time": 1600}]}),
    ("L4_prj_9", "project", "ArchitectureDiagram", "WhatsApp API <em>к сделке</em>", "унести нельзя", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "WhatsApp API", "subtitle": "корпоративный", "icon": "lucide:message-circle", "color": "chart-2", "start_time": 0, "is_main": False, "to": ["deal"]},
        {"id": "deal", "title": "Сделка в CRM", "subtitle": "жёстко привязан", "icon": "lucide:database", "color": "chart-1", "start_time": 800, "is_main": True, "to": ["hist"]},
        {"id": "hist", "title": "История переписки", "subtitle": "видна офису", "icon": "lucide:history", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["lock"]},
        {"id": "lock", "title": "Унести нельзя", "subtitle": "данные у компании", "icon": "lucide:lock", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L4_prj_10", "project", "AnimatedStatsSlide", "Разработка <em>20%</em>", "дисциплина 80%", {"variant": "tech", "stats": [
        {"label": "Разработка", "value": 20, "suffix": "%", "color": A1, "icon": "lucide:code", "start_time": 0},
        {"label": "Дисциплина", "value": 80, "suffix": "%", "color": A3, "icon": "lucide:shield-check", "start_time": 800},
        {"label": "Жёсткое правило", "value": 1, "suffix": "", "color": A2, "icon": "lucide:list-checks", "start_time": 1600}]}),
    ("L4_prj_11", "project", "QuoteCard", "Сказал <em>в глаза</em>", "жёстко", {"variant": "tech",
        "quote": "Если ты хоть раз примешь отчёт от менеджера в Excel — система умрёт через месяц.",
        "author": "Игорь", "author_title": "IT2B", "source": "правило внедрения"}),
    ("L4_prj_12", "project", "PremiumChecklist", "Жёсткое <em>правило</em>", "без исключений", {"variant": "tech", "items": [
        {"label": "Нет сделки в системе", "desc": "её не существует", "icon": "heroicons:document-text", "color": "brand-blue", "start_time": 0},
        {"label": "Комиссия не платится", "desc": "жёсткая привязка", "icon": "heroicons:banknotes", "color": "brand-amber", "start_time": 800},
        {"label": "Иначе система умрёт", "desc": "через месяц", "icon": "heroicons:exclamation-triangle", "color": "brand-green", "start_time": 1600}]}),
    ("L4_prj_13", "project", "AnimatedStatsSlide", "Результат <em>за 2 месяца</em>", "база стала активом", {"variant": "tech", "stats": [
        {"label": "Месяцев до результата", "value": 2, "suffix": "", "color": A2, "icon": "heroicons:calendar-days", "start_time": 0},
        {"label": "Видит историю", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:eye", "start_time": 800},
        {"label": "Комиссия по правилам", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:banknotes", "start_time": 1600}]}),
    ("L4_prj_14", "project", "ComparisonTable", "База стала <em>активом</em>", "было и стало", {"variant": "tech", "headers": ["", "Было", "Стало"], "items": [
        {"id": "r1", "label": "Данные у менеджера", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Данные у компании", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Сделка передаётся", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Зависимость от человека", "values": [True, False], "start_time": 2400}]}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L4_whr_1", "where", "PremiumChecklist", "Когда <em>не подойдёт</em>", "честно", {"variant": "tech", "items": [
        {"label": "Стартап", "desc": "модель меняется часто", "icon": "heroicons:rocket-launch", "color": "brand-blue", "start_time": 0},
        {"label": "Нужна гибкость", "desc": "жёсткая база парализует", "icon": "heroicons:arrow-path", "color": "brand-amber", "start_time": 800},
        {"label": "Нет контроля правил", "desc": "чудо не сработает", "icon": "heroicons:hand-raised", "color": "brand-green", "start_time": 1600}]}),
    ("L4_whr_2", "where", "ComparisonTable", "Стартап <em>или</em> зрелый", "кому что", {"variant": "tech", "headers": ["", "Стартап", "Зрелый бизнес"], "items": [
        {"id": "r1", "label": "Меняет модель каждую неделю", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Нужна жёсткая база", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Гибкость важнее порядка", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Дисциплина решает", "values": [False, True], "start_time": 2400}]}),
    ("L4_whr_3", "where", "AnimatedStatsSlide", "Без <em>контроля</em>", "не работает", {"variant": "tech", "stats": [
        {"label": "Готовность контролировать", "value": 100, "suffix": "%", "color": A3, "icon": "lucide:shield-check", "start_time": 0},
        {"label": "Гибкость стартапу", "value": 100, "suffix": "%", "color": A1, "icon": "lucide:arrow-left-right", "start_time": 800},
        {"label": "Жёстких правил", "value": 2, "suffix": "", "color": A2, "icon": "lucide:list-checks", "start_time": 1600}]}),
    ("L4_whr_4", "where", "QuoteCard", "Честно", "без иллюзий", {"variant": "tech",
        "quote": "Если ты сам не готов контролировать соблюдение правил — надеяться на чудо бессмысленно.",
        "author": "Игорь", "author_title": "IT2B", "source": "граница применимости"}),
    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L4_cnc_1", "conclusion", "QuoteCard", "Главное <em>правило</em>", "забрать с собой", {"variant": "tech",
        "quote": "Если база зависит от памяти отдельных людей — масштаб бизнеса заблокирован навсегда.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод"}),
    ("L4_cnc_2", "conclusion", "DefinitionBlock", "База — <em>актив</em>", "термин", {"variant": "tech",
        "term": "Актив компании",
        "definition": "Данные, которые принадлежат бизнесу, а не памяти отдельного сотрудника.",
        "examples": [
            {"id": "d1", "text": "Сделку открывает любой менеджер.", "start_time": 1000},
            {"id": "d2", "text": "Уход человека ничего не рушит.", "start_time": 2000}],
        "related_terms": ["Данные", "Контроль", "Масштаб"]}),
    ("L4_cnc_3", "conclusion", "QuoteCard", "Одна <em>мысль</em>", "на выход", {"variant": "tech",
        "quote": "Автоматизация хаоса даёт один результат: очень дорогой автоматизированный хаос.",
        "author": "Игорь", "author_title": "IT2B", "source": "финал"}),
    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L4_cta_1", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
