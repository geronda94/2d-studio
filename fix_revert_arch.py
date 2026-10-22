import json
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://presentation_user:presentation_password@localhost:5435/presentation_db')

payload = {'variant': 'tech', 'nodes': [{'id': 'lb', 'label': 'Load Balancer', 'desc': 'Cloudflare', 'color': 'chart-1', 'icon': 'heroicons:server', 'details': 'Балансировщик нагрузки (CDN). Фильтрует DDoS атаки.', 'to': ['web1', 'web2'], 'start_time': 0}, {'id': 'web1', 'label': 'Web Server 1', 'desc': 'Node.js / Vue', 'color': 'chart-2', 'icon': 'heroicons:computer-desktop', 'details': 'Первичный фронтенд-сервер.', 'to': ['api'], 'start_time': 0}, {'id': 'web2', 'label': 'Web Server 2', 'desc': 'Node.js / Vue', 'color': 'chart-2', 'icon': 'heroicons:computer-desktop', 'details': 'Резервный фронтенд-сервер.', 'to': ['api'], 'start_time': 0}, {'id': 'api', 'label': 'API Gateway', 'desc': 'Kong', 'color': 'chart-1', 'icon': 'heroicons:arrows-right-left', 'details': 'Единая точка входа для всех запросов.', 'to': ['auth', 'db', 'cache', 'queue'], 'start_time': -800}, {'id': 'auth', 'label': 'Auth Service', 'desc': 'Keycloak', 'color': 'chart-3', 'icon': 'heroicons:key', 'details': 'Сервис аутентификации.', 'to': [], 'start_time': 700}, {'id': 'cache', 'label': 'Redis Cache', 'desc': 'In-Memory', 'color': 'chart-4', 'icon': 'heroicons:circle-stack', 'details': 'Сверхбыстрое in-memory хранилище.', 'to': [], 'start_time': 4200}, {'id': 'queue', 'label': 'Message Queue', 'desc': 'RabbitMQ', 'color': 'chart-3', 'icon': 'heroicons:queue-list', 'details': 'Брокер сообщений.', 'to': ['worker'], 'start_time': 5200}, {'id': 'worker', 'label': 'Async Worker', 'desc': 'Celery', 'color': 'chart-1', 'icon': 'heroicons:cpu-chip', 'details': 'Фоновый воркер.', 'to': ['db'], 'start_time': 2200}, {'id': 'db', 'label': 'Primary DB', 'desc': 'PostgreSQL', 'color': 'chart-4', 'icon': 'heroicons:circle-stack', 'details': 'Основная база данных.', 'to': [], 'start_time': 7200}]}

with engine.connect() as conn:
    conn.execute(
        text("UPDATE components SET default_payload = :payload, example = :payload WHERE slug = 'InteractiveArchitecture'"),
        {"payload": json.dumps(payload)}
    )
    conn.commit()
print("InteractiveArchitecture restored in DB!")
