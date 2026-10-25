# WORKLOG — что делалось, какие были ошибки и как исправляли

Хронология форка. Полезно, чтобы новый агент не повторял ошибки.

---

## 2026-10-22 — форк и фундамент

### 1. Копирование проекта
- `rsync` из `Presentation/` в `SceneEngine/` без `.git`, `node_modules`, `dist`,
  `uploads`, `dump.sql.gz`, `__pycache__`.
- Новый git-репозиторий, baseline-коммит.
- Удалены старые медиа: `core/public/audio` (37 MB), `core/public/generated` (22 MB),
  `chaos.png`, `efficient.png`.

### 2. Инфраструктура
- `docker-compose.yml`: `name: scene-saas`, БД `scene_db`/`scene_user`, порты
  `5175 / 8002 / 5436`, том `scene_postgres_data`.
- Backend-образ переиспользован: `presentation-saas-backend:latest` → `scene-saas-backend:latest`.
- `backend/database.py`, `core/vite.config.js`, `scripts/*` переведены на 8002.
- `start.sh` / `stop.sh` обновлены.

### 3. Scene runtime
- `core/src/scenes/runtime.js`: сборка `srcdoc`, тема, GSAP, `scene-ready`,
  `seek`/`seek-done`.
- `core/src/scenes/SceneHost.vue`: sandboxed iframe, `seek(t)`, handshake,
  `preview`-режим для редактора.
- `core/src/scenes/SceneEditor.vue`: HTML/CSS/JS/Props, превью, play, таймлайн-скраб.
- `Slide.vue` получил `bare`: сцена рисует весь кадр, без заголовка/паддингов.
- `MainPresentation.vue`: `__scene__` → `SceneHost`, остальное — legacy fallback.
- `componentsRegistry.js` очищен (старые 117 компонентов не импортируются).

### 4. Данные и API
- В `slides` добавлены поля: `kind`, `duration`, `code`, `props`, `props_schema`,
  `track`, `z_index`.
- `_ensure_columns()` дополнен ALTER-ами.
- `SlideCreate`/`Slide` схемы расширены.
- CRUD сцен: `/presentations/{id}/scenes`, `/presentations/scenes/{id}`.
- Валидация: `code` — объект, `html/css/js` — строки, `duration > 0`.
- `renders.py`: fallback-длительность учитывает `start + duration`.
- EndMarker синхронизируется на фронте: `max(start+duration)+1000`.

### 5. Демо и сиды
- `scripts/seed_scene_demo.py`: project `scene-demo`, folder `scenes`, presentation
  `Demo Scene`, сцена `forest-drive`, EndMarker.
- Сиды тем/вариантов/пресетов.

---

## Ошибки и решения

### Ошибка 1. `Cannot read properties of null (reading 'querySelector')`
**Симптом:** в iframe `VM8 about:srcdoc:14 Uncaught TypeError`.
**Причина:** шаблоны собирались из environment + objects, но HTML не оборачивался
в `<div class="scene">`. JS делал `document.querySelector('.scene')` → `null`.
**Решение:** `_compose()` в `backend/scene_library.py` оборачивает HTML в
`<div class="scene">…</div>`.
**Проверка:** `t['code']['html']` содержит `<div class="scene">`; после рестарта
backend и повторного сида демо обновилось.

### Ошибка 2. Сид не обновил код сцены
**Симптом:** после фикса wrapper в БД всё ещё старый код.
**Причина:** сид запускался в момент рестарта/старого процесса; порядок команд
был неудачный.
**Решение:** `docker compose restart backend` → дождаться `Application startup complete`
→ `docker compose exec -T backend python scripts/seed_scene_demo.py`.
**Проверка:** `GET /presentations/1/scenes` → `code.html` содержит wrapper.

### Ошибка 3. Редактор: чёрное превью
**Причина:** тема инжектится в `.slides-container`, а редактор — вне него;
`var(--bg-base)` не определён, фон прозрачный.
**Решение:** `collectThemeVars` фолбэчится на `document.querySelector('.slides-container')`
и добавлены дефолтные CSS-переменные в `:root` iframe.
**Дополнительно:** превью открывается на `1200 мс`, а не на `0`, чтобы был виден кадр.

### Ошибка 4. Редактор: светлый хром
**Причина:** Tailwind-цвета используют `--bg-base-rgb`, `--text-primary-rgb`, а не
только `--bg-base`.
**Решение:** в `SceneEditor` добавлен `editorTheme` с `-rgb`-переменными.

### Ошибка 5. `/scene-library/*` → 404
**Причина:** роутер добавлен, но backend не перезапущен.
**Решение:** `docker compose restart backend`; проверка `curl`.
**Урок:** после правок Python — всегда рестарт backend (нет `--reload`).

### Ошибка 6. `git push` → `src refspec main does not match`
**Причина:** `git init` создал ветку `master`.
**Решение:** `git branch -M main` → `git push -u origin main`.

### Ошибка 7. В репозиторий мог попасть `SERVER_ACCESS.md`
**Причина:** старый документ с инфраструктурной информацией.
**Решение:** удалён до коммита; старые доки перенесены в `docs/legacy/`.
**Правило:** перед push проверять `git diff --cached --name-only` на `.env`,
`secret`, `credential`, `server_access`, `id_rsa`, `*.pem`.

### Ошибка 8. Старые медиа в git
**Причина:** baseline включал voiceover WAV и generated PNG.
**Решение:** удалены из рабочего дерева и из репозитория (37 MB + 22 MB).

---

## 2026-10-22 — классификация, views, слои

### Классификация
- `ENV_META`: domain (outdoor/indoor/stage), views, default_view, perspective.
- `OBJ_META`: domain, environments, surface, views, default_view.
- API:
  - `GET /scene-library/environments/{slug}/objects`
  - `GET /scene-library/objects?environment=forest`
  - `GET /scene-library/compatibility`
  - `POST /scene-library/validate-composition`
- Редактор: `activeEnvironment`, фильтр объектов, предупреждение о несовместимости.

### Views
- `view` сцены → `<body class="view-...">`.
- Окружения: day/sunset/night, night/dusk, dawn/day, day/evening, dark/blue.
- Объекты: `views` в метаданных; CSS `.obj-car.view-front`, `.obj-building.view-corner`,
  `.obj-person.view-side`.
- `SceneKit.views(root, { car: 'front' })` — переключение per-object.
- Решение: **не делать глобальную 3D-камеру**; делать time-of-day для мира +
  per-object views. Иначе логика превращается в 3D-движок.

### Слои/объекты в редакторе
- Вкладка `Layers`: парсит `code.html` через `DOMParser`, находит `.obj-*`.
- Для выбранного объекта: left/bottom/width/height/z-index/transform/view,
  duplicate/delete.
- Это не drag-n-drop, но уже реальное управление объектами без нового формата сцены.
- Следующий шаг: canvas-выделение и drag/resize.

---

## Текущее состояние на момент записи

- Frontend/back/DB запущены.
- Демо `/p/1` — `forest-drive`.
- Классификация/views/слои добавлены, но **ещё не закоммичены** (см. `git status`).
- Нужно: `npm run build`, рестарт backend, повторный сид, проверка API, коммит/push.

---

## 2026-10-22 — документация и принципы анимации

### Добавлено
- `docs/ANIMATION.md` — принципы из motion-навыка `vizavi-motion`, адаптированные
  под `seek(t)`: режиссура, камера/параллакс, вес и инерция, типографика,
  motion blur/DOF (с оговоркой про paint), звук, обязательная итерация, чек-лист.
- `docs/DECISIONS.md` — ADR по форку, iframe/seek, GSAP+SceneKit, таблице `slides`,
  realtime-рендеру, библиотеке миров/объектов, классификации, views, слоям.
- `docs/WORKLOG.md` — этот файл.
- `docs/README.md` — индекс документации.
- `AGENTS.md` обновлён: ссылки на STATUS/ROADMAP/ANIMATION/WORKLOG/DECISIONS,
  `SceneKit`, модель `Environment + Objects + Mechanisms + Cues`.

### Ошибка 9. Seed обновил не ту сцену
**Симптом:** после добавления `view` в payload у демо `view` был `None`.
**Причина:** в презентации было две `__scene__` (демо + тестовая из API).
`db.query(...).filter(component='__scene__').first()` без сортировки вернул
тестовую сцену, а не `scene-demo-1`.
**Решение:** seed ищет строго `slide_id == "scene-demo-1"`; лишняя тестовая
сцена удалена через `DELETE /presentations/scenes/5`.
**Урок:** в сидах всегда фильтровать по стабильному `slide_id`, а не `.first()`.

### Ошибка 10. `view` не доходил до рендера
**Причина:** `normalizeScenePayload` в `demoScene.js` не пробрасывал `view`;
`SceneHost` не принимал `view`; `buildSceneDoc` не ставил класс на `<body>`.
**Решение:** добавлен `view` в normalize, prop `SceneHost`, класс
`view-<name>` на `<body>`, `view` в payload и `SceneEditor`.
**Урок:** при добавлении поля сцены проверять всю цепочку:
DB → API → `scenePayload` → `SceneHost` → `runtime` → CSS.

### Текущая проверка
- `npm run build` — OK.
- `GET /scene-library/environments/forest/objects` — 200.
- `POST /scene-library/validate-composition` — корректно отдаёт ошибки
  для `car`/`street-lamp` в `office`.
- Демо `/p/1` — `forest-drive`, `view: day`, wrapper на месте.


---

## 2026-10-22 — sliders, cues, human+AI research

### Сделано
- Layers: слайдеры вместо текстовых полей.
- Live-patch стилей в iframe через `patch-style` (без пересборки).
- Cues-редактор: маркеры, время, `key=value`, add/delete.
- `window.__sceneCues` + `SceneKit.cues` интеграция.
- Добавлен объект `character` (SVG-риг-заготовка).
- `docs/HUMAN_AI_STUDIO.md` — исследование best practices 2026.
- `docs/CHARACTERS.md` — варианты движка персонажей и липсинка.

### Источники исследования
- HyperFrames vs Remotion (Voyager, HyperFrames docs)
- Human-in-the-loop (Velt, Manava)
- Motion graphics AI pipeline (TapVid)
- Theatre.js sequences
- Rive lip sync (10 visemes)

### Вывод
- Строим **human-in-the-loop** конвейер: AI предлагает, человек утверждает.
- Ворота: brief → storyboard → scene → animation → QA → render → publish.
- Не делать полностью автономный ИИ и нодовый редактор раньше слоёв/таймлайна.
- Персонажи: начать с SVG-рига, Rive/Spine — после проб.

---

## 2026-10-22 — human+AI решения, learnings, DAM, персонажи

### Решения пользователя
- Утверждать раскадровку и каждую сцену.
- Ошибки документировать, чтобы ИИ не повторял.
- ИИ: и прямое редактирование, и diff-предложения.
- Сначала opencode + качественная документация; позже агенты по API.
- Персонажи: Rive/Spine/бесплатные аналоги; только видео.
- Ассеты: полный DAM.
- UI: итеративно.

### Сделано
- Таблица `scene_learnings` + API `GET/POST /scene-library/learnings`.
- Сид `scripts/seed_learnings.py` (10 записей).
- `docs/LEARNINGS.md`, `docs/ENGINE.md`, `docs/API.md`, `docs/EDITOR.md`,
  `docs/ASSETS.md`, `docs/HUMAN_AI_STUDIO.md`.
- Объект `character` (SVG-риг-заготовка) и `docs/CHARACTERS.md` с таблицей
  Rive/Spine/DragonBones/Live2D/OpenToonz/Synfig/Blender.
- Cues в шаблонах читают `window.__sceneCues`.
- Персонаж/ключи/слайдеры собраны; `npm run build` проходит.

### Проверки
- `GET /scene-library/learnings` → 10 записей.
- `POST /scene-library/learnings` → создаёт запись (тестовая удалена).
- `POST /scene-library/validate-composition` → корректные ошибки.
- `npm run build` — OK.


---

## 2026-10-22 — слои, CodeMirror, scatter, Object Studio

- HTML-контракт слоёв: `layer-world / layer-objects / layer-actors / layer-fx / layer-overlay`.
- `_compose` раскладывает мир/объекты/персонажей по слоям.
- CodeMirror 6 для HTML/CSS/JS (async chunk).
- `SceneKit.scatter` + seeded PRNG; forest-drive генерирует деревья/сосны, mountain-flight — птиц.
- Learnings: AI-записи создаются как `proposed`, человек утверждает.
- `docs/OBJECT_STUDIO.md` — создание объектов по тексту/фото.
- `docs/ENGINE.md`, `docs/API.md`, `docs/EDITOR.md`, `docs/ASSETS.md`.

### Ошибка 11. CodeMirror раздул основной бандл
**Симптом:** MainPresentation вырос до ~759 KB.
**Причина:** статический импорт CodeMirror.
**Решение:** `defineAsyncComponent(() => import('./CodeEditor.vue'))` → отдельный chunk.
**Урок:** тяжёлые редакторы подключать лениво.


---

## 2026-10-22 — 2.5D-камера и режимы сцен

- `SceneKit.camera` + шаблон `cinematic-forest`.
- `docs/SCENE_MODES.md`: code vs composite, каст проекта, 2.5D-техники.
- Подчёркнуто: библиотека объектов — опция; большинство сцен можно писать с нуля.


---

## 2026-10-22 — PRAVOSLAVIE content pack

### Сделано
- Проект `pravoslavie`, папка, две презентации: `/p/2` (студия), `/p/3` (Э1).
- 6 миров, 9 персонажей Open Peeps (CC0), 9 шаблонов сцен.
- Студия: foreground-стол, монитор, книги, постер, растение, lower third,
  canvas-пыль, монитор с media/video.
- Персонажи: Open Peeps вместо детских SVG-блоков.
- Редактор: фикс пустого превью (iframe key), inline-позиции для слайдеров.

### Ошибка 12. Превью редактора пустое
**Симптом:** iframe с srcdoc 145 KB, но body пустой.
**Причина:** iframe не перезагружал srcdoc после асинхронной сборки.
**Решение:** `:key="frameKey"` + инкремент после rebuild.
**Урок:** большой srcdoc в модалке — пересоздавать iframe.

### Ошибка 13. Слайдеры показывали не те позиции
**Симптом:** монитор на 58%/40%, слайдеры 12%/18%.
**Причина:** позиции в CSS, редактор читает inline style.
**Решение:** `object_styles` в `_compose` → inline style.

### Ошибка 14. Таймлайн перекрывал lower third
**Причина:** оба внизу.
**Решение:** `.studio-lower-third { display:none }` в TIMELINE_CSS.


### Ошибка 15. Фигуры исторических сцен «плавали» и стояли в реке
**Причина:** `object_styles` дописывались в начало inline style, а дефолт
в конце перекрывал их; фигуры стояли в воде.
**Решение:** дописывать `object_styles` в конец style; поднять фигуры на
передний план (`bottom:8%`); опустить крест на купол.
**Урок:** inline-стили должны дописываться после дефолтных, а не до.


### 2026-10-22 — Media tab
- Вкладка Media в редакторе: загрузка картинки/видео, URL, очистка.
- `STUDIO_JS` читает `monitor_media`/`monitor_video` из cues и переключает монитор.
- Табы редактора сделаны горизонтально скроллируемыми.


### 2026-10-23 — portrait/Shorts + агенты
- Портретные оверрайды для PRAV-шаблонов (`@media (orientation: portrait)`):
  персонаж по центру, монитор сверху, lower third снизу.
- Добавлены opencode-агенты `.opencode/agent/`:
  `pravoslavie-producer`, `script-analyst`, `storyboard-director`,
  `scene-builder`, `scene-qa`, `visual-researcher`.


### 2026-10-23 — рендер проверен
- `POST /renders/realtime` для презентации 2 → `completed`, 36.9 с, 30 fps, 5 МБ.
- Кадры 2 с (студия) и 20 с (империя) корректны.
- Вывод: сцены рендерятся тем же пайплайном, что и слайды; handshake работает.


### 2026-10-23 — статусы сцен
- В редакторе появился статус сцены: draft/review/approved (payload `status`).
  Это первый шаг к воротам качества human+AI.


### 2026-10-23 — детализированные портреты
- Сгенерированы 5 портретов (host/cohost/priest/historian/sociologist) через
  Gemini Image; chroma-key + crop (`scripts/generate_prav_portraits.py`).
- Заменены Open Peeps у основного каста на портреты (`/portraits/*.png`).
- Добавлено процедурное движение: дыхание/качание портрета, камера студии,
  световой свип, сканлайн монитора, анимация lower third и caption.
- Портреты приведены к квадрату и `object-fit: cover`, чтобы лица были
  одного масштаба в панели.


### 2026-10-23 — Аудит качества и конвейер DeepSeek (от Claude)
- Проведен комплексный аудит кодовой базы, всех 15 шаблонов и SceneKit.
- Оформлен документ `docs/CLAUDE_ANALYSIS.md`:
  - Выделены сильные стороны (детерминизм `seek(t)`, sandboxing, `scene_learnings`).
  - Учтены осознанные проектные решения автора (realtime-рендер, отсутствие Alembic).
  - Сформулированы 7 обязательных компонентов premium-качества (GSAP timelines вместо vanilla math, canvas particles, film grain/vignette/grading, контактные тени, кинетическая типографика, вторичное движение, 2.5D параллакс).
  - Определена архитектура конвейера с DeepSeek: JSON Schema контракт, 5 gold-standard шаблонов (few-shot), автоматический инжект learnings, валидация forbidden APIs.
  - Спланированы расширения SceneKit (`particles`, `idle`, `postFx`, `ease`).
- Документ подписан: Claude (Anthropic).

### 2026-10-23 — Управляемый персонаж + липсинк + инструменты кинематографичности
- Rive CLI 1.7.0 установлен (загрузка 24 МБ с CloudFront шла ~2 МБ/мин, докачано
  вручную с проверкой SHA-256). Решение по движку: Rive отложен — нет
  произвольного `seek(t)` и внутренних часов runtime; рабочий путь — SVG-риг.
- Объект `character` переписан из силуэта в полноценный риг: голова, веки,
  зрачки (взгляд), брови (настроение), рот с 10 формами-виземами + язык,
  торс (дыхание), руки (жест), ноги (ходьба). Цвета — CSS-переменные
  `--char-*`, переопределяются пропсами.
- `SceneKit.characterRig(el, opts)` — драйвер персонажа: виземы с кроссфейдом,
  челюсть/язык по открытости, моргание (3400/170 мс + seed), дыхание,
  качание, саккадический взгляд, настроение neutral/joy/anger/sad/surprise,
  жест рукой, ходьба.
- `SceneKit.visemeBlend(visemes, t, blend)` и `lipsync({blend, onVisemePair})` —
  плавный переход форм рта вместо ступеньки.
- Расширен SceneKit: `particles(canvas, opts)`, `idle(root, opts)`,
  `grain(root, opts)` (зерно+виньетка+грейд), `shadow(el, opts)` (контактная
  тень), `cues(list, {smooth:true})` — плавная интерполяция ключей, устранена
  ступенчатая скорость в drive-шаблонах.
- Новый шаблон `character-talk` — первый gold-standard: GSAP-таймлайн,
  кинетическая типографика (маска + yPercent + letterSpacing + stagger),
  пыль, зерно/виньетка/грейд, контактная тень, ореол, световой свип, липсинк.
  Проверен в 16:9 и 9:16.
- Демо: `scripts/seed_character_talk.py` → `/p/4`.
- Тест-харнес `core/public/rig-test.html`: `?tpl=`, `?pres=&slide=`, `?ar=9:16`,
  `?t=мс` — быстрая покадровая проверка сцен без плеера.
- Доки: `docs/CHARACTERS.md` (риг и драйвер), `docs/LIPSYNC.md` (виземы вместо
  Rive), `docs/ANIMATION.md` §1.5 (стандарт кинематографичности), `docs/SCENES.md`
  (справочник SceneKit), `docs/STATUS.md`, `AGENTS.md` §5.5.


### 2026-10-23 — Rive-риг персонажа (скелет + липсинк)

- Собран собственный `.riv` из RML через Rive CLI 1.7:
  `core/rive/character/` + `scripts/build_rive_character.py` →
  `core/public/rive/character.riv`.
- 21 кость, 10 форм рта, глаза/веки/брови, 5 пресетов (host/cohost/priest/
  historian/sociologist), клипы idle/talk/wave/point/open/shrug/walk.
- `RiveCharacter` (`core/public/vendor/rive-character.js`) пишет VM-числа из
  `seek(t)` и вызывает `drawFrame()`; `SceneKit.riveCharacter` — обёртка.
- Шаблон `character-rive`, демо `/p/5`; `SceneHost` инжектит `.riv` base64,
  чтобы обойти CORS песочницы.
- Проверено: плеер 16:9/9:16, seek(0)/seek(5200), жест, ходьба, липсинк,
  редактор, консоль без ошибок.

Ошибки/решения:
1. `bind-target-missing-property` на RootBone x/y — у RootBone ключи 90/91,
   не 13/14. Симптом: файл собирается, но не двигается.
2. Пустой кадр/невидимый персонаж при `--screenshot` — ошибки биндов; смотреть
   `rive inspect --summary` (`problems`), а не только код возврата.
3. Рот/подбородок закрыт — порядок отрисовки Rive: первый child сверху.
   Торс/шея, объявленные раньше головы, перекрывают лицо. Рисуем лицо и
   детали раньше базы.
4. В iframe `fetch('/rive/character.riv')` даёт CORS (opaque origin) —
   читаем файл в родителе и передаём base64/buffer.
5. Готовые чужие `.riv` (tiny/toshi и др.) не подходят: у большинства нет
   контракта виземов; у tiny он есть, но GPL и маскот. Свой риг — рабочий путь.


### 2026-10-23 — Rive panel (два персонажа)

- Шаблон `character-rive-panel`: два canvas, один `.riv`/буфер, два пресета
  (host + cohost), общий seek. Демо `/p/6`.
- `RIVE_PANEL_JS` берёт `props.cast[]` (character/mood/visemes/gestures) и
  создаёт отдельный `RiveCharacter` на каждый canvas.
- Проверено: 16:9, `/p/6`, консоль чистая; характеры двигаются/говорят
  синхронно.


### 2026-10-23 (вечер) — готовые Rive-актёры: state machine вместо scrub

- `RiveActor` получил режим `stateMachine`: после загрузки вызывается
  `play(stateMachine)`, затем `stopRendering()`, а `seek(t)` двигает
  `StateMachine.advanceAndApply(dt)` шагами 1/60 и вызывает `drawFrame()`.
- View model: `mouth` (enum `Default/OO/AAA`), `face` (`Normal/wow`),
  `leftHand` (trigger). 10 визёмов маппятся в три формы рта.
- Добавлено вторичное движение (наклон/дыхание/смещение canvas) и
  периодический жест, иначе на общем плане персонаж читается как стоп-кадр.
- `character-oldman-panel`: два независимых актёра, второй отзеркален и
  тонирован; подписи «Летописец» / «Старец»; `/p/8`.
- `scripts/seed_oldman.py` и `seed_oldman_panel.py` генерируют виземы из
  текста через `scripts/text_to_visemes.py`.
- API `GET /scene-library/characters`, редактор — вкладка Characters.
- `/p/8` отрендерен в mp4: 1920×1080, 30 fps, 8.9 с; кадры проверены.

#### Ошибка 16. «Персонаж только моргает»
**Симптом:** в сцене видно моргание/дыхание, но руки, тело и рот не двигаются.
**Причина:** ассет содержит state machine, а драйвер скрабил отдельные линейные
анимации (`Talking`, `Foot Tap`, `Mouth A`). При наличии state machine Rive
игнорирует линейные анимации; последовательные `scrub()` перетирают друг друга.
**Решение:** играть state machine и управлять им через view model, а не
скрабить клипы. Для детерминизма — `stopRendering()` + `advanceAndApply(dt)`.
**Урок:** если у `.riv` есть state machine, единственный честный путь — view model.

#### Ошибка 17. Панель в 9:16 наезжала персонажами друг на друга
**Причина:** оба персонажа имели высоту 103vmin и нижнюю привязку 34%/2%.
**Решение:** в портрете — два персонажа по 46vmin шириной, 82vmin высотой,
слева/справа; подписи над головами.


### 2026-10-24 — 3D-аватар: Babylon + Ready Player Me + Mixamo-ретаргет

- Добавлен шаблон `character-3d` и демо `/p/10`: GLB-аватар Ready Player Me
  (67 костей, 72 ARKit/Oculus-морфа), Babylon.js, один кадр на `seek(t)`.
- Драйвер `core/public/vendor/babylon-character.js`:
  - загрузка `.glb` из URL или `ArrayBuffer`/base64 (для sandbox-iframe);
  - клипы Mixamo (GLB, 16 штук) ретаргетятся на RPM-скелет;
  - липсинк 10 визёмов → Oculus-морфы, кроссфейд 80 мс;
  - моргание, взгляд, настроение, жесты, контактная тень, ground clamp;
  - позы-оверрайды (`pose`) и ключи позы (`pose_keys`);
  - детерминизм: повторный `seek(t)` даёт тот же кадр (проверено хешем).
- Редактор: вкладка **3D** (кадр, клипы, вес речи, настроение, взгляд,
  реплика → виземы, жесты, слайдеры костей, ключи позы). Правки идут
  postMessage-сообщениями `avatar-*`, без пересборки iframe.
- `SceneHost.post(type, data)` — общий live-канал в сцену.
- `scripts/fetch_avatar_anims.py` + `scripts/extract_avatar_anims.py` —
  скачивание Mixamo-клипов и сборка `avatar-anims.js`.
- `scripts/build_avatar_asset.py` — обёртка GLB в classic script для iframe.

#### Ошибка 18. Руки выворачивались в разные стороны
**Причина:** Mixamo-клипы сняты с T-pose, а RPM-аватар — в A-pose. Локальные
дельты и world-дельты давали разный результат; при world-дельте ломался локоть.
**Решение:** абсолютный world-ретаргет:
`W_tgt(t) = (W_tgt_rest * inv(W_src_rest)) * W_src(t)`, затем локальная
кватернионная цепочка. Плюс eye-кости исключены из ретаргета.
**Урок:** при разных rest-позах нельзя переносить дельту — переносится
абсолютная ориентация с поправкой на rest.

#### Ошибка 19. Пропадали голова и рука
**Причина:** Babylon считает frustum culling по статическому bounding box
skinned-меша; при повороте костей меш выходит за него и на кадр исчезает.
**Решение:** `mesh.alwaysSelectAsActiveMesh = true` для всех мешей аватара.
**Урок:** для skinned-мешей culling по bind-pose bbox — источник «мигающих»
частей тела.

#### Ошибка 20. Глаза постепенно уезжали вбок
**Причина:** eye-кости ретаргетились из Mixamo-клипов, где eye-look треки
плохо совместимы с RPM-ригом; поверх ещё добавлялся gaze.
**Решение:** `LeftEye`/`RightEye` не берутся из клипов; gaze считается
от rest-кватерниона, а не от текущего (без накопления).

#### Ошибка 21. Улыбка перетянута во время речи
**Причина:** `mood: joy` давал `mouthSmile* 0.75`, который складывался с
виземами; плюс вес речевого клипа 0.55.
**Решение:** веса улыбки снижены (0.35/0.18), дефолт `mood: neutral`,
`talk_weight` 0.4; в сиде тоже neutral.

#### Ошибка 22. Камера обрезала голову/руки
**Причина:** фиксированные radius/target не учитывали aspect и размах рук.
**Решение:** у presets появились `covW/covH`, `fit()` считает радиус из
вертикального и горизонтального покрытия; портрет — отдельный коэффициент.

#### Ошибка 23. Live-правки в редакторе пересобирали iframe
**Причина:** props обновлялись через `propsText`, а `SceneHost` реагировал
на изменение props пересозданием iframe (6 МБ GLB + 2.6 МБ клипов).
**Решение:** `SceneHost.post()` + сообщения `avatar-pose`, `avatar-visemes`,
`avatar-clips`, `avatar-gestures`, `avatar-preset`, `avatar-mood`,
`avatar-gaze`, `avatar-text`; props пишутся только по кнопке/Save.

### 2026-10-25 — SceneRig 1.0: свой контракт ригов и валидатор

- Решение: не изобретать бинарный формат скелета, а зафиксировать канон поверх
  glTF 2.0. Blender и Babylon работают с GLB нативно, JSON-манифест описывает
  риг, сокеты, клипы и лицо.
- Семейства: `human` (humanoid), `animal` (quadruped), `winged`
  (avian, insectoid). 21 обязательная кость у humanoid, крылья/лапы/хвост у
  животных и насекомых.
- Добавлены `docs/RIG_FORMAT.md`, `docs/ASSET_FORMAT.md`, JSON-схемы в
  `schemas/`.
- Добавлен stdlib-валидатор `backend/rig/`:
  - GLB/GLTF-парсер без зависимостей (JSON/BIN-чанки, аксессоры, world-матрицы);
  - алиасы Mixamo / RPM / Rigify / VRM;
  - проверки костей, весов (≤4 влияния, сумма ≈1), морфов, клипов, A-pose,
    взгляда `+Z`, роста, бюджета;
  - CLI `python -m backend.rig scan|validate|archetypes`.
- API `/rig/archetypes`, `/rig/health`, `POST /rig/validate` (upload).
- Прототип `core/public/rig-studio.html`: Babylon-превью, дерево костей,
  морфы, валидация через API, редактор/экспорт манифеста.
- Импорт `scripts/rig_import.py` → `core/public/models/brunette.scenerig.json`
  (67 костей, 72 морфа, 0 ошибок).
- Прототип `core/public/object-studio.html`: GLB-объект, габариты,
  pivot/ground/facing, сокеты, черновик `sceneasset/1`.
- API `/rig/validate` получил `require_rig` для статических объектов.
- Компилятор `backend/rig/compile.py`: переименование skin-джойнтов в канон,
  сборка GLB без внешних зависимостей. На brunette переименованы 67 костей;
  выходной манифест валиден без `bones.map`.
- Blender-экспортёр `scripts/blender/scene_rig_export.py`: проверка костей,
  весов, A-pose, взгляда; GLB + манифест + валидация. Проверен round-trip
  на тестовом риге (21 кость) и на RPM brunette (67 костей, 72 морфа).
- Проверено на `brunette.glb`: 67 костей, 72 морфа, 13 317 треугольников,
  0 ошибок, 2 предупреждения. 16 unit-тестов.

#### Ошибка 24. Валидатор показывал «head below hips»
**Симптом:** корректный RPM-аватар получал warning `pose.upside_down`, угол рук
был отрицательным.
**Причина:** `joint_names()` возвращает имена в порядке массива `skin.joints`,
а `joint_world_positions()` ключуется индексами **узлов** glTF. Словарь
канонических костей строился по индексам массива joints, а не по node index.
**Решение:** сопоставлять `zip(joint_names, skin_joint_indices)`.
**Урок:** в glTF индекс сустава в `skin.joints` и индекс узла в `nodes` — разные
пространства; смешивать их нельзя.

#### Ошибка 25. Компилятор не переименовывал кости
**Симптом:** `compile` писал `renamed_nodes=0`, хотя манифест содержал map.
**Причина:** `_source_map` возвращал `canonical -> source`, а цикл переименования
искал `source -> canonical`. Плюс переименовывались **все** узлы, включая меши
(`EyeLeft` конфликтовал с костью `LeftEye`).
**Решение:** возвращать `source -> canonical`; переименовывать только индексы
из `skin.joints`.
**Урок:** в GLB меши и кости живут в одном массиве `nodes`; трогать надо только
skin-джойнты.

#### 2026-10-25 — bake клипа и полный round-trip

- `backend/rig/bake.py`: `*.sclip.json` → glTF `animations[]` (body channels,
  resample 30 fps, quaternion slerp, accessors + bufferViews в BIN-чанк).
- Проверено end-to-end: `wave` (2 канала, 2 с) → baked GLB → Blender import
  (`action wave`, 0–48 кадров) → exporter → GLB снова валиден, анимация на месте.
- Лицо (morph weights) пока не печётся: warning `bake.face`.

### 2026-10-25 — чистка репозитория и подготовка к SceneRig

- Удалено **393** файла мусора и мёртвого кода:
  - 158 неиспользуемых Vue-компонентов (`components/slides`, `components/ui`,
    `_template`, `HelloWorld`), граф импортов от `main.js`/router пуст;
  - 78 старых slide/seed/fix/probe-скриптов (`build_*`, `fix_*`,
    `seed_components`, `seed_manifests`, `_orthodox_meta`, `_inbox` и т.п.);
  - ad-hoc тесты/пробы в `backend/` (`test_422`, `test_render*`, `fix_db*`);
  - root-мусор (`fix*.py`, `manual_fix*`, `probe_*`, `dump.sql.gz`,
    `test_bg*.html`);
  - legacy Rive-тест-страницы и неиспользуемые `.riv`-эксперименты;
  - собственный исходник Rive-рига `core/rive/` и его генератор.
- Из `backend/scene_library.py` убраны собственный Rive-объект
  `character-rive`, его шаблоны и capability-карточка. Остались готовые
  актёры `oldman`/`bob` и 3D-аватар как legacy-bridge; старые сцены в БД
  `/p/5`/`/p/6` продолжают работать на замороженном runtime.
- `.dockerignore` сокращает контекст сборки; `.gitignore` больше не обещает
  коммитить `dump.sql.gz`.
- Документация обновлена: SceneRig — основной путь, Rive — frozen legacy,
  порт Postgres на хосте `5437`.
- Проверки после чистки: все роутеры импортируются, 25 Python-тестов + 14 Node
  assertions проходят, Blender round-trip 0 ошибок.
- **Ошибка 26. Удалил `style_lint.py`, который импортируется роутерами.**
  Симптом: `presentations.py`/`components.py` падают на импорте.
  Решение: восстановил из архива, проверил импорт всех роутеров.
  Урок: перед удалением backend-модуля — `grep` по `from ..<module>`.

### 2026-10-25 — меню студий и библиотека объектов

- Добавлено меню «Студии» на главной и в `AppShell`:
  Object Studio, Rig Studio, Clip Editor (открываются в новой вкладке).
- Object Studio научился создавать/редактировать/удалять объекты:
  загрузка GLB в `/uploads/scene-assets`, список сохранённых, `POST/PUT/DELETE /scene-assets`.
- Новая таблица `scene_assets` (slug, title, kind, category, manifest, source_url)
  создаётся через `Base.metadata.create_all`.
- API `/scene-assets` + `/scene-assets/upload`; GLB валидируется SceneRig
  (`require_rig=false`).
- Проверено Playwright: сохранение URL-объекта, локальный upload, загрузка из
  библиотеки, удаление; меню на `/` и `/themes`.

### 2026-10-25 — Mark/Mira, Character Studio и первый SceneRig-дуэт

- Сгенерированы два low-poly персонажа из примитивов
  (`scripts/blender/make_poly_characters.py`): Mark (1.80 м) и Mira (1.69 м).
  Канонический humanoid-риг, 25 костей, 20 морфов (Oculus-15, blink, jawOpen,
  smile/frown), 2 клипа, CC0.
- `scene-rig.js` — канонический runtime: `seek(t)`, материалы/аксессуары,
  визёмы с кроссфейдом, моргание, idle/talk, камера/свет/тень.
- `character-studio.html` — настройки внешности и тест липсинка по тексту;
  сохранение/загрузка через `scene_assets`.
- `character-poly-duo` + `/p/11`; в библиотеке `character-mark`/`character-mira`.
- CORS для `/models`, `/vendor`, `/rive`, чтобы sandbox-iframe мог грузить GLB.
- Проверено: Character Studio (внешность, speak, library), `/p/11` в 16:9 и
  9:16, морфы визёмов в сцене, render `/p/11` → mp4 1920×1080/30fps/9.9 с.

#### Ошибка 27. Рот исчезал в Babylon, хотя в Blender был
**Симптом:** в Character Studio и сцене лицо без рта; при отключении скелета
рот появлялся.
**Причина:** у joined-объекта `Mouth` origin находился в центре рта, а shape
keys строились вокруг **мирового** центра. После экспорта это давало морфу
смещение ~1.57 м по Z. Runtime ставил `viseme_sil = 1`, и рот уезжал из кадра.
**Решение:** shape keys вокруг **локального** центра (centroid вершин), как и
для глаз. Плюс исправлена нормализация JOINTS_0 в `backend/rig/glb.py`
(не применять `normalized`, если флаг не выставлен).
**Урок:** для shape keys всегда локальные координаты; world-центр допустим
только для объектов с origin в 0.
