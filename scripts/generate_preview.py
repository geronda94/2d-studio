"""
Матрица превью (P5): презентации «Регрессия стилей» — все компоненты × 3 варианта.

Для каждого варианта (tech/classic/derevnya): преза в черновиках соответствующего
проекта (токены тянутся через папку), по слайду на компонент (default_payload +
variant), шаг 5с, в конце EndMarkerSlide. Идемпотентно: презы с тем же title
пересоздаются. Плюс назначается style_preset (без лока).

Визуальный чеклист — docs/STYLE_FLEX_PLAN.md P5.

Запуск: docker compose exec backend python scripts/generate_preview.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models


MATRIX = [
    # (variant, folder_id, preset_slug)
    ("tech", 3, "it2b-tech"),
    ("classic", 5, "history-classic"),
    ("derevnya", 6, "derevnya-eco"),
]

STEP_MS = 5000


def run():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        comps = db.query(models.Component).order_by(models.Component.id).all()
        print(f"Компонентов: {len(comps)}")
        for variant, folder_id, preset_slug in MATRIX:
            folder = db.query(models.Folder).filter(models.Folder.id == folder_id).first()
            if not folder:
                print(f"Нет папки id={folder_id} — пропуск {variant}")
                continue
            title = f"Regression: {variant}"
            # идемпотентность: сносим прошлый прогон
            for old in db.query(models.Presentation).filter(
                    models.Presentation.title == title).all():
                for f in list(old.folders):
                    if old in f.presentations:
                        f.presentations.remove(old)
                db.delete(old)
            db.flush()

            pres = models.Presentation(title=title, variant=variant)
            preset = db.query(models.StylePreset).filter(
                models.StylePreset.slug == preset_slug).first()
            if preset:
                pres.style_preset = preset.slug
            db.add(pres)
            db.flush()
            folder.presentations.append(pres)

            order = 0
            for comp in comps:
                if comp.slug == "EndMarkerSlide":
                    continue
                payload = dict(comp.default_payload or {})
                payload["variant"] = variant
                s = models.Slide(
                    presentation_id=pres.id,
                    slide_id=f"regression-{variant}-{comp.slug}",
                    component=comp.slug,
                    start_time=order * STEP_MS,
                    title=comp.title,
                    order_index=order,
                )
                db.add(s)
                db.flush()
                db.add(models.SlideData(slide_id=s.id, payload=payload))
                order += 1
            # маркер конца: старт последнего + окно
            end = models.Slide(
                presentation_id=pres.id,
                slide_id=f"regression-{variant}-end",
                component="EndMarkerSlide",
                start_time=order * STEP_MS,
                order_index=order,
            )
            db.add(end)
            db.commit()
            print(f"{title}: id={pres.id} (/p/{pres.id}), слайдов {order + 1}, пресет {preset_slug}")
        print("Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
