# Компоненты для презентаций — дорожная карта

> Текущий статус: **50 компонентов** в продакшене (32 + 18 из этого роадмапа).
> Все 18 новых (P1–P4) реализованы; целевое покрытие достигнуто.
>
> Сверх плана реализованы (перенос из прототипа Diademas): `PortraitLampSlide`,
> `TimelineSlide`. Механизм создания — `docs/COMPONENT_PIPELINE.md`.
>
> Реализовано: `SpecTable`, `KpiDashboard`, `GanttChart`, `TeamGrid`, `PricingTable`,
> `FlashCards`, `QuizSlide`, `StepByStep`, `DefinitionBlock`, `KnowledgeGraph`,
> `TimelineEras`, `QuoteCard`, `MapVisualization`, `HistoricalCompare`,
> `CircularGauge`, `SustainabilityTimeline`, `ValuesTable`, `OrganicGrid`.
> Демо-черновики: `/p/46` (IT2B, variant tech) и `/p/47` (Diademas, variant diademas).

---

## Существующие компоненты (30)

| slug | Назначение | Универсальность |
|------|-----------|-----------------|
| `ArchitectureDiagram` | Блок-схема: ноды + связи + поток данных | B2B, IT |
| `InteractiveArchitecture` | Интерактивная схема с зумом и подсветкой | B2B, IT |
| `EcosystemSlide` | Центральный элемент + ноды-интеграции | B2B |
| `ChatMockupSlide` | Мокап переписки/чат-бота | B2B, IT |
| `TerminalMockup` | Мокап терминала | IT |
| `CodeExplain` | Разбор кода построчно | IT, обучение |
| `CodeComparisonSlide` | Два окна кода (до/после) | IT |
| `ComparisonTable` | Таблица с галочками/крестиками | Универсал |
| `ModernTable` | Таблица с иконками/трендами/статусами | Универсал |
| `NetworkWaterfall` | Waterfall сетевых запросов | IT |
| `ProductCard` | Карточки товара/тарифа | B2B, продажи |
| `ReceiptCard` | Карточка чека | Продажи |
| `PremiumChecklist` | Чеклист с иконками | Универсал |
| `ProcessFunnel` | Воронка этапов | B2B, продажи |
| `Roadmap` | Дорожная карта этапов | Универсал |
| `InfographicCards` | Карточки с цифрами/трендами | Универсал |
| `StatsBarChart` | Столбчатая диаграмма | Универсал |
| `MetricScales` | Шкалы метрик (проценты) | Универсал |
| `ProgressScalesSlide` | Шкалы прогресса | Универсал |
| `AnimatedStatsSlide` | Крупные метрики с ростом | Универсал |
| `BentoGridGallery` | Bento-сетка плиток | Универсал |
| `BrowserMockup` | Мокап браузера со скроллом | IT, продажи |
| `BeforeAfterSlide` | До/после (два окна) | Универсал |
| `MediaSlide` | Медиа с зумом/панорамой | Универсал |
| `AdvancedVideoSlide` | Скринкаст с рамкой | IT |
| `CrmCardSlide` | Карточка клиента в CRM | B2B |
| `RoiCalculatorSlide` | ROI-калькулятор | B2B, продажи |
| `TechStackSlide` | Сетка технологий | IT |
| `OutroSlide` | Финальная заставка | Универсал |
| `EndMarkerSlide` | Служебный маркер конца | Системный |

---

## Новые компоненты (18)

### 🔴 Приоритет 1 — B2B / продажи (5 компонентов)

Самые востребованные в IT2B и коммерческих предложениях.

| # | slug | Название | Описание | Ключевые поля payload |
|---|------|----------|----------|----------------------|
| 1 | `SpecTable` | Таблица спецификаций | Двухколоночная таблица «параметр → значение» с иконками и выделением ключевых строк | `columns`, `rows`, `highlight_rows`, `variant` |
| 2 | `KpiDashboard` | KPI-дашборд | Сетка из 4-6 крупных метрик с трендами,迷你-графиками и подписями | `metrics[].value`, `metrics[].label`, `metrics[].trend`, `metrics[].sparkline` |
| 3 | `GanttChart` | Диаграмма Ганта | Горизонтальные полосы этапов с зависимостями, milestone-маркеры | `tasks[].name`, `tasks[].start`, `tasks[].end`, `tasks[].progress`, `milestones` |
| 4 | `TeamGrid` | Команда | Сетка карточек людей: фото, имя, роль, контакты | `members[].photo`, `members[].name`, `members[].role`, `members[].contacts` |
| 5 | `PricingTable` | Тарифы | 2-4 карточки тарифов с ценами, чеклистом возможностей, CTA-кнопкой | `plans[].name`, `plans[].price`, `plans[].features`, `plans[].highlighted` |

### 🟡 Приоритет 2 — Обучение (5 компонентов)

Огромный трафик (шаблоны для студентов, лекции, курсы).

| # | slug | Название | Описание | Ключевые поля payload |
|---|------|----------|----------|----------------------|
| 6 | `FlashCards` | Фронт-カード | Карточки с вопросом/ответом, анимация переворота по таймлайну | `cards[].front`, `cards[].back`, `cards[].start_time` |
| 7 | `QuizSlide` | Викторина | Вопрос + 2-4 варианта ответа с подсветкой правильного | `question`, `options[].text`, `options[].correct`, `explanation` |
| 8 | `StepByStep` | Пошаговый процесс | Вертикальный или горизонтальный поток шагов с нумерацией и описаниями | `steps[].number`, `steps[].title`, `steps[].description`, `steps[].icon` |
| 9 | `DefinitionBlock` | Определение | Крупный термин + определение + примеры использования | `term`, `definition`, `examples`, `related_terms` |
| 10 | `KnowledgeGraph` | Граф знаний | Ноды-концепции с связями «зависит от / связано с», визуальная карта | `concepts[].id`, `concepts[].label`, `concepts[].connections` |

### 🟢 Приоритет 3 — История (4 компонента)

Визуально впечатляющие, хорошо для маркетинговых демо.

| # | slug | Название | Описание | Ключевые поля payload |
|---|------|----------|----------|----------------------|
| 11 | `TimelineEras` | Хронология эпох | Горизонтальная шкала с эпохами, иконками, краткими описаниями | `eras[].name`, `eras[].period`, `eras[].icon`, `eras[].color`, `eras[].description` |
| 12 | `QuoteCard` | Цитата | Крупная цитата с автором, должностью, фото; стилизация под печать/гравюру | `quote`, `author`, `role`, `photo`, `source` |
| 13 | `MapVisualization` | Карта | Интерактивная или статичная карта с точками, зонами, метками | `map_type`, `points[].lat`, `points[].lng`, `points[].label`, `zones` |
| 14 | `HistoricalCompare` | Сравнение эпох | Два изображения/блока «до и после» с.timeline-переходом и комментариями | `before.image`, `before.caption`, `after.image`, `after.caption`, `transition_style` |

### 🔵 Приоритет 4 — Эко / философия (4 компонента)

Узкая ниша, но визуально уникальная.

| # | slug | Название | Описание | Ключевые поля payload |
|---|------|----------|----------|----------------------|
| 15 | `CircularGauge` | Круговая метрика | Кольцевой прогресс-бар с центровым числом и подписью; анимация заполнения | `value`, `max`, `label`, `color`, `icon` |
| 16 | `SustainabilityTimeline` | Шкала устойчивости | Вертикальная шкала с этапами перехода к устойчивому развитию | `milestones[].year`, `milestones[].event`, `milestones[].impact` |
| 17 | `ValuesTable` | Таблица ценностей | Столбцы «ценность → практика → результат» с иконками и цветовой кодировкой | `columns`, `rows`, `color_scheme` |
| 18 | `OrganicGrid` | Органическая сетка | Нестандартная сетка плиток с неправильными формами, скруглениями, наложением | `items[].content`, `items[].size`, `items[].position`, `items[].overlay` |

---

## Рефакторинг существующих (через варианты)

Эти компоненты **не нужно создавать с нуля** — достаточно добавить новые варианты отрисовки в `style_variants`:

| Существующий компонент | Новый вариант | Для ниши |
|------------------------|---------------|----------|
| `Roadmap` | `timeline-eras` | История |
| `BeforeAfterSlide` | `historical` | История |
| `ProcessFunnel` | `education-steps` | Обучение |
| `InfographicCards` | `eco-organic` | Эко |
| `ComparisonTable` | `spec-table` | B2B |
| `AnimatedStatsSlide` | `kpi-dashboard` | B2B |
| `ProgressScalesSlide` | `circular-gauge` | Эко |
| `ProductCard` | `team-card` | B2B |
| `PremiumChecklist` | `quiz-options` | Обучение |

---

## Порядок реализации

```
Фаза 1 (2-3 недели):  SpecTable → KpiDashboard → PricingTable → TeamGrid → GanttChart
Фаза 2 (2-3 недели):  FlashCards → QuizSlide → StepByStep → DefinitionBlock → KnowledgeGraph
Фаза 3 (1-2 недели):  TimelineEras → QuoteCard → MapVisualization → HistoricalCompare
Фаза 4 (1-2 недели):  CircularGauge → SustainabilityTimeline → ValuesTable → OrganicGrid
```

Итого: **~8-10 недель** на компоненты. Затем стили/темы → AI → запуск.

---

## Источники вдохновения

- **Gamma** (gamma.app) — референс по UX и генерации
- **Slidesgo** (slidesgo.com) — шаблоны, 1.3M визитов/мес
- **Beautiful.ai** — умные слайды
- **Pitch** — командные презентации
- **Canva** — массовый рынок
