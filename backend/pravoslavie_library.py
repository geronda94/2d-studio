from pathlib import Path

"""Pravoslavie channel content pack: worlds, cast, studio, scenes.

Installed into scene_library at import time. The cast is SVG for now; each
character is rig-ready (data-rig parts) and can later be replaced by Rive /
DragonBones through the same object slug.
"""

# ─────────────────────────────────────────────────────────────────────────────
# CHARACTER FACTORY
# ─────────────────────────────────────────────────────────────────────────────

CHAR_CSS = """
.char { position:absolute; transform-origin:50% 100%; filter:drop-shadow(0 1.2vmin 1.4vmin rgba(0,0,0,.35)); }
.char .char-svg { width:100%; height:100%; overflow:visible; }
.char [data-rig="head"] { transform-box:fill-box; transform-origin:50% 82%; }
.char [data-rig="arm-left"], .char [data-rig="arm-right"],
.char [data-rig="leg-left"], .char [data-rig="leg-right"] { transform-box:fill-box; transform-origin:50% 8%; }
.char [data-rig="mouth"] { transform-box:fill-box; transform-origin:50% 50%; }
"""


def _char(slug, title, *, skin="#C98E6B", hair="#2A1B12", cloth="#2E4A6A",
          legs="#1F2937", accent="#D4A843", beard=False, glasses=False,
          scarf=False, cassock=False, skirt=False, cross=False, hat=None,
          category="character", description="", tags=None):
    beard_svg = (
        f'<path d="M35 46 Q35 82 60 86 Q85 82 85 46 L76 46 Q72 62 60 62 Q48 62 44 46 Z" fill="{hair}" opacity=".98"/>'
        if beard else ""
    )
    glasses_svg = (
        '<g fill="none" stroke="#E5E7EB" stroke-width="2" opacity=".9">'
        '<circle cx="50" cy="42" r="7"/><circle cx="70" cy="42" r="7"/><path d="M57 42h6"/></g>'
        if glasses else ""
    )
    scarf_svg = (
        f'<path fill-rule="evenodd" d="M18 162 Q22 18 60 10 Q98 18 102 162 Q60 178 18 162 Z '
        f'M38 38 Q38 22 60 20 Q82 22 82 38 Q82 62 60 64 Q38 62 38 38 Z" fill="{accent}"/>'
        if scarf else ""
    )
    hat_svg = ""
    if hat == "kamilavka":
        hat_svg = '<path d="M32 30 Q32 8 60 8 Q88 8 88 30 L92 40 L28 40 Z" fill="#101215"/><rect x="26" y="38" width="68" height="6" rx="2" fill="#101215"/>'
    elif hat == "cap":
        hat_svg = f'<path d="M30 30 Q30 10 60 10 Q90 10 90 30 L94 38 L26 38 Z" fill="{accent}"/><rect x="22" y="36" width="76" height="5" rx="2" fill="{accent}"/>'
    elif hat == "helmet":
        hat_svg = '<path d="M32 42 Q32 6 60 6 Q88 6 88 42 L88 52 L32 52 Z" fill="#6B7280"/><rect x="30" y="48" width="60" height="6" rx="2" fill="#4B5563"/>'
    elif hat == "fur":
        hat_svg = '<path d="M28 34 Q28 8 60 8 Q92 8 92 34 L96 46 L24 46 Z" fill="#6B4A2E"/><rect x="22" y="42" width="76" height="8" rx="4" fill="#8B5E3C"/>'

    skirt_svg = f'<path d="M36 148 L84 148 L100 264 L20 264 Z" fill="{cloth}"/>' if skirt else ""
    cassock_svg = '<path d="M30 74 L90 74 L100 256 L20 256 Z" fill="#15171C"/><path d="M52 74 L60 90 L68 74" fill="#F8FAFC"/>' if cassock else ""
    cross_svg = f'<path d="M58 104h4v18h10v4H62v18h-4V126H48v-4h10z" fill="{accent}"/>' if cross else ""
    legs_svg = "" if (skirt or cassock) else (
        f'<path data-rig="leg-left" d="M46 152 L40 262 L55 262 L58 156 Z" fill="{legs}"/>'
        f'<path data-rig="leg-right" d="M74 152 L80 262 L65 262 L62 156 Z" fill="{legs}"/>'
        f'<ellipse cx="47" cy="264" rx="10" ry="4" fill="#0B0F14"/><ellipse cx="73" cy="264" rx="10" ry="4" fill="#0B0F14"/>'
    )
    torso = (
        f'<path data-rig="torso" d="M34 74 L86 74 L92 154 Q60 166 28 154 Z" fill="#15171C"/>'
        if cassock else
        f'<path data-rig="torso" d="M34 76 Q60 66 86 76 L92 154 Q60 166 28 154 Z" fill="{cloth}"/>'
    )
    arms = (
        f'<path data-rig="arm-left" d="M34 82 L18 150 L29 154 L44 90 Z" fill="{cloth}" stroke="rgba(0,0,0,.12)"/>'
        f'<path data-rig="arm-right" d="M86 82 L102 150 L91 154 L76 90 Z" fill="{cloth}" stroke="rgba(0,0,0,.12)"/>'
        f'<circle cx="24" cy="152" r="5" fill="{skin}"/><circle cx="96" cy="152" r="5" fill="{skin}"/>'
    )

    html = f'''
<div class="obj-{slug} char" style="--skin:{skin};--hair:{hair};--cloth:{cloth};--legs:{legs};--accent:{accent}">
  <svg viewBox="0 0 120 300" class="char-svg">
    <g data-rig="root">
      <g data-rig="head">
        <rect x="52" y="64" width="16" height="14" fill="{skin}"/>
        <circle cx="60" cy="43" r="25" fill="{skin}"/>
        <path d="M35 43 Q35 14 60 14 Q85 14 85 43 Q80 29 60 29 Q40 29 35 43 Z" fill="{hair}"/>
        {hat_svg}
        {scarf_svg}
        {beard_svg}
        {glasses_svg}
        <path d="M44 36 Q50 33 54 36" fill="none" stroke="{hair}" stroke-width="2" stroke-linecap="round"/>
        <path d="M66 36 Q70 33 76 36" fill="none" stroke="{hair}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="50" cy="42" r="2.4" fill="#0B1118"/>
        <circle cx="70" cy="42" r="2.4" fill="#0B1118"/>
        <path d="M57 46 L60 54 L63 46" fill="none" stroke="rgba(80,40,30,.45)" stroke-width="1.4" stroke-linecap="round"/>
        <ellipse data-rig="mouth" cx="60" cy="56" rx="6" ry="2.4" fill="#5B2A2A"/>
      </g>
      {torso}
      {"" if cassock else '<path d="M52 74 L60 86 L68 74" fill="#F8FAFC" opacity=".9"/>'}
      {arms}
      {skirt_svg}
      {cassock_svg}
      {legs_svg}
      {cross_svg}
    </g>
  </svg>
</div>'''.strip()

    css = CHAR_CSS + f'''
.obj-{slug} {{ left:50%; bottom:14%; width:16vmin; height:38vmin; }}
'''
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "description": description,
        "tags": tags or ["character", "pravoslavie"],
        "mechanics": ["idle", "talk", "blink"],
        "rig": {"type": "svg", "parts": ["root", "head", "mouth", "torso", "arm-left", "arm-right", "leg-left", "leg-right"], "clips": ["idle", "talk"], "visemes": 10},
        "domain": ["outdoor", "indoor", "stage"],
        "environments": [],
        "surface": "ground",
        "views": ["front"],
        "default_view": "front",
        "cast_order": CAST_ORDER.get(slug, 20),
        "html": html,
        "css": css,
    }


ASSET_DIR = Path(__file__).resolve().parent / "pravoslavie_assets"
CAST_ORDER = {"host": 0, "cohost": 1, "priest": 2, "historian": 3, "sociologist": 4}


def _peep(slug, title, file_name, *, skin, cloth, hair, description="", tags=None, category="character"):
    raw = (ASSET_DIR / file_name).read_text(encoding="utf-8")
    raw = raw.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    raw = raw.replace("<svg ", '<svg class="char-svg" ', 1)
    html = f'''<div class="obj-{slug} char peep" data-rig="root" style="--skin:{skin};--cloth:{cloth};--hair:{hair}">
{raw}
</div>'''.strip()
    css = f'''
.obj-{slug} {{ position:absolute; left:50%; bottom:10%; width:27vmin; height:36vmin; transform-origin:50% 100%;
  filter:drop-shadow(0 1.2vmin 1.6vmin rgba(0,0,0,.42)); }}
.obj-{slug} .char-svg {{ width:100%; height:100%; overflow:visible; }}
.obj-{slug} .char-svg [id^="head/"] path[fill="#FFFFFF"] {{ fill: var(--skin); }}
.obj-{slug} .char-svg [id^="body/"] path[fill="#FFFFFF"] {{ fill: var(--cloth); }}
.obj-{slug} .char-svg [id^="facial-hair/"] path[fill="#FFFFFF"] {{ fill: var(--hair); }}
.obj-{slug} .char-svg [id^="accessories/"] path[fill="#FFFFFF"] {{ fill: rgba(255,255,255,.18); }}
.obj-{slug} .char-svg [id^="head/"] path[fill="#000000"],
.obj-{slug} .char-svg [id^="body/"] path[fill="#000000"],
.obj-{slug} .char-svg [id^="face/"] path[fill="#000000"],
.obj-{slug} .char-svg [id^="facial-hair/"] path[fill="#000000"] {{ fill: #15100C; }}
.obj-{slug} .priest-cross {{ position:absolute; left:50%; top:57%; width:3vmin; height:5.4vmin; transform:translateX(-50%); }}
.obj-{slug} .priest-cross::before {{ content:''; position:absolute; left:50%; top:0; width:0.55vmin; height:100%;
  background:#D4A843; transform:translateX(-50%); box-shadow:0 0 1.2vmin rgba(212,168,67,.5); }}
.obj-{slug} .priest-cross::after {{ content:''; position:absolute; left:0; top:31%; width:100%; height:0.55vmin;
  background:#D4A843; box-shadow:0 0 1.2vmin rgba(212,168,67,.5); }}
'''.strip()
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "description": description,
        "tags": tags or ["character", "pravoslavie", "openpeeps"],
        "mechanics": ["idle", "talk", "blink"],
        "rig": {"type": "svg-openpeeps", "source": "Open Peeps (CC0)", "clips": ["idle", "talk"], "visemes": 0},
        "domain": ["outdoor", "indoor", "stage"],
        "environments": [],
        "surface": "ground",
        "views": ["front"],
        "default_view": "front",
        "cast_order": CAST_ORDER.get(slug, 20),
        "html": html,
        "css": css,
    }


HOST = _peep("host", "Ведущий", "host.svg", skin="#C98E6B", cloth="#4F7CAC", hair="#2A1B12",
             description="Мужчина ~30, борода, рубашка/пиджак. Основной ведущий.")
COHOST = _peep("cohost", "Соведущая", "cohost.svg", skin="#D8A17E", cloth="#2F4A6A", hair="#2A1B12",
               description="Женщина 30–35, платок, длинная юбка.")
PRIEST = _peep("priest", "Священник", "priest.svg", skin="#C98E6B", cloth="#15171C", hair="#1A1A1A",
               description="Священник: борода, чёрное облачение, крест.")
HISTORIAN = _peep("historian", "Историк", "historian.svg", skin="#C98E6B", cloth="#3B3B4A", hair="#4A4038",
                  description="Историк: очки, борода, пиджак.")
SOCIOLOGIST = _peep("sociologist", "Социолог", "sociologist.svg", skin="#C98E6B", cloth="#4A5568", hair="#2A1B12",
                    description="Социолог: очки, рубашка.")
PEASANT = _peep("peasant", "Прихожанка", "parishioner.svg", skin="#C08A63", cloth="#6B5A45", hair="#3A2A1A",
                description="Прихожанка/массовка: платок, скромная одежда.")
WARRIOR = _peep("warrior", "Гость", "guest.svg", skin="#C98E6B", cloth="#4A4F57", hair="#2A1B12",
                description="Гость/эксперт, массовка.")
MONK = _peep("monk", "Монах", "monk.svg", skin="#C98E6B", cloth="#15171C", hair="#1A1A1A",
             description="Монах: борода, чёрное облачение.")
WORKER = _peep("worker", "Горожанин", "youth.svg", skin="#C98E6B", cloth="#3B4A5A", hair="#2A1B12",
               description="Горожанин/массовка.")
PRIEST["html"] = PRIEST["html"].replace("</svg>", "</svg><div class=\"priest-cross\"></div>")
CHARACTERS = [HOST, COHOST, PRIEST, HISTORIAN, SOCIOLOGIST, PEASANT, WARRIOR, MONK, WORKER]

FIGURE_CSS = '''
.period-figure { position:absolute; transform-origin:50% 100%; filter:drop-shadow(0 .8vmin 1.2vmin rgba(0,0,0,.45)); }
.period-figure svg { width:100%; height:100%; overflow:visible; }
.period-figure .rim { fill:none; stroke:#D4A843; stroke-width:2; opacity:.22; }
'''


def _figure(slug, title, kind):
    if kind == "peasant":
        body = '''
  <path d="M50 78 Q34 84 30 120 L24 260 L76 260 L70 120 Q66 84 50 78 Z" fill="#1A1D22"/>
  <path d="M30 120 L16 210 L28 214 L38 132 Z" fill="#15171B"/>
  <path d="M70 120 L84 210 L72 214 L62 132 Z" fill="#15171B"/>
  <path d="M31 80 Q34 58 50 58 Q66 58 69 80 Q64 92 50 92 Q36 92 31 80 Z" fill="#1A1D22"/>
  <path d="M26 64 Q30 28 50 24 Q70 28 74 64 Q66 50 50 50 Q34 50 26 64 Z" fill="#2A1D18"/>
  <path d="M34 160 L66 160" stroke="#D4A843" stroke-width="2" opacity=".25"/>
'''
    elif kind == "warrior":
        body = '''
  <path d="M50 76 Q34 82 30 116 L26 250 L40 250 L44 150 L56 150 L60 250 L74 250 L70 116 Q66 82 50 76 Z" fill="#1A1D22"/>
  <path d="M30 116 L14 206 L26 212 L38 130 Z" fill="#15171B"/>
  <path d="M70 116 L86 206 L74 212 L62 130 Z" fill="#15171B"/>
  <path d="M32 78 Q34 54 50 54 Q66 54 68 78 Q64 90 50 90 Q36 90 32 78 Z" fill="#1A1D22"/>
  <path d="M31 66 Q31 30 50 26 Q69 30 69 66 L73 74 L27 74 Z" fill="#3A3F46"/>
  <path d="M48 74 L52 74 L52 92 L48 92 Z" fill="#6B7280"/>
  <path d="M86 150 L88 260" stroke="#9CA3AF" stroke-width="4"/>
'''
    elif kind == "monk":
        body = '''
  <path d="M50 74 Q34 80 30 118 L22 264 L78 264 L70 118 Q66 80 50 74 Z" fill="#111317"/>
  <path d="M30 118 L16 208 L28 212 L38 132 Z" fill="#0D0F12"/>
  <path d="M70 118 L84 208 L72 212 L62 132 Z" fill="#0D0F12"/>
  <path d="M31 78 Q32 52 50 50 Q68 52 69 78 Q64 92 50 92 Q36 92 31 78 Z" fill="#1A1D22"/>
  <path d="M28 64 Q30 26 50 20 Q70 26 72 64 L78 96 L22 96 Z" fill="#111317"/>
  <path d="M32 150 L68 150" stroke="#D4A843" stroke-width="2" opacity=".35"/>
  <path d="M48 120 L52 120 L52 140 L60 140 L60 144 L52 144 L52 164 L48 164 L48 144 L40 144 L40 140 L48 140 Z" fill="#D4A843" opacity=".7"/>
'''
    else:
        body = '''
  <path d="M50 76 Q36 82 32 116 L28 176 L40 176 L44 150 L56 150 L60 176 L72 176 L68 116 Q64 82 50 76 Z" fill="#1A1D22"/>
  <path d="M32 116 L18 200 L30 204 L40 130 Z" fill="#15171B"/>
  <path d="M68 116 L82 200 L70 204 L60 130 Z" fill="#15171B"/>
  <path d="M44 174 L40 260 L54 260 L56 180 Z" fill="#15171B"/>
  <path d="M56 174 L60 260 L46 260 L44 180 Z" fill="#15171B"/>
  <path d="M32 78 Q34 54 50 54 Q66 54 68 78 Q64 90 50 90 Q36 90 32 78 Z" fill="#1A1D22"/>
  <path d="M31 64 Q31 40 50 38 Q69 40 69 64 L73 70 L27 70 Z" fill="#2A2F36"/>
  <path d="M30 150 L70 150" stroke="#D4A843" stroke-width="2" opacity=".25"/>
'''
    html = f'''<div class="obj-{slug} period-figure" style="left:20%;bottom:8%;width:11vmin;height:36vmin">
  <svg viewBox="0 0 100 300">
    {body}
    <path class="rim" d="M30 120 Q28 180 26 250"/>
  </svg>
</div>'''.strip()
    css = FIGURE_CSS + f'''
.obj-{slug} {{ position:absolute; }}
'''.strip()
    return {
        "slug": slug,
        "title": title,
        "category": "character",
        "description": "Историческая массовка (силуэт).",
        "tags": ["character", "figure", "history"],
        "mechanics": ["sway"],
        "rig": {"type": "svg-silhouette", "clips": ["idle"]},
        "domain": ["outdoor", "indoor", "stage"],
        "environments": [],
        "surface": "ground",
        "views": ["front"],
        "default_view": "front",
        "cast_order": 80,
        "html": html,
        "css": css,
    }


FIGURES = [
    _figure("figure-peasant", "Крестьянка (силуэт)", "peasant"),
    _figure("figure-warrior", "Воин (силуэт)", "warrior"),
    _figure("figure-monk", "Монах (силуэт)", "monk"),
    _figure("figure-worker", "Рабочий (силуэт)", "worker"),
]


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENTS
# ─────────────────────────────────────────────────────────────────────────────

STUDIO_PRAV = {
    "slug": "studio-prav",
    "title": "Студия «Механизм»",
    "description": "Тёмная графитовая студия с тёплым золотым светом, столом, полкой и монитором.",
    "tags": ["studio", "pravoslavie", "indoor"],
    "domain": "indoor",
    "views": ["dark", "warm"],
    "default_view": "dark",
    "perspective": "front",
    "html": """
<div class="env env-studio-prav">
  <div class="wall"></div>
  <div class="shelf"><div class="books"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
  <div class="poster"><span>МЕХАНИЗМ</span><small>социальная история</small></div>
  <div class="plant"></div>
  <div class="desk"></div>
  <div class="lamp"></div>
  <div class="glow"></div>
  <div class="vignette"></div>
</div>""",
    "css": """
.env-studio-prav { position:absolute; inset:0; overflow:hidden; background:#0B0C0F; }
.env-studio-prav .wall { position:absolute; inset:0 0 28% 0;
  background:linear-gradient(180deg,#14161B 0%,#1B1714 55%,#241D18 100%); }
.env-studio-prav .wall::before { content:''; position:absolute; inset:0;
  background:repeating-linear-gradient(90deg,transparent 0 120px,rgba(255,255,255,.025) 120px 122px); }
.env-studio-prav .shelf { position:absolute; left:6%; top:12%; width:28%; height:34%;
  background:linear-gradient(180deg,#2A211A,#1A1410); border:2px solid #3A2C22; border-radius:4px;
  box-shadow:inset 0 0 30px rgba(0,0,0,.5); }
.env-studio-prav .shelf::after { content:''; position:absolute; left:8%; right:8%; top:30%; height:4px; background:#4A382A; box-shadow:0 9vh 0 #4A382A; }
.env-studio-prav .shelf .books { position:absolute; left:8%; right:8%; top:8%; height:22%; display:flex; align-items:flex-end; gap:.35vmin; }
.env-studio-prav .shelf .books i { flex:1; height:80%; background:#5B3A2A; border-radius:2px 2px 0 0; box-shadow:inset 0 0 0 1px rgba(255,255,255,.06); }
.env-studio-prav .shelf .books i:nth-child(2) { height:62%; background:#3E4A5A; }
.env-studio-prav .shelf .books i:nth-child(3) { height:92%; background:#6B4A32; }
.env-studio-prav .shelf .books i:nth-child(4) { height:70%; background:#4A3A2A; }
.env-studio-prav .shelf .books i:nth-child(5) { height:84%; background:#2F3A4A; }
.env-studio-prav .shelf .books i:nth-child(6) { height:58%; background:#6A3A2A; }
.env-studio-prav .shelf .books i:nth-child(7) { height:76%; background:#3A2A1E; }
.env-studio-prav .poster { position:absolute; left:36%; top:14%; width:14%; height:20%; background:#0E0F12;
  border:1px solid rgba(212,168,67,.35); display:flex; flex-direction:column; align-items:center; justify-content:center;
  box-shadow:0 1vh 2vh rgba(0,0,0,.35); }
.env-studio-prav .poster span { font-family:var(--font-heading); font-size:clamp(8px,.9vw,13px); letter-spacing:.18em; color:var(--brand-amber); }
.env-studio-prav .poster small { margin-top:.4vh; font-family:var(--font-mono); font-size:clamp(5px,.5vw,8px); letter-spacing:.1em; color:var(--text-muted); }
.env-studio-prav .plant { position:absolute; right:6%; bottom:24%; width:8vmin; height:18vmin; transform-origin:50% 100%; }
.env-studio-prav .plant::before { content:''; position:absolute; left:30%; bottom:0; width:40%; height:28%; border-radius:0 0 30% 30%; background:#3A2A1E; }
.env-studio-prav .plant::after { content:''; position:absolute; left:18%; bottom:22%; width:64%; height:78%;
  background:radial-gradient(ellipse at 50% 60%,#2F6A4A,#163A28 70%); clip-path:polygon(50% 0,64% 28%,82% 18%,72% 44%,94% 46%,70% 62%,80% 82%,54% 74%,50% 100%,46% 74%,20% 82%,30% 62%,6% 46%,28% 44%,18% 18%,36% 28%); }
.env-studio-prav .desk { position:absolute; left:8%; right:8%; bottom:0; height:26%;
  background:linear-gradient(180deg,#4A3425,#2C1D14); border-top:6px solid #6B4A32;
  box-shadow:0 -1vh 3vh rgba(0,0,0,.5); }
.env-studio-prav .desk::after { content:''; position:absolute; left:4%; right:4%; top:12%; height:1px; background:rgba(255,255,255,.08); box-shadow:0 4vh 0 rgba(0,0,0,.25); }
.env-studio-prav .lamp { position:absolute; right:14%; top:18%; width:16vmin; height:16vmin; border-radius:50%;
  background:radial-gradient(circle,#FFE1A0 0%,#D4A843 20%,rgba(212,168,67,0) 68%); filter:blur(2px); opacity:.55; }
.env-studio-prav .glow { position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse at 78% 18%,rgba(212,168,67,.14),transparent 42%); }
.env-studio-prav .vignette { position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse at 50% 45%,transparent 48%,rgba(0,0,0,.55) 100%); }
""",
}

CHURCH = {
    "slug": "church",
    "title": "Храм",
    "description": "Тёмный храм: арки, свечи, золотой свет, иконостас без ликов крупно.",
    "tags": ["church", "pravoslavie", "indoor"],
    "domain": "indoor",
    "views": ["candlelight"],
    "default_view": "candlelight",
    "perspective": "front",
    "html": """
<div class="env env-church">
  <div class="wall"></div>
  <div class="arches"><i></i><i></i><i></i></div>
  <div class="iconostasis"></div>
  <div class="candles"><i></i><i></i><i></i><i></i></div>
  <div class="light"></div>
  <div class="floor"></div>
  <div class="vignette"></div>
</div>""",
    "css": """
.env-church { position:absolute; inset:0; overflow:hidden; background:#090807; }
.env-church .wall { position:absolute; inset:0 0 24% 0; background:linear-gradient(180deg,#16110D,#241A12 60%,#2E2118); }
.env-church .arches { position:absolute; left:6%; right:6%; top:8%; height:58%; display:flex; gap:4%; }
.env-church .arches i { flex:1; border-radius:50% 50% 0 0; border:2px solid rgba(212,168,67,.18);
  background:linear-gradient(180deg,rgba(212,168,67,.08),rgba(0,0,0,.15)); }
.env-church .iconostasis { position:absolute; left:18%; right:18%; top:12%; height:42%;
  background:linear-gradient(180deg,#2A1B10,#1A110B); border:2px solid rgba(212,168,67,.3);
  display:grid; grid-template-columns:repeat(4,1fr); gap:2%; padding:2%; }
.env-church .iconostasis::before { content:''; position:absolute; inset:4%;
  background:repeating-linear-gradient(90deg,rgba(212,168,67,.18) 0 2px,transparent 2px 25%); }
.env-church .candles { position:absolute; left:8%; right:8%; bottom:22%; height:18%; display:flex; justify-content:space-around; align-items:flex-end; }
.env-church .candles i { width:1.2vmin; height:8vmin; background:linear-gradient(180deg,#F8E7B0,#C9A227); border-radius:2px;
  box-shadow:0 0 3vmin rgba(255,214,120,.7); }
.env-church .light { position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse at 50% 28%,rgba(255,214,120,.14),transparent 55%); }
.env-church .floor { position:absolute; left:0; right:0; bottom:0; height:24%;
  background:linear-gradient(180deg,#2A1D14,#0D0907); }
.env-church .vignette { position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse at 50% 45%,transparent 42%,rgba(0,0,0,.6) 100%); }
""",
}

ANCIENT_RUS = {
    "slug": "ancient-rus",
    "title": "Древняя Русь",
    "description": "Деревянное село, река, лес и деревянный храм с луковичным куполом.",
    "tags": ["history", "russia", "outdoor"],
    "domain": "outdoor",
    "views": ["day", "sunset"],
    "default_view": "day",
    "perspective": "side",
    "html": """
<div class="env env-ancient-rus">
  <svg class="scene-svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="anSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#6F8FA3"/><stop offset=".55" stop-color="#AFC5C5"/>
        <stop offset=".82" stop-color="#DCC9A4"/><stop offset="1" stop-color="#EAD8B0"/>
      </linearGradient>
      <linearGradient id="anRiver" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#8FB4B4"/><stop offset=".55" stop-color="#4F797B"/><stop offset="1" stop-color="#27484C"/>
      </linearGradient>
      <radialGradient id="anSun"><stop offset="0" stop-color="#FFF8DC"/><stop offset=".4" stop-color="#FFD37A"/><stop offset="1" stop-color="#FFD37A" stop-opacity="0"/></radialGradient>
    </defs>
    <rect width="1920" height="1080" fill="url(#anSky)"/>
    <circle cx="1480" cy="230" r="170" fill="url(#anSun)" opacity=".9"/>
    <path d="M0 640 Q140 560 300 620 T620 585 T920 635 T1240 590 T1540 630 T1920 575 L1920 820 L0 820 Z" fill="#3D5B4A" opacity=".55"/>
    <g fill="#244A3A" opacity=".85">
      <path d="M80 700 l34 -170 l34 170 z"/><path d="M160 710 l30 -150 l30 150 z"/>
      <path d="M250 700 l38 -190 l38 190 z"/><path d="M350 710 l32 -160 l32 160 z"/>
      <path d="M1500 700 l36 -180 l36 180 z"/><path d="M1600 710 l30 -150 l30 150 z"/>
      <path d="M1700 700 l40 -200 l40 200 z"/><path d="M1810 715 l32 -160 l32 160 z"/>
    </g>
    <path d="M0 800 Q480 740 960 780 T1920 760 L1920 960 Q1440 930 960 960 T0 930 Z" fill="url(#anRiver)" opacity=".9"/>
    <path d="M0 900 Q480 870 960 900 T1920 880 L1920 1080 L0 1080 Z" fill="#2B2618"/>
    <g fill="#4A3324">
      <path d="M150 790 l110 -60 l110 60 l0 90 l-220 0 z"/>
      <path d="M310 805 l90 -50 l90 50 l0 75 l-180 0 z"/>
      <path d="M510 795 l120 -65 l120 65 l0 85 l-240 0 z"/>
    </g>
    <g fill="#3A2A1E">
      <path d="M170 790 l90 -48 l90 48 z"/><path d="M330 805 l70 -40 l70 40 z"/><path d="M530 795 l100 -52 l100 52 z"/>
    </g>
    <g transform="translate(1200,610)">
      <path d="M0 170 L0 -30 L190 -30 L190 170 Z" fill="#5A3E28"/>
      <path d="M-25 -30 L95 -125 L215 -30 Z" fill="#3A2A1E"/>
      <path d="M55 -125 Q95 -245 135 -125 Z" fill="#4A3520"/>
      <path d="M94 -185 L96 -245 M78 -215 L112 -215" stroke="#D4A843" stroke-width="7" stroke-linecap="round"/>
      <rect x="40" y="60" width="28" height="55" rx="12" fill="#1A120C" opacity=".55"/>
      <rect x="120" y="60" width="28" height="55" rx="12" fill="#1A120C" opacity=".55"/>
    </g>
    <path d="M0 930 Q480 900 960 930 T1920 910 L1920 1080 L0 1080 Z" fill="#22200F"/>
    <g stroke="#5A6B3A" stroke-width="5" opacity=".55">
      <path d="M120 990 l-12 -38 M120 990 l14 -34 M150 1000 l-8 -30"/>
      <path d="M1680 980 l-10 -36 M1680 980 l12 -32 M1710 990 l-8 -28"/>
    </g>
  </svg>
  <div class="fog"></div>
</div>""",
    "css": """
.env-ancient-rus { position:absolute; inset:0; overflow:hidden; background:#1B2A2E; }
.env-ancient-rus .scene-svg { position:absolute; inset:0; width:100%; height:100%; }
.env-ancient-rus .fog { position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(180deg,transparent 50%,rgba(220,230,220,.10) 82%,rgba(20,25,20,.2)); }
""",
}

EMPIRE = {
    "slug": "empire",
    "title": "Империя",
    "description": "Городская улица XIX века: классические фасады, фонари, мостовая.",
    "tags": ["history", "empire", "outdoor"],
    "domain": "outdoor",
    "views": ["day", "evening"],
    "default_view": "day",
    "perspective": "side",
    "html": """
<div class="env env-empire">
  <svg class="scene-svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="emSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#8FA0AC"/><stop offset=".6" stop-color="#C8C2B4"/><stop offset="1" stop-color="#E1D2B6"/>
      </linearGradient>
      <linearGradient id="emStreet" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#5A554C"/><stop offset="1" stop-color="#2B2824"/>
      </linearGradient>
    </defs>
    <rect width="1920" height="1080" fill="url(#emSky)"/>
    <rect y="760" width="1920" height="320" fill="url(#emStreet)"/>
    <!-- far buildings -->
    <g fill="#8A806E" opacity=".75">
      <rect x="0" y="430" width="300" height="340"/><rect x="320" y="470" width="260" height="300"/>
      <rect x="1340" y="450" width="280" height="320"/><rect x="1640" y="420" width="280" height="350"/>
    </g>
    <!-- main facades -->
    <g>
      <rect x="80" y="300" width="470" height="480" fill="#B9A88E"/>
      <rect x="80" y="300" width="470" height="34" fill="#D8C9B0"/>
      <rect x="80" y="334" width="470" height="12" fill="#8E7F68"/>
      <g fill="#6E604C">
        <rect x="120" y="390" width="70" height="100" rx="24"/><rect x="230" y="390" width="70" height="100" rx="24"/>
        <rect x="340" y="390" width="70" height="100" rx="24"/><rect x="450" y="390" width="70" height="100" rx="24"/>
        <rect x="120" y="540" width="70" height="100" rx="24"/><rect x="230" y="540" width="70" height="100" rx="24"/>
        <rect x="340" y="540" width="70" height="100" rx="24"/><rect x="450" y="540" width="70" height="100" rx="24"/>
      </g>
      <rect x="120" y="680" width="70" height="100" fill="#4A3B2C"/><rect x="230" y="680" width="70" height="100" fill="#4A3B2C"/>
      <rect x="340" y="680" width="70" height="100" fill="#4A3B2C"/><rect x="450" y="680" width="70" height="100" fill="#4A3B2C"/>
    </g>
    <g>
      <rect x="620" y="340" width="360" height="440" fill="#C8B89E"/>
      <rect x="620" y="340" width="360" height="28" fill="#E2D3B8"/>
      <g fill="#7D6C56">
        <rect x="650" y="400" width="60" height="90" rx="20"/><rect x="740" y="400" width="60" height="90" rx="20"/>
        <rect x="830" y="400" width="60" height="90" rx="20"/><rect x="920" y="400" width="60" height="90" rx="20"/>
        <rect x="650" y="540" width="60" height="90" rx="20"/><rect x="740" y="540" width="60" height="90" rx="20"/>
        <rect x="830" y="540" width="60" height="90" rx="20"/><rect x="920" y="540" width="60" height="90" rx="20"/>
      </g>
      <rect x="740" y="680" width="120" height="100" fill="#3E3022"/>
    </g>
    <g>
      <rect x="1060" y="320" width="420" height="460" fill="#B4A48A"/>
      <rect x="1060" y="320" width="420" height="30" fill="#D6C7AC"/>
      <g fill="#6F5F4A">
        <rect x="1100" y="380" width="64" height="100" rx="22"/><rect x="1200" y="380" width="64" height="100" rx="22"/>
        <rect x="1300" y="380" width="64" height="100" rx="22"/><rect x="1400" y="380" width="64" height="100" rx="22"/>
        <rect x="1100" y="530" width="64" height="100" rx="22"/><rect x="1200" y="530" width="64" height="100" rx="22"/>
        <rect x="1300" y="530" width="64" height="100" rx="22"/><rect x="1400" y="530" width="64" height="100" rx="22"/>
      </g>
      <rect x="1180" y="680" width="140" height="100" fill="#3E3022"/>
    </g>
    <g>
      <rect x="1520" y="360" width="400" height="420" fill="#9C8D76"/>
      <rect x="1520" y="360" width="400" height="28" fill="#CBB99E"/>
      <g fill="#5F503E">
        <rect x="1560" y="420" width="58" height="90" rx="20"/><rect x="1650" y="420" width="58" height="90" rx="20"/>
        <rect x="1740" y="420" width="58" height="90" rx="20"/><rect x="1830" y="420" width="58" height="90" rx="20"/>
        <rect x="1560" y="550" width="58" height="90" rx="20"/><rect x="1650" y="550" width="58" height="90" rx="20"/>
        <rect x="1740" y="550" width="58" height="90" rx="20"/><rect x="1830" y="550" width="58" height="90" rx="20"/>
      </g>
    </g>
    <!-- street perspective -->
    <path d="M0 760 L1920 760 L1920 1080 L0 1080 Z" fill="url(#emStreet)"/>
    <path d="M0 800 L1920 800" stroke="#6B6257" stroke-width="3" opacity=".5"/>
    <path d="M0 860 L1920 860" stroke="#6B6257" stroke-width="2" opacity=".35"/>
    <path d="M0 940 L1920 940" stroke="#6B6257" stroke-width="2" opacity=".25"/>
    <g stroke="#4A443C" stroke-width="3" opacity=".5">
      <path d="M120 780 L60 1080"/><path d="M380 780 L340 1080"/><path d="M640 780 L620 1080"/>
      <path d="M900 780 L900 1080"/><path d="M1160 780 L1180 1080"/><path d="M1420 780 L1460 1080"/><path d="M1680 780 L1740 1080"/>
    </g>
    <!-- lamps -->
    <g fill="#1F2937">
      <rect x="560" y="700" width="8" height="180"/><circle cx="564" cy="690" r="20" fill="#FDE68A"/>
      <rect x="1360" y="700" width="8" height="180"/><circle cx="1364" cy="690" r="20" fill="#FDE68A"/>
    </g>
    <g fill="#FDE68A" opacity=".18">
      <circle cx="564" cy="690" r="60"/><circle cx="1364" cy="690" r="60"/>
    </g>
    <rect y="760" width="1920" height="320" fill="#2B2824" opacity=".18"/>
  </svg>
  <div class="fog"></div>
</div>""",
    "css": """
.env-empire { position:absolute; inset:0; overflow:hidden; background:#1A1A1C; }
.env-empire .scene-svg { position:absolute; inset:0; width:100%; height:100%; }
.env-empire .fog { position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(180deg,transparent 55%,rgba(220,210,190,.10) 85%,rgba(20,18,15,.2)); }
""",
}

SOVIET = {
    "slug": "soviet",
    "title": "Советский город",
    "description": "Улица 1930-х: кирпичные дома, плакатные формы, приглушённый свет.",
    "tags": ["history", "soviet", "outdoor"],
    "domain": "outdoor",
    "views": ["day", "grey"],
    "default_view": "grey",
    "perspective": "side",
    "html": """
<div class="env env-soviet">
  <svg class="scene-svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
    <defs>
      <linearGradient id="svSky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#7C8992"/><stop offset=".65" stop-color="#AAAFA8"/><stop offset="1" stop-color="#C9C4B8"/>
      </linearGradient>
      <linearGradient id="svStreet" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#4A4A46"/><stop offset="1" stop-color="#1C1C1A"/>
      </linearGradient>
    </defs>
    <rect width="1920" height="1080" fill="url(#svSky)"/>
    <rect y="740" width="1920" height="340" fill="url(#svStreet)"/>
    <!-- far blocks -->
    <g fill="#6A5A4A" opacity=".65">
      <rect x="0" y="390" width="320" height="350"/><rect x="340" y="440" width="240" height="300"/>
      <rect x="1340" y="420" width="260" height="320"/><rect x="1620" y="380" width="300" height="360"/>
    </g>
    <!-- main brick blocks -->
    <g>
      <rect x="60" y="280" width="520" height="460" fill="#6B4A3A"/>
      <rect x="60" y="280" width="520" height="22" fill="#4A332A"/>
      <g fill="#2E211C">
        <rect x="100" y="340" width="62" height="80"/><rect x="190" y="340" width="62" height="80"/>
        <rect x="280" y="340" width="62" height="80"/><rect x="370" y="340" width="62" height="80"/><rect x="460" y="340" width="62" height="80"/>
        <rect x="100" y="460" width="62" height="80"/><rect x="190" y="460" width="62" height="80"/>
        <rect x="280" y="460" width="62" height="80"/><rect x="370" y="460" width="62" height="80"/><rect x="460" y="460" width="62" height="80"/>
        <rect x="100" y="580" width="62" height="80"/><rect x="190" y="580" width="62" height="80"/>
        <rect x="280" y="580" width="62" height="80"/><rect x="370" y="580" width="62" height="80"/><rect x="460" y="580" width="62" height="80"/>
      </g>
      <rect x="280" y="660" width="90" height="80" fill="#2A1D18"/>
    </g>
    <g>
      <rect x="660" y="330" width="440" height="410" fill="#7A5542"/>
      <rect x="660" y="330" width="440" height="20" fill="#513A2E"/>
      <g fill="#2F211B">
        <rect x="700" y="390" width="58" height="76"/><rect x="790" y="390" width="58" height="76"/><rect x="880" y="390" width="58" height="76"/><rect x="970" y="390" width="58" height="76"/>
        <rect x="700" y="510" width="58" height="76"/><rect x="790" y="510" width="58" height="76"/><rect x="880" y="510" width="58" height="76"/><rect x="970" y="510" width="58" height="76"/>
        <rect x="700" y="630" width="58" height="76"/><rect x="790" y="630" width="58" height="76"/><rect x="880" y="630" width="58" height="76"/><rect x="970" y="630" width="58" height="76"/>
      </g>
      <rect x="830" y="660" width="100" height="80" fill="#2A1D18"/>
    </g>
    <g>
      <rect x="1180" y="360" width="420" height="380" fill="#6A4A3A"/>
      <rect x="1180" y="360" width="420" height="20" fill="#4A332A"/>
      <g fill="#2C1F1A">
        <rect x="1220" y="420" width="56" height="72"/><rect x="1300" y="420" width="56" height="72"/><rect x="1380" y="420" width="56" height="72"/><rect x="1460" y="420" width="56" height="72"/>
        <rect x="1220" y="530" width="56" height="72"/><rect x="1300" y="530" width="56" height="72"/><rect x="1380" y="530" width="56" height="72"/><rect x="1460" y="530" width="56" height="72"/>
      </g>
      <rect x="1340" y="660" width="100" height="80" fill="#2A1D18"/>
    </g>
    <!-- poster -->
    <g transform="translate(1640,420)">
      <rect width="180" height="230" fill="#8C2F2F" stroke="#C9B38A" stroke-width="5"/>
      <path d="M20 190 L70 80 L120 160 L160 60 L170 190 Z" fill="#C9B38A" opacity=".9"/>
      <rect x="20" y="20" width="140" height="18" fill="#C9B38A" opacity=".8"/>
    </g>
    <!-- street -->
    <path d="M0 740 L1920 740 L1920 1080 L0 1080 Z" fill="url(#svStreet)"/>
    <g stroke="#5A5A54" stroke-width="3" opacity=".45">
      <path d="M0 800 L1920 800"/><path d="M0 870 L1920 870"/><path d="M0 960 L1920 960"/>
    </g>
    <g stroke="#3A3A36" stroke-width="3" opacity=".5">
      <path d="M160 760 L100 1080"/><path d="M520 760 L500 1080"/><path d="M900 760 L900 1080"/><path d="M1280 760 L1320 1080"/><path d="M1660 760 L1740 1080"/>
    </g>
    <!-- lamps -->
    <g fill="#1F2937">
      <rect x="620" y="680" width="7" height="170"/><circle cx="623" cy="670" r="18" fill="#D9C27A"/>
      <rect x="1260" y="680" width="7" height="170"/><circle cx="1263" cy="670" r="18" fill="#D9C27A"/>
    </g>
    <g fill="#D9C27A" opacity=".14"><circle cx="623" cy="670" r="55"/><circle cx="1263" cy="670" r="55"/></g>
  </svg>
  <div class="fog"></div>
</div>""",
    "css": """
.env-soviet { position:absolute; inset:0; overflow:hidden; background:#15161A; }
.env-soviet .scene-svg { position:absolute; inset:0; width:100%; height:100%; }
.env-soviet .fog { position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(180deg,transparent 50%,rgba(160,160,150,.12) 82%,rgba(15,15,14,.25)); }
""",
}

MODERN_CITY_DAY = {
    "slug": "modern-city-day",
    "title": "Современный город",
    "description": "Дневной город: стеклянные фасады, улица, свет.",
    "tags": ["modern", "city", "outdoor"],
    "domain": "outdoor",
    "views": ["day", "evening"],
    "default_view": "day",
    "perspective": "side",
    "html": """
<div class="env env-modern-city">
  <div class="sky"></div>
  <div class="towers"><i></i><i></i><i></i><i></i></div>
  <div class="street"></div>
  <div class="fog"></div>
</div>""",
    "css": """
.env-modern-city { position:absolute; inset:0; overflow:hidden; background:#10151C; }
.env-modern-city .sky { position:absolute; inset:0 0 32% 0; background:linear-gradient(180deg,#5A8FB8,#A8C8D8 70%,#D8E4E8); }
.env-modern-city .towers { position:absolute; left:0; right:0; bottom:28%; height:52%; display:flex; align-items:flex-end; gap:2%; padding:0 4%; }
.env-modern-city .towers i { flex:1; background:linear-gradient(180deg,#6B7C8C,#3A4A5A); border:1px solid rgba(255,255,255,.08);
  clip-path:polygon(6% 0,94% 0,100% 100%,0 100%); }
.env-modern-city .towers i::after { content:''; position:absolute; inset:8% 12%;
  background:repeating-linear-gradient(90deg,rgba(180,220,240,.35) 0 12%,transparent 12% 24%),
             repeating-linear-gradient(180deg,rgba(180,220,240,.3) 0 10%,transparent 10% 24%); }
.env-modern-city .street { position:absolute; left:0; right:0; bottom:0; height:30%; background:linear-gradient(180deg,#3A4048,#15181C); }
.env-modern-city .fog { position:absolute; inset:0; pointer-events:none; background:linear-gradient(180deg,transparent 55%,rgba(220,235,240,.1) 85%,transparent); }
""",
}

ENVIRONMENTS = [STUDIO_PRAV, CHURCH, ANCIENT_RUS, EMPIRE, SOVIET, MODERN_CITY_DAY]

# ─────────────────────────────────────────────────────────────────────────────
# STUDIO MONITOR (functional screen)
# ─────────────────────────────────────────────────────────────────────────────

STUDIO_MONITOR = {
    "slug": "studio-monitor",
    "title": "Студийный монитор",
    "category": "prop",
    "description": "Большой монитор: картинка/видео из props.monitor_media / monitor_video.",
    "tags": ["studio", "monitor", "screen"],
    "mechanics": ["media"],
    "domain": ["indoor"],
    "environments": ["studio-prav"],
    "surface": "desk",
    "views": ["front"],
    "default_view": "front",
    "html": """
<div class="obj-studio-monitor">
  <div class="monitor-frame">
    <div class="monitor-screen">
      <img data-monitor-image alt="" />
      <video data-monitor-video muted playsinline></video>
      <div class="monitor-placeholder">MECHANISM</div>
    </div>
    <div class="monitor-brand">MECHANISM · STUDIO</div>
  </div>
  <div class="monitor-neck"></div>
  <div class="monitor-base"></div>
</div>""",
    "css": """
.obj-studio-monitor { position:absolute; left:50%; bottom:38%; width:44vmin; height:28vmin; transform:translateX(-50%); }
.obj-studio-monitor .monitor-frame { position:absolute; inset:0 0 12% 0; border-radius:1.2vmin;
  background:linear-gradient(180deg,#1A1D22,#0B0D10); border:0.6vmin solid #2A2F36;
  box-shadow:0 0 5vmin rgba(212,168,67,.08), inset 0 0 2vmin rgba(0,0,0,.6); padding:1.4vmin; }
.obj-studio-monitor .monitor-screen { position:relative; width:100%; height:100%; overflow:hidden; border-radius:0.6vmin;
  background:radial-gradient(circle at 50% 35%,#1B2A3A,#0A0F16 70%); }
.obj-studio-monitor .monitor-screen img, .obj-studio-monitor .monitor-screen video { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:none; }
.obj-studio-monitor .monitor-placeholder { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  font-family:var(--font-mono); letter-spacing:.3em; font-size:clamp(10px,1.1vw,16px); color:rgba(212,168,67,.55); }
.obj-studio-monitor .monitor-brand { position:absolute; left:2%; bottom:-9%; font-family:var(--font-mono);
  font-size:clamp(7px,.7vw,10px); letter-spacing:.18em; color:rgba(226,232,240,.35); }
.obj-studio-monitor .monitor-neck { position:absolute; left:45%; bottom:5%; width:10%; height:8%; background:#1F242B; }
.obj-studio-monitor .monitor-base { position:absolute; left:30%; bottom:0; width:40%; height:6%; border-radius:999px; background:#1F242B; }
""",
}

PROPS = [STUDIO_MONITOR]

# ─────────────────────────────────────────────────────────────────────────────
# SCENE JS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

STUDIO_FRONT_CSS = """
.studio-front { position:absolute; left:0; right:0; bottom:0; height:27%; z-index:5; pointer-events:none; }
.studio-front .desk-front { position:absolute; left:0; right:0; bottom:0; height:100%;
  background:linear-gradient(180deg,#5A3E2A 0%,#3A2718 38%,#24170E 100%);
  border-top:0.7vmin solid #7A5638; box-shadow:0 -1.4vmin 3vmin rgba(0,0,0,.5); }
.studio-front .desk-front::before { content:''; position:absolute; inset:0;
  background:repeating-linear-gradient(90deg,transparent 0 12%,rgba(255,255,255,.035) 12% 12.4%,transparent 12.4% 24%); }
.studio-front .papers { position:absolute; left:18%; bottom:78%; width:9vmin; height:3.4vmin;
  background:linear-gradient(180deg,#F3EBDD,#D8C9AE); transform:rotate(-4deg); box-shadow:0 .4vmin 1vmin rgba(0,0,0,.25); }
.studio-front .papers::after { content:''; position:absolute; inset:18% 12%;
  background:repeating-linear-gradient(180deg,rgba(40,30,20,.25) 0 1px,transparent 1px 6px); }
.studio-front .mic { position:absolute; left:72%; bottom:84%; width:1.1vmin; height:8vmin; background:#111; border-radius:999px; transform:rotate(9deg); }
.studio-front .mic::before { content:''; position:absolute; left:50%; top:-2.2vmin; width:3.2vmin; height:3.2vmin;
  border-radius:50%; background:radial-gradient(circle at 38% 32%,#4B5563,#111); transform:translateX(-50%); }
.studio-front .coffee { position:absolute; left:28%; bottom:82%; width:4.4vmin; height:5.4vmin; border-radius:0 0 35% 35%;
  background:linear-gradient(180deg,#F8FAFC,#CBD5E1); box-shadow:inset 0 -.5vmin 0 #94A3B8; }
.studio-front .coffee::after { content:''; position:absolute; right:-34%; top:18%; width:42%; height:44%;
  border:.55vmin solid #E2E8F0; border-left:0; border-radius:0 999px 999px 0; }
.studio-lower-third { position:absolute; left:6%; bottom:7%; z-index:20; display:flex; flex-direction:column; gap:.5vh;
  padding:1.4vh 1.6vw; border-left:0.7vmin solid var(--brand-amber); background:rgba(12,12,14,.72);
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }
.studio-lower-third .name { font-family:var(--font-heading); font-size:clamp(14px,1.6vw,24px); color:var(--text-primary); }
.studio-lower-third .role { font-family:var(--font-mono); font-size:clamp(9px,.95vw,13px); letter-spacing:.14em;
  text-transform:uppercase; color:var(--brand-amber); }
.studio-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; mix-blend-mode:screen; opacity:.55; z-index:30; }
"""

STUDIO_FRONT_HTML = """
<div class="studio-front">
  <div class="desk-front"></div>
  <div class="papers"></div>
  <div class="coffee"></div>
  <div class="mic"></div>
</div>
<div class="studio-lower-third">
  <div class="name" data-lt-name></div>
  <div class="role" data-lt-role></div>
</div>
<canvas class="studio-dust" width="1920" height="1080"></canvas>
"""

DUSK_JS = """
const dustCanvas = root.querySelector('.studio-dust');
let dustCtx = null;
let dust = [];
if (dustCanvas) {
  dustCanvas.width = 1920; dustCanvas.height = 1080;
  dustCtx = dustCanvas.getContext('2d');
  const rand = SceneKit.mulberry32(7);
  dust = Array.from({ length: 70 }, () => ({
    x: rand() * 1920, y: rand() * 1080, r: 0.5 + rand() * 1.8,
    s: 2 + rand() * 9, a: 0.04 + rand() * 0.16,
  }));
}
function drawDust(t) {
  if (!dustCtx) return;
  dustCtx.clearRect(0, 0, 1920, 1080);
  dust.forEach((p, i) => {
    let y = p.y - (t / 1000) * p.s;
    y = ((y % 1080) + 1080) % 1080;
    const x = p.x + Math.sin(t / 2200 + i) * 22;
    dustCtx.beginPath();
    dustCtx.arc(x, y, p.r, 0, Math.PI * 2);
    dustCtx.fillStyle = `rgba(255,225,170,${p.a})`;
    dustCtx.fill();
  });
}
const ltName = root.querySelector('[data-lt-name]');
const ltRole = root.querySelector('[data-lt-role]');
if (ltName) ltName.textContent = p.host_name || 'Ведущий';
if (ltRole) ltRole.textContent = p.host_role || 'МЕХАНИЗМ · авторский разбор';
"""

STUDIO_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const monitorImg = root.querySelector('[data-monitor-image]');
const monitorVid = root.querySelector('[data-monitor-video]');
const placeholder = root.querySelector('.monitor-placeholder');

function setMonitor(media, video) {
  if (media && monitorImg) {
    monitorImg.src = media;
    monitorImg.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
  }
  if (video && monitorVid) {
    monitorVid.src = video;
    monitorVid.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
  }
}
setMonitor(p.monitor_media, p.monitor_video);

const chars = Array.from(root.querySelectorAll('.char'));
function animateChars(t) {
  chars.forEach((el, i) => {
    const head = el.querySelector('[data-rig="head"]');
    const mouth = el.querySelector('[data-rig="mouth"]');
    const armL = el.querySelector('[data-rig="arm-left"]');
    const armR = el.querySelector('[data-rig="arm-right"]');
    if (head) head.style.transform = `rotate(${Math.sin(t / 1100 + i) * 1.6}deg)`;
    if (armL) armL.style.transform = `rotate(${Math.sin(t / 1300 + i) * 2.2}deg)`;
    if (armR) armR.style.transform = `rotate(${Math.sin(t / 1200 + i + 1) * 2.2}deg)`;
    if (mouth) mouth.style.transform = `scaleY(${0.7 + Math.abs(Math.sin(t / 160 + i)) * 0.55})`;
  });
}

function seek(t) {
  animateChars(t);
  drawDust(t);
  if (monitorVid && monitorVid.src && monitorVid.duration) {
    try { monitorVid.currentTime = Math.min(monitorVid.duration, t / 1000); } catch (e) {}
  }
}
window.scene = { seek };
"""

STUDIO_JS = STUDIO_JS + "\n" + DUSK_JS

PANEL_JS = STUDIO_JS + """
const panelCues = SceneKit.cues([
  { at: 0, set: { active: 0 } },
  { at: 2200, set: { active: 1 } },
  { at: 4500, set: { active: 2 } },
]);
function panelSeek(t) {
  seek(t);
  const st = panelCues.stateAt(t);
  chars.forEach((el, i) => { el.style.opacity = i === st.active ? '1' : '0.72'; });
}
window.scene = { seek: panelSeek };
"""

QUOTE_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const q = root.querySelector('[data-quote]');
const a = root.querySelector('[data-author]');
if (q) q.textContent = p.quote || '';
if (a) a.textContent = p.author || '';
function seek(t) {
  const el = root.querySelector('.obj-priest');
  if (el) {
    const head = el.querySelector('[data-rig="head"]');
    const mouth = el.querySelector('[data-rig="mouth"]');
    if (head) head.style.transform = `rotate(${Math.sin(t / 1200) * 1.4}deg)`;
    if (mouth) mouth.style.transform = `scaleY(${0.7 + Math.abs(Math.sin(t / 170)) * 0.5})`;
  }
}
window.scene = { seek };
"""

HISTORY_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const figures = Array.from(root.querySelectorAll('.period-figure'));
const cap = root.querySelector('[data-caption]');
if (cap) cap.textContent = p.caption || '';
function seek(t) {
  figures.forEach((el, i) => {
    el.style.transform = `translateY(${Math.sin(t / 1400 + i) * 2.2}px) rotate(${Math.sin(t / 2200 + i) * 0.6}deg)`;
  });
}
window.scene = { seek };
"""

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

CAPTION_CSS = """
.prav-caption { position:absolute; left:6%; bottom:8%; z-index:50; padding:1.3vh 1.5vw;
  border-left:0.65vmin solid var(--brand-amber); background:rgba(10,10,12,.72);
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }
.prav-caption span { font-family:var(--font-heading); font-size:clamp(14px,1.6vw,26px); color:var(--text-primary); }
"""

TIMELINE_CSS = CAPTION_CSS + """
.studio-lower-third { display:none; }
.prav-timeline { position:absolute; left:7%; right:7%; bottom:12%; z-index:50; }
.prav-timeline .rail { position:relative; height:2px; background:rgba(226,232,240,.18); }
.prav-timeline .progress { position:absolute; inset:0; transform-origin:left center; transform:scaleX(0);
  background:linear-gradient(90deg,var(--brand-amber),var(--brand-light-blue)); }
.prav-timeline .ev { position:absolute; top:-1.4vh; transform:translateX(-50%); text-align:center; min-width:12vw; }
.prav-timeline .dot { width:1.4vmin; height:1.4vmin; border-radius:50%; background:var(--brand-amber);
  margin:0 auto 1.4vh; box-shadow:0 0 1.4vmin rgba(212,168,67,.5); }
.prav-timeline .year { font-family:var(--font-mono); font-size:clamp(9px,1vw,14px); letter-spacing:.12em; color:var(--brand-amber); }
.prav-timeline .label { margin-top:.6vh; font-family:var(--font-heading); font-size:clamp(10px,1.1vw,16px); color:var(--text-primary); }
"""

TIMELINE_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const progress = root.querySelector('[data-progress]');
const cap = root.querySelector('[data-caption]');
if (cap) cap.textContent = p.caption || '';
const total = Number(p.timeline_duration) || 7000;
function seek(t) {
  if (progress) progress.style.transform = `scaleX(${Math.max(0, Math.min(1, t / total))})`;
  const ltName = root.querySelector('[data-lt-name]');
  if (ltName) ltName.textContent = p.host_name || 'Ведущий';
}
window.scene = { seek };
"""

def install(environments, objects, templates, compose):
    environments.extend(ENVIRONMENTS)
    objects.extend(CHARACTERS + FIGURES + PROPS)

    studio_css = """
.layer-actors .obj-host { left:24%; bottom:10%; width:42vmin; height:54vmin; }
.layer-actors .obj-cohost { left:68%; bottom:10%; width:38vmin; height:50vmin; }
.layer-actors .obj-priest { left:43%; bottom:8%; width:33vmin; height:45vmin; }
.layer-actors .obj-historian { left:16%; bottom:8%; width:32vmin; height:44vmin; }
.layer-actors .obj-sociologist { left:64%; bottom:8%; width:32vmin; height:44vmin; }
.layer-objects .obj-studio-monitor { left:58%; bottom:40%; width:36vmin; height:23vmin; }
"""
    history_css = """
.layer-actors .obj-host { left:14%; bottom:12%; width:22vmin; height:48vmin; }
.layer-actors .obj-historian { left:54%; bottom:12%; width:21vmin; height:46vmin; }
.layer-actors .obj-peasant { left:80%; bottom:12%; width:16vmin; height:38vmin; opacity:.85; }
"""
    church_css = """
.layer-actors .obj-priest { left:68%; bottom:14%; width:19vmin; height:44vmin; }
.prav-quote { position:absolute; left:8%; top:18%; width:48%; z-index:50;
  font-family:var(--font-heading); color:var(--text-primary); text-shadow:0 2px 12px rgba(0,0,0,.6); }
.prav-quote .mark { font-size:clamp(60px,8vw,120px); line-height:.6; color:var(--brand-amber); opacity:.55; }
.prav-quote blockquote { margin:0; font-size:clamp(22px,2.8vw,44px); line-height:1.15; letter-spacing:-.02em; }
.prav-quote .author { margin-top:2.4vh; font-family:var(--font-mono); font-size:clamp(10px,1vw,14px);
  letter-spacing:.14em; text-transform:uppercase; color:var(--brand-amber); }
"""
    studio_styles = {
        "host": "left:24%;bottom:10%;width:42vmin;height:54vmin",
        "cohost": "left:68%;bottom:10%;width:38vmin;height:50vmin",
        "priest": "left:43%;bottom:8%;width:33vmin;height:45vmin",
        "historian": "left:16%;bottom:8%;width:32vmin;height:44vmin",
        "sociologist": "left:64%;bottom:8%;width:32vmin;height:44vmin",
        "studio-monitor": "left:58%;bottom:40%;width:36vmin;height:23vmin",
    }
    history_styles = {
        "figure-peasant": "left:16%;bottom:8%;width:12vmin;height:36vmin",
        "figure-warrior": "left:38%;bottom:8%;width:13vmin;height:38vmin",
        "figure-monk": "left:60%;bottom:8%;width:12vmin;height:36vmin",
        "figure-worker": "left:78%;bottom:8%;width:12vmin;height:36vmin",
    }
    church_styles = {"priest": "left:68%;bottom:14%;width:34vmin;height:46vmin"}
    timeline_styles = {"host": "left:24%;bottom:10%;width:42vmin;height:54vmin", "studio-monitor": "left:58%;bottom:40%;width:36vmin;height:23vmin"}

    templates.extend([
        compose(
            "studio-prav", ["host", "studio-monitor"], STUDIO_JS,
            title="Prav · Studio host", slug="prav-studio-host",
            description="Студия «Механизм»: ведущий, монитор с картинкой/видео.",
            tags=["pravoslavie", "studio", "host"],
            duration=6000,
            props_schema={
                "host_name": {"type": "text", "label": "Имя ведущего"},
                "monitor_media": {"type": "image", "label": "Картинка на мониторе"},
                "monitor_video": {"type": "video", "label": "Видео на мониторе"},
            },
            default_props={"host_name": "Ведущий", "host_role": "МЕХАНИЗМ · авторский разбор", "monitor_media": "", "monitor_video": ""},
            extra_css=studio_css + STUDIO_FRONT_CSS,
            extra_html=STUDIO_FRONT_HTML,
            object_styles=studio_styles,
        ),
        compose(
            "studio-prav", ["host", "priest", "historian", "studio-monitor"], PANEL_JS,
            title="Prav · Studio panel", slug="prav-studio-panel",
            description="Панель: ведущий, священник, историк; монитор с медиа.",
            tags=["pravoslavie", "studio", "panel"],
            duration=7000,
            props_schema={
                "monitor_media": {"type": "image", "label": "Картинка на мониторе"},
                "monitor_video": {"type": "video", "label": "Видео на мониторе"},
            },
            default_props={"monitor_media": "", "monitor_video": ""},
            extra_css=studio_css + STUDIO_FRONT_CSS,
            extra_html=STUDIO_FRONT_HTML,
            object_styles=studio_styles,
        ),
        compose(
            "studio-prav", ["host", "sociologist", "studio-monitor"], STUDIO_JS,
            title="Prav · Sociologist", slug="prav-studio-sociologist",
            description="Ведущий и социолог в студии.",
            tags=["pravoslavie", "studio", "sociologist"],
            duration=6000,
            props_schema={"monitor_media": {"type": "image", "label": "Медиа"}},
            default_props={"monitor_media": ""},
            extra_css=studio_css + STUDIO_FRONT_CSS,
            extra_html=STUDIO_FRONT_HTML,
            object_styles=studio_styles,
        ),
        compose(
            "empire", ["figure-peasant", "figure-warrior", "figure-monk"], HISTORY_JS,
            title="Prav · Empire history", slug="prav-empire-history",
            description="Историческая сцена: империя и массовка эпохи.",
            tags=["pravoslavie", "history", "empire"],
            duration=7000,
            props_schema={"caption": {"type": "text", "label": "Подпись"}},
            default_props={"caption": "Империя накануне"},
            extra_css=history_css + CAPTION_CSS,
            extra_html='<div class="prav-caption"><span data-caption></span></div>',
            object_styles=history_styles,
        ),
        compose(
            "ancient-rus", ["figure-peasant", "figure-monk", "figure-warrior"], HISTORY_JS,
            title="Prav · Ancient Rus", slug="prav-ancient-rus",
            description="Древняя Русь: ведущий, историк, прихожанка; подпись эпохи.",
            tags=["pravoslavie", "history", "ancient-rus"],
            duration=7000,
            props_schema={"caption": {"type": "text", "label": "Подпись"}},
            default_props={"caption": "Древняя Русь · до империи"},
            extra_css=history_css + CAPTION_CSS,
            extra_html='<div class="prav-caption"><span data-caption></span></div>',
            object_styles=history_styles,
        ),
        compose(
            "soviet", ["figure-worker", "figure-peasant", "figure-warrior"], HISTORY_JS,
            title="Prav · Soviet history", slug="prav-soviet-history",
            description="Советский город: ведущий, историк, горожанин; подпись эпохи.",
            tags=["pravoslavie", "history", "soviet"],
            duration=7000,
            props_schema={"caption": {"type": "text", "label": "Подпись"}},
            default_props={"caption": "Советский город · 1930-е"},
            extra_css=history_css + CAPTION_CSS,
            extra_html='<div class="prav-caption"><span data-caption></span></div>',
            object_styles=history_styles,
        ),
        compose(
            "studio-prav", ["host", "studio-monitor"], TIMELINE_JS,
            title="Prav · Timeline", slug="prav-timeline",
            description="Таймлайн эпох: 1905 → 1917 → 1937 → 1953 → 1991.",
            tags=["pravoslavie", "history", "timeline"],
            duration=7000,
            props_schema={"caption": {"type": "text", "label": "Заголовок"}, "timeline_duration": {"type": "integer", "label": "Длительность, мс"}},
            default_props={"caption": "Сто лет упадка", "timeline_duration": 7000},
            extra_css=studio_css + STUDIO_FRONT_CSS + TIMELINE_CSS,
            object_styles=timeline_styles,
            extra_html=STUDIO_FRONT_HTML + '''<div class="prav-timeline">
  <div class="prav-caption" style="left:0;bottom:calc(100% + 2.6vh);background:transparent;backdrop-filter:none;border-left:0;padding:0;">
    <span data-caption></span>
  </div>
  <div class="rail"><div class="progress" data-progress></div></div>
  <div class="ev" style="left:10%"><div class="dot"></div><div class="year">1905</div><div class="label">Кровавое воскресенье</div></div>
  <div class="ev" style="left:30%"><div class="dot"></div><div class="year">1917</div><div class="label">Революция</div></div>
  <div class="ev" style="left:50%"><div class="dot"></div><div class="year">1937</div><div class="label">Террор</div></div>
  <div class="ev" style="left:70%"><div class="dot"></div><div class="year">1953</div><div class="label">После войны</div></div>
  <div class="ev" style="left:90%"><div class="dot"></div><div class="year">1991</div><div class="label">Свобода</div></div>
</div>''',
        ),
        compose(
            "church", ["priest"], QUOTE_JS,
            title="Prav · Church quote", slug="prav-church-quote",
            description="Храм, священник и крупная цитата.",
            tags=["pravoslavie", "church", "quote"],
            duration=6000,
            props_schema={"quote": {"type": "long_text", "label": "Цитата"}, "author": {"type": "text", "label": "Автор"}},
            default_props={"quote": "Вера на языке, а сердце в стороне.", "author": "По мотивам Писания"},
            extra_css=church_css,
            extra_html='<div class="prav-quote"><div class="mark">“</div><blockquote data-quote></blockquote><div class="author" data-author></div></div>',
            object_styles=church_styles,
        ),
        compose(
            "studio-prav", ["host", "cohost", "studio-monitor"], STUDIO_JS,
            title="Prav · Outro", slug="prav-outro",
            description="Финальная сцена: ведущий и соведущая в студии.",
            tags=["pravoslavie", "outro", "studio"],
            duration=5000,
            props_schema={"headline": {"type": "text", "label": "Заголовок"}, "handle": {"type": "text", "label": "Контакт"}},
            default_props={"headline": "Дальше — самое горькое", "handle": "@mechanism"},
            object_styles=studio_styles,
            extra_css=studio_css + STUDIO_FRONT_CSS + """
.prav-outro { position:absolute; left:8%; bottom:10%; z-index:50; }
.prav-outro h2 { margin:0; font-family:var(--font-heading); font-size:clamp(28px,3.6vw,54px); color:var(--text-primary); }
.prav-outro .handle { margin-top:1.6vh; font-family:var(--font-mono); color:var(--brand-amber); letter-spacing:.12em; }
""",
            extra_html=STUDIO_FRONT_HTML + '<div class="prav-outro"><h2 data-headline></h2><div class="handle" data-handle></div></div>',
        ),
    ])
    # The outro headline/handle need a tiny JS hook; append to the generated template JS.
    templates[-1]["code"]["js"] += """
const po = document.querySelector('.prav-outro');
const h = document.querySelector('[data-headline]');
const hd = document.querySelector('[data-handle]');
if (h) h.textContent = (window.__sceneProps || {}).headline || '';
if (hd) hd.textContent = (window.__sceneProps || {}).handle || '';
"""
