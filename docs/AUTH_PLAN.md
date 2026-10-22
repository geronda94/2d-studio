# AUTH_PLAN.md — Аутентификация, пользователи, владение и права

Целевая модель: у проекта есть **владелец** (`projects.owner_id`) и **участники**
(смежная таблица `project_members`, 1 запись = 1 связка проект+пользователь).
Публичный просмотр по ссылке (`/p/:slug`) остаётся без логина. Правки — только у
владельца и назначенных им редакторов.

Решения (согласованы):
1. Транспорт сессии — **httpOnly cookie + CSRF** (безопаснее Bearer в localStorage).
2. Регистрация — **открытая** (+ rate-limit на login/register).
3. **Стиль/токены/палитра и управление командой — только владелец.** `editor` правит
   контент (слайды, данные, медиа, AI, рендер), но не тему.

Инварианты проекта (AI_PLATFORM §0): не ломать существующие контракты; только
`ADD COLUMN/TABLE IF NOT EXISTS`; фиче-флаги (`AUTH_MODE`) по умолчанию выключены;
рендер не трогать.

---

## 1. Модель данных

### `users` (новая)
| Колонка | Тип | Назначение |
|---|---|---|
| `id` | int PK | |
| `email` | str unique (lower) | логин |
| `password_hash` | str | scrypt (stdlib, без новых зависимостей) |
| `display_name` | str? | имя |
| `is_active` | bool | блокировка |
| `is_superadmin` | bool | платформенный админ |
| `created_at`, `last_login_at` | datetime | |

### `user_sessions` (новая)
`id, user_id FK→users.id, token_hash (sha256), csrf_token, created_at, expires_at,
revoked_at?, user_agent?, ip?`. Плейнтекст токена — только в cookie, в БД хеш.

### `project_members` (новая) — смежная таблица
`id, project_id FK→projects.id, user_id FK→users.id, role ('editor'|'viewer'),
invited_by FK→users.id?, created_at, scope_folder_id FK→folders.id?`.
`UNIQUE(project_id, user_id)`. Владелец **не дублируется** — он в `projects.owner_id`.
`scope_folder_id` — задел на будущее ограничение прав конкретными папками (сейчас NULL = весь проект).

### `projects` (есть)
`owner_id` (int, nullable, index) — **источник истины по владельцу**. Системные/шаблоны = NULL.
Позже: FK на `users.id` (nullable, чтобы не ломать системные).

### `presentations` (добавить позже, Ф4)
`visibility` (`public` по умолчанию | `private`). Сейчас публичный просмотр по ссылке.

---

## 2. Роли и матрица прав

| Действие | Гость | viewer | editor | owner | superadmin |
|---|---|---|---|---|---|
| Просмотр презентации по ссылке | ✅ | ✅ | ✅ | ✅ | ✅ |
| Список «мои проекты» | — | ✅ | ✅ | ✅ | ✅ |
| Слайды/данные/медиа (write) | — | — | ✅ | ✅ | ✅ |
| AI-генерация / рендер | — | — | ✅ | ✅ | ✅ |
| Токены/палитра/стиль | — | — | — | ✅ | ✅ |
| Команда, передача владения, удаление проекта | — | — | — | ✅ | ✅ |
| Компоненты/варианты/пресеты (write) | — | — | — | — | ✅ |

`viewer` — «помощник на просмотр»: видит проект, не правит. `editor` — правит контент.

---

## 3. Аутентификация

- **Пароли:** `hashlib.scrypt` (stdlib), формат `scrypt$n$r$p$salt$hash`, сравнение `hmac.compare_digest`.
- **Сессия:** `POST /auth/login|register` → httpOnly cookie `sid` (`SameSite=Lax`, `Secure` если `COOKIE_SECURE=true`) + читаемая cookie `csrf`.
- **CSRF:** на мутации (POST/PUT/PATCH/DELETE) с cookie-сессией обязателен заголовок `X-CSRF-Token`, равный `csrf` из cookie (double-submit).
- **Резолвер:** расширить до `_current_user` — cookie-сессия **или** `Authorization: Bearer pk_...` (API-ключи для агентов/скриптов). `AUTH_MODE=on` — обязательная аутентификация; `off` — обратная совместимость (как сейчас).
- **Rate-limit:** login/register — N попыток/мин на IP+email (in-memory; позже Redis).
- **CORS:** при cookie — только явный origin фронта (env `FRONTEND_ORIGIN`), не `*`.

### Endpoints (Ф1)
`POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.

---

## 4. Backend: централизация прав (Ф2+)

Модуль `backend/auth.py` (Ф1: пароли/сессии/`_current_user`; Ф2+: зависимости ролей):
- `require_user` — валидная сессия/ключ;
- `project_role(project_id, min_role)` — owner из `projects.owner_id` ∪ `project_members` (+ `scope_folder_id` в Ф4);
- `presentation_role(pres_id, min_role)` — резолв презентация → `folder_presentation` → `projects` → роль;
- `require_style_owner(...)` — токены/палитра только владелец.

Маппинг: read презентаций (`visibility=public`) — публично; write — `editor`+;
стиль/токены/палитра/команда — `owner`. Применить ко всем роутерам:
`presentations.py`, `ai.py`, `renders.py`, `components.py`, `variants.py`,
`presets.py`, `api_keys.py` (сейчас create/list/revoke без auth — закрыть).

---

## 5. UI

- `/login`, `/register` — вью; `router` guard (публичны `/p/:slug`, `/login`, `/register`).
- `composables/useAuth.js` — `currentUser`, `login/register/logout/ensureLoaded`; глобальный `auth:unauthorized` → редирект на `/login`.
- `services/api.js` — `apiFetch` с `credentials:'include'` + `X-CSRF-Token`.
- `AuthMenu` в `AppShell.vue` — аватар, «Мои проекты», «Выйти».
- Вкладка **«Команда»** в `ProjectSettings.vue` (Ф2): владелец, участники (email, роль, scope), приглашение/смена роли/удаление/передача.
- Режим viewer: прятать Save/Delete/редактор/рендер/AI/«добавить слайд» при отсутствии `editor` (бэкенд всё равно отклоняет).

---

## 6. Фазы

1. **Ф1 — Идентичность.** `users`/`user_sessions`, `auth.py`, `/auth/*`, `useAuth`, `/login`, `/register`, AuthMenu. `AUTH_MODE=off` — ничего не ломается.
2. **Ф2 — Владение и участники.** `project_members`, вкладка «Команда», приглашения, enforce в `projects.py` + `presentations.py` (write), viewer-режим UI.
3. **Ф3 — Полный enforcement.** `ai.py`, `renders.py`, `components.py`, `variants.py`, `presets.py`, `api_keys.py`; стиль/токены → owner.
4. **Ф4 — Папки и приватность.** `project_members.scope_folder_id`, folder-level enforcement, `presentations.visibility`.

---

## 8. Статус реализации

- **Ф1 — DONE.** `users`/`user_sessions`, `backend/auth.py` (scrypt, cookie+CSRF), `/auth/register|login|logout|me`, `useAuth`, `/login`, `/register`, AuthMenu.
- **Ф2 — DONE.** `project_members` + `permissions.py::enforce_write` на всех роутерах: аноним → 401, каталог → только супер-админ, `/projects` → владелец, `/presentations` → editor (стиль/токены/палитра → owner), `/ai`+`/renders` → editor; loopback render-воркера пропускается. Team-endpoints + секция «Команда» в `ProjectSettings`, режим просмотра (`GET /presentations/{id}/access`). Админ — bootstrap из `ADMIN_EMAIL`/`ADMIN_PASSWORD` (не «первый зарегистрированный»).
- **Ф3 — DONE.** Строгий CSRF (double-submit) на мутациях, смена пароля `POST /auth/password` (+`/account`), scoping `GET /presentations/`.
- **Ф4a — DONE.** `presentations.visibility` (public/private, только владелец; toggle в настройках презентации), приватные скрыты из списка и отдают 404 анониму; закрыта утечка `GET /projects/{id}/media`; `DELETE/PATCH /renders/{job_id}` привязаны к презентации (редактор).
- **Ф4b — DONE.** `project_members.scope_folder_id`: участник с папкой получает роль только для презентаций этой папки; `presentation_role` учитывает папки, membership API принимает `scope_folder_id`, `GET /projects/{id}/folders`, в UI — выбор папки у участника и при добавлении.
- **Ф5 — DONE.** Админка пользователей `/admin/users` (супер-админ): список, блокировка, выдача/снятие админа, сброс пароля; защита от самоблокировки. UI API-ключей в `/account` (создать/список/отозвать, плейнтекст один раз). Гигиена: очистка истёкших сессий на старте, CSRF на `/auth/logout`, защита `/admin/*` (только админ).
- **Сервисные скрипты.** `scripts/_api_auth.py` (импортируется сайд-эффектом в 17 скриптов)
  прокидывает `X-Internal-Token` в `requests` — **только для локальных хостов** (не для
  внешних URL, чтобы не утекал токен) и переписывает `:8001 → :8000` при запуске внутри
  контейнера. Иначе `AUTH_MODE=on` ломал пайплайн (401).
- **Тесты.** `backend/tests/`: `test_brand_config` (22), `test_auth` (7), `test_permissions_db` (13,
  in-memory SQLite: роли, папочный scope, приватность, `enforce_write`, CSRF, scopes, internal-bypass).
  Запуск: `docker compose exec backend python -m unittest discover -s backend/tests -t . -p "test_*.py"`.
- **Backlog.** Голос проекта в пайплайне (скрипты шлют `voice` явно — LOCKED, нужно решение владельца);
  восстановление пароля / верификация email (нужен SMTP).

## 7. Безопасность (чеклист)

scrypt-пароли; хеши токенов/сессий в БД; TTL сессий + revoke; rate-limit login/register;
явный CORS origin; CSRF double-submit; `httpOnly`+`SameSite`+`Secure` в проде;
не логировать секреты; миграции только `ADD ... IF NOT EXISTS`.
