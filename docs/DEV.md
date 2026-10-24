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

Демо: http://localhost:5175/p/1 (машина), `/p/5` (Rive-персонаж).

## Rive-риг персонажа

```bash
~/.rive/bin/rive --version          # нужен Rive CLI 1.7
python3 scripts/build_rive_character.py
```

Скрипт генерирует `core/rive/character/scene.rml`, собирает `.riv` и копирует
его в `core/public/rive/character.riv`. Демо: `/p/5` (один ведущий),
`/p/6` (host + cohost).

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


## 3D-ассеты (2026-10-24)

3D-аватар использует Ready Player Me GLB и мокап-клипы Mixamo. GLB лежит в
репозитории; клипы — нет (лицензия Adobe ограничивает перераспространение).

```bash
python scripts/fetch_avatar_anims.py      # скачать 16 Mixamo GLB
python scripts/extract_avatar_anims.py    # собрать avatar-anims.js
python scripts/build_avatar_asset.py      # обернуть GLB в .js для iframe
```

На сервер `core/public/models/anim/` и `.env` переносятся вручную (scp),
не через GitHub.
