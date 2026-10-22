# Генерация презентаций из сценариев — Инструкция для ИИ-агента

## Обзор пайплайна

```
Сценарий (.md) + Текст озвучки (.txt)
    │
    ▼
┌─────────────────────┐
│ 1. PARSE SCENARIO   │  Извлечь секции: [HOOK], [МОСТ], [PROOF], [PAYOFF], [HOOK OUT]
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 2. CREATE PRES      │  POST /presentations/ + назначить папку
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. GENERATE TTS     │  POST /ai/presentations/{id}/generate-speech
│    (по секции)      │  → WAV файл + MediaFile запись
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 4. GET DURATIONS    │  GET /ai/audio-duration?file_path=...
│    (ffprobe)        │  → duration_ms для каждой секции
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 5. WHISPER TRANS    │  POST /ai/transcribe
│    (word timestamps)│  → word-level timestamps (начало каждого слова)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 6. CALC BOUNDARIES  │  Сопоставить word timestamps с boundaries секций
│    (section splits) │  → absolute start/end для каждой секции
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 7. BUILD TIMELINE   │  audio_timeline: voice clips + BGM на 15%
│    + SAVE TO PRES   │  PUT /presentations/{id}
└─────────┬───────────┘
          ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. CREATE SLIDES                                            │
│  ⚠️ ОБЯЗАТЕЛЬНО: перед заполнением payload получить         │
│     example + payload_schema через GET /components/         │
│     Не выдумывать структуру данных — использовать пример!   │
│  → POST /presentations/{id}/slides (по одному)             │
└─────────────────────────────────────────────────────────────┘
          ▼
┌─────────────────────┐
│ 9. VERIFY           │  http://localhost:5174/p/{id}
└─────────────────────┘
```

---

## Этап 1: Подготовка

### 1.1 Найти сценарий
```
Путь: /home/goga/Рабочий стол/Projects/YouTube Channel/готовые_сценарии/
  ├── Месяц_1/
  │   ├── Длинное_01/    — длинные видео
  │   ├── Шортс_01/      — шортсы (5 штук в месяце)
  │   ├── ...
  └── Тексты_под_озвучку/
      ├── Длинное_01.txt  — чистый текст для TTS
      ├── Шортс_01.txt
      ├── ...
```

### 1.2 Прочитать сценарий
Формат `.md`:
```markdown
### [СЕКЦИЯ] start–end
Текст озвучки...

[ВИЗУАЛ: описание]
```

**Секции шортса** (5 штук):
- `[HOOK]` 0–3с — зацепка
- `[МОСТ]` 3–8с — связка с проблемой
- `[PROOF]` 8–45с — основной разбор (самая длинная)
- `[PAYOFF]` 45–55с — вывод/инсайт
- `[HOOK OUT]` 55–60с — CTA

### 1.3 Определить папку
```
Проект IT2B → Папка "Шортсы" (folder_id=2)
Проект IT2B → Папка "Длинные" (folder_id=1)
```

---

## Этап 2: Генерация TTS

### API
```
POST http://localhost:8001/ai/presentations/{presentation_id}/generate-speech

{
  "text": "Текст секции...",
  "voice": "Charon",
  "audio_profile": "A confident and dynamic tech expert with a deep, resonant voice.",
  "style": "Engaging and professional.",
  "pace": "Fast, continuous, and energetic, with absolutely no long pauses.",
  "tone": "Authoritative, convincing, and lively.",
  "scene": "A high-end tech YouTube channel for IT2B.",
  "temperature": 0.8,
  "batch_id": "short_2_1234567890"
}
```

### Голоса
| Имя | Характер |
|-----|----------|
| Charon | Глубокий, уверенный (основной) |
| Aoede | Женский, профессиональный |
| Fenrir | Молодой, энергичный |
| Kore | Мягкий, дружелюбный |
| Puck | Динамичный, технический |

### Важно
- Каждая секция → отдельный TTS-вызов
- `batch_id` общий для всех клипов презентации
- TTS возвращает MediaFile с `file_path` (напр. `/media/ai_voice_xxx.wav`)

---

## Этап 3: Длительность аудио

### API
```
GET http://localhost:8001/ai/audio-duration?file_path=/media/ai_voice_xxx.wav

→ { "file_path": "...", "duration_ms": 6000.0 }
```

---

## Этап 4: Whisper транскрипция

### API
```
POST http://localhost:8001/ai/transcribe

{
  "file_path": "/media/ai_voice_xxx.wav",
  "language": "ru",
  "model_size": "base"
}

→ {
    "text": "Полный текст...",
    "words": [
      {"word": "Смотри,", "start": 0.0, "end": 600.0},
      {"word": "как", "start": 680.0, "end": 740.0},
      ...
    ],
    "segments": [...]
  }
```

**Для русского языка**: `base` модель — оптимальный баланс.

### Зачем word-level timestamps
- Позволяет точно определить где заканчивается каждая мысль
- Помогает расставить слайды по границам фраз, а не по среднему

---

## Этап 5: Расчёт границ секций

### Формула
```
section[i].start_time = sum(durations[0..i-1]) + (i * 200ms gap)
section[i].end_time = section[i].start_time + duration[i]
```

---

## Этап 6: Audio Timeline

### Структура (4 трека — ВСЕГДА)
```json
{
  "tracks": [
    {
      "id": "main",
      "type": "voiceover",
      "clips": [
        {
          "id": "ai_0",
          "name": "ai_voice_xxx.wav",
          "src": "/media/ai_voice_xxx.wav",
          "start_time": 0,
          "end_time": 6000,
          "media_offset": 0,
          "volume": 1.0,
          "type": "ai_voice"
        }
      ]
    },
    {
      "id": "overlay",
      "type": "voiceover",
      "clips": [
        {
          "id": "bgm_0",
          "name": "Automated_Horizon.mp3",
          "src": "/media/94372fbfcdca4683ba46d34ae1fd78a5.mp3",
          "start_time": 0,
          "end_time": 62000,
          "volume": 0.15,
          "type": "audio"
        }
      ]
    },
    {"id": "bgm", "type": "bgm", "clips": []},
    {"id": "sfx", "type": "sfx", "clips": []}
  ]
}
```

### BGM файлы IT2B
| Файл | Путь | Назначение |
|------|------|-----------|
| Automated_Horizon.mp3 | `/media/94372fbfcdca4683ba46d34ae1fd78a5.mp3` | Техно/бизнес (основной) |
| Structured_Intent.mp3 | `/media/e1ecd277d28e4e13b9bf3b7305d34dd5.mp3` | Спокойный |

### Сохранение timeline
```
PUT http://localhost:8001/presentations/{id}
{ "audio_timeline": { ... } }
```

---

## Этап 7: Создание слайдов (КЛЮЧЕВОЙ)

### ⚠️ ПРАВИЛО №1: ВСЕГДА получай example перед заполнением

```bash
# 1. Получить все компоненты с example и payload_schema
curl -s "http://localhost:8001/components/" | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    if c['slug'] == 'ТВОЙ_КОМПОНЕНТ':
        print('example:', json.dumps(c['example'], ensure_ascii=False))
        print('schema:', json.dumps(c['payload_schema'], ensure_ascii=False))
"
```

**НИКОГДА не выдумывай payload.** Всегда опирайся на `example` + `payload_schema`.

### API создания слайда
```
POST http://localhost:8001/presentations/{id}/slides

{
  "slide_id": "s2_hook_1",
  "component": "ChatMockupSlide",
  "start_time": 0,
  "order_index": 0,
  "title": "ИИ-агент пообещал скидку",
  "subtitle": "Клиенту — которой нет в природе",
  "layout": "col",
  "data": {
    "payload": {
      ... (из example компонента)
    }
  }
}
```

### slug компонента = ключ в реестре
Компонент в слайде `slide.component` **точно** должен совпадать с ключом в `componentsRegistry.js`:
- ✅ `BrowserMockup` (правильно)
- ❌ `BrowserMockupSlide` (НЕПРАВИЛЬНО — не в реестре, экран будет пустым)

### Правила
1. **Длительность слайда: шортсы 3–6с, длинные 4–10с, оптимум 5–7с.** Дольше 7с — только в крайних случаях (много инфы / нужно задержаться на слайде)
2. **Минимальная дистанция между стартами соседних слайдов — 2000 мс. Без исключений.** Слайды строго не налезают друг на друга
3. **Без повторов** компонента в 4 ближайших слайдах
4. **Привязка к контенту** — компонент отражает суть секции
5. **Краткость** — текст на слайде ≠ текст озвучки (синонимы, сокращения)
6. **Разряженные тайминги айтемов** — шаг между соседними `start_time` в payload ≥ 800–1000 мс (плотная набивка = рваный эффект). Кроме `InteractiveArchitecture` — у неё своя механика (см. ниже)
7. **Финальный технический слайд** — `EndMarkerSlide` всегда последний, ровно на конце озвучки (трек 1 `main`/`voiceover`, НЕ BGM). Если озвучки нет — старт последнего слайда + его длительность
8. **Валидация**: `POST /components/{slug}/validate` с `{"payload": {...}}`

### Маппинг секция → компонент

| Тип секции | Подходящие компоненты | Пример |
|------------|----------------------|--------|
| HOOK (зацепка) | `ChatMockupSlide`, `BrowserMockup`, `ReceiptCard` | Показать фейковый ответ бота |
| МОСТ (проблема) | `AnimatedStatsSlide`, `InfographicCards`, `NetworkWaterfall` | Цифры потерь |
| PROOF (разбор) | `ArchitectureDiagram`, `ComparisonTable`, `CodeExplain`, `InteractiveArchitecture`, `ProcessFunnel`, `StatsBarChart`, `PremiumChecklist` | Схемы, таблицы, чеклисты |
| PAYOFF (вывод) | `MetricScales`, `InfographicCards`, `ProcessFunnel` | Сравнение до/после |
| HOOK OUT (CTA) | `OutroSlide` | Контакт, QR |

---

## КРИТИЧЕСКИЕ ПРАВИЛА ПО КОМПОНЕНТАМ

> Каждое правило ниже — результат реальных ошибок. Нарушение = слайд не рендерится или выглядит сломанно.

### BrowserMockup
- **slug = `BrowserMockup`** (не `BrowserMockupSlide`!)
- `type: "html"` — content = HTML-строка (надёжнее image URL)
- `type: "image"` — content = URL картинки (может не грузиться из-за CORS)
- Пример: `{"items": [{"id": "b1", "url": "example.com", "type": "html", "content": "<div>...</div>", "scroll": false, "start_time": 0}]}`

### InteractiveArchitecture
- **НЕ задавай `x`/`y` в нодах** — компонент сам раскидывает через топологический BFS
- **`start_time` ТОЛЬКО у ОДНОГО ноды** (фокус камеры). Остальные ноды БЕЗ `start_time` — появляются автоматически
- Если `start_time` у всех нод → хаотичная анимация (колбасит)
- Правила плотности айтемов на этот компонент НЕ распространяются вообще (своя механика: фокус камеры по единственному `start_time`)
- Пример: `{"nodes": [{"id": "n1", "label": "X", "start_time": 0}, {"id": "n2", "label": "Y"}, {"id": "n3", "label": "Z"}]}`

### ArchitectureDiagram
- `color` — `chart-N` (chart-1..chart-4) или `color-primary` (не hex)
- `start_time` ТОЛЬКО у ОДНОГО ноды для анимации фокуса
- `show_data_flow: true` для отрисовки связей

### AnimatedStatsSlide
- `value` — **INTEGER** (не строка), избегай 0 — неинформативно
- Каждая метрика — **ОБЯЗАТЕЛЬНО РАЗНЫЙ** `color` (hex) и `icon` (lucide:...)
- Пример: `{"stats": [{"value": 100, "label": "X", "color": "#EF4444", "icon": "lucide:trending-down", "start_time": 0}]}`

### InfographicCards
- `value` — **КОРОТКИЙ** текст (1 слово/символ: «0%», «100%», «!»), иначе не влезет в карточку (text-4xl)
- Каждый item — **ОБЯЗАТЕЛЬНО РАЗНЫЙ** `color` (hex) и `icon` (heroicons:...)
- `id` — integer (1, 2, 3...)
- Пример: `{"items": [{"id": 1, "label": "X", "value": "0%", "trend": "Риск", "icon": "heroicons:exclamation-triangle", "color": "#EF4444", "start_time": 300}]}`

### PremiumChecklist
- Каждый item — **ОБЯЗАТЕЛЬНО РАЗНЫЙ** `icon` и `color` (brand-blue, brand-amber, brand-purple, brand-green, brand-red)
- Пример: `{"items": [{"label": "X", "desc": "Описание", "icon": "heroicons:document-text", "color": "brand-blue", "start_time": 300}]}`

### ProcessFunnel
- `layout` — **`horizontal`** (по умолчанию, НЕ vertical)
- `label` — короткое слово/фраза **БЕЗ числа** (count показан крупно сам)
- Максимум 4 items для horizontal
- Пример: `{"layout": "horizontal", "steps": [{"label": "Входящих", "count": 100, "icon": "heroicons:chat-bubble-left-right", "start_time": 300, "color": "#10B981"}]}`

### MetricScales
- `percentage` — integer 0–100 (НЕ `value`/`max_value`)
- `color` — gradient строка: `"linear-gradient(to right, #38BDF8, #60A5FA)"`
- `id` — integer
- Пример: `{"metrics": [{"id": 1, "label": "X", "percentage": 87, "color": "linear-gradient(to right, #38BDF8, #60A5FA)", "start_time": 0}]}`

### ReceiptCard
- `total_text` — **СЛОВО** («ИТОГО», «ПОТЕРЯНО», «TOTAL DUE»), не число
- `items[].name` + `items[].price` (integer)
- `total_start_time` — время появления итога
- Пример: `{"title": "CORPORATE CARD", "total_text": "ИТОГО", "currency": "€", "items": [{"name": "X", "price": 15000, "start_time": 300}]}`

### ComparisonTable
- Каждый item — **ОБЯЗАТЕЛЬНО** с полем `id` (строка: «r1», «r2»...)
- `values`: `[true/false]` или строки («< 1 сек»)
- `headers[0]` = `«»` (пустая — заголовок колонки признаков)
- Пример: `{"headers": ["", "Мой подход", "Другие"], "items": [{"id": "r1", "label": "Функция", "values": [true, false], "start_time": 0}]}`

### ChatMockupSlide
- Поле `role` (не `sender`!): `"user"` / `"assistant"`
- `bot_name`, `bot_subtitle`, `bot_avatar` — верхняя часть чата
- Пример: `{"bot_name": "AI Bot", "bot_subtitle": "bot", "bot_avatar": "AI", "messages": [{"role": "user", "text": "Вопрос", "start_time": 0}]}`

### NetworkWaterfall
- `start_ms`/`duration_ms` (не `start_pct`/`duration_pct`!)
- Каждый request: `name`, `method`, `type`, `start_ms`, `duration_ms`, `start_time`, `color`, `icon`
- `total_ms` — общая длительность

---

## Известные pitfalls

| Проблема | Решение |
|----------|---------|
| Слайд пустой (нет контента) | Проверь `slide.component` — должен точно совпадать с ключом в `componentsRegistry.js` |
| PUT `/presentations/slides/{id}` возвращает 404 | Используй `localhost:8000` (backend) изнутри контейнера, `localhost:8001` (proxy) с хоста |
| Payload не сохраняется | PUT требует ВСЕ обязательные поля: `slide_id`, `component`, `start_time`, `order_index`, `title`, `subtitle`, `layout`, `data` |
| `AnimatedStatsSlide` value=0 | Неинформативно, используй положительные числа |
| InteractiveArchitecture хаотичная анимация | `start_time` ТОЛЬКО у одной ноды |
| ProcessFunnel вертикальный | `layout: "horizontal"` |
| InfographicCards текст не влезает | `value` = 1 слово/символ |
| PremiumChecklist одинаковые иконки | Каждый item = РАЗНЫЙ icon + color |
| BrowserMockup пустой | slug = `BrowserMockup`, `type: "html"` |

---

## Быстрый старт (для нового шортса)

```bash
# 1. Создать презентацию + TTS + timeline
docker compose exec backend python scripts/generate_short.py --short N

# 2. Переозвучить существующую презентацию из .txt файла
docker compose exec backend python scripts/revoice_from_file.py --pres-id N --file scripts/_inbox/text.txt

# 3. Транскрибировать PROOF (самую длинную секцию)
curl -X POST http://localhost:8001/ai/transcribe \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/media/ai_voice_XXX.wav","language":"ru","model_size":"base"}'

# 3. Получить example нужных компонентов
curl -s "http://localhost:8001/components/" | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    if c['slug'] in ['ChatMockupSlide','AnimatedStatsSlide','...']:
        print(f\"=== {c['slug']} ===\")
        print(json.dumps(c['example'], ensure_ascii=False))
"

# 4. Создать слайды через API (POST /presentations/{id}/slides)
#    Каждый payload = из example компонента, адаптированный под контент

# 5. Проверить
open http://localhost:5174/p/{id}
```
