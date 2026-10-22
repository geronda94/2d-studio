# COMPONENT_PIPELINE.md — механизм создания компонентов (для ИИ-агента)

> Канон создания нового компонента презентаций. Цель — предсказуемый, повторяемый
> конвейер, пригодный для автоматизации ИИ: минимум импровизации, максимум правил,
> проверяемый результат на каждом шаге.
>
> Если что-то расходится с кодом — прав код (`AGENTS.md`, `useVariant.js`,
> `seed_components.py`). Этот документ — рабочая инструкция, а не источник истины.

---

## 0. TL;DR — конвейер

```
1. .vue           props из payload + relativeTime + useVariant
2. registry       core/src/config/componentsRegistry.js  (ключ = slug = имя файла)
3. seed           scripts/seed_components.py             (slug, title, type, cat, payload)
4. schemas        scripts/generate_schemas.py            (типы полей, enum, min/max)
5. examples       scripts/generate_examples.py           (example из /p/4 или default_payload)
6. manifests      scripts/seed_manifests.py              (description, manifest, required)
7. validate       POST /components/{slug}/validate?lint=true  → 0 errors
8. visual         слайд в тестовой презентации → рендер без ошибок
```

Порядок обязателен: `seed_components → generate_schemas → generate_examples → seed_manifests`.
Все генераторы идемпотентны и НЕ трогают кастомы (`is_custom`).

---

## 1. Контракт компонента

Компонент получает **все данные через props**. Движок (`SlidePresentation → Slide`)
делает `v-bind="payload"`: каждый ключ верхнего уровня `payload` становится пропом.

**Обязательные системные пропсы** (движок, не из payload):

```js
const props = defineProps({
  mobile: Boolean,                 // мобильный вид
  clicks: { type: Number, default: 0 },
  slideStartTime: { type: Number, default: 0 },
  // …далее — ключи payload (snake_case как есть)
})
```

**Время** — только через inject (локальное время слайда, мс):

```js
const relativeTime = inject('relativeTime', ref(0))
```

**Вариант отрисовки** (форма/материал) — через composable:

```js
const { itemVars, itemPrimaryVars, line, motion } = useVariant(computed(() => props.variant), '<Slug>')
```

Правила:
- Данные — **только из props**. Никакого хардкода текста/медиа/чисел.
- Цвета/фон — **только токены** (`var(--…)`) и `var(--item-*)` от варианта.
- Анимации — **детерминированы** от `relativeTime` (§5).
- Не писать свою шапку/тайминг — их даёт `Slide.vue` (title/subtitle/layout).

---

## 2. Куда положить и как назвать

| Слой | Папка | Регистрация | Когда |
|---|---|---|---|
| UI-блок | `core/src/components/ui/` | в `componentsMap` | элемент внутри слайда (карточки, таблицы, диаграммы) |
| Полноэкранный | `core/src/components/slides/` | в `componentsMap` | композиция на весь слайд (`*Slide`) |
| Внутренний | `ui/` | **НЕ** в реестре | building block для `*Slide`-обёрток (Lampada, RoiCalculator, ChatMockup…) |

**Ключ реестра = `slug` в БД = имя `.vue` файла.** Расхождение → пустой экран.
Контроль дрейфа: `python scripts/check_consistency.py` (**запускать с хоста** —
в backend-контейнере `core/` не смонтирован; иначе он видит устаревший registry).

Внутренние building blocks добавляй в `INTERNAL` в `check_consistency.py`,
если имя не подпадает под фильтр `*Modal|*Divider|*Picker|*Editor|*Logo|*Preview`.

---

## 3. Пошаговая инструкция

### Шаг 1. Файл компонента
Скопируй `core/src/components/_template/ComponentTemplate.vue` (канонический паттерн
«список айтемов с последовательным появлением») и перепиши под свою задачу.
Для композиций/медиа за основу бери существующий близкий компонент.

### Шаг 2. Props под payload
Объяви системные пропсы + все ключи `default_payload`. `variant: String` — если
компонент поддерживает варианты (а поддерживают почти все).

### Шаг 3. Разметка
- Корень получает `:style="{ ...itemVars, ...itemPrimaryVars }"`.
- Айтемы: `background: var(--item-bg)`, `borderRadius: var(--item-radius)`,
  `boxShadow: var(--item-shadow)`, `backdropFilter: var(--item-backdrop)`.
- Если фон айтема задаётся классом Tailwind — добавь класс `variant-item`
  (он включает `backdrop-filter` из `style.css`).
- Фон слайда — `var(--surface-bg)` (не хардкодь `bg-bg-base`).

### Шаг 4. Анимации
См. §5. Только `relativeTime`, `transition`/`TransitionGroup`, `Math.sin`.

### Шаг 5. Реестр
```js
// core/src/config/componentsRegistry.js
import MyThing from '../components/ui/MyThing.vue'
export const componentsMap = { /* … */ MyThing }
```

### Шаг 6. Сид
Добавь запись в `scripts/seed_components.py` (`components_data`), перед `EndMarkerSlide`:
```python
{
    "slug": "MyThing",
    "title": "Человеческое название",
    "type": type_ui,          # type_ui | type_slide | type_interactive
    "cat": cat_ui,            # cat_backend | cat_sales | cat_ui | cat_stats
    "payload": {              # default_payload — образец, вставляется в новый слайд
        "variant": "tech",
        # …поля…
    },
},
```
`start_time` внутри массивов — нарастающе, шаг **≥ 800–1000 мс** (нормализатор
в сиде всё равно подтянет плотность, но лучше сразу писать правильно).

### Шаг 7. Генераторы (в backend-контейнере)
```bash
docker compose exec backend python scripts/seed_components.py
docker compose exec backend python scripts/generate_schemas.py
docker compose exec backend python scripts/generate_examples.py
docker compose exec backend python scripts/seed_manifests.py
```

### Шаг 8. Манифест
В `scripts/seed_manifests.py`:
- `REQUIRED_FIELDS["MyThing"] = ["…"]` — обязательные поля верхнего уровня.
- `MANIFESTS["MyThing"] = {"description": "…", "manifest": "Подходит: … Не использовать: …"}`
  — это то, по чему ИИ выбирает компонент под задачу.

Затем снова `seed_manifests.py`.

### Шаг 9. Валидация
```bash
POST /components/{slug}/validate?lint=true   {"payload": {…default_payload…}}
```
Цель: `valid: true`, `errors: []`. `warnings` (no-hex / accent-budget / dense_timing) —
поправить: токены вместо hex, ≤4 акцентов, шаг ≥ 800 мс.

### Шаг 10. Визуальная приёмка
Добавь слайд с компонентом в тестовую презентацию (payload + `variant`), открой
`/p/{id}` и убедись, что рендер корректен (в т.ч. мобильный вид).

---

## 4. Данные и типизация

- **Ключи — snake_case** (`start_time`, `show_data_flow`, `lamp_side`).
- **Тип выводится** `generate_schemas.py` по имени ключа + типу значения.
  Единая точка правки типов — этот скрипт (`COLOR_KEYS`, `IMAGE_KEYS`, `ENUM_OPTIONS`, …).
- **Enum** объявляется в `ENUM_OPTIONS`. Уже заняты: `role`, `sender`, `align`, `size`,
  `frame`, `layout`, `lamp_side`. Новый enum-ключ → добавить в `ENUM_OPTIONS`
  (и он автоматически станет `enum` в `infer_scalar_type`).
- **Массивы**: `min_items: 1`, `max_items: max(n*2, 6)` (авто). Не делай массив пустым
  в `default_payload`, если он обязателен.
- **Полиморфные/опциональные массивы** (`to`, `values`) — в `PERMISSIVE_ARRAYS`.

### Подводные камни имён (проверено на практике)
| Ключ | Ловушка |
|---|---|
| `role`, `sender` | жёстко типизируются как enum `user/bot/assistant`. Для «роли человека» используй `caption`/`subtitle` |
| `image`, `icon`, `logo`, `photo` | → медиа/иконка. Для обычного текста не называй так |
| `color`, `*_color`, `fill`, `stroke` | → color (пикер). Свои цветовые поля добавляй в `COLOR_KEYS` |
| `description`, `desc`, `details`, `text` | → long_text |
| `*_position`, `object_position` | → position (`"x% y%"`) |
| `start_time`, `duration`, `delay` | → time (мс) |

---

## 5. Анимации — детерминизм обязателен

**Запрещено** (§11 `AGENTS.md`): `requestAnimationFrame`, CSS `animation: … infinite`,
SVG `<animate>`/`<animateMotion>`. Иначе покадровый/видео-рендер «угорает».

**Разрешённые паттерны:**
1. **Зацикленные эффекты** — математика от `relativeTime`:
   `Math.sin((t / 2000) * Math.PI * 2)` (пульс, качание, мерцание).
2. **Сложные переходы** — `watch(relativeTime)` со состоянием анимации.
3. **Простые появления** — `transition` + `relativeTime >= item.start_time`,
   `TransitionGroup` для списков.
4. **Смена контента по времени** — `<Transition :key="activeIndex">` (one-time).

**Compositor vs Paint — критично для рендера:**
При программном рендер ffmpeg/Playwright (`--disable-gpu`) **каждое изменение `paint`-свойств**
(`background-position`, `width`, `left`, `top`, `opacity` напрямую) перерисовывает DOM-узел
**каждый кадр**. Это даёт дёрганье и просадку FPS.

Вместо этого используй **`transform`** (compositor thread, zero-paint):
- `background-position: X%` → `transform: translateX(X%)` через overlay-элемент с `will-change: transform`.
- `width: 0 → 100%` → `transform: scaleX(0 → 1)` с `transform-origin: left`.
- `left/top` позиционирование → `transform: translate()`.

Правило: **`transform` и `opacity`** — безопасны (compositor). **`width`/`left`/`top`/`background-position`**
— ломают рендер (paint). Анимируй только через `transform`, `opacity`, `filter`.

**Тайминги айтемов**: `start_time` нарастающе и **разряженно** (шаг ≥ 800–1000 мс);
после последнего — ≥ 2000 мс воздуха. Исключение — `InteractiveArchitecture`
(там `start_time` только у ОДНОЙ ноды).

**Ритм** берётся из варианта: `useVariant().motion` (`appear_ms`, `stagger_ms`,
`count_ms`) — не хардкодь длительности.

---

## 6. Стили и палитра

- Фон айтема — `var(--item-bg)`; акцентного — `var(--item-primary-bg)`.
- Радиус/тень/рамка/паддинг — `var(--item-*)` от `useVariant`.
- **Вариант НЕ задаёт цвета** — только материал/форму/линии. Цвета — из токенов палитры.
- Резолв цвета: `getHexColor(key)` (legacy-имена → `var(--*)`, hex/var passthrough),
  прозрачность: `getColorAlpha(key, a)`.
- Быстрые дефолты для айтемов — шахматка `var(--item-accent-{(i%4)+1})`;
  для бейджей — `color-success/danger/warning/info` (+`-soft`).
- Разрешённый хардкод — только «материал»: specular-блики (`#FFFFFF` с opacity),
  тёмная зона кода, фиксированный белый `ReceiptCard`.

---

## 7. Документирование в библиотеке (БД)

Таблица `components` — «паспорт» компонента. Заполняется так:

| Поле | Источник | Кто заполняет |
|---|---|---|
| `slug` | = имя файла = ключ registry | `seed_components.py` |
| `title` | человеческое имя | `seed_components.py` |
| `type_id` / `categories` | `type_ui`/`type_slide`/`type_interactive`, `cat_*` | `seed_components.py` |
| `default_payload` | каркас (вставляется в новый слайд) | `seed_components.py` |
| `payload_schema` | типы/required/enum/min-max | `generate_schemas.py` |
| `example` | эталонное заполнение (из `/p/4` или fallback) | `generate_examples.py` |
| `description` + `manifest` | что это / когда использовать | `seed_manifests.py` |
| `is_custom` | `False` (managed из файла) | сид |

`manifest` — ключ к автоматическому выбору компонента ИИ: пиши «Подходит: … Не использовать: …».

---

## 8. Приёмка (чек-лист)

- [ ] `.vue` трансформируется Vite: `GET /src/components/…/MyThing.vue` → 200.
- [ ] `check_consistency.py` (с хоста): registry == db == .vue, без дрейфа.
- [ ] `POST /components/MyThing/validate?lint=true` → `valid: true`, `errors: []`.
- [ ] `default_payload` / `example` / `manifest` / `required` в БД заполнены.
- [ ] Слайд в тестовой презентации рендерится (desktop + mobile), без ошибок в консоли.
- [ ] Анимации детерминированы (нет rAF/infinite/`<animate>`).
- [ ] Цвета — токены; вариант отвечает только за форму.
- [ ] `p4`/`p13` (эталонные) не сломаны, счётчик компонентов в докax обновлён.

---

## 9. Реестр уроков (дополнять при каждом инциденте)

- **slug ≠ имя файла** → пустой экран (`BrowserMockupSlide` — не в реестре).
- **`role` занят enum** → поле переименовано в `caption` (PortraitLampSlide).
- **SVG-шум без `width/height`** → браузер растягивает на кадр, зерно крупное/размытое.
  Всегда задавай явные размеры (см. `gen_diademas_bg.py`).
- **`var(--item-bg)` без `backdrop-filter`** → фон полупрозрачный, но не «стекло».
  Добавляй `backdropFilter: var(--item-backdrop)` или класс `variant-item`.
- **Внутренние блоки** (`Lampada`, `RoiCalculator`, `ChatMockup`) — не в registry
  и не в `components.slug`, иначе `check_consistency` ругается.
- **`generate_examples.py`** берёт пример из `/p/4`; для новых компонентов — fallback
  на `default_payload` (это нормально).
- **Пустой `video_url`** в `AdvancedVideoSlide` → `AdvancedVideoPlayer` спамит
  warning «no supported sources» каждый кадр. В демо-презентациях задавай видео
  или чини гард в плеере.
- **`background-position` для анимации** → paint per frame в программном рендере.
  Используй `transform: translateX()` через overlay-элемент с `will-change: transform`.
  `transform` и `opacity` — compositor (zero-paint), всё остальное — paint (дёрганье).
  См. §5 Compositor vs Paint.

---

## 10. Кейсы (эталонные реализации)

### PortraitLampSlide — портрет с лампадкой (перенос из Diademas)
- Файлы: `slides/PortraitLampSlide.vue` (регистрируемый) + `ui/Lampada.vue` (внутренний).
- Payload: `image`, `name` (required), `caption`, `description`, `lamp`,
  `lamp_color`, `flame_color`, `variant`.
- Лампадка **всегда по центру ПОД** окладом (`top-full`, `left-1/2 -translate-x-1/2`).
  Цепочки уходят под оклад — визуально лампадка «подвесная».
- Анимация блика оклада: overlay `.portrait-sheen` с `transform: translateX()`
  (compositor, zero-paint). **НЕ** `background-position` — он даёт paint per frame
  в программном рендере (см. §5 Compositor vs Paint).
- Анимация лампадки: качание/мерцание — `Math.sin(relativeTime)` в `Lampada`.
- Цвета лампадки — токены (`color-primary`/`color-warning`), поэтому она адаптируется
  под палитру (в дневной Diademas — лесная, в тёмной — золотая).

### TimelineSlide — линия времени
- Файл: `slides/TimelineSlide.vue`.
- Payload: `events[]` (`id`, `year`, `title`, `description`, `image`, `start_time`),
  `show_images`, `variant`.
- Анимация: `exactProgress` — дробный индекс (0..len-1), интерполирует между точками
  по времени. `fillScale` — `transform: scaleX()` для прогресса линии (compositor).
  Точки позиционируются абсолютно через `dotPos(i)`, годы появляются по `start_time`.
- Контент чередует сторону картинки по чётности активного индекса.

Оба — пример «композиционного» компонента (не список айтемов): данные приходят
объектом/массивом объектов, время ведёт активное состояние.
