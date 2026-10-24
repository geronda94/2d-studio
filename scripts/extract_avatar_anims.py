#!/usr/bin/env python3
"""Extract Mixamo/RPM GLB clips into one compact JS asset for the 3D avatar.

The scene iframe cannot fetch(), so the data is wrapped into a classic script
(window.__avatarAnims). We keep:
  * rest hierarchy (T-pose) of the source armature — needed for retargeting;
  * per-clip rotation tracks for every bone;
  * translation tracks only where they actually move (Hips).

    python scripts/extract_avatar_anims.py
"""
import json
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "core" / "public" / "models" / "anim"
DST_JSON = SRC_DIR / "avatar-anims.json"
DST_JS = SRC_DIR / "avatar-anims.js"

CLIPS = [
    "Idle", "Neutral_Idle", "Standing_Idle", "Talking",
    "Standing_Greeting", "Pointing", "Shrugging", "Hard_Head_Nod",
    "Agreeing", "Thinking", "Look_Around", "Strong_Gesture",
    "Standing_Thumbs_Up", "Dismissing_Gesture", "Look_Away_Gesture",
    "Standing_Clap",
]

COMPONENTS = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load_glb(path):
    data = path.read_bytes()
    magic, ver, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, path
    off = 12
    js = None
    binchunk = None
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        off += clen
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            binchunk = chunk
    return js, binchunk


def read_accessor(g, buf, idx):
    acc = g["accessors"][idx]
    bv = g["bufferViews"][acc["bufferView"]]
    fmt, size = COMPONENTS[acc["componentType"]]
    n = NCOMP[acc["type"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or size * n
    out = []
    for i in range(acc["count"]):
        vals = struct.unpack_from("<" + fmt * n, buf, start + i * stride)
        out.append(vals if n > 1 else vals[0])
    return out


def quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ]


def quat_from_euler_xyz(x, y, z):
    import math
    cx, sx = math.cos(x / 2), math.sin(x / 2)
    cy, sy = math.cos(y / 2), math.sin(y / 2)
    cz, sz = math.cos(z / 2), math.sin(z / 2)
    return [sx * cy * cz + cx * sy * sz, cx * sy * cz - sx * cy * sz,
            cx * cy * sz + sx * sy * cz, cx * cy * cz - sx * sy * sz]


def rest_world_positions(rest, order, parent):
    pos = {}
    for name in order:
        t = rest[name]["t"]
        p = parent.get(name)
        if p and p in pos:
            # rotation ignored here: Mixamo rest is axis-aligned per bone; only
            # hips height is needed for scale, which is the root bone.
            pos[name] = [pos[p][i] + t[i] for i in range(3)]
        else:
            pos[name] = list(t)
    return pos


def main():
    clips = {}
    rest = None
    parent = {}
    order = []
    for clip_name in CLIPS:
        path = SRC_DIR / (clip_name + ".glb")
        if not path.exists():
            print("skip missing", path.name)
            continue
        g, buf = load_glb(path)
        names = [n.get("name") or ("node%d" % i) for i, n in enumerate(g["nodes"])]
        if rest is None:
            rest = {}
            for i, n in enumerate(g["nodes"]):
                nm = names[i]
                rest[nm] = {
                    "t": list(n.get("translation", [0, 0, 0])),
                    "q": list(n.get("rotation", [0, 0, 0, 1])),
                    "s": list(n.get("scale", [1, 1, 1])),
                }
                for c in n.get("children", []):
                    parent[names[c]] = nm
            # topological order
            def walk(nm):
                order.append(nm)
                for i, n in enumerate(g["nodes"]):
                    if names[i] == nm:
                        for c in n.get("children", []):
                            walk(names[c])
                        break
            roots = [names[i] for i in g["scenes"][g.get("scene", 0)]["nodes"]]
            for r in roots:
                walk(r)
        dur = 0.0
        tracks = {}
        for a in g.get("animations", []):
            for ch in a["channels"]:
                node = names[ch["target"]["node"]]
                path_ = ch["target"]["path"]
                if path_ == "scale":
                    continue
                s = a["samplers"][ch["sampler"]]
                times = read_accessor(g, buf, s["input"])
                vals = read_accessor(g, buf, s["output"])
                interp = s.get("interpolation", "LINEAR")
                if interp == "CUBICSPLINE":
                    # keep the middle value of each in/out tangents triplet
                    vals = [vals[i] for i in range(1, len(vals), 3)]
                dur = max(dur, times[-1])
                if path_ == "rotation":
                    tracks.setdefault(node, {})["rt"] = [round(x, 4) for x in times]
                    tracks[node]["rot"] = [[round(x, 5) for x in v] for v in vals]
                elif path_ == "translation":
                    if max(abs(v[0] - vals[0][0]) + abs(v[1] - vals[0][1]) + abs(v[2] - vals[0][2]) for v in vals) < 0.0005:
                        continue
                    tracks.setdefault(node, {})["pt"] = [round(x, 4) for x in times]
                    tracks[node]["pos"] = [[round(x, 5) for x in v] for v in vals]
        clips[clip_name] = {"duration": round(dur, 4), "tracks": tracks}
        print(f"{clip_name:22s} {dur:6.2f}s  bones {len(tracks)}")

    # source height: hips rest world Y
    hpos = rest_world_positions(rest, order, parent)
    hips = next((n for n in rest if n.endswith("Hips")), "mixamorig:Hips")
    height = hpos[hips][1]
    out = {
        "hips": hips,
        "root": order[0] if order else "",
        "order": order,
        "parent": parent,
        "rest": rest,
        "height": height,
        "clips": clips,
    }
    DST_JSON.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    DST_JS.write_text("window.__avatarAnims=" + json.dumps(out, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"\n{len(clips)} clips, source hips height {height:.1f} -> {DST_JS.name} {DST_JS.stat().st_size/1048576:.2f} MB")


if __name__ == "__main__":
    main()
