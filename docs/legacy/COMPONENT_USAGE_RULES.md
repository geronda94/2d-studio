# COMPONENT_USAGE_RULES — правила использования компонентов (для ИИ-генерации)

Единый свод правил, чтобы модели генерировали слайды **без косяков анимации, без
переполнений, с правильными данными и без текстового перегруза**. Компактная версия
этих правил автоматически добавляется в `manifest` каждого компонента в БД
(`scripts/seed_manifests.py` → `RULES`), поэтому доступна через `GET /components/`.

> Перед генерацией всегда получай контракт: `GET /components/{slug}` → `payload_schema`
> (типы/`required`/`min_items`/`max_items`/`enum`) + `example` (эталон данных).

---

## 1. Бюджет кадра (главное)

Полноэкранный слайд — это НЕ страница. Канвас `/p/{id}`: **980×552**, контентная область
**884×381 CSS** (пропорция ~2.32:1). Мобильный лист — **450×800**.

Правило: контент обязан **заполнить кадр целиком и не выйти за него**:
- нет «мёртвых» полос (>25% пустоты);
- нет обрезанного/уехавшего за край контента;
- нет появления скролла (ни десктоп, ни мобильный).

Что делать: `root` компонента — `w-full max-w-6xl mx-auto h-full min-h-0 flex flex-col`;
заполнение по высоте — `flex-1 min-h-0`. Никаких фиксированных `min-height`, превышающих кадр.

---

## 2. Переполнение и скролл

- **Никаких внутренних скроллов** в контенте (`overflow-y-auto` для кода/терминала —
  только если контент реально длинный; в остальных случаях данные ужимать).
- Декоративные элементы (glow, пульсации, блики) обязаны иметь `pointer-events-none`,
  иначе они раздувают `scrollWidth/scrollHeight` и дают ложное «переполнение».
  Пример: свечение `-right-32 w-64` = ровно +128px.

- **Стекло (glassmorphism)**: если элемент имеет `background: var(--item-bg)` /
  `var(--item-primary-bg)`, он ОБЯЗАН нести `backdropFilter: var(--item-backdrop)` /
  `var(--item-primary-backdrop)` **и** `WebkitBackdropFilter`. `backdrop-filter` не
  наследуется — без него линия/фон просвечивает сквозь айтем («смешивание»).
- Соединительные линии рисуются ПОД узлами; узлы перекрывают их (`z-20`) и применяют blur.
- **Вариативность (обязательно):** материал, формы и тени берутся ТОЛЬКО из варианта:
  `var(--item-radius)`, `var(--item-shadow)`, `var(--item-border-*)`, `var(--item-bg)`,
  `var(--item-padding/gap)` (и `--item-primary-*` для акцентных). Хардкод
  `rounded-lg/xl/2xl`, `shadow-*`, `border-[N]px` внутри айтемов **запрещён** — он
  игнорирует `config` из `style_variants` (компонент использует палитру, но «выпадает»
  при смене варианта/темы проекта). Вложенные элементы — производные:
  `calc(var(--item-radius) - 4px)`. Исключения (круглые аватары/точки/пилюли) — `999px`,
  но только для семантически круглых форм.

---

## 3. Текстовый бюджет (эстетика, «воздух»)

Меньше текста — больше воздуха. Слайд передаёт **смысл**, а не абзац.

- `title` слайда: **≤ 6 слов**, ~половина слов в `<em>`.
- Пункт списка / подпись карточки: **≤ 6 слов**; описание — **≤ 90 символов**, 1–2 строки.
- Таблица: **≤ 6 строк**, значение — **≤ 24 символов**.
- Дашборд: **≤ 4–6 KPI**, значение — **1 число / 1 слово**.
- Никогда не дублируй озвучку дословно. Нет «стен текста»: если нужно больше — разбивай
  на подслайды (§8.1 AGENTS), а не ужимай шрифт.
- Легенды/футноты — одной строкой, `text-muted`, ≤ 80 символов.
- Отступы важнее шрифта: увеличивай `gap`/`padding` (вариант `item.spacing`) вместо
  уменьшения кегля.

Минимумы (широкий формат не прощает пустоты):
`InfographicCards` = ровно 4 · `CrmCardSlide` = ровно 4 поля + 2 кнопки · `ReceiptCard` ≥ 3 ·
`ProcessFunnel` ≥ 4 · `PremiumChecklist` ≥ 3 · `StatsBarChart` ≥ 4 · `ComparisonTable` ≥ 3 ·
`MetricScales` ≥ 3.

---

## 4. Анимация (детерминизм — иначе видео/seek «угорает»)

Допустимы только детерминированные от `inject('relativeTime')` анимации:

- **Запрещено:** `requestAnimationFrame`, `setInterval`/`setTimeout` как источник анимации,
  CSS `animation: … infinite`, SVG `<animate>`/`<animateMotion>`, `performance.now()`,
  `Date.now()`, `Math.random()`.
- **Допустимо:** CSS `transition` на `transform`/`opacity` (однократный), вычисления по
  `relativeTime` (`Math.sin` и т.п. для «бегущих» эффектов).
- Анимируй только **`transform` и `opacity`** (compositor, zero-paint). Не `width/height/
  left/top/background-position` — это paint, перерисовка каждый кадр в софтверном рендере.
  Вместо `width: 0→100%` — `transform: scaleX()`; вместо `background-position` — overlay с
  `translateX()`.
- Появление: `relativeTime >= item.start_time` + `<TransitionGroup>`.
- **Reveal-тайминги должны укладываться в слайд**: шаг `stagger_ms ≥ 800`, а последний элемент
  — не позже ~4000 мс. Если элементов много, шаг считается как
  `min(stagger_ms, 4000 / (n-1))` (как в `WaterfallChart`), не `i * stagger_ms` вслепую.
- `source_note`/футноты: появление привязывай к последнему элементу
  (`max(start_time) + appear_ms`), а не к `len * stagger_ms` (иначе не появляется).
- Длительности берутся из `useVariant().motion` (`appear_ms`/`stagger_ms`/`count_ms`),
  не хардкодятся.
- `InteractiveArchitecture` — исключение: `start_time` только у ОДНОЙ ноды (фокус камеры).

---

## 5. Данные (без фактических ошибок)

- **Валюта — только €**. Символы `₽`/`$` запрещены.
- **Эмодзи запрещены** в payload (иконки — только Iconify `lucide:*`/`heroicons:*`/`logos:*`).
- Заголовки — с `<em>` (~половина слов); пустые заголовки у `ReceiptCard`/`BrowserMockup`/
  `TerminalMockup`/`OutroSlide` — норма.
- Суммы/числа в таблицах и чеках — **сходятся** со сценарием/озвучкой (сверяйся с текстом).
- Не ставь `0` в метриках/статах — переформулируй достижением (`value: 3, label: "Месяца без конфликтов"`).
- `start_time` **только snake_case**, мс, монотонно. Глобальные старты слайдов = `audio_timeline.tracks[0].clips[i].start_time`; соседние старты ≥ 2000 мс.
- Данные — только из props; текст — лаконичный; цвета — токены/`var(--…)`, не hex.

---

## 6. Медиа-библиотека

- `image`/`video`/`audio` — только валидный URL из библиотеки (`/media/...` или загруженный).
- **Не выдумывай URL** и не хардкодь чужие фото. Если ассета нет — используй **стилизованное
  пустое состояние** (токены + иконка + подпись), а НЕ «битую картинку».
- Перед сохранением проверь, что файл существует (`/media/...`), иначе слайд будет пустым.
- Медиа в портретном рендере ужимается safe-zone 0.85 — не прижимай важное к краям.

---

## 7. Обязательный прогон перед сдачей

1. `POST /components/{slug}/validate?lint=true` — исправить `errors` и `warnings`
   (`dense_timing`, `no-hex`, `accent-budget`).
2. Визуальный аудит: `scripts/qa_audit.py <pres> <i> <i+1>` (desktop) и `… mobile`
   → `flagged=0` (нет `rootOff/hOver/vOver/clip/scrollReq/contentOver`).
3. `python3 scripts/check_consistency.py` → `OK`.

---

## Приложение · Быстрые оговорки по компонентам

Полная конкретика — в `AGENTS.md §4.4` и `payload_schema`/`example` из API. Ключевое:

| Компонент | Оговорка |
|-----------|----------|
| `BrowserMockup` | `type: "html"` + реальный UI (сайдбар/хедер/карточки), адаптив, `flex min-h-full w-full` |
| `InteractiveArchitecture` | не задавать `x`/`y` — авто-layout; `start_time` у одной ноды |
| `ReceiptCard` | `total_text` = слово; пункты сходятся с озвучкой; ≥3 позиции |
| `CrmCardSlide` | `customer.{name,avatar_text,id_text,status}`; ровно 4 поля + 2 кнопки |
| `ProcessFunnel` | `layout: horizontal`; каждый step: `count`+`icon`+`color`; ≥4 |
| `MetricScales` | `percentage` 1–100 (0 запрещён); `color` — gradient |
| `InfographicCards` | ровно 4; `value` = 1 слово; `id`/`trend`/`color`/`icon` |
| `WaterfallChart` | reveal-шаг ≤4000мс; подписи над столбцами |
| `TimelineSlide` | точки — `transform: scale()`, НЕ `transition-all` |
| `Ecosystem`/`ChurchAsBody` | коннекторы из центра под стекло; note-reveal от последней ноды |
