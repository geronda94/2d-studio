# CANVAS CHARACTERS — Paper Cast 2D / 2.5D

Статус: **production (2026-10-27)**. 3D/Babylon заморожен и вынесен в
`drafts/3d/`. Персонажи сцен — Canvas 2D с общим скелетом.

## 1. Что это

`core/public/vendor/paper-cast.js` — детерминированный 2D-риг «бумажные
человечки». Один скелет, разные скины. Никакого WebGL, Babylon, GLB,
`requestAnimationFrame` или внутренних часов: кадр — чистая функция от `t`.

```
PaperCast.create(canvas, opts) -> {
  ready, seek(t), setPose, setPoseObject, setCharacter, setEmotion,
  setAppearance, setGaze, setPhoneme, setVisemes, speak, playGesture,
  setPoseKeys, setClip, playClip, setLife, setYaw, setBlink, setSkeleton,
  setAutoGaze, destroy, getState
}

PaperCast.registerPose(name, pose)   // пресет из Pose Studio
PaperCast.registerClip(id, clip)     // клип жеста
PaperCast.CLIPS                      // библиотека клипов
PaperCast.validatePose(pose|name)    // { ok, issues[] } по LIMITS
PaperCast.skeleton(pose, yaw)        // скелет кадра без отрисовки
PaperCast.LIMITS                     // диапазоны суставов
```

Сцена обязана вызывать `rig.seek(t)` из `window.scene.seek(t)`.

## 2. Скелет и скины

- 15 узлов: таз, шея, голова, плечи, локти, запястья, бёдра, колени, стопы.
- 2 сегмента рук и ног в скелете; руки решаются 2-bone IK по цели кисти.
  Рисуются конечности одной трубой `limb` (см. §7.7), а не набором конусов.
- `RIG` — единые длины и координаты для всех персонажей.
- Таз сведён к `hipL/hipR = 272/328`; промежность закрывает V-шов
  (`drawPantsGap`, до 664 px), поэтому ноги читаются как брюки.
- `CHARACTERS.mark` / `CHARACTERS.mira` — только палитра, причёска, борода,
  очки, пропорции. Кости не меняются.
- `setAppearance({ skin, hair, shirt, pants, shoes, accent, ... })`
  перекрашивает активный скин; поза и скелет остаются общими.

## 3. Позы и жесты

31 статичная поза в `PaperCast.POSES`:

`neutral, wave, point, explain, shrug, think, thumbsUp, ok, stop, cheer,
crossArms, handsOnHips, facepalm, salute, bow, leanIn, clap, count, present,
heart, fist, peace, chin, openPalms, tapFoot, nod, headShake, listen, shush,
armsWide, lowPresent`

- `setPose(name)` — статичная поза.
- `playGesture(name, at, duration)` — переход к позе и обратно на таймлайне.
- `setPoseKeys([{ at, pose }, ...])` — детерминированная интерполяция поз.
- Дыхание, покачивание, моргание и взгляд добавляются поверх позы.

## 4. Фонемы и липсинк

Инвентарь: **82 фонемы** — 42 русские + 39 английских ARPAbet + `sil`.
Они сведены к **18 формам рта** (`VISEMES`).

```js
rig.setPhoneme('AA')             // одна фонема
rig.setVisemes([{ t: 0, viseme: 'MBP' }, ...])
rig.speak('Привет, это липсинк', 2600, 0)
PaperCast.phonemize('Привет')    // приблизительная текстовая раскладка
PaperCast.visemesFromText(text, duration, start)
```

`speak()` раскладывает фонемы по времени и возвращает массив визёмов.
Русская раскладка учитывает `ь` (палатализация), `е/ё/ю/я`, диграфы
`дж/дз/тс`; английская — базовые диграфы. Это не фонетический словарь, а
детерминированная аппроксимация для анимации.

## 4.4. Внешность и гардероб

`setAppearance` принимает поверх скина:

- лицо: `headScale`, `eyeSize`, `eyeGap`, `mouthW`;
- тело: `shoulderW`, `hipW`, `armLen`, `legLen` (ноги поднимают таз, кисти
  смещаются вместе с корпусом, стопы остаются на полу);
- волосы: `hairStyle` = `short | bob | bun | ponytail | bald`;
- аксессуары: `headwear` = `cap | beanie`, `glasses`, `scarf`, `capColor`,
  `scarfColor`;
- одежда: `outfit` = `shirt | tee | hoodie | coat | dress`,
  `bottom` = `pants | shorts | skirt`, `sleeves` = `short | long | auto`,
  `coatColor`, `skirtColor`;
- цвета: `skin`, `hair`, `shirt`, `pants`, `shoes`, `accent`.

`auto`-рукав: пальто/худи/платье — длинный, футболка — короткий, рубашка —
по причёске (bob → длинный). Брюки/шорты/юбка меняют и ноги: шорты и юбка
рисуют кожу ниже линии, брюки — ткань.

## 4.4.1. Сцена из конфига

`paper-cast-stage.js` — окружение + каст + тайминги: `pose`, `clip`,
`gesture`, `speak`, `visemes`, `emotion`, `turn`, `lookAt`, `blink`,
субтитры. Шаблон `paper-director`, демо `director-demo.html`, `/p/13`.
Подробно: `docs/PAPERCAST_DIRECTOR.md`.

## 4.5. Животные

`core/public/vendor/paper-cast-animals.js` — отдельный риг, общий стиль:

```
PaperCastAnimals.create(canvas, { kind: 'dog', pose: 'sit', gait: 'walk' })
  -> { seek, setKind, setPose, setGait, setPalette, setSkeleton, getState }
```

- quadruped: пёс, кот, свинья, корова; avian: курица, голубь, орёл, синица;
  insectoid: жук, пчела;
- позы: stand/sit/lie/bark/wag (четвероногие), stand/peck/flap (птицы),
  stand/fly (насекомые);
- походки: walk/run/fly; `setSkeleton(true)` показывает кости;
- **кости животных** (`setFK`): четвероногие — `head, neck, tail, fl/fr/bl/br
  + Hip/Knee`; птицы — `head, neck, wing`; насекомые — `head, neck` и
  `l1..l6 + Hip/Knee` (пары ног); слайдеры в Character Builder,
  «Сбросить кости»;
- `PaperCastAnimals.skeleton(kind, pose, t, gait, seed, fk)` — позиции
  суставов для инструментов; в Builder при «скелет» появляются точки,
  которые тянутся (голова/хвост/колени/стопы/крыло). У насекомых точки
  сгруппированы по парам ног: одна точка вращает обе ноги пары, тонкая
  настройка — слайдерами;
- сцена грузит файл, если в JS есть `PaperCastAnimals` (SceneHost).

## 4.5.1. Анатомия и библиотеки внешности

- `docs/ANATOMY_RIG.md` — ROM-таблицы и перенос на животных;
  `PaperCast.ANATOMY`, `jointRange(joint, axis)`, `clampJoint`,
  `anatomyReport(pose)`, `FINGER_CURL` / `fingerCurl(0..1)`.
- `PaperCast.LIMITS` выведены из анатомии: локоть 0…150, колено 0…135,
  запястье −80…70, бедро −30…45 (отведение), стопа −50…20.
- `PaperCast.PALETTES` (skin/hair/fabric/accent) и списки стилей:
  `HAIR_STYLES`, `BEARD_STYLES`, `NOSE_STYLES`, `EYE_STYLES`,
  `BROW_STYLES`, `LIP_STYLES`, `PATTERNS` (solid/stripes/check/dots),
  `ACCESSORIES` (tie/bowtie/necklace/badge), `GLASSES_STYLES`,
  `OUTFITS` (shirt/tee/hoodie/sweater/jacket/vest/coat/dress), `BOTTOMS`.
- `normalizeAppearance(a)` / `validateAppearance(a)` — единые правила
  слоёв: платье задаёт низ, футболка не бывает с длинным рукавом,
  пальто+шорты конфликтуют. `create` и `setAppearance` нормализуют сами,
  Builder показывает предупреждение.
- Локоть IK: из двух решений берётся анатомически нижнее (под плечом —
  наружное), поэтому рука не складывается через грудь.
- Пронация — `armX.handRot` (−90…90), не путать с `fk.wrist`
  (сгибание −80…70).
- Моргание рисуется внутри глаза и учитывает yaw/eyeSize/eyeGap.

## 4.6. Позы, лимиты и 2.5D

- `LIMITS` — диапазоны body/head/arm/leg; `makeSkeleton` клэмпит их на
  отрисовке, `validatePose` возвращает нарушения списком.
- Минимальная дистанция кисти от плеча — `LIMITS.arm.reachMin` (34 px):
  локоть не складывается в точку.
- `setPoseObject(pose)` — произвольная поза без регистрации (студия).
- `setPoseKeys` принимает и имена, и объекты поз.
- `setLife({on, breath, sway, nod})` — амплитуды дыхания/качания.
- Клип: `{ id, duration, loop, keys:[{at, pose, ease}] }`; `ease` —
  `linear/in/out/inOut/backIn/backOut/expoOut`, применяется к сегменту,
  который заканчивается на ключе. `playClip(id, at)` ставит клип на
  таймлайн, `setPoseKeys`/`setPose` его сбрасывают.
- **Одежда следует за конечностями**: `sk.liftL/liftR` — насколько стопа
  оторвана от пола (0…1). Подол платья/юбки поднимается и расходится на
  стороне поднятой ноги, складки тянутся к колену; поднятая нога рисуется
  **после** юбки, поэтому не режется ею. Шорты получили оболочку таза
  (иначе поднятые колени открывали промежность), их подол — полоса,
  перпендикулярная бедру. Рукав при согнутом локте сохраняет непрерывность
  (диск ткани на сгибе).
- **Свободные кости** (`pose.fk`): `spine, neck, head, shL/R, elbowL/R,
  wristL/R, hipL/R, kneeL/R, ankleL/R` — градусы поверх IK-позы; лимиты
  `LIMITS.fk`. В Pose Studio панель «Кости (FK)» + режим «кости»: точки на
  всех суставах, перетаскивание вращает родительскую кость; кнопка
  «Сбросить кости».
- `setYaw(-1..1)` — 3/4 и профиль: при |yaw| ≥ 0.97 рисуется боковой
  набор (голова, торс, одна рука, ноги, шея). Одна видимая рука
  проецируется на боковой силуэт и уходит под торс, когда опущена; жест
  (wave/point/think/explain) рисуется поверх, и берётся та рука, которой
  жест сделан. Шея висит от воротника, стопа разворачивается носком в
  сторону поворота. До 0.97 корпус и бёдра
  сужаются вместе с головой
  (`profileNarrow`), голова поворачивается (сдвиг черт, сужение
  дальнего глаза, скрытие дальнего уха, тень на дальней стороне), дальняя
  рука уходит за торс и темнеет. Есть экспериментальная ветка
  `profileHead` (|yaw| ≥ 0.9): боковая голова и сужение корпуса. В Builder
  она не включена — набор профиля уже включается на краях yaw.
  Полноценные 360° на плоских слоях не планируются
  (см. `docs/PAPERCAST_ROADMAP.md`).
- `setBack(true)` — вид со спины: затылок без лица, спинной шов, без
  пуговиц/карманов/шарфа; `skeleton3D(pose, angle)` — те же суставы в
  ортопроекции `[x, y, z]` (турнтейбл, `rig3d.html`).

## 5. Студии

- Мобильный вид Pose Studio: липкая сцена сверху (при скролле сжимается до
  превью 24dvh), транспорт в две строки, панели в порядке персонаж → жесты →
  лимиты → поза, длинные панели свёрнуты, ручки кистей 40 px, кнопка ⛶
  разворачивает сцену на 74dvh. Проверено на 360×740, 390×844, 430×932 и
  844×390 (landscape: сцена не липкая).
- `http://localhost:5175/character-builder.html` — конструктор персонажа:
  человек/животное, `headScale/eyeSize/eyeGap/mouthW`, причёски
  short/bob/bun/ponytail/bald, `shoulderW/hipW/armLen/legLen`,
  `outfit` (shirt/tee/hoodie/coat/dress),
  `bottom` (pants/shorts/skirt), `sleeves` (auto/short/long), палитры,
  пресеты и экспорт. Животные: пёс/кот/курица/голубь, позы и шаг/бег.
- Таймлайн в Pose Studio: ключи `{at, pose, ease}`, длительность, дорожка
  с маркерами, «взять/снять», Play; экспорт как clip.
- Все 12 суставов видны сразу; кисти и стопы тянутся (стопа — через
  2-bone IK), плечи/бёдра/шея/голова вращают родителя; кольцо у кисти —
  пронация, панель «Пальцы» — 8 форм; двойной клик сбрасывает точку.
- `http://localhost:5175/pose-studio.html` — авторская студия поз:
  перетаскивание кистей, слайдеры, лимиты, пресеты (localStorage),
  библиотека клипов (8 жестов), A→B с ping-pong/циклом, scrub, экспорт
  JSON и JS (`registerPose`/`registerClip`) для сцены.
- `http://localhost:5175/rig3d.html` — 3D-вид рига (турнтейбл):
  орбита/наклон камеры, поворот персонажа 0–360°, глубина, фас/спина,
  скелет в ортопроекции и экспорт `skeleton3D`/сцены. Арт — билборд,
  сбоку он приглушается: плоский риг сбоку показывает, что профиля нет
  (см. `docs/PAPERCAST_ROADMAP.md`, M6).
- **Общая сессия студий** `core/public/vendor/paper-cast-session.js`
  (ключ `papercast.session.v1`): активный персонаж, скины обоих персонажей
  (`skins.mark` / `skins.mira`), поза, yaw и режим/животное Builder.
  Lab, Pose Studio, Builder и 3D-вид читают сессию при открытии и пишут
  при изменениях; `?char=mira` в URL перекрывает сохранённого персонажа.
  Скин применяется только к своему персонажу (`appearanceChar`/`skins`),
  поэтому переключение Mark ↔ Mira не смешивает цвета и причёски.
  Живая синхронизация: запись помечается `_by`, другие вкладки получают
  `storage`-событие и применяют персонажа/скин/позу/yaw без reload;
  свои записи и одинаковые payload'ы игнорируются. Верхнее меню студий
  работает как вкладки: текущая подсвечена.
- `http://localhost:5175/character-studio.html`

- два скина на одном риге;
- 31 кнопка поз, 8 эмоций;
- переключатель RU / EN / ALL и все 82 фонемы;
- ввод текста → `speak()`, таймлайн, скорость, loop;
- цвета кожи/верха/волос, скелет, моргание, взгляд;
- копирование конфига сцены в JSON.

## 6. Сцена

Шаблон: `character-paper-duo` (`backend/scene_library.py`).
Демо: `/p/12`, пересев:

```bash
docker compose exec -T backend python scripts/seed_paper_duo.py
```

Объект библиотеки: `character-paper`; карточки персонажей:
`character-paper-mark`, `character-paper-mira`.

Хост загружает `paper-cast.js` только если JS сцены содержит
`PaperCast` / `paper-cast` / `obj-paper`.

## 7. Правила

1. Никакого `requestAnimationFrame`, `Date.now`, `performance.now` в сцене;
   только `seek(t)`.
2. Не менять скелет под одного персонажа — добавлять скин/палитру.
3. Рот — только `setPhoneme` / `setVisemes` / `speak`, не `Math.sin`.
4. Сцена должна работать в 16:9 и 9:16: карточки стекаются в portrait.
5. Не возвращать Babylon/GLB в `core/public`: 3D лежит в `drafts/3d/`.
6. `seek(t)` детерминирован: 31 поза × 2 скина проходят проверку
   «после цикла поз вернуться в neutral» и не текут `ctx.save/restore`.
7. Позы и жесты не хардкодить в сцене: собирать в Pose Studio, сохранять
   пресетом и регистрировать `PaperCast.registerPose`. Пресет обязан
   проходить `PaperCast.validatePose` без issues.
8. Конечности не собираются из конусов: рука и нога рисуются одной
   непрерывной трубой `limb(ctx, pts, radii, …)` по polyline
   плечо→локоть→запястье / бедро→колено→щиколотка, с круглыми caps.
   Сегментированные `tapered`-сегменты и joint-диски для рук/ног
   запрещены: на стыках видны конусы. `tapered` остаётся только для шеи.

## 7.5. Дальше

Пропорции тела/лица, гардероб, зоопарк скелетов (quadruped/avian/insectoid),
профиль 2.5D — план и статусы в `docs/PAPERCAST_ROADMAP.md`.

## 8. 3D archive

Всё 3D (Babylon, GLB, SceneRig, Rig/Object/Clip Studio, старые скрипты)
перенесено в `drafts/3d/`. Это черновик, не production. Восстановление — см.
`drafts/3d/README.md`.
