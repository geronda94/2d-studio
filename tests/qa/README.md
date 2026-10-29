# Paper Cast QA

Repeatable checks for the character system. Runs against a live dev/preview URL.

```bash
npm i -D playwright
npx playwright install chromium
node tests/qa/run.cjs http://localhost:5175
```

Checks:

- `/pose-studio.html`, `/character-builder.html`, `/character-studio.html`
  load with `PaperCast` and no console errors.
- 31 poses are deterministic (same frame on repeated `seek`).
- 9 gesture clips are deterministic (walk is a looping cycle).
- 10 animal kinds are deterministic across their poses.
- `POSE_SCHEMA === 2` and `normalizePose` fills defaults.
- `PaperCastAnimals.skeleton` exposes joints; insect FK moves legs.
- `PaperCast.skeleton3D` projects joints with a real depth axis.
- Studio session (`papercast.session.v1`) is shared by Lab / Pose / Builder:
  character, per-character skins and pose survive page switches.
- Look validators: dress forces the bottom slot, conflicts are reported;
  anatomy ranges/clamps (`elbow 0…150`, `knee ≤135`, `wrist ≤70`).
- Pose Studio: 12 joint handles + 2 hands + 2 rotation rings + 8 finger
  presets; dragging a foot changes the leg, presets change the hand.
- Live sync: a pose change in Builder reaches an open Pose Studio tab
  through `storage` without reload.
- Visual library: 61 preview thumbnails are generated and a click applies
  the outfit (dress also sets the bottom slot).
- 390×844: no horizontal overflow on Pose Studio and Builder.

Exit code 1 on failure. CI: set `CHROMIUM_PATH` if Chromium is not at
`/usr/bin/chromium-browser`.

## Golden frames

`node tests/qa/golden.cjs <url>` renders 11 reference frames (both skins, dress,
jacket, beard, 3/4, profile, spine bend, knee/elbow bend) into 200×300 canvases
and compares them with `golden/*.png`. Up to 1.5 % of the pixels may change;
anything more is a visual regression. Rewrite the references with `--update`
after an intentional art change:

```bash
node tests/qa/golden.cjs http://localhost:5590 --update
```
