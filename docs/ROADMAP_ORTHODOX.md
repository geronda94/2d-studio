# ROADMAP_ORTHODOX — компоненты для православного канала

Канал: диалог о Боге и святых на стыке **Писания, науки, философии, психологии, истории и
человеческих отношений**. Форматы: шортсы (вертикаль) и широкоформат. Проект-хост: Diademas.

Документ — план расширения библиотеки под этот канал. Соблюдает контракт компонента v2
(`docs/COMPONENTS_ROADMAP_V2.md` §2) и стандарт движения (`docs/MOTION_STANDARD.md`).

---

## 0. Что уже есть (2 компонента)

| slug | Что делает | Почему подходит каналу |
|------|-----------|------------------------|
| `PortraitLampSlide` | Портрет в арочном окладе с подвесной лампадкой | Образ святого/подвижника + слово; лампадка — тёплый акцент |
| `TimelineSlide` | Линия времени, активное событие раскрывается | Житие: постриг → подвиг → преставление |

Этого мало: канал требует разбора Писания, параллелей «наука ↔ вера», шкал страстей/добродетелей,
сравнения эпох, аргументации и т.д. Ниже — **40 новых компонентов** (итого 42 под канал).

---

## 1. Дизайн-язык канала

- **Вариант отрисовки:** расширить `style_variants` новым `orthodox` (или использовать
  существующий `diademas`): тёплое золото/пурпур на пергаменте или глубокой ночи, тонкие
  золотые хайрлайны, радиус 8–10px, мягкое «свечное» свечение (`glow-accent`).
- **Типографика:** серифы (у Diademas уже `EB Garamond` + `Cinzel`) — заголовки, тело; моно —
  только для ссылок на стихи/дат.
- **Цвета — только токены темы** (`var(--color-*)`, `var(--item-*)`, `getHexColor`/`getColorAlpha`).
  Никаких хардкоженных hex. Золото = акцент, но не «всё золотое».
- **Образы:** живопись/иконография из медиа-библиотеки; `object-fit: cover`; без клип-арта,
  без эмодзи. Иконки — Lucide/Heroicons (`lucide:*`, `heroicons:*`).
- **Движение:** сдержанное (см. `MOTION_STANDARD.md` §4, паттерн «иконы/образы» = gentle fade).
  Медленный ритм (`appear_ms ~600`, `stagger_ms ~1200`).

## 2. Тест на «слоп» (обязателен для каждого)

1. Это новый **архетип**, а не «карточка + иконка + цифра»?
2. Нельзя ли собрать из существующего примитива (композиция вместо клона)?
3. Есть ли у компонента **один вопрос**, на который он отвечает?
4. Данные — только из payload, без демо-хардкода и валюты?
5. Ссылки на Писание/источник обязательны там, где есть цитата/тезис.

## 3. Каталог: 40 новых компонентов

Легенда композиции: **[new]** — собственный макет; **→ X** — переиспользует примитив X.

### 3.1 Священное Писание (6)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S1 | `VerseFocus` | [new] | Один стих крупно: текст, ссылка, перевод/оригинал, подсветка слов | `verse`, `reference`, `translation`, `original`, `highlight[]` |
| S2 | `ScriptureParallel` | [new] | Параллельные места в 2–3 колонки (Синодальный / ЦСЯ / оригинал) | `columns[] (label,text)`, `reference` |
| S3 | `ParableExplainer` | [new] | Разбор притчи: образ → символ → смысл → применение | `image`, `title`, `symbols[] (icon,meaning)`, `moral` |
| S4 | `ProphecyFulfillment` | [new] | Пророчество → исполнение (две колонки со связями) | `prophecies[] (text,ref,year)`, `fulfillments[]`, `links` |
| S5 | `GenealogyTree` | [new] | Родословие (патриархи, род Христа) | `nodes[] (id,name,note,children)`, `layout` |
| S6 | `CommandmentBoard` | [new] | Заповеди/блаженства: номер → текст → смысл | `items[] (no,text,meaning,icon)` |

### 3.2 Святые и подвижники (4 + 2 существующих)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S7 | `VirtuesRadar` | → RadarProfile | Профиль добродетелей подвижника vs обычного человека | `axes[]`, `series[] (name,values[])` |
| S8 | `AsceticFeats` | [new] | Подвиги (пост, молитва, бдение, нестяжание) как уровни/иконки | `feats[] (name,icon,level,note)` |
| S9 | `SaintQuote` | → QuoteCard | Изречение святого с портретом и источником | `quote`, `author`, `image`, `source` |
| S10 | `RelicsMap` | → MapVisualization | География святынь/мощей/монастырей | `points[] (x,y,label,type)`, `legend` |
| — | `PortraitLampSlide` | существует | Образ + слово | — |
| — | `TimelineSlide` | существует | Житие по годам | — |

### 3.3 Наука и вера (5)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S11 | `ScienceFaithParallel` | [new] | Открытие ↔ Писание (две колонки со связью) | `pairs[] (science,scripture,note)`, `source` |
| S12 | `CosmologyGenesis` | → ProcessFunnel | Большой взрыв ↔ Дни творения (этапы) | `stages[] (cosmic,biblical,time)` |
| S13 | `SacredNumbers` | [new] | Числа и символизм (7, 40, 12, 3) | `numbers[] (value,meaning,occurrences[])` |
| S14 | `FineTuningScales` | → MetricScales | Антропный принцип: тонкая настройка констант | `constants[] (name,value,tolerance,note)` |
| S15 | `ArchaeologyConfirms` | → ModernTable | Археология подтверждает Писание | `finds[] (artifact,place,year,confirms)` |

### 3.4 Философия и богословие (5)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S16 | `ConceptDiptych` | [new] | Два понятия (сущность/энергия, вера/знание) | `left (title,points[])`, `right (...)`, `note` |
| S17 | `ArgumentStructure` | [new] | Тезис → посылки → вывод → возражение | `thesis`, `premises[]`, `conclusion`, `objection` |
| S18 | `ApologeticsQA` | [new] | Возражение → ответ с источником | `items[] (objection,answer,source)` |
| S19 | `WorldviewMatrix` | → HeatmapMatrix | Сравнение мировоззрений по критериям | `worldviews[]`, `criteria[]`, `map[][]` |
| S20 | `TheologicalSchools` | → RadarProfile | Школы/отцы Церкви: акценты и представители | `schools[] (name,emphasis,representatives[])` |

### 3.5 Психология души (6)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S21 | `PassionsVirtues` | → MetricScales | Парные шкалы: страсть ↔ добродетель | `pairs[] (passion,virtue,level)` |
| S22 | `SoulStructure` | [new] | Структура души: ум / воля / чувства (схема) | `parts[] (name,role,icon)` |
| S23 | `StagesOfSin` | → ProcessFunnel | Развитие греха: помысл → пленение → страсть | `stages[] (name,description,icon)` |
| S24 | `LadderOfVirtues` | → BloomLadder | Лествица добродетелей (восхождение) | `levels[] (name,description,icon)`, `active` |
| S25 | `EmotionHealing` | [new] | Состояния/чувства и их исцеление | `emotions[] (name,cause,remedy)` |
| S26 | `HabitLoop` | → NodeFlow | Петля привычки и духовная замена | `loop[] (stage,spiritual)` |

### 3.6 Взаимоотношения (4)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S27 | `LoveTypes` | [new] | Виды любви: агапэ/эрос/филия/сторге | `types[] (name,greek,meaning,example)` |
| S28 | `FamilyOrder` | [new] | Семья: роли, обязанности, основание | `roles[] (member,role,scripture)` |
| S29 | `ReconciliationPath` | → StepByStep | Путь примирения: шаги | `steps[] (name,description,icon)` |
| S30 | `ChurchAsBody` | → EcosystemSlide | Церковь как тело: центр и служения | `center`, `nodes[]` |

### 3.7 История и цивилизации (5)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S31 | `MoralDecline` | → SCurve | Деградация морали во времени (маркеры переломов) | `periods[]`, `values[]`, `markers[]` |
| S32 | `ValuesOfEpochs` | → TimelineEras | Ценности эпох/цивилизаций | `epochs[] (name,core_values[],artifact)` |
| S33 | `CivilizationCycle` | [new] | Цикл подъёма/упадка: фазы и признаки | `phases[] (name,signs[],duration)` |
| S34 | `ChristianityImpact` | → InfographicCards | Влияние христианства: область → было → стало | `areas[] (domain,before,after)` |
| S35 | `PersecutionWaves` | → TimelineEras | Волны гонений: период, масштаб, место | `waves[] (period,scale,place)` |

### 3.8 Личности (3)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S36 | `FigureCard` | → ObjectPassport | Карточка личности: эпоха, вклад, цитата | `image`, `name`, `years`, `role`, `contribution`, `quote` |
| S37 | `RulerCompare` | → ComparisonTable | Правители: вера / дела / наследие | `rulers[] (name,years,deeds,legacy)` |
| S38 | `InfluenceMap` | → KnowledgeGraph | Кто на кого повлиял (граф) | `nodes[]`, `edges[]` |

### 3.9 Законы и параллели (2)

| # | slug | Композиция | Что показывает | Ключевые поля payload |
|---|------|-----------|----------------|----------------------|
| S39 | `LawParallel` | → ComparisonTable | Физический закон ↔ духовный принцип (посев/жатва, энтропия/благодать) | `rows[] (physical,spiritual,principle)` |
| S40 | `SeedAndSoil` | [new] | Притча о сеятеле как модель: почва → человек → плод | `soils[] (type,icon,outcome)` |

**Итог:** 40 новых + 2 существующих = **42 компонента** под канал.

---

## 4. Карта переиспользования (что уже есть в библиотеке 92)

Не нужно дублировать — канал покрывается композицией:

| Задача канала | Существующий компонент |
|---------------|------------------------|
| Цитата с автором | `QuoteCard` |
| Эпохи/хронология | `TimelineEras`, `TimelineSlide` |
| «До / после» | `HistoricalCompare`, `BeforeAfterSlide` |
| География | `MapVisualization` |
| Профиль по осям | `RadarProfile` |
| Матрица сравнения | `HeatmapMatrix`, `NotationTable`, `ComparisonTable`, `ModernTable` |
| Схема/поток | `NodeFlow`, `ArchitectureDiagram`, `KnowledgeGraph`, `EcosystemSlide` |
| Этапы/воронка | `ProcessFunnel`, `StepByStep` |
| Лестница уровней | `BloomLadder` |
| Шкалы/метрики | `MetricScales`, `ProgressScalesSlide`, `StatsBarChart` |
| Графики | `SCurve`, `WaterfallChart`, `ParetoChart`, `ControlChart` |
| Карточка личности | `ObjectPassport` |
| Образ святого | `PortraitLampSlide` |
| Медиа | `MediaSlide` |

## 5. Фазы

- **Ф0 — фундамент:** variant `orthodox` + токены (золото/пергамент/ночь), `useMotion`
  (см. `MOTION_STANDARD.md`), ретрофит 2 существующих под канал.
- **Ф1 — ядро (P0, 12):** `VerseFocus`, `SaintQuote`, `ParableExplainer`,
  `ScienceFaithParallel`, `CosmologyGenesis`, `PassionsVirtues`, `MoralDecline`,
  `ValuesOfEpochs`, `FigureCard`, `LoveTypes`, `ArgumentStructure`, `LawParallel`.
- **Ф2 — глубина (P1, 14):** `ScriptureParallel`, `ProphecyFulfillment`, `CommandmentBoard`,
  `VirtuesRadar`, `SacredNumbers`, `FineTuningScales`, `WorldviewMatrix`, `ApologeticsQA`,
  `StagesOfSin`, `LadderOfVirtues`, `CivilizationCycle`, `ChristianityImpact`, `RulerCompare`,
  `SeedAndSoil`.
- **Ф3 — полнота (P2, 14):** `GenealogyTree`, `AsceticFeats`, `RelicsMap`, `ArchaeologyConfirms`,
  `ConceptDiptych`, `TheologicalSchools`, `SoulStructure`, `EmotionHealing`, `HabitLoop`,
  `FamilyOrder`, `ReconciliationPath`, `ChurchAsBody`, `PersecutionWaves`, `InfluenceMap`.

## 6. Метрики успеха

- ≥ 80% слайдов канала собираются из 42 компонентов без «пустых кадров».
- Ни один компонент не дублирует существующий примитив (проверка `check_consistency` + ревью).
- Покадровый аудит движения: монотонный рост видимых элементов, финальный кадр полный.
- Демо-презентации: шортс (вертикаль) + широкоформат на одном контенте.

## 7. Anti-goals

- Не делать «иконостас из карточек» — образ дозируется, не заливает слайд.
- Не смешивать эпохи/стили в одном кадре.
- Не caricature: уважительная подача, без клип-арта и эмодзи.
- Цитаты и тезисы — только с источником/ссылкой; без выдуманных «фактов».
- Не тащить внешние API/карты — только данные из payload.

## 8. Связь

- Контракт компонента: `docs/COMPONENTS_ROADMAP_V2.md` §2, §4.4.
- Движение: `docs/MOTION_STANDARD.md`.
- Процесс сборки презентации: `docs/AGENT_PLAYBOOK.md`.

---

## 9. Статус реализации

**Создано и подключено: 40 компонентов** (итого под канал — 42 с двумя существующими).

- Реестр/БД/файлы: `registry = db = 132`, `.vue = 163`, `check_consistency` — OK.
- Все 40 компилируются в Vite (HTTP 200) и проходят
  `POST /components/{slug}/validate?strict=true&lint=true` для `default_payload` и `example`:
  **80/80 блоков, 0 ошибок, 0 warnings**.
- Метаданные: `scripts/_orthodox_meta/<Slug>.json`; сиды — через `scripts/_orthodox_seed.py`
  (подключается в `seed_components.py` и `seed_manifests.py`).
- Демо-презентация: **`/p/59`** «Православный канал: 40 компонентов (Diademas)» (folder 24, variant `diademas`),
  скрипт — `scripts/build_orthodox_draft.py`.
- QA кадров (1920×1080 и 450×800): корень всех 40 укладывается в кадр; визуально проверено ~20,
  исправлены 7 layout-багов (обрезание верха/переполнение): `ScienceFaithParallel`, `LawParallel`,
  `SacredNumbers`, `ArchaeologyConfirms`, `RulerCompare`, `ArgumentStructure`, `EmotionHealing`,
  `GenealogyTree`. Скриншоты — `qa-orthodox/`.

**Технические заметки:**

- Конфликты имён полей с глобальными типами схемы устранены переименованием:
  `role → office/duty/function`, `duration → span`, `time → epoch`, `layout → orientation`, `scale → scope`.
- `ScienceFaithParallel`/`SacredNumbers`/`LawParallel` переведены на `justify-start + overflow-y-auto`,
  чтобы при переполнении не обрезался верх (flexbox-баг центрирования).

**Ограничения / следующий шаг:**

- Стандарт движения (`docs/MOTION_STANDARD.md`) — пока план; `useMotion` не внедрён, компоненты
  используют общий паттерн `relativeTime + start_time + motion`.
- Видео-рендер в этом окружении не запускается (в backend-контейнере пуст `$DISPLAY`).
- Картинки-примеры в payload (иконы/портреты) указывают на несуществующие файлы `/media/...` —
  компоненты показывают fallback; для продакшена подставить реальные медиа.

---

## 10. Быстрая визуализация (дополнение по фидбеку)

Добавлен приоритетный компонент:

- **`CharacterStats`** — персонаж (прозрачный PNG/SVG) + шкалы-статы; режимы `single` (герой крупно)
  и `group` (сетка людей). Поля: `mode`, `characters[] (name,subtitle,image,color,stats[],traits[],start_time)`,
  `max_stat`, `show_values`, `source_note`. Демо: **`/p/60`** (одиночный + группа).

Библиотека: **133 компонента** (registry = db = 133, `.vue` = 164), `check_consistency` — OK.

### Кандидаты на «быструю визуализацию» (предложить к следующей итерации)

Идея: меньше текста, больше образа/схемы в один кадр.

1. `ImageCompareSlider` — две картинки с ползунком (было/стало, икона/фото).
2. `HeroVsVillain` — два персонажа лицом к лицу (портреты + короткие тезисы).
3. `MapHotspots` — изображение-карта с кликабельными точками и подписями.
4. `StatOrbit` — центральный образ + метрики по орбите (солнце/планеты-качества).
5. `MetaphorSplit` — образ слева, объяснение справа (икона/фото + 2–3 тезиса).
6. `TimelineHero` — лента жизни с портретом на каждом этапе.
7. `QuotePortrait` — крупный портрет + цитата поверх (расширение `SaintQuote`).
8. `ScaleBalance` — весы: две чаши (страсть/добродетель, закон/благодать).
9. `Pillars` — столпы/опоры концепции (3–5 вертикальных колонн).
10. `ImageGrid` — мозаика образов с подписями (без текстовых абзацев).
