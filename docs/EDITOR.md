# EDITOR — редактор сцен: текущее и план

## 1. Текущее состояние

`core/src/scenes/SceneEditor.vue` — полноэкранный редактор одной сцены.

Вкладки:
- **Scenes** — готовые шаблоны.
- **Worlds** — миры (forest/city/...).
- **Objects** — объекты, отфильтрованные по совместимости с миром.
- **Layers** — объекты сцены + слайдеры.
- **Cues** — ключи локального таймлайна.
- **HTML / CSS / JS** — код сцены.
- **Props** — JSON параметров.
- **Info** — метаданные, view мира.

Превью — `SceneHost` с ручным временем, play/pause, слайдер 0..duration.

## 2. Как устроены слои

Редактор не хранит отдельную layer-модель. Он парсит `code.html`:

```js
const doc = new DOMParser().parseFromString(code.html, 'text/html')
const els = [...doc.body.querySelectorAll('*')].filter(el =>
  [...el.classList].some(c => c.startsWith('obj-')))
```

Каждому объекту ставится `data-layer-id="layer-N"`.
Для выбранного объекта:
- X (`left`), Y (`bottom`), ширина/высота, масштаб, поворот, opacity, z-index;
- view (per-object);
- duplicate/delete.

Слайдеры:
1. обновляют `code.html` (персистентность);
2. шлют `postMessage({ type: 'patch-style', id, styles })` в iframe,
   чтобы превью менялось без пересоздания iframe.

## 2.5. Подсветка синтаксиса

HTML/CSS/JS редактируются через CodeMirror 6 (`CodeEditor.vue`).
Подключён лениво (async component), чтобы не раздувать основной бандл.
Тема — oneDark.

## 2.6. Слои сцены (HTML-контракт)

Сцена размечается слоями:

```html
<div class="scene">
  <div class="layer layer-world" data-layer="world">...</div>
  <div class="layer layer-objects" data-layer="objects">...</div>
  <div class="layer layer-actors" data-layer="actors">...</div>
  <div class="layer layer-fx" data-layer="fx">...</div>
  <div class="layer layer-overlay" data-layer="overlay">...</div>
</div>
```

Правила:
- мир — только `layer-world`;
- объекты — `layer-objects`;
- персонажи — `layer-actors`;
- эффекты — `layer-fx` (pointer-events:none);
- текст/оверлеи — `layer-overlay` (pointer-events:none).
- Каждый объект имеет `class="obj-<slug>"` и `data-layer-id`.

Это даёт ИИ и редактору однозначную иерархию.

## 2.7. Процедурная генерация

`SceneKit.scatter(root, { count, x, y, scale, rotate, seed })` детерминированно
клонирует объект (деревья, птицы, кусты) с разбросом. Никакого `Math.random` —
только seeded PRNG. Параметры задаются в props (`tree_count`, `pine_count`, ...).

## 3. Ключи (Cues)

`form.cues = [{ at, set: { speed: 3, brake: true } }]`.
- В UI: таймлайн-маркеры, время, `key=value`.
- В iframe: `window.__sceneCues`.
- Шаблон читает:
```js
const cueList = (window.__sceneCues && window.__sceneCues.length)
  ? window.__sceneCues
  : defaultCues
const cues = SceneKit.cues(cueList)
```
- `SceneKit.cues` даёт `stateAt(t)` и `integrate(key, t)`.
- `integrate` обязателен, если скорость меняется ключами — иначе фаза прыгает.

## 4. Что добавить (приоритет)

### Phase A — управление
- [ ] Drag объекта на канвасе (pointer events).
- [ ] Resize-хэндлы.
- [ ] Snap к сетке/центру/другим объектам.
- [ ] Multi-select, align, distribute.
- [ ] Z-order drag в списке слоёв.
- [ ] Undo/redo на уровне сцены.
- [ ] Копировать/вставить объект между сценами.

### Phase B — ключи и кривые
- [ ] Keyframe-редактор по свойствам (X/Y/scale/opacity/rotation).
- [ ] Aggregate keyframes (Theatre-style).
- [ ] Tween/easing редактор.
- [ ] Focus range.
- [ ] Multi-track curve editor.
- [ ] Привязка ключей к аудио-акцентам.

### Phase C — review/approve
- [ ] Статусы: draft → review → approved → locked.
- [ ] Комментарии к времени/объекту.
- [ ] Diff версий (код/сцена/тайминг).
- [ ] Approve/Request changes/Reject.
- [ ] Audit trail.

### Phase D — Object Studio / ассеты
- [ ] Object Studio: создание объекта по промпту/фото (`OBJECT_STUDIO.md`).
- [ ] Asset library (см. `ASSETS.md`).
- [ ] Thumbnails.
- [ ] Варианты объектов/миров.
- [ ] Drag из библиотеки в сцену.

### Phase E — AI
- [ ] AI-чат с контекстом сцены.
- [ ] AI-предложение (`propose`) с превью и diff.
- [ ] AI QA (детерминизм, overflow, contrast).
- [ ] «Сделай 3 варианта», «переделай под 9:16».

## 5. UX-принципы

- Сначала читаемый финальный кадр, потом анимация.
- Слайдеры — для быстрых правок; код — для структуры.
- Любое изменение AI — через preview/diff/approve.
- Не перегружать: один главный акцент на сцену.
- Все ошибки — в `scene_learnings`.

## 6. Технические заметки

- `SceneHost` в редакторе — `preview`: не владеет глобальным handshake.
- `docKey` включает `code`, `props`, `cues`, `format`, `view`.
- `patch-style` работает только для уже существующих `data-layer-id`.
- При изменении структуры HTML iframe пересобирается (debounce 180 мс).
- `DOMParser` может менять форматирование HTML — это нормально.
