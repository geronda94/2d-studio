# FROZEN 3D TEMPLATE DRAFT — not imported by backend.
# Extracted from backend/scene_library.py on 2026-10-27.

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


POLY_DUO_HTML = """
<div class="scene poly-duo">
  <div class="layer layer-world" data-layer="world">
    <div class="duo-bg"></div>
    <div class="duo-spot duo-spot-a"></div>
    <div class="duo-spot duo-spot-b"></div>
    <div class="duo-floor"></div>
  </div>
  <div class="layer layer-objects" data-layer="objects"></div>
  <div class="layer layer-actors" data-layer="actors">
    <div class="duo-actor obj-character-mark">
      <canvas class="scene-rig-canvas" width="720" height="1080"></canvas>
      <div class="duo-name">Mark</div>
    </div>
    <div class="duo-actor obj-character-mira">
      <canvas class="scene-rig-canvas" width="720" height="1080"></canvas>
      <div class="duo-name">Mira</div>
    </div>
  </div>
  <div class="layer layer-fx" data-layer="fx"><canvas class="duo-dust" width="1920" height="1080"></canvas></div>
  <div class="layer layer-overlay" data-layer="overlay">
    <div class="duo-caption">
      <div class="duo-kicker">SCENERIG / POLY</div>
      <div class="duo-mask"><span class="duo-line">Два голоса</span></div>
    </div>
  </div>
</div>
<script src="/vendor/babylon.js"></script>
<script src="/vendor/babylonjs.loaders.min.js"></script>
"""

POLY_DUO_CSS = """
.poly-duo { background:#070b12; overflow:hidden; }
.duo-bg { position:absolute; inset:0; background:
  radial-gradient(90% 70% at 50% 8%, #26334b 0%, #141d2b 45%, #070b12 100%); }
.duo-spot { position:absolute; top:-12%; width:44%; height:98%; pointer-events:none;
  background:radial-gradient(ellipse at 50% 0%, rgba(120,170,255,.20), transparent 68%);
  filter:blur(18px); }
.duo-spot-a { left:2%; } .duo-spot-b { right:2%;
  background:radial-gradient(ellipse at 50% 0%, rgba(120,255,200,.14), transparent 68%); }
.duo-floor { position:absolute; left:0; right:0; bottom:0; height:32%;
  background:linear-gradient(180deg, rgba(8,12,20,0) 0%, rgba(8,12,20,.78) 55%, #070b12 100%); }
.duo-actor { position:absolute; bottom:1%; width:40%; height:92%; }
.obj-character-mark { left:4%; }
.obj-character-mira { right:4%; }
.duo-actor .scene-rig-canvas { width:100%; height:100%; display:block; }
.duo-name { position:absolute; left:50%; bottom:1.5%; transform:translateX(-50%);
  font-family:var(--font-mono); font-size:clamp(9px,1.3vmin,15px); letter-spacing:.18em;
  text-transform:uppercase; color:rgba(220,235,255,.62); }
.duo-dust { position:absolute; inset:0; width:100%; height:100%; pointer-events:none;
  mix-blend-mode:screen; opacity:.55; }
.duo-caption { position:absolute; left:50%; bottom:4.5%; transform:translateX(-50%);
  text-align:center; font-family:var(--font-heading); color:var(--text-primary);
  text-shadow:0 2px 20px rgba(0,0,0,.7); z-index:20; }
.duo-kicker { font-family:var(--font-sans); font-size:clamp(9px,1.25vmin,15px);
  letter-spacing:.24em; text-transform:uppercase; color:var(--brand-light-blue); margin-bottom:1vmin; }
.duo-mask { overflow:hidden; padding:.08em 0 .14em; }
.duo-line { display:inline-block; font-size:clamp(20px,4.6vmin,64px); line-height:1.02; }
@media (orientation: portrait) {
  .duo-actor { width:84%; height:48%; left:50% !important; right:auto !important; transform:translateX(-50%); }
  .obj-character-mark { bottom:44%; }
  .obj-character-mira { bottom:2%; }
  .duo-caption { top:5%; bottom:auto; width:92%; }
  .duo-line { font-size:clamp(18px,6vmin,42px); }
}
"""

POLY_DUO_JS = """
const p = window.__sceneProps || {};
const root = document.querySelector('.scene');
const HERO_MAP = {
  Hips: 'hips', Spine: 'spine', Spine1: 'spine1', Spine2: 'chest',
  Neck: 'neck', Head: 'head', LeftEye: 'eye.L', RightEye: 'eye.R',
  LeftShoulder: 'shoulder.L', RightShoulder: 'shoulder.R',
  LeftArm: 'upperArm.L', RightArm: 'upperArm.R',
  LeftForeArm: 'lowerArm.L', RightForeArm: 'lowerArm.R',
  LeftHand: 'hand.L', RightHand: 'hand.R',
  LeftHandMiddle1: 'middle1.L', RightHandMiddle1: 'middle1.R',
  LeftUpLeg: 'upperLeg.L', RightUpLeg: 'upperLeg.R',
  LeftLeg: 'lowerLeg.L', RightLeg: 'lowerLeg.R',
  LeftFoot: 'foot.L', RightFoot: 'foot.R',
  LeftToeBase: 'toe.L', RightToeBase: 'toe.R',
};
const mobile = matchMedia('(pointer:coarse)').matches || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
const specs = [
  {
    src: mobile ? '/models/hero/mark-hd-mobile.glb' : '/models/hero/mark-hd.glb',
    preset: 'bust', height: 1.80,
    appearance: p.appearanceA || {},
    visemes: p.visemesA || [],
    mood: p.moodA || 'neutral',
    map: HERO_MAP, armRestZ: -1.5, armTwist: 0, handTwist: 1.15, headPitch: 0.10,
  },
  {
    src: '/models/brunette.glb',
    preset: 'bust', height: 1.70,
    appearance: p.appearanceB || {},
    visemes: p.visemesB || [],
    mood: p.moodB || 'neutral',
    map: HERO_MAP, armRestZ: -0.50, headPitch: 0.0,
  },
];
const rigs = Array.from(root.querySelectorAll('.scene-rig-canvas')).map((canvas, i) => {
  const s = specs[i] || specs[0];
  return SceneRig.create(canvas, {
    src: s.src, preset: s.preset, height: s.height,
    appearance: s.appearance, mood: s.mood, motion: 'talk', interactive: false,
    boneMap: s.map || null, armRestZ: s.armRestZ || 0, armTwist: s.armTwist || 0, handTwist: s.handTwist || 0, headPitch: s.headPitch || 0,
  });
});
const ready = Promise.all(rigs.map(async (rig, i) => {
  await rig.ready;
  rig.setAppearance(specs[i].appearance);
  rig.setVisemes(specs[i].visemes);
  rig.setMood(specs[i].mood);
}));
const dust = SceneKit.particles(root.querySelector('.duo-dust'), {
  count: Number(p.dust_count) || 44, seed: 23, color: '205,225,255',
  speedY: 7, driftX: 18, sizeMin: 0.8, sizeMax: 2.2, alphaMin: 0.04, alphaMax: 0.18,
});
SceneKit.grain(root, { grainOpacity: 0.09, vignetteStrength: 0.5 });

const caption = root.querySelector('.duo-line');
if (caption && p.headline) caption.textContent = p.headline;
const kicker = root.querySelector('.duo-kicker');
if (kicker && p.kicker) kicker.textContent = p.kicker;

const tl = gsap.timeline({ paused: true });
tl.from('.duo-kicker', { opacity: 0, letterSpacing: '0.4em', duration: 0.8, ease: 'power3.out' }, 0)
  .from('.duo-line', { yPercent: 120, rotate: 2, duration: 0.9, ease: 'power4.out' }, 0.15)
  .from('.duo-actor', { y: 26, opacity: 0, duration: 0.8, ease: 'power3.out', stagger: 0.12 }, 0.1)
  .to('.duo-caption', { opacity: 0, y: -16, duration: 0.5, ease: 'power2.in' }, 7.2);

window.scene = {
  ready,
  seek(t) {
    rigs.forEach((rig) => rig.seek(t));
    tl.seek(t / 1000);
    dust.seek(t);
  },
};
"""

POLY_DUO_TEMPLATE = {
    "slug": "character-poly-duo",
    "title": "Poly duo",
    "description": "Два полигональных SceneRig-персонажа: скелет, настройки внешности, Oculus-15 липсинк, детерминированный seek(t).",
    "tags": ["scene", "character", "scenerig", "lipsync", "3d", "poly", "studio"],
    "duration": 8000,
    "environment": "studio",
    "view": "night",
    "objects": [],
    "props_schema": {
        "headline": {"type": "text", "label": "Заголовок"},
        "kicker": {"type": "text", "label": "Надпись сверху"},
        "visemesA": {"type": "json", "label": "Виземы Mark [{t,viseme}]"},
        "visemesB": {"type": "json", "label": "Виземы Mira [{t,viseme}]"},
        "appearanceA": {"type": "json", "label": "Внешность Mark"},
        "appearanceB": {"type": "json", "label": "Внешность Mira"},
        "moodA": {"type": "select", "label": "Настроение Mark", "options": ["neutral", "joy", "sad"]},
        "moodB": {"type": "select", "label": "Настроение Mira", "options": ["neutral", "joy", "sad"]},
        "dust_count": {"type": "integer", "label": "Пылинки"},
    },
    "default_props": {
        "headline": "Два голоса",
        "kicker": "SCENERIG / POLY",
        "visemesA": VIS_DEMO,
        "visemesB": VIS_DEMO_B,
        "appearanceA": {"skin": "#c98b6b", "hair": "#241812", "top": "#2d5f46",
                        "bottom": "#45454c", "shoes": "#151312", "eyes": "#3c6a8a",
                        "lips": "#8c3d38", "glasses": False, "hood": True, "scale": 1},
        "appearanceB": {"skin": "#dba68a", "hair": "#752914", "top": "#33734f",
                        "bottom": "#382b3d", "shoes": "#3d1c1a", "eyes": "#3373a0",
                        "lips": "#ad4c4c", "glasses": True, "hood": False, "scale": 1},
        "moodA": "neutral", "moodB": "joy", "dust_count": 44,
    },
    "code": {
        "html": POLY_DUO_HTML.strip(),
        "css": (BASE_CSS + "\n" + POLY_DUO_CSS).strip(),
        "js": POLY_DUO_JS.strip(),
    },
}

