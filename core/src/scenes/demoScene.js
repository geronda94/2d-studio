// Starter scene for a clean SceneEngine fork.
// It demonstrates the mandatory contract: window.scene.seek(t) drives everything.

export const DEMO_SCENE = {
  code: {
    html: `
<div class="scene">
  <div class="orb orb-a"></div>
  <div class="orb orb-b"></div>
  <div class="grid"></div>

  <div class="content">
    <div class="eyebrow">SCENE ENGINE</div>
    <h1>
      <span class="line">Динамические</span>
      <span class="line accent">сцены</span>
    </h1>
    <p class="sub">HTML · CSS · JS · один контракт: seek(t)</p>
  </div>

  <div class="bars">
    <i class="bar"></i><i class="bar"></i><i class="bar"></i><i class="bar"></i>
    <i class="bar"></i><i class="bar"></i><i class="bar"></i><i class="bar"></i>
  </div>

  <div class="footer">
    <span class="dot"></span>
    <span>детерминированно · без слайдов · из кода</span>
  </div>
</div>`,
    css: `
.scene {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 20%, color-mix(in srgb, var(--brand-blue) 22%, transparent), transparent 38%),
    radial-gradient(circle at 82% 78%, color-mix(in srgb, var(--brand-green) 18%, transparent), transparent 42%),
    var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.grid {
  position: absolute;
  inset: -20%;
  background-image:
    linear-gradient(to right, color-mix(in srgb, var(--text-primary) 7%, transparent) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--text-primary) 7%, transparent) 1px, transparent 1px);
  background-size: 54px 54px;
  transform: perspective(700px) rotateX(58deg) translateY(18%);
  transform-origin: center bottom;
  opacity: 0.55;
}

.orb {
  position: absolute;
  width: 42vmin;
  height: 42vmin;
  border-radius: 50%;
  filter: blur(46px);
  opacity: 0.5;
}
.orb-a { background: var(--brand-blue); top: -12vmin; left: -10vmin; }
.orb-b { background: var(--brand-green); right: -12vmin; bottom: -10vmin; opacity: 0.35; }

.content {
  position: absolute;
  left: 8%;
  top: 50%;
  transform: translateY(-50%);
  max-width: 78%;
}

.eyebrow {
  font-family: var(--font-mono);
  font-size: clamp(10px, 1.2vw, 15px);
  letter-spacing: 0.32em;
  color: var(--text-secondary);
  margin-bottom: 2.2vh;
}

h1 {
  margin: 0;
  font-family: var(--font-heading);
  font-size: clamp(42px, 7.2vw, 118px);
  line-height: 0.98;
  letter-spacing: -0.03em;
}
h1 .line { display: block; }
h1 .accent {
  background: linear-gradient(90deg, var(--brand-light-blue), var(--brand-blue));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.sub {
  margin: 2.4vh 0 0;
  font-size: clamp(13px, 1.55vw, 22px);
  color: var(--text-secondary);
  letter-spacing: 0.01em;
}

.bars {
  position: absolute;
  right: 7%;
  bottom: 12%;
  display: flex;
  align-items: flex-end;
  gap: clamp(5px, 0.8vw, 11px);
  height: 26vh;
}
.bar {
  display: block;
  width: clamp(6px, 0.8vw, 12px);
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(to top, var(--brand-blue), var(--brand-light-blue));
  transform-origin: bottom;
  opacity: 0.85;
}

.footer {
  position: absolute;
  left: 8%;
  bottom: 7%;
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: clamp(9px, 1vw, 13px);
  color: var(--text-muted);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--brand-green);
  box-shadow: 0 0 12px var(--brand-green);
}
`,
    js: `
const tl = gsap.timeline({ paused: true });

tl.from('.eyebrow', { y: 18, opacity: 0, duration: 0.55, ease: 'power3.out' })
  .from('h1 .line', { y: 70, opacity: 0, duration: 0.8, stagger: 0.13, ease: 'power4.out' }, 0.08)
  .from('.sub', { y: 18, opacity: 0, duration: 0.6, ease: 'power3.out' }, 0.62)
  .from('.bar', { scaleY: 0, duration: 0.65, stagger: 0.055, ease: 'power2.out' }, 0.5)
  .from('.footer', { opacity: 0, duration: 0.6 }, 1.0)
  .from('.orb', { scale: 0.72, opacity: 0, duration: 1.2, stagger: 0.12, ease: 'power2.out' }, 0)
  .to('.grid', { backgroundPosition: '0px 54px', duration: 6, ease: 'none' }, 0);

window.scene = {
  seek(t) { tl.seek(t / 1000); }
};
`,
  },
  props: {
    title: 'Динамические сцены',
    subtitle: 'HTML · CSS · JS · один контракт: seek(t)',
  },
  duration: 6000,
}

export function normalizeScenePayload(payload) {
  const p = payload || {}
  return {
    code: {
      html: p.code?.html || DEMO_SCENE.code.html,
      css: p.code?.css || DEMO_SCENE.code.css,
      js: p.code?.js || DEMO_SCENE.code.js,
    },
    props: p.props || {},
    props_schema: p.props_schema || {},
    duration: Number(p.duration) || DEMO_SCENE.duration,
    view: p.view || '',
  }
}
