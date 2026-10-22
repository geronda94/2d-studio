#!/usr/bin/env python3
"""Слайды для Длинное_06 «MVP за несколько недель» (presentation 84), 7 блоков.

Запуск с хоста: python3 scripts/build_long06_slides.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
PRES_ID = 84
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]
A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L6_tez_1", "tezis", "InfographicCards", "Полгода и <em>$15 000</em>", "релиз прогремел", {"variant": "tech", "items": [
        {"id": 1, "label": "Платформа", "value": "Собрана", "trend": "полгода работы", "color": A1, "icon": "heroicons:rectangle-stack", "start_time": 0},
        {"id": 2, "label": "Бюджет", "value": "$15 000", "trend": "потрачен", "color": A3, "icon": "heroicons:banknotes", "start_time": 800},
        {"id": 3, "label": "Клиенты просят", "value": "Бот", "trend": "одна кнопка", "color": A2, "icon": "heroicons:cursor-arrow-rays", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Впустую", "trend": "до первой продажи", "color": A4, "icon": "heroicons:arrow-trending-down", "start_time": 2400}]}),
    ("L6_tez_2", "tezis", "AnimatedStatsSlide", "Сгорело <em>впустую</em>", "сложный MVP", {"variant": "tech", "stats": [
        {"label": "Денег", "value": 15000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Месяцев", "value": 6, "suffix": "", "color": A4, "icon": "heroicons:calendar-days", "start_time": 800},
        {"label": "Нужен бот с", "value": 1, "suffix": "кнопкой", "color": A1, "icon": "heroicons:cursor-arrow-rays", "start_time": 1600}]}),
    ("L6_tez_3", "tezis", "ComparisonTable", "Платформа <em>или</em> бот", "что проверит рынок", {"variant": "tech", "headers": ["", "Платформа", "Бот"], "items": [
        {"id": "r1", "label": "Полгода разработки", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "$15 000 бюджета", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Одна кнопка", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Проверяет, платит ли рынок", "values": [False, True], "start_time": 2400}]}),
    ("L6_tez_4", "tezis", "DefinitionBlock", "MVP", "что это на самом деле", {"variant": "tech",
        "term": "MVP",
        "definition": "Минимальный инструмент, чтобы проверить, платит ли рынок. Не уменьшенная копия полного продукта.",
        "examples": [
            {"id": "d1", "text": "Проверяет гипотезу, а не собирает всё сразу.", "start_time": 1000},
            {"id": "d2", "text": "Запускается быстро и стоит дёшево.", "start_time": 2000}],
        "related_terms": ["Гипотеза", "Рынок", "Запуск"]}),
    ("L6_tez_5", "tezis", "MetricScales", "Код — <em>20%</em>", "остальное — смысл", {"variant": "tech", "title": "Код — 20%", "subtitle": "остальное — смысл", "metrics": [
        {"id": 1, "label": "Код", "percentage": 20, "color": G2c, "start_time": 0},
        {"id": 2, "label": "Смысл и процесс", "percentage": 100, "color": G1c, "start_time": 800},
        {"id": 3, "label": "Проверка рынка", "percentage": 100, "color": G1c, "start_time": 1600}]}),
    ("L6_tez_6", "tezis", "PremiumChecklist", "Что <em>покажу</em>", "на реальном проекте", {"variant": "tech", "items": [
        {"label": "Как собирали", "desc": "первую версию", "icon": "heroicons:wrench-screwdriver", "color": "brand-blue", "start_time": 0},
        {"label": "От чего отказались", "desc": "жёстко", "icon": "heroicons:scissors", "color": "brand-amber", "start_time": 800},
        {"label": "Почему код", "desc": "только 20% работы", "icon": "heroicons:code-bracket", "color": "brand-green", "start_time": 1600}]}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L6_hyp_1", "hype", "QuoteCard", "Что пишут <em>статьи</em>", "про MVP", {"variant": "tech",
        "quote": "MVP — это когда кнопки съехали, а дизайна нет.",
        "author": "Стартап-статья", "author_title": "обещает простоту", "source": "на деле всё иначе"}),
    ("L6_hyp_2", "hype", "ComparisonTable", "Заказчик <em>и</em> закупщик", "разные потребности", {"variant": "tech", "headers": ["", "Заказчик хочет", "Закупщику нужно"], "items": [
        {"id": "r1", "label": "Ролевая модель", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Личный кабинет", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "10 платёжных шлюзов", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Металл и дата отгрузки", "values": [False, True], "start_time": 2400}]}),
    ("L6_hyp_3", "hype", "AnimatedStatsSlide", "$30 000 <em>и ждать</em>", "типичный запрос", {"variant": "tech", "stats": [
        {"label": "Бюджет", "value": 30000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Платёжных шлюзов", "value": 10, "suffix": "", "color": A4, "icon": "heroicons:credit-card", "start_time": 800},
        {"label": "Ролей в системе", "value": 4, "suffix": "", "color": A2, "icon": "heroicons:users", "start_time": 1600}]}),
    ("L6_hyp_4", "hype", "ArchitectureDiagram", "Айсберг <em>MVP</em>", "сверху — простое", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "top", "title": "Форма заявки", "subtitle": "и PDF", "icon": "lucide:file-text", "color": "chart-2", "start_time": 0, "is_main": True, "to": ["cab"]},
        {"id": "cab", "title": "Личные кабинеты", "subtitle": "под водой", "icon": "lucide:layout-dashboard", "color": "chart-5", "start_time": 800, "is_main": False, "to": ["ana"]},
        {"id": "ana", "title": "Аналитика", "subtitle": "и рекомендации", "icon": "lucide:chart-line", "color": "chart-6", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L6_hyp_5", "hype", "PremiumChecklist", "Что реально <em>нужно</em>", "заводу", {"variant": "tech", "items": [
        {"label": "Чистая страница", "desc": "без лишнего", "icon": "heroicons:document-text", "color": "brand-blue", "start_time": 0},
        {"label": "Хорошая презентация", "desc": "понятный оффер", "icon": "heroicons:presentation-chart-bar", "color": "brand-amber", "start_time": 800},
        {"label": "Простая форма заявки", "desc": "один шаг", "icon": "heroicons:clipboard-document-list", "color": "brand-green", "start_time": 1600}]}),
    ("L6_hyp_6", "hype", "QuoteCard", "Закупщику <em>плевать</em>", "на дашборд", {"variant": "tech",
        "quote": "Есть ли металл на складе и когда будет отгрузка. Всё.",
        "author": "Закупщик", "author_title": "на заводе", "source": "реальная потребность"}),
    ("L6_hyp_7", "hype", "MetricScales", "Фантазии <em>сжигают</em>", "бюджет", {"variant": "tech", "title": "Фантазии сжигают", "subtitle": "бюджет", "metrics": [
        {"id": 1, "label": "Ролевая модель", "percentage": 100, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Умные рекомендации", "percentage": 100, "color": G3c, "start_time": 800},
        {"id": 3, "label": "Польза закупщику", "percentage": 10, "color": G2c, "start_time": 1600}]}),
    ("L6_hyp_8", "hype", "DefinitionBlock", "Миф об <em>MVP</em>", "термин", {"variant": "tech",
        "term": "Миф об MVP",
        "definition": "Первая версия — это не про кнопки и не про дизайн. Это про проверку, готов ли рынок платить.",
        "examples": [
            {"id": "d1", "text": "Кнопки и дизайн — второй слой.", "start_time": 1000},
            {"id": "d2", "text": "Первый слой — понятный оффер и форма.", "start_time": 2000}],
        "related_terms": ["Оффер", "Форма", "Рынок"]}),
    ("L6_hyp_9", "hype", "PremiumChecklist", "Не про <em>кнопки</em>", "про проверку", {"variant": "tech", "items": [
        {"label": "Первая версия", "desc": "проверяет спрос", "icon": "heroicons:eye", "color": "brand-blue", "start_time": 0},
        {"label": "Кнопки и дизайн", "desc": "второй слой", "icon": "heroicons:cursor-arrow-rays", "color": "brand-amber", "start_time": 800},
        {"label": "Оффер", "desc": "первый слой", "icon": "heroicons:document-text", "color": "brand-green", "start_time": 1600}]}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L6_how_1", "how", "QuoteCard", "Главный <em>вопрос</em>", "до кода", {"variant": "tech",
        "quote": "Какова реальная цель — проверить, купят ли услугу?",
        "author": "Игорь", "author_title": "IT2B", "source": "первый вопрос"}),
    ("L6_how_2", "how", "ProcessFunnel", "Фильтр <em>фич</em>", "три вопроса", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Фича", "count": 100, "icon": "heroicons:cube", "color": A1, "start_time": 0},
        {"label": "Приносит деньги", "count": 60, "icon": "heroicons:banknotes", "color": A2, "start_time": 800},
        {"label": "Решает боль", "count": 35, "icon": "heroicons:heart", "color": A3, "start_time": 1600},
        {"label": "Не вручную", "count": 20, "icon": "heroicons:hand-raised", "color": A4, "start_time": 2400}]}),
    ("L6_how_3", "how", "InfographicCards", "Три <em>вопроса</em>", "каждой фиче", {"variant": "tech", "items": [
        {"id": 1, "label": "Деньги", "value": "Напрямую", "trend": "приносит?", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"id": 2, "label": "Боль", "value": "Сейчас", "trend": "решает?", "color": A2, "icon": "heroicons:heart", "start_time": 800},
        {"id": 3, "label": "Ручная работа", "value": "Можно", "trend": "на 100 заказов?", "color": A3, "icon": "heroicons:hand-raised", "start_time": 1600},
        {"id": 4, "label": "Итог", "value": "Режем", "trend": "лишнее", "color": A4, "icon": "heroicons:scissors", "start_time": 2400}]}),
    ("L6_how_4", "how", "ComparisonTable", "Автоматизируем <em>или</em> вручную", "решение по фиче", {"variant": "tech", "headers": ["", "Автоматизируем", "Оставляем вручную"], "items": [
        {"id": "r1", "label": "Приносит деньги", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Главная боль сейчас", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Первые 100 заказов", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Заменимо менеджером", "values": [False, True], "start_time": 2400}]}),
    ("L6_how_5", "how", "MetricScales", "Режем <em>функционал</em>", "до упора", {"variant": "tech", "title": "Режем функционал", "subtitle": "до упора", "metrics": [
        {"id": 1, "label": "Заявленный функционал", "percentage": 100, "color": G3c, "start_time": 0},
        {"id": 2, "label": "Остаётся в первой версии", "percentage": 20, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Проверка рынка", "percentage": 100, "color": G1c, "start_time": 1600}]}),
    ("L6_how_6", "how", "DefinitionBlock", "Ручная <em>работа</em>", "на старте", {"variant": "tech",
        "term": "Ручная работа на старте",
        "definition": "Первые сто заказов менеджер может обрабатывать руками. Автоматизировать это в первой версии не нужно.",
        "examples": [
            {"id": "d1", "text": "Меньше кода — быстрее запуск.", "start_time": 1000},
            {"id": "d2", "text": "Ручное видно и легко чинится.", "start_time": 2000}],
        "related_terms": ["Старт", "Менеджер", "Заказы"]}),
    ("L6_how_7", "how", "QuoteCard", "Если «да» — <em>не автоматизируем</em>", "правило", {"variant": "tech",
        "quote": "Если фичу можно заменить ручной работой на первые сто заказов, в первой версии её нет.",
        "author": "Игорь", "author_title": "IT2B", "source": "фильтр фич"}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L6_prj_1", "project", "CrmCardSlide", "Портал <em>аренды техники</em>", "спецтехника", {"variant": "tech", "customer": {"name": "Аренда спецтехники", "avatar_text": "А", "id_text": "ID: #mvp-06", "status": "запуск"},
        "fields": [
            {"label": "ИДЕЯ", "value": "Матчинг", "field_icon": "heroicons:arrows-right-left", "field_color": "brand-blue", "start_time": 300},
            {"label": "ЧАТ", "value": "Защищённый", "field_icon": "heroicons:chat-bubble-left", "field_color": "brand-amber", "start_time": 1100},
            {"label": "КАБИНЕТЫ", "value": "Личные", "field_icon": "heroicons:user", "field_color": "brand-green", "start_time": 1900},
            {"label": "ОСТАВИЛИ", "value": "Каталог + форма", "field_icon": "heroicons:clipboard-document-list", "field_color": "brand-orange", "start_time": 2700}],
        "buttons": [
            {"text": "Отрезать лишнее", "btn_color": "", "btn_text_color": "", "start_time": 3200},
            {"text": "Запустить", "btn_color": "", "btn_text_color": "", "start_time": 4000}]}),
    ("L6_prj_2", "project", "ComparisonTable", "Идея <em>и</em> первая версия", "что выжило", {"variant": "tech", "headers": ["", "Идея", "Первая версия"], "items": [
        {"id": "r1", "label": "Автоматический матчинг", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Защищённый чат", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Личные кабинеты", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Каталог и форма", "values": [False, True], "start_time": 2400}]}),
    ("L6_prj_3", "project", "InfographicCards", "Что <em>оставили</em>", "минимум", {"variant": "tech", "items": [
        {"id": 1, "label": "Каталог", "value": "Есть", "trend": "техника", "color": A1, "icon": "heroicons:rectangle-stack", "start_time": 0},
        {"id": 2, "label": "Форма", "value": "Запросить", "trend": "технику", "color": A2, "icon": "heroicons:clipboard-document-list", "start_time": 800},
        {"id": 3, "label": "Лишнее", "value": "Отрезано", "trend": "жёстко", "color": A3, "icon": "heroicons:scissors", "start_time": 1600},
        {"id": 4, "label": "Запуск", "value": "Быстрый", "trend": "без ожидания", "color": A4, "icon": "heroicons:bolt", "start_time": 2400}]}),
    ("L6_prj_4", "project", "QuoteCard", "Поначалу <em>идеально</em>", "до трафика", {"variant": "tech",
        "quote": "Всё работало идеально — до реального трафика.",
        "author": "Игорь", "author_title": "IT2B", "source": "первый запуск"}),
    ("L6_prj_5", "project", "AnimatedStatsSlide", "4000 <em>фотографий</em>", "прямо с фотоаппарата", {"variant": "tech", "stats": [
        {"label": "Фото залито", "value": 4000, "suffix": "", "color": A3, "icon": "heroicons:photo", "start_time": 0},
        {"label": "Неделя запуска", "value": 1, "suffix": "", "color": A4, "icon": "heroicons:calendar-days", "start_time": 800},
        {"label": "Белый экран", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:exclamation-triangle", "start_time": 1600}]}),
    ("L6_prj_6", "project", "ArchitectureDiagram", "Сайт <em>лёг</em>", "в первую неделю", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "4000 фото", "subtitle": "без сжатия", "icon": "lucide:image", "color": "chart-3", "start_time": 0, "is_main": False, "to": ["load"]},
        {"id": "load", "title": "Тяжёлая загрузка", "subtitle": "долго", "icon": "lucide:clock", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["white"]},
        {"id": "white", "title": "Белый экран", "subtitle": "сайт лежит", "icon": "lucide:monitor-off", "color": "chart-6", "start_time": 1600, "is_main": False, "to": ["gone"]},
        {"id": "gone", "title": "Клиент ушёл", "subtitle": "плохой интернет", "icon": "lucide:user-x", "color": "chart-4", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L6_prj_7", "project", "PremiumChecklist", "Кто <em>ушёл</em>", "со строек", {"variant": "tech", "items": [
        {"label": "Клиенты со строек", "desc": "плохой интернет", "icon": "heroicons:user-minus", "color": "brand-blue", "start_time": 0},
        {"label": "Долгая загрузка", "desc": "белый экран", "icon": "heroicons:clock", "color": "brand-amber", "start_time": 800},
        {"label": "Фото без сжатия", "desc": "4K с камеры", "icon": "heroicons:photo", "color": "brand-green", "start_time": 1600}]}),
    ("L6_prj_8", "project", "QuoteCard", "Второй <em>провал</em>", "финансовый", {"variant": "tech",
        "quote": "Менеджер перепутал шаблоны и отправил счёт с реквизитами другой фирмы.",
        "author": "Игорь", "author_title": "IT2B", "source": "ручные счета"}),
    ("L6_prj_9", "project", "AnimatedStatsSlide", "Сделка <em>$35 000</em>", "сорвалась", {"variant": "tech", "stats": [
        {"label": "Сделка", "value": 35000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Заподозрил мошенничество", "value": 1, "suffix": "клиент", "color": A4, "icon": "heroicons:exclamation-triangle", "start_time": 800},
        {"label": "Сорвалась", "value": 100, "suffix": "%", "color": A1, "icon": "heroicons:x-circle", "start_time": 1600}]}),
    ("L6_prj_10", "project", "ComparisonTable", "Ручные <em>счета</em>", "и автоматика", {"variant": "tech", "headers": ["", "Вручную", "Автоматически"], "items": [
        {"id": "r1", "label": "Перепутать шаблон", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Чужие реквизиты", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Ошибки исчезли", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Сборка за 2 дня", "values": [False, True], "start_time": 2400}]}),
    ("L6_prj_11", "project", "ArchitectureDiagram", "Картинки <em>починил</em>", "скорость вернулась", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Фото", "subtitle": "любые", "icon": "lucide:image", "color": "chart-2", "start_time": 0, "is_main": False, "to": ["script"]},
        {"id": "script", "title": "Скрипт сжатия", "subtitle": "пережимает", "icon": "lucide:wrench", "color": "chart-1", "start_time": 800, "is_main": True, "to": ["cdn"]},
        {"id": "cdn", "title": "CDN", "subtitle": "доставка", "icon": "lucide:globe", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["fast"]},
        {"id": "fast", "title": "Скорость", "subtitle": "вернулась", "icon": "lucide:zap", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L6_prj_12", "project", "ProcessFunnel", "Счёт <em>автоматом</em>", "без почты", {"variant": "tech", "layout": "horizontal", "steps": [
        {"label": "Заявка", "count": 100, "icon": "heroicons:inbox", "color": A1, "start_time": 0},
        {"label": "Make", "count": 85, "icon": "heroicons:bolt", "color": A2, "start_time": 800},
        {"label": "PDF-счёт", "count": 70, "icon": "heroicons:document-text", "color": A3, "start_time": 1600},
        {"label": "Telegram менеджеру", "count": 55, "icon": "heroicons:paper-airplane", "color": A4, "start_time": 2400}]}),
    ("L6_prj_13", "project", "AnimatedStatsSlide", "За <em>2 дня</em>", "без бэкенд-кода", {"variant": "tech", "stats": [
        {"label": "Дней на переделку", "value": 2, "suffix": "", "color": A1, "icon": "heroicons:calendar-days", "start_time": 0},
        {"label": "Сервис автоматизации", "value": 1, "suffix": "Make", "color": A2, "icon": "heroicons:bolt", "start_time": 800},
        {"label": "Ручных ошибок убрали", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:check-badge", "start_time": 1600}]}),
    ("L6_prj_14", "project", "InfographicCards", "Что <em>исчезло</em>", "после переделки", {"variant": "tech", "items": [
        {"id": 1, "label": "Ручные счета", "value": "Нет", "trend": "автоматом", "color": A1, "icon": "heroicons:document-text", "start_time": 0},
        {"id": 2, "label": "Шаблоны", "value": "Путаницы", "trend": "больше нет", "color": A2, "icon": "heroicons:scissors", "start_time": 800},
        {"id": 3, "label": "Загрузка", "value": "Быстрая", "trend": "CDN + сжатие", "color": A3, "icon": "heroicons:bolt", "start_time": 1600},
        {"id": 4, "label": "Ошибки", "value": "Убраны", "trend": "ручные", "color": A4, "icon": "heroicons:check-badge", "start_time": 2400}]}),
    ("L6_prj_15", "project", "QuoteCard", "Итог <em>кейса</em>", "два дня", {"variant": "tech",
        "quote": "Ручные ошибки исчезли. И я сделал это за два дня без единой строчки бэкенд-кода.",
        "author": "Игорь", "author_title": "IT2B", "source": "результат"}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L6_whr_1", "where", "PremiumChecklist", "Где <em>не работает</em>", "честно", {"variant": "tech", "items": [
        {"label": "Нет бюджета на трафик", "desc": "MVP висит мёртвым грузом", "icon": "heroicons:banknotes", "color": "brand-blue", "start_time": 0},
        {"label": "Медицинское ПО", "desc": "безопасность нельзя допилить потом", "icon": "heroicons:heart", "color": "brand-amber", "start_time": 800},
        {"label": "Финтех", "desc": "та же история с безопасностью", "icon": "heroicons:lock-closed", "color": "brand-green", "start_time": 1600}]}),
    ("L6_whr_2", "where", "ComparisonTable", "MVP <em>с трафиком</em>", "и без маркетинга", {"variant": "tech", "headers": ["", "С трафиком", "Без маркетинга"], "items": [
        {"id": "r1", "label": "Проверяет рынок", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Приносит заявки", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Висит мёртвым грузом", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Сжигает бюджет", "values": [False, True], "start_time": 2400}]}),
    ("L6_whr_3", "where", "QuoteCard", "Без <em>маркетинга</em>", "итог", {"variant": "tech",
        "quote": "Первая версия будет просто висеть мёртвым грузом.",
        "author": "Игорь", "author_title": "IT2B", "source": "граница применимости"}),
    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L6_cnc_1", "conclusion", "DefinitionBlock", "MVP — <em>покупка информации</em>", "термин", {"variant": "tech",
        "term": "MVP",
        "definition": "Дешёвая покупка информации о рынке. Готовым бизнесом он не становится.",
        "examples": [
            {"id": "d1", "text": "Проверяет, платит ли рынок.", "start_time": 1000},
            {"id": "d2", "text": "Не заменяет продажи и маркетинг.", "start_time": 2000}],
        "related_terms": ["Рынок", "Гипотеза", "Бизнес"]}),
    ("L6_cnc_2", "conclusion", "QuoteCard", "Не <em>готовый бизнес</em>", "одна мысль", {"variant": "tech",
        "quote": "MVP показывает, есть ли спрос. Дальше начинается работа, которую он не делает за тебя.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод"}),
    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L6_cta_1", "cta", "PremiumChecklist", "Пришли <em>суть</em>", "в Telegram", {"variant": "tech", "items": [
        {"label": "Идея проекта", "desc": "что хочешь запустить", "icon": "heroicons:light-bulb", "color": "brand-blue", "start_time": 0},
        {"label": "Цель", "desc": "что проверяем", "icon": "heroicons:flag", "color": "brand-amber", "start_time": 800},
        {"label": "Что выкинуть", "desc": "предложу для старта", "icon": "heroicons:scissors", "color": "brand-green", "start_time": 1600}]}),
    ("L6_cta_2", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
