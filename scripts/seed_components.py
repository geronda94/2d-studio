import os
import sys

# Ensure backend module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from backend.models import Base, ComponentType, Category, Component
from backend.database import SQLALCHEMY_DATABASE_URL
from scripts import _domain_v2
from scripts import _orthodox_seed

engine = create_engine(SQLALCHEMY_DATABASE_URL)

def seed_db(force=False):
    """P0-конвенция: DROP таблиц УДАЛЁН — сид делает upsert по slug.
    Кастомы (is_custom, созданные через API) не трогаем никогда.
    Существующие managed-компоненты обновляем из файла (title/type/payload/categories);
    description/schema/example/manifest принадлежат генераторам (generate_*.py / seed_manifests.py).
    Плотность start_time нормализуется под AGENTS.md §8.3 (шаг ≥ 800мс, InteractiveArchitecture — skip).
    """
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Миграция без alembic: колонка is_custom для существующих БД
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE components ADD COLUMN IF NOT EXISTS is_custom BOOLEAN DEFAULT FALSE"))
        conn.commit()

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    def get_or_create(model, slug, name):
        obj = session.query(model).filter(model.slug == slug).first()
        if not obj:
            obj = model(slug=slug, name=name)
            session.add(obj)
            session.commit()
            print(f"Создан {model.__tablename__} «{slug}»")
        return obj

    print("Seeding types...")
    type_interactive = get_or_create(ComponentType, "interactive", "Интерактивный компонент")
    type_slide = get_or_create(ComponentType, "slide", "Полноэкранный компонент")
    type_ui = get_or_create(ComponentType, "ui", "UI Элемент")

    print("Seeding categories...")
    cat_backend = get_or_create(Category, "backend", "Бэкенд & Архитектура")
    cat_sales = get_or_create(Category, "sales", "Продажи & Воронки")
    cat_ui = get_or_create(Category, "ui", "Интерфейсы")
    cat_stats = get_or_create(Category, "stats", "Статистика & Графики")

    print("Seeding components...")
    
    components_data = [
        # ─── INTERACTIVE ───
        {
            "slug": "ArchitectureDiagram",
            "title": "Диаграмма архитектуры",
            "type": type_ui,
            "cat": cat_backend,
            "payload": {
                "nodes": [
                    {
                        "id": "in1",
                        "title": "Telegram Bot",
                        "subtitle": "Frontend",
                        "icon": "telegram",
                        "color": "chart-2",
                        "start_time": 500,
                        "is_main": False,
                        "to": ["core1"]
                    },
                    {
                        "id": "core1",
                        "title": "ИИ Драйвер",
                        "subtitle": "Agent Router",
                        "icon": "cpu",
                        "color": "color-primary",
                        "start_time": 1166,
                        "is_main": True,
                        "to": ["out1", "out2"]
                    },
                    {
                        "id": "out1",
                        "title": "База данных",
                        "subtitle": "PostgreSQL",
                        "icon": "db",
                        "color": "chart-3",
                        "start_time": 1832,
                        "is_main": False
                    },
                    {
                        "id": "out2",
                        "title": "Make.com",
                        "subtitle": "Webhooks",
                        "icon": "api",
                        "color": "chart-4",
                        "start_time": 2498,
                        "is_main": False
                    }
                ],
                "show_data_flow": True,
                "variant": "tech"
            }
        },
        {
            "slug": "InteractiveArchitecture",
            "title": "Интерактивная архитектура",
            "type": type_interactive,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "nodes": [
                    {
                        "id": "lb",
                        "label": "Load Balancer",
                        "desc": "Cloudflare",
                        "color": "chart-1",
                        "icon": "heroicons:server",
                        "details": "Балансировщик нагрузки (CDN). Фильтрует DDoS атаки.",
                        "to": [
                            "web1",
                            "web2"
                        ],
                        "start_time": 0
                    },
                    {
                        "id": "web1",
                        "label": "Web Server 1",
                        "desc": "Node.js / Vue",
                        "color": "chart-2",
                        "icon": "heroicons:computer-desktop",
                        "details": "Первичный фронтенд-сервер.",
                        "to": [
                            "api"
                        ],
                        "start_time": 0
                    },
                    {
                        "id": "web2",
                        "label": "Web Server 2",
                        "desc": "Node.js / Vue",
                        "color": "chart-2",
                        "icon": "heroicons:computer-desktop",
                        "details": "Резервный фронтенд-сервер.",
                        "to": [
                            "api"
                        ],
                        "start_time": 0
                    },
                    {
                        "id": "api",
                        "label": "API Gateway",
                        "desc": "Kong",
                        "color": "chart-1",
                        "icon": "heroicons:arrows-right-left",
                        "details": "Единая точка входа для всех запросов.",
                        "to": [
                            "auth",
                            "db",
                            "cache",
                            "queue"
                        ],
                        "start_time": -800
                    },
                    {
                        "id": "auth",
                        "label": "Auth Service",
                        "desc": "Keycloak",
                        "color": "chart-3",
                        "icon": "heroicons:key",
                        "details": "Сервис аутентификации.",
                        "to": [],
                        "start_time": 700
                    },
                    {
                        "id": "cache",
                        "label": "Redis Cache",
                        "desc": "In-Memory",
                        "color": "chart-4",
                        "icon": "heroicons:circle-stack",
                        "details": "Сверхбыстрое in-memory хранилище.",
                        "to": [],
                        "start_time": 4200
                    },
                    {
                        "id": "queue",
                        "label": "Message Queue",
                        "desc": "RabbitMQ",
                        "color": "chart-3",
                        "icon": "heroicons:queue-list",
                        "details": "Брокер сообщений.",
                        "to": [
                            "worker"
                        ],
                        "start_time": 5200
                    },
                    {
                        "id": "worker",
                        "label": "Async Worker",
                        "desc": "Celery",
                        "color": "chart-1",
                        "icon": "heroicons:cpu-chip",
                        "details": "Фоновый воркер.",
                        "to": [
                            "db"
                        ],
                        "start_time": 2200
                    },
                    {
                        "id": "db",
                        "label": "Primary DB",
                        "desc": "PostgreSQL",
                        "color": "chart-4",
                        "icon": "heroicons:circle-stack",
                        "details": "Основная база данных.",
                        "to": [],
                        "start_time": 7200
                    }
                ]
            }
        },

        # ─── FULL-SLIDE ───
        {
            "slug": "OutroSlide",
            "title": "Завершающая заставка",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "logo": "",
                "qr_code": "/generated/qr.svg",
                "handle": "@it00101",
                "headline": ""
            }
        },
        {
            "slug": "ChatMockupSlide",
            "title": "Чат (на весь экран)",
            "type": type_slide,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "bot_name": "Telegram Bot",
                "bot_subtitle": "bot",
                "bot_avatar": "T",
                "messages": [
                    {
                        "role": "user",
                        "text": "Привет!",
                        "image": "",
                        "start_time": 0
                    },
                    {
                        "role": "assistant",
                        "text": "Здравствуйте! Чем могу помочь?",
                        "image": "",
                        "start_time": 1500
                    }
                ]
            }
        },
        {
            "slug": "CodeComparisonSlide",
            "title": "Сравнение кода",
            "type": type_slide,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "windows": [
                    {
                        "title": "n8n (Code Node)",
                        "color": "var(--color-accent)",
                        "file": "FindNewEmails.js",
                        "code": "// Поиск уникальных email-ов\nlet new_emails = [];\nfor (let i = 0; i < api_emails.length; i++) {\n  let found = False;\n  for (let j = 0; j < db_emails.length; j++) {\n    if (api_emails[i] === db_emails[j]) {\n      found = True;\n      break;\n    }\n  }\n  if (!found) {\n    new_emails.push(api_emails[i]);\n  }\n}\nreturn new_emails;",
                        "typing": True,
                        "start_time": 554
                    },
                    {
                        "title": "Python",
                        "color": "var(--item-accent-1)",
                        "file": "find_emails.py",
                        "code": "# Поиск уникальных email-ов\n\napi_set = set(api_emails)\ndb_set = set(db_emails)\n\nnew_emails = list(api_set - db_set)",
                        "typing": True,
                        "start_time": 2054
                    }
                ]
            }
        },
        {
            "slug": "ProgressScalesSlide",
            "title": "Шкалы прогресса",
            "type": type_slide,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "scales": [
                    {"label": "Готовность данных", "value": 82, "max": 100, "color": "var(--color-secondary)", "icon": "lucide:database", "start_time": 0},
                    {"label": "Автоматизация поддержки", "value": 67, "max": 100, "color": "var(--color-success)", "icon": "lucide:bot", "start_time": 900},
                    {"label": "Доля ИИ-ответов", "value": 54, "max": 100, "color": "var(--color-warning)", "icon": "lucide:message-square", "start_time": 1800},
                    {"label": "Удовлетворённость клиентов", "value": 91, "max": 100, "color": "var(--color-accent)", "icon": "lucide:smile", "start_time": 2700}
                ]
            }
        },
        {
            "slug": "BeforeAfterSlide",
            "title": "До / После",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "windows": [
                    {
                        "title": "До: хаос",
                        "image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1200&auto=format&fit=crop",
                        "start_time": 1000
                    },
                    {
                        "title": "После: порядок",
                        "image": "https://images.unsplash.com/photo-1483058712412-4245e9b90334?q=80&w=1200&auto=format&fit=crop",
                        "start_time": 3500
                    }
                ]
            }
        },
        {
            "slug": "AnimatedStatsSlide",
            "title": "Анимированная статистика",
            "type": type_slide,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "stats": [
                    {
                        "label": "Конверсия",
                        "value": 42,
                        "suffix": "%",
                        "color": "var(--color-success)",
                        "icon": "lucide:trending-up",
                        "start_time": 0
                    },
                    {
                        "label": "Отказы",
                        "value": -15,
                        "suffix": "%",
                        "color": "var(--color-danger)",
                        "icon": "lucide:trending-down",
                        "start_time": 300
                    },
                    {
                        "label": "Доход",
                        "value": 5,
                        "suffix": "M €",
                        "color": "var(--color-warning)",
                        "icon": "lucide:euro",
                        "start_time": 600
                    }
                ]
            }
        },
        {
            "slug": "TechStackSlide",
            "title": "Технологический стек",
            "type": type_slide,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "technologies": [
                    {
                        "name": "Vue.js",
                        "icon": "logos:vue",
                        "desc": "Фронтенд фреймворк",
                        "color": "#42b883",
                        "start_time": 0
                    },
                    {
                        "name": "FastAPI",
                        "icon": "logos:fastapi",
                        "desc": "REST API бэкенд",
                        "color": "#009688",
                        "start_time": 150
                    },
                    {
                        "name": "PostgreSQL",
                        "icon": "logos:postgresql",
                        "desc": "Реляционная БД",
                        "color": "#336791",
                        "start_time": 300
                    }
                ]
            }
        },

        {
            "slug": "MediaSlide",
            "title": "Медиа-контент",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "media_url": "/uploads/a23bdaf300aa43dcac4db2099d0b7a36.jpg",
                "caption": "Подпись к изображению",
                "start_time": 200,
                "target_scale": 1.1,
                "zoom_duration": 600,
                "target_position": "50% 50%",
                "object_position": "50% 62.5%",
                "initial_scale": 1.45
            }
        },

        {
            "slug": "CrmCardSlide",
            "title": "CRM Карточка",
            "type": type_slide,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "customer": {
                    "name": "Иван Иванов",
                    "avatar_text": "И",
                    "id_text": "ID: #49281",
                    "status": "горячий"
                },
                "fields": [
                    {
                        "label": "КОМПАНИЯ",
                        "value": "ООО Компания",
                        "field_icon": "",
                        "field_color": "",
                        "start_time": 500
                    },
                    {
                        "label": "ТЕЛЕФОН",
                        "value": "+7 999 000-00-00",
                        "field_icon": "",
                        "field_color": "",
                        "start_time": 1000
                    },
                    {
                        "label": "EMAIL",
                        "value": "ivan@example.com",
                        "field_icon": "",
                        "field_color": "",
                        "start_time": 1500
                    },
                    {
                        "label": "СУММА СДЕЛКИ",
                        "value": "150 000 €",
                        "field_icon": "",
                        "field_color": "",
                        "start_time": 2000
                    }
                ],
                "buttons": [
                    {
                        "text": "Взять в работу",
                        "btn_color": "",
                        "btn_text_color": "",
                        "start_time": 2500
                    },
                    {
                        "text": "Отклонить",
                        "btn_color": "",
                        "btn_text_color": "",
                        "start_time": 2700
                    }
                ]
            }
        },

        # ─── UI ELEMENTS ───
        {
            "slug": "ReceiptCard",
            "title": "Карточка чека",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "CORPORATE CARD",
                "subtitle": "August 2026",
                "currency": "€",
                "total_text": "TOTAL DUE",
                "footer_text": "THANK YOU FOR YOUR MONEY",
                "total_start_time": 2000,
                "items": [
                    {
                        "name": "AmoCRM Subscription",
                        "price": 89,
                        "start_time": 500
                    },
                    {
                        "name": "Make.com Automation",
                        "price": 49,
                        "start_time": 1000
                    },
                    {
                        "name": "ChatBot SaaS",
                        "price": 150,
                        "start_time": 1500
                    }
                ]
            }
        },
        {
            "slug": "ModernTable",
            "title": "Современная таблица",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "columns": [
                    {
                        "key": "col1_icon",
                        "label": "Иконка",
                        "type": "icon",
                        "align": "center",
                        "start_time": 1000
                    },
                    {
                        "key": "col2_text",
                        "label": "Название",
                        "type": "text",
                        "align": "left",
                        "start_time": 2000
                    },
                    {
                        "key": "col3_trend",
                        "label": "Прогресс",
                        "type": "trend",
                        "align": "center",
                        "start_time": 3000
                    },
                    {
                        "key": "col4_text",
                        "label": "Доход",
                        "type": "text",
                        "align": "right",
                        "start_time": 4000
                    },
                    {
                        "key": "col5_status",
                        "label": "Активен",
                        "type": "boolean",
                        "align": "center",
                        "start_time": 5000
                    }
                ],
                "rows": [
                    {
                        "start_time": 0,
                        "col1_icon": "lucide:rocket",
                        "col2_text": "Проект Alpha",
                        "col3_trend": 15,
                        "col4_text": "120K €",
                        "col5_status": True
                    },
                    {
                        "start_time": 300,
                        "col1_icon": "lucide:briefcase",
                        "col2_text": "Проект Beta",
                        "col3_trend": -5,
                        "col4_text": "85K €",
                        "col5_status": False,
                        "is_focused": True
                    },
                    {
                        "start_time": 600,
                        "col1_icon": "lucide:star",
                        "col2_text": "Проект Gamma",
                        "col3_trend": 25,
                        "col4_text": "200K €",
                        "col5_status": True
                    }
                ],
                "focus": {
                    "start_time": 1500
                }
            }
        },
        {
            "slug": "TerminalMockup",
            "title": "Терминал",
            "type": type_ui,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "commands": [
                    {
                        "cmd": "git pull origin main",
                        "output": "From https://github.com/user/youtube-channel\n * branch            main       -> FETCH_HEAD\nUpdating 3a4b5c6..7d8e9f0\nFast-forward\n backend/main.py       | 12 +++++++-----\n core/package.json     |  2 +-\n docker-compose.yml    |  1 +\n 3 files changed, 9 insertions(+), 6 deletions(-)",
                        "start_time": 500
                    },
                    {
                        "cmd": "docker compose build",
                        "output": "[+] Building 15.2s (24/24) FINISHED\n => [backend internal] load build definition from Dockerfile\n => [frontend internal] load build definition from Dockerfile\n => [backend 1/6] FROM docker.io/library/python:3.12-slim\n => [frontend 1/4] FROM docker.io/library/node:20-alpine\n => [backend 5/6] RUN pip install --no-cache-dir -r requirements.txt\n => [frontend 3/4] RUN npm install\n => [backend] exporting to image\n => [frontend] exporting to image\n => => naming to docker.io/library/youtubechannel-frontend:latest",
                        "start_time": 3000
                    },
                    {
                        "cmd": "docker compose up -d",
                        "output": "[+] Running 4/4\n ✔ Container youtubechannel-db-1        Started\n ✔ Container youtubechannel-redis-1      Started\n ✔ Container youtubechannel-backend-1   Started\n ✔ Container youtubechannel-frontend-1  Started",
                        "start_time": 7000
                    },
                    {
                        "cmd": "docker compose logs -f --tail=10",
                        "output": "db-1        | PostgreSQL init process complete; ready for start up.\ndb-1        | database system is ready to accept connections\nredis-1     | Ready to accept connections tcp\nbackend-1   | INFO:     Running on http://0.0.0.0:8000 (Press CTRL+C to quit)\nbackend-1   | INFO:     Application startup complete.\nfrontend-1  | \nfrontend-1  |   VITE v5.0.0  ready in 245 ms\nfrontend-1  | \nfrontend-1  |   ➜  Local:   http://localhost:5173/\nfrontend-1  |   ➜  Network: use --host to expose",
                        "start_time": 10000
                    }
                ]
            }
        },
        {
            "slug": "NetworkWaterfall",
            "title": "Сетевой водопад",
            "type": type_ui,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "total_ms": 2000,
                "requests": [
                    {
                        "name": "CI Сборка",
                        "method": "BUILD",
                        "type": "api",
                        "start_ms": 0,
                        "duration_ms": 500,
                        "start_time": 0,
                        "color": "var(--item-accent-1)",
                        "icon": "heroicons:cog-8-tooth"
                    },
                    {
                        "name": "Unit Тесты",
                        "method": "TEST",
                        "type": "js",
                        "start_ms": 500,
                        "duration_ms": 400,
                        "start_time": 600,
                        "color": "var(--item-accent-3)",
                        "icon": "heroicons:beaker"
                    },
                    {
                        "name": "E2E Тесты",
                        "method": "CYPRESS",
                        "type": "html",
                        "start_ms": 900,
                        "duration_ms": 700,
                        "start_time": 1100,
                        "color": "var(--item-accent-4)",
                        "icon": "heroicons:shield-check"
                    },
                    {
                        "name": "Деплой Production",
                        "method": "DEPLOY",
                        "type": "api",
                        "start_ms": 1600,
                        "duration_ms": 300,
                        "start_time": 1900,
                        "color": "var(--item-accent-2)",
                        "icon": "heroicons:rocket-launch"
                    }
                ],
                "legend": [
                    {
                        "label": "Сборка (API)",
                        "color": "var(--item-accent-1)",
                        "start_time": 1000
                    },
                    {
                        "label": "Логика (JS)",
                        "color": "var(--item-accent-3)",
                        "start_time": 2000
                    },
                    {
                        "label": "Интерфейс (HTML)",
                        "color": "var(--item-accent-4)",
                        "start_time": 3000
                    },
                    {
                        "label": "Деплой",
                        "color": "var(--item-accent-2)",
                        "start_time": 4000
                    }
                ]
            }
        },
        {
            "slug": "CodeExplain",
            "title": "Объяснение кода",
            "type": type_ui,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "language": "python",
                "blocks": [
                    {
                        "code": "from fastapi import FastAPI\nfrom pydantic import BaseModel\nimport httpx\n\n",
                        "start_time": 0
                    },
                    {
                        "code": "app = FastAPI()\n\nclass User(BaseModel):\n    name: str\n    email: str\n\n",
                        "start_time": 1500
                    },
                    {
                        "code": "@app.post(\"/users\")\nasync def create_user(user: User):\n    async with httpx.AsyncClient() as client:\n        await client.post(\"https://crm.api/add\", json=user.dict())\n    return {\"status\": \"success\", \"user\": user.name}\n",
                        "start_time": 3500
                    }
                ]
            }
        },
        {
            "slug": "ProcessFunnel",
            "title": "Воронка процессов",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "layout": "horizontal",
                "steps": [
                    {
                        "label": "Посетители",
                        "count": 10000,
                        "icon": "heroicons:users",
                        "start_time": 0,
                        "color": "var(--item-accent-1)"
                    },
                    {
                        "label": "Лиды",
                        "count": 3500,
                        "icon": "heroicons:envelope",
                        "start_time": 1000,
                        "color": "var(--item-accent-3)"
                    },
                    {
                        "label": "Клиенты",
                        "count": 420,
                        "icon": "heroicons:check-circle",
                        "start_time": 2000,
                        "color": "var(--item-accent-2)"
                    }
                ]
            }
        },
        {
            "slug": "Roadmap",
            "title": "Дорожная карта",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "label": "Запуск MVP",
                        "desc": "Q1 2025",
                        "icon": "heroicons:rocket-launch",
                        "color": "chart-1",
                        "start_time": 0
                    },
                    {
                        "label": "Первые 100 клиентов",
                        "desc": "Q2 2025",
                        "icon": "heroicons:users",
                        "color": "chart-3",
                        "start_time": 1000
                    },
                    {
                        "label": "Выход на рынок",
                        "desc": "Q4 2025",
                        "icon": "heroicons:globe-alt",
                        "color": "chart-4",
                        "start_time": 2000
                    },
                    {
                        "label": "Масштабирование",
                        "desc": "2026",
                        "icon": "heroicons:arrow-trending-up",
                        "color": "chart-1",
                        "start_time": 3000
                    }
                ]
            }
        },
        {
            "slug": "PremiumChecklist",
            "title": "Премиум чеклист",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "label": "Анализ ЦА",
                        "desc": "Глубинные интервью и сегментация аудитории",
                        "icon": "heroicons:users",
                        "color": "chart-1",
                        "start_time": 0
                    },
                    {
                        "label": "MVP разработка",
                        "desc": "Реализация базового функционала и архитектуры",
                        "icon": "heroicons:code-bracket",
                        "color": "chart-3",
                        "start_time": 1200
                    },
                    {
                        "label": "Бета-тестирование",
                        "desc": "Запуск в закрытой группе, сбор первых метрик",
                        "icon": "heroicons:bug-ant",
                        "color": "chart-5",
                        "start_time": 2400
                    },
                    {
                        "label": "Маркетинг план",
                        "desc": "Подготовка креативов и рекламных кампаний",
                        "icon": "heroicons:megaphone",
                        "color": "chart-1",
                        "start_time": 3600
                    },
                    {
                        "label": "Официальный релиз",
                        "desc": "Открытие доступа для всех пользователей",
                        "icon": "heroicons:rocket-launch",
                        "color": "chart-4",
                        "start_time": 4800
                    },
                    {
                        "label": "Сбор фидбека",
                        "desc": "Анализ отзывов и формирование нового бэклога",
                        "icon": "heroicons:chat-bubble-bottom-center-text",
                        "color": "chart-3",
                        "start_time": 6000
                    }
                ]
            }
        },
        {
            "slug": "ComparisonTable",
            "title": "Таблица сравнения",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "headers": [
                    "Мой подход (Vue)",
                    "Tilda",
                    "WordPress"
                ],
                "items": [
                    {
                        "id": "r1",
                        "label": "Полная кастомизация",
                        "values": [
                            True,
                            False,
                            True
                        ],
                        "start_time": 0
                    },
                    {
                        "id": "r2",
                        "label": "Скорость загрузки (LCP)",
                        "values": [
                            "< 1 сек",
                            "~3 сек",
                            "> 2 сек"
                        ],
                        "start_time": 700
                    },
                    {
                        "id": "r3",
                        "label": "Отсутствие абон. платы",
                        "values": [
                            True,
                            False,
                            False
                        ],
                        "start_time": 1400
                    },
                    {
                        "id": "r4",
                        "label": "Безопасность",
                        "values": [
                            "Высокая",
                            "Средняя",
                            "Уязвима"
                        ],
                        "start_time": 2100
                    }
                ]
            }
        },
        {
            "slug": "BrowserMockup",
            "title": "Браузер",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "id": "b1",
                        "url": "https://antigravity.dev/landing",
                        "type": "image",
                        "content": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000&h=3000",
                        "scroll": True,
                        "scroll_duration": 6,
                        "scroll_amount": 100,
                        "image_position": "top",
                        "start_time": 0
                    },
                    {
                        "id": "b2",
                        "url": "https://antigravity.dev/dashboard",
                        "type": "html",
                        "content": "<div style='display:flex;min-height:100%;width:100%;color:var(--text-primary)'><aside class='hidden md:flex' style='flex-direction:column;gap:4px;width:180px;flex-shrink:0;padding:16px 12px;border-right:1px solid var(--item-border)'><div style='display:flex;align-items:center;gap:8px;margin-bottom:14px'><span style='width:24px;height:24px;border-radius:8px;background:var(--color-secondary)'></span><b style='font-size:13px'>IT2B Cloud</b></div><div style='padding:8px 10px;border-radius:10px;font-size:12px;background:color-mix(in srgb,var(--color-secondary) 16%,transparent)'>Обзор</div><div style='padding:8px 10px;font-size:12px;color:var(--text-muted)'>Сделки</div><div style='padding:8px 10px;font-size:12px;color:var(--text-muted)'>Аналитика</div></aside><div style='flex:1;min-width:0;display:flex;flex-direction:column'><div style='display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid var(--item-border)'><b style='font-size:16px'>Обзор продаж</b><span style='margin-left:auto;font-size:11px;color:var(--text-muted)'>Обновлено 5 минут назад</span></div><div style='display:flex;flex-direction:column;gap:12px;padding:16px 18px;flex:1'><div style='display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px'><div style='border:1px solid var(--item-border);border-radius:10px;padding:10px'><div style='font-size:10px;color:var(--text-muted);text-transform:uppercase'>Выручка</div><div style='font-size:20px;font-weight:800;margin-top:3px'>284 500 €</div></div><div style='border:1px solid var(--item-border);border-radius:10px;padding:10px'><div style='font-size:10px;color:var(--text-muted);text-transform:uppercase'>Сделки</div><div style='font-size:20px;font-weight:800;margin-top:3px'>1 248</div></div><div style='border:1px solid var(--item-border);border-radius:10px;padding:10px'><div style='font-size:10px;color:var(--text-muted);text-transform:uppercase'>Конверсия</div><div style='font-size:20px;font-weight:800;margin-top:3px'>38%</div></div><div style='border:1px solid var(--item-border);border-radius:10px;padding:10px'><div style='font-size:10px;color:var(--text-muted);text-transform:uppercase'>Ответ ИИ</div><div style='font-size:20px;font-weight:800;margin-top:3px'>73%</div></div></div><div style='border:1px solid var(--item-border);border-radius:10px;padding:12px'><b style='font-size:12px'>Выручка по месяцам</b><div style='display:flex;align-items:flex-end;gap:8px;height:110px;margin-top:12px'><span style='flex:1;height:42%;border-radius:5px 5px 0 0;background:var(--color-secondary)'></span><span style='flex:1;height:58%;border-radius:5px 5px 0 0;background:var(--color-secondary)'></span><span style='flex:1;height:50%;border-radius:5px 5px 0 0;background:var(--color-secondary)'></span><span style='flex:1;height:74%;border-radius:5px 5px 0 0;background:var(--color-success)'></span><span style='flex:1;height:66%;border-radius:5px 5px 0 0;background:var(--color-secondary)'></span><span style='flex:1;height:88%;border-radius:5px 5px 0 0;background:var(--color-success)'></span><span style='flex:1;height:80%;border-radius:5px 5px 0 0;background:var(--color-secondary)'></span></div></div></div></div></div>",
                        "scroll": False,
                        "start_time": 8000
                    },
                    {
                        "id": "b3",
                        "url": "https://antigravity.dev/settings",
                        "type": "image",
                        "content": "https://images.unsplash.com/photo-1618477247222-acabb0f2af2a?auto=format&fit=crop&q=80&w=1000",
                        "scroll": False,
                        "scroll_duration": 6,
                        "scroll_amount": 100,
                        "image_position": "top",
                        "start_time": 14000
                    }
                ]
            }
        },
        {
            "slug": "BentoGridGallery",
            "title": "Bento Галерея",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "id": "g1",
                        "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&q=80&w=800",
                        "title": "Кибербезопасность",
                        "desc": "Надежная защита данных",
                        "size": "2x2",
                        "start_time": 0
                    },
                    {
                        "id": "g2",
                        "image": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=800",
                        "title": "Облака",
                        "desc": "Быстрый доступ 24/7",
                        "size": "1x2",
                        "start_time": 1000
                    },
                    {
                        "id": "g3",
                        "image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&q=80&w=800",
                        "title": "Алгоритмы",
                        "desc": "Нейросети",
                        "size": "1x1",
                        "start_time": 2000
                    },
                    {
                        "id": "g4",
                        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=800",
                        "title": "Оборудование",
                        "desc": "Серверы",
                        "size": "1x1",
                        "start_time": 3000
                    },
                    {
                        "id": "g5",
                        "image": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&q=80&w=800",
                        "title": "Технологии",
                        "desc": "Будущее",
                        "size": "2x1",
                        "start_time": 4000
                    },
                    {
                        "id": "g6",
                        "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=800",
                        "title": "Разработка",
                        "desc": "Код",
                        "size": "2x1",
                        "start_time": 5000
                    }
                ]
            }
        },
        {
            "slug": "ProductCard",
            "title": "Карточки",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "id": "pc1",
                        "variant": "pricing",
                        "title": "Starter AI",
                        "price": "49 €",
                        "period": "/мес",
                        "features": [
                            "1 Агент",
                            "Базовые API",
                            "Поддержка email"
                        ],
                        "btn_text": "Начать",
                        "start_time": 0
                    },
                    {
                        "id": "pc2",
                        "variant": "pricing",
                        "badge": "Популярно",
                        "title": "Pro Team",
                        "price": "199 €",
                        "period": "/мес",
                        "features": [
                            "10 Агентов",
                            "Доступ к GPT-5",
                            "Выделенный сервер"
                        ],
                        "btn_text": "Купить",
                        "btn_icon": "heroicons:rocket-launch",
                        "accent_color": "var(--item-accent-1)",
                        "border_color": "rgb(var(--item-accent-1-rgb) / 0.3)",
                        "highlight": True,
                        "start_time": 1000
                    },
                    {
                        "id": "pc3",
                        "variant": "photo",
                        "image": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=800",
                        "badge": "UI/UX",
                        "title": "Умный Дашборд",
                        "desc": "Следите за всеми агентами в реальном времени",
                        "btn_text": "Смотреть демо",
                        "btn_icon": "heroicons:play",
                        "accent_color": "var(--item-accent-4)",
                        "start_time": 2000
                    },
                    {
                        "id": "pc4",
                        "variant": "photo",
                        "image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&q=80&w=800",
                        "title": "API Доступ",
                        "desc": "Интегрируйте нейросети в любой продукт за 5 минут",
                        "btn_text": "Документация",
                        "btn_icon": "heroicons:document-text",
                        "accent_color": "var(--item-accent-2)",
                        "start_time": 3000
                    }
                ]
            }
        },
        {
            "slug": "InfographicCards",
            "title": "Инфографика",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "items": [
                    {
                        "id": 1,
                        "label": "Active Users",
                        "value": "14.2M",
                        "trend": "+24%",
                        "color": "var(--item-accent-1)",
                        "icon": "heroicons:users",
                        "start_time": 0
                    },
                    {
                        "id": 2,
                        "label": "Latency",
                        "value": "24ms",
                        "trend": "-12%",
                        "color": "var(--item-accent-2)",
                        "icon": "heroicons:server",
                        "start_time": 500
                    },
                    {
                        "id": 3,
                        "label": "Error Rate",
                        "value": "0.01%",
                        "trend": "-0.05%",
                        "color": "var(--item-accent-3)",
                        "icon": "",
                        "start_time": 1000
                    }
                ]
            }
        },
        {
            "slug": "StatsBarChart",
            "title": "Столбчатая диаграмма",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "base_color": "var(--chart-1)",
                "peak_color": "var(--color-accent)",
                "data": [
                    {
                        "label": "Янв",
                        "value": 65,
                        "start_time": 0
                    },
                    {
                        "label": "Фев",
                        "value": 82,
                        "start_time": 300
                    },
                    {
                        "label": "Мар",
                        "value": 91,
                        "highlight": True,
                        "start_time": 600
                    },
                    {
                        "label": "Апр",
                        "value": 78,
                        "start_time": 900
                    }
                ],
                "title": "Динамика продаж",
                "subtitle": "Последние 4 месяца"
            }
        },
        {
            "slug": "MetricScales",
            "title": "Метрики и шкалы",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "metrics": [
                    {
                        "id": 1,
                        "label": "Производительность",
                        "percentage": 87,
                        "color": "linear-gradient(to right, var(--color-secondary), var(--color-primary))",
                        "start_time": 0
                    },
                    {
                        "id": 2,
                        "label": "Качество кода",
                        "percentage": 92,
                        "color": "linear-gradient(to right, var(--color-success), var(--color-accent))",
                        "start_time": 800
                    },
                    {
                        "id": 3,
                        "label": "Покрытие тестами",
                        "percentage": 64,
                        "color": "linear-gradient(to right, var(--color-warning), var(--color-accent))",
                        "start_time": 1600
                    }
                ],
                "title": "Показатели",
                "subtitle": "Ключевые метрики"
            }
        },
        {
            "slug": "RoiCalculatorSlide",
            "title": "ROI Калькулятор",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "variables": [
                    {
                        "label": "Тикетов закрыто ИИ",
                        "icon": "lucide:bot",
                        "min": 0,
                        "max": 10000,
                        "target": 4500,
                        "step": 100,
                        "multiplier": 5,
                        "suffix": "шт",
                        "start_time": 0,
                        "duration": 600
                    },
                    {
                        "label": "Сэкономлено зарплат",
                        "icon": "lucide:users",
                        "min": 0,
                        "max": 50,
                        "target": 8,
                        "step": 1,
                        "multiplier": 3000,
                        "suffix": "чел",
                        "start_time": 300,
                        "duration": 600
                    },
                    {
                        "label": "Рост удержания (LTV)",
                        "icon": "lucide:heart-handshake",
                        "min": 0,
                        "max": 15,
                        "target": 5.5,
                        "step": 0.5,
                        "multiplier": 12000,
                        "suffix": "%",
                        "start_time": 600,
                        "duration": 600
                    },
                    {
                        "label": "Увеличение Upsell",
                        "icon": "lucide:badge-dollar-sign",
                        "min": 0,
                        "max": 30,
                        "target": 12,
                        "step": 1,
                        "multiplier": 4500,
                        "suffix": "%",
                        "start_time": 900,
                        "duration": 600
                    },
                    {
                        "label": "Снижение штрафов SLA",
                        "icon": "lucide:shield-check",
                        "min": 0,
                        "max": 200,
                        "target": 85,
                        "step": 5,
                        "multiplier": 100,
                        "suffix": "кейс",
                        "start_time": 1200,
                        "duration": 600
                    },
                    {
                        "label": "Оптимизация серверов",
                        "icon": "lucide:server",
                        "min": 0,
                        "max": 5000,
                        "target": 1200,
                        "step": 100,
                        "multiplier": 1,
                        "suffix": "$",
                        "start_time": 1500,
                        "duration": 600
                    },
                    {
                        "label": "Внедрение ИИ (аморт.)",
                        "icon": "lucide:wrench",
                        "min": 0,
                        "max": 20000,
                        "target": 5000,
                        "step": 500,
                        "multiplier": -0.2,
                        "suffix": "$",
                        "start_time": 1800,
                        "duration": 600
                    },
                    {
                        "label": "Лицензия Платформы",
                        "icon": "lucide:credit-card",
                        "min": 0,
                        "max": 10000,
                        "target": 2500,
                        "step": 100,
                        "multiplier": -1,
                        "suffix": "$",
                        "start_time": 2100,
                        "duration": 600
                    }
                ],
                "result_base": 0,
                "result_label": "Ежемесячный ROI",
                "result_suffix": "$",
                "result_description": "Экономия на рутинных операциях при тех же затратах на команду"
            }
        },
        {
            "slug": "AdvancedVideoSlide",
            "title": "Скринкаст",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "video_url": "/uploads/26c1802ed41647059d15b907a4600e30.mp4",
                "frame": "browser",
                "domain": "app.startup.io",
                "trim_start": 1,
                "trim_end": 15,
                "initial_scale": 1.2500000000000002,
                "target_scale": 1.2,
                "object_position": "100% 0%"
            }
        },
        {
            "slug": "EcosystemSlide",
            "title": "Экосистема",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "center": {
                    "label": "IT2B",
                    "logo": "it2b"
                },
                "nodes": [
                    {
                        "label": "Stripe",
                        "icon": "logos:stripe"
                    },
                    {
                        "label": "Salesforce",
                        "icon": "logos:salesforce"
                    },
                    {
                        "label": "HubSpot",
                        "icon": "logos:hubspot"
                    },
                    {
                        "label": "Telegram",
                        "icon": "logos:telegram"
                    },
                    {
                        "label": "Slack",
                        "icon": "logos:slack-icon"
                    }
                ]
            }
        },
        {
            "slug": "PortraitLampSlide",
            "title": "Портрет с лампадкой",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "image": "",
                "name": "Старец Гавриил",
                "caption": "Преподобный",
                "description": "Портрет в арочном окладе с подвесной лампадкой: образ и слово.",
                "lamp": True,
                "lamp_color": "color-primary",
                "flame_color": "color-warning"
            }
        },
        {
            "slug": "TimelineSlide",
            "title": "Линия времени",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "show_images": True,
                "events": [
                    {
                        "id": "e1",
                        "year": 1929,
                        "title": "Рождение и детство",
                        "description": "Родился в Тифлисе, рано потерял отца.",
                        "image": "",
                        "start_time": 0
                    },
                    {
                        "id": "e2",
                        "year": 1955,
                        "title": "Принятие монашества",
                        "description": "Пострижен в монахи с именем Гавриил.",
                        "image": "",
                        "start_time": 2000
                    },
                    {
                        "id": "e3",
                        "year": 1965,
                        "title": "Подвиг юродства",
                        "description": "Публичное обличение и гонения.",
                        "image": "",
                        "start_time": 4000
                    },
                    {
                        "id": "e4",
                        "year": 1971,
                        "title": "Служение в Самтавро",
                        "description": "Любовь, прозорливость и терпение болезней.",
                        "image": "",
                        "start_time": 6000
                    },
                    {
                        "id": "e5",
                        "year": 1995,
                        "title": "Преставление",
                        "description": "Похоронен по завещанию, место исцелений.",
                        "image": "",
                        "start_time": 8000
                    }
                ]
            }
        },
        # ─── ROADMAP V2 · TIER 0 — ОБЩИЕ ПРИМИТИВЫ ───
        {
            "slug": "ParetoChart",
            "title": "Диаграмма Парето",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "items": [
                    {"label": "Простой", "value": 42},
                    {"label": "Брак", "value": 26},
                    {"label": "Логистика", "value": 15},
                    {"label": "Наладка", "value": 9},
                    {"label": "Прочее", "value": 5}
                ],
                "threshold": 80,
                "value_suffix": " мин"
            }
        },
        {
            "slug": "WaterfallChart",
            "title": "Водопад изменений",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "start_label": "Q1",
                "start_value": 120,
                "steps": [
                    {"label": "Новые", "delta": 45, "kind": "pos"},
                    {"label": "Расширение", "delta": 28, "kind": "pos"},
                    {"label": "Отток", "delta": -33, "kind": "neg"},
                    {"label": "Скидки", "delta": -12, "kind": "neg"}
                ],
                "end_label": "Q2",
                "value_prefix": "€",
                "value_suffix": "k"
            }
        },
        {
            "slug": "SCurve",
            "title": "S-кривая (EVM)",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "periods": ["Янв", "Фев", "Мар", "Апр", "Май", "Июн"],
                "pv": [10, 25, 45, 65, 85, 100],
                "ev": [9, 22, 40, 58, 74, 88],
                "ac": [11, 27, 49, 70, 92, 108],
                "show_index": True,
                "value_suffix": "%"
            }
        },
        {
            "slug": "ControlChart",
            "title": "Контрольная карта",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "points": [12.1, 11.8, 12.4, 12.0, 11.6, 12.2, 12.9, 12.3, 11.9, 12.1, 12.5, 12.0],
                "mean": 12.15,
                "ucl": 13.0,
                "lcl": 11.3,
                "unit": " мм",
                "violations": [6]
            }
        },
        {
            "slug": "RadarProfile",
            "title": "Профиль компетенций",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "axes": ["Скорость", "Качество", "Цена", "Сервис", "Инновации", "Бренд"],
                "series": [
                    {"label": "Мы", "color": "var(--color-secondary)", "values": [80, 72, 60, 85, 78, 55]},
                    {"label": "Рынок", "color": "var(--text-muted)", "values": [65, 80, 75, 55, 60, 82]}
                ],
                "max": 100
            }
        },
        {
            "slug": "HeatmapMatrix",
            "title": "Матрица рисков",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "rows": ["Разработка", "Закупки", "Логистика", "Монтаж"],
                "cols": ["W1", "W2", "W3", "W4", "W5"],
                "cells": [
                    ["L", "M", "H", "M", "L"],
                    ["L", "L", "M", "H", "M"],
                    ["M", "H", "H", "M", "L"],
                    ["L", "L", "M", "M", "H"]
                ],
                "scale": "rag",
                "source_note": "Оценка риск-менеджмента"
            }
        },
        {
            "slug": "QuadrantMatrix",
            "title": "Матрица 2×2",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "points": [
                    {"label": "CRM", "x": 72, "y": 80, "bubble": 30, "color": "var(--color-success)"},
                    {"label": "ERP", "x": 40, "y": 55, "bubble": 24, "color": "var(--color-warning)"},
                    {"label": "Склад", "x": 25, "y": 30, "bubble": 22, "color": "var(--color-secondary)"},
                    {"label": "HR", "x": 60, "y": 20, "bubble": 18, "color": "var(--color-accent)"}
                ],
                "x_label": "Простота",
                "y_label": "Эффект",
                "quadrant_labels": ["Стратегические", "Быстрые победы", "Отложить", "Пересмотреть"]
            }
        },
        {
            "slug": "CohortGrid",
            "title": "Когортная таблица",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "cohorts": ["Янв", "Фев", "Мар", "Апр", "Май"],
                "periods": ["M0", "M1", "M2", "M3", "M4"],
                "values": [
                    [100, 92, 88, 85, 83],
                    [100, 90, 86, 84, None],
                    [100, 94, 89, None, None],
                    [100, 91, None, None, None],
                    [100, None, None, None, None]
                ],
                "metric": "Retention",
                "suffix": "%"
            }
        },
        {
            "slug": "NodeFlow",
            "title": "Поток узлов",
            "type": type_ui,
            "cat": cat_backend,
            "payload": {
                "variant": "tech",
                "flow_layout": "layered",
                "nodes": [
                    {"id": "in", "label": "Сырьё", "icon": "heroicons:cube", "status": "muted", "x": 12, "y": 50, "start_time": 0},
                    {"id": "cut", "label": "Резка", "icon": "heroicons:scissors", "status": "ok", "start_time": 900},
                    {"id": "weld", "label": "Сварка", "icon": "heroicons:fire", "status": "warn", "start_time": 1800},
                    {"id": "qc", "label": "ОТК", "icon": "heroicons:shield-check", "status": "ok", "start_time": 2700},
                    {"id": "ship", "label": "Отгрузка", "icon": "heroicons:truck", "status": "info", "start_time": 3600}
                ],
                "edges": [
                    {"from": "in", "to": "cut", "label": "подача"},
                    {"from": "cut", "to": "weld", "label": "партия", "duration_label": "12 мин"},
                    {"from": "weld", "to": "qc", "label": "контроль"},
                    {"from": "qc", "to": "ship", "label": "годные"}
                ]
            }
        },
        {
            "slug": "NotationTable",
            "title": "Иерархическая таблица",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "columns": ["Наименование", "Ед.", "Кол-во", "Цена", "Сумма"],
                "groups": [
                    {
                        "label": "Земляные работы",
                        "rows": [
                            {"cells": ["Разработка грунта", "м³", "1 200", "14,00", "16 800"], "highlight": False},
                            {"cells": ["Обратная засыпка", "м³", "640", "9,50", "6 080"]}
                        ],
                        "subtotal": "22 880"
                    },
                    {
                        "label": "Монолит",
                        "rows": [
                            {"cells": ["Бетон B25", "м³", "480", "96,00", "46 080"], "highlight": True},
                            {"cells": ["Арматура A500", "т", "38", "720,00", "27 360"]}
                        ],
                        "subtotal": "73 440"
                    }
                ],
                "unit": "€",
                "source_note": "Смета, раздел 2"
            }
        },
        # ─── ROADMAP P1 — B2B / ПРОДАЖИ ───
        {
            "slug": "SpecTable",
            "title": "Таблица спецификаций",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "Спецификация решения",
                "subtitle": "Ключевые параметры",
                "columns": ["Параметр", "Значение"],
                "rows": [
                    {"id": "r1", "label": "Процессор", "value": "Apple M3 Pro", "icon": "lucide:cpu", "color": "var(--color-secondary)", "highlight": True, "start_time": 0},
                    {"id": "r2", "label": "Память", "value": "36 ГБ", "icon": "lucide:memory-stick", "color": "var(--color-success)", "start_time": 900},
                    {"id": "r3", "label": "Накопитель", "value": "1 ТБ SSD", "icon": "lucide:hard-drive", "color": "var(--color-warning)", "start_time": 1800},
                    {"id": "r4", "label": "Автономность", "value": "до 18 часов", "icon": "lucide:battery-full", "color": "var(--color-accent)", "start_time": 2700}
                ],
                "highlight_rows": ["r1"]
            }
        },
        {
            "slug": "KpiDashboard",
            "title": "KPI-дашборд",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "title": "Ключевые метрики",
                "subtitle": "За последние 30 дней",
                "metrics": [
                    {"id": "m1", "label": "Выручка", "value": "2.4", "unit": "M €", "trend": "+18%", "color": "var(--color-success)", "icon": "heroicons:banknotes", "sparkline": [12, 18, 15, 22, 26, 24, 31], "start_time": 0},
                    {"id": "m2", "label": "Конверсия", "value": "6.8", "unit": "%", "trend": "+2.1%", "color": "var(--color-secondary)", "icon": "heroicons:cursor-arrow-rays", "sparkline": [3, 4, 4, 5, 5, 6, 7], "start_time": 900},
                    {"id": "m3", "label": "Средний чек", "value": "480", "unit": "€", "trend": "-4%", "color": "var(--color-warning)", "icon": "heroicons:receipt-percent", "sparkline": [520, 510, 500, 495, 490, 485, 480], "start_time": 1800},
                    {"id": "m4", "label": "Отток", "value": "1.2", "unit": "%", "trend": "-0.6%", "color": "var(--color-accent)", "icon": "heroicons:arrow-trending-down", "sparkline": [3, 2.6, 2.2, 2, 1.7, 1.4, 1.2], "start_time": 2700}
                ]
            }
        },
        {
            "slug": "GanttChart",
            "title": "Диаграмма Ганта",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "План запуска",
                "subtitle": "12 недель до релиза",
                "tasks": [
                    {"id": "t1", "name": "Аналитика", "start": 0, "end": 20, "progress": 100, "color": "var(--color-success)", "icon": "heroicons:chart-pie", "start_time": 0},
                    {"id": "t2", "name": "Дизайн", "start": 15, "end": 45, "progress": 80, "color": "var(--color-secondary)", "icon": "heroicons:paint-brush", "start_time": 900},
                    {"id": "t3", "name": "Разработка", "start": 40, "end": 80, "progress": 45, "color": "var(--color-primary)", "icon": "heroicons:code-bracket", "start_time": 1800},
                    {"id": "t4", "name": "Тесты и запуск", "start": 78, "end": 100, "progress": 10, "color": "var(--color-warning)", "icon": "heroicons:rocket-launch", "start_time": 2700}
                ],
                "milestones": [
                    {"id": "ms1", "label": "MVP", "at": 45, "color": "var(--color-warning)", "start_time": 3600},
                    {"id": "ms2", "label": "Релиз", "at": 100, "color": "var(--color-success)", "start_time": 4500}
                ]
            }
        },
        {
            "slug": "TeamGrid",
            "title": "Команда",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "Команда проекта",
                "subtitle": "Кто ведёт запуск",
                "members": [
                    {"id": "p1", "name": "Анна Ковалёва", "title": "Руководитель", "color": "var(--color-secondary)", "contacts": [{"icon": "heroicons:envelope", "text": "anna@it2b.top"}], "start_time": 0},
                    {"id": "p2", "name": "Игорь Лебедев", "title": "Техлид", "color": "var(--color-success)", "contacts": [{"icon": "heroicons:envelope", "text": "igor@it2b.top"}], "start_time": 900},
                    {"id": "p3", "name": "Мария Соколова", "title": "Продукт", "color": "var(--color-warning)", "contacts": [{"icon": "heroicons:paper-airplane", "text": "@msokolova"}], "start_time": 1800},
                    {"id": "p4", "name": "Павел Орлов", "title": "Маркетинг", "color": "var(--color-accent)", "contacts": [{"icon": "heroicons:chart-bar", "text": "pavel@it2b.top"}], "start_time": 2700}
                ]
            }
        },
        {
            "slug": "PricingTable",
            "title": "Тарифы",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "Тарифы",
                "subtitle": "Выберите подходящий",
                "plans": [
                    {"id": "pl1", "name": "Старт", "description": "Для первых шагов", "price": "490", "period": "€/мес", "features": ["1 агент", "1 000 диалогов", "Email-поддержка"], "cta": "Начать", "highlighted": False, "color": "var(--color-secondary)", "start_time": 0},
                    {"id": "pl2", "name": "Рост", "description": "Для растущей команды", "price": "1 490", "period": "€/мес", "badge": "Популярный", "features": ["5 агентов", "20 000 диалогов", "CRM-интеграция", "Приоритетная поддержка"], "cta": "Оформить", "highlighted": True, "color": "var(--color-secondary)", "start_time": 900},
                    {"id": "pl3", "name": "Enterprise", "description": "Для крупного бизнеса", "price": "По запросу", "period": "", "features": ["Неограниченно агентов", "SLA 99.9%", "Персональный менеджер", "On-premise"], "cta": "Связаться", "highlighted": False, "color": "var(--color-accent)", "start_time": 1800}
                ]
            }
        },
        # ─── ROADMAP P2 — ОБУЧЕНИЕ ───
        {
            "slug": "FlashCards",
            "title": "Флэш-карточки",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Проверьте себя",
                "subtitle": "Карточки-вопросы",
                "cards": [
                    {"id": "c1", "front": "Что такое RAG?", "back": "Retrieval-Augmented Generation — генерация с опорой на внешние документы.", "icon": "heroicons:document-magnifying-glass", "color": "var(--color-secondary)", "start_time": 0},
                    {"id": "c2", "front": "Зачем нужен векторный индекс?", "back": "Чтобы быстро находить похожие фрагменты по эмбеддингам.", "icon": "heroicons:circle-stack", "color": "var(--color-success)", "start_time": 2500},
                    {"id": "c3", "front": "Что такое галлюцинация?", "back": "Уверенный, но ложный ответ модели без опоры на факты.", "icon": "heroicons:exclamation-triangle", "color": "var(--color-warning)", "start_time": 5000}
                ]
            }
        },
        {
            "slug": "QuizSlide",
            "title": "Викторина",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "question": "Что снижает риск галлюцинаций у ИИ-агента?",
                "options": [
                    {"id": "o1", "text": "Более крупная модель", "correct": False, "start_time": 0},
                    {"id": "o2", "text": "Опорные источники (RAG)", "correct": True, "start_time": 800},
                    {"id": "o3", "text": "Повышение температуры", "correct": False, "start_time": 1600},
                    {"id": "o4", "text": "Больше промптов", "correct": False, "start_time": 2400}
                ],
                "explanation": "RAG подаёт модели проверенные факты из базы знаний — это главный способ борьбы с галлюцинациями.",
                "reveal_time": 5000
            }
        },
        {
            "slug": "StepByStep",
            "title": "Пошаговый процесс",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Как мы запускаем агента",
                "subtitle": "Четыре шага",
                "layout": "vertical",
                "steps": [
                    {"id": "s1", "number": 1, "title": "Аудит", "description": "Разбираем процессы и находим узкие места.", "icon": "heroicons:magnifying-glass", "color": "var(--color-secondary)", "start_time": 0},
                    {"id": "s2", "number": 2, "title": "Данные", "description": "Собираем базу знаний и регламенты.", "icon": "heroicons:circle-stack", "color": "var(--color-success)", "start_time": 1000},
                    {"id": "s3", "number": 3, "title": "Прототип", "description": "Собираем агента и тестируем на реальных кейсах.", "icon": "heroicons:wrench-screwdriver", "color": "var(--color-warning)", "start_time": 2000},
                    {"id": "s4", "number": 4, "title": "Запуск", "description": "Интегрируем с CRM и телефонией.", "icon": "heroicons:rocket-launch", "color": "var(--color-accent)", "start_time": 3000}
                ]
            }
        },
        {
            "slug": "DefinitionBlock",
            "title": "Определение",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "term": "Векторный поиск",
                "definition": "Технология поиска по смыслу: текст превращается в эмбеддинги, а близкие по смыслу фрагменты находятся по косинусной близости.",
                "examples": [
                    {"id": "e1", "text": "Поиск ответа в базе знаний, когда формулировка клиента не совпадает с документом.", "start_time": 1000},
                    {"id": "e2", "text": "Подбор похожих товаров или статей по смыслу, а не по ключевым словам.", "start_time": 2000}
                ],
                "related_terms": ["Эмбеддинг", "RAG", "Косинусная близость"]
            }
        },
        {
            "slug": "KnowledgeGraph",
            "title": "Граф знаний",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "concepts": [
                    {"id": "ai", "label": "ИИ-агент", "icon": "heroicons:cpu-chip", "color": "var(--color-secondary)", "is_main": True, "start_time": 0},
                    {"id": "crm", "label": "CRM", "icon": "heroicons:user-group", "color": "var(--color-success)", "start_time": 800},
                    {"id": "kb", "label": "База знаний", "icon": "heroicons:book-open", "color": "var(--color-warning)", "start_time": 1600},
                    {"id": "phone", "label": "Телефония", "icon": "heroicons:phone", "color": "var(--color-accent)", "start_time": 2400},
                    {"id": "analytics", "label": "Аналитика", "icon": "heroicons:chart-bar", "color": "var(--color-secondary)", "start_time": 3200}
                ],
                "connections": [
                    {"from": "ai", "to": "crm", "label": "сделки", "start_time": 900},
                    {"from": "ai", "to": "kb", "label": "поиск", "start_time": 1700},
                    {"from": "ai", "to": "phone", "label": "звонки", "start_time": 2500},
                    {"from": "ai", "to": "analytics", "label": "метрики", "start_time": 3300}
                ]
            }
        },
        # ─── ROADMAP P3 — ИСТОРИЯ ───
        {
            "slug": "TimelineEras",
            "title": "Хронология эпох",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Эпохи развития",
                "subtitle": "От механизации к ИИ",
                "eras": [
                    {"id": "er1", "name": "Индустрия 1.0", "period": "1784", "icon": "heroicons:cog-6-tooth", "color": "var(--color-secondary)", "description": "Пар и механизация.", "start_time": 0},
                    {"id": "er2", "name": "Индустрия 2.0", "period": "1870", "icon": "heroicons:bolt", "color": "var(--color-success)", "description": "Электричество и конвейер.", "start_time": 1000},
                    {"id": "er3", "name": "Индустрия 3.0", "period": "1969", "icon": "heroicons:cpu-chip", "color": "var(--color-warning)", "description": "Компьютеры и автоматизация.", "start_time": 2000},
                    {"id": "er4", "name": "Индустрия 4.0", "period": "2011", "icon": "heroicons:sparkles", "color": "var(--color-accent)", "description": "Сети и ИИ-агенты.", "start_time": 3000}
                ]
            }
        },
        {
            "slug": "QuoteCard",
            "title": "Цитата",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "quote": "Лучший способ предсказать будущее — создать его.",
                "author": "Питер Друкер",
                "author_title": "Теоретик менеджмента",
                "source": "Management, 1973"
            }
        },
        {
            "slug": "MapVisualization",
            "title": "Карта",
            "type": type_ui,
            "cat": cat_sales,
            "payload": {
                "variant": "tech",
                "title": "География клиентов",
                "subtitle": "Центры и связи",
                "points": [
                    {"id": "p1", "label": "Берлин", "x": 52, "y": 40, "color": "var(--color-secondary)", "icon": "heroicons:building-office-2", "start_time": 0},
                    {"id": "p2", "label": "Мюнхен", "x": 50, "y": 62, "color": "var(--color-success)", "icon": "heroicons:building-office-2", "start_time": 900},
                    {"id": "p3", "label": "Вена", "x": 66, "y": 58, "color": "var(--color-warning)", "icon": "heroicons:building-office-2", "start_time": 1800},
                    {"id": "p4", "label": "Цюрих", "x": 44, "y": 70, "color": "var(--color-accent)", "icon": "heroicons:building-office-2", "start_time": 2700}
                ],
                "connections": [
                    {"from": "p1", "to": "p2", "start_time": 1000},
                    {"from": "p1", "to": "p3", "start_time": 1900},
                    {"from": "p2", "to": "p4", "start_time": 2800}
                ]
            }
        },
        {
            "slug": "HistoricalCompare",
            "title": "Сравнение эпох",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "transition_style": "slide",
                "before": {"label": "До", "caption": "Сотрудник вручную отвечает на однотипные вопросы по 15 минут.", "image": "", "start_time": 0},
                "after": {"label": "После", "caption": "ИИ-агент отвечает мгновенно и передаёт сложное менеджеру.", "image": "", "start_time": 1500}
            }
        },
        # ─── ROADMAP P4 — ЭКО / ФИЛОСОФИЯ ───
        {
            "slug": "CircularGauge",
            "title": "Круговая метрика",
            "type": type_ui,
            "cat": cat_stats,
            "payload": {
                "variant": "tech",
                "title": "Прогресс внедрения",
                "subtitle": "Ключевые показатели",
                "gauges": [
                    {"id": "g1", "value": 82, "max": 100, "unit": "%", "label": "Автоматизация", "color": "var(--color-secondary)", "icon": "heroicons:bolt", "start_time": 0},
                    {"id": "g2", "value": 64, "max": 100, "unit": "%", "label": "Доля ИИ-ответов", "color": "var(--color-success)", "icon": "heroicons:chat-bubble-left-right", "start_time": 900},
                    {"id": "g3", "value": 96, "max": 100, "unit": "%", "label": "Довольных клиентов", "color": "var(--color-warning)", "icon": "heroicons:face-smile", "start_time": 1800}
                ]
            }
        },
        {
            "slug": "SustainabilityTimeline",
            "title": "Шкала устойчивости",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Путь к устойчивости",
                "subtitle": "Этапы перехода",
                "milestones": [
                    {"id": "s1", "year": "2022", "event": "Аудит углеродного следа", "impact": "Базовая линия выбросов.", "icon": "heroicons:magnifying-glass", "color": "var(--color-secondary)", "start_time": 0},
                    {"id": "s2", "year": "2023", "event": "Переход на ВИЭ", "impact": "−40% выбросов Scope 2.", "icon": "heroicons:bolt", "color": "var(--color-success)", "start_time": 1000},
                    {"id": "s3", "year": "2024", "event": "Безотходное производство", "impact": "94% отходов в переработку.", "icon": "heroicons:arrow-path", "color": "var(--color-warning)", "start_time": 2000},
                    {"id": "s4", "year": "2026", "event": "Углеродная нейтральность", "impact": "Net Zero по Scope 1–2.", "icon": "heroicons:globe-europe-africa", "color": "var(--color-accent)", "start_time": 3000}
                ]
            }
        },
        {
            "slug": "ValuesTable",
            "title": "Таблица ценностей",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Наши ценности",
                "subtitle": "Ценность → практика → результат",
                "columns": ["Ценность", "Практика", "Результат"],
                "rows": [
                    {"id": "v1", "value": "Прозрачность", "practice": "Открытые отчёты и метрики для клиента.", "result": "Рост доверия и LTV.", "icon": "heroicons:eye", "color": "var(--color-secondary)", "start_time": 0},
                    {"id": "v2", "value": "Скорость", "practice": "Отвечаем и знакомимся в тот же день.", "result": "Короче цикл сделки.", "icon": "heroicons:bolt", "color": "var(--color-success)", "start_time": 900},
                    {"id": "v3", "value": "Забота", "practice": "Поддерживаем пользователей 24/7.", "result": "NPS выше 60.", "icon": "heroicons:heart", "color": "var(--color-warning)", "start_time": 1800}
                ],
                "color_scheme": "neutral"
            }
        },
        {
            "slug": "OrganicGrid",
            "title": "Органическая сетка",
            "type": type_ui,
            "cat": cat_ui,
            "payload": {
                "variant": "tech",
                "title": "Направления",
                "subtitle": "Органическая сетка",
                "items": [
                    {"id": "o1", "title": "Автоматизация", "desc": "Рутина уходит к агентам.", "icon": "heroicons:cpu-chip", "color": "var(--color-secondary)", "size": "2x2", "start_time": 0},
                    {"id": "o2", "title": "Аналитика", "desc": "Решения на данных.", "icon": "heroicons:chart-bar", "color": "var(--color-success)", "size": "2x1", "start_time": 900},
                    {"id": "o3", "title": "Поддержка", "desc": "24/7 без очередей.", "icon": "heroicons:lifebuoy", "color": "var(--color-warning)", "size": "2x1", "start_time": 1800},
                    {"id": "o4", "title": "Интеграции", "desc": "CRM, телефония, склад.", "icon": "heroicons:puzzle-piece", "color": "var(--color-accent)", "size": "4x2", "start_time": 2700}
                ]
            }
        },
        {
            "slug": "EndMarkerSlide",
            "title": "Конец презентации",
            "type": type_slide,
            "cat": cat_ui,
            "payload": {}
        }
    ]

    _cat_map = {"backend": cat_backend, "sales": cat_sales, "ui": cat_ui, "stats": cat_stats}
    components_data += [
        {**entry, "type": type_slide, "cat": _cat_map[entry["cat"]]}
        for entry in _domain_v2.build()
    ]

    components_data += [
        {**entry, "type": type_slide, "cat": _cat_map[entry["cat"]]}
        for entry in _orthodox_seed.build()
    ]

    def _normalize_density(node, min_step=800):
        """Разряжает start_time в массивах до шага ≥ min_step (AGENTS.md §8.3):
        только сдвигает вперёд, первый элемент и синхронные (gap 0) не трогает."""
        if isinstance(node, dict):
            return {k: _normalize_density(v, min_step) for k, v in node.items()}
        if isinstance(node, list):
            node = [_normalize_density(v, min_step) for v in node]
            prev = None
            for item in node:
                if not isinstance(item, dict):
                    continue
                t = item.get("start_time")
                if isinstance(t, (int, float)) and not isinstance(t, bool):
                    if prev is not None:
                        gap = t - prev
                        # gap == 0 — намеренная синхронность (не трогаем);
                        # 0 < gap < min_step или gap < 0 (нарушен порядок) → выравниваем вперёд
                        if gap != 0 and gap < min_step:
                            item["start_time"] = prev + min_step
                            t = item["start_time"]
                    prev = t
            return node
        return node

    def _normalize_interactive(node):
        """InteractiveArchitecture (AGENTS §4.4): тайминг только у ОДНОЙ ноды (фокус камеры),
        остальные появляются автоматически. Убираем разнобой/отрицательные значения,
        который валидатор считает non_monotonic. Первая нода = 0."""
        if not isinstance(node, dict):
            return node
        nodes = node.get("nodes")
        if isinstance(nodes, list):
            for i, n in enumerate(nodes):
                if isinstance(n, dict):
                    if i == 0:
                        n["start_time"] = 0
                    else:
                        n.pop("start_time", None)
        return node

    import copy
    created, updated, skipped = 0, 0, 0
    for data in components_data:
        payload = data["payload"]
        if data["slug"] == "InteractiveArchitecture":
            payload = _normalize_interactive(copy.deepcopy(payload))
        else:
            payload = _normalize_density(copy.deepcopy(payload))
        existing = session.query(Component).filter(Component.slug == data["slug"]).first()
        if existing:
            if getattr(existing, "is_custom", False):
                print(f"Пропущен кастомный компонент «{data['slug']}» (сид не трогает)")
                skipped += 1
                continue
            existing.title = data["title"]
            existing.type_id = data["type"].id
            existing.default_payload = payload
            existing.categories = [data["cat"]]
            existing.is_custom = False
            try:
                session.commit()
                print(f"Обновлён {data['slug']}")
                updated += 1
            except Exception as e:
                print(f"Failed to update {data['slug']}: {e}")
                session.rollback()
            continue

        desc = f"Компонент {data['slug']}"
        if data["slug"] == "RoiCalculatorSlide":
            desc = "Мощный ROI-калькулятор бизнес-показателей. Поддерживает таймлайны (каскадную анимацию), линейную математику множителей и ручное управление ползунками во время питча."

        comp = Component(
            slug=data["slug"],
            title=data["title"],
            description=desc,
            type_id=data["type"].id,
            default_payload=payload,
            is_custom=False,
        )
        comp.categories.append(data["cat"])
        session.add(comp)
        try:
            session.commit()
            print(f"Added {comp.slug}")
            created += 1
        except Exception as e:
            print(f"Failed to add {comp.slug}: {e}")
            session.rollback()

    print(f"Seeding complete! Создано: {created}, обновлено: {updated}, пропущено кастомов: {skipped}.")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Сид компонентов (upsert по slug, DROP удалён). Кастомы через API не трогает никогда.")
    ap.add_argument("--force", action="store_true", help="(зарезервировано) Перезаписать managed-компоненты — сейчас поведение по умолчанию")
    seed_db(force=ap.parse_args().force)
