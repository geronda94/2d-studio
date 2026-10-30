# Дампы базы SceneEngine

`scene_db_YYYY-MM-DD.sql.gz` — полный дамп PostgreSQL (`scene_db`), снятый из контейнера
`scene-saas-db-1`. В дампе вся схема и данные: пользователи, проекты, ассеты, сцены.

## Снять свежий дамп

```bash
docker exec scene-saas-db-1 pg_dump -U scene_user -d scene_db --no-owner --no-privileges \
  | gzip -9 > db/scene_db_$(date +%F).sql.gz
```

## Восстановить

```bash
# пустая база (осторожно: перезапишет данные)
docker exec -i scene-saas-db-1 psql -U scene_user -d scene_db \
  < <(zcat db/scene_db_2026-10-30.sql.gz)
```

Если базы ещё нет:

```bash
docker exec scene-saas-db-1 createdb -U scene_user scene_db
```

## Важно

- В дампе есть персональные данные и хэши паролей — репозиторий должен оставаться приватным.
- Объём: ~7 МБ в сжатом виде (несжатый ~40 МБ), поэтому файл лежит в git как есть.
- Файлы пользователей (`uploads/`) в репозиторий не попадают — они в `.gitignore`.
