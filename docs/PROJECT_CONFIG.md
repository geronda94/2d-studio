# PROJECT_CONFIG.md — Конфиг проекта (Brand Kit)

Проектный уровень настройки (`projects.config`, JSON): бренд-ассеты, контакты,
дефолты компонентов, голос и фон. Резолвится в презентацию/слайд, чтобы не
дублировать данные в каждом payload/презентации.

## Схема

```json
{
  "brand":    { "name": "IT2B", "logo": "/media/logo.png", "qr_code": "/media/qr.png",
                "qr_data": "https://t.me/it00101" },
  "contacts": { "telegram": "@it00101", "site": "https://it2b.top",
                "email": "hi@it2b.top", "phone": "+49...",
                "whatsapp": "...", "instagram": "...", "youtube": "...", "linkedin": "..." },
  "defaults": { "OutroSlide": { "headline": "Подпишись" },
                "ChatMockupSlide": { "bot_name": "AI-агент", "bot_avatar": "" } },
  "voice":    { "voice": "Charon", "temperature": 0.8, "style": "...", "pace": "...", "tone": "..." },
  "audio":    { "bgm": "/media/bgm.mp3", "volume": 0.15 }
}
```

## Резолв

- `GET /presentations/{id}/config` — конфиг проекта презентации.
- `MainPresentation` мёржит `defaults[<Component>]` **под** payload слайда.
  Пустые значения payload (`""`/`null`) НЕ перекрывают дефолт.
- `OutroSlide`: `logo` ← `brand.logo`; `qr_code` ← `brand.qr_code`, а если пусто —
  авто-QR `GET /projects/{id}/qr.svg` из `brand.qr_data` / `contacts.telegram|site`;
  `handle` ← `contacts.telegram`.
- `voice`/`audio` — дефолты для AI-озвучки и фоновой музыки.

## Статус

1. **Auto-QR — DONE.** `segno==1.6.6`; `GET /projects/{id}/qr.svg` (публичный, кэш 1ч),
   data = `brand.qr_data` → `contacts.telegram` (t.me) → `contacts.site`. Фронт подставляет
   `/api/projects/{id}/qr.svg` в OutroSlide, если `brand.qr_code` не задан.
2. **Соцсети — DONE.** `contacts.{whatsapp,instagram,youtube,linkedin}` + UI, доступны в defaults/AI.
3. **Голос — DONE (фронт).** `voice.*` → дефолты `AIVoiceModal` (`:defaults`).
4. **BGM — DONE.** `audio.bgm`/`volume` → при `POST /presentations/` без таймлайна
   сейвим трек `bgm` (длительность через ffprobe).
5. **UI — DONE.** Секция «Бренд проекта»: бренд/контакты/соцсети/голос/BGM + JSON defaults.

3. **Голос — DONE (фронт + бэк-фолбэк).** `voice.*` → дефолты `AIVoiceModal`; на бэке
   `generate-speech` при **незаданных** полях берёт `config.voice` (приоритет: запрос →
   config → встроенный дефолт). ⚠️ Пайплайн (`generate_short.py`, `build_long02.py`)
   шлёт `voice`/`temperature` явно, поэтому конфиг проекта ими пока НЕ используется —
   для этого нужно убрать явные параметры в скриптах (LOCKED, решение за владельцем).
6. **Force-empty — DONE.** Значение `__none__` в поле payload принудительно отключает
   бренд-дефолт для этого слайда (поле рендерится пустым). Подсказка в редакторе.

## Тесты

Логика вынесена в `backend/brand_config.py` (без FastAPI/БД) и покрыта юнит-тестами:

```bash
docker compose exec backend python -m unittest backend.tests.test_brand_config -v
```

Покрыто: `public_config` (скрытие email/phone/voice/audio), `merge_config`
(секционный merge, лимит размера, тип), `local_media_path` (схемы/существование),
`probe_duration_ms` (парсинг/кэш/ошибка), `seed_bgm_from_config` (пропуск битого файла).

## Merge и сентинел

- `PUT /projects/{id}/config` — **рекурсивный merge** секций `brand/contacts/voice/audio/defaults`
  (частичное обновление сохраняет соседние поля; `null` удаляет ключ). Прочие секции заменяются.
- `"__none__"` в поле payload слайда — принудительно отключает бренд-дефолт для этого поля
  (только для скалярных значений).

## Инварианты

Только `ADD COLUMN IF NOT EXISTS`; payload слайда приоритетнее дефолтов;
запись конфига — владелец (`/projects/*` mutation).
