# STATUS — текущее состояние SceneEngine

Обновлено: 2026-10-22.

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

## Что ещё не сделано

1. **Рендер не проверен end-to-end** после перехода на сцены. Realtime-захват
   оставлен, handshake добавлен, но полный прогон mp4 нужно сделать.
2. **Нет thumbnails** для шаблонов/объектов.
3. **Props — только JSON**, авто-формы из `props_schema` нет.
4. **Нет визуального размещения объектов** (drag-n-drop). Объекты вставляются
   как HTML-сниппеты.
5. **Нет валидатора сцены** (forbidden APIs, детерминизм, overflow).
6. **Нет AI-генерации сцены** (только ручной редактор/API).
7. **Нет сохранения пользовательских объектов/миров** в библиотеку.
8. **Персонажи — статичный силуэт**, ригов и липсинка нет.
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
7. Добавить механизмы: `wheelSpin`, `sway`, `steam`, `flicker`, `cycle`,
   `walk`, `breathe` как именованные пресеты.
8. Добавить `SceneKit.cues` редактор (таблица ключей: at / set).
9. AI: `POST /presentations/{id}/scenes/generate` из сценария.
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
```

Открыть `http://localhost:5175/p/1` — должна ехать машина по лесной трассе.

## Известные нюансы

- `SceneHost` в редакторе — `preview`, он не владеет глобальным handshake.
- В редакторе тема берётся из `.slides-container` за модалкой.
- `SceneKit` инжектится в iframe так же, как GSAP (локально, без CDN).
- В сцене нельзя использовать `rAF`, `Date.now`, `setInterval`, `Math.random`,
  бесконечные CSS-анимации.
