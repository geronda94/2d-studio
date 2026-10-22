# SceneEngine (2d-studio)

Форк движка презентаций, перестроенный под **2D-сцены**: окружения, физические
объекты, механизмы и ключи на локальном таймлайне. Не набор готовых слайдов.

- Frontend: `http://localhost:5175`
- Backend: `http://localhost:8002`
- Postgres: `localhost:5436`
- Демо: `http://localhost:5175/p/1` (машина едет по лесной трассе)

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d
docker compose exec -T backend python scripts/seed_tokens.py
docker compose exec -T backend python scripts/seed_variants.py
docker compose exec -T backend python scripts/seed_presets.py
docker compose exec -T backend python scripts/seed_scene_demo.py
```

## Документация

- `docs/SCENES.md` — контракт сцены
- `docs/STATUS.md` — текущий этап
- `docs/ROADMAP_2D.md` — вектор развития
- `docs/PROCESSES.md` — контент-пайплайн
- `docs/DEV.md` — порты
- `docs/SERVER.md` — сервер
- `AGENTS.md` — правила для ИИ

## Идея

```
Environment + Objects + Mechanisms + Cues = Scene
```

`window.scene.seek(t)` — единственный источник времени. Детерминированно
в браузере, редакторе и рендере.
