"""Сцена Diademas (прототип Church/DIADEMAS): звёздное небо и облака.

Детерминированные SVG-фоны для токенов `bg-decorations` / `bg-overlay`:
  - STARFIELD_URI — тёмная тема (Midnight/Gold): звёзды + созвездие-диадема.
  - CLOUDS_URI    — светлая тема (Overcast/Forest): мягкие облака.
  - NOISE_URI     — общий мягкий шум (bg-overlay).
  - STAR_PATTERN_URI / DOT_PATTERN_URI — pattern-bg (мелкая текстура).

Анимации запрещены (§11 AGENTS): всё статично, без <animate>/infinite/rAF.
SVG-ассемблер — как в gen_forest_bg.py (url("data:image/svg+xml,...")).
"""


def _rng(seed):
    """Детерминированный ЛКГ (без random — одинаковый SVG на каждом прогоне)."""
    state = seed & 0x7FFFFFFF

    def nxt():
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF

    return nxt


W, H = 1600, 900


def _stars(count, rnd, gold_ratio=0.22):
    parts = []
    for _ in range(count):
        x = round(rnd() * W, 1)
        y = round(rnd() * H, 1)
        r = rnd()
        if r < 0.72:
            rad = round(0.3 + rnd() * 0.5, 2)
            op = round(0.18 + rnd() * 0.35, 2)
        elif r < 0.94:
            rad = round(0.6 + rnd() * 0.8, 2)
            op = round(0.35 + rnd() * 0.4, 2)
        else:
            rad = round(1.2 + rnd() * 1.0, 2)
            op = round(0.7 + rnd() * 0.3, 2)
        color = "#FFF5DC" if rnd() < gold_ratio else "#FFFFFF"
        parts.append(f"<circle cx='{x}' cy='{y}' r='{rad}' fill='{color}' opacity='{op}'/>")
    return "".join(parts)


def _glow_stars(rnd):
    """Крупные звёзды с ореолом (статичный radial-gradient)."""
    parts = []
    for i in range(5):
        x = round(180 + rnd() * (W - 360), 1)
        y = round(80 + rnd() * (H * 0.55), 1)
        r = round(2.2 + rnd() * 2.2, 2)
        parts.append(
            f"<circle cx='{x}' cy='{y}' r='{round(r * 6, 1)}' fill='url(#diadStarGlow)'/>"
            f"<circle cx='{x}' cy='{y}' r='{r}' fill='#FFF9E8'/>"
        )
    return "".join(parts)


def _comets():
    """Лёгкие статичные штрихи падающих звёзд."""
    data = [(1200, 120, 1020, 250), (430, 90, 250, 220)]
    parts = []
    for x1, y1, x2, y2 in data:
        parts.append(
            f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' "
            "stroke='url(#diadComet)' stroke-width='1.6' stroke-linecap='round'/>"
        )
    return "".join(parts)


def _crown_constellation():
    """Созвездие в форме диадемы (5 зубцов) в верхней части неба."""
    base_y = 250
    peaks = [(560, 150), (680, 196), (800, 118), (920, 196), (1040, 150)]
    valleys = [(620, 214), (740, 226), (860, 226), (980, 214)]

    nodes = []
    for x, y in peaks:
        nodes.append((x, y))
        nodes.append((x, y))
    # порядок обхода: пик, впадина, пик, ...
    path = [peaks[0], valleys[0], peaks[1], valleys[1], peaks[2],
            valleys[2], peaks[3], valleys[3], peaks[4]]

    pts = []
    for k, (x, y) in enumerate(path):
        pts.append(f"{x if k == 0 else 'L'}{'' if k == 0 else ' '}{x},{y}" if k else f"M{x},{y}")
    # проще собрать d вручную
    d = "M" + " L".join(f"{x},{y}" for x, y in path)
    d += f" M560,{base_y} L1040,{base_y}"

    lines = f"<path d='{d}' fill='none' stroke='#C7A557' stroke-width='1.3' opacity='0.42'/>"
    jewels = []
    for i, (x, y) in enumerate(peaks):
        big = i == 2
        jewels.append(
            f"<circle cx='{x}' cy='{y}' r='{3.4 if big else 2.2}' fill='#FFF5DC' opacity='0.85'/>"
            f"<circle cx='{x}' cy='{y}' r='{9 if big else 6}' fill='url(#diadStarGlow)'/>"
        )
    return lines + "".join(jewels)


def build_starfield_svg():
    rnd = _rng(20260920)
    defs = (
        "<defs>"
        "<radialGradient id='diadStarGlow'>"
        "<stop offset='0%' stop-color='#FFF5DC' stop-opacity='0.5'/>"
        "<stop offset='100%' stop-color='#FFF5DC' stop-opacity='0'/>"
        "</radialGradient>"
        "<linearGradient id='diadComet' x1='0%' y1='0%' x2='100%' y2='0%'>"
        "<stop offset='0%' stop-color='#FFF5DC' stop-opacity='0.55'/>"
        "<stop offset='100%' stop-color='#FFF5DC' stop-opacity='0'/>"
        "</linearGradient>"
        "</defs>"
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' "
        f"preserveAspectRatio='xMidYMid slice'>"
        + defs
        + _stars(210, rnd)
        + _glow_stars(rnd)
        + _comets()
        + _crown_constellation()
        + "</svg>"
    )


def build_clouds_svg():
    rnd = _rng(77)
    defs = (
        "<defs>"
        "<radialGradient id='diadCloud'>"
        "<stop offset='0%' stop-color='#FFFFFF' stop-opacity='0.95'/>"
        "<stop offset='70%' stop-color='#F2F6FA' stop-opacity='0.55'/>"
        "<stop offset='100%' stop-color='#DDE5EE' stop-opacity='0'/>"
        "</radialGradient>"
        "</defs>"
    )
    clouds = []
    for _ in range(7):
        cx = round(rnd() * W, 1)
        cy = round(60 + rnd() * (H * 0.45), 1)
        s = 0.7 + rnd() * 0.9
        clouds.append(f"<g transform='translate({cx},{cy}) scale({round(s, 2)})'>")
        for _ in range(9):
            ox = round((rnd() - 0.5) * 320, 1)
            oy = round((rnd() - 0.5) * 90, 1)
            rx = round(70 + rnd() * 110, 1)
            ry = round(rx * (0.42 + rnd() * 0.2), 1)
            clouds.append(
                f"<ellipse cx='{ox}' cy='{oy}' rx='{rx}' ry='{ry}' fill='url(#diadCloud)'/>"
            )
        clouds.append("</g>")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' "
        f"preserveAspectRatio='xMidYMid slice'>"
        + defs
        + "".join(clouds)
        + "</svg>"
    )


def build_noise_svg():
    # Явные width/height обязательны: без них браузер растягивает SVG на весь
    # кадр, и зерно становится крупным и размытым. С размером — тайлится 1:1.
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180' "
        "viewBox='0 0 180 180'>"
        "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
        "numOctaves='2' stitchTiles='stitch'/></filter>"
        "<rect width='100%' height='100%' filter='url(#n)'/></svg>"
    )


def build_star_pattern():
    """Мелкая звёздная пыль для pattern-bg (тёмная тема)."""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48'>"
        "<circle cx='5' cy='7' r='1' fill='#FFF5DC' fill-opacity='0.16'/>"
        "<circle cx='28' cy='14' r='0.7' fill='#C7A557' fill-opacity='0.14'/>"
        "<circle cx='39' cy='31' r='1.1' fill='#FFFFFF' fill-opacity='0.10'/>"
        "<circle cx='14' cy='38' r='0.8' fill='#FFF5DC' fill-opacity='0.12'/>"
        "</svg>"
    )


def build_dot_pattern():
    """Тонкая сетка точек для pattern-bg (светлая тема)."""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='26' height='26'>"
        "<circle cx='1' cy='1' r='1' fill='#2D6A4F' fill-opacity='0.10'/>"
        "</svg>"
    )


def _uri(svg):
    return "url(\"data:image/svg+xml," + svg.replace("#", "%23") + "\")"


STARFIELD_URI = _uri(build_starfield_svg())
CLOUDS_URI = _uri(build_clouds_svg())
NOISE_URI = _uri(build_noise_svg())
STAR_PATTERN_URI = _uri(build_star_pattern())
DOT_PATTERN_URI = _uri(build_dot_pattern())


if __name__ == "__main__":
    print("starfield", len(STARFIELD_URI))
    print("clouds   ", len(CLOUDS_URI))
    print("noise    ", len(NOISE_URI))
    print("pattern  ", len(STAR_PATTERN_URI), len(DOT_PATTERN_URI))
