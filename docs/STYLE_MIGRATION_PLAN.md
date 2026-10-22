# План миграции на новый формат стилей

> Зафиксировано 2026-09-16. Цель — не терять контекст между итерациями. Итерация 1 завершена, 2 часа ушли на правки контраста/таймлайна. Шахматка отменена.

## Цель

Перейти на новый формат `style_variants` + `design_tokens`:
- `item.bg.type` = `solid|gradient|blur|transparent` + `variant` в payload
- Токены — единый мерж `global (80) → project` в БД, фронт тянет via `/projects/{id}/tokens`
- `project_colors` удалена, чтение через `/projects/{id}/tokens` и `/presentations/{id}/tokens`

## Новые переменные (все добавлены, пер-темно)

| Группа | Ключи | Где |
|--------|-------|-----|
| role aliases | `color-danger`, `color-danger-soft/strong`, `color-info`, `color-info-soft/strong` | `GLOBAL_TOKENS`, `HISTORICAL_TOKENS`, `DEREVNYA_TOKENS` |
| item шахматка | `item-accent-1..4` | 3 палитры |
| slide фоны | `slide-bg-1..4` | 3 палитры (IT2B: `#0B1322/#0F1D33/#121E32/#1C2A42` — `slide-bg-3` изменён с `#152033` чтоб не совпадал с `bg-surface`) |
| surfaces/borders | `bg-base/surface/surface-2/hover/overlay`, `border-main/strong/accent` | уже в `GLOBAL_TOKENS` |
| text/roles | `text-primary/secondary/muted`, `color-primary/secondary/accent...` + soft/strong | уже |
| charts/effects | `chart-1..6/grid/axis`, `gradient-*/glow-*/glass-bg/pattern-bg` | уже |
| fonts | `font-sans/heading/mono`, `font_link` | уже |

Итого: `global 80`, `it2b 1` override (`bg-image`), `history 80`, `derevnya 81` (`docs/DATABASE.md:174`).

## Итерации

### Итерация 1 — DONE (закоммитить отдельно нельзя, в `git diff` 15 файлов)

- `core/src/components/ui/ColorLibraryModal.vue:2,89,114,136,250` — отвязка от `it2b`: `props: projectId/presentationId`, `categoryForKey()`, `resolveProjectId()` (presentation → `fetchPresentationTokens` → URL `/p/{id}` → fallback `it2b`), `handleSave` → `upsertProjectTokens(pid)`, `loadColors` из `presentationId`, категории `surface/text/role/item-accent/slide-bg/chart/effect`
- `core/src/components/ui/SlideEditorModal.vue:5` — прокидывает `presentation-id` в `ColorLibraryModal`
- `scripts/seed_components.py:280-757` — ~15 хардкод hex `#F97316/#38BDF8/#10B981/#EF4444/#F59E0B/#EC4899` → `var(--color-*)` / `var(--item-accent-*)` шахматом
- `core/src/style.css:91-104` — fallback `*-rgb` для `color-danger/info`, `item-accent-1..4`, `slide-bg-1..4` (10 строк, фиксит `rgb(/0.1)` на первом кадре)
- `scripts/seed_tokens.py:41` — `GLOBAL_TOKENS` 80, `slide-bg-3` `#121E32`
- `docs/DATABASE.md:174` — 80/1/80/81, пояснено `global===IT2B`
- `AGENTS.md:524` — **ОТМЕНЕНО**: было `Фон слайда шахматит slide-bg-{(index%4)+1}` `Slide.vue:9`, откачено на `Фон слайда всегда растянут на весь кадр — жмётся только .slides-safebox` (фикс ниже)

### Итерация 1b — правки контраста/таймлайна (2 часа, в том же diff)

- `core/src/components/engine/Slide.vue:9` — **откачено**: `slideBgVar/slideBgStyle` шахматка → `var(--surface-bg)` (шахматка криво смотрелась, фоны восстановлены)
- `core/src/components/engine/DirectorDebugPanel.vue` + `AudioTimeline.vue` — убраны `isFullscreen` ternaries `bg-black/30→bg-white`, `h-6→h-[48px]` — таймлайн одинаковый в fullscreen
- `scripts/seed_variants.py:26-45` — `tech` `item.bg blur 0.45 → solid bg-surface`, `border color border-main`, `item_primary solid bg-surface`, + `components.TerminalMockup/CodeExplain/BrowserMockup → bg-surface-hover` для контраста фуллскринов
- `core/src/components/ui/TerminalMockup.vue:174,178` — `bg-bg-base→bg-[var(--item-bg)]`
- `core/src/components/ui/BrowserMockup.vue:129,150,177` — `bg-bg-base/surface→bg-[var(--item-bg)]`
- `core/src/components/ui/ReceiptCard.vue:1-3` — убран `useVariant`/`variant` prop, всегда `bg-[#F8FAFC]` статично
- `core/src/components/ui/InfographicCards.vue`, `PremiumChecklist.vue` — тинты `getColorAlpha(...,0.12/0.10)` — аппрувнуто
- `AGENTS.md:335,524` + `docs/DATABASE.md:174` — тайминги и токены уже обновлены

### Итерация 2 — DONE (2026-09-17)

1. ✅ Откачен `AGENTS.md:524` шахматка → `Фон слайда всегда растянут...` (синхрон с `Slide.vue:9`)
2. ✅ Добиты `seed_components.py` hex: `ProductCard accent_color #38BDF8/#EC4899/#10B981 → var(--item-accent-1/4/2)`, `border_color rgba(56,189,248,0.3) → rgb(var(--item-accent-1-rgb) / 0.3)` (паттерн совпадает с дефолтами `ProductCard.vue:34-35`). Логотипы `#42b883/#009688/#336791` оставлены.
3. ✅ Пересеяно: `seed_tokens (global 80/history 80/derevnya 81) → seed_variants (5) → seed_components (30) → generate_schemas (30) → generate_examples (29 из /p/4 + 1) → seed_manifests (30/30)`
4. ✅ Верификация: `GET /presentations/11/tokens` → `slide-bg` бумажные `#FBF9F6/#F3F0EA/#EAE5DE/#FFFFFF`, `danger #873230/info #3E5C76` пер-темно; `Slide.vue` 200, `surface-bg` 1, `slide-bg` 0; `POST /components/ProductCard/validate` → `{"valid":true}`

## Команды

```bash
# Внутри backend
docker compose exec backend python scripts/seed_tokens.py
docker compose exec backend python scripts/seed_variants.py
docker compose exec backend python scripts/seed_components.py
docker compose exec backend python scripts/generate_schemas.py
docker compose exec backend python scripts/generate_examples.py
docker compose exec backend python scripts/seed_manifests.py

# Проверка
curl -s http://localhost:8001/presentations/11/tokens | python -m json.tool | grep -A2 slide-bg
curl -s http://localhost:5174/src/components/engine/Slide.vue -o /tmp/s.js -w "%{http_code}\n" && grep -c "surface-bg" /tmp/s.js
curl -s http://localhost:8001/components/ | python -m json.tool | grep -A2 '"slug": "ReceiptCard"'
```

### Итерация 3 — DONE (2026-09-17): защита дефолтов + `var()` вставка

Проблема: свои цвета падали в общую кучу токенов (не удалить), выбор из библиотеки вставлял резолвленный hex (правки проекта не распространялись).

1. ✅ `backend/models.py:46` — `DesignToken.is_custom: Boolean = False`. Миграция без alembic: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` в `seed_tokens.py run()`
2. ✅ `backend/routers/projects.py:100` — мерж отдаёт `"custom": bool`; `upsert` помечает новые `is_custom=True`; новый `DELETE /{project_id}/tokens/{key}` — 404 нет ключа, 403 дефолт
3. ✅ `scripts/seed_tokens.py` — `_seed_tokens` ставит `is_custom=False` (сид владеет ключом); `1312` (создан юзером ранее) вручную → `True`
4. ✅ `core/src/services/api.js` — `deleteProjectToken()`, `fetchProjectColors` прокидывает `custom`
5. ✅ `ColorLibraryModal.vue` — проп `adminMode`; вкладка «Мои»; бейджи lock/`мой`; edit дефолтов только в `adminMode` (+имя зафиксировано); delete только custom (с обработкой rename-orphan); `selectColor` эмитит `` var(--${name}) `` вместо значения; подпись под цветом — `var(--name)`
6. ✅ `core/src/views/ProjectView.vue` — кнопка «Цвета проекта» → модалка с `project-id` + `admin-mode` (настройки темы; select там только закрывает)
7. ✅ Верификация: `DELETE bg-base → 403`, `PUT tmp → custom:True`, `DELETE tmp → 200` + gone; `1312 → custom:True`; фронт 200 без ошибок; `color: var()` валиден (`validation.py:47-50`)
8. ✅ `docs/DATABASE.md:168-176` — колонка `is_custom`, `var()`-вставка, DELETE-правило

### Итерация 4 — DONE (2026-09-17): откат тинта фона айтемов

Тестовый тинт (`getColorAlpha(item.color, 0.10/0.12)`) красил весь фон карточек в акцентный цвет. Откачено:
- `PremiumChecklist.vue:78` → `background: 'var(--item-bg)'` (остались: левый край-маркер `:91`, чип иконки `:97-99`)
- `InfographicCards.vue:73` → `background: 'var(--item-bg)'` (остались: `borderTopColor`, trend-пилюля, watermark)
- Тинт был только в коде `.vue` — в БД откатывать нечего (payload'ы содержат `color` только для иконок, bg-полей нет)
- `AGENTS.md:195` — правило: `color` = только иконка/маркер/текст, фон всегда `var(--item-bg)`
- Фронт: оба компонента 200, ошибок нет

### Итерация 5 — DONE (2026-09-17): /p/13 деревня — белый фон перекрывал иллюстрацию

Симптом: слайды derevnya сплошные белые, нет `bg-image` градиента и `bg-decorations` леса.
Корень: `SlidePresentation.vue:327-346` — иллюстрация/градиент/шум лежат на контейнере и слоях `z-0` ПОД слайдом; `Slide.vue:9` красит слайд в `var(--surface-bg)`. В БД `derevnya.surface` оказался `solid bg-base` (белый непрозрачный) — наш пересев `seed_variants.py` (итерация 2) перезаписал конфиг файлом, стерев рабочее состояние.
Фикс в источнике правды: `seed_variants.py` derevnya `surface.bg → transparent` (+комментарий почему) → пересев. `useVariant.js:53-55` даёт `background: transparent`, подложка видна. tech/classic/industrial/educational не тронуты.
Проверено: `GET /variants/derevnya → surface.transparent`, токены `bg-image`/`bg-decorations` в `/presentations/13/tokens` на месте. Нужен reload страницы (варианты кэшируются фронтом однократно).

### Итерация 6 — DONE (2026-09-17): лес обрезан справа (половина ширины)

Симптом: после прозрачного surface лес виден, но занимает левую ~половину с вертикальным срезом.
Корень — НЕ наши правки: `gen_forest_bg.py` в коммите `9333d81` сменил `viewBox='0 170 1440 330'` (full-bleed) на `viewBox='0 0 1440 500'` + `<g transform='translate(0,250) scale(0.5)'>` (чтобы не резать кроны) — это сжало весь лес в левую половину канвы. Раньше дефект был скрыт белой подложкой, наш transparent его exposed.
Фикс: убран scale, `viewBox='0 40 1440 460'` — вся ширина + запас сверху (мин. крона y=110). Пересев токенов (81 derevnya), в URI scale отсутствует. Слой: `100% auto, bottom center` — фулл-видс, пропорциональная высота (~55% кадра при 1920).

### Итерация 7 — DONE (2026-09-17): аудит всех компонентов под новые типы токенов

Аудит 50 `.vue` (slides + ui): обёртки `*Slide` вариант форвардят (`:variant`), hex остался только в хроме редактора (`#A78BFA` — легитимно, хром фиксированный) и шимах совместимости. Найдено и fixed 5 мест:
1. `Ecosystem.vue:40,47` — БАГ: `getColorAlpha(`var(--${node.color}, ${node.color})`)` ломал извлечение `--X-rgb` (декларация дропалась, бордеры/тени нод битые) → `getColorAlpha(node.color)` + `getHexColor(node.color)` (+импорт)
2. `WindowHeader.vue:15` — `var(--bg-surface)` → `var(--item-bg, var(--bg-surface))` (наследует item-bg окон)
3. `CodeExplain.vue:194` — тёмная зона `bg-bg-surface` → `bg-[var(--item-bg)]` (светлая `#FEFEFE` оставлена)
4. `BrowserMockup.vue:153,160,165` — loading/content/image `bg-bg-surface` → `bg-[var(--item-bg)]`
5. `TerminalMockup.vue:206,210` — скроллбар `var(--bg-base)` → `var(--item-bg, var(--bg-base))`
Проверено: 5 файлов 200, ошибок нет; `validate` — `EcosystemSlide/TerminalMockup/BrowserMockup/CodeExplain → valid:true`. `AGENTS.md:637` — контракт резолва + правило фонов.

## Риски

- Шахматка отменена сознательно — не возвращать без перекалибровки. `slide-bg-*` токены остаются (для будущих экспериментов), но `Slide.vue` их не использует.
- `Terminal/Code/Browser` фуллскрины должны контрастировать с `bg-base #0B1322` через `bg-surface-hover #1F2D44` (override в `seed_variants`), а не через `bg-surface #152033` (сливается).
- `ReceiptCard` — единственный компонент с фиксированным белым, без `useVariant`.
