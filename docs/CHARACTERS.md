# CHARACTERS — персонажи, риги и липсинк

Статус: **решение принято (2026-10-25)** — SceneRig 1.0 поверх glTF 2.0,
см. `docs/RIG_FORMAT.md`. Rive остаётся legacy-рантаймом; SVG-риг `character`
используется для простых 2D-сцен.

Готовые полигональные персонажи: **Mark** и **Mira** (генератор v3,
`core/public/models/characters/`), 25 костей, 34 морфа (Oculus-15, blink,
body/face), липсинк, idle/talk, жесты `wave / point / explain`.
Character Studio: `core/public/character-studio.html`, демо `/p/11`.
Генератор: `scripts/blender/make_poly_characters_v3.py`, пресеты —
`assets/characters/presets/*.json`.

### Управление SceneRig

```js
rig.setVisemes([{ t: 0, viseme: 1 }, ...])
rig.setMotion('idle' | 'talk')
rig.setMood('neutral' | 'joy' | 'sad')
rig.setGesture('none' | 'wave' | 'point' | 'explain')
rig.setShape({ bodyShoulder: 0.2, bodyWaist: 0.15, ... })
rig.setOutfit({ top: 'hoodie', bottom: 'pants', shoes: 'sneaker', hair: 'short' })
rig.setAppearance({ skin: '#bd8766', top: '#24477a', ... })
```

Руки: ладонь к бедру, пальцы вниз по предплечью, большой палец вперёд;
`lowerArm` X < 0 сгибает локоть вперёд. Полное правило — `AGENTS.md` §3.7.1
и `docs/LEARNINGS.md` §7. Любой roll кисти вокруг оси руки запрещён.

Ниже — исходный research, сохранён для истории.

---

## 1. Что нужно от персонажа

- 2D или «около-3D» внешний вид.
- Части: голова, лицо, глаза, рот, торс, руки, ноги.
- Анимации: idle, walk, run, talk, blink, эмоции.
- Липсинк по озвучке.
- Детерминизм: `seek(t)` → одинаковый кадр.
- Возможность хранить персонажа как объект библиотеки и переиспользовать.

---

## 2. Варианты движка

### A. SVG/DOM-риг (рекомендуется для старта)
Персонаж — SVG с группами (`data-rig="head"`, `"arm-left"`, `"mouth"`).
Сцена/`SceneKit` двигает группы через `transform` от `t`.

Плюсы:
- полный контроль, никаких внешних runtime;
- детерминизм, рендер в том же iframe;
- легко генерировать ИИ (SVG — код);
- части можно стилизовать под любую палитру.

Минусы:
- сложная кожа/IK/деформации — вручную;
- walk-цикл нужно рисовать/кодить;
- visemes — отдельные формы рта.

**Вывод:** идеально для Phase 1–3. Начать с простого рига (голова/торс/руки/ноги/рот).

### B. Rive
`.riv`-файл, state machine, числовой вход `phoneme`, 10 визомов.
Runtime `@rive-app/canvas` / `@rive-app/webgl`.

Плюсы:
- профессиональные state machines;
- visemes и плавные переходы «из коробки»;
- интерактивность;
- fake-3D параллакс головы.

Минусы:
- нужен Rive-редактор/ассеты;
- `.riv` — бинарный формат, не HTML-код;
- детерминированный seek требует `advance(dt)`/ручного управления;
- лицензия/рантайм.

**Вывод:** лучший кандидат для сложных персонажей после MVP.

### C. Spine
2D skeletal animation, JSON/atlas, runtime.

Плюсы: мощный риг, скины, анимации.
Минусы: лицензия, ассеты, интеграция, не HTML-native.
**Вывод:** рассматривать, если Rive не подойдёт.

### D. Lottie
After Effects → JSON, `goToAndStop(frame)`.

Плюсы: детерминизм, простые циклы.
Минусы: не настоящий риг, visemes — предрендер, сложно менять.
**Вывод:** для простых заставок/иконок, не для персонажей.

### E. CSS 3D / Three.js
Псевдо-3D или настоящий 3D.

Плюсы: объём, камера.
Минусы: тяжело, не 2D-пайплайн, дорогой рендер.
**Вывод:** не сейчас.

---

## 3. Рекомендуемая архитектура

```
Character (asset)
  rig: SVG parts
  clips: idle / walk / run / talk / blink
  visemes: 10 mouth shapes
  views: front / three-quarter / side
  palette: tokens
```

### SVG-риг
```html
<g class="rig-root">
  <g class="rig-head" data-rig="head">...</g>
  <g class="rig-torso" data-rig="torso">...</g>
  <g class="rig-arm" data-rig="arm-left">...</g>
  <g class="rig-leg" data-rig="leg-left">...</g>
  <ellipse class="rig-mouth" data-rig="mouth"/>
</g>
```

### Клипы
Каждый клип — функция от `t`:
```js
const clips = {
  idle(t) { head.rotation = Math.sin(t / 900) * 2; },
  walk(t) { legL.rotation = Math.sin(t / 180) * 28; ... },
  talk(t, viseme) { mouth.scaleY = mouthFor(viseme); },
}
```
`SceneKit.character(el, { clip, t })` — будущий helper.

### Липсинк
1. TTS/транскрипт даёт character-level timestamps.
2. Маппинг в 10 визомов:
   `0 neutral, 1 AEI, 2 BMP, 3 FV, 4 CDGKNRSTXYZ, 5 U, 6 ChJSh, 7 L, 8 O, 9 QW`.
3. Массив `{ chars, viseme, timeMs }`.
4. На `seek(t)` выбираем визем и интерполируем форму рта.
5. Для Rive — `phoneme.value = viseme`.

Пример:
```js
const visemes = [
  { chars: 'H', viseme: 6, timeMs: 0 },
  { chars: 'e', viseme: 1, timeMs: 58 },
  { chars: 'll', viseme: 7, timeMs: 112 },
]
function visemeAt(t) {
  let v = 0
  for (const item of visemes) if (t >= item.timeMs) v = item.viseme
  return v
}
```

### Fake-3D
Лёгкий параллакс головы/торса от `t` (sin/cos) оживляет персонажа даже в молчании.
Не заменяет настоящий 3D и не должен ломать силуэт.

---

## 3.5. Решение по подходу (принято 2026-10-23)

Пользователь уже пробовал SVG+JS через Gemini Pro — результат слабый.
Это ожидаемо: LLM хорошо генерирует **код**, но плохо строит **риг** без
визуального редактора (кости, веса, IK, деформации).

**Решение: SVG/DOM-риг — рабочий путь, Rive — отложен.**
- Риг написан руками (координаты SVG), LLM его не «фантазирует», а меняет.
- Полный контроль: любую часть можно двигать из `seek(t)`, из пропсов и из cues.
- Детерминизм: никаких внутренних часов движка, только `t`.
- AI-генерируемость: правки персонажа = правка чисел и путей, а не ассетов.

Rive остаётся как путь для «геройских» персонажей (сложный скелет, IK,
веса, нестандартная мимика), но конвейер не должен зависеть от него:
абстракция `SceneKit.characterRig(el, opts)` даёт `seek(t)` и может быть
заменена на Rive-драйвер без переписывания сцен.

## 4. Что сделано (2026-10-23)

1. **Объект `character` переписан** (`backend/scene_library.py`): полноценный
   SVG-риг вместо силуэта.
   Части: `root`, `head`, `gaze`, `lid-left/right`, `brow-left/right`,
   `mouth`, `torso`, `arm-left/right`, `leg-left/right`.
   Рот — 10 форм-визёмов (`data-viseme="0..9"`) + язык (`data-viseme="t"`).
   Цвета — CSS-переменные `--char-skin/hair/shirt/pants/mouth/eye/pupil/shoe`,
   переопределяются пропсами `colors`.
2. **`SceneKit.characterRig(el, opts)`** (`core/public/vendor/scene-kit.js`):
   один драйвер управляет всем ригом от `t`.
   - виземы с кроссфейдом (`visemeBlend`), челюсть и язык по «открытости»;
   - моргание (период 3400 мс, окно 170 мс, seed-сдвиг);
   - дыхание, покачивание, наклон головы;
   - саккадический взгляд (зрачки);
   - настроение `neutral|joy|anger|sad|surprise` (брови);
   - жест рукой (`gestureAt`/`gestureDur`), ходьба (`walk`).
3. **Шаблон `character-talk`** — студийный talking-head: GSAP-таймлайн,
   кинетическая типографика, пыль, зерно/виньетка/грейд, контактная тень.
4. **`SceneKit.visemeBlend` / `lipsync({blend, onVisemePair})`** — плавный
   переход между формами рта вместо ступеньки.
5. **Демо**: `scripts/seed_character_talk.py` → `/p/4`.

### Как сделать своего персонажа

```js
const rig = SceneKit.characterRig(root.querySelector('.obj-character'), {
  visemes: p.visemes || [],   // [{t, viseme}]
  mood: 'joy',                // neutral|joy|anger|sad|surprise
  gestureAt: 4300,            // мс — подъём правой руки
  gestureDur: 1600,
  walk: false,
  seed: 0,                    // сдвиг фазы моргания
});
window.scene = { seek(t) { rig.seek(t); } };
```

Свой SVG-риг подключается тем же драйвером, если в нём есть
`[data-rig="mouth"]` с 10 путями `[data-viseme="0..9"]` и части головы/тела.

## 5. Что не делать сейчас

- Не строить полноценный 3D-риг.
- Не обещать консистентность персонажа без rig/asset pipeline.
- Rive — не тянуть, пока не ясны требования к «геройским» персонажам.
- Не анимировать рот через `Math.sin` — только виземы.

## 6. Ссылки

- Rive lip sync, 10 visemes: https://rive.expert/blog/lip-sync-animation
- Rive character integration: https://rivecharacter.com/docs/
- Rive lip sync API: https://templates.mascot.bot/lip-sync-api-2d-characters

---

## 7. Бесплатные и условно-бесплатные аналоги (2026)

| Инструмент | Лицензия/цена | Сильные стороны | Слабые стороны | Подходит нам |
|---|---|---|---|---|
| **SVG + JS (свой риг)** | бесплатно | полный контроль, детерминизм, HTML | сложные скелеты/IK вручную | **да, старт** |
| **Rive** | free to build; shipping/runtime может требовать платного плана (проверять актуальные условия) | state machines, visemes, интерактив, хороший редактор | `.riv` бинарный, не HTML-код, лицензия | **да, кандидат №1 для сложных** |
| **Spine** | платная лицензия (Essential/Pro), runtime интегрируется бесплатно, но пользователям нужна лицензия | индустриальный стандарт, скелеты, скины | цена, ассеты, не HTML-native | если нужен game-grade риг |
| **DragonBones** | бесплатно, open source (MIT), JS runtime | бесплатный аналог Spine, skeletal | проект старее, меньше контента | **да, бесплатный кандидат** |
| **Live2D Cubism** | free/pro, SDK по лицензии | VTuber-стиль, лицо, волосы | не общий 2D-риг, лицензия | если нужен именно Live2D-вид |
| **OpenToonz** | бесплатно, open source | классическая 2D-анимация, студийный пайплайн | не skeletal runtime, экспорт кадров | для pre-rendered вставок |
| **Synfig Studio** | бесплатно, open source | векторная 2D-анимация, скелеты | не runtime для браузера | для pre-rendered |
| **Blender Grease Pencil** | бесплатно | 2D/3D, камера, свет, рендер | тяжёлый, не HTML | для сложных вставок/3D-вида |
| **Pencil2D** | бесплатно | простая frame-by-frame | нет рига | для черновых аниматиков |

### Рекомендация для видео-only

1. **Сейчас:** SVG-риг + visemes. Это детерминированно, встраивается в наш iframe,
   не требует внешних лицензий.
2. **Если нужен сложный скелет:** прототип на **DragonBones** (бесплатно) и
   **Rive** (лучший workflow). Сравнить по:
   - качеству деформаций;
   - удобству visemes;
   - детерминированному seek;
   - лицензии на коммерческий видео-контент.
3. **Spine** — только если DragonBones/Rive не хватит; это платный game-grade
   инструмент.
4. **OpenToonz/Synfig/Blender** — для pre-rendered вставок, где не нужен
   динамический липсинк.

### Что важно для видео-only

- Нам не нужен интерактивный state machine в браузере; нужен **детерминированный
  seek** и возможность отрендерить кадр.
- Для Rive: проверить, как `advance(dt)`/`seek` работает при покадровом рендере.
- Для DragonBones: проверить, как выставлять время анимации вручную.
- Для SVG: всё под нашим контролем, но сложные риги будут дороже в разработке.


---

## 8. Текущий рабочий риг: Rive (2026-10-23)

Главный путь для персонажей — **собственный Rive-риг**, а не натягивание рта
на фото и не готовые чужие `.riv` (у них нет контракта виземов/скелета).

### Что собрано

- ~~`core/rive/character/`~~ — исходник собственного Rive-рига удалён из
  активного репозитория (frozen legacy). Ниже — историческая справка:
  `rive.yaml`, `scene.rml` (генерируется).
- ~~`scripts/build_rive_character.py`~~ — удалён; собственный Rive-риг больше
  не поддерживается. Новые риги — SceneRig (`docs/RIG_FORMAT.md`).
- `core/public/rive/character.riv` — рантайм-ассет.
- `core/public/vendor/rive-character.js` — детерминированный контроллер:
  `RiveCharacter.create(canvas, opts)` / `SceneKit.riveCharacter`.
- Шаблоны `character-rive` (`/p/5`) и `character-rive-panel` (`/p/6`).

### Скелет

Кости (21): `root, spine, chest, neck, head`, `shoulder/upperArm/foreArm/hand`
(L/R), `hip/thigh/shin/foot` (L/R). Каждая кость — view-model число; контроллер
пишет углы из `seek(t)` и вызывает `drawFrame()`. Внутренние часы Rive не
используются: state machine запускает пустую анимацию только чтобы работали
data binds.

### Лицо и липсинк

- 10 форм рта (`m0..m9`) — отдельные Shape, opacity которых пишется
  контроллером; кроссфейд 70 мс, зубы/язык привязаны к тем же виземам.
- Глаза: белки + радужка/зрачок/блик (общий gaze-узел), веки на `blink`,
  брови на `browY/browTilt`.
- Голова: `head` (наклон), `neck`, `chest`, `spine`.

### Пресеты

`host`, `cohost`, `priest`, `historian`, `sociologist` — цвета (skin, hair,
shirt, pants, shoe, lip, iris, scarf, skirt, cassock) и флаги
(`beard`, `glasses`, `scarfOn`, `skirtOn`, `cassockOn`, `blazerOn`, `longHair`).
Один `.riv` обслуживает весь каст; переключение — `rig.setPreset(name)`.

### Клипы/движения

`idle` (дыхание, вес, голова, взгляд, моргание), `talk` (кивки), `wave`,
`point`, `open`, `shrug`, `walk` (in-place, с опциональным переносом root).
Жесты задаются списком `[{at, type, hand, dur}]`.

### Сборка

```bash
# Rive CLI 1.7: ~/.rive/bin/rive (или rive в PATH)
# Удалено. Новый путь: docs/RIG_FORMAT.md + scripts/blender/scene_rig_export.py
```

### Грабли (важно)

1. **Порядок отрисовки Rive:** первый child рисуется сверху. Торс, объявленный
   раньше головы, закрывает подбородок/рот. Сначала рисуем лицо/детали, потом
   базу; для одежды — сначала детали, потом рубашку.
2. **У `RootBone` x/y — ключи 90/91**, а не 13/14 (это Node). Ошибка
   `bind-target-missing-property` тихая: ассет собирается, но не двигается.
3. **Data binds работают только при запущенной state machine.** Держим
   пустую animation, `play()` и `drawFrame()`.
4. **`.riv` в sandboxed iframe:** `fetch` из opaque origin блокируется CORS.
   `SceneHost` читает файл в родителе и инжектит base64; контроллер принимает
   `buffer`.
5. **Шея как Shape в neck-кости закрывает рот** (она рисуется раньше головы).
   Шею не рисуем отдельно; её закрывает голова/торс.
6. **Портреты** (`core/public/portraits`) остаются для старого `character-talk`;
   основной новый путь — SceneRig (`docs/RIG_FORMAT.md`).

### Ограничения текущего арта

- Это **cutout-риг** (жёсткие части на костях), без mesh-скиннинга; швы
  скрываются накладками/суставами.
- Арт — стилизованный вектор-база; детализацию (лица, одежда, волосы, обувь)
  можно было наращивать в удалённом `scripts/build_rive_character.py`; новый путь — SceneRig.
- Нет head yaw/3D-поворота, нет IK, нет физики волос; ходьба in-place.

### Legacy SVG/портреты

- Риг `character` (SVG) — рабочий, драйвер `SceneKit.characterRig`, демо `/p/4`.
- Портреты каста — Gemini Image + chroma-key, анимация дыхания/качания,
  `SceneKit.idle`; рот процедурный.
- `scripts/generate_prav_portraits.py` — генератор портретов.


## 9. Готовые Rive-актёры (2026-10-23, вечер)

Каталог: `GET /scene-library/characters` (и `/{slug}`). Карточка содержит
лицензию, автора, режим драйвера, число визёмов и список возможностей.

| slug | актив | режим | тело | липсинк | лицензия |
|---|---|---|---|---|---|
| `character-oldman` | Old Man | state machine + view model | полное (ткань, верёвка, стопа) | 3 формы (`Default/OO/AAA`) | CC BY 4.0, ar.akash |
| `character-bob` | Bob | linear (SM остановлен) | бюст, дыхание, взгляд | 10 визёмов | CC BY 4.0, emanuelcabezas |
| `character-rive` | собственный риг | view-model numbers | полное, 21 кость | 10 визёмов | internal |

### Как устроен Old Man

- `SceneKit.riveActor(canvas, { character:'oldman', visemes, gestures, mood })`.
- Драйвер: `core/public/vendor/rive-actor.js`, режим `stateMachine`.
- После загрузки: `play('State Machine 1')` → `stopRendering()`.
- `seek(t)`:
  - двигает state machine `advanceAndApply(dt)` шагами 1/60;
  - выставляет `mouth` (`Default/OO/AAA`), `face` (`Normal/wow`);
  - по жестам дергает `leftHand` trigger;
  - добавляет вторичное движение (наклон/дыхание/смещение).
- Виземы приходят из `props.visemes` (`[{t, viseme}]`). В редакторе открой
  вкладку **Characters**, введи реплику и выбери актёра: текст уйдёт в
  `POST /scene-library/text-to-visemes`, а сцена откроется с готовым липсинком.
  Офлайн — `scripts/text_to_visemes.py`.

### Ограничения

- У Old Man нет ходьбы и IK; это сценический статичный персонаж с жестами.
- Bob: numeric view model (`visemes/poses/expressions/mood`) ещё не
  разобран — позы не переключаются, но линейные виземы/дыхание/взгляд
  работают после остановки state machine (`/p/9`).
- Для массовки и других возрастов нужны новые готовые `.riv` или
  доработка собственного рига.

## 10. 3D-аватар (GLB + Babylon, 2026-10-24)

Полноценный 3D-персонаж для студийных сцен: Ready Player Me GLB, Babylon.js,
мокап-клипы Mixamo. Работает в sandbox-iframe и остаётся детерминированным:
один кадр на `seek(t)`, без render loop и внутренних часов.

### Файлы

- `core/public/models/brunette.glb` — аватар (67 костей, 72 морфа).
- `core/public/models/brunette.glb.js` — тот же GLB в base64 для iframe
  (`scripts/build_avatar_asset.py`).
- `core/public/models/anim/*.glb` — клипы Mixamo (не в git, см. лицензию).
- `core/public/models/anim/avatar-anims.js` — сжатые треки для рантайма
  (`scripts/extract_avatar_anims.py`).
- `core/public/vendor/babylon-character.js` — драйвер.
- `core/public/vendor/babylon.js`, `babylonjs.loaders.min.js` — движок.
- `core/public/babylon-avatar.html` — удалён вместе с legacy-харнессами.

### Как устроен драйвер

```
SceneKit.babylonCharacter(canvas, {
  buffer, preset, visemes, mood, gaze, gestures,
  idleClip, talkClip, talkWeight, pose, poseKeys,
  seed, intensity,
}) -> { ready, seek(t), setPose, setVisemes, ... }
```

- **Ретаргет**: Mixamo-клипы сняты с T-pose, RPM-аватар — в A-pose.
  Переносится абсолютная world-ориентация:
  `W_tgt(t) = (W_tgt_rest * inv(W_src_rest)) * W_src(t)`, затем локальная
  кватернионная цепочка. Локальные/мировые дельты ломают локти.
- **Eye-кости не ретаргетятся** — иначе глаза уезжают; gaze добавляется
  к rest-кватерниону.
- **Липсинк**: 10 визёмов движка → Oculus-морфы (`viseme_aa`, `viseme_O`,
  `viseme_PP`, ...), кроссфейд 80 мс; виземы приходят из
  `POST /scene-library/text-to-visemes`.
- **Моргание** — детерминированный импульс раз в ~3.6 с.
- **Ground clamp** — самый низкий стоп возвращается на rest-высоту.
- **Culling** — `alwaysSelectAsActiveMesh = true` для skinned-мешей, иначе
  голова/рука исчезают на кадр.
- **Камера** — presets `face/bust/full/wide` с `covW/covH`, радиус считается
  из покрытия и aspect; портрет отдельно.
- **Позы**: `pose = {bone: [x,y,z]}` — статическое смещение в локальной
  системе кости (градусы); `pose_keys = [{at,bone,x,y,z}]` — ключи,
  держатся до следующего ключа этой кости.

### Редактор

Вкладка **3D** в `SceneEditor.vue`: кадр, базовый/речевой клип, вес речи,
настроение, взгляд, реплика → виземы, жесты, слайдеры позы, ключи позы.
Правки уходят в сцену сообщениями `avatar-*` через `SceneHost.post()`
(без пересборки iframe); в props пишутся кнопкой «Записать в props» или Save.

### Ассеты и лицензия

- Аватар: Ready Player Me (free avatar), можно использовать в проекте.
- Клипы: Mixamo / deevid-mixamo-assets. Бесплатны для коммерческого
  использования по условиям Adobe, но **перераспространение сырых ассетов
  ограничено** — не держите их в публичном репозитории. Скачивание:
  `python scripts/fetch_avatar_anims.py`, затем
  `python scripts/extract_avatar_anims.py`.
- На сервер клипы переносятся вручную (scp), как и `.env`.

### Добавить клип

1. Скачать `.glb` (Mixamo, без скина) в `core/public/models/anim/`.
2. Добавить имя в `CLIPS` в `scripts/extract_avatar_anims.py`.
3. `python scripts/extract_avatar_anims.py`.
4. В редакторе выбрать клип в «Базовый клип»/«Клип речи» или добавить
   в `gestureOptions`.
