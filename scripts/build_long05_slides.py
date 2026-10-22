#!/usr/bin/env python3
"""Слайды для Длинное_05 «Кейс: автоматизация ночных заявок» (presentation 79), 7 блоков.

Запуск с хоста: python3 scripts/build_long05_slides.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_auth  # noqa: E402,F401
import generate_short as gs  # noqa: E402
from build_shorts04 import IT2B_OUTRO, normalize_bgm_track  # noqa: E402

BASE = gs.BASE
PRES_ID = 79
SECTIONS = ["tezis", "hype", "how", "project", "where", "conclusion", "cta"]
A1, A2, A3, A4 = "var(--item-accent-1)", "var(--item-accent-2)", "var(--item-accent-3)", "var(--item-accent-4)"
G1c = "linear-gradient(to right, #34D399, #2DD4BF)"
G2c = "linear-gradient(to right, #F59E0B, #FB923C)"
G3c = "linear-gradient(to right, #EF4444, #F87171)"

SLIDES = [
    # ─── ТЕЗИС ─────────────────────────────────────────────────────────
    ("L5_tez_1", "tezis", "InfographicCards", "Клиент в <em>2:00</em> ночи", "а менеджер спит", {"variant": "tech", "items": [
        {"id": 1, "label": "Контакт", "value": "2:00", "trend": "ночи", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"id": 2, "label": "Менеджер", "value": "Спит", "trend": "до утра", "color": A4, "icon": "heroicons:clock", "start_time": 800},
        {"id": 3, "label": "Звонок", "value": "10:00", "trend": "слишком поздно", "color": A2, "icon": "heroicons:sun", "start_time": 1600},
        {"id": 4, "label": "Деньги", "value": "У других", "trend": "быстрее ответили", "color": A3, "icon": "heroicons:arrow-right-circle", "start_time": 2400}]}),
    ("L5_tez_2", "tezis", "AnimatedStatsSlide", "Сгорает <em>треть</em>", "ночных заявок", {"variant": "tech", "stats": [
        {"label": "Ночных заявок сгорает", "value": 30, "suffix": "%", "color": A3, "icon": "heroicons:fire", "start_time": 0},
        {"label": "Часов до ответа", "value": 8, "suffix": "", "color": A4, "icon": "heroicons:clock", "start_time": 800},
        {"label": "Ответивших ночью", "value": 1, "suffix": "конкурент", "color": A2, "icon": "heroicons:user-minus", "start_time": 1600}]}),
    ("L5_tez_3", "tezis", "ComparisonTable", "Ночь <em>против</em> утра", "когда клиент горячий", {"variant": "tech", "headers": ["", "2:00 ночи", "10:00 утра"], "items": [
        {"id": "r1", "label": "Горячий клиент", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Готов перевести деньги", "values": [True, False], "start_time": 800},
        {"id": "r3", "label": "Остыл", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Купил у другого", "values": [False, True], "start_time": 2400}]}),
    ("L5_tez_4", "tezis", "QuoteCard", "Очевидный <em>шаг</em>", "и его ловушка", {"variant": "tech",
        "quote": "Поставить бота, который зафиксирует контакт и квалифицирует его. Кажется, этого достаточно.",
        "author": "Игорь", "author_title": "IT2B", "source": "ночная автоматизация"}),
    ("L5_tez_5", "tezis", "DefinitionBlock", "Ловушка <em>шаблона</em>", "термин", {"variant": "tech",
        "term": "Ловушка шаблона",
        "definition": "Кажется, что бота достаточно. Но система падает с треском, если не учесть детали.",
        "examples": [
            {"id": "d1", "text": "Шаблон не понимает контекст запроса.", "start_time": 1000},
            {"id": "d2", "text": "Одна деталь — и сделка зависает.", "start_time": 2000}],
        "related_terms": ["Бот", "Контекст", "Детали"]}),
    ("L5_tez_6", "tezis", "QuoteCard", "Разберу на <em>проекте</em>", "как устроено внутри", {"variant": "tech",
        "quote": "Покажу на реальном проекте, как это устроено внутри и почему система падает без учёта деталей.",
        "author": "Игорь", "author_title": "IT2B", "source": "план разбора"}),
    # ─── ХАЙП vs РЕАЛЬНОСТЬ ────────────────────────────────────────────
    ("L5_hyp_1", "hype", "QuoteCard", "Обещание <em>интеграторов</em>", "магия в две кнопки", {"variant": "tech",
        "quote": "Подключил шаблон, нажал две кнопки — и иди спокойно спать.",
        "author": "Продавец интеграций", "author_title": "обещает магию", "source": "и я сам через это проходил"}),
    ("L5_hyp_2", "hype", "AnimatedStatsSlide", "Неделя — <em>и конфликты</em>", "на практике", {"variant": "tech", "stats": [
        {"label": "Дней работает", "value": 7, "suffix": "", "color": A1, "icon": "heroicons:calendar-days", "start_time": 0},
        {"label": "Дежурных автоответов", "value": 100, "suffix": "%", "color": A4, "icon": "heroicons:chat-bubble-left", "start_time": 800},
        {"label": "Закупщик в ярости", "value": 100, "suffix": "%", "color": A3, "icon": "heroicons:exclamation-triangle", "start_time": 1600}]}),
    ("L5_hyp_3", "hype", "PremiumChecklist", "Кто пишет <em>ночью</em>", "не от скуки", {"variant": "tech", "items": [
        {"label": "Инженер", "desc": "у которого горит план", "icon": "heroicons:wrench-screwdriver", "color": "brand-blue", "start_time": 0},
        {"label": "Закупщик", "desc": "собирает пул поставщиков", "icon": "heroicons:user", "color": "brand-amber", "start_time": 800},
        {"label": "Техзапрос с PDF", "desc": "на партию товара", "icon": "heroicons:document-text", "color": "brand-green", "start_time": 1600}]}),
    ("L5_hyp_4", "hype", "ArchitectureDiagram", "Собирает <em>пул</em>", "в два часа ночи", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Закупщик 2:00", "subtitle": "горит план", "icon": "lucide:user", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["req"]},
        {"id": "req", "title": "Техзапрос + PDF", "subtitle": "спецификация", "icon": "lucide:file-text", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["pool"]},
        {"id": "pool", "title": "Пул поставщиков", "subtitle": "ищет быстрых", "icon": "lucide:users", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["wait"]},
        {"id": "wait", "title": "Ждёт ответа", "subtitle": "прямо сейчас", "icon": "lucide:clock", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L5_hyp_5", "hype", "ComparisonTable", "Запрос <em>против</em> шаблона", "что видит закупщик", {"variant": "tech", "headers": ["", "Живой запрос", "Шаблон"], "items": [
        {"id": "r1", "label": "Учитывает спецификацию", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "«Свяжемся в рабочее время»", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Дата отгрузки сразу", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Бесит закупщика", "values": [False, True], "start_time": 2400}]}),
    ("L5_hyp_6", "hype", "ChatMockupSlide", "Диалог <em>ночью</em>", "живой запрос и бот", {"variant": "tech", "bot_name": "Закупщик", "bot_subtitle": "пишет в 2:00", "bot_avatar": "З", "messages": [
        {"role": "user", "text": "Нужна партия серверов, спецификация в PDF.", "start_time": 0},
        {"role": "assistant", "text": "Спасибо, свяжемся в рабочее время.", "start_time": 1500},
        {"role": "user", "text": "Я 15 минут писал детали. Вы издеваетесь?", "start_time": 3000}]}),
    ("L5_hyp_7", "hype", "QuoteCard", "Автоответчик <em>из нулевых</em>", "что чувствует закупщик", {"variant": "tech",
        "quote": "Человек потратил пятнадцать минут на детали — и получил глупый автоответчик из нулевых.",
        "author": "Игорь", "author_title": "IT2B", "source": "реакция закупщика"}),
    ("L5_hyp_8", "hype", "PremiumChecklist", "Иллюзия <em>допродаж</em>", "и почему рушит доверие", {"variant": "tech", "items": [
        {"label": "Чехол по акции", "desc": "при заказе серверов", "icon": "heroicons:shopping-cart", "color": "brand-amber", "start_time": 0},
        {"label": "Выглядит странно", "desc": "неуместная допродажа", "icon": "heroicons:face-frown", "color": "brand-blue", "start_time": 800},
        {"label": "Доверие рушится", "desc": "оптовик уходит", "icon": "heroicons:shield-exclamation", "color": "brand-green", "start_time": 1600}]}),
    ("L5_hyp_9", "hype", "ArchitectureDiagram", "Стена <em>шаблона</em>", "между бизнесом и клиентом", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Твой бизнес", "subtitle": "реальные люди", "icon": "lucide:building", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["wall"]},
        {"id": "wall", "title": "Шаблон", "subtitle": "стена", "icon": "lucide:brick-wall", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["buyer"]},
        {"id": "buyer", "title": "Покупатель", "subtitle": "не достучаться", "icon": "lucide:user-x", "color": "chart-6", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L5_hyp_10", "hype", "QuoteCard", "Стена", "одна мысль", {"variant": "tech",
        "quote": "Шаблоны строят стену между твоим бизнесом и реальным покупателем.",
        "author": "Игорь", "author_title": "IT2B", "source": "итог по хайпу"}),
    # ─── КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ ────────────────────────────────────
    ("L5_how_1", "how", "QuoteCard", "Смотрю на <em>три</em> вещи", "перед автоматизацией", {"variant": "tech",
        "quote": "Когда ко мне приходят за ночной автоматизацией, я всегда смотрю на три вещи.",
        "author": "Игорь", "author_title": "IT2B", "source": "подход"}),
    ("L5_how_2", "how", "ComparisonTable", "Розница <em>или опт</em>", "кто перед ботом", {"variant": "tech", "headers": ["", "Розница", "Опт"], "items": [
        {"id": "r1", "label": "Простая корзина", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Спецификация и ЛПР", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Нужна маршрутизация", "values": [True, True], "start_time": 1600},
        {"id": "r4", "label": "Иная обработка", "values": [False, True], "start_time": 2400}]}),
    ("L5_how_3", "how", "DefinitionBlock", "Коридор <em>бота</em>", "термин", {"variant": "tech",
        "term": "Коридор бота",
        "definition": "Собрать спецификацию, получить контакты ЛПР и мягко назначить созвон с инженером. Без точных цен на сложные сборки.",
        "examples": [
            {"id": "d1", "text": "Не называет точную цену на сложные сборки.", "start_time": 1000},
            {"id": "d2", "text": "Мягко ставит время созвона с инженером.", "start_time": 2000}],
        "related_terms": ["Ограничение", "ЛПР", "Созвон"]}),
    ("L5_how_4", "how", "PremiumChecklist", "Что бот <em>не делает</em>", "жёсткие рамки", {"variant": "tech", "items": [
        {"label": "Не называет цены", "desc": "на сложные сборки", "icon": "heroicons:tag", "color": "brand-blue", "start_time": 0},
        {"label": "Не продаёт в лоб", "desc": "только удержание", "icon": "heroicons:hand-raised", "color": "brand-amber", "start_time": 800},
        {"label": "Не игнорирует контекст", "desc": "читает запрос", "icon": "heroicons:eye-slash", "color": "brand-green", "start_time": 1600}]}),
    ("L5_how_5", "how", "ArchitectureDiagram", "Устойчивость", "если API отвалился", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заявка", "subtitle": "от клиента", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["api"]},
        {"id": "api", "title": "API мессенджера", "subtitle": "может упасть", "icon": "lucide:cloud-off", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["db"]},
        {"id": "db", "title": "База данных", "subtitle": "заявка не потеряется", "icon": "lucide:database", "color": "chart-2", "start_time": 1600, "is_main": False, "to": []}]}),
    ("L5_how_6", "how", "MetricScales", "Три <em>опоры</em>", "надёжной автоматизации", {"variant": "tech", "title": "Три опоры", "subtitle": "надёжной автоматизации", "metrics": [
        {"id": 1, "label": "Маршрутизация", "percentage": 100, "color": G1c, "start_time": 0},
        {"id": 2, "label": "Ограничения бота", "percentage": 100, "color": G2c, "start_time": 800},
        {"id": 3, "label": "Устойчивость", "percentage": 100, "color": G3c, "start_time": 1600}]}),
    ("L5_how_7", "how", "QuoteCard", "На деталях <em>теряют деньги</em>", "почему начинаю с этого", {"variant": "tech",
        "quote": "Я не случайно начинаю с этого — именно на таких деталях клиенты теряют деньги.",
        "author": "Игорь", "author_title": "IT2B", "source": "принцип"}),
    # ─── РЕАЛЬНЫЙ ПРОЕКТ ───────────────────────────────────────────────
    ("L5_prj_1", "project", "AnimatedStatsSlide", "Дистрибьютор <em>электротехники</em>", "ночные заявки сгорают", {"variant": "tech", "stats": [
        {"label": "Забираем после", "value": 19, "suffix": "ч", "color": A1, "icon": "heroicons:moon", "start_time": 0},
        {"label": "Сгорает ночью", "value": 30, "suffix": "%", "color": A3, "icon": "heroicons:fire", "start_time": 800},
        {"label": "Менеджеры спят", "value": 100, "suffix": "%", "color": A4, "icon": "heroicons:users", "start_time": 1600}]}),
    ("L5_prj_2", "project", "QuoteCard", "Задача <em>жёстко</em>", "после 19:00", {"variant": "tech",
        "quote": "Забирать заявки после 19:00 — менеджеры спят, а клиент должен быть в фокусе.",
        "author": "Игорь", "author_title": "IT2B", "source": "постановка задачи"}),
    ("L5_prj_3", "project", "ArchitectureDiagram", "Стандартная <em>связка</em>", "первые дни", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Форма", "subtitle": "заявка", "icon": "lucide:file-text", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["sc"]},
        {"id": "sc", "title": "Сценарий", "subtitle": "обработка", "icon": "lucide:git-branch", "color": "chart-2", "start_time": 800, "is_main": True, "to": ["reg"]},
        {"id": "reg", "title": "Рег. номер", "subtitle": "компании", "icon": "lucide:search", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["chk"]},
        {"id": "chk", "title": "Сервис проверки", "subtitle": "обогащение", "icon": "lucide:shield-check", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L5_prj_4", "project", "AnimatedStatsSlide", "Первые <em>дни</em>", "перехватывали десятки", {"variant": "tech", "stats": [
        {"label": "Дней работало", "value": 14, "suffix": "", "color": A2, "icon": "heroicons:calendar-days", "start_time": 0},
        {"label": "Перехватывали заявок", "value": 40, "suffix": "шт", "color": A1, "icon": "heroicons:inbox", "start_time": 800},
        {"label": "Юр. название сменилось", "value": 1, "suffix": "", "color": A4, "icon": "heroicons:document-text", "start_time": 1600}]}),
    ("L5_prj_5", "project", "QuoteCard", "Через <em>две недели</em>", "система встала", {"variant": "tech",
        "quote": "Через две недели система встала.",
        "author": "Игорь", "author_title": "IT2B", "source": "первый сбой"}),
    ("L5_prj_6", "project", "AnimatedStatsSlide", "Завод из <em>Германии</em>", "ночная заявка", {"variant": "tech", "stats": [
        {"label": "Ошибка внешнего API", "value": 500, "suffix": "", "color": A4, "icon": "heroicons:exclamation-triangle", "start_time": 0},
        {"label": "Зависшая сделка", "value": 120000, "suffix": "$", "color": A3, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Дней в пустоте", "value": 1, "suffix": "", "color": A1, "icon": "heroicons:clock", "start_time": 1600}]}),
    ("L5_prj_7", "project", "ArchitectureDiagram", "Цепочка <em>оборвалась</em>", "ошибка 500", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Ночная заявка", "subtitle": "завод", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["api"]},
        {"id": "api", "title": "Внешний API", "subtitle": "ошибка 500", "icon": "lucide:plug-zap", "color": "chart-5", "start_time": 800, "is_main": True, "to": ["crm"]},
        {"id": "crm", "title": "Не в CRM", "subtitle": "письмо не ушло", "icon": "lucide:database", "color": "chart-4", "start_time": 1600, "is_main": False, "to": ["lost"]},
        {"id": "lost", "title": "Сделка в пустоте", "subtitle": "$120 000", "icon": "lucide:file-x", "color": "chart-6", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L5_prj_8", "project", "QuoteCard", "Вытащил <em>из логов</em>", "на следующий день", {"variant": "tech",
        "quote": "Сделку на 120 тысяч долларов я чудом вытащил из логов на следующий день.",
        "author": "Игорь", "author_title": "IT2B", "source": "спасение сделки"}),
    ("L5_prj_9", "project", "PremiumChecklist", "Вторая <em>проблема</em>", "слабая защита формы", {"variant": "tech", "items": [
        {"label": "Форма без валидации", "desc": "номер не проверяется", "icon": "heroicons:clipboard-document-list", "color": "brand-blue", "start_time": 0},
        {"label": "Клиент просил оставить", "desc": "так удобнее", "icon": "heroicons:user", "color": "brand-amber", "start_time": 800},
        {"label": "Бот-спамер у конкурентов", "desc": "фейковые заявки", "icon": "heroicons:bug-ant", "color": "brand-green", "start_time": 1600}]}),
    ("L5_prj_10", "project", "AnimatedStatsSlide", "400 <em>фейков</em> за ночь", "просто на сбой", {"variant": "tech", "stats": [
        {"label": "Фейковых заявок", "value": 400, "suffix": "", "color": A3, "icon": "heroicons:bug-ant", "start_time": 0},
        {"label": "Слили за ночь", "value": 300, "suffix": "$", "color": A4, "icon": "heroicons:banknotes", "start_time": 800},
        {"label": "Порог блокировки", "value": 5, "suffix": "заявок/час", "color": A1, "icon": "heroicons:shield-check", "start_time": 1600}]}),
    ("L5_prj_11", "project", "InfographicCards", "Что я <em>сделал</em>", "снёс старую логику", {"variant": "tech", "items": [
        {"id": 1, "label": "Снёс логику", "value": "Всю", "trend": "безжалостно", "color": A1, "icon": "heroicons:trash", "start_time": 0},
        {"id": 2, "label": "Запасной путь", "value": "Есть", "trend": "сырые данные", "color": A2, "icon": "heroicons:arrow-uturn-left", "start_time": 800},
        {"id": 3, "label": "Фильтр", "value": "IP", "trend": "5 заявок в час", "color": A3, "icon": "heroicons:funnel", "start_time": 1600},
        {"id": 4, "label": "Триггер", "value": "10:30", "trend": "пуш директору", "color": A4, "icon": "heroicons:bell", "start_time": 2400}]}),
    ("L5_prj_12", "project", "ArchitectureDiagram", "Запасной <em>путь</em>", "если сервис упал", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Сервис упал", "subtitle": "API недоступен", "icon": "lucide:cloud-off", "color": "chart-5", "start_time": 0, "is_main": False, "to": ["raw"]},
        {"id": "raw", "title": "Сырые данные", "subtitle": "фиксируем", "icon": "lucide:database", "color": "chart-1", "start_time": 800, "is_main": True, "to": ["hub"]},
        {"id": "hub", "title": "Hubspot", "subtitle": "кидаем в CRM", "icon": "lucide:tags", "color": "chart-2", "start_time": 1600, "is_main": False, "to": ["tag"]},
        {"id": "tag", "title": "Тег «ручная проверка»", "subtitle": "не теряется", "icon": "lucide:clipboard-check", "color": "chart-3", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L5_prj_13", "project", "AnimatedStatsSlide", "Фильтр <em>5 за час</em>", "и SMS на паузе", {"variant": "tech", "stats": [
        {"label": "Порог на IP", "value": 5, "suffix": "заявок/час", "color": A1, "icon": "heroicons:shield-check", "start_time": 0},
        {"label": "Блок SMS", "value": 100, "suffix": "%", "color": A2, "icon": "heroicons:no-symbol", "start_time": 800},
        {"label": "Спам отсечён", "value": 400, "suffix": "", "color": A4, "icon": "heroicons:bug-ant", "start_time": 1600}]}),
    ("L5_prj_14", "project", "ArchitectureDiagram", "Триггер <em>к 10:30</em>", "директору", {"variant": "tech", "show_data_flow": True, "nodes": [
        {"id": "in1", "title": "Заявка", "subtitle": "к 10:30", "icon": "lucide:inbox", "color": "chart-1", "start_time": 0, "is_main": False, "to": ["stat"]},
        {"id": "stat", "title": "Статус?", "subtitle": "проверка", "icon": "lucide:circle-help", "color": "chart-4", "start_time": 800, "is_main": True, "to": ["no"]},
        {"id": "no", "title": "Не «Взят в работу»", "subtitle": "висит", "icon": "lucide:bell", "color": "chart-5", "start_time": 1600, "is_main": False, "to": ["boss"]},
        {"id": "boss", "title": "Пуш директору", "subtitle": "в Telegram", "icon": "lucide:user-check", "color": "chart-2", "start_time": 2400, "is_main": False, "to": []}]}),
    ("L5_prj_15", "project", "ComparisonTable", "До <em>и после</em>", "сбоя", {"variant": "tech", "headers": ["", "До сбоя", "После"], "items": [
        {"id": "r1", "label": "Заявка терялась", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Запасной путь", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Фильтр спама", "values": [False, True], "start_time": 1600},
        {"id": "r4", "label": "Триггер руководителю", "values": [False, True], "start_time": 2400}]}),
    ("L5_prj_16", "project", "PremiumChecklist", "Три <em>доработки</em>", "после сбоя", {"variant": "tech", "items": [
        {"label": "Запасной путь в Hubspot", "desc": "тег ручной проверки", "icon": "heroicons:circle-stack", "color": "brand-blue", "start_time": 0},
        {"label": "Фильтр по IP", "desc": "5 заявок в час", "icon": "heroicons:funnel", "color": "brand-amber", "start_time": 800},
        {"label": "Пуш директору к 10:30", "desc": "если статус не сменился", "icon": "heroicons:bell", "color": "brand-green", "start_time": 1600}]}),
    # ─── ГДЕ НЕ РАБОТАЕТ ───────────────────────────────────────────────
    ("L5_whr_1", "where", "AnimatedStatsSlide", "Микробизнесу <em>избыточно</em>", "честно", {"variant": "tech", "stats": [
        {"label": "Средний чек", "value": 50, "suffix": "$", "color": A1, "icon": "heroicons:banknotes", "start_time": 0},
        {"label": "Окупаемость внедрения", "value": 3, "suffix": "года", "color": A3, "icon": "heroicons:calendar-days", "start_time": 800},
        {"label": "Нужна стандартная линейка", "value": 100, "suffix": "%", "color": A2, "icon": "heroicons:list-bullet", "start_time": 1600}]}),
    ("L5_whr_2", "where", "ComparisonTable", "Кому <em>подходит</em>", "а кому нет", {"variant": "tech", "headers": ["", "Подходит", "Не подходит"], "items": [
        {"id": "r1", "label": "Стандартная линейка", "values": [True, False], "start_time": 0},
        {"id": "r2", "label": "Каждый заказ уникален", "values": [False, True], "start_time": 800},
        {"id": "r3", "label": "Оптовые продажи", "values": [True, False], "start_time": 1600},
        {"id": "r4", "label": "Хаос в процессах", "values": [False, True], "start_time": 2400}]}),
    ("L5_whr_3", "where", "QuoteCard", "Честно", "без иллюзий", {"variant": "tech",
        "quote": "Без стандартизированной линейки ИИ-агент просто запутает твоего клиента.",
        "author": "Игорь", "author_title": "IT2B", "source": "граница применимости"}),
    # ─── ВЫВОД ─────────────────────────────────────────────────────────
    ("L5_cnc_1", "conclusion", "QuoteCard", "Порядок <em>прежде</em> автоматизации", "главный принцип", {"variant": "tech",
        "quote": "Софт бессилен перед бардаком в процессах: сначала порядок, а потом уже автоматизация ночи.",
        "author": "Игорь", "author_title": "IT2B", "source": "вывод"}),
    ("L5_cnc_2", "conclusion", "DefinitionBlock", "Автоматизация <em>масштабирует</em>", "термин", {"variant": "tech",
        "term": "Автоматизация процесса",
        "definition": "Масштабирует уже наведённый порядок. Сначала порядок — потом инструмент.",
        "examples": [
            {"id": "d1", "text": "Хаос инструмент только ускорит.", "start_time": 1000},
            {"id": "d2", "text": "Порядок инструмент масштабирует.", "start_time": 2000}],
        "related_terms": ["Порядок", "Процесс", "Ночи"]}),
    # ─── МЯГКИЙ CTA ────────────────────────────────────────────────────
    ("L5_cta_1", "cta", "QuoteCard", "Пришли <em>процесс</em>", "разберу узкие места", {"variant": "tech",
        "quote": "Опиши, как устроена обработка входящих заявок — пришли в Telegram. Найду узкие места.",
        "author": "Игорь", "author_title": "IT2B", "source": "мягкий CTA"}),
    ("L5_cta_2", "cta", "OutroSlide", "", "", {"variant": "tech", **IT2B_OUTRO}),
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
    print(f"Preview: http://localhost:5174/p/{PRES_ID}")


if __name__ == "__main__":
    main()
