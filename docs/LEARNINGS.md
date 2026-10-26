# LEARNINGS — реестр ошибок и правил

Цель: каждая найденная ошибка превращается в правило, которое ИИ читает
перед генерацией и не повторяет.

---

## 1. Где хранится

Два уровня:
- **БД** `scene_learnings` + API `/scene-library/learnings` (машиночитаемо).
- **Этот файл** — человекочитаемый обзор и процесс.

Модель:
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

Категории:
`determinism`, `layout`, `compatibility`, `visuals`, `audio`, `process`, `performance`.

---

## 2. Процесс

### Перед генерацией
1. `GET /scene-library/learnings?status=active`
2. Прочитать правила категории.
3. Учесть в коде/сцене.

### Статусы
- `proposed` — предложено ИИ, ещё не правило.
- `active` — утверждено человеком, используется.
- `archived` — устарело.

`POST /scene-library/learnings` с `source=ai` создаёт `proposed`.
Человек утверждает: `POST /scene-library/learnings/{id}/approve`.
Архив: `POST /scene-library/learnings/{id}/archive`.

### После QA / ревью
1. Найти ошибку.
2. Исправить.
3. Добавить запись `POST /scene-library/learnings`:
   - symptom — что видно;
   - cause — почему;
   - fix — как исправили;
   - rule — как не повторить;
   - tags/category.
4. Если правило уже есть — не дублировать, а обновить/уточнить.

### На ревью
Человек видит список ошибок и правил; может архивировать (`status=archived`).

---

## 3. Начальные записи

| Категория | Симптом | Правило |
|---|---|---|
| layout | `querySelector` null в iframe | Сцена всегда в `<div class="scene">` |
| process | Seed обновил не ту сцену | Искать по `slide_id`, не `.first()` |
| visuals | Чёрное превью редактора | Тема + дефолтные CSS-переменные вне `.slides-container` |
| visuals | Светлый хром редактора | Задавать `--*-rgb` переменные |
| process | 404 после нового роутера | Рестарт backend + curl |
| process | `git push` refspec main | `git branch -M main` |
| process | Утечка infra-доков | Проверять staged files перед push |
| visuals | `view` не доходит | Проверить всю цепочку до CSS |
| compatibility | Фонарь в офисе | `domain/environments` + фильтр |
| process | Cues не влияют | Шаблон читает `window.__sceneCues` |
| determinism | Анимация «плывёт» | Только `seek(t)`, без rAF/Date.now |
| performance | Тяжёлый blur | Предразмытые слои, transform/opacity |

---

## 4. API

```http
GET  /scene-library/learnings?category=visuals&status=active
GET  /scene-library/learnings?q=theme
POST /scene-library/learnings
```

### Пример POST
```json
{
  "category": "compatibility",
  "symptom": "Машина в офисе",
  "cause": "Не проверен environment",
  "fix": "Фильтр объектов по environment",
  "rule": "Сначала выбрать мир, потом объект",
  "tags": ["objects", "office"],
  "source": "ai"
}
```

---

## 5. Что считать хорошей записью

- Симптом воспроизводим.
- Причина конкретна (файл/поле/шаг).
- Исправление проверено.
- Правило короткое и применимое к будущим сценам.
- Есть теги/категория.

Плохо: «сцена сломалась, починили».
Хорошо: «`root` null, потому что HTML не обёрнут в `.scene`; правило: всегда оборачивать».

---

## 6. Сид

`python scripts/seed_learnings.py` — добавляет начальные записи, не дублирует
по `symptom`.

---

## 7. Персонажи: руки и локти (обязательное правило)

### Симптом
Пользователь видит «руки вывернуты назад»; ладонь/пальцы смотрят за спину,
особенно в talk-позе и при взгляде сбоку.

### Причина (три независимые ошибки)
1. `add_oriented_sphere` для ладони получал `y_axis=(0, 1, 0)` для обеих рук.
   У левой ладонь смотрела к бедру, у правой — наружу. Нужен зеркальный
   `y_axis=(0, sx, 0)`.
2. `rotate_mesh(hand, palm_c, d, 32°)` — дополнительный roll вокруг оси руки
   уводил пальцы назад. Никакого roll не нужно: плоскость ладони уже задана
   ориентацией эллипсоида.
3. В `scene-rig.js` `lowerArm` имел положительный X в talk-позе. Для этого
   скелета положительный X сгибает локоть **за спину**. Натуральный сгиб —
   отрицательный X.

### Правило
- Ладонь: `add_oriented_sphere(..., d, (0, sx, 0))`.
- Пальцы: вниз по предплечью, большой палец вперёд (`-Y`).
- Никаких `rotate_mesh` вокруг оси руки.
- В рантайме: `lowerArm` X < 0 (вперёд), X > 0 запрещён.
- Плечо: рукав из 3 колец с весами `shoulder/chest → shoulder/upperArm → upperArm`.
  Патч на 100% `upperArm` при подъёме становится шаром; если патч нужен — 50/50.
- Проверка: рендер обеих рук сбоку (`+X` и `-X`) в rest и talk;
  wave — дополнительно сзади (`+Y`) и в 3/4.


## 8. Hero-риги: T-pose и наклон головы

- Импортированные hero-меши (Avatar SDK, RPM) часто стоят в **T-pose**, а не
  в A-pose. Локальный Euler по `upperArm` только скручивает/уводит руку
  вперёд. Правильно: повернуть вокруг **мира Z** с пересчётом через
  родителя: `local = parentQ⁻¹ · Rz · parentQ · rest`.
- Голова у этих же ригов лежит с наклоном; локальные `x`-смещения дают
  «смотрит в потолок». Вводится `headPitch` как калибровка rest-позы;
  анимационные наклоны головы для hero-ригов лучше не задавать локальным
  Euler без отдельной проверки.
- Отображать HD-базу и процедурную базу как два класса: у HD фиксированный
  гардероб/идентичность, у процедурной — параметры и массовка.
