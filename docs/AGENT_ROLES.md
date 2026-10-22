# AGENT_ROLES — роли ИИ в производстве сцен

Цель: ИИ делает объём, человек утверждает. Каждая роль читает
`docs/CHANNEL_PRAVOSLAVIE.md`, `docs/SCENES.md`, `docs/ANIMATION.md`,
`docs/LEARNINGS.md` и `GET /scene-library/learnings`.

---

## 1. Script Analyst

**Вход:** сценарий `.md`, бриф проекта.
**Выход:** список смысловых блоков:
```json
[
  {"id":"hook","text":"...","theme":"ставка","seconds":5},
  {"id":"fact","text":"...","theme":"факт","seconds":6}
]
```
**Правила:**
- не менять текст сценария;
- выделять один смысловой акцент на блок;
- отмечать, где нужен эксперт/цитата/цифра;
- проверять длину: 4–7 с на блок.

## 2. Storyboard Director

**Вход:** блоки Script Analyst + каталог миров/шаблонов.
**Выход:** раскадровка:
```json
{
  "episode": "Э1",
  "scenes": [
    {"template":"prav-studio-host","world":"studio-prav","cast":["host"],
     "caption":"Империя до 1905","seconds":6,"monitor_media":""}
  ]
}
```
**Правила:**
- 3–5 вариантов на ключевую сцену, выбрать сильнейший;
- чередовать студию и исторические миры;
- не ставить два одинаковых шаблона подряд без причины;
- учитывать 16:9 и 9:16;
- утверждение человеком обязательно.

## 3. Scene Builder

**Вход:** одна сцена раскадровки.
**Выход:** `code`/`props`/`cues` для `POST /presentations/{id}/scenes`.
**Правила:**
- использовать шаблон + `object_styles`/`extra_html`, не переписывать всё;
- `window.scene.seek(t)` — единственный источник времени;
- `SceneKit.cues` для ключей, `scatter` для массовки;
- никаких `rAF`, `Date.now`, `setInterval`, `Math.random`;
- проверить `GET /scene-library/learnings?status=active` перед генерацией.

## 4. QA Agent

**Вход:** созданная сцена.
**Выход:** отчёт:
```json
{"valid":true,"errors":[],"warnings":[],"screenshots":[]}
```
**Проверки:**
- forbidden APIs;
- детерминизм: два `seek` → одинаковый кадр;
- overflow/scroll;
- contrast;
- совместимость мира/объектов;
- тайминг;
- 16:9/9:16.

**После исправления:** `POST /scene-library/learnings` со `source=ai`,
`status=proposed`. Человек утверждает.

## 5. Visual Researcher

**Вход:** тема/эпоха.
**Выход:** референсы, палитра, детали среды, 3–5 идей сцен.
**Правила:**
- не выдумывать факты/цены/цитаты;
- источники — в отчёте;
- визуал — через среду и свет, не через стоковые клише.

## 6. Asset Librarian

**Вход:** новые объекты/миры/ассеты.
**Выход:** карточки с метаданными, тегами, совместимостью, превью.
**Правила:**
- `domain`/`environments`/`surface`/`views`;
- не дублировать существующий объект;
- сохранять источник/лицензию.

## 7. Human Reviewer (человек)

- утверждает раскадровку и каждую сцену;
- оставляет точечные правки;
- утверждает `proposed` learnings;
- финальное «да» на рендер.

---

## Процесс

```
Script Analyst → Storyboard Director → [human approve]
→ Scene Builder → QA Agent → [human approve]
→ Render Operator → [human approve] → publish
```

## Формат ответа агента

```json
{
  "role": "Scene Builder",
  "summary": "Сцена входа в студию",
  "scene": {"template":"prav-studio-host","props":{},"cues":[]},
  "warnings": [],
  "learnings_used": ["id1","id2"]
}
```

Все изменения — через API/ревизии, с audit trail.
