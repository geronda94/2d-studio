/* PaperCast — deterministic 2D / 2.5D paper-cut characters on Canvas.
 *
 * One shared skeleton, many skins. No WebGL, no Babylon, no per-frame clocks.
 * `seek(t)` draws exactly the same frame for the same t.
 *
 *   const cast = PaperCast.create(canvas, { character: 'mark', pose: 'wave' })
 *   cast.setPose('think')
 *   cast.speak('Привет, это тест липсинка', 2600)
 *   cast.seek(1200)
 *
 * Public data: PaperCast.POSES, PHONEMES, VISEMES, CHARACTERS, RIG.
 */
(function () {
  'use strict'

  const TAU = Math.PI * 2
  const DEG = Math.PI / 180

  // ── one skeleton for every character ────────────────────────────────────
  const RIG = {
    width: 600,
    height: 900,
    floor: 848,
    hip: [300, 545],
    neck: [300, 292],
    head: [300, 186],
    shoulderL: [208, 338],
    shoulderR: [392, 338],
    upperArm: 110,
    lowerArm: 105,
    hipL: [264, 548],
    hipR: [336, 548],
    upperLeg: 158,
    lowerLeg: 148,
    foot: 30,
    joints: ['hip', 'neck', 'head', 'shoulderL', 'elbowL', 'wristL', 'shoulderR', 'elbowR', 'wristR', 'hipL', 'kneeL', 'ankleL', 'hipR', 'kneeR', 'ankleR'],
  }

  // ── joint limits: what a paper puppet may physically do ──────────────────
  // Poses outside the envelope are clamped at draw time; validatePose() reports
  // them so an authoring tool can show the violation instead of hiding it.
  // Anatomical ranges (degrees). See docs/ANATOMY_RIG.md for sources and
  // for the canonical mapping to non-human skeletons. Soft limits are ~90 %
  // of the clinical maximum so live posing never hits the hyperextended end.
  const ANATOMY = {
    shoulder: { flex: [0, 170], extension: [-55, 0], abduct: [0, 170], adduct: [-40, 0], rotIn: [-65, 0], rotOut: [0, 85] },
    elbow: { flex: [0, 150], hyper: [-5, 0] },
    forearm: { pronation: [-85, 85], supination: [-85, 85] },
    wrist: { flex: [-80, 70], radial: [-20, 0], ulnar: [0, 30] },
    fingers: { mcp: [0, 90], pip: [0, 100], dip: [0, 70], thumbCmc: [0, 70], thumbMcp: [0, 50], thumbIp: [0, 80] },
    hip: { flex: [0, 120], extension: [-30, 0], abduct: [0, 45], adduct: [-30, 0], rot: [-45, 45] },
    knee: { flex: [0, 135], hyper: [-10, 0] },
    ankle: { dorsiflex: [0, 20], plantarflex: [-50, 0], inversion: [0, 35], eversion: [0, 15] },
    spine: { lateral: [-40, 40], rot: [-15, 15] },
    neck: { lateral: [-45, 45], rot: [-80, 80] },
    head: { tilt: [-30, 30], turn: [-80, 80], nod: [-20, 20] },
  }
  const FINGER_CURL = { mcp: 90, pip: 100, dip: 70, thumbCmc: 70, thumbMcp: 50, thumbIp: 80 }

  // Curated colour libraries. Studios show them as swatches; arbitrary
  // colours stay available as a custom slot.
  const PALETTES = {
    skin: ['#f6d5bd', '#efc3a3', '#e2b08c', '#d79a72', '#b9815f', '#8d5a3f', '#5f3a28'],
    hair: ['#1c1918', '#2a201c', '#3a2a22', '#5a3a28', '#6b3226', '#8a4b2f', '#b07a3f', '#d9c08a', '#8d8d8d', '#5a5f6a'],
    fabric: ['#2f6b50', '#3f7f6a', '#1f4e3b', '#c98a3f', '#e0b25a', '#a33f3f', '#7a4fbf', '#2b3644', '#2f4452', '#d8d2c4', '#e28a5a', '#4f8e6c'],
    accent: ['#d86a3d', '#c94a4a', '#d8b46f', '#67d8c8', '#4a7bd8', '#8a5ac9'],
    eye: ['#486f5b', '#5b7fa6', '#3d5a80', '#6b4f8a', '#4a6b3f', '#8a6a2f', '#7a5a3f', '#2f2f35'],
  }
  const HAIR_STYLES = ['short', 'bob', 'bun', 'ponytail', 'long', 'curly', 'pixie', 'afro', 'mohawk', 'bald']
  const BEARD_STYLES = ['none', 'short', 'full', 'long', 'goatee', 'mustache']
  const NOSE_STYLES = ['straight', 'button', 'wide', 'hooked', 'small']
  const EYE_STYLES = ['round', 'almond', 'narrow', 'wide']
  const BROW_STYLES = ['soft', 'thick', 'thin', 'straight']
  const LIP_STYLES = ['thin', 'full', 'wide', 'small']
  const PATTERNS = ['solid', 'stripes', 'check', 'dots']
  const ACCESSORIES = ['none', 'tie', 'bowtie', 'necklace', 'badge']
  const GLASSES_STYLES = ['round', 'square', 'aviator']
  const FACE_SHAPES = ['oval', 'round', 'square', 'heart']
  const OUTFITS = ['shirt', 'tee', 'hoodie', 'sweater', 'jacket', 'vest', 'coat', 'dress']
  const BOTTOMS = ['pants', 'shorts', 'skirt', 'dress']

  // One source of truth for outfit combinations. Scenes call this too, so a
  // scene can never render a dress over trousers or two skirts at once.
  function normalizeAppearance(input) {
    const out = Object.assign({}, input || {})
    const outfit = OUTFITS.includes(out.outfit) ? out.outfit : 'shirt'
    out.outfit = outfit
    if (outfit === 'dress') out.bottom = 'dress'
    else if (!BOTTOMS.includes(out.bottom) || out.bottom === 'dress') out.bottom = 'pants'
    if (outfit === 'tee' && (!out.sleeves || out.sleeves === 'auto')) out.sleeves = 'short'
    if ((outfit === 'coat' || outfit === 'jacket') && !out.coatColor) out.coatColor = out.shirtDark || '#2b3644'
    // Unset styles stay unset: the character base (Mark's beard, Mira's bob)
    // must win. Only explicit, invalid values are canonicalised.
    if (out.hairStyle !== undefined) {
      out.hairStyle = HAIR_STYLES.includes(out.hairStyle) ? out.hairStyle : 'short'
    }
    if (out.beardStyle !== undefined) {
      out.beardStyle = BEARD_STYLES.includes(out.beardStyle) ? out.beardStyle : 'none'
      out.beard = out.beardStyle !== 'none'
    } else if (typeof out.beard === 'boolean') {
      out.beardStyle = out.beard ? 'full' : 'none'
    }
    if (out.noseStyle !== undefined && !NOSE_STYLES.includes(out.noseStyle)) out.noseStyle = 'straight'
    if (out.eyeStyle !== undefined && !EYE_STYLES.includes(out.eyeStyle)) out.eyeStyle = 'round'
    if (out.browStyle !== undefined && !BROW_STYLES.includes(out.browStyle)) out.browStyle = 'soft'
    if (out.lipStyle !== undefined && !LIP_STYLES.includes(out.lipStyle)) out.lipStyle = 'full'
    if (out.pattern !== undefined && !PATTERNS.includes(out.pattern)) out.pattern = 'solid'
    if (out.accessory !== undefined && !ACCESSORIES.includes(out.accessory)) out.accessory = 'none'
    if (out.glassesStyle !== undefined && !GLASSES_STYLES.includes(out.glassesStyle)) out.glassesStyle = 'round'
    if (out.faceShape !== undefined && !FACE_SHAPES.includes(out.faceShape)) out.faceShape = 'oval'
    return out
  }

  function validateAppearance(input) {
    const a = input || {}
    const issues = []
    const outfit = a.outfit || 'shirt'
    if (outfit === 'dress' && a.bottom && a.bottom !== 'dress') {
      issues.push({ code: 'dress-bottom', text: 'Платье уже задаёт низ: брюки/юбка игнорируются', fix: 'bottom=dress' })
    }
    if (outfit === 'tee' && a.sleeves === 'long') {
      issues.push({ code: 'tee-long', text: 'У футболки длинные рукава — будет свитер', fix: 'sleeves=short' })
    }
    if (outfit === 'coat' && a.bottom === 'shorts') {
      issues.push({ code: 'coat-shorts', text: 'Пальто с шортами: зимний/летний образ смешан', fix: 'bottom=pants' })
    }
    if (!HAIR_STYLES.includes(a.hairStyle) && a.hairStyle) {
      issues.push({ code: 'hair-style', text: 'Неизвестная причёска', fix: 'hairStyle=short' })
    }
    if (!BEARD_STYLES.includes(a.beardStyle) && a.beardStyle) {
      issues.push({ code: 'beard-style', text: 'Неизвестная борода', fix: 'beardStyle=none' })
    }
    return { ok: issues.length === 0, issues, fixed: normalizeAppearance(a) }
  }

  // Per-joint motion envelopes for direct manipulation. One entry per FK
  // channel; `axis` names the motion a person performs (not the bone name),
  // so the studio can label a handle "подъём", "сгиб", "наклон".
  // Values are degrees in the canvas plane for the LEFT side; `mirror` means
  // the right side uses the negated range (a right arm raises with a negative
  // rotation), which is what jointRangeFor() returns.
  const JOINT_RANGES = {
    spine: { min: -40, max: 40, axis: 'наклон корпуса' },
    neck: { min: -40, max: 40, axis: 'наклон шеи' },
    head: { min: -28, max: 28, axis: 'наклон головы' },
    sh: { min: -55, max: 170, mirror: true, axis: 'подъём руки' },
    elbow: { min: 0, max: 150, mirror: true, axis: 'сгиб локтя' },
    wrist: { min: -70, max: 70, axis: 'сгиб кисти' },
    hip: { min: -25, max: 90, mirror: true, axis: 'отведение бедра' },
    // the shin swings back and inward, so the left knee bends counter-clockwise
    knee: { min: -135, max: 0, mirror: true, axis: 'сгиб колена' },
    ankle: { min: -45, max: 25, axis: 'сгиб стопы' },
  }
  function jointRangeFor(rangeKey, side) {
    const r = JOINT_RANGES[rangeKey]
    if (!r) return null
    if (r.mirror && side === 'R') return { min: -r.max, max: -r.min, axis: r.axis }
    return r
  }
  const LIMITS = {
    body: { x: [-46, 46], y: [-26, 26], rot: [-16, 16] },
    head: { tilt: [-30, 30], turn: [-0.8, 0.8], nod: [-20, 20] },
    arm: { reachMin: 34, reachMax: 0.995, elbow: [10, 150] },
    leg: { swing: [-30, 45], knee: [0, 135] },
    // engine-side safety clamp: the union of both sides
    fk: Object.fromEntries(Object.entries(JOINT_RANGES).map(([k, v]) => {
      const m = Math.max(Math.abs(v.min), Math.abs(v.max))
      return [k, [-m, m]]
    })),
  }

  const INK = '#20232d'
  const PAPER = '#f8f2e6'

  // ── skins ────────────────────────────────────────────────────────────────
  const CHARACTERS = {
    mark: {
      id: 'mark',
      label: 'Mark',
      pronoun: 'он',
      skin: '#d79a72',
      skinLight: '#efbd95',
      skinDark: '#ae704f',
      hair: '#2a201c',
      hairLight: '#4a3830',
      shirt: '#2f6b50',
      shirtDark: '#1f4e3b',
      shirtLight: '#4f8e6c',
      pants: '#343b4a',
      pantsDark: '#242a36',
      shoes: '#211b19',
      sole: '#c9b9a0',
      accent: '#d86a3d',
      eye: '#486f5b',
      lip: '#a95f55',
      beard: true,
      glasses: false,
      hairStyle: 'short',
      headScale: 0.84,
      build: 1.04,
      shoulder: 1.06,
    },
    mira: {
      id: 'mira',
      label: 'Mira',
      pronoun: 'она',
      skin: '#e2b08c',
      skinLight: '#f5cbaa',
      skinDark: '#b77b5e',
      hair: '#6b3226',
      hairLight: '#9a513d',
      shirt: '#c98a3f',
      shirtDark: '#97632c',
      shirtLight: '#e1a95a',
      pants: '#2f4452',
      pantsDark: '#22323d',
      shoes: '#5a2e2a',
      sole: '#d3c2ab',
      accent: '#2e7a78',
      eye: '#4f7890',
      lip: '#b85f63',
      beard: false,
      glasses: true,
      hairStyle: 'bob',
      headScale: 0.86,
      build: 0.94,
      shoulder: 0.91,
    },
  }

  // ── 17 mouth shapes, shared by every phoneme ─────────────────────────────
  const VISEMES = {
    sil: { w: 45, h: 4, teeth: 0, tongue: 0, round: 0.10, smile: 0.42 },
    AA:  { w: 48, h: 31, teeth: 1, tongue: 0.20, round: 0.05, smile: 0.08 },
    E:   { w: 49, h: 18, teeth: 1, tongue: 0.05, round: 0.02, smile: 0.20 },
    I:   { w: 45, h: 9,  teeth: 1, tongue: 0.00, round: 0.00, smile: 0.28 },
    O:   { w: 27, h: 27, teeth: 0, tongue: 0.10, round: 0.80, smile: 0.02 },
    U:   { w: 24, h: 20, teeth: 0, tongue: 0.00, round: 0.88, smile: 0.00 },
    MBP: { w: 32, h: 2,  teeth: 0, tongue: 0.00, round: 0.00, smile: 0.10 },
    FV:  { w: 37, h: 8,  teeth: 1, tongue: 0.00, round: 0.00, smile: 0.06 },
    L:   { w: 36, h: 23, teeth: 0, tongue: 1.00, round: 0.05, smile: 0.10 },
    WQ:  { w: 22, h: 17, teeth: 0, tongue: 0.00, round: 0.94, smile: 0.00 },
    TH:  { w: 34, h: 12, teeth: 1, tongue: 0.65, round: 0.02, smile: 0.04 },
    S:   { w: 39, h: 7,  teeth: 1, tongue: 0.00, round: 0.00, smile: 0.12 },
    SH:  { w: 31, h: 15, teeth: 0, tongue: 0.00, round: 0.64, smile: 0.03 },
    R:   { w: 25, h: 13, teeth: 0, tongue: 0.10, round: 0.58, smile: 0.05 },
    N:   { w: 34, h: 8,  teeth: 0, tongue: 0.05, round: 0.06, smile: 0.08 },
    D:   { w: 38, h: 15, teeth: 0, tongue: 0.08, round: 0.04, smile: 0.06 },
    K:   { w: 35, h: 12, teeth: 1, tongue: 0.10, round: 0.14, smile: 0.04 },
    CH:  { w: 31, h: 19, teeth: 0, tongue: 0.12, round: 0.30, smile: 0.02 },
  }

  // ── phoneme inventory ────────────────────────────────────────────────────
  // Russian: 6 vowels + 36 consonants = 42. English (ARPAbet): 39.
  // These are the labels a character can be driven by; text is approximated
  // to the same inventory by phonemize().
  const PHONEMES = {}
  function ph(id, ipa, viseme, kind, example, lang) {
    PHONEMES[id] = { id, ipa, viseme, kind, example, lang }
  }

  // Russian vowels
  ;[
    ['a', 'a', 'AA', 'глаз'], ['o', 'o', 'O', 'дом'], ['u', 'u', 'U', 'лук'],
    ['ɨ', 'ɨ', 'I', 'сын'], ['ɛ', 'ɛ', 'E', 'это'], ['i', 'i', 'I', 'ива'],
  ].forEach(([id, ipa, v, ex]) => ph(id, ipa, v, 'vowel', ex, 'ru'))

  // Russian consonants
  ;[
    ['b', 'b', 'MBP', 'был'], ['bʲ', 'bʲ', 'MBP', 'бить'],
    ['p', 'p', 'MBP', 'пар'], ['pʲ', 'pʲ', 'MBP', 'пить'],
    ['v', 'v', 'FV', 'вол'], ['vʲ', 'vʲ', 'FV', 'вить'],
    ['f', 'f', 'FV', 'фон'], ['fʲ', 'fʲ', 'FV', 'фильм'],
    ['g', 'g', 'K', 'год'], ['gʲ', 'gʲ', 'K', 'гиря'],
    ['k', 'k', 'K', 'кот'], ['kʲ', 'kʲ', 'K', 'кит'],
    ['d', 'd', 'D', 'дом'], ['dʲ', 'dʲ', 'D', 'день'],
    ['t', 't', 'D', 'том'], ['tʲ', 'tʲ', 'D', 'тетя'],
    ['z', 'z', 'S', 'зуб'], ['zʲ', 'zʲ', 'S', 'зима'],
    ['s', 's', 'S', 'сом'], ['sʲ', 'sʲ', 'S', 'сила'],
    ['ʐ', 'ʐ', 'SH', 'жук'], ['ʂ', 'ʂ', 'SH', 'шум'],
    ['ɕː', 'ɕː', 'SH', 'щи'], ['ts', 'ts', 'S', 'цвет'],
    ['tɕ', 'tɕ', 'CH', 'час'],
    ['m', 'm', 'MBP', 'мама'], ['mʲ', 'mʲ', 'MBP', 'мяч'],
    ['n', 'n', 'N', 'нос'], ['nʲ', 'nʲ', 'N', 'нет'],
    ['l', 'l', 'L', 'лампа'], ['lʲ', 'lʲ', 'L', 'лес'],
    ['r', 'r', 'R', 'рак'], ['rʲ', 'rʲ', 'R', 'рис'],
    ['j', 'j', 'I', 'йод'], ['x', 'x', 'K', 'хор'], ['xʲ', 'xʲ', 'K', 'хит'],
  ].forEach(([id, ipa, v, ex]) => ph(id, ipa, v, 'consonant', ex, 'ru'))

  // English ARPAbet
  ;[
    ['AA', 'ɑ', 'AA', 'father'], ['AE', 'æ', 'AA', 'cat'], ['AH', 'ʌ', 'AA', 'cup'],
    ['AO', 'ɔ', 'O', 'thought'], ['AW', 'aʊ', 'AA', 'cow'], ['AY', 'aɪ', 'AA', 'my'],
    ['EH', 'ɛ', 'E', 'bed'], ['ER', 'ɝ', 'R', 'bird'], ['EY', 'eɪ', 'E', 'say'],
    ['IH', 'ɪ', 'I', 'sit'], ['IY', 'i', 'I', 'see'], ['OW', 'oʊ', 'O', 'go'],
    ['OY', 'ɔɪ', 'O', 'boy'], ['UH', 'ʊ', 'U', 'book'], ['UW', 'u', 'U', 'too'],
    ['B', 'b', 'MBP', 'boy'], ['CH', 'tʃ', 'CH', 'chair'], ['D', 'd', 'D', 'dog'],
    ['DH', 'ð', 'TH', 'this'], ['F', 'f', 'FV', 'fish'], ['G', 'g', 'K', 'go'],
    ['HH', 'h', 'K', 'hat'], ['JH', 'dʒ', 'CH', 'jump'], ['K', 'k', 'K', 'key'],
    ['L', 'l', 'L', 'lip'], ['M', 'm', 'MBP', 'man'], ['N', 'n', 'N', 'no'],
    ['NG', 'ŋ', 'N', 'sing'], ['P', 'p', 'MBP', 'pen'], ['R', 'ɹ', 'R', 'red'],
    ['S', 's', 'S', 'sun'], ['SH', 'ʃ', 'SH', 'ship'], ['T', 't', 'D', 'top'],
    ['TH', 'θ', 'TH', 'thin'], ['V', 'v', 'FV', 'van'], ['W', 'w', 'WQ', 'we'],
    ['Y', 'j', 'I', 'yes'], ['Z', 'z', 'S', 'zoo'], ['ZH', 'ʒ', 'SH', 'measure'],
  ].forEach(([id, ipa, v, ex]) => ph(id, ipa, v, 'consonant', ex, 'en'))

  ph('sil', '—', 'sil', 'silence', 'пауза', 'both')

  // ── poses: static hand targets, using the same skeleton for all skins ────
  // hand targets are absolute canvas points in the neutral body frame.
  const BASE_POSE = {
    body: { x: 0, y: 0, rot: 0 },
    head: { tilt: 1.2, turn: 0.03, nod: 0 },
    armL: { hand: [132, 532], bend: 1, handPose: 'relaxed', handRot: 0 },
    armR: { hand: [468, 526], bend: -1, handPose: 'relaxed', handRot: 0 },
    legL: { swing: -2.5, knee: 4 },
    legR: { swing: 2.5, knee: 6 },
    front: 'R',
    emotion: 'neutral',
  }

  function pose(name, p) {
    return Object.assign({}, BASE_POSE, p, { name })
  }

  const POSES = {
    neutral: pose('neutral', {}),
    wave: pose('wave', {
      armR: { hand: [452, 105], bend: -1, handPose: 'open', handRot: 8 },
      armL: { hand: [168, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -4, turn: -0.08, nod: 0 }, emotion: 'joy', front: 'R',
    }),
    point: pose('point', {
      armR: { hand: [525, 300], bend: -1, handPose: 'point', handRot: 4 },
      armL: { hand: [172, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 0, turn: 0.28, nod: 0 }, front: 'R',
    }),
    explain: pose('explain', {
      armR: { hand: [405, 415], bend: -1, handPose: 'palm', handRot: 75 },
      armL: { hand: [195, 415], bend: 1, handPose: 'palm', handRot: -75 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, front: 'both',
    }),
    shrug: pose('shrug', {
      armR: { hand: [500, 300], bend: -1, handPose: 'palm', handRot: -24 },
      armL: { hand: [100, 300], bend: 1, handPose: 'palm', handRot: 24 },
      head: { tilt: 5, turn: 0, nod: 0 }, body: { x: 0, y: 4, rot: 0 },
      emotion: 'surprise', front: 'both',
    }),
    think: pose('think', {
      armR: { hand: [356, 222], bend: -1, handPose: 'pinch', handRot: -18 },
      armL: { hand: [180, 510], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 8, turn: -0.10, nod: 0 }, emotion: 'think', front: 'R',
    }),
    thumbsUp: pose('thumbsUp', {
      armR: { hand: [486, 300], bend: -1, handPose: 'thumb', handRot: 0 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -2, turn: 0, nod: 0 }, emotion: 'joy', front: 'R',
    }),
    ok: pose('ok', {
      armR: { hand: [380, 390], bend: -1, handPose: 'ok', handRot: 0 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -2, turn: 0, nod: 0 }, emotion: 'joy', front: 'R',
    }),
    stop: pose('stop', {
      armR: { hand: [500, 280], bend: -1, handPose: 'palm', handRot: -4 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, emotion: 'surprise', front: 'R',
    }),
    cheer: pose('cheer', {
      armR: { hand: [485, 105], bend: -1, handPose: 'open', handRot: 10 },
      armL: { hand: [115, 105], bend: 1, handPose: 'open', handRot: -10 },
      head: { tilt: 0, turn: 0, nod: -3 }, emotion: 'joy', front: 'both',
    }),
    crossArms: pose('crossArms', {
      armR: { hand: [250, 410], bend: -1, handPose: 'relaxed', handRot: -68 },
      armL: { hand: [350, 398], bend: 1, handPose: 'relaxed', handRot: 68 },
      head: { tilt: 2, turn: 0, nod: 0 }, front: 'both',
    }),
    handsOnHips: pose('handsOnHips', {
      armR: { hand: [402, 495], bend: -1, handPose: 'relaxed', handRot: -20 },
      armL: { hand: [198, 495], bend: 1, handPose: 'relaxed', handRot: 20 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, front: 'both',
    }),
    facepalm: pose('facepalm', {
      armR: { hand: [322, 222], bend: -1, handPose: 'palm', handRot: -92 },
      armL: { hand: [180, 510], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 14, turn: -0.12, nod: 0 }, emotion: 'sad', front: 'R',
    }),
    salute: pose('salute', {
      armR: { hand: [345, 240], bend: -1, handPose: 'palm', handRot: -18 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, front: 'R',
    }),
    bow: pose('bow', {
      armR: { hand: [450, 510], bend: -1, handPose: 'relaxed', handRot: 0 },
      armL: { hand: [150, 510], bend: 1, handPose: 'relaxed', handRot: 0 },
      body: { x: 0, y: 8, rot: 7 }, head: { tilt: 10, turn: 0, nod: 3 },
      front: 'R',
    }),
    leanIn: pose('leanIn', {
      armR: { hand: [430, 405], bend: -1, handPose: 'palm', handRot: -8 },
      armL: { hand: [210, 405], bend: 1, handPose: 'palm', handRot: 8 },
      body: { x: 10, y: 2, rot: -2 }, head: { tilt: 2, turn: 0, nod: 2 },
      front: 'both',
    }),
    clap: pose('clap', {
      armR: { hand: [310, 405], bend: -1, handPose: 'palm', handRot: -8 },
      armL: { hand: [290, 405], bend: 1, handPose: 'palm', handRot: 8 },
      head: { tilt: -2, turn: 0, nod: 0 }, emotion: 'joy', front: 'both',
    }),
    count: pose('count', {
      armR: { hand: [440, 260], bend: -1, handPose: 'one', handRot: 4 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -2, turn: 0.10, nod: 0 }, front: 'R',
    }),
    present: pose('present', {
      armR: { hand: [535, 430], bend: -1, handPose: 'palm', handRot: -6 },
      armL: { hand: [195, 500], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 0, turn: 0.32, nod: 0 }, front: 'R',
    }),
    heart: pose('heart', {
      armR: { hand: [330, 360], bend: -1, handPose: 'heart', handRot: -26 },
      armL: { hand: [270, 360], bend: 1, handPose: 'heart', handRot: 26 },
      head: { tilt: -3, turn: 0, nod: 0 }, emotion: 'joy', front: 'both',
    }),
    fist: pose('fist', {
      armR: { hand: [430, 380], bend: -1, handPose: 'fist', handRot: 0 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 2, turn: 0, nod: 0 }, emotion: 'anger', front: 'R',
    }),
    peace: pose('peace', {
      armR: { hand: [460, 150], bend: -1, handPose: 'peace', handRot: 4 },
      armL: { hand: [170, 530], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -2, turn: 0, nod: 0 }, emotion: 'joy', front: 'R',
    }),
    chin: pose('chin', {
      armR: { hand: [345, 232], bend: -1, handPose: 'pinch', handRot: -44 },
      armL: { hand: [235, 420], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 6, turn: -0.10, nod: 0 }, emotion: 'think', front: 'R',
    }),
    openPalms: pose('openPalms', {
      armR: { hand: [500, 390], bend: -1, handPose: 'palm', handRot: -18 },
      armL: { hand: [100, 390], bend: 1, handPose: 'palm', handRot: 18 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, front: 'both',
    }),
    tapFoot: pose('tapFoot', {
      armR: { hand: [460, 525], bend: -1, handPose: 'relaxed', handRot: 0 },
      armL: { hand: [140, 525], bend: 1, handPose: 'relaxed', handRot: 0 },
      legR: { swing: 0, knee: 18 }, head: { tilt: 3, turn: 0, nod: 0 },
      emotion: 'think', front: 'R',
    }),
    nod: pose('nod', {
      head: { tilt: 0, turn: 0, nod: 9 }, emotion: 'joy', front: 'R',
    }),
    headShake: pose('headShake', {
      head: { tilt: 0, turn: -0.75, nod: 0 }, emotion: 'neutral', front: 'R',
    }),
    listen: pose('listen', {
      armR: { hand: [355, 245], bend: -1, handPose: 'palm', handRot: -84 },
      armL: { hand: [180, 510], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: -3, turn: -0.30, nod: 0 }, emotion: 'neutral', front: 'R',
    }),
    shush: pose('shush', {
      armR: { hand: [333, 275], bend: -1, handPose: 'point', handRot: -90 },
      armL: { hand: [180, 510], bend: 1, handPose: 'relaxed', handRot: 0 },
      head: { tilt: 2, turn: 0, nod: 0 }, emotion: 'neutral', front: 'R',
    }),
    armsWide: pose('armsWide', {
      armR: { hand: [535, 330], bend: -1, handPose: 'open', handRot: -10 },
      armL: { hand: [65, 330], bend: 1, handPose: 'open', handRot: 10 },
      head: { tilt: 1.2, turn: 0.03, nod: 0 }, emotion: 'joy', front: 'both',
    }),
    lowPresent: pose('lowPresent', {
      armR: { hand: [500, 510], bend: -1, handPose: 'palm', handRot: -4 },
      armL: { hand: [120, 370], bend: 1, handPose: 'palm', handRot: 12 },
      head: { tilt: 1, turn: 0.20, nod: 0 }, front: 'both',
    }),
  }

  // ── gesture clips: keyframes with per-segment easing ────────────────────
  function derivePose(base, patch) {
    const out = JSON.parse(JSON.stringify(base))
    for (const key of Object.keys(patch)) {
      const v = patch[key]
      if (v && typeof v === 'object' && !Array.isArray(v)) Object.assign(out[key], v)
      else out[key] = v
    }
    return out
  }

  function makeClip(id, duration, keys, loop) {
    return { id, duration, loop: !!loop, keys }
  }

  // anticipation (backIn) → action (backOut) → settle (inOut)
  const CLIPS = {
    wave: makeClip('wave', 1500, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 170, pose: derivePose(POSES.neutral, {
        armR: { hand: [428, 472], bend: -1, handPose: 'relaxed', handRot: 0 },
        body: { rot: -2 }, head: { tilt: -3 },
      }), ease: 'backIn' },
      { at: 430, pose: POSES.wave, ease: 'backOut' },
      { at: 650, pose: derivePose(POSES.wave, {
        armR: { hand: [462, 116], handRot: -6 }, head: { tilt: 4 },
      }), ease: 'inOut' },
      { at: 830, pose: derivePose(POSES.wave, {
        armR: { hand: [442, 100], handRot: 12 }, head: { tilt: -2 },
      }), ease: 'inOut' },
      { at: 1030, pose: POSES.wave, ease: 'inOut' },
      { at: 1500, pose: POSES.neutral, ease: 'inOut' },
    ]),
    point: makeClip('point', 1300, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 180, pose: derivePose(POSES.neutral, {
        armR: { hand: [392, 418], bend: -1, handPose: 'relaxed', handRot: -10 },
        head: { turn: -0.12 },
      }), ease: 'backIn' },
      { at: 440, pose: POSES.point, ease: 'backOut' },
      { at: 950, pose: POSES.point, ease: 'inOut' },
      { at: 1300, pose: POSES.neutral, ease: 'inOut' },
    ]),
    explain: makeClip('explain', 1700, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 260, pose: POSES.explain, ease: 'backOut' },
      { at: 620, pose: derivePose(POSES.explain, {
        armR: { hand: [418, 404] }, head: { tilt: 3 },
      }), ease: 'inOut' },
      { at: 980, pose: derivePose(POSES.explain, {
        armL: { hand: [186, 408] }, head: { tilt: -2 },
      }), ease: 'inOut' },
      { at: 1260, pose: POSES.explain, ease: 'inOut' },
      { at: 1700, pose: POSES.neutral, ease: 'inOut' },
    ]),
    shrug: makeClip('shrug', 1250, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 240, pose: POSES.shrug, ease: 'backOut' },
      { at: 820, pose: POSES.shrug, ease: 'inOut' },
      { at: 1250, pose: POSES.neutral, ease: 'inOut' },
    ]),
    think: makeClip('think', 1600, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 320, pose: POSES.think, ease: 'backOut' },
      { at: 1150, pose: derivePose(POSES.think, { head: { tilt: 10 } }), ease: 'inOut' },
      { at: 1600, pose: POSES.neutral, ease: 'inOut' },
    ]),
    thumbsUp: makeClip('thumbsUp', 1250, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 280, pose: POSES.thumbsUp, ease: 'backOut' },
      { at: 850, pose: POSES.thumbsUp, ease: 'inOut' },
      { at: 1250, pose: POSES.neutral, ease: 'inOut' },
    ]),
    present: makeClip('present', 1350, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 260, pose: derivePose(POSES.neutral, {
        armR: { hand: [430, 470], bend: -1, handPose: 'relaxed' }, body: { rot: -1.5 },
      }), ease: 'backIn' },
      { at: 520, pose: POSES.present, ease: 'backOut' },
      { at: 1000, pose: POSES.present, ease: 'inOut' },
      { at: 1350, pose: POSES.neutral, ease: 'inOut' },
    ]),
    nod: makeClip('nod', 1100, [
      { at: 0, pose: POSES.neutral, ease: 'inOut' },
      { at: 240, pose: derivePose(POSES.neutral, { head: { nod: 9, tilt: 2 } }), ease: 'out' },
      { at: 460, pose: derivePose(POSES.neutral, { head: { nod: -3 } }), ease: 'inOut' },
      { at: 700, pose: POSES.neutral, ease: 'inOut' },
      { at: 1100, pose: POSES.neutral, ease: 'inOut' },
    ]),
    // A front-view walk in place: the lifted knee reads as a step, the body
    // bobs and the arms counter-swing. Loop it and move the actor in a scene.
    walk: makeClip('walk', 1000, [
      { at: 0, pose: derivePose(POSES.neutral, {
        legL: { swing: -14, knee: 36 }, legR: { swing: 4, knee: 7 },
        body: { x: 0, y: 2, rot: -1 }, head: { tilt: 1, turn: 0.05 },
        armL: { hand: [168, 500], bend: 1, handPose: 'relaxed', handRot: -8 },
        armR: { hand: [446, 526], bend: -1, handPose: 'relaxed', handRot: 8 },
      }), ease: 'inOut' },
      { at: 250, pose: derivePose(POSES.neutral, {
        legL: { swing: -2, knee: 10 }, legR: { swing: 2, knee: 14 },
        body: { x: 0, y: -3, rot: 0.5 }, head: { tilt: 0, turn: 0.02 },
        armL: { hand: [138, 524], bend: 1, handPose: 'relaxed', handRot: 0 },
        armR: { hand: [462, 524], bend: -1, handPose: 'relaxed', handRot: 0 },
      }), ease: 'inOut' },
      { at: 500, pose: derivePose(POSES.neutral, {
        legL: { swing: 4, knee: 7 }, legR: { swing: -14, knee: 36 },
        body: { x: 0, y: 2, rot: 1 }, head: { tilt: 1, turn: -0.05 },
        armL: { hand: [154, 526], bend: 1, handPose: 'relaxed', handRot: 8 },
        armR: { hand: [432, 500], bend: -1, handPose: 'relaxed', handRot: -8 },
      }), ease: 'inOut' },
      { at: 750, pose: derivePose(POSES.neutral, {
        legL: { swing: -2, knee: 14 }, legR: { swing: 2, knee: 10 },
        body: { x: 0, y: -3, rot: -0.5 }, head: { tilt: 0, turn: -0.02 },
        armL: { hand: [138, 524], bend: 1, handPose: 'relaxed', handRot: 0 },
        armR: { hand: [462, 524], bend: -1, handPose: 'relaxed', handRot: 0 },
      }), ease: 'inOut' },
      { at: 1000, pose: derivePose(POSES.neutral, {
        legL: { swing: -14, knee: 36 }, legR: { swing: 4, knee: 7 },
        body: { x: 0, y: 2, rot: -1 }, head: { tilt: 1, turn: 0.05 },
        armL: { hand: [168, 500], bend: 1, handPose: 'relaxed', handRot: -8 },
        armR: { hand: [446, 526], bend: -1, handPose: 'relaxed', handRot: 8 },
      }), ease: 'inOut' },
    ], true),
  }

  const EMOTIONS = {
    neutral: { brow: 0, browTilt: 0, eye: 0, mouthCurve: 0, blush: 0.12 },
    joy: { brow: -3, browTilt: 0.04, eye: 0.10, mouthCurve: 0.28, blush: 0.22 },
    sad: { brow: -1, browTilt: -0.30, eye: -0.16, mouthCurve: -0.26, blush: 0.08 },
    anger: { brow: 4, browTilt: 0.35, eye: -0.20, mouthCurve: -0.20, blush: 0.18 },
    surprise: { brow: -8, browTilt: 0.10, eye: 0.28, mouthCurve: 0.06, blush: 0.10 },
    fear: { brow: -5, browTilt: -0.20, eye: 0.34, mouthCurve: -0.08, blush: 0.05 },
    think: { brow: -1, browTilt: 0.22, eye: -0.05, mouthCurve: 0.02, blush: 0.08 },
    disgust: { brow: 2, browTilt: -0.22, eye: -0.12, mouthCurve: -0.34, blush: 0.05 },
  }

  // ── text -> phonemes (approximate, deterministic) ───────────────────────
  const RU_GRAPHEMES = {
    а: ['a'], б: ['b'], в: ['v'], г: ['g'], д: ['d'], е: ['je'], ё: ['jo'],
    ж: ['ʐ'], з: ['z'], и: ['i'], й: ['j'], к: ['k'], л: ['l'], м: ['m'],
    н: ['n'], о: ['o'], п: ['p'], р: ['r'], с: ['s'], т: ['t'], у: ['u'],
    ф: ['f'], х: ['x'], ц: ['ts'], ч: ['tɕ'], ш: ['ʂ'], щ: ['ɕː'],
    ъ: [], ы: ['ɨ'], ь: ['ʲ'], э: ['ɛ'], ю: ['ju'], я: ['ja'],
  }
  const RU_DIGRAPHS = { дж: ['d', 'ʐ'], дз: ['d', 'z'], тс: ['ts'] }
  const EN_DIGRAPHS = {
    sh: ['SH'], ch: ['CH'], th: ['TH'], ph: ['F'], wh: ['W'], ng: ['NG'],
    oo: ['UW'], ee: ['IY'], ea: ['IY'], ai: ['EY'], ay: ['EY'], oa: ['OW'],
    oi: ['OY'], oy: ['OY'], ou: ['AW'], ow: ['OW'], ar: ['AA', 'R'],
    er: ['ER'], ir: ['ER'], or: ['AO', 'R'], ur: ['ER'], qu: ['K', 'W'],
  }
  const EN_LETTERS = {
    a: ['AE'], b: ['B'], c: ['K'], d: ['D'], e: ['EH'], f: ['F'], g: ['G'],
    h: ['HH'], i: ['IH'], j: ['JH'], k: ['K'], l: ['L'], m: ['M'], n: ['N'],
    o: ['AA'], p: ['P'], q: ['K'], r: ['R'], s: ['S'], t: ['T'], u: ['AH'],
    v: ['V'], w: ['W'], x: ['K', 'S'], y: ['Y'], z: ['Z'],
  }
  const RU_CONSONANTS = new Set(['b', 'bʲ', 'p', 'pʲ', 'v', 'vʲ', 'f', 'fʲ', 'g', 'gʲ', 'k', 'kʲ', 'd', 'dʲ', 't', 'tʲ', 'z', 'zʲ', 's', 'sʲ', 'ʐ', 'ʂ', 'ɕː', 'ts', 'tɕ', 'm', 'mʲ', 'n', 'nʲ', 'l', 'lʲ', 'r', 'rʲ', 'x', 'xʲ'])

  function phonemize(text) {
    const s = String(text || '').toLowerCase().replace(/[«»"“”.,!?;:()\[\]{}]/g, ' ')
    const cyr = /[а-яё]/.test(s)
    const out = []
    if (cyr) {
      for (let i = 0; i < s.length; i++) {
        const ch = s[i]
        if (/\s/.test(ch) || ch === '—' || ch === '-') {
          if (out.length && out[out.length - 1] !== 'sil') out.push('sil')
          continue
        }
        const pair = s.slice(i, i + 2)
        if (RU_DIGRAPHS[pair]) {
          out.push(...RU_DIGRAPHS[pair]); i++; continue
        }
        const ids = RU_GRAPHEMES[ch]
        if (!ids) continue
        if (ch === 'ь') {
          const prev = out[out.length - 1]
          if (prev && RU_CONSONANTS.has(prev) && !prev.endsWith('ʲ')) {
            out[out.length - 1] = prev + 'ʲ'
          }
          continue
        }
        if (ch === 'ъ') continue
        out.push(...ids.filter((id) => PHONEMES[id]))
      }
    } else {
      for (let i = 0; i < s.length; i++) {
        const ch = s[i]
        if (/\s/.test(ch) || ch === '—' || ch === '-') {
          if (out.length && out[out.length - 1] !== 'sil') out.push('sil')
          continue
        }
        const pair = s.slice(i, i + 2)
        if (EN_DIGRAPHS[pair]) {
          out.push(...EN_DIGRAPHS[pair]); i++; continue
        }
        const ids = EN_LETTERS[ch]
        if (ids) out.push(...ids)
      }
    }
    while (out.length && out[out.length - 1] === 'sil') out.pop()
    return out.length ? out : ['sil']
  }

  function visemeOf(id) {
    const p = PHONEMES[id]
    return p ? p.viseme : 'sil'
  }

  function visemesFromText(text, duration, start) {
    const phs = phonemize(text)
    const total = Math.max(1, Number(duration) || 2400)
    const t0 = Number(start) || 0
    const weights = phs.map((id) => (id === 'sil' ? 0.55 : PHONEMES[id] && PHONEMES[id].kind === 'vowel' ? 1.15 : 0.92))
    const sum = weights.reduce((a, b) => a + b, 0) || 1
    let acc = 0
    return phs.map((id, i) => {
      const at = t0 + (acc / sum) * total
      acc += weights[i]
      return { t: Math.round(at), phoneme: id, viseme: visemeOf(id), dur: Math.round((weights[i] / sum) * total) }
    })
  }

  // ── math / drawing helpers ───────────────────────────────────────────────
  const clamp = (x, a, b) => (x < a ? a : x > b ? b : x)
  const inRange = (x, r) => x >= r[0] && x <= r[1]
  const lerp = (a, b, t) => a + (b - a) * t
  const smooth = (x) => { const t = clamp(x, 0, 1); return t * t * (3 - 2 * t) }
  const round = (n) => Math.round(n * 1000) / 1000

  function rr(ctx, x, y, w, h, r) {
    const q = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2)
    ctx.beginPath()
    ctx.moveTo(x + q, y)
    ctx.arcTo(x + w, y, x + w, y + h, q)
    ctx.arcTo(x + w, y + h, x, y + h, q)
    ctx.arcTo(x, y + h, x, y, q)
    ctx.arcTo(x, y, x + w, y, q)
    ctx.closePath()
  }

  function poly(ctx, pts, close) {
    ctx.beginPath()
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i]
      if (i === 0) ctx.moveTo(p[0], p[1])
      else ctx.lineTo(p[0], p[1])
    }
    if (close !== false) ctx.closePath()
  }

  function fillStroke(ctx, fill, stroke, width) {
    if (fill) { ctx.fillStyle = fill; ctx.fill() }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width || 3; ctx.stroke() }
  }

  function rotPoint(x, y, cx, cy, a) {
    const s = Math.sin(a), c = Math.cos(a)
    const dx = x - cx, dy = y - cy
    return [cx + dx * c - dy * s, cy + dx * s + dy * c]
  }

  function mix(a, b, k) {
    if (typeof a === 'number' && typeof b === 'number') return lerp(a, b, k)
    if (Array.isArray(a) && Array.isArray(b)) return a.map((v, i) => mix(v, b[i], k))
    if (a && b && typeof a === 'object' && typeof b === 'object') {
      const o = {}
      for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) o[key] = mix(a[key], b[key], k)
      return o
    }
    return k < 0.5 ? a : b
  }

  function blendPose(a, b, k) {
    if (k <= 0) return a
    if (k >= 1) return b
    const o = mix(a, b, k)
    o.name = b.name || a.name
    return o
  }

  function easeOut(x) { return 1 - Math.pow(1 - clamp(x, 0, 1), 3) }
  function easeInOut(x) { const t = clamp(x, 0, 1); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2 }

  // easing names used by clip keyframes (the key's ease applies to the segment
  // that ends on that key)
  const EASES = {
    linear: (x) => clamp(x, 0, 1),
    in: (x) => Math.pow(clamp(x, 0, 1), 3),
    out: easeOut,
    inOut: easeInOut,
    backIn: (x) => { const t = clamp(x, 0, 1); return 2.70158 * t * t * t - 1.70158 * t * t },
    backOut: (x) => { const t = clamp(x, 0, 1) - 1; return 1 + 2.70158 * t * t * t + 1.70158 * t * t },
    expoOut: (x) => { const t = clamp(x, 0, 1); return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t) },
  }

  // ── pose solving ─────────────────────────────────────────────────────────
  function solveArm(shoulder, target, upper, lower, bendSign) {
    let dx = target[0] - shoulder[0]
    let dy = target[1] - shoulder[1]
    let d = Math.hypot(dx, dy) || 0.0001
    const max = (upper + lower) * LIMITS.arm.reachMax
    const min = Math.max(Math.abs(upper - lower) + 4, LIMITS.arm.reachMin)
    if (d > max) { dx *= max / d; dy *= max / d; d = max }
    if (d < min) { const f = min / d; dx *= f; dy *= f; d = min }
    const ux = dx / d, uy = dy / d
    const a = (upper * upper - lower * lower + d * d) / (2 * d)
    const h = Math.sqrt(Math.max(0, upper * upper - a * a))
    const px = shoulder[0] + ux * a
    const py = shoulder[1] + uy * a
    // Both circle intersections are valid IK solutions. Humans bend the elbow
    // down/outward; the old explicit `bend` sign often picked the "elbow above
    // the hand" variant and the arm read as broken. Prefer the lower elbow,
    // and for a perfectly horizontal arm the one farther from the body.
    const e1 = [px - uy * h, py + ux * h]
    const e2 = [px + uy * h, py - ux * h]
    // Below the shoulder the elbow must stay outside the torso, otherwise the
    // forearms cross over the chest. Above the shoulder the lower elbow reads
    // naturally. Ties go outward.
    const outward = (e) => Math.abs(e[0] - 300)
    const below = target[1] > shoulder[1] + 6
    const pick = below
      ? (outward(e1) >= outward(e2) ? e1 : e2)
      : (e1[1] > e2[1] + 2 ? e1 : e2[1] > e1[1] + 2 ? e2 : (outward(e1) >= outward(e2) ? e1 : e2))
    void bendSign
    return { elbow: pick, wrist: [shoulder[0] + dx, shoulder[1] + dy] }
  }

  function solveLeg(hip, swingDeg, kneeDeg, upper, lower) {
    const u = upper || RIG.upperLeg
    const l = lower || RIG.lowerLeg
    const a = (90 + swingDeg) * DEG
    const kx = hip[0] + Math.cos(a) * u
    const ky = hip[1] + Math.sin(a) * u
    const b = a + kneeDeg * DEG
    const ax = kx + Math.cos(b) * l
    const ay = ky + Math.sin(b) * l
    return { knee: [kx, ky], ankle: [ax, ay], angle: b }
  }

  function makeSkeleton(p, yawIn, skin) {
    const yaw = clamp(Number(yawIn) || 0, -1, 1)
    const sc = skin || {}
    const fS = sc.shoulderW || 1
    const fH = sc.hipW || 1
    const fA = sc.armLen || 1
    const fL = sc.legLen || 1
    const legDelta = (fL - 1) * (RIG.upperLeg + RIG.lowerLeg)
    const bodyRot = clamp(p.body.rot || 0, LIMITS.body.rot[0], LIMITS.body.rot[1]) * DEG
    const bodyX = clamp(p.body.x || 0, LIMITS.body.x[0], LIMITS.body.x[1])
    const bodyY = clamp(p.body.y || 0, LIMITS.body.y[0], LIMITS.body.y[1])
    const hip = [RIG.hip[0] + bodyX, RIG.hip[1] + bodyY - legDelta]
    const transform = (pt) => rotPoint(pt[0] + bodyX, pt[1] + bodyY - legDelta, hip[0], hip[1], bodyRot)

    // 2.5D: the far shoulder slides toward the centre; the torso covers its root
    const inward = Math.abs(yaw) * 6
    const drop = Math.abs(yaw) * 3
    const narrowY = profileNarrow(yaw, sc.profileHead)
    const baseShL = [300 + (RIG.shoulderL[0] - 300) * fS * narrowY, RIG.shoulderL[1]]
    const baseShR = [300 + (RIG.shoulderR[0] - 300) * fS * narrowY, RIG.shoulderR[1]]
    const shLp = yaw > 0 ? [baseShL[0] + inward, baseShL[1] - drop] : baseShL
    const shRp = yaw < 0 ? [baseShR[0] - inward, baseShR[1] - drop] : baseShR
    let shL = transform(shLp)
    let shR = transform(shRp)
    // longer legs lift the hip; keep the hands relative to the torso
    const hand = (h) => transform([h[0], h[1] - legDelta])
    const armL = solveArm(shL, hand(p.armL.hand), RIG.upperArm * fA, RIG.lowerArm * fA, p.armL.bend || 1)
    const armR = solveArm(shR, hand(p.armR.hand), RIG.upperArm * fA, RIG.lowerArm * fA, p.armR.bend || -1)
    const hipL = transform([300 + (RIG.hipL[0] - 300) * fH * narrowY, RIG.hipL[1]])
    const hipR = transform([300 + (RIG.hipR[0] - 300) * fH * narrowY, RIG.hipR[1]])
    const swingL = clamp(p.legL.swing || 0, LIMITS.leg.swing[0], LIMITS.leg.swing[1])
    const swingR = clamp(p.legR.swing || 0, LIMITS.leg.swing[0], LIMITS.leg.swing[1])
    const kneeL = clamp(p.legL.knee || 0, LIMITS.leg.knee[0], LIMITS.leg.knee[1])
    const kneeR = clamp(p.legR.knee || 0, LIMITS.leg.knee[0], LIMITS.leg.knee[1])
    const legL = solveLeg(hipL, swingL, kneeL, RIG.upperLeg * fL, RIG.lowerLeg * fL)
    const legR = solveLeg(hipR, -swingR, kneeR, RIG.upperLeg * fL, RIG.lowerLeg * fL)

    // the body is drawn in a transformed frame, but the joints above are final.
    const nod = clamp(p.head.nod || 0, LIMITS.head.nod[0], LIMITS.head.nod[1])
    // keep the chin near the collar when the head is scaled
    const hsK = (sc.headScale || 1)
    const headBase = [RIG.head[0], RIG.head[1] + 107 * (1 - hsK)]
    let head = transform([headBase[0], headBase[1] + nod])
    let neck = transform(RIG.neck)

    // free-bone FK on top of the IK base pose
    const fk = p.fk || {}
    const fd = (v, key) => clamp(Number(v) || 0, LIMITS.fk[key][0], LIMITS.fk[key][1]) * DEG
    const rotA = (pt, ctr, a) => (a ? rotPoint(pt[0], pt[1], ctr[0], ctr[1], a) : pt)
    const spineA = fd(fk.spine, 'spine')
    const neckA = fd(fk.neck, 'neck')
    const headA = fd(fk.head, 'head')
    const waistP = transform([300, 527])
    if (spineA) {
      neck = rotA(neck, waistP, spineA)
      head = rotA(head, waistP, spineA)
      shL = rotA(shL, waistP, spineA); shR = rotA(shR, waistP, spineA)
      armL.elbow = rotA(armL.elbow, waistP, spineA); armL.wrist = rotA(armL.wrist, waistP, spineA)
      armR.elbow = rotA(armR.elbow, waistP, spineA); armR.wrist = rotA(armR.wrist, waistP, spineA)
    }
    if (neckA) head = rotA(head, neck, neckA)
    const shAL = fd(fk.shL, 'sh'); const shAR = fd(fk.shR, 'sh')
    if (shAL) { armL.elbow = rotA(armL.elbow, shL, shAL); armL.wrist = rotA(armL.wrist, shL, shAL) }
    if (shAR) { armR.elbow = rotA(armR.elbow, shR, shAR); armR.wrist = rotA(armR.wrist, shR, shAR) }
    const elL = fd(fk.elbowL, 'elbow'); const elR = fd(fk.elbowR, 'elbow')
    if (elL) armL.wrist = rotA(armL.wrist, armL.elbow, elL)
    if (elR) armR.wrist = rotA(armR.wrist, armR.elbow, elR)
    const hipLfk = fd(fk.hipL, 'hip'); const hipRfk = fd(fk.hipR, 'hip')
    if (hipLfk) { legL.knee = rotA(legL.knee, hipL, hipLfk); legL.ankle = rotA(legL.ankle, hipL, hipLfk) }
    if (hipRfk) { legR.knee = rotA(legR.knee, hipR, hipRfk); legR.ankle = rotA(legR.ankle, hipR, hipRfk) }
    const knL = fd(fk.kneeL, 'knee'); const knR = fd(fk.kneeR, 'knee')
    if (knL) legL.ankle = rotA(legL.ankle, legL.knee, knL)
    if (knR) legR.ankle = rotA(legR.ankle, legR.knee, knR)
    legL.angle = Math.atan2(legL.ankle[1] - legL.knee[1], legL.ankle[0] - legL.knee[0])
    legR.angle = Math.atan2(legR.ankle[1] - legR.knee[1], legR.ankle[0] - legR.knee[0])
    const fkOut = {
      spine: spineA / DEG, neck: neckA / DEG, head: headA / DEG,
      shL: shAL / DEG, shR: shAR / DEG,
      elbowL: elL / DEG, elbowR: elR / DEG,
      wristL: clamp(Number(fk.wristL) || 0, LIMITS.fk.wrist[0], LIMITS.fk.wrist[1]),
      wristR: clamp(Number(fk.wristR) || 0, LIMITS.fk.wrist[0], LIMITS.fk.wrist[1]),
      hipL: hipLfk / DEG, hipR: hipRfk / DEG,
      kneeL: knL / DEG, kneeR: knR / DEG,
      ankleL: clamp(Number(fk.ankleL) || 0, LIMITS.fk.ankle[0], LIMITS.fk.ankle[1]),
      ankleR: clamp(Number(fk.ankleR) || 0, LIMITS.fk.ankle[0], LIMITS.fk.ankle[1]),
    }

    return {
      hip, neck, head, shL, shR, yaw, profileHead: !!sc.profileHead,
      spineRot: bodyRot + spineA, headExtra: headA + neckA * 0.5,
      fk: fkOut,
      elbowL: armL.elbow, wristL: armL.wrist,
      elbowR: armR.elbow, wristR: armR.wrist,
      hipL, kneeL: legL.knee, ankleL: legL.ankle, legAngleL: legL.angle,
      hipR, kneeR: legR.knee, ankleR: legR.ankle, legAngleR: legR.angle,
      bodyRot, hipBase: hip, profile: Math.abs(yaw) >= 0.97, headTilt: (p.head.tilt || 0) * DEG,
      // how far each leg is lifted in front of the body: the skirt hem and the
      // draw order react to it (adaptive clothing)
      // a foot off the floor means the leg is in front of the skirt: the hem
      // follows the same 0..1 value (a walking step stays near zero)
      liftL: clamp((RIG.floor - legL.ankle[1]) / 260, 0, 1),
      liftR: clamp((RIG.floor - legR.ankle[1]) / 260, 0, 1),
    }
  }

  // ── drawing: limbs and body ──────────────────────────────────────────────
  // The contact shadow is baked once: a soft radial ellipse, no ctx.filter.
  let SHADOW_SPRITE = null
  function shadowSprite() {
    if (SHADOW_SPRITE) return SHADOW_SPRITE
    const c = document.createElement('canvas')
    c.width = 312
    c.height = 60
    const g = c.getContext('2d')
    g.save()
    g.translate(156, 30)
    g.scale(1, 0.19)
    const grd = g.createRadialGradient(0, 0, 0, 0, 0, 150)
    grd.addColorStop(0, 'rgba(16,18,27,1)')
    grd.addColorStop(0.62, 'rgba(16,18,27,0.92)')
    grd.addColorStop(1, 'rgba(16,18,27,0)')
    g.fillStyle = grd
    g.beginPath()
    g.arc(0, 0, 150, 0, TAU)
    g.fill()
    g.restore()
    SHADOW_SPRITE = c
    return c
  }

  // A rounded capsule from a to b. The caps are cubic beziers (the same
  // 0.5523 magic number as the limb tube): canvas arcs plus a closing chord
  // used to cut the shape open, so the neck showed the page through the gap.
  function tapered(ctx, a, b, r1, r2, fill, outline, hi) {
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0])
    const ca = Math.cos(ang), sa = Math.sin(ang)
    const nx = -sa, ny = ca
    const k = 0.5523
    const a1 = [a[0] + nx * r1, a[1] + ny * r1]
    const a2 = [a[0] - nx * r1, a[1] - ny * r1]
    const b1 = [b[0] + nx * r2, b[1] + ny * r2]
    const b2 = [b[0] - nx * r2, b[1] - ny * r2]
    ctx.beginPath()
    ctx.moveTo(a1[0], a1[1])
    ctx.lineTo(b1[0], b1[1])
    ctx.bezierCurveTo(
      b1[0] + ca * r2 * k, b1[1] + sa * r2 * k,
      b2[0] + ca * r2 * k, b2[1] + sa * r2 * k,
      b2[0], b2[1])
    ctx.lineTo(a2[0], a2[1])
    ctx.bezierCurveTo(
      a2[0] - ca * r1 * k, a2[1] - sa * r1 * k,
      a1[0] - ca * r1 * k, a1[1] - sa * r1 * k,
      a1[0], a1[1])
    ctx.closePath()
    fillStroke(ctx, fill, outline, 3)
    if (hi) {
      ctx.beginPath()
      ctx.moveTo(a[0] + nx * r1 * 0.42, a[1] + ny * r1 * 0.42)
      ctx.lineTo(b[0] + nx * r2 * 0.42, b[1] + ny * r2 * 0.42)
      ctx.strokeStyle = hi
      ctx.lineWidth = Math.max(2, Math.min(r1, r2) * 0.40)
      ctx.lineCap = 'round'
      ctx.globalAlpha = 0.45
      ctx.stroke()
      ctx.globalAlpha = 1
    }
  }

  // A paper-cut shoe: heel counter, vamp, rounded toe box and a raised sole.
  // Local space has the ankle at the origin and the toe towards +x.
  function drawShoe(ctx, ankle, angle, c) {
    ctx.save()
    ctx.translate(ankle[0], ankle[1])
    ctx.rotate(angle - Math.PI / 2)
    // outsole slab with a toe spring
    ctx.beginPath()
    ctx.moveTo(-30, 12)
    ctx.quadraticCurveTo(-34, 28, -18, 29)
    ctx.lineTo(28, 29)
    ctx.quadraticCurveTo(44, 29, 47, 14)
    ctx.lineTo(47, 8)
    ctx.quadraticCurveTo(41, 19, 28, 19)
    ctx.lineTo(-16, 18)
    ctx.quadraticCurveTo(-26, 18, -30, 12)
    ctx.closePath()
    fillStroke(ctx, c.sole, INK, 2.4)
    // upper: heel counter -> vamp -> toe box
    ctx.beginPath()
    ctx.moveTo(-14, -26)
    ctx.quadraticCurveTo(-24, -20, -26, -6)
    ctx.quadraticCurveTo(-28, 6, -24, 15)
    ctx.quadraticCurveTo(-12, 19, 2, 19)
    ctx.lineTo(27, 19)
    ctx.quadraticCurveTo(39, 19, 43, 12)
    ctx.quadraticCurveTo(45, 3, 35, -5)
    ctx.quadraticCurveTo(25, -14, 13, -23)
    ctx.quadraticCurveTo(4, -28, -14, -26)
    ctx.closePath()
    fillStroke(ctx, c.shoes, INK, 3)
    // toe cap seam
    ctx.beginPath()
    ctx.moveTo(34, -6)
    ctx.quadraticCurveTo(30, 8, 31, 18)
    ctx.strokeStyle = 'rgba(0,0,0,.18)'
    ctx.lineWidth = 2.2
    ctx.stroke()
    // heel counter
    ctx.beginPath()
    ctx.moveTo(-24, 14)
    ctx.quadraticCurveTo(-27, 2, -25, -6)
    ctx.strokeStyle = 'rgba(0,0,0,.20)'
    ctx.lineWidth = 2.4
    ctx.stroke()
    // laces on the vamp
    for (let i = 0; i < 3; i++) {
      const x = 4 + i * 7
      ctx.beginPath()
      ctx.moveTo(x, -17 + i * 3)
      ctx.lineTo(x + 6, -11 + i * 3)
      ctx.strokeStyle = 'rgba(255,255,255,.34)'
      ctx.lineWidth = 2.6
      ctx.lineCap = 'round'
      ctx.stroke()
    }
    // soft highlight along the instep
    ctx.beginPath()
    ctx.moveTo(-8, -18)
    ctx.quadraticCurveTo(8, -20, 24, -8)
    ctx.strokeStyle = 'rgba(255,255,255,.16)'
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.restore()
  }


  function unit(a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1]
    const l = Math.hypot(dx, dy) || 1
    return [dx / l, dy / l]
  }

  // One continuous paper-cut limb through a polyline: a smooth tube with
  // rounded caps, instead of "cone + joint disc + cone".
  function limb(ctx, pts, radii, fill, outline, lw) {
    const slices = 14
    const samples = []
    for (let s = 0; s < pts.length - 1; s++) {
      const a = pts[s], b = pts[s + 1]
      const ra = radii[s], rb = radii[s + 1]
      for (let i = 0; i < slices; i++) {
        const t = i / slices
        samples.push({
          x: a[0] + (b[0] - a[0]) * t,
          y: a[1] + (b[1] - a[1]) * t,
          r: ra + (rb - ra) * t,
        })
      }
    }
    const last = pts.length - 1
    samples.push({ x: pts[last][0], y: pts[last][1], r: radii[last] })

    const left = [], right = []
    for (let i = 0; i < samples.length; i++) {
      const a = samples[Math.max(0, i - 1)]
      const b = samples[Math.min(samples.length - 1, i + 1)]
      let dx = b.x - a.x, dy = b.y - a.y
      const l = Math.hypot(dx, dy) || 1
      dx /= l; dy /= l
      const nx = -dy, ny = dx
      const s = samples[i]
      left.push([s.x + nx * s.r, s.y + ny * s.r])
      right.push([s.x - nx * s.r, s.y - ny * s.r])
    }
    const d0 = unit([samples[0].x, samples[0].y], [samples[1].x, samples[1].y])
    const dn = unit([samples[samples.length - 2].x, samples[samples.length - 2].y], [samples[samples.length - 1].x, samples[samples.length - 1].y])
    const p0 = samples[0], pn = samples[samples.length - 1]
    const k = 0.5523
    const lEnd = left[left.length - 1], rEnd = right[right.length - 1]
    const lStart = left[0], rStart = right[0]

    ctx.beginPath()
    ctx.moveTo(lStart[0], lStart[1])
    for (let i = 1; i < left.length; i++) ctx.lineTo(left[i][0], left[i][1])
    // rounded cap at the far end
    ctx.bezierCurveTo(
      lEnd[0] + dn[0] * pn.r * k, lEnd[1] + dn[1] * pn.r * k,
      rEnd[0] + dn[0] * pn.r * k, rEnd[1] + dn[1] * pn.r * k,
      rEnd[0], rEnd[1])
    for (let i = right.length - 2; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1])
    // rounded cap at the start
    ctx.bezierCurveTo(
      rStart[0] - d0[0] * p0.r * k, rStart[1] - d0[1] * p0.r * k,
      lStart[0] - d0[0] * p0.r * k, lStart[1] - d0[1] * p0.r * k,
      lStart[0], lStart[1])
    ctx.closePath()
    fillStroke(ctx, fill, outline, lw || 3)
    return { samples, left, right }
  }

  function drawLeg(ctx, sk, side, c, front) {
    const farLeg = sk.profile && ((sk.yaw > 0 && side === 'L') || (sk.yaw < 0 && side === 'R'))
    if (farLeg) {
      ctx.save()
      ctx.translate(sk.yaw > 0 ? -8 : 8, 0)
    }
    const hip = side === 'L' ? sk.hipL : sk.hipR
    const knee = side === 'L' ? sk.kneeL : sk.kneeR
    const ankle = side === 'L' ? sk.ankleL : sk.ankleR
    const ankleFk = (sk.fk && sk.fk[side === 'L' ? 'ankleL' : 'ankleR']) || 0
    const angle = (side === 'L' ? sk.legAngleL : sk.legAngleR) + ankleFk * DEG
    const dark = farLeg ? c.pantsDark : (side === 'R' ? c.pantsDark : c.pants)
    const bare = c.bottom === 'shorts' || c.bottom === 'skirt' || c.outfit === 'dress'
    const calf = [
      knee[0] + (ankle[0] - knee[0]) * 0.46,
      knee[1] + (ankle[1] - knee[1]) * 0.46,
    ]
    // a raised knee pulls the garment up with it: the hip cap and the shorts
    // hem follow the thigh instead of staying at the pelvis
    const thighA = Math.atan2(knee[1] - hip[1], knee[0] - hip[0])
    if (!bare) {
      ctx.beginPath()
      ctx.arc(hip[0], hip[1], 34, 0, TAU)
      fillStroke(ctx, dark, INK, 3)
    }
    limb(ctx, [hip, knee, calf, ankle], [33, 27, 24, 17], bare ? c.skin : dark, INK, 3)
    if (bare && c.bottom === 'shorts') {
      const cut = 0.46
      const hem = [hip[0] + (knee[0] - hip[0]) * cut, hip[1] + (knee[1] - hip[1]) * cut]
      limb(ctx, [hip, hem], [33, 28], dark, INK, 3)
      // the hem is a band across the thigh, not a horizontal line
      const nx = -Math.sin(thighA), ny = Math.cos(thighA)
      ctx.beginPath()
      ctx.moveTo(hem[0] + nx * 26, hem[1] + ny * 26)
      ctx.lineTo(hem[0] - nx * 26, hem[1] - ny * 26)
      ctx.strokeStyle = 'rgba(0,0,0,.28)'
      ctx.lineWidth = 2.4
      ctx.stroke()
    }
    if (!bare) {
      // re-draw the hip cap over the tube seam so a lifted thigh never shows
      // the skin body through the joint
      ctx.beginPath()
      ctx.arc(hip[0], hip[1], 32, 0, TAU)
      ctx.fillStyle = dark
      ctx.fill()
      ctx.beginPath()
      ctx.arc(knee[0], knee[1], 24, 0, TAU)
      ctx.fillStyle = dark
      ctx.fill()
    }
    // side seam only on trousers
    if (!bare) {
      ctx.beginPath()
      ctx.moveTo(hip[0] - 9, hip[1] + 20)
      ctx.quadraticCurveTo(knee[0] - 7, knee[1] - 10, (knee[0] + ankle[0]) / 2 - 7, (knee[1] + ankle[1]) / 2)
      ctx.strokeStyle = 'rgba(0,0,0,.16)'
      ctx.lineWidth = 2.4
      ctx.stroke()
    }
    drawShoe(ctx, ankle, angle + (side === 'L' ? -0.16 : 0.16) + (sk.profile ? (sk.yaw < 0 ? Math.PI : 0) : 0), c)
    if (front) {
      ctx.beginPath()
      ctx.ellipse(hip[0] + 6, hip[1] + 4, 25, 19, sk.bodyRot, 0, TAU)
      ctx.fillStyle = 'rgba(255,255,255,.07)'
      ctx.fill()
    }
    if (farLeg) ctx.restore()
  }

  function cuffs(ctx, p, angle, c) {
    ctx.save()
    ctx.translate(p[0], p[1])
    // a band across the arm, not a patch along it
    ctx.rotate(angle - Math.PI / 2)
    rr(ctx, -17, -7, 34, 14, 6)
    fillStroke(ctx, c.shirtDark, INK, 2.5)
    ctx.restore()
  }

  function wristCuff(ctx, p, angle, c) {
    ctx.save()
    ctx.translate(p[0], p[1])
    ctx.rotate(angle - Math.PI / 2)
    rr(ctx, -12, -6, 24, 12, 5)
    fillStroke(ctx, c.accent, INK, 2.2)
    ctx.restore()
  }

  function drawArm(ctx, sk, side, p, c, far) {
    if (far) { ctx.save(); ctx.globalAlpha *= 0.88 }
    const sh = side === 'L' ? sk.shL : sk.shR
    const el = side === 'L' ? sk.elbowL : sk.elbowR
    const wr = side === 'L' ? sk.wristL : sk.wristR
    const upper = side === 'L' ? p.armL : p.armR
    // near limbs keep the normal skin tone; only the far side darkens
    const skin = far ? c.skinDark : c.skin
    const outfit = c.outfit || 'shirt'
    const sleeveless = outfit === 'vest'
    const covered = c.sleeves === 'short' ? false
      : c.sleeves === 'long' ? true
        : (outfit === 'tee' || sleeveless ? false : true)
    const wristFk = (p.fk && p.fk[side === 'L' ? 'wristL' : 'wristR']) || 0
    const pronation = clamp(Number(upper.handRot) || 0, ANATOMY.forearm.pronation[0], ANATOMY.forearm.pronation[1])
    const angle = Math.atan2(wr[1] - el[1], wr[0] - el[0]) + wristFk * DEG
    const sleeveFill = far ? c.shirtDark : ((outfit === 'coat' || outfit === 'jacket') ? (c.coatColor || c.shirtDark) : c.shirt)

    if (covered) {
      limb(ctx, [sh, el, wr], [18, 15.5, 11.5], sleeveFill, INK, 3.2)
      // rounded deltoid painted over the tube seam (the side view already
      // pins the arm to the torso edge, so it would read as a pillow there)
      if (!sk.profileArm) {
        ctx.beginPath()
        ctx.ellipse(sh[0] - 2, sh[1] + 8, 24, 18, 0, 0, TAU)
        ctx.fillStyle = sleeveFill
        ctx.fill()
      }
      // a folded elbow pinches the tube: a disc of cloth keeps the sleeve
      // continuous instead of showing a notch at the joint
      ctx.beginPath()
      ctx.arc(el[0], el[1], 15.5, 0, TAU)
      ctx.fillStyle = sleeveFill
      ctx.fill()
      // soft crease on the inside of the elbow
      const a1 = Math.atan2(el[1] - sh[1], el[0] - sh[0])
      ctx.beginPath()
      ctx.arc(el[0], el[1], 13.5, a1 - 1.55, a1 - 0.35)
      ctx.strokeStyle = 'rgba(0,0,0,.18)'
      ctx.lineWidth = 2.4
      ctx.stroke()
    } else {
      limb(ctx, [sh, el, wr], [16.5, 14.5, 11.5], skin, INK, 3)
      if (!sleeveless) {
        // short sleeve over the upper arm, with a rounded elbow cap
        const t = 0.62
        const end = [sh[0] + (el[0] - sh[0]) * t, sh[1] + (el[1] - sh[1]) * t]
        const aUp = Math.atan2(el[1] - sh[1], el[0] - sh[0])
        limb(ctx, [sh, end], [20, 18], sleeveFill, INK, 3)
        cuffs(ctx, end, aUp, c)
        if (!sk.profileArm) {
          ctx.beginPath()
          ctx.ellipse(sh[0] - 2, sh[1] + 8, 23, 17, 0, 0, TAU)
          ctx.fillStyle = sleeveFill
          ctx.fill()
        }
      } else {
        // armhole trim for the vest: no sleeve, just the garment edge
        ctx.beginPath()
        ctx.arc(sh[0], sh[1] + 2, 20, Math.PI * 0.15, Math.PI * 0.85, true)
        ctx.strokeStyle = c.shirtDark
        ctx.lineWidth = 4
        ctx.stroke()
      }
      ctx.beginPath()
      ctx.arc(el[0], el[1], 13, 0, TAU)
      ctx.fillStyle = skin
      ctx.fill()
    }
    wristCuff(ctx, wr, angle, c)
    drawHand(ctx, wr, angle, upper.handPose || 'relaxed', pronation * DEG, side, c, far)
    if (far) ctx.restore()
  }

  function drawHand(ctx, wrist, angle, kind, extraRot, side, c, far) {
    const skinFill = far ? c.skinDark : c.skin
    ctx.save()
    ctx.translate(wrist[0], wrist[1])
    ctx.rotate(angle - Math.PI / 2 + extraRot)
    ctx.scale(1.22, 1.22)
    const flip = side === 'L' ? -1 : 1
    ctx.lineJoin = 'round'
    ctx.lineCap = 'round'

    function digit(x, y, w, h, rot) {
      ctx.save()
      ctx.translate(x, y)
      ctx.rotate(rot || 0)
      rr(ctx, -w / 2, 0, w, h, w / 2)
      fillStroke(ctx, skinFill, INK, 2.1)
      ctx.restore()
    }

    const HAND_CURLS = {
      relaxed: [0.14, 0.2, 0.26, 0.32],
      open: [0.03, 0.03, 0.03, 0.03],
      palm: [0.03, 0.03, 0.03, 0.03],
      point: [0.02, 1, 1, 1],
      one: [0.02, 1, 1, 1],
      peace: [0.02, 0.02, 1, 1],
      fist: [1, 1, 1, 1],
      thumb: [1, 1, 1, 1],
      ok: [0.10, 0.35, 1, 1],
      pinch: [0.10, 0.25, 0.85, 0.85],
    }
    const THUMB_CURL = {
      relaxed: 0.25, open: 0.05, palm: 0.05, point: 0.65, one: 0.65,
      peace: 0.65, fist: 0.90, thumb: 0.02, ok: 0.10, pinch: 0.10,
    }
    const curls = HAND_CURLS[kind] || HAND_CURLS.relaxed
    const thumbCurl = THUMB_CURL[kind] === undefined ? 0.35 : THUMB_CURL[kind]

    // palm
    ctx.beginPath()
    ctx.moveTo(-14, 0)
    ctx.quadraticCurveTo(-19, 14, -13, 28)
    ctx.quadraticCurveTo(-6, 35, 4, 33)
    ctx.quadraticCurveTo(16, 28, 16, 11)
    ctx.quadraticCurveTo(15, 0, 8, -2)
    ctx.closePath()
    fillStroke(ctx, skinFill, INK, 2.7)
    ctx.beginPath()
    ctx.ellipse(-4, 12, 6, 10, -0.15, 0, TAU)
    ctx.fillStyle = 'rgba(255,255,255,.13)'
    ctx.fill()

    if (kind === 'heart') {
      ctx.restore()
      ctx.save()
      ctx.translate(wrist[0] + (side === 'L' ? 18 : -18), wrist[1] - 8)
      ctx.rotate((side === 'L' ? 0.18 : -0.18) + extraRot)
      ctx.beginPath()
      ctx.moveTo(0, 16)
      ctx.bezierCurveTo(-28, -2, -16, -23, 0, -10)
      ctx.bezierCurveTo(16, -23, 28, -2, 0, 16)
      ctx.closePath()
      fillStroke(ctx, c.accent, INK, 2.5)
      ctx.restore()
      return
    }

    // three phalanges per finger, curl 0..1 shortens them (paper foreshortening)
    const fan = [-0.34, -0.11, 0.11, 0.34]
    const lengths = [31, 37, 35, 28]
    const xs = [-12, -4, 4, 12]
    // A finger is a chain of three phalanges (MCP → PIP → DIP). Curl shortens
    // every phalanx and bends the chain toward the palm centre. The chain is
    // drawn as one smooth tube, then joint creases are added on top.
    function fingerChain(x, len, w, rot, curl, bendDir) {
      const ratios = [0.45, 0.33, 0.22]
      const bends = [FINGER_CURL.mcp * 0.22, FINGER_CURL.pip * 0.32, FINGER_CURL.dip * 0.34]
      const shrink = 1 - 0.34 * curl
      const pts = [[x, 26]]
      const rads = [w * 0.52]
      let px = x, py = 26, ang = rot
      for (let k = 0; k < 3; k++) {
        const L = len * ratios[k] * shrink
        px += Math.sin(ang) * L
        py += Math.cos(ang) * L
        pts.push([px, py])
        rads.push(w * (0.5 - k * 0.06))
        ang += bendDir * bends[k] * DEG * curl
      }
      limb(ctx, pts, rads, skinFill, INK, 1.9)
      for (let j = 1; j <= 2; j++) {
        const pnt = pts[j]
        ctx.beginPath()
        ctx.moveTo(pnt[0] - w * 0.32, pnt[1])
        ctx.lineTo(pnt[0] + w * 0.32, pnt[1])
        ctx.strokeStyle = 'rgba(90,48,38,.28)'
        ctx.lineWidth = 1.3
        ctx.stroke()
      }
      return py - 21
    }
    for (let i = 0; i < 4; i++) {
      const c1 = curls[i]
      const len = Math.max(7, lengths[i] * (1 - 0.3 * c1))
      const rot = fan[i] * (1 - 0.55 * c1)
      const bendDir = xs[i] < 0 ? 1 : -1
      fingerChain(xs[i], len, 6.4, rot, c1, bendDir)
    }
    if (kind === 'fist') {
      ctx.beginPath()
      ctx.moveTo(-12, 25)
      ctx.quadraticCurveTo(0, 34, 14, 25)
      ctx.strokeStyle = 'rgba(0,0,0,.24)'
      ctx.lineWidth = 2.5
      ctx.stroke()
    }

    // thumb: up for "thumb", curled against the palm otherwise
    if (kind === 'thumb') {
      ctx.save()
      ctx.translate(-10 * flip, 3)
      ctx.rotate(-0.18 * flip)
      digit(0, -20, 12, 30, 0)
      ctx.restore()
    } else if (kind === 'ok' || kind === 'pinch') {
      ctx.beginPath()
      ctx.arc(3, 18, 10, 0, TAU)
      ctx.strokeStyle = INK
      ctx.lineWidth = 6
      ctx.stroke()
      ctx.strokeStyle = skinFill
      ctx.lineWidth = 3
      ctx.stroke()
      ctx.save()
      ctx.translate(-10 * flip, 12)
      ctx.rotate(-0.75 * flip)
      digit(0, -6, 10, 18, 0)
      ctx.restore()
    } else {
      ctx.save()
      ctx.translate(-16 * flip, 3)
      ctx.rotate(-1.12 * flip)
      digit(0, 0, 8, 21 * (1 - 0.55 * thumbCurl), 0)
      ctx.restore()
    }
    ctx.restore()
  }

  function drawTorsoSide(ctx, sk, p, c) {
    ctx.save()
    ctx.translate(sk.hipBase[0], sk.hipBase[1])
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    const yaw = sk.yaw || 0
    const outfit = c.outfit || 'shirt'
    const spS = (sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot
    if (spS) { ctx.translate(300, 527); ctx.rotate(spS); ctx.translate(-300, -527) }
    if (yaw < 0) { ctx.translate(300, 0); ctx.scale(-1, 1); ctx.translate(-300, 0) }
    // chest → belly → back, one paper plate seen edge-on
    ctx.beginPath()
    ctx.moveTo(270, 310)
    ctx.quadraticCurveTo(248, 332, 246, 392)
    ctx.quadraticCurveTo(242, 470, 252, 545)
    ctx.lineTo(352, 545)
    ctx.quadraticCurveTo(360, 486, 356, 430)
    ctx.quadraticCurveTo(352, 364, 338, 320)
    ctx.quadraticCurveTo(310, 302, 270, 310)
    ctx.closePath()
    fillStroke(ctx, c.shirt, INK, 3.4)
    ctx.save()
    ctx.clip()
    ctx.beginPath()
    ctx.moveTo(300, 320)
    ctx.quadraticCurveTo(330, 420, 322, 548)
    ctx.lineTo(380, 548)
    ctx.quadraticCurveTo(370, 420, 346, 320)
    ctx.closePath()
    ctx.fillStyle = 'rgba(0,0,0,.13)'
    ctx.fill()
    ctx.restore()
    // belt (a dress carries its own waistline)
    if (outfit !== 'dress') {
      rr(ctx, 244, 522, 112, 26, 5)
      fillStroke(ctx, c.pantsDark, INK, 2.6)
      rr(ctx, 338, 524, 16, 18, 4)
      fillStroke(ctx, c.accent, INK, 2)
    }
    // front placket + buttons on the visible edge
    if (outfit === 'shirt' || outfit === 'coat' || outfit === 'jacket') {
      ctx.beginPath()
      ctx.moveTo(346, 356)
      ctx.quadraticCurveTo(352, 440, 344, 516)
      ctx.strokeStyle = 'rgba(0,0,0,.20)'
      ctx.lineWidth = 2.4
      ctx.stroke()
      for (let i = 0; i < 4; i++) {
        ctx.beginPath(); ctx.arc(347, 380 + i * 34, 3, 0, TAU)
        fillStroke(ctx, c.accent, INK, 1.4)
      }
    }
    // patch pocket sits on the near side
    if (outfit === 'shirt' || outfit === 'coat') {
      ctx.beginPath()
      ctx.moveTo(296, 412); ctx.lineTo(326, 412); ctx.lineTo(326, 440); ctx.lineTo(296, 440)
      ctx.strokeStyle = 'rgba(0,0,0,.22)'; ctx.lineWidth = 2; ctx.stroke()
    }
    // coat panel
    if (outfit === 'coat' || outfit === 'jacket') {
      ctx.beginPath()
      ctx.moveTo(338, 330)
      ctx.quadraticCurveTo(360, 420, 356, 545)
      ctx.lineTo(300, 545)
      ctx.quadraticCurveTo(330, 430, 322, 340)
      ctx.closePath()
      fillStroke(ctx, c.coatColor || c.shirtDark, INK, 3)
    }
    // dress silhouette
    if (outfit === 'dress') {
      ctx.beginPath()
      ctx.moveTo(258, 512)
      ctx.quadraticCurveTo(300, 506, 350, 512)
      ctx.lineTo(372, 650)
      ctx.quadraticCurveTo(304, 668, 246, 650)
      ctx.closePath()
      fillStroke(ctx, c.skirtColor || c.shirt, INK, 3)
    }
    // side collar
    const collarFill = (outfit === 'coat' || outfit === 'jacket') ? (c.coatColor || c.shirtDark) : c.shirtDark
    if (outfit === 'tee' || outfit === 'vest' || outfit === 'dress') {
      // a flat rib band: these garments have no stand-up collar
      ctx.beginPath()
      ctx.moveTo(268, 320)
      ctx.quadraticCurveTo(304, 348, 342, 322)
      ctx.lineTo(346, 338)
      ctx.quadraticCurveTo(304, 366, 264, 336)
      ctx.closePath()
      fillStroke(ctx, collarFill, INK, 2.6)
    } else {
      ctx.beginPath()
      ctx.moveTo(272, 308)
      ctx.quadraticCurveTo(306, 352, 340, 314)
      ctx.lineTo(346, 332)
      ctx.quadraticCurveTo(306, 372, 266, 330)
      ctx.closePath()
      fillStroke(ctx, collarFill, INK, 2.8)
    }
    // cloth shadow under the arm
    ctx.beginPath()
    ctx.ellipse(304, 360, 26, 12, 0.1, 0, TAU)
    ctx.fillStyle = 'rgba(0,0,0,.10)'
    ctx.fill()
    ctx.restore()
  }

  function drawSkirtBlock(ctx, sk, c, outfit, bottom, spA) {
    const fill = c.skirtColor || (outfit === 'dress' ? c.shirt : c.pants)
    // Cloth hangs: the waist turns with the body, but the hem lags behind
    // (35 % of the spine bend instead of 100 %). The inherited transform
    // already carries the full bend, so undo 65 % of it around the waist.
    ctx.save()
    if (spA) { ctx.translate(300, 527); ctx.rotate(-spA * 0.65); ctx.translate(-300, -527) }
    // The hem lifts and parts on the side of a raised leg: a knee above the
    // hip pulls the cloth up, so the skirt never cuts the thigh in half.
    const liftL = sk.liftL || 0
    const liftR = sk.liftR || 0
    const hemL = 660 - liftL * 104
    const hemR = 660 - liftR * 104
    const outL = 200 - liftL * 6
    const outR = 400 + liftR * 6
    const sag = 678 - Math.min(liftL, liftR) * 26
    const topL = [208, 494]
    const topC = [300, 486]
    const topR = [392, 494]
    ctx.beginPath()
    ctx.moveTo(topL[0], topL[1])
    ctx.quadraticCurveTo(topC[0], topC[1], topR[0], topR[1])
    ctx.lineTo(outR, hemR)
    ctx.quadraticCurveTo(300 + (liftR - liftL) * 34, sag, outL, hemL)
    ctx.closePath()
    ctx.fillStyle = fill
    ctx.fill()
    // outline the silhouette only: no line across the waist
    ctx.beginPath()
    ctx.moveTo(topL[0], topL[1] + 2)
    ctx.lineTo(outL, hemL)
    ctx.quadraticCurveTo(300 + (liftR - liftL) * 34, sag, outR, hemR)
    ctx.lineTo(topR[0], topR[1] + 2)
    ctx.strokeStyle = INK
    ctx.lineWidth = 3.2
    ctx.stroke()
    // folds follow the hem: a raised side gets a longer, leaning crease
    for (const x of [-44, 0, 44]) {
      const lift = x < 0 ? liftL : liftR
      const hem = 658 - lift * 100
      ctx.beginPath()
      ctx.moveTo(300 + x * 0.7, 528)
      ctx.lineTo(300 + x + (x < 0 ? -lift : lift) * 8, hem)
      ctx.strokeStyle = 'rgba(0,0,0,.14)'
      ctx.lineWidth = 2.2
      ctx.stroke()
    }
    // a soft fold from the hip toward the raised knee sells the drape
    for (const [side, lift] of [['L', liftL], ['R', liftR]]) {
      if (lift < 0.15) continue
      const knee = side === 'L' ? sk.kneeL : sk.kneeR
      ctx.beginPath()
      ctx.moveTo(300 + (side === 'L' ? -58 : 58), 536)
      ctx.quadraticCurveTo(knee[0] * 0.42 + 300 * 0.58, 600, knee[0] * 0.5 + 150, 660 - lift * 96)
      ctx.strokeStyle = 'rgba(0,0,0,.10)'
      ctx.lineWidth = 3
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.moveTo(210, 640 - liftL * 96)
    ctx.quadraticCurveTo(300 + (liftR - liftL) * 30, 656 - Math.min(liftL, liftR) * 30, 390, 640 - liftR * 96)
    ctx.strokeStyle = c.accent
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.restore()
  }

  function drawTorso(ctx, sk, p, c) {
    if (sk.profile) { drawTorsoSide(ctx, sk, p, c); return }
    ctx.save()
    ctx.translate(sk.hipBase[0], sk.hipBase[1])
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    const spA = (sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot
    if (spA) { ctx.translate(300, 527); ctx.rotate(spA); ctx.translate(-300, -527) }
    const nProf = profileNarrow(sk.yaw, sk.profileHead)
    if ((c.shoulderW && c.shoulderW !== 1) || nProf !== 1) {
      ctx.translate(300, 0); ctx.scale((c.shoulderW || 1) * nProf, 1); ctx.translate(-300, 0)
    }
    const shY = RIG.shoulderL[1]
    const sL = RIG.shoulderL[0] - 10
    const sR = RIG.shoulderR[0] + 10
    const waist = 79
    const hipW = 94
    const outfit = c.outfit || 'shirt'
    const bottom = c.bottom || 'pants'
    const back = !!sk.back

    // shirt body — a soft trapezoid, not a rectangular card
    ctx.beginPath()
    ctx.moveTo(266, 314)
    ctx.quadraticCurveTo(230, 316, 204, 342)   // sloped trapezius
    ctx.quadraticCurveTo(216, 420, 211, 470)   // waist
    ctx.quadraticCurveTo(205, 510, 206, 545)
    ctx.lineTo(394, 545)
    ctx.quadraticCurveTo(395, 510, 389, 470)
    ctx.quadraticCurveTo(384, 420, 396, 342)
    ctx.quadraticCurveTo(370, 316, 334, 314)
    ctx.quadraticCurveTo(300, 332, 266, 314)   // neckline scoop
    ctx.closePath()
    fillStroke(ctx, c.shirt, INK, 3.4)

    // fabric pattern lives inside the garment silhouette
    if (!back && (c.pattern || 'solid') !== 'solid') {
      ctx.save()
      ctx.clip()
      ctx.strokeStyle = c.patternColor || c.shirtLight || c.shirt
      ctx.fillStyle = c.patternColor || c.shirtLight || c.shirt
      ctx.globalAlpha = 0.32
      const pat = c.pattern
      if (pat === 'stripes') {
        ctx.lineWidth = 7
        for (let x = 180; x < 430; x += 26) {
          ctx.beginPath(); ctx.moveTo(x, 300); ctx.lineTo(x + 26, 560); ctx.stroke()
        }
      } else if (pat === 'check') {
        ctx.lineWidth = 4
        for (let x = 190; x < 420; x += 28) { ctx.beginPath(); ctx.moveTo(x, 300); ctx.lineTo(x, 560); ctx.stroke() }
        for (let y = 320; y < 560; y += 28) { ctx.beginPath(); ctx.moveTo(180, y); ctx.lineTo(420, y); ctx.stroke() }
      } else if (pat === 'dots') {
        for (let y = 330; y < 560; y += 30) {
          for (let x = 200 + ((y / 30) % 2) * 15; x < 410; x += 30) {
            ctx.beginPath(); ctx.arc(x, y, 5, 0, TAU); ctx.fill()
          }
        }
      }
      ctx.restore()
    }

    // raglan seams turn the shoulder join into a garment detail
    if (!back && outfit !== 'coat' && outfit !== 'jacket' && outfit !== 'vest') {
      for (const side of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(300 + side * 30, 318)
        ctx.quadraticCurveTo(300 + side * 58, 372, 300 + side * 84, 425)
        ctx.strokeStyle = 'rgba(0,0,0,.14)'
        ctx.lineWidth = 2.4
        ctx.stroke()
      }
    }

    // side plane / paper fold
    ctx.save()
    ctx.clip()
    ctx.beginPath()
    ctx.moveTo(330, 330)
    ctx.quadraticCurveTo(350, 420, 337, 545)
    ctx.lineTo(410, 545)
    ctx.quadraticCurveTo(395, 390, 380, 330)
    ctx.closePath()
    ctx.fillStyle = 'rgba(0,0,0,.12)'
    ctx.fill()
    ctx.beginPath()
    ctx.moveTo(210, 350)
    ctx.quadraticCurveTo(230, 450, 230, 545)
    ctx.lineTo(190, 545)
    ctx.closePath()
    ctx.fillStyle = 'rgba(255,255,255,.07)'
    ctx.fill()
    ctx.restore()

    // waist / belt (a dress carries its own waistline)
    if (outfit !== 'dress') {
    ctx.beginPath()
    ctx.moveTo(213, 527)
    ctx.quadraticCurveTo(300, 516, 387, 527)
    ctx.lineTo(390, 548)
    ctx.quadraticCurveTo(300, 538, 210, 548)
    ctx.closePath()
    fillStroke(ctx, c.pantsDark, INK, 2.6)
    if (!back) {
      rr(ctx, 286, 524, 28, 18, 4)
      fillStroke(ctx, c.accent, INK, 2.2)
    }
    }

    if (!back && outfit === 'sweater') {
      // ribbed round collar and hem, no buttons
      ctx.beginPath()
      ctx.moveTo(262, 318)
      ctx.quadraticCurveTo(300, 352, 338, 318)
      ctx.strokeStyle = c.shirtDark
      ctx.lineWidth = 12
      ctx.lineCap = 'round'
      ctx.stroke()
      for (let i = 0; i < 7; i++) {
        ctx.beginPath()
        ctx.moveTo(256 + i * 15, 524)
        ctx.lineTo(256 + i * 15, 542)
        ctx.strokeStyle = 'rgba(0,0,0,.18)'
        ctx.lineWidth = 3
        ctx.stroke()
      }
    }
    if (!back && outfit === 'vest') {
      // deep V over the shirt, bare arms
      ctx.beginPath()
      ctx.moveTo(262, 316)
      ctx.lineTo(300, 388)
      ctx.lineTo(338, 316)
      ctx.quadraticCurveTo(300, 334, 262, 316)
      ctx.closePath()
      fillStroke(ctx, c.skin, INK, 2.4)
      ctx.beginPath()
      ctx.moveTo(262, 316)
      ctx.lineTo(300, 388)
      ctx.lineTo(338, 316)
      ctx.strokeStyle = c.shirtLight || c.shirtDark
      ctx.lineWidth = 5
      ctx.stroke()
    }
    // collar, buttons, scarf, pocket — depends on the outfit
    if (!back && outfit !== 'tee' && outfit !== 'hoodie' && outfit !== 'sweater' && outfit !== 'vest') {
      ctx.beginPath()
      ctx.moveTo(268, 322)
      ctx.lineTo(300, 360)
      ctx.lineTo(332, 322)
      ctx.quadraticCurveTo(300, 338, 268, 322)
      ctx.closePath()
      fillStroke(ctx, c.shirtDark, INK, 2.4)
    }
    if (!back && outfit === 'tee') {
      // crew neck: skin inside, ribbed band
      ctx.beginPath()
      ctx.moveTo(264, 318)
      ctx.quadraticCurveTo(300, 358, 336, 318)
      ctx.quadraticCurveTo(300, 338, 264, 318)
      ctx.closePath()
      fillStroke(ctx, c.skin, INK, 2.6)
      ctx.beginPath()
      ctx.moveTo(264, 318)
      ctx.quadraticCurveTo(300, 356, 336, 318)
      ctx.strokeStyle = c.shirtDark
      ctx.lineWidth = 6
      ctx.stroke()
    }
    if (c.scarf) {
      const sc = c.scarfColor || c.accent
      ctx.beginPath()
      ctx.moveTo(256, 318)
      ctx.quadraticCurveTo(300, 348, 344, 318)
      ctx.lineTo(354, 342)
      ctx.quadraticCurveTo(300, 378, 246, 342)
      ctx.closePath()
      fillStroke(ctx, sc, INK, 2.6)
      ctx.beginPath()
      ctx.moveTo(262, 340)
      ctx.quadraticCurveTo(250, 390, 258, 430)
      ctx.lineTo(282, 424)
      ctx.quadraticCurveTo(276, 382, 284, 350)
      ctx.closePath()
      fillStroke(ctx, sc, INK, 2.4)
    }

    if (!back && (outfit === 'shirt' || outfit === 'coat' || outfit === 'jacket')) {
      ctx.beginPath()
      ctx.moveTo(300, 360)
      ctx.lineTo(300, 515)
      ctx.strokeStyle = 'rgba(0,0,0,.22)'
      ctx.lineWidth = 2.5
      ctx.stroke()
      for (let i = 0; i < 4; i++) {
        ctx.beginPath()
        ctx.arc(300, 382 + i * 31, 3.2, 0, TAU)
        fillStroke(ctx, c.accent, INK, 1.6)
      }
    }

    if (!back && outfit === 'shirt' && c.neckerchief) {
      ctx.beginPath()
      ctx.moveTo(268, 326)
      ctx.quadraticCurveTo(300, 348, 332, 326)
      ctx.lineTo(346, 344)
      ctx.quadraticCurveTo(300, 374, 254, 344)
      ctx.closePath()
      fillStroke(ctx, c.scarfColor || c.accent, INK, 2.5)
    }
    if (!back && outfit === 'shirt') {
      // crisp collar band instead of a bib
      ctx.beginPath()
      ctx.moveTo(264, 316)
      ctx.lineTo(300, 352)
      ctx.lineTo(336, 316)
      ctx.strokeStyle = c.shirtLight || c.shirtDark
      ctx.lineWidth = 4
      ctx.stroke()
    }

    if (!back && (outfit === 'shirt' || outfit === 'coat')) {
      // patch pocket with a stitched line
      ctx.beginPath()
      ctx.moveTo(238, 414)
      ctx.lineTo(270, 414)
      ctx.lineTo(270, 442)
      ctx.lineTo(238, 442)
      ctx.closePath()
      ctx.strokeStyle = 'rgba(0,0,0,.24)'
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(241, 418)
      ctx.lineTo(267, 418)
      ctx.strokeStyle = 'rgba(255,255,255,.15)'
      ctx.stroke()
    }

    if (!back && outfit === 'hoodie') {
      // hood behind the neck
      ctx.beginPath()
      ctx.moveTo(254, 324)
      ctx.quadraticCurveTo(240, 284, 300, 278)
      ctx.quadraticCurveTo(360, 284, 346, 324)
      ctx.quadraticCurveTo(300, 342, 254, 324)
      ctx.closePath()
      fillStroke(ctx, c.shirtDark, INK, 3)
      // kangaroo pocket
      ctx.beginPath()
      ctx.moveTo(242, 452)
      ctx.lineTo(358, 452)
      ctx.quadraticCurveTo(362, 512, 344, 512)
      ctx.lineTo(256, 512)
      ctx.quadraticCurveTo(238, 512, 242, 452)
      ctx.closePath()
      fillStroke(ctx, c.shirtDark, INK, 2.6)
      // drawstrings
      for (const x of [288, 312]) {
        ctx.beginPath()
        ctx.moveTo(x, 332)
        ctx.quadraticCurveTo(x - 2, 372, x + 2, 404)
        ctx.strokeStyle = c.shirtLight
        ctx.lineWidth = 3
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(x + 2, 407, 3, 0, TAU)
        fillStroke(ctx, c.accent, INK, 1.4)
      }
    }

    if (outfit === 'coat' || outfit === 'jacket') {
      const coat = c.coatColor || c.shirtDark
      const hemY = outfit === 'jacket' ? 566 : 618
      // two long panels, open at the front
      for (const side of [-1, 1]) {
        const outerTop = 300 + side * 96
        const outerBot = 300 + side * 102
        const innerTop = 300 + side * 20
        const innerBot = 300 + side * 5
        ctx.beginPath()
        ctx.moveTo(innerTop, 334)
        ctx.lineTo(outerTop, 340)
        ctx.quadraticCurveTo(300 + side * 96, 480, outerBot, hemY)
        ctx.lineTo(innerBot, hemY)
        ctx.quadraticCurveTo(300 + side * 8, 470, innerTop, 334)
        ctx.closePath()
        fillStroke(ctx, coat, INK, 3)
      }
      // lapels
      for (const side of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(300 + side * 24, 324)
        ctx.lineTo(300 + side * 6, 392)
        ctx.lineTo(300 + side * 46, 350)
        ctx.closePath()
        fillStroke(ctx, coat, INK, 2.4)
      }
    }


    // dress / skirt: drawn over the torso hem, but with no stroke on its top
    // edge, so a dress reads as one garment instead of two plates
    if (outfit === 'dress' || bottom === 'skirt') drawSkirtBlock(ctx, sk, c, outfit, bottom, spA)
    if (!back && c.accessory && c.accessory !== 'none') {
      const ac = c.accessoryColor || c.accent
      if (c.accessory === 'tie') {
        ctx.beginPath()
        ctx.moveTo(294, 352); ctx.lineTo(306, 352); ctx.lineTo(303, 368); ctx.lineTo(297, 368)
        ctx.closePath(); fillStroke(ctx, ac, INK, 2)
        ctx.beginPath()
        ctx.moveTo(298, 368); ctx.lineTo(302, 368); ctx.lineTo(310, 470); ctx.lineTo(300, 486); ctx.lineTo(290, 470)
        ctx.closePath(); fillStroke(ctx, ac, INK, 2.2)
      } else if (c.accessory === 'bowtie') {
        for (const side of [-1, 1]) {
          ctx.beginPath()
          ctx.moveTo(300, 356)
          ctx.lineTo(300 + side * 24, 344)
          ctx.lineTo(300 + side * 24, 370)
          ctx.closePath(); fillStroke(ctx, ac, INK, 2)
        }
        ctx.beginPath(); ctx.arc(300, 357, 5, 0, TAU); fillStroke(ctx, ac, INK, 1.6)
      } else if (c.accessory === 'necklace') {
        ctx.beginPath()
        ctx.moveTo(278, 322)
        ctx.quadraticCurveTo(300, 368, 322, 322)
        ctx.strokeStyle = ac; ctx.lineWidth = 3; ctx.stroke()
        ctx.beginPath(); ctx.arc(300, 366, 6, 0, TAU); fillStroke(ctx, ac, INK, 1.6)
      } else if (c.accessory === 'badge') {
        ctx.beginPath(); ctx.arc(338, 402, 11, 0, TAU); fillStroke(ctx, ac, INK, 2)
        ctx.beginPath(); ctx.moveTo(332, 402); ctx.lineTo(344, 402); ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.stroke()
      }
    }
    if (back) {
      ctx.beginPath()
      ctx.moveTo(300, 342)
      ctx.lineTo(300, 516)
      ctx.strokeStyle = 'rgba(0,0,0,.18)'
      ctx.lineWidth = 2.4
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(236, 356)
      ctx.quadraticCurveTo(300, 378, 364, 356)
      ctx.strokeStyle = 'rgba(255,255,255,.10)'
      ctx.lineWidth = 4
      ctx.stroke()
    }
    // sleeve seam is intentionally invisible: the arm sits under this shape.
    ctx.restore()
  }

  function drawWaistCover(ctx, sk, c) {
    ctx.save()
    ctx.translate(sk.hipBase[0], sk.hipBase[1])
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    const spW = (sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot
    if (spW) { ctx.translate(300, 527); ctx.rotate(spW); ctx.translate(-300, -527) }
    ctx.translate(300, 0); ctx.scale(c.hipW || 1, 1); ctx.translate(-300, 0)
    rr(ctx, 206, 518, 188, 44, 10)
    fillStroke(ctx, c.pantsDark, INK, 3)
    rr(ctx, 286, 524, 28, 18, 4)
    fillStroke(ctx, c.accent, INK, 2)
    ctx.restore()
  }

  // Shorts are two tubes plus a small shell at the hips: without the shell a
  // raised knee opens the crotch and the skin body shows through.
  function drawShortsShell(ctx, sk, c) {
    ctx.save()
    ctx.translate(sk.hipBase[0], sk.hipBase[1])
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    if ((c.hipW && c.hipW !== 1) || sk.profileHead) {
      ctx.translate(300, 0); ctx.scale((c.hipW || 1) * profileNarrow(sk.yaw, sk.profileHead), 1); ctx.translate(-300, 0)
    }
    ctx.beginPath()
    ctx.moveTo(232, 526)
    ctx.quadraticCurveTo(300, 515, 368, 526)
    ctx.quadraticCurveTo(374, 566, 356, 596)
    ctx.quadraticCurveTo(336, 612, 300, 606)
    ctx.quadraticCurveTo(264, 612, 244, 596)
    ctx.quadraticCurveTo(226, 566, 232, 526)
    ctx.closePath()
    fillStroke(ctx, c.pants, INK, 3)
    ctx.beginPath()
    ctx.moveTo(300, 548)
    ctx.quadraticCurveTo(298, 578, 300, 600)
    ctx.strokeStyle = 'rgba(0,0,0,.20)'
    ctx.lineWidth = 2.2
    ctx.stroke()
    ctx.restore()
  }

  function drawPelvis(ctx, sk, c) {
    ctx.save()
    if (sk.profile) {
      ctx.translate(sk.hipBase[0], sk.hipBase[1])
      ctx.rotate(sk.bodyRot)
      ctx.translate(-RIG.hip[0], -RIG.hip[1])
      if ((sk.yaw || 0) < 0) { ctx.translate(300, 0); ctx.scale(-1, 1); ctx.translate(-300, 0) }
      ctx.beginPath()
      ctx.moveTo(252, 526)
      ctx.quadraticCurveTo(300, 516, 350, 526)
      ctx.quadraticCurveTo(356, 560, 346, 592)
      ctx.quadraticCurveTo(322, 604, 300, 602)
      ctx.quadraticCurveTo(278, 604, 256, 592)
      ctx.quadraticCurveTo(246, 560, 252, 526)
      ctx.closePath()
      ctx.fillStyle = c.pants
      ctx.fill()
      ctx.strokeStyle = INK
      ctx.lineWidth = 3
      ctx.beginPath(); ctx.moveTo(252, 526); ctx.quadraticCurveTo(300, 516, 350, 526); ctx.stroke()
      ctx.beginPath(); ctx.moveTo(350, 526); ctx.quadraticCurveTo(356, 560, 346, 592); ctx.stroke()
      ctx.beginPath(); ctx.moveTo(252, 526); ctx.quadraticCurveTo(246, 560, 256, 592); ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(300, 548)
      ctx.quadraticCurveTo(300, 580, 300, 600)
      ctx.strokeStyle = 'rgba(0,0,0,.22)'
      ctx.lineWidth = 2.2
      ctx.stroke()
      ctx.restore()
      return
    }
    ctx.translate(sk.hipBase[0], sk.hipBase[1])
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    if ((c.hipW && c.hipW !== 1) || Math.abs(sk.yaw || 0) > 0.001 || sk.profileHead) {
      ctx.translate(300, 0); ctx.scale((c.hipW || 1) * profileNarrow(sk.yaw, sk.profileHead), 1); ctx.translate(-300, 0)
    }
    ctx.beginPath()
    ctx.moveTo(228, 528)
    ctx.quadraticCurveTo(300, 517, 372, 528)
    ctx.quadraticCurveTo(372, 566, 356, 588)
    ctx.quadraticCurveTo(340, 600, 318, 602)
    ctx.quadraticCurveTo(306, 604, 302, 592)
    ctx.quadraticCurveTo(300, 586, 298, 592)
    ctx.quadraticCurveTo(294, 604, 282, 602)
    ctx.quadraticCurveTo(260, 600, 244, 588)
    ctx.quadraticCurveTo(228, 566, 228, 528)
    ctx.closePath()
    ctx.fillStyle = c.pants
    ctx.fill()
    // outline only the top and the outer hips: the bottom blends into thighs
    ctx.strokeStyle = INK
    ctx.lineWidth = 3
    ctx.beginPath(); ctx.moveTo(228, 528); ctx.quadraticCurveTo(300, 517, 372, 528); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(372, 528); ctx.quadraticCurveTo(372, 566, 356, 588); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(228, 528); ctx.quadraticCurveTo(228, 566, 244, 588); ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(300, 552)
    ctx.lineTo(300, 586)
    ctx.strokeStyle = 'rgba(0,0,0,.22)'
    ctx.lineWidth = 2.2
    ctx.stroke()
    for (const sx of [-1, 1]) {
      ctx.beginPath()
      ctx.moveTo(300 + sx * 16, 596)
      ctx.quadraticCurveTo(300 + sx * 24, 616, 300 + sx * 30, 640)
      ctx.strokeStyle = 'rgba(0,0,0,.14)'
      ctx.lineWidth = 5
      ctx.stroke()
    }
    ctx.restore()
  }

  function drawTorsoBack(ctx, sk, c) {
    // a thin dark shape behind the torso gives 2.5D depth
    ctx.save()
    ctx.translate(sk.hipBase[0] + 8, sk.hipBase[1] - 2)
    ctx.rotate(sk.bodyRot)
    ctx.translate(-RIG.hip[0], -RIG.hip[1])
    const spB = (sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot
    if (spB) { ctx.translate(300, 527); ctx.rotate(spB); ctx.translate(-300, -527) }
    if ((c.shoulderW && c.shoulderW !== 1) || sk.profileHead) {
      ctx.translate(300, 0); ctx.scale((c.shoulderW || 1) * profileNarrow(sk.yaw, sk.profileHead), 1); ctx.translate(-300, 0)
    }
    ctx.beginPath()
    ctx.moveTo(210, 332)
    ctx.quadraticCurveTo(260, 320, 300, 322)
    ctx.quadraticCurveTo(348, 320, 392, 334)
    ctx.quadraticCurveTo(393, 430, 397, 546)
    ctx.lineTo(206, 546)
    ctx.quadraticCurveTo(205, 430, 210, 332)
    ctx.closePath()
    ctx.fillStyle = c.shirtDark
    ctx.fill()
    ctx.restore()
  }

  // ── head / face ──────────────────────────────────────────────────────────
  function drawNeck(ctx, sk, c) {
    if (sk.profile) {
      const top = sk.head[1] + 66
      const bottom = sk.neck[1] + 46
      tapered(ctx, [sk.neck[0], top], [sk.neck[0], bottom], 25, 31, c.skin, INK, 'rgba(255,255,255,.10)')
      ctx.beginPath()
      ctx.moveTo(sk.neck[0] + 6, top + 4)
      ctx.quadraticCurveTo(sk.neck[0] + 14, bottom - 22, sk.neck[0] + 11, bottom - 6)
      ctx.strokeStyle = 'rgba(90,48,38,.18)'
      ctx.lineWidth = 7
      ctx.stroke()
      return
    }
    // A real column from the jaw to the collar. It used to sit entirely
    // behind the head, so the puppet read as "head on a shirt".
    const spN = (sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot
    const waistF = rotPoint(300, 527, sk.hipBase[0], sk.hipBase[1], sk.bodyRot)
    const bodyB = rotPoint(300, 336, sk.hipBase[0], sk.hipBase[1], sk.bodyRot)
    const bp = spN ? rotPoint(bodyB[0], bodyB[1], waistF[0], waistF[1], spN) : bodyB
    const ha = (sk.headTilt || 0) + sk.bodyRot * 0.45 + (sk.headExtra || 0) + spN * 0.8
    const hs = c.headScale || 1
    const topX = sk.head[0] - Math.sin(ha) * 72 * hs
    const top = sk.head[1] + Math.cos(ha) * 72 * hs
    tapered(ctx, [topX, top], [bp[0], bp[1]], 22, 28, c.skin, INK, 'rgba(255,255,255,.10)')
    // shadow under the jaw and on the far side
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(topX - 21, top + 2)
    ctx.quadraticCurveTo(topX, top + 16, topX + 21, top + 2)
    ctx.lineTo(topX + 21, top + 15)
    ctx.quadraticCurveTo(topX, top + 28, topX - 21, top + 15)
    ctx.closePath()
    ctx.fillStyle = 'rgba(60,30,24,.22)'
    ctx.fill()
    ctx.restore()
    ctx.beginPath()
    ctx.moveTo(topX + 8, top + 4)
    ctx.quadraticCurveTo(topX + 16, bp[1] - 20, topX + 13, bp[1] - 4)
    ctx.strokeStyle = 'rgba(90,48,38,.18)'
    ctx.lineWidth = 7
    ctx.stroke()
    // collar sits above the neck root, so the head does not float on a stick.
    // It is a solid bib, not a crescent: the neckline scoop must not show skin.
    if (c.outfit !== 'vest') {
      const tee = c.outfit === 'tee'
      ctx.save()
      ctx.translate(sk.hipBase[0], sk.hipBase[1])
      ctx.rotate(sk.bodyRot)
      ctx.translate(-RIG.hip[0], -RIG.hip[1])
      if (spN) { ctx.translate(300, 527); ctx.rotate(spN); ctx.translate(-300, -527) }
      // A shallow scoop: a deep V would open a gap between the neck and the
      // collar, showing the background through the neckline.
      ctx.beginPath()
      ctx.moveTo(tee ? 258 : 248, 304)
      ctx.quadraticCurveTo(300, tee ? 318 : 319, tee ? 342 : 352, 304)
      ctx.lineTo(tee ? 346 : 356, tee ? 330 : 338)
      ctx.quadraticCurveTo(300, tee ? 366 : 380, tee ? 254 : 244, tee ? 330 : 338)
      ctx.closePath()
      fillStroke(ctx, (c.outfit === 'coat' || c.outfit === 'jacket') ? (c.coatColor || c.shirtDark) : c.shirtDark, INK, 2.8)
      if (c.outfit === 'sweater') {
        for (let i = 0; i < 7; i++) {
          ctx.beginPath()
          ctx.moveTo(262 + i * 13, 318)
          ctx.lineTo(266 + i * 13, 334)
          ctx.strokeStyle = 'rgba(255,255,255,.10)'
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }
      ctx.restore()
    }
  }

  function drawHairBack(ctx, c) {
    if (c.hairStyle === 'bun') {
      ctx.beginPath()
      ctx.arc(0, -96, 27, 0, TAU)
      fillStroke(ctx, c.hair, INK, 3.2)
      ctx.beginPath()
      ctx.arc(-6, -102, 12, 0, TAU)
      ctx.strokeStyle = c.hairLight
      ctx.lineWidth = 4
      ctx.globalAlpha = 0.5
      ctx.stroke()
      ctx.globalAlpha = 1
      return
    }
    if (c.hairStyle === 'ponytail') {
      ctx.beginPath()
      ctx.moveTo(62, -46)
      ctx.quadraticCurveTo(118, -18, 112, 46)
      ctx.quadraticCurveTo(92, 78, 78, 52)
      ctx.quadraticCurveTo(92, 6, 54, -28)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
      ctx.beginPath()
      ctx.moveTo(72, -22)
      ctx.quadraticCurveTo(104, 8, 96, 54)
      ctx.strokeStyle = c.hairLight
      ctx.lineWidth = 5
      ctx.globalAlpha = 0.4
      ctx.stroke()
      ctx.globalAlpha = 1
      return
    }
    if (c.hairStyle === 'long') {
      ctx.beginPath()
      ctx.moveTo(-84, -34)
      ctx.quadraticCurveTo(-102, 50, -88, 128)
      ctx.quadraticCurveTo(-60, 152, -26, 138)
      ctx.quadraticCurveTo(0, 128, 26, 138)
      ctx.quadraticCurveTo(60, 152, 88, 128)
      ctx.quadraticCurveTo(102, 50, 84, -34)
      ctx.quadraticCurveTo(42, -86, 0, -90)
      ctx.quadraticCurveTo(-42, -86, -84, -34)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3.2)
      for (const x of [-54, 54]) {
        ctx.beginPath()
        ctx.moveTo(x, 10)
        ctx.quadraticCurveTo(x * 1.22, 74, x * 0.88, 124)
        ctx.strokeStyle = c.hairLight
        ctx.lineWidth = 4.5
        ctx.globalAlpha = 0.3
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      return
    }
    if (c.hairStyle === 'afro') {
      ctx.beginPath()
      ctx.arc(0, -34, 92, 0, TAU)
      fillStroke(ctx, c.hair, INK, 3.2)
      return
    }
    if (c.hairStyle === 'mohawk') return
    if (c.hairStyle === 'curly') {
      for (const [x, y, r] of [[-48, -62, 30], [0, -78, 34], [48, -60, 30], [-64, -20, 26], [64, -20, 26], [0, -36, 30]]) {
        ctx.beginPath()
        ctx.arc(x, y, r, 0, TAU)
        fillStroke(ctx, c.hair, INK, 2.8)
      }
      return
    }
    if (c.hairStyle !== 'bob') return
    ctx.beginPath()
    ctx.moveTo(-87, -18)
    ctx.quadraticCurveTo(-108, 42, -91, 96)
    ctx.quadraticCurveTo(-68, 130, -34, 118)
    ctx.quadraticCurveTo(0, 106, 34, 118)
    ctx.quadraticCurveTo(68, 130, 91, 96)
    ctx.quadraticCurveTo(108, 42, 87, -18)
    ctx.quadraticCurveTo(43, -78, 0, -83)
    ctx.quadraticCurveTo(-43, -78, -87, -18)
    ctx.closePath()
    fillStroke(ctx, c.hair, INK, 3.2)
    ctx.beginPath()
    ctx.moveTo(-72, 38)
    ctx.quadraticCurveTo(-84, 84, -62, 110)
    ctx.strokeStyle = c.hairLight
    ctx.lineWidth = 5
    ctx.globalAlpha = 0.35
    ctx.stroke()
    ctx.globalAlpha = 1
  }

  function drawFace(ctx, c, p, emo, turn, yawIn, blinkIn) {
    const blink = blinkIn || 0
    const yaw = yawIn || 0
    ctx.save()
    ctx.translate(turn * 8, 0)
    ctx.scale(1 + Math.abs(turn) * 0.045, 1)
    // face silhouettes: oval / round / square / heart
    const shape = c.faceShape || 'oval'
    const fw = shape === 'round' ? 85 : shape === 'square' ? 80 : shape === 'heart' ? 83 : 80
    const jw = shape === 'round' ? 45 : shape === 'square' ? 53 : shape === 'heart' ? 24 : 34
    const chin = shape === 'round' ? 101 : shape === 'heart' ? 110 : 107
    const cheek = shape === 'square' ? 70 : 74
    ctx.beginPath()
    ctx.moveTo(0, -92)
    ctx.bezierCurveTo(fw * 0.7, -92, fw, -50, fw, -2)
    ctx.bezierCurveTo(fw, 43, jw * 1.8, cheek, jw, chin - 13)
    ctx.bezierCurveTo(jw * 0.65, chin - 4, jw * 0.26, chin, 0, chin)
    ctx.bezierCurveTo(-jw * 0.26, chin, -jw * 0.65, chin - 4, -jw, chin - 13)
    ctx.bezierCurveTo(-jw * 1.8, cheek, -fw, 43, -fw, -2)
    ctx.bezierCurveTo(-fw, -50, -fw * 0.7, -92, 0, -92)
    ctx.closePath()
    fillStroke(ctx, c.skin, INK, 3.4)

    ctx.save()
    ctx.clip()
    // flat paper shadows: one cool side plane, one warm cheek plane
    const shSide = yaw > 0 ? -1 : 1
    ctx.beginPath()
    ctx.moveTo(shSide * 31, -90)
    ctx.quadraticCurveTo(shSide * 66, 2, shSide * 44, 94)
    ctx.lineTo(shSide * 90, 112)
    ctx.lineTo(shSide * 90, -94)
    ctx.closePath()
    ctx.fillStyle = 'rgba(71,48,42,.13)'
    ctx.fill()
    ctx.beginPath()
    ctx.ellipse(-37, -8, 23, 14, -0.3, 0, TAU)
    ctx.ellipse(37, -8, 23, 14, 0.3, 0, TAU)
    ctx.fillStyle = `rgba(220,100,90,${emo.blush})`
    ctx.fill()
    ctx.restore()

    // ears: the far one disappears in a 3/4 turn
    for (const s of [-1, 1]) {
      const far = (yaw > 0 && s === -1) || (yaw < 0 && s === 1)
      if (far && Math.abs(yaw) > 0.5) continue
      const er = far ? 1 - 0.4 * Math.abs(yaw) : 1
      ctx.beginPath()
      ctx.ellipse(s * 79, 5, 14 * er, 25 * er, 0, 0, TAU)
      fillStroke(ctx, c.skin, INK, 2.8)
      ctx.beginPath()
      ctx.ellipse(s * 80, 7, 7 * er, 13 * er, 0, 0, TAU)
      ctx.fillStyle = 'rgba(120,64,48,.30)'
      ctx.fill()
    }

    // facial features slide toward the near side
    ctx.save()
    ctx.translate(yaw * 16, 0)

    // nose: a small library of silhouettes instead of one line
    const nose = c.noseStyle || 'straight'
    const nx = turn * 4 + yaw * 6
    ctx.strokeStyle = 'rgba(94,54,40,.55)'
    ctx.lineWidth = 3
    if (nose === 'button') {
      ctx.beginPath()
      ctx.moveTo(nx + 1, -8)
      ctx.quadraticCurveTo(nx + 3, 12, nx + 1, 20)
      ctx.quadraticCurveTo(nx - 4, 26, nx - 10, 22)
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(nx - 1, 21, 9, 5.5, -0.1, 0, TAU)
      ctx.fillStyle = 'rgba(94,54,40,.14)'
      ctx.fill()
    } else if (nose === 'wide') {
      ctx.beginPath()
      ctx.moveTo(nx - 6, -10)
      ctx.quadraticCurveTo(nx + 2, 12, nx - 2, 28)
      ctx.quadraticCurveTo(nx - 8, 35, nx - 18, 32)
      ctx.moveTo(nx + 6, -10)
      ctx.quadraticCurveTo(nx + 9, 14, nx + 7, 28)
      ctx.quadraticCurveTo(nx + 5, 34, nx - 2, 34)
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(nx - 10, 32, 6, 3, -0.15, 0, TAU)
      ctx.ellipse(nx + 4, 33, 6, 3, 0.15, 0, TAU)
      ctx.fillStyle = 'rgba(94,54,40,.22)'
      ctx.fill()
    } else if (nose === 'hooked') {
      ctx.beginPath()
      ctx.moveTo(nx + 2, -12)
      ctx.quadraticCurveTo(nx + 12, 10, nx + 9, 26)
      ctx.quadraticCurveTo(nx + 4, 36, nx - 12, 34)
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(nx - 8, 34, 7, 3, -0.2, 0, TAU)
      ctx.fillStyle = 'rgba(255,255,255,.16)'
      ctx.fill()
    } else if (nose === 'small') {
      ctx.beginPath()
      ctx.moveTo(nx, 4)
      ctx.quadraticCurveTo(nx + 2, 20, nx - 3, 25)
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(nx - 5, 26, 5, 2.5, -0.15, 0, TAU)
      ctx.fillStyle = 'rgba(255,255,255,.16)'
      ctx.fill()
    } else {
      ctx.beginPath()
      ctx.moveTo(turn * 3 + yaw * 5, -13)
      ctx.quadraticCurveTo(nx + 4, 13, nx + 1, 27)
      ctx.quadraticCurveTo(nx - 2, 34, nx - 11, 32)
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(nx - 8, 33, 7, 3.2, -0.15, 0, TAU)
      ctx.fillStyle = 'rgba(255,255,255,.18)'
      ctx.fill()
    }

    // eyes: the far one narrows in a 3/4 turn
    const farSign = yaw > 0 ? -1 : 1
    const eyeS = c.eyeSize || 1
    const gapK = c.eyeGap || 1
    for (const s of [-1, 1]) {
      const ex = s * 34 * gapK + turn * 9
      const ey = -9
      const eyeStyle = c.eyeStyle || 'round'
      const rxBase = eyeStyle === 'almond' ? 21 : eyeStyle === 'narrow' ? 22 : eyeStyle === 'wide' ? 17.5 : 19
      const ryBase = eyeStyle === 'almond' ? 9.5 : eyeStyle === 'narrow' ? 7.5 : eyeStyle === 'wide' ? 13 : 11.5
      const rx = s === farSign ? rxBase * eyeS * (1 - 0.45 * Math.abs(yaw)) : rxBase * eyeS
      const ry = ryBase * (0.7 + 0.3 * eyeS)
      ctx.beginPath()
      ctx.ellipse(ex, ey, rx, ry, 0, 0, TAU)
      fillStroke(ctx, '#f7f0df', INK, 2.6)
      ctx.save()
      ctx.beginPath()
      ctx.ellipse(ex, ey, rx, ry, 0, 0, TAU)
      ctx.clip()
      ctx.beginPath()
      ctx.arc(ex + (p.gazeX || 0) * 4.5, ey + (p.gazeY || 0) * 2.2, 7.3, 0, TAU)
      fillStroke(ctx, c.eye, INK, 1.2)
      ctx.beginPath()
      ctx.arc(ex + (p.gazeX || 0) * 4.5, ey + (p.gazeY || 0) * 2.2, 3.2, 0, TAU)
      ctx.fillStyle = INK
      ctx.fill()
      ctx.beginPath()
      ctx.arc(ex - 4.5, ey - 4, 2.2, 0, TAU)
      ctx.fillStyle = '#fffdf6'
      ctx.fill()
      // upper lid
      ctx.beginPath()
      const lw = rx + 1
      ctx.moveTo(ex - lw, ey - 1)
      ctx.quadraticCurveTo(ex, ey - (ry + 6) * (1 - (emo.eye || 0)), ex + lw, ey - 1)
      ctx.strokeStyle = INK
      ctx.lineWidth = 3.4
      ctx.stroke()
      if (blink > 0.02) {
        const lidY = ey - 12 + 24 * blink
        ctx.beginPath()
        ctx.rect(ex - rx - 2, ey - 14, rx * 2 + 4, Math.max(0, lidY - (ey - 14)))
        ctx.fillStyle = c.skin
        ctx.fill()
        ctx.beginPath()
        ctx.moveTo(ex - rx, lidY)
        ctx.quadraticCurveTo(ex, lidY + 2.5 * (1 - blink), ex + rx, lidY)
        ctx.strokeStyle = INK
        ctx.lineWidth = 3.4
        ctx.stroke()
      }
      ctx.restore()
      // lashes for Mira
      if (c.id === 'mira' && blink < 0.4) {
        ctx.beginPath()
        ctx.moveTo(ex + s * 17, ey - 4)
        ctx.lineTo(ex + s * 26, ey - 9)
        ctx.strokeStyle = INK
        ctx.lineWidth = 2.4
        ctx.stroke()
      }
    }

    // brows
    for (const s of [-1, 1]) {
      const bx = s * 34 * gapK + turn * 8
      const by = -33 + (emo.brow || 0)
      const bw = 17 * eyeS
      const browStyle = c.browStyle || 'soft'
      const thick = browStyle === 'thick' ? 7.5 : browStyle === 'thin' ? 3 : 5
      const curve = browStyle === 'straight' ? 0 : 7
      ctx.beginPath()
      ctx.moveTo(bx - bw, by + (s < 0 ? (emo.browTilt || 0) * 12 : -(emo.browTilt || 0) * 12))
      ctx.quadraticCurveTo(bx, by - curve, bx + bw, by + (s < 0 ? -(emo.browTilt || 0) * 12 : (emo.browTilt || 0) * 12))
      ctx.strokeStyle = c.hair
      ctx.lineWidth = thick
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    if (c.beard) drawBeard(ctx, c)
    if (c.glasses) drawGlasses(ctx, c, turn)
    ctx.restore()
    ctx.restore()
  }

  function drawMustache(ctx, c, w) {
    const hair = c.hair
    ctx.beginPath()
    ctx.moveTo(-4, 38)
    ctx.quadraticCurveTo(-22, 31, -36, 39)
    ctx.quadraticCurveTo(-26, 50, -4, 46)
    ctx.quadraticCurveTo(0, 47, 4, 46)
    ctx.quadraticCurveTo(26, 50, 36, 39)
    ctx.quadraticCurveTo(22, 31, 4, 38)
    ctx.closePath()
    fillStroke(ctx, hair, INK, 2.2)
    if (w > 1) {
      ctx.beginPath()
      ctx.moveTo(-10, 42)
      ctx.quadraticCurveTo(-24, 37, -33, 41)
      ctx.strokeStyle = 'rgba(255,255,255,.12)'
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }

  function drawBeard(ctx, c) {
    const style = c.beardStyle || (c.beard ? 'full' : 'none')
    if (style === 'none') return
    ctx.save()
    if (style === 'mustache') {
      drawMustache(ctx, c, 1)
      ctx.restore()
      return
    }
    if (style === 'goatee') {
      ctx.beginPath()
      ctx.moveTo(-38, 60)
      ctx.quadraticCurveTo(-34, 84, 0, 96)
      ctx.quadraticCurveTo(34, 84, 38, 60)
      ctx.quadraticCurveTo(18, 70, 0, 70)
      ctx.quadraticCurveTo(-18, 70, -38, 60)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 2.4)
      drawMustache(ctx, c, 1)
      ctx.restore()
      return
    }
    const short = style === 'short'
    const longBeard = style === 'long'
    const chinY = short ? 78 : longBeard ? 112 : 89
    const shape = c.faceShape || 'oval'
    const jw = shape === 'round' ? 45 : shape === 'square' ? 53 : shape === 'heart' ? 24 : 34
    const bw = Math.min(57, jw + 17)
    // jaw mask: sideburns → jaw → chin, top edge follows the nose base
    ctx.beginPath()
    ctx.moveTo(-bw, 16)
    ctx.bezierCurveTo(-bw - 3, 46, -bw * 0.66, chinY - 12, 0, chinY)
    ctx.bezierCurveTo(bw * 0.66, chinY - 12, bw + 3, 46, bw, 16)
    ctx.quadraticCurveTo(bw * 0.8, 28, bw * 0.55, 35)
    ctx.quadraticCurveTo(bw * 0.26, 41, 0, 41)
    ctx.quadraticCurveTo(-bw * 0.26, 41, -bw * 0.55, 35)
    ctx.quadraticCurveTo(-bw * 0.8, 28, -bw, 16)
    ctx.closePath()
    fillStroke(ctx, c.beardColor || c.hair, INK, 2.5)
    if (longBeard) {
      ctx.beginPath()
      ctx.moveTo(-22, 96)
      ctx.quadraticCurveTo(-8, 126, 0, 132)
      ctx.quadraticCurveTo(8, 126, 22, 96)
      ctx.quadraticCurveTo(0, 112, -22, 96)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 2.2)
    }
    // mouth opening so lips stay readable
    ctx.beginPath()
    ctx.ellipse(0, 50, 25.5, 10.5, 0, 0, TAU)
    ctx.fillStyle = c.skin
    ctx.fill()
    // a little texture so the beard does not read as a flat mask
    ctx.strokeStyle = c.hairLight || c.hair
    ctx.globalAlpha = 0.32
    ctx.lineWidth = 2
    for (const sx of [-1, 1]) {
      ctx.beginPath()
      ctx.moveTo(sx * (bw - 12), 34)
      ctx.quadraticCurveTo(sx * (bw - 18), 62, sx * 18, chinY - 8)
      ctx.stroke()
    }
    ctx.globalAlpha = 1
    // mustache over the opening
    drawMustache(ctx, c, short ? 0.6 : 1)
    if (short) {
      ctx.beginPath()
      ctx.moveTo(-40, 64)
      ctx.quadraticCurveTo(0, 84, 40, 64)
      ctx.strokeStyle = 'rgba(255,255,255,.10)'
      ctx.lineWidth = 3
      ctx.stroke()
    }
    ctx.restore()
  }

  function drawGlasses(ctx, c, turn) {
    ctx.strokeStyle = c.glassesColor || c.accent
    ctx.lineWidth = 3
    const style = c.glassesStyle || 'round'
    for (const s of [-1, 1]) {
      const ex = s * 34 + turn * 9
      ctx.beginPath()
      if (style === 'square') {
        rr(ctx, ex - 22, -23, 44, 28, 7)
      } else if (style === 'aviator') {
        ctx.moveTo(ex - 23, -20)
        ctx.quadraticCurveTo(ex, -26, ex + 23, -20)
        ctx.quadraticCurveTo(ex + 18, 6, ex, 9)
        ctx.quadraticCurveTo(ex - 18, 6, ex - 23, -20)
      } else {
        ctx.ellipse(ex, -9, 23, 15.5, 0, 0, TAU)
      }
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(ex + s * 22, -10)
      ctx.lineTo(s * 72, -15)
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.moveTo(-11, -11)
    ctx.quadraticCurveTo(0, -16, 11, -11)
    ctx.stroke()
  }

  function mouthParams(p, state) {
    let vis = VISEMES.sil
    if (state.phoneme) vis = VISEMES[visemeOf(state.phoneme)] || vis
    else if (state.mouth) vis = state.mouth
    return vis
  }

  function drawMouth(ctx, vis, c, emo, state) {
    const y = 49
    const lip = c.lipStyle || 'full'
    const lipK = lip === 'wide' ? 1.22 : lip === 'small' ? 0.82 : lip === 'thin' ? 0.94 : 1.04
    const lipT = lip === 'thin' ? 3.2 : lip === 'small' ? 3.4 : 5
    const w = vis.w * (c.mouthW || 1) * lipK
    const h = vis.h
    const curve = (emo.mouthCurve || 0) * 14 + (vis.smile || 0) * 3
    if (h < 5 && !state.speaking) {
      ctx.beginPath()
      ctx.moveTo(-w / 2, y - curve * 0.35)
      ctx.quadraticCurveTo(0, y + curve, w / 2, y - curve * 0.35)
      ctx.strokeStyle = c.lip
      ctx.lineWidth = lipT
      ctx.lineCap = 'round'
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(-w / 2 + 3, y - curve * 0.2)
      ctx.quadraticCurveTo(0, y + curve * 0.6, w / 2 - 3, y - curve * 0.2)
      ctx.strokeStyle = 'rgba(255,255,255,.18)'
      ctx.lineWidth = 2
      ctx.stroke()
      return
    }
    const top = y - h * 0.48
    const bot = y + h * 0.52
    const left = -w / 2
    const right = w / 2
    ctx.beginPath()
    ctx.moveTo(left, y)
    ctx.quadraticCurveTo(left + w * 0.18, top - h * 0.08, 0, top)
    ctx.quadraticCurveTo(right - w * 0.18, top - h * 0.08, right, y)
    ctx.quadraticCurveTo(right - w * 0.22, bot + h * 0.08, 0, bot)
    ctx.quadraticCurveTo(left + w * 0.22, bot + h * 0.08, left, y)
    ctx.closePath()
    fillStroke(ctx, '#3a2022', INK, 2.4)
    ctx.save()
    ctx.clip()
    // tongue
    if (vis.tongue > 0) {
      ctx.beginPath()
      ctx.ellipse(0, bot - 2, w * 0.29, Math.max(3, h * 0.25 * vis.tongue), 0, 0, TAU)
      ctx.fillStyle = '#c7646b'
      ctx.fill()
    }
    // teeth
    if (vis.teeth > 0) {
      ctx.beginPath()
      ctx.rect(left, top, w, Math.max(2.5, h * 0.20))
      ctx.fillStyle = '#f7f0de'
      ctx.fill()
    }
    // rounded lips
    ctx.beginPath()
    ctx.ellipse(0, y, w * (0.50 - vis.round * 0.04), h * 0.53, 0, 0, TAU)
    ctx.strokeStyle = c.lip
    ctx.lineWidth = 3.2
    ctx.stroke()
    ctx.restore()
    // lips
    ctx.beginPath()
    ctx.moveTo(left, y)
    ctx.quadraticCurveTo(left + w * 0.18, top - h * 0.12, 0, top - 1)
    ctx.quadraticCurveTo(right - w * 0.18, top - h * 0.12, right, y)
    ctx.strokeStyle = c.lip
    ctx.lineWidth = Math.max(2.6, lipT - 0.6)
    ctx.lineCap = 'round'
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(left + 2, y)
    ctx.quadraticCurveTo(0, bot + 2, right - 2, y)
    ctx.strokeStyle = 'rgba(90,38,38,.45)'
    ctx.lineWidth = 2.4
    ctx.stroke()
  }

  function drawHairFront(ctx, c) {
    if (c.hairStyle === 'bald') return
    if (c.hairStyle === 'afro') {
      // a ring, not a disc: the face stays open
      ctx.beginPath()
      ctx.arc(0, -34, 94, 0, TAU)
      ctx.arc(0, -14, 70, 0, TAU, true)
      ctx.fillStyle = c.hair
      ctx.fill('evenodd')
      ctx.beginPath()
      ctx.arc(0, -34, 94, 0, TAU)
      ctx.strokeStyle = INK
      ctx.lineWidth = 3.2
      ctx.stroke()
      return
    }
    if (c.hairStyle === 'mohawk') {
      ctx.beginPath()
      ctx.moveTo(-44, -48)
      ctx.quadraticCurveTo(-54, -104, -20, -116)
      ctx.quadraticCurveTo(-8, -142, 8, -118)
      ctx.quadraticCurveTo(46, -108, 40, -50)
      ctx.quadraticCurveTo(18, -70, 0, -72)
      ctx.quadraticCurveTo(-22, -70, -44, -48)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
      ctx.beginPath()
      ctx.moveTo(-2, -112)
      ctx.quadraticCurveTo(0, -94, 2, -74)
      ctx.strokeStyle = c.hairLight
      ctx.lineWidth = 4
      ctx.globalAlpha = 0.4
      ctx.stroke()
      ctx.globalAlpha = 1
      return
    }
    if (c.hairStyle === 'bob' || c.hairStyle === 'long') {
      ctx.beginPath()
      ctx.moveTo(-82, -10)
      ctx.quadraticCurveTo(-92, -68, -42, -88)
      ctx.quadraticCurveTo(0, -103, 42, -88)
      ctx.quadraticCurveTo(92, -68, 82, -10)
      ctx.quadraticCurveTo(66, -42, 40, -51)
      ctx.quadraticCurveTo(16, -57, 2, -53)
      ctx.quadraticCurveTo(-22, -59, -46, -48)
      ctx.quadraticCurveTo(-67, -39, -82, -10)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3.2)
      // paper locks
      for (let i = -1; i <= 1; i++) {
        ctx.beginPath()
        ctx.moveTo(i * 30, -81)
        ctx.quadraticCurveTo(i * 45 - 4, -54, i * 36 + 3, -38)
        ctx.strokeStyle = c.hairLight
        ctx.lineWidth = 4
        ctx.globalAlpha = 0.35
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      // side locks framing the face
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(s * 79, -24)
        ctx.quadraticCurveTo(s * 93, c.hairStyle === 'long' ? 70 : 24, s * 78, c.hairStyle === 'long' ? 118 : 68)
        ctx.quadraticCurveTo(s * 68, c.hairStyle === 'long' ? 132 : 84, s * 56, c.hairStyle === 'long' ? 116 : 69)
        ctx.quadraticCurveTo(s * 72, 26, s * 64, -14)
        ctx.closePath()
        fillStroke(ctx, c.hair, INK, 2.8)
      }
    } else {
      ctx.beginPath()
      ctx.moveTo(-77, -12)
      ctx.quadraticCurveTo(-82, -70, -31, -88)
      ctx.quadraticCurveTo(21, -106, 67, -71)
      ctx.quadraticCurveTo(89, -53, 77, -12)
      ctx.quadraticCurveTo(67, -42, 38, -50)
      ctx.quadraticCurveTo(4, -58, -22, -46)
      ctx.quadraticCurveTo(-53, -34, -77, -12)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3.2)
      // fringe locks sweep left
      for (let i = 0; i < 4; i++) {
        ctx.beginPath()
        ctx.moveTo(58 - i * 22, -73)
        ctx.quadraticCurveTo(20 - i * 16, -61, -34 - i * 7, -36 + i * 4)
        ctx.strokeStyle = c.hairLight
        ctx.lineWidth = 4.2
        ctx.globalAlpha = 0.28
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      for (const s of [-1, 1]) {
        ctx.beginPath()
        ctx.moveTo(s * 77, -13)
        ctx.quadraticCurveTo(s * 78, 10, s * 69, 28)
        ctx.quadraticCurveTo(s * 64, 34, s * 59, 25)
        ctx.quadraticCurveTo(s * 67, 8, s * 66, -9)
        ctx.closePath()
        fillStroke(ctx, c.hair, INK, 2.5)
      }
    }
    if (c.hairStyle === 'curly') {
      for (const [x, y, r] of [[-56, -60, 20], [-20, -86, 24], [20, -88, 24], [56, -58, 20]]) {
        ctx.beginPath()
        ctx.arc(x, y, r, 0, TAU)
        fillStroke(ctx, c.hair, INK, 2.8)
      }
    }
    if (c.hairStyle === 'pixie') {
      ctx.beginPath()
      ctx.moveTo(-72, -48)
      ctx.quadraticCurveTo(-96, -84, -52, -78)
      ctx.quadraticCurveTo(-38, -106, -6, -92)
      ctx.quadraticCurveTo(30, -114, 48, -84)
      ctx.quadraticCurveTo(84, -78, 70, -46)
      ctx.quadraticCurveTo(44, -60, 16, -56)
      ctx.quadraticCurveTo(-30, -60, -72, -48)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
    }
  }

  function profileNarrow(yaw, on) {
    // 3/4 turns narrow the whole paper body, not only the head. The extra
    // profile term is kept for the experimental side-view branch.
    const k = clamp(Math.abs(yaw || 0), 0, 1)
    const extra = on ? clamp((k - 0.7) / 0.3, 0, 1) * 0.12 : 0
    return 1 - 0.16 * k - extra
  }

  // A side-view head for the last 10% of the yaw range. The body narrows to a
  // 3/4 stance (see profileNarrow), so the character can face sideways without
  // pretending to be a full 3D model.
  function drawProfileHead(ctx, p, c, state) {
    const emo = EMOTIONS[state.emotion] || EMOTIONS.neutral
    const vis = state.mouth || VISEMES.sil
    const speaking = !!state.speaking

    // hair behind the skull
    if (c.hairStyle === 'afro') {
      ctx.beginPath()
      ctx.arc(-8, -26, 86, 0, TAU)
      fillStroke(ctx, c.hair, INK, 3.2)
    } else if (c.hairStyle === 'bob' || c.hairStyle === 'long') {
      ctx.beginPath()
      ctx.moveTo(-54, -54)
      ctx.bezierCurveTo(-84, -20, -82, 40, -62, 72)
      ctx.quadraticCurveTo(-44, 92, -20, 78)
      ctx.quadraticCurveTo(-40, 40, -36, -10)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
    } else if (c.hairStyle === 'bun' || c.hairStyle === 'ponytail') {
      ctx.beginPath()
      ctx.arc(-42, -74, 22, 0, TAU)
      fillStroke(ctx, c.hair, INK, 3)
      if (c.hairStyle === 'ponytail') {
        ctx.beginPath()
        ctx.moveTo(-40, -50)
        ctx.quadraticCurveTo(-86, -20, -74, 34)
        ctx.quadraticCurveTo(-58, 44, -50, 26)
        ctx.quadraticCurveTo(-58, -6, -30, -30)
        ctx.closePath()
        fillStroke(ctx, c.hair, INK, 3)
      }
    }

    // head silhouette: back of skull -> forehead -> nose -> lips -> chin
    ctx.beginPath()
    ctx.moveTo(-54, -50)
    ctx.bezierCurveTo(-50, -86, -8, -102, 28, -92)
    ctx.bezierCurveTo(52, -84, 62, -62, 60, -42)
    ctx.quadraticCurveTo(59, -28, 58, -20)
    ctx.lineTo(58, -12)
    ctx.bezierCurveTo(76, -4, 78, 8, 68, 14)
    ctx.quadraticCurveTo(63, 17, 58, 15)
    ctx.quadraticCurveTo(61, 22, 60, 28)
    ctx.quadraticCurveTo(57, 36, 50, 44)
    ctx.quadraticCurveTo(44, 54, 32, 62)
    ctx.quadraticCurveTo(20, 70, 4, 70)
    ctx.bezierCurveTo(-22, 70, -46, 54, -54, 28)
    ctx.bezierCurveTo(-58, 12, -56, -26, -54, -50)
    ctx.closePath()
    fillStroke(ctx, c.skin, INK, 3.2)

    // far-side shading
    ctx.save()
    ctx.clip()
    ctx.beginPath()
    ctx.moveTo(-54, -50)
    ctx.bezierCurveTo(-30, -70, -10, -60, -6, 40)
    ctx.lineTo(-60, 70)
    ctx.lineTo(-60, -60)
    ctx.closePath()
    ctx.fillStyle = 'rgba(71,48,42,.16)'
    ctx.fill()
    ctx.restore()

    // ear
    ctx.beginPath()
    ctx.ellipse(-6, 4, 11, 17, -0.1, 0, TAU)
    fillStroke(ctx, c.skin, INK, 2.8)
    ctx.beginPath()
    ctx.ellipse(-6, 5, 5, 9, 0, 0, TAU)
    ctx.fillStyle = 'rgba(120,64,48,.30)'
    ctx.fill()

    // eye
    ctx.beginPath()
    ctx.ellipse(34, -22, 10, 8, -0.06, 0, TAU)
    fillStroke(ctx, '#f7f0df', INK, 2.2)
    ctx.beginPath()
    ctx.arc(37 + (p.gazeX || 0) * 2.5, -22 + (p.gazeY || 0) * 1.4, 4.4, 0, TAU)
    ctx.fillStyle = c.eye
    ctx.fill()
    ctx.beginPath()
    ctx.arc(38.5, -24, 1.5, 0, TAU)
    ctx.fillStyle = '#fff'
    ctx.fill()
    // brow
    ctx.beginPath()
    ctx.moveTo(22, -36 + (emo.brow || 0) * 0.5)
    ctx.quadraticCurveTo(34, -42 + (emo.brow || 0) * 0.5, 46, -35)
    ctx.strokeStyle = c.hair
    ctx.lineWidth = 4.4
    ctx.lineCap = 'round'
    ctx.stroke()

    // nostril
    ctx.beginPath()
    ctx.ellipse(66, 6, 3, 2.2, 0.3, 0, TAU)
    ctx.fillStyle = 'rgba(70,40,30,.45)'
    ctx.fill()

    // mouth (profile)
    const my = 24
    const curve = (emo.mouthCurve || 0) * 4 + (vis.smile || 0) * 1.6
    if (vis.h < 5 && !speaking) {
      ctx.beginPath()
      ctx.moveTo(56, my)
      ctx.quadraticCurveTo(60, my + curve, 64, my - 1)
      ctx.strokeStyle = c.lip
      ctx.lineWidth = 3.6
      ctx.stroke()
    } else {
      const h = Math.max(4, vis.h * 0.42)
      ctx.beginPath()
      ctx.moveTo(56, my)
      ctx.quadraticCurveTo(61, my - h * 0.5, 65, my)
      ctx.quadraticCurveTo(61, my + h, 56, my)
      ctx.closePath()
      fillStroke(ctx, '#3a2022', INK, 1.8)
      if (vis.teeth > 0) {
        ctx.beginPath()
        ctx.rect(56, my - h * 0.45, 8, Math.max(1.5, h * 0.25))
        ctx.fillStyle = '#f7f0de'
        ctx.fill()
      }
    }

    // hair on top
    if (c.hairStyle !== 'bald') {
      ctx.beginPath()
      ctx.moveTo(-54, -50)
      ctx.bezierCurveTo(-52, -88, -8, -104, 30, -94)
      ctx.bezierCurveTo(54, -86, 64, -64, 62, -46)
      ctx.quadraticCurveTo(50, -64, 30, -70)
      ctx.quadraticCurveTo(6, -74, -14, -58)
      ctx.quadraticCurveTo(-34, -44, -40, -22)
      ctx.quadraticCurveTo(-46, -34, -54, -50)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
      ctx.beginPath()
      ctx.moveTo(10, -84)
      ctx.quadraticCurveTo(34, -80, 50, -62)
      ctx.strokeStyle = c.hairLight
      ctx.lineWidth = 4
      ctx.globalAlpha = 0.35
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    // beard along the jaw
    if (c.beard) {
      ctx.beginPath()
      ctx.moveTo(-24, 8)
      ctx.quadraticCurveTo(2, 56, 26, 64)
      ctx.quadraticCurveTo(44, 60, 52, 40)
      ctx.quadraticCurveTo(54, 50, 44, 60)
      ctx.quadraticCurveTo(24, 74, 2, 72)
      ctx.quadraticCurveTo(-26, 62, -36, 22)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 2.4)
    }

    // glasses
    if (c.glasses) {
      ctx.beginPath()
      ctx.ellipse(34, -22, 14, 12, 0, 0, TAU)
      ctx.strokeStyle = INK
      ctx.lineWidth = 2.6
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(20, -22)
      ctx.lineTo(-2, -18)
      ctx.stroke()
    }
  }

  function drawBackHead(ctx, sk, p, c) {
    const hs = c.headScale || 1
    ctx.save()
    ctx.translate(sk.head[0], sk.head[1])
    ctx.rotate((p.head.tilt || 0) * DEG + (p.body.rot || 0) * DEG * 0.45 + (sk.headExtra || 0) + ((sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot) * 0.8)
    if (hs !== 1) ctx.scale(hs, hs)
    // back of the skull is hair (or skin for a bald character)
    ctx.beginPath()
    ctx.moveTo(0, -92)
    ctx.bezierCurveTo(56, -92, 81, -50, 80, -2)
    ctx.bezierCurveTo(80, 43, 62, 74, 34, 94)
    ctx.bezierCurveTo(22, 103, 9, 107, 0, 107)
    ctx.bezierCurveTo(-9, 107, -22, 103, -34, 94)
    ctx.bezierCurveTo(-62, 74, -80, 43, -80, -2)
    ctx.bezierCurveTo(-81, -50, -56, -92, 0, -92)
    ctx.closePath()
    fillStroke(ctx, c.hairStyle === 'bald' ? c.skin : c.hair, INK, 3.2)
    // ears
    for (const s2 of [-1, 1]) {
      ctx.beginPath()
      ctx.ellipse(s2 * 79, 5, 14, 25, 0, 0, TAU)
      fillStroke(ctx, c.skin, INK, 2.8)
      ctx.beginPath()
      ctx.ellipse(s2 * 80, 7, 7, 13, 0, 0, TAU)
      ctx.fillStyle = 'rgba(120,64,48,.30)'
      ctx.fill()
    }
    // hair grooves + crown whorl
    if (c.hairStyle !== 'bald') {
      for (let i = -2; i <= 2; i++) {
        ctx.beginPath()
        ctx.moveTo(i * 18, -84)
        ctx.quadraticCurveTo(i * 26 + 8, -30, i * 18 + 4, 34)
        ctx.strokeStyle = c.hairLight
        ctx.lineWidth = 4
        ctx.globalAlpha = 0.28
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      ctx.beginPath()
      ctx.arc(-6, -46, 16, 0.4, 4.2)
      ctx.strokeStyle = c.hairLight
      ctx.lineWidth = 4
      ctx.globalAlpha = 0.4
      ctx.stroke()
      ctx.globalAlpha = 1
    }
    if (c.hairStyle === 'bob' || c.hairStyle === 'long') {
      ctx.beginPath()
      ctx.moveTo(-86, -30)
      ctx.quadraticCurveTo(-92, 60, -62, 108)
      ctx.quadraticCurveTo(-30, 122, 0, 118)
      ctx.quadraticCurveTo(30, 122, 62, 108)
      ctx.quadraticCurveTo(92, 60, 86, -30)
      ctx.closePath()
      fillStroke(ctx, c.hair, INK, 3)
    }
    if (c.headwear === 'cap' || c.headwear === 'beanie') {
      const capC = c.capColor || c.accent
      ctx.beginPath()
      ctx.moveTo(-84, -22)
      ctx.quadraticCurveTo(-92, -88, 0, -110)
      ctx.quadraticCurveTo(92, -88, 84, -22)
      ctx.quadraticCurveTo(0, -44, -84, -22)
      ctx.closePath()
      fillStroke(ctx, capC, INK, 3)
    }
    ctx.restore()
  }

  // A short neck joins the profile head to the collar. It is painted before
  // the torso, so the shirt collar closes the neck root instead of leaving a
  // flat skin cut-out over the shoulder.
  function drawProfileNeck(ctx, sk, p, c) {
    const hs = c.headScale || 1
    const ang = (p.head.tilt || 0) * DEG + (p.body.rot || 0) * DEG * 0.45 + (sk.headExtra || 0) + ((sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot) * 0.8
    // the neck hangs from the collar, not from the middle of the skull, so a
    // head tilt does not swing it out behind the jaw
    const baseY = sk.head[1] + 22 + 124 * hs * 1.08
    ctx.save()
    ctx.translate(sk.head[0], baseY)
    ctx.rotate(ang * 0.55)
    ctx.translate(-sk.head[0], -baseY)
    ctx.translate(sk.head[0], sk.head[1] + 22)
    ctx.scale(hs * 1.08 * (sk.yaw < 0 ? -1 : 1), hs * 1.08)
    tapered(ctx, [0, 58], [0, 124], 22, 27, c.skinDark, INK, 'rgba(255,255,255,.12)')
    ctx.restore()
  }

  function drawHead(ctx, sk, p, c, state) {
    if (sk.back) { drawBackHead(ctx, sk, p, c); return }
    const emo = state.emoBlend || EMOTIONS[state.emotion] || EMOTIONS.neutral
    const yaw = state.yaw || 0
    const turn = (p.head.turn || 0) + (state.gazeTurn || 0) + yaw * 0.5
    ctx.save()
    ctx.translate(sk.head[0], sk.head[1])
    ctx.rotate((p.head.tilt || 0) * DEG + (p.body.rot || 0) * DEG * 0.45 + (sk.headExtra || 0) + ((sk.spineRot !== undefined ? sk.spineRot : sk.bodyRot) - sk.bodyRot) * 0.8)
    const hs = c.headScale || 1
    if ((c.profileHead && Math.abs(yaw) >= 0.9) || Math.abs(yaw) >= 0.97) {
      ctx.translate(0, 22)
      ctx.scale(hs * 1.08 * (yaw < 0 ? -1 : 1), hs * 1.08)
      drawProfileHead(ctx, p, c, state)
      ctx.restore()
      return
    }
    if (hs !== 1) ctx.scale(hs, hs)
    ctx.translate(yaw * 9, 0)
    ctx.scale(1 - Math.abs(yaw) * 0.15, 1)
    drawHairBack(ctx, c)
    drawFace(ctx, c, { gazeX: state.gazeX || 0, gazeY: state.gazeY || 0 }, emo, turn, yaw, state.blink || 0)
    ctx.save()
    ctx.translate(turn * 8 + yaw * 6, 0)
    ctx.scale(1 + Math.abs(turn) * 0.045, 1)
    drawMouth(ctx, mouthParams(p, state), c, emo, state)
    ctx.restore()
    drawHairFront(ctx, c)
    if (c.headwear === 'cap') {
      const capC = c.capColor || c.accent
      ctx.beginPath()
      ctx.moveTo(-84, -22)
      ctx.quadraticCurveTo(-94, -86, -28, -106)
      ctx.quadraticCurveTo(32, -114, 78, -76)
      ctx.quadraticCurveTo(92, -52, 84, -22)
      ctx.quadraticCurveTo(0, -44, -84, -22)
      ctx.closePath()
      fillStroke(ctx, capC, INK, 3)
      ctx.beginPath()
      ctx.ellipse(8, -18, 76, 15, 0.04, 0, TAU)
      fillStroke(ctx, capC, INK, 2.6)
      ctx.beginPath()
      ctx.moveTo(-60, -38)
      ctx.quadraticCurveTo(0, -52, 62, -34)
      ctx.strokeStyle = 'rgba(0,0,0,.22)'
      ctx.lineWidth = 2.4
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(0, -104, 5, 0, TAU)
      fillStroke(ctx, capC, INK, 2)
    } else if (c.headwear === 'beanie') {
      const capC = c.capColor || c.accent
      ctx.beginPath()
      ctx.moveTo(-86, -18)
      ctx.quadraticCurveTo(-92, -92, 0, -112)
      ctx.quadraticCurveTo(92, -92, 86, -18)
      ctx.quadraticCurveTo(0, -40, -86, -18)
      ctx.closePath()
      fillStroke(ctx, capC, INK, 3)
      ctx.beginPath()
      ctx.moveTo(-88, -20)
      ctx.quadraticCurveTo(0, -44, 88, -20)
      ctx.lineTo(88, -2)
      ctx.quadraticCurveTo(0, -24, -88, -2)
      ctx.closePath()
      fillStroke(ctx, c.capColor ? c.capColor : c.shirtDark, INK, 2.4)
    }
    // a tiny paper highlight on the crown
    ctx.beginPath()
    ctx.ellipse(-26, -74, 17, 4, -0.22, 0, TAU)
    ctx.fillStyle = 'rgba(255,255,255,.14)'
    ctx.fill()
    ctx.restore()

    // Mira's earrings sit outside the transformed face
    if (c.id === 'mira') {
      for (const s of [-1, 1]) {
        const far = (yaw > 0 && s === -1) || (yaw < 0 && s === 1)
        if (far && Math.abs(yaw) > 0.5) continue
        ctx.beginPath()
        ctx.arc(sk.head[0] + s * 80 * hs + turn * 8 + yaw * 6, sk.head[1] + 27 * hs, 4.5 * hs, 0, TAU)
        fillStroke(ctx, c.accent, INK, 2)
      }
    }
  }

  // ── entry ────────────────────────────────────────────────────────────────
  // ── authoring helpers: register a studio preset, check joint limits ──────
  function skeleton3D(pose, angleRad, skin) {
    const p = normalizePose(pose || POSES.neutral)
    const sk = makeSkeleton(p, 0, skin || {})
    const a = Number(angleRad) || 0
    const ca = Math.cos(a), sa = Math.sin(a)
    const map = (pt) => [ (pt[0] - 300) * ca, pt[1], (pt[0] - 300) * sa ]
    const out = {}
    for (const key of ['hip', 'neck', 'head', 'shL', 'shR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR']) {
      if (sk[key]) out[key] = map(sk[key])
    }
    return out
  }

  function jointRange(joint, axis) {
    const j = ANATOMY[joint]
    return j && j[axis] ? j[axis].slice() : null
  }
  function clampJoint(joint, axis, value) {
    const r = jointRange(joint, axis)
    return r ? clamp(Number(value) || 0, r[0], r[1]) : value
  }
  function fingerCurl(c) {
    const k = clamp(Number(c) || 0, 0, 1)
    return {
      mcp: FINGER_CURL.mcp * k,
      pip: FINGER_CURL.pip * k,
      dip: FINGER_CURL.dip * k,
      thumbCmc: FINGER_CURL.thumbCmc * Math.min(1, k * 1.2),
      thumbMcp: FINGER_CURL.thumbMcp * k,
      thumbIp: FINGER_CURL.thumbIp * k,
    }
  }
  function anatomyReport(pose) {
    const p = normalizePose(pose || POSES.neutral)
    const fk = p.fk || {}
    const rows = []
    const add = (joint, axis, value, range) => {
      if (value === undefined || value === null) return
      rows.push({ joint, axis, value, range, ok: value >= range[0] && value <= range[1] })
    }
    add('elbow', 'flex', fk.elbowL, ANATOMY.elbow.flex)
    add('elbow', 'flex', fk.elbowR, ANATOMY.elbow.flex)
    add('forearm', 'pronation', p.armL.handRot, ANATOMY.forearm.pronation)
    add('forearm', 'pronation', p.armR.handRot, ANATOMY.forearm.pronation)
    add('wrist', 'flex', fk.wristL, ANATOMY.wrist.flex)
    add('wrist', 'flex', fk.wristR, ANATOMY.wrist.flex)
    add('hip', 'abduct', fk.hipL, ANATOMY.hip.abduct)
    add('hip', 'abduct', fk.hipR, ANATOMY.hip.abduct)
    add('knee', 'flex', fk.kneeL, ANATOMY.knee.flex)
    add('knee', 'flex', fk.kneeR, ANATOMY.knee.flex)
    add('ankle', 'flex', fk.ankleL, ANATOMY.ankle.plantarflex)
    add('ankle', 'flex', fk.ankleR, ANATOMY.ankle.plantarflex)
    add('spine', 'lateral', fk.spine, ANATOMY.spine.lateral)
    add('neck', 'lateral', fk.neck, ANATOMY.neck.lateral)
    add('head', 'tilt', (p.head.tilt || 0) + (fk.head || 0), ANATOMY.head.tilt)
    return rows
  }
  function registerClip(id, clip) {
    if (!id || !clip || !Array.isArray(clip.keys)) return false
    CLIPS[id] = JSON.parse(JSON.stringify(clip))
    if (!CLIPS[id].id) CLIPS[id].id = id
    return true
  }

  const POSE_SCHEMA = 2
  function normalizePose(input) {
    const p = input || {}
    const out = JSON.parse(JSON.stringify(BASE_POSE))
    Object.assign(out, p)
    out.body = Object.assign({}, BASE_POSE.body, p.body || {})
    out.head = Object.assign({}, BASE_POSE.head, p.head || {})
    out.armL = Object.assign({}, BASE_POSE.armL, p.armL || {})
    out.armR = Object.assign({}, BASE_POSE.armR, p.armR || {})
    out.legL = Object.assign({}, BASE_POSE.legL, p.legL || {})
    out.legR = Object.assign({}, BASE_POSE.legR, p.legR || {})
    out.fk = Object.assign({
      spine: 0, neck: 0, head: 0,
      shL: 0, elbowL: 0, wristL: 0, shR: 0, elbowR: 0, wristR: 0,
      hipL: 0, kneeL: 0, ankleL: 0, hipR: 0, kneeR: 0, ankleR: 0,
    }, p.fk || {})
    out.schemaVersion = POSE_SCHEMA
    return out
  }

  function registerPose(name, pose) {
    if (!name || !pose || !pose.body || !pose.armL || !pose.armR) return false
    POSES[name] = normalizePose(JSON.parse(JSON.stringify(pose)))
    return true
  }

  function validatePose(input) {
    const p = typeof input === 'string' ? POSES[input] : input
    const issues = []
    if (!p || !p.body) return { ok: false, issues: [{ joint: 'pose', axis: '-', value: null, limit: 'unknown pose' }] }
    const chk = (joint, axis, v, r) => {
      if (typeof v === 'number' && !inRange(v, r)) issues.push({ joint, axis, value: v, limit: [r[0], r[1]] })
    }
    chk('body', 'x', p.body.x, LIMITS.body.x)
    chk('body', 'y', p.body.y, LIMITS.body.y)
    chk('body', 'rot', p.body.rot, LIMITS.body.rot)
    chk('head', 'tilt', p.head.tilt, LIMITS.head.tilt)
    chk('head', 'turn', p.head.turn, LIMITS.head.turn)
    chk('head', 'nod', p.head.nod, LIMITS.head.nod)
    chk('legL', 'swing', p.legL && p.legL.swing, LIMITS.leg.swing)
    chk('legL', 'knee', p.legL && p.legL.knee, LIMITS.leg.knee)
    chk('legR', 'swing', p.legR && p.legR.swing, LIMITS.leg.swing)
    chk('legR', 'knee', p.legR && p.legR.knee, LIMITS.leg.knee)

    const sk = makeSkeleton(p, 0)
    for (const side of ['L', 'R']) {
      const sh = side === 'L' ? sk.shL : sk.shR
      const el = side === 'L' ? sk.elbowL : sk.elbowR
      const wr = side === 'L' ? sk.wristL : sk.wristR
      const a = [sh[0] - el[0], sh[1] - el[1]]
      const b = [wr[0] - el[0], wr[1] - el[1]]
      const la = Math.hypot(a[0], a[1]) || 1
      const lb = Math.hypot(b[0], b[1]) || 1
      const ang = Math.acos(clamp((a[0] * b[0] + a[1] * b[1]) / (la * lb), -1, 1)) / DEG
      if (!inRange(ang, LIMITS.arm.elbow)) {
        issues.push({ joint: 'elbow' + side, axis: 'flex', value: +ang.toFixed(1), limit: LIMITS.arm.elbow.slice() })
      }
      const target = p['arm' + side].hand
      const dist = Math.hypot(target[0] - sh[0], target[1] - sh[1])
      const max = (RIG.upperArm + RIG.lowerArm) * LIMITS.arm.reachMax
      if (dist > max + 1) {
        issues.push({ joint: 'arm' + side, axis: 'reach', value: +dist.toFixed(1), limit: [LIMITS.arm.reachMin, +max.toFixed(1)] })
      }
    }
    return { ok: issues.length === 0, issues }
  }

  function create(canvas, opts) {
    const o = opts || {}
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('PaperCast needs a 2D canvas')
    const state = {
      character: CHARACTERS[o.character] ? o.character : 'mark',
      pose: typeof o.pose === 'string' && POSES[o.pose] ? o.pose : 'neutral',
      emotion: o.emotion || 'neutral',
      emotionFrom: o.emotion || 'neutral',
      emotionAt: -1e9,
      phoneme: o.phoneme || null,
      visemes: Array.isArray(o.visemes) ? o.visemes.slice() : [],
      speaking: false,
      mouth: null,
      time: 0,
      blink: o.blink !== false,
      seed: Number(o.seed) || 0,
      gazeX: 0,
      gazeY: 0,
      gazeTurn: 0,
      showSkeleton: !!o.showSkeleton,
      autoGaze: o.autoGaze !== false,
      yaw: clamp(Number(o.yaw) || 0, -1, 1),
      back: !!o.back,
      life: Object.assign(
        { on: o.life !== false, breath: 1, sway: 1, nod: 1 },
        o.life && typeof o.life === 'object' ? o.life : {},
      ),
      customPose: o.pose && typeof o.pose === 'object' ? normalizePose(o.pose) : null,
      clip: null,
      clipAt: 0,
      poseKeys: Array.isArray(o.poseKeys) ? o.poseKeys.slice() : [],
      gesture: null,
      appearance: Object.assign({}, o.appearance || {}),
      fps: 0,
    }
    let palette = Object.assign({}, CHARACTERS[state.character], normalizeAppearance(state.appearance))
    let w = 600, h = 900, dpr = 1
    let lastFrame = null

    function currentChar() {
      return Object.assign({}, CHARACTERS[state.character], state.appearance, { id: state.character })
    }

    // Backing-store budget: flat paper-cut art stays readable when the canvas
    // is a bit smaller than the device, and every extra megapixel is paid on
    // every frame (phones with dpr 3 and 4K canvases otherwise drop to ~20 fps).
    // 1.4 Mpx is ~1.25× a 1280×720 slide: enough for flat vector art, and four
    // times cheaper than rendering at dpr 2 on a 1080p stage. Offscreen canvases
    // (the video renderer) keep their own size and are never scaled down.
    const PIXEL_BUDGET = 1.4e6

    // Explicit backing size for offscreen hosts (PaperCastStage renders each
    // actor into its own canvas and blits it: sizing that canvas to the real
    // on-screen size removes both the overdraw and the huge blit).
    let fixedSize = null

    function setSize(wpx, hpx) {
      const cw = Math.max(1, Math.round(Number(wpx) || 1))
      const ch = Math.max(1, Math.round(Number(hpx) || 1))
      if (fixedSize && fixedSize[0] === cw && fixedSize[1] === ch) return
      fixedSize = [cw, ch]
      if (canvas.width !== cw || canvas.height !== ch) {
        canvas.width = cw
        canvas.height = ch
      }
      w = cw
      h = ch
      draw(state.time)
    }

    function resize() {
      if (fixedSize) { w = fixedSize[0]; h = fixedSize[1]; return }
      const rect = canvas.getBoundingClientRect()
      const displayed = rect.width > 0 && rect.height > 0
      dpr = Math.min(window.innerWidth < 700 ? 1.25 : 1.75, window.devicePixelRatio || 1)
      let cw = Math.max(1, Math.round((rect.width || canvas.width) * dpr))
      let ch = Math.max(1, Math.round((rect.height || canvas.height) * dpr))
      const px = cw * ch
      // only supersampled (dpr > 1) canvases are capped: a 1080p dpr-1
      // export canvas keeps its exact size
      if (displayed && dpr > 1.001 && px > PIXEL_BUDGET) {
        const k = Math.sqrt(PIXEL_BUDGET / px)
        cw = Math.max(1, Math.round(cw * k))
        ch = Math.max(1, Math.round(ch * k))
      }
      if (canvas.width !== cw || canvas.height !== ch) {
        canvas.width = cw
        canvas.height = ch
      }
      w = cw
      h = ch
    }

    function poseOf(x) {
      if (typeof x === 'string') return POSES[x] || POSES.neutral
      return x ? normalizePose(x) : POSES.neutral
    }

    function clipPose(t) {
      const c = state.clip
      const keys = c.keys || []
      if (!keys.length) return POSES.neutral
      const dur = c.duration || keys[keys.length - 1].at || 1
      let lt = t - (c.at || 0)
      if (lt < 0) lt = 0
      if (c.loop) lt = ((lt % dur) + dur) % dur
      else lt = Math.min(lt, dur)
      if (lt <= keys[0].at) return poseOf(keys[0].pose)
      for (let i = 1; i < keys.length; i++) {
        const a = keys[i - 1], b = keys[i]
        if (lt <= b.at || i === keys.length - 1) {
          const span = Math.max(1, b.at - a.at)
          const raw = clamp((lt - a.at) / span, 0, 1)
          const fn = EASES[b.ease] || easeInOut
          return blendPose(poseOf(a.pose), poseOf(b.pose), fn(raw))
        }
      }
      return poseOf(keys[keys.length - 1].pose)
    }

    function resolvePose(t) {
      if (state.clip) return applyLife(clipPose(t), t)
      let p = state.customPose || POSES[state.pose] || POSES.neutral
      if (state.poseKeys.length) {
        const keys = state.poseKeys.slice().sort((a, b) => (a.at || 0) - (b.at || 0))
        if (t <= (keys[0].at || 0)) p = poseOf(keys[0].pose)
        else {
          for (let i = 0; i < keys.length - 1; i++) {
            const a = keys[i], b = keys[i + 1]
            if (t >= (a.at || 0) && t < (b.at || 0)) {
              p = blendPose(poseOf(a.pose), poseOf(b.pose), easeInOut((t - a.at) / Math.max(1, b.at - a.at)))
              break
            }
            if (i === keys.length - 2) p = poseOf(keys[keys.length - 1].pose)
          }
        }
      }
      if (state.gesture) {
        const g = state.gesture
        const end = g.at + g.duration
        let k = 0
        if (t > g.at - 120 && t < g.at + 120) k = smooth((t - (g.at - 120)) / 240)
        else if (t >= g.at + 120 && t <= end - 180) k = 1
        else if (t > end - 180 && t < end + 120) k = 1 - smooth((t - (end - 180)) / 300)
        if (k > 0) p = blendPose(p, poseOf(g.pose), k)
      }
      return applyLife(p, t)
    }

    // life: breathing, sway, nod (all deterministic functions of t)
    function applyLife(pIn, t) {
      const life = state.life
      let p = pIn
      if (life.on) {
        const s = t / 1000
        const breath = Math.sin(s * 1.42 + state.seed * 0.8) * life.breath
        const sway = Math.sin(s * 0.72 + state.seed) * life.sway
        const nodW = Math.sin(s * 0.55 + 0.7) * life.nod
        p = mix(p, p, 1)
        p.body = Object.assign({}, p.body, {
          x: (p.body.x || 0) + sway * 2.2,
          y: (p.body.y || 0) + breath * 1.7,
          rot: (p.body.rot || 0) + sway * 0.5,
        })
        p.head = Object.assign({}, p.head, {
          tilt: (p.head.tilt || 0) + sway * 1.5,
          turn: (p.head.turn || 0) + Math.sin(s * 0.41 + 1.1) * 0.02,
          nod: (p.head.nod || 0) + nodW * 1.2,
        })
        p.armL = Object.assign({}, p.armL, { hand: [p.armL.hand[0] + sway * 1.4, p.armL.hand[1] + breath * 0.9] })
        p.armR = Object.assign({}, p.armR, { hand: [p.armR.hand[0] - sway * 1.4, p.armR.hand[1] + breath * 0.9] })
      }
      return p
    }

    function visemeAt(t) {
      if (state.phoneme) {
        const v = VISEMES[visemeOf(state.phoneme)]
        return { vis: v, open: v.h / 31, speaking: true }
      }
      if (!state.visemes.length) return { vis: VISEMES.sil, open: 0, speaking: false }
      const lastItem = state.visemes[state.visemes.length - 1]
      const lastAt = lastItem.t !== undefined ? lastItem.t : (lastItem.timeMs || 0)
      if (t > lastAt + (Number(lastItem.dur) || 180) + 100) return { vis: VISEMES.sil, open: 0, speaking: false }
      let cur = state.visemes[0], next = null
      for (let i = 0; i < state.visemes.length; i++) {
        const at = state.visemes[i].t !== undefined ? state.visemes[i].t : state.visemes[i].timeMs
        if (at <= t) { cur = state.visemes[i]; next = state.visemes[i + 1] || null }
        else { next = next || state.visemes[i]; break }
      }
      const curV = VISEMES[cur.viseme] || VISEMES[visemeOf(cur.phoneme)] || VISEMES.sil
      if (!next) return { vis: curV, open: curV.h / 31, speaking: true }
      const nextAt = next.t !== undefined ? next.t : next.timeMs
      const nextV = VISEMES[next.viseme] || VISEMES[visemeOf(next.phoneme)] || VISEMES.sil
      const blend = 65
      const k = nextAt !== null ? smooth((t - (nextAt - blend)) / blend) : 0
      const vis = mix(curV, nextV, k)
      return { vis, open: vis.h / 31, speaking: true }
    }

    function draw(t) {
      resize()
      const c = currentChar()
      const p = resolvePose(t)
      const vv = visemeAt(t)
      state.mouth = vv.vis
      state.speaking = vv.speaking
      const s = t / 1000
      const blinkPeriod = 3600
      const bt = ((t + state.seed * 431) % blinkPeriod + blinkPeriod) % blinkPeriod
      const blink = state.blink ? (bt < 170 ? Math.sin((bt / 170) * Math.PI) : 0) : 0
      if (state.autoGaze) {
        state.gazeX = Math.sin(s * 0.57 + state.seed) * 0.75 + Math.sin(s * 1.7) * 0.18
        state.gazeY = Math.cos(s * 0.44 + state.seed * 0.2) * 0.45
        state.gazeTurn = Math.sin(s * 0.33) * 0.08
      }
      if (blink > 0.9) state.gazeY = 0
      const sk = makeSkeleton(p, state.yaw, c)
      sk.back = state.back
      sk.profile = Math.abs(state.yaw) >= 0.97
      const scale = Math.min(w / 600, h / 900)
      const ox = (w - 600 * scale) / 2
      const oy = (h - 900 * scale) / 2
      ctx.setTransform(scale, 0, 0, scale, ox, oy)
      ctx.clearRect(0, 0, 600, 900)
      ctx.lineJoin = 'round'
      ctx.lineCap = 'round'

      // contact shadow (a cached sprite: ctx.filter blurs cost tens of ms at
      // 1080p, and the shadow is the same soft ellipse on every frame)
      ctx.save()
      ctx.globalAlpha = 0.16
      ctx.drawImage(shadowSprite(), 300 + (p.body.x || 0) * 0.4 - 156, 848 - 30, 312, 60)
      ctx.restore()

      // back layer
      const yawOn = Math.abs(state.yaw) > 0.35
      const farSide = state.yaw > 0 ? 'L' : 'R'
      const thin = c.outfit === 'tee' || c.outfit === 'vest' || c.outfit === 'dress'
      if (!sk.profile && !thin) drawTorsoBack(ctx, sk, c)
      // hanging arms sit behind the torso: the shoulder join disappears
      const armsBehind = { L: false, R: false }
      const spineA = (p.fk && Number(p.fk.spine)) || 0
      if (!yawOn && !sk.profile && Math.abs(spineA) < 4) {
        for (const side of ['L', 'R']) {
          const wr = side === 'L' ? sk.wristL : sk.wristR
          const sh = side === 'L' ? sk.shL : sk.shR
          armsBehind[side] = wr[1] > sh[1] + 20 && (wr[0] < 212 || wr[0] > 388)
          if (armsBehind[side]) {
            // cut the tube at the shirt line: no spike above the shoulder
            ctx.save()
            ctx.beginPath()
            ctx.rect(0, 338, 600, 570)
            ctx.clip()
            drawArm(ctx, sk, side, p, c)
            ctx.restore()
          }
        }
      }
      const legOrder = sk.profile && sk.yaw < 0 ? ['R', 'L'] : ['L', 'R']
      // A leg lifted in front of the body (a raised knee) is drawn after the
      // skirt, so the garment cannot slice through the thigh.
      const lifted = { L: (sk.liftL || 0) > 0.3, R: (sk.liftR || 0) > 0.3 }
      if (sk.profile) { lifted.L = false; lifted.R = false }
      const frontLegs = legOrder.filter((side) => lifted[side])
      const backLegs = legOrder.filter((side) => !lifted[side])
      if (!sk.profile && c.bottom === 'shorts' && c.outfit !== 'dress') drawShortsShell(ctx, sk, c)
      for (const side of backLegs) drawLeg(ctx, sk, side, c, side === legOrder[1])
      const skirtWear = c.outfit === 'dress' || c.bottom === 'skirt'
      if (!skirtWear) drawPelvis(ctx, sk, c)
      if (sk.profile) drawProfileNeck(ctx, sk, p, c)
      // One visible arm in the side view, pinned to the near silhouette edge.
      // The frontal shoulder is ~90 px out to the side, so the limb is
      // projected onto the torso side. It is drawn *under* the torso: the
      // shirt edge cuts the sleeve seam, and no "pillow" shoulder remains.
      let profileArmSk = null
      if (sk.profile) {
        const nearSide = state.yaw > 0 ? 'R' : 'L'
        const otherSide = nearSide === 'L' ? 'R' : 'L'
        // an active far arm wins over a hanging near one, otherwise a wave,
        // a point or a forward gesture would simply disappear in the side view
        const weight = (side) => {
          const sh = sk['sh' + side]
          const wr = sk['wrist' + side]
          return Math.max(0, sh[1] + 40 - wr[1]) + Math.max(0, Math.abs(wr[0] - sh[0]) - 100)
        }
        const near = weight(otherSide) > weight(nearSide) + 30 ? otherSide : nearSide
        const dir = state.yaw > 0 ? 1 : -1
        const edge = state.yaw > 0 ? 350 : 250
        const shKey = near === 'L' ? 'shL' : 'shR'
        const elKey = near === 'L' ? 'elbowL' : 'elbowR'
        const wrKey = near === 'L' ? 'wristL' : 'wristR'
        const s0 = sk[shKey]
        profileArmSk = Object.assign({}, sk, { profileArm: true, armSide: near })
        profileArmSk[shKey] = [edge - dir * 12, s0[1] + 8]
        for (const k of [elKey, wrKey]) {
          const pt = sk[k]
          const out = clamp((pt[0] - s0[0]) * 0.5, 0, 64)
          profileArmSk[k] = [edge + dir * out, pt[1]]
        }
        // A hand at the hip belongs to the body silhouette (drawn under the
        // shirt); a raised or forward hand is in front of it.
        const pwr = profileArmSk[wrKey]
        const del = profileArmSk[elKey]
        profileArmSk.inFront = !(pwr[1] > sk.hipBase[1] - 70 &&
          Math.abs(pwr[0] - edge) < 34 && Math.abs(del[0] - edge) < 34)
        if (!profileArmSk.inFront) drawArm(ctx, profileArmSk, near, p, c)
      }
      drawTorso(ctx, sk, p, c)
      for (const side of frontLegs) drawLeg(ctx, sk, side, c, true)
      // A belt-like cover hides the shirt/pelvis seam on a bent spine. A dress
      // or skirt is continuous at the waist, so the band would cut it in half.
      if (p.fk && Math.abs(p.fk.spine || 0) > 0.5 && !skirtWear) drawWaistCover(ctx, sk, c)
      if (!sk.profile) drawNeck(ctx, sk, c)

      if (profileArmSk) {
        if (profileArmSk.inFront) {
          drawArm(ctx, profileArmSk, profileArmSk.armSide, p, c)
        } else {
          // the hand reads better in front of the hip line
          const near = profileArmSk.armSide
          const wr = profileArmSk[near === 'L' ? 'wristL' : 'wristR']
          const el = profileArmSk[near === 'L' ? 'elbowL' : 'elbowR']
          const upper = near === 'L' ? p.armL : p.armR
          const wf = (p.fk && p.fk[near === 'L' ? 'wristL' : 'wristR']) || 0
          const pron = clamp(Number(upper.handRot) || 0, ANATOMY.forearm.pronation[0], ANATOMY.forearm.pronation[1])
          drawHand(ctx, wr, Math.atan2(wr[1] - el[1], wr[0] - el[0]) + wf * DEG, upper.handPose || 'relaxed', pron * DEG, near, c, false)
        }
      } else if (yawOn) {
        const near = farSide === 'L' ? 'R' : 'L'
        // the far arm stays visible: paper layer over the torso, darker
        drawArm(ctx, sk, farSide, p, c, true)
        drawArm(ctx, sk, near, p, c, false)
      } else if (p.front === 'L') {
        if (!armsBehind.R) drawArm(ctx, sk, 'R', p, c)
        if (!armsBehind.L) drawArm(ctx, sk, 'L', p, c)
      } else {
        if (!armsBehind.L) drawArm(ctx, sk, 'L', p, c)
        if (!armsBehind.R) drawArm(ctx, sk, 'R', p, c)
      }

      // head
      const emoTo = EMOTIONS[state.emotion] || EMOTIONS.neutral
      const emoFrom = EMOTIONS[state.emotionFrom] || emoTo
      const emoK = state.emotionAt > -1e8 ? smooth((state.time - state.emotionAt) / 320) : 1
      state.emoBlend = emoK >= 1 ? emoTo : mix(emoFrom, emoTo, emoK)
      drawHead(ctx, sk, p, c, {
        yaw: state.yaw,
        emoBlend: state.emoBlend,
        emotion: state.emotion,
        mouth: vv.vis,
        speaking: vv.speaking,
        gazeX: state.gazeX,
        gazeY: state.gazeY,
        gazeTurn: state.gazeTurn,
        blink,
      })

      if (state.showSkeleton) drawSkeleton(ctx, sk)
      lastFrame = { pose: p, skeleton: sk, viseme: vv.vis }
    }

    function drawSkeleton(ctx, sk) {
      ctx.save()
      ctx.globalAlpha = 0.82
      ctx.strokeStyle = '#69d6ff'
      ctx.fillStyle = '#69d6ff'
      ctx.lineWidth = 2
      const bones = [
        [sk.hip, sk.neck], [sk.neck, sk.head],
        [sk.shL, sk.elbowL], [sk.elbowL, sk.wristL],
        [sk.shR, sk.elbowR], [sk.elbowR, sk.wristR],
        [sk.hipL, sk.kneeL], [sk.kneeL, sk.ankleL],
        [sk.hipR, sk.kneeR], [sk.kneeR, sk.ankleR],
        [sk.hipL, sk.hipR], [sk.shL, sk.shR],
      ]
      for (const [a, b] of bones) {
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke()
      }
      for (const j of [sk.hip, sk.neck, sk.head, sk.shL, sk.elbowL, sk.wristL, sk.shR, sk.elbowR, sk.wristR, sk.hipL, sk.kneeL, sk.ankleL, sk.hipR, sk.kneeR, sk.ankleR]) {
        ctx.beginPath(); ctx.arc(j[0], j[1], 4, 0, TAU); ctx.fill()
      }
      ctx.restore()
    }

    function seek(t) {
      state.time = Number(t) || 0
      draw(state.time)
    }

    function setPose(name, at) {
      if (!POSES[name]) return false
      state.pose = name
      state.customPose = null
      state.clip = null
      if (at !== undefined) state.time = Number(at) || 0
      draw(state.time)
      return true
    }

    // a full pose object from the studio / a saved preset
    function setPoseObject(pose) {
      state.customPose = pose ? normalizePose(pose) : null
      if (pose) state.clip = null
      draw(state.time)
      return !!state.customPose
    }

    // gesture clip: { id, duration, loop, keys:[{at, pose, ease}] }
    function setClip(clip, at) {
      const c = typeof clip === 'string' ? CLIPS[clip] : clip
      state.clip = c ? JSON.parse(JSON.stringify(c)) : null
      state.clipAt = Number(at) || 0
      if (state.clip) state.clip.at = state.clipAt
      draw(state.time)
      return !!state.clip
    }

    function playClip(id, at) {
      return setClip(id, at !== undefined ? at : state.time)
    }

    function setLife(v) {
      if (v === undefined || v === true) state.life.on = true
      else if (v === false) state.life.on = false
      else if (v && typeof v === 'object') Object.assign(state.life, v)
      draw(state.time)
      return Object.assign({}, state.life)
    }

    function setYaw(v) {
      state.yaw = clamp(Number(v) || 0, -1, 1)
      draw(state.time)
      return state.yaw
    }

    function setBack(on) {
      state.back = !!on
      draw(state.time)
      return state.back
    }

    function setCharacter(name) {
      if (!CHARACTERS[name]) return false
      state.character = name
      palette = Object.assign({}, CHARACTERS[name], normalizeAppearance(state.appearance))
      draw(state.time)
      return true
    }

    function setEmotion(name) {
      const next = EMOTIONS[name] ? name : 'neutral'
      if (next !== state.emotion) {
        state.emotionFrom = state.emotion
        state.emotionAt = state.time
        state.emotion = next
      }
      draw(state.time)
      return state.emotion
    }

    function setAppearance(a) {
      state.appearance = normalizeAppearance(Object.assign({}, state.appearance, a || {}))
      palette = Object.assign({}, CHARACTERS[state.character], state.appearance)
      draw(state.time)
    }

    function setGaze(x, y) {
      state.autoGaze = false
      state.gazeX = clamp(Number(x) || 0, -1, 1)
      state.gazeY = clamp(Number(y) || 0, -1, 1)
      draw(state.time)
    }

    function setPhoneme(id, at) {
      state.phoneme = id && PHONEMES[id] ? id : null
      if (at !== undefined) state.time = Number(at) || 0
      draw(state.time)
    }

    function setVisemes(list) {
      state.visemes = Array.isArray(list) ? list.slice() : []
      state.phoneme = null
      draw(state.time)
    }

    function speak(text, duration, start) {
      const list = visemesFromText(text, duration || 2600, start || state.time)
      state.visemes = list
      state.phoneme = null
      state.speaking = true
      draw(state.time)
      return list
    }

    function playGesture(name, at, duration) {
      if (name === null || name === undefined) {
        state.gesture = null
        draw(state.time)
        return true
      }
      if (!POSES[name]) return false
      state.gesture = { pose: name, at: Number(at !== undefined ? at : state.time), duration: Number(duration) || 1200 }
      draw(state.time)
      return true
    }

    function setPoseKeys(keys) {
      state.poseKeys = Array.isArray(keys) ? keys.slice() : []
      state.clip = null
      draw(state.time)
    }

    function setBlink(on) {
      state.blink = on !== false
      draw(state.time)
    }

    function setSkeleton(on) {
      state.showSkeleton = !!on
      draw(state.time)
    }

    function setAutoGaze(on) {
      state.autoGaze = on !== false
      if (!state.autoGaze) { state.gazeX = 0; state.gazeY = 0; state.gazeTurn = 0 }
      draw(state.time)
    }

    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => draw(state.time)) : null
    if (ro) ro.observe(canvas)
    draw(state.time)

    return {
      ready: Promise.resolve(true),
      seek,
      setPose,
      setSize,
      setPoseObject,
      setClip,
      playClip,
      setLife,
      setYaw,
      setBack,
      setCharacter,
      setEmotion,
      setAppearance,
      setGaze,
      setPhoneme,
      setVisemes,
      speak,
      playGesture,
      setPoseKeys,
      setBlink,
      setSkeleton,
      setAutoGaze,
      getState() {
        return {
          character: state.character,
          pose: state.pose,
          emotion: state.emotion,
          phoneme: state.phoneme,
          visemes: state.visemes.slice(),
          time: state.time,
          yaw: state.yaw,
          back: state.back,
          life: Object.assign({}, state.life),
          customPose: !!state.customPose,
          clip: state.clip ? state.clip.id || 'custom' : null,
          poseCount: Object.keys(POSES).length,
          phonemeCount: Object.keys(PHONEMES).length,
          visemeCount: Object.keys(VISEMES).length,
          lastFrame,
        }
      },
      destroy() {
        if (ro) ro.disconnect()
        ctx.setTransform(1, 0, 0, 1, 0, 0)
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      },
      palette: () => palette,
    }
  }

  window.PaperCast = {
    create,
    RIG,
    CHARACTERS,
    POSES,
    PHONEMES,
    VISEMES,
    EMOTIONS,
    phonemize,
    visemeOf,
    visemesFromText,
    INK,
    PAPER,
    LIMITS,
    JOINT_RANGES,
    jointRangeFor,
    ANATOMY,
    FINGER_CURL,
    PALETTES,
    HAIR_STYLES,
    BEARD_STYLES,
    NOSE_STYLES,
    EYE_STYLES,
    BROW_STYLES,
    LIP_STYLES,
    PATTERNS,
    ACCESSORIES,
    GLASSES_STYLES,
    FACE_SHAPES,
    OUTFITS,
    BOTTOMS,
    normalizeAppearance,
    validateAppearance,
    jointRange,
    clampJoint,
    fingerCurl,
    anatomyReport,
    POSE_SCHEMA,
    normalizePose,
    blendPose,
    EASES,
    CLIPS,
    registerPose,
    registerClip,
    validatePose,
    // A raw partial pose (a preset written by hand, an old save) must not
    // crash a studio: normalise before solving.
    skeleton: (pose, yaw) => {
      const p = typeof pose === 'string'
        ? (POSES[pose] || POSES.neutral)
        : normalizePose(pose || POSES.neutral)
      return makeSkeleton(p, yaw || 0)
    },
    skeleton3D,
    counts: {
      get poses() { return Object.keys(POSES).length },
      get phonemes() { return Object.keys(PHONEMES).length },
      get visemes() { return Object.keys(VISEMES).length },
      get bones() { return RIG.joints.length },
    },
  }
})()
