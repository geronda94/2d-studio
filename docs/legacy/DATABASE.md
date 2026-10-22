# DATABASE.md — Структура БД проекта

Справочник по таблицам PostgreSQL: что где лежит, как связано, как управлять.
Бэкенд: FastAPI + SQLAlchemy (`backend/models.py`). Все таблицы создаются через
`Base.metadata.create_all` при старте backend; derived-колонки — скриптами в `scripts/`.

> Прямой доступ к БД: `docker compose exec db psql -U presentation_user -d presentation_db`

---

## 1. Карта связей (ER)

```
projects ─1:N─ folders ─N:N─ presentations ─1:N─ slides ─1:1─ slide_data
                                        │              └─1:N─ director_events
                                        ├─1:N─ media_files
                                        └─1:N─ render_jobs

components ─N:1─ component_types
components ─N:N─ categories          (через component_category)

design_tokens   (scoped: project / presentation / slide)   ← тема
style_variants  (standalone)                               ← варианты отрисовки
```

`folder_presentation` — M2M между `folders` и `presentations` (папка может содержать несколько презентаций, презентация — в нескольких папках).

---

## 2. Контент-модель (дерево презентации)

### `projects` — проект
| Колонка | Тип | Назначение |
|---|---|---|
| `id` | int PK | |
| `slug` | str unique | идентификатор (`it2b`, `history`) |
| `title` | str | название |
| `description` | str? | описание |
| `created_at`, `is_archived` | | |

Пример: `1 = IT2B`, `2 = history`.

### `folders` — папка внутри проекта
| Колонка | Назначение |
|---|---|
| `id`, `slug`, `title`, `desc` | |
| `project_id` → projects.id | к какому проекту относится |
| `theme` | тема папки (визуальная метка; НЕ темизирует слайды) |
| `icon`, `is_archived` | |

Папка **группирует презентации** и задаёт проектную привязку. Связь с презентациями — M2M (`folder_presentation`).

### `presentations` — презентация
| Колонка | Назначение |
|---|---|
| `id`, `title` | |
| `audio_src`, `audio_timeline` (JSON) | озвучка + таймлайн клипов |
| **`variant`** | **дефолтный вариант отрисовки** (если слайд не задал свой). Напр. `classic` |
| `created_at`, `is_archived` | |

Презентация = таймлайн слайдов. Привязана к папкам через `folder_presentation`.

### `slides` — слайд
| Колонка | Назначение |
|---|---|
| `id` (int PK) | внутренний |
| `slide_id` (str, unique) | **строковый ID слайда** (уникален глобально), напр. `hist_ArchitectureDiagram_2` |
| `presentation_id` → presentations.id | |
| `component` (str) | **slug компонента** из `components` (напр. `ArchitectureDiagram`) |
| `start_time` (float) | глобальное время старта, мс |
| `order_index` (int) | порядок в презентации |
| `title`, `subtitle`, `layout` | шапка слайда / раскладка (`col`/`row`) |

### `slide_data` — данные слайда (payload)
| Колонка | Назначение |
|---|---|
| `id`, `slide_id` → slides.id | 1:1 со слайдом |
| `payload` (JSON) | данные компонента (то, что уходит в пропсы). Всё про payload — в `AGENTS.md` |

### `director_events` — события таймлайна слайда
| Колонка | Назначение |
|---|---|
| `id`, `slide_id` → slides.id | |
| `time` (float) | абсолютное время события, мс |
| `action`, `event_type` | тип события (напр. переключение слайда) |
| `payload` (JSON) | параметры события |

### `media_files` — медиа презентации
| Колонка | Назначение |
|---|---|
| `id`, `presentation_id` → presentations.id | |
| `filename`, `file_type` (`audio`/`video`/`image`), `file_path` | файл |
| `ai_text`, `ai_settings` (JSON) | сгенерированная озвучка / настройки |

### `render_jobs` — задачи видео-рендера
| Колонка | Назначение |
|---|---|
| `id`, `presentation_id` → presentations.id | |
| `status` (`pending`/`rendering`/`completed`/`failed`), `progress` | |
| `settings` (JSON), `file_url`, `error_log` | |

Рендер-пайплайн: `backend/scripts/render_video.py` (Playwright + ffmpeg).

---

## 3. Библиотека компонентов

### `components` — компонент (паспорт)
| Колонка | Назначение |
|---|---|
| `id`, `slug` (unique) | slug = имя `.vue` файла; используется в `slides.component` |
| `title`, `description` | название и краткое описание |
| `type_id` → component_types.id | тип (см. §4) |
| `default_payload` (JSON) | каркас (вставляется в новый слайд) |
| `payload_schema` (JSON) | типы полей (для редактора/валидатора/ИИ) |
| `example` (JSON) | эталонный заполненный пример |
| `manifest` (str) | «Подходит / Не использовать» |

Источник: `scripts/seed_components.py`. Derived-колонки (`payload_schema`, `example`, `manifest`) — генераторами (`generate_schemas.py`, `generate_examples.py`, `seed_manifests.py`).

### `component_types` — типы компонентов (3)
| slug | name | смысл |
|---|---|---|
| `interactive` | Интерактивный компонент | с панорамированием/зумом (`InteractiveArchitecture`) |
| `slide` | Полноэкранный компонент | занимает весь слайд (обёртка в `components/slides/`) |
| `ui` | UI Элемент | блок внутри слайда (карточки, таблицы, диаграммы) |

### `categories` — категории (4)
`backend` (Бэкенд & Архитектура), `sales` (Продажи & Воронки), `ui` (Интерфейсы), `stats` (Статистика & Графики).
Связь с компонентами — M2M через `component_category`. Используются для фильтра в выборе компонента.

---

## 4. «Типы» — важное: осей классификации несколько

Не путать — в проекте **разные оси**, и слово «тип» относится к разным вещам:

| Ось | Где | Значения | Отвечает за |
|---|---|---|---|
| **Тип компонента** | `component_types` | `interactive` / `slide` / `ui` | *что это за компонент* (интерактивный / полноэкранный / блок) |
| **Категория** | `categories` | `backend` / `sales` / `ui` / `stats` | *тематическая группа* для фильтра |
| **Вариант отрисовки** | `style_variants` | `tech` / `classic` / `industrial` / `educational` | *как рисуются* айтемы/линии (форма, тень, радиус, линии) |
| **Тема** | `design_tokens` | цвета/шрифты по уровням | *какими цветами/шрифтами* (палитра) |

Итого: **тип** = `component_types` (что за компонент), **вариант** = `style_variants` (как нарисовано), **тема** = `design_tokens` (чем покрашено).

Управление:
- Типы/категории — таблицы + API `/components/types`, `/components/categories`; сид в `seed_components.py`.
- Варианты — `/variants`, сид `seed_variants.py` (см. §5).
- Тема — `/projects/{id}/tokens`, сид `seed_tokens.py` (см. §5).

---

## 5. Тема и стили

### `design_tokens` — дизайн-токены (тема)
Единственный источник темы. Иерархия (чем ниже уровень, тем выше приоритет, мерж снизу вверх):

```
global (все NULL)  →  project_id  →  presentation_id  →  slide_id
```

| Колонка | Назначение |
|---|---|
| `id` | |
| `project_id` / `presentation_id` / `slide_id` | уровни скоупа (NULL = выше) |
| `token_key` | `bg-base`, `brand-blue`, `text-primary`, `font-heading`, `font_link`, … |
| `token_type` | `color` / `font_family` / `font_link` / `gradient` / `shadow` / `radius` |
| `value` | значение (hex, CSS-стек шрифта, URL Google Fonts, …) |
| `is_custom` | `false` = дефолт из сидов (удаление запрещено, правка только в настройках проекта); `true` = создан через библиотеку (можно править/удалять). В мерже отдаётся как `custom` |

- Применяются к слайду как CSS-переменные на `.slides-container` (`useTheme.js` → `applyTheme`). Для hex-цветов создаётся `--{key}-rgb`.
- `font_link` — URL Google Fonts, грузится динамически (`applyFontLink`), шрифты не хранятся в репозитории.
- **Закрыто (не токены):** паддинги и размеры шрифтов — только вариант + дизайн-система компонента.
- Уровни: global (80 токенов — дефолт IT2B, `seed_tokens.py:41 GLOBAL_TOKENS`), project `it2b` (1 оверрайд `bg-image` поверх global), `history` (80), `derevnya` (81). `global === IT2B` — `it2b` тянет цвета из `global` через мерж `global→project` (`useTheme.js:58`). Новые шахматные `item-accent-1..4`/`slide-bg-1..4`/`color-danger`/`color-info` — во всех 3 палитрах пер-темно.

> Старая таблица `project_colors` **удалена** — палитры перенесены в `design_tokens`. Чтение палитры во фронте (`fetchProjectColors`) идёт через `/projects/{id}/tokens`.
> Выбор цвета из библиотеки вставляет **ссылку `var(--{key})`**, а не резолвленное значение — правки токена на уровне проекта применяются автоматически. Валидатор `color` принимает `hex | ключ | gradient(...) | var(...)` (`validation.py:47-50`). Удаление: `DELETE /projects/{id}/tokens/{key}` — только `is_custom=true`, иначе 403.

### `style_variants` — варианты отрисовки
| Колонка | Назначение |
|---|---|
| `id`, `slug` (unique), `name`, `description` | |
| `config` (JSON) | единый конфиг: `item` / `item_primary` / `line` / `surface` + `components.<slug>` override |

- Задаётся на слайде полем payload `variant`, на презентации — `presentations.variant` (дефолт).
- Резолв: `payload.variant` → `presentations.variant` → `tech`.
- Применяется composable `useVariant` → CSS-переменные `--item-*`. Подробности — `AGENTS.md` §10.

---

## 6. API (по таблицам)

| Префикс | Таблицы | Основное |
|---|---|---|
| `/projects` | projects, folders, design_tokens | `GET /`, `GET /{slug}`, `POST /{id}/folders`, `GET/PUT /{id}/tokens` |
| `/presentations` | presentations, slides, slide_data, media_files, director_events | `GET /`, `GET /{id}`, `POST /`, `PUT /{id}`, `POST /{id}/slides`, `PUT/DELETE /slides/{slide_id}`, media-эндпоинты |
| `/components` | components, component_types, categories | `GET /` (паспорт+schema+example+manifest), `GET /types`, `GET /categories`, `POST /{slug}/validate[?lint=true]` (warnings: `no-hex`/`accent-budget`/`dense_timing`, не блокируют) |
| `/variants` | style_variants | `GET /`, `GET /{slug}`, `POST /` (`is_custom=True`; сид не перезаписывает кастомы без `--force`) |
| `/presets` | style_presets | `GET /`, `GET /{slug}`, `POST /` (400 на битые палитру/вариант), `DELETE /{slug}` (только custom, иначе 403) |
| `/renders` | render_jobs | запуск/статус рендера |
| `/ai` | — | AI-эндпоинты (озвучка и т.п.) |

---

## 7. Типичные задачи

| Задача | Как |
|---|---|
| Добавить компонент | `.vue` + запись в `componentsRegistry.js` + `seed_components.py` → прогнать генераторы (см. `AGENTS.md` §4.4) |
| Поменять тип/категорию компонента | таблицы `component_types`/`categories` (+ `component_category`), API `/components/types` \| `/categories` |
| Сменить тему проекта | `PUT /projects/{id}/tokens` или `seed_tokens.py` |
| Сменить дефолтный вариант презентации | `PUT /presentations/{id}` с полем `variant` |
| Назначить вектор/лок | `PUT /presentations/{id}/style` (`{style_preset, style_lock}`; лок без пресета → 400; выход за вектор на save → 422) |
| Добавить вариант отрисовки | запись в `style_variants` (`seed_variants.py`) |
| Перегенерировать схему/пример/манифест | `seed_components.py` → `generate_schemas.py` → `generate_examples.py` → `seed_manifests.py` |
| Проверить вкус слайда | `POST /components/{slug}/validate?lint=true`; на save слайда линт считается всегда (`warnings` в ответе, `low-contrast` только там) |

---

## 8. Нюансы

- **`folders.theme`** — визуальная метка папки, слайды не темизирует (тема — только `design_tokens`).
