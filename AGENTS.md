# AGENTS.md — Руководство для ИИ-агентов по созданию презентаций

Единый актуальный справочник по движку презентаций. Написан для ИИ-агентов, которые
генерируют данные презентаций. Здесь — только то, что правда в текущем коде.

**Главное правило:** не угадывай структуру данных. Спрашивай API. Библиотека компонентов
отдаёт всё: `payload_schema` (типы полей), `example` (живой пример), `manifest` (когда использовать).

> ⚠️ **ОБЯЗАТЕЛЬНО:** список компонентов, их поля и схемы могут меняться. Никогда не полагайся
> на запомненный/захардкоженный список — **каждый раз запрашивай свежие данные**:
> `GET /components/` (все компоненты: `slug`, `payload_schema`, `example`, `manifest`) и
> `GET /variants/` (варианты отрисовки). Каталог в §4.3 — лишь снимок-шпаргалка, сверяйся с API.
> Для каждого payload прогоняй `POST /components/{slug}/validate` до создания слайда.

---

## 1. Что это и как запущено

Конструктор презентаций. Стек:

| Слой | Технология | Порт |
|------|-----------|------|
| БД | PostgreSQL (db `presentation_db`) | `5435` |
| Backend | FastAPI (Python) | `8001` |
| Frontend | Vue 3 + Vite + Tailwind | `5174` |

- Запуск: `docker compose up` (compose-проект `presentation-saas`).
- Frontend доступен на `http://localhost:5174`, API напрямую на `http://localhost:8001`.
- Frontend проксирует `/api/*`, `/uploads/*`, `/media/*` на backend (`vite.config.js`).
- Примеры живых презентаций: `http://localhost:5174/p/10` (IT2B, тёмная), `http://localhost:5174/p/11` (историческая, светлая).

Код: `backend/` (FastAPI + SQLAlchemy), `core/` (Vue), `scripts/` (сиды и генераторы).

---

## 2. Модель данных (БД)

> Полный справочник по таблицам, связям и осям классификации — `docs/DATABASE.md`.
> Ниже — краткая выжимка для генерации презентаций.

Таблицы, важные для генерации презентаций:

| Таблица | Что хранит | Ключевые поля |
|---------|-----------|---------------|
| `projects` | проект (набор презентаций + тема) | `slug`, `title` |
| `folders` | папка (привязка проекта к презентациям) | `slug`, `title`, `project_id`, `theme` |
| `presentations` | презентация | `title`, `audio_timeline`, `variant` (дефолтный вариант отрисовки) |
| `slides` | слайд | `slide_id` (строка, уникальна), `component` (slug), `start_time` (мс, float), `order_index`, `title`, `subtitle`, `layout` |
| `slide_data` | payload слайда (JSON) | `payload` |
| `components` | библиотека компонентов | `slug`, `title`, `description`, `default_payload`, `payload_schema`, `example`, `manifest` |
| `component_types` | тип компонента | `slug`: `interactive` / `slide` / `ui` |
| `categories` | категория | `slug`: `backend` / `sales` / `ui` / `stats` |
| `design_tokens` | тема (токены) | `token_key`, `token_type`, `value`, `project_id`/`presentation_id`/`slide_id` |
| `style_variants` | варианты отрисовки (типы) | `slug`, `config` (JSON) |
| `media_files` | медиа | `filename`, `file_type`, `file_path` |
| `director_events` | события таймлайна слайда | `time`, `event_type`, `payload` |

Слайд = запись в `slides` + вложенный `data.payload` (JSON). `component` — это `slug`
компонента из `components`.

---

## 3. Как данные попадают в компонент

Поток данных (frontend):

```
MainPresentation.vue
  └─ SlidePresentation.vue        (управляет слайдами, таймлайном, хромом)
       └─ Slide.vue               (обёртка: заголовок, layout, provide('relativeTime'))
            └─ <component :is="componentsMap[slide.component]" v-bind="payload" />
```

- **Стилизация заголовков:** `MainPresentation.vue` отдает layout, а заголовки/подзаголовки рисуются внутри `Slide.vue`.
- **Глассморфизм и Неон:** Архитектура `style_variants` поддерживает размытие и сложные тени «из коробки» без изменения кода компонентов.
  - **Glassmorphism:** В `style_variants` задайте для `item.bg`: `{ "type": "blur", "value": "bg-surface", "opacity": 0.2, "blur": "16px" }` и легкую тень `0 8px 32px rgba(0,0,0,0.3)`. Компонент автоматически станет стеклянным (`backdropFilter: blur`).
  - **Neon:** Установите `item.bg` в `transparent`, `item.border.width` в `2`, `item.border.color` в акцентный цвет и добавьте неоновое свечение в `item.shadow`: `0 0 15px var(--color-primary)`.

Конкретика из `MainPresentation.vue`:

```vue
<component
  :is="componentsMap[slide.component]"
  :mobile="isMobile"
  :clicks="clicks"
  :slide-start-time="slide.start_time || slide.startTime || 0"
  v-bind="slide.data?.payload || slide.data || {}"
/>
```

Что это значит для компонента:

1. `componentsMap[slide.component]` — реестр `core/src/config/componentsRegistry.js`,
   где **ключ = slug компонента = имя `.vue` файла**.
2. `v-bind="payload"` — каждый ключ верхнего уровня `payload` становится **пропом** компонента.
   Т.е. поле `payload.bot_name` → проп `bot_name`; `payload.messages` → проп `messages`.
3. **Системные пропсы** добавляются движком независимо от payload:
   - `mobile` (boolean) — мобильный вид.
   - `clicks` (number) — число кликов по слайду.
   - `slideStartTime` (number) — глобальное `start_time` слайда (передаётся атрибутом `:slide-start-time`).
4. Внутри слайда доступно `inject('relativeTime')` — локальное время слайда (мс от его старта),
   через него делаются анимации (см. §11).

**Как объявляются пропсы:** в компоненте через `defineProps`. Пропсы соответствуют ключам
payload «как есть» (в коде принят snake_case, Vue принимает snake-ключи напрямую как пропсы).
Например, `ArchitectureDiagram` объявляет `nodes`, `show_data_flow`, `showDataFlow`, `variant`.

---

## 4. Библиотека компонентов

### 4.1 Как устроена

- Файлы компонентов лежат в `core/src/components/ui/` (элементы) и `core/src/components/slides/` (полноэкранные обёртки).
- Каждый компонент **зарегистрирован** в `core/src/config/componentsRegistry.js` (`componentsMap`).
  **Новый компонент = новый `.vue` + запись в реестре + запись в `scripts/seed_components.py`.**
  Исключение: внутренние building blocks (`RoiCalculator`, `Ecosystem`, `AdvancedVideoPlayer`,
  `ChatMockup`, `BeforeAfter` и т.п. из `ui/`) используются только внутри `*Slide`-обёрток
  и в реестр **не входят**. Контроль дрейфа: `python scripts/check_consistency.py`.
- «Паспорт» компонента (что видит ИИ) хранится в БД, таблица `components`. Источник заполнения —
  `scripts/seed_components.py`.

### 4.2 Контракт компонента (то, что возвращает `GET /components/`)

| Поле | Назначение |
|------|-----------|
| `slug` | идентификатор = имя `.vue` файла. Использовать в `slide.component`. |
| `title` | человекочитаемое название. |
| `description` | одна фраза, что делает. |
| `manifest` | «Подходит / Не использовать» — для выбора правильного компонента. |
| `default_payload` | каркас (вставляется в новый слайд). |
| `payload_schema` | **типы полей** (структура вложенности, enum, min/max_items, required). |
| `example` | **эталонный заполненный пример** (живые данные). |
| `type` / `categories` | тип (`interactive`/`slide`/`ui`) и категории. |

> Для заполнения данных ИИ должен опираться на `payload_schema` + `example` (а не выдумывать).

### 4.3 Каталог (32 компонента)

Полная структура вложенных полей каждого компонента — в `payload_schema`/`example` через
`GET /components/`. Ниже — быстрая шпаргалка (slug → назначение → ключи верхнего уровня payload).

| slug | Назначение | Ключи верхнего уровня |
|------|-----------|----------------------|
| `ArchitectureDiagram` | Блок-схема: ноды + связи + поток данных | `nodes`, `show_data_flow`, `variant` |
| `InteractiveArchitecture` | Интерактивная схема с зумом и подсветкой | `nodes` |
| `EcosystemSlide` | Центральный элемент + ноды-интеграции | `center`, `nodes` |
| `ChatMockupSlide` | Мокап переписки/чат-бота | `bot_name`, `bot_subtitle`, `bot_avatar`, `messages` |
| `TerminalMockup` | Мокап терминала | `commands` |
| `CodeExplain` | Разбор кода построчно | `language`, `blocks` |
| `CodeComparisonSlide` | Два окна кода (до/после) | `windows` |
| `ComparisonTable` | Таблица с галочками/крестиками | `headers`, `items` |
| `ModernTable` | Таблица с иконками/трендами/статусами | `columns`, `rows`, `focus` |
| `NetworkWaterfall` | Waterfall сетевых запросов | `total_ms`, `requests`, `legend` |
| `ProductCard` | Карточки товара/тарифа | `items` |
| `ReceiptCard` | Карточка чека | `title`, `subtitle`, `currency`, `total_text`, `footer_text`, `total_start_time`, `items` |
| `PremiumChecklist` | Чеклист с иконками | `items` |
| `ProcessFunnel` | Воронка этапов | `layout`, `steps` |
| `Roadmap` | Дорожная карта этапов | `items` |
| `InfographicCards` | Карточки с цифрами/трендами | `items` |
| `StatsBarChart` | Столбчатая диаграмма | `base_color`, `peak_color`, `data`, `title`, `subtitle` |
| `MetricScales` | Шкалы метрик (проценты) | `metrics`, `title`, `subtitle` |
| `ProgressScalesSlide` | Шкалы прогресса | `scales` |
| `AnimatedStatsSlide` | Крупные метрики с ростом | `stats` |
| `BentoGridGallery` | Bento-сетка плиток | `items` |
| `BrowserMockup` | Мокап браузера со скроллом | `items` |
| `BeforeAfterSlide` | До/после (два окна) | `windows` |
| `MediaSlide` | Медиа с зумом/панорамой (Ken Burns) | `media_url`, `caption`, `start_time`, `initial_scale`, `target_scale`, `zoom_duration`, `object_position`, `target_position` |
| `AdvancedVideoSlide` | Скринкаст с рамкой | `video_url`, `frame`, `domain`, `trim_start`, `trim_end`, `initial_scale`, `target_scale`, `object_position` |
| `CrmCardSlide` | Карточка клиента в CRM | `customer`, `fields`, `buttons` |
| `RoiCalculatorSlide` | ROI-калькулятор | `variables`, `result_base`, `result_label`, `result_suffix`, `result_description` |
| `TechStackSlide` | Сетка технологий | `technologies` |
| `OutroSlide` | Финальная заставка (лого, QR, контакт) | `logo`, `qr_code`, `handle`, `headline` |
| `PortraitLampSlide` | Портрет в арочном окладе с подвесной лампадкой | `image`, `name`, `caption`, `description`, `lamp`, `lamp_side`, `lamp_color`, `flame_color`, `image_position` |
| `TimelineSlide` | Линия времени: события по таймлайну, активное раскрывается | `events`, `show_images` |
| `EndMarkerSlide` | Служебный маркер конца (без данных) | — |

> `EndMarkerSlide` — технический маркер конца таймлайна, ставится последним, без payload.

### 4.4 Критические правила заполнения payload (по компонентам)

> Каждое правило ниже — результат реальных ошибок. Нарушение = слайд не рендерится или выглядит сломанно.
> **Перед заполнением payload ВСЕГДА получай `example` через `GET /components/`.**

| Правило | Компонент | Описание |
|---------|-----------|----------|
| slug = `BrowserMockup` | `BrowserMockup` | slug точь-в-точь как ключ в реестре. `BrowserMockupSlide` — не в реестре, экран пустой |
| `type: "html"` | `BrowserMockup` | HTML-строка в `content` надёжнее, чем image URL (CORS) |
| HTML = реальный UI | `BrowserMockup` | `content` обязан выглядеть как настоящий интерфейс: сайдбар/навигация (desktop), хедер с заголовком, карточки/таблицы данных. **НЕ** просто голые блоки — только полный UI с контекстом |
| Мобильная адаптация HTML | `BrowserMockup` | `content` обязан адаптироваться: сайдбар `hidden md:flex`, хедер с hamburger `md:hidden`, карточки `grid-cols-2 lg:grid-cols-4`, отступы `p-3 md:p-5`. Обязательно `flex min-h-full w-full` на корне |
| `<em>` в title | Все | ~половина слов в `title` оборачивается в `<em>` (градиент в tech-варианте) |
| Пропорции `size` | `BentoGridGallery` | Для 3 айтемов: `2x1 + 1x2 + 2x1` ( заполняет сетку без пустых рядов). Не `2x2 + 1x1 + 1x1` — будут дыры |
| НЕ задавай `x`/`y` | `InteractiveArchitecture` | Auto-layout через топологический BFS. Координаты ломают раскладку |
| `start_time` у ОДНОЙ ноды | `InteractiveArchitecture` | Остальные ноды БЕЗ `start_time` — появляются автоматически. Если у всех → хаос. Правила плотности айтемов (§8.3) на этот компонент НЕ распространяются вообще — у него своя механика воспроизведения (фокус камеры по единственному `start_time`) |
| Разряженные `start_time` айтемов | Все (кроме `InteractiveArchitecture`) | Шаг между соседними айтемами **≥ 800–1000 мс** (лучше ~1000+). Плотная набивка (200–500 мс) = рваный резкий эффект. Валидатор ловит только немонотонность, плотность — на совести агента |
| `value` = integer | `AnimatedStatsSlide` | Не строка. Избегай 0 — неинформативно |
| РАЗНЫЕ color/icon | `AnimatedStatsSlide`, `InfographicCards`, `PremiumChecklist` | Каждый item = уникальная комбинация. `color` управляет ТОЛЬКО иконкой/маркером/текстом, фон айтема всегда `var(--item-bg)` — тинт фона от акцента запрещён |
| `value` = 1 слово | `InfographicCards` | Иначе не влезет в карточку (text-4xl) |
| `layout: "horizontal"` | `ProcessFunnel` | Не vertical. Label БЕЗ числа (count показан сам) |
| `percentage` (int 0–100) | `MetricScales` | Не `value`/`max_value`. Color = gradient строка |
| `total_text` = слово | `ReceiptCard` | «ИТОГО», «ПОТЕРЯНО», не число |
| `role` (не `sender`!) | `ChatMockupSlide` | `"user"` / `"assistant"` |
| Живая переписка | `ChatMockupSlide` | Диалог обязан быть двусторонним: `user` → `assistant` → `user`... Одинокий `user` без ответа бота = мёртвый кадр. Если следующий слайд разбирает ошибку бота — бот на этом слайде ОБЯЗАН ошибиться в ответе (выдуманный факт/ссылка), иначе сетап не работает |
| `color` + без 0 | `AnimatedStatsSlide` | Каждый stat: `color` (hex, у всех разный) + `icon`. `value: 0` запрещён даже для «0 конфликтов» — переформулируй достижением (`value: 3, label: "Месяца без конфликтов"`). Статов ≥2, лучше 3 |
| `id` обязателен | `ComparisonTable` | Строка: «r1», «r2»... `headers[0]` = `""` |
| `start_ms`/`duration_ms` | `NetworkWaterfall` | Не `start_pct`/`duration_pct` |
| `color` ТОЛЬКО из списка | `ArchitectureDiagram` | Разрешено: `blue` / `green` / `amber` (legacy-имена), `chart-1`..`chart-4`, полные токены `color-secondary`/`color-success`/`color-warning`/`color-accent`, hex `#...`. **ЗАПРЕЩЁН** голый `primary` — `getHexColor` превратит его в `var(--primary)`, которого нет в теме → нода/линия белая. Маппинг — `core/src/utils/colors.ts` (`blue→color-secondary`, `green→color-success`, `amber→color-warning`) |
| Минимум айтемов (широкоформат) | Все списочные | Широкий экран пустотой не прощает: `InfographicCards` = **ровно 4** (не 6! 6 ломает сетку), `ReceiptCard` ≥3, `ProcessFunnel` ≥4 шага, `PremiumChecklist` ≥3, `StatsBarChart` ≥4, `ComparisonTable` ≥3 строк, `MetricScales` ≥3, `CrmCardSlide` = **ровно 4 поля + 2 кнопки** (не 5! 5-е поле ломает сетку 2×2). 1–2 айтема на 1920×1080 = пустой кадр |
| `label` (не `title`!) + `color` | `PremiumChecklist` | Ключ заголовка — `label`, рядом `desc`, `icon`, **`color`** (hex, у каждого айтема свой). Без `color` все иконки одного цвета |
| `count`+`icon`+`color` | `ProcessFunnel` | Каждый step ОБЯЗАН иметь `count` (integer, иначе renders `0`), `icon`, `color` (hex, у каждого шага свой). Без них — нули и одинаковые галочки |
| `id`+`trend`+`color` | `InfographicCards` | Каждый item: `id` (int), `value` (1 слово), `label`, `trend` (строка, напр. `+15%`), `color` (hex, у каждого свой), `icon`. Без `color`/`trend` карточки плоские |
| `id`, без 0% | `MetricScales` | Каждая метрика: `id` (int), `label` (понятный, не «Ложь агента»), `percentage` 1–100 (**0% запрещён** — неинформативно, как в `AnimatedStatsSlide`), `color` = gradient строка, у каждой метрики свой |
| `start_time` у строк, 3–4 строки | `ComparisonTable` | Каждая строка: `id` («r1»...), `label`, `values`, **`start_time`** (0/700/1400/2100). Иконок-колонок у компонента НЕТ — разнообразие даёт `true/false` (галочки) + строки. `headers[0]` = `""` |
| Суммы = озвучка, ≥3 пункта | `ReceiptCard` | `price` каждого пункта обязан совпадать с цифрами из сценария/озвучки (сверяйся с `scripts/_inbox/*.txt`). Пункты в сумме дают заявленный убыток (напр. 25000+9000+6000=40000). 1 пункт = пустой чек |
| Ключи CRM | `CrmCardSlide` | `customer`: `name` + `avatar_text` + `id_text` + `status` (НЕ `company`!). Поля: `label`/`value`/`field_icon`/`field_color` (НЕ `icon`!). Кнопки: `text` (НЕ `label`!) + `btn_color`. Иначе кнопка — пустая синяя плашка |
| `cmd` (не `text`!) | `TerminalMockup` | Ключ команды — `cmd` + `output`. С `text` команда не рендерится |

### 4.5 Создание нового компонента (обязательный порядок)

> 📘 **Полный конвейер (для ИИ-автоматизации): `docs/COMPONENT_PIPELINE.md`** —
> пошаговый механизм, типизация полей, детерминированные анимации, формат
> документирования в БД, чек-лист приёмки и реестр подводных камней.

Общей «обёртки», которая рендерит любой компонент, **не существует** (DOM у диаграммы, чата и
таблицы разный). Но 3 слоя уже нормализуют 80% работы, и компоненту остаётся только написать
свой контент:

1. **`Slide.vue`** (движок) — сам даёт заголовок, layout, `relativeTime`, `clicks`. НЕ писать свою шапку/тайминг.
2. **`useVariant`** — сам даёт стили айтемов (`var(--item-*)`) и линий, привязанные к теме и варианту.
3. **Контракт в БД** (`default_payload` + `payload_schema` + `example` + `manifest`) — сам даёт заполнение и валидацию.

**Базовая структура (соблюдать всегда):**

- Компонент объявляет пропсы `mobile`, `clicks`, `slideStartTime` + ключи payload из `default_payload` — всё через `defineProps`.
- Данные только из props. Никакого хардкода текста/медиа/цветов.
- Время: `inject('relativeTime')`, появление по `relativeTime >= item.start_time`.
- Анимации детерминированные (см. §11), без `requestAnimationFrame` и CSS `infinite`.
- Стили: токены `var(--text-primary)` / классы `text-text-primary`, `bg-bg-surface` и т.п. + `useVariant` для вариантов.

**Чеклист создания:**

1. Скопируй заготовку `core/src/components/_template/ComponentTemplate.vue` (там уже всё по конвенциям).
2. Перепиши `defineProps` под свои ключи payload, заполни шаблон контентом.
3. Зарегистрируй в `core/src/config/componentsRegistry.js` (ключ `componentsMap` = slug = имя файла).
4. Добавь запись в `scripts/seed_components.py` (`slug`, `title`, `type`, `cat`, `payload` — образец данных).
5. Перегенерируй: `seed_components.py` → `generate_schemas.py` → `generate_examples.py` → `seed_manifests.py`.
6. Опиши `manifest` (когда использовать / не использовать) в `scripts/seed_manifests.py`.
7. Проверь, что `payload_schema` и `example` у нового компонента валидны (`GET /components/`).

---

## 5. Схема полей (`payload_schema`)

`payload_schema` — рекурсивная структура, зеркалящая `default_payload`. Формат:

```json
{
  "type": "object",
  "fields": {
    "title": { "type": "text", "required": true },
    "nodes": {
      "type": "array", "min_items": 1, "max_items": 14,
      "item": { "type": "object", "fields": { "id": {"type":"text"}, "to": {"type":"array","item":{"type":"text"}} } }
    }
  }
}
```

- Скаляр — `{ "type": "..." }` (+ `options` для enum, `required: true`).
- Массив — `{ "type": "array", "min_items", "max_items", "item": <схема элемента> }`.
- Объект — `{ "type": "object", "fields": { ... } }`.

### Словарь типов полей

| type | Смысл | Редактор рисует |
|------|-------|----------------|
| `text` | короткий текст | input |
| `long_text` | абзац/описание | textarea |
| `code` | код/терминал | textarea (моно) |
| `html` | сырой HTML | textarea |
| `number` | число (float) | number |
| `integer` | целое | number (step 1) |
| `boolean` | флаг | переключатель |
| `color` | hex-цвет | палитра |
| `gradient` | `linear-gradient(...)` | палитра/строка |
| `image` | картинка | медиа-библиотека |
| `video` | видео | медиа-библиотека |
| `audio` | аудио | медиа-библиотека |
| `icon` | иконка | иконка-пикер |
| `time` | время в мс | тайм-пикер |
| `position` | `"x% y%"` | строка |
| `enum` | выбор из списка | select (`options`) |
| `array` | массив | редактор массива (`item`) |
| `object` | вложенный объект | рекурсия (`fields`) |

Тип выводится автоматически скриптом `scripts/generate_schemas.py` (по имени ключа + типу значения),
а затем уточняется вручную. Единая точка правки типов — `generate_schemas.py`.

---

## 6. Валидация

- Endpoint: `POST /components/{slug}/validate` с телом `{ "payload": {...} }`, опционально `?strict=true`, `?lint=true`.
- Возвращает `{ "valid": bool, "errors": [{ "path", "type", "message }], "warnings": [...] }`.
- Проверяет: `required`, типы, `min_items`/`max_items`, `enum`, форматы `color/icon/image/video/audio`, монотонность `start_time` в массивах (`non_monotonic_start_time`).
- `strict=true`: дополнительно ловит неизвестные поля (`unknown_field`, опечатки) — для проверки перед сохранением; сохранение слайдов работает в нестрогом режиме.
- `lint=true`: style-lint (`backend/style_lint.py`), warnings НЕ блокируют (`valid` от них не меняется):
  `no-hex` (hex в поле `color` — только типизированные поля; `code`/`html` не трогаем; бренд-hex логотипов `#42b883/#009688/#336791` разрешены),
  `accent-budget` (>4 distinct акцентов), `dense_timing` (шаг `start_time` 0<gap<800мс; gap 0 = синхронность, `InteractiveArchitecture` — skip),
  на сохранении слайда плюс `low-contrast` (заголовок < 4.5, нужна тема; transparent surface → `bg-base`).
  Сохранение слайда (`POST/PUT`) всегда считает линт и возвращает `warnings` в ответе; редактор показывает их жёлтой плашкой и не закрывается.
- Сохранение слайда через API тоже валидирует (невалидный payload → 422).

ИИ-агент обязан: заполнить payload → `POST /components/{slug}/validate?lint=true` → при ошибках поправить по `message` → повторить; warnings — поправить тоже (плотность ≥800мс, токены вместо hex, ≤4 акцентов).

---

## 7. Редактор

Правую панель рисуют два компонента:

- `SlideEditorModal.vue` — модал редактирования слайда (открывается из плеера).
- `DynamicJsonEditor.vue` — рекурсивный редактор JSON, **управляется схемой** (`payload_schema`).
- Сайдбар слайдов (`SlidePresentation.vue`): правый клик по слайду — контекстное меню
  (переименовать inline / дублировать / вариант из библиотеки / удалить).
- Шестерёнка — `PresentationSettingsModal.vue`: пресет+лок, вариант по умолчанию, шахматка opt-in
  (`presentations.chessboard` → `Slide.vue` фон `slide-bg-{(index%4)+1}`, по дефолту выкл).

Логика типизации полей в `DynamicJsonEditor`:

1. Тип инпута берётся из `payload_schema.fields[key].type` (schema-driven).
2. Если ключа нет в схеме — **fallback** на эвристики по имени ключа (обратная совместимость): `image/media/video` → медиа, `color/gradient/fill/stroke` → цвет, `icon` → иконка, `time/duration/delay` → время, `role`/`sender` → enum, `scale/opacity/speed` → число, и т.д.
3. Спец-кейсы: полиморфное поле `content` (BrowserMockup) — картинка **или** html в зависимости от соседнего `type`; `columns` редактируются как таблица колонок.

Чтобы новое поле в компоненте редактировалось правильным инпутом — оно обязано:
- присутствовать в `default_payload` (в `seed_components.py`) **и**
- получить корректный `type` в `payload_schema` (через `generate_schemas.py`).

---

## 8. Тайминги (`start_time`)

### 8.1 Длительность слайда

- **Шортсы: 3–6 секунд. Длинные видео: 4–10 секунд. Оптимум — 5–7 секунд.**
- **Дольше 7 секунд — только в крайних случаях:** много информации на слайде или нужно
  особо задержаться именно на этом слайде. Долгий статичный кадр убивает динамику.
- **Разбивай аудио-клип на подслайды** под эти диапазоны.
  Текст/данные внутри клипа распределяй по подслайдам (не дублируй).
  Клип короче 2с — не дробить: один слайд покрывает несколько таких клипов (см. §8.3).
- Пример: аудио-клип 15с → 3 слайда по 5с; клип 4.7с → 1 слайд; клип 12с → 2 слайда по 6с.

### 8.2 Финальный технический слайд

- **EndMarkerSlide ставится ВСЕГДА последним, без payload.** Презентация без маркера = некорректный конец видео.
- **Если на таймлайне есть озвучка** (трек озвучки `main` / `voiceover`, обычно `tracks[0]`):
  `EndMarker.start_time` = **ровно конец последнего клипа озвучки** (`clip.start_time + длительность`).
  Ориентир — **дорожка озвучки (трек 1), НЕ фоновая музыка** (трек `overlay`/BGM — она длиннее и не якорь).
- **OutroSlide** — последний контентный слайд перед маркером: его окно **заканчивается там, где начинается маркер**
  (`Outro.start = конец_озвучки − длительность_Outro`, длительность Outro в рамках §8.1).
- **Если озвучки нет:** `EndMarker = старт последнего слайда + его длительность`. Хвост после маркера ≤ 5с.
- **EndMarkerSlide — якорь конца видео** (`renders.py` + фронт берут `EndMarker.start_time`):
  `duration = EndMarker/1000 + 1с` (+ ~1-1.5с оверхеда захвата ≈ 2-2.5с хвоста).
  **Двигая маркер, ты двигаешь конец mp4.**

### 8.3 Общие правила таймлайна

- **Глобальный таймлайн:** каждый слайд имеет `start_time` (мс, от начала презентации).
  **Слайды СТРОГО не налезают друг на друга:** `start_time(N+1) > start_time(N)`,
  проверка перед сохранением: `start_time(N+1) − start_time(N) ≥ 2000`.
- **Минимальная дистанция между стартами соседних слайдов — 2000 мс. Без исключений**
  (ни для шортсов, ни для длинных с аудио-таймлайном).
- **Старты слайдов = координаты аудио-клипов.** Бери `start_time` из `audio_timeline.tracks[0].clips[i].start_time`, не пересчитывай вручную — накапливается ошибка.
- **Локальный таймлайн (разряженность айтемов):** внутри payload массивы элементов (`messages`, `nodes`, `items`, ...)
  имеют свои `start_time` — **относительно старта слайда** (0 = сразу). Распределяй нарастающе **и разряженно**:
  шаг между соседними айтемами — **≥ 800–1000 мс (рекомендовано ~1000+)**,
  чтобы анимация каждого айтема успевала плавно проиграться. Плотная набивка (шаг 200–500 мс) =
  рваный резкий эффект: анимации не успевают отыграть и наслаиваются друг на друга.
  Валидатор проверяет только монотонность `start_time`, но НЕ плотность — это дисциплина агента.
  После последнего элемента оставляй ≥ 2000 мс до перехода к следующему слайду.
- **Исключение: `InteractiveArchitecture` (канвас-схема).** Правила плотности на неё **не распространяются вообще**:
  у неё своя механика воспроизведения — `start_time` ставится **только у ОДНОЙ ноды** (фокус камеры),
  остальные ноды появляются автоматически (см. §4.4). Назначение таймингов всем нодам ломает схему.
- Ключ тайминга — **только `start_time`** (snake_case). Внутри `director_events` для события используется `time`.

---

## 9. Темы и стили (design tokens)

Стили вынесены из кода в БД (таблица `design_tokens`).

- **Иерархия:** `global (project_id=NULL)` → `project` → `presentation` → `slide`. Чем ниже уровень, тем выше приоритет (мерж снизу вверх).
- **Применение:** токены превращаются в CSS-переменные на контейнере `.slides-container` (`core/src/composables/useTheme.js` → `applyThemeToSlides`). Для hex-цветов дополнительно создаётся `--{key}-rgb` (`"21 32 51"`).
- **Ключи токенов** (глобальные дефолты, тёмная тема IT2B):

| Ключ | Значение | Назначение |
|------|---------|-----------|
| `bg-base` | `#0B1322` | фон слайда |
| `bg-surface` | `#152033` | поверхность (карточки) |
| `bg-surface-hover` | `#1F2D44` | поверхность hover |
| `brand-blue` | `#2563EB` | акцент |
| `brand-light-blue` | `#38BDF8` | светлый акцент |
| `brand-green` | `#10B981` | успех |
| `brand-amber` | `#F59E0B` | предупреждение |
| `brand-orange` | `#EA580C` | акцент 2 |
| `text-primary` | `#F8FAFC` | основной текст |
| `text-secondary` | `#94A3B8` | вторичный текст |
| `text-muted` | `#64748B` | приглушённый текст |
| `font-sans` / `font-heading` / `font-mono` | — | шрифты (CSS font-family) |
| `font_link` | Google Fonts URL | ссылка на шрифты (грузится динамически, см. ниже) |

- **Шрифты — из Google, не хранятся в репозитории.** Токен `font_link` содержит ссылку на Google Fonts
  (`https://fonts.googleapis.com/css2?...`). Фронт при загрузке темы вставляет `<link rel="stylesheet">`
  (`useTheme.js` → `applyFontLink`), а `font-sans`/`font-heading`/`font-mono` задают CSS-стеки этих шрифтов.
  Меняешь `font_link` + имена шрифтов в токенах — тема переходит на другие шрифты без правки кода.
- **Закрыто (не редактируется):** отступы/паддинги **НЕ токены**. Они задаются только
  вариантом отрисовки (`style_variants.config` → `item.spacing`) и дизайн-системой компонента.
- **Типографическая шкала — исключение:** `type-display/h1/h2/body/caption` — токены кеглей
  (контролируемая шкала, не произвольные размеры). `Slide.vue` читает `var(--type-h1)` /
  `var(--type-body)` с fallback на текущие классы (`text-4xl`/`text-lg`), tech-значения равны
  текущим — tech попиксельно не меняется.
- В Tailwind цвета/шрифты заведены как `bg-bg-base`, `text-text-primary`, `border-text-muted`, `bg-brand-*` и т.д.
- **Второй проект `history` (id=2)** имеет светлую «бумажную» тему (серифные шрифты). Презентация `/p/11` — пример.
- API: `GET/PUT /projects/{id}/tokens`, `GET /presentations/{id}/tokens`.
- Заполнение: `scripts/seed_tokens.py`.

> Скоуп темы: только `.slides-container` (контент слайда). Хром редактора/плеера остаётся на фиксированном тёмном `:root`.

---

## 10. Варианты отрисовки (типы) — `style_variants`

Отдельная ось от темы. **Тема** меняет цвета/шрифты, **вариант** меняет *как* рисуются части
компонента (радиусы, тени, тип фона, стиль линий). Вариант ложится поверх любой темы (классика + историческая палитра и т.п.).

### 10.1 Модель и API

- Таблица `style_variants`. Сейчас 5 вариантов: `tech`, `classic`, `industrial`, `educational`, `derevnya` (эко-стиль проекта `derevnya`).
- API: `GET /variants/`, `GET /variants/{slug}`, `POST /variants/`.
- Заполнение: `scripts/seed_variants.py`.
- Вариант задаётся на слайде как **top-level поле payload `variant: "classic"`** (в схеме — `enum` со слug'ами вариантов).
- **Вариант поддерживают все компоненты** (кроме служебного `EndMarkerSlide`) — радиусы/рамки/тени айтемов и контейнеров идут через `var(--item-*)`. Код/терминал (`CodeExplain`, `CodeWindow`, `TerminalMockup`) остаются тёмными внутри (Shiki/терминал), но их рамка/радиус — тоже от варианта.
- **Разделение осей — варианты НЕ задают цвета.** Вариант управляет материалом/формой/линиями/радиусами (solid/gradient/blur, border width, radius, shadow, line style). Цвета (заголовки `<em>`, текст, акценты айтемов, градиенты) — только из ПАЛИТРЫ (токены темы). Запрещено: жёсткие хью в `config.line.color` и в CSS `.variant-* { color: ... }` (старый баг: `.variant-classic em { color: brand-orange }` перекрашивал палитру при смене варианта). Допустимые исключения — стекло/неон (blur, glow), где материал сам ссылается на токены палитры.
  Обработка `<em>` (градиент `brand-light-blue → brand-blue`) — глобальная, не зависит от
  варианта: смена classic/industrial не должна «сплющивать» её в сплошной цвет.
- `tech` — глобально «сплошные карточки» (solid), стекло только у `ArchitectureDiagram` через per-component override (`components.ArchitectureDiagram`).
- **Резолв варианта слайда** (приоритет): `payload.variant` → `presentation.variant` (дефолт презентации, поле `variant`) → `tech`. Т.е. у презентации можно задать дефолт (напр. `classic` для исторической), и все слайды без явного `variant` его наследуют.

### 10.2 Единый формат `config`

```json
{
  "item": {                                   // обычный айтем/нода
    "bg": { "type": "solid|gradient|blur|transparent",
            "value": "bg-surface", "from": "bg-surface", "to": "bg-surface-hover",
            "angle": 135, "opacity": 0.7, "blur": "16px" },
    "border": { "width": 1, "style": "solid" },
    "radius": "16px",
    "shadow": "0 4px 12px rgb(0 0 0 / 0.15)",
    "spacing": { "padding": "12px", "gap": "8px" }
  },
  "item_primary": { ... },                    // акцентный/главный айтем (наследует item, если не задан)
  "line": { "color": "brand-light-blue", "style": "solid|dashed|dotted",
            "width": 2, "animation": "none|dash|particles|pulse|solid" },
  "surface": { "bg": { "type": "...", ... } }, // фон контейнера
  "motion": { "appear_ms": 500, "stagger_ms": 1000, "count_ms": 2000 },
                          // ритм: появление / шаг айтемов (§8.3) / счётчики. Компонент читает
                          // через useVariant().motion, хардкод длительностей запрещён
  "components": {                             // точечное переопределение под конкретный компонент
    "ArchitectureDiagram": { "item": { "bg": { "type": "blur", "value": "bg-surface", "opacity": 0.7, "blur": "16px" } } }
  }
}
```

- Цвета — это **ключи токенов темы** (не hex), поэтому вариант компонуется с палитрой.
- `bg.type` = `solid` / `gradient` / `blur` (glass) / `transparent`.
- `components.<slug>` — переопределяет секции `item`/`item_primary`/`line`/`surface` для одного компонента (мерж поверх глобальных значений).

### 10.3 Применение — composable `useVariant`

`core/src/composables/useVariant.js`. Компонент вызывает `useVariant(props.variant, '<slug>')` и получает
CSS-переменные + объект линий (второй аргумент — для per-component override):

- `itemVars` → `--item-bg`, `--item-backdrop`, `--item-radius`, `--item-shadow`, `--item-border-width`, `--item-border-style`, `--item-padding`, `--item-gap`.
- `itemPrimaryVars` → те же с префиксом `--item-primary-*`.
- `surfaceVars` → `--surface-bg`, `--surface-backdrop`.
- `line` → `{ color, style, dash, width, animation }`.

**Паттерн для компонента** (эталон — `ArchitectureDiagram.vue`):

```js
const { itemVars, itemPrimaryVars, line } = useVariant(computed(() => props.variant))
```

- Переменные накладываются на корень компонента: `:style="{ ...itemVars, ...itemPrimaryVars }"`.
- Айтемы читают `var(--item-radius)` / `var(--item-bg)` и т.д.; акцентный айтем — `var(--item-primary-*)`.
- SVG-линии используют `line.color / line.width / line.dash / line.animation`.
- Семантические цвета (роль ноды, цвет потока данных) остаются в компоненте; вариант задаёт только «форму/материал».

Чтобы добавить **новый вариант** — достаточно завести запись в `style_variants` (без правки кода компонентов).
Чтобы перевести **новый компонент** на варианты — добавить `variant` в его `default_payload` и применить тот же паттерн.

---

## 11. Анимации (правила для компонентов)

Актуальный рендер — realtime-захват (`backend/render_fullscreen_capture.py`, см. §11.1),
но правила ниже обязательны в любом случае: только детерминированные анимации дают
одинаковый результат в браузере, в покадровом рендере и при seek по таймлайну.

- **Запрещено** `requestAnimationFrame`, бесконечные CSS/SVG-анимации (`animation: ... infinite`), теги `<animate>`/`<animateMotion>` в SVG.
- Все анимации **детерминированы от `relativeTime`** (локальное время слайда, мс, через `inject('relativeTime')`).
- Зацикленные эффекты = математика в шаблоне: `Math.sin((relativeTime / 2000) * Math.PI * 2)` и т.п.
- Появление по времени: `relativeTime >= item.start_time` + `<TransitionGroup>` / CSS-transition.
- **Compositor vs Paint:** анимируй только через `transform` и `opacity` (compositor thread, zero-paint).
  `background-position`, `width`, `left`, `top` — paint properties, перерисовывают DOM **каждый кадр**
  в программном рендере (`--disable-gpu`). Вместо `background-position` — overlay с `transform: translateX()`.
  Вместо `width: 0→100%` — `transform: scaleX()`. Подробнее: `docs/COMPONENT_PIPELINE.md` §5.
- Подробнее: `docs/animation_guidelines.md`.

### 11.1 Серверный рендер видео (`backend/render_fullscreen_capture.py`)

Экспорт видео = **тот же Vue-фронтенд**, открытый в браузере под Playwright. Отдельного пути
рендера нет — если компонент корректно работает в браузере и соблюдает правила §11, он рендерится в видео автоматически.

Как это устроено (актуально, `backend/routers/renders.py` → `_presentation_duration_seconds`):

- Realtime-захват: `ffmpeg x11grab ($DISPLAY)` + pulse-аудио пишут mp4, параллельно Playwright
  (headless=False, fullscreen) открывает `/p/{id}?render=true` и крутит `window.useDirectorInstance.play()`.
- Длительность — **якорь `EndMarkerSlide`** (единственная точка истины, `renders.py:41`):
  если маркер есть, `duration = EndMarker.start_time/1000 + 1с` (захват добавляет сверху ~1-1.5с оверхеда
  на старт ffmpeg/цикл, итого хвост после маркера ≈ 2-2.5с; аудио за маркером жёстко режется).
  Fallback без маркера: `max(слайды, аудио.end_time)/1000 + 3с`. Фронт делает то же самое
  (`RenderManagerModal.getPresentationEndTime` + `useScreenRecorder.resolveEndTime` +300мс), поэтому
  **двигая `EndMarkerSlide`, ты двигаешь конец видео**. Размер из `settings.format`
  (`mobile 1080x1920, square 1080x1080, landscape 1920x1280, default 1920x1080`).
- Один активный рендер на job; новый убивает старый (`ACTIVE_RENDERS`). Требует `$DISPLAY` (Xvfb/headful) —
  в headless-окружении без дисплея рендер не стартует.
- Легаси-путь `backend/scripts/render_video.py` (покадровый headless Chromium +
  `Emulation.setVirtualTimePolicy('pause')` + `seek(time_ms)` + скриншоты в ffmpeg) сейчас **не вызывается**.
  Если к нему вернутся — время в компоненте обязано идти от `inject('relativeTime')`
  (`useDirector.currentTime`), а не от `performance.now()`/wall-clock.

**Вывод для новых компонентов:** никакого спецкода под рендер не нужно. Достаточно соблюдать §11
(детерминированные анимации от `relativeTime`, без `rAF`/`infinite`/`<animate>`) и тянуть время
только через `inject('relativeTime')`.

### 11.2 Safe-zone для шортс (портретный рендер)

Вертикальное видео уходит под кнопки YouTube/TikTok (справа рейл, снизу 400–500px UI).
Поэтому **только портретный рендер** ужимает контентный слой: скейл `0.85` + сдвиг `−2%`
(почти по центру, чуть выше). **Фон слайда всегда растянут на весь кадр** — жмётся только
внутренний `.slides-safebox`, вёрстка не трогается (чистый `transform`, без рефлоу).
Поля вокруг контента = фон темы (никаких белых полос).

- Серверный захват: `render_fullscreen_capture.py` при `height > width` дописывает к URL
  `?safe=0.85&safeshift=-0.02` (параметры `--safe-scale`, `--safe-shift`, шифт — доля высоты слоя).
- Live-захват: `useScreenRecorder` (только `format: portrait`) ставит `window.__safeZone` +
  событие `presentation:safezone`.
- Применение: `SlidePresentation.containerStyle` (обе ветки — `renderWidth` и обычная).
  Ландшафт и обычный просмотр/редактирование safe-zone не затрагивает.

---

## 12. Скрипты (сиды и генераторы)

| Скрипт | Что делает |
|--------|-----------|
| `scripts/seed_components.py` | пересоздаёт таблицу `components` и заливает 32 компонента (с `default_payload`) |
| `scripts/generate_schemas.py` | генерирует `payload_schema` (типы + min/max_items + enum, включая enum `variant` из `style_variants`) |
| `scripts/generate_examples.py` | генерирует `example` (из живой презентации `/p/4`) |
| `scripts/seed_manifests.py` | заполняет `description` + `manifest` + `required` |
| `scripts/seed_tokens.py` | глобальные токены + проект `history` |
| `scripts/seed_variants.py` | варианты отрисовки `style_variants` |
| `scripts/check_consistency.py` | сверка `components.slug ↔ componentsMap ↔ .vue` (запуск с хоста, exit 1 при дрейфе) |
| `scripts/generate_short.py` | 🔒 LOCKED — из сценария: презентация + TTS + `audio_timeline` + `EndMarkerSlide`. **Слайды НЕ создаёт** (см. ниже / `docs/AGENT_PLAYBOOK.md`) |
| `scripts/revoice_from_file.py` | переозвучка существующей презентации из .txt файла (слайды ремапятся) |
| `scripts/build_shorts20_slides.py` | шаблон сборки контентных слайдов: массив `SLIDES` → `validate` → `POST /slides` |
| `scripts/trim_payload_text.py` | обрезка длинных текстов payload под бюджет «воздуха» (`source_note` ≤80, `description` ≤90, `subtitle` ≤60) |

> **Полный процесс «сценарий → готовая презентация» (озвучка, таймлайн, данные, слайды) —
> `docs/AGENT_PLAYBOOK.md`.** Это главная инструкция агента по созданию презентаций.

### 🔒 Базовый шаблон шортсов (locked, p/16 calibration)

Параметры по умолчанию для нового контента. **Не менять без перекалибровки.**

| Параметр | Значение |
|----------|----------|
| Gemini TTS pace | `"Very fast, rapid-fire, urgent"` (текстовый промпт) |
| ffmpeg speedup | **1.0** (без ускорения) |
| Паузы между блоками | **200мс** (только между смысловыми блоками) |
| Внутри блока | непрерывный поток, без пауз |
| Слайды | **3–6с** каждый, ~14 слайдов на ~53с |
| Блоки TTS | 5 (hook/most/proof/payoff/cta) = 1 TTS-вызов на блок |
| Голос | `Charon`, temperature 0.8 (hook: 0.9) |
| BGM | `Automated_Horizon.mp3`, volume 0.15 |

**Запуск:** `docker compose exec backend python scripts/generate_short.py --short N`
или из своего сценария: `... generate_short.py --file scripts/_inbox/text.txt --title "Название"`
**Переозвучка:** `docker compose exec backend python scripts/revoice_from_file.py --pres-id N --file scripts/_inbox/text.txt`
**Слайды:** отдельным скриптом (`scripts/build_shorts*_slides.py`) или через API — см. `docs/AGENT_PLAYBOOK.md`.

**Порядок после изменения `seed_components.py`** (внутри backend-контейнера):

```
python scripts/seed_components.py
python scripts/generate_schemas.py
python scripts/generate_examples.py
python scripts/seed_manifests.py
```

(Все генераторы идемпотентны. Через docker: `docker compose exec backend python scripts/...`.)

---

## 13. Рабочий процесс ИИ-агента (как создавать презентацию)

0. **Выбрать вектор**: `GET /presets/` → назначь пресет (`PUT /presentations/{id}/style`).
   Все слайды — в его варианте и правилах; с `style_lock=true` выход за вектор = 422.
1. **Выбрать компоненты** под сценарий — по `manifest` каждого компонента из `GET /components/`.
2. **Получить контракт** нужного компонента: `payload_schema` (типы/обязательность) + `example` (образец).
3. **Заполнить payload** по схеме + примеру (используй `start_time` для последовательного появления).
4. **Провалидировать**: `POST /components/{slug}/validate` `{"payload": {...}}` → при ошибках поправить.
5. **Создать презентацию и слайды** (см. API ниже): слайд = `slide_id` (уникальная строка) + `component` + `start_time` + `order_index` + `data.payload`.
6. Расставить слайды с отступами ≥ 2000 мс; в конце — `EndMarkerSlide`.

### Пример payload (ArchitectureDiagram)

```json
{
  "variant": "tech",
  "show_data_flow": true,
  "nodes": [
    { "id": "in1", "title": "Telegram Bot", "subtitle": "Frontend", "icon": "telegram", "color": "blue", "start_time": 500, "is_main": false, "to": ["core1"] },
    { "id": "core1", "title": "ИИ Драйвер", "subtitle": "Agent Router", "icon": "cpu", "color": "#8c75ff", "start_time": 1600, "is_main": true, "to": ["out1"] },
    { "id": "out1", "title": "База данных", "subtitle": "PostgreSQL", "icon": "db", "color": "green", "start_time": 2700, "is_main": false }
  ]
}
```

---

## 14. Справочник API (для агента)

Базовый URL: `http://localhost:8001` (или `/api/...` через фронт).

| Метод | Endpoint | Назначение |
|-------|---------|-----------|
| GET | `/components/` | библиотека: `slug, title, description, manifest, default_payload, payload_schema, example, type, categories` |
| GET | `/components/types`, `/components/categories` | типы и категории |
| POST | `/components/{slug}/validate` | валидация payload |
| GET | `/variants/`, `/variants/{slug}` | варианты отрисовки |
| GET | `/projects/`, `/projects/{slug}` | проекты |
| GET/PUT | `/projects/{id}/tokens` | токены темы проекта |
| GET | `/presentations/`, `/presentations/{id}` | презентации |
| GET | `/presentations/{id}/tokens` | токены (мерж глобал+проект) презентации |
| POST | `/presentations/` | создать презентацию |
| POST | `/presentations/{id}/slides` | создать слайд |
| PUT | `/presentations/slides/{slide_id}` | обновить слайд |
| DELETE | `/presentations/slides/{slide_id}` | удалить слайд |
| POST | `/presentations/{id}/media` | загрузить медиа |
| GET | `/presentations/{id}/global-media`, `/presentations/search/media` | медиа-библиотека |

**Тело создания слайда** (`POST /presentations/{id}/slides`): обязательные `slide_id` (строка), `component` (slug), `start_time` (мс), `order_index`; опциональные `title`, `subtitle`, `layout`, `data: { payload: {...} }`, `events`.

---

## 15. Конвенции

- **Имена ключей** — snake_case (`start_time`, `show_data_flow`, `bot_name`). Компонент принимает пропы «как есть».
- **`start_time`** — только snake_case, мс. Внутри payload-массивов — локальное время слайда.
- **Иконки** — Iconify: префиксы `lucide:*`, `heroicons:*`, `logos:*` (поле типа `icon`).
- **Цвета — быстрые дефолты (не пикер):** для бейджей — `color-success/danger/warning/info` (+ `-soft` для фона, `getColorAlpha` для `0.15`); для разноцветных айтемов — шахматка `item-accent-1..4` циклично `var(--item-accent-{(i%4)+1})` (см. `TOKEN_SPEC.md §1.9`), вместо случайного hex/пикера. Для диаграмм — `chart-1..6`.
- **Резолв токенов в коде (`core/src/utils/colors.ts`):** `getHexColor(id)` — legacy-имена (`brand-*`, `blue/green/amber`) → `var(--*)`, hex/var/rgb — passthrough, иначе `var(--id)` (голый `primary` даст битую `var(--primary)` — только полные ключи). `getColorAlpha(id, a)` — только `var(--X)` (нужен `--X-rgb`, генерится `useTheme` из hex и rgba) или чистый hex; градиенты/rgba-строки/токены без `-rgb` → fallback `color-secondary`. НЕ оборачивать ключ в `var(--X, X)` вручную — ломает извлечение `-rgb` (баг `Ecosystem.vue`, итерация 7).
- **Фоны только через вариант:** фон айтема — `var(--item-bg)` (root спредит `...itemVars`), фон слайда — `var(--surface-bg)`. Хардкод `bg-bg-base`/`bg-bg-surface` внутри контентных компонентов запрещён (исключения: `ReceiptCard` — фиксированный белый, тёмная зона кода, плейсхолдеры пустых медиа). Внутренние дивы окон (`TerminalMockup`, `BrowserMockup`, `CodeExplain`) — `bg-[var(--item-bg)]`, `WindowHeader` — `var(--item-bg, var(--bg-surface))`. Скроллбары — `var(--item-bg, var(--bg-base))`.
- **Текст** — лаконичные `title`/`subtitle`; пояснения оставляй озвучке, а не на слайде.
- **Тайтлы — `<em>` теги** — **ОБЯЗАТЕЛЬНО**: ~половина слов в `title` оборачивается в `<em>`. В tech-варианте `<em>` получает градиент (`brand-light-blue → brand-blue`). Пример: `"Сделка <em>встала</em>"`, `"Без границ — <em>фантазёр</em>"`, `"<em>Результат</em>"`. Пустые тайтлы (ReceiptCard, BrowserMockup, TerminalMockup, OutroSlide) — без изменений.
- **Разделители слайда** — **ОБЯЗАТЕЛЬНО**: если видимая длина `title` и `subtitle` пуста (после удаления HTML-тегов и пробелов), `HorizontalDivider` и `VerticalDivider` в `Slide.vue` не отображаются.
- **Не хардкодить стили** в компонентах — только токены/варианты.
- **Валюта — только €**. Символ ₽ **ЗАПРЕЩЁН** во всех презентациях. Проект работает на евро. `currency` в ReceiptCard и любых других компонентах — только `"€"`.
- **Эмодзи запрещены** в payload компонентов. В полях `bot_avatar`, `icon`, `value`, `label`, `name` — только Lucide/Heroicons иконки (`lucide:package`, `lucide:clock` и т.п.) или текстовые значения. Unicode-эмодзи (📦🚚💰🤖💸🇩🇪⏱️⚠️) **нельзя**.
- **Тайтлы без эмодзи** — `<em>` теги и текст, никаких графических символов.
- **Текст тайтлов — перефразировка** озвучки, а не копирование. Слайд передаёт **смысл**, но слово в слово не повторяет голос. Пример: агент говорит «Менеджеры полдня отвечают на одно и то же» → тайтл «Операционная перегрузка», а не «Менеджеры отвечают на одно и то же».

---

## 16. Бюджет кадра, текста и анимации (обязательный чек-лист генерации)

> 📘 Полный свод: **`docs/COMPONENT_USAGE_RULES.md`**. Компактная версия автоматически
> добавляется в `manifest` каждого компонента в БД (`scripts/seed_manifests.py` → `MANIFEST_RULES`)
> и отдаётся через `GET /components/` — модель обязана её соблюдать.

- **Кадр:** `/p/{id}` = **980×552**, контентная область **884×381 CSS**; мобайл — **450×800**.
  Контент обязан **заполнить кадр без пустот (>25%), без скролла и без обрезки**. `root` —
  `w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col`, заполнение — `flex-1 min-h-0`.
- **Текст (эстетика/воздух):** `title` ≤ 6 слов (с `<em>`), пункт ≤ 6 слов, описание ≤ 90 симв.,
  таблица ≤ 6 строк, значение ≤ 24 симв. Больше `gap`/`padding`, а не меньше кегль. Нет «стен текста» —
  при перегрузе дроби на подслайды (§8.1).
- **Анимация (детерминизм, §11):** только от `inject('relativeTime')`. Запрещено: `requestAnimationFrame`,
  CSS `animation: … infinite`, SVG `<animate>`/`<animateMotion>`, `setInterval`/`setTimeout` как источник
  анимации, `performance.now()`/`Date.now()`, `Math.random()`. Анимируй только `transform`/`opacity`.
  Reveal-шаг `≥800мс`, последний элемент `≤~4000мс` (шаг = `min(stagger_ms, 4000/(n-1))`); `source_note` —
  от последней ноды (`max(start_time)+appear_ms`), не от `len*stagger`. Длительности — из `useVariant().motion`.
- **Стекло:** элемент с `background: var(--item-bg)`/`--item-primary-bg` **обязан** нести
  `backdropFilter: var(--item-backdrop)`/`--item-primary-backdrop` **и** `WebkitBackdropFilter` (не наследуется).
  Декоративный glow/пульсации — `pointer-events-none` (иначе ложное переполнение: `-right-32 w-64` = +128px).
- **Данные:** валюта только **€**, эмодзи запрещены, числа сходятся с озвучкой, `0` в метриках запрещён,
  `start_time` snake_case (мс, монотонно, соседние слайды ≥ 2000мс), медиа — валидный URL или
  **стилизованное пустое состояние** (не «битая картинка»).
- **Перед сдачей:** `POST /components/{slug}/validate?lint=true` + `scripts/qa_audit.py <pres> i i+1`
  (desktop и `mobile`) → `flagged=0` + `python3 scripts/check_consistency.py` → OK.
