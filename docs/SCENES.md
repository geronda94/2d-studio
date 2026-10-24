# SCENES.md — контракт сцен SceneEngine

> Это главный документ форка. Сцена — не «слайд с компонентом», а **самостоятельная
> веб-страница**, которая умеет рисовать себя в заданный момент времени.

---

## 1. Что такое сцена

Сцена = HTML + CSS + JS + `props`.

Она живёт в sandboxed iframe и обязана реализовать один контракт:

```js
window.scene = {
  ready?: Promise,          // шрифты/картинки/ассеты (необязательно)
  seek(t) { ... },          // t — миллисекунды от старта сцены
  destroy?() { ... }        // очистка (необязательно)
}
```

`t` — **единственный источник времени**. Никакого `Date.now()`, `requestAnimationFrame`,
`setInterval`, бесконечных CSS-анимаций. Один и тот же `t` обязан давать один и тот же кадр
в браузере, в редакторе и в рендере.

### Параметры сцены

`props` доступны внутри сцены как:

```js
const p = window.__sceneProps || {}
```

`props` — это «пульт»: текст, цвета, числа, массивы. Редактор показывает их как форму,
ИИ может менять их вместе с кодом.

### Тема

В iframe уже инжектнуты CSS-переменные темы:

```css
var(--bg-base) var(--bg-surface) var(--text-primary) var(--text-secondary)
var(--brand-blue) var(--brand-light-blue) var(--brand-green)
var(--font-sans) var(--font-heading) var(--font-mono)
```

Использовать только их (или `color-mix` от них), не хардкодить палитру.

### Формат кадра

Сцена заполняет весь iframe. iframe уже отмасштабирован под:
- 16:9 (desktop / YouTube long-form);
- 9:16 (Shorts / mobile);
- 1:1 (square), 1920×1280 (landscape).

Внутри сцены можно использовать `vw/vh/%` и `@media (orientation: portrait)`.
Хост сам применяет safe-zone для портретного рендера.

---

## 2. Детерминизм — обязательные правила

| Нельзя | Почему | Как правильно |
|---|---|---|
| `requestAnimationFrame` | не сикается | `seek(t)` |
| `Date.now()` / `performance.now()` | зависит от wall-clock |время только из `t` |
| `setInterval` для анимации | не детерминировано | GSAP timeline + `seek` |
| `animation: ... infinite` | не сикается | CSS transition/transform от `t` |
| `<animate>` / `<animateMotion>` | не сикается | JS/SVG от `t` |
| `Math.random()` без seed | разный кадр | фиксированные значения / seeded PRNG |
| `fetch()` внешних API | рендер может быть offline | данные через `props` |
| `document.write` | ломает документ | обычный DOM |

Рекомендуемый способ — **paused GSAP timeline**:

```js
const tl = gsap.timeline({ paused: true })
tl.from('.title', { y: 60, opacity: 0, duration: .8 })
  .from('.sub', { opacity: 0, duration: .5 }, .4)

window.scene = { seek(t) { tl.seek(t / 1000) } }
```

GSAP уже загружен в iframe (`window.gsap`) локально из `core/public/vendor/gsap.min.js`.
Никаких CDN в сцене.

Медиа: `img`/`video` должны быть готовы до первого кадра. Хост ждёт `document.fonts.ready`
и `img.onload`; для видео на первом этапе лучше не использовать, либо ставить постер.

---

## 3. Данные сцены

Таблица `slides` (сохранена для совместимости с таймлайном/рендером) содержит поля сцены:

| Поле | Тип | Смысл |
|---|---|---|
| `component` | string | `__scene__` для сцены |
| `kind` | string | `scene` / `legacy` |
| `start_time` | float | старт на глобальном таймлайне, мс |
| `duration` | float | длительность сцены, мс |
| `code` | JSON | `{ html, css, js }` |
| `props` | JSON | параметры сцены |
| `props_schema` | JSON | схема формы параметров |
| `track` | string | `main` (задел на слои) |
| `z_index` | int | задел на наложения |
| `data.payload` | JSON | дублирующий снимок для обратной совместимости |

`EndMarkerSlide` остаётся техническим маркером конца видео, но его `start_time`
автоматически синхронизируется с `max(start_time + duration)`.

---

## 4. API

### Сцены

```http
GET    /presentations/{presentation_id}/scenes
POST   /presentations/{presentation_id}/scenes
PUT    /presentations/scenes/{scene_id}
DELETE /presentations/scenes/{scene_id}
```

Тело создания/обновления:

```json
{
  "slide_id": "scene-1720000000000",
  "component": "__scene__",
  "kind": "scene",
  "start_time": 0,
  "duration": 5000,
  "title": "Название",
  "layout": "col",
  "order_index": 0,
  "code": { "html": "...", "css": "...", "js": "..." },
  "props": {},
  "props_schema": {},
  "track": "main",
  "z_index": 0,
  "data": { "payload": {} },
  "events": []
}
```

Валидация сцены: `code` — объект, `html/css/js` — строки, `duration > 0`.
Ошибка — `422 { message, errors }`.

### Библиотека

```http
GET /scene-library/templates
GET /scene-library/templates/{slug}
GET /scene-library/objects
```

`templates` — готовые сцены (`code`, `props_schema`, `default_props`, `duration`, `tags`).
`environments` — миры: `forest`, `city`, `mountains`, `office`, `studio`.
`objects` — физические объекты: `car`, `road`, `tree`, `pine`, `cloud`, `bird`,
`street-lamp`, `building`, `desk`, `monitor`, `coffee`, `plant`, `person`,
`traffic-light`, `sun`, `moon` (`html`, `css`, `mechanics`).

В iframe также доступен `window.SceneKit`:

```js
const cues = SceneKit.cues([{ at: 0, set: { speed: 1 } }, { at: 2000, set: { speed: 3 } }])
const dist = cues.integrate('speed', t) // без скачков фазы
const wheel = SceneKit.mechanism({ start: 0, speed: 2, update(phase) { /* ... */ } })
const layers = SceneKit.parallax([{ el, depth: 0.2 }])
```

`SceneKit` — не обязателен, но рекомендован для механизмов и ключей.

### Справочник SceneKit

| Метод | Что делает |
|---|---|
| `cues(list, {smooth})` | Ключи локального таймлайна: `stateAt(t)`, `integrate(key,t)`, `valueAt(key,t)`. `smooth: true` — плавная (smoothstep) интерполяция между ключами вместо ступенейки |
| `mechanism({start,speed,loop,update})` | Механизм с фазой (колёса, качание, пар) |
| `parallax(layers, {speed})` | Параллакс слоёв по глубине |
| `camera(layers, {path})` | 2.5D-камера: `path(t) → {x,y,z,zoom,rot}` |
| `scatter(root, {count,x,y,scale,rotate,seed})` | Массовое размножение объекта с детерминированным PRNG |
| `mulberry32(seed)` | Seeded PRNG (без `Math.random`) |
| `views(root, map)` | Переключение вида объектов (`.view-front`, `.view-side`…) |
| `compose(...items)` | Свести несколько `seek(t)`-драйверов в один |
| `visemeAt(visemes, t)` | Номер визема в момент `t` |
| `visemeBlend(visemes, t, blend)` | `{cur, next, k}` — кроссфейд форм рта |
| `lipsync({visemes, blend, onViseme, onVisemePair})` | Драйвер липсинка |
| `characterRig(el, opts)` | Управляемый персонаж: виземы, моргание, взгляд, дыхание, брови-настроение, жесты, ходьба |
| `particles(canvas, opts)` | Детерминированные частицы на canvas (пыль, снег, искры) |
| `idle(root, {index})` | Микро-анимация: дыхание, качание, моргание (портрет или SVG-риг) |
| `grain(root, opts)` | Пост-обработка кадра: зерно + виньетка + цветовая коррекция |
| `shadow(el, opts)` | Контактная тень под объектом |

Пример премиум-кадра:

```js
const tl = gsap.timeline({ paused: true });
tl.from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out' });
const dust = SceneKit.particles(root.querySelector('.dust'), { count: 40, seed: 7 });
SceneKit.grain(root);
window.scene = { seek(t) { tl.seek(t / 1000); dust.seek(t); } };
```

---

## 5. Редактор

`core/src/scenes/SceneEditor.vue`:
- вкладки `Templates` / `Objects` / `HTML` / `CSS` / `JS` / `Props` / `Info`;
- живое превью через `SceneHost` с ручным `time`;
- кнопки `Сохранить` / `Удалить` / `Закрыть`;
- `start_time` и `duration` в шапке.

`SceneHost.vue`:
- строит sandboxed iframe (`sandbox="allow-scripts"`);
- инжектит тему и GSAP;
- отправляет `seek(t)` при каждом изменении времени;
- ждёт `scene-ready` и шлёт `seek-done`.

---

## 6. Handshake готовности (что это)

Handshake — это сигнал «сцена готова к кадру». Без него рендер может начать захват,
когда шрифты/картинки/GSAP ещё не загрузились, и первые секунды видео будут пустыми.

Механика:

1. `SceneHost` монтирует iframe.
2. Сцена загружает GSAP, строит DOM, ждёт `document.fonts.ready` и картинки.
3. Сцена отправляет `postMessage({ type: 'scene-ready' })`.
4. `SceneHost` ставит `window.__sceneReady = true` и `window.__sceneSeek = seek`.
5. Рендерер (`render_fullscreen_capture.py`) ждёт `window.__sceneReady === true`
   перед стартом `ffmpeg` и `play()`.
6. На каждый `seek(t)` сцена отвечает `seek-done`; для будущего покадрового рендера
   можно ждать этот ответ.

---

## 7. Рендер и форматы

- Realtime-захват сохранён: `backend/render_fullscreen_capture.py`.
- Длительность: `EndMarkerSlide`, синхронизированный с `max(start + duration)`.
- Форматы: `default 1920×1080`, `mobile 1080×1920`, `square 1080×1080`,
  `landscape 1920×1280`, `portrait 1280×1920`.
- Портрет: safe-zone `0.85` + сдвиг `−2%` (как в исходном проекте).
- В будущем: покадровый `engine=frame` (seek → screenshot → ffmpeg), без удаления realtime.

---

## 8. Карта файлов

```
core/src/scenes/
  SceneHost.vue      iframe + sandbox + seek + theme + ready
  SceneEditor.vue    редактор сцены
  runtime.js         сборка srcdoc, тема, GSAP, протокол
  demoScene.js       стартовая сцена

backend/
  scene_library.py   шаблоны и объекты
  routers/scene_library.py
  routers/presentations.py  /scenes CRUD
  models.py          поля сцены
  render_fullscreen_capture.py  handshake

docs/
  SCENES.md          этот файл
  DEV.md             порты и запуск
  LEGACY_AGENTS.md   старые правила слайдов (не использовать для новых сцен)
```

---

## 9. Чек-лист перед сохранением сцены

- [ ] `window.scene.seek(t)` есть и не использует wall-clock.
- [ ] Нет `rAF`, `setInterval`, `Date.now`, `Math.random`.
- [ ] Нет бесконечных CSS/SVG-анимаций.
- [ ] Контент заполняет кадр, нет скролла и обрезанных краёв.
- [ ] Текст короткий, числа сходятся с озвучкой.
- [ ] Валюта только `€`, эмодзи нет.
- [ ] Цвета — токены темы, не случайный hex.
- [ ] Сцена проверена в 16:9 и 9:16.
- [ ] `duration` больше 0 и соответствует смыслу.
