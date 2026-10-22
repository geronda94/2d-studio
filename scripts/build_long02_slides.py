#!/usr/bin/env python3
"""Слайды для широкоформатного Длинное_02 (presentation 38), 7 блоков.

Запуск с хоста: python3 scripts/build_long02_slides.py
Тайминги распределяются по секциям пропорционально (шаг 2–8с), BGM на `bgm` до EndMarker.
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401  (патчит requests: авторизация + CSRF)
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
PRES_ID = 38
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]

A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L_tez_1", "tezis", "InfographicCards", "Что обещали <em>заменить</em>", "а что вышло", {"variant": "tech", "items": [
        {"id": 1, "label": "Обещали", "value": "Заменит", "trend": "весь отдел", "color": A1, "icon": "heroicons:user-group", "start_time": 0},
        {"id": 2, "label": "Обещали", "value": "Сам", "trend": "дожимает", "color": A4, "icon": "heroicons:fire", "start_time": 800},
        {"id": 3, "label": "Обещали", "value": "24/7", "trend": "без выходных", "color": A3, "icon": "heroicons:clock", "start_time": 1600},
        {"id": 4, "label": "Через месяц", "value": "Хаос", "trend": "конфликтов больше", "color": A2, "icon": "heroicons:exclamation-triangle", "start_time": 2400}]}),
    ("L_tez_2", "tezis", "ComparisonTable", "Обещали и <em>по факту</em>", "без маркетинга", {"variant": "tech", "headers": ["", "Обещали", "По факту"], "items": [
        {"id": "r1", "label": "Прайс и сроки", "values": [True, True], "start_time": 0},
        {"id": "r2", "label": "Скидки", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Спецификация", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "«Сможете иначе»", "values": [True, False], "start_time": 2400}]}),
    ("L_tez_3", "tezis", "MetricScales", "Что реально <em>умеет</em>", "без хайпа", {"variant": "tech", "title": "Что реально умеет", "subtitle": "без хайпа", "metrics": [
        {"id": 1, "label": "Прайс", "percentage": 100, "color": G1c, "start_time": 0},
        {"id": 2, "label": "Сроки", "percentage": 100, "color": G1c, "start_time": 800},
        {"id": 3, "label": "Скидки", "percentage": 15, "color": G2c, "start_time": 1600},
        {"id": 4, "label": "Спецификация", "percentage": 10, "color": G3c, "start_time": 2400}]}),
    ("L_tez_4", "tezis", "AnimatedStatsSlide", "Через месяц <em>итог</em>", "отдел на месте", {"variant": "tech", "stats": [
        {"label": "Отдел на месте", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:users", "start_time": 0},
        {"label": "Конфликтов стало", "value": 3, "suffix": "", "color": A4, "icon": "lucide:alert-triangle", "start_time": 800},
        {"label": "Условий для старта", "value": 3, "suffix": "шт", "color": A1, "icon": "lucide:list-checks", "start_time": 1600}]}),
    ("L_tez_5", "tezis", "PremiumChecklist", "Три условия <em>заранее</em>", "без них не начинаю", {"variant": "tech", "items": [
        {"label": "Право говорить", "desc": "строго по базе", "icon": "heroicons:lock-closed", "color": "brand-blue", "start_time": 0},
        {"label": "Граница с человеком", "desc": "сложное — человеку", "icon": "heroicons:user-group", "color": "brand-amber", "start_time": 800},
        {"label": "Данные", "desc": "всё в CRM, не в чате", "icon": "heroicons:circle-stack", "color": "brand-green", "start_time": 1600}]}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L_hyp_1", "hype", "ChatMockupSlide", "Бот <em>обещает</em> скидку", "которой нет", {"variant": "tech", "bot_name": "AI-агент", "bot_subtitle": "отдел продаж", "bot_avatar": "AI", "messages": [
        {"role": "user", "text": "Нужна скидка на партию серверов. $80 000.", "start_time": 0},
        {"role": "assistant", "text": "Сделаем скидку 15% и бесплатную доставку!", "start_time": 1500},
        {"role": "user", "text": "Отлично, фиксирую.", "start_time": 3000}]}),
    ("L_hyp_2", "hype", "ReceiptCard", "", "", {"variant": "tech", "title": "ЗАКАЗ НА $80 000", "subtitle": "серверы", "currency": "$", "total_text": "ОБЕЩАНО", "footer_text": "ЧЕГО НЕТ В ПРАЙСЕ", "total_start_time": 2600, "items": [
        {"name": "Скидка 15%", "price": 12000, "start_time": 300},
        {"name": "Бесплатная доставка", "price": 3000, "start_time": 1100},
        {"name": "Скидка партнёра", "price": 5000, "start_time": 1900}]}),
    ("L_hyp_3", "hype", "ArchitectureDiagram", "Откуда <em>фантазия</em>", "нет опоры на базу", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клиент", "subtitle": "$80 000", "icon": "lucide:message-circle", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core"]},
        {"id": "core", "title": "ИИ-агент", "subtitle": "нет в базе", "icon": "lucide:cpu", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["out"]},
        {"id": "out", "title": "Фантазия", "subtitle": "скидка 15%", "icon": "lucide:sparkles", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["con"]},
        {"id": "con", "title": "Конфликт", "subtitle": "с клиентом", "icon": "lucide:alert-triangle", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L_hyp_4", "hype", "AnimatedStatsSlide", "Цифры <em>обещаний</em>", "из воздуха", {"variant": "tech", "stats": [
        {"label": "Скидка", "value": 15, "suffix": "%", "color": A3, "icon": "lucide:percent", "start_time": 0},
        {"label": "Доставка", "value": 1, "suffix": "", "color": A4, "icon": "lucide:truck", "start_time": 800},
        {"label": "Сделка", "value": 80000, "suffix": "$", "color": A1, "icon": "lucide:package", "start_time": 1600}]}),
    ("L_hyp_5", "hype", "ComparisonTable", "Ожидание и <em>реальность</em>", "одна система", {"variant": "tech", "headers": ["", "Ожидание", "Реальность"], "items": [
        {"id": "r1", "label": "Отвечает по прайсу", "values": [True, True], "start_time": 0},
        {"id": "r2", "label": "Признаёт «не знаю»", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Передаёт человеку", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Не выдумывает", "values": [True, False], "start_time": 2400}]}),
    ("L_hyp_6", "hype", "MetricScales", "Почему <em>выдумывает</em>", "природа модели", {"variant": "tech", "title": "Почему выдумывает", "subtitle": "природа модели", "metrics": [
        {"id": 1, "label": "Уверенность бота", "percentage": 98, "color": G2c, "start_time": 0},
        {"id": 2, "label": "Опора на базу", "percentage": 2, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Желание угодить", "percentage": 100, "color": G1c, "start_time": 1600}]}),
    ("L_hyp_7", "hype", "InfographicCards", "Что <em>произошло</em>", "по шагам", {"variant": "tech", "items": [
        {"id": 1, "label": "Признание", "value": "Нет", "trend": "не сказал «не знаю»", "color": A4, "icon": "heroicons:face-frown", "start_time": 0},
        {"id": 2, "label": "Ответ", "value": "Угадал", "trend": "вместо факта", "color": A3, "icon": "heroicons:sparkles", "start_time": 800},
        {"id": 3, "label": "Подарок", "value": "15%", "trend": "скидка из воздуха", "color": A1, "icon": "heroicons:gift", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Конфликт", "trend": "с клиентом", "color": A2, "icon": "heroicons:fire", "start_time": 2400}]}),
    ("L_hyp_8", "hype", "PremiumChecklist", "Почему так <em>устроено</em>", "и кто платит", {"variant": "tech", "items": [
        {"label": "Языковая модель", "desc": "создана угадывать", "icon": "heroicons:cpu-chip", "color": "brand-blue", "start_time": 0},
        {"label": "Без рамок", "desc": "угадывает, чтобы угодить", "icon": "heroicons:arrow-trending-up", "color": "brand-amber", "start_time": 800},
        {"label": "Платит за это", "desc": "твой бизнес", "icon": "heroicons:banknotes", "color": "brand-green", "start_time": 1600}]}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L_how_1", "how", "ArchitectureDiagram", "Границы <em>вокруг</em> агента", "строго по базе", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клиент", "subtitle": "вопрос", "icon": "lucide:message-circle", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core"]},
        {"id": "core", "title": "Агент", "subtitle": "только база", "icon": "lucide:cpu", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["stop", "human"]},
        {"id": "stop", "title": "Нет в базе", "subtitle": "стоп", "icon": "lucide:square", "color": "chart-4", "start_time": 1600, "is_main": False, "to": []},
        {"id": "human", "title": "Инженер", "subtitle": "передать", "icon": "lucide:user-check", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L_how_2", "how", "ChatMockupSlide", "Право <em>молчать</em>", "правильный ответ бота", {"variant": "tech", "bot_name": "Агент", "bot_subtitle": "квалификация", "bot_avatar": "AI", "messages": [
        {"role": "user", "text": "А нестандартные условия дадите?", "start_time": 0},
        {"role": "assistant", "text": "Передам ваш запрос ведущему инженеру.", "start_time": 1500}]}),
    ("L_how_3", "how", "CrmCardSlide", "Сделка <em>в CRM</em>", "а не в чате", {"variant": "tech", "customer": {"name": "Клиент из Европы", "avatar_text": "EU", "id_text": "ID: #80421", "status": "ночной"},
        "fields": [
            {"label": "БЮДЖЕТ", "value": "€40 000", "field_icon": "heroicons:banknotes", "field_color": "brand-green", "start_time": 300},
            {"label": "ЗАПРОС", "value": "Объём партии", "field_icon": "heroicons:cube", "field_color": "brand-blue", "start_time": 1100},
            {"label": "КАНАЛ", "value": "WhatsApp", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-amber", "start_time": 1900},
            {"label": "ВРЕМЯ", "value": "02:14", "field_icon": "heroicons:clock", "field_color": "brand-blue", "start_time": 2700}],
        "buttons": [
            {"text": "Взять в работу", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Запросить детали", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L_how_4", "how", "InfographicCards", "Ночной <em>поток</em>", "что делает агент", {"variant": "tech", "items": [
        {"id": 1, "label": "Ночью", "value": "30%", "trend": "лидов в B2B", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"id": 2, "label": "Агент", "value": "24/7", "trend": "квалифицирует", "color": A2, "icon": "heroicons:cpu-chip", "start_time": 800},
        {"id": 3, "label": "Бюджет", "value": "Собирает", "trend": "сразу", "color": A3, "icon": "heroicons:banknotes", "start_time": 1600},
        {"id": 4, "label": "CRM", "value": "Hubspot", "trend": "карточка готова", "color": A4, "icon": "heroicons:circle-stack", "start_time": 2400}]}),
    ("L_how_5", "how", "MetricScales", "Три <em>вопроса</em>", "до первой строки кода", {"variant": "tech", "title": "Три вопроса", "subtitle": "до первой строки кода", "metrics": [
        {"id": 1, "label": "Право говорить", "percentage": 100, "color": G1c, "start_time": 0},
        {"id": 2, "label": "Граница с человеком", "percentage": 100, "color": G1c, "start_time": 800},
        {"id": 3, "label": "Данные в CRM", "percentage": 90, "color": G2c, "start_time": 1600}]}),
    ("L_how_6", "how", "Roadmap", "Маршрут <em>ответа</em>", "от вопроса до человека", {"variant": "tech", "items": [
        {"label": "Вопрос", "desc": "принять", "icon": "heroicons:chat-bubble-left", "color": "chart-1", "start_time": 0},
        {"label": "База", "desc": "проверить", "icon": "heroicons:book-open", "color": "chart-2", "start_time": 800},
        {"label": "Нет ответа", "desc": "замолчать", "icon": "heroicons:bell-slash", "color": "chart-3", "start_time": 1600},
        {"label": "Данные", "desc": "в CRM", "icon": "heroicons:circle-stack", "color": "chart-4", "start_time": 2400},
        {"label": "Человек", "desc": "передать", "icon": "lucide:user-check", "color": "chart-1", "start_time": 3200}]}),
    ("L_how_7", "how", "StatsBarChart", "Когда приходят <em>лиды</em>", "B2B-трафик", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Когда приходят лиды", "subtitle": "B2B-трафик", "data": [
        {"label": "9–18", "value": 70, "start_time": 0},
        {"label": "18–21", "value": 30, "start_time": 800},
        {"label": "21–24", "value": 20, "highlight": True, "start_time": 1600},
        {"label": "0–9", "value": 10, "start_time": 2400}]}),
    ("L_how_8", "how", "PremiumChecklist", "Правила <em>молчания</em>", "когда агент уходит в сторону", {"variant": "tech", "items": [
        {"label": "Нет в базе", "desc": "молчит и зовёт человека", "icon": "heroicons:bell-alert", "color": "brand-blue", "start_time": 0},
        {"label": "Сложный запрос", "desc": "не квалификация — человеку", "icon": "heroicons:user-group", "color": "brand-amber", "start_time": 800},
        {"label": "Любые данные", "desc": "фиксируются в CRM", "icon": "heroicons:circle-stack", "color": "brand-green", "start_time": 1600}]}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L_prj_1", "project", "ChatMockupSlide", "Бот <em>пообещал</em> выезд", "которого не будет", {"variant": "tech", "bot_name": "Свободный бот", "bot_subtitle": "входящие", "bot_avatar": "AI", "messages": [
        {"role": "user", "text": "Инженер нужен завтра на объект.", "start_time": 0},
        {"role": "assistant", "text": "Инженер будет завтра!", "start_time": 1500},
        {"role": "user", "text": "Объект в 300 км от базы. Точно завтра?", "start_time": 3000},
        {"role": "assistant", "text": "Подтверждаю: завтра.", "start_time": 4500}]}),
    ("L_prj_2", "project", "ReceiptCard", "", "", {"variant": "tech", "title": "КОМПЕНСАЦИИ", "subtitle": "«выезд завтра»", "currency": "€", "total_text": "ВЫПЛАТЫ", "footer_text": "ВЫКРУЧИВАЛИСЬ РУКАМИ", "total_start_time": 2600, "items": [
        {"name": "Простой", "price": 5000, "start_time": 300},
        {"name": "Логистика", "price": 3000, "start_time": 1100},
        {"name": "Репутация", "price": 8000, "start_time": 1900}]}),
    ("L_prj_3", "project", "CodeComparisonSlide", "Промпты <em>или</em> регламент", "что я переделал", {"variant": "tech", "windows": [
        {"title": "Свободный диалог", "color": "var(--color-accent)", "file": "free_chat.py", "code": "# отвечай на всё\nreply = llm(prompt)\nreturn reply", "typing": True, "start_time": 0},
        {"title": "Регламент", "color": "var(--item-accent-1)", "file": "rules.py", "code": "if topic not in KB:\n    escalate('engineer')\n    return SILENCE", "typing": True, "start_time": 1900}]}),
    ("L_prj_4", "project", "ComparisonTable", "Свободный <em>или управляемый</em>", "разные системы", {"variant": "tech", "headers": ["", "Свободный бот", "Регламент"], "items": [
        {"id": "r1", "label": "Опирается на базу", "values": [False, True], "start_time": 0},
        {"id": "r2", "label": "Знает, где молчать", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "STOP-слова", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Не выдумывает", "values": [False, True], "start_time": 2400}]}),
    ("L_prj_5", "project", "MetricScales", "Из чего состоит <em>работа</em>", "код — меньшая часть", {"variant": "tech", "title": "Из чего состоит работа", "subtitle": "код — меньшая часть", "metrics": [
        {"id": 1, "label": "Код", "percentage": 20, "color": G2c, "start_time": 0},
        {"id": 2, "label": "Бизнес-логика", "percentage": 80, "color": G1c, "start_time": 800},
        {"id": 3, "label": "Регламент", "percentage": 100, "color": G1c, "start_time": 1600}]}),
    ("L_prj_6", "project", "ArchitectureDiagram", "Ночная <em>архитектура</em>", "работает сама", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Клиент 02:14", "subtitle": "объём партии", "icon": "lucide:moon", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["core"]},
        {"id": "core", "title": "Агент", "subtitle": "сроки, наличие", "icon": "lucide:cpu", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["crm"]},
        {"id": "crm", "title": "CRM", "subtitle": "карточка", "icon": "lucide:database", "color": "chart-3", "start_time": 1600, "is_main": False, "to": ["mgr"]},
        {"id": "mgr", "title": "Менеджер утром", "subtitle": "ведёт сделку", "icon": "lucide:user-check", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L_prj_7", "project", "ProcessFunnel", "Ночной <em>поток</em>", "от письма до сделки", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Пишут", "count": 100, "icon": "heroicons:chat-bubble-left", "color": A1, "start_time": 0},
        {"label": "Квалифицировал", "count": 100, "icon": "heroicons:cpu-chip", "color": A2, "start_time": 800},
        {"label": "Человеку", "count": 60, "icon": "heroicons:user", "color": A3, "start_time": 1600},
        {"label": "Сделка", "count": 12, "icon": "heroicons:check-circle", "color": A4, "start_time": 2400}]}),
    ("L_prj_8", "project", "CrmCardSlide", "Сделка <em>€40 000</em>", "утром уже готова", {"variant": "tech", "customer": {"name": "Ночной клиент", "avatar_text": "02", "id_text": "ID: #40200", "status": "квалифицирован"},
        "fields": [
            {"label": "БЮДЖЕТ", "value": "€40 000", "field_icon": "heroicons:banknotes", "field_color": "brand-green", "start_time": 300},
            {"label": "ЗАПРОС", "value": "Партия серверов", "field_icon": "heroicons:cube", "field_color": "brand-blue", "start_time": 1100},
            {"label": "КАНАЛ", "value": "WhatsApp", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-amber", "start_time": 1900},
            {"label": "ВРЕМЯ", "value": "02:14", "field_icon": "heroicons:clock", "field_color": "brand-blue", "start_time": 2700}],
        "buttons": [
            {"text": "Принять сделку", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Позвонить", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L_prj_9", "project", "AnimatedStatsSlide", "Результат <em>ночи</em>", "без выдумок", {"variant": "tech", "stats": [
        {"label": "Сделка", "value": 40000, "suffix": "€", "color": A2, "icon": "lucide:handshake", "start_time": 0},
        {"label": "Полей в карточке", "value": 8, "suffix": "", "color": A1, "icon": "lucide:list-checks", "start_time": 800},
        {"label": "Регламент", "value": 100, "suffix": "%", "color": A3, "icon": "lucide:shield-check", "start_time": 1600}]}),
    ("L_prj_10", "project", "TerminalMockup", "Каждый шаг <em>в логе</em>", "видно, где упало", {"variant": "tech", "commands": [
        {"cmd": "$ flow --logs --night", "output": "02:14 intake ok\n02:14 qualify ok\n02:15 crm.save ok\nescalation: no", "start_time": 300},
        {"cmd": "$ flow --status", "output": "uptime: 100%\nfallbacks: 0\nhandoffs: 4", "start_time": 2000}]}),
    ("L_prj_11", "project", "StatsBarChart", "Ночные <em>заявки</em>", "до и после регламента", {"variant": "tech", "base_color": "var(--chart-1)", "peak_color": "var(--color-accent)", "title": "Ночные заявки", "subtitle": "до и после регламента", "data": [
        {"label": "До", "value": 20, "start_time": 0},
        {"label": "Обрыв", "value": 5, "start_time": 800},
        {"label": "После", "value": 90, "highlight": True, "start_time": 1600},
        {"label": "Месяц", "value": 100, "start_time": 2400}]}),
    ("L_prj_12", "project", "InfographicCards", "Утро <em>менеджера</em>", "спокойное", {"variant": "tech", "items": [
        {"id": 1, "label": "Ночь", "value": "Спокоен", "trend": "агент держит", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"id": 2, "label": "Утро", "value": "Готова", "trend": "карточка в CRM", "color": A2, "icon": "heroicons:circle-stack", "start_time": 800},
        {"id": 3, "label": "Сделка", "value": "€40k", "trend": "квалификация", "color": A3, "icon": "heroicons:banknotes", "start_time": 1600},
        {"id": 4, "label": "Обещания", "value": "Факт", "trend": "только из базы", "color": A4, "icon": "heroicons:check-badge", "start_time": 2400}]}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L_whr_1", "where", "PremiumChecklist", "Когда <em>не работает</em>", "честные ограничения", {"variant": "tech", "items": [
        {"label": "Бардак в процессах", "desc": "регламент масштабирует хаос", "icon": "heroicons:exclamation-triangle", "color": "brand-blue", "start_time": 0},
        {"label": "Длинный цикл B2B", "desc": "несколько лиц и политика", "icon": "heroicons:user-group", "color": "brand-amber", "start_time": 800},
        {"label": "Нет правил", "desc": "автоматизировать нечего", "icon": "heroicons:no-symbol", "color": "brand-green", "start_time": 1600}]}),
    ("L_whr_2", "where", "ArchitectureDiagram", "Где агент <em>не лезет</em>", "политика решает человек", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Политика клиента", "subtitle": "закупка, юристы", "icon": "lucide:scale", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["human"]},
        {"id": "human", "title": "Человек", "subtitle": "ведёт сделку", "icon": "lucide:user-check", "color": "chart-3", "start_time": 800, "is_main": True, "to": []},
        {"id": "agent", "title": "Агент", "subtitle": "в стороне", "icon": "lucide:cpu", "color": "chart-4", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L_whr_3", "where", "MetricScales", "Порог <em>применимости</em>", "что важнее", {"variant": "tech", "title": "Порог применимости", "subtitle": "что важнее", "metrics": [
        {"id": 1, "label": "Готовность процесса", "percentage": 10, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Скорость ответа", "percentage": 90, "color": G1c, "start_time": 800},
        {"id": 3, "label": "Политика сделки", "percentage": 5, "color": G2c, "start_time": 1600}]}),
    ("L_whr_4", "where", "ComparisonTable", "Кому <em>что остаётся</em>", "агент и человек", {"variant": "tech", "headers": ["", "Агент", "Человек"], "items": [
        {"id": "r1", "label": "Квалификация", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Переговоры", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Политика", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Длинный цикл", "values": [False, True], "start_time": 2400}]}),

    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L_cnc_1", "conclusion", "Roadmap", "Цепочка <em>как надо</em>", "кто за что отвечает", {"variant": "tech", "items": [
        {"label": "Лид", "desc": "пришёл", "icon": "heroicons:inbox-arrow-down", "color": "chart-1", "start_time": 0},
        {"label": "Агент", "desc": "квалификация", "icon": "heroicons:cpu-chip", "color": "chart-2", "start_time": 800},
        {"label": "Менеджер", "desc": "переговоры", "icon": "heroicons:user-group", "color": "chart-3", "start_time": 1600},
        {"label": "Сделка", "desc": "закрыта", "icon": "heroicons:check-badge", "color": "chart-4", "start_time": 2400}]}),
    ("L_cnc_2", "conclusion", "AnimatedStatsSlide", "Кто <em>что делает</em>", "рутина и переговоры", {"variant": "tech", "stats": [
        {"label": "Рутина — агенту", "value": 100, "suffix": "%", "color": A2, "icon": "lucide:bot", "start_time": 0},
        {"label": "Переговоры — человеку", "value": 100, "suffix": "%", "color": A1, "icon": "lucide:users", "start_time": 800},
        {"label": "Сделок с гарантией", "value": 1, "suffix": "", "color": A3, "icon": "lucide:handshake", "start_time": 1600}]}),
    ("L_cnc_3", "conclusion", "PremiumChecklist", "Итог <em>без хайпа</em>", "одна мысль", {"variant": "tech", "items": [
        {"label": "Агент", "desc": "рутина и сбор данных", "icon": "heroicons:cpu-chip", "color": "brand-blue", "start_time": 0},
        {"label": "Менеджер", "desc": "переговоры и политика", "icon": "heroicons:user-group", "color": "brand-amber", "start_time": 800},
        {"label": "Бизнес-логика", "desc": "без неё — бомба замедленного действия", "icon": "heroicons:exclamation-triangle", "color": "brand-green", "start_time": 1600}]}),

    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L_cta_1", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
    print(f"Preview: http://localhost:5174/p/{PRES_ID}")


if __name__ == "__main__":
    main()
