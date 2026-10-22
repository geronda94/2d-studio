# План: гибкие стили + премиальный вид + защита от поломок ИИ

> 2026-09-17. Цель: презентации гибкие (пресеты/темы/моушн), выглядят премиально
> (консистентный моушн, типографика, свет/стекло), ИИ не ломает (линт + локи + сиды не затирают).
> Порядок: P0 → P1 → P2 → P3 → P4 → P5.

## P0. Защита сидов — DONE (2026-09-17)

Проблема (кусала дважды: `derevnya.surface`, тинт): сиды перезаписывали БД, стирая доводку и кастомы.

Конвенция (асимметричная, осознанно):
- **Токены** (значения крутят в UI): по умолчанию только досеив отсутствующих;
  значения managed — только с `--force`; кастомы — никогда.
- **Варианты/компоненты** (дизайн из файлов): по умолчанию обновляют managed из файла,
  кастомы — skip (варианты — только с `--force`).

Что сделано:
1. `models.py`: `is_custom` у `StyleVariant` + `Component` (у токенов был с итерации 3).
   Миграции без alembic: `ALTER ... ADD COLUMN IF NOT EXISTS` внутри сидов.
2. `routers/components.py`: `POST /` ставит `is_custom=True`.
3. `seed_tokens.py`: `--force`, skip `is_custom`, иначе create-missing-only.
4. `seed_variants.py`: `--force`, skip custom-конфигов.
5. `seed_components.py`: **DROP таблиц удалён** (он сносил `payload_schema/example/manifest`
   и кастомы); upsert по slug + `get_or_create` типов/категорий; убран задвоенный блок категорий.
6. Приёмка (фикстуры `p0-test-*`, затем удалены): без флагов — кастомы живы, sentinel
   `#SENTINEL` на месте, schema/example целы; с `--force` — managed из файлов, кастомы всё равно живы.

## P1. Валидатор вкуса — style-lint — DONE (2026-09-17)

Реализовано (`backend/style_lint.py` + wiring, warnings не блокируют):
1. `no-hex` — hex в поле типа `color` (бренд-hex логотипов `#42b883/#009688/#336791` allowlist; `code`/`html` не трогаем).
2. `accent-budget` — >4 distinct (`color`/`*_color` кроме `border_*`/`btn_*`/`bg_*`, `var(--x)`==`x`).
3. `density` — 0<gap<800мс (`§8.3`); gap 0 = синхронность; `InteractiveArchitecture` skip.
4. `low-contrast` — только save (нужна тема): `text-primary` vs surface (< 4.5; transparent → `bg-base`).
5. `validate?lint=true` → warnings в ответе; `POST/PUT slides` считают линт всегда, `warnings`
   в ответе (`schemas.Slide` + поле с дефолтом, pydantic v2 — GET не сломан).
6. Каталог вычищен: нормалайзер плотности в `seed_components.py` (push-forward ≥800,
   `InteractiveArchitecture` skip) → 30 default_payloads = 0 warnings.
7. UI: `SlideEditorModal` жёлтая dismissible-плашка + проп `saveWarnings`; `MainPresentation`
   собирает warnings со всех PUT (дедуп), модалка не закрывается при warnings, `handleCloseEditor` чистит.
8. Приёмка: endpoint valid+warning; PUT 200+warnings; restore PUT вернул слайд 157 p4;
   invalid save → 422; contrast unit (dark ok / low 1.2 warn / transparent ok);
   variant enum полный (5/5); `test_422.py` зелёный (созданный им слайд 1885 удалён из p13);
   фронт 200 без ошибок; `GET /presentations/4` — 30 слайдов (схема не сломана).
9. Инциденты по ходу: `style_lint.py` пропадал с диска (переписан полностью, проверен `ls`);
   `schemas.py` NameError (`ValidationError` ниже `Slide` — классы валидации подняты выше);
   crash-loop бэкенда (живой маунт, поднялся сам после фикса).

## P2. Вектор стилей: пресеты + локи — DONE (2026-09-17, M)

Реализовано:
1. `models.py`: `StylePreset` (slug/title/palette/variant/rules/is_custom) +
   `Presentation.style_preset/style_lock` (миграция ALTER в `seed_presets.py`).
2. `style_lint.lint_preset` → ERRORS: `wrong-variant` (effective vs preset.variant),
   `accent-budget` (rules.max_accents), `title-em` (заголовок без `<em>`).
3. Enforcement на save (`_enforce_preset_lock` в create/update): rules = 
   `{"variant": preset.variant, **preset.rules}` → 422 `Слайд вне вектора пресета`.
4. API: `GET/POST /presets/`, `DELETE /presets/{slug}` (только custom, иначе 403),
   `GET/PUT /presentations/{id}/style` (400 на битые ссылки); `POST /variants/` ставит `is_custom=True`.
5. `seed_presets.py`: `it2b-tech/history-classic/derevnya-eco` (palette+variant+rules), P0-конвенция.
6. UI: бейдж пресета + пикер + лок — в шапке `SlideEditorModal` (контекст презентации;
   `api.js`: `fetchPresets/fetchPresentationStyle/updatePresentationStyle`;
   `MainPresentation`: `editorPreset`, fetch при открытии, `@update-style`).
   Пикер в `ProjectView` не делали осознанно: пресет назначается презентации, а не проекту.
7. Приёмка: presets 3/3; lock p4 → bad-variant 422, no-em 422, good 200; cleanup (пробы удалены,
   p4 = 30 слайдов, unlocked); фронт 200.
8. Инциденты: rules без ключа `variant` в сиде (лечилось мержем в enforcement);
   рестарт-цикл из-за отсутствия --reload; **клоббер файлов** (см. P2.1).

## P2.1. Инцидент: reproducibility правок (2026-09-17)

Симптом: часть применённых и проверенных правок исчезла с диска (P1 schemas, seeds,
фронт warnings UI; новые файлы `style_lint.py`, `STYLE_FLEX_PLAN.md` пропадали целиком).
Причина не установлена (синк-процессов нет). Защита: проверять `grep/ls` СРАЗУ после
каждой правки + финальный `git diff` review + checksums (`/tmp/checksums.txt`).
Всё восстановлено и перепроверено батареей (см. выше).

## P3.1. Аудит P3+P4 — DONE (2026-09-17, maximally critical)

P3: motion во всех 5 конфигах БД `{500,1000,2000}` ✓; компоненты ссылаются (6/1/1) ✓;
хардкодов таймингов не осталось ✓; node-тест мержа пройден ранее ✓.
P4: type-* во всех палитрах (p4/p11/p13 сверены) ✓; Slide оба layout по 2 var() с fallback ✓;
счётчики 85/1→?/85/86 — см. находку ниже.
Общее: трансформы 200, ошибок нет; p4/p13 = 30/30 pristine; пресеты 3/3.
НАХОДКА (починена): **теневое копирование палитры** — `ColorLibraryModal.handleSave` слал
full-list PUT, дублируя все 85 global-токенов в скоуп проекта (it2b: 86 строк) и замораживая
палитру (пересевы global переставали действовать). Фикс: single-key PUT только изменённого
токена. Дедуп: удалены 78 no-op теней (значение == global); оставлены 8 (bg-image, 1312,
3 пользовательских transparent/gradient, text-secondary/text-muted — отличаются от global:
либо осознанный оверрайд, либо stale; удаляются через библиотеку). it2b: 86→8.

## P2.1. Аудит P1+P2 — DONE (2026-09-17, maximally critical)

P1: validate plain/lint/strict+lint ✓; каталог 0 warnings ✓; PUT warnings + restore ✓;
invalid save 422 ✓; contrast unit ✓; variant enum 5/5 ✓; фронт 200, импорты целы ✓;
p4/p13 pristine (30/30) ✓.
P2: presets CRUD ✓ (POST custom `is_custom:true`, bad refs 400, DELETE default 403);
style get/put ✓; lock на CREATE (bad-variant 422, no-em 422, good 200) и UPDATE ✓;
custom rules (max_accents=2 → 5 акцентов 422) ✓.
Найденные дыры и фиксы:
1. **Lock без пресета = silent no-op** → теперь 400 `style_lock requires style_preset`.
2. Dangling preset (удалён назначенный): graceful skip, 200 без краша — ок, задокументировано.
3. Клоббер файлов (P2.1 выше): всё перепроверено маркерами + батареей; checksums стабильны 60с+.
UI пикер/бейдж: проводка ревью (open→fetch style→prop→select/lock→emit→PUT→refresh), трансформы 200.
Мусор зачищен: пробы 1887/1889/1890/1891/1892, audit-пресеты, p4/p13 = 30/30, unlocked.

## P2-план (исходный, ниже)

Проблема: вектор сейчас только в головах. Сущность «пресет» делает его выбираемым и проверяемым.

1. Таблица `style_presets`: `slug`, `title`, `palette` (slug проекта-палитры, переиспользуем
   проекты как палитры — нового хранения цветов не надо), `variant` (slug), `motion`
   (пока ссылка на вариант, после P3 — свой блок), `rules JSON`
   (`{max_accents, allow_glass: [slugs], title_em: bool, ...}`), `is_custom`.
   Сид: 3 пресета (`it2b-tech`, `history-classic`, `derevnya-eco`).
2. `presentations`: `style_preset` (nullable FK/slug) + `style_lock` (bool, default false).
   При `lock=true` сохранение слайда проверяет: `variant` слайда ∈ пресет + правила пресета
   (через линт P1 как errors) → иначе 422 с понятным message.
3. API: `GET/POST /presets/`, `GET /presentations/{id}/style` (разрезолвленный пресет),
   `PUT /presentations/{id}/style` (назначить/лок).
4. Фронт: пикер пресета в `ProjectView` (рядом с «Цвета проекта») + бейдж пресета/лока в редакторе.
5. ИИ: `AGENTS.md §13` шаг 0 — «выбери пресет, все слайды в его векторе»; манифесты не меняются.
6. Приёмка: залоченная преза реджектит чужой variant (422); пикер назначает и показывает.

## P3. Motion как часть варианта — DONE (2026-09-17, M)

Реализовано:
1. `style_variants.config.motion = {appear_ms: 500, stagger_ms: 1000, count_ms: 2000}` во всех
   5 вариантах (`seed_variants.py`); дефолты = текущие хардкоды (`appear` 500, `stagger` 1000 = §8.3, `count` 2000).
   `easing`/`blur_ms` осознанно НЕ добавляли (нечем потребить — dead config).
2. `useVariant.js`: `DEFAULT_MOTION` + `FALLBACK_CONFIG.motion` (синхрон!) + мерж
   `{...DEFAULT, ...base.motion, ...over.motion}` (per-component override тоже работает) + возврат `motion`.
   Кастомы без motion получают дефолты (P0-safe).
3. Компоненты: `PremiumChecklist` (appear+stagger-fallback), `InfographicCards` (appear),
   `AnimatedStats` (count). Единственное намеренное изменение поведения: entrance чеклиста
   700→500 (унификация, был случайный дрейф в том же файле).
4. Приёмка: motion во всех 5 конфигах БД; 4 файла 200 без ошибок; node-тест реального
   `useVariant.js` (стаб api): fallback `{500,1000,2000}`, custom base применяется,
   per-component override мержится (`{100,1200,2500}`).

## P3-план (исходный, ниже)

Сейчас длительности/изинги захардкожены в компонентах (300–800мс вразнобой) — премиальность
во многом про консистентный моушн.

1. `style_variants.config += motion: {appear_ms, stagger_ms, easing, blur_ms}`.
   Дефолты = текущие значения (поведение не меняется): `stagger_ms: 1000` (связать с §8.3!).
2. `useVariant.js` отдаёт `motion`; `FALLBACK_CONFIG` — синхронно (там комментарий-требование).
3. Компоненты переводятся постепенно, старт: `PremiumChecklist`, `InfographicCards`,
   `AnimatedStats` (их `getAnimProgress/getElasticProgress` durations + шаги `start_time`
   в сидах сверяются с `stagger_ms`).
4. Кастомные варианты в БД: `motion` отсутствует → дефолт через мерж (не затирать, см. P0).
5. Приёмка: смена `motion` в варианте visibly ретаймит; дефолт = попиксельно как было.

## P4. Типографическая шкала — DONE (2026-09-17, S)

Реализовано:
1. `type-display/h1/h2/body/caption` в 3 палитрах (`seed_tokens.py`): global
   `3.5/2.25/1.75/1.125/0.8rem` (= текущие классы, tech не меняется), history
   `4/2.75/2/1.15/0.85rem` (editorial serif с присутствием), derevnya
   `3.25/2.5/1.85/1.125/0.8rem`. Досеяно safe-режимом (без --force): 81→86.
2. `Slide.vue` (col+row): `h1` → `:style {fontSize: var(--type-h1, 2.25rem)}`,
   subtitle → `var(--type-body, 1.125rem)`; классы `text-4xl`/`text-lg` оставлены как fallback-носители.
3. Приёмка: токены пер-палитра (p4/p11/p13 проверены), `Slide.vue` 200 без ошибок, tech-значения = текущим.
4. `AGENTS.md §9`: шкала — исключение из «закрыто».

## P4-план (исходный, ниже)

Размеры сейчас «закрыты» (AGENTS §9). Компромисс — контролируемая шкала, не анархия:

1. Токены `type-display/h1/h2/body/caption` (+`type-*` веса при нужде) в каждой палитре.
2. `Slide.vue` — тайтлы/сабтайтлы на `var(--type-h1)` etc. с fallback на текущие классы;
   затем опционально компоненты.
3. Доки: обновить §9 (шкала — исключение из «закрыто»).
4. Приёмка: у `history`/`derevnya` свои кегли, tech не изменился, fallback держит без токенов.

## P5. Матрица превью + доки — DONE (2026-09-17, S)

Реализовано:
1. `scripts/generate_preview.py`: презы «Regression: {tech,classic,derevnya}» — все 30 компонентов
   (default_payload + variant), шаг 5с, EndMarker в конце, `presentation.variant` + `style_preset`
   назначены (без лока), папки-черновики проектов (токены через папку). Идемпотентно
   (пересоздание по title, каскад чистит слайды; проверено: 404 старых, 0 orphan SlideData).
   Текущие: смотри `title LIKE 'Regression:%'` (p26/27/28 на момент написания).
2. `TOKEN_SPEC.md`: §1.9 `slide-bg` помечены ЗАРЕЗЕРВИРОВАНЫ (шахматка отменена) + актуальные
   значения; §1.10 шкала; §1.11 motion/пресеты.
3. `DATABASE.md`: строки `/presets`, вектора в задачах.
4. Чеклист визуального прохода (по матрице, ~10 мин):
   - [ ] tech: стекло/тени карточек, glow-пятна подложки видны (контейнер, не перекрыты)
   - [ ] classic/derevnya: бумага/крем фоны, читаемость serif
   - [ ] derevnya: лес full-bleed снизу, без среза; градиент-пятна
   - [ ] фуллскрины (Terminal/Browser/Code): контраст с фоном слайда
   - [ ] ReceiptCard белый всегда; тинтов фона айтемов нет (только иконки/маркеры)
   - [ ] тайминги: появление разряжено (~1с), без рваности
   - [ ] тайтлы с `<em>`, шкала кеглей пер-тема

## P5-план (исходный, ниже)

1. `scripts/generate_preview.py`: презентации «Регрессия стилей» — все 30 компонентов ×
   3 дефолтных варианта (3 презы: tech/classic/derevnya). Ручной визуальный проход по чеклисту
   (док): контраст, лес/глоу подложки, тинты, тайминги.
2. `TOKEN_SPEC.md` — новые секции (motion, type, presets); `AGENTS.md` — шаги workflow 0 (пресет),
   §6 (warnings — DONE), §9 (шкала); `DATABASE.md` — `style_presets`, `is_custom` вариантов.

## Карта файлов

| Фаза | Backend | Scripts | Frontend | Docs |
|------|---------|---------|----------|------|
| P0 DONE | `models.py` (`StyleVariant/Component.is_custom`), `routers/components.py` | `seed_*.py` (`--force`, skip custom, DROP удалён) | — | план |
| P1 DONE | `style_lint.py` (new), `validation.py` (без изменений), `routers/components.py` (`?lint`), `routers/presentations.py` (lint на save), `schemas.py` (warnings) | `seed_components.py` (нормалайзер плотности) | `SlideEditorModal.vue` (плашка), `MainPresentation.vue` (сбор) | `AGENTS.md §6`, план |
| P2 | `models.py` (`StylePreset`, `Presentation.style_preset/lock`), `routers/presets.py` | `seed_presets.py` | `ProjectView.vue`, редактор (бейдж) | `AGENTS.md §13` |
| P3 | — (конфиг) | `seed_variants.py` (motion) | `useVariant.js`, 3 компонента | `AGENTS.md §8.3/§10` |
| P4 | — | `seed_tokens.py` (type-*) | `Slide.vue` (+компоненты) | `AGENTS.md §9` |
| P5 | — | `generate_preview.py` | — | `TOKEN_SPEC.md`, чеклист |

## Риски

- Линт без `presentation_id` не считает контраст — явно skip, не false-positive (контраст только на save).
- `no-hex` только по типизированным полям, иначе заденет подсветку синтаксиса в `code`.
- Пресеты ссылаются на проекты-палитры — удаление проекта-палитры роняет пресет (FK restrict + проверка в API).
- Motion-дефолты обязаны совпадать с текущими хардкодами, иначе «поплывёт» весь каталог.
