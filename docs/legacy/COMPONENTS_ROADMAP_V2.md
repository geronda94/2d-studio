# COMPONENTS_ROADMAP_V2 — расширение на строительство / образование / B2B / промышленность

> Статус: стратегия. Ничего из этого документа ещё не реализовано.
> Предыдущая карта: `docs/COMPONENTS_ROADMAP.md` (18 компонентов, реализованы → 50 в движке).
> Аудит текущего состояния: `docs/COMPONENT_AUDIT.md`.
>
> Цель: **+42 компонента** (10 общих примитивов + 32 доменных архетипа) без «нейрослопа» —
> без одинаковых карточек «иконка + цифра + подпись» и без дублей, которые уже есть в аудите.

---

## 0. Главный принцип: не плодить клоны

Проблема, которую нельзя повторить (см. `COMPONENT_AUDIT.md`, §2): 18 прошлых компонентов
схлопнулись в ~7 визуальных архетипов, а `KnowledgeGraph` и `MapVisualization` почти
строка-в-строку идентичны. Если добавить ещё 42 «карточки», движок превратится в кашу.

Поэтому новая архитектура — **двухуровневая**:

```
Tier 0  ПРИМИТИВЫ (общие, не доменные)     10 шт
        Pareto, Waterfall, S-Curve/EVM, ControlChart(SPC), RadarProfile,
        HeatmapMatrix, QuadrantMatrix, CohortGrid, NodeFlow, NotationTable

Tier 1  ДОМЕННЫЕ АРХЕТИПЫ (композиции примитивов + метафора)   32 шт
        Строительство 8 · Образование 8 · Промышленность 8 · B2B 8
```

Правило: доменный компонент **не пишет свой график заново** — он оборачивает примитив
и добавляет доменную семантику (единицы, нотацию, подписи, порядок). Дубль запрещён
на этапе ревью: два компонента не могут иметь одинаковый `family` + одинаковый layout.

---

## 1. Тест на «нейрослоп» (обязателен для каждого нового компонента)

Компонент проходит приёмку только если отвечает «да» на всё:

1. **Узнаваем в миниатюре 120×68 px** без текста — у него есть уникальный силуэт/мотив.
2. **Правильный тип графика/нотации** для данных (Парето — сортированное убывание,
   S-curve — кумулятив, SPC — UCL/LCL, OEE — 3 столпа, I/R/M/A — символы, а не проценты).
3. **Нет «декоративного шума»**: eyebrow-плашка над каждым заголовком, accent-полоска
   у каждой карточки, курсив на последнем слове — запрещены как приём по умолчанию.
4. **Нет выдуманных данных по умолчанию** (никаких `$49`/демо-массивов внутри
   компонента — только явный `demo: true`).
5. **Реальные единицы**: € (только!), м², м³, %, ‰, ppm, ч, т, LTIFR, TRIR, OEE, SPI/CPI, DOK.
6. **Сформированные пустое и вырожденное состояние** (0 элементов, 1 элемент, 9999999).
7. **Один смысловой акцент** — компонент отвечает на один вопрос, а не «дашборд всего».
8. **Детерминирован** от `relativeTime`, только `transform`/`opacity`, `motion` из `useVariant`.
9. **Заголовок не дублируется**: `payload.title` в дата-компонентах **отсутствует** —
   заголовок рисует `Slide.vue` (см. §3).
10. **Доступность**: смысл не передаётся только цветом (есть подпись/значение/иконка).

---

## 2. Стандарт компонента v2 (контракт)

Отличия от v1 (устраняют системные болячки из аудита):

| Аспект | v1 (как было) | v2 (как делать) |
|---|---|---|
| Заголовок | часть компонентов рисует свой `title` (`{{ }}`) → двойной заголовок и сломанный `<em>` | дата-компонент **не рисует** заголовок; `Slide.vue` владеет h1/`<em>` |
| Заголовок в payload | `title`/`subtitle` у 15 компонентов | убрать из новых; максимум `label` (короткая метка блока) |
| Данные по умолчанию | захардкоженные демо-массивы (`ProductCard`, `StatsBarChart`…) | компонент умеет пустое состояние; демо — только `demo: true` |
| Фон | иногда `bg-bg-surface`/`bg-bg-base` | только `var(--item-*)` / `var(--surface-*)` |
| Ритм | локальные `500/400/300` мс | `motion.appear_ms` / `stagger_ms` / `count_ms` |
| Мобильный | Tailwind `md:` без явного `mobile` | явный `mobile` prop + 3 контрольные ширины |
| Варианты | `variant` = форма/материал | то же + опциональный `density: compact\|comfortable\|board` |
| Метаданные | `manifest` свободным текстом | `manifest` + поле `family` (для контроля дублей) + domain-теги |
| Доступность | частично | обязательные `aria-label`/`role` для интерактивных и `alt`/fallback для медиа |
| Нотация | — | поле `notation` описывает доменную нотацию (I/R/M/A, RAG, SPI/CPI, OEE-столпы) |

**Инварианты** (как в v1, не отменяются): данные только из props; цвета только токены
темы; вариант не задаёт цвет; детерминизм от `relativeTime`; регистрация = slug = имя
файла; `seed_components → generate_schemas → generate_examples → seed_manifests`.

Дополнительно к v2:
- **`family`** — строка (`table`, `chart-pareto`, `gantt`, `heatmap`, `node-flow`, `board`,
  `report`, `passport`, `matrix`…). `check_consistency.py` можно расширить проверкой:
  две новые компоненты с одним `family` + одинаковым layout → warning.
- **Empty-state helper** — общий компонент `ui/primitives/EmptyState.vue` (внутренний,
  не в реестре), единый вид «нет данных» с подсказкой полей.
- **`SourceNote`** — общий внутренний примитив для сносок «источник/методика» (борьба
  со слопом №6 из исследования: необоснованные цифры).

---

## 3. Дизайн-язык по доменам (чтобы не было одинаковых карточек)

Каждый домен получает собственный «материал» и мотив, поверх общего `useVariant`:

- **Строительство — «чертёж / стройплощадка».** Мотив: технический чертёж (mono-цифры,
  тонкие размерные линии, штриховки, выноски), статус-штампы, RAG-матрицы. Палитра
  нейтрально-стальная, акценты — из темы. Нотация: м²/м³, €, недели, трейд-коды.
- **Образование — «тетрадь / worksheet».** Мотив: миллиметровая сетка, маркер-хайлайтер,
  аннотации на полях, rubric-чипы, символы I/R/M/A. Нотация: DOK/Bloom-уровни, %, баллы.
- **Промышленность — «control room / andon».** Мотив: статус-лампы, круговые шкалы,
  takt-линия, таймер простоя, 5S. Нотация: OEE (A×P×Q), ppm, MTBF/MTTR, OTIF.
- **B2B — «редакционный меморандум».** Мотив: сноски-источники, аннотации-выноски,
  спокойная типографика, «один слайд = один тезис + доказательство». Нотация: €, NRR,
  CAC/LTV, coverage ratio, burn multiple.

---

## 4. Каталог: Tier 0 — общие примитивы (10)

> Регистрируются как обычные компоненты (можно ставить отдельным слайдом),
> но спроектированы как база для доменных обёрток.

| # | slug | family | Что показывает | Ключевые поля payload |
|---|------|--------|----------------|----------------------|
| P1 | `ParetoChart` | chart-pareto | Убывающие столбцы + кумулятивный % (80/20), подсветка Vital Few | `items[] (label,value)`, `threshold` (80), `value_suffix`, `cumulative_label` |
| P2 | `WaterfallChart` | chart-waterfall | Мост «откуда → куда»: +/- столбцы и итог | `start_label,start_value`, `steps[] (label,delta,type)`, `end_label,value_prefix` |
| P3 | `SCurve` | chart-evm | Кумулятивные PV/EV/AC + разрывы CV/SV, SPI/CPI | `periods[]`, `pv[]`, `ev[]`, `ac[]`, `show_index` |
| P4 | `ControlChart` | chart-spc | X̄/R-карта: линия, UCL/LCL, выбросы, тренд | `points[]`, `mean`, `ucl`, `lcl`, `violations[]`, `unit` |
| P5 | `RadarProfile` | chart-radar | 6–9 компетенций, 2 наложенных полигона | `axes[]`, `series[] (label,color,values[])`, `max` |
| P6 | `HeatmapMatrix` | heatmap | Матрица R×C с уровнями (0–4 / RAG / I/R/M/A) | `rows[]`, `cols[]`, `cells[][]`, `scale` (rag/irms/bloom), `legend` |
| P7 | `QuadrantMatrix` | matrix | 2×2/ABC-матрица с пузырями | `axes_x`, `axes_y`, `points[] (label,x,y,size,color)`, `quadrant_labels[]` |
| P8 | `CohortGrid` | heatmap-cohort | Когортный треугольник (retention/NRR по периодам) | `cohorts[]`, `periods[]`, `values[][]`, `metric` |
| P9 | `NodeFlow` | node-flow | Направленный поток узлов (процесс/логистика/VSM) с временем | `nodes[] (id,label,meta,status)`, `edges[] (from,to,label,duration)`, `layout` |
| P10 | `NotationTable` | table-notation | Иерархическая таблица со сворачиванием, subtotal-строками и правым выравниванием чисел | `columns[]`, `groups[] (label,rows[])`, `subtotals`, `unit` |

Общие поля примитивов: `variant`, `density`, `source_note` (сноска-источник), `demo`.

Примечание: `NodeFlow` — правильная замена дублю `KnowledgeGraph`/`MapVisualization`
(один движок раскладки: `radial` / `coords` / `layered`). Существующие два компонента
**не трогаем** сейчас, но помечаем как кандидатов на слияние в аудите.

---

## 5. Каталог: Tier 1 — доменные архетипы (32)

### 5.1 Строительство (8)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| C1 | `BoqSmeta` | NotationTable | Ведомость объёмов работ: разделы → код → ед. → кол-во → цена → сумма, subtotals, НДС/итог | `sections[] (code,name,rows[])`, `rows[].unit/qty/rate`, `subtotal`, `total`, `currency` |
| C2 | `ObjectPassport` | custom (ID-card) | Паспорт объекта: фото + ключевые ТЭП + статус | `image`, `name`, `address`, `status`, `specs[] (label,value,unit)`, `energy_class` |
| C3 | `FloorPlanZones` | Canvas+hotspots | План этажа/генплан с зонами и легендой (площади/цена) | `plan_image`, `zones[] (x,y,label,area,value,color)`, `legend` |
| C4 | `HandoverMatrix` | HeatmapMatrix | Матрица сдачи: этажи/системы × статус (не начато / в работе / замечания / сдано) | `rows[]`, `cols[] (systems)`, `cells[][]`, `states[]` |
| C5 | `SnagBoard` | board | Punch-list: карточки замечаний по подрядчику/локации/дедлайну, старение | `items[] (id,title,trade,location,severity,due,status,photo)` |
| C6 | `SafetyDashboard` | KPI + Pareto | Охрана труда: leading (инспекции, talks) vs lagging (LTIFR, TRIR), дни без инцидентов | `days_without`, `leading[]`, `lagging[]`, `incidents_by_type[]` |
| C7 | `SiteLogisticsMap` | NodeFlow(coords) | Стройгенплан: краны, дороги, склады, поток материалов | `site_image`, `objects[] (x,y,type,label)`, `flows[] (from,to,label)` |
| C8 | `ChangeOrderLog` | NotationTable + waterfall | Журнал изменений: статус, влияние на бюджет/срок, накопленный эффект | `orders[] (id,title,status,cost_delta,days_delta)`, `cumulative` |

Специфично: C1–C8 все. Переиспользуют: `WaterfallChart` (C8), `HeatmapMatrix` (C4),
`ParetoChart` (C6), `NodeFlow` (C7), `NotationTable` (C1, C8).

### 5.2 Образование (8)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| E1 | `LearningObjectives` | cards+verb | Цели обучения по ABCD: измеряемый глагол, условие, критерий | `objectives[] (verb,behavior,condition,degree,level)` |
| E2 | `BloomLadder` | custom (ladder) | Лестница/пирамида Блума: 6 уровней с глаголами и заданиями | `levels[] (name,verbs[],task,color)`, `active_level` |
| E3 | `LessonArc` | timeline | 5E / I-do–We-do–You-do: фазы с таймингами (таймбоксы) | `phases[] (name,minutes,activity,icon)` |
| E4 | `CurriculumMap` | HeatmapMatrix(irms) | Матрица «курс × результат» с нотацией I/R/M/A | `courses[]`, `outcomes[]`, `map[][]`, `notation:'irms'` |
| E5 | `AssessmentBlueprint` | NotationTable | Blueprint теста: стандарт → DOK → тип → баллы → % от итога | `rows[] (standard,skill,dok,items,points)`, `totals`, `rigor_dist` |
| E6 | `ItemAnalysis` | Pareto + flags | Анализ заданий: % верных, сложность, дискриминация, дистракторы | `items[] (no,pct,difficulty,discrimination,distractors[])`, `flags` |
| E7 | `StudentGrowth` | line+target | Рост: baseline → interim → target, полосы proficiency, рост-стрелка | `points[] (label,value)`, `target`, `bands[]`, `growth` |
| E8 | `TimetableGrid` | custom grid | Расписание: неделя × пара, предмет/аудитория, конфликты | `days[]`, `periods[]`, `cells[][] (subject,teacher,room,color,conflict)` |

Специфично: E1–E8. Переиспользуют: `HeatmapMatrix` (E4), `NotationTable` (E5),
`ParetoChart` (E6).

### 5.3 Промышленность (8)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| M1 | `OeeDashboard` | Gauge + 3 pillars | OEE = A×P×Q, столпы, разбивка потерь, по машинам | `lines[] (name,availability,performance,quality,oee,target)` |
| M2 | `PaceBoard` | Andon board | План vs факт, такт, почасовая накопленная, таймер простоя | `plan`, `actual`, `takt`, `hourly[]`, `stoppage_sec`, `status` |
| M3 | `ShiftHandover` | report | Сменный отчёт: выпуск, простои, качество, персонал, открытые вопросы, подписи | `shift`, `output`, `downtime[]`, `quality`, `labor`, `issues[]`, `signoff[]` |
| M4 | `YamazumiBalance` | stacked bars + takt | Балансировка линии: станции, элементы работ, линия такта, бутылочное горло | `stations[] (name,elements[] (label,sec))`, `takt_sec`, `bottleneck` |
| M5 | `ValueStreamMap` | NodeFlow + time ladder | VSM: материальный/информационный поток, VA/NVA, lead time | `processes[] (name,cycle_time,wait_time)`, `flows[]`, `va_time`, `lead_time` |
| M6 | `MachineStatusBoard` | tile grid | Статусы оборудования (работа/простой/наладка), MTBF/MTTR | `machines[] (name,state,since,mtbf,mttr)` |
| M7 | `MaintenanceBoard` | board/calendar | ППР и заявки: просроченные, калибровка, запчасти, тренд MTTR | `orders[] (id,asset,type,due,status,assignee)`, `overdue` |
| M8 | `AbcXyzMatrix` | QuadrantMatrix | ABC/XYZ по ценности и волатильности, классы, пороги | `items[] (sku,value,variability,class)`, `thresholds` |

Специфично: M1–M8. Переиспользуют: `QuadrantMatrix` (M8), `NodeFlow` (M5),
`ParetoChart` (потери, можно в M1).

### 5.4 B2B (8)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| B1 | `PipelineBoard` | staged board/funnel | Воронка по стадиям: кол-во, сумма, конверсия, velocity, coverage | `stages[] (name,count,value,conversion,aging)`, `coverage` |
| B2 | `MarketSizing` | nested/TAM | TAM/SAM/SOM: слои, рост, доля сегмента | `layers[] (name,value,growth)`, `currency`, `source_note` |
| B3 | `RevenueWaterfall` | WaterfallChart | Мост выручки: prior → new → expansion → churn → current | `start`, `steps[] (label,delta,type)`, `end` |
| B4 | `CohortRetention` | CohortGrid | Когорты logo/revenue retention, NRR/GRR, churn | `cohorts[]`, `values[][]`, `metric` (logo/nrr) |
| B5 | `OrgChart` | custom tree | Оргструктура: роли, подчинение, headcount по функциям | `nodes[] (id,name,title,headcount,children[])`, `layout` |
| B6 | `UnitEconomics` | KPI + timeline | Юнит-экономика: CAC, LTV, payback-мес, gross margin, magic number | `metrics[] (label,value,unit,target)`, `payback_months` |
| B7 | `UseOfFunds` | allocation donut/bars | Распределение инвестиций + привязка к вехам | `buckets[] (label,amount,color)`, `milestones[]`, `total` |
| B8 | `JourneyMap` | stages + touchpoints | Клиентский путь: стадии, точки контакта, боли, метрики | `stages[] (name,touchpoints[],pains[],kpi)` |

Специфично: B1–B8. Переиспользуют: `WaterfallChart` (B3), `CohortGrid` (B4).

---

## 6. Приоритизация и фазы

Критерий приоритета: **частота в реальных питчах × уникальность × переиспользуемость**.

| Фаза | Состав | Почему так |
|------|--------|-----------|
| **Ф1 — фундамент (10)** | Tier 0: P1–P10 | Без примитивов доменные компоненты снова станут клонами. Даёт 80% новых графиков. |
| **Ф2 — Строительство (8)** | C1–C8 | Самая широкая вертикаль (заказчики, тендеры, сдача). C1/C2/C4 — must-have. |
| **Ф3 — Промышленность (8)** | M1–M8 | Высокий чек, уникальные нотации (OEE/VSM/SPC), сильное демо. |
| **Ф4 — Образование (8)** | E1–E8 | Массовый трафик, шаблоны/курсы; много переиспользований Heatmap/Notation. |
| **Ф5 — B2B добор (8)** | B1–B8 | Закрывает дыры инвеста/RevOps (pipeline, NRR, waterfall). |

Порядок: **Строительство → Промышленность → Образование → B2B** (по цене/скорости сделок),
но фундамент всегда первым.

---

## 7. Оценка объёма (почему 42, а не 30 и не 50)

- 30 было бы мало: 4 домена × минимум 6–8 архетипов = 24–32 только доменных, плюс примитивы.
- 50+ грозит дублями (что уже случилось с прошлыми 18).
- **42 = 10 примитивов + 32 доменных** — покрывает 4 домена с запасом на композиции,
  при этом каждый компонент либо примитив, либо уникальная нотация.

Ориентир LOC: примитивы ~150–300 строк, доменные ~120–250. Итого ~8–11k строк Vue.

---

## 8. Метрики успеха (как поймём, что не слоп)

- [ ] В миниатюре каждый из 42 узнаётся без текста (тест «thumbnail 120×68»).
- [ ] Ноль новых дублей: `family` + layout уникальны (проверка скриптом).
- [ ] Ноль hex в новых компонентах; ноль `payload.title`; ноль выдуманных дефолтов.
- [ ] Все проходят `validate?lint=true` (0 errors/warnings) и рендерятся desktop+mobile.
- [ ] Демо-презентации по 4 доменам: строительная смета, урок, цех, инвест-дек.

---

## 9. Anti-goals (что НЕ делаем)

- Не добавляем ещё N вариантов «карточка + иконка + цифра».
- Не дублируем Timeline/Gantt/Radar/Heatmap по доменам — только композиция примитивов.
- Не делаем «дашборд всего» — один компонент = один вопрос.
- Не оставляем захардкоженные демо-данные/валюты внутри компонентов.
- Не тащим внешние карты/тайлы и API — только детерминированные данные из payload.
- Не трогаем существующие 50 компонентов в рамках этой карты (см. аудит — отдельное решение).

---

## 10. Связь с аудитом

`docs/COMPONENT_AUDIT.md` фиксирует, что нужно починить в существующих 50. Часть
рекомендаций пересекается с этим планом (единый `NodeFlow`, отказ от двойного заголовка,
motion из `useVariant`) — их стоит внедрять **одновременно** с Ф1, чтобы новые компоненты
сразу строились по v2-контракту, а старые чинились без «раздробления поведения».

---

## 11. Статус реализации (обновлено)

**Готово и проверено:**

- **P0-фиксы существующих компонентов:** `InteractiveArchitecture` (isPlaying),
  `AdvancedVideoSlide` (slug варианта), `CrmCardSlide` (`--text-on-color`),
  `KpiDashboard` (`w-5 h-5`), `MapVisualization` (CSS-сетка вместо SVG pattern id).
- **Tier 0 — 10 примитивов:** `ParetoChart`, `WaterfallChart`, `SCurve`, `ControlChart`,
  `RadarProfile`, `HeatmapMatrix`, `QuadrantMatrix`, `CohortGrid`, `NodeFlow`, `NotationTable`.
- **Tier 1 — 32 доменных архетипа:** Строительство (8), Образование (8), Промышленность (8), B2B (8).
- **Библиотека:** 92 компонента (registry = DB = 92, `.vue` = 123), `check_consistency` — OK.
- **Валидация:** все 42 новых payload'а (`default_payload` + `example`) проходят
  `POST /components/{slug}/validate?strict=true&lint=true` — 0 ошибок, 0 warnings.
- **QA кадров:** десктоп 1920×1080 и мобайл 450×800 — корень всех 42 компонентов
  укладывается в кадр (без выхода за границы и наложения на заголовок).
  Скриншоты: `qa-roadmap/t0-*.png`, `qa-roadmap/m-t0-*.png`, `qa-roadmap/d1-*.png`.
- **Демо-презентации:** `/p/56` (IT2B, tech) и `/p/57` (Diademas, diademas) — по 32 слайда.

**Известные ограничения:**

- Табличные компоненты (`BoqSmeta`, `ChangeOrderLog`) при очень больших payload'ах
  скроллят контент внутри bounded-области (кадр не ломается).
- Видео-рендер в текущем окружении не запускается: в backend-контейнере не задан `$DISPLAY`
  (нужен Xvfb/headful). Компоненты к рендеру готовы (детерминированные анимации от
  `inject('relativeTime')`).

**Артефакты кода:**

- `scripts/_domain_v2.py` — payload'ы 32 доменных компонентов (источник для `seed_components.py`).
- `scripts/build_domain_v2_draft.py` — сборка демо-презентаций `/p/56`, `/p/57`.

---

## 12. Стандарт движения (motion system) — план

Зафиксирован отдельным документом: **`docs/MOTION_STANDARD.md`**. Кратко:

- Инварианты: время только из `inject('relativeTime')`; анимируем только `transform`/`opacity`;
  без `requestAnimationFrame`, `infinite`, `<animate>`; детерминизм (seek == realtime).
- Ритм — из `style_variants.config.motion` (`appear_ms`, `stagger_ms`, `count_ms`), не хардкод.
- Единый словарь паттернов по архетипу: карточки — rise+fade; бары — grow; линии — draw;
  матрицы — cascade; числа — count-up; потоки — edge→node; образы — gentle fade.
- Единый easing-набор (easeOutCubic / easeInOutQuad / linear).
- Composable `useMotion(relativeTime, motion)` → `reveal / grow / draw / count / stagger / cascade`
  вместо копипасты `ease(clamp01(...))` в каждом компоненте.
- Ретрофит: Tier 0 → доменные → старые; приёмка — покадровый аудит + скриншот-диф seek/realtime.

## 13. Второй канал: православный (Diademas)

Отдельный roadmap: **`docs/ROADMAP_ORTHODOX.md`** — 40 новых компонентов (Писание, святые,
наука и вера, философия, психология души, отношения, история, личности, законы-параллели)
плюс 2 уже существующих (`PortraitLampSlide`, `TimelineSlide`) = 42 под канал.
План соблюдает контракт v2 и стандарт движения; описаны дизайн-язык, карта переиспользования
существующих 92 компонентов, фазы P0/P1/P2 и anti-goals.
