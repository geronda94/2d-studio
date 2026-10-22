# ASSETS — полноценный DAM для SceneEngine

Цель: единая библиотека ассетов для сцен, миров, объектов, персонажей,
озвучки, рендеров и документов. С метаданными, вариантами, тегами,
коллекциями, правами и использованием.

---

## 1. Типы ассетов

| Тип | Пример | Хранение |
|---|---|---|
| `image` | фон, текстура, спрайт | файл |
| `video` | b-roll, скринкаст | файл |
| `audio` | озвучка, музыка, SFX | файл |
| `font` | шрифт | файл |
| `svg` | иконка, элемент | файл/код |
| `rig` | персонаж (SVG/Rive/Spine) | файл + JSON |
| `object` | объект сцены | код/JSON |
| `world` | окружение | HTML/CSS |
| `template` | сцена | JSON/код |
| `render` | готовый mp4 | файл |
| `document` | бриф, сценарий | файл |

---

## 2. Метаданные

Общие:
- `title`, `slug`, `description`;
- `type`, `category`, `tags[]`;
- `source` (upload / generated / library);
- `author`, `license`, `rights`;
- `checksum`, `size`, `mime`;
- `created_at`, `updated_at`, `version`;
- `status` (draft/active/archived);
- `thumbnail`.

Для медиа:
- `width`, `height`, `duration_ms`, `fps`, `color_space`, `has_alpha`.

Для 2D:
- `palette[]`, `style_tags[]`;
- `compatibility`: `domain`, `environments`, `surface`;
- `views[]`, `default_view`;
- `anchor` (ground/wall/sky/desk);
- `default_scale`;
- `rig` (parts/clips/visemes).

---

## 3. Варианты

Один ассет = много вариантов:
- формат/разрешение (16:9, 9:16, 1:1);
- цвет/палитра;
- ракурс (`front/side/...`);
- состояние (day/night, on/off);
- язык озвучки;
- качество (proxy/full).

Модель:
```
asset
  └─ asset_variants (label, format, width, height, file, metadata)
```

---

## 4. Коллекции и теги

- `asset_tags` — свободные теги.
- `asset_collections` — наборы («Лес», «Город», «Персонажи», «Музыка»).
- `asset_collection_items`.
- Поиск по тегам, типу, совместимости, цвету, дате, автору.

---

## 5. Использование

`asset_usages`:
- где используется (project/presentation/scene/object);
- роль (background, character, voice, sfx);
- дата;
- при удалении — warning «используется в N сценах».

Это защищает от «удалил фон — сломались 20 сцен».

---

## 6. Версии и права

- `asset_versions` — история файлов/кода.
- `license`, `rights`, `attribution`, `expires_at`.
- Для AI-генераций — `model`, `prompt`, `seed`, `provider`.
- Для внешних ассетов — источник и лицензия.

---

## 7. API (план)

```
POST   /assets/upload
GET    /assets?type=image&tag=forest&environment=forest
GET    /assets/{id}
PUT    /assets/{id}
DELETE /assets/{id}
POST   /assets/{id}/variants
GET    /assets/{id}/usages
POST   /assets/{id}/collections
GET    /assets/search?q=...
```

ИИ читает `GET /assets?...` перед генерацией, чтобы переиспользовать
существующие ассеты, а не плодить дубли.

---

## 8. UI

- Grid/list с превью.
- Фильтры: тип, теги, мир, совместимость, цвет, дата.
- Карточка: превью, метаданные, варианты, использования, права.
- Drag в сцену.
- «Заменить» с сохранением позиции/масштаба.
- «Сохранить объект из сцены в библиотеку».
- Bulk upload, auto-thumbnails.

---

## 9. Хранилище

Сейчас: `uploads/` и `backend/media/` (локально).
Дальше:
- S3-совместимое хранилище (MinIO/S3);
- CDN для превью;
- checksum/dedupe;
- proxy-версии для редактора, full — для рендера.

---

## 10. Фазы

1. **MVP**: таблица `assets`, upload, list, tags, thumbnail, usage.
2. **Variants**: форматы/ракурсы/цвета.
3. **Search**: фильтры + полнотекст.
4. **Rights**: лицензии/атрибуция.
5. **AI**: генерация ассетов и авто-теги.
6. **S3/CDN**: масштабирование.

## 11. Связь с объектами

Объект сцены (`obj-car`) — это **код**, а не файл. В DAM он может быть
`type=object` с полями `code`, `props_schema`, `mechanics`, `views`.
Так библиотека объектов и DAM становятся одной системой.
