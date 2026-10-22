"""ROADMAP V2 · Tier 1 — доменные архетипы (32).

Данные (title / payload / category) для seed_components.py.
Собирается в build() и распаковывается в components_data.
"""

BACKEND, SALES, UI, STATS = "backend", "sales", "ui", "stats"


def _c(slug, title, cat, payload):
    return {"slug": slug, "title": title, "cat": cat, "payload": payload}


def build():
    return [
        # ─── СТРОИТЕЛЬСТВО ───
        _c("BoqSmeta", "Ведомость объёмов работ", SALES, {
            "variant": "tech", "currency": "€",
            "sections": [
                {"code": "01", "name": "Земляные работы", "start_time": 0, "rows": [
                    {"name": "Разработка грунта экскаватором", "unit": "м³", "qty": 1850, "rate": 14.5},
                    {"name": "Обратная засыпка с уплотнением", "unit": "м³", "qty": 640, "rate": 9.8},
                    ]},
                {"code": "02", "name": "Фундаменты и монолит", "start_time": 1000, "rows": [
                    {"name": "Бетон B25, фундаментная плита", "unit": "м³", "qty": 480, "rate": 96.0},
                    {"name": "Арматура A500C", "unit": "т", "qty": 38, "rate": 720.0},
                    ]},
                {"code": "03", "name": "Кровля и фасад", "start_time": 2000, "rows": [
                    {"name": "Мембрана ПВХ, кровля", "unit": "м²", "qty": 3200, "rate": 27.0},
                    {"name": "Навесной фасад, керамогранит", "unit": "м²", "qty": 4600, "rate": 118.0},
                    ]},],
            "subtotal": 735737, "total": 882884,
            "source_note": "Смета по ГЭСН-2024, объект «Северный парк», корпус 3"}),
        _c("ObjectPassport", "Паспорт объекта", UI, {
            "variant": "tech", "image": "",
            "name": "Жилой комплекс «Северный парк», корпус 3",
            "address": "г. Санкт-Петербург, Приморский район, ул. Заречная, 14",
            "status": "Строится", "energy_class": "A",
            "specs": [
                {"label": "Общая площадь", "value": "24 800", "unit": "м²", "start_time": 0},
                {"label": "Этажность", "value": "17", "unit": "эт.", "start_time": 1000},
                {"label": "Квартир", "value": "312", "unit": "шт.", "start_time": 2000},
                {"label": "Готовность", "value": "64", "unit": "%", "start_time": 3000},
                {"label": "Срок сдачи", "value": "IV кв. 2026", "unit": "", "start_time": 4000},
                {"label": "Класс бетона", "value": "B30", "unit": "", "start_time": 5000}],
            "source_note": "Данные проектной документации, стадия РД"}),
        _c("FloorPlanZones", "План с зонами", STATS, {
            "variant": "tech", "plan_image": "",
            "zones": [
                {"x": 22, "y": 34, "label": "Офисный блок", "area": 3200, "value": 4800000, "color": "var(--item-accent-1)", "start_time": 0},
                {"x": 48, "y": 62, "label": "Торговая галерея", "area": 5400, "value": 8100000, "color": "var(--item-accent-2)", "start_time": 1000},
                {"x": 71, "y": 28, "label": "Паркинг", "area": 8600, "value": 4300000, "color": "var(--item-accent-3)", "start_time": 2000},
                {"x": 78, "y": 74, "label": "Технические помещения", "area": 1450, "value": 980000, "color": "var(--item-accent-4)", "start_time": 3000},
                {"x": 38, "y": 82, "label": "Благоустройство", "area": 2200, "value": 640000, "color": "var(--item-accent-1)", "start_time": 4000}],
            "legend": [
                {"label": "Коммерческие площади", "color": "var(--item-accent-1)"},
                {"label": "Общественные зоны", "color": "var(--item-accent-2)"},
                {"label": "Паркинг", "color": "var(--item-accent-3)"},
                {"label": "Технические зоны", "color": "var(--item-accent-4)"}],
            "source_note": "Экспликация помещений, 1 этаж"}),
        _c("HandoverMatrix", "Матрица сдачи", STATS, {
            "variant": "tech",
            "rows": ["Этаж 1", "Этаж 2", "Этаж 3", "Этаж 4", "Кровля"],
            "cols": ["Монолит", "Фасад", "ОВиК", "Электрика", "Отделка"],
            "cells": [
                ["D", "D", "W", "W", "N"],
                ["D", "W", "W", "I", "N"],
                ["D", "W", "I", "N", "N"],
                ["W", "N", "N", "N", "N"],
                ["W", "I", "N", "N", "N"]],
            "states": [
                {"code": "N", "label": "Не начато"},
                {"code": "W", "label": "В работе"},
                {"code": "I", "label": "Замечания"},
                {"code": "D", "label": "Сдано"}],
            "source_note": "Обход комиссии, неделя 34"}),
        _c("SnagBoard", "Реестр замечаний", UI, {
            "variant": "tech",
            "items": [
                {"id": "S-101", "title": "Вертикальная трещина в плите перекрытия", "trade": "Монолит", "location": "Этаж 3, оси Б-В", "severity": "Критично", "due": "24.09.2026", "status": "В работе", "photo": "", "start_time": 0},
                {"id": "S-102", "title": "Не заделаны отверстия после монтажа стояков", "trade": "ОВиК", "location": "Этаж 2, санузлы", "severity": "Высокая", "due": "26.09.2026", "status": "Новая", "photo": "", "start_time": 1000},
                {"id": "S-103", "title": "Отклонение фасадных панелей от вертикали", "trade": "Фасад", "location": "Южный фасад, оси 4-6", "severity": "Высокая", "due": "29.09.2026", "status": "На проверке", "photo": "", "start_time": 2000},
                {"id": "S-104", "title": "Не смонтирован датчик пожарной сигнализации", "trade": "Электрика", "location": "Этаж 4, коридор", "severity": "Средняя", "due": "01.10.2026", "status": "Новая", "photo": "", "start_time": 3000},
                {"id": "S-105", "title": "Протечка в узле ввода водопровода", "trade": "ВК", "location": "Техподполье", "severity": "Критично", "due": "23.09.2026", "status": "Закрыта", "photo": "", "start_time": 4000},
                {"id": "S-106", "title": "Повреждена кромка плитки в местах общего пользования", "trade": "Отделка", "location": "Этаж 1, холл", "severity": "Низкая", "due": "05.10.2026", "status": "Закрыта", "photo": "", "start_time": 5000}],
            "source_note": "Реестр замечаний, обход от 22.09.2026"}),
        _c("SafetyDashboard", "Охрана труда", STATS, {
            "variant": "tech", "days_without": 148,
            "leading": [
                {"label": "Инспекции", "value": 96, "unit": "шт.", "icon": "lucide:clipboard-check", "start_time": 0},
                {"label": "Пятиминутки по ТБ", "value": 42, "unit": "шт.", "icon": "lucide:users", "start_time": 1000},
                {"label": "Обучение", "value": 310, "unit": "чел.-ч", "icon": "lucide:graduation-cap", "start_time": 2000},
                {"label": "Почти-инциденты", "value": 27, "unit": "шт.", "icon": "lucide:eye", "start_time": 3000}],
            "lagging": [
                {"label": "LTIFR", "value": 0.42, "unit": "", "icon": "lucide:activity", "start_time": 0},
                {"label": "TRIR", "value": 1.18, "unit": "", "icon": "lucide:heart-pulse", "start_time": 1000},
                {"label": "Дни нетрудоспособности", "value": 6, "unit": "дн.", "icon": "lucide:calendar-x", "start_time": 2000}],
            "incidents_by_type": [
                {"label": "Падение с высоты", "value": 8},
                {"label": "Удар инструментом", "value": 6},
                {"label": "Порезы", "value": 4},
                {"label": "Электротравма", "value": 2},
                {"label": "ДТП на площадке", "value": 1}],
            "source_note": "Статистика ОТ и ТБ за 9 месяцев 2026"}),
        _c("SiteLogisticsMap", "Стройгенплан и логистика", BACKEND, {
            "variant": "tech", "site_image": "",
            "objects": [
                {"id": "crane1", "x": 30, "y": 32, "type": "crane", "label": "Башенный кран КБ-1", "start_time": 0},
                {"id": "wh1", "x": 72, "y": 24, "type": "warehouse", "label": "Склад материалов", "start_time": 1000},
                {"id": "gate", "x": 88, "y": 58, "type": "gate", "label": "КПП и весовая", "start_time": 2000},
                {"id": "road1", "x": 56, "y": 70, "type": "road", "label": "Внутриплощадочная дорога", "start_time": 3000},
                {"id": "office", "x": 14, "y": 66, "type": "office", "label": "Бытовой городок", "start_time": 4000},
                {"id": "zone1", "x": 44, "y": 48, "type": "zone", "label": "Зона монтажа", "start_time": 5000}],
            "flows": [
                {"from": "gate", "to": "wh1", "label": "поставка"},
                {"from": "wh1", "to": "crane1", "label": "подача"},
                {"from": "crane1", "to": "zone1", "label": "монтаж"},
                {"from": "office", "to": "zone1", "label": "бригада"}],
            "source_note": "Стройгенплан, период монтажа каркаса"}),
        _c("ChangeOrderLog", "Журнал изменений", SALES, {
            "variant": "tech", "currency": "€",
            "orders": [
                {"id": "ИЗ-01", "title": "Усиление фундаментной плиты по результатам экспертизы", "status": "Утверждено", "cost_delta": 84000, "days_delta": 12, "start_time": 0},
                {"id": "ИЗ-02", "title": "Замена остекления на энергоэффективное", "status": "Утверждено", "cost_delta": 126000, "days_delta": 0, "start_time": 1000},
                {"id": "ИЗ-03", "title": "Перенос ввода электрических сетей", "status": "На согласовании", "cost_delta": 47000, "days_delta": 18, "start_time": 2000},
                {"id": "ИЗ-04", "title": "Сокращение объёма благоустройства первой очереди", "status": "Утверждено", "cost_delta": -58000, "days_delta": -6, "start_time": 3000},
                {"id": "ИЗ-05", "title": "Дополнительная шумоизоляция инженерных стояков", "status": "Отклонено", "cost_delta": 32000, "days_delta": 0, "start_time": 4000}],
            "cumulative": {"cost_delta": 231000, "days_delta": 24},
            "source_note": "Журнал изменений, реестр ИЗ, сентябрь 2026"}),

        # ─── ОБРАЗОВАНИЕ ───
        _c("LearningObjectives", "Цели обучения (ABCD)", UI, {
            "variant": "tech",
            "objectives": [
                {"verb": "классифицирует", "behavior": "основные виды доходов и расходов семьи", "condition": "на примерах из личного бюджета", "degree": "не менее 90% верных решений", "level": "Понимание", "start_time": 0},
                {"verb": "рассчитывает", "behavior": "сложный процент по вкладу", "condition": "по формуле и таблице капитализации", "degree": "с точностью до 0,1%", "level": "Применение", "start_time": 1000},
                {"verb": "анализирует", "behavior": "признаки мошеннических финансовых схем", "condition": "на реальных примерах объявлений", "degree": "выявляет минимум три признака обмана", "level": "Анализ", "start_time": 2000},
                {"verb": "составляет", "behavior": "личный финансовый план на год", "condition": "по шаблону с доходами, расходами и целями", "degree": "без дефицита бюджета и с резервом", "level": "Создание", "start_time": 3000}]}),
        _c("BloomLadder", "Лестница Блума", UI, {
            "variant": "tech", "active_level": 3,
            "levels": [
                {"name": "Знание", "verbs": ["называет", "перечисляет", "определяет"], "task": "Назвать ключевые термины темы", "color": "var(--item-accent-1)", "start_time": 0},
                {"name": "Понимание", "verbs": ["объясняет", "описывает", "пересказывает"], "task": "Объяснить своими словами правило", "color": "var(--item-accent-2)", "start_time": 1000},
                {"name": "Применение", "verbs": ["применяет", "решает", "использует"], "task": "Решить типовую задачу по алгоритму", "color": "var(--item-accent-3)", "start_time": 2000},
                {"name": "Анализ", "verbs": ["анализирует", "сравнивает", "разбирает"], "task": "Найти причину ошибки в решении", "color": "var(--item-accent-4)", "start_time": 3000},
                {"name": "Оценка", "verbs": ["оценивает", "критикует", "аргументирует"], "task": "Обосновать выбор метода решения", "color": "var(--item-accent-1)", "start_time": 4000},
                {"name": "Создание", "verbs": ["проектирует", "составляет", "придумывает"], "task": "Разработать собственный проект", "color": "var(--item-accent-2)", "start_time": 5000}]}),
        _c("LessonArc", "Ход урока", UI, {
            "variant": "tech",
            "phases": [
                {"name": "Вовлечение", "minutes": 5, "activity": "Проблемный вопрос и связь темы с опытом учеников", "icon": "lucide:sparkles", "start_time": 0},
                {"name": "Исследование", "minutes": 10, "activity": "Работа в парах с данными и проверка гипотез", "icon": "lucide:search", "start_time": 1000},
                {"name": "Объяснение", "minutes": 12, "activity": "Разбор правила и ключевых понятий с примерами", "icon": "lucide:book-open", "start_time": 2000},
                {"name": "Применение", "minutes": 10, "activity": "Самостоятельное решение задач по образцу", "icon": "lucide:pencil", "start_time": 3000},
                {"name": "Оценивание", "minutes": 8, "activity": "Рефлексия и проверочная работа по критериям", "icon": "lucide:clipboard-check", "start_time": 4000}]}),
        _c("CurriculumMap", "Карта учебной программы", STATS, {
            "variant": "tech", "notation": "irms",
            "courses": ["Математика 7 класс", "Алгебра 8 класс", "Геометрия 8 класс", "Вероятность и статистика"],
            "outcomes": ["Дроби", "Уравнения", "Функции", "Площади", "Вероятность"],
            "map": [
                ["I", "R", "I", "", ""],
                ["M", "M", "R", "I", ""],
                ["", "", "R", "M", "I"],
                ["", "", "", "I", "M"]]}),
        _c("AssessmentBlueprint", "Спецификация теста", STATS, {
            "variant": "tech",
            "rows": [
                {"standard": "ФГОС 7.2", "skill": "Действия с дробями", "dok": 1, "items": 6, "points": 6},
                {"standard": "ФГОС 7.3", "skill": "Линейные уравнения", "dok": 2, "items": 4, "points": 8},
                {"standard": "ФГОС 7.5", "skill": "Анализ функций", "dok": 3, "items": 3, "points": 9},
                {"standard": "ФГОС 7.8", "skill": "Текстовые задачи", "dok": 3, "items": 2, "points": 8},
                {"standard": "ФГОС 7.9", "skill": "Доказательство", "dok": 4, "items": 1, "points": 4}],
            "totals": {"items": 16, "points": 35},
            "rigor_dist": [
                {"label": "DOK 1", "pct": 20},
                {"label": "DOK 2", "pct": 25},
                {"label": "DOK 3", "pct": 40},
                {"label": "DOK 4", "pct": 15}]}),
        _c("ItemAnalysis", "Анализ тестовых заданий", STATS, {
            "variant": "tech",
            "items": [
                {"no": 1, "pct": 92, "difficulty": "Лёгкое", "discrimination": 0.12, "distractors": [{"label": "B", "pct": 5}, {"label": "C", "pct": 2}, {"label": "D", "pct": 1}]},
                {"no": 2, "pct": 78, "difficulty": "Среднее", "discrimination": 0.34, "distractors": [{"label": "A", "pct": 12}, {"label": "C", "pct": 6}, {"label": "D", "pct": 4}]},
                {"no": 3, "pct": 41, "difficulty": "Трудное", "discrimination": 0.48, "distractors": [{"label": "A", "pct": 28}, {"label": "B", "pct": 19}, {"label": "D", "pct": 12}]},
                {"no": 4, "pct": 35, "difficulty": "Трудное", "discrimination": 0.09, "distractors": [{"label": "A", "pct": 31}, {"label": "B", "pct": 22}, {"label": "C", "pct": 12}]},
                {"no": 5, "pct": 88, "difficulty": "Лёгкое", "discrimination": 0.21, "distractors": [{"label": "B", "pct": 7}, {"label": "C", "pct": 3}, {"label": "D", "pct": 2}]}],
            "flags": [
                {"no": 4, "text": "Слабая дискриминация: задание не различает сильных и слабых"},
                {"no": 1, "text": "Слишком лёгкое: проверить формулировку и дистракторы"}]}),
        _c("StudentGrowth", "Динамика роста ученика", STATS, {
            "variant": "tech",
            "points": [
                {"label": "Сентябрь", "value": 42, "start_time": 0},
                {"label": "Декабрь", "value": 58, "start_time": 1000},
                {"label": "Март", "value": 71, "start_time": 2000},
                {"label": "Май", "value": 84, "start_time": 3000}],
            "target": 80,
            "bands": [
                {"label": "Ниже базового", "from": 0, "to": 50, "color": "var(--color-danger)"},
                {"label": "Базовый", "from": 50, "to": 70, "color": "var(--color-warning)"},
                {"label": "Повышенный", "from": 70, "to": 100, "color": "var(--color-success)"}],
            "growth": "+42 п.п."}),
        _c("TimetableGrid", "Сетка расписания", UI, {
            "variant": "tech",
            "days": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"],
            "periods": ["1 пара", "2 пара", "3 пара", "4 пара"],
            "cells": [
                [
                    {"subject": "Алгебра", "teacher": "Иванова Л. П.", "room": "Каб. 204", "color": "var(--color-secondary)", "conflict": False},
                    {"subject": "Геометрия", "teacher": "Петров А. С.", "room": "Каб. 205", "color": "var(--color-success)", "conflict": False},
                    {"subject": "Русский язык", "teacher": "Смирнова О. В.", "room": "Каб. 112", "color": "var(--color-warning)", "conflict": False},
                    {"subject": "Физика", "teacher": "Кузнецов Д. М.", "room": "Лаб. 305", "color": "var(--color-accent)", "conflict": False},
                    {"subject": "История", "teacher": "Орлова Н. И.", "room": "Каб. 108", "color": "var(--color-secondary)", "conflict": False}],
                [
                    {"subject": "Физика", "teacher": "Кузнецов Д. М.", "room": "Лаб. 305", "color": "var(--color-accent)", "conflict": True},
                    {"subject": "Физика", "teacher": "Кузнецов Д. М.", "room": "Лаб. 306", "color": "var(--color-accent)", "conflict": True},
                    {"subject": "Алгебра", "teacher": "Иванова Л. П.", "room": "Каб. 204", "color": "var(--color-secondary)"},
                    {"subject": "Литература", "teacher": "Смирнова О. В.", "room": "Каб. 112", "color": "var(--color-warning)"},
                    {"subject": "Геометрия", "teacher": "Петров А. С.", "room": "Каб. 205", "color": "var(--color-success)"}],
                [
                    {"subject": "Информатика", "teacher": "Волков И. Р.", "room": "Каб. 401", "color": "var(--color-secondary)"},
                    {"subject": "История", "teacher": "Орлова Н. И.", "room": "Каб. 108", "color": "var(--color-success)"},
                    {"subject": "Физика", "teacher": "Кузнецов Д. М.", "room": "Лаб. 305", "color": "var(--color-accent)"},
                    {"subject": "Алгебра", "teacher": "Иванова Л. П.", "room": "Каб. 204", "color": "var(--color-secondary)"},
                    {"subject": "Литература", "teacher": "Смирнова О. В.", "room": "Каб. 112", "color": "var(--color-warning)"}],
                [
                    {"subject": "Геометрия", "teacher": "Петров А. С.", "room": "Каб. 205", "color": "var(--color-success)"},
                    {"subject": "Информатика", "teacher": "Волков И. Р.", "room": "Каб. 401", "color": "var(--color-secondary)"},
                    {"subject": "История", "teacher": "Орлова Н. И.", "room": "Каб. 108", "color": "var(--color-success)"},
                    {"subject": "Русский язык", "teacher": "Смирнова О. В.", "room": "Каб. 112", "color": "var(--color-warning)"},
                    {"subject": "Информатика", "teacher": "Волков И. Р.", "room": "Каб. 401", "color": "var(--color-secondary)"}]]}),

        # ─── ПРОМЫШЛЕННОСТЬ ───
        _c("OeeDashboard", "OEE-дашборд", STATS, {
            "variant": "tech",
            "lines": [
                {"name": "Линия розлива", "availability": 92, "performance": 88, "quality": 99.2, "oee": 80.3, "target": 85, "start_time": 0},
                {"name": "Линия упаковки", "availability": 88, "performance": 91, "quality": 98.5, "oee": 78.9, "target": 82, "start_time": 1000},
                {"name": "Пресс-форма", "availability": 95, "performance": 84, "quality": 99.5, "oee": 79.4, "target": 80, "start_time": 2000},
                {"name": "Сборочный робот", "availability": 97, "performance": 93, "quality": 99.8, "oee": 90.0, "target": 90, "start_time": 3000},
                {"name": "Лазерная резка", "availability": 90, "performance": 86, "quality": 97.5, "oee": 75.5, "target": 80, "start_time": 4000}]}),
        _c("PaceBoard", "Андон-табло темпа", UI, {
            "variant": "tech", "plan": 1200, "actual": 1080, "takt": 18,
            "hourly": [
                {"hour": "08:00", "plan": 200, "actual": 210, "start_time": 0},
                {"hour": "09:00", "plan": 400, "actual": 405, "start_time": 1000},
                {"hour": "10:00", "plan": 600, "actual": 590, "start_time": 2000},
                {"hour": "11:00", "plan": 800, "actual": 760, "start_time": 3000},
                {"hour": "12:00", "plan": 1000, "actual": 900, "start_time": 4000},
                {"hour": "13:00", "plan": 1200, "actual": 1080, "start_time": 5000}],
            "stoppage_sec": 1450, "status": "warning"}),
        _c("ShiftHandover", "Сменный отчёт", UI, {
            "variant": "tech", "shift": "Смена А · 07:00–15:00",
            "output": {"plan": 1200, "actual": 1080, "unit": "шт"},
            "downtime": [
                {"reason": "Замена рулона", "minutes": 18, "start_time": 0},
                {"reason": "Наладка форсунок", "minutes": 12, "start_time": 1000},
                {"reason": "Сбой датчика", "minutes": 25, "start_time": 2000},
                {"reason": "Ожидание сырья", "minutes": 9, "start_time": 3000}],
            "quality": {"fpy": 97.5, "scrap_pct": 1.8, "rework": 14},
            "labor": {"present": 22, "required": 24, "overtime_h": 6},
            "issues": [
                {"text": "Датчик Line-3 требует замены", "owner": "М. Орлов", "start_time": 0},
                {"text": "Задержка поставки ПЭТ-преформ", "owner": "С. Гурьева", "start_time": 1000},
                {"text": "Калибровка весов до 12:00", "owner": "А. Ким", "start_time": 2000}],
            "signoff": [
                {"position": "Мастер смены", "name": "И. Ветров", "start_time": 0},
                {"position": "Начальник ОТК", "name": "Л. Романова", "start_time": 1000},
                {"position": "Механик", "name": "П. Зайцев", "start_time": 2000}]}),
        _c("YamazumiBalance", "Балансировка линии", STATS, {
            "variant": "tech",
            "stations": [
                {"name": "Станция 1 · Резка", "start_time": 0, "elements": [{"label": "Подача", "sec": 8}, {"label": "Резка", "sec": 14}, {"label": "Съём", "sec": 6}]},
                {"name": "Станция 2 · Сварка", "start_time": 1000, "elements": [{"label": "Позиционирование", "sec": 10}, {"label": "Сварка шва", "sec": 26}, {"label": "Контроль", "sec": 7}]},
                {"name": "Станция 3 · Сборка", "start_time": 2000, "elements": [{"label": "Укладка", "sec": 12}, {"label": "Фиксация", "sec": 18}, {"label": "Протяжка", "sec": 4}]},
                {"name": "Станция 4 · Окраска", "start_time": 3000, "elements": [{"label": "Подготовка", "sec": 9}, {"label": "Нанесение", "sec": 16}, {"label": "Сушка", "sec": 12}]},
                {"name": "Станция 5 · Упаковка", "start_time": 4000, "elements": [{"label": "Комплектация", "sec": 11}, {"label": "Упаковка", "sec": 13}, {"label": "Маркировка", "sec": 5}]}],
            "takt_sec": 36, "bottleneck": "Станция 2 · Сварка"}),
        _c("ValueStreamMap", "Карта потока создания ценности", UI, {
            "variant": "tech",
            "processes": [
                {"name": "Штамповка", "cycle_time": 42, "wait_time": 3600, "start_time": 0},
                {"name": "Сварка", "cycle_time": 55, "wait_time": 1800, "start_time": 1000},
                {"name": "Окраска", "cycle_time": 38, "wait_time": 5400, "start_time": 2000},
                {"name": "Сборка", "cycle_time": 64, "wait_time": 900, "start_time": 3000},
                {"name": "Упаковка", "cycle_time": 30, "wait_time": 1200, "start_time": 4000}],
            "flows": [
                {"from": "Штамповка", "to": "Сварка", "label": "партия", "duration_label": "60 мин"},
                {"from": "Сварка", "to": "Окраска", "label": "партия", "duration_label": "30 мин"},
                {"from": "Окраска", "to": "Сборка", "label": "партия", "duration_label": "90 мин"},
                {"from": "Сборка", "to": "Упаковка", "label": "партия", "duration_label": "15 мин"}],
            "va_time": 229, "lead_time": 13129}),
        _c("MachineStatusBoard", "Статусы оборудования", UI, {
            "variant": "tech",
            "machines": [
                {"name": "Пресс-1", "state": "ran", "since": "06:00", "mtbf": 186.0, "mttr": 2.4, "start_time": 0},
                {"name": "Пресс-2", "state": "setup", "since": "12:40", "mtbf": 172.5, "mttr": 3.1, "start_time": 1000},
                {"name": "Робот-сварки A", "state": "ran", "since": "06:00", "mtbf": 240.0, "mttr": 1.2, "start_time": 2000},
                {"name": "Робот-сварки B", "state": "down", "since": "11:05", "mtbf": 158.0, "mttr": 4.6, "start_time": 3000},
                {"name": "Линия окраски", "state": "idle", "since": "13:10", "mtbf": 205.4, "mttr": 2.0, "start_time": 4000},
                {"name": "Упаковщик", "state": "ran", "since": "06:00", "mtbf": 260.8, "mttr": 0.9, "start_time": 5000}]}),
        _c("MaintenanceBoard", "Доска ТОиР", UI, {
            "variant": "tech",
            "orders": [
                {"id": "ППР-1042", "asset": "Пресс-1", "type": "pm", "due": "22.09 14:00", "status": "in_progress", "assignee": "А. Ким", "start_time": 0},
                {"id": "ЗАЯ-318", "asset": "Робот-сварки B", "type": "request", "due": "21.09 18:00", "status": "overdue", "assignee": "П. Зайцев", "start_time": 1000},
                {"id": "КАЛ-077", "asset": "Весы Line-3", "type": "calibration", "due": "23.09 09:00", "status": "planned", "assignee": "С. Гурьева", "start_time": 2000},
                {"id": "ППР-1039", "asset": "Линия окраски", "type": "pm", "due": "21.09 12:00", "status": "overdue", "assignee": "М. Орлов", "start_time": 3000},
                {"id": "ЗАП-205", "asset": "Пресс-2", "type": "spare", "due": "24.09 11:00", "status": "planned", "assignee": "И. Ветров", "start_time": 4000},
                {"id": "ППР-1030", "asset": "Упаковщик", "type": "pm", "due": "20.09 10:00", "status": "done", "assignee": "А. Ким", "start_time": 5000}],
            "overdue": 2}),
        _c("AbcXyzMatrix", "ABC/XYZ-матрица", STATS, {
            "variant": "tech",
            "items": [
                {"sku": "SKU-1001", "value": 42000, "variability": 6, "class": "AX", "start_time": 0},
                {"sku": "SKU-1002", "value": 31000, "variability": 12, "class": "AY", "start_time": 1000},
                {"sku": "SKU-1003", "value": 18000, "variability": 28, "class": "AZ", "start_time": 2000},
                {"sku": "SKU-1004", "value": 9000, "variability": 8, "class": "BX", "start_time": 3000},
                {"sku": "SKU-1005", "value": 5200, "variability": 18, "class": "BY", "start_time": 4000},
                {"sku": "SKU-1006", "value": 3100, "variability": 41, "class": "CZ", "start_time": 5000}],
            "thresholds": {"a": 80, "b": 95, "x": 10, "y": 25}}),

        # ─── B2B ───
        _c("PipelineBoard", "Воронка пайплайна", SALES, {
            "variant": "tech", "coverage": 3.4, "currency": "€",
            "stages": [
                {"name": "Лиды", "count": 420, "value": 180000, "conversion": 100, "aging": 4, "start_time": 0},
                {"name": "Квалификация", "count": 210, "value": 145000, "conversion": 50, "aging": 9, "start_time": 1000},
                {"name": "Демо", "count": 118, "value": 98000, "conversion": 56, "aging": 12, "start_time": 2000},
                {"name": "Предложение", "count": 64, "value": 72000, "conversion": 54, "aging": 16, "start_time": 3000},
                {"name": "Сделка", "count": 31, "value": 51000, "conversion": 48, "aging": 7, "start_time": 4000}]}),
        _c("MarketSizing", "Объём рынка (TAM/SAM/SOM)", SALES, {
            "variant": "tech", "currency": "€",
            "source_note": "Источник: отраслевой отчёт 2025; SAM — ICP-фильтр, SOM — достижимая доля за 3 года",
            "layers": [
                {"name": "TAM", "value": 2400000000, "growth": 12, "start_time": 0},
                {"name": "SAM", "value": 480000000, "growth": 18, "start_time": 1000},
                {"name": "SOM", "value": 64000000, "growth": 27, "start_time": 2000}]}),
        _c("RevenueWaterfall", "Мост выручки", SALES, {
            "variant": "tech", "start": 120, "end": 148,
            "steps": [
                {"label": "Новые", "delta": 45, "type": "new", "start_time": 0},
                {"label": "Расширение", "delta": 28, "type": "expansion", "start_time": 1000},
                {"label": "Отток", "delta": -33, "type": "churn", "start_time": 2000},
                {"label": "Даунгрейд", "delta": -12, "type": "downgrade", "start_time": 3000}]}),
        _c("CohortRetention", "Когортное удержание", SALES, {
            "variant": "tech", "metric": "nrr",
            "cohorts": ["Янв", "Фев", "Мар", "Апр", "Май"],
            "values": [
                [100, 104, 112, 118, 121],
                [100, 106, 115, 120, None],
                [100, 103, 111, None, None],
                [100, 105, None, None, None],
                [100, None, None, None, None]]}),
        _c("OrgChart", "Оргструктура", UI, {
            "variant": "tech", "layout": "vertical",
            "nodes": [
                {"id": "ceo", "name": "Анна Ковалёва", "title": "CEO", "headcount": 1, "children": [
                    {"id": "sales", "name": "Игорь Петров", "title": "Директор по продажам", "headcount": 18, "children": [
                        {"id": "sdr", "name": "Команда SDR", "title": "Лидогенерация" , "headcount": 8},
                        {"id": "ae", "name": "Команда AE", "title": "Закрытие сделок" , "headcount": 10}]},
                    {"id": "product", "name": "Мария Соколова", "title": "CPO", "headcount": 22, "children": [
                        {"id": "design", "name": "Продукт-дизайн", "title": "UX/UI" , "headcount": 6},
                        {"id": "engineering", "name": "Разработка", "title": "Backend и Frontend" , "headcount": 16}]},
                    {"id": "finance", "name": "Дмитрий Орлов", "title": "CFO" , "headcount": 5}]}]}),
        _c("UnitEconomics", "Юнит-экономика", SALES, {
            "variant": "tech", "payback_months": 14,
            "metrics": [
                {"label": "CAC", "value": 4200, "unit": "€", "target": 3500, "start_time": 0},
                {"label": "LTV", "value": 26400, "unit": "€", "target": 24000, "start_time": 1000},
                {"label": "LTV / CAC", "value": 6.3, "unit": "×", "target": 5.0, "start_time": 2000},
                {"label": "Gross Margin", "value": 78, "unit": "%", "target": 75, "start_time": 3000},
                {"label": "Magic Number", "value": 1.4, "unit": "×", "target": 1.2, "start_time": 4000}]}),
        _c("UseOfFunds", "Распределение инвестиций", SALES, {
            "variant": "tech", "total": 3000000,
            "buckets": [
                {"label": "Разработка продукта", "amount": 1350000, "color": "var(--item-accent-1)", "start_time": 0},
                {"label": "Продажи и маркетинг", "amount": 900000, "color": "var(--item-accent-2)", "start_time": 1000},
                {"label": "Найм и команда", "amount": 450000, "color": "var(--item-accent-3)", "start_time": 2000},
                {"label": "Инфраструктура", "amount": 300000, "color": "var(--item-accent-4)", "start_time": 3000}],
            "milestones": [
                {"label": "Релиз v2.0", "period": "Q1 2026", "start_time": 4000},
                {"label": "Первые 500 клиентов", "period": "Q3 2026", "start_time": 5000},
                {"label": "Выход на прибыльность", "period": "Q4 2027", "start_time": 6000}]}),
        _c("JourneyMap", "Карта клиентского пути", SALES, {
            "variant": "tech",
            "stages": [
                {"name": "Осознание", "kpi": "CPL 42 €", "touchpoints": ["Реклама в поиске", "Публикации в отраслевых медиа"], "pains": ["Не понимает, чем мы отличаемся от конкурентов"], "start_time": 0},
                {"name": "Рассмотрение", "kpi": "Демо → пилот 38%", "touchpoints": ["Сайт и кейсы", "Вебинар с продуктом"], "pains": ["Непонятная цена и объём внедрения"], "start_time": 1000},
                {"name": "Пилот", "kpi": "Time-to-value 14 дней", "touchpoints": ["Onboarding-встреча", "Тестовый доступ"], "pains": ["Долгая настройка интеграций"], "start_time": 2000},
                {"name": "Внедрение", "kpi": "NRR 118%", "touchpoints": ["Обучение команды", "Чек-ин с CSM"], "pains": ["Сопротивление сотрудников новому процессу"], "start_time": 3000}]}),
    ]
