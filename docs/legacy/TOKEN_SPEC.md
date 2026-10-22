# TOKEN_SPEC.md — Семантическая дизайн-система токенов

Спецификация для рефакторинга цветов: уходим от `brand-blue` (привязка к конкретному цвету)
к **семантическим ролям**. Компоненты используют роли, а тема подставляет значения.

> **Принцип:** имена токенов = унификация; значения токенов = характер темы.
> Один компонент пишет `color-accent` — в IT2B это электрик-оранж, в исторической — сургучный вермильон.

---

## 1. Слои токенов

### 1.1 Поверхности (`bg-*`)
| Токен | Роль |
|---|---|
| `bg-base` | фон слайда/экрана |
| `bg-surface` | основные карточки/окна/плашки |
| `bg-surface-2` | вложенные поверхности (поля, внутренние карточки) |
| `bg-hover` | фон при hover/активном состоянии |
| `bg-overlay` | затемняющий слой поверх медиа (scrim) |
| `bg-overlay-light` | осветляющий слой (для светлых тем / светлых акцентов) |

### 1.2 Границы (`border-*`)
| Токен | Роль |
|---|---|
| `border-main` | обычные границы, разделители, обводки таблиц |
| `border-strong` | акцентные границы, шапки таблиц |
| `border-accent` | фокус, выделение, активный элемент |

### 1.3 Текст (`text-*`)
| Токен | Роль |
|---|---|
| `text-primary` | основной читаемый текст |
| `text-secondary` | подзаголовки, второстепенный текст |
| `text-muted` | плейсхолдеры, мелкие подписи |
| `text-on-color` | текст поверх цветных плашек (кнопки/бейджи) — всегда контрастный |

### 1.4 Семантические роли (`color-*`)
| Токен | Роль | Пример использования |
|---|---|---|
| `color-primary` | главный цвет | первичная кнопка, сообщение пользователя, главная нода |
| `color-primary-soft` | мягкий тинт primary | фон бейджа/иконки-чипа |
| `color-secondary` | вторичный | поддерживающий акцент, светлый оттенок |
| `color-secondary-soft` | тинт secondary | фон второстепенных элементов |
| `color-accent` | яркий акцент | пик на графике, бейдж «Новинка», CTA |
| `color-accent-soft` | тинт accent | фон акцентной плашки |
| `color-accent-2` | второй акцент | второй график/нода/серия данных |
| `color-accent-2-soft` | тинт accent-2 | фон |
| `color-success` | успех/рост | статус «Выполнено», позитивный тренд |
| `color-success-soft` | тинт success | фон |
| `color-warning` | предупреждение | ожидание, «внимание» |
| `color-warning-soft` | тинт warning | фон |
| `color-error` | ошибка/падение | падение тренда, «нет» |
| `color-error-soft` | тинт error | фон |

### 1.5 Данные/инфографика (`chart-*`)
| Токен | Роль |
|---|---|
| `chart-1` … `chart-6` | гармоничная палитра для диаграмм/графиков/воронок/bento (циклично) |
| `chart-grid` | линии сетки графиков |
| `chart-axis` | оси/подписи осей |

### 1.6 Эффекты
| Токен | Роль |
|---|---|
| `gradient-primary` | градиент главного действия/CTA |
| `gradient-accent` | градиент акцента |
| `gradient-hero` | фон hero-секции/слайда |
| `gradient-surface` | лёгкий отлив карточек/панелей |
| `gradient-text` | градиент для заголовков (`bg-clip-text`) |
| `gradient-chart` | заливка площади графика (area) |
| `glow-primary` | свечение вокруг главного элемента (box-shadow) |
| `glow-accent` | свечение вокруг акцента (box-shadow) |
| `shadow-color` | цвет теней темы (тёплый для бумаги, чёрный для тёмной) |
| `glass-bg` | фон стеклянных панелей (glassmorphism) |
| `pattern-bg` | текстура фона слайда (SVG data-URI: зерно/сетка) |

### 1.7 Состояния (`color-*-strong`)
Более насыщенный/контрастный оттенок роли — для hover/active и акцентных плашек.
На тёмной теме «strong» светлее, на светлой — темнее (задаётся значением темы).

| Токен |
|---|
| `color-primary-strong`, `color-secondary-strong`, `color-accent-strong`, `color-accent-2-strong`, `color-success-strong`, `color-warning-strong`, `color-error-strong` |

### 1.8 Текст на цветных поверхностях
| Токен | Роль |
|---|---|
| `text-on-color` | общий контрастный текст на цветных плашках |
| `text-on-primary` | текст на `color-primary` (кнопки/бейджи) |
| `text-on-accent` | текст на `color-accent` (в т.ч. светлый акцент → тёмный текст) |

> Шрифты (`font-sans`/`font-heading`/`font-mono`/`font_link`) — без изменений.

### 1.9 Быстрые дефолты для ИИ и человека (шахматка + бейджи)

Чтобы не выбирать из 30 токенов и не тянуть случайный hex, держи короткий набор, который **всегда есть в каждой палитре** и гармоничен с ней:

| Токен | Роль | Как использовать |
|---|---|---|
| `color-danger` / `color-danger-soft` / `color-danger-strong` | алиас `color-error` — читаемее для ИИ (`danger` vs `error`) | бейдж ошибки: `bg=color-danger-soft`, `text/border=color-danger` |
| `color-info` / `color-info-soft` / `color-info-strong` | алиас `color-secondary` | бейдж инфо |
| `item-accent-1` .. `item-accent-4` | 4 гармоничных акцента для шахматки айтемов (циклично `{(i%4)+1}`) | `items[i].color = var(--item-accent-{(i%4)+1})` — `InfographicCards`, `PremiumChecklist`, ноды `ArchitectureDiagram`, бorders карточек |

Значения пер-темно (см. `seed_tokens.py`): IT2B `1:#38BDF8 2:#10B981 3:#F59E0B 4:#8B5CF6`; history `1:#6B2927 2:#244B3B 3:#B89254 4:#3B5C7D`; derevnya `1:#D87B22 2:#4A6038 3:#E89538 4:#5E724F`. Меняешь 4 строки в `seed_tokens.py` — шахматка всего проекта перекрасилась.

| `slide-bg-1` .. `slide-bg-4` | ЗАРЕЗЕРВИРОВАНЫ (шахматка слайдов отменена — `Slide.vue` всегда `var(--surface-bg)`; токены лежат на будущее) | пер-темно: IT2B `#0B1322/#0F1D33/#121E32/#1C2A42` (`slide-bg-3` ≠ `bg-surface`, чтобы фуллскрины не сливались), history `#FBF9F6/#F3F0EA/#EAE5DE/#FFFFFF`, derevnya `#FFFFFF/#FFF8EB/#F5E9D2/#EAE5DE` |

### 1.10 Типографическая шкала (`type-*`, P4)

Контролируемая шкала кеглей — единственное исключение из «размеры не токены»:

| Токен | IT2B | history | derevnya | Где |
|---|---|---|---|---|
| `type-display` | `3.5rem` | `4rem` | `3.25rem` | hero-заголовки (компоненты, опционально) |
| `type-h1` | `2.25rem` | `2.75rem` | `2.5rem` | `Slide.vue` тайтл (`var(--type-h1, 2.25rem)`) |
| `type-h2` | `1.75rem` | `2rem` | `1.85rem` | подзаголовки секций (опционально) |
| `type-body` | `1.125rem` | `1.15rem` | `1.125rem` | `Slide.vue` subtitle (`var(--type-body, 1.125rem)`) |
| `type-caption` | `0.8rem` | `0.85rem` | `0.8rem` | подписи (опционально) |

Правило: компонент читает шкалу с CSS-fallback на текущий класс; tech-значения равны текущим — tech попиксельно не меняется.

### 1.11 Смежные оси (не токены, но рядом)

- **Motion** (`style_variants.config.motion`, P3): `{appear_ms: 500, stagger_ms: 1000, count_ms: 2000}`.
  `stagger_ms` связан с §8.3 AGENTS (шаг айтемов). Компонент читает через `useVariant().motion`.
- **Пресеты** (`style_presets`, P2): вектор = палитра-проект + вариант + `rules {max_accents, title_em}`.
  `it2b-tech` / `history-classic` / `derevnya-eco`. С `style_lock=true` выход за вектор = 422.

---

## 2. Значения: IT2B (техно, тёмная, сочная)

```json
{
  "bg-base": "#0B1322",
  "bg-surface": "#152033",
  "bg-surface-2": "#1C2A42",
  "bg-hover": "#1F2D44",
  "bg-overlay": "rgba(6, 11, 22, 0.72)",

  "border-main": "#2A3A55",
  "border-strong": "#3D5175",
  "border-accent": "#38BDF8",

  "text-primary": "#F8FAFC",
  "text-secondary": "#A6B4C8",
  "text-muted": "#6C7C96",
  "text-on-color": "#FFFFFF",

  "color-primary": "#2563EB",
  "color-primary-soft": "#17284A",
  "color-secondary": "#38BDF8",
  "color-secondary-soft": "#0E2E3A",
  "color-accent": "#F97316",
  "color-accent-soft": "#3A2410",
  "color-accent-2": "#8B5CF6",
  "color-accent-2-soft": "#241E4A",
  "color-success": "#10B981",
  "color-success-soft": "#0E2E26",
  "color-warning": "#F59E0B",
  "color-warning-soft": "#3A2C0E",
  "color-error": "#EF4444",
  "color-error-soft": "#3A1717",

  "chart-1": "#2563EB",
  "chart-2": "#38BDF8",
  "chart-3": "#8B5CF6",
  "chart-4": "#F472B6",
  "chart-5": "#F97316",
  "chart-6": "#10B981",
  "chart-grid": "rgba(148, 163, 184, 0.12)",
  "chart-axis": "#64748B",

  "gradient-primary": "linear-gradient(135deg, #3B82F6 0%, #22D3EE 100%)",
  "gradient-accent": "linear-gradient(135deg, #F97316 0%, #F43F5E 100%)",
  "gradient-hero": "linear-gradient(135deg, #0B1322 0%, #17284A 55%, #1C2A42 100%)",
  "gradient-surface": "linear-gradient(160deg, #18243A 0%, #131E30 100%)",
  "gradient-text": "linear-gradient(90deg, #38BDF8 0%, #8B5CF6 100%)",
  "gradient-chart": "linear-gradient(180deg, rgba(37,99,235,0.5) 0%, rgba(37,99,235,0) 100%)",
  "glow-primary": "0 0 30px rgba(37, 99, 235, 0.35)",
  "glow-accent": "0 0 30px rgba(249, 115, 22, 0.35)",
  "shadow-color": "rgba(0, 0, 0, 0.45)",
  "glass-bg": "rgba(21, 32, 51, 0.55)",
  "pattern-bg": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'%3E%3Ccircle cx='1' cy='1' r='1' fill='%2394a3b8' fill-opacity='0.06'/%3E%3C/svg%3E\")",
  "bg-overlay-light": "rgba(255, 255, 255, 0.55)",

  "color-primary-strong": "#60A5FA",
  "color-secondary-strong": "#7DD3FC",
  "color-accent-strong": "#FB923C",
  "color-accent-2-strong": "#A78BFA",
  "color-success-strong": "#34D399",
  "color-warning-strong": "#FBBF24",
  "color-error-strong": "#F87171",
  "text-on-primary": "#FFFFFF",
  "text-on-accent": "#FFFFFF"
}
```

---

## 3. Значения: Историческая (иллюминированная рукопись, светлая, СОЧНАЯ)

Не «мрачный музей», а **светлый пергамент + «драгоценные» акценты**: лазурь, вердигри,
киноварь, золотой лист. Базис светлый и тёплый, акценты — насыщенные и «светящиеся».

```json
{
  "bg-base": "#FAF4E4",
  "bg-surface": "#F3E9D2",
  "bg-surface-2": "#EADFC4",
  "bg-hover": "#F0E6CE",
  "bg-overlay": "rgba(43, 33, 24, 0.5)",

  "border-main": "#DCC9A2",
  "border-strong": "#C2A878",
  "border-accent": "#C8462E",

  "text-primary": "#34291C",
  "text-secondary": "#6B573C",
  "text-muted": "#9C8460",
  "text-on-color": "#FBF6E9",

  "color-primary": "#244E7A",
  "color-primary-soft": "#DCE8F3",
  "color-secondary": "#3E7C6A",
  "color-secondary-soft": "#D6E8E1",
  "color-accent": "#C8462E",
  "color-accent-soft": "#F5DAD1",
  "color-accent-2": "#D9A93A",
  "color-accent-2-soft": "#F6E7B8",
  "color-success": "#5E8A3E",
  "color-success-soft": "#E4EBCE",
  "color-warning": "#D9A93A",
  "color-warning-soft": "#F6E7B8",
  "color-error": "#A83232",
  "color-error-soft": "#F2D4D4",

  "chart-1": "#C8462E",
  "chart-2": "#244E7A",
  "chart-3": "#3E7C6A",
  "chart-4": "#D9A93A",
  "chart-5": "#B5703C",
  "chart-6": "#A83232",
  "chart-grid": "rgba(90, 74, 56, 0.15)",
  "chart-axis": "#9C8460",

  "gradient-primary": "linear-gradient(135deg, #244E7A 0%, #3E7C6A 100%)",
  "gradient-accent": "linear-gradient(135deg, #C8462E 0%, #D9A93A 55%, #F0D06A 100%)",
  "gradient-hero": "radial-gradient(120% 100% at 50% 20%, #FDF8EC 0%, #F3E9D2 60%, #E4D5B4 100%)",
  "gradient-surface": "linear-gradient(160deg, #F7EEDB 0%, #EFE4C8 100%)",
  "gradient-text": "linear-gradient(90deg, #C8462E 0%, #D9A93A 100%)",
  "gradient-chart": "linear-gradient(180deg, rgba(200,70,46,0.4) 0%, rgba(200,70,46,0) 100%)",
  "glow-primary": "0 0 28px rgba(36, 78, 122, 0.28)",
  "glow-accent": "0 0 28px rgba(200, 70, 46, 0.28)",
  "shadow-color": "rgba(74, 48, 22, 0.18)",
  "glass-bg": "rgba(243, 233, 210, 0.62)",
  "pattern-bg": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E\")",
  "bg-overlay-light": "rgba(255, 255, 255, 0.55)",

  "color-primary-strong": "#1B3D62",
  "color-secondary-strong": "#2F6355",
  "color-accent-strong": "#A83A24",
  "color-accent-2-strong": "#B88C28",
  "color-success-strong": "#4A6F30",
  "color-warning-strong": "#B88C28",
  "color-error-strong": "#8A2828",
  "text-on-primary": "#FBF6E9",
  "text-on-accent": "#FFF8EE"
}
```

---

## 4. Маппинг старых токенов → новых

| Было | Стало |
|---|---|
| `brand-blue` | `color-primary` |
| `brand-light-blue` | `color-secondary` |
| `brand-green` | `color-success` |
| `brand-amber` | `color-warning` |
| `brand-orange` | `color-accent` |
| `brand-accent` | `color-accent` |
| `bg-surface-hover` | `bg-hover` |
| `bg-base`, `bg-surface`, `text-*`, `font-*` | без изменений |

Tailwind-классы (примеры): `bg-brand-blue`→`bg-color-primary`, `text-brand-lightBlue`→`text-color-secondary`,
`border-brand-green/30`→`border-color-success/30`, `from-brand-orange`→`from-color-accent`.

---

## 5. Tailwind config

```js
colors: {
  bg: { base, surface, 'surface-2', hover, 'overlay-light' },
  border: { main, strong, accent },
  text: { primary, secondary, muted, 'on-color', 'on-primary', 'on-accent' },
  color: {
    primary, secondary, accent, 'accent-2', success, warning, error,
    // + -soft и -strong для каждой роли
    'primary-soft', 'primary-strong', ...,
  },
  chart: { 1..6, grid, axis },
}
```
Эффекты (`gradient-*`, `glow-*`, `shadow-color`, `pattern-bg`, `glass-bg`, `bg-overlay`) — не цвета,
используются напрямую как `var(--gradient-hero)`, `box-shadow: var(--glow-accent)` и т.п.
Каждый hex-токен автоматически даёт `--{key}-rgb` (см. `applyTheme`), поэтому opacity-модификаторы
(`bg-color-primary/10`) работают.

---

## 6. Безопасная миграция (важно — иначе будут мины)

1. **Добавить новые токены** в `seed_tokens.py` (global + historical), НЕ удаляя старые.
2. **Оставить старые `brand-*` как алиасы** на переходный период:
   - в `tailwind.config.js` временно смапить `brand.blue → --color-primary-rgb` и т.д.;
   - для «сырых» `var(--brand-*)` в компонентах/данных — заменить на `var(--color-*)`.
3. **Мигрировать данные**, а не только код:
   - payload'ы слайдов: `base_color`/`peak_color`/`color`/`field_color`/`btn_color` (там `var(--brand-*)`);
   - `style_variants.config` (там `line.color = brand-light-blue` → `color-secondary`);
   - `project_colors`/`design_tokens` в БД.
4. **Компоненты:** заменить классы/`var()` на новые. Использовать палитру `chart-1..6` в
   диаграммах/шкалах/водопаде/воронке (циклично) вместо хардкода зелёных/янтарных.
5. **Удалить алиасы** только после полной миграции и проверки.

---

## 7. Чек-лист проверки (после рефакторинга)

- [ ] Все `.vue` компилируются (нет 500).
- [ ] Нет `var(--...)`, которых никто не определяет (как было с `--item-border`).
- [ ] Нет консольных ошибок на `/p/4` (все компоненты), `/p/10` (IT2B), `/p/11` (историческая).
- [ ] Контраст текста ≥ 2.0 на обеих темах (особенно светлой).
- [ ] `bg-color-primary`, `text-color-accent`, `bg-chart-1` и т.п. реально меняются при смене темы.
- [ ] Диаграммы/графики используют `chart-*` (не тускло, не сливаются с фоном).

---

## 8. Идеи для «сочности» (сверх цветов)

- **Текстуры** (`pattern-paper`, `pattern-grid`) — фон слайда с лёгкой текстурой.
- **Свечения** (`glow-accent`) — для диаграмм/графиков.
- **Семантика нод** диаграмм через роли (`color-primary`/`color-accent-2`/`color-success`).
- **`-soft` тинты** вместо повсеместных `bg-brand-*/10`.
