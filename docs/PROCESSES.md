# PROCESSES — как делается контент и код

## 1. Модель контента

```
Environment (мир)   forest | city | mountains | office | studio
      +
Objects (объекты)  car | road | tree | pine | cloud | bird | lamp | ...
      +
Mechanisms         wheels | sway | steam | flicker | cycle | walk | ...
      +
Cues (ключи)       at: 0/2200/4600 → set: { speed, brake, ... }
      =
Scene (сцена)      HTML + CSS + JS + props + duration
```

### Environment
Полноэкранный фон из слоёв. Слои помечаются `data-depth` для параллакса.
CSS-классы скоупятся `.env-<slug>`, чтобы миры композились без конфликтов.

### Object
Переиспользуемый HTML/CSS-сниппет. Класс `.obj-<slug>`.
Внутри могут быть `data-*`-крючки для механизмов:
- `data-wheel` — колесо,
- `data-depth` — слой параллакса,
- `data-*` — любые другие.

Объект не запускает анимацию сам. Анимацию запускает сцена через `seek(t)`.

### Mechanism
Именованная функция фазы. Пример:

```js
const wheels = [...document.querySelectorAll('[data-wheel]')]
const spin = SceneKit.mechanism({
  start: 0,
  speed: 1.5,
  loop: true,
  update(phase) {
    wheels.forEach((w) => { w.style.transform = `rotate(${phase * 360}deg)` })
  },
})
```

Для скорости, которая меняется ключами, используйте `cues.integrate('speed', t)`,
а не `phase`, чтобы колесо не «прыгало».

### Cue (ключ)
Событие на локальном таймлайне, которое меняет состояние:

```js
const cues = SceneKit.cues([
  { at: 0,    set: { speed: 1.4, brake: false } },
  { at: 2200, set: { speed: 2.9 } },
  { at: 4600, set: { speed: 0.35, brake: true } },
])
```

`cues.stateAt(t)` — состояние на момент `t`.
`cues.integrate('speed', t)` — интеграл скорости (фаза/дистанция) без скачков.

---

## 2. Создать сцену вручную

1. Открыть `/p/{id}` → «Редактировать» (или `E`).
2. `Scenes` — готовый шаблон; `Worlds` — только фон; `Objects` — вставить объект.
3. `HTML/CSS/JS` — доработать код.
4. `Props` — параметры (JSON).
5. `duration` / `start_time` — тайминг.
6. Сохранить.

## 3. Создать сцену через API

```bash
curl -X POST http://localhost:8002/presentations/1/scenes \
  -H 'Content-Type: application/json' \
  -d '{
    "slide_id":"scene-my-1",
    "component":"__scene__",
    "kind":"scene",
    "start_time":0,
    "duration":6000,
    "title":"My scene",
    "layout":"col",
    "order_index":0,
    "code":{"html":"...","css":"...","js":"..."},
    "props":{},
    "props_schema":{},
    "track":"main",
    "z_index":0,
    "data":{"payload":{}},
    "events":[]
  }'
```

## 3.5. HTML-слои сцены

Любая сцена строится по контракту:

```html
<div class="scene">
  <div class="layer layer-world" data-layer="world">...</div>
  <div class="layer layer-objects" data-layer="objects">...</div>
  <div class="layer layer-actors" data-layer="actors">...</div>
  <div class="layer layer-overlay" data-layer="overlay">...</div>
</div>
```

`_compose()` в `scene_library.py` уже раскладывает мир/объекты/персонажей по слоям.
Новый объект получает `class="obj-<slug>"`, новый персонаж — `category: "character"`.

## 3.6. Процедурная генерация

Для деревьев/птиц/кустов не дублируй слои вручную:

```js
SceneKit.scatter(root.querySelector('.obj-tree'), {
  count: p.tree_count || 6,
  x: [0.05, 0.95], y: [0.16, 0.32],
  scale: [0.6, 1.4], seed: 11,
})
```

`scatter` использует seeded PRNG → детерминизм сохраняется.

## 4. Добавить новый мир

1. В `backend/scene_library.py` добавить объект в `ENVIRONMENTS`:
   `slug`, `title`, `description`, `tags`, `layers`, `html`, `css`.
2. Классы скоупить `.env-<slug>`.
3. Слои для параллакса пометить `data-depth="0.1"`.
4. Перезапустить backend.
5. `GET /scene-library/environments` — проверить.

## 5. Добавить новый объект

1. В `OBJECTS`: `slug`, `title`, `category`, `description`, `tags`,
   `mechanics`, `html`, `css`.
2. Класс `.obj-<slug>`.
3. Механизмы — через `data-*`-атрибуты, не через собственный таймер.
4. Перезапустить backend.
5. `GET /scene-library/objects` — проверить.

## 6. AI-процесс генерации сцены

1. `GET /scene-library/templates` — посмотреть примеры.
2. `GET /scene-library/environments` — выбрать мир.
3. `GET /scene-library/objects` — выбрать объекты.
4. Сгенерировать `code.html` из мира + объектов.
5. Сгенерировать `code.css` из их CSS + сценарные правки.
6. Сгенерировать `code.js`:
   - `SceneKit.cues`
   - механизмы
   - `window.scene = { seek(t) { ... } }`
7. `POST /presentations/{id}/scenes`.
8. Проверить `window.__sceneReady`, `seek`, отсутствие ошибок.
9. Открыть `/p/{id}`.
10. При необходимости — правки в редакторе.

## 7. QA сцены

- [ ] Нет `rAF`, `Date.now`, `setInterval`, `Math.random`, `infinite`, `<animate>`.
- [ ] `seek(0)`, `seek(3000)`, `seek(6000)` дают осмысленные кадры.
- [ ] Нет скролла и обрезанных краёв.
- [ ] 16:9 и 9:16.
- [ ] В консоли iframe нет ошибок.
- [ ] `window.__sceneReady === true`.
- [ ] `duration > 0`, `start_time` не пересекается.
- [ ] `EndMarker` = `max(start+duration)+1000`.

## 8. Рендер

- Realtime: `backend/render_fullscreen_capture.py`.
- Ждёт `window.__sceneReady === true` перед `ffmpeg`/`play`.
- Длительность: `EndMarkerSlide`.
- Форматы: 1920×1080, 1080×1920, 1080×1080, 1920×1280, 1280×1920.
- Портрет: safe-zone 0.85 + сдвиг −2%.

## 9. Git-процесс

- Ветка `main`.
- Remote: `git@github.com:geronda94/2d-studio.git`.
- Коммитить только осмысленные изменения.
- Не коммитить `.env`, `uploads/`, `backend/media/`, `core/node_modules/`, `core/dist/`.
- Перед push: `npm run build` в `core`, `docker compose restart backend`, проверить API.

## 10. Сервер

См. `docs/SERVER.md`: клонирование, `.env`, docker compose, сиды, обновление.
