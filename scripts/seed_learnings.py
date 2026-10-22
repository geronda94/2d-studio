#!/usr/bin/env python3
"""Seed the scene learning registry with known errors/fixes.

Run inside backend:
    python scripts/seed_learnings.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models

LEARNINGS = [
    {
        "category": "visuals",
        "symptom": "Персонажи выглядят как детские SVG-блоки",
        "cause": "Слишком простая геометрия, нет деталей и рига",
        "fix": "Open Peeps (CC0) как плейсхолдер + план Rive/DragonBones",
        "rule": "Не рисовать персонажей из кругов и палок; использовать готовую библиотеку или риг-движок",
        "source": "human",
        "tags": ["characters", "quality"],
    },
    {
        "category": "visuals",
        "symptom": "Редактор сцены показывает пустой iframe",
        "cause": "Iframe не перезагружал srcdoc после асинхронной сборки",
        "fix": "Добавить :key на iframe и инкрементить при rebuild",
        "rule": "Большой srcdoc в модалке — пересоздавать iframe по key",
        "source": "human",
        "tags": ["editor", "iframe"],
    },
    {
        "category": "layout",
        "symptom": "Слайдеры слоя показывают 12%/18%, а объект стоит на 58%/40%",
        "cause": "Позиции заданы CSS-классами, а редактор читает только inline style",
        "fix": "Инжектить object_styles в inline style при сборке шаблона",
        "rule": "Позиции объектов, которые редактируются слайдерами, должны быть в inline style",
        "source": "human",
        "tags": ["editor", "layers"],
    },
    {
        "category": "visuals",
        "symptom": "Персонаж «висит» перед столом, а не сидит за ним",
        "cause": "Стол в слое мира ниже персонажей",
        "fix": "Передний слой стола в layer-overlay",
        "rule": "Для ток-шоу нужен foreground-слой стола поверх персонажей",
        "source": "human",
        "tags": ["studio", "composition"],
    },
    {
        "category": "visuals",
        "symptom": "Lower third перекрывает таймлайн",
        "cause": "Оба элемента внизу кадра",
        "fix": "Скрыть lower third в шаблоне таймлайна",
        "rule": "В шаблонах с нижней графикой отключать стандартный lower third",
        "source": "human",
        "tags": ["timeline", "lower-third"],
    },
    {
        "category": "process",
        "symptom": "ИИ-правило сразу попало в активную базу",
        "cause": "Не было статуса proposed",
        "fix": "source=ai → status=proposed; approve отдельным endpoint",
        "rule": "ИИ предлагает правила, человек утверждает",
        "source": "human",
        "tags": ["learnings", "governance"],
    },
    {
        "category": "layout",
        "symptom": "Cannot read properties of null (reading 'querySelector') in iframe",
        "cause": "Composed scene HTML was not wrapped in <div class=\"scene\">, so document.querySelector('.scene') returned null",
        "fix": "Wrap every composed scene in <div class=\"scene\"> in _compose()",
        "rule": "Любая собранная сцена обязана иметь корневой <div class=\"scene\">; JS сцены не должен падать при отсутствии root",
        "source": "human",
        "tags": ["runtime", "wrapper"],
    },
    {
        "category": "process",
        "symptom": "Seed updated the wrong scene / payload lost fields",
        "cause": "db.query(...).filter(component='__scene__').first() returned another scene",
        "fix": "Filter by stable slide_id, e.g. scene-demo-1; delete test scenes",
        "rule": "В сидах и миграциях искать сцену по slide_id, а не .first()",
        "source": "human",
        "tags": ["seed", "db"],
    },
    {
        "category": "visuals",
        "symptom": "Editor preview is black / transparent",
        "cause": "Theme variables live on .slides-container, editor is outside it; var(--bg-base) is empty",
        "fix": "Fallback to document.querySelector('.slides-container') and inject default theme vars into iframe",
        "rule": "SceneHost должен работать и вне .slides-container: всегда иметь дефолтные CSS-переменные",
        "source": "human",
        "tags": ["editor", "theme"],
    },
    {
        "category": "visuals",
        "symptom": "Editor chrome is light while player is dark",
        "cause": "Tailwind colors use --bg-base-rgb/--text-primary-rgb, not only --bg-base",
        "fix": "Add -rgb variables to editorTheme",
        "rule": "Для тёмного хрома редактора задавать и --*-rgb переменные",
        "source": "human",
        "tags": ["editor", "tailwind"],
    },
    {
        "category": "process",
        "symptom": "API /scene-library returns 404 after adding router",
        "cause": "Backend was not restarted (no --reload)",
        "fix": "docker compose restart backend and wait for Application startup complete",
        "rule": "После правок Python — рестарт backend и проверка curl",
        "source": "human",
        "tags": ["backend", "dev"],
    },
    {
        "category": "process",
        "symptom": "git push fails: src refspec main does not match",
        "cause": "git init created master",
        "fix": "git branch -M main && git push -u origin main",
        "rule": "В новом репозитории сразу проверять имя ветки",
        "source": "human",
        "tags": ["git"],
    },
    {
        "category": "process",
        "symptom": "Infrastructure/access notes could leak to a public repo",
        "cause": "Old docs/SERVER_ACCESS.md contained server host/paths",
        "fix": "Delete/redact before commit; keep generic docs/SERVER.md",
        "rule": "Перед push проверять staged files на .env/secret/server_access/id_rsa",
        "source": "human",
        "tags": ["security", "git"],
    },
    {
        "category": "visuals",
        "symptom": "view field did not reach the rendered scene",
        "cause": "normalizeScenePayload, SceneHost prop, runtime body class and payload were not all wired",
        "fix": "Pass view through DB/payload → SceneHost → buildSceneDoc → body class",
        "rule": "Новое поле сцены проверять во всей цепочке до CSS/JS",
        "source": "human",
        "tags": ["view", "runtime"],
    },
    {
        "category": "compatibility",
        "symptom": "Street lamp/skyscraper placed in an interior",
        "cause": "Objects had no domain/environment metadata",
        "fix": "Add ENV_META/OBJ_META + compatibility API + editor filter",
        "rule": "Объект можно ставить только в совместимый мир; несовместимость — предупреждение",
        "source": "human",
        "tags": ["classification"],
    },
    {
        "category": "process",
        "symptom": "Cues in editor did not affect the template scene",
        "cause": "Template JS used hardcoded cues and ignored window.__sceneCues",
        "fix": "Use window.__sceneCues when present, fallback to default cues",
        "rule": "Шаблон должен читать window.__sceneCues, иначе редактор ключей бесполезен",
        "source": "human",
        "tags": ["cues", "editor"],
    },
]


def run():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = 0
        for item in LEARNINGS:
            exists = db.query(models.SceneLearning).filter(
                models.SceneLearning.symptom == item["symptom"]
            ).first()
            if exists:
                continue
            db.add(models.SceneLearning(**item))
            created += 1
        db.commit()
        print(f"Learnings added: {created}, total: {len(LEARNINGS)}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
