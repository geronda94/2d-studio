"""
Генератор example для компонентов (Итерация 1.2).

Берёт реальный заполненный payload из презентации 4 (эталонный «трушный» вид),
чистит его от служебного шума (пустые sfx) и кладёт в components.example.
Если у компонента нет слайда в /p/4 — фолбэк на default_payload.

Запуск: python scripts/generate_examples.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models
from sqlalchemy import text
from scripts._ensure_columns import ensure_columns

# Эталонная презентация, от которой берём примеры
REFERENCE_PRESENTATION_ID = 4

# Реалистичный HTML-контент для BrowserMockup (сайдбар/навигация, KPI, настоящий
# график, таблица). Инлайн-стили + prefixed-классы, чтобы не зависеть от JIT-скан
# Tailwind (v-html не попадает в content-скан) и корректно адаптироваться на мобиле.
_BROWSER_DASHBOARD_HTML = """
<style>
.bmx{display:flex;min-height:100%;width:100%;color:var(--text-primary);font-family:inherit}
.bmx *{box-sizing:border-box}
.bmx-side{display:none;flex-direction:column;gap:2px;width:196px;flex-shrink:0;padding:16px 12px;border-right:1px solid var(--item-border);background:color-mix(in srgb, var(--text-primary) 3%, transparent)}
.bmx-logo{display:flex;align-items:center;gap:9px;margin-bottom:14px;padding:0 6px}
.bmx-logo i{width:26px;height:26px;border-radius:8px;background:var(--color-secondary);display:block}
.bmx-logo span{font-weight:700;font-size:14px}
.bmx-nav{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;font-size:13px;color:var(--text-secondary)}
.bmx-nav.on{background:color-mix(in srgb, var(--color-secondary) 16%, transparent);color:var(--text-primary);font-weight:600}
.bmx-nav b{width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.7;display:block}
.bmx-main{flex:1;min-width:0;display:flex;flex-direction:column}
.bmx-head{display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--item-border)}
.bmx-burger{display:flex;flex-direction:column;gap:3px}
.bmx-burger s{width:16px;height:2px;background:var(--text-muted);display:block;border-radius:2px}
.bmx-head h2{margin:0;font-size:17px;font-weight:700}
.bmx-head p{margin:2px 0 0;font-size:12px;color:var(--text-muted)}
.bmx-search{margin-left:auto;font-size:12px;color:var(--text-muted);border:1px solid var(--item-border);border-radius:999px;padding:6px 14px}
.bmx-ava{width:30px;height:30px;border-radius:50%;background:var(--color-accent);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--bg-base)}
.bmx-body{flex:1;min-height:0;display:flex;flex-direction:column;gap:14px;padding:16px 18px}
.bmx-kpis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.bmx-card{background:color-mix(in srgb, var(--text-primary) 4%, transparent);border:1px solid var(--item-border);border-radius:12px;padding:12px 14px}
.bmx-kpi .l{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-muted)}
.bmx-kpi .v{font-size:24px;font-weight:800;margin-top:4px}
.bmx-kpi .d{font-size:11px;margin-top:2px;font-weight:600}
.bmx-grid{display:grid;grid-template-columns:1fr;gap:14px;flex:1;min-height:0}
.bmx-chart{display:flex;align-items:flex-end;gap:7px;height:104px;margin-top:12px}
.bmx-bar{flex:1;border-radius:5px 5px 0 0;background:linear-gradient(180deg,var(--color-secondary),color-mix(in srgb, var(--color-secondary) 25%, transparent))}
.bmx-bar.hi{background:linear-gradient(180deg,var(--color-success),color-mix(in srgb, var(--color-success) 25%, transparent))}
.bmx-row{display:flex;align-items:center;justify-content:space-between;font-size:12px;padding:7px 0;border-bottom:1px solid color-mix(in srgb, var(--text-primary) 7%, transparent)}
.bmx-row:last-child{border-bottom:0}
.bmx-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:8px}
.bmx-tbl{width:100%;border-collapse:collapse;font-size:12px}
.bmx-tbl th{text-align:left;font-weight:600;color:var(--text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.05em;padding:0 0 7px}
.bmx-tbl td{padding:7px 0;border-top:1px solid color-mix(in srgb, var(--text-primary) 7%, transparent)}
.bmx-pill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px}
@media(min-width:768px){
 .bmx-side{display:flex}
 .bmx-burger{display:none}
 .bmx-kpis{grid-template-columns:repeat(4,minmax(0,1fr))}
 .bmx-grid{grid-template-columns:1.6fr 1fr}
}
</style>
<div class="bmx">
 <aside class="bmx-side">
  <div class="bmx-logo"><i></i><span>IT2B Cloud</span></div>
  <div class="bmx-nav on"><b></b>Обзор</div>
  <div class="bmx-nav"><b></b>Сделки</div>
  <div class="bmx-nav"><b></b>Клиенты</div>
  <div class="bmx-nav"><b></b>Аналитика</div>
  <div class="bmx-nav"><b></b>Настройки</div>
 </aside>
 <div class="bmx-main">
  <header class="bmx-head">
   <div class="bmx-burger"><s></s><s></s><s></s></div>
   <div><h2>Обзор продаж</h2><p>Обновлено 5 минут назад</p></div>
   <div class="bmx-search">Поиск по клиентам</div>
   <div class="bmx-ava">IT</div>
  </header>
  <div class="bmx-body">
   <div class="bmx-kpis">
    <div class="bmx-card bmx-kpi"><div class="l">Выручка</div><div class="v">284 500 €</div><div class="d" style="color:var(--color-success)">+12,4%</div></div>
    <div class="bmx-card bmx-kpi"><div class="l">Сделки</div><div class="v">1 248</div><div class="d" style="color:var(--color-success)">+8,1%</div></div>
    <div class="bmx-card bmx-kpi"><div class="l">Конверсия</div><div class="v">38%</div><div class="d" style="color:var(--color-warning)">−2,0%</div></div>
    <div class="bmx-card bmx-kpi"><div class="l">Ответ ИИ</div><div class="v">73%</div><div class="d" style="color:var(--color-success)">+21%</div></div>
   </div>
   <div class="bmx-grid">
    <div class="bmx-card">
     <div style="display:flex;align-items:center;justify-content:space-between">
      <strong style="font-size:13px">Выручка по месяцам</strong>
      <span style="font-size:11px;color:var(--text-muted)">2026</span>
     </div>
     <div class="bmx-chart">
      <div class="bmx-bar" style="height:42%"></div>
      <div class="bmx-bar" style="height:58%"></div>
      <div class="bmx-bar" style="height:50%"></div>
      <div class="bmx-bar hi" style="height:74%"></div>
      <div class="bmx-bar" style="height:66%"></div>
      <div class="bmx-bar hi" style="height:88%"></div>
      <div class="bmx-bar" style="height:80%"></div>
     </div>
    </div>
    <div class="bmx-card">
     <strong style="font-size:13px">Топ клиентов</strong>
     <div style="margin-top:8px">
      <div class="bmx-row"><span><i class="bmx-dot" style="background:var(--color-secondary)"></i>ООО «Ромашка»</span><b>82 400 €</b></div>
      <div class="bmx-row"><span><i class="bmx-dot" style="background:var(--color-success)"></i>Nordwind GmbH</span><b>64 900 €</b></div>
      <div class="bmx-row"><span><i class="bmx-dot" style="background:var(--color-warning)"></i>Sigma Logistics</span><b>51 200 €</b></div>
      <div class="bmx-row"><span><i class="bmx-dot" style="background:var(--color-accent)"></i>Alpine Retail</span><b>43 750 €</b></div>
     </div>
    </div>
   </div>
   <div class="bmx-card">
    <table class="bmx-tbl">
     <thead><tr><th>Сделка</th><th>Менеджер</th><th>Сумма</th><th>Статус</th></tr></thead>
     <tbody>
      <tr><td>Внедрение CRM</td><td>Дмитрий Волков</td><td>120 000 €</td><td><span class="bmx-pill" style="color:var(--color-success);background:color-mix(in srgb, var(--color-success) 14%, transparent)">Оплачено</span></td></tr>
      <tr><td>Интеграция 1С</td><td>Елена Морозова</td><td>86 400 €</td><td><span class="bmx-pill" style="color:var(--color-secondary);background:color-mix(in srgb, var(--color-secondary) 14%, transparent)">В работе</span></td></tr>
      <tr><td>Аудит процессов</td><td>Артём Соколов</td><td>54 000 €</td><td><span class="bmx-pill" style="color:var(--color-warning);background:color-mix(in srgb, var(--color-warning) 14%, transparent)">Договор</span></td></tr>
     </tbody>
    </table>
   </div>
  </div>
 </div>
</div>
""".strip()

# Второй экран — воронка сделок (реальный интерфейс, не заглушка).
_BROWSER_DEALS_HTML = """
<style>
.bmd{display:flex;min-height:100%;width:100%;flex-direction:column;gap:14px;padding:18px;color:var(--text-primary);font-family:inherit}
.bmd *{box-sizing:border-box}
.bmd-head{display:flex;align-items:center;gap:12px}
.bmd-head h2{margin:0;font-size:17px;font-weight:700}
.bmd-head p{margin:2px 0 0;font-size:12px;color:var(--text-muted)}
.bmd-add{margin-left:auto;font-size:12px;font-weight:600;border-radius:9px;padding:7px 14px;background:var(--color-secondary);color:var(--bg-base)}
.bmd-cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;flex:1;min-height:0}
.bmd-col{background:color-mix(in srgb, var(--text-primary) 3%, transparent);border:1px solid var(--item-border);border-radius:12px;padding:10px}
.bmd-col h3{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted)}
.bmd-card{background:color-mix(in srgb, var(--text-primary) 6%, transparent);border:1px solid var(--item-border);border-radius:9px;padding:9px 10px;margin-bottom:8px}
.bmd-card b{font-size:12.5px;display:block}
.bmd-card span{font-size:11px;color:var(--text-muted)}
.bmd-card em{font-size:11.5px;font-style:normal;font-weight:700;display:block;margin-top:4px}
@media(min-width:768px){.bmd-cols{grid-template-columns:repeat(4,minmax(0,1fr))}}
</style>
<div class="bmd">
 <div class="bmd-head">
  <div><h2>Воронка сделок</h2><p>Активные возможности</p></div>
  <div class="bmd-add">Новая сделка</div>
 </div>
 <div class="bmd-cols">
  <div class="bmd-col"><h3>Новые · 4</h3>
   <div class="bmd-card"><b>Alpine Retail</b><span>Входящая заявка</span><em style="color:var(--color-secondary)">32 000 €</em></div>
   <div class="bmd-card"><b>Delta Media</b><span>Квалификация</span><em style="color:var(--color-secondary)">18 500 €</em></div>
  </div>
  <div class="bmd-col"><h3>Переговоры · 3</h3>
   <div class="bmd-card"><b>Nordwind GmbH</b><span>Обсуждение SLA</span><em style="color:var(--color-warning)">64 900 €</em></div>
   <div class="bmd-card"><b>Sigma Logistics</b><span>Пилот</span><em style="color:var(--color-warning)">51 200 €</em></div>
  </div>
  <div class="bmd-col"><h3>Договор · 2</h3>
   <div class="bmd-card"><b>ООО «Ромашка»</b><span>Юристы</span><em style="color:var(--color-accent)">82 400 €</em></div>
  </div>
  <div class="bmd-col"><h3>Оплачено · 5</h3>
   <div class="bmd-card"><b>Внедрение CRM</b><span>Закрыта</span><em style="color:var(--color-success)">120 000 €</em></div>
   <div class="bmd-card"><b>Интеграция 1С</b><span>Закрыта</span><em style="color:var(--color-success)">86 400 €</em></div>
  </div>
 </div>
</div>
""".strip()

# Курированные примеры (Roadmap P1–P4). Приоритет: curated → /p/4 → default_payload.
# Показывают «живое» применение компонента, отличаются от default_payload-каркаса.
# Только токены (без hex), ≤4 акцентов, start_time нарастающе (шаг ≥800мс).
CURATED_EXAMPLES = {
    "AnimatedStatsSlide": {
        "variant": "tech",
        "stats": [
            {"label": "Конверсия", "value": 42, "suffix": "%", "color": "var(--color-success)", "icon": "lucide:trending-up", "start_time": 0},
            {"label": "Отказы", "value": -15, "suffix": "%", "color": "var(--color-danger)", "icon": "lucide:trending-down", "start_time": 900},
            {"label": "Доход", "value": 5, "suffix": "M €", "color": "var(--color-warning)", "icon": "lucide:euro", "start_time": 1800}
        ]
    },
    "SpecTable": {
        "variant": "tech",
        "title": "Интеграция с 1С",
        "subtitle": "Технические параметры",
        "columns": ["Параметр", "Значение"],
        "rows": [
            {"id": "s1", "label": "Протокол", "value": "REST + Webhooks", "icon": "lucide:plug", "color": "var(--color-secondary)", "highlight": True, "start_time": 0},
            {"id": "s2", "label": "Частота обмена", "value": "раз в 5 минут", "icon": "lucide:refresh-cw", "color": "var(--color-success)", "start_time": 900},
            {"id": "s3", "label": "Объём данных", "value": "до 50 000 строк", "icon": "lucide:database", "color": "var(--color-warning)", "start_time": 1800},
            {"id": "s4", "label": "Отказоустойчивость", "value": "retry + очередь", "icon": "lucide:shield-check", "color": "var(--color-accent)", "start_time": 2700}
        ],
        "highlight_rows": ["s1"]
    },
    "KpiDashboard": {
        "variant": "tech",
        "title": "Поддержка под контролем",
        "subtitle": "Метрики клиентского сервиса",
        "metrics": [
            {"id": "k1", "label": "Первый ответ", "value": "28", "unit": "сек", "trend": "-62%", "color": "var(--color-success)", "icon": "heroicons:clock", "sparkline": [95, 80, 64, 50, 40, 33, 28], "start_time": 0},
            {"id": "k2", "label": "CSAT", "value": "4.8", "unit": "/5", "trend": "+0.4", "color": "var(--color-secondary)", "icon": "heroicons:face-smile", "sparkline": [4.1, 4.2, 4.4, 4.5, 4.6, 4.7, 4.8], "start_time": 900},
            {"id": "k3", "label": "Решено ИИ", "value": "73", "unit": "%", "trend": "+21%", "color": "var(--color-accent)", "icon": "heroicons:cpu-chip", "sparkline": [40, 46, 52, 58, 64, 69, 73], "start_time": 1800},
            {"id": "k4", "label": "Тикетов в день", "value": "1 240", "unit": "", "trend": "-8%", "color": "var(--color-warning)", "icon": "heroicons:inbox", "sparkline": [1500, 1470, 1420, 1380, 1330, 1280, 1240], "start_time": 2700}
        ]
    },
    "GanttChart": {
        "variant": "tech",
        "title": "Внедрение CRM",
        "subtitle": "10 недель",
        "tasks": [
            {"id": "g1", "name": "Аудит процессов", "start": 0, "end": 18, "progress": 100, "color": "var(--color-success)", "icon": "heroicons:clipboard-document-list", "start_time": 0},
            {"id": "g2", "name": "Миграция данных", "start": 14, "end": 52, "progress": 70, "color": "var(--color-secondary)", "icon": "heroicons:circle-stack", "start_time": 900},
            {"id": "g3", "name": "Интеграции", "start": 46, "end": 84, "progress": 30, "color": "var(--color-primary)", "icon": "heroicons:link", "start_time": 1800},
            {"id": "g4", "name": "Обучение команды", "start": 80, "end": 100, "progress": 0, "color": "var(--color-warning)", "icon": "heroicons:academic-cap", "start_time": 2700}
        ],
        "milestones": [
            {"id": "gm1", "label": "Пилот", "at": 52, "color": "var(--color-warning)", "start_time": 3600},
            {"id": "gm2", "label": "Запуск", "at": 100, "color": "var(--color-success)", "start_time": 4500}
        ]
    },
    "TeamGrid": {
        "variant": "tech",
        "title": "Команда внедрения",
        "subtitle": "Выделенная группа",
        "members": [
            {"id": "t1", "name": "Дмитрий Волков", "title": "Project Lead", "color": "var(--color-secondary)", "contacts": [{"icon": "heroicons:envelope", "text": "dmitry@company.eu"}], "start_time": 0},
            {"id": "t2", "name": "Елена Морозова", "title": "Data Engineer", "color": "var(--color-success)", "contacts": [{"icon": "heroicons:envelope", "text": "elena@company.eu"}], "start_time": 900},
            {"id": "t3", "name": "Артём Соколов", "title": "Solution Architect", "color": "var(--color-warning)", "contacts": [{"icon": "heroicons:paper-airplane", "text": "@asokolov"}], "start_time": 1800}
        ]
    },
    "PricingTable": {
        "variant": "tech",
        "title": "Поддержка и SLA",
        "subtitle": "Три уровня сервиса",
        "plans": [
            {"id": "pr1", "name": "Базовый", "description": "Для небольших команд", "price": "290", "period": "€/мес", "features": ["Ответ за 8 часов", "Email-канал", "База знаний"], "cta": "Выбрать", "highlighted": False, "color": "var(--color-secondary)", "start_time": 0},
            {"id": "pr2", "name": "Стандарт", "description": "Рабочая лошадка", "price": "790", "period": "€/мес", "badge": "Хит", "features": ["Ответ за 2 часа", "Телефон и чат", "Дежурный инженер", "Отчёты SLA"], "cta": "Выбрать", "highlighted": True, "color": "var(--color-secondary)", "start_time": 900},
            {"id": "pr3", "name": "Премиум", "description": "Критичные системы", "price": "2 400", "period": "€/мес", "features": ["Ответ за 15 минут", "Выделенный инженер", "SLA 99.99%", "Разбор инцидентов"], "cta": "Обсудить", "highlighted": False, "color": "var(--color-accent)", "start_time": 1800}
        ]
    },
    "FlashCards": {
        "variant": "tech",
        "title": "Термины ИИ",
        "subtitle": "Короткая разминка",
        "cards": [
            {"id": "f1", "front": "Что такое LLM?", "back": "Large Language Model — большая языковая модель, обученная предсказывать следующий токен.", "icon": "heroicons:language", "color": "var(--color-secondary)", "start_time": 0},
            {"id": "f2", "front": "Что такое эмбеддинг?", "back": "Числовой вектор, кодирующий смысл текста для поиска и сравнения.", "icon": "heroicons:variable", "color": "var(--color-success)", "start_time": 2500},
            {"id": "f3", "front": "Что такое промпт?", "back": "Инструкция модели на естественном языке, задающая задачу и контекст.", "icon": "heroicons:chat-bubble-left", "color": "var(--color-warning)", "start_time": 5000}
        ]
    },
    "QuizSlide": {
        "variant": "tech",
        "question": "Что означает аббревиатура RAG?",
        "options": [
            {"id": "q1", "text": "Real-time API Gateway", "correct": False, "start_time": 0},
            {"id": "q2", "text": "Retrieval-Augmented Generation", "correct": True, "start_time": 800},
            {"id": "q3", "text": "Random Answer Generator", "correct": False, "start_time": 1600},
            {"id": "q4", "text": "Rapid Agent Graph", "correct": False, "start_time": 2400}
        ],
        "explanation": "RAG — генерация с опорой на поиск: модель дополняет ответ фактами из базы знаний.",
        "reveal_time": 5000
    },
    "StepByStep": {
        "variant": "tech",
        "title": "Подключение к API",
        "subtitle": "Пять шагов",
        "layout": "horizontal",
        "steps": [
            {"id": "st1", "number": 1, "title": "Ключ", "description": "Получите токен в личном кабинете.", "icon": "heroicons:key", "color": "var(--color-secondary)", "start_time": 0},
            {"id": "st2", "number": 2, "title": "Запрос", "description": "Отправьте первый POST-запрос.", "icon": "heroicons:paper-airplane", "color": "var(--color-success)", "start_time": 1000},
            {"id": "st3", "number": 3, "title": "Ответ", "description": "Разберите JSON-ответ.", "icon": "heroicons:code-bracket", "color": "var(--color-warning)", "start_time": 2000},
            {"id": "st4", "number": 4, "title": "Вебхук", "description": "Подпишитесь на события.", "icon": "heroicons:bell-alert", "color": "var(--color-accent)", "start_time": 3000},
            {"id": "st5", "number": 5, "title": "Прод", "description": "Перенесите интеграцию в прод.", "icon": "heroicons:rocket-launch", "color": "var(--color-success)", "start_time": 4000}
        ]
    },
    "DefinitionBlock": {
        "variant": "tech",
        "term": "Галлюцинация",
        "definition": "Уверенный, но фактически неверный ответ языковой модели, не опирающийся на проверенные источники.",
        "examples": [
            {"id": "d1", "text": "Модель выдумывает несуществующую ссылку или статью.", "start_time": 1000},
            {"id": "d2", "text": "Придумывает точные цифры, которых нет в базе.", "start_time": 2000}
        ],
        "related_terms": ["RAG", "Фактчекинг", "Температура"]
    },
    "KnowledgeGraph": {
        "variant": "tech",
        "concepts": [
            {"id": "kg0", "label": "Магазин", "icon": "heroicons:shopping-bag", "color": "var(--color-secondary)", "is_main": True, "start_time": 0},
            {"id": "kg1", "label": "Платежи", "icon": "heroicons:credit-card", "color": "var(--color-success)", "start_time": 800},
            {"id": "kg2", "label": "Доставка", "icon": "heroicons:truck", "color": "var(--color-warning)", "start_time": 1600},
            {"id": "kg3", "label": "Аналитика", "icon": "heroicons:chart-bar", "color": "var(--color-accent)", "start_time": 2400},
            {"id": "kg4", "label": "Поддержка", "icon": "heroicons:lifebuoy", "color": "var(--color-secondary)", "start_time": 3200}
        ],
        "connections": [
            {"from": "kg0", "to": "kg1", "label": "оплата", "start_time": 900},
            {"from": "kg0", "to": "kg2", "label": "логистика", "start_time": 1700},
            {"from": "kg0", "to": "kg3", "label": "данные", "start_time": 2500},
            {"from": "kg0", "to": "kg4", "label": "тикеты", "start_time": 3300}
        ]
    },
    "TimelineEras": {
        "variant": "tech",
        "title": "Эволюция веба",
        "subtitle": "Четыре поколения",
        "eras": [
            {"id": "e1", "name": "Web 1.0", "period": "1991", "icon": "heroicons:document", "color": "var(--color-secondary)", "description": "Статичные страницы.", "start_time": 0},
            {"id": "e2", "name": "Web 2.0", "period": "2004", "icon": "heroicons:users", "color": "var(--color-success)", "description": "Соцсети и UGC.", "start_time": 1000},
            {"id": "e3", "name": "Web 3.0", "period": "2016", "icon": "heroicons:cube-transparent", "color": "var(--color-warning)", "description": "Блокчейн и данные.", "start_time": 2000},
            {"id": "e4", "name": "Web 4.0", "period": "2024", "icon": "heroicons:sparkles", "color": "var(--color-accent)", "description": "ИИ-агенты и семантики.", "start_time": 3000}
        ]
    },
    "QuoteCard": {
        "variant": "tech",
        "quote": "Простота — это высшая степень изощрённости.",
        "author": "Леонардо да Винчи",
        "author_title": "Художник и изобретатель",
        "source": "Записные книжки"
    },
    "MapVisualization": {
        "variant": "tech",
        "title": "Складская сеть",
        "subtitle": "Распределение по стране",
        "points": [
            {"id": "mp1", "label": "Москва", "x": 26, "y": 44, "color": "var(--color-secondary)", "icon": "heroicons:building-office-2", "start_time": 0},
            {"id": "mp2", "label": "Казань", "x": 40, "y": 54, "color": "var(--color-success)", "icon": "heroicons:building-office-2", "start_time": 900},
            {"id": "mp3", "label": "Екатеринбург", "x": 58, "y": 50, "color": "var(--color-warning)", "icon": "heroicons:building-office-2", "start_time": 1800},
            {"id": "mp4", "label": "Новосибирск", "x": 76, "y": 56, "color": "var(--color-accent)", "icon": "heroicons:building-office-2", "start_time": 2700}
        ],
        "connections": [
            {"from": "mp1", "to": "mp2", "start_time": 1000},
            {"from": "mp2", "to": "mp3", "start_time": 1900},
            {"from": "mp3", "to": "mp4", "start_time": 2800}
        ]
    },
    "HistoricalCompare": {
        "variant": "tech",
        "transition_style": "slide",
        "before": {"label": "Раньше", "caption": "Онбординг — 3 письма и звонок менеджера через неделю.", "image": "", "start_time": 0},
        "after": {"label": "Теперь", "caption": "Онбординг — персональный ИИ-гид в первый же день.", "image": "", "start_time": 1500}
    },
    "CircularGauge": {
        "variant": "tech",
        "title": "Цели квартала",
        "subtitle": "Выполнение плана",
        "gauges": [
            {"id": "cg1", "value": 118, "max": 100, "unit": "%", "label": "План продаж", "color": "var(--color-success)", "icon": "heroicons:banknotes", "start_time": 0},
            {"id": "cg2", "value": 71, "max": 100, "unit": "%", "label": "Удержание", "color": "var(--color-secondary)", "icon": "heroicons:arrow-path", "start_time": 900},
            {"id": "cg3", "value": 89, "max": 100, "unit": "%", "label": "NPS", "color": "var(--color-warning)", "icon": "heroicons:face-smile", "start_time": 1800}
        ]
    },
    "SustainabilityTimeline": {
        "variant": "tech",
        "title": "Путь к zero waste",
        "subtitle": "Пять лет",
        "milestones": [
            {"id": "z1", "year": "2021", "event": "Старт программы", "impact": "Базовая линия отходов.", "icon": "heroicons:play", "color": "var(--color-secondary)", "start_time": 0},
            {"id": "z2", "year": "2023", "event": "Раздельный сбор", "impact": "Переработка 60%.", "icon": "heroicons:arrow-path", "color": "var(--color-success)", "start_time": 1000},
            {"id": "z3", "year": "2025", "event": "Компостирование", "impact": "Органика — в оборот.", "icon": "heroicons:sparkles", "color": "var(--color-warning)", "start_time": 2000},
            {"id": "z4", "year": "2026", "event": "Zero waste статус", "impact": "99% отходов переработано.", "icon": "heroicons:globe-europe-africa", "color": "var(--color-accent)", "start_time": 3000}
        ]
    },
    "ValuesTable": {
        "variant": "tech",
        "title": "Принципы инженерии",
        "subtitle": "Принцип → практика → результат",
        "columns": ["Принцип", "Практика", "Результат"],
        "rows": [
            {"id": "vt1", "value": "Простота", "practice": "Минимум абстракций и слоёв.", "result": "Быстрее онбординг.", "icon": "heroicons:minus-circle", "color": "var(--color-secondary)", "start_time": 0},
            {"id": "vt2", "value": "Надёжность", "practice": "Тесты и наблюдаемость по умолчанию.", "result": "Меньше инцидентов.", "icon": "heroicons:shield-check", "color": "var(--color-success)", "start_time": 900},
            {"id": "vt3", "value": "Скорость", "practice": "Малые релизы каждый день.", "result": "Быстрая обратная связь.", "icon": "heroicons:bolt", "color": "var(--color-warning)", "start_time": 1800}
        ],
        "color_scheme": "cool"
    },
    "OrganicGrid": {
        "variant": "tech",
        "title": "Компетенции",
        "subtitle": "Что умеем",
        "items": [
            {"id": "og1", "title": "AI & ML", "desc": "Модели, RAG, агенты.", "icon": "heroicons:cpu-chip", "color": "var(--color-secondary)", "size": "2x2", "start_time": 0},
            {"id": "og2", "title": "Data", "desc": "ETL и хранилища.", "icon": "heroicons:circle-stack", "color": "var(--color-success)", "size": "2x1", "start_time": 900},
            {"id": "og3", "title": "Cloud", "desc": "Масштаб и отказоустойчивость.", "icon": "heroicons:cloud", "color": "var(--color-warning)", "size": "2x1", "start_time": 1800},
            {"id": "og4", "title": "Security", "desc": "Безопасность и аудит.", "icon": "heroicons:lock-closed", "color": "var(--color-accent)", "size": "4x2", "start_time": 2700}
        ]
    },
    "ProgressScalesSlide": {
        "variant": "tech",
        "scales": [
            {"label": "Готовность данных", "value": 82, "max": 100, "color": "var(--color-secondary)", "icon": "lucide:database", "start_time": 0},
            {"label": "Автоматизация поддержки", "value": 67, "max": 100, "color": "var(--color-success)", "icon": "lucide:bot", "start_time": 900},
            {"label": "Доля ИИ-ответов", "value": 54, "max": 100, "color": "var(--color-warning)", "icon": "lucide:message-square", "start_time": 1800},
            {"label": "Удовлетворённость клиентов", "value": 91, "max": 100, "color": "var(--color-accent)", "icon": "lucide:smile", "start_time": 2700}
        ]
    },
    "BeforeAfterSlide": {
        "variant": "tech",
        "windows": [
            {"title": "До: хаос", "image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1200&auto=format&fit=crop", "start_time": 1000},
            {"title": "После: порядок", "image": "https://images.unsplash.com/photo-1483058712412-4245e9b90334?q=80&w=1200&auto=format&fit=crop", "start_time": 3500}
        ]
    },
    "ProductCard": {
        "variant": "tech",
        "items": [
            {"id": "pc1", "variant": "pricing", "title": "Starter AI", "price": "49 €", "period": "/мес", "features": ["1 Агент", "Базовые API", "Поддержка email"], "btn_text": "Начать", "start_time": 0},
            {"id": "pc2", "variant": "pricing", "badge": "Популярно", "title": "Pro Team", "price": "199 €", "period": "/мес", "features": ["10 Агентов", "Доступ к GPT-5", "Выделенный сервер"], "btn_text": "Купить", "btn_icon": "heroicons:rocket-launch", "accent_color": "var(--color-secondary)", "border_color": "rgb(var(--color-secondary-rgb) / 0.3)", "highlight": True, "start_time": 900},
            {"id": "pc3", "variant": "photo", "image": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=800", "badge": "UI/UX", "title": "Умный Дашборд", "desc": "Следите за всеми агентами в реальном времени", "btn_text": "Смотреть демо", "btn_icon": "heroicons:play", "accent_color": "var(--color-primary)", "start_time": 1800},
            {"id": "pc4", "variant": "photo", "image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&q=80&w=800", "title": "API Доступ", "desc": "Интегрируйте нейросети в любой продукт за 5 минут", "btn_text": "Документация", "btn_icon": "heroicons:document-text", "accent_color": "var(--color-success)", "start_time": 2700}
        ]
    },
    "BrowserMockup": {
        "variant": "tech",
        "items": [
            {
                "id": "b1",
                "url": "https://it2b.cloud/overview",
                "type": "html",
                "content": _BROWSER_DASHBOARD_HTML,
                "scroll": False,
                "start_time": 0
            },
            {
                "id": "b2",
                "url": "https://it2b.cloud/deals",
                "type": "html",
                "content": _BROWSER_DEALS_HTML,
                "scroll": False,
                "start_time": 7000
            },
            {
                "id": "b3",
                "url": "https://it2b.cloud/analytics",
                "type": "image",
                "content": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1200",
                "scroll": False,
                "start_time": 13000
            }
        ]
    },
    "InfographicCards": {
        "variant": "tech",
        "items": [
            {"id": 1, "value": "42%", "label": "Автоматизация", "trend": "+24%", "color": "var(--color-secondary)", "icon": "lucide:cpu", "start_time": 0},
            {"id": 2, "value": "1.2K", "label": "Заявок в день", "trend": "+18%", "color": "var(--color-success)", "icon": "lucide:inbox", "start_time": 900},
            {"id": 3, "value": "24мс", "label": "Отклик системы", "trend": "-31%", "color": "var(--color-warning)", "icon": "lucide:zap", "start_time": 1800},
            {"id": 4, "value": "3.9", "label": "Оценка клиента", "trend": "+0.6", "color": "var(--color-accent)", "icon": "lucide:star", "start_time": 2700}
        ]
    },
    "ProcessFunnel": {
        "variant": "tech",
        "layout": "horizontal",
        "steps": [
            {"label": "Посетители", "count": 10000, "icon": "heroicons:users", "color": "var(--color-secondary)", "start_time": 0},
            {"label": "Лиды", "count": 3500, "icon": "heroicons:envelope", "color": "var(--color-warning)", "start_time": 900},
            {"label": "Сделки", "count": 820, "icon": "heroicons:hand-raised", "color": "var(--color-accent)", "start_time": 1800},
            {"label": "Клиенты", "count": 420, "icon": "heroicons:check-circle", "color": "var(--color-success)", "start_time": 2700}
        ]
    },
    "RoiCalculatorSlide": {
        "variant": "tech",
        "variables": [
            {"label": "Тикетов закрыто ИИ", "icon": "lucide:bot", "min": 0, "max": 10000, "target": 4500, "step": 100, "multiplier": 4, "suffix": "шт", "start_time": 0, "duration": 800},
            {"label": "Сэкономлено часов", "icon": "lucide:clock", "min": 0, "max": 500, "target": 120, "step": 10, "multiplier": 25, "suffix": "ч", "start_time": 900, "duration": 800},
            {"label": "Рост удержания", "icon": "lucide:heart-handshake", "min": 0, "max": 15, "target": 5.5, "step": 0.5, "multiplier": 1200, "suffix": "%", "start_time": 1800, "duration": 800},
            {"label": "Рост upsell", "icon": "lucide:trending-up", "min": 0, "max": 30, "target": 12, "step": 1, "multiplier": 450, "suffix": "%", "start_time": 2700, "duration": 800},
            {"label": "Амортизация внедрения", "icon": "lucide:wrench", "min": 0, "max": 20000, "target": 5000, "step": 500, "multiplier": -0.2, "suffix": "€", "start_time": 3600, "duration": 800}
        ],
        "result_base": 0,
        "result_label": "Экономия в месяц",
        "result_suffix": "€",
        "result_description": "Расчёт по вашим объёмам"
    },
    "OutroSlide": {
        # Без захардкоженного CTA: headline пустой по умолчанию (заполняется осознанно
        # под конкретный ролик/бренд). QR/лого/контакт приходят из brand-kit проекта.
        "variant": "tech",
        "logo": "",
        "qr_code": "/generated/qr.svg",
        "handle": "@it00101",
        "headline": ""
    },
}


def clean(obj):
    """Чистит пример: убирает пустые sfx и пустые значения ('' / [] / {} / None).

    Пустые значения не являются «здоровым заполнением» — структуру полей
    ИИ берёт из payload_schema, а example должен показывать только заполненные.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ("sfx", "item_sfx") and isinstance(v, dict) and not v.get("src"):
                continue
            v2 = clean(v)
            if v2 in ("", [], {}, None):
                continue
            out[k] = v2
        return out
    if isinstance(obj, list):
        out = []
        for x in obj:
            x2 = clean(x)
            if x2 in ("", {}, None):
                continue
            out.append(x2)
        return out
    return obj


# Hex палитры → токен темы. Бренд-hex (Vue/Postgres и др.) намеренно НЕ трогаем —
# они исключены в style_lint. Любой другой палитровый hex в примере = дефект:
# при смене темы (classic/industrial/derevnya/diademas) он не перекрашивается.
_HEX_TO_TOKEN = {
    "#38BDF8": "var(--color-secondary)", "#2563EB": "var(--color-primary)",
    "#10B981": "var(--color-success)", "#34D399": "var(--color-success)",
    "#F59E0B": "var(--color-warning)", "#FB923C": "var(--color-accent)",
    "#EA580C": "var(--color-accent)", "#F97316": "var(--color-accent)",
    "#EC4899": "var(--item-accent-3)", "#2DD4BF": "var(--color-accent)",
    "#60A5FA": "var(--color-secondary)",
}
# Зарезервированные бренд-цвета (совпадают с whitelist backend/style_lint.py).
_HEX_KEEP = {"#42B883", "#009688", "#336791"}


def _norm_hex(v):
    if not isinstance(v, str):
        return v
    up = v.upper()
    if up in _HEX_KEEP:
        return v
    return _HEX_TO_TOKEN.get(up, v)


MIN_GAP_MS = 800  # §8.3: шаг reveal айтемов в теле слайда


def _norm_start_times(items):
    """Пересобирает монотонный start_time с шагом ≥ MIN_GAP_MS, сохраняя порядок.
    Трогает только массивы, где реально есть ≥2 различных start_time (не синхронные).
    Не добавляет start_time там, где его не было (InteractiveArchitecture и т.п.)."""
    if not isinstance(items, list):
        return items
    idx = [i for i, x in enumerate(items) if isinstance(x, dict) and "start_time" in x]
    vals = sorted({float(items[i]["start_time"] or 0) for i in idx})
    if len(vals) < 2:
        return items
    order = sorted(idx, key=lambda i: float(items[i]["start_time"] or 0))
    for rank, i in enumerate(order):
        items[i]["start_time"] = rank * MIN_GAP_MS
    return items


def normalize(obj, _key=None):
    """Приводит example к правилам: hex → токены палитры, reveal ≥800мс.
    Ключи color/from/to/fill/stroke/bg_color/accent_color — зона цвета (hex→токен);
    массивы с start_time — зона таймингов. Код/HTML (code/content) не трогаем."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nv = _norm_hex(v) if k in ("color", "from", "to", "fill", "stroke",
                                       "bg_color", "accent_color") else v
            out[k] = normalize(nv, k)
        return out
    if isinstance(obj, list):
        out = [normalize(x) for x in obj]
        if out and all(isinstance(x, dict) for x in out) and any("start_time" in x for x in out):
            _norm_start_times(out)
        return out
    return obj


def run():
    ensure_columns()

    db = SessionLocal()
    try:
        slides = db.query(models.Slide).filter(
            models.Slide.presentation_id == REFERENCE_PRESENTATION_ID
        ).all()

        payload_by_component = {}
        for s in slides:
            if s.component and s.data and s.data.payload:
                payload_by_component.setdefault(s.component, s.data.payload)

        comps = db.query(models.Component).order_by(models.Component.slug).all()
        from_curated = 0
        from_ref = 0
        from_fallback = 0
        for c in comps:
            if c.slug in CURATED_EXAMPLES:
                # Курированный пример имеет приоритет (Roadmap P1–P4).
                c.example = clean(CURATED_EXAMPLES[c.slug])
                from_curated += 1
                continue
            if c.slug == "InteractiveArchitecture":
                # Спец-правило §4.4: start_time только у ОДНОЙ ноды (фокус камеры).
                # /p/4 содержит start_time у всех нод → берём корректный default_payload.
                c.example = normalize(clean(c.default_payload or {}))
                from_curated += 1
                continue
            payload = payload_by_component.get(c.slug)
            if payload is not None:
                c.example = normalize(clean(payload))
                from_ref += 1
            else:
                c.example = normalize(clean(c.default_payload or {}))
                from_fallback += 1
        db.commit()
        print(
            f"example заполнен: {from_curated} curated, {from_ref} из /p/4, "
            f"{from_fallback} из default_payload (всего {len(comps)})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
