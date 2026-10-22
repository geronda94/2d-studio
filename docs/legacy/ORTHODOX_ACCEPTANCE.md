# ORTHODOX_ACCEPTANCE — критерии приёмки компонентов канала

Единый чек-лист для всех компонентов `docs/ROADMAP_ORTHODOX.md`. Нарушение = брак.
Агент обязан самопроверить каждый пункт **до** сдачи; ревьюер перепроверяет после правок.

## A. Файл и регистрация

- A1. Файл: `core/src/components/ui/<Slug>.vue`. Имя файла == slug == `defineProps`-контракт.
- A2. `<script setup>` (Composition API), без Options API.
- A3. Метаданные рядом: `scripts/_orthodox_meta/<Slug>.json` (см. §F).

## B. Контракт пропсов и данных

- B1. `defineProps({ mobile: Boolean, variant: String, ...ключи payload })`.
- B2. Все данные — из props. Никакого хардкода текста/чисел/медиа/цветов в шаблоне.
- B3. Компонент **не** рисует заголовок/подзаголовок слайда (это делает `Slide.vue`).
- B4. Ключи — snake_case.

## C. Стили и тема

- C1. `useVariant(computed(() => props.variant), '<Slug>')` → `itemVars/itemPrimaryVars/motion`.
- C2. Корень: `:style="{ ...itemVars }"`; айтемы: `background: 'var(--item-bg)'`,
  `borderRadius: 'var(--item-radius)'`, `boxShadow: 'var(--item-shadow)'`,
  `backdropFilter: 'var(--item-backdrop)'`.
- C3. Цвета — только `var(--...)`, `getHexColor()`, `getColorAlpha()` из `../../utils/colors`.
  **Ноль литеральных hex** (`#rrggbb`). Ноль `bg-bg-base`/`bg-bg-surface` внутри контента.
- C4. Фон айтема — `var(--item-bg)`; фон слайда — `var(--surface-bg)` (если нужен).

## D. Движение (см. `docs/MOTION_STANDARD.md`)

- D1. Время — только `inject('relativeTime', ref(0))`.
- D2. Появление: `relativeTime >= (item.start_time ?? i * motion.stagger_ms)`.
- D3. Анимируются только `transform`/`opacity`.
- D4. Запрещено: `requestAnimationFrame`, `infinite`, `<animate>`, `background-position`,
  `width/height/left/top` в анимации.
- D5. Длительности — из `motion.value` (`appear_ms`, `stagger_ms`, `count_ms`), не хардкод.

## E. Вёрстка и адаптив

- E1. Корень: `w-full max-w-6xl mx-auto h-full min-h-0 overflow-hidden flex flex-col`.
- E2. Основной контент: `flex-1 min-h-0 overflow-hidden` (не `min-h-[320px]` без ограничения).
- E3. Полноразмерный SVG — `class="absolute inset-0 w-full h-full"` (никогда просто `w-full h-full`).
- E4. Не задавать высоту flex-ребёнка через `aspect-ratio` (раздувает кадр).
- E5. Встроенный примитив — обернуть в `flex-1 min-h-0 overflow-hidden` и при необходимости
  сузить его внутренний `min-h` таргетным селектором `[&_.min-h-\[Npx\]]:min-h-[Mpx]`.
  **Запрещён** `[&_*]:!min-h-0` (ломает бары/сегменты).
- E6. Мобильно: стек (`grid-cols-1`/`flex-col`); широкий контент — внутри `overflow-x-auto`.
- E7. Компонент не должен выходить за кадр ни на 1920×1080, ни на 450×800.

## F. Метаданные `scripts/_orthodox_meta/<Slug>.json`

```json
{
  "slug": "VerseFocus",
  "title": "Фокус на стихе",
  "description": "Одна фраза, что делает.",
  "manifest": "Подходит: ... Не использовать: ...",
  "categories": ["stats"],
  "required": ["verse"],
  "payload": { "variant": "diademas", "...": "..." }
}
```

- F1. `categories` — из `backend|sales|ui|stats`.
- F2. `payload` — полноценный `default_payload` (production-quality).
- F3. `required` — список обязательных top-level полей.

## G. Контент

- G1. Русский текст; `€` при деньгах; **ноль эмодзи**.
- G2. Иконки — `lucide:*`/`heroicons:*` через `@iconify/vue`.
- G3. Ссылки на Писание/источник — там, где есть цитата/тезис.
- G4. Массивы: 3–6 элементов, `start_time` монотонно, шаг ≥ 1000 мс.
- G5. Уважительная подача: без клип-арта, карикатур, «иконостаса из карточек».

## H. Композиция

- H1. Если в roadmap указано `→ X` — импортировать `./X.vue` и передать props,
  а не дублировать внутренности графика.
- H2. Перед композицией прочитать файл примитива и свериться с его пропсами.

## I. Проверка (обязательна перед сдачей)

- I1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:5174/src/components/ui/<Slug>.vue"` == 200.
- I2. `grep -n "#[0-9a-fA-F]\{3,6\}" <file>` — пусто.
- I3. `grep -n "\[&_\*\]" <file>` — пусто.
- I4. `grep -nE "requestAnimationFrame|infinite|<animate" <file>` — пусто.
- I5. Перечитать файл целиком: теги сбалансированы, нет мёртвого кода.
