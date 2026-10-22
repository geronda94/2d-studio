# AGENT_PLAYBOOK.md — Как агент собирает презентацию из сценария

> Единая пошаговая инструкция для ИИ-агента: **на входе сценарий → на выходе готовая
> презентация с озвучкой, таймлайном и слайдами.**
> Дополняет (не заменяет): `AGENTS.md` (правила компонентов §4.4, тайминги §8, скрипты §12),
> `docs/PRESENTATION_PIPELINE.md` (этапы пайплайна), `docs/animation_guidelines.md` (анимации),
> `docs/TOKEN_SPEC.md` (цвета). При расхождении — приоритет у этого файла по процессу,
> у `AGENTS.md` — по контрактам компонентов.

---

## 0. Режим работы

Пользователь даёт **сценарий** (текст озвучки, разбитый на смысловые блоки). Агент:

1. создаёт презентацию в нужной папке проекта;
2. озвучивает её через Gemini TTS (голос + пресеты по блокам);
3. строит `audio_timeline` (4 дорожки, BGM);
4. ставит `EndMarkerSlide` — якорь конца видео;
5. собирает слайды по блокам (компоненты + payload по контрактам);
6. выравнивает тайминги слайдов по координатам клипов озвучки;
7. валидирует и отдаёт ссылку на просмотр/рендер.

**Жёсткие инварианты (не нарушать):**
- Не выдумывать payload — только `payload_schema` + `example` из `GET /components/`.
- Валюта только **€**. Эмодзи запрещены. Тайтлы с `<em>`.
- Старты соседних слайдов — шаг **≥ 2000 мс**.
- `EndMarkerSlide` — **всегда последний**, без payload.
- Не ломать рендер: только детерминированные анимации от `relativeTime` (см. `animation_guidelines.md`).

---

## 1. Формат входа (сценарий)

### 1.1 Если пользователь даёт «просто текст»
Агент сам режет его на **5 смысловых блоков** (шортс) или N секций (длинное видео):

| id | label | окно (шортс) | роль |
|----|-------|--------------|------|
| `hook` | HOOK | 0–3с | зацепка |
| `most` | МОСТ | 3–8с | связка с проблемой |
| `proof` | PROOF | 8–45с | основной разбор (самый длинный) |
| `payoff` | PAYOFF | 45–55с | вывод/инсайт |
| `hook_out` | HOOK OUT / CTA | 55–60с | призыв |

### 1.2 Если пользователь даёт .txt-файл
Его можно подать в `generate_short.py --file`. Парсер `load_scenario_from_file` требует
**≥4 абзаца, разделённых пустой строкой**, в порядке:
```
абзац 1            → hook
абзац 2            → most
абзацы 3..n-2      → proof (склеиваются в один)
абзац n-1          → payoff
абзац n            → cta
```
Примеры: `scripts/_inbox/short03.txt`, `scripts/_inbox/long01.txt`.

> ⚠️ Сценарий — это **только текст озвучки**. Тайминги, слайды и данные придумывает агент.

---

## 2. Предусловия

- Инфраструктура поднята: `docker compose up -d` (db `5435`, backend `8001`, frontend `5174`).
- Проект и папка известны:
  - проект **IT2B** (`projects.slug = it2b`), папки: `long` «Широкоформатные» (id=1), `shorts` «Шортсы» (id=2), `drafts` (id=3).
  - history (id=2) и derevnya (id=3) — свои темы.
- **Порты/адреса (важно):**
  - С **хоста**: API `http://localhost:8001`, медиа `/media/*`, `/uploads/*`.
  - **Внутри контейнера backend** скрипты бьют в `http://localhost:8000` (см. `revoice_from_file.py`, `build_*_slides.py`) — это тот же процесс на порту 8000.
- Проверка живости: `curl -s http://localhost:8001/` и `curl -s http://localhost:8001/components/ | head -c 200`.

---

## 3. Алгоритм по шагам

### Шаг 1 — Разобрать сценарий
Определить: тип (шортс/длинное), блоки, ключевые цифры/факты (они попадут в ReceiptCard, AnimatedStats, StatsBarChart и должны совпадать с озвучкой).

### Шаг 2 — Создать презентацию
```
POST /presentations/
{ "title": "<заголовок>", "folder_id": 2 }   # 2 = Шортсы, 1 = Длинные
```
Ответ → `id` презентации (далее `PRES_ID`).

### Шаг 3 — TTS (озвучка) по блокам
**1 вызов на смысловой блок** (не на предложение). Внутри блока — непрерывный поток,
паузы только между блоками (200 мс, задаются на этапе таймлайна).

```
POST /ai/presentations/{PRES_ID}/generate-speech
{
  "text": "<текст блока>",
  "voice": "Charon",
  "audio_profile": "A confident and dynamic tech expert with a deep, resonant voice.",
  "style": "<из пресета блока>",
  "pace":  "<из пресета блока>",
  "tone":  "<из пресета блока>",
  "scene": "A high-end tech YouTube channel for IT2B — business automation and AI.",
  "temperature": 0.9,                 # hook 0.9, остальные 0.8
  "batch_id": "short_<N>_<timestamp>" # общий для всех клипов презентации
}
```
Ответ → `MediaFile` с `file_path` (напр. `/media/ai_voice_xxx.wav`) и `id`.

**Голоса:** `Charon` (основной, глубокий), `Aoede` (женский), `Fenrir` (энергичный),
`Kore` (мягкий), `Puck` (технический).

**Пресеты по блокам (locked, p/16):**

| блок | pace | tone | temperature |
|------|------|------|-------------|
| hook | Very fast, rapid-fire, urgent (5-sec elevator pitch) | Provocative, sharp, alarming | **0.9** |
| most | Very fast, brisk, driving, urgent storytelling | Storytelling, slightly ironic | 0.8 |
| proof | Very fast, rapid-fire, news-anchor speed | Grounded, vivid, confident | 0.8 |
| payoff | Fast, firm, decisive | Wise, conclusive, memorable | 0.8 |
| cta | Fast, personal, like a friend texting | Friendly, direct, inviting | 0.8 |

ffmpeg-ускорение (`speedup`) = **1.0** (без ускорения) в базовом шаблоне.

### Шаг 4 — Длительности
```
GET /ai/audio-duration?file_path=/media/ai_voice_xxx.wav
→ { "duration_ms": 6000.0 }
```
(опционально — Whisper word-level: `POST /ai/transcribe {file_path, language:"ru", model_size:"base"}`
для точной привязки границ, если сценарий длинный.)

### Шаг 5 — Собрать `audio_timeline` (4 дорожки, ВСЕГДА)
Координаты: `start = текущая`, `end = start + duration`, `next_start = end + 200` (пауза 200 мс
**только между блоками**).
```
{
  "tracks": [
    { "id": "main",    "type": "voiceover", "clips": [ {id,name,src,start_time,end_time,media_offset:0,volume:1,type:"ai_voice",ai_settings} ] },
    { "id": "overlay", "type": "voiceover", "clips": [ {id,name:"Automated_Horizon.mp3",src:"/media/94372...mp3",start_time:0,end_time:<total+2000>,volume:0.15,type:"audio"} ] },
    { "id": "bgm",     "type": "bgm",       "clips": [] },
    { "id": "sfx",     "type": "sfx",       "clips": [] }
  ]
}
```
Сохранить: `PUT /presentations/{PRES_ID} { "audio_timeline": {...} }`.

**BGM IT2B:** `Automated_Horizon.mp3` → `/media/94372fbfcdca4683ba46d34ae1fd78a5.mp3` (основной),
`Structured_Intent.mp3` → `/media/e1ecd277d28e4e13b9bf3b7305d34dd5.mp3`.

### Шаг 6 — Якорь конца: `EndMarkerSlide`
- `start_time` = **ровно конец последнего клипа дорожки озвучки** (`main`/`voiceover`, обычно `tracks[0]`),
  **НЕ** BGM (`overlay` длиннее и не якорь).
- `order_index = 999`, без payload.
- От него считается длительность видео: `duration = EndMarker.start_time/1000 + 1с` (плюс ~1–1.5с
  оверхеда захвата). Двигая маркер — двигаешь конец mp4.

### Шаг 7 — Слайды (ключевой шаг)
Для каждого блока — 1–несколько слайдов, длительность 3–6с (шортс) / 4–10с (длинное).

**Маппинг блок → компоненты (ориентир, не догма):**

| блок | подходящие компоненты |
|------|----------------------|
| HOOK | `ChatMockupSlide`, `BrowserMockup`, `ReceiptCard` |
| МОСТ | `AnimatedStatsSlide`, `InfographicCards`, `NetworkWaterfall` |
| PROOF | `ArchitectureDiagram`, `InteractiveArchitecture`, `ComparisonTable`, `ModernTable`, `CodeExplain`, `CodeComparisonSlide`, `ProcessFunnel`, `StatsBarChart`, `PremiumChecklist`, `MetricScales` |
| PAYOFF | `MetricScales`, `InfographicCards`, `ProcessFunnel`, `BentoGridGallery`, `AnimatedStatsSlide` |
| CTA | `OutroSlide` |

**Цикл на каждый слайд:**
1. `GET /components/` → взять нужный компонент, прочитать `manifest` (когда использовать/
   не использовать), `payload_schema` (типы, required, min/max_items) и `example` (эталон).
2. Заполнить payload по `example`, адаптировав под сценарий (тексты — перефразировка озвучки,
   цифры — строго как в озвучке).
3. `POST /components/{slug}/validate?lint=true { "payload": {...} }` → при errors поправить,
   warnings тоже устранить (`no-hex`, `accent-budget`, `dense_timing`, `low-contrast`).
4. `POST /presentations/{PRES_ID}/slides`:
```
{
  "slide_id": "<уникальная строка>",
  "component": "<slug из реестра>",
  "start_time": <мс>,
  "order_index": <N>,
  "title": "<с <em>>",
  "subtitle": "<...>",
  "layout": "col",
  "data": { "payload": { ... } }
}
```
5. Не повторять один компонент в 4 соседних слайдах.
6. Последним — `EndMarkerSlide` (шаг 6).

> Полные правила по каждому из 30 компонентов — `AGENTS.md` §4.4. Обязательно сверяться с ними
> перед заполнением.

### Шаг 8 — Выровнять тайминги слайдов
- Старты слайдов = координаты клипов озвучки из `tracks[0].clips[i].start_time`, **не пересчитывать вручную**.
- Шаг между стартами соседних слайдов **≥ 2000 мс** (без исключений).
- `OutroSlide` — последний контентный, заканчивается там, где начинается маркер.
- Внутри payload айтемы разряжены: шаг `start_time` ≥ 800–1000 мс (рекоменд. ~1000+);
  после последнего айтема ≥ 2000 мс. Исключение — `InteractiveArchitecture` (см. §5).

### Шаг 9 — Проверка и рендер
- Просмотр: `http://localhost:5174/p/{PRES_ID}`.
- Проверка данных/таймингов: `GET /presentations/{PRES_ID}` (слайды + payload).
- Рендер: UI «Рендер-ферма» либо `POST /renders/realtime {presentation_id, settings}`.

---

## 4. Управление таймлайном

### 4.1 Две шкалы
- **Глобальная** (`slides.start_time`, мс от начала презы): последовательность слайдов;
  шаг ≥ 2000 мс, без наложений. Смена слайда в плеере — по событиям `SLIDE_CHANGE`
  (`MainPresentation.vue` строит их из `start_time`).
- **Локальная** (payload-поля `start_time` внутри массивов): появление айтемов
  относительно старта слайда (0 = сразу). См. §5.

### 4.2 Движение/сдвиг
- В UI — таймлайн в `DirectorDebugPanel`/`AudioTimeline`; перетаскивание старта слайда
  каскадно сдвигает последующие (min 2000 мс от предыдущего).
- Программно — `PUT /presentations/slides/{slide_id}` (нужны ВСЕ обязательные поля:
  `slide_id`, `component`, `start_time`, `order_index`, `title`, `subtitle`, `layout`, `data`).
- После смены озвучки — `revoice_from_file.py` пересчитывает границы и **ремапит** слайды
  пропорционально, сохраняя payload.

### 4.3 Точки синхронизации
- `audio_timeline.tracks[0].clips[i].start/end_time` — источник истины для стартов слайдов.
- `EndMarkerSlide.start_time` — источник истины для конца видео.
- `render_fullscreen_capture.py` слушает `useDirector`; анимации обязаны идти от `relativeTime`.

### 4.4 Быстрое редактирование
- Изменить текст/цифры слайда → `PUT /presentations/slides/{slide_id}` (тот же payload с правкой).
- Изменить только вариант слайда → `"variant"` в payload (или `set_slide_variant` в change-set).
- Пакетные правки без UI → `POST /presentations/{PRES_ID}/change-set` (dry_run по умолчанию,
  атомарно); удобно для ИИ. История — `GET /presentations/{PRES_ID}/revisions`.

---

## 5. Управление данными (payload)

### 5.1 Базовые правила
- **Только из `example` + `payload_schema`.** Схема задаёт типы, `required`, `min_items`/`max_items`, enum.
- Числовые поля — числа (не строки); `AnimatedStatsSlide`/`InfographicCards` value ≠ 0.
- Цвета — токены (`color-*`, `chart-1..6`, `item-accent-1..4`), hex в цветовых полях → warning.
- Разнообразие: в списочных компонентах у каждого айтема **свой** `color`/`icon`.
- Тайминг айтемов ≥ 800–1000 мс.
- Эмодзи в JSON запрещены (только Lucide/Heroicons).

### 5.2 Минимумы под широкий формат (1920×1080)
| компонент | правило |
|-----------|---------|
| `InfographicCards` | **ровно 4** айтема |
| `ReceiptCard` | ≥ 3 пункта, сумма = озвученный убыток |
| `ProcessFunnel` | ≥ 4 шага, `layout:"horizontal"`, `count` int |
| `PremiumChecklist` | ≥ 3 пункта |
| `StatsBarChart` | ≥ 4 столбца |
| `ComparisonTable` | 3–4 строки, `headers[0]=""` |
| `MetricScales` | ≥ 3 метрики, `percentage` 1–100 |
| `CrmCardSlide` | **ровно 4 поля + 2 кнопки** |

### 5.3 Особые контракты (частые ошибки)
- `ChatMockupSlide`: ключ `role` (`user`/`assistant`), диалог двусторонний; в сетапе ошибки бот обязан ошибиться.
- `TerminalMockup`: ключ команды — `cmd` (не `text`).
- `PremiumChecklist`: ключ заголовка — `label` (не `title`).
- `ArchitectureDiagram`: `color` только `chart-N`/полный токен (`color-primary`), **не голый `primary`**.
- `InteractiveArchitecture`: `start_time` ровно у **одной** ноды; `x/y` не задавать.
- `BrowserMockup`: slug без `Slide`, `type:"html"`, content = реальный UI с адаптивом.
- `CrmCardSlide`: `field_icon`/`field_color` (не `icon`), кнопка — `text` (не `label`).

> Полный справочник — `AGENTS.md` §4.4 и `docs/PRESENTATION_PIPELINE.md` §«Критические правила».

---

## 6. Скрипты и команды (cheatsheet)

```
# 1) Сценарий → презентация + TTS + timeline + EndMarker (БЕЗ слайдов!)
docker compose exec backend python scripts/generate_short.py --file scripts/_inbox/short03.txt --title "Мой шортс"
docker compose exec backend python scripts/generate_short.py --short 2        # встроенный сценарий

# 2) Переозвучка существующей презентации (слайды ремапятся, payload сохраняется)
docker compose exec backend python scripts/revoice_from_file.py --pres-id 16 --file scripts/_inbox/shorts02.txt
#   --gap 200     пауза между блоками
#   --speedup 1.2 ffmpeg atempo (ускорение)

# 3) Сборка слайдов (шаблон авторинга: массив SLIDES → validate → POST slides)
docker compose exec backend python scripts/build_shorts20_slides.py

# 4) Любая правка/проверка — через API (см. §3)
```

**⚠️ `generate_short.py` НЕ создаёт контентные слайды.** Он делает шаги 2–6 (презентация,
озвучка, `audio_timeline`, `EndMarkerSlide`). Слайды (шаг 7) строятся отдельным скриптом
(`build_shorts*_slides.py`) или руками через API. Это главная причина пустого «шортса из коробки».

**Порядок после правки библиотеки компонентов** (внутри backend-контейнера):
```
python scripts/seed_components.py
python scripts/generate_schemas.py
python scripts/generate_examples.py
python scripts/seed_manifests.py
```

---

## 7. Валидация, линт, пресет-лок

- `POST /components/{slug}/validate { "payload": {...} }`, опц. `?strict=true&lint=true`.
- **errors** (блокируют): `missing_required`, `type_mismatch`, `invalid_format`, `invalid_enum`,
  `min_items`, `max_items`, `non_monotonic_start_time`; при `strict` — `unknown_field`.
- **warnings** (не блокируют, но правим): `no-hex`, `accent-budget` (>4 акцентов),
  `dense_timing` (0 < gap < 800 мс), при сохранении слайда ещё `low-contrast`.
- **preset-lock**: если у презентации `style_lock=true`, слайд вне вектора пресета → 422.
  Пресеты: `it2b-tech`, `history-classic`, `derevnya-eco` (rules `{max_accents:4, title_em:true}`).

---

## 8. Темы и варианты (кратко)

- **Вариант** (`payload.variant` → `presentation.variant` → `tech`): `tech/classic/industrial/educational/derevnya` — форма/радиусы/линии, **не цвет**.
- **Тема** (`design_tokens`, global→project→presentation→slide): цвета/шрифты. Шахматка айтемов `item-accent-1..4`; диаграммы `chart-1..6`; Tailwind-классы `bg-bg-base`, `text-text-primary` и т.п.
- `history` — светлая «бумажная»; `derevnya` — эко; IT2B — тёмная техно (дефолт).

---

## 9. Грабли (проверять перед сдачей)

1. `slide.component` не совпадает с slug реестра (напр. `BrowserMockupSlide`) → пустой экран.
2. `generate_short.py` запущен, но слайды не собраны → преза из маркера.
3. Плотные тайминги айтемов (200–500 мс) → рваный эффект.
4. Дубли/гап < 2000 мс между слайдами → нарушения (есть в архивных p5/p14).
5. `ArchitectureDiagram` цвет `primary` → белая нода.
6. `AnimatedStatsSlide` value=0 или строкой.
7. `ReceiptCard` суммы не совпадают с озвучкой / 1 пункт.
8. `ChatMockupSlide` односторонний диалог.
9. `InfographicCards` 6 айтемов → ломает сетку.
10. EndMarker не на конце озвучки (взял BGM) → неверная длительность видео.
11. Hex вместо токена в цветовом поле → warning (и мимо темы).

---

## 10. Чек-лист перед сдачей

- [ ] Презентация создана в нужной папке проекта.
- [ ] Озвучка: 1 клип на блок, пресеты по таблице, общий `batch_id`.
- [ ] `audio_timeline`: 4 дорожки, BGM на 15%, паузы 200 мс между блоками.
- [ ] `EndMarkerSlide` стоит на конце дорожки озвучки, без payload.
- [ ] Слайды: компоненты по `manifest`, payload по `example`+`payload_schema`, validate(+lint) пройден.
- [ ] Старты слайдов = клипы озвучки, шаг ≥ 2000 мс; айтемы разряжены ≥ 800–1000 мс.
- [ ] Тайтлы с `<em>`, без эмодзи, валюта €; тексты — перефразировка озвучки.
- [ ] Не более 4 разных акцентов; hex только там, где разрешён.
- [ ] Просмотр `/p/{PRES_ID}` без ошибок; при необходимости — рендер.

---

## 11. Референс-пример (p20 — «02 - ИИ-агент начал врать клиентам»)

Блоки (72.0с): HOOK 0–3960 · MOST 4160–12360 · PROOF 12560–54560 · PAYOFF 54760–63480 · CTA 63680–71840.

Порядок слайдов (17): `ChatMockupSlide → ReceiptCard → InfographicCards → ArchitectureDiagram →
ProcessFunnel → MetricScales → ChatMockupSlide → AnimatedStatsSlide → ComparisonTable →
StatsBarChart → TerminalMockup → ArchitectureDiagram → CodeExplain → PremiumChecklist →
BentoGridGallery → OutroSlide → EndMarkerSlide`.

Скрипт-эталон: `scripts/build_shorts20_slides.py` (массив `SLIDES`: `validate` → `POST /slides`).

---

## 12. Журнал итераций и постоянные правила IT2B (живой раздел)

> Дополняется по мере работы над шортсами/роликами. Читать перед каждой новой сборкой.

### 12.1 Постоянные правила контента IT2B
- **Фоновая музыка — ВСЕГДА** в IT2B, на **выделенной дорожке `bgm`** (трек «3» на таймлайне):
  клип `type:"audio"`, `Automated_Horizon.mp3` (`/media/bgm_automated_horizon_v2.mp3`),
  **volume `0.15`**, `start_time:0`, `media_offset: ~20000` (начало трека обрезано ~20 с — эталон p35),
  `end_time: конец озвучки (main) + 2000`.
  **Музыка обязана заполнять весь таймлайн до `EndMarkerSlide`.** Если трек короче ролика —
  выкладываем несколько клипов **подряд** (loop): `start_time` следующего = `end_time` предыдущего.
  Пример: ролик 5 мин, трек 2 мин → 3 клипа (2+2+1) до EndMarker.
  `transfer`: `generate_short` кладёт музыку в `overlay` c `media_offset:0` — сборочный скрипт обязан
  перенести её в `bgm`, выставить offset и замостить до конца (`normalize_bgm_track`, константы
  `BGM_MEDIA_OFFSET_MS`/`BGM_SRC` в `scripts/build_shorts04.py`). Легаси-p9/p21 — не ориентир.
- Озвучка: 5 блоков (hook/most/proof/payoff/cta), 1 TTS-вызов на блок, голос `Charon`,
  паузы **200 мс только между блоками**, `batch_id` общий. Пресеты — §4 / `VOICE_PRESETS`.
- Тайминг: старты слайдов = координаты клипов `main`, шаг **≥ 2000 мс**; айтемы ≥ 800–1000 мс.
- `EndMarkerSlide` — последний, без payload; `OutroSlide` — последний контентный.
- **OutroSlide IT2B — ЭТАЛОН (зафиксирован по p35/s04_10):** только лого + QR, `handle`/`headline` пустые.
  ```json
  {"variant":"tech",
   "logo":"/media/it2b_logo_v2.png",
   "qr_code":"/media/it2b_qr_v2.png",
   "handle":"",
   "headline":""}
  ```
  Файлы: `it2b_logo_v2.png` (IT2B), `it2b_qr_v2.png` (Telegram). Не добавлять подписи — формат единый
  для всех шортов IT2B. Скрипты: `IT2B_OUTRO` в `scripts/build_shorts04.py`.
  Если картинки «битые» — см. §12.4 (кэш Cloudflare).
- Тайтлы: ~половина слов в `<em>`; валюта только €; эмодзи запрещены.

### 12.2 Конвенции заполнения payload (для понятности)
- **InfographicCards / PremiumChecklist и любые карточки:** `label` — понятная фраза
  («Прайс и наличие», «Нестандартный торг»), а не одно слово; `value` — 1 короткое слово/символ
  («Да»/«Нет»/«€0»), `trend` — человеческое пояснение («только человек», «клиент ушёл»).
  Слайд должен читаться без озвучки.
- **Цвета — только токены**, не hex: разноцветные айтемы → `var(--item-accent-1..4)` циклом
  `{(i%4)+1}`; диаграммы → `chart-1..6`; семантика → `color-success/warning/error/**danger**`.
- **Разнообразие:** у каждого айтема свой `color` + `icon` (не повторять).
- **Позитив/негатив — токенами.** Галочки/крестики и статусы красить по смыслу:
  позитив (`true`) → `color-success` (`bg-color-success/20 text-color-success border-color-success/30`),
  негатив (`false`) → `color-danger` (`bg-color-danger/15 text-color-danger border-color-danger/30`).
  `ComparisonTable` уже семантичен (`true`→зелёный, `false`→красный) — «наш» столбец ставить **первым**,
  иначе подсветка заголовка ляжет на негативную колонку.
- **Иконки — всегда валидные и с префиксом.** Пиши `heroicons:*`, `lucide:*`, `logos:*` и проверяй
  существование в Iconify. Частый трап: **`heroicons:fence` не существует** (нужен `lucide:fence`).
  `PremiumChecklist`/`InfographicCards`/`AnimatedStats` НЕ достраивают префикс, поэтому короткое
  имя (`cpu`) даст битую иконку; `ArchitectureDiagram` умеет достраивать `lucide:`, но лучше явно.
  Перед сдачей: `python3 scripts/check_icons.py <PRES_ID>` → должно быть `проблемных: 0`.
- **`BrowserMockup` HTML на всю высоту:** контентный контейнер имеет `container-type:size`, а его
  обёртка — только `min-h-full`, поэтому `height:100%`/`min-height:100%` **не резолвятся** и снизу
  остаётся пустота. Задавай корню `min-height:100cqh` (+ `box-sizing:border-box;overflow:hidden`).
  Нав держать в **одну строку** (`flex-wrap:nowrap`, мелкие кегли), иначе он вылезает/переносится
  и контент режется по бокам.
- **InfographicCards = ровно 4** айтема (6 ломает сетку); `AnimatedStats.value` int ≠ 0.
- `title`/`subtitle` слайда — перефразировка озвучки, не копия.
- После сборки прогнать `POST /components/{slug}/validate?lint=true` по каждому слайду →
  должно быть **0 errors и 0 warnings** (частая правка: hex→токены, шаг айтемов <800 мс).

### 12.3 Порядок сборки (устойчивый)
> 🔐 **Авторизация.** С 2026-09 backend работает с `AUTH_MODE=on`: каталог (`/components`),
> `/variants`, `/presets` — только **супер-админ**, POST/PUT требуют **CSRF**. Сборочные скрипты
> обязаны первой строкой делать `import agent_auth` (логин из `.env` `ADMIN_EMAIL`/`ADMIN_PASSWORD`,
> патчит `requests`: сессия + `X-CSRF-Token`). Проверка: `curl -s -o /dev/null -w "%{http_code}"
> -X POST .../components/X/validate` → 401 без сессии / 200 с ней.

1. Скрипт-сборщик: `scripts/build_shortsNN.py` (по образцу `build_shorts04.py`), запуск **с хоста**
   (`python3 scripts/build_shortsNN.py`) — TTS/таймлайн через `generate_short.py` (BASE `localhost:8001`).
2. Скрипт делает: create presentation (folder_id=2) → TTS 5 блоков → `audio_timeline` → `EndMarkerSlide`
   → слайды (validate → `POST /slides`) c таймингами из клипов.
3. Проверки: монотонность стартов ≥2000 мс, lint = 0, BGM на треке `bgm` vol 0.15,
   иконки: `python3 scripts/check_icons.py <PRES_ID>` → 0 проблемных.

### 12.4 Грабли
- 🔥 **Timeline Cleaner мог стереть озвучку/музыку.** При перезапуске backend (или сетевом сбое)
  у открытой страницы аудио не грузилось, срабатывал `audio-clip-error`, и
  `MainPresentation.handleAudioClipError` **удалял клипы и сохранял таймлайн**. Так пропали 4 из 5
  голосовых клипов p35. **Исправлено:** Cleaner теперь удаляет клип только если файл реально
  отсутствует (`HEAD` → `404`); транзиентные ошибки игнорируются. Перезапуская backend при открытой
  у вьюера странице — будь готов, что cliпы могли «усохнуть»; проверяй `main` после таких сессий.
- 🔥 **Cloudflare кэширует 404 на год.** Прод отдаётся через `*.it2b.top` (Cloudflare). Бэкенд
  ставил `Cache-Control: immutable` на **все** `/media/*`, включая 404 → CF закэшировал битые файлы
  (`cf-cache-status: HIT`), что давало «битые» лого/QR и BGM. **Исправлено:** `main.py` ставит
  immutable только на `200`, на остальное `no-store`. Если файл всё же закэширован как 404 (нет токена
  CF для purge) — залей под **новым именем** (`*_v2`) и обнови ссылку. Проверка:
  `curl -skI https://5174.it2b.top/media/<file>`.

- ⚠️ **BGM мог сбрасываться при UI-сохранении** (`PUT /presentations/{id}` из редактора приходит
  с `audio_timeline` без музыки). **Защита на бэкенде** (`presentations.py`, `update_presentation`):
  если в старом таймлайне был BGM-клип (`type=="audio"`), а новый пришёл без него — клип сохраняется.
- **Кнопка × у дорожки** в `AudioTimeline` (`removeTrack`) очищает клипы трека — не удалять
  дорожку 3 (`bgm`) с музыкой (бэкенд-защита вернёт клип при сохранении).
- `generate_short.py` не создаёт слайды (только презу/TTS/таймлайн/маркер) — слайды отдельно.
- `AnimatedStats.value=0` и `InfographicCards` >4 айтемов — запрещены.

### 12.5 Широкоформатные ролики (longform)
- **Структура 7 блоков:** ТЕЗИС · ХАЙП vs РЕАЛЬНОСТЬ · КАК Я ДУМАЮ ОБ ЭТОЙ ЗАДАЧЕ · РЕАЛЬНЫЙ
  ПРОЕКТ · ГДЕ НЕ РАБОТАЕТ · ВЫВОД · МЯГКИЙ CTA. Источник — `.md` (парсим секции, `[ВИЗУАЛ]` пропускаем).
- **Папка `Длинные`** (`folder_id=1`). TTS — **7 вызовов**, спокойные пресеты (`LONG_PRESETS` в
  `scripts/build_long02.py`), пауза между блоками **200 мс**. Голос `Charon`.
  🔒 **Скорость longform:** ускорять wav на **`atempo=1.08`** (+8%, допустимо 1.05–1.10) —
  «присыпающую» подачу не терпим; паузы короткие. Реализация: `speedup_and_upload()` +
  `SPEEDUP` в `scripts/build_long03b.py`. Шортсы и так идут «очень быстро» (preset pace).
  🔒 **Никаких шёпотов:** подача ясная и ровная, без шёпота/бормотания/затухания; в `audio_profile`
  явно «clear and projecting, never whispers». Шёпотный фрагмент — перегенерировать блок.
- **Слайды:** шаг 5–8 с (long-формат 4–10 с), ~40–45 слайдов на 4–5 мин; `compute_times`
  распределяет по секциям пропорционально. Компоненты переиспользуются с разными payload.
- **BGM:** та же логика (`bgm`, vol 0.15, offset 20000), но **loop клипами** до `EndMarker`
  (на ~4.6 мин — 2 клипа; см. §12.1).
- **Скрипты:** `scripts/build_long02.py` (озвучка + таймлайн + EndMarker) →
  `scripts/build_long02_slides.py` (слайды). Отдельно от шортсовых `build_shortsNN.py`.

### 12.6 Журнал сборок
| Дата | Ролик | PRES id | Файл сценария | Слайды | Заметки |
|------|-------|---------|---------------|--------|---------|
| 2026-09-19 | Шортс_04 «Пытались закрывать сделки силами ИИ» | **35** | `Тексты_под_озвучку/Месяц_1/Шортс_04…txt` | 10 | TTS 53.5с; BGM `bgm` 0.15 (0→54480); иконки 16/16; lint 0/0; `scripts/build_shorts04.py` |
| 2026-09-19 | Шортс_05 «Сайт выглядит дорого. Заявок ноль» | **36** | `Тексты_под_озвучку/Месяц_1/Шортс_05…txt` | 10 | TTS 49.4с; BGM `bgm` 0.15 offset 20000 (0→50400); иконки 14/14; lint 0/0; `scripts/build_shorts05.py` |
| 2026-09-19 | Шортс_06 «Что делать когда старая интеграция упала» | **37** | `Тексты_под_озвучку/Месяц_1/Шортс_06…txt` | 9 | TTS 55.5с; BGM `bgm` 0.15 offset 20000 (0→56480); иконки 18/18; lint 0/0; `scripts/build_shorts06.py` |
| 2026-09-19 | **Длинное_02** «Что ИИ-агент реально умеет в продажах» | **38** | `Месяц_1/Длинное_02…md` | 41 | TTS 275.3с; 7 блоков; BGM `bgm` 2 клипа (0→276320); иконки 40/40; lint 0/0; `build_long02.py` + `build_long02_slides.py` |
| 2026-09-27 | Шортс_07 «Галлюцинация агента в реальном диалоге» | **65** | `it2b/…/Тексты_под_озвучку/Месяц_1/Шортс_07…txt` | 10 | TTS 50.8с; BGM `bgm` 0.15 offset 20000 (0→51800); иконки 17/17; lint 0/0; `scripts/build_shorts07.py`; добавлен `scripts/agent_auth.py` |
| 2026-09-27 | Шортс_07 **v2 (новые компоненты)** | **67** | та же озвучка (копия p65) | 10 | NodeFlow/QuadrantMatrix/HeatmapMatrix/DefinitionBlock/WaterfallChart/ControlChart/StepByStep/CircularGauge/JourneyMap; lint 0/0; иконки 10/10; `scripts/build_shorts07_v2.py` |
| 2026-09-27 | **Длинное_03** «Почему сайты на Tilda не конвертируют» | **68** | `it2b/…/Месяц_1/Длинное_03…md` | 43 | TTS 280с; 7 блоков; BGM `bgm` 2 клипа (0→281040); иконки 44/44; lint 0/0; `build_long03.py` + `build_long03_slides.py`; новые: QuadrantMatrix/WaterfallChart/StepByStep/KpiDashboard |
| 2026-09-27 | **Длинное_03 v2** «Привет из 2010» (переписанный сценарий) | **69** | тот же `.md` (обновлён) | 44 | TTS 308.5с; 7 блоков; BGM `bgm` **3 клипа** (0→309520); иконки 41/41; lint 0/0; `build_long03b.py` + `build_long03b_slides.py`; новые: QuoteCard/DefinitionBlock/QuadrantMatrix/WaterfallChart/StepByStep/KpiDashboard |
| 2026-09-27 | **Длинное_03 v3** «Привет из 2010» (**озвучка быстрее**) | **70** | тот же `.md` | 44 | TTS 284.2с (atempo ×1.08, паузы 200мс); BGM `bgm` 2 клипа (0→285173); lint 0/0; 🔒 правило скорости в §12.5 + `инструкция_для_агента_озвучки.md` |
| 2026-09-27 | Шортс_08 «Скорость 6 секунд против 1.8» | **71** | `it2b/…/Месяц_1/Шортс_08…txt` | 10 | TTS 63.2с; BGM `bgm` 0.15 offset 20000 (0→64200); иконки 11/11; lint 0/0; `scripts/build_shorts08.py`; профиль голоса +`never whispers` |
| 2026-09-27 | Шортс_09 «Hubspot за 500 евро в месяц» | **72** | `it2b/…/Месяц_1/Шортс_09…txt` | 10 | TTS 69.3с; BGM `bgm` 0.15 offset 20000 (0→69320); иконки 16/16; lint 0/0; `scripts/build_shorts09.py` |
| 2026-09-27 | Шортс_09 **v2** «$500 в месяц за CRM» (обновлённый сценарий) | **73** | тот же `.txt` (обновлён) | 11 | TTS ~70с; валютa $; +слайд «первый месяц красиво»; BGM `bgm` (0→70000); иконки 17/17; lint 0/0 |
| 2026-09-27 | Шортс_10 «Почему кастомный код дешевле nocode» | **74** | `it2b/…/Месяц_1/Шортс_10…txt` | 11 | TTS 60.9с; валютa $; StatsBarChart (шаг ≥800мс); λ `lucide:gauge`; BGM `bgm` 0.15 offset 20000 (0→61880); иконки 14/14; lint 0/0; `scripts/build_shorts10.py` |
| 2026-09-27 | **Длинное_04** «Как хаос в данных убивает продажи» | **75** | `it2b/…/Месяц_1/Длинное_04…md` | 48 | TTS 313.5с; 7 блоков; BGM `bgm` **3 клипа** (0→314494); иконки 51/51; lint 0/0; `build_long04.py` + `build_long04_slides.py`; парсер: +фильтр метки `[ГОЛОС КЛИЕНТА]` и `---` |
| 2026-09-27 | Шортс_11 «Клиент ушёл из-за формы на 10 секунд» | **76** | `it2b/…/Месяц_1/Шортс_11…txt` | 11 | TTS 65.8с; валютa $; BGM `bgm` 0.15 offset 20000 (0→65760); иконки 19/19; lint 0/0; `scripts/build_shorts11.py` |
| 2026-09-27 | Шортс_12 «Данные клиентов в WhatsApp» | **77** | `it2b/…/Месяц_1/Шортс_12…txt` | 11 | TTS 62.8с; BGM `bgm` 0.15 offset 20000 (0→62760); иконки 18/18; lint 0/0; `scripts/build_shorts12.py` |
| 2026-09-27 | Шортс_13 «30% заявок приходит ночью» | **78** | `it2b/…/Месяц_1/Шортс_13…txt` | 13 | TTS 67.5с; BGM `bgm` 0.15 offset 20000 (0→67480); иконки 23/23; lint 0/0; `scripts/build_shorts13.py`; в HOOK и PAYOFF добавлены подслайды (были >7с) |
| 2026-09-27 | **Длинное_05** «Кейс: автоматизация ночных заявок» | **79** | `it2b/…/Месяц_2/Длинное_05…md` | 46 | TTS 284.4с; 7 блоков; BGM `bgm` 2 клипа (0→285366); lint 0/0; иконки проверены; `build_long05.py` + `build_long05_slides.py` |
| 2026-09-27 | Шортс_14 «Утренний созвон с остывшим клиентом» | **80** | `it2b/…/Месяц_2/Шортс_14…txt` | 11 | TTS ~71.5с; BGM `bgm` 0.15 offset 20000 (0→72160); lint 0/0; `scripts/build_shorts14.py` |
| 2026-09-27 | Шортс_15 «ИИ квалифицирует клиента лучше стажёра» | **81** | `it2b/…/Месяц_2/Шортс_15…txt` | 11 | TTS ~81.5с; BGM `bgm` 0.15 offset 20000 (0→82040); lint 0/0; `scripts/build_shorts15.py`; λ `heroicons:user-check`→`lucide:user-check` |
| 2026-09-27 | Шортс_16 «Ошибка: пытаться закрыть сделку ночью» | **82** | `it2b/…/Месяц_2/Шортс_16…txt` | 11 | TTS ~74с; BGM `bgm` 0.15 offset 20000 (0→74480); lint 0/0; `scripts/build_shorts16.py`; ⚠️ префикс `s16_` занят p16 → взял `sh16_` |
| 2026-09-27 | Шортс_15 **v2** «Менеджер упустил оптовика на $30 000» (новый сценарий, VO/ЭКРАН, 14 строк) | **83** | `it2b/…/Месяц_2/Шортс_15…txt` | 14 | По-строчная озвучка (1 TTS на строку), 40.4с; BGM `bgm` 0.15 (0→41440); lint 0/0; `scripts/build_shorts15b.py`; ⚠️ ретрай TTS при 500 |
| 2026-09-27 | **Длинное_06** «MVP за несколько недель» (6 глав → 7 блоков) | **84** | `it2b/…/Месяц_2/Длинное_06…txt` | 44 | TTS 258.2с; 7 блоков; BGM `bgm` 2 клипа (0→259209); иконки 42/42; lint 0/0; `build_long06.py` + `build_long06_slides.py` |

