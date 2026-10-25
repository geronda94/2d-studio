# API — справочник SceneEngine

Базовый URL: `http://localhost:8002` (или `/api/...` через Vite).
Авторизация: cookie-сессия + CSRF для мутаций (если `AUTH_MODE=on`).
В dev по умолчанию `AUTH_MODE=off`.

---

## 1. Презентации

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/presentations/` | список |
| GET | `/presentations/{id}` | презентация + `slides` |
| POST | `/presentations/` | создать |
| PUT | `/presentations/{id}` | обновить |
| DELETE | `/presentations/{id}` | удалить |
| GET | `/presentations/{id}/access` | права |
| GET | `/presentations/{id}/tokens` | тема |
| GET | `/presentations/{id}/config` | brand config |
| POST | `/presentations/{id}/slides` | создать legacy-элемент/EndMarker |
| PUT | `/presentations/slides/{slide_id}` | обновить legacy-элемент |

`GET /presentations/{id}` возвращает `slides[]` — для сцен это элементы с
`component: "__scene__"` и полями `kind`, `duration`, `code`, `props`,
`props_schema`, `track`, `z_index`.

---

## 2. Сцены

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/presentations/{id}/scenes` | список сцен |
| POST | `/presentations/{id}/scenes` | создать сцену |
| PUT | `/presentations/scenes/{scene_id}` | обновить |
| DELETE | `/presentations/scenes/{scene_id}` | удалить |

Тело:
```json
{
  "slide_id": "scene-1720000000000",
  "component": "__scene__",
  "kind": "scene",
  "start_time": 0,
  "duration": 6000,
  "title": "Лесная трасса",
  "layout": "col",
  "order_index": 0,
  "code": {
    "html": "<div class=\"scene\">...</div>",
    "css": ".scene{position:absolute;inset:0}",
    "js": "window.scene={seek(t){}}"
  },
  "props": {},
  "props_schema": {},
  "track": "main",
  "z_index": 0,
  "data": { "payload": {} },
  "events": []
}
```

Валидация:
- `code` — объект;
- `html/css/js` — строки;
- `duration > 0`;
- иначе `422 { message, errors }`.

---

## 3. Библиотека

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/scene-library/templates` | все шаблоны сцен |
| GET | `/scene-library/templates/{slug}` | шаблон |
| GET | `/scene-library/environments` | миры |
| GET | `/scene-library/environments/{slug}` | мир |
| GET | `/scene-library/environments/{slug}/objects` | совместимые объекты |
| GET | `/scene-library/objects` | все объекты |
| GET | `/scene-library/objects?environment=forest` | фильтр |
| GET | `/scene-library/objects/{slug}` | объект |
| GET | `/scene-library/characters` | готовые актёры (Rive) |
| GET | `/scene-library/characters/{slug}` | карточка актёра |
| POST | `/scene-library/text-to-visemes` | `{text,start,end}` → `[{t,viseme}]` |
| GET | `/scene-library/compatibility` | матрица совместимости |
| POST | `/scene-library/validate-composition` | проверить состав |

`validate-composition`:
```json
{ "environment": "office", "objects": ["desk", "car"] }
```
→
```json
{ "valid": false, "errors": [{ "path": "objects.car", "message": "car is not allowed in office" }] }
```

---

## 4. Learnings (реестр ошибок)

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/scene-library/learnings` | список |
| GET | `/scene-library/learnings?category=visuals&q=theme` | фильтр |
| POST | `/scene-library/learnings` | добавить запись |

Тело:
```json
{
  "category": "visuals",
  "symptom": "Editor preview is black",
  "cause": "Theme variables not injected",
  "fix": "Fallback to .slides-container + defaults",
  "rule": "SceneHost must work outside .slides-container",
  "scene_ref": "scene-demo-1",
  "tags": ["editor", "theme"],
  "status": "active",
  "source": "ai"
}
```

ИИ обязан:
1. читать `GET /scene-library/learnings` перед генерацией;
2. добавлять новую запись после QA/ревью, если найдена ошибка;
3. не дублировать существующие правила.

---

## 5. AI / озвучка

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/presentations/{id}/generate-speech` | TTS |
| POST | `/presentations/{id}/generate-slides` | генерация (legacy) |
| POST | `/presentations/{id}/generate-from-audio` | из аудио |
| POST | `/presentations/{id}/change-set` | атомарные операции |
| GET | `/presentations/{id}/ai-context` | контекст для агента |
| GET | `/ai/tools` | инструменты |

---

## 6. Рендер

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/renders/presentation/{id}` | запустить рендер |
| GET | `/renders/jobs/{id}` | статус |
| GET | `/renders/presentation/{id}` | список |
| DELETE | `/renders/{job_id}` | отменить |

---

## 7. Проекты/папки/темы

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/projects/` | проекты |
| GET | `/projects/{slug}` | проект |
| GET | `/projects/{id}/tokens` | токены |
| PUT | `/projects/{id}/tokens` | обновить токены |
| GET | `/variants/` | варианты |
| GET | `/presets/` | пресеты |

---

## 7.5. Риги (SceneRig)

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/rig/archetypes` | канонические архетипы и кости |
| GET | `/rig/health` | версия валидатора |
| POST | `/rig/validate` | валидировать загруженный `.glb`/`.gltf` |
| POST | `/rig/validate-manifest` | валидировать `scenerig`/`sceneasset`/`sceneclip` + GLB |

`POST /rig/validate` — `multipart/form-data`:

```bash
curl -X POST http://localhost:8002/rig/validate   -F "file=@core/public/models/brunette.glb"   -F "archetype=humanoid"
```

Для статического объекта: `-F "require_rig=false"`.

`POST /rig/validate-manifest` — `multipart/form-data` с полем `manifest`
(JSON-строка) и необязательным `file` (GLB). Путь в `geometry.file` заменяется
на имя загруженного файла.

Ответ — отчёт:

```json
{
  "ok": true,
  "archetype": "human/humanoid",
  "errors": 0,
  "warnings": 2,
  "facts": { "joints": 67, "morphs": 72, "triangles": 13317 },
  "issues": [ { "level": "warning", "code": "budget.materials", "message": "…" } ],
  "children": []
}
```

CLI:

```bash
python -m backend.rig scan model.glb --archetype humanoid
python -m backend.rig validate character.scenerig.json
python -m backend.rig compile character.scenerig.json --out dist/
```

---

## 7.6. Scene-ассеты (пользовательские объекты)

Сохранённые объекты/персонажи/окружения из Object Studio. Встроенная библиотека
(`scene_library.py`) здесь не дублируется.

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/scene-assets?kind=prop3d&q=` | список сохранённых ассетов |
| GET | `/scene-assets/{id\|slug}` | ассет + манифест |
| POST | `/scene-assets` | создать (slug уникален) |
| PUT | `/scene-assets/{id}` | обновить |
| DELETE | `/scene-assets/{id}` | удалить |
| POST | `/scene-assets/upload` | загрузить `.glb`/`.svg`/картинку в `/uploads/scene-assets` |

Создание:

```json
{
  "slug": "chair-wooden",
  "title": "Деревянный стул",
  "kind": "prop3d",
  "category": "furniture",
  "source_url": "/uploads/scene-assets/abc-chair.glb",
  "manifest": {
    "format": "sceneasset/1",
    "id": "chair-wooden",
    "title": "Деревянный стул",
    "kind": "prop3d",
    "geometry": { "type": "gltf", "file": "/uploads/scene-assets/abc-chair.glb" },
    "license": { "name": "CC0" }
  }
}
```

`POST /scene-assets/upload` возвращает `url`, `filename`, `size`, `kind` и
`validation` (для GLB — отчёт SceneRig с `require_rig=false`).

---

## 8. Ошибки

- `422` — валидация; тело: `{ message, errors: [{ path, type, message }] }`.
- `404` — не найдено.
- `401` — требуется авторизация.
- `403` — нет прав.
- `500` — смотреть `docker compose logs -f backend`.

---

## 9. Пример: создать сцену из шаблона

```bash
TPL=$(curl -s http://localhost:8002/scene-library/templates/forest-drive)
# взять code/props/duration/cues и собрать payload
curl -X POST http://localhost:8002/presentations/1/scenes \
  -H 'Content-Type: application/json' \
  -d '{"slide_id":"scene-1","component":"__scene__","kind":"scene",
       "start_time":0,"duration":7000,"title":"Forest drive","order_index":0,
       "code":{...},"props":{...},"cues":[...],"data":{"payload":{}}}'
```
