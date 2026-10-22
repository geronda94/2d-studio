// Scene runtime: builds a sandboxed HTML document for a scene.
//
// A scene is a small web page with a mandatory time contract:
//   window.scene = { ready?: Promise, seek(t: number): void|Promise, destroy?(): void }
//
// The host calls seek(localTimeMs) on every timeline change. Scenes must not use
// requestAnimationFrame / Date.now / setInterval for animation: the only source of
// time is seek(t). This keeps playback, scrubbing and video export deterministic.

const THEME_KEYS = [
  'bg-base', 'bg-surface', 'bg-surface-hover', 'bg-hover',
  'brand-blue', 'brand-light-blue', 'brand-green', 'brand-amber', 'brand-orange',
  'color-primary', 'color-secondary', 'color-success', 'color-warning', 'color-danger', 'color-info',
  'text-primary', 'text-secondary', 'text-muted',
  'font-sans', 'font-heading', 'font-mono',
  'type-display', 'type-h1', 'type-h2', 'type-body', 'type-caption',
  'item-bg', 'item-primary-bg', 'item-radius', 'item-shadow',
  'item-border-width', 'item-border-style', 'item-padding', 'item-gap',
  'surface-bg', 'line-color',
  'bg-image', 'bg-decorations', 'bg-decorations-size', 'bg-decorations-position',
  'bg-overlay', 'bg-overlay-opacity',
  'slide-bg-1', 'slide-bg-2', 'slide-bg-3', 'slide-bg-4',
]

export function collectThemeVars(hostEl) {
  // In the player the host lives inside .slides-container. In the editor modal it
  // does not, so fall back to the player container behind the modal (if present).
  const container = hostEl?.closest?.('.slides-container') || document.querySelector('.slides-container')
  if (!container) return ''
  const cs = getComputedStyle(container)
  const out = []
  for (const key of THEME_KEYS) {
    const v = cs.getPropertyValue(`--${key}`).trim()
    if (v) out.push(`--${key}: ${v};`)
    const rgb = cs.getPropertyValue(`--${key}-rgb`).trim()
    if (rgb) out.push(`--${key}-rgb: ${rgb};`)
  }
  const fontLink = cs.getPropertyValue('--font-link').trim()
  if (fontLink) out.push(`/* font_link: ${fontLink} */`)
  return out.join('\n')
}

function escapeScript(code) {
  return String(code || '').replace(/<\/script/gi, '<\\/script')
}

function escapeStyle(code) {
  return String(code || '').replace(/<\/style/gi, '<\\/style')
}

export function buildSceneDoc({ code = {}, sceneProps = {}, cues = [], themeCss = '', format = 'landscape', view = '', gsapSource = '', kitSource = '' }) {
  const html = String(code.html || '')
  const css = escapeStyle(code.css || '')
  const js = escapeScript(code.js || '')
  const propsJson = JSON.stringify(sceneProps || {}).replace(/</g, '\\u003c')

  return `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root {
    --bg-base:#0B1322; --bg-surface:#152033; --bg-surface-hover:#1F2D44; --bg-hover:#152033;
    --brand-blue:#2563EB; --brand-light-blue:#38BDF8; --brand-green:#10B981;
    --brand-amber:#F59E0B; --brand-orange:#EA580C;
    --color-primary:var(--brand-blue); --color-secondary:var(--brand-light-blue);
    --color-success:var(--brand-green); --color-warning:var(--brand-amber);
    --text-primary:#F8FAFC; --text-secondary:#94A3B8; --text-muted:#64748B;
    --font-sans:'Inter',sans-serif; --font-heading:'Space Grotesk',sans-serif; --font-mono:'Space Mono',monospace;
    ${themeCss}
    --scene-format: ${format};
  }
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:transparent; }
  *, *::before, *::after { box-sizing:border-box; }
  ${css}
</style>
${gsapSource ? `<script>${escapeScript(gsapSource)}</script>` : ''}
${kitSource ? `<script>${escapeScript(kitSource)}</script>` : ''}
</head>
<body class="view-${view || 'default'}">
${html}
<script>
  window.__sceneProps = ${propsJson};
  window.__sceneCues = ${JSON.stringify(cues || []).replace(/</g, '\\u003c')};
  window.__sceneSend = function (type, data) {
    try { parent.postMessage(Object.assign({ type: type, __scene: true }, data || {}), '*'); } catch (e) {}
  };
  window.addEventListener('error', function (e) {
    window.__sceneSend('scene-error', { message: e.message || 'Script error', source: e.filename || '', line: e.lineno || 0 });
  });
  window.addEventListener('unhandledrejection', function (e) {
    window.__sceneSend('scene-error', { message: String((e.reason && e.reason.message) || e.reason || 'Unhandled rejection') });
  });
  ${js}
</script>
<script>
  (function () {
    window.addEventListener('message', async function (e) {
      var msg = e.data || {};
      if (msg.type === 'patch-style') {
        try {
          var el = document.querySelector('[data-layer-id="' + msg.id + '"]');
          if (el && msg.styles) {
            Object.keys(msg.styles).forEach(function (k) {
              var v = msg.styles[k];
              if (v === null || v === undefined || v === '') el.style.removeProperty(k);
              else el.style.setProperty(k, String(v));
            });
          }
        } catch (e) { window.__sceneSend('scene-error', { message: String(e) }); }
        return;
      }
      if (msg.type === 'seek') {
        try {
          if (window.scene && typeof window.scene.seek === 'function') {
            await window.scene.seek(msg.t);
          }
        } catch (err) {
          window.__sceneSend('scene-error', { message: String((err && err.message) || err) });
        } finally {
          window.__sceneSend('seek-done', { id: msg.id, t: msg.t });
        }
      }
    });
    (async function () {
      try {
        if (window.scene && window.scene.ready) await window.scene.ready;
        if (document.fonts && document.fonts.ready) await document.fonts.ready;
        var imgs = Array.from(document.images || []);
        await Promise.all(imgs.map(function (img) {
          if (img.complete) return Promise.resolve();
          return new Promise(function (resolve) { img.onload = img.onerror = resolve; });
        }));
        window.__sceneSend('scene-ready');
      } catch (err) {
        window.__sceneSend('scene-error', { message: String((err && err.message) || err) });
        window.__sceneSend('scene-ready');
      }
    })();
  })();
</script>
</body>
</html>`
}

let gsapPromise = null
export function loadGsapSource() {
  if (!gsapPromise) {
    gsapPromise = fetch('/vendor/gsap.min.js')
      .then((r) => (r.ok ? r.text() : ''))
      .catch(() => '')
  }
  return gsapPromise
}

let kitPromise = null
export function loadKitSource() {
  if (!kitPromise) {
    kitPromise = fetch('/vendor/scene-kit.js')
      .then((r) => (r.ok ? r.text() : ''))
      .catch(() => '')
  }
  return kitPromise
}
