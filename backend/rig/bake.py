"""Bake a SceneClip (*.sclip.json) into a canonical GLB animation.

Body channels only (rotation/translation/scale). Face morph tracks are reported
as unsupported for now; they can be added in the next pass.

The output is a normal glTF 2.0 GLB that Blender and Babylon read without
custom plugins.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

from . import glb as glbmod
from .archetypes import normalize_bone
from .compile import write_glb
from .validate import Report, validate_glb, validate_manifest


def _align4(buf: bytearray) -> None:
    while len(buf) % 4:
        buf.append(0)


def _add_view(doc: dict, buf: bytearray, payload: bytes) -> int:
    _align4(buf)
    offset = len(buf)
    buf.extend(payload)
    views = doc.setdefault("bufferViews", [])
    views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload)})
    return len(views) - 1


def _add_accessor(doc: dict, buf: bytearray, rows: list[tuple[float, ...]],
                  type_name: str, *, bounds: bool = False) -> int:
    n = len(rows[0]) if rows else 0
    payload = b"".join(struct.pack("<" + "f" * n, *row) for row in rows)
    view = _add_view(doc, buf, payload)
    acc = {
        "bufferView": view,
        "componentType": 5126,
        "count": len(rows),
        "type": type_name,
    }
    if bounds and rows:
        acc["min"] = [min(r[i] for r in rows) for i in range(n)]
        acc["max"] = [max(r[i] for r in rows) for i in range(n)]
    accessors = doc.setdefault("accessors", [])
    accessors.append(acc)
    return len(accessors) - 1


def _qslerp(a, b, t):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    d = ax * bx + ay * by + az * bz + aw * bw
    if d < 0:
        bx, by, bz, bw = -bx, -by, -bz, -bw
        d = -d
    if d > 0.9995:
        x, y, z, w = ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t, aw + (bw - aw) * t
    else:
        theta0 = math.acos(max(-1.0, min(1.0, d)))
        theta = theta0 * t
        sin0 = math.sin(theta0)
        s0 = math.sin(theta0 - theta) / sin0
        s1 = math.sin(theta) / sin0
        x = ax * s0 + bx * s1
        y = ay * s0 + by * s1
        z = az * s0 + bz * s1
        w = aw * s0 + bw * s1
    length = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return (x / length, y / length, z / length, w / length)


def _resample(keys: list[tuple[float, tuple[float, ...]]], fps: float,
              duration: float) -> list[tuple[float, tuple[float, ...]]]:
    """Resample sparse keys to a stable 30 fps grid for predictable export."""
    keys = sorted(keys, key=lambda k: k[0])
    if len(keys) < 2:
        return keys
    step = 1.0 / max(1.0, fps)
    times = [i * step for i in range(int(duration / step) + 1)]
    if times[-1] < duration - 1e-6:
        times.append(duration)
    out = []
    j = 0
    for t in times:
        while j + 2 < len(keys) and keys[j + 1][0] <= t:
            j += 1
        a_t, a = keys[j]
        b_t, b = (keys[j + 1] if j + 1 < len(keys) else keys[j])
        if b_t <= a_t:
            out.append((t, a))
            continue
        u = max(0.0, min(1.0, (t - a_t) / (b_t - a_t)))
        if len(a) == 4:
            out.append((t, _qslerp(a, b, u)))
        else:
            out.append((t, tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))))
    return out


def bake_clip(manifest_path: str | Path, clip_path: str | Path,
              out_path: str | Path | None = None, *,
              replace: bool = True, fps: float | None = None) -> tuple[Report, Path]:
    mpath = Path(manifest_path).resolve()
    cpath = Path(clip_path).resolve()
    rep = Report(path=str(mpath), kind="bake")
    data = json.loads(mpath.read_text(encoding="utf-8"))
    if data.get("format") != "scenerig/1":
        rep.error("bake.manifest", "only scenerig/1 is supported")
        return rep, mpath
    clip = json.loads(cpath.read_text(encoding="utf-8"))
    clip_rep = validate_manifest(cpath)
    if not clip_rep.ok:
        rep.children.append(clip_rep)
        rep.error("bake.clip", "clip is invalid; see child report")
        return rep, mpath

    geom = (data.get("geometry") or {}).get("file")
    if not geom:
        rep.error("bake.geometry", "geometry.file is required")
        return rep, mpath
    glb_path = (mpath.parent / geom).resolve()
    if not glb_path.exists():
        rep.error("bake.geometry", f"geometry not found: {glb_path}")
        return rep, mpath
    doc = glbmod.read(glb_path)
    if not doc.animations:
        doc.json.setdefault("animations", [])

    name_to_node: dict[str, int] = {}
    for i, node in enumerate(doc.nodes):
        name = str((node or {}).get("name") or "")
        if name and name not in name_to_node:
            name_to_node[name] = i

    clip_fps = float(fps or clip.get("fps") or 30)
    duration = float(clip.get("duration") or 0)
    tracks = clip.get("tracks") or {}
    bin_data = bytearray(doc.bin or b"")

    samplers: list[dict] = []
    channels: list[dict] = []
    bound = 0
    for bone, chans in tracks.items():
        canon = normalize_bone(bone) or bone
        node_index = name_to_node.get(canon) or name_to_node.get(bone)
        if node_index is None:
            rep.error("bake.bone", f"bone {bone!r} not found in the GLB")
            continue
        for path_name in ("rotation", "translation", "scale"):
            raw = chans.get(path_name) if isinstance(chans, dict) else None
            if not raw:
                continue
            keys: list[tuple[float, tuple[float, ...]]] = []
            for key in raw:
                if not isinstance(key, list) or len(key) < 2:
                    continue
                t = float(key[0])
                val = tuple(float(v) for v in key[1:])
                if path_name == "rotation":
                    if len(val) != 4:
                        continue
                    length = math.sqrt(sum(v * v for v in val)) or 1.0
                    val = tuple(v / length for v in val)
                elif len(val) != 3:
                    continue
                keys.append((t, val))
            if not keys:
                continue
            if not any(abs(k[0]) < 1e-9 for k in keys):
                keys.insert(0, (0.0, keys[0][1]))
            if not any(abs(k[0] - duration) < 1e-6 for k in keys):
                keys.append((duration, keys[-1][1]))
            sampled = _resample(keys, clip_fps, duration)
            input_acc = _add_accessor(doc.json, bin_data,
                                      [(t,) for t, _ in sampled], "SCALAR", bounds=True)
            out_acc = _add_accessor(doc.json, bin_data,
                                    [v for _, v in sampled],
                                    "VEC4" if path_name == "rotation" else "VEC3")
            samplers.append({"input": input_acc, "output": out_acc, "interpolation": "LINEAR"})
            channels.append({
                "sampler": len(samplers) - 1,
                "target": {"node": node_index, "path": path_name},
            })
            bound += 1

    if not channels:
        rep.error("bake.empty", "no body channels were baked")
        return rep, mpath

    anims = doc.json.get("animations") or []
    if replace:
        anims = [a for a in anims if (a.get("name") or "") != str(clip.get("name"))]
    anims.append({"name": str(clip.get("name") or "clip"),
                  "samplers": samplers, "channels": channels})
    doc.json["animations"] = anims
    if bin_data:
        buffers = doc.json.setdefault("buffers", [{"byteLength": 0}])
        buffers[0]["byteLength"] = len(bin_data)

    if clip.get("face"):
        rep.warn("bake.face", "face morph tracks are not baked yet; body channels only")

    out = Path(out_path).resolve() if out_path else glb_path.with_name(
        f"{glb_path.stem}.{clip.get('name') or 'clip'}.glb")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(write_glb(doc.json, bytes(bin_data)))

    rep.facts.update({
        "clip": clip.get("name"),
        "channels": bound,
        "duration": duration,
        "output": str(out),
        "size": out.stat().st_size,
    })
    sub = validate_glb(out, None, require_rig=True)
    rep.children.append(sub)
    if not sub.ok:
        rep.error("bake.validation", "baked GLB failed validation; see child report")
    return rep, out
