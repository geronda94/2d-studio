# ENGINE — как устроен SceneEngine

Полный обзор движка для агента, который подхватывает работу. Детали сцены —
`SCENES.md`, API — `API.md`, редактор — `EDITOR.md`, процессы — `PROCESSES.md`.

---

## 1. Назначение

SceneEngine — движок для производства **2D-сцен** и видео:
- сцена = HTML + CSS + JS + props;
- время детерминировано: `window.scene.seek(t)`;
- библиотека миров, объектов и механизмов;
- редактор с кодом, слоями и ключами;
- рендер в mp4;
- human+AI контроль (см. `HUMAN_AI_STUDIO.md`).

---

## 2. Стек и инфраструктура

| Слой | Технология | Порт |
|---|---|---|
| Frontend | Vue 3 + Vite + Tailwind | `5175` |
| Backend | FastAPI + SQLAlchemy | `8002` |
| БД | PostgreSQL (`scene_db`) | `5436` |
| Compose | `scene-saas` | — |

Запуск: `docker compose up -d`. Сиды: `docs/DEV.md`.

---

## 3. Карта репозитория

```
backend/
  main.py                 FastAPI, роутеры, ensure columns
  models.py               Project/Folder/Presentation/Slide/SceneLearning/...
  schemas.py              Pydantic-схемы
  routers/
    presentations.py      презентации + сцены (/scenes)
    scene_library.py      миры/объекты/шаблоны/совместимость/learnings
    renders.py            рендер-джобы
    ai.py                 TTS/генерация
  render_fullscreen_capture.py
  scene_library.py        ENVIRONMENTS / OBJECTS / TEMPLATES

core/src/
  views/MainPresentation.vue     загрузка, плеер, редактор
  components/engine/             SlidePresentation, Slide, AudioTimeline
  scenes/
    SceneHost.vue                iframe + seek + handshake + theme
    SceneEditor.vue              редактор сцены
    runtime.js                   srcdoc, GSAP, SceneKit, cues, patch-style
    demoScene.js                 fallback
  composables/useDirector.js     глобальные часы
  composables/useAudioEngine.js  аудио-клипы
  services/api.js                API-клиент

core/public/vendor/
  gsap.min.js             локальный GSAP
  scene-kit.js            cues/integrate/mechanism/parallax/views

docs/                     документация
scripts/                  сиды и утилиты
```

---

## 4. Поток данных

```
GET /presentations/{id}
  → presentation.slides[] (сцены + EndMarker)
  → MainPresentation
  → SlidePresentation (плеер, таймлайн)
  → Slide (v-show, bare для сцены)
  → SceneHost (iframe, theme, props, cues)
  → window.scene.seek(t)
```

Глобальное время: `useDirector.currentTime`.
Локальное время сцены: `currentTime - slide.start_time`.

---

## 5. Контракт сцены

```js
window.scene = {
  ready?: Promise,
  seek(t) { /* t, мс от старта сцены */ },
  destroy?() {}
}
```

В iframe доступны:
- `window.__sceneProps` — props сцены;
- `window.__sceneCues` — ключи из редактора;
- `window.gsap` — GSAP;
- `window.SceneKit` — cues/integrate/mechanism/parallax/views;
- CSS-переменные темы.

Запрещено: `rAF`, `Date.now`, `performance.now`, `setInterval` для анимации,
`Math.random` без seed, бесконечные CSS/SVG-анимации, внешний `fetch`.

---

## 6. Жизненный цикл сцены

1. `SceneHost` монтирует iframe с `srcdoc`.
2. Сцена строит DOM, ждёт шрифты/картинки, отправляет `scene-ready`.
3. `SceneHost` ставит `window.__sceneReady = true`, `window.__sceneSeek = seek`.
4. На каждое изменение времени шлёт `{ type: 'seek', t }`.
5. Сцена отвечает `seek-done`.
6. Рендерер ждёт `__sceneReady` перед захватом.
7. При смене сцены старый iframe размонтируется, новый проходит цикл.

Handshake описан в `SCENES.md` §6.

---

## 7. SceneKit

```js
SceneKit.cues(list)        // stateAt(t), integrate(key, t)
SceneKit.mechanism(spec)   // фаза от start/speed/loop
SceneKit.parallax(layers)  // translate по depth
SceneKit.views(root, map)  // per-object view-классы
SceneKit.compose(...)      // объединить механизмы
```

Ключи: `[{ at, set: { speed: 3, brake: true } }]`.
`integrate` нужен, чтобы скорость можно было менять без скачка фазы.

---

## 8. Библиотека

- `ENVIRONMENTS`: forest, city, mountains, office, studio.
- `OBJECTS`: character, car, road, tree, pine, cloud, bird, street-lamp,
  building, desk, monitor, coffee, plant, person, traffic-light, sun, moon.
- `TEMPLATES`: forest-drive, city-night-drive, mountain-flight, office-day,
  studio-intro.

Метаданные:
- мир: `domain` (outdoor/indoor/stage), `views`, `default_view`, `perspective`;
- объект: `domain`, `environments`, `surface`, `views`, `default_view`,
  `mechanics`, `rig` (для персонажа).

Совместимость:
```
GET /scene-library/environments/{slug}/objects
GET /scene-library/objects?environment=forest
GET /scene-library/compatibility
POST /scene-library/validate-composition
```

---

## 9. Редактор

`SceneEditor.vue`:
- вкладки `Scenes / Worlds / Objects / Layers / Cues / HTML / CSS / JS / Props / Info`;
- превью `SceneHost` с ручным временем;
- `Layers`: парсит `.obj-*`, слайдеры X/Y, размер, масштаб, поворот,
  opacity, z-index; duplicate/delete; live-patch в iframe;
- `Cues`: маркеры, время, `key=value`, add/delete; live-preview;
- `Props`: JSON параметров;
- `Code`: HTML/CSS/JS.

Слайдеры используют `data-layer-id` и `postMessage({type:'patch-style'})`,
чтобы не пересобирать iframe на каждый тик.

---

## 10. Тайминг и длительность

- `slide.start_time` — старт на глобальном таймлайне.
- `slide.duration` — длительность сцены.
- `EndMarkerSlide.start_time` = `max(start + duration) + 1000`.
- Минимальная дистанция между стартами — 2000 мс.
- `renders.py` использует EndMarker как якорь конца.

---

## 11. Аудио

`presentation.audio_timeline`:
```json
{ "tracks": [ { "id": "main", "clips": [ { "src": "...", "start_time": 0, "end_time": 3200, "volume": 1 } ] } ] }
```
`useAudioEngine` синхронизирует клипы с `currentTime`. Сцена может добавлять
SFX через события/виртуальные клипы.

---

## 12. Рендер

`backend/render_fullscreen_capture.py`:
- Playwright открывает `/p/{id}?render=true`;
- ждёт `window.__sceneReady`;
- ffmpeg `x11grab` + pulse;
- длительность = EndMarker;
- форматы: 1920×1080, 1080×1920, 1080×1080, 1920×1280, 1280×1920;
- портрет: safe-zone 0.85 / shift -2%.

Покадровый `engine=frame` — будущая опция, не замена.

---

## 13. Данные

Основные таблицы:
- `projects`, `folders`, `presentations`;
- `slides` (внутри — сцены, `component='__scene__'`);
- `slide_data` (payload);
- `design_tokens`, `style_variants`;
- `media_files`;
- `render_jobs`;
- `scene_learnings` (реестр ошибок/правил).

Поля сцены: `kind`, `duration`, `code`, `props`, `props_schema`, `track`,
`z_index`.

---

## 14. Human+AI

Ворота: brief → storyboard → scene → animation/cues → QA → render → publish.
AI предлагает, человек утверждает.
AI читает `scene_learnings` перед генерацией и пишет новые после QA.
Подробно — `HUMAN_AI_STUDIO.md`.

---

## 15. Разработка

```bash
cd Projects/SceneEngine
docker compose up -d
docker compose restart backend   # после Python
# frontend — Vite HMR
npm run build                    # в core
```

Проверка:
```bash
curl -s http://localhost:8002/presentations/1/scenes
curl -s http://localhost:8002/scene-library/templates
curl -s http://localhost:8002/scene-library/environments/forest/objects
curl -s http://localhost:8002/scene-library/learnings
```

---

## 16. Известные ограничения

- Таблица называется `slides` (исторически).
- 117 старых Vue-компонентов и 16 slide-обёрток — мёртвый код.
- Нет frame-step рендера.
- Нет drag/resize на канвасе (только слайдеры).
- Нет полноценного keyframe-редактора (только cues).
- Нет asset library/DAM.
- Персонажи — SVG-заготовка, без visemes/липсинка.
- Нет review/approve/diff в UI.
