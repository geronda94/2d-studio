# AGENTS.md — правила для ИИ-агентов SceneEngine

Этот репозиторий — форк движка презентаций, перестроенный под **динамические сцены**.
Старые правила слайдов и 100+ компонентов лежат в `docs/legacy/LEGACY_AGENTS.md` и **не используются**.

> **2026-10-27: 3D/Babylon заморожен.** Production-персонажи — Canvas 2D
> `PaperCast`: один скелет, скины, 31 поза, 82 фонемы. 3D-код и GLB лежат
> только в `drafts/3d/` и не загружаются. Подробно: `docs/CANVAS_CHARACTERS.md`.
> Не создавай новые 3D-сцены и не возвращай Babylon в `core/public` без
> явного запроса.

Главный документ: **`docs/SCENES.md`**. Порты и запуск: **`docs/DEV.md`**.
Текущий этап: **`docs/STATUS.md`**. Вектор: **`docs/ROADMAP_2D.md`**.
Анимация: **`docs/ANIMATION.md`**. Ошибки/решения: **`docs/WORKLOG.md`**.
Решения: **`docs/DECISIONS.md`**.
Human+AI продукт: **`docs/HUMAN_AI_STUDIO.md`**. Персонажи: **`docs/CHARACTERS.md`**.
Анатомия и диапазоны суставов: **`docs/ANATOMY_RIG.md`**.
Липсинк: **`docs/LIPSYNC.md`**.
Архитектура: **`docs/ENGINE.md`**. API: **`docs/API.md`**. Редактор: **`docs/EDITOR.md`**.
Ассеты: **`docs/ASSETS.md`**. Риги: **`docs/RIG_FORMAT.md`**, студия: **`docs/RIG_STUDIO.md`**.
Позы/жесты/гардероб/зоопарк скелетов/2.5D: **`docs/PAPERCAST_ROADMAP.md`**.
Аудит и план устранения: **`docs/PAPERCAST_AUDIT.md`**. Бэклог: **`docs/PAPERCAST_BACKLOG.md`**.
Директор сцен (окружение, каст, тайминги из конфига): **`docs/PAPERCAST_DIRECTOR.md`**. Объекты/окружения: **`docs/ASSET_FORMAT.md`**. Ошибки/правила: **`docs/LEARNINGS.md`**.
Object Studio: **`docs/OBJECT_STUDIO.md`**. Режимы сцен: **`docs/SCENE_MODES.md`**. UI студий: **`docs/PAPERCAST_UI.md`**.
Канал: **`docs/CHANNEL_PRAVOSLAVIE.md`**. Роли ИИ: **`docs/AGENT_ROLES.md`**.
Как делать контент: **`docs/PROCESSES.md`**. Сервер: **`docs/SERVER.md`**.
Аудит и конвейер DeepSeek: **`docs/CLAUDE_ANALYSIS.md`**.

---

## 1. Что здесь «сцена»

Сцена — свободная HTML/CSS/JS-страница в sandboxed iframe. Она обязана реализовать:

```js
window.scene = {
  ready?: Promise,
  seek(t) { /* отрисовать состояние на t мс */ },
  destroy?() {}
}
```

`window.__sceneProps` — параметры сцены из БД.
`window.gsap` — локальный GSAP, уже загружен.
`window.SceneKit` — `cues`, `integrate`, `mechanism`, `parallax`, `compose`.
`SceneKit.cues` — ключи локального таймлайна; `integrate` — интеграл скорости,
чтобы механизмы не «прыгали» при смене ключа.
CSS-переменные темы (`--bg-base`, `--text-primary`, `--brand-blue`, `--font-heading`, ...)
уже инжектнуты.

**Запрещено:** `requestAnimationFrame`, `Date.now()`, `performance.now()`, `setInterval`
для анимации, бесконечные CSS/SVG-анимации (`infinite`, `<animate>`), `Math.random()` без seed,
внешние `fetch`.

**Разрешено:** paused GSAP timeline + `seek`, CSS `transform`/`opacity` от `t`,
детерминированная математика, `props`.

---

## 2. Как создать сцену через API

```http
POST http://localhost:8002/presentations/{presentation_id}/scenes
Content-Type: application/json
```

```json
{
  "slide_id": "scene-1720000000000",
  "component": "__scene__",
  "kind": "scene",
  "start_time": 0,
  "duration": 5000,
  "title": "Название сцены",
  "layout": "col",
  "order_index": 0,
  "code": {
    "html": "<div class=\"scene\">...</div>",
    "css": ".scene{position:absolute;inset:0;background:var(--bg-base)}",
    "js": "const tl=gsap.timeline({paused:true});...;window.scene={seek(t){tl.seek(t/1000)}}"
  },
  "props": {},
  "props_schema": {},
  "track": "main",
  "z_index": 0,
  "data": { "payload": {} },
  "events": []
}
```

Обновление: `PUT /presentations/scenes/{scene_id}`.
Удаление: `DELETE /presentations/scenes/{scene_id}`.

Валидация: `code` — объект, `html/css/js` — строки, `duration > 0`. Иначе `422`.

---

## 3. Библиотека

Перед генерацией сцены с нуля проверь готовые шаблоны и объекты:

```http
GET http://localhost:8002/scene-library/templates
GET http://localhost:8002/scene-library/templates/{slug}
GET http://localhost:8002/scene-library/environments
GET http://localhost:8002/scene-library/environments/{slug}
GET http://localhost:8002/scene-library/objects
GET http://localhost:8002/scene-library/objects/{slug}
GET http://localhost:8002/scene-library/characters
GET http://localhost:8002/scene-library/characters/{slug}
```

- `templates` — полные сцены (`code`, `props_schema`, `default_props`, `duration`, `tags`).
- `environments` — миры: forest / city / mountains / office / studio.
- `objects` — физические объекты: car / road / tree / pine / cloud / bird / lamp / ...
  (`html`, `css`, `mechanics`).
- `characters` — готовые Rive-актёры (`character-oldman`, `character-bob`,
  `character-rive`): режим драйвера, лицензия, виземы, возможности.

Бери мир + объекты за основу и меняй `props`/код под сценарий.
**Не делай UI-карточки и дашборды** — это не сцены.

---

## 3.5. HTML-слои сцены (обязательно)

```html
<div class="scene">
  <div class="layer layer-world" data-layer="world">...</div>
  <div class="layer layer-objects" data-layer="objects">...</div>
  <div class="layer layer-actors" data-layer="actors">...</div>
  <div class="layer layer-fx" data-layer="fx">...</div>
  <div class="layer layer-overlay" data-layer="overlay">...</div>
</div>
```

- мир → `layer-world`;
- объекты → `layer-objects`;
- персонажи → `layer-actors`;
- эффекты → `layer-fx`;
- текст/оверлеи → `layer-overlay`.
- каждый объект: `class="obj-<slug>"`, `data-layer-id`.

## 3.6. 3D-аватар (архив, заморожен)

- Шаблон `character-3d`, драйвер `SceneKit.babylonCharacter`
  (`core/public/vendor/babylon-character.js`).
- GLB + мокап-клипы: `core/public/models/`; для iframe — base64-обёртка `.glb.js`.
- Mixamo-клипы не коммитить в публичный репозиторий; скачивать
  `scripts/fetch_avatar_anims.py` + `scripts/extract_avatar_anims.py`.
- Управление: `setPose`, `setVisemes`, `setClips`, `setGestures`, `setMood`,
  `setGaze`; из редактора — сообщения `avatar-*`.

## 3.7. Риги и персонажи (SceneRig 1.0, архив)

- Канон: `human` / `animal` / `winged` (`humanoid`, `quadruped`, `avian`, `insectoid`).
- Формат и правила: `docs/RIG_FORMAT.md`; объекты/окружения: `docs/ASSET_FORMAT.md`.
- Skeletons — glTF 2.0, A-pose, метры, взгляд `+Z`, origin между ступнями.
- Не ретаргетить в рантайме: клип авторится на каноне; адаптеры — только импорт.
- Перед сдачей: `python -m backend.rig validate <manifest>` без ошибок,
  затем `python -m backend.rig compile <manifest> --out dist/`;
  клип: `python -m backend.rig bake <manifest> <clip> --out dist/`.
- Объект/персонаж: `core/public/rig-studio.html`, `core/public/object-studio.html`,
  `core/public/clip-editor.html`.
- Blender: `scripts/blender/scene_rig_export.py` (GLB + манифест + проверка);
  генератор полигональных персонажей `scripts/blender/make_poly_characters_v3.py`
  (пресеты — `assets/characters/presets/*.json`).
- Rive остаётся legacy-рантаймом; round-trip в Rive не делаем.
- Mixamo-клипы не коммитить в публичный репозиторий.

### 3.7.1. Руки и кисти — жёсткое правило

Симптом, который повторялся: «руки вывернуты назад», ладонь смотрит наружу,
пальцы уходят за спину. Причины и запреты:

- **Ладонь к бедру.** При генерации кисти:
  `add_oriented_sphere(..., d, (0, sx, 0))`, где `sx = +1` для L и `-1` для R.
  Нельзя использовать `(0, 1, 0)` для обеих рук: у правой ладонь смотрит наружу.
- **Пальцы вниз по предплечью**, большой палец — вперёд (`-Y`). Не разворачивать
  кисть «для красоты».
- **Никакого `rotate_mesh` вокруг оси руки.** Любой дополнительный roll
  (даже 32°) уводит пальцы назад.
- **В рантайме `lowerArm` X < 0** сгибает локоть вперёд. `X > 0` — это сгиб
  за спину; так делать нельзя.
- **Проверять обе руки сбоку**: камера `+X` и `-X`, rest и talk-позу.
  Вид спереди эту ошибку не показывает.
- **Плечо:** рукав — 3 кольца у плеча с весами `shoulder/chest → shoulder/upperArm → upperArm`.
  Отдельный патч, привязанный на 100% к `upperArm`, при подъёме руки
  превращается в шар. Патч (если нужен) — только 50/50 и маленький.
- **Wave проверять сзади** (`+Y`) и в 3/4: шар/щель видны именно там.
- Изменения кистей/локтей фиксировать тестом-рендером `side` до деплоя.

## 4. Модель 2D-сцены

```
Environment + Objects + Mechanisms + Cues = Scene
```

- Окружение — слои с `data-depth` для параллакса.
- Объект — `.obj-<slug>`, крючки `data-wheel`, `data-depth`, ...
- Механизм — функция фазы от `t` (колёса, качание, пар, светофор).
- Ключ — `{ at, set }` на локальном таймлайне.
- Массовые объекты (деревья/птицы) — `SceneKit.scatter(...)`, не дублировать вручную.
- «3D-вид» — `SceneKit.camera` + слои/глубина, не плоский zoom.
- Уникальные сцены можно писать с нуля; библиотека не обязательна.
- Персонаж — объект `character` (SVG-риг) + `SceneKit.characterRig` (липсинк,
  моргание, взгляд, настроение, жесты). Рот — только виземы, не `Math.sin`.

Пример:

```js
const cues = SceneKit.cues([
  { at: 0,    set: { speed: 1.4, brake: false } },
  { at: 2200, set: { speed: 2.9 } },
  { at: 4600, set: { speed: 0.35, brake: true } },
])
function seek(t) {
  const dist = cues.integrate('speed', t) * 90
  wheels.forEach(w => { w.style.transform = `rotate(${cues.integrate('speed', t) * 360}deg)` })
  car.style.transform = `translate3d(${dist}px,0,0)`
}
window.scene = { seek }
```

## 5. Правила контента

- Текст короткий: заголовок ≤ 6 слов, пункт ≤ 6 слов, описание ≤ 90 символов.
- Не дублируй озвучку дословно — передавай смысл.
- Валюта только `€`. Эмодзи запрещены.
- Цвета — токены темы, не случайный hex.
- Заполняй кадр: нет пустот > 25%, нет скролла, нет обрезанных краёв.
- Числа и суммы сходятся со сценарием/озвучкой.
- Одна сцена = один смысловой бит. Длительность 3–6 с, оптимум 5–7 с.
- Между стартами соседних сцен ≥ 2000 мс.

## 5.5. Стандарт кинематографичности (минимум 5 из 7)

Подробно — `docs/ANIMATION.md`, раздел 1.5. Эталон — шаблон
`character-talk`.

1. Плавные кривые: `gsap.timeline({paused:true})` + `tl.seek(t/1000)`,
   easing `power4.out` / `power2.inOut` / `expo.out`.
2. Частицы: `SceneKit.particles(canvas, {...})` — пыль, снег, искры.
3. Кадр, а не страница: `SceneKit.grain(root)` — зерно + виньетка + грейд.
4. Объекты стоят на земле: `SceneKit.shadow(el, {...})`.
5. Кинетическая типографика: маска + `yPercent` ревил, `letterSpacing`, stagger.
6. Вторичные реакции: фон живой (качание, пыль, дрейф света, дрейф камеры).
7. Рот — виземы (`SceneKit.characterRig`, `visemeBlend`), не `Math.sin`.

Ключи — только плавно: `SceneKit.cues(list, { smooth: true })`.

---

## 6. Форматы

Сцена обязана работать в 16:9 и 9:16.

- Используй `vw/vh/%`, `clamp()`, `@media (orientation: portrait)`.
- Не хардкодь размеры под один формат.
- Портретный рендер сам применяет safe-zone (0.85), не дублируй её.
- Проверяй, что текст не уезжает за кадр в обоих форматах.

---

## 7. Редактор и handshake

- Редактор: `core/src/scenes/SceneEditor.vue`.
- Хост: `core/src/scenes/SceneHost.vue`.
- Рантайм: `core/src/scenes/runtime.js`.
- `scene-ready` → `window.__sceneReady = true`; рендерер ждёт этот флаг.
- `seek(t)` → `seek-done`; для будущего покадрового рендера ждать ответ.
- Тема инжектится в iframe; в редакторе берётся из `.slides-container`.

---

## 8. Проверка перед сдачей

1. `POST /presentations/{id}/scenes` проходит без 422.
2. Сцена открывается в `/p/{id}` и реагирует на `seek`.
3. Нет ошибок в консоли iframe.
4. `window.__sceneReady === true` после загрузки.
5. Проверены 16:9 и 9:16.
6. `duration` > 0, `start_time` не пересекается с соседями.
7. `EndMarkerSlide` синхронизирован с `max(start + duration)`.

---

## 9. Запуск

```bash
docker compose up -d
docker compose exec -T backend python scripts/seed_scene_demo.py
```

- Frontend: http://localhost:5175
- Backend: http://localhost:8002
- Postgres: localhost:5437
- Демо: http://localhost:5175/p/1
