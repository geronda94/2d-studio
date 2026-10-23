# CHARACTERS — персонажи, риги и липсинк

Статус: **research / placeholder**. В библиотеке уже есть объект `character`
(SVG-заготовка с частями рига), но полноценный движок персонажей ещё не выбран.

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

## 3.5. Решение по подходу

Пользователь уже пробовал SVG+JS через Gemini Pro — результат слабый.
Это ожидаемо: LLM хорошо генерирует **код**, но плохо строит **риг** без
визуального редактора (кости, веса, IK, деформации).

Поэтому:
- SVG-риг — **timeboxed эксперимент** (1 персонаж, 2–3 клипа, 6–10 визомов).
- Если результат не предсказуем — переходим на **Rive** (лучший workflow)
  или **DragonBones** (бесплатный).
- Абстракция `CharacterRuntime` в сцене: `seek(t)`, `setClip`, `setViseme`.
  Тогда SVG/Rive/DragonBones можно менять, не переписывая сцены.

## 4. Что делать сейчас

1. Оставить `character` как SVG-заготовку с частями рига.
2. Добавить 2–3 клипа: idle, walk, talk (пока без visemes).
3. Сделать `SceneKit.character` helper:
   - `setClip(name)`, `seek(t)`, `setViseme(v)`.
4. Подготовить `visemes` в payload сцены (позже — из TTS).
5. Выбрать Rive vs SVG по результатам проб:
   - нужен ли сложный скелет/IK;
   - важна ли интерактивность;
   - готов ли ты работать с `.riv`/Spine-ассетами.

## 5. Что не делать сейчас

- Не строить полноценный 3D-риг.
- Не обещать консистентность персонажа без rig/asset pipeline.
- Не тащить Rive, пока не ясны требования к персонажам.

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

## 8. Текущий статус (2026-10-23)

- Основной каст (`host`, `cohost`, `priest`, `historian`, `sociologist`) —
  **детализированные портреты**, сгенерированные Gemini Image и вырезанные
  chroma-key. Файлы: `core/public/portraits/`.
- Портреты анимируются детерминированно: дыхание, лёгкое качание, масштаб;
  камера/свет/пыль двигаются отдельно.
- Историческая массовка — SVG-силуэты.
- Липсинк и полноценные риги (Rive/DragonBones) ещё не подключены; текущий
  портрет — статичный bust с процедурным «дыханием».
- Генератор: `scripts/generate_prav_portraits.py` (Gemini 3 Pro Image +
  chroma-key + crop).
