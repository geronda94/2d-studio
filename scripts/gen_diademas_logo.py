"""Логотип Diademas: перекраска серафима из прототипа Church под темы проекта.

Источник — scripts/assets/logo-diadems.svg (серафим, заливка #c3a557 = золото).
Готовит два ассета в backend/media/ (отдаётся как /media/<file>):
  - diademas_logo.svg       — дневная тема: кристальный градиент леса
  - diademas_logo_gold.svg  — тёмная тема (запас): золотой градиент

Запуск: docker compose exec backend python scripts/gen_diademas_logo.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "assets", "logo-diadems.svg")
MEDIA = os.path.join(ROOT, "backend", "media")

GOLD = "#c3a557"

DAY_GRADIENT = (
    "<defs><linearGradient id='diadLogo' x1='0%' y1='0%' x2='100%' y2='0%'>"
    "<stop offset='0%' stop-color='#1B4332'/>"
    "<stop offset='50%' stop-color='#99D98C'/>"
    "<stop offset='100%' stop-color='#2D6A4F'/>"
    "</linearGradient></defs>"
)
NIGHT_GRADIENT = (
    "<defs><linearGradient id='diadLogo' x1='0%' y1='0%' x2='100%' y2='0%'>"
    "<stop offset='0%' stop-color='#C7A557'/>"
    "<stop offset='50%' stop-color='#FFF5DC'/>"
    "<stop offset='100%' stop-color='#C7A557'/>"
    "</linearGradient></defs>"
)


def build(variant: str) -> str:
    with open(SRC, "r", encoding="utf-8") as f:
        svg = f.read()
    defs = DAY_GRADIENT if variant == "day" else NIGHT_GRADIENT
    # Градиент вставляем сразу после открывающего тега <svg ...>
    head_end = svg.index(">") + 1
    svg = svg[:head_end] + defs + svg[head_end:]
    # Перекрашиваем основной силуэт серафима
    svg = svg.replace(f'fill="{GOLD}"', "fill='url(#diadLogo)'")
    return svg


def run():
    os.makedirs(MEDIA, exist_ok=True)
    out = {
        "diademas_logo.svg": build("day"),
        "diademas_logo_gold.svg": build("night"),
    }
    for name, data in out.items():
        path = os.path.join(MEDIA, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Записан {path} ({len(data)} bytes)")


if __name__ == "__main__":
    run()
