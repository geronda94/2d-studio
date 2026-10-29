# 3D / Babylon archive (frozen 2026-10-27)

This folder is a **draft archive**, not production. Nothing here is loaded by
the frontend or referenced by the Paper Cast scenes.

## What is here

- `vendor/`: Babylon, loaders, `babylon-character.js`, `scene-rig.js`,
  `scene-clip.js`.
- `models/`: HD GLBs (`mark-hd.glb`, `mark-hd-mobile.glb`, `avatarsdk-man.glb`,
  `brunette.glb`), custom GLBs and SceneRig manifests.
- `tools/`: old 3D Character Studio, Rig Studio, Object Studio, Clip Editor.
- `scripts/`: old 3D seed/import/build scripts.
- `screenshots/`: old mobile/3D checks.

## Restore

1. Copy the needed files back into `core/public/` at their old paths.
2. For the old Character Studio: `tools/character-studio-3d.html` →
   `core/public/character-studio.html`.
3. Restore the SceneRig loader in `core/src/scenes/SceneHost.vue` and the 3D
   templates in `backend/scene_library.py` from git history.
4. Do not put these assets in the normal production bundle without checking
   licenses and mobile weight.

The current production stack is documented in `docs/CANVAS_CHARACTERS.md`.

> Large models, Babylon binaries and screenshots are intentionally ignored by
> `.gitignore`. They remain on disk; code/tools/scripts are tracked as the draft.
