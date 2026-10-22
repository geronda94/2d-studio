# DEV — рабочие порты SceneEngine

Проект поднимается отдельно от исходного `Presentation`, чтобы оба могли работать одновременно.

| Сервис | URL / порт | Контейнер |
|---|---|---|
| Frontend | http://localhost:5175 | `scene-saas-frontend-1` |
| Backend API | http://localhost:8002 | `scene-saas-backend-1` |
| API через Vite | http://localhost:5175/api/... | proxy → backend |
| PostgreSQL | localhost:5436 | `scene-saas-db-1` |
| DB name | `scene_db` | |
| DB user / pass | `scene_user` / `scene_password` | |

Compose project: `scene-saas`. Тома: `scene-saas_scene_postgres_data`.

## Запуск

```bash
cd "Projects/SceneEngine"
docker compose up -d
```

## Первичный сид (один раз на чистой БД)

```bash
docker compose exec -T backend python scripts/seed_tokens.py
docker compose exec -T backend python scripts/seed_variants.py
docker compose exec -T backend python scripts/seed_presets.py
docker compose exec -T backend python scripts/seed_scene_demo.py
```

Демо: http://localhost:5175/p/1

## Полезное

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose restart backend
docker compose down
```

## Важно

- Не занимать порты исходного проекта: `5174 / 8001 / 5435`.
- Не менять `name: scene-saas` и имя тома без необходимости — иначе compose создаст второй набор контейнеров/БД.
