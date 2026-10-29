# PAPER CAST DIRECTOR — сцена из конфига

`core/public/vendor/paper-cast-stage.js` собирает сцену целиком: бумажное
окружение, несколько персонажей, тайминги поз/клипов/речи/эмоций/взглядов
и субтитры. Сцена вызывает только `seek(t)`.

- Демо: `http://localhost:5175/director-demo.html`
- Шаблон библиотеки: `paper-director` (см. `backend/scene_library.py`)
- Демо-презентация: `/p/13` (seed: `scripts/seed_paper_director.py`)

```js
const stage = PaperCastStage.create(canvas, window.__sceneProps.director)
window.scene = { seek(t) { stage.seek(t) } }
```

## 1. Конфиг

```json
{
  "duration": 12000,
  "background": "#efe4d1",
  "title": "PAPER STAGE",
  "autoInteract": true,
  "environment": { "preset": "room", "palette": {}, "props": {} },
  "cast": [
    { "id": "mark", "character": "mark", "x": 0.34, "y": 0.95,
      "facing": 1, "scale": 1, "pose": "explain",
      "appearance": { "outfit": "shirt" }, "emotion": "neutral" },
    { "id": "mira", "character": "mira", "x": 0.66, "y": 0.95,
      "facing": -1, "pose": "neutral" }
  ],
  "timeline": [ { "at": 300, "type": "speak", "who": "mark",
                  "text": "Привет", "dur": 2600 } ],
  "captions": [ { "at": 300, "text": "Привет", "dur": 2600 } ]
}
```

- `x`/`y` — 0..1 в кадре (y — линия стоп).
- `facing` — 1 вправо, -1 влево; `flip` переворачивает спрайт.
- `character` — скин `mark` / `mira`; `appearance` — всё из `setAppearance`
  (одежда, причёска, пропорции, аксессуары).
- `scale` — размер персонажа.

## 2. Таймлайн

События сортируются по `at` (мс). `who` — `id` персонажа или `all`/`both`.

| type | поля | что делает |
|---|---|---|
| `pose` | `pose`, `fade` | статичная поза; `fade` мс — плавный переход |
| `clip` | `clip` или `clipObj` | клип жеста с антиципацией |
| `gesture` | `pose`, `dur` | короткий жест поверх позы |
| `speak` | `text`, `dur` | липсинк: текст → виземы от `at` |
| `visemes` | `visemes: [{t, viseme}]` | точный липсинк |
| `emotion` | `emotion` | плавная смена эмоции (320 мс) |
| `turn` | `yaw` −1..1 | поворот 3/4 |
| `lookAt` | `target: id` | взгляд на персонажа |
| `blink` | `on` | моргание вкл/выкл |

Приоритет: клип > жест > поза. Жест/клип заканчиваются по своей
длительности и возвращают позу.

## 3. Авто-взаимодействие

При `autoInteract: true`:

- говорящий поворачивается к партнёру (`turn` можно переопределить);
- слушающий смотрит на говорящего (`lookAt` можно переопределить);
- в начале чужой реплики слушающий коротко кивает (`nod`);
- взгляд считается из позиций голов в кадре.

## 3.5. Камера

```json
"camera": { "zoom": 1.02, "x": 0, "y": 0, "follow": "speaker" }
```

События `{ "at": 6200, "type": "camera", "zoom": 1.12, "x": -0.02, "dur": 900 }`
плавно ведут камеру (ease inOut); `follow: "speaker"` слегка подводит к
говорящему. Субтитры и заголовок рисуются поверх камеры.

## 3.6. Транскрипт → таймлайн

```js
const part = PaperCastStage.fromTranscript([
  { start: 0, end: 2.4, speaker: 'mark', text: 'Первая реплика.' },
  { start: 2.6, end: 5.2, speaker: 'mira', text: 'Ответ.', pose: 'present', emotion: 'joy' },
], { tail: 700 })
// -> { duration, timeline, captions }
```

`start/end` — секунды или мс (авто-определение); `pose/emotion/gesture`
опциональны. Результат подмешивается в конфиг сцены.

## 3.7. SRT → таймлайн

```js
const part = PaperCastStage.fromSRT(srtText, { tail: 700, speakers: ['mark','mira'] })
```

- Парсит `HH:MM:SS,mmm --> HH:MM:SS,mmm`, многострочный текст, `<i>`.
- Спикер: `mark: текст` или `[mira] текст`; иначе чередование `speakers`.
- Возвращает `{ duration, timeline, captions }`.

В демо есть панель «Транскрипт → таймлайн»: вставьте SRT (или JSON
сегментов) и нажмите «Собрать сцену» — `timeline/captions/duration`
перезапишутся, персонажи и окружение останутся.

## 4. Окружение

Пресеты: `home`, `office`, `cafe`, `loft`, `room`, `street`, `studio`, `park`.
`home/office/cafe/loft` — параметрическая комната (один рендерер + стиль).

```json
"environment": {
  "preset": "cafe",
  "palette": { "wall": "#d9c3ad", "accent": "#cf7a3a" },
  "props": {
    "windows": 2, "frames": 1, "door": true, "horizon": 0.64,
    "furniture": [
      { "type": "table", "x": 0.5, "scale": 1 },
      { "type": "shelf", "x": 0.86 },
      { "type": "menu", "x": 0.12 },
      { "type": "lamp", "x": 0.3 }
    ]
  }
}
```

Типы мебели: `sofa`, `table`, `desk` (стол + монитор), `shelf`, `plant`,
`rug`, `door`, `chairs`, `menu`, `frames`, `lamp`. Можно строкой (позиция по
умолчанию) или объектом с `x` (0..1) и `scale`.

Палитра: `wall/floor/trim/accent/sky/lamp/sofa/sofaLight/plant`.
Окружение детерминировано; штора/пыль/дождь — функция `t`.

## 5. Детерминизм и слои

- `seek(t)` — чистая функция; повторный вызов даёт тот же кадр.
- Персонажи сортируются по `y` (дальние раньше), затем по `x`.
- Каждый персонаж рисуется в offscreen 600×900 и вставляется на сцену;
  `flip` зеркалит спрайт.
- Субтитры — бумажная плашка внизу, `captions`.
- Заголовок — `title` (опционально).

## 6. Сцена

Шаблон `paper-director`:

```python
props = {"director": { ... }}
```

JS шаблона:

```js
const stage = PaperCastStage.create(canvas, window.__sceneProps.director)
window.scene = { ready: stage.ready, seek(t) { stage.seek(t) }, destroy() { stage.destroy() } }
```

`SceneHost` сам подгружает `paper-cast-stage.js`, если в JS сцены есть
`PaperCastStage`. Версия — в `core/public/vendor/versions.json` (`stage`).

## 7. Ограничения / следующий шаг

- Окружения — 4 пресета; генератор произвольных комнат/улиц ещё нет.
- Повороты — 3/4, профиля нет (см. `docs/PAPERCAST_AUDIT.md`).
- Между `pose`-ключами нет плавного перехода: поза меняется на ближайшем
  событии; для плавности используйте `clip`/A→B.
- Аудио-дорожка и тайминги из внешнего транскрипта пока не подключены;
  `speak` берёт `text`/`dur` из конфига.
- Нет камеры (зум/панорама) — только позиции персонажей.
