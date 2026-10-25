# Backups

## scene_db_2026-10-25.sql.gz

Полный дамп `scene_db` (PostgreSQL 15), снят 2026-10-25:

```bash
docker compose exec -T db pg_dump -U scene_user -d scene_db \
  --clean --if-exists --no-owner | gzip -9 > backups/scene_db_2026-10-25.sql.gz
```

Восстановление:

```bash
gunzip -c backups/scene_db_2026-10-25.sql.gz | \
  docker compose exec -T db psql -U scene_user -d scene_db
```

Важно:
- В этом дампе таблицы `users`, `api_keys`, `user_sessions` пусты — секретов нет.
- Перед будущими дампами проверяй, что в БД нет паролей/токенов/ключей.
  Репозиторий публичный: полный дамп с секретами коммитить нельзя.
