import re
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
    "title": "Персонаж",
    "category": "character",
    "description": "Риг-заготовка: голова, лицо, рот, руки, ноги. Позже — visemes и липсинк.",
    "tags": ["character", "rig", "person"],
    "mechanics": ["idle", "walk", "talk", "blink"],
    "rig": {
        "type": "svg",
        "parts": ["root", "head", "face", "mouth", "arm-left", "arm-right", "leg-left", "leg-right"],
        "clips": ["idle", "walk", "talk", "blink"],
        "visemes": 10,
    },
    "html": """
<div class="obj-character" style="left:50%; bottom:14%; width:14vmin; height:34vmin">
  <svg viewBox="0 0 120 300" class="character-svg">
    <g class="rig-root" data-rig="root">
      <g class="rig-head" data-rig="head">
        <circle cx="60" cy="44" r="26" fill="#1B2430"/>
        <g class="rig-face" data-rig="face">
          <circle class="rig-eye left" cx="50" cy="40" r="3.4" fill="#E2E8F0"/>
          <circle class="rig-eye right" cx="70" cy="40" r="3.4" fill="#E2E8F0"/>
          <ellipse class="rig-mouth" data-rig="mouth" cx="60" cy="54" rx="7" ry="3" fill="#0B1118"/>
        </g>
      </g>
      <path class="rig-torso" data-rig="torso" d="M38 76 Q60 68 82 76 L88 152 Q60 162 32 152 Z" fill="#1B2430"/>
      <path class="rig-arm left" data-rig="arm-left" d="M38 82 L24 148 L34 150 L46 88 Z" fill="#151D28"/>
      <path class="rig-arm right" data-rig="arm-right" d="M82 82 L96 148 L86 150 L74 88 Z" fill="#151D28"/>
      <path class="rig-leg left" data-rig="leg-left" d="M46 152 L40 262 L54 262 L58 156 Z" fill="#151D28"/>
      <path class="rig-leg right" data-rig="leg-right" d="M74 152 L80 262 L66 262 L62 156 Z" fill="#151D28"/>
    </g>
  </svg>
</div>""",
    "css": """
.obj-character { position:absolute; transform-origin:50% 100%; }
.obj-character .character-svg { width:100%; height:100%; overflow:visible; }
.obj-character .rig-head { transform-box:fill-box; transform-origin:50% 80%; }
.obj-character .rig-arm, .obj-character .rig-leg { transform-box:fill-box; transform-origin:50% 8%; }
.obj-character .rig-mouth { transform-box:fill-box; transform-origin:50% 50%; }
.obj-character.view-side { transform:scaleX(.72); }
""",
}

OBJECTS = [CHARACTER, CAR, ROAD, TREE, PINE, CLOUD, BIRD, LAMP, BUILDING, DESK, MONITOR, COFFEE, PLANT, PERSON, TRAFFIC_LIGHT, SUN, MOON]

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
const cues = SceneKit.cues(cueList);
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
const cues = SceneKit.cues(cueList);
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
const cues = SceneKit.cues(cueList);

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

TEMPLATES = [
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
