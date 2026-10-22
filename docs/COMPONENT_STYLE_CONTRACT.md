# COMPONENT_STYLE_CONTRACT — материал vs палитра (канон стилей компонента)

Единый контракт: как контентный компонент получает данные, цвета и форму. Нарушение
любого пункта — баг (слайд перестаёт следовать теме/варианту при их смене).

> Две таблицы — **две ортогональные оси**. Не смешивать.
> - `design_tokens` — **палитра/тема**: цвета и шрифты. Что «чем покрашено».
> - `style_variants` — **материал/форма**: фон-материал, радиус, тень, границы, линии, ритм.
>   Что «как нарисовано». Цвета вариант НЕ задаёт.

---

## 1. Поток данных

```
legacy DB "components"             frontend
  ├─ slug ───────────────────────► componentsRegistry.componentsMap[slug] = .vue  (идентичность)
  ├─ default_payload ─────────────► template для нового слайда
  ├─ payload_schema ──────────────► DynamicJsonEditor (тип инпута) + POST /validate
  └─ example / manifest ──────────► подсказки ИИ

slides.data.payload ──────────────► v-bind="payload"  (пропсы, snake_case)
Slide.vue ────────────────────────► inject('relativeTime')  (локальное время слайда)

design_tokens   (палитра) ────────► useTheme  → var(--*)   на .slides-container
style_variants  (материал) ───────► useVariant(slug,'X') → --item-* / line / motion
```

- Данные — только из props + `inject('relativeTime')`. Никаких данных в коде.
- Системные пропсы: `mobile`, `clicks`, `slideStartTime`.
- `variant` — top-level поле payload; резолв: `payload.variant → presentation.variant → tech`.

---

## 2. Обязательный паттерн применения варианта

```js
import { useVariant } from '../../composables/useVariant'
const { itemVars, itemPrimaryVars, line, motion } = useVariant(
  computed(() => props.variant), 'ТочныйSlug',   // slug = имя .vue (для components.<slug> override)
)
```
`:style="{ ...itemVars, ...itemPrimaryVars }"` вешается на корень компонента; элементы читают
CSS-переменные. Если элемент имеет `background: var(--item-bg)` — он ОБЯЗАН нести
`backdropFilter: var(--item-backdrop)` **и** `WebkitBackdropFilter` (не наследуется).

### Доступные переменные
| Переменная | Смысл |
|---|---|
| `--item-bg` / `--item-primary-bg` | фон-материал айтема (solid/gradient/blur/rgb) |
| `--item-backdrop` / `--item-primary-backdrop` | backdrop-filter (стекло) |
| `--item-radius` / `--item-primary-radius` | радиус |
| `--item-shadow` / `--item-primary-shadow` | тень |
| `--item-border-width` / `--item-border-style` / `--item-border` | граница |
| `--item-padding` / `--item-gap` | внутренние отступы |
| `line: { color, style, dash, width, animation }` | SVG-линии |
| `motion: { appear_ms, stagger_ms, count_ms }` | ритм анимаций (без хардкода длительностей) |

---

## 3. Правила (нарушение = дефект)

1. **Материал айтема — только `var(--item-*)`.** Фон карточки/ноды/строки/панели —
   `var(--item-bg)`, НЕ `bg-bg-base`/`bg-bg-surface`/`bg-white`/`var(--bg-surface)`.
2. **Радиус/тень карточки — только `var(--item-radius)`/`var(--item-shadow)`.**
   Tailwind `rounded-lg/xl/2xl`, `shadow-md/lg/xl` — запрещены для контейнеров/карточек.
   Для иконок-плиток допустим производный `calc(var(--item-radius) - 4px)`.
   `rounded-full` для точек/аватаров/индикаторов — легитимен (не материал карточки).
3. **Mobile и desktop — одна token-модель.** Различается раскладка (`mobile` prop),
   но НЕ материал: mobile-ветка не смеет подменять `var(--item-*)` на `bg-bg-surface`.
4. **Цвет — только из палитры** (`var(--color-*)`, `var(--item-accent-1..4)`, `var(--chart-N)`).
   Hex в контенте запрещён (кроме бренд-лого/терминала/кода — см. §5).
   Strim/overlay/«подложка под текст» — `rgb(var(--bg-base-rgb) / α)`, НЕ `getColorAlpha('var(--bg-base)', α)`.
   Текст на цветной плашке — `var(--text-on-color)`.
5. **Вариант НЕ задаёт цвет, тема НЕ задаёт радиус/тень** (см. инвариант выше).
6. **Ритм — из `motion`**, шаг reveal ≥ 800мс (§8.3), анимации детерминированы от
   `relativeTime` (без rAF/infinite/`<animate>`), только `transform`/`opacity`.
7. **Обёртка `*Slide`** прокидывает `:variant` во внутренний UI-компонент; внутренний
   сам зовёт `useVariant` и применяет `--item-*`.

---

## 4. Периметр (кто обязан соблюдать)

Обязаны: все зарегистрированные в `componentsMap` контентные компоненты (кат. `ui`/`slide`)
и внутренние building-blocks, которые рендерят контент (ChatMockup, CodeWindow, BeforeAfter,
RoiCalculator, Ecosystem, AnimatedStats, ProgressScale, TechCard, NodeFlow, WindowHeader).

## 5. Осознанные исключения (whitelist)

| Группа | Файлы | Почему |
|---|---|---|
| Chrome редактора | `*Modal`,`*Picker`,`TimePicker`,`DynamicJsonEditor`,`PageSkeleton`,`SafeComponentPreview` | вне `.slides-container`, живут на фикс. тёмном `:root` |
| Тёмная зона кода/терминала | `TerminalMockup`, `CodeWindow`, `CodeExplain`, `AdvancedVideoPlayer`, `BrowserMockup` | Shiki/терминал намеренно тёмные; рамка/радиус — всё равно из варианта |
| Бренд-фикс | `It2bLogo`, `Lampada`, `PortraitLampSlide`, `ProjectBrand`, `OutroSlide` | лого/лампадка/QR — фиксированный бренд |
| Бумага | `ReceiptCard` | фиксированный белый «чек» (по AGENTS.md) |
| Служебный | `EndMarkerSlide` | без контента |

---

## 6. Проверка перед сдачей

```bash
# 1. payload-валидация (schema + style-lint: no-hex/accent-budget/density/contrast)
docker compose exec backend python -c "..."   # POST /components/{slug}/validate?lint=true

# 2. статический guard по контракту стиля
python3 scripts/check_consistency.py           # slug ↔ registry ↔ .vue
python3 scripts/style_guard.py                 # material/palette-инварианты (см. §3)

# 3. визуальный QA (desktop И mobile)
docker compose exec backend python scripts/qa_audit.py <pres> <i0> <i1> desktop
docker compose exec backend python scripts/qa_audit.py <pres> <i0> <i1> mobile
```

Цель: `flagged=0` и в desktop, и в mobile; смена варианта (tech ↔ diademas ↔ classic)
не должна менять палитру, а смена темы — форму (радиусы/тени).
