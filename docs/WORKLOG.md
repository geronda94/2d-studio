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
