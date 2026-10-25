# RIG_STUDIO — браузерный инспектор и редактор персонажей

Первый шаг к собственному редактору: визуальная проверка рига, морфов и
манифеста до того, как персонаж попадёт в сцену.

**Сейчас:** `core/public/rig-studio.html` — инспектор,
`core/public/clip-editor.html` — редактор ключей.
**Дальше:** вкладка в `SceneEditor` + Wardrobe + публикация в библиотеку.

---

## 1. Что уже работает

```bash
docker compose up -d
# открыть:
http://localhost:5175/rig-studio.html
```

- загрузка `.glb`/`.gltf` по URL или с диска;
- Babylon-превью с орбитальной камерой и светом;
- дерево костей (клик — камера на кость);
- список морф-таргетов;
- список анимаций и скраб по кадрам, если они есть в файле;
- валидация через `POST /api/rig/validate`:
  - архетип, кости, веса, морфы, rest-поза, бюджет;
- редактор манифеста `scenerig/1`:
  - генерируется из загруженной модели;
  - `Copy` / `Download` (`*.scenerig.json`);
- подсказки: высота, число костей/морфов/треугольников, ошибки и warning'и.

Страница не пишет в БД и не сохраняет ассеты. Это инспектор, а не публикатор.

---

## 2. Почему отдельная страница

- Не зависит от Vue-сборки и тяжёлого редактора сцен.
- Работает как harness: можно быстро проверить новый GLB.
- Использует те же `/vendor/babylon.js` и `/vendor/babylonjs.loaders.min.js`,
  что и сцена.
- Валидация — на сервере, один источник правды (`backend/rig/`).

Когда прототип устоится, панели переезжают в Vue-компонент
`core/src/rig/RigStudio.vue` и вкладку редактора.

---

## 3. Что показывает валидатор

| Код | Смысл |
|---|---|
| `glb.parse` | файл не читается как GLB |
| `skin.missing` | у персонажа нет скина |
| `bones.missing` | нет обязательных костей архетипа |
| `bones.duplicate` | две кости маппятся в один канон |
| `bones.unmapped` | незнакомые кости (warning, можно в `bones.extra`) |
| `weights.attributes` | нет `JOINTS_0`/`WEIGHTS_0` |
| `weights.sum` | веса не суммируются в 1 |
| `weights.influences` | больше 4 влияний на вершину |
| `face.min` | не хватает морфов для липсинка |
| `pose.tpose` | руки почти горизонтальны, нужна A-pose |
| `pose.ground` | ступни не на `y=0` |
| `pose.facing` | персонаж смотрит не в `+Z` |
| `units.height` | рост вне 1.2–2.4 м |
| `anim.*` | пустые/битые клипы |
| `budget.*` | превышен бюджет треугольников/материалов |

Ошибки блокируют компиляцию; warning'и — повод посмотреть, но не блокер.

---

## 4. Манифест из инспектора

Инспектор собирает черновик:

```json
{
  "format": "scenerig/1",
  "id": "brunette",
  "family": "human",
  "archetype": "humanoid",
  "geometry": { "file": "brunette.glb", "units": "m", "up": "Y", "facing": "+Z" },
  "rest": { "pose": "A", "origin": "feet" },
  "bones": { "canonical": true, "map": { "...": "..." }, "extra": [] },
  "face": { "morphs": ["..."], "visemes": "oculus-15", "jaw_bone": "jaw" },
  "sockets": [],
  "clips": [],
  "license": { "name": "TBD" }
}
```

Черновик нужно довести руками:

- `id`, `title`, `license`;
- `sockets` (шляпа, рука, спина, седло);
- `clips` (после экспорта клипов);
- `bones.extra` для незнакомых костей.

Затем:

```bash
python -m backend.rig validate character.scenerig.json
```

---

## 5. Clip Editor

`core/public/clip-editor.html`:

- загрузка GLB, список костей, поиск;
- выбор кости → слайдеры X/Y/Z (delta от rest);
- таймлайн, play/loop, время;
- `Ключ кости` / `Ключ всех`, удаление ключа на времени;
- импорт/экспорт `*.sclip.json`;
- `Проверить` → `POST /api/rig/validate-manifest`;
- после экспорта: `python -m backend.rig bake ...` → GLB для Blender/Babylon.

Ядро вычислений — `core/public/vendor/scene-clip.js` (чистые функции `t`).
Тесты: `node scripts/test_scene_clip.mjs`.

## 6. Следующие панели

1. **Clip Editor v2** — кривые/easing, onion skin, события, слой лица.
2. **Wardrobe** — слоты, skinned/socket, варианты материалов.
3. **Converter** — RPM/Mixamo → канон с отчётом о переносе.
4. **Object Studio** — `prop3d`/`prop2d` (см. `ASSET_FORMAT.md`).
5. **Environment Composer** — слои, палитры, скаттер.

---

## 7. Ограничения прототипа

- Нет редактирования поз и весов.
- Нет сохранения в библиотеку.
- Нет загрузки клипов `.sclip.json` (только просмотр анимаций из GLB).
- Нет thumbnails.
- Валидация требует запущенного backend; без него превью работает, отчёт — нет.
