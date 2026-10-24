import re

from . import character_rig
"""Built-in 2D world library: environments, physical objects, scene templates.

Not UI cards. This is a content factory primitive:
  environments — forest, city, mountains, office, studio
  objects      — car, road, tree, pine, cloud, bird, building, lamp, desk, ...
  templates    — complete scenes composed from an environment + objects + cues

Every scene is deterministic: window.scene.seek(t) is the only clock.
SceneKit (window.SceneKit in the iframe) gives cues/integrate/mechanism helpers.
"""

BASE_CSS = """
.scene { position:absolute; inset:0; overflow:hidden; background:var(--bg-base);
  color:var(--text-primary); font-family:var(--font-sans); }
.scene * { box-sizing:border-box; }
.scene > .layer { position:absolute; inset:0; }
.layer-world { z-index:0; }
.layer-objects { z-index:10; }
.layer-actors { z-index:20; }
.layer-fx { z-index:30; pointer-events:none; }
.layer-overlay { z-index:40; pointer-events:none; }
"""

# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENTS
# ─────────────────────────────────────────────────────────────────────────────

FOREST = {
    "slug": "forest",
    "title": "Лес",
    "description": "Хвойный лес, горы на горизонте, туман. Слои для параллакса.",
    "tags": ["nature", "day", "forest"],
    "layers": ["sky", "sun", "ridge", "pines-far", "pines-near", "ground", "fog"],
    "html": """
<div class="env env-forest">
  <div class="sky"></div>
  <div class="sun"></div>
  <svg class="ridge" data-depth="0.10" viewBox="0 0 1920 1080" preserveAspectRatio="none">
    <polygon points="0,720 250,470 500,660 760,430 1040,680 1310,470 1600,650 1920,510 1920,1080 0,1080" fill="#123039" opacity=".85"/>
    <polygon points="0,820 230,640 470,780 720,590 1000,800 1260,620 1540,790 1820,640 1920,720 1920,1080 0,1080" fill="#0C242B" opacity=".92"/>
  </svg>
  <svg class="pines-far" data-depth="0.22" viewBox="0 0 1920 420" preserveAspectRatio="none">
    <defs>
      <pattern id="forestPineFar" width="92" height="240" patternUnits="userSpaceOnUse">
        <polygon points="46,10 84,230 8,230" fill="#123B34"/>
        <polygon points="46,52 78,230 14,230" fill="#174A3E" opacity=".75"/>
      </pattern>
    </defs>
    <rect width="1920" height="420" fill="url(#forestPineFar)"/>
  </svg>
  <svg class="pines-near" data-depth="0.42" viewBox="0 0 1920 520" preserveAspectRatio="none">
    <defs>
      <pattern id="forestPineNear" width="150" height="340" patternUnits="userSpaceOnUse">
        <polygon points="75,0 140,320 10,320" fill="#08201C"/>
        <polygon points="75,70 126,320 24,320" fill="#0B2C24" opacity=".85"/>
      </pattern>
    </defs>
    <rect width="1920" height="520" fill="url(#forestPineNear)"/>
  </svg>
  <div class="ground"></div>
  <div class="fog"></div>
</div>""",
    "css": """
.env-forest { position:absolute; inset:0; overflow:hidden; background:#08161C; }
.env-forest .sky { position:absolute; inset:0; background:linear-gradient(180deg,#0A1A2A 0%,#123447 42%,#1B4B49 68%,#24553F 100%); }
.env-forest .sun { position:absolute; left:68%; top:10%; width:20vmin; height:20vmin; border-radius:50%;
  background:radial-gradient(circle,#FFF0B8 0%,#FFC857 32%,rgba(255,200,87,0) 70%); filter:blur(2px); opacity:.95; }
.env-forest .ridge { position:absolute; left:-6%; right:-6%; bottom:24%; width:112%; height:42%; }
.env-forest .pines-far { position:absolute; left:-8%; right:-8%; bottom:15%; width:116%; height:36%; opacity:.75; }
.env-forest .pines-near { position:absolute; left:-6%; right:-6%; bottom:-4%; width:112%; height:48%; }
.env-forest .ground { position:absolute; left:0; right:0; bottom:0; height:24%;
  background:linear-gradient(180deg,#12382E 0%,#071A16 100%); }
.env-forest .fog { position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(180deg,transparent 38%,rgba(150,200,180,.08) 66%,transparent 92%); }
""",
}

CITY = {
    "slug": "city",
    "title": "Город",
    "description": "Ночной город: небо, силуэты, окна, улица.",
    "tags": ["city", "night", "urban"],
    "layers": ["sky", "stars", "moon", "skyline", "buildings", "street"],
    "html": """
<div class="env env-city">
  <div class="sky"></div>
  <div class="stars"></div>
  <div class="moon"></div>
  <svg class="skyline" data-depth="0.12" viewBox="0 0 1920 1080" preserveAspectRatio="none">
    <polygon points="0,760 80,760 80,620 160,620 160,700 250,700 250,540 340,540 340,700 430,700 430,600 520,600 520,720 620,720 620,520 720,520 720,680 820,680 820,580 930,580 930,740 1040,740 1040,560 1150,560 1150,700 1260,700 1260,520 1370,520 1370,680 1480,680 1480,600 1590,600 1590,720 1700,720 1700,560 1810,560 1810,700 1920,700 1920,1080 0,1080" fill="#0B1324"/>
  </svg>
  <div class="buildings" data-depth="0.28">
    <i style="--x:2%;--w:12%;--h:46%"></i>
    <i style="--x:16%;--w:10%;--h:62%"></i>
    <i style="--x:28%;--w:14%;--h:38%"></i>
    <i style="--x:44%;--w:9%;--h:70%"></i>
    <i style="--x:55%;--w:15%;--h:52%"></i>
    <i style="--x:72%;--w:11%;--h:78%"></i>
    <i style="--x:85%;--w:13%;--h:44%"></i>
  </div>
  <div class="street"></div>
</div>""",
    "css": """
.env-city { position:absolute; inset:0; overflow:hidden; background:#050814; }
.env-city .sky { position:absolute; inset:0; background:linear-gradient(180deg,#050814 0%,#0B1330 52%,#1A2445 78%,#2A2140 100%); }
.env-city .stars { position:absolute; inset:0; opacity:.7;
  background-image:radial-gradient(circle,rgba(255,255,255,.85) 1px,transparent 1.4px),
                   radial-gradient(circle,rgba(180,210,255,.55) 1px,transparent 1.4px);
  background-size:140px 140px, 220px 220px; background-position:0 0, 40px 60px; }
.env-city .moon { position:absolute; right:16%; top:10%; width:9vmin; height:9vmin; border-radius:50%;
  background:radial-gradient(circle at 38% 38%,#F8FAFC,#CBD5E1 62%,#94A3B8 100%);
  box-shadow:0 0 8vmin rgba(200,220,255,.35); }
.env-city .skyline { position:absolute; left:-4%; right:-4%; bottom:14%; width:108%; height:46%; }
.env-city .buildings { position:absolute; left:-6%; right:-6%; bottom:14%; height:58%; }
.env-city .buildings i { position:absolute; left:var(--x); bottom:0; width:var(--w); height:var(--h);
  background:linear-gradient(180deg,#101A2E,#0A1020); border:1px solid rgba(160,190,255,.08);
  border-radius:3px 3px 0 0; }
.env-city .buildings i::after { content:''; position:absolute; inset:7% 12%;
  background-image:repeating-linear-gradient(90deg,transparent 0 18%,rgba(255,214,120,.8) 18% 26%,transparent 26% 44%),
                   repeating-linear-gradient(180deg,transparent 0 12%,rgba(255,214,120,.75) 12% 19%,transparent 19% 36%);
  background-size:44px 34px; opacity:.55; }
.env-city .street { position:absolute; left:0; right:0; bottom:0; height:15%;
  background:linear-gradient(180deg,#111827,#05060A); box-shadow:inset 0 2px 0 rgba(255,255,255,.05); }
""",
}

MOUNTAINS = {
    "slug": "mountains",
    "title": "Горы",
    "description": "Рассвет, слои гор со снежными вершинами, облака.",
    "tags": ["nature", "dawn", "mountains"],
    "layers": ["sky", "sun", "ridge-far", "ridge-mid", "ridge-near", "valley"],
    "html": """
<div class="env env-mountains">
  <div class="sky"></div>
  <div class="sun"></div>
  <svg class="ridge-far" data-depth="0.08" viewBox="0 0 1920 1080" preserveAspectRatio="none">
    <polygon points="0,650 180,420 360,600 560,300 760,560 980,360 1180,590 1400,390 1620,580 1800,430 1920,560 1920,1080 0,1080" fill="#5B5F82" opacity=".7"/>
    <polygon points="520,380 560,300 610,395 575,375 545,390" fill="#F1F5F9" opacity=".9"/>
    <polygon points="940,430 980,360 1030,445 995,425 965,440" fill="#F1F5F9" opacity=".85"/>
  </svg>
  <svg class="ridge-mid" data-depth="0.18" viewBox="0 0 1920 1080" preserveAspectRatio="none">
    <polygon points="0,760 220,540 430,720 680,470 930,730 1180,520 1420,740 1660,540 1920,720 1920,1080 0,1080" fill="#3C3F60" opacity=".9"/>
    <polygon points="640,520 680,470 730,535 695,515 665,532" fill="#E2E8F0" opacity=".85"/>
    <polygon points="1140,565 1180,520 1230,580 1195,560 1165,575" fill="#E2E8F0" opacity=".8"/>
  </svg>
  <svg class="ridge-near" data-depth="0.30" viewBox="0 0 1920 1080" preserveAspectRatio="none">
    <polygon points="0,880 260,690 500,860 760,640 1040,880 1300,700 1580,900 1820,720 1920,800 1920,1080 0,1080" fill="#24263F"/>
  </svg>
  <div class="valley"></div>
</div>""",
    "css": """
.env-mountains { position:absolute; inset:0; overflow:hidden; background:#1B2440; }
.env-mountains .sky { position:absolute; inset:0;
  background:linear-gradient(180deg,#141B3A 0%,#3A3A63 38%,#8C5A72 62%,#E39A6A 84%,#F3C48A 100%); }
.env-mountains .sun { position:absolute; left:68%; top:48%; width:16vmin; height:16vmin; border-radius:50%;
  background:radial-gradient(circle,#FFF4C7 0%,#FFD27A 38%,rgba(255,210,122,0) 72%); filter:blur(1px); }
.env-mountains .ridge-far { position:absolute; left:-5%; right:-5%; bottom:18%; width:110%; height:52%; }
.env-mountains .ridge-mid { position:absolute; left:-6%; right:-6%; bottom:8%; width:112%; height:56%; }
.env-mountains .ridge-near { position:absolute; left:-8%; right:-8%; bottom:-8%; width:116%; height:54%; }
.env-mountains .valley { position:absolute; left:0; right:0; bottom:0; height:22%;
  background:linear-gradient(180deg,#1A1C32,#0B0D18); }
""",
}

OFFICE = {
    "slug": "office",
    "title": "Офис",
    "description": "Интерьер: стена, окно с городом, пол. Мебель добавляется объектами.",
    "tags": ["interior", "office", "day"],
    "layers": ["wall", "window", "floor"],
    "html": """
<div class="env env-office">
  <div class="wall"></div>
  <div class="window">
    <div class="window-sky"></div>
    <div class="window-city"></div>
    <div class="window-frame"></div>
  </div>
  <div class="art"><i></i><i></i><i></i></div>
  <div class="floor"></div>
  <div class="rug"></div>
</div>""",
    "css": """
.env-office { position:absolute; inset:0; overflow:hidden; background:#E8E2D8; }
.env-office .wall { position:absolute; inset:0 0 22% 0; background:linear-gradient(180deg,#EFEAE1,#D8D0C4); }
.env-office .window { position:absolute; left:58%; top:10%; width:32%; height:46%;
  border:10px solid #B9AE9E; border-radius:4px; overflow:hidden; box-shadow:0 2vh 4vh rgba(60,50,40,.18); }
.env-office .window-sky { position:absolute; inset:0; background:linear-gradient(180deg,#8EC5E8,#D9EDF7 60%,#F2E8D5); }
.env-office .window-city { position:absolute; left:0; right:0; bottom:0; height:52%;
  background:linear-gradient(180deg,transparent,rgba(90,110,130,.22));
  clip-path:polygon(0 52%,8% 52%,8% 38%,16% 38%,16% 56%,24% 56%,24% 30%,32% 30%,32% 50%,41% 50%,41% 40%,50% 40%,50% 58%,60% 58%,60% 34%,70% 34%,70% 52%,80% 52%,80% 42%,90% 42%,90% 60%,100% 60%,100% 100%,0 100%); }
.env-office .window-frame { position:absolute; left:50%; top:0; bottom:0; width:3px; background:#B9AE9E; transform:translateX(-50%); }
.env-office .art { position:absolute; left:16%; top:14%; width:18%; height:22%; background:#F7F3EC;
  border:8px solid #B9AE9E; box-shadow:0 1vh 2vh rgba(60,50,40,.12); display:flex; gap:6%; padding:6%; }
.env-office .art i { flex:1; border-radius:50% 50% 0 0; background:#C9A27E; }
.env-office .art i:nth-child(2) { background:#7E9A8B; height:70%; align-self:flex-end; }
.env-office .art i:nth-child(3) { background:#6F86A6; height:50%; align-self:flex-end; }
.env-office .floor { position:absolute; left:0; right:0; bottom:0; height:24%;
  background:linear-gradient(180deg,#B79F80,#8C6F52); }
.env-office .rug { position:absolute; left:18%; right:18%; bottom:2%; height:18%; border-radius:50%;
  background:radial-gradient(ellipse at center,#465A63 0%,#2E3B42 70%,rgba(0,0,0,0) 72%); opacity:.55; }
""",
}

STUDIO = {
    "slug": "studio",
    "title": "Студия",
    "description": "Тёмная студия: прожекторы, пол, дымка. Для интро и акцентов.",
    "tags": ["studio", "dark", "stage"],
    "layers": ["backdrop", "beams", "floor", "haze"],
    "html": """
<div class="env env-studio">
  <div class="backdrop"></div>
  <div class="beam beam-a"></div>
  <div class="beam beam-b"></div>
  <div class="beam beam-c"></div>
  <div class="floor"></div>
  <div class="haze"></div>
</div>""",
    "css": """
.env-studio { position:absolute; inset:0; overflow:hidden; background:#05070C; }
.env-studio .backdrop { position:absolute; inset:0;
  background:radial-gradient(circle at 50% 38%,#1B2740 0%,#0A0F1C 44%,#04060A 100%); }
.env-studio .floor { position:absolute; left:-10%; right:-10%; bottom:-6%; height:34%; border-radius:50% 50% 0 0;
  background:radial-gradient(ellipse at 50% 0%,#1A2436,#070A11 70%); }
.env-studio .beam { position:absolute; top:-10%; width:26%; height:95%; filter:blur(2px); opacity:.55;
  background:linear-gradient(180deg,rgba(120,170,255,.42),rgba(120,170,255,0) 78%);
  clip-path:polygon(46% 0,54% 0,100% 100%,0 100%); transform-origin:top center; }
.env-studio .beam-a { left:8%; transform:rotate(10deg); }
.env-studio .beam-b { left:37%; transform:rotate(-2deg); opacity:.4; }
.env-studio .beam-c { right:8%; transform:rotate(-12deg); }
.env-studio .haze { position:absolute; inset:0;
  background:radial-gradient(ellipse at 50% 70%,rgba(120,150,255,.08),transparent 60%); }
""",
}

ENVIRONMENTS = [FOREST, CITY, MOUNTAINS, OFFICE, STUDIO]

# ─────────────────────────────────────────────────────────────────────────────
# OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

CAR = {
    "slug": "car",
    "title": "Машина",
    "category": "transport",
    "description": "Машина с колёсами. Колёса вращаются через [data-wheel].",
    "tags": ["vehicle", "car", "transport"],
    "mechanics": ["wheels", "brake-light"],
    "html": """
<div class="obj-car" style="left:12%; bottom:18%; --car-color:#E4572E">
  <div class="car-shadow"></div>
  <div class="car-body"></div>
  <div class="car-cabin"></div>
  <div class="car-window"></div>
  <div class="car-light front"></div>
  <div class="car-light back"></div>
  <div class="wheel" data-wheel style="left:4.2vmin"></div>
  <div class="wheel" data-wheel style="right:4.2vmin"></div>
</div>""",
    "css": """
.obj-car { position:absolute; width:38vmin; height:16vmin; }
.obj-car .car-shadow { position:absolute; left:2%; right:2%; bottom:1.2vmin; height:2.2vmin; border-radius:50%;
  background:rgba(0,0,0,.45); filter:blur(0.6vmin); }
.obj-car .car-body { position:absolute; left:0; right:0; bottom:3vmin; height:7.2vmin;
  border-radius:2.4vmin 2.4vmin 1.1vmin 1.1vmin; background:var(--car-color,#E4572E);
  box-shadow:inset 0 -1.2vmin 0 rgba(0,0,0,.18), 0 0.6vmin 1.4vmin rgba(0,0,0,.35); }
.obj-car .car-cabin { position:absolute; left:9vmin; bottom:9.4vmin; width:17vmin; height:5.6vmin;
  border-radius:3.2vmin 3.2vmin 0 0; background:var(--car-color,#E4572E);
  box-shadow:inset 0 -0.8vmin 0 rgba(0,0,0,.14); }
.obj-car .car-window { position:absolute; left:11vmin; bottom:10.2vmin; width:13vmin; height:3.5vmin;
  border-radius:2.2vmin 2.2vmin 0 0; background:linear-gradient(180deg,#BFE3F5,#7FB2CC); opacity:.9; }
.obj-car .car-light { position:absolute; bottom:5.2vmin; width:1.8vmin; height:1.2vmin; border-radius:50%;
  background:#FFF3C4; box-shadow:0 0 1.6vmin #FFE08A; }
.obj-car .car-light.front { right:0.4vmin; }
.obj-car .car-light.back { left:0.4vmin; background:#FF6B6B; box-shadow:0 0 1.4vmin #FF6B6B; }
.obj-car .wheel { position:absolute; bottom:0; width:5.4vmin; height:5.4vmin; border-radius:50%;
  background:radial-gradient(circle at 50% 50%,#CBD5E1 0 20%,#1F2937 21% 58%,#0B0F14 59%);
  border:0.45vmin solid #0B0F14; }
.obj-car .wheel::after { content:''; position:absolute; inset:1.4vmin; border-radius:50%;
  background:conic-gradient(from 0deg,#94A3B8 0 8%,transparent 8% 25%,#94A3B8 25% 33%,transparent 33% 50%,
    #94A3B8 50% 58%,transparent 58% 75%,#94A3B8 75% 83%,transparent 83%); }
.obj-car.braking .car-light.back { background:#FF3B3B; box-shadow:0 0 2.4vmin #FF3B3B; }
""",
}

ROAD = {
    "slug": "road",
    "title": "Дорога",
    "category": "environment",
    "description": "Асфальт с перспективой и бегущей разметкой.",
    "tags": ["road", "ground"],
    "mechanics": ["dashes"],
    "html": """
<div class="obj-road">
  <div class="road-surface"></div>
  <div class="road-edge left"></div>
  <div class="road-edge right"></div>
  <div class="road-dashes"></div>
</div>""",
    "css": """
.obj-road { position:absolute; left:-8%; right:-8%; bottom:-2%; height:32%; overflow:hidden; }
.obj-road .road-surface { position:absolute; inset:0;
  background:linear-gradient(180deg,#1E232A,#0B0D10);
  clip-path:polygon(34% 0,66% 0,100% 100%,0 100%); }
.obj-road .road-edge { position:absolute; top:0; bottom:0; width:2.2%;
  background:rgba(226,232,240,.5); }
.obj-road .road-edge.left { left:33.4%; clip-path:polygon(0 0,100% 0,36% 100%,0 100%); }
.obj-road .road-edge.right { right:33.4%; clip-path:polygon(0 0,100% 0,100% 100%,64% 100%); }
.obj-road .road-dashes { position:absolute; left:-50%; right:-50%; top:0; bottom:0; width:200%;
  background:repeating-linear-gradient(180deg,transparent 0 7%,#E2E8F0 7% 10%,transparent 10% 18%);
  clip-path:polygon(49% 0,51% 0,56% 100%,44% 100%); opacity:.85; }
""",
}

TREE = {
    "slug": "tree",
    "title": "Дерево",
    "category": "nature",
    "description": "Лиственное дерево. Качается через transform-origin снизу.",
    "tags": ["nature", "tree"],
    "mechanics": ["sway"],
    "html": """
<div class="obj-tree" style="left:78%; bottom:22%; width:14vmin; height:30vmin">
  <div class="tree-trunk"></div>
  <div class="tree-crown"></div>
</div>""",
    "css": """
.obj-tree { position:absolute; transform-origin:50% 100%; }
.obj-tree .tree-trunk { position:absolute; left:46%; bottom:0; width:8%; height:58%;
  background:linear-gradient(90deg,#3B2416,#5A3A24); border-radius:2px; }
.obj-tree .tree-crown { position:absolute; left:0; right:0; top:0; height:76%; border-radius:50% 50% 44% 44%;
  background:radial-gradient(circle at 42% 32%,#3E8A5B,#1E5A3A 62%,#123A28 100%);
  box-shadow:inset -1vmin -1.4vmin 0 rgba(0,0,0,.18); }
""",
}

PINE = {
    "slug": "pine",
    "title": "Сосна",
    "category": "nature",
    "description": "Сосна из трёх ярусов. Качается.",
    "tags": ["nature", "pine"],
    "mechanics": ["sway"],
    "html": """
<div class="obj-pine" style="left:20%; bottom:24%; width:10vmin; height:32vmin">
  <div class="pine-trunk"></div>
  <i></i><i></i><i></i>
</div>""",
    "css": """
.obj-pine { position:absolute; transform-origin:50% 100%; }
.obj-pine .pine-trunk { position:absolute; left:47%; bottom:0; width:6%; height:34%; background:#3B2416; }
.obj-pine i { position:absolute; left:50%; transform:translateX(-50%); width:0; height:0;
  border-left:5vmin solid transparent; border-right:5vmin solid transparent; border-bottom:11vmin solid #17503A; }
.obj-pine i:nth-child(2) { bottom:22%; border-bottom-width:12vmin; border-left-width:5.6vmin; border-right-width:5.6vmin; }
.obj-pine i:nth-child(3) { bottom:40%; border-bottom-width:13vmin; border-left-width:6.2vmin; border-right-width:6.2vmin; background:#1B5C42; }
.obj-pine i:nth-child(4) { bottom:58%; border-bottom-width:14vmin; border-left-width:6.8vmin; border-right-width:6.8vmin; }
""",
}

CLOUD = {
    "slug": "cloud",
    "title": "Облако",
    "category": "nature",
    "description": "Мягкое облако, дрейфует по сцене.",
    "tags": ["sky", "cloud"],
    "mechanics": ["drift"],
    "html": """
<div class="obj-cloud" style="left:18%; top:16%">
  <i style="left:0;width:8vmin;height:6vmin"></i>
  <i style="left:5vmin;width:11vmin;height:8vmin"></i>
  <i style="left:12vmin;width:7vmin;height:5vmin"></i>
</div>""",
    "css": """
.obj-cloud { position:absolute; width:20vmin; height:9vmin; opacity:.8; }
.obj-cloud i { position:absolute; bottom:0; border-radius:50%; background:#DCE7F2;
  filter:blur(0.15vmin); }
""",
}

BIRD = {
    "slug": "bird",
    "title": "Птица",
    "category": "nature",
    "description": "Силуэт птицы с машущими крыльями.",
    "tags": ["nature", "bird"],
    "mechanics": ["flap"],
    "html": """
<svg class="obj-bird" viewBox="0 0 100 40" style="left:70%; top:30%; width:7vmin">
  <path class="wing-left" d="M50 22 C36 6, 18 4, 2 16 C20 14, 36 18, 50 24 Z" fill="#0B1118"/>
  <path class="wing-right" d="M50 22 C64 6, 82 4, 98 16 C80 14, 64 18, 50 24 Z" fill="#0B1118"/>
  <path d="M46 20 L54 20 L50 28 Z" fill="#0B1118"/>
</svg>""",
    "css": """
.obj-bird { position:absolute; transform-origin:50% 55%; }
.obj-bird .wing-left, .obj-bird .wing-right { transform-origin:50px 22px; }
""",
}

LAMP = {
    "slug": "street-lamp",
    "title": "Фонарь",
    "category": "city",
    "description": "Уличный фонарь со световым конусом.",
    "tags": ["city", "light"],
    "mechanics": ["flicker"],
    "html": """
<div class="obj-lamp" style="right:12%; bottom:16%; width:4vmin; height:32vmin">
  <div class="lamp-cone"></div>
  <div class="lamp-pole"></div>
  <div class="lamp-head"></div>
</div>""",
    "css": """
.obj-lamp { position:absolute; }
.obj-lamp .lamp-pole { position:absolute; left:46%; bottom:0; width:8%; height:86%;
  background:linear-gradient(90deg,#1F2937,#4B5563); border-radius:2px; }
.obj-lamp .lamp-head { position:absolute; left:18%; top:4%; width:64%; height:7%; border-radius:999px;
  background:linear-gradient(180deg,#FDE68A,#F59E0B); box-shadow:0 0 2vmin #FDE68A; }
.obj-lamp .lamp-cone { position:absolute; left:50%; top:8%; width:22vmin; height:28vmin;
  transform:translateX(-50%); background:linear-gradient(180deg,rgba(253,230,138,.38),rgba(253,230,138,0) 78%);
  clip-path:polygon(50% 0,100% 100%,0 100%); mix-blend-mode:screen; }
""",
}

BUILDING = {
    "slug": "building",
    "title": "Здание",
    "category": "city",
    "description": "Коробка с окнами. Масштабируется через width/height.",
    "tags": ["city", "building"],
    "mechanics": ["windows"],
    "html": """
<div class="obj-building" style="left:62%; bottom:16%; width:18vmin; height:42vmin">
  <div class="building-windows"></div>
</div>""",
    "css": """
.obj-building { position:absolute; background:linear-gradient(180deg,#121A2B,#0A1020);
  border:1px solid rgba(160,190,255,.08); border-radius:3px 3px 0 0; }
.obj-building .building-windows { position:absolute; inset:7% 12%;
  background-image:repeating-linear-gradient(90deg,transparent 0 18%,rgba(255,214,120,.8) 18% 26%,transparent 26% 44%),
                   repeating-linear-gradient(180deg,transparent 0 12%,rgba(255,214,120,.7) 12% 19%,transparent 19% 36%);
  background-size:44px 34px; opacity:.6; }
""",
}

DESK = {
    "slug": "desk",
    "title": "Стол",
    "category": "interior",
    "description": "Рабочий стол с тумбой.",
    "tags": ["office", "furniture"],
    "mechanics": [],
    "html": """
<div class="obj-desk" style="left:22%; bottom:18%; width:44vmin; height:18vmin">
  <div class="desk-top"></div>
  <div class="desk-leg left"></div>
  <div class="desk-leg right"></div>
  <div class="desk-drawer"></div>
</div>""",
    "css": """
.obj-desk { position:absolute; }
.obj-desk .desk-top { position:absolute; left:0; right:0; top:0; height:14%; border-radius:4px;
  background:linear-gradient(180deg,#8B5E3C,#6B4428); box-shadow:0 1vmin 2vmin rgba(0,0,0,.2); }
.obj-desk .desk-leg { position:absolute; bottom:0; width:5%; height:88%; background:#5A3924; }
.obj-desk .desk-leg.left { left:4%; } .obj-desk .desk-leg.right { right:4%; }
.obj-desk .desk-drawer { position:absolute; right:12%; bottom:4%; width:26%; height:56%; border-radius:3px;
  background:linear-gradient(180deg,#7A5133,#5A3924); }
""",
}

MONITOR = {
    "slug": "monitor",
    "title": "Монитор",
    "category": "interior",
    "description": "Монитор со свечением и строками интерфейса.",
    "tags": ["office", "screen"],
    "mechanics": ["glow"],
    "html": """
<div class="obj-monitor" style="left:30%; bottom:36%; width:26vmin; height:18vmin">
  <div class="monitor-screen"><i></i><i></i><i></i><i></i></div>
  <div class="monitor-neck"></div>
  <div class="monitor-base"></div>
</div>""",
    "css": """
.obj-monitor { position:absolute; }
.obj-monitor .monitor-screen { position:absolute; left:0; right:0; top:0; height:74%; border-radius:8px;
  background:linear-gradient(180deg,#0B1220,#101A2E); border:0.5vmin solid #111827; overflow:hidden;
  box-shadow:0 0 4vmin rgba(80,160,255,.18); }
.obj-monitor .monitor-screen i { display:block; height:7%; margin:6% 8%; border-radius:2px;
  background:linear-gradient(90deg,#3B82F6,#38BDF8); opacity:.7; }
.obj-monitor .monitor-screen i:nth-child(2) { width:64%; opacity:.45; }
.obj-monitor .monitor-screen i:nth-child(3) { width:78%; opacity:.3; }
.obj-monitor .monitor-screen i:nth-child(4) { width:44%; opacity:.25; }
.obj-monitor .monitor-neck { position:absolute; left:46%; bottom:8%; width:8%; height:14%; background:#1F2937; }
.obj-monitor .monitor-base { position:absolute; left:34%; bottom:3%; width:32%; height:7%; border-radius:999px;
  background:#1F2937; }
""",
}

COFFEE = {
    "slug": "coffee",
    "title": "Кофе",
    "category": "interior",
    "description": "Кружка с паром.",
    "tags": ["office", "prop"],
    "mechanics": ["steam"],
    "html": """
<div class="obj-coffee" style="left:52%; bottom:36%; width:6vmin; height:8vmin">
  <div class="coffee-steam s1"></div>
  <div class="coffee-steam s2"></div>
  <div class="coffee-mug"></div>
</div>""",
    "css": """
.obj-coffee { position:absolute; }
.obj-coffee .coffee-mug { position:absolute; left:8%; bottom:0; width:70%; height:60%; border-radius:0 0 40% 40%;
  background:linear-gradient(180deg,#F8FAFC,#CBD5E1); box-shadow:inset 0 -3px 0 #94A3B8; }
.obj-coffee .coffee-mug::after { content:''; position:absolute; right:-28%; top:18%; width:36%; height:44%;
  border:4px solid #E2E8F0; border-left:0; border-radius:0 999px 999px 0; }
.obj-coffee .coffee-steam { position:absolute; bottom:56%; width:22%; height:46%; border-radius:50%;
  background:linear-gradient(180deg,rgba(255,255,255,.6),rgba(255,255,255,0)); filter:blur(2px); }
.obj-coffee .coffee-steam.s1 { left:22%; } .obj-coffee .coffee-steam.s2 { left:50%; opacity:.6; }
""",
}

PLANT = {
    "slug": "plant",
    "title": "Растение",
    "category": "interior",
    "description": "Горшок с листьями. Качается.",
    "tags": ["office", "nature"],
    "mechanics": ["sway"],
    "html": """
<div class="obj-plant" style="right:18%; bottom:22%; width:12vmin; height:26vmin">
  <div class="plant-pot"></div>
  <div class="plant-leaves"><i></i><i></i><i></i><i></i><i></i></div>
</div>""",
    "css": """
.obj-plant { position:absolute; transform-origin:50% 100%; }
.obj-plant .plant-pot { position:absolute; left:24%; bottom:0; width:52%; height:28%; border-radius:0 0 30% 30%;
  background:linear-gradient(180deg,#B4532A,#7C3519); }
.obj-plant .plant-leaves { position:absolute; left:0; right:0; bottom:24%; height:76%; }
.obj-plant .plant-leaves i { position:absolute; left:46%; bottom:0; width:16%; height:70%; border-radius:50% 50% 40% 40%;
  background:linear-gradient(180deg,#2F8F5B,#145A36); transform-origin:50% 100%; }
.obj-plant .plant-leaves i:nth-child(1) { transform:rotate(-28deg); }
.obj-plant .plant-leaves i:nth-child(2) { transform:rotate(-12deg); height:84%; }
.obj-plant .plant-leaves i:nth-child(3) { transform:rotate(0deg); height:92%; }
.obj-plant .plant-leaves i:nth-child(4) { transform:rotate(14deg); height:82%; }
.obj-plant .plant-leaves i:nth-child(5) { transform:rotate(30deg); }
""",
}

PERSON = {
    "slug": "person",
    "title": "Человек",
    "category": "character",
    "description": "Силуэт человека. Позже станет ригом с липсинком.",
    "tags": ["character", "silhouette"],
    "mechanics": ["breathe"],
    "html": """
<svg class="obj-person" viewBox="0 0 100 220" style="left:66%; bottom:18%; width:10vmin; height:26vmin">
  <circle cx="50" cy="30" r="18" fill="#101820"/>
  <path d="M32 54 Q50 44 68 54 L74 122 Q50 132 26 122 Z" fill="#101820"/>
  <path d="M34 120 L28 200 L40 200 L48 130 Z" fill="#101820"/>
  <path d="M66 120 L72 200 L60 200 L52 130 Z" fill="#101820"/>
</svg>""",
    "css": """
.obj-person { position:absolute; transform-origin:50% 100%; }
""",
}

TRAFFIC_LIGHT = {
    "slug": "traffic-light",
    "title": "Светофор",
    "category": "city",
    "description": "Светофор с переключением по фазе.",
    "tags": ["city", "traffic"],
    "mechanics": ["cycle"],
    "html": """
<div class="obj-traffic" style="right:26%; bottom:16%; width:4vmin; height:16vmin">
  <div class="traffic-pole"></div>
  <div class="traffic-box"><i class="red"></i><i class="yellow"></i><i class="green"></i></div>
</div>""",
    "css": """
.obj-traffic { position:absolute; }
.obj-traffic .traffic-pole { position:absolute; left:46%; bottom:0; width:8%; height:62%; background:#1F2937; }
.obj-traffic .traffic-box { position:absolute; left:0; top:0; width:100%; height:44%; border-radius:999px;
  background:#111827; border:2px solid #374151; display:flex; flex-direction:column; align-items:center;
  justify-content:space-evenly; padding:8% 0; }
.obj-traffic .traffic-box i { width:56%; aspect-ratio:1; border-radius:50%; background:#1F2937; opacity:.35; }
.obj-traffic .traffic-box i.on { opacity:1; box-shadow:0 0 2vmin currentColor; }
.obj-traffic .traffic-box i.red { color:#EF4444; background:#EF4444; }
.obj-traffic .traffic-box i.yellow { color:#F59E0B; background:#F59E0B; }
.obj-traffic .traffic-box i.green { color:#10B981; background:#10B981; }
""",
}

SUN = {
    "slug": "sun",
    "title": "Солнце",
    "category": "sky",
    "description": "Солнце с ореолом.",
    "tags": ["sky", "light"],
    "mechanics": [],
    "html": '<div class="obj-sun" style="right:18%; top:12%; width:14vmin; height:14vmin"></div>',
    "css": """
.obj-sun { position:absolute; border-radius:50%;
  background:radial-gradient(circle,#FFF6C8 0%,#FFD166 46%,rgba(255,209,102,0) 72%);
  filter:blur(1px); }
""",
}

MOON = {
    "slug": "moon",
    "title": "Луна",
    "category": "sky",
    "description": "Луна с мягким свечением.",
    "tags": ["sky", "night"],
    "mechanics": [],
    "html": '<div class="obj-moon" style="right:16%; top:12%; width:8vmin; height:8vmin"></div>',
    "css": """
.obj-moon { position:absolute; border-radius:50%;
  background:radial-gradient(circle at 38% 38%,#F8FAFC,#CBD5E1 64%,#94A3B8);
  box-shadow:0 0 7vmin rgba(200,220,255,.4); }
""",
}

CHARACTER = {
    "slug": "character",
    "title": "Персонаж (риг)",
    "category": "character",
    "description": "Управляемый SVG-риг: голова, объём, взгляд, моргание, брови-настроение, одежда с деталями, обувь, 10 визёмов рта. Драйвер — SceneKit.characterRig.",
    "tags": ["character", "rig", "person", "lipsync", "visemes"],
    "mechanics": ["lipsync", "blink", "breathe", "sway", "gaze", "gesture", "walk", "mood", "hair-lag"],
    "rig": {
        "type": "svg",
        "parts": ["root", "head", "hair", "gaze", "lid-left", "lid-right", "brow-left", "brow-right", "mouth", "torso", "arm-left", "arm-right", "leg-left", "leg-right"],
        "clips": ["idle", "walk", "talk", "blink"],
        "visemes": 10,
        "driver": "SceneKit.characterRig",
        "palette": ["skin", "hair", "shirt", "pants", "shoe", "iris", "line"],
    },
    "html": character_rig.CHARACTER_HTML,
    "css": character_rig.CHARACTER_CSS,
}

PORTRAIT = {
    "slug": "portrait",
    "title": "Персонаж (нарисованный портрет)",
    "category": "character",
    "description": "Нарисованный портрет + оверлей рта с 10 виземами: драйвер SceneKit.portraitRig. Геометрия рта и глаза — в пропсах.",
    "tags": ["character", "portrait", "lipsync", "visemes"],
    "mechanics": ["lipsync", "blink", "breathe", "sway"],
    "rig": {
        "type": "portrait",
        "parts": ["portrait-img", "mouth-layer", "mouth", "lid-left", "lid-right"],
        "clips": ["idle", "talk", "blink"],
        "visemes": 10,
        "driver": "SceneKit.portraitRig",
    },
    "html": """
<div class="obj-portrait char portrait" data-rig="root">
  <img class="portrait-img" src="/portraits/host.png" alt="" />
</div>""",
    "css": """
.obj-portrait { position:absolute; left:50%; bottom:10%; width:34vmin; height:34vmin;
  margin-left:-17vmin; transform-origin:50% 100%; }
.obj-portrait .portrait-img { position:absolute; inset:0; width:100%; height:100%;
  object-fit:contain; object-position:50% 50%; transform-origin:50% 100%; will-change:transform;
  filter:drop-shadow(0 1.2vmin 1.8vmin rgba(0,0,0,.45)); }
.obj-portrait .mouth-layer { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; }
.obj-portrait .mouth-layer .vis { fill:#3B1A1C; stroke:#16090A; stroke-width:.55; stroke-linejoin:round; opacity:0; }
.obj-portrait .mouth-layer .vis-base { fill:#8E4A44; }
.obj-portrait .mouth-layer .tongue { fill:#C7606A; stroke:none; }
.obj-portrait .mouth-layer .lid { fill:#E9B892; stroke:#16090A; stroke-width:.4; transform-box:fill-box; transform-origin:50% 0%; }
""",
}

PRESENTER = {
    "slug": "presenter",
    "title": "Ведущий (canvas-риг)",
    "category": "character",
    "description": "Риг персонажа на canvas: скелет (плечо/локоть/запястье, бедро/колено), 10 визёмов рта, моргание, взгляд, дыхание, жест, ходьба.",
    "tags": ["character", "canvas", "rig", "lipsync", "presenter"],
    "mechanics": ["lipsync", "blink", "breathe", "gaze", "gesture", "walk", "mood"],
    "rig": {
        "type": "canvas",
        "driver": "CharacterRig.create",
        "bones": ["hips", "neck", "head", "shoulder", "elbow", "wrist", "hip", "knee", "ankle"],
        "clips": ["idle", "talk", "walk"],
        "visemes": 10,
    },
    "html": """
<div class="obj-presenter" style="left:50%; bottom:6%; width:26vmin; height:42vmin; margin-left:-13vmin">
  <canvas class="char-canvas" width="720" height="1150"></canvas>
</div>""",
    "css": """
.obj-presenter { position:absolute; transform-origin:50% 100%; }
.obj-presenter .char-canvas { width:100%; height:100%; display:block; }
""",
}

RIVE_CHARACTER = {
    "slug": "character-rive",
    "title": "Ведущий (Rive-риг)",
    "category": "character",
    "description": "Полноценный Rive-риг: скелет (плечи/локти/кисти, бёдра/колени/стопы), 10 визёмов рта, моргание, взгляд, брови, жесты и ходьба. Драйвер — SceneKit.riveCharacter.",
    "tags": ["character", "rive", "rig", "skeleton", "lipsync", "visemes", "presenter"],
    "mechanics": ["lipsync", "blink", "breathe", "gaze", "gesture", "walk", "mood"],
    "rig": {
        "type": "rive",
        "driver": "SceneKit.riveCharacter",
        "bones": ["root", "spine", "chest", "neck", "head", "shoulder", "upperArm", "foreArm", "hand", "hip", "thigh", "shin", "foot"],
        "clips": ["idle", "talk", "walk", "wave", "point", "open", "shrug"],
        "visemes": 10,
        "asset": "/rive/character.riv",
        "presets": ["host", "cohost", "priest", "historian", "sociologist"],
    },
    "html": """
<div class="obj-character-rive">
  <canvas class="rive-canvas" width="600" height="1000"></canvas>
</div>""",
    "css": """
.obj-character-rive { position:absolute; left:50%; bottom:3%; width:42vmin; height:70vmin;
  margin-left:-21vmin; transform-origin:50% 100%; }
.obj-character-rive .rive-canvas { width:100%; height:100%; display:block; }
.obj-character-rive::after { content:''; position:absolute; left:18%; right:18%; bottom:-1.2vmin;
  height:2.2vmin; border-radius:50%; background:radial-gradient(ellipse,rgba(0,0,0,.55),rgba(0,0,0,0) 70%);
  filter:blur(.4vmin); z-index:-1; }
@media (orientation: portrait) {
  .obj-character-rive { left:50%; bottom:15%; width:84vmin; height:140vmin; margin-left:-42vmin; }
}
""",
}

RIVE_BOB = {
    "slug": "character-bob",
    "title": "Bob (ready-made Rive, CC BY 4.0)",
    "category": "character",
    "description": "Готовый Rive-персонаж Bob: полный бюст/тело, 10 визёмов, выражения, взгляд, дыхание, жесты. Лицензия CC BY 4.0 — требуется атрибуция emanuelcabezas.",
    "tags": ["character", "rive", "ready", "lipsync", "visemes", "bob"],
    "mechanics": ["lipsync", "blink", "breathe", "gaze", "gesture", "mood"],
    "rig": {
        "type": "rive",
        "driver": "SceneKit.riveActor",
        "clips": ["idle", "talk", "wave", "point", "lean"],
        "visemes": 10,
        "asset": "/rive/ready/bob.riv",
        "license": "CC BY 4.0",
        "author": "emanuelcabezas",
        "source": "https://rive.app/marketplace/28111-53105-bob-lip-sync-character-system-in-rive/",
    },
    "html": """
<div class="obj-character-bob">
  <canvas class="rive-canvas" width="1080" height="1920"></canvas>
</div>""",
    "css": """
.obj-character-bob { position:absolute; left:62%; bottom:0; width:46vmin; height:81.8vmin;
  margin-left:-23vmin; transform-origin:50% 100%; }
.obj-character-bob .rive-canvas { width:100%; height:100%; display:block; }
.obj-character-bob::after { content:''; position:absolute; left:24%; right:24%; bottom:-.6vmin;
  height:2vmin; border-radius:50%; background:radial-gradient(ellipse,rgba(0,0,0,.55),rgba(0,0,0,0) 70%);
  filter:blur(.4vmin); z-index:-1; }
@media (orientation: portrait) {
  .obj-character-bob { left:50%; bottom:2%; width:70vmin; height:124.4vmin; margin-left:-35vmin; }
}
""",
}

RIVE_OLDMAN = {
    "slug": "character-oldman",
    "title": "Старец (ready-made Rive, CC BY 4.0)",
    "category": "character",
    "description": "Готовый Rive-персонаж: старец в рясе с посохом. Полное тело, ткань, верёвка, ноги, глаза, моргание, говорящий рот. CC BY 4.0 — атрибуция ar.akash.",
    "tags": ["character", "rive", "ready", "lipsync", "oldman", "historical"],
    "mechanics": ["lipsync", "blink", "breathe", "gaze", "gesture"],
    "rig": {
        "type": "rive",
        "driver": "SceneKit.riveActor",
        "clips": ["talking", "idle", "cloth", "foot-tap", "eyes"],
        "visemes": 3,
        "asset": "/rive/ready/oldman.riv",
        "license": "CC BY 4.0",
        "author": "ar.akash",
        "source": "https://rive.app/marketplace/28375-53657-old-man-character-animation-or-rive-interactive-v02/",
    },
    "html": """
<div class="obj-character-oldman">
  <canvas class="rive-canvas" width="1080" height="1920"></canvas>
</div>""",
    "css": """
.obj-character-oldman { position:absolute; left:62%; bottom:0; width:42vmin; height:74.7vmin;
  margin-left:-21vmin; transform-origin:50% 100%; }
.obj-character-oldman .rive-canvas { width:100%; height:100%; display:block; }
.obj-character-oldman::after { content:''; position:absolute; left:20%; right:20%; bottom:-.4vmin;
  height:2vmin; border-radius:50%; background:radial-gradient(ellipse,rgba(0,0,0,.55),rgba(0,0,0,0) 70%);
  filter:blur(.4vmin); z-index:-1; }
@media (orientation: portrait) {
  .obj-character-oldman { left:50%; bottom:4%; width:64vmin; height:113.8vmin; margin-left:-32vmin; }
}
""",
}

OBJECTS = [CHARACTER, PORTRAIT, PRESENTER, RIVE_CHARACTER, RIVE_BOB, RIVE_OLDMAN, CAR, ROAD, TREE, PINE, CLOUD, BIRD, LAMP, BUILDING, DESK, MONITOR, COFFEE, PLANT, PERSON, TRAFFIC_LIGHT, SUN, MOON]

# Ready actors: a compact catalogue for the editor and AI agents. The full
# object entry (HTML/CSS) is in OBJECTS; this is the capability card.
CHARACTERS = [
    {
        "slug": "character-oldman",
        "title": "Старец (Old Man)",
        "template": "character-oldman",
        "kind": "ready-rive",
        "driver": "SceneKit.riveActor",
        "mode": "stateMachine",
        "state_machine": "State Machine 1",
        "view_model": ["mouth", "face", "leftHand"],
        "visemes": 3,
        "viseme_labels": ["Default", "OO", "AAA"],
        "body": ["idle", "cloth", "rope", "foot-tap", "blink", "hand-gesture"],
        "lip_sync": True,
        "full_body": True,
        "license": "CC BY 4.0",
        "author": "ar.akash",
        "source": "https://rive.app/marketplace/28375-53657-old-man-character-animation-or-rive-interactive-v02/",
        "asset": "/rive/ready/oldman.riv",
    },
    {
        "slug": "character-bob",
        "title": "Bob",
        "template": "character-bob",
        "kind": "ready-rive",
        "driver": "SceneKit.riveActor",
        "mode": "linear",
        "state_machine": "State Machine 1",
        "view_model": ["visemes", "poses", "expressions", "mood", "pupils", "headAuto"],
        "visemes": 10,
        "body": ["idle", "breath", "head-idle", "pupils", "hand-poses"],
        "lip_sync": True,
        "full_body": False,
        "license": "CC BY 4.0",
        "author": "emanuelcabezas",
        "source": "https://rive.app/marketplace/28111-53105-bob-lip-sync-character-system-in-rive/",
        "asset": "/rive/ready/bob.riv",
    },
    {
        "slug": "character-3d",
        "title": "3D-аватар (Ready Player Me)",
        "template": "character-3d",
        "kind": "glb-3d",
        "driver": "SceneKit.babylonCharacter",
        "mode": "morph-targets",
        "visemes": 10,
        "viseme_set": "oculus-15",
        "body": ["idle", "breath", "blink", "gaze", "head", "wave", "point", "nod"],
        "lip_sync": True,
        "full_body": True,
        "license": "Ready Player Me (free avatar)",
        "author": "Ready Player Me",
        "asset": "/models/brunette.glb",
    },
    {
        "slug": "character-rive",
        "title": "Собственный Rive-риг",
        "template": "character-rive",
        "kind": "own-rive",
        "driver": "SceneKit.riveCharacter",
        "mode": "viewModel-numbers",
        "visemes": 10,
        "body": ["idle", "talk", "walk", "wave", "point", "open", "shrug"],
        "lip_sync": True,
        "full_body": True,
        "license": "internal",
        "author": "SceneEngine",
        "asset": "/rive/character.riv",
    },
]


def list_characters():
    return CHARACTERS


def get_character(slug: str):
    return next((c for c in CHARACTERS if c["slug"] == slug), None)

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION / COMPATIBILITY / VIEWS
# ─────────────────────────────────────────────────────────────────────────────
# domain: outdoor | indoor | stage
# surface: ground | road | sky | wall | desk | ceiling
# environments: explicit allow-list (empty = all in the same domain)
# views: object variants (side/front/...) — optional, default is the first one.
# Environments expose `views` for lighting/time-of-day (day/sunset/night/...).

ENV_META = {
    "forest":    {"domain": "outdoor", "views": ["day", "sunset", "night"], "default_view": "day", "perspective": "side"},
    "city":      {"domain": "outdoor", "views": ["night", "dusk"], "default_view": "night", "perspective": "side"},
    "mountains": {"domain": "outdoor", "views": ["dawn", "day"], "default_view": "dawn", "perspective": "side"},
    "office":    {"domain": "indoor",  "views": ["day", "evening"], "default_view": "day", "perspective": "front"},
    "studio":    {"domain": "stage",   "views": ["dark", "blue"], "default_view": "dark", "perspective": "front"},
}

OBJ_META = {
    "car":           {"domain": ["outdoor"], "environments": ["forest", "city", "mountains"], "surface": "road", "views": ["side", "front"], "default_view": "side"},
    "road":          {"domain": ["outdoor"], "environments": ["forest", "city", "mountains"], "surface": "road", "views": ["straight"], "default_view": "straight"},
    "tree":          {"domain": ["outdoor"], "environments": ["forest", "mountains", "city"], "surface": "ground", "views": ["front"], "default_view": "front"},
    "pine":          {"domain": ["outdoor"], "environments": ["forest", "mountains"], "surface": "ground", "views": ["front"], "default_view": "front"},
    "cloud":         {"domain": ["outdoor"], "environments": ["forest", "city", "mountains"], "surface": "sky", "views": ["side"], "default_view": "side"},
    "bird":          {"domain": ["outdoor"], "environments": ["forest", "city", "mountains"], "surface": "sky", "views": ["side"], "default_view": "side"},
    "street-lamp":   {"domain": ["outdoor"], "environments": ["city", "forest"], "surface": "ground", "views": ["side"], "default_view": "side"},
    "building":      {"domain": ["outdoor"], "environments": ["city"], "surface": "ground", "views": ["front", "corner"], "default_view": "front"},
    "desk":          {"domain": ["indoor"], "environments": ["office"], "surface": "ground", "views": ["front"], "default_view": "front"},
    "monitor":       {"domain": ["indoor"], "environments": ["office"], "surface": "desk", "views": ["front"], "default_view": "front"},
    "coffee":        {"domain": ["indoor"], "environments": ["office"], "surface": "desk", "views": ["side"], "default_view": "side"},
    "plant":         {"domain": ["indoor", "stage"], "environments": ["office", "studio"], "surface": "ground", "views": ["front"], "default_view": "front"},
    "person":        {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front", "side"], "default_view": "front"},
    "character":     {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front", "three-quarter", "side"], "default_view": "front"},
    "character-rive": {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front"], "default_view": "front"},
    "character-3d": {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front"], "default_view": "front"},
    "character-bob": {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front"], "default_view": "front"},
    "character-oldman": {"domain": ["outdoor", "indoor", "stage"], "environments": [], "surface": "ground", "views": ["front"], "default_view": "front"},
    "traffic-light": {"domain": ["outdoor"], "environments": ["city"], "surface": "ground", "views": ["front"], "default_view": "front"},
    "sun":           {"domain": ["outdoor"], "environments": ["forest", "mountains", "city"], "surface": "sky", "views": ["front"], "default_view": "front"},
    "moon":          {"domain": ["outdoor"], "environments": ["city", "forest"], "surface": "sky", "views": ["front"], "default_view": "front"},
}

for _e in ENVIRONMENTS:
    _e.update(ENV_META.get(_e["slug"], {}))
for _o in OBJECTS:
    _o.update(OBJ_META.get(_o["slug"], {}))
for _o in OBJECTS:
    if _o["slug"] in ("character", "person"):
        _o["hidden"] = True

# Time-of-day / lighting views. The host puts `view-<name>` on <body>, so a scene
# can switch the whole world without rotating every object (that would be 3D).
VIEWS_ENV_CSS = """
.view-sunset .env-forest .sky { background:linear-gradient(180deg,#2A1B3D 0%,#7A3B4A 45%,#D97745 75%,#F2B36B 100%); }
.view-sunset .env-forest .sun { left:76%; top:34%; background:radial-gradient(circle,#FFE0A3 0%,#FF8C42 40%,rgba(255,140,66,0) 72%); }
.view-night .env-forest .sky { background:linear-gradient(180deg,#040814 0%,#0A1730 55%,#0E2430 100%); }
.view-night .env-forest .sun { opacity:0; }
.view-night .env-forest .pines-far, .view-night .env-forest .pines-near { filter:brightness(.55) saturate(.75); }
.view-dusk .env-city .sky { background:linear-gradient(180deg,#1A1030 0%,#4B2450 55%,#C25A4A 100%); }
.view-dusk .env-city .moon { opacity:.35; }
.view-dusk .env-city .stars { opacity:.25; }
.view-day .env-mountains .sky { background:linear-gradient(180deg,#1B2A4A 0%,#4A6A8A 45%,#9BC0D6 75%,#E8D9B8 100%); }
.view-day .env-mountains .sun { top:18%; background:radial-gradient(circle,#FFF9D9 0%,#FFE08A 36%,rgba(255,224,138,0) 70%); }
.view-evening .env-office .wall { background:linear-gradient(180deg,#D9C6B0,#B79A7E); }
.view-evening .env-office .window-sky { background:linear-gradient(180deg,#5B4A6B 0%,#C77B5A 70%,#E8B07A 100%); }
.view-evening .env-office .floor { background:linear-gradient(180deg,#9A7A58,#6B4E36); }
.view-blue .env-studio .beam { background:linear-gradient(180deg,rgba(120,170,255,.55),rgba(120,170,255,0) 78%); }
.view-blue .env-studio .backdrop { background:radial-gradient(circle at 50% 38%,#16264A 0%,#08101F 46%,#03060B 100%); }
"""

VIEWS_OBJ_CSS = """
.obj-car.view-front { width:20vmin; }
.obj-car.view-front .car-body { left:1.6vmin; right:1.6vmin; height:6.4vmin; border-radius:2vmin; }
.obj-car.view-front .car-cabin { left:6vmin; width:8vmin; bottom:8.4vmin; }
.obj-car.view-front .car-window { left:7vmin; width:6vmin; height:3vmin; }
.obj-car.view-front .wheel { display:none; }
.obj-building.view-corner { clip-path:polygon(0 0,78% 6%,100% 18%,100% 100%,0 100%); }
.obj-person.view-side { transform:scaleX(.72); }
"""

for _e in ENVIRONMENTS:
    _e["css"] = _e.get("css", "") + "\n" + VIEWS_ENV_CSS
for _o in OBJECTS:
    if _o["slug"] in ("car", "building", "person"):
        _o["css"] = _o.get("css", "") + "\n" + VIEWS_OBJ_CSS


def objects_for_environment(env_slug: str):
    env = get_environment(env_slug)
    if not env:
        return []
    out = []
    for o in OBJECTS:
        if o.get("hidden"):
            continue
        allowed = o.get("environments") or []
        if allowed:
            if env_slug in allowed:
                out.append(o)
        elif env.get("domain") in (o.get("domain") or []):
            out.append(o)
    return sorted(out, key=lambda o: (0 if o.get("category") == "character" else 1, o.get("cast_order", 50), o.get("title", "")))


def environments_for_object(obj_slug: str):
    obj = get_object(obj_slug)
    if not obj:
        return []
    allowed = obj.get("environments") or []
    if allowed:
        return [e for e in ENVIRONMENTS if e["slug"] in allowed]
    return [e for e in ENVIRONMENTS if e.get("domain") in (obj.get("domain") or [])]


def compatibility_matrix():
    return {
        "environments": {
            e["slug"]: [o["slug"] for o in objects_for_environment(e["slug"])]
            for e in ENVIRONMENTS
        },
        "objects": {
            o["slug"]: [e["slug"] for e in environments_for_object(o["slug"])]
            for o in OBJECTS
        },
    }


def validate_composition(environment: str, object_slugs: list):
    env = get_environment(environment)
    if not env:
        return {"valid": False, "errors": [{"path": "environment", "message": "Unknown environment"}]}
    allowed = {o["slug"] for o in objects_for_environment(environment)}
    errors = []
    for slug in object_slugs or []:
        if slug not in allowed:
            errors.append({"path": f"objects.{slug}", "message": f"{slug} is not allowed in {environment}"})
    return {"valid": not errors, "errors": errors}

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

def _env(slug):
    return next(e for e in ENVIRONMENTS if e["slug"] == slug)


def _obj(slug):
    return next(o for o in OBJECTS if o["slug"] == slug)


def _compose(env_slug, obj_slugs, js, *, title, description, tags, duration, props_schema=None, default_props=None, cues=None, extra_css='', extra_html='', slug=None, object_styles=None):
    env = _env(env_slug)
    objs = [_obj(s) for s in obj_slugs]
    def _with_style(o):
        html = o["html"]
        extra = (object_styles or {}).get(o["slug"], "")
        if not extra:
            return html
        if 'style="' in html:
            return re.sub(r'style="([^"]*)"', lambda m: f'style="{m.group(1)};{extra}"', html, count=1)
        return re.sub(r'(<div class="obj-[^"]*")', r'\1 style="' + extra + '"', html, count=1)

    actors = [o for o in objs if o.get("category") == "character"]
    props = [o for o in objs if o.get("category") != "character"]
    html = (
        '<div class="scene">\n'
        + '<div class="layer layer-world" data-layer="world">\n' + env["html"] + '\n</div>\n'
        + '<div class="layer layer-objects" data-layer="objects">\n'
        + "\n".join(_with_style(o) for o in props)
        + '\n</div>\n'
        + ('<div class="layer layer-actors" data-layer="actors">\n'
           + "\n".join(_with_style(o) for o in actors) + '\n</div>\n' if actors else '')
        + ('<div class="layer layer-overlay" data-layer="overlay">' + extra_html + '</div>' if extra_html else '')
        + '</div>'
    )
    css = (BASE_CSS + "\n" + env["css"] + "\n" + "\n".join(o["css"] for o in objs) + "\n" + extra_css).strip()
    return {
        "slug": slug or title.lower().replace(" ", "-"),
        "title": title,
        "description": description,
        "tags": tags,
        "duration": duration,
        "environment": env_slug,
        "view": env.get("default_view", ""),
        "cues": cues or [],
        "objects": obj_slugs,
        "props_schema": props_schema or {},
        "default_props": default_props or {},
        "code": {"html": html.strip(), "css": css, "js": js.strip()},
    }


FOREST_DRIVE_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const car = root.querySelector('.obj-car');
const wheels = root.querySelectorAll('[data-wheel]');
const tree = root.querySelector('.obj-tree');
const pine = root.querySelector('.obj-pine');
if (tree) SceneKit.scatter(tree, { count: Number(p.tree_count) || 4, x: [0.05, 0.95], y: [0.16, 0.32], scale: [0.6, 1.4], seed: 11 });
if (pine) SceneKit.scatter(pine, { count: Number(p.pine_count) || 5, x: [0.02, 0.98], y: [0.12, 0.34], scale: [0.6, 1.5], seed: 23 });
const dashes = root.querySelector('.obj-road .road-dashes');
const pines = root.querySelectorAll('[data-depth]');
const clouds = root.querySelectorAll('.obj-cloud');
if (car && p.car_color) car.style.setProperty('--car-color', p.car_color);
SceneKit.views(root, p.views || { car: 'side' });
const base = Number(p.cruise_speed) || 1.4;
const defaultCues = [
  { at: 0,    set: { speed: base, brake: false } },
  { at: 2200, set: { speed: base * 2.1 } },
  { at: 4600, set: { speed: base * 0.25, brake: true } },
];
const cueList = (window.__sceneCues && window.__sceneCues.length) ? window.__sceneCues : defaultCues;
const cues = SceneKit.cues(cueList, { smooth: true });
function seek(t) {
  const st = cues.stateAt(t);
  const dist = cues.integrate('speed', t) * 90;
  if (car) car.style.transform = `translate3d(${dist}px,0,0)`;
  wheels.forEach((w) => { w.style.transform = `rotate(${cues.integrate('speed', t) * 360}deg)`; });
  if (dashes) dashes.style.transform = `translate3d(${-dist * 0.8}px,0,0)`;
  pines.forEach((el) => {
    const depth = Number(el.dataset.depth) || 0.2;
    el.style.transform = `translate3d(${-dist * depth}px,0,0)`;
  });
  clouds.forEach((el, i) => {
    el.style.transform = `translate3d(${(t / 1000) * (3 + i * 1.5)}px,0,0)`;
  });
  if (car) car.classList.toggle('braking', !!st.brake);
}
window.scene = { seek };
"""

CITY_DRIVE_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const car = root.querySelector('.obj-car');
const wheels = root.querySelectorAll('[data-wheel]');
const tree = root.querySelector('.obj-tree');
const pine = root.querySelector('.obj-pine');
if (tree) SceneKit.scatter(tree, { count: Number(p.tree_count) || 4, x: [0.05, 0.95], y: [0.16, 0.32], scale: [0.6, 1.4], seed: 11 });
if (pine) SceneKit.scatter(pine, { count: Number(p.pine_count) || 5, x: [0.02, 0.98], y: [0.12, 0.34], scale: [0.6, 1.5], seed: 23 });
const dashes = root.querySelector('.obj-road .road-dashes');
const layers = root.querySelectorAll('[data-depth]');
if (car && p.car_color) car.style.setProperty('--car-color', p.car_color);
SceneKit.views(root, p.views || { car: 'side' });
const base = Number(p.cruise_speed) || 1.2;
const defaultCues = [
  { at: 0,    set: { speed: base } },
  { at: 1800, set: { speed: base * 1.8 } },
  { at: 4200, set: { speed: base * 0.35 } },
];
const cueList = (window.__sceneCues && window.__sceneCues.length) ? window.__sceneCues : defaultCues;
const cues = SceneKit.cues(cueList, { smooth: true });
function seek(t) {
  const dist = cues.integrate('speed', t) * 80;
  if (car) car.style.transform = `translate3d(${dist}px,0,0)`;
  wheels.forEach((w) => { w.style.transform = `rotate(${cues.integrate('speed', t) * 360}deg)`; });
  if (dashes) dashes.style.transform = `translate3d(${-dist * 0.8}px,0,0)`;
  layers.forEach((el) => {
    const depth = Number(el.dataset.depth) || 0.15;
    el.style.transform = `translate3d(${-dist * depth}px,0,0)`;
  });
  root.querySelectorAll('.obj-lamp .lamp-cone').forEach((el, i) => {
    el.style.opacity = 0.28 + 0.08 * Math.sin((t / 700) + i);
  });
}
window.scene = { seek };
"""

MOUNTAIN_FLIGHT_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const bird = root.querySelector('.obj-bird');
if (bird) SceneKit.scatter(bird, { count: Number(p.bird_count) || 3, x: [0.1, 0.9], y: [0.2, 0.4], scale: [0.7, 1.4], seed: 5 });
const birds = root.querySelectorAll('.obj-bird');
const clouds = root.querySelectorAll('.obj-cloud');
const layers = root.querySelectorAll('[data-depth]');
function seek(t) {
  const s = t / 1000;
  birds.forEach((b, i) => {
    const x = -10 + ((s * (7 + i * 1.5) + i * 22) % 120);
    const y = 28 + Math.sin(s * 1.2 + i) * 4;
    b.style.left = x + '%';
    b.style.top = y + '%';
    const flap = Math.sin(s * 8 + i) * 18;
    const l = b.querySelector('.wing-left');
    const r = b.querySelector('.wing-right');
    if (l) l.style.transform = `rotate(${flap}deg)`;
    if (r) r.style.transform = `rotate(${-flap}deg)`;
  });
  clouds.forEach((c, i) => { c.style.transform = `translate3d(${(s * (3 + i)) % 140}px,0,0)`; });
  layers.forEach((el) => {
    const depth = Number(el.dataset.depth) || 0.1;
    el.style.transform = `translate3d(${-s * depth * 12}px,0,0)`;
  });
}
window.scene = { seek };
"""

OFFICE_DAY_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const steam = root.querySelectorAll('.coffee-steam');
const leaves = root.querySelector('.obj-plant');
const screen = root.querySelector('.monitor-screen');
function seek(t) {
  const s = t / 1000;
  steam.forEach((el, i) => {
    const ph = (s * 0.6 + i * 0.5) % 1;
    el.style.transform = `translateY(${-ph * 18}px) scale(${0.7 + ph * 0.5})`;
    el.style.opacity = String(0.55 * (1 - ph));
  });
  if (leaves) leaves.style.transform = `rotate(${Math.sin(s * 1.1) * 2.2}deg)`;
  if (screen) screen.style.filter = `brightness(${1 + Math.sin(s * 3) * 0.03})`;
}
window.scene = { seek };
"""

STUDIO_INTRO_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const beams = root.querySelectorAll('.env-studio .beam');
const floor = root.querySelector('.env-studio .floor');
function seek(t) {
  const s = t / 1000;
  beams.forEach((el, i) => {
    const base = [-10, 2, 10][i] || 0;
    el.style.transform = `rotate(${base + Math.sin(s * 0.7 + i) * 3}deg)`;
  });
  if (floor) floor.style.opacity = String(0.86 + Math.sin(s * 1.4) * 0.06);
}
window.scene = { seek };
"""

CINEMATIC_FOREST_CSS = """
.scene { perspective: 1400px; transform-style: preserve-3d; }
.layer-world, .layer-objects, .layer-actors { transform-style: preserve-3d; }
.scene::after { content:''; position:absolute; inset:0; pointer-events:none; z-index:60;
  background:radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,.45) 100%);
  mix-blend-mode:multiply; }
.scene::before { content:''; position:absolute; inset:0; pointer-events:none; z-index:55;
  background:linear-gradient(180deg, rgba(255,220,150,.06), transparent 30%, transparent 75%, rgba(0,0,0,.18));
  mix-blend-mode:screen; }
"""

CINEMATIC_FOREST_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const car = root.querySelector('.obj-car');
const wheels = root.querySelectorAll('[data-wheel]');
const dashes = root.querySelector('.obj-road .road-dashes');
const tree = root.querySelector('.obj-tree');
const pine = root.querySelector('.obj-pine');
if (tree) SceneKit.scatter(tree, { count: Number(p.tree_count) || 5, x: [0.05, 0.95], y: [0.16, 0.32], scale: [0.6, 1.4], seed: 11 });
if (pine) SceneKit.scatter(pine, { count: Number(p.pine_count) || 6, x: [0.02, 0.98], y: [0.12, 0.34], scale: [0.6, 1.5], seed: 23 });
if (car && p.car_color) car.style.setProperty('--car-color', p.car_color);
SceneKit.views(root, p.views || { car: 'side' });

const depthEls = [
  { el: root.querySelector('.env-forest .sky'), depth: 0.15 },
  { el: root.querySelector('.env-forest .sun'), depth: 0.2 },
  { el: root.querySelector('.env-forest .ridge'), depth: 0.35 },
  { el: root.querySelector('.env-forest .pines-far'), depth: 0.55 },
  { el: root.querySelector('.env-forest .pines-near'), depth: 0.8 },
  { el: root.querySelector('.env-forest .ground'), depth: 0.9 },
  { el: root.querySelector('.env-forest .fog'), depth: 1.0 },
].filter((x) => x.el);
const cam = SceneKit.camera(depthEls, {
  path(t) {
    const a = Number(p.camera_amount) || 1;
    return {
      x: Math.sin(t / 2600) * 26 * a,
      y: Math.cos(t / 3400) * 10 * a,
      z: -t * 0.01 * a,
      zoom: Math.sin(t / 4200) * 0.02 * a,
      rot: Math.sin(t / 5000) * 0.5 * a,
    };
  },
});

const base = Number(p.cruise_speed) || 1.4;
const defaultCues = [
  { at: 0, set: { speed: base, brake: false } },
  { at: 2200, set: { speed: base * 2.1 } },
  { at: 4600, set: { speed: base * 0.25, brake: true } },
];
const cueList = (window.__sceneCues && window.__sceneCues.length) ? window.__sceneCues : defaultCues;
const cues = SceneKit.cues(cueList, { smooth: true });

function seek(t) {
  const st = cues.stateAt(t);
  const dist = cues.integrate('speed', t) * 90;
  cam.seek(t);
  if (car) car.style.transform = `translate3d(${dist}px,0,0)`;
  wheels.forEach((w) => { w.style.transform = `rotate(${cues.integrate('speed', t) * 360}deg)`; });
  if (dashes) dashes.style.transform = `translate3d(${-dist * 0.8}px,0,0)`;
  if (car) car.classList.toggle('braking', !!st.brake);
}
window.scene = { seek };
"""

# Демо-тайминги липсинка: «Мир вам — это сцена с живым липсинком» (text_to_visemes).
VIS_PAIRS = [(700, 2), (800, 1), (900, 4), (1050, 3), (1150, 1), (1250, 2), (1450, 1), (1550, 4), (1650, 8),
             (1850, 4), (1940, 4), (2030, 1), (2120, 4), (2210, 1), (2400, 4), (2560, 6), (2658, 1), (2756, 3),
             (2854, 1), (2952, 2), (3150, 7), (3233, 1), (3316, 2), (3400, 4), (3483, 1), (3566, 4),
             (3650, 4), (3733, 8), (3816, 2)]
VIS_DEMO = [{"t": t, "viseme": v} for t, v in VIS_PAIRS]
VIS_DEMO_B = [{"t": t + 3000, "viseme": v} for t, v in VIS_PAIRS]

PRESENTER_TALK_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const canvas = root.querySelector('.obj-presenter canvas');
const rig = window.CharacterRig ? CharacterRig.create(canvas, {
  visemes: p.visemes || [],
  mood: p.mood || 'neutral',
  gestureAt: p.gesture_at !== undefined && p.gesture_at !== null ? Number(p.gesture_at) : 4200,
  gestureDur: Number(p.gesture_dur) || 1500,
  walk: !!p.walk,
  seed: Number(p.seed) || 0,
}) : { seek() {} };
const cap = root.querySelector('.talk-caption');
const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});

const halo = root.querySelector('.talk-halo');
const actors = root.querySelector('.layer-actors');
const actorBox = root.querySelector('.obj-presenter');
if (halo && actors && actorBox) actors.insertBefore(halo, actorBox);

const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 46, seed: 17, color: '255,225,175',
  speedY: 9, driftX: 22, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.06, alphaMax: 0.26,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.45 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.82, duration: 1.1, ease: 'power3.out' }, 0)
  .from('.obj-presenter', { y: 30, opacity: 0, duration: 0.85, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = { seek(t) { tl.seek(t / 1000); rig.seek(t); dust.seek(t); } };
"""

CHARACTER_TALK_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const actor = root.querySelector('.obj-portrait');
const eyeY = Number(p.eye_y) || 30;
const rig = SceneKit.portraitRig(actor, {
  image: p.image || '/portraits/host.png',
  mouth: { x: Number(p.mouth_x) || 49, y: Number(p.mouth_y) || 45.5, w: Number(p.mouth_w) || 7 },
  eyes: p.blink ? [[Number(p.eye_lx) || 41, eyeY, 3.6, 2.6], [Number(p.eye_rx) || 57, eyeY, 3.6, 2.6]] : null,
  visemes: p.visemes || [],
  mood: p.mood || 'neutral',
  seed: Number(p.seed) || 0,
});
const cap = root.querySelector('.talk-caption');
const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});

// ореол светится ЗА героем
const halo = root.querySelector('.talk-halo');
const actors = root.querySelector('.layer-actors');
if (halo && actors) actors.insertBefore(halo, actor);

// атмосфера: пыль в луче + пост-обработка кадра (зерно/виньетка/грейд)
const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 46, seed: 17, color: '255,225,175',
  speedY: 9, driftX: 22, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.06, alphaMax: 0.26,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.45 });

// кинетическая типографика + появление героя
const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.82, duration: 1.1, ease: 'power3.out' }, 0)
  .from('.obj-portrait', { y: 34, opacity: 0, duration: 0.85, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = { seek(t) { tl.seek(t / 1000); rig.seek(t); dust.seek(t); } };
"""

RIVE_CHARACTER_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const canvas = root.querySelector('.obj-character-rive canvas');
const raw = window.__riveCharacterBuffer || '';
let buffer = null;
try {
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) { window.__sceneSend && window.__sceneSend('scene-error', { message: 'rive buffer: ' + e }); }

const rig = SceneKit.riveCharacter(canvas, {
  buffer,
  character: p.character || 'host',
  visemes: p.visemes || [],
  gestures: p.gestures || [{ at: 4200, type: 'wave', hand: 'R', dur: 1600 }],
  walk: !!p.walk,
  mood: p.mood || 'neutral',
  seed: Number(p.seed) || 0,
  props: p,
});

const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});

const halo = root.querySelector('.talk-halo');
const actors = root.querySelector('.layer-actors');
const actorBox = root.querySelector('.obj-character-rive');
if (halo && actors && actorBox) actors.insertBefore(halo, actorBox);

const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 46, seed: 17, color: '255,225,175',
  speedY: 9, driftX: 22, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.06, alphaMax: 0.26,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.45 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.82, duration: 1.1, ease: 'power3.out' }, 0)
  .from('.obj-character-rive', { y: 24, duration: 0.85, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = {
  ready: rig.ready,
  seek(t) {
    if (rig) rig.seek(t);
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""

RIVE_PANEL_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const raw = window.__riveCharacterBuffer || '';
let buffer = null;
try {
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) {}

const canvases = Array.from(root.querySelectorAll('.obj-character-rive canvas'));
const cast = Array.isArray(p.cast) && p.cast.length ? p.cast : [
  { character: 'host', mood: 'joy' },
  { character: 'cohost', mood: 'joy' },
];
const rigs = canvases.map((canvas, i) => SceneKit.riveCharacter(canvas, {
  buffer,
  character: (cast[i] && cast[i].character) || 'host',
  visemes: (cast[i] && cast[i].visemes) || p.visemes || [],
  gestures: (cast[i] && cast[i].gestures) || [],
  mood: (cast[i] && cast[i].mood) || p.mood || 'neutral',
  walk: !!(cast[i] && cast[i].walk),
  seed: Number((cast[i] && cast[i].seed) || i * 17),
  props: cast[i] || {},
}));

const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});
const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 52, seed: 19, color: '255,225,175',
  speedY: 8, driftX: 20, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.05, alphaMax: 0.22,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.45 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.86, duration: 1, ease: 'power3.out' }, 0)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = {
  ready: Promise.all(rigs.map((r) => r.ready)),
  seek(t) {
    rigs.forEach((r) => r.seek(t));
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""

RIVE_BOB_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const canvas = root.querySelector('.obj-character-bob canvas');
const raw = window.__riveActorBuffer || '';
let buffer = null;
try {
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) {}

const rig = SceneKit.riveActor(canvas, {
  buffer,
  visemes: p.visemes || [],
  gestures: p.gestures || [{ at: 4200, type: 'wave', dur: 1800 }],
  mood: p.mood || 'neutral',
  props: p,
});

const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});
const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 46, seed: 17, color: '255,225,175',
  speedY: 9, driftX: 22, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.06, alphaMax: 0.26,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.45 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.86, duration: 1, ease: 'power3.out' }, 0)
  .from('.obj-character-bob', { y: 26, duration: 0.9, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.obj-character-bob', { y: -6, rotation: 0.35, duration: 3.1, yoyo: true, repeat: 1, ease: 'sine.inOut' }, 0.95)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = {
  ready: rig.ready,
  seek(t) {
    if (rig) rig.seek(t);
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""

RIVE_OLDMAN_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const canvas = root.querySelector('.obj-character-oldman canvas');
const raw = window.__riveOldManBuffer || '';
let buffer = null;
try {
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) {}

const rig = SceneKit.riveActor(canvas, {
  buffer,
  character: 'oldman',
  visemes: p.visemes || [],
  gestures: p.gestures || [{ at: 4200, type: 'point', dur: 1500 }],
  mood: p.mood || 'neutral',
  props: p,
});

const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});
const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 54, seed: 23, color: '255,225,175',
  speedY: 8, driftX: 20, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.06, alphaMax: 0.26,
});
SceneKit.grain(root, { grainOpacity: 0.12, vignetteStrength: 0.5 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.86, duration: 1, ease: 'power3.out' }, 0)
  .from('.obj-character-oldman', { y: 26, duration: 0.9, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.talk-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = {
  ready: rig.ready,
  seek(t) {
    if (rig) rig.seek(t);
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""

RIVE_OLDMAN_PANEL_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const raw = window.__riveOldManBuffer || '';
let buffer = null;
try {
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) {}

const canvases = Array.from(root.querySelectorAll('.obj-character-oldman canvas'));
const cast = Array.isArray(p.cast) && p.cast.length ? p.cast : [
  { name: 'Летописец', mood: 'neutral', visemes: p.visemes || [], gestures: [{ at: 4200, type: 'point', dur: 1500 }] },
  { name: 'Старец', mood: 'surprise', visemes: p.visemes_b || [], gestures: [{ at: 6200, type: 'point', dur: 1400 }] },
];
const rigs = canvases.map((canvas, i) => SceneKit.riveActor(canvas, {
  buffer,
  character: 'oldman',
  visemes: (cast[i] && cast[i].visemes) || [],
  gestures: (cast[i] && cast[i].gestures) || [],
  mood: (cast[i] && cast[i].mood) || 'neutral',
  props: cast[i] || {},
}));

const line = root.querySelector('.talk-line');
if (line && p.headline) line.textContent = p.headline;
SceneKit.views(root, p.views || {});
const dustCanvas = root.querySelector('.talk-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 58, seed: 29, color: '255,225,175',
  speedY: 8, driftX: 22, sizeMin: 0.8, sizeMax: 2.4, alphaMin: 0.05, alphaMax: 0.24,
});
SceneKit.grain(root, { grainOpacity: 0.12, vignetteStrength: 0.52 });

const tl = gsap.timeline({ paused: true });
tl.from('.talk-halo', { opacity: 0, scale: 0.86, duration: 1.1, ease: 'power3.out' }, 0)
  .from('.layer-actors > .obj-character-oldman', { y: 28, duration: 0.95, stagger: 0.12, ease: 'power4.out' }, 0.05)
  .from('.talk-line', { yPercent: 118, rotate: 3, duration: 0.9, ease: 'power4.out' }, 0.4)
  .fromTo('.talk-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.55)
  .to('.talk-sweep', { xPercent: 130, duration: 2.6, ease: 'power2.inOut' }, 0.6)
  .to('.talk-caption', { opacity: 0, y: -18, duration: 0.6, ease: 'power2.in' }, 6.4);

window.scene = {
  ready: Promise.all(rigs.map((r) => r.ready)),
  seek(t) {
    rigs.forEach((r) => r.seek(t));
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3D AVATAR (Ready Player Me GLB + Babylon.js)
# ─────────────────────────────────────────────────────────────────────────────
# The model ships 67 bones and 72 ARKit/Oculus morph targets (15 visemes).
# Babylon is loaded via <script src> because the sandbox has an opaque origin;
# the GLB is wrapped into /models/brunette.glb.js for the same reason (fetch is
# blocked there). BabylonCharacter draws exactly one frame per seek(t).

CHARACTER_3D_HTML = """
<div class="scene">
  <div class="layer layer-world" data-layer="world">
    <div class="av-bg"></div>
    <div class="av-glow"></div>
  </div>
  <div class="layer layer-actors" data-layer="actors">
    <div class="obj-character-3d" data-layer-id="hero">
      <canvas class="av-canvas" width="1600" height="900"></canvas>
    </div>
  </div>
  <div class="layer layer-overlay" data-layer="overlay">
    <div class="av-sweep"></div>
    <canvas class="av-dust" width="1920" height="1080"></canvas>
    <div class="av-caption">
      <div class="av-kicker">3D STUDIO</div>
      <div class="av-mask"><span class="av-line">Живой 3D-аватар</span></div>
    </div>
  </div>
</div>
<script src="/vendor/babylon.js"></script>
<script src="/vendor/babylonjs.loaders.min.js"></script>
<script src="/vendor/babylon-character.js"></script>
<script src="/models/brunette.glb.js"></script>
"""

CHARACTER_3D_CSS = """
.av-bg { position:absolute; inset:0;
  background:radial-gradient(120% 90% at 50% 12%, #2b3a52 0%, #161d29 46%, #090c12 100%); }
.av-glow { position:absolute; left:50%; top:4%; width:78vmin; height:78vmin; margin-left:-39vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(130,175,255,.20) 0%, rgba(130,175,255,.05) 46%, transparent 70%);
  filter:blur(8px); }
.obj-character-3d { position:absolute; inset:0; }
.obj-character-3d .av-canvas { width:100%; height:100%; display:block; }
.av-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.av-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.55; }
.av-caption { position:absolute; left:7%; bottom:9%; max-width:46%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.av-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue);
  margin-bottom:1.2vmin; }
.av-mask { overflow:hidden; padding:.12em 0 .18em; }
.av-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06;
  transform-origin:left bottom; }
.av-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px;
  background:var(--brand-light-blue); }
@media (orientation: portrait) {
  .av-caption { left:8%; right:8%; bottom:7%; max-width:none; text-align:center; }
  .av-caption::before { display:none; }
  .av-line { font-size:clamp(18px, 6vmin, 40px); }
}
"""

CHARACTER_3D_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const canvas = root.querySelector('.av-canvas');

let buffer = null;
try {
  const raw = window.__avatarGlb || '';
  if (raw) {
    const bin = atob(raw);
    const u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    buffer = u.buffer;
  }
} catch (e) {
  window.__sceneSend && window.__sceneSend('scene-error', { message: 'avatar buffer: ' + e });
}

const rig = SceneKit.babylonCharacter(canvas, {
  buffer,
  preset: p.preset || 'bust',
  visemes: p.visemes || [],
  mood: p.mood || 'neutral',
  gestures: p.gestures || [{ at: 4200, type: 'wave', duration: 1800 }],
  gaze: p.gaze || { x: 0, y: 0 },
  idleClip: p.idleClip || 'Neutral_Idle',
  talkClip: p.talkClip || 'Talking',
  talkWeight: p.talk_weight !== undefined ? Number(p.talk_weight) : 0.4,
  pose: p.pose || {},
  poseKeys: p.pose_keys || [],
  seed: Number(p.seed) || 0,
  intensity: p.intensity !== undefined ? Number(p.intensity) : 1,
  onError(e) {
    window.__sceneSend && window.__sceneSend('scene-error', { message: 'avatar: ' + (e && e.message ? e.message : e) });
  },
});

const line = root.querySelector('.av-line');
if (line && p.headline) line.textContent = p.headline;
const kicker = root.querySelector('.av-kicker');
if (kicker && p.kicker) kicker.textContent = p.kicker;

const dustCanvas = root.querySelector('.av-dust');
const dust = SceneKit.particles(dustCanvas, {
  count: Number(p.dust_count) || 44, seed: 23, color: '210,225,255',
  speedY: 8, driftX: 18, sizeMin: 0.8, sizeMax: 2.2, alphaMin: 0.05, alphaMax: 0.22,
});
SceneKit.grain(root, { grainOpacity: 0.1, vignetteStrength: 0.46 });

const tl = gsap.timeline({ paused: true });
tl.from('.av-glow', { opacity: 0, scale: 0.86, duration: 1.1, ease: 'power3.out' }, 0)
  .from('.obj-character-3d', { opacity: 0, y: 22, duration: 0.9, ease: 'power4.out' }, 0.05)
  .from('.av-line', { yPercent: 118, rotate: 2, duration: 0.9, ease: 'power4.out', stagger: 0.12 }, 0.35)
  .fromTo('.av-kicker', { letterSpacing: '0.34em', opacity: 0 }, { letterSpacing: '0.12em', opacity: 1, duration: 1.1, ease: 'power3.out' }, 0.5)
  .to('.av-sweep', { xPercent: 130, duration: 2.4, ease: 'power2.inOut' }, 0.6)
  .to('.av-caption', { opacity: 0, y: -16, duration: 0.6, ease: 'power2.in' }, 6.2);

// live controls from the editor (no iframe rebuild)
window.addEventListener('message', (e) => {
  const m = e.data || {};
  if (!m || !m.type || m.type.indexOf('avatar-') !== 0) return;
  try {
    if (m.type === 'avatar-pose') rig.setPose(m.pose || {});
    else if (m.type === 'avatar-pose-keys') rig.setPoseKeys(m.keys || []);
    else if (m.type === 'avatar-visemes') rig.setVisemes(m.visemes || []);
    else if (m.type === 'avatar-mood') rig.setMood(m.mood || 'neutral');
    else if (m.type === 'avatar-gaze') rig.setGaze(m.gaze || { x: 0, y: 0 });
    else if (m.type === 'avatar-gestures') rig.setGestures(m.gestures || []);
    else if (m.type === 'avatar-clips') rig.setClips(m.clips || {});
    else if (m.type === 'avatar-preset') rig.applyPreset(m.preset || 'bust');
    else if (m.type === 'avatar-text') {
      const line = root.querySelector('.av-line');
      if (line && m.headline) line.textContent = m.headline;
      const kicker = root.querySelector('.av-kicker');
      if (kicker && m.kicker) kicker.textContent = m.kicker;
    }
  } catch (err) {
    window.__sceneSend && window.__sceneSend('scene-error', { message: 'avatar control: ' + err });
  }
});

window.scene = {
  ready: rig.ready,
  seek(t) {
    rig.seek(t);
    tl.seek(t / 1000);
    dust.seek(t);
  },
  destroy() { try { rig.destroy(); } catch (e) {} },
};
"""

CHARACTER_3D_TEMPLATE = {
    "slug": "character-3d",
    "title": "3D avatar",
    "description": "Ready Player Me: скелет 67 костей и 72 ARKit-морфа. Липсинк по 15 Oculus-виземам, моргание, дыхание, взгляд, жесты, кинетическая типографика.",
    "tags": ["scene", "character", "lipsync", "3d", "avatar", "babylon", "studio"],
    "duration": 7000,
    "environment": "studio",
    "view": "",
    "cues": [],
    "objects": [],
    "props_schema": {
        "headline": {"type": "text", "label": "Подпись"},
        "kicker": {"type": "text", "label": "Надпись сверху"},
        "preset": {"type": "select", "label": "Кадр", "options": ["face", "bust", "full", "wide"]},
        "idleClip": {"type": "select", "label": "Базовый клип", "options": ["Neutral_Idle", "Idle", "Talking", "Thinking", "Look_Around"]},
        "talkClip": {"type": "select", "label": "Клип речи", "options": ["Talking", "Neutral_Idle", "Thinking"]},
        "talk_weight": {"type": "number", "label": "Вес речи 0..1"},
        "pose": {"type": "json", "label": "Поза {кость: [x,y,z]}°"},
        "pose_keys": {"type": "json", "label": "Ключи позы [{at,bone,x,y,z}]"},
        "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "sad", "surprise", "anger"]},
        "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
        "gestures": {"type": "json", "label": "Жесты [{at,type,duration}]"},
        "gaze": {"type": "json", "label": "Взгляд {x,y}"},
        "seed": {"type": "integer", "label": "Seed"},
    },
    "default_props": {
        "headline": "Живой 3D-аватар",
        "kicker": "3D STUDIO",
        "preset": "bust",
        "idleClip": "Neutral_Idle",
        "talkClip": "Talking",
        "talk_weight": 0.4,
        "pose": {},
        "pose_keys": [],
        "mood": "neutral",
        "visemes": [],
        "gestures": [{"at": 4200, "type": "wave", "duration": 1800}],
        "gaze": {"x": 0, "y": 0},
        "seed": 3,
    },
    "code": {
        "html": CHARACTER_3D_HTML.strip(),
        "css": (BASE_CSS + "\n" + CHARACTER_3D_CSS).strip(),
        "js": CHARACTER_3D_JS.strip(),
    },
}


TEMPLATES = [
    CHARACTER_3D_TEMPLATE,
    _compose(
        "forest", ["road", "car", "tree", "pine", "cloud"],
        FOREST_DRIVE_JS,
        title="Forest drive",
        description="Машина едет по лесной трассе: колёса, разметка, параллакс леса.",
        tags=["scene", "drive", "forest"],
        duration=7000,
        props_schema={
            "car_color": {"type": "color", "label": "Цвет машины"},
            "cruise_speed": {"type": "number", "label": "Скорость"},
            "tree_count": {"type": "integer", "label": "Деревьев"},
            "pine_count": {"type": "integer", "label": "Сосен"},
        },
        default_props={"car_color": "#E4572E", "cruise_speed": 1.4, "tree_count": 4, "pine_count": 5, "views": {"car": "side"}},
        cues=[{"at": 0, "set": {"speed": 1.4, "brake": False}}, {"at": 2200, "set": {"speed": 2.9}}, {"at": 4600, "set": {"speed": 0.35, "brake": True}}],
    ),
    _compose(
        "city", ["road", "car", "street-lamp", "building"],
        CITY_DRIVE_JS,
        title="City night drive",
        description="Ночная городская трасса: машина, фонари, окна, параллакс.",
        tags=["scene", "drive", "city"],
        duration=6500,
        props_schema={
            "car_color": {"type": "color", "label": "Цвет машины"},
            "cruise_speed": {"type": "number", "label": "Скорость"},
            "tree_count": {"type": "integer", "label": "Деревьев"},
            "pine_count": {"type": "integer", "label": "Сосен"},
        },
        default_props={"car_color": "#38BDF8", "cruise_speed": 1.2, "views": {"car": "side"}},
        cues=[{"at": 0, "set": {"speed": 1.2}}, {"at": 1800, "set": {"speed": 2.16}}, {"at": 4200, "set": {"speed": 0.42}}],
    ),
    _compose(
        "mountains", ["bird", "cloud", "sun"],
        MOUNTAIN_FLIGHT_JS,
        title="Mountain flight",
        description="Птицы над горами на рассвете, облака и параллакс хребтов.",
        tags=["scene", "nature", "flight"],
        duration=6000,
        props_schema={"bird_count": {"type": "integer", "label": "Птиц"}},
        default_props={"bird_count": 3},
    ),
    _compose(
        "office", ["desk", "monitor", "coffee", "plant", "person"],
        OFFICE_DAY_JS,
        title="Office day",
        description="Офис: стол, монитор, кофе с паром, растение, человек.",
        tags=["scene", "interior", "office"],
        duration=6000,
        props_schema={"monitor_title": {"type": "text", "label": "Заголовок на экране"}},
        default_props={"monitor_title": "Live"},
    ),
    _compose(
        "studio", [],
        STUDIO_INTRO_JS,
        title="Studio intro",
        description="Тёмная студия с прожекторами и дымкой.",
        tags=["scene", "studio", "intro"],
        duration=5000,
        props_schema={"headline": {"type": "text", "label": "Заголовок"}},
        default_props={"headline": "STUDIO"},
    ),
    _compose(
        "forest", ["road", "car", "tree", "pine", "cloud"],
        CINEMATIC_FOREST_JS,
        title="Cinematic forest",
        description="2.5D-камера: глубина, параллакс, свет, виньетка, машина в кадре.",
        tags=["scene", "cinematic", "2.5d", "forest"],
        duration=7000,
        props_schema={
            "car_color": {"type": "color", "label": "Цвет машины"},
            "cruise_speed": {"type": "number", "label": "Скорость"},
            "tree_count": {"type": "integer", "label": "Деревьев"},
            "pine_count": {"type": "integer", "label": "Сосен"},
            "camera_amount": {"type": "number", "label": "Амплитуда камеры"},
        },
        default_props={"car_color": "#E4572E", "cruise_speed": 1.4, "tree_count": 5, "pine_count": 6, "camera_amount": 1, "views": {"car": "side"}},
        cues=[{"at": 0, "set": {"speed": 1.4, "brake": False}}, {"at": 2200, "set": {"speed": 2.9}}, {"at": 4600, "set": {"speed": 0.35, "brake": True}}],
        extra_css=CINEMATIC_FOREST_CSS,
    ),
    _compose(
        "studio", ["portrait"],
        CHARACTER_TALK_JS,
        title="Portrait talk",
        description="Нарисованный портрет + оверлей рта: липсинк по виземам, дыхание, кинетическая типографика, пыль.",
        tags=["scene", "character", "lipsync", "studio", "portrait"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "image": {"type": "text", "label": "Портрет (путь)"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "anger", "sad", "surprise"]},
            "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
            "mouth_x": {"type": "number", "label": "Рот X, %"},
            "mouth_y": {"type": "number", "label": "Рот Y, %"},
            "mouth_w": {"type": "number", "label": "Ширина рта, %"},
            "blink": {"type": "boolean", "label": "Моргание"},
        },
        default_props={
            "headline": "Живой персонаж",
            "image": "/portraits/host.png",
            "mood": "joy",
            "visemes": VIS_DEMO,
            "mouth_x": 49, "mouth_y": 45.5, "mouth_w": 7,
            "blink": False,
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">ЖИВОЙ ПЕРСОНАЖ</div>'
            '<div class="talk-mask"><span class="talk-line">Живой персонаж</span></div>'
            '</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 58% 40%, rgba(120,165,255,.12), transparent 60%); }
.obj-portrait { left:58% !important; bottom:2% !important; width:60vmin !important; height:60vmin !important;
  margin-left:-30vmin !important; }
.talk-halo { position:absolute; left:58%; top:4%; width:56vmin; height:56vmin; margin-left:-28vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(150,190,255,.24) 0%, rgba(150,190,255,.05) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.6; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:10%;
  text-align:left; max-width:44%; z-index:35;
  font-family:var(--font-heading); font-weight:700;
  color:var(--text-primary); text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue);
  margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06;
  transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px;
  background:var(--brand-light-blue); }
@media (orientation: portrait) {
  .obj-portrait { left:50% !important; bottom:10% !important; width:86vmin !important; height:86vmin !important;
    margin-left:-43vmin !important; }
  .talk-halo { left:50%; top:8%; width:84vmin; height:84vmin; margin-left:-42vmin; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
  .talk-line { font-size:clamp(18px, 6vmin, 40px); }
}
""",
    ),
    _compose(
        "studio", ["presenter"],
        PRESENTER_TALK_JS,
        title="Character talk",
        description="Ригированный ведущий на canvas: скелет, липсинк по виземам, моргание, взгляд, жест.",
        tags=["scene", "character", "lipsync", "studio", "canvas", "rig"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "anger", "sad", "surprise"]},
            "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
            "gesture_at": {"type": "number", "label": "Жест, мс"},
            "gesture_dur": {"type": "number", "label": "Длительность жеста, мс"},
            "walk": {"type": "boolean", "label": "Ходьба"},
        },
        default_props={
            "headline": "Живой персонаж",
            "mood": "joy",
            "visemes": VIS_DEMO,
            "gesture_at": 4200,
            "gesture_dur": 1500,
            "walk": False,
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">ЖИВОЙ ПЕРСОНАЖ</div>'
            '<div class="talk-mask"><span class="talk-line">Живой персонаж</span></div>'
            '</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 58% 40%, rgba(120,165,255,.12), transparent 60%); }
.obj-presenter { left:60% !important; bottom:4% !important; width:34vmin !important; height:54vmin !important;
  margin-left:-17vmin !important; }
.talk-halo { position:absolute; left:60%; top:6%; width:50vmin; height:50vmin; margin-left:-25vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(150,190,255,.24) 0%, rgba(150,190,255,.05) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.6; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:10%;
  text-align:left; max-width:44%; z-index:35;
  font-family:var(--font-heading); font-weight:700;
  color:var(--text-primary); text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue);
  margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06;
  transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px;
  background:var(--brand-light-blue); }
@media (orientation: portrait) {
  .obj-presenter { left:50% !important; bottom:8% !important; width:66vmin !important; height:104vmin !important;
    margin-left:-33vmin !important; }
  .talk-halo { left:50%; top:12%; width:64vmin; height:64vmin; margin-left:-32vmin; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
  .talk-line { font-size:clamp(18px, 6vmin, 40px); }
}
""",
    ),
    _compose(
        "studio", ["character-rive"],
        RIVE_CHARACTER_JS,
        title="Rive character",
        slug="character-rive",
        description="Rive-риг ведущего: скелет, липсинк по виземам, моргание, взгляд, жесты, ходьба, пресеты персонажей.",
        tags=["scene", "character", "lipsync", "rive", "skeleton", "studio"],
        duration=7000,
        props_schema={
            "character": {"type": "select", "label": "Персонаж", "options": ["host", "cohost", "priest", "historian", "sociologist"]},
            "headline": {"type": "text", "label": "Подпись"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "anger", "sad", "surprise"]},
            "walk": {"type": "boolean", "label": "Ходьба"},
            "gestures": {"type": "json", "label": "Жесты [{at,type,hand,dur}]"},
            "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
            "seed": {"type": "number", "label": "Seed"},
        },
        default_props={
            "character": "host",
            "headline": "Живой персонаж",
            "mood": "joy",
            "walk": False,
            "gestures": [{"at": 4200, "type": "wave", "hand": "R", "dur": 1600}],
            "visemes": VIS_DEMO,
            "seed": 7,
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">RIVE / SKELETON</div>'
            '<div class="talk-mask"><span class="talk-line">Живой персонаж</span></div>'
            '</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 58% 40%, rgba(120,165,255,.12), transparent 60%); }
.talk-halo { position:absolute; left:50%; top:2%; width:62vmin; height:62vmin; margin-left:-31vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(150,190,255,.22) 0%, rgba(150,190,255,.05) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.6; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:10%; text-align:left; max-width:44%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue); margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06; transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px; background:var(--brand-light-blue); }
@media (orientation: portrait) {
  .talk-halo { left:50%; top:4%; width:86vmin; height:86vmin; margin-left:-43vmin; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
  .talk-line { font-size:clamp(18px, 6vmin, 40px); }
}
""",
    ),
    _compose(
        "studio", ["character-rive", "character-rive"],
        RIVE_PANEL_JS,
        title="Rive panel",
        slug="character-rive-panel",
        description="Двое ведущих на Rive-риге: разные пресеты, синхронный seek, общий липсинк.",
        tags=["scene", "character", "lipsync", "rive", "panel", "studio"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "cast": {"type": "json", "label": "Каст [{character,mood,visemes,gestures}]"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "anger", "sad", "surprise"]},
            "visemes": {"type": "json", "label": "Виземы по умолчанию"},
        },
        default_props={
            "headline": "Двое в студии",
            "mood": "joy",
            "visemes": VIS_DEMO,
            "cast": [
                {"character": "host", "mood": "joy"},
                {"character": "cohost", "mood": "joy"},
            ],
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">RIVE / CAST</div>'
            '<div class="talk-mask"><span class="talk-line">Двое в студии</span></div>'
            '</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 50% 40%, rgba(120,165,255,.12), transparent 60%); }
.layer-actors > .obj-character-rive:nth-of-type(1) { left:33% !important; bottom:2% !important; width:36vmin !important; height:60vmin !important; margin-left:-18vmin !important; }
.layer-actors > .obj-character-rive:nth-of-type(2) { left:67% !important; bottom:2% !important; width:36vmin !important; height:60vmin !important; margin-left:-18vmin !important; }
.talk-halo { position:absolute; left:50%; top:2%; width:70vmin; height:70vmin; margin-left:-35vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(150,190,255,.20) 0%, rgba(150,190,255,.04) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.6; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:8%; text-align:left; max-width:50%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue); margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06; transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px; background:var(--brand-light-blue); }
@media (orientation: portrait) {
  .layer-actors > .obj-character-rive:nth-of-type(1) { left:50% !important; bottom:36% !important; width:62vmin !important; height:103vmin !important; margin-left:-31vmin !important; }
  .layer-actors > .obj-character-rive:nth-of-type(2) { left:50% !important; bottom:4% !important; width:62vmin !important; height:103vmin !important; margin-left:-31vmin !important; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
}
""",
    ),
    _compose(
        "studio", ["character-bob"],
        RIVE_BOB_JS,
        title="Bob / ready Rive",
        slug="character-bob",
        description="Готовый Rive-персонаж Bob: 10 визёмов, выражения, взгляд, дыхание, жесты. CC BY 4.0 — emanuelcabezas.",
        tags=["scene", "character", "lipsync", "rive", "ready", "studio"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "joy", "smile", "sad", "surprise", "thinking", "warm", "proud", "focus"]},
            "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
            "gestures": {"type": "json", "label": "Жесты [{at,type,dur}]"},
        },
        default_props={
            "headline": "Мир вам — это живая сцена",
            "mood": "joy",
            "visemes": VIS_DEMO,
            "gestures": [{"at": 4200, "type": "wave", "dur": 1800}],
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">READY RIVE / BOB</div>'
            '<div class="talk-mask"><span class="talk-line">Живой персонаж</span></div>'
            '</div>'
            '<div class="bob-credit">Bob — emanuelcabezas · CC BY 4.0</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 58% 40%, rgba(120,165,255,.12), transparent 60%); }
.talk-halo { position:absolute; left:62%; top:2%; width:62vmin; height:62vmin; margin-left:-31vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(150,190,255,.20) 0%, rgba(150,190,255,.04) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(190,215,255,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.6; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:12%; text-align:left; max-width:44%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-light-blue); margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06; transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px; background:var(--brand-light-blue); }
.bob-credit { position:absolute; right:2.5%; bottom:2.5%; z-index:40; font:400 clamp(8px,1vmin,11px)/1.3 var(--font-sans);
  color:rgba(232,238,247,.5); letter-spacing:.04em; text-shadow:0 1px 6px rgba(0,0,0,.7); }
@media (orientation: portrait) {
  .obj-character-bob { left:50% !important; bottom:8% !important; width:82vmin !important; height:145.8vmin !important; margin-left:-41vmin !important; }
  .talk-halo { left:50%; top:4%; width:84vmin; height:84vmin; margin-left:-42vmin; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
}
""",
    ),
    _compose(
        "studio", ["character-oldman"],
        RIVE_OLDMAN_JS,
        title="Old Man / ready Rive",
        slug="character-oldman",
        description="Готовый Rive-старец в рясе с посохом: полное тело, ткань, глаза, моргание, говорящий рот. CC BY 4.0 — ar.akash.",
        tags=["scene", "character", "lipsync", "rive", "ready", "oldman", "historical"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "mood": {"type": "select", "label": "Настроение", "options": ["neutral", "surprise"]},
            "visemes": {"type": "json", "label": "Виземы [{t,viseme}]"},
            "gestures": {"type": "json", "label": "Жесты [{at,type,dur}]"},
        },
        default_props={
            "headline": "Слово о главном",
            "mood": "neutral",
            "visemes": VIS_DEMO,
            "gestures": [{"at": 4200, "type": "point", "dur": 1500}],
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">READY RIVE / OLD MAN</div>'
            '<div class="talk-mask"><span class="talk-line">Слово о главном</span></div>'
            '</div>'
            '<div class="bob-credit">Old Man — ar.akash · CC BY 4.0</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 58% 38%, rgba(255,190,110,.10), transparent 62%); }
.talk-halo { position:absolute; left:62%; top:2%; width:60vmin; height:60vmin; margin-left:-30vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(255,196,120,.20) 0%, rgba(255,196,120,.04) 45%, transparent 70%);
  filter:blur(6px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(255,225,175,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.65; z-index:30; }
.talk-caption { position:absolute; left:7%; bottom:12%; text-align:left; max-width:44%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-amber); margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4.2vmin, 56px); line-height:1.06; transform-origin:left bottom; }
.talk-caption::before { content:''; position:absolute; left:-14px; top:0; bottom:0; width:3px; background:var(--brand-amber); }
.bob-credit { position:absolute; right:2.5%; bottom:2.5%; z-index:40; font:400 clamp(8px,1vmin,11px)/1.3 var(--font-sans);
  color:rgba(232,238,247,.5); letter-spacing:.04em; text-shadow:0 1px 6px rgba(0,0,0,.7); }
@media (orientation: portrait) {
  .obj-character-oldman { left:50% !important; bottom:8% !important; width:76vmin !important; height:135.1vmin !important; margin-left:-38vmin !important; }
  .talk-halo { left:50%; top:4%; width:82vmin; height:82vmin; margin-left:-41vmin; }
  .talk-caption { left:8%; right:8%; bottom:8%; max-width:none; text-align:center; }
  .talk-caption::before { display:none; }
}
""",
    ),
    _compose(
        "studio", ["character-oldman", "character-oldman"],
        RIVE_OLDMAN_PANEL_JS,
        title="Old Man panel",
        slug="character-oldman-panel",
        description="Два готовых Rive-старца в одной сцене: у каждого свой липсинк, настроение и жест; общий seek и независимые state machine.",
        tags=["scene", "character", "lipsync", "rive", "ready", "oldman", "panel", "historical"],
        duration=7000,
        props_schema={
            "headline": {"type": "text", "label": "Подпись"},
            "cast": {"type": "json", "label": "Каст [{name,mood,visemes,gestures}]"},
            "visemes": {"type": "json", "label": "Виземы первого"},
            "visemes_b": {"type": "json", "label": "Виземы второго"},
        },
        default_props={
            "headline": "Два свидетеля",
            "visemes": VIS_DEMO,
            "visemes_b": VIS_DEMO_B,
            "cast": [
                {"name": "Летописец", "mood": "neutral", "visemes": VIS_DEMO,
                 "gestures": [{"at": 4200, "type": "point", "dur": 1500}]},
                {"name": "Старец", "mood": "surprise", "visemes": VIS_DEMO_B,
                 "gestures": [{"at": 6200, "type": "point", "dur": 1400}]},
            ],
        },
        extra_html=(
            '<div class="talk-halo"></div>'
            '<div class="talk-sweep"></div>'
            '<canvas class="talk-dust" width="1920" height="1080"></canvas>'
            '<div class="actor-tag tag-a">Летописец</div>'
            '<div class="actor-tag tag-b">Старец</div>'
            '<div class="talk-caption">'
            '<div class="talk-kicker">READY RIVE / TWO ELDERS</div>'
            '<div class="talk-mask"><span class="talk-line">Два свидетеля</span></div>'
            '</div>'
            '<div class="bob-credit">Old Man — ar.akash · CC BY 4.0</div>'
        ),
        extra_css="""
.layer-actors { background:radial-gradient(ellipse at 50% 40%, rgba(255,190,110,.10), transparent 64%); }
.layer-actors > .obj-character-oldman:nth-of-type(1) { left:33% !important; bottom:0 !important; width:38vmin !important; height:67.6vmin !important; margin-left:-19vmin !important; }
..layer-actors > .obj-character-oldman:nth-of-type(2) { left:67% !important; bottom:0 !important; width:38vmin !important; height:67.6vmin !important; margin-left:-19vmin !important; transform:scaleX(-1); filter:hue-rotate(-16deg) saturate(.9) brightness(1.03); }
.actor-tag { position:absolute; z-index:36; bottom:42%; font-family:var(--font-sans); font-size:clamp(9px,1.35vmin,14px);
  letter-spacing:.16em; text-transform:uppercase; color:var(--brand-amber); opacity:.9;
  text-shadow:0 2px 12px rgba(0,0,0,.7); }
.actor-tag.tag-a { left:24%; }
.actor-tag.tag-b { left:76%; }
.talk-halo { position:absolute; left:50%; top:2%; width:76vmin; height:76vmin; margin-left:-38vmin;
  border-radius:50%; pointer-events:none;
  background:radial-gradient(circle, rgba(255,196,120,.18) 0%, rgba(255,196,120,.04) 45%, transparent 70%);
  filter:blur(7px); }
.talk-sweep { position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(105deg, transparent 42%, rgba(255,225,175,.10) 50%, transparent 58%);
  transform:translateX(-30%); }
.talk-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.62; z-index:30; }
.talk-caption { position:absolute; left:50%; bottom:7%; transform:translateX(-50%); text-align:center; max-width:72%; z-index:35;
  font-family:var(--font-heading); font-weight:700; color:var(--text-primary);
  text-shadow:0 2px 18px rgba(0,0,0,.6); }
.talk-kicker { font-family:var(--font-sans); font-size:clamp(10px, 1.5vmin, 16px);
  letter-spacing:.12em; text-transform:uppercase; color:var(--brand-amber); margin-bottom:1.2vmin; }
.talk-mask { overflow:hidden; padding:.12em 0 .18em; }
.talk-line { display:inline-block; font-size:clamp(20px, 4vmin, 52px); line-height:1.06; }
.bob-credit { position:absolute; right:2.5%; bottom:2.5%; z-index:40; font:400 clamp(8px,1vmin,11px)/1.3 var(--font-sans);
  color:rgba(232,238,247,.5); letter-spacing:.04em; text-shadow:0 1px 6px rgba(0,0,0,.7); }
@media (orientation: portrait) {
  .layer-actors > .obj-character-oldman:nth-of-type(1) { left:26% !important; bottom:14% !important; width:48vmin !important; height:92vmin !important; margin-left:-24vmin !important; }
  .layer-actors > .obj-character-oldman:nth-of-type(2) { left:74% !important; bottom:14% !important; width:48vmin !important; height:92vmin !important; margin-left:-24vmin !important; }
  .talk-halo { left:50%; top:8%; width:90vmin; height:90vmin; margin-left:-45vmin; }
  .talk-caption { left:8%; right:8%; bottom:3%; max-width:none; transform:none; }
  .actor-tag { bottom:auto; top:30%; font-size:8px; letter-spacing:.1em; }
  .actor-tag.tag-a { left:26%; transform:translateX(-50%); }
  .actor-tag.tag-b { left:74%; transform:translateX(-50%); }
}
""",
    ),
]


def list_environments():
    return ENVIRONMENTS


def get_environment(slug: str):
    return next((e for e in ENVIRONMENTS if e["slug"] == slug), None)


def list_templates():
    return TEMPLATES


def get_template(slug: str):
    return next((t for t in TEMPLATES if t["slug"] == slug), None)


def list_objects():
    items = [o for o in OBJECTS if not o.get("hidden")]
    return sorted(items, key=lambda o: (0 if o.get("category") == "character" else 1, o.get("cast_order", 50), o.get("title", "")))


def get_object(slug: str):
    return next((o for o in OBJECTS if o["slug"] == slug), None)


# ── Pravoslavie channel content pack ────────────────────────────────────────
try:
    from . import pravoslavie_library
    pravoslavie_library.install(ENVIRONMENTS, OBJECTS, TEMPLATES, _compose)
except Exception as _exc:  # pragma: no cover
    print(f"pravoslavie_library install skipped: {_exc}", flush=True)