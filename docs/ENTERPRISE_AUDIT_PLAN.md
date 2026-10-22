# ENTERPRISE_AUDIT_PLAN.md — Логирование, версии/откат, ИИ-аккаунты

Проект для трёх связанных подсистем: **аудит-лог**, **версии проектов с откатом**,
**технические ИИ-аккаунты с работой «от имени пользователя»** и обязательной проверкой прав.
Опирается на существующее: `presentation_revisions`, `ApiKey`, `permissions.enforce_write`,
`auth.resolve_current_user`.

---

## 0. Принципы

1. **Единый резолвер контекста.** Один раз на запрос вычисляем «кто», «от чьего имени»,
   «что за цель», «какая роль» — и используем это и для авторизации, и для аудита.
   Дублировать логику прав нельзя.
2. **Аудит — append-only, best-effort.** Запись лога никогда не ломает бизнес-операцию;
   сбой лога логируется отдельно.
3. **Бот не доверенный субъект.** Права проверяются у **эффективного пользователя**
   (человека), а не у бота.
4. **Версии — не бэкап БД, а откат контента.** Восстановление создаёт новую ревизию
   (неразрушающе), откатываем данные проекта, не системные таблицы.
5. **Всё аддитивно.** Только `ADD COLUMN/TABLE IF NOT EXISTS`, фиче-флаги, без ломки API.

---

## 1. Аудит-лог (кто что сделал)

### 1.1 Модель `audit_log` (append-only)

| Колонка | Тип | Смысл |
|---|---|---|
| `id` | bigint PK | |
| `created_at` | timestamptz | |
| `request_id` | str | корреляция (из middleware), связать с AI-run |
| `actor_type` | str | `user` / `service` (бот) / `system` |
| `actor_user_id` | int? | кто инициировал (для бота — сам бот-аккаунт) |
| `actor_key_id` | int? | API-ключ, которым пришли |
| `on_behalf_of_user_id` | int? | человек, от имени которого действовал бот |
| `effective_user_id` | int | у кого проверялись права (subject) |
| `project_id` | int? | цель |
| `presentation_id` | int? | цель |
| `slide_id` | str? | цель |
| `action` | str | `slide.create`, `config.update`, `style.update`, `bot.delegate`, … |
| `method` / `path` | str | HTTP-контекст |
| `status` | int | HTTP-код ответа |
| `decision` | str | `allow` / `deny` |
| `deny_reason` | str? | `no_role`, `csrf`, `scope`, … |
| `ip`, `user_agent` | str | |
| `ai_run_id` | str? | id прогона ИИ (X-AI-Run-Id) |
| `diff` | jsonb | before/after для ключевых сущностей (redacted) |
| `meta` | jsonb | доп. данные (напр. `{"revision_n": 12}`) |
| `prev_hash` / `hash` | str | цепочка хешей для tamper-evidence |

Индексы: `(project_id, created_at desc)`, `(created_at desc)`, `(actor_user_id)`, `(on_behalf_of_user_id)`, `(request_id)`.

### 1.2 Как снимать — **middleware + общий резолвер** (рекомендация)

Сравнение вариантов:

| Подход | Плюсы | Минусы |
|---|---|---|
| Декоратор на каждый эндпоинт | явно | boilerplate, легко забыть новый роут |
| FastAPI dependency на роутер | централизованно | не даёт статус/после-состояние, дубли со shлюзом |
| **HTTP middleware** | один раз на всё, видит request+response | нужен резолвер без `Depends` |

**Рекомендация:** `AuditMiddleware` (Starlette) + `permissions.resolve_request_context(request, db)`.
Порядок: (1) сгенерировать `request_id`; (2) разрешить контекст (пользователь/бот/on-behalf/цель);
(3) положить в `request.state.ctx`; (4) `call_next`; (5) записать `audit_log` (только мутации;
опционально — чувствительные чтения); (6) при `decision=deny` от `enforce_write` — тоже пишем.

`enforce_write` переиспользует `request.state.ctx` (без повторных запросов в БД).
Запись — через **очередь + воркер** (`asyncio.Queue` + фоновый таск; fallback — синхронный insert
в `try/except`), чтобы latency запроса не росла.

### 1.3 Что логировать

- Все мутации (`POST/PUT/PATCH/DELETE`) — обязательно, включая `deny` (401/403/CSRF).
- Создание/отзыв API-ключей, смена пароля, передача владения, изменение участников.
- ИИ-операции: `actor_type=service`, `on_behalf_of`, `ai_run_id`, `ops` diff.
- (Флаг) чтения приватных проектов и медиа-скачивания — для комплаенса.

### 1.4 Redaction и размер
- Вырезать `password`, `key`, `token`, `cookie`, `authorization`, `secret` (deep-walk по `meta/diff`).
- Лимит `diff` (напр. 32 КБ, длинные строки обрезать).
- В аудит **не** кладём полные payload-и, только ключи/суммы изменений + ссылку на ревизию.

### 1.5 API для чтения логов
- `GET /projects/{id}/audit?actor=&action=&from=&to=&limit=` — owner.
- `GET /audit/me` — свои действия.
- Экспорт `GET /projects/{id}/audit.csv` (SIEM/аудит), позже — стрим в syslog/webhook.

---

## 2. Версии проекта и откат

### 2.1 Что уже есть
`presentation_revisions` — снимки **слайдов презентации** + `ops`; restore есть.
Не хватает: уровня **проекта** (несколько презентаций, папки, токены, config, участники).

### 2.2 Модель `project_revisions`
| Колонка | Смысл |
|---|---|
| `id`, `project_id`, `n` (в рамках проекта) | |
| `created_at`, `author_user_id?`, `on_behalf_of_user_id?` | кто |
| `source` | `manual` / `autosave` / `ai` / `restore` / `import` |
| `label` | человекочитаемая метка («перед правками ИИ») |
| `content_hash` | sha256 канонизированного снапшота (дедуп) |
| `snapshot` | jsonb (нормализованный) |
| `size_bytes`, `is_checkpoint` | полнота/прунинг |

**Снимок проекта:** `project` (meta, brief, config, default_variant), `folders`,
`presentations` (поля), `slides` + `slide_data`, `design_tokens`
(project/presentation scope), `project_members`. Ассеты/медиа — по ссылкам (не дублируем бинарь).

### 2.3 Стратегия хранения
- **Полные снапшоты + дедуп по `content_hash`** (если не менялось — не пишем).
- **Коалесинг автосейва:** не более 1 `autosave`-ревизии в N сек на проект (напр. 30 c);
  ручные/ИИ-точки — всегда.
- **Прунинг:** держать последние K полных (напр. 50) + все `is_checkpoint`; старые — архивировать
  (gzip в той же строке или внешний сторедж).
- Хранить в JSONB; при росте — вынести в отдельную таблицу/партиции по `project_id`.

### 2.4 Откат
- `POST /projects/{id}/revisions/{n}/restore` (owner): применяет снапшот, **создаёт новую ревизию**
  `source=restore` (история не переписывается). Возвращает diff «что изменилось».
- `GET /projects/{id}/revisions?limit=` — список; `GET .../{n}` — детали/diff.
- **Diff-движок:** сравнение по сущностям (`slide_id`, `presentation_id`, `token_key`) → added/removed/changed.
- Восстановление — атомарно (одна транзакция, rollback при ошибке), как `change-set`.

### 2.5 Авто-точки (триггеры)
- Перед `change-set apply` (ИИ) — автоснапшот `source=ai` с `label` и `ai_run_id`.
- При `POST /projects/{id}/fork` — снапшот источника не нужен.
- Периодический autosave по факту мутаций (dirty-флаг + debounce).

### 2.6 UI
История проекта (панель): таймлайн ревизий, автор/источник (человек/ИИ, от чьего имени),
diff, кнопка «Откатить». Сейчас ревизии презентации без UI.

---

## 3. Технические ИИ-аккаунты и «от имени пользователя»

### 3.1 Модель
- `users.is_bot` (bool), `users.owner_user_id` (кто завёл бота), `is_active`.
  Бот-аккаунт: без пароля, не может логиниться, только API-ключи.
- `api_keys` расширить:
  | Поле | Смысл |
  |---|---|
  | `kind` | `personal` / `service` |
  | `created_by_user_id` | человек, создавший ключ |
  | `project_id?` | ключ ограничен проектом (scope) |
  | `can_delegate` | может действовать `X-On-Behalf-Of` |
  | `rate_limit` | лимит запросов/мин |
  | `last_used_at` | |
- `bot_delegations` (опц.): `bot_user_id`, `subject_user_id`, `project_id`, `can_delegate`
  — матрица «какому боту за кого можно». Для мульти-пользовательских ботов.

### 3.2 Поток «бот от имени человека»
1. Запрос с `Authorization: Bearer <bot-key>`.
2. Если есть `X-On-Behalf-Of: <email|id>`:
   - ключ обязан быть `kind=service` и `can_delegate=true`;
   - резолвим subject-пользователя; проверяем `bot_delegations` (если задана): разрешено ли
     этому боту за этого человека;
   - проверяем **права subject на цель** (project/presentation) по обычному резолверу ролей.
3. Если on-behalf нет: effective user = владелец ключа (бот как самостоятельный участник проекта).
4. `enforce_write` проверяет роль **effective user**; бот не может «повысить» права.
5. В аудит: `actor_type=service`, `actor_user_id=bot`, `on_behalf_of_user_id=subject`,
   `effective_user_id=subject`, `actor_key_id`.

### 3.3 Обязательные проверки (жёстко)
- Запрещено: бот без on-behalf, если ключ `kind=service` и политика требует делегирования.
- Роль проверяется у subject; `admin`-scope ключа **не** даёт прав на чужие проекты.
- `X-On-Behalf-Of` игнорируется для cookie-сессий (только для service-ключей).
- Ограничение по проекту (`api_keys.project_id`) — цель обязана совпасть.
- Rate-limit на ключ; аномалии (резкий рост) — в аудит/алерт.

### 3.4 Провенанс ИИ
- Заголовки `X-AI-Run-Id`, `X-AI-Agent` (имя агента), `X-AI-Model`.
- Аудит-строка + `project_revisions.source=ai` с `ai_run_id` → полная трассировка:
  «агент X, модель Y, от имени пользователя Z, ревизия N, ops …».

---

## 4. Изменения схемы (миграции, все IF NOT EXISTS)

```
users:            ADD is_bot boolean default false; owner_user_id int; last_login_at (есть)
api_keys:         ADD kind varchar default 'personal'; created_by_user_id int;
                  ADD project_id int; can_delegate boolean default false;
                  ADD rate_limit int; last_used_at timestamptz
audit_log:        CREATE TABLE (+ индексы)
project_revisions:CREATE TABLE (+ уникальность UNIQUE(project_id, n))
bot_delegations:  CREATE TABLE (opc.)
presentations:    (есть visibility, revisions на уровне presentation)
```

---

## 5. Фазы внедрения

1. **Ф1 — Аудит-фундамент.** Таблица `audit_log`, `resolve_request_context`, `AuditMiddleware`,
   переиспользование контекста в `enforce_write`, redaction, очередь-воркер. Логируем мутации
   и `deny`. API чтения для owner. Уже даёт enterprise-ценность без влияния на контент.
2. **Ф2 — Project revisions.** Снапшоты, diff, restore, авто-точки (change-set/fork), прунинг,
   UI истории.
3. **Ф3 — ИИ-аккаунты.** `is_bot`, service-ключи, `X-On-Behalf-Of`, `bot_delegations`,
   проверка прав subject, rate-limit, провенанс (`ai_run_id`).
4. **Ф4 — Enterprise-плюшки.** Хеш-цепочка (tamper-evidence), экспорт в SIEM/webhook,
   retention-политики, алерты на аномалии, раздельные права на чтение аудита.

---

## 6. Риски и решения

| Риск | Решение |
|---|---|
| Объём `audit_log`/ревизий растёт | партиции по времени/проекту, прунинг, gzip, дедуп по hash |
| Лог тормозит запросы | очередь + воркер, best-effort, лимиты размера |
| Утечка секретов в diff | deep-redaction, whitelist полей |
| Бот обходит права | effective-user проверка, запрет on-behalf для cookie, project-scope |
| Подмена истории | append-only + `prev_hash`; запрет UPDATE/DELETE на `audit_log` |
| Откат ломает связи | атомарная транзакция + новая ревизия, never in-place |
| Идемпотентность ИИ-операций | `ai_run_id` + уникальные ключи операций |

---

## 7. Что меняется в существующем коде

- `permissions.py`: новый `resolve_request_context` (используется и `enforce_write`, и аудитом).
- `main.py`: подключить `AuditMiddleware` (после CORS/кэша).
- `models.py`: `AuditLog`, `ProjectRevision`, правки `ApiKey`/`User`.
- `auth.py`: резолв бота; `X-On-Behalf-Of` только для service-ключей.
- `presentations.py`: `_log_revision` дополнить автором/`ai_run_id` (сейчас пишет без автора).
- `routers/`: чтение аудита/ревизий; restore проекта.
- Frontend: панель истории проекта (diff + «Откатить»), раздел «Боты/ключи» в аккаунте,
  индикатор «действует от имени …».

---

# Приложение A. DDL (эскиз, всё IF NOT EXISTS)

```sql
CREATE TABLE IF NOT EXISTS audit_log (
  id            BIGSERIAL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  request_id    TEXT,
  actor_type    TEXT NOT NULL,              -- user | service | system
  actor_user_id INT,
  actor_key_id  INT,
  on_behalf_of_user_id INT,
  effective_user_id    INT,
  project_id    INT,
  presentation_id INT,
  slide_id      TEXT,
  action        TEXT NOT NULL,
  method        TEXT, path TEXT, status INT,
  decision      TEXT NOT NULL DEFAULT 'allow',   -- allow | deny
  deny_reason   TEXT,
  ip TEXT, user_agent TEXT,
  ai_run_id     TEXT,
  diff          JSONB,
  meta          JSONB,
  prev_hash     TEXT,
  hash          TEXT,
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS project_revisions (
  id BIGSERIAL PRIMARY KEY,
  project_id INT NOT NULL,
  n INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  author_user_id INT,
  on_behalf_of_user_id INT,
  source TEXT NOT NULL DEFAULT 'manual',   -- manual|autosave|ai|restore|import
  label TEXT,
  content_hash TEXT,
  snapshot JSONB NOT NULL,
  size_bytes INT,
  is_checkpoint BOOLEAN DEFAULT false,
  UNIQUE (project_id, n)
);

ALTER TABLE users    ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT false;
ALTER TABLE users    ADD COLUMN IF NOT EXISTS owner_user_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS kind TEXT DEFAULT 'personal';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS created_by_user_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS project_id INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS can_delegate BOOLEAN DEFAULT false;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rate_limit INT;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ;
```

# Приложение B. Алгоритм resolve_request_context

```
ctx = request.state.ctx
user = resolve_current_user(db, request)              # cookie → session, иначе Bearer key
actor_type = "service" if key.kind == "service" else ("user" if user else "system")
subject = user
if key and key.kind == "service" and request.headers["X-On-Behalf-Of"]:
    if not key.can_delegate: deny(403, "delegation not allowed")
    subject = find_user(X-On-Behalf-Of); if not subject.active: deny(403)
    if bot_delegations exists and not allowed(key, subject, target): deny(403)
# target (project/presentation) — из path_params, доступных ВНУТРИ зависимости
role = project_role/presentation_role(db, target, subject)
decision = rank(role) >= need ? allow : deny
```

# Приложение C. Middleware (эскиз)

```
class AuditMiddleware:
    async def __call__(request, call_next):
        if not AUDIT_ENABLED or request.url.path in SKIP or method in SAFE: 
            return await call_next(request)          # быстрый путь
        rid = request.headers.get("X-Request-Id") or uuid4()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            enqueue(audit_from(request, response, request.state.ctx))   # очередь+воркер
```

# Приложение D. Эндпоинты

```
GET  /projects/{id}/audit?actor&action&from&to&limit        # owner
GET  /audit/me                                              # свои
GET  /projects/{id}/revisions?limit                         # owner/member
GET  /projects/{id}/revisions/{n}                           # diff
POST /projects/{id}/revisions/{n}/restore  {dry_run}        # owner
POST /projects/{id}/checkpoint {label}                      # owner
POST /api-keys/            {kind:"service", can_delegate, project_id, rate_limit}
POST /bots/{bot_id}/delegations {subject_user_id, project_id}
```
