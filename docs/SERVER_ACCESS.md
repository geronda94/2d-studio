# SERVER_ACCESS.md — рабочий сервер, проект и как подключиться с ПК

Актуально: работа над проектом перенесена на рабочий сервер. На сервере над одним
рабочим деревом могут одновременно работать несколько агентов/сессий — **будь аккуратен
с git** (см. раздел «Git»).

## Сервер и проект

- SSH: `ssh root@min-server` (хост `min-server`; если DNS не резолвится — используй IP, порт 22).
- Проект: `~/projects/Presentation` (`root@min-server:~/projects/Presentation`).
- Список всех проектов на сервере: `ls -la ~/projects`.

## Что запущено

Compose-проект `presentation-saas`, три сервиса: `db` (PostgreSQL 15), `backend` (FastAPI),
`frontend` (Vite).

- Порты на сервере: frontend `5174`, backend `8001`, БД `5435` (наружу) → внутри контейнера `5432`.
- Статус: `cd ~/projects/Presentation && docker compose ps`.
- Логи: `docker compose logs -f backend` / `docker compose logs -f frontend`.
- Backend после правок Python перезапускать: `docker compose restart backend`
  (нет `--reload`). Frontend — dev c volume `./core`, правки подхватываются без рестарта.

## Подключение с ПК (SSH-туннель к веб-интерфейсу)

```bash
ssh -N -L 5174:localhost:5174 -L 8001:localhost:8001 root@min-server
```

Оставь это окно открытым, затем на ПК открой:

- интерфейс: http://localhost:5174
- API напрямую: http://localhost:8001

## Бэкап и восстановление БД

```bash
# Бэкап (пишет в корень проекта). Сырой дамп БД уже >100 МБ, поэтому в git
# коммитим gzip-версию (dump.sql.gz), а сырой dump.sql — локально, вне git.
cd ~/projects/Presentation
docker compose exec -T db pg_dump -U presentation_user -d presentation_db | gzip -9 > dump.sql.gz

# Восстановление (из gzip)
gunzip -c dump.sql.gz | docker compose exec -T db psql -U presentation_user -d presentation_db
```

Свежий `dump.sql.gz` — точка сохранности БД, коммитится в репозиторий
(сырой `dump.sql` в `.gitignore` из-за лимита GitHub 100 МБ на файл).

> ⚠️ После наката дампа обязательно синхронизируй медиа (см. следующий раздел) —
> иначе картинки/аудио в слайдах и рендере будут «пустыми» (в БД пути есть, файлов нет).

## Медиа и загрузки НЕ в git — синхронизировать вручную

Библиотека медиа и загрузки презентаций **не коммитятся** (в `.gitignore`: `uploads/`,
`backend/media/`). Поэтому после `git pull` + восстановления БД из дампа файлы локально
**отсутствуют**: в рендере/слайдах картинки не отрисуются, пока не подтянешь файлы с сервера.

```bash
cd ~/projects/Presentation    # локально, на ПК
rsync -rlt --info=stats2 -e ssh root@min-server:'~/projects/Presentation/backend/media/' "backend/media/"
rsync -rlt --info=stats2 -e ssh root@min-server:'~/projects/Presentation/uploads/'      "uploads/"
```

- `-rlt` (recursive + сохранять время) без `-a` — чтобы не тянуть root-ownership/права.
- Направление одностороннее (сервер → ПК). Для удаления лишнего локально — добавь `--delete`
  (осторожно, без него только докачивает/обновляет).

## Git

- Ветка `main`, remote `origin` = `git@github.com:geronda94/Presentation.git`.
- **Не делай `git add -A` на сервере**: в дереве есть незакоммиченные правки других
  агентов. Стейджи и коммить только свои файлы, чужие изменения не трогай.
- Push: `git push origin main` (при необходимости `git pull --rebase` перед пушем).

## Что не коммитить (рабочий мусор)

`.playwright-mcp/`, `deploy.log`, `qa-*.png`, `media-library-fixed.png` и прочие временные
скриншоты — это артефакты сессий. Их стоит вынести в `.gitignore`, а не коммитить.
