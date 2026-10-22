# COMPONENT_AUDIT — аудит 50 компонентов движка

> Тип: **аудит + backlog. Ничего не изменено.** Все правки — только после согласования.
> Дата: 2026-09-22. Метод: машинный скан 50 `.vue` (метрики) + чтение всех компонентов
> + UX/overflow-замеры в браузере (desktop 1920×1080, mobile 450×800) + рендер-кадры.
> Связанная стратегия: `docs/COMPONENTS_ROADMAP_V2.md`.

---

## 1. Сводные метрики

| Метрика | Значение |
|---|---|
| Зарегистрированных компонентов | **50** (35 `ui/` + 15 `slides/`) |
| Суммарный объём (только зарегистрированные) | ~7 050 строк Vue |
| Компонентов с hex/`rgba` вне токенов | 3: `ReceiptCard`, `TerminalMockup`, `ProductCard` |
| `@keyframes` в компонентах | 3: `ArchitectureDiagram`, `ProcessFunnel`, `OutroSlide` |
| `requestAnimationFrame` | **0** |
| Бесконечные/не-детерминированные анимации | `OutroSlide` (mount fade), `MediaSlide` (`<video loop autoplay>`) |
| Без `useVariant` | 10 (в основном thin-обёртки `*Slide` + `ReceiptCard`) |
| Без `relativeTime` | 10 (обёртки делегируют внутрь + `OutroSlide` — реально) |
| Без `mobile`-prop | 3: `ReceiptCard`, `MetricScales`, `MediaSlide` |
| Рисуют свой `{{ title }}` (риск двойного заголовка) | 15 |
| Используют `v-html` | 5 (`InteractiveArchitecture`, `TerminalMockup`, `CodeExplain`, `PremiumChecklist`, `BrowserMockup`) |
| Фактические баги (undefined/токен/слаг) | 5 (см. §6) |
| Overflow/налезание на заголовок после проверки | 0 (найденные — исправлены в 18 новых) |

---

## 2. Системные выводы

1. **Ядро движка здоровое.** Оригинальные «дифференцирующие» компоненты (`ArchitectureDiagram`,
   `InteractiveArchitecture`, `TerminalMockup`, `CodeExplain`, `NetworkWaterfall`, `BrowserMockup`,
   `MediaSlide`, `AdvancedVideoSlide`, `PortraitLampSlide`, `TimelineSlide`, `Roadmap`,
   `ProcessFunnel`, `ReceiptCard`, `ChatMockupSlide`, `CodeComparisonSlide`, `CrmCardSlide`)
   имеют уникальный DOM и реально разные.
2. **18 новых сгруппировались в ~7 архетипов.** Функционально корректны и консистентны
   (`useVariant`/`relativeTime`), но визуально это одна «тёмная карточка + иконка + заголовок».
   Их ценность — данные/нотация, а не силуэт.
3. **Главная системная проблема — двойной заголовок.** 15 компонентов рисуют `payload.title`,
   и `Slide.vue` тоже рисует заголовок слайда. Плюс компоненты интерполируют `title` через
   `{{ }}`, поэтому мандатные `<em>`-теги рендерятся буквально (в `Slide.vue` — через `v-html`).
4. **Ещё одна системная проблема — выдуманные демо-данные внутри компонентов.** Часть
   компонентов при пустом payload показывает захардкоженный демо-контент (в т.ч. цены `$`),
   что маскирует ошибку авторинга и нарушает правило «только €».
5. **Hardcoded surfaces** нарушают правило «фон только через вариант» в 8 компонентах
   (`bg-bg-surface`/`bg-bg-base` внутри контента).
6. **Motion не унифицирован**: часть компонентов читает `motion` из `useVariant`, часть
   хардкодит длительности (`defaultDelay`, `500ms`, `idx*300`).

---

## 3. Кластеры дублей (главный анти-слоп сигнал)

| Кластер | Компоненты | Вердикт |
|---|---|---|
| Таблицы | `SpecTable` ≈ `ValuesTable`; частично `ModernTable`, `ComparisonTable` | `ValuesTable` = `SpecTable` с 3 колонками → нужен один параметризуемый `NotationTable` |
| Метрик-карточки | `KpiDashboard` ≈ `InfographicCards`; `CircularGauge`, `AnimatedStatsSlide` | один архетип карточки/доната, разные данные |
| Таймлайны | `Roadmap`, `TimelineEras`, `SustainabilityTimeline`, `StepByStep`, `ProcessFunnel` | `TimelineEras` ≈ desktop-ветка `Roadmap`; `SustainabilityTimeline` ≈ `StepByStep` |
| Node-link | `KnowledgeGraph` ≈ `MapVisualization` (почти строка-в-строку) | слить в один `NodeFlow` с layout `radial`/`coords` |
| Крупный текст | `QuoteCard` ≈ `DefinitionBlock` | развести или оставить один |
| Q&A | `FlashCards` ≈ `QuizSlide` | разные механики (flip vs multiple choice) — допустимо |
| Bento | `OrganicGrid` ≈ `BentoGridGallery` | один bento с разными span-картами |

**Генерик-рецепт** (одинаковые до контента): `SpecTable`, `ValuesTable`, `TeamGrid`,
`StepByStep`, `SustainabilityTimeline`, `TimelineEras`, `KpiDashboard`, `CircularGauge`,
`OrganicGrid`, `PricingTable` + оригинальный `InfographicCards`.

---

## 4. Технические проблемы (file:line)

### 4.1 Hardcoded цвета / surfaces
- `ui/ReceiptCard.vue:65,68,134` — `bg-[#F8FAFC]`; `:86,95,103` `red-600`; `:73-74,85,129` `slate-*`; `:21` default `currency:'$'` (нарушает €).
- `ui/TerminalMockup.vue:36-62,184,191` — inline hex синтаксиса; `:206-214` hex-fallback скроллбара.
- `ui/ProductCard.vue:83-85` — ремап legacy-hex; `:219` `bg-bg-surface`.
- `bg-bg-base`/`bg-bg-surface` внутри контента: `Roadmap:144,243`, `NetworkWaterfall:132-136`,
  `MetricScales:91`, `ModernTable:63,84,96,173`, `ComparisonTable:113`, `MediaSlide:25,143`,
  `BeforeAfterSlide:14,18`.
- `slides/PortraitLampSlide.vue:140` — белый блик `rgba(255,255,255,0.12)` (допустимый материал).

### 4.2 Мёртвый код / CSS
- `ui/ArchitectureDiagram.vue:716-742` — неиспользуемые `@keyframes`/классы.
- `ui/ProcessFunnel.vue:204-220` — мёртвые `@keyframes flow-h/v` + пустые классы.
- `tailwind.config.js:99-113` — глобальный `gradient-x ... infinite` (латентный).
- `ui/ModernTable.vue:35-36` — поле `focus` задокументировано как no-effect.
- `ui/Roadmap.vue:29` dead `isVisible`; `:105` `ref="el"` без `el`; `:87` опечатка `step.startTime` (убивает scale-эффект).
- `ui/PremiumChecklist.vue:70` `ref="el"` без `el`; `ui/InteractiveArchitecture.vue:29` `injectedTime` unused.

### 4.3 Анимации
- `slides/OutroSlide.vue:56-67` — `animation: fadeInUp` на mount (не от `relativeTime`) → риск в seek/рендере.
- `slides/MediaSlide.vue:24` — `<video autoplay loop muted>`; `loop` неограничен, `autoplay` не seek-safe.
- Найденные в метрике `infinite` у `TimelineSlide`/`MapVisualization` — **в комментариях**, не в CSS (проверено).

### 4.4 Мобильный
- Нет `mobile`-prop: `ui/ReceiptCard.vue`, `ui/MetricScales.vue`, `slides/MediaSlide.vue`.
- Объявлен, но не используется как логика (полагаются на `md:`): `KpiDashboard`, `TeamGrid`,
  `FlashCards`, `KnowledgeGraph`, `QuoteCard`, `MapVisualization`, `CircularGauge`,
  `SustainabilityTimeline`, `QuizSlide` и др.

### 4.5 Доступность
- `ui/InteractiveArchitecture.vue` — canvas-drag/зум/закрытие без `aria-label`, нет клавиатуры.
- `slides/QuizSlide.vue:76-100` — варианты `<div>`, нет `role="radio"`/`aria-checked`, верный ответ только цветом.
- `ui/GanttChart.vue:82-93` — прогресс только шириной/цветом.
- Нет `alt`/`@error`: `TeamGrid:69`, `QuoteCard:60`, `HistoricalCompare:76`.
- `slides/EndMarkerSlide.vue:3-6` — SVG без `role="img"`.

### 4.6 Пустые состояния и «выдуманные» дефолты
- Нет пустого состояния (пустой бокс/сетка): все 18 новых + `StatsBarChart`, `MetricScales`.
- Наоборот, захардкоженный демо-payload (опасно): `ProductCard:13-62`, `StatsBarChart:31-39`,
  `BentoGridGallery:11-15`, `MetricScales:14-19`, `InfographicCards:13-15`, `CrmCardSlide:25-36`.
- Хорошо сделано: `ArchitectureDiagram:710-712` (placeholder), `BrowserMockup:30-38` (fallback item),
  `MediaSlide:78-81` (error). → взять за образец.

### 4.7 Не унифицирован motion
- `FlashCards:22` (500ms), `KnowledgeGraph:51-52` (400/600ms), `DefinitionBlock:91` (`idx*300`),
  `QuizSlide:13` (`reveal_time` 4000), `BentoGridGallery:8`/`ProductCard:10`/`StatsBarChart:18`
  (`defaultDelay`) — вместо `motion.appear_ms/stagger_ms`.

---

## 5. UX-проблемы

1. **Двойной заголовок** (см. §2.3) — самый заметный дефект при авторинге.
2. **`<em>`-контракт противоречив**: `Slide.vue:19` (`v-html`) vs компоненты (`{{ }}`) → literal `<em>`.
3. **Разнобой масштаба заголовка**: `text-4xl` (Slide) vs `text-2xl md:text-3xl` (новые) vs
   `text-3xl md:text-4xl` (`DefinitionBlock`) vs `text-xl md:text-3xl` (`QuoteCard`).
4. **Разнобой паддингов/радиусов/гапов**: `CrmCardSlide:48` дублирует padding классом и
   `var(--item-padding)`; кнопки хардкодят `rounded-xl/rounded-lg`; гапы `3/4/5/6`.
5. **Форсирование layout**: `ReceiptCard:30-32`, `ChatMockup:38-40` вызывают `setSlideLayout('row')` —
   побочный эффект в setup, недокументирован.
6. **Риски переполнения** (после правок 18 новых — чисто, остальное):
   `TimelineEras:67`/`StepByStep:85` `repeat(n,1fr)` сжимается при 6+; `GanttChart:105` milestone
   `nowrap`; `KnowledgeGraph:93` пилюли `nowrap`; `MapVisualization:105` подписи без клампа по краям;
   `FlashCards:65` фикс `200px` (длинный `back` обрежется); `ReceiptCard:65` `w-80`/`rotate-2`/`mb-12`
   без реflow; `TerminalMockup:171` фикс `500px`.
7. **Hover-эффекты** (`StatsBarChart:194`, `ProductCard`, `OutroSlide:21`) в видео не работают —
   безвредно, но в редакторе создаёт ожидание интерактива.

---

## 6. Конкретные баги (P0)

| # | Файл:строка | Что | Эффект |
|---|---|---|---|
| 1 | `ui/InteractiveArchitecture.vue:629` | `isPlaying` не объявлен, но используется в шаблоне | runtime warning; ветка «centered while playing» мертва |
| 2 | `slides/AdvancedVideoSlide.vue:24` | `useVariant(..., 'AdvancedVideoPlayer')` вместо `'AdvancedVideoSlide'` | per-component override в `style_variants` не применяется |
| 3 | `slides/CrmCardSlide.vue:109` | `var(--text-on-primary)` — токена нет | цвет текста кнопки падает в fallback |
| 4 | `ui/KpiDashboard.vue:85` | `w-4.5 h-4.5` — нет в шкале Tailwind | размер иконки не применяется |
| 5 | `ui/MapVisualization.vue:66` | статический `<pattern id="map-grid">` | дубли id при нескольких слайдах → bleed паттерна |

Минорные: `ui/ArchitectureDiagram.vue:349` `Math.random()` для uid (лучше счётчик);
`slides/PortraitLampSlide.vue` — `lamp_side`/`image_position` объявлены, но игнорируются (`:74`).

---

## 7. Приоритетный backlog (документировано, НЕ реализовано)

### P0 — баги и нарушения инвариантов
1. `InteractiveArchitecture` — объявить/удалить `isPlaying`.
2. `AdvancedVideoSlide` — исправить slug варианта.
3. `CrmCardSlide` — `--text-on-primary` → `--text-on-color`.
4. `KpiDashboard` — `w-4.5` → `w-4`/`w-5`.
5. `ReceiptCard` — токены вместо `#F8FAFC`/`slate`/`red`, `currency: '€'`, добавить `mobile`.
6. `MediaSlide` — `mobile` prop, seek-driven видео вместо `loop autoplay`, MIME-детект (`.mp4/.webm/.mov`).
7. `OutroSlide` — детерминированный reveal от `relativeTime`.

### P1 — системные контракты
8. **Единый заголовок**: убрать `payload.title` из дата-компонентов; заголовок — только `Slide.vue`.
   Обновить `seed_components.py`/схемы и `AGENTS.md`.
9. **`<em>`-контракт**: либо компоненты рендерят свой `title` через `v-html`, либо запретить `<em>` вне `Slide.vue`.
10. **Политика пустых состояний**: общий `EmptyState`; убрать/флаг `demo` для выдуманных дефолтов.
11. **Унификация motion**: везде `useVariant().motion`.
12. **Фон только через вариант**: заменить hardcoded surfaces в 8 компонентах.

### P2 — дедупликация и качество
13. Слить `ValuesTable`→`NotationTable`, `KnowledgeGraph`+`MapVisualization`→`NodeFlow`,
    `OrganicGrid`→`BentoGridGallery` (или параметризовать).
14. Капнуть/перенести переполнения: `repeat(n)` сетки, milestone/label wrap, clamp подписей карты.
15. Доступность: `aria`/`role`/`alt` (InteractiveArchitecture, QuizSlide, Gantt, TeamGrid, QuoteCard).
16. Мёртвый код: keyframes/классы/`focus`/`ref="el"`/`step.startTime`/`hexToRgb`.

Порядок внедрения: P0 → P1 §8–9 (вместе с Ф1 нового плана) → §10–12 → P2.
**Важно:** §8–9 меняют контракт данных (payload/schema/manifest) — их нельзя делать без
синхронного обновления `AGENTS.md` и переобучения генераторов.

---

## 8. Что сделано хорошо (не ломать)

- `useVariant` + токены дают адаптацию под 6 тем/вариантов без правки кода — подтверждено на
  `tech/classic/industrial/educational/derevnya/diademas`.
- Детерминизм: нет `requestAnimationFrame`, `Math.sin`-циклы вместо `infinite`, `transform/opacity`.
- Оригинальные «сложные» компоненты — реально уникальный DOM (canvas, мини-карта, печатная машинка,
  Shiki, chrome браузера, Ken Burns, арочный оклад + лампадка, snake-roadmap).
- `seed/generate/manifests` + `check_consistency` — надёжный конвейер, дрейфа нет.

---

## 9. Итоговый вердикт

- **Функционально:** 50/50 валидны, коллекция рендерица в 6 темах, критичных поломок — 5 (P0, точечные).
- **Дизайн:** ядро сильное; 18 новых — корректные, но «плоские» по силуэту и частично дублируют друг друга.
- **Системно:** три контрактных долга (двойной заголовок + `<em>`, выдуманные дефолты, hardcoded фон/motion).
- **Изменений в существующие компоненты не вносилось** (кроме 18 новых в рамках предыдущей задачи).
  Все правки — по согласованию, порциями P0→P1→P2, чтобы не «раздробить поведение».
