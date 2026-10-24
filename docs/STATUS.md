# STATUS — текущее состояние SceneEngine

Обновлено: 2026-10-23.

## Готовые Rive-персонажи (2026-10-23, вечер)

- `RiveActor` переведён на **state machine + view model**: для ассетов с
  состоянием (`oldman`) больше не скрабятся отдельные линейные анимации —
  они конфликтовали, и персонаж «только моргал».
- `seek(t)` вручную двигает state machine (`advanceAndApply`, шаг 1/60),
  Rive-цикл остановлен (`stopRendering`) — время по-прежнему детерминировано.
- `character-oldman` (ar.akash, CC BY 4.0): полное тело, ткань/верёвка/стопа,
  моргание, рот `Default/OO/AAA`, лицо, жест левой рукой. Добавлено видимое
  вторичное движение (наклон/дыхание/смещение).
- `scripts/seed_oldman.py` → **`/p/7`** (один старец, реплика с виземами из
  `text_to_visemes`).
- Bob: у ассета тоже есть state machine; драйвер останавливает его и скрабит
  линейные клипы — теперь работают 10 визёмов, моргание и дыхание.
  `scripts/seed_bob.py` → **`/p/9`** (бюст, говорит).
- `character-oldman-panel` → **`/p/8`**: два старца, независимые state machine,
  свой липсинк и жесты; второй отзеркален и тонирован, есть подписи.
- `GET /scene-library/characters` и `/{slug}` — каталог готовых актёров
  (лицензия, режим, виземы, возможности).
- Редактор: вкладка **Characters** — карточки актёров, поле реплики;
  текст уходит в `POST /scene-library/text-to-visemes`, и сцена открывается с
  готовым липсинком (проверено: «Привет, это тест липсинка» → 20+ визёмов).
- Проверено: `/p/8` отрендерен в mp4 (1920×1080 и 1080×1920, 30 fps, 8.9 с);
  кадры 1.5/4.5/6.5 с содержат двух персонажей, у второго в 4.5 с открыт рот.
- Проверено: `/p/9` (Bob) — рот меняет форму по виземам, моргание/дыхание.
- 9:16: панель перестроена (два персонажа рядом, подписи над головами).

## Rive-риг персонажей (2026-10-23)

- Собственный `.riv` собран из RML: **скелет 21 кость** (root/spine/chest/neck/head,
  плечи/локти/кисти, бёдра/колени/стопы), 10 форм рта, глаза/веки/брови,
  одежда и аксессуары.
- Драйвер `SceneKit.riveCharacter` / `RiveCharacter.create`: все движения —
  чистая функция от `seek(t)`; кости и рот управляются через view-model числа,
  без внутренних часов Rive.
- 5 пресетов: `host`, `cohost`, `priest`, `historian`, `sociologist`
  (цвета, борода, очки, платок, юбка, ряса, блейзер).
- Клипы: idle, talk, wave, point, open, shrug, walk (in-place).
- Исходник: `core/rive/character/` (`scene.rml` + `rive.yaml`).
  Генератор: `scripts/build_rive_character.py` (Rive CLI 1.7).
  Рантайм-ассет: `core/public/rive/character.riv`.
- Контроллер: `core/public/vendor/rive-character.js`.
- Шаблоны `character-rive` (один ведущий, `/p/5`) и `character-rive-panel`
  (host + cohost, `/p/6`); редактор показывает превью, `SceneHost` инжектит
  `.riv` как base64 (обходит CORS песочницы).
- Проверено: сцена в плеере 16:9 и 9:16, seek 0/5.2 с, жест, ходьба,
  липсинк (визем 1 на 0.9 с), редактор, отсутствие ошибок в консоли.



## Что уже работает

### Инфраструктура
- Отдельный compose-проект `scene-saas`.
- Frontend `http://localhost:5175`, backend `http://localhost:8002`,
  Postgres `localhost:5436` (`scene_db` / `scene_user`).
- Чистая БД, сиды тем/вариантов/пресетов, демо `http://localhost:5175/p/1`.

### Сцена
- Sandboxed iframe (`sandbox="allow-scripts"`).
- Инжект темы (CSS-переменные) и локального GSAP.
- Контракт `window.scene.seek(t)`.
- `SceneKit`: `cues`, `integrate`, `mechanism`, `parallax`, `compose`.
- Handshake: `scene-ready` → `window.__sceneReady = true`; рендерер ждёт флаг.
- Только активная сцена монтируется в плеере (`Slide.vue` `bare`).

### Данные и API
- Поля сцены в `slides`: `kind`, `duration`, `code`, `props`, `props_schema`,
  `track`, `z_index`.
- CRUD: `/presentations/{id}/scenes`, `/presentations/scenes/{id}`.
- Валидация: `code` — объект, `html/css/js` — строки, `duration > 0`.
- Длительность: `start_time + duration`; `EndMarkerSlide` синхронизируется
  с `max(start + duration) + 1000`.
- Фронт пишет сцены через `/scenes`, EndMarker — через `/slides`.

### Редактор
- Полноэкранный `SceneEditor`.
- Вкладки: Scenes / Worlds / Objects / HTML / CSS / JS / Props / Info.
- Живое превью с ручным временем и play.
- Загрузка шаблона/окружения, вставка объекта.
- Сохранение/удаление, `start_time`, `duration`, `props_schema`.

### Библиотека
- 5 окружений: forest, city, mountains, office, studio.
- 16 объектов: car, road, tree, pine, cloud, bird, street-lamp, building,
  desk, monitor, coffee, plant, person, traffic-light, sun, moon.
- 5 шаблонов: forest-drive, city-night-drive, mountain-flight, office-day,
  studio-intro.
- API: `/scene-library/templates|environments|objects` (+ `/{slug}`).

### Персонажи и липсинк (2026-10-23)
- Объект `character` — полноценный SVG-риг: голова, взгляд, веки, брови,
  рот с 10 формами-виземами + язык, торс, руки, ноги.
- `SceneKit.characterRig(el, opts)` — драйвер: виземы с кроссфейдом, челюсть,
  моргание, дыхание, качание, саккадический взгляд, настроение (брови),
  жест рукой, ходьба.
- `SceneKit.visemeBlend` / `lipsync({blend})` — плавный переход форм рта.
- Шаблон `character-talk` — эталон кинематографичности: GSAP-таймлайн,
  кинетическая типографика, пыль, зерно/виньетка/грейд, контактная тень.
- Демо: `scripts/seed_character_talk.py` → `/p/4`.

### Инструменты кинематографичности (SceneKit)
- `particles(canvas, opts)` — детерминированные частицы (пыль, снег, искры).
- `idle(root, {index})` — дыхание/качание/моргание (портрет или SVG-риг).
- `grain(root, opts)` — зерно + виньетка + цветовая коррекция одним вызовом.
- `shadow(el, opts)` — контактная тень под объектом.
- `cues(list, {smooth:true})` — плавная интерполяция ключей (устранена
  ступенчатая скорость в drive-шаблонах).
- Стандарт качества — `docs/ANIMATION.md`, раздел 1.5.

### Документация
- `docs/SCENES.md` — контракт сцены.
- `docs/PROCESSES.md` — как создавать контент.
- `docs/ROADMAP_2D.md` — вектор.
- `docs/DEV.md` — порты.
- `docs/SERVER.md` — деплой на сервер.
- `AGENTS.md` — правила для ИИ.

## Классификация, views, слои (добавлено 2026-10-22)

- `ENV_META` / `OBJ_META` в `backend/scene_library.py`.
- API совместимости:
  - `GET /scene-library/environments/{slug}/objects`
  - `GET /scene-library/objects?environment=forest`
  - `GET /scene-library/compatibility`
  - `POST /scene-library/validate-composition`
- Редактор: выбранный мир фильтрует Objects; несовместимые — с предупреждением.
- Views: `view` сцены → `<body class="view-...">`; time-of-day для миров;
  per-object views через `SceneKit.views(root, { car: 'front' })`.
- Вкладка `Layers`: парсит `.obj-*` из HTML, даёт left/bottom/width/height/
  z-index/transform/view, duplicate/delete.

## Управление и ключи (добавлено 2026-10-22)

- Layers: слайдеры X/Y, ширина/высота, масштаб, поворот, opacity, z-index.
- Живой patch стилей в preview через `postMessage` (`patch-style`), без полного
  пересоздания iframe.
- Cues: таймлайн-маркеры, время, `key=value`, add/delete, live preview.
- `window.__sceneCues` в iframe; `SceneKit.cues` читает их.
- Персонаж: объект `character` (SVG-риг-заготовка) + `docs/CHARACTERS.md`.

## Learning registry / DAM / characters (2026-10-22)

- Добавлена таблица `scene_learnings`, API `/scene-library/learnings`,
  сид `scripts/seed_learnings.py`, документ `docs/LEARNINGS.md`.
- Добавлен объект `character` (SVG-риг-заготовка), `docs/CHARACTERS.md`
  с сравнением Rive/Spine/DragonBones/Live2D/OpenToonz/Synfig/Blender.
- Добавлены `docs/ENGINE.md`, `docs/API.md`, `docs/EDITOR.md`, `docs/ASSETS.md`,
  `docs/HUMAN_AI_STUDIO.md`.

## Редактор: подсветка, слои, scatter (2026-10-22)

- CodeMirror 6 для HTML/CSS/JS (ленивый chunk).
- HTML-контракт слоёв: world/objects/actors/fx/overlay.
- `SceneKit.scatter` для деревьев/птиц с seeded PRNG.
- Learnings: `proposed` для ИИ, approve/archive.
- `docs/OBJECT_STUDIO.md` — создание объектов по промпту/фото.
- `docs/ENGINE.md`, `API.md`, `EDITOR.md`, `ASSETS.md`.

## 2.5D и режимы сцен (2026-10-22)

- `SceneKit.camera` — детерминированная 2.5D-камера по слоям.
- Шаблон `cinematic-forest`: perspective, параллакс, свет, виньетка, машина.
- `docs/SCENE_MODES.md`: code vs composite; переиспользование — опция, а не ограничение.
- Персонажи/миры — основные кандидаты на переиспользование; сцены можно писать с нуля.

## PRAVOSLAVIE content pack (2026-10-22)

- Проект `pravoslavie`, демо `/p/2`, эпизод `/p/3`.
- 6 миров: studio-prav, church, ancient-rus, empire, soviet, modern-city-day.
- Исторические миры — SVG-иллюстрации (лес/река/храм, улицы, кирпичные дома).
- Историческая массовка — 4 SVG-силуэта (крестьянка, воин, монах, рабочий).
- 9 персонажей (Open Peeps CC0): host, cohost, priest, historian, sociologist,
  peasant, warrior, monk, worker.
- 9 шаблонов: prav-studio-host/panel/sociologist, empire/ancient/soviet,
  timeline, church quote, outro.
- Студия: foreground-стол, монитор, книги, постер, растение, lower third,
  canvas-пыль.
- Редактор: iframe пересоздаётся по key (фикс пустого превью), позиции
  объектов в inline style (слайдеры совпадают), CodeMirror.
- Learnings: 16 записей.
- Media-вкладка в редакторе: загрузка/URL картинки и видео на монитор,
  переключение медиа ключами (`monitor_media=...`).
- Портретные оверрайды для Shorts (персонаж по центру, монитор сверху).
- OpenCode-агенты: `.opencode/agent/` (producer, analyst, storyboard,
  scene-builder, QA, researcher).
- Статус сцены: `draft` / `review` / `approved` в шапке редактора и payload.
- **Рендер проверен end-to-end:** `Prav_Studio_demo` 36.9 с, 30 fps, 5 МБ;
  кадры 2 с и 20 с содержат студийную и историческую сцены.

## Что ещё не сделано

1. **Кастомный `/p/5` ещё не прогнан в mp4**; готовые актёры `/p/7` и `/p/8` уже рендерятся.
2. **Нет thumbnails** для шаблонов/объектов.
3. **Props — только JSON**, авто-формы из `props_schema` нет.
4. **Нет визуального размещения объектов** (drag-n-drop). Объекты вставляются
   как HTML-сниппеты.
5. **Нет валидатора сцены** (forbidden APIs, детерминизм, overflow).
6. **Нет AI-генерации сцены** (только ручной редактор/API).
7. **Нет сохранения пользовательских объектов/миров** в библиотеку.
8. **Персонажи**: готовый Old Man и панель двух старцев работают; осталось добавить других актёров (молодой ведущий, женщина, массовка), разобрать numeric view model у Bob и довести арт собственного рига.
9. **Старые 117 Vue-компонентов и 16 slide-обёрток остались на диске**
   как мёртвый код; не импортируются (registry пуст), но репозиторий можно
   почистить в Phase 2.
10. **Таблица называется `slides`**, хотя домен — сцены. Переименование
    запланировано отдельной миграцией, чтобы не ломать аудио/рендер.

## Ближайшие 10 задач

1. Прогнать реальный рендер `forest-drive` в mp4 и проверить handshake.
2. Добавить thumbnails: рендер кадра `duration/2` для шаблонов и объектов.
3. Сделать авто-форму props из `props_schema` (text/number/boolean/color).
4. Добавить в редактор drag-n-drop объекта на сцену (позиция/масштаб).
5. Валидатор сцены: запрещённые API, двойной `seek` → одинаковый кадр.
6. Улучшить 5 окружений до «кинематографичного» вида (свет, туман, глубина).
7. **Сделать ещё 4 эталона** в стиле `character-talk` (GSAP + частицы + grain +
   тень + кинетическая типографика) — это few-shot для DeepSeek.
8. **Перевести портреты канала на виземы** (слой рта поверх фото или SVG-риг).
9. AI: `POST /presentations/{id}/scenes/generate` из сценария + JSON-контракт
   промпта и валидатор ответа (см. `docs/CLAUDE_ANALYSIS.md`, шаг 3).
10. Почистить legacy: удалить неиспользуемые `components/ui`, `components/slides`,
    старые seed-скрипты и docs.

## Как проверить, что всё живо

```bash
cd "Projects/SceneEngine"
docker compose ps
curl -s http://localhost:8002/presentations/1/scenes
curl -s http://localhost:8002/scene-library/templates | head -c 200
curl -s http://localhost:8002/scene-library/environments | head -c 200
curl -s http://localhost:8002/scene-library/objects | head -c 200
curl -s http://localhost:8002/scene-library/templates/character-rive | head -c 200
```

Открыть `http://localhost:5175/p/1` — машина по лесной трассе; `http://localhost:5175/p/5` — Rive-персонаж.

## Известные нюансы

- `SceneHost` в редакторе — `preview`, он не владеет глобальным handshake.
- В редакторе тема берётся из `.slides-container` за модалкой.
- `SceneKit` инжектится в iframe так же, как GSAP (локально, без CDN).
- В сцене нельзя использовать `rAF`, `Date.now`, `setInterval`, `Math.random`,
  бесконечные CSS-анимации.
