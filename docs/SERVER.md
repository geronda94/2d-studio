# SERVER — деплой и продолжение работы на сервере

Репозиторий: `git@github.com:geronda94/2d-studio.git` (HTTPS: `https://github.com/geronda94/2d-studio.git`).
Ветка: `main`.

## 1. Требования

- Linux, Docker + Docker Compose v2.
- Свободные порты: `5175` (frontend), `8002` (backend), `5437` (Postgres).
- Для рендера: `ffmpeg`, `xvfb`, `openbox`, `xdotool` (уже в backend-образе),
  Playwright Chromium (уже в образе), `$DISPLAY` для realtime-захвата.

## 2. Клонирование

```bash
mkdir -p ~/projects && cd ~/projects
git clone git@github.com:geronda94/2d-studio.git SceneEngine
cd SceneEngine
```

## 3. Окружение

```bash
cp .env.example .env
# заполнить ключи (Gemini/Freesound) только если нужен AI/TTS
# AUTH_MODE=off для локальной разработки
```

`.env` **не коммитится**. Секреты не хранить в репозитории.

## 4. Запуск

```bash
docker compose up -d
docker compose ps
```

Ожидаемые контейнеры:
- `scene-saas-frontend-1` → `5175`
- `scene-saas-backend-1` → `8002`
- `scene-saas-db-1` → `5437`

## 5. Первичный сид (чистая БД)

```bash
docker compose exec -T backend python scripts/seed_tokens.py
docker compose exec -T backend python scripts/seed_variants.py
docker compose exec -T backend python scripts/seed_presets.py
docker compose exec -T backend python scripts/seed_scene_demo.py
```

Демо: `http://SERVER:5175/p/1`.

## 6. SSH-туннель (если порты закрыты)

```bash
ssh -N -L 5175:localhost:5175 -L 8002:localhost:8002 user@server
```

Затем локально: `http://localhost:5175`.

## 7. Обновление кода

```bash
cd ~/projects/SceneEngine
git pull --rebase origin main
docker compose restart backend
# frontend — Vite dev, подхватывает изменения сам
```

Если менялись зависимости:
```bash
docker compose exec -T frontend npm install
```

## 8. Логи и здоровье

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
curl -s http://localhost:8002/presentations/1/scenes
curl -s http://localhost:8002/scene-library/templates | head -c 200
```

## 9. Бэкап БД

```bash
cd ~/projects/SceneEngine
docker compose exec -T db pg_dump -U scene_user -d scene_db | gzip -9 > backup-$(date +%F).sql.gz
```

Восстановление:
```bash
gunzip -c backup-YYYY-MM-DD.sql.gz | docker compose exec -T db psql -U scene_user -d scene_db
```

## 10. Медиа

`uploads/` и `backend/media/` не в git. Для сцен пока не критичны: демо и
шаблоны используют CSS/SVG. При появлении медиа — синхронизировать отдельно
(`rsync`) или хранить в S3-совместимом хранилище.

## 11. Рендер

Realtime-захват:
- требует `$DISPLAY` (Xvfb/headful Chromium);
- backend ждёт `window.__sceneReady === true`;
- длительность — `EndMarkerSlide`;
- портретный safe-zone — 0.85.

Полный прогон рендера пока не автоматизирован в CI. Проверять вручную через UI
«Рендер» или `POST /renders/`.

## 12. Что агенту делать первым делом

1. `git pull`.
2. `docker compose up -d`.
3. `docker compose ps` — все три сервиса Up.
4. `curl` эндпоинты из §8.
5. Открыть `/p/1`.
6. Прочитать `docs/STATUS.md` → «Ближайшие 10 задач».
7. Работать по `docs/PROCESSES.md` и `docs/ROADMAP_2D.md`.

## 13. Правила git на сервере

- Не делать `git add -A`, если в дереве могут быть чужие правки.
- Стейджить только свои файлы.
- Перед push: `git pull --rebase`, `npm run build` (core), проверка API.
- Не коммитить `.env`, `uploads/`, `backend/media/`, `node_modules/`, `dist/`.
