# План: AI+Human платформа создания презентаций

> 2026-09-18. Цель: человек смотрит проект и даёт ИИ команды; ИИ, следуя специфике проекта,
> строит пайплайны. Документ — ТОЛЬКО план. Ничего в рантайме не меняем.
> **Жёсткое требование: не сломать текущий YouTube-пайплайн генерации презентаций.**

## 0. Инварианты (что нельзя ломать)

Текущий рабочий процесс (opencode-агент + API) кормит YouTube-канал. Поэтому:

- **Никаких изменений существующих контрактов.** Все новые поля — nullable, все новые
  эндпоинты — новые пути. `GET /components/`, `/variants/`, `/presets/`, `/presentations/*`,
  `/presentations/slides/*`, `/projects/*/tokens` — поведение не меняется.
- **Никаких обязательных миграций.** Только `ADD COLUMN IF NOT EXISTS` (nullable) и новые таблицы.
- **Никаких изменений рендера.** `render_fullscreen_capture.py`, `renders.py`, `useDirector`,
  safe-zone — не трогаем вообще.
- **Фиче-флаги.** Новые возможности включаются флагом (`AUTH_MODE`, `AI_FEATURES`), по умолчанию
  выключены → старое поведение 1-в-1.
- **Агент только через API** (не в БД) — сохраняем границу.
- **Ревизии — фоновый лог**, не блокируют запись: если лог упал, запись всё равно проходит.

## 1. Что уже готово (фундамент верный)

| Слой | Артефакт | Для агента это |
|---|---|---|
| Каталог | `GET /components/` → `manifest`+`payload_schema`+`example` | tool-описания и few-shot |
| Валидация | `validate?strict&lint`, `{path,type,message}` | self-correction loop |
| Стилевой вектор | `style_presets` + `style_lock` (422) | агент не выходит за стиль |
| Тема | `design_tokens` скоупы global→project→presentation→slide | тема как данные |
| Идемпотентность | клиентский `slide_id` | безопасные ретраи |
| Владение | `owner_id`/`parent_id`/`is_template` | скоуп агента под пользователя |
| Рендер | realtime capture + jobs | отделён от авторинга |

Вывод: фундамент **правильный**, не хватает операционной модели вокруг него.

## 2. Чего не хватает (пробелы)

1. Identity: `X-Owner-Id` — заглушка; нужен API-ключ/токен агента.
2. Revision/undo: правки перезаписывают без отката.
3. Единый контекст: агенту нужно 5 вызовов, чтобы понять проект.
4. Атомарность: колода = N запросов, сбой → частичное состояние.
5. Runtime-промпт: `AGENTS.md` — для кодинг-агента, не для API-агента.
6. Tool-схемы: OpenAPI есть, function-calling схем из компонентов — нет.
7. Job-модель генерации: рендер — job, генерация колоды — синхронна.
8. Ревью/diff UI: человек не видит предложенные правки до применения.

## 3. Целевая архитектура (цикл агента)

```
человек → КОМАНДА (чат/кнопка)
   → [1] CONTEXT        GET /presentations/{id}/ai-context      (read-only)
   → [2] PLAN           LLM: brief + context + tools → набор ops
   → [3] VALIDATE       POST /presentations/{id}/change-set?dry_run=true
   → [4] REVIEW         UI: diff предложенных ops (человек принимает/правит)
   → [5] APPLY          POST .../change-set (атомарно) + revision
   → [6] RENDER         существующий pipeline (не трогаем)
```

Ключ: агент выдаёт **структурированные операции**, не свободный текст/HTML.
Каждая операция проходит ту же `validation.py`+`style_lint.py`, что и ручная запись.

## 4. API-добавления (все аддитивные)

### 4.1 Контекст (read-only, нулевой риск) — Ф1
```
GET /presentations/{id}/ai-context
→ {
    brief, tokens (merged), preset {variant,rules,lock},
    allowed_variants, components [ {slug,manifest,schema,example} ],
    coverage, slides [ {slide_id,component,start_time,title} ]
  }
```
Один вызов вместо пяти. Ничего не пишет.

### 4.2 Ревизии (аддитивная таблица) — Ф1
```
Таблица presentation_revisions(id, presentation_id, n, ops JSON, snapshot JSON, created_at)
GET  /presentations/{id}/revisions
POST /presentations/{id}/revisions/{n}/restore
```
Пишется **после** успешной записи, в try/except — не влияет на основной путь.

### 4.3 Change-set (атомарные ops) — Ф2
```
POST /presentations/{id}/change-set
{ "dry_run": true, "ops": [
   {"op":"add_slide","slide_id":"...","component":"...","payload":{...}},
   {"op":"update_slide","slide_id":"...","patch":{...}},
   {"op":"delete_slide","slide_id":"..."},
   {"op":"set_presentation_variant","variant":"classic"},
   {"op":"set_slide_variant","slide_id":"...","variant":"derevnya|null"},
   {"op":"set_tokens","scope":"presentation|project","tokens":{...}}
]}
→ dry_run: {valid, errors[], warnings[], diff}
→ apply:   одна транзакция; при любой ошибке — rollback (0 изменений)
```
Внутри переиспользует существующие `_validate_slide_payload`/`_lint_slide_warnings`.

### 4.4 Brief проекта (данные) — Ф3
```
GET/PUT /projects/{id}/brief
{ "about":"", "audience":"", "tone":"", "must":[], "forbidden":[], "voice":"charon" }
```
Колонка `projects.brief JSON NULL`. Читается агентом как «знание проекта».

### 4.5 Tool-схемы — Ф1
```
GET /ai/tools
→ JSON-schema function-definitions, сгенерированные из GET /components/ + ops DSL
```
Единый источник правды: меняется компонент → меняются инструменты.

### 4.6 Identity — Ф4
```
Таблица api_keys(key_hash, owner_id, scopes, created_at)
Authorization: Bearer <key> → owner_id + scopes
AUTH_MODE=off (default) → текущее поведение (X-Owner-Id/None)
```

## Ф1 — DONE (2026-09-18)

Реализовано (всё аддитивно, ничего существующего не менял):
1. `GET /presentations/{id}/ai-context` — единый read-only контекст (presentation/project/brief/
   tokens/preset/variants[+config]/components[manifest,schema,example]/slides).
2. `GET /ai/tools` — ops DSL + каталог компонентов как function-definitions.
3. `presentation_revisions` (новая таблица, `create_all` на старте) + фоновый лог `_log_revision`
   в create/update/delete slide (try/except, не роняет запись); `GET /presentations/{id}/revisions`,
   `POST /presentations/{id}/revisions/{n}/restore`.

Попутно найдено и починено (влияет на агента):
- `AnimatedStatsSlide.default_payload` был **невалиден** (мой密度-нормалайзер давал 0,800,600) —
  исправлен на монотонный (0,800,1600).
- `InteractiveArchitecture.default_payload` имел разнобой/отрицательные `start_time` (валидатор
  ругался non_monotonic) — приведён к AGENTS §4.4: тайминг только у первой ноды.
- Схемы: `generate_schemas` брал поля только первого элемента массива → `badge/btn_icon/highlight/
  is_focused` выпадали (strict → unknown_field). Теперь union ключей по всем элементам.
- `validation.py`: цвет теперь принимает `rgb()/rgba()/color-mix()` (был отказ на `getColorAlpha`).
Итог: **все 30 default_payload валидны (strict=true)**, каталог полностью агент-совместим.

Проверка: ai-context/ai-tools/revisions/restore работают; регрессии `/components`,`/variants`,
`/presets`, `p4/p13`=30/30, фронт 200; временные презы зачищены (revisions строк 0).

## Ф2 — DONE (2026-09-18, backend + API-хук)

`POST /presentations/{id}/change-set` `{ops[], dry_run=true}`:
- ops: `add_slide`, `update_slide`, `set_slide_variant`, `delete_slide`, `reorder_slides`,
  `set_presentation_variant`, `set_tokens`, `apply_palette`.
- **dry_run по умолчанию** → `{valid, errors, warnings, diff}` без записи.
- **Атомарно**: все ops валидируются, применяются в одной транзакции, rollback при ошибке.
- Валидация переиспользует `validate_component_payload` + `style_lint`; preset-lock учитывается
  (правила пресета при `style_lock`).
- После apply — запись ревизии.
- Фронт-хук: `api.applyChangeSet`.

Приёмка: dry_run не пишет (0 слайдов); apply создаёт 2; ошибка в op → `valid:false`, 0 применений
(атомарность); multi (variant+patch+reorder) применён корректно; ревизии пишутся; пруфы зачищены.
Review-diff в UI — зависит от чат-агента (Ф4), бэкенд diff уже отдаёт.

## Ф3 — DONE (2026-09-18, генерация из сценария)

1. **Brief проекта**: `projects.brief JSON` (+миграция), `GET/PUT /projects/{id}/brief`
   (about/audience/tone/must[]/forbidden[]/voice). Прокидывается в `ai-context`.
2. **`POST /ai/presentations/{id}/generate-slides`**: из брифа + каталога (manifest/schema/example)
   LLM (Gemini, `GEMINI_TEXT_MODEL`, default gemini-2.5-flash) строит ops DSL.
   Возвращает **предложение**: `{ops, valid, errors, warnings, diff, applied}`.
   По умолчанию `apply:false` — ничего не пишет; при `apply:true` и `valid` — через change-set.
   Валидация переиспользует change-set (dry_run).

Приёмка: brief PUT/GET и в ai-context; генерация 2 слайдов → `valid:true`, `applied:false`,
`p4` остался 30 слайдов, ревизий 0 (ничего не записано). Регрессии 200.

### Ф3.2 — DONE (аудио→слайды + review-diff UI)

- `POST /ai/presentations/{id}/generate-from-audio` — по сегментам транскрипта
  (`{text,start_ms,end_ms}`, либо fallback на клипы озвучки презентации) строит слайды и
  **жёстко синхронизирует** `add_slide.start_time = segment.start_ms`. По умолчанию только
  предложение, `apply:false`.
- **Review-diff UI**: `AiAssistantModal.vue` (кнопка «✨ AI-ассистент» в настройках презентации):
  команда → «Предложить» (generate-slides, apply=false) → список операций + ошибки/warnings →
  «Применить» (change-set). `api.generateSlides`/`applyChangeSet`.
- Приёмка: 2 сегмента (0/5000мс) → 2 ops с ровно этими start_time, valid, не применено;
  p4 не тронут; фронт 200.

## Ф4 — DONE (2026-09-18, API-ключи/авторизация)

1. Таблица `api_keys` (key_hash sha256, owner_id, label, scopes, is_active).
2. `_current_owner` расширен: `AUTH_MODE=on` → обязателен `Authorization: Bearer <key>`,
   owner берётся из ключа (401 при отсутствии/неверном); `AUTH_MODE=off` (default) — прежнее
   поведение `X-Owner-Id`, пусто = system. **По умолчанию off → текущая работа не меняется.**
3. Роутер `/api-keys`: `POST /` (плейнтекст отдаётся ОДИН раз), `GET /` (маскированно),
   `DELETE /{id}` (revoke), `GET /whoami`.
4. Владение из ключа работает во всех owner-зависимых эндпоинтах автоматически.

Приёмка: off-режим — регрессии 200, p4/p13=30; ключ создан (owner 7); логика on проверена
напрямую: валидный ключ → owner 7, без заголовка → 401, битый → 401. Тестовый ключ удалён.
Скоупы (`scopes`) — **enforcement DONE**: при `AUTH_MODE=on` `_current_owner` проверяет скоуп
по методу (GET→read, мутации→write, admin проходит). Проверено: read-ключ GET→owner,
read-ключ POST→403, rw-ключ POST→owner. При `off` — поведение не меняется.

## 5. Фазы

| Фаза | Что | Риск для текущего |
|---|---|---|
| Ф0 | Этот план | ноль (doc) |
| Ф1 | ai-context, revisions (лог), /ai/tools | ноль (read-only + фоновый лог) |
| Ф2 | change-set (dry_run/apply) + review-diff в UI | ноль (новый путь рядом) |
| Ф3 | brief + генерация «сценарий→слайды», «аудио→слайды» | низкий (новые эндпоинты) |
| Ф4 | api_keys/auth + scopes + job-модель генерации | низкий (под флагом) |

## 6. Как не сломать YouTube-пайплайн (чеклист внедрения)

1. Каждая фаза — отдельная ветка/коммит; рабочий процесс продолжает жить на текущих эндпоинтах.
2. Ф1: `ai-context`/`revisions`/`tools` — **только чтение/лог**, включаются без флагов, не влияют.
3. Ф2: change-set — **новый** эндпоинт; старый `POST/PUT slides` не трогается.
4. Ф3: `brief` — nullable-колонка; без brief агент работает как сейчас.
5. Ф4: auth под `AUTH_MODE=off` по умолчанию → поведение идентично.
6. После каждой фазы: регресс — `p4/p13`=30/30, `p26/27/28`, один тестовый рендер (portrait+landscape).
7. Не менять `AGENTS.md`-контракты, пока новый runtime-промпт не будет сгенерирован из них
   (единый источник, иначе разъедутся).

## 7. Открытые вопросы (решить до реализации)

1. Триггер агента: чат в UI vs внешний сервис по API? (влияет на Ф2/Ф4).
2. Кто владелец «проектного пайплайна»: пользователь или системный шаблон? (связь с OWNERSHIP).
3. Бюджет генерации: лимит ops/токенов на презентацию.
4. Review-модель: построчный diff vs «превью слайда до/после».
5. Хранение ревизий: полный snapshot (проще restore) vs патчи (легче) — рекомендую snapshot JSON.

## 8. Вердикт

Реализуемо и перспективно; фундамент (data-as-contract, валидация, стилевой вектор) —
верный и обеспечивает главное: ИИ не ломает фирстиль. Работа — надстройка, а не переделка,
и спроектирована так, чтобы текущая генерация презентаций для канала продолжала работать
без изменений.
