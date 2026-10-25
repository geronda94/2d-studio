"""Minimal stdlib glTF/GLB reader for rig validation.

No third-party dependencies. Reads the JSON and BIN chunks, accessors, node
hierarchy and world transforms. Supports .glb and .gltf with external or
data-URI buffers.
"""
from __future__ import annotations

import base64
import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

COMPONENT = {
    5120: ("b", 1, 127.0),
    5121: ("B", 1, 255.0),
    5122: ("h", 2, 32767.0),
    5123: ("H", 2, 65535.0),
    5125: ("I", 4, 4294967295.0),
    5126: ("f", 4, None),
}

TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


class GLBError(Exception):
    pass


@dataclass
class GLTF:
    path: Path
    json: dict[str, Any]
    bin: bytes = b""
    buffers: list[bytes] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def asset_version(self) -> str:
        return str((self.json.get("asset") or {}).get("version") or "")

    @property
    def nodes(self) -> list[dict]:
        return self.json.get("nodes") or []

    @property
    def meshes(self) -> list[dict]:
        return self.json.get("meshes") or []

    @property
    def skins(self) -> list[dict]:
        return self.json.get("skins") or []

    @property
    def animations(self) -> list[dict]:
        return self.json.get("animations") or []

    def buffer(self, index: int) -> bytes:
        if 0 <= index < len(self.buffers):
            return self.buffers[index]
        return b""


def _decode_uri(uri: str, base: Path) -> bytes:
    if uri.startswith("data:"):
        head, _, payload = uri.partition(",")
        if ";base64" in head:
            return base64.b64decode(payload)
        return payload.encode("utf-8")
    p = (base / uri).resolve()
    try:
        return p.read_bytes()
    except OSError as exc:
        raise GLBError(f"cannot read buffer {uri!r}: {exc}") from exc


def read_gltf(path: str | Path) -> GLTF:
    """Read a .gltf (JSON + buffers) file."""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GLBError(f"cannot read glTF {p}: {exc}") from exc
    buffers: list[bytes] = []
    for buf in data.get("buffers") or []:
        uri = buf.get("uri")
        if uri:
            buffers.append(_decode_uri(uri, p.parent))
        else:
            buffers.append(b"")
    return GLTF(path=p, json=data, buffers=buffers)


def read_glb(path: str | Path) -> GLTF:
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise GLBError(f"cannot read {p}: {exc}") from exc
    if len(raw) < 12:
        raise GLBError("file is shorter than a GLB header")
    magic, version, length = struct.unpack_from("<III", raw, 0)
    if magic != GLB_MAGIC:
        raise GLBError("not a GLB file (bad magic)")
    if version != 2:
        raise GLBError(f"unsupported GLB version {version}")
    if length != len(raw):
        raise GLBError(f"GLB length mismatch: header {length}, file {len(raw)}")

    chunks: list[tuple[int, bytes]] = []
    off = 12
    while off + 8 <= len(raw):
        clen, ctype = struct.unpack_from("<II", raw, off)
        off += 8
        if off + clen > len(raw):
            raise GLBError("chunk extends past the end of the file")
        chunks.append((ctype, raw[off:off + clen]))
        off += clen
    if off != len(raw):
        raise GLBError("trailing bytes after the last GLB chunk")

    json_chunk = next((d for t, d in chunks if t == CHUNK_JSON), None)
    if not json_chunk:
        raise GLBError("GLB has no JSON chunk")
    try:
        doc = json.loads(json_chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GLBError(f"invalid GLB JSON: {exc}") from exc

    bin_chunk = next((d for t, d in chunks if t == CHUNK_BIN), b"")
    buffers: list[bytes] = []
    for i, buf in enumerate(doc.get("buffers") or []):
        uri = buf.get("uri")
        if uri:
            buffers.append(_decode_uri(uri, p.parent))
        elif i == 0:
            buffers.append(bin_chunk)
        else:
            buffers.append(b"")
    return GLTF(path=p, json=doc, bin=bin_chunk, buffers=buffers)


def read(path: str | Path) -> GLTF:
    p = Path(path)
    if p.suffix.lower() == ".gltf":
        return read_gltf(p)
    return read_glb(p)


# ── accessors ───────────────────────────────────────────────────────────────

def accessor_info(gltf: GLTF, index: int) -> dict:
    accs = gltf.json.get("accessors") or []
    if not (0 <= index < len(accs)):
        raise GLBError(f"accessor {index} does not exist")
    return accs[index]


def read_accessor(gltf: GLTF, index: int, limit: int | None = None) -> list[tuple[float, ...]]:
    """Decode an accessor into rows of floats.

    Integer components are normalised like glTF requires. Sparse accessors are
    not expanded (returns an empty list; the validator reports a warning).
    """
    acc = accessor_info(gltf, index)
    if acc.get("sparse"):
        return []
    comp = acc.get("componentType")
    if comp not in COMPONENT:
        raise GLBError(f"accessor {index}: unknown componentType {comp}")
    fmt, csize, norm = COMPONENT[comp]
    ncomp = TYPE_COMPONENTS.get(acc.get("type"))
    if not ncomp:
        raise GLBError(f"accessor {index}: unknown type {acc.get('type')}")
    count = int(acc.get("count") or 0)
    if limit is not None:
        count = min(count, limit)

    bv_index = acc.get("bufferView")
    if bv_index is None:
        return [tuple([0.0] * ncomp) for _ in range(count)]

    views = gltf.json.get("bufferViews") or []
    if not (0 <= bv_index < len(views)):
        raise GLBError(f"accessor {index}: bufferView {bv_index} does not exist")
    bv = views[bv_index]
    buf = gltf.buffer(int(bv.get("buffer") or 0))
    base = int(bv.get("byteOffset") or 0) + int(acc.get("byteOffset") or 0)
    stride = int(bv.get("byteStride") or 0) or (csize * ncomp)
    out: list[tuple[float, ...]] = []
    for i in range(count):
        start = base + i * stride
        if start + csize * ncomp > len(buf):
            break
        vals = struct.unpack_from("<" + fmt * ncomp, buf, start)
        if acc.get("normalized") and norm is not None and comp != 5126:
            if comp in (5120, 5122):
                vals = tuple(max(v / norm, -1.0) for v in vals)
            else:
                vals = tuple(v / norm for v in vals)
        out.append(tuple(float(v) for v in vals))
    return out


def accessor_scalar_values(gltf: GLTF, index: int) -> list[float]:
    rows = read_accessor(gltf, index)
    return [r[0] for r in rows if r]


# ── node hierarchy and transforms ───────────────────────────────────────────

def mat4_identity() -> list[float]:
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def mat4_mul(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * 16
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
    return out


def mat4_from_quat(q: list[float]) -> list[float]:
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [
        1 - 2 * (yy + zz), 2 * (xy + wz), 2 * (xz - wy), 0,
        2 * (xy - wz), 1 - 2 * (xx + zz), 2 * (yz + wx), 0,
        2 * (xz + wy), 2 * (yz - wx), 1 - 2 * (xx + yy), 0,
        0, 0, 0, 1,
    ]


def node_local_matrix(node: dict) -> list[float]:
    if "matrix" in node and len(node["matrix"]) == 16:
        return [float(v) for v in node["matrix"]]
    t = [float(v) for v in (node.get("translation") or [0, 0, 0])]
    q = [float(v) for v in (node.get("rotation") or [0, 0, 0, 1])]
    s = [float(v) for v in (node.get("scale") or [1, 1, 1])]
    m = mat4_from_quat(q)
    for c in range(3):
        for r in range(3):
            m[c * 4 + r] *= s[c]
    m[12], m[13], m[14] = t[0], t[1], t[2]
    return m


def node_world_matrices(gltf: GLTF) -> dict[int, list[float]]:
    nodes = gltf.nodes
    parents: dict[int, int] = {}
    for i, node in enumerate(nodes):
        for child in node.get("children") or []:
            parents[int(child)] = i
    cache: dict[int, list[float]] = {}

    def world(i: int) -> list[float]:
        if i in cache:
            return cache[i]
        local = node_local_matrix(nodes[i])
        p = parents.get(i)
        m = local if p is None else mat4_mul(world(p), local)
        cache[i] = m
        return m

    for i in range(len(nodes)):
        world(i)
    return cache


def transform_point(m: list[float], p: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = p
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


def joint_world_positions(gltf: GLTF) -> dict[int, tuple[float, float, float]]:
    mats = node_world_matrices(gltf)
    return {i: (m[12], m[13], m[14]) for i, m in mats.items()}


# ── model facts ─────────────────────────────────────────────────────────────

def skin_joint_indices(gltf: GLTF) -> list[int]:
    out: list[int] = []
    for skin in gltf.skins:
        for j in skin.get("joints") or []:
            j = int(j)
            if j not in out:
                out.append(j)
    return out


def joint_names(gltf: GLTF) -> list[str]:
    nodes = gltf.nodes
    return [str((nodes[i] or {}).get("name") or f"node_{i}") for i in skin_joint_indices(gltf)]


def morph_target_names(gltf: GLTF) -> list[str]:
    names: list[str] = []
    for mesh in gltf.meshes:
        extras = mesh.get("extras") or {}
        for name in extras.get("targetNames") or []:
            n = str(name)
            if n not in names:
                names.append(n)
        for prim in mesh.get("primitives") or []:
            if not (mesh.get("extras") or {}).get("targetNames"):
                # Unnamed morph targets: synthesise stable names.
                for k in range(len(prim.get("targets") or [])):
                    n = f"target_{k}"
                    if n not in names:
                        names.append(n)
    return names


def primitive_attributes(gltf: GLTF) -> list[dict]:
    out: list[dict] = []
    for mi, mesh in enumerate(gltf.meshes):
        for pi, prim in enumerate(mesh.get("primitives") or []):
            out.append({"mesh": mi, "primitive": pi, "attributes": prim.get("attributes") or {},
                        "material": prim.get("material"), "targets": prim.get("targets") or []})
    return out


def triangle_count(gltf: GLTF) -> int:
    total = 0
    for prim in primitive_attributes(gltf):
        indices = (gltf.meshes[prim["mesh"]].get("primitives") or [])[prim["primitive"]].get("indices")
        if indices is not None:
            try:
                total += len(read_accessor(gltf, int(indices))) // 3
            except GLBError:
                pass
        else:
            pos = prim["attributes"].get("POSITION")
            if pos is not None:
                try:
                    total += len(read_accessor(gltf, int(pos))) // 3
                except GLBError:
                    pass
    return total


def position_bounds(gltf: GLTF) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    lo = [math.inf, math.inf, math.inf]
    hi = [-math.inf, -math.inf, -math.inf]
    found = False
    for prim in primitive_attributes(gltf):
        idx = prim["attributes"].get("POSITION")
        if idx is None:
            continue
        acc = accessor_info(gltf, int(idx))
        mn, mx = acc.get("min"), acc.get("max")
        if isinstance(mn, list) and isinstance(mx, list) and len(mn) >= 3 and len(mx) >= 3:
            for k in range(3):
                lo[k] = min(lo[k], float(mn[k]))
                hi[k] = max(hi[k], float(mx[k]))
            found = True
    if not found:
        return None
    return (lo[0], lo[1], lo[2]), (hi[0], hi[1], hi[2])


def texture_count(gltf: GLTF) -> int:
    return len(gltf.json.get("textures") or [])


def material_count(gltf: GLTF) -> int:
    return len(gltf.json.get("materials") or [])


def animation_info(gltf: GLTF) -> list[dict]:
    out: list[dict] = []
    for ai, anim in enumerate(gltf.animations):
        channels = anim.get("channels") or []
        samplers = anim.get("samplers") or []
        duration = 0.0
        targets: set[int] = set()
        paths: set[str] = set()
        keys: list[int] = []
        for ch in channels:
            target = ch.get("target") or {}
            node = target.get("node")
            if node is not None:
                targets.add(int(node))
            path = target.get("path")
            if path:
                paths.add(str(path))
            sampler_idx = ch.get("sampler")
            if sampler_idx is None or not (0 <= int(sampler_idx) < len(samplers)):
                continue
            sampler = samplers[int(sampler_idx)]
            inp = sampler.get("input")
            if inp is None:
                continue
            try:
                times = accessor_scalar_values(gltf, int(inp))
            except GLBError:
                continue
            if times:
                duration = max(duration, max(times))
                keys.append(len(times))
        out.append({
            "index": ai,
            "name": anim.get("name") or f"anim_{ai}",
            "channels": len(channels),
            "targets": sorted(targets),
            "paths": sorted(paths),
            "duration": duration,
            "min_keys": min(keys) if keys else 0,
            "max_keys": max(keys) if keys else 0,
        })
    return out
