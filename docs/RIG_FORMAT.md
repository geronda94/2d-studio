# RIG_FORMAT — SceneRig 1.0

Контракт ригов и персонажей SceneEngine. Цель — перестать подгонять каждый
ассет под каждый движок: один канонический скелет, один формат клипов, один
обменник (glTF 2.0) и предсказуемый экспорт в Blender и обратно.

```
Blender / DCC  ──glTF──▶  SceneRig manifest + .glb  ──compile──▶  runtime (.glb + .js)
      ▲                         │
      └────────glTF─────────────┘
```

- **Истина для редактора** — JSON-манифест `*.scenerig.json`.
- **Истина для геометрии** — `.glb` (mesh + skin + morph targets).
- **Истина для анимации** — `*.sclip.json` (авторские кривые) или `.glb`-клип.
- **Рантайм** — собранный `.glb` без ретаргета: канонический скелет = прямые треки.
- **Rive / Mixamo / RPM** — только входные адаптеры, не рантайм-форматы.

---

## 1. Принципы

1. **Один скелет — три семейства.** `human`, `animal`, `winged`.
2. **Никакого ретаргета в рантайме.** Клип авторится на каноне и применяется
   напрямую. Адаптер работает только на импорте.
3. **Время снаружи.** Клип — чистая функция `t`; в сцене по-прежнему только
   `window.scene.seek(t)`.
4. **glTF — обменник.** Blender импортирует/экспортирует GLB нативно; Babylon
   читает его без конвертеров.
5. **Веб — авторинг и валидация, Blender — меш и скиннинг.** В браузере нет
   sculpt/weight painting.
6. **Всё машинночитаемо.** Схемы, алиасы, валидатор, CLI.

---

## 2. Координаты, единицы, rest-поза

| Параметр | Значение | Проверка |
|---|---|---|
| Единицы | метры, scale = 1.0 | рост человека 1.4–2.2 м |
| Up | glTF: `+Y`; Blender: `+Z` | экспортёр конвертирует |
| Взгляд | `+Z` | вектор `foot → toe` в среднем по `+Z` |
| Origin | между ступнями, `y = 0` | `minY` bind-pose ≈ 0 |
| Rest pose | **A-pose** (руки ~35–55° вниз) | эвристика по плечу/локтю |
| Root | `root` на земле, `hips` — таз | `root` опционален |
| Bone axes | X вдоль кости, roll = 0 | рекомендуется; рантайм не зависит |
| Max influences | 4 на вершину | `JOINTS_0`/`WEIGHTS_0` |
| Normals | единичные, без NaN | валидатор |
| Facing | персонаж смотрит в `+Z` | предупреждение при `-Z` |

> **Почему A-pose:** удобнее для скиннинга и одинаково предсказуем для клипов.
> T-pose допустим только как входной формат — компилятор печёт в A-pose.

### Формат файлов

```
character.scenerig.json      манифест (этот документ)
character.glb                геометрия + скелет + морфы (bind pose)
clips/idle.sclip.json        авторский клип
clips/walk.sclip.json
dist/character.glb           собранный ассет (baked clips, canonical rig)
dist/character.js            base64-обёртка для sandbox-iframe
```

---

## 3. Семейства и архетипы

| Семейство | Архетип | Для кого |
|---|---|---|
| `human` | `humanoid` | люди, ведущие, исторические персонажи |
| `animal` | `quadruped` | собака, конь, кот, волк, медведь |
| `winged` | `avian` | птицы (воробей, ворон, орёл) |
| `winged` | `insectoid` | пчёлы, мухи, стрекозы, жуки |

`animal` и `winged` — это **семейства**, архетип уточняет скелет. В манифесте
указываются оба: `family` + `archetype`.

### 3.1. Humanoid (21 обязательная кость)

```
root?  hips
       spine → spine1? → chest → neck → head
       shoulder.L → upperArm.L → lowerArm.L → hand.L
       shoulder.R → upperArm.R → lowerArm.R → hand.R
       upperLeg.L → lowerLeg.L → foot.L → toe.L
       upperLeg.R → lowerLeg.R → foot.R → toe.R

опции: jaw, eye.L/R, headTop,
       thumb1-4.L/R, index1-4.L/R, middle1-4.L/R, ring1-4.L/R, pinky1-4.L/R
```

**Обязательные:** `hips, spine, chest, neck, head`, пары
`shoulder/upperArm/lowerArm/hand`, `upperLeg/lowerLeg/foot/toe`.
`spine1` опционален (RPM и Mixamo его имеют, Rigify — нет).

### 3.2. Quadruped

```
root?  hips → spine → chest → neck → head
       shoulder.L → upperArm.L → lowerArm.L → hand.L   (передняя лапа)
       shoulder.R → upperArm.R → lowerArm.R → hand.R
       upperLeg.L → lowerLeg.L → foot.L → toe.L        (задняя лапа)
       upperLeg.R → lowerLeg.R → foot.R → toe.R
       tail1 → tail2? → tail3? → tail4?
опции: ear.L/R, jaw, eye.L/R
```

**Обязательные:** `hips, spine, chest, neck, head`, все четыре конечности по
схеме выше. Хвост и уши — опциональны (но `tail1` рекомендуется).

### 3.3. Avian (птица)

```
root?  hips → spine → chest → neck → head
       wingRoot.L → wingMid.L → wingTip.L
       wingRoot.R → wingMid.R → wingTip.R
       upperLeg.L → lowerLeg.L → foot.L → toe.L
       upperLeg.R → lowerLeg.R → foot.R → toe.R
       tail1 → tail2? → tail3?
опции: beak, jaw, eye.L/R, wingHind.L/R
```

**Обязательные:** `hips, spine, chest, neck, head`, пара крыльев
`wingRoot/wingMid/wingTip`, пара ног `upperLeg/lowerLeg/foot`.
`beak` — предпочтительная кость для рта; `jaw` — альтернатива.

### 3.4. Insectoid (пчела, муха, жук)

```
root?  thorax → abdomen
       head
       wingRoot.L → wingMid.L → wingTip.L
       wingRoot.R → wingMid.R → wingTip.R
       wingHind.L/R (вторая пара, опция)
       legFront.L/R → legMid.L/R → legHind.L/R   (по 2–3 сегмента)
опции: antenna.L/R, stinger, mandible.L/R, eye.L/R
```

**Обязательные:** `thorax, abdomen, head`, пара крыльев
`wingRoot/wingMid/wingTip`, `legFront/legMid/legHind` (по одной кости на
сегмент достаточно; глубже — `legFront1/2/3`).

> Для насекомых `hips` = `thorax`, `spine` = `abdomen` допускаются как алиасы.

---

## 4. Именование и алиасы

### 4.1. Канон

- `camelCase`, стороны — суффикс `.L` / `.R` (`upperArm.L`).
- Точка — родная для Blender-симметрии; glTF сохраняет имя как есть.
- Никаких пробелов, `:` и кириллицы в именах костей.
- Одинаковые имена костей в разных мешах запрещены.

### 4.2. Входные алиасы (адаптеры)

| Источник | Пример | Канон |
|---|---|---|
| Mixamo | `mixamorig:LeftForeArm` | `lowerArm.L` |
| RPM | `LeftUpLeg` | `upperLeg.L` |
| RPM / Mixamo | `Spine1` | `spine1` |
| RPM / Mixamo | `Spine2` | `chest` |
| RPM | `LeftToeBase` | `toe.L` |
| RPM | `HeadTop_End` | `headTop` |
| Rigify | `upper_arm.L` | `upperArm.L` |
| Rigify | `forearm.L` | `lowerArm.L` |
| Rigify | `thigh.L` | `upperLeg.L` |
| Rigify | `shin.L` | `lowerLeg.L` |
| Rigify | `spine.001` | `spine1` |
| Rigify | `spine.002` | `chest` |
| Rigify | `spine.003` | `neck` |
| VRM | `J_Bip_C_Hips` | `hips` |

Полная таблица — в `backend/rig/archetypes.py`. Незнакомые кости попадают в
`unmapped` и **не ломают** импорт: их можно объявить в `bones.extra` манифеста.

### 4.3. Стороны

Поддерживаются `Left/Right`, `left/right`, `.L/.R`, `_L/_R`, `-L/-R`.
Если сторона не распознана — кость считается центральной.

---

## 5. Лицо, морфы и визёмы

### 5.1. Канонический набор

- **ARKit-52** — имена как в blendshapes (`jawOpen`, `mouthSmileLeft`, …).
- **Oculus-15** — визёмы (`viseme_sil`, `viseme_PP`, `viseme_FF`, `viseme_TH`,
  `viseme_DD`, `viseme_kk`, `viseme_CH`, `viseme_SS`, `viseme_nn`, `viseme_RR`,
  `viseme_aa`, `viseme_E`, `viseme_I`, `viseme_O`, `viseme_U`).
- **SceneEngine 10** — внутренние визёмы 0..9; таблица маппинга уже есть в
  `core/public/vendor/babylon-character.js`.

Манифест объявляет, что реально есть в меше:

```json
"face": {
  "morphs": ["jawOpen", "mouthOpen", "viseme_sil", "viseme_aa", "viseme_O", "eyeBlinkLeft", "eyeBlinkRight"],
  "visemes": "oculus-15",
  "engine_map": "scene-10",
  "jaw_bone": "jaw"
}
```

Правила:

- Для человека предпочтительны ARKit-52 + Oculus-15.
- Минимум для липсинка: `jawOpen` **или** кость `jaw`, и хотя бы 5 визёмов.
- Моргание: `eyeBlinkLeft`/`eyeBlinkRight` или кости век.
- У птиц/насекомых лицо может быть костным (`beak`, `mandible`) — морфы не
  обязательны.
- Имена морфов сохраняются при экспорте glTF (`mesh.extras.targetNames`).

---

## 6. Сокеты (одежда и предметы)

Сокет — именованная точка на кости. Используется для шляп, очков, инструментов,
микрофона, поводка, седла, сот.

```json
"sockets": [
  { "name": "head.top",  "bone": "head",  "offset": [0, 0.12, 0], "rotation": [0,0,0,1] },
  { "name": "hand.R",    "bone": "hand.R","offset": [0, 0, 0],    "rotation": [0,0,0,1] },
  { "name": "back",      "bone": "chest", "offset": [0, 0, -0.10] },
  { "name": "saddle",    "bone": "spine", "offset": [0, 0.15, 0] }
]
```

Правила:

- `bone` обязан существовать в скелете (валидатор — ошибка).
- `offset` в метрах, в пространстве кости; `rotation` — кватернион xyzw.
- Одежда: либо skinned mesh на тех же костях, либо rigid prop на сокете.
- Для animal/winged сокеты `saddle`, `back`, `beak`, `stinger` — по желанию.

---

## 7. Клипы

### 7.1. Авторский формат `*.sclip.json`

```json
{
  "format": "sceneclip/1",
  "name": "idle",
  "fps": 30,
  "duration": 4.0,
  "loop": true,
  "tracks": {
    "chest":      { "rotation": [[0, 0, 0, 0, 1], [1.2, 0, 0.02, 0, 0.9998]] },
    "upperArm.L": { "rotation": [[0, 0, 0, -0.17, 0.985]] },
    "hips":       { "translation": [[0, 0, 0, 0], [2.0, 0, -0.01, 0]] }
  },
  "face": {
    "viseme_sil": [[0, 1], [3.4, 1], [3.5, 0]],
    "eyeBlinkLeft": [[2.9, 0], [3.0, 1], [3.1, 0]]
  },
  "events": [{ "t": 0.4, "name": "step" }]
}
```

- Ключ: `[timeSeconds, ...value]`. `rotation` — кватернион xyzw,
  `translation`/`scale` — xyz, `face` — скаляр веса.
- Кривые разреженные; компилятор печёт в glTF (linear/step) на `fps`.
- Клип не содержит state machine. Состояния — в манифесте ассета.
- Все клипы in-place; движение по миру задаёт сцена/камера.
- События — для SFX/шагов/жестов, не для анимации.

### 7.2. Клип как GLB

Допустимый вариант: один `.glb` на клип (как сейчас у Mixamo). Требования:

- имя анимации = имя клипа;
- таргеты — только канонические кости/морфы;
- длительность > 0, ≥ 2 ключа на канал;
- fps не хранится в glTF; считаем 30 для authored, 24–60 для импорта.

### 7.3. Bake в GLB

Авторский клип превращается в обычную glTF-анимацию, которую читают Blender и
Babylon без плагинов:

```bash
python -m backend.rig bake character.scenerig.json clips/wave.sclip.json \
  --out dist/character-wave.glb
```

- тело: `rotation` / `translation` / `scale`;
- ключи пересэмплируются на `fps` (по умолчанию 30), кватернионы нормируются;
- выход — валидный GLB с `animations[]`;
- лицо (морфы) пока не печётся — warning `bake.face`.

Проверено: `wave` (2 с, 2 канала) → GLB → Blender import → экспорт → снова
валидный GLB, анимация сохранена.

### 7.4. Слои

- **body** — скелет.
- **face** — морфы/челюсть.
- **secondary** — дыхание, ткань, хвост, антенны.
- **procedural** — gaze, blink, idle (чистые функции `t`).

Слои складываются в рантайме поверх клипа, не заменяя его.

---

## 8. Манифест `*.scenerig.json`

```json
{
  "format": "scenerig/1",
  "id": "character-oldman",
  "title": "Старец",
  "family": "human",
  "archetype": "humanoid",
  "geometry": {
    "file": "oldman.glb",
    "sha256": "…",
    "units": "m",
    "up": "Y",
    "facing": "+Z"
  },
  "rest": { "pose": "A", "origin": "feet" },
  "bones": {
    "canonical": true,
    "map": { "mixamorig:Hips": "hips" },
    "extra": ["beard", "cape"]
  },
  "face": { "morphs": ["…"], "visemes": "oculus-15", "jaw_bone": "jaw" },
  "sockets": [ { "name": "hand.R", "bone": "hand.R" } ],
  "clips": [
    { "name": "idle", "file": "clips/idle.glb", "loop": true, "fps": 30, "duration": 4.0 },
    { "name": "talk", "file": "clips/talk.glb", "loop": false, "fps": 30, "duration": 6.0 }
  ],
  "lod": [
    { "level": 0, "file": "oldman.glb" },
    { "level": 1, "file": "oldman_lod1.glb", "max_distance": 6 }
  ],
  "license": { "name": "CC BY 4.0", "author": "…", "source": "…" },
  "source": { "blender": "src/oldman.blend", "sha256": "…" },
  "tags": ["human", "oldman", "russian"]
}
```

Обязательные поля: `format`, `id`, `family`, `archetype`, `geometry.file`,
`license.name`. Остальное — по возможности.

`id` — `[a-z0-9][a-z0-9-]{1,63}`. Совпадает с именем ассета в библиотеке.

---

## 9. Профиль GLB

Ассет обязан:

- быть glTF 2.0, один `.glb` (JSON + BIN);
- иметь `asset.version = "2.0"`;
- содержать **один** skin на персонажа;
- скиннинг: `JOINTS_0` + `WEIGHTS_0`, ≤ 4 влияния, сумма весов ≈ 1;
- `POSITION` с `min`/`max`;
- морфы: `mesh.extras.targetNames`, имена канонические;
- клипы: `animations[]`, таргеты — узлы скелета/морфы;
- материалы: Principled BSDF-совместимые, текстуры embedded или рядом;
- без скриптов, камер по умолчанию и лишних сцен;
- `extras` для `rig_id`, `sockets`, `license` (по желанию).

Рекомендуется:

- Draco/Meshopt для геометрии, KTX2/Basis для текстур;
- LOD 0/1/2;
- атлас материалов ≤ 4 на персонажа;
- бюджет: human ≤ 60k tris (LOD0), ≤ 8 морф-таргетов на голову при мобильном.

---

## 10. Blender: импорт и экспорт

### 10.1. Blender → SceneEngine

1. Модель в метрах, A-pose, origin между ступнями, взгляд `+Z`.
2. Кости названы канонически (или добавлены в `bones.map`).
3. Скиннинг: ≤ 4 влияния, веса нормализованы.
4. `File → Export → glTF 2.0 (.glb)`:
   - `+Y Up`;
   - Apply Modifiers — по необходимости (скиннинг не применять!);
   - `Use Rest Position Armature` — включить, если pose ≠ rest;
   - экспорт морфов и анимаций — включить;
   - `Extras` — включить, если нужны сокеты/лицензия.
5. `python -m backend.rig validate character.scenerig.json` — ошибки чинятся до
   коммита.
6. `python -m backend.rig compile character.scenerig.json --out dist/` —
   переименовывает кости в канон, пишет `dist/character.glb` и манифест
   без `bones.map`.

### 10.1.1. Готовый экспортёр

```bash
blender --background character.blend \
  --python scripts/blender/scene_rig_export.py -- \
  --id character-hero --family human --archetype humanoid \
  --license "CC BY 4.0" --author "You" --out dist/
```

Скрипт:

- находит armature и все меши, привязанные к нему;
- проверяет кости, веса, A-pose, взгляд, форму;
- экспортирует GLB (`+Y up`, без применения Armature);
- пишет `*.scenerig.json` (включая `bones.map`, морфы, клипы, лицензию);
- валидирует результат через `backend.rig`.

Проверено: тестовый риг 21 кость → GLB → манифест → 0 ошибок;
канонический RPM `brunette.glb` → Blender import → export → 0 ошибок,
67 костей и 72 морфа сохранены.

Тестовый риг для проверки пайплайна:

```bash
blender --background --python scripts/blender/make_test_rig.py -- /tmp/rig.blend
blender --background /tmp/rig.blend \
  --python scripts/blender/scene_rig_export.py -- \
  --id test-human --family human --archetype humanoid --license CC0 --out /tmp/dist
```

### 10.2. SceneEngine → Blender

- Клипы компилируются в GLB с `animations[]` (bake 30 fps). Blender открывает
  файл без аддона.
- Манифест и сокеты лежат в glTF `extras`; при экспорте из Blender включите
  `Extras`, чтобы не потерять.
- IK/констрейнты/драйверы в glTF не переносятся. Решайте IK в Blender и
  пеките; в вебе IK не обязателен.

### 10.3. Что теряется

| Теряется | Решение |
|---|---|
| IK-констрейнты | bake в Blender |
| Драйверы, водители | bake в клипы |
| Blender-модификаторы | Apply до экспорта (кроме Armature) |
| Сложные material nodes | Principled BSDF + текстуры |
| Rigify-контроллеры | канонический скелет + `bones.map` |

---

## 11. Валидатор

CLI (stdlib, без тяжёлых зависимостей):

```bash
python -m backend.rig scan core/public/models/brunette.glb
python -m backend.rig scan core/public/models/brunette.glb --archetype human --json
python -m backend.rig validate character.scenerig.json
python -m backend.rig compile character.scenerig.json --out dist/
python -m backend.rig bake character.scenerig.json clips/wave.sclip.json --out dist/wave.glb
python -m backend.rig archetypes
```

HTTP (для браузерных студий): `POST /rig/validate` (GLB), `POST /rig/validate-manifest`
(JSON + GLB), `GET /rig/archetypes`.

Проверки:

- GLB: заголовок, версия, чанки, JSON, BIN;
- скелет: обязательные кости, дубликаты, unmapped, дубликаты канона;
- веса: сумма, максимум влияний, наличие `JOINTS_0/WEIGHTS_0`;
- морфы: имена, минимум для липсинка;
- клипы: таргеты, длительность, ключи, fps-gap;
- rest: A-pose, ступни на земле, взгляд `+Z`, рост;
- манифест: файлы, sha256, сокеты, лицензия, формат;
- бюджет: материалы, текстуры, треугольники.

Коды ошибок — стабильные (`bones.missing`, `weights.sum`, `pose.tpose`, …),
чтобы ИИ и CI могли читать отчёт машинно.

---

## 12. Версионирование

- `format`: `scenerig/1`, `sceneclip/1`.
- Ломающие изменения → `2`. Старые манифесты поддерживаются адаптером.
- `geometry.sha256` и `source.sha256` фиксируют версию файлов.
- `dist/` — артефакт сборки, не редактируется руками.

---

## 13. Что не делаем

- Свой бинарный формат скелета.
- Rive-round-trip (закрытый формат; Rive остаётся legacy-рантаймом).
- IK/физику в вебе (только bake).
- Weight painting и sculpt в браузере.
- Ретаргет в рантайме (только на импорте).
- Хранение Mixamo-клипов в публичном репозитории (лицензия Adobe).
