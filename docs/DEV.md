# DEV — рабочие порты SceneEngine

Проект поднимается отдельно от исходного `Presentation`, чтобы оба могли работать одновременно.

| Сервис | URL / порт | Контейнер |
|---|---|---|
| Frontend | http://localhost:5175 | `scene-saas-frontend-1` |
| Backend API | http://localhost:8002 | `scene-saas-backend-1` |
| API через Vite | http://localhost:5175/api/... | proxy → backend |
| PostgreSQL | localhost:5437 | `scene-saas-db-1` |
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

## Rive (frozen legacy)

Собственный Rive-риг и его генератор удалены из активного пайплайна. В репозитории
остались только готовые актёры `oldman`/`bob` и рантайм для старых сцен:
`core/public/rive/`, `core/public/vendor/rive-actor.js`. Новые персонажи —
SceneRig: `docs/RIG_FORMAT.md`.

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


## 2D Paper Cast (production)

3D/Babylon заморожен. Персонажи — Canvas 2D:

- `http://localhost:5175/character-studio.html` — Paper Cast Studio
  (31 поза, 82 фонемы, липсинк, палитра);
- `http://localhost:5175/p/12` — демо-сцена `character-paper-duo`;
- шаблон: `GET http://localhost:8002/scene-library/templates/character-paper-duo`;
- объект: `GET http://localhost:8002/scene-library/objects/character-paper`.

Пересев демо:

```bash
docker compose exec -T backend python scripts/seed_paper_duo.py
```

API библиотеки, который нужен сценам:

```bash
curl http://localhost:8002/scene-library/templates
curl http://localhost:8002/scene-library/objects/character-paper
curl http://localhost:8002/scene-library/characters
```

## 3D archive (frozen)

Всё 3D лежит в `drafts/3d/`: Babylon, GLB, SceneRig, Rig Studio, Object
Studio, Clip Editor и старые seed/import-скрипты. Это не production;
`core/public` больше не содержит 3D-движок. Инструкция по возврату —
`drafts/3d/README.md`.

Старые команды `backend.rig`, Blender и `scripts/rig_import.py` относятся к
архиву; не использовать для новых сцен без явного запроса.

## Local Whisper (STT)

Бэкенд **не устанавливает** torch/whisper: транскрипция идёт в локальный
OpenAI-совместимый сервис (faster-whisper) через `STT_URL`.

```bash
# .env
STT_URL=http://host.docker.internal:8788
STT_KEY=local-whisper-key
```

В Docker `127.0.0.1:8788` указывает на контейнер, поэтому нужен
`host.docker.internal`. Проверка: `curl http://127.0.0.1:8788/health`.

## Сборка backend

По умолчанию compose использует уже собранный `scene-saas-backend:latest`
(в текущем окружении — совместимый предсобранный образ), а код монтируется
из `./backend` и `./scripts`. Чистая пересборка:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build backend
```

`backend/Dockerfile` ставит только лёгкие зависимости; Whisper/torch в образ
не входят — STT идёт через `STT_URL`.

## Frontend: native binding (Alpine)

Vite 8 использует rolldown с платформенными optional-зависимостями:
`@rolldown/binding-linux-x64-gnu` (glibc) и `...-musl` (Alpine). `npm ci`
ставит биндинг только под текущую libc, поэтому общий `core/node_modules`
между хостом и контейнером ломает одну из сторон.

Сейчас `node_modules` контейнера вынесен в отдельный named-volume
`scene_node_modules` — хост и Alpine больше не пересекаются:

- **Docker**: `docker compose up -d frontend` — при первом старте контейнер
  сам выполнит `npm ci` внутри volume (поставится musl-биндинг).
- **Хост**: `cd core && npm ci` — ставится gnu-биндинг, Docker это не ломает.
- **Переустановить зависимости контейнера**:
  `docker compose run --rm frontend npm ci` или
  `docker volume rm scene-saas_scene_node_modules` (при остановленном frontend).

Если когда-нибудь понадобится вернуться к общему `node_modules`, после
`npm ci` на хосте доставьте musl-биндинг:
`npm install --no-save @rolldown/binding-linux-x64-musl@1.2.5`.

Альтернатива без Docker: `npm run dev -- --host 0.0.0.0 --port 5175` на хосте.

## STT proxy (Docker → localhost Whisper)

Если Whisper слушает только `127.0.0.1:8788`, контейнер до него не дотянется.
Прокси на Docker-шлюзе:

```bash
python3 scripts/stt_proxy.py --listen-host 172.17.0.1
# при другой сети: --listen-host <gateway>
```

Плюс правило UFW для Docker-сетей:

```bash
ufw allow from 172.16.0.0/12 to any port 8788 proto tcp
```

Проверка из контейнера:

```bash
docker compose exec backend python -c \"import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:8788/health', timeout=3).read())\"
```
