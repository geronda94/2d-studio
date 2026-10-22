# ENTERPRISE_AUDIT_PLAN_V2.md — Логи, версии, ИИ-аккаунты (переработанный)

> Заменяет `ENTERPRISE_AUDIT_PLAN.md` (v1). В v1 были фатальные дефекты:
> middleware-аудит не транзакционен и не видит `path_params`; in-memory очередь теряла
> записи; «tamper-evident» на app-хешах — фикция; полные снапшоты раздували БД;
> on-behalf без согласия = имперсонация; отсутствовали тесты/SLO/concurrency.
> В v2 это закрыто.

---

## 0. Изменения относительно v1 (кратко)

| v1 (дефект) | v2 (решение) |
|---|---|
| Резолв в middleware | **Резолв — FastAPI-зависимость** (видит `path_params`, роль, цель) |
| Аудит после коммита, отдельная сессия | **Транзакционный аудит**: строка в **той же транзакции** (session event `before_commit`) |
| In-memory очередь | **Durable outbox** (таблица) + воркер для внешних sink'ов |
| App-хеш «tamper-evident» | Честно: app-хеш **не** защищает от DBA; immutability = DB-ревоук/триггер + внешний sink (Ф4) |
| Полные снапшоты | **Checkpoints (full) + дельты**, object-level **content-addressed dedup** |
| Два механизма версий без ролей | Явно: **`project_revisions` — источник истины**; `presentation_revisions` — op-log без снапшотов |
| Restore всего, включая участников | Restore **только контент**; members/tokens — исключены (security) |
| On-behalf без согласия | **Consent-модель**: subject явно одобряет делегирование |
| Клиентский `X-AI-Run-Id` | **Серверный AI-run** (`/ai/runs`), ссылка обязательна и валидируется |
| Нет concurrency | **Optimistic locking**: `version` + `If-Match` → 409 |
| Нет тестов/SLO/флагов | Добавлены разделы 8–10 |

---

## 1. Аудит: транзакционная модель (без middleware)

### 1.1 Почему не middleware
- middleware **не имеет** `path_params` (роутинг позже) → цель/роль не определить надёжно;
- middleware пишет **после** коммита → лог не атомарен с мутацией.

### 1.2 Как правильно
1. `get_db` отдаёт сессию запроса (`session.info["audit"] = []`).
2. Зависимость `resolve_context` (в том же пути, что `enforce_write`) вычисляет
   `{actor_type, actor_user_id, actor_key_id, on_behalf_of_user_id, effective_user_id,
   project_id, presentation_id, action, decision, deny_reason, ai_run_id}` и кладёт в `session.info`.
3. **Хук `before_commit`** (SQLAlchemy `event.listens_for(Session, "before_commit")`) дописывает
   `AuditLog`-строки в **ту же транзакцию**. Итог: мутация и лог **вместе коммитятся или вместе
   откатываются** — дыр нет.
4. **Deny (401/403/CSRF/scopes)**: транзакции-мутации нет → пишем deny отдельной короткой сессией
   синхронно, `try/except` (безопасность важнее latency). Это единственный «после-факта» путь.
5. **Внешние sink'и (SIEM/webhook)** — через **durable outbox**: `before_commit` дополнительно
   кладёт `audit_outbox`-строку; отдельный воркер вычитывает и пушит. Перезапуск не теряет.

### 1.3 Модель `audit_log` (+ партиции)
`id BIGSERIAL, created_at TIMESTAMPTZ` (составной PK), `request_id`, `actor_type`, `actor_user_id`,
`actor_key_id`, `on_behalf_of_user_id`, `effective_user_id`, `project_id`, `presentation_id`,
`slide_id`, `action`, `method/path/status`, `decision`, `deny_reason`, `ip/user_agent`,
`ai_run_id`, `diff_masked` JSONB, `meta_masked` JSONB.
- Партиции **по месяцам**, дефолтная партиция, автосоздание (managed job) на 2 месяца вперёд.
- Индексы: `(project_id, created_at desc)`, `(effective_user_id, created_at desc)`, `(request_id)`.
- **Иммутабельность** (Ф4): `REVOKE UPDATE, DELETE` для app-роли + триггер, отклоняющий UPDATE/DELETE;
  хеш-цепочка **только** вместе с внешним sink/WORM — иначе не заявляется как tamper-evidence.

### 1.4 Маскирование (PII + секреты)
Deep-redaction по denylist: `password, key, token, cookie, authorization, secret` **и PII**
(`email, phone, telegram` — маска `i***@d***`). `diff_masked` хранит **ключи/суммы**, не полные
payload; глубокая ссылка — на `project_revisions.id`. Лимит 32 КБ.

### 1.5 Что логируем
Все мутации (allow+deny), операции с ключами/паролями/участниками/владением, AI-операции.
Чтения — **не по умолчанию**; отдельный флаг `AUDIT_LOG_READS` (комплаенс), с отдельной партицией
и семплированием, чтобы не взорвать объём.

---

## 2. Версии: единый источник истины + дельты

### 2.1 Разграничение (устраняет дрейф)
- **`project_revisions` — источник истины для отката** (контент проекта).
- **`presentation_revisions` — op-log** для аудита/истории правок презентации; **снапшоты из неё
  убираем** (миграция: перестаём писать `snapshot`, поле оставляем nullable для легаси).
  Двойного хранения нет.

### 2.2 Content-addressed dedup (убирает раздувание)
- Таблица `content_blobs(hash PK, data JSONB, size, created_at)`.
- Снапшот ревизии = **дерево хешей** (`slides → payload_hash`, meta/tokens). Дельты — по сущностям.
- Один и тот же payload 60 раз не хранится 60 раз — ссылаемся на blob.

### 2.3 Checkpoints + дельты
| Тип | Что | Когда |
|---|---|---|
| `checkpoint` | полный снапшот (дерево хешей) | каждый N-й autosave / вручную / перед ИИ |
| `delta` | только изменённые сущности | каждая мутация (из `before/after` хука) |
| `restore` | снапшот после отката | откат |

Прунинг: последние K checkpoints (напр. 20) + дельты между ними; старше — gzip/архив.

### 2.4 Restore (безопасный)
- `POST /projects/{id}/revisions/{n}/restore?dry_run=true` (owner): применяет контент
  (project meta, brief, config, folders, presentations, slides+payloads, tokens).
- **Исключено:** `project_members`, владение, API-ключи, рендеры — их откат не выполняется
  (иначе воскрешение прав/персон). Это отдельные административные действия.
- Батчинг по презентациям, чтобы не держать гигантскую транзакцию; каждая партия атомарна,
  общий прогресс — в audit/outbox. Восстановление создаёт новую ревизию `source=restore`.

### 2.5 Concurrency (optimistic locking)
- `projects.version`, `presentations.version` (int, +1 на контентную мутацию).
- Клиент/агент шлёт `If-Match: <version>` (или `expected_version`). Несовпадение → **409
  `version_conflict`** с текущей версией. ИИ-джобы стартуют с базовой версией и получают 409,
  если человек успел изменить. Это закрывает «человек и бот одновременно».

---

## 3. ИИ-аккаунты и делегирование (с согласием)

### 3.1 Модель
- `users.is_bot`, `users.owner_user_id` (человек-владелец бота). Бот не логинится, только ключи.
- `api_keys`: `kind=service`, `created_by_user_id`, `project_id?`, `can_delegate`, `rate_limit`,
  `last_used_at`.
- `bot_delegations(bot_user_id, subject_user_id, project_id?, approved_at, approved_by, revoked_at)`.

### 3.2 Consent (закрывает имперсонацию)
- Делегирование **активируется только после одобрения subject** (`approved_by == subject_user_id`).
  До одобрения `X-On-Behalf-Of` → **403 `delegation_not_approved`** (fail-closed).
- Subject видит запрос в «Аккаунт → Делегирования» (approve/revoke) + уведомление.
- Каждое использование — в аудите (`on_behalf_of_user_id`).

### 3.3 Серверный AI-run (неподделываемый провенанс)
- `POST /ai/runs {project_id, agent, model, base_version}` → `{run_id}` (создаёт запись
  `ai_runs(id, bot_user_id, project_id, agent, model, base_version, created_at, status)`).
- Мутации агента несут `X-AI-Run-Id`; сервер проверяет: run существует, принадлежит этому боту
  и проекту, `status=running`, `base_version` совпадает (иначе 409). **Клиентский заголовок без
  валидации не принимается.**
- Аудит/revisions ссылаются на `ai_run_id`.

### 3.4 Cap прав бота (закрывает эскалацию)
- Effective rights = `min(member_role, bot_policy)`, где `bot_policy` по умолчанию
  **не включает** `style` (токены/палитра), `team` (участники), `transfer` (владение),
  `delete_project`. Эти действия боту запрещены, даже если subject — владелец, кроме явного гранта.
- Бот **не может** стать владельцем (transfer на бота запрещён).
- `admin`-scope ключа **не** даёт доступ к чужим проектам.

### 3.5 Обязательные проверки
- `X-On-Behalf-Of` принимается **только** для `kind=service` (cookie игнорит).
- `api_keys.project_id`: цель обязана входить в scope; при M2M-папках — проверка по любому
  проекту, дающему доступ (по резолверу), иначе deny.
- Rate-limit по ключу — **в БД** (таблица/Redis), не in-memory.
- Идемпотентность: `Idempotency-Key` на мутации агента; повтор возвращает прежний результат.

---

## 4. Схема БД (аддитивно)

```sql
-- audit + outbox
CREATE TABLE IF NOT EXISTS audit_log (... ) PARTITION BY RANGE (created_at);
CREATE TABLE IF NOT EXISTS audit_outbox (id BIGSERIAL PK, payload JSONB, created_at, delivered_at);

-- версии
CREATE TABLE IF NOT EXISTS project_revisions (... UNIQUE(project_id,n));
CREATE TABLE IF NOT EXISTS content_blobs (hash TEXT PRIMARY KEY, data JSONB, size_bytes INT, created_at);
ALTER TABLE projects       ADD COLUMN IF NOT EXISTS version INT DEFAULT 0;
ALTER TABLE presentations  ADD COLUMN IF NOT EXISTS version INT DEFAULT 0;

-- ИИ
ALTER TABLE users    ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT false;
ALTER TABLE users    ADD COLUMN IF NOT EXISTS owner_user_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS kind TEXT DEFAULT 'personal';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS created_by_user_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS project_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS can_delegate BOOLEAN DEFAULT false;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rate_limit INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS bot_delegations (...);
CREATE TABLE IF NOT EXISTS ai_runs (...);
```

---

## 5. Резолвер контекста (dependency, не middleware)

```
def resolve_access(...):        # вешается на роутеры рядом с enforce_write
    user, key = resolve_current_user_and_key(db, request)
    actor_type = "service" if key?.kind=="service" else ("user" if user else "system")
    subject = user
    if actor_type=="service" and request.headers.get("X-On-Behalf-Of"):
        if not key.can_delegate: deny("delegation_not_allowed")
        subj = find_user(header)
        deleg = find_delegation(key.owner_bot_id, subj.id, target_project)
        if not deleg or not deleg.approved_at: deny("delegation_not_approved")
        subject = subj
    # target/role считаются здесь: path_params доступны (это dependency, а не middleware)
    role = effective_role(db, target, subject) # с учётом bot_policy cap
    ctx = {...}; request.state.ctx = ctx; session.info["audit"] = ctx
    if rank(role) < need: deny(...)   # deny пишется отдельной сессией
```

---

## 6. API

```
# аудит
GET  /projects/{id}/audit?actor&action&from&to&limit   # owner
GET  /audit/me
# версии
GET  /projects/{id}/revisions?limit
GET  /projects/{id}/revisions/{n}                      # diff
POST /projects/{id}/revisions/{n}/restore {dry_run}    # owner
POST /projects/{id}/checkpoint {label}                 # owner
# ии-аккаунты
POST /api-keys/ {kind:"service", can_delegate, project_id, rate_limit}
POST /delegations {bot_user_id, subject_user_id, project_id}      # subject approves
POST /delegations/{id}/approve | /revoke
POST /ai/runs {project_id, agent, model, base_version}
```

---

## 7. Изменения в существующем коде

- `database.py`/`get_db`: `session.info["audit"]=[]` + `@event.listens_for(Session,"before_commit")`.
- Новый `audit.py`: буфер, redaction, запись в `audit_log`+`audit_outbox`.
- `permissions.py`: `resolve_access` (dependency) вместо логики в `enforce_write`; cap бота.
- `auth.py`: резолв key+user раздельно; `X-On-Behalf-Of` только service.
- `presentations.py`: `_log_revision` → дельта + author + `ai_run_id`; убрать snapshot.
- Новые роутеры: `revisions.py` (project), `audit.py`, `ai_runs.py`, `delegations.py`.
- Frontend: панель истории (diff/restore/checkpoint), «Боты и делегирования», индикатор
  «действует от имени».

---

## 8. Тестирование (обязательно до прода)

- **Unit:** резолвер ролей/делегирования, redaction (PII+секреты), diff/дедуп, bot-cap.
- **Integration (SQLite, как `test_permissions_db`):**
  - аудит **атомарен**: rollback мутации → нет строки аудита; commit → есть ровно одна;
  - deny (401/403/CSRF/scope/делегирование) логируется;
  - restore не воскрешает members/токены; создаёт новую ревизию;
  - версии: параллельные правки → 409;
  - delegation: до approve → 403, после → allow; revoke → 403.
- **Migration/backfill:** `presentation_revisions` без снапшотов, автор неизвестен (`null`);
  создание партиций; идемпотентность миграций.
- **Perf:** бюджет latency аудита (P95 не +X мс), нагрузочный тест 100 мутаций/с.
- **Security:** попытка подделать `ai_run_id`, `X-On-Behalf-Of` cookie-сессией, cross-project key.

---

## 9. SLO и бюджет объёма

- Замер: `N` мутаций/сутки сейчас (из логов nginx/БД) → оценка строк/мес и ГБ.
- Цели: аудит p95 overhead ≤ 15 мс; потеря аудита = 0 для allow/deny (транзакционно).
- Ретеншен: аудит — горячий 90 дней, тёплый 1 год, холодный 5 лет (архив).
- Ревизии: K checkpoints (20) + дельты; максимум на проект лимит; старые — gzip/архив.
- Партиции по месяцам + job автосоздания.

## 10. Раскатка, флаги, миграции

- Флаги: `AUDIT_ENABLED`, `AUDIT_LOG_READS`, `PROJECT_REVISIONS_ENABLED`,
  `BOT_DELEGATION_ENABLED`, `AI_RUNS_REQUIRED`. Kill-switch на каждый.
- Порядок: shadow (только запись аудита, enforcement выключен) → включить enforcement →
  ревизии → боты/делегирование → WORM/immutability.
- Миграции аддитивны, обратимы (drop колонок/таблиц), backfill идёт фоново с прогрессом.
- Все подсистемы за флагом; выключение не ломает существующий API.

## 11. Фазы

1. **Ф1 — Аудит (транзакционный) — DONE.** Таблицы `audit_log`/`audit_outbox`; хук
   `before_commit` (`backend/audit.py`) пишет строку в транзакции мутации; `enforce_write`
   строит контекст (actor/effective/target/action) и логирует allow (200) и deny
   (401/403/csrf/scope); redaction секретов и PII; чтение `GET /projects/{id}/audit` (owner),
   `GET /audit/me`. Тесты `backend/tests/test_audit_db.py` (8) — атомарность (commit→есть,
   rollback→нет), маскирование, derive_action. Всего в сьюте 52 теста.
   Осталось по Ф1 (мелочи): партиции по месяцам и immutability — перенесены в Ф4.
2. **Ф2 — Версии — DONE (бэкенд).** `project_revisions` (полные снапшоты контента),
   `content_hash`-дедуп, `build_snapshot`/`diff_snapshot`/`restore_snapshot` (`backend/revisions.py`),
   API `GET /projects/{id}/revisions[/{n}]`, `POST /checkpoint`, `POST /revisions/{n}/restore?dry_run`;
   авто-точка перед `change-set` ИИ; restore НЕ трогает участников/ключи; optimistic locking
   (`presentations.version` + `expected_version` → 409; версия растёт на update/слайды).
   Тесты `test_revisions_db` (4). Полный сьют **56**.
   **UI истории — DONE:** `ProjectHistory.vue` в настройках проекта (список ревизий, diff, «Откатить», «Сохранить точку»).
   Осталось: `content_blobs` (object-level dedup — снапшоты пока целостные, но с дедупом),
   версии проектных токенов/config как отдельные дельты.
3. **Ф3 — ИИ-аккаунты — DONE (бэкенд).** `users.is_bot/owner_user_id`; `api_keys.kind=service`
   (+ `can_delegate/project_id/rate_limit`), создание бота при выдаче service-ключа и editor-участие
   в проекте; `bot_delegations` с **consent** (approve subject); `X-On-Behalf-Of` → effective=subject,
   права проверяются у subject; **cap бота** (style/tokens/palette/team/transfer/admin/api-keys/
   создание проектов запрещены даже от имени админа); `ai_runs` (`POST /ai/runs`, валидация
   `X-AI-Run-Id` run↔bot↔project↔status, флаг `AI_RUNS_REQUIRED`); rate-limit на ключ; scope ключа
   на проект. API: `/delegations` (request/approve/revoke/me), `/ai/runs`. Тесты `test_permissions_db`
   (+2: cap при superadmin-subject, бот не управляет ключами). Полный сьют **58**.
   **UI — DONE:** в `/account` создание бота (service-ключ) и раздел «Боты и делегирования»
   (запрос по email, одобрение/отзыв). `ApiKeyOut` отдаёт `kind/project_id/can_delegate`.
   Осталось: rate-limit в Redis, идемпотентность `Idempotency-Key`.
4. **Ф4 — Enterprise+ (частично DONE).**
   - **Immutability — DONE.** Postgres-триггер `audit_log_no_change` (`BEFORE UPDATE OR DELETE`)
     отклоняет изменение/удаление `audit_log` (проверено: UPDATE/DELETE → «append-only»).
   - **Внешний sink (SIEM/webhook) — DONE.** Durable-экспортёр из `audit_outbox`
     (`AUDIT_WEBHOOK_URL`; выключен без env), ретеншен доставленного (7 дней). Аудит в `audit_log`
     не чистится.
   - **Аудит чтений — DONE.** Флаг `AUDIT_LOG_READS`: чувствительные GET (`/presentations`,
     `/projects`, `/admin`, `/audit`, `/api-keys`) пишутся отдельной сессией (`read.*`).
   - **`Idempotency-Key` — DONE.** Таблица `idempotency_keys` + зависимость `idempotency_guard`
     на `/ai/runs`, `change-set`, `/renders/realtime`: повтор с тем же ключом → 409.
   - **Исправления по ревью (DONE):** права `ai_runs` у effective-субъекта (on-behalf работает);
     scope API-ключа для всех ключей и для body-эндпоинтов; `enforce_write` подключён к
     `ai_runs`/`delegations`; валидация `X-AI-Run-Id` для всех акторов; restore восстанавливает
     presentation-токены и удаляет лишние папки, бампает `presentation.version`; change-set
     бампает версию; `UNIQUE(project_id,n)` на ревизиях; аудит без дублей при повторных commit;
     outbox не копится без webhook.
   - **Второй раунд ревью (DONE):** делегирование с project-scope снова проверяется; restore
     снимает `scope_folder_id` и slide-scope токены (FK-безопасность); `create_revision` с
     retry и пересчётом `n`; `diff` не считает презентацию изменённой из-за слайдов;
     ретеншен `idempotency_keys`; dev-байпас в аудит-роутере.
   - **Отложено (инфраструктура/оптимизация, осознанно):** партиции `audit_log` по месяцам,
     алерты на аномалии, rate-limit в Redis (сейчас in-memory), `content_blobs`
     (object-level dedup ревизий — сейчас целостные снапшоты + дедуп по хэшу).

## 12. Риски (обновлено)

| Риск | Митигация |
|---|---|
| Overhead транзакционного аудита | один INSERT в той же транзакции, партиции, outbox для sink |
| Долгий restore | батчинг по презентациям, dry_run, прогресс |
| Раздувание базы | content-addressed dedup, checkpoints+дельты, ретеншен |
| Имперсонация | consent-модель (approve subject), аудит, уведомления |
| Эскалация бота | bot-cap (нет style/team/transfer), transfer на бота запрещён |
| Подделка провенанса | серверные `ai_runs`, валидация run↔bot↔project↔version |
| Конкурентные правки | optimistic locking → 409 |
| «Аудит best-effort» | для allow/deny — транзакционно; sink — durable outbox |
