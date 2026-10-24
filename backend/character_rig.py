"""SVG-риг персонажа SceneEngine.

Модуль вынесен из `scene_library.py`, чтобы внешность правилась в одном месте.
Стиль: flat-иллюстрация с контуром, локальными тенями и деталями одежды.
Пропорции: ~4.7 головы ростом, плечи ≈1.7 ширины головы.

Контракт с драйвером `SceneKit.characterRig`:
  data-rig="root" | head | hair | gaze | lid-left | lid-right
            | brow-left | brow-right | mouth | torso
            | arm-left | arm-right | leg-left | leg-right
  data-viseme="0..9" — формы рта, "t" — язык.

ViewBox: 0 0 200 380.
"""

CHARACTER_HTML = """
<div class="obj-character" style="left:50%; bottom:10%; width:24vmin; height:56vmin; margin-left:-12vmin">
  <svg viewBox="0 0 200 380" class="character-svg" xmlns="http://www.w3.org/2000/svg">
    <g data-rig="root">

      <!-- ── дальняя рука ───────────────────────────────────────────────── -->
      <g data-rig="arm-left">
        <path class="body shirt" d="M60 106 C50 110 46 124 45 145 L42 230 C41 240 47 244 52 243 C57 242 59 237 59 229 L60 152 C61 130 64 114 70 108 Z"/>
        <path class="sh-r" d="M45 145 L42 230 C41 240 47 244 52 243 C54 242 55 240 55 236 L57 151 C58 128 60 114 63 109 Z"/>
        <path class="ln cuff" d="M43 228 C47 231 54 231 59 228 L59 237 C54 240 47 240 42 237 Z"/>
        <path class="body skin" d="M47 241 C52 240 57 242 58 247 C59 253 55 259 50 259 C45 259 42 254 42 248 C42 245 44 242 47 241 Z"/>
        <path class="det" d="M48 246 L48 255 M52 247 L52 256"/>
      </g>

      <!-- ── ноги ────────────────────────────────────────────────────────── -->
      <g data-rig="leg-left">
        <path class="body pants" d="M62 216 L138 216 L135 246 L132 314 L112 314 L103 254 L97 254 L88 314 L68 314 L65 246 Z"/>
        <path class="det crease" d="M79 254 L77 308 M121 254 L123 308"/>
        <path class="body shoe" d="M66 312 L90 312 L92 330 C92 336 88 339 82 339 L66 339 C62 339 60 336 61 330 Z"/>
        <path class="sole" d="M61 330 L92 330 L92 339 L62 339 C60 339 60 336 61 330 Z"/>
        <path class="det" d="M72 320 L84 320 M74 325 L86 325"/>
      </g>
      <g data-rig="leg-right">
        <path class="body shoe" d="M110 312 L134 312 L139 330 C140 336 137 339 131 339 L110 339 C106 339 105 336 106 330 Z"/>
        <path class="sole" d="M106 330 L139 330 C140 336 137 339 131 339 L106 339 Z"/>
        <path class="det" d="M116 320 L128 320 M114 325 L126 325"/>
      </g>

      <!-- ── корпус ─────────────────────────────────────────────────────── -->
      <g data-rig="torso">
        <path class="body shirt" d="M100 100 C114 100 129 102 140 106 C147 109 150 119 150 130 L147 170 C145 186 143 202 141 216 L59 216 C57 202 55 186 53 170 L50 130 C50 119 53 109 60 106 C71 102 86 100 100 100 Z"/>
        <path class="sh-l" d="M50 130 C51 152 54 190 59 216 L67 216 C63 195 61 165 60 140 C59 122 57 112 53 108 C51 114 50 122 50 130 Z"/>
        <path class="sh-r" d="M150 130 C149 152 146 190 141 216 L133 216 C137 195 139 165 140 140 C141 122 143 112 147 108 C149 114 150 122 150 130 Z"/>
        <path class="ln" d="M100 112 L100 214"/>
        <circle class="btn" cx="100" cy="134" r="2.5"/>
        <circle class="btn" cx="100" cy="160" r="2.5"/>
        <circle class="btn" cx="100" cy="186" r="2.5"/>
        <path class="ln pocket" d="M66 136 L84 136 L84 154 L66 154 Z"/>
        <path class="det" d="M68 139 L82 139"/>
        <path class="belt" d="M59 210 L141 210 L141 221 L59 221 Z"/>
        <path class="buckle" d="M94 211 L106 211 L106 220 L94 220 Z"/>
        <path class="det" d="M100 214 L100 219"/>
        <g class="rim">
          <path d="M150 132 C148.5 152 146 190 141.5 214"/>
          <path d="M141 108 C146 110 149 116 150 126"/>
        </g>
      </g>

      <!-- ── ближняя рука ────────────────────────────────────────────────── -->
      <g data-rig="arm-right">
        <path class="body shirt" d="M140 106 C150 110 154 124 155 145 L158 230 C159 240 153 244 148 243 C143 242 141 237 141 229 L140 152 C139 130 136 114 130 108 Z"/>
        <path class="sh-r" d="M155 145 L158 230 C159 240 153 244 148 243 C146 242 145 240 145 236 L143 151 C142 128 140 114 137 109 Z"/>
        <path class="ln cuff" d="M141 228 C146 231 153 231 158 228 L158 237 C153 240 146 240 141 237 Z"/>
        <path class="body skin" d="M153 241 C148 240 143 242 142 247 C141 253 145 259 150 259 C155 259 158 254 158 248 C158 245 156 242 153 241 Z"/>
        <path class="det" d="M152 246 L152 255 M148 247 L148 256"/>
      </g>

      <!-- ── голова ─────────────────────────────────────────────────────── -->
      <g data-rig="head">
        <path class="body skin" d="M91 86 L109 86 L109 104 C109 107 105 109 100 109 C95 109 91 107 91 104 Z"/>
        <path class="sh-d" d="M91 86 L109 86 L109 94 C104 98 96 98 91 94 Z"/>
        <path class="body skin" d="M72 56 C65 54 61 60 63 67 C64 73 68 76 72 74 Z"/>
        <path class="body skin" d="M128 56 C135 54 139 60 137 67 C136 73 132 76 128 74 Z"/>
        <path class="sh-d" d="M70 60 C66 60 65 66 69 70 Z"/>
        <path class="sh-d" d="M130 60 C134 60 135 66 131 70 Z"/>
        <path class="body skin" d="M100 26 C116 26 128 39 128 58 C128 70 124 80 117 86 C111 91 106 94 100 94 C94 94 89 91 83 86 C76 80 72 70 72 58 C72 39 84 26 100 26 Z"/>
        <ellipse class="sh-l" cx="88" cy="46" rx="17" ry="11"/>
        <path class="sh-r" d="M127 56 C128 70 123 80 116 87 C123 79 125 68 125 56 Z"/>
        <path class="sh-d" d="M84 78 C90 88 95 92 100 92 C105 92 110 88 116 78 C112 89 106 94 100 94 C94 94 88 89 84 78 Z"/>
        <ellipse class="sh-d" cx="87" cy="62" rx="9.5" ry="5.6"/>
        <ellipse class="sh-d" cx="113" cy="62" rx="9.5" ry="5.6"/>
        <ellipse class="eye" cx="87" cy="62" rx="6.6" ry="4.2"/>
        <ellipse class="eye" cx="113" cy="62" rx="6.6" ry="4.2"/>
        <g data-rig="gaze">
          <circle class="iris" cx="87" cy="62" r="2.7"/>
          <circle class="iris" cx="113" cy="62" r="2.7"/>
          <circle class="pupil" cx="87" cy="62" r="1.2"/>
          <circle class="pupil" cx="113" cy="62" r="1.2"/>
          <circle class="gloss" cx="85.9" cy="60.7" r="0.85"/>
          <circle class="gloss" cx="111.9" cy="60.7" r="0.85"/>
        </g>
        <path class="lash" d="M80.4 61 C82.6 57.8 91.4 57.8 93.6 61"/>
        <path class="lash" d="M106.4 61 C108.6 57.8 117.4 57.8 119.6 61"/>
        <path class="det eye-low" d="M81 66.4 C84 68 90 68 93 66.4 M107 66.4 C110 68 116 68 119 66.4"/>
        <path class="body skin lid" data-rig="lid-left" d="M80 55.5 L94 55.5 C94 63 90.4 67.4 87 67.4 C83.4 67.4 80 63 80 55.5 Z"/>
        <path class="body skin lid" data-rig="lid-right" d="M106 55.5 L120 55.5 C120 63 116.4 67.4 113 67.4 C109.4 67.4 106 63 106 55.5 Z"/>
        <path class="brow" data-rig="brow-left" d="M78.5 52.5 C84 49.6 90.5 49.6 95 52.2"/>
        <path class="brow" data-rig="brow-right" d="M105 52.2 C109.5 49.6 116 49.6 121.5 52.5"/>
        <path class="det nose" d="M99.6 64 C101 67 101.4 69.6 100.4 71.6"/>
        <path class="sh-d nose-sh" d="M100 64 C102 68 103 71.6 101 74 C100.4 74.8 99.4 74.6 99 74 C100.4 70.6 100 67.4 100 64 Z"/>
        <ellipse class="nostril" cx="96.4" cy="74.6" rx="1.4" ry="0.9"/>
        <ellipse class="nostril" cx="103.6" cy="74.6" rx="1.4" ry="0.9"/>
        <ellipse class="blush" cx="79" cy="71" rx="5.5" ry="3"/>
        <ellipse class="blush" cx="121" cy="71" rx="5.5" ry="3"/>
        <path class="det phil" d="M98 76.2 L98 78.4 M102 76.2 L102 78.4"/>
        <g data-rig="mouth">
          <path class="vis" data-viseme="0" d="M86 80 Q100 87 114 80 Q100 84 86 80 Z"/>
          <path class="vis" data-viseme="1" d="M83 76 Q100 70 117 76 Q111 93 100 93 Q89 93 83 76 Z"/>
          <path class="vis" data-viseme="2" d="M93 80 Q100 83 107 80 Q100 82 93 80 Z"/>
          <path class="vis" data-viseme="3" d="M89 78 Q100 76 111 78 Q106 86 100 86 Q94 86 89 78 Z"/>
          <path class="vis" data-viseme="4" d="M85 77 Q100 73 115 77 Q109 90 100 90 Q91 90 85 77 Z"/>
          <path class="vis" data-viseme="5" d="M94 78 Q100 76 106 78 Q105 86 100 86 Q95 86 94 78 Z"/>
          <path class="vis" data-viseme="6" d="M92 77.5 Q100 75 108 77.5 Q104 89 100 89 Q96 89 92 77.5 Z"/>
          <path class="vis" data-viseme="7" d="M91 77 Q100 73 109 77 Q105 92 100 92 Q95 92 91 77 Z"/>
          <path class="vis" data-viseme="8" d="M93 77 Q100 74 107 77 Q107 88 100 88 Q93 88 93 77 Z"/>
          <path class="vis" data-viseme="9" d="M95 79 Q100 77 105 79 Q104 85 100 85 Q96 85 95 79 Z"/>
          <path class="vis tongue" data-viseme="t" d="M93 87 Q100 84 107 87 Q104 92 100 92 Q96 92 93 87 Z"/>
        </g>
        <path class="lip-hi" d="M94 86.6 C97 87.6 103 87.6 106 86.6"/>
        <g data-rig="hair">
          <path class="body hair" d="M66 68 C62 38 78 16 100 16 C122 16 138 38 134 68 C131 52 124 43 110 39 C102 36 94 36 86 39 C74 43 67 52 66 68 Z"/>
          <path class="hair-sh" d="M66 68 C62 38 78 16 100 16 C104 16 108 16.4 112 17.4 C96 18 78 34 71 54 C69 60 67 65 66 68 Z"/>
          <path class="hair-hi" d="M78 28 C86 21 100 18 112 21 C104 21 90 24 78 28 Z"/>
          <path class="hair-hi" d="M122 31 C128 39 131 49 132 60 C130 47 126 37 122 31 Z"/>
          <path class="body hair" d="M84 40 C92 36 108 36 116 40 C112 44.5 88 44.5 84 40 Z"/>
          <path class="body hair" d="M70 58 C69 64 70 69 72 72 C73 67 73 62 73 57 Z"/>
          <path class="body hair" d="M130 58 C131 64 130 69 128 72 C127 67 127 62 127 57 Z"/>
        </g>
        <!-- контровой свет от ключевого источника (справа) -->
        <g class="rim">
          <path d="M129 52 C130.5 60 130 70 126 79"/>
          <path d="M126 84 C122 90 116 94 110 95.5"/>
          <path d="M133 40 C135 46 136 52 135.5 58"/>
        </g>
      </g>
    </g>
  </svg>
</div>"""

CHARACTER_CSS = """
.obj-character { position:absolute; transform-origin:50% 100%;
  --char-skin:#F0C9A2; --char-hair:#3B2C24; --char-shirt:#2F6FB3; --char-pants:#2A3444;
  --char-shoe:#1B2230; --char-mouth:#3A1A1C; --char-tongue:#C7606A; --char-eye:#F6F9FC;
  --char-iris:#4A7FB5; --char-pupil:#10161F; --char-line:#1A2230; --char-belt:#243044; }
.obj-character .character-svg { width:100%; height:100%; overflow:visible; }
.obj-character [data-rig] { transform-box:fill-box; }
.obj-character [data-rig="root"] { transform-origin:50% 100%; }
.obj-character [data-rig="head"] { transform-origin:50% 88%; }
.obj-character [data-rig="hair"] { transform-origin:50% 18%; }
.obj-character [data-rig="torso"] { transform-origin:50% 100%; }
.obj-character [data-rig^="arm"] { transform-origin:50% 4%; }
.obj-character [data-rig^="leg"] { transform-origin:50% 1%; }
.obj-character .lid { transform-origin:50% 0%; }
.obj-character [data-rig^="brow"] { transform-origin:50% 100%; }

.obj-character .body { stroke:var(--char-line); stroke-width:1.5; stroke-linejoin:round; stroke-linecap:round; }
.obj-character .shirt { fill:var(--char-shirt); }
.obj-character .pants { fill:var(--char-pants); }
.obj-character .shoe { fill:var(--char-shoe); }
.obj-character .skin { fill:var(--char-skin); }
.obj-character .hair { fill:var(--char-hair); stroke:var(--char-line); stroke-width:1.5; stroke-linejoin:round; }
.obj-character .belt { fill:var(--char-belt); }
.obj-character .buckle { fill:#C8D2E0; stroke:var(--char-line); stroke-width:1.1; }
.obj-character .sole { fill:#C3CDDB; stroke:var(--char-line); stroke-width:1.1; stroke-linejoin:round; }
.obj-character .eye { fill:var(--char-eye); stroke:var(--char-line); stroke-width:1.1; }
.obj-character .iris { fill:var(--char-iris); }
.obj-character .pupil { fill:var(--char-pupil); }
.obj-character .gloss { fill:#FFFFFF; opacity:.9; }
.obj-character .brow { fill:none; stroke:var(--char-hair); stroke-width:2.9; stroke-linecap:round; }
.obj-character .lash { fill:none; stroke:var(--char-line); stroke-width:1.2; stroke-linecap:round; opacity:.7; }
.obj-character .det { fill:none; stroke:var(--char-line); stroke-width:1.1; opacity:.5; stroke-linecap:round; }
.obj-character .det.eye-low { opacity:.3; }
.obj-character .det.crease { opacity:.22; }
.obj-character .det.nose { opacity:.45; }
.obj-character .det.phil { opacity:.22; }
.obj-character .ln { fill:none; stroke:var(--char-line); stroke-width:1.4; opacity:.5; stroke-linecap:round; }
.obj-character .ln.cuff { opacity:.45; }
.obj-character .ln.pocket { opacity:.35; }
.obj-character .nostril { fill:var(--char-line); opacity:.5; }
.obj-character .blush { fill:#E8736B; opacity:.16; }
.obj-character .lip-hi { fill:none; stroke:#FFFFFF; stroke-width:1.5; opacity:.16; stroke-linecap:round; }
.obj-character .vis { fill:var(--char-mouth); opacity:0; stroke:var(--char-line); stroke-width:1.1; stroke-linejoin:round; }
.obj-character [data-viseme="0"] { opacity:1; }
.obj-character .tongue { fill:var(--char-tongue); stroke:none; }
.obj-character .btn { fill:#EEF3F8; stroke:var(--char-line); stroke-width:1; }

.obj-character .sh-l { fill:#FFFFFF; opacity:.09; stroke:none; }
.obj-character .sh-r { fill:#000000; opacity:.10; stroke:none; }
.obj-character .sh-d { fill:#000000; opacity:.16; stroke:none; }
.obj-character .hair-sh { fill:#000000; opacity:.22; stroke:none; }
.obj-character .hair-hi { fill:#FFFFFF; opacity:.14; stroke:none; }
.obj-character .nose-sh { opacity:.14; }

.obj-character .rim { fill:none; stroke:#CFE3FF; stroke-width:2.1; opacity:.5; stroke-linecap:round; }
.obj-character.view-side { transform:scaleX(.72); }
.obj-character.view-three-quarter { transform:scaleX(.88); }
"""
