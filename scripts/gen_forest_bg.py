"""Уютный SVG-фон деревни: раскрывает <use>-ёлки PostMaker в плоские полигоны.

Источник композиции: Derevnya_Final_Deliverables/Derevnya_Deliverables/PostMaker.html
(дальний + средний лес, холм-основание). Без village/campfire — фон не должен
спорить с контентом слайда.
"""

TREE1 = ["0,0 -15,50 15,50", "0,25 -20,90 20,90", "0,50 -25,140 25,140"]
TREE2 = ["0,0 -20,70 20,70", "0,30 -25,110 25,110", "0,60 -30,170 30,170"]

FAR = [
    ("t1", 50, 200, 1.6), ("t2", 150, 150, 2.1), ("t1", 280, 120, 2.5),
    ("t2", 400, 180, 1.8), ("t1", 550, 100, 2.8), ("t2", 700, 140, 2.2),
    ("t1", 850, 90, 3.0), ("t2", 1000, 160, 1.9), ("t1", 1150, 130, 2.4),
    ("t2", 1300, 110, 2.6), ("t1", 1420, 180, 1.7),
]
MID = [
    ("t2", 20, 280, 1.4), ("t1", 110, 240, 1.8), ("t2", 220, 300, 1.2),
    ("t1", 340, 220, 2.0), ("t2", 480, 260, 1.5), ("t1", 620, 210, 2.1),
    ("t2", 780, 250, 1.6), ("t1", 900, 230, 1.9), ("t2", 1050, 270, 1.4),
    ("t1", 1200, 230, 1.9), ("t2", 1350, 290, 1.3),
]


def _band(placements, color, opacity):
    # Заливка, не обводка: контурные треугольники на крупном масштабе
    # выглядят ломаными; сплошные силуэты читаются как лес.
    parts = [f"<g fill='{color}' opacity='{opacity}'>"]
    for kind, x, y, s in placements:
        for pts in TREE1 if kind == "t1" else TREE2:
            parts.append(
                f"<polygon points='{pts}' transform='translate({x},{y}) scale({s})'/>"
            )
    parts.append("</g>")
    return "".join(parts)


def _teepee(x, y, s):
    return (
        f"<g transform='translate({x},{y}) scale({s})'>"
        "<path d='M0,0 Q-25,40 -45,100 L45,100 Q25,40 0,0 Z' fill='#8B7355'/>"
        "<path d='M0,0 Q-25,40 -45,100 L0,100 Z' fill='#6E5A42'/>"
        "<path d='M0,35 L-15,100 L15,100 Z' fill='#2A2318'/>"
        "<line x1='0' y1='5' x2='-15' y2='-20' stroke='#2C211A' stroke-width='4' stroke-linecap='round'/>"
        "<line x1='0' y1='5' x2='2' y2='-25' stroke='#2C211A' stroke-width='3' stroke-linecap='round'/>"
        "</g>"
    )


def _campfire(x, y, s):
    return (
        f"<g transform='translate({x},{y}) scale({s})'>"
        "<path d='M-15,10 L15,25 M-15,25 L15,10' stroke='#2C211A'"
        " stroke-width='4' stroke-linecap='round'/>"
        "<path fill='#D87B22' d='M0,-10 Q8,5 12,15 Q15,25 0,25 Q-15,25 -12,15 Q-8,5 0,-10 Z'/>"
        "<path fill='#FFC107' d='M0,2 Q6,8 8,16 Q9,23 0,23 Q-9,23 -8,16 Q-6,8 0,2 Z'/>"
        "</g>"
    )


def _flowers():
    spots = [(150, 480), (250, 465), (450, 455), (580, 470), (850, 460),
             (950, 485), (1100, 450), (1250, 475), (1380, 465)]
    return "".join(
        f"<circle cx='{x}' cy='{y}' r='2.5' fill='#D87B22' opacity='0.7'/>"
        for x, y in spots
    )


def build_forest_svg():
    # Full-bleed: композиция на всю ширину канвы БЕЗ scale (scale(0.5) сжимал
    # лес в левую половину — см. итерацию 6). Кроны целы за счёт viewBox с
    # запасом сверху: самая высокая крона y=110, viewBox начинается с y=40.
    village = (
        "<g opacity='0.85'>"
        + _teepee(480, 360, 0.9)
        + _teepee(590, 375, 0.75)
        + _teepee(850, 375, 0.75)
        + _teepee(960, 360, 0.9)
        + _campfire(720, 420, 1.2)
        + "</g>"
    )
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 40 1440 460'>"
        + _band(FAR, "#4A6038", 0.15)
        + _band(MID, "#4A6038", 0.32)
        + "<path d='M-100,500 L-100,450 Q720,400 1540,450 L1540,500 Z'"
          " fill='#7d9674' opacity='0.55'/>"
        + village
        + _flowers()
        + "</svg>"
    )


def build_forest_uri():
    return (
        'url("data:image/svg+xml,'
        + build_forest_svg().replace("#", "%23")
        + '") bottom center / 100% auto no-repeat'
    )


FOREST_URI = build_forest_uri()
