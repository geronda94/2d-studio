# ASSET_FORMAT — объекты, окружения и общий манифест

Единый контракт для всего, что кладётся в сцену: персонажи, объекты, окружения,
эффекты. Риги и клипы описаны отдельно в `docs/RIG_FORMAT.md`.

```
SceneAsset
  ├── character   → RIG_FORMAT + клипы + гардероб
  ├── prop3d      → .glb + материалы + сокеты + LOD
  ├── prop2d      → SVG/HTML + части + views + механизмы
  ├── environment → слои + палитры + скаттер + камера
  └── fx          → частицы, туман, свет, оверлеи
```

---

## 1. Общие принципы

1. **Один манифест — один ассет.** `*.sceneasset.json`, рядом — геометрия.
2. **Тип определяет редактор и валидатор.** `kind` — дискриминатор.
3. **Ассет не знает про время.** Состояния/механизмы — чистые функции от `t`.
4. **Сцена собирает ассеты**, а не наоборот.
5. **Всё переиспользуемо:** LOD, варианты материалов, лицензия, теги, версия.
6. **Никаких UI-карточек.** Ассет — физический объект мира.

---

## 2. Манифест

```json
{
  "format": "sceneasset/1",
  "id": "chair-wooden",
  "title": "Деревянный стул",
  "kind": "prop3d",
  "category": "furniture",
  "tags": ["wood", "interior"],
  "geometry": {
    "type": "gltf",
    "file": "chair-wooden.glb",
    "sha256": "…",
    "units": "m",
    "up": "Y",
    "facing": "+Z"
  },
  "rig": null,
  "anchors": {
    "pivot": "bottom",
    "ground": true,
    "forward": "+Z",
    "bounds": [0.45, 0.9, 0.5]
  },
  "sockets": [],
  "states": [],
  "materials": [
    { "slot": "wood", "base_color": "#8B5A2B", "roughness": 0.7 },
    { "slot": "fabric", "base_color": "#3B4A5A", "roughness": 0.9 }
  ],
  "lod": [
    { "level": 0, "file": "chair-wooden.glb", "tris": 1200 },
    { "level": 1, "file": "chair-wooden_lod1.glb", "tris": 400, "max_distance": 8 }
  ],
  "license": { "name": "CC0", "author": "SceneEngine", "source": "internal" }
}
```

Обязательные: `format`, `id`, `kind`, `geometry.type`, `license.name`.
`id` — `[a-z0-9][a-z0-9-]{1,63}`.

---

## 3. Виды ассетов

### 3.1. `character`

```json
{
  "kind": "character",
  "family": "human",
  "archetype": "humanoid",
  "rig": "character-oldman.scenerig.json",
  "geometry": { "type": "gltf", "file": "oldman.glb" },
  "clips": ["idle", "talk", "wave"],
  "wardrobe": [
    { "slot": "hat", "socket": "head.top", "asset": "hat-monk" },
    { "slot": "robe", "mode": "skinned", "file": "robe.glb" }
  ]
}
```

- Скелет, клипы, морфы — по `RIG_FORMAT`.
- Гардероб: `skinned` (общий скелет) или `socket` (rigid prop).
- Редактор персонажа: Rig Inspector + Clip Editor + Wardrobe.

### 3.2. `prop3d`

- `.glb` без скелета (или со скелетом, если объект механический).
- `states` — простые клипы/трансформации: `door.open`, `wheel.spin`,
  `light.on`.
- `sockets` — точки крепления (сиденье, руль, крюк).
- `anchors.ground` — ставить на землю; `pivot: bottom|center|custom`.

### 3.3. `prop2d`

- `geometry.type = "svg"` или `"html"`.
- Части: `data-part="wheel"`, `data-rig` для простых механизмов.
- `views`: `front|side|corner`, `day|night`.
- `states`: механизмы (`wheel`, `swing`, `steam`, `blink`, `traffic-cycle`).

```json
{
  "kind": "prop2d",
  "geometry": { "type": "svg", "file": "car.svg", "viewbox": "0 0 400 200" },
  "parts": ["body", "wheel-front", "wheel-rear", "window"],
  "views": ["side", "front"],
  "states": [
    { "name": "drive", "mechanism": "wheel", "params": { "radius": 0.18 } }
  ]
}
```

### 3.4. `environment`

```json
{
  "id": "forest",
  "kind": "environment",
  "domain": "outdoor",
  "perspective": "side",
  "palette": {
    "day":    { "sky": ["#BFE3FF", "#EAF7FF"], "fog": "#CFE8F5", "ground": "#4F7942" },
    "sunset": { "sky": ["#F6B26B", "#7A4E8E"], "fog": "#E8B98A", "ground": "#3E5A34" },
    "night":  { "sky": ["#0B1322", "#1B2A45"], "fog": "#16233A", "ground": "#1E2B24" }
  },
  "layers": [
    { "id": "sky",    "depth": 0.0, "type": "gradient" },
    { "id": "far",    "depth": 0.2, "type": "svg", "file": "forest-far.svg", "repeat": true },
    { "id": "mid",    "depth": 0.5, "type": "svg", "file": "forest-mid.svg" },
    { "id": "ground", "depth": 1.0, "type": "svg", "file": "forest-ground.svg", "y": 0.72 }
  ],
  "scatter": [
    { "layer": "mid", "asset": "pine", "count": 18, "seed": 7, "y": [0.55, 0.75] }
  ],
  "fx": [
    { "type": "fog", "density": 0.25 },
    { "type": "dust", "seed": 11, "count": 40 }
  ],
  "camera": { "mode": "parallax", "speed": 0.35 },
  "formats": {
    "landscape": { "safe": 1.0 },
    "portrait":  { "safe": 0.85, "layers": { "far": { "scale": 1.2 } } }
  }
}
```

- `domain`: `outdoor | indoor | stage`.
- `depth` → `SceneKit.parallax`; `camera.mode`: `parallax | 2.5d | static`.
- `palette` — токены, не случайный hex; view выбирает палитру.
- `scatter` — детерминированный seeded PRNG (`SceneKit.scatter`).
- 3D-окружение — позже: `geometry.type = "gltf-scene"` + камера.

### 3.5. `fx`

```json
{
  "id": "dust-warm",
  "kind": "fx",
  "fx": { "type": "particles", "kind": "dust", "count": 40, "seed": 7,
          "color": "--brand-amber", "size": [1, 4], "speed": 0.2 }
}
```

Типы: `particles`, `fog`, `light`, `grain`, `vignette`, `rain`, `snow`,
`embers`, `trail`.

---

## 4. Категории объектов

Категория — для фильтрации и совместимости. Не путать с `kind`.

| Категория | Примеры |
|---|---|
| `nature` | tree, pine, bush, rock, grass, flower |
| `vehicle` | car, bus, bicycle, cart, boat, train |
| `furniture` | chair, table, desk, shelf, bench, bed |
| `architecture` | building, house, wall, lamp, sign, bridge |
| `interior` | monitor, coffee, plant, book, rug |
| `instrument` | microphone, camera, tool, weapon |
| `food` | bread, cup, bowl, basket |
| `character` | human, animal, winged |
| `effect` | dust, fog, light |
| `environment` | forest, city, studio |

Совместимость ассета с миром:

```json
"compat": {
  "domain": ["outdoor"],
  "environments": ["forest", "mountains"],
  "surface": ["ground"],
  "views": ["side"]
}
```

Правило: `domain` и `surface` обязательны; `environments` пустой = все миры
своего домена.

---

## 5. Состояния и механизмы

Состояние — именованное поведение, которое сцена включает ключом.

```json
"states": [
  { "name": "spin",  "mechanism": "wheel",  "params": { "radius": 0.18, "speed": 1 } },
  { "name": "open",  "mechanism": "hinge",  "params": { "axis": "Y", "angle": 95 } },
  { "name": "glow",  "mechanism": "light",  "params": { "color": "var(--brand-amber)" } },
  { "name": "walk",  "clip": "walk" }
]
```

- Механизм — чистая функция `(t, params) → transform/opacity`.
- Сцена задаёт ключи: `[{ "at": 0, "set": { "state": "spin" } }]`.
- Для персонажей состояние = клип + слой лица + процедурный idle.
- Никаких `setInterval`/`rAF`; всё через `seek(t)`.

---

## 6. Редактор (браузер)

### 6.1. Object Studio

Панели по типу:

- **prop3d:** импорт GLB, pivot/ground, материалы, сокеты, LOD, состояния,
  превью, валидация.
- **prop2d:** SVG-части, pivot, views, механизмы, слои.
- **character:** Rig Inspector, Clip Editor, Wardrobe (см. `RIG_FORMAT`).
- **environment:** слои, depth, палитры, скаттер, fx, камера, форматы.
- **fx:** параметры частиц/тумана/света, seed, превью.

Общий цикл:

```
import → validate → preview → save manifest → compile → publish to library
```

### 6.2. Rig Inspector (первый экран)

- дерево костей + rest-pose;
- оси и длины костей (диагностика);
- список морфов/визёмов;
- сокеты;
- клипы и скраб `seek(t)`;
- ошибки валидатора с кодами;
- кнопки `Re-scan`, `Export GLB`, `Open in Blender` (путь/инструкция).

### 6.3. Clip Editor

- таймлайн, ключи на кость, слой лица, loop, события;
- кривые/интерполяция;
- `bake` в `.glb`;
- предпросмотр через Babylon-драйвер.

### 6.4. Wardrobe

- слоты (`hat`, `robe`, `shoes`, `back`, `hand.R`);
- skinned или socket;
- варианты материалов;
- проверка пересечений (warning).

---

## 7. Пайплайн сборки

```
source/
  chair.blend
  chair.sceneasset.json
  chair.glb
clips/
  door-open.sclip.json
dist/
  chair.glb          (baked, optimized)
  chair.js           (base64 wrapper для iframe)
  thumbnail.png
```

Команды (план):

```bash
python -m backend.asset validate chair.sceneasset.json
python -m backend.asset compile chair.sceneasset.json --out dist/
python -m backend.asset thumbnail chair.sceneasset.json
```

`dist/` — артефакт, руками не правится. `thumbnail` — кадр из Babylon или
Blender; нужен для библиотеки (сейчас thumbnails нет — см. `STATUS.md`).

---

## 8. Правила качества

- Pivot на земле/в точке вращения, не в центре bounding box по умолчанию.
- Масштаб 1 unit = 1 м; объекты не «прилипают» к камере.
- Материалы: ≤ 4 слота на объект, текстуры ≤ 2k для фона, ≤ 1k для реквизита.
- LOD: 0 — камера, 1 — средний, 2 — дальний.
- Треугольники: реквизит ≤ 10k, машина ≤ 30k, персонаж ≤ 60k (LOD0).
- Все анимации in-place; мир двигает сцена.
- Лицензия обязательна; Mixamo/Adobe-клипы не коммитить.
- Теги и категория — для поиска и ИИ.

---

## 9. Совместимость со старым форматом

- `backend/scene_library.py` (`OBJECTS`, `ENVIRONMENTS`, `TEMPLATES`) остаётся
  рабочим источником для сцен.
- Новые манифесты **не заменяют** его сразу: компилятор умеет отдавать
  `html`/`css`/`js`-сниппет для существующего редактора.
- Постепенно `OBJECTS` превращается в индекс по `*.sceneasset.json`.
- `slides`/`__scene__` не трогаем — это уровень сцен, не ассетов.
