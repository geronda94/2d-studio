"""SceneRig polygonal character generator v2.

Run:
    blender --background --python scripts/blender/make_poly_characters_v2.py

Then export each .blend with scripts/blender/scene_rig_export.py.

The characters are original CC0 low-poly humans built from lofted meshes:
gender-shaped torso, tapered limbs, hands with fingers, a shaped head,
separate eyebrows/eyes/nose/lips, several hair styles and a small wardrobe.
All meshes are weighted to the canonical 25-bone SceneRig skeleton.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "characters" / "src"
SRC.mkdir(parents=True, exist_ok=True)
TAU = math.pi * 2


# ── materials ───────────────────────────────────────────────────────────────

def material(name, color, roughness=0.75, metallic=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m


def apply_common(obj, mat=None, smooth=True):
    if mat:
        obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = smooth
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def add_sphere(name, loc, scale, mat, segments=20, rings=14, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_common(obj, mat, smooth)
    return obj


def add_box(name, loc, scale, mat, bevel=0.0, smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_common(obj, mat, smooth)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2 if smooth else 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def add_torus(name, loc, major, minor, mat, rotation=(math.pi / 2, 0, 0), smooth=True):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=24, minor_segments=8,
                                     location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply_common(obj, mat, smooth)
    return obj


def mesh_object(name, verts, faces, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], faces)
    me.update(calc_edges=True)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = smooth
    return obj


# ── geometry ────────────────────────────────────────────────────────────────

def loft(name, rings, mat, segments=20, smooth=True, cap=True):
    """Vertical elliptical loft.

    ring = (z, rx, ry_front, ry_back, y_offset)
    Front is -Y (the character faces -Y in Blender).
    """
    verts, faces = [], []
    for z, rx, ryf, ryb, yo in rings:
        for i in range(segments):
            a = TAU * i / segments
            x = math.cos(a) * rx
            s = math.sin(a)
            ry = ryf if s < 0 else ryb
            verts.append((x, yo + s * ry, z))
    nr = len(rings)
    for r in range(nr - 1):
        for i in range(segments):
            j = (i + 1) % segments
            a = r * segments + i
            b = r * segments + j
            c = (r + 1) * segments + j
            d = (r + 1) * segments + i
            faces.append((a, b, c, d))
    if cap:
        bottom = len(verts); verts.append((0, rings[0][4], rings[0][0]))
        top = len(verts); verts.append((0, rings[-1][4], rings[-1][0]))
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((bottom, j, i))
            faces.append((top, (nr - 1) * segments + i, (nr - 1) * segments + j))
    return mesh_object(name, verts, faces, mat, smooth)


def tube(name, pts, radii, mat, sides=12, depth=1.0, smooth=True, cap=True,
         weights=None):
    """Tube through points with per-point radii.

    weights: list of dicts; a ring's vertices get those vertex groups.
    """
    pts = [Vector(p) for p in pts]
    if len(pts) < 2:
        return None
    verts, faces, ring_weights = [], [], []
    prev_u = None
    for k, p in enumerate(pts):
        if k == 0:
            tangent = (pts[1] - pts[0]).normalized()
        elif k == len(pts) - 1:
            tangent = (pts[-1] - pts[-2]).normalized()
        else:
            tangent = ((pts[k + 1] - pts[k]).normalized() +
                       (pts[k] - pts[k - 1]).normalized()).normalized()
        ref = Vector((0, 0, 1))
        if abs(tangent.dot(ref)) > 0.94:
            ref = Vector((0, 1, 0))
        u = tangent.cross(ref).normalized()
        if prev_u is not None and u.dot(prev_u) < 0:
            u = -u
        v = tangent.cross(u).normalized()
        prev_u = u
        r = radii[k]
        for i in range(sides):
            a = TAU * i / sides
            verts.append(tuple(p + u * (math.cos(a) * r) + v * (math.sin(a) * r * depth)))
        ring_weights.append(weights[k] if weights else None)
    for k in range(len(pts) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            a = k * sides + i; b = k * sides + j
            c = (k + 1) * sides + j; d = (k + 1) * sides + i
            faces.append((a, b, c, d))
    if cap:
        b0 = len(verts); verts.append(tuple(pts[0]))
        b1 = len(verts); verts.append(tuple(pts[-1]))
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((b0, i, j))
            faces.append((b1, (len(pts) - 1) * sides + j, (len(pts) - 1) * sides + i))
    obj = mesh_object(name, verts, faces, mat, smooth)
    # weights: add groups ring by ring
    if weights:
        for k, w in enumerate(weights):
            if not w:
                continue
            for gi in range(sides):
                idx = k * sides + gi
                for bone, val in w.items():
                    vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
                    vg.add([idx], val, "REPLACE")
        # caps follow the nearest ring
        if cap:
            for idx, w in ((len(verts) - 2, weights[0]), (len(verts) - 1, weights[-1])):
                if w:
                    for bone, val in w.items():
                        vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
                        vg.add([idx], val, "REPLACE")
    return obj


def bind(obj, arm):
    if not obj:
        return obj
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    return obj


def weight_all(obj, arm, bone):
    vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    return bind(obj, arm)


def weight_z(obj, arm, cuts=None):
    """Torso weights by world Z."""
    cuts = cuts or [(1.02, "hips"), (1.20, "spine"), (99, "chest")]
    for v in obj.data.vertices:
        z = v.co.z
        bone = cuts[-1][1]
        for lim, name in cuts:
            if z <= lim:
                bone = name
                break
        vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
        vg.add([v.index], 1.0, "REPLACE")
    return bind(obj, arm)


# ── armature ────────────────────────────────────────────────────────────────

def build_armature(cfg):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "Armature"
    arm = ob.data
    arm.name = "SceneRig"
    for b in list(arm.edit_bones):
        arm.edit_bones.remove(b)
    made = {}

    def bone(name, head, tail, parent=None):
        eb = arm.edit_bones.new(name)
        eb.head = Vector((head[0] * s, head[1] * s, head[2] * s))
        eb.tail = Vector((tail[0] * s, tail[1] * s, tail[2] * s))
        eb.use_connect = False
        if parent:
            eb.parent = made[parent]
        made[name] = eb
        return eb

    bone("root", (0, 0, 0), (0, 0, 0.12))
    bone("hips", (0, 0, 0.92), (0, 0, 1.04), "root")
    bone("spine", (0, 0, 1.04), (0, 0, 1.18), "hips")
    bone("chest", (0, 0, 1.18), (0, 0, 1.38), "spine")
    bone("neck", (0, 0, 1.38), (0, 0, 1.51), "chest")
    bone("head", (0, 0, 1.51), (0, 0, 1.74), "neck")
    bone("jaw", (0, -0.055, 1.61), (0, -0.085, 1.53), "head")
    for side, sx in (("L", 1), ("R", -1)):
        bone(f"eye.{side}", (sx * 0.05, -0.105, 1.66), (sx * 0.05, -0.125, 1.66), "head")
        bone(f"shoulder.{side}", (0, 0, 1.36), (sx * sh, 0, 1.36), "chest")
        # A-pose: 45° below horizontal, with a relaxed elbow.
        bone(f"upperArm.{side}", (sx * sh, 0, 1.36), (sx * (sh + 0.17), 0, 1.19), f"shoulder.{side}")
        bone(f"lowerArm.{side}", (sx * (sh + 0.17), 0, 1.19), (sx * (sh + 0.30), 0, 1.02), f"upperArm.{side}")
        bone(f"hand.{side}", (sx * (sh + 0.30), 0, 1.02), (sx * (sh + 0.36), 0, 0.94), f"lowerArm.{side}")
        bone(f"upperLeg.{side}", (sx * hip, 0, 0.94), (sx * hip, 0, 0.53), "hips")
        bone(f"lowerLeg.{side}", (sx * hip, 0, 0.53), (sx * hip, 0, 0.11), f"upperLeg.{side}")
        bone(f"foot.{side}", (sx * hip, 0, 0.11), (sx * hip, -0.09, 0.045), f"lowerLeg.{side}")
        bone(f"toe.{side}", (sx * hip, -0.09, 0.045), (sx * hip, -0.20, 0.04), f"foot.{side}")

    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "XYZ"
    return ob


# ── head / face ─────────────────────────────────────────────────────────────

def build_head(cfg, arm, skin, hair, lip, white, iris, dark, teeth, tongue, mats):
    s = cfg["scale"]
    g = cfg["gender"]
    head = add_sphere("Head", (0, -0.002 * s, 1.625 * s),
                      (0.135 * s, 0.122 * s, 0.166 * s), skin, segments=28, rings=20)
    # Shape the sphere into a head: taper the jaw, add a small chin, cheeks and
    # a slightly flatter back.
    cz = 1.625 * s
    for v in head.data.vertices:
        nz = (v.co.z) / (0.166 * s)  # -1..1
        nx = v.co.x / (0.135 * s)
        # jaw taper below the cheekbones
        if nz < 0:
            f = 1.0 + nz * (0.22 if g == "female" else 0.14)
            v.co.x *= f
        # chin forward
        if nz < -0.45:
            k = (-nz - 0.45) / 0.55
            if v.co.y < 0:
                v.co.y -= 0.020 * s * k
        # cheek volume
        if -0.5 < nz < 0.2 and v.co.y < 0:
            v.co.y -= (0.010 if g == "female" else 0.006) * s * (1 - abs(nz - 0.0))
        # flatter back of the skull
        if v.co.y > 0:
            v.co.y *= 0.92
        # brow ridge (male only)
        if g == "male" and 0.15 < nz < 0.45 and v.co.y < 0:
            v.co.y -= 0.004 * s
    weight_all(head, arm, "head")

    # neck
    neck = tube("Neck", [(0, 0.005, 1.38 * s), (0, 0.005, 1.505 * s)],
                [0.060 * s, 0.052 * s], skin, sides=14, depth=0.92,
                weights=[{"neck": 0.55, "chest": 0.45}, {"neck": 1.0}])
    bind(neck, arm)

    # ears
    for side, sx in (("L", 1), ("R", -1)):
        ear = add_sphere(f"Ear.{side}", (sx * 0.132 * s, 0.005 * s, 1.615 * s),
                         (0.024 * s, 0.014 * s, 0.039 * s), skin, segments=14, rings=10)
        weight_all(ear, arm, "head")

    # eyes: sclera, iris and pupil in a shallow socket
    ex = 0.046 * s
    ey = -0.119 * s
    ez = 1.655 * s
    es = 1.0 if g == "male" else 1.08
    for side, sx in (("L", 1), ("R", -1)):
        eye = add_sphere(f"EyeWhite.{side}", (sx * ex, ey, ez),
                         (0.022 * es * s, 0.010 * s, 0.020 * es * s), white, segments=18, rings=12)
        weight_all(eye, arm, f"eye.{side}")
        iris_obj = add_sphere(f"Iris.{side}", (sx * ex, ey - 0.009 * s, ez),
                              (0.011 * s, 0.004 * s, 0.012 * s), iris, segments=16, rings=10)
        weight_all(iris_obj, arm, f"eye.{side}")
        pupil = add_sphere(f"Pupil.{side}", (sx * ex, ey - 0.012 * s, ez),
                           (0.0055 * s, 0.002 * s, 0.0060 * s), dark, segments=12, rings=8)
        weight_all(pupil, arm, f"eye.{side}")
        # eyelash line
        lash = tube(f"Lash.{side}",
                    [(sx * (ex - 0.020 * es) * s, ey - 0.013 * s, ez + 0.014 * es * s),
                     (sx * ex * s, ey - 0.015 * s, ez + 0.021 * es * s),
                     (sx * (ex + 0.020 * es) * s, ey - 0.013 * s, ez + 0.010 * es * s)],
                    [0.0015 * s, 0.0025 * s, 0.0012 * s], dark, sides=5, depth=0.7)
        weight_all(lash, arm, "head")

    # brows: a gentle arch, thicker/lower for male
    for side, sx in (("L", 1), ("R", -1)):
        bz = 1.692 * s
        pts = [(sx * 0.027 * s, -0.126 * s, bz),
               (sx * 0.045 * s, -0.130 * s, bz + 0.004 * s),
               (sx * 0.063 * s, -0.124 * s, bz - 0.001 * s)]
        brow = tube(f"Brow.{side}", pts,
                    [(0.0065 if g == "male" else 0.0050) * s,
                     (0.0075 if g == "male" else 0.0055) * s,
                     (0.0035 if g == "male" else 0.0030) * s],
                    hair, sides=7, depth=0.7)
        weight_all(brow, arm, "head")

    # nose: a small bridge + tip, not a sphere
    nose = tube("Nose",
                [(0, -0.126 * s, 1.665 * s),
                 (0, -0.145 * s, 1.630 * s),
                 (0, -0.153 * s, 1.614 * s)],
                [0.010 * s, 0.016 * s, 0.022 * s], skin, sides=9, depth=0.72)
    weight_all(nose, arm, "head")
    for side, sx in (("L", 1), ("R", -1)):
        wing = add_sphere(f"NoseWing.{side}", (sx * 0.018 * s, -0.145 * s, 1.618 * s),
                          (0.010 * s, 0.011 * s, 0.008 * s), skin, segments=10, rings=8)
        weight_all(wing, arm, "head")

    # mouth assembled into one mesh for the viseme morphs
    czm = 1.574 * s
    cavity = add_sphere("MouthCavity", (0, -0.129 * s, czm),
                        (0.030 * s, 0.007 * s, 0.008 * s), dark, segments=18, rings=10)
    upper = add_sphere("UpperLip", (0, -0.135 * s, czm + 0.0040 * s),
                       (0.033 * s, 0.008 * s, 0.0055 * s), lip, segments=18, rings=10)
    lower = add_sphere("LowerLip", (0, -0.135 * s, czm - 0.0045 * s),
                       (0.034 * s, 0.008 * s, 0.0068 * s), lip, segments=18, rings=10)
    for side, sx in (("L", 1), ("R", -1)):
        corner = add_sphere(f"LipCorner.{side}", (sx * 0.031 * s, -0.133 * s, czm),
                            (0.004 * s, 0.004 * s, 0.006 * s), lip, segments=8, rings=6)
        upper = join_objects([upper, corner])
    teeth_obj = add_box("Teeth", (0, -0.134 * s, czm + 0.0035 * s),
                        (0.021 * s, 0.003 * s, 0.0032 * s), teeth, bevel=0.0012)
    tongue_obj = add_sphere("Tongue", (0, -0.132 * s, czm - 0.0025 * s),
                            (0.014 * s, 0.004 * s, 0.004 * s), tongue, segments=12, rings=8)
    for part in (cavity, upper, lower, teeth_obj, tongue_obj):
        part.vertex_groups.new(name="part_tongue").add(
            list(range(len(part.data.vertices))), 1.0, "REPLACE")
    for part in (cavity, upper, lower, teeth_obj):
        vg = part.vertex_groups.get("part_tongue")
        if vg:
            vg.remove(list(range(len(part.data.vertices))))
    mouth = join_objects([cavity, upper, lower, teeth_obj, tongue_obj])
    mouth.name = "Mouth"
    add_mouth_shape_keys(mouth)
    pg = mouth.vertex_groups.get("part_tongue")
    if pg:
        mouth.vertex_groups.remove(pg)
    weight_all(mouth, arm, "head")

    # hair styles: the inactive styles are hidden by the runtime outfit call
    hair_cap = add_sphere("HairCap", (0, 0.012 * s, 1.690 * s),
                          (0.147 * s, 0.132 * s, 0.140 * s), hair, segments=24, rings=16)
    weight_all(hair_cap, arm, "head")
    if cfg["hair_style"] in ("bob", "ponytail"):
        back = add_sphere("HairBack", (0, 0.060 * s, 1.565 * s),
                          (0.150 * s, 0.105 * s, 0.200 * s), hair, segments=20, rings=14)
        weight_all(back, arm, "head")
        for side, sx in (("L", 1), ("R", -1)):
            strand = tube(f"HairSide.{side}",
                          [(sx * 0.120 * s, 0.020 * s, 1.665 * s),
                           (sx * 0.138 * s, 0.025 * s, 1.560 * s),
                           (sx * 0.125 * s, 0.030 * s, 1.440 * s)],
                          [0.032 * s, 0.036 * s, 0.025 * s], hair, sides=10, depth=0.9)
            weight_all(strand, arm, "head")
    if cfg["hair_style"] == "ponytail":
        tail = tube("HairTail",
                    [(0, 0.120 * s, 1.690 * s),
                     (0, 0.175 * s, 1.610 * s),
                     (0, 0.195 * s, 1.500 * s)],
                    [0.040 * s, 0.050 * s, 0.018 * s], hair, sides=12, depth=1.0)
        weight_all(tail, arm, "head")
    if cfg["hair_style"] == "short":
        for side, sx in (("L", 1), ("R", -1)):
            sideburn = add_box(f"Sideburn.{side}", (sx * 0.125 * s, 0.006 * s, 1.600 * s),
                               (0.022 * s, 0.032 * s, 0.050 * s), hair, bevel=0.004, smooth=True)
            weight_all(sideburn, arm, "head")

    # glasses / hood are optional accessories, kept as separate meshes
    if cfg.get("glasses"):
        for side, sx in (("L", 1), ("R", -1)):
            frame = add_torus(f"Glass.{side}", (sx * 0.050 * s, -0.137 * s, 1.657 * s),
                              0.028 * s, 0.0032 * s, dark)
            weight_all(frame, arm, "head")
        bridge = add_box("GlassBridge", (0, -0.139 * s, 1.659 * s),
                         (0.032 * s, 0.004 * s, 0.004 * s), dark, bevel=0.001)
        weight_all(bridge, arm, "head")

    mats.update({"brow": hair})
    return {
        "head": head, "neck": neck, "mouth": mouth,
        "eyeL": bpy.data.objects.get("EyeWhite.L"), "eyeR": bpy.data.objects.get("EyeWhite.R"),
    }


def join_objects(parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    return bpy.context.object


def add_mouth_shape_keys(obj):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    c = Vector((0, 0, 0))
    for v in obj.data.vertices:
        c += v.co
    c /= max(1, len(obj.data.vertices))
    scale = {
        "viseme_sil": (1.00, 1.00, 0.000), "viseme_PP": (0.85, 0.70, 0.001),
        "viseme_FF": (0.95, 0.80, 0.001), "viseme_TH": (0.95, 1.40, 0.001),
        "viseme_DD": (1.00, 2.20, 0.000), "viseme_kk": (0.95, 2.50, 0.000),
        "viseme_CH": (0.85, 1.60, 0.000), "viseme_SS": (1.22, 1.00, 0.000),
        "viseme_nn": (1.00, 1.80, 0.000), "viseme_RR": (0.90, 1.90, 0.000),
        "viseme_aa": (1.20, 3.40, -0.001), "viseme_E": (1.35, 2.20, 0.000),
        "viseme_I": (1.25, 1.50, 0.000), "viseme_O": (0.85, 2.80, -0.001),
        "viseme_U": (0.70, 2.00, 0.000), "jawOpen": (1.00, 3.60, -0.002),
        "mouthSmile": (1.30, 1.10, 0.001), "mouthFrown": (0.90, 1.10, -0.001),
        "mouthPress": (1.10, 0.55, 0.000), "mouthPucker": (0.55, 1.10, 0.001),
        "mouthStretch": (1.35, 1.35, 0.000),
    }
    for name, (sx, sz, dz) in scale.items():
        key = obj.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for i, v in enumerate(obj.data.vertices):
            co = key.data[i].co.copy()
            co.x = c.x + (co.x - c.x) * sx
            co.z = c.z + (co.z - c.z) * sz + dz
            key.data[i].co = co
    # lip fullness (kept separate from the visemes)
    key = obj.shape_key_add(name="lipFull", from_mix=False)
    key.value = 0.0
    for i, v in enumerate(obj.data.vertices):
        co = key.data[i].co.copy()
        co.x = c.x + (co.x - c.x) * 1.10
        if co.y < c.y:
            co.y -= 0.0025
        key.data[i].co = co


# ── body / wardrobe ─────────────────────────────────────────────────────────

def torso_rings(cfg):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    bust = cfg.get("bust", 0.0) * s
    waist = cfg.get("waist", 0.135) * s
    return [
        (0.90 * s, hip * 1.45, 0.115 * s, 0.105 * s, 0),
        (0.98 * s, hip * 1.52, 0.120 * s, 0.105 * s, 0),
        (1.06 * s, waist * 0.96, 0.105 * s, 0.095 * s, 0),
        (1.16 * s, waist * 1.05, 0.110 * s + bust * 0.30, 0.100 * s, 0),
        (1.26 * s, sh * 1.00, 0.112 * s + bust, 0.100 * s, 0),
        (1.34 * s, sh * 1.08, 0.100 * s, 0.095 * s, 0),
        (1.385 * s, sh * 0.44, 0.070 * s, 0.065 * s, 0),
    ]


def build_body(cfg, arm, mats):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    skin, top, bottom, shoe, metal = mats["skin"], mats["top"], mats["bottom"], mats["shoe"], mats["metal"]
    rings = torso_rings(cfg)
    body = loft("Body", rings, skin, segments=20)
    weight_z(body, arm)
    pelvis = loft("Pelvis", [
        (0.84 * s, hip * 1.38, 0.108 * s, 0.100 * s, 0),
        (0.92 * s, hip * 1.48, 0.118 * s, 0.108 * s, 0),
        (1.00 * s, hip * 1.42, 0.112 * s, 0.104 * s, 0),
    ], skin, segments=20)
    weight_z(pelvis, arm, [(1.04, "hips"), (99, "spine")])

    # ── tops ───────────────────────────────────────────────────────────────
    top_rings = [(z, rx + 0.012 * s, rf + 0.012 * s, rb + 0.012 * s, y)
                 for z, rx, rf, rb, y in rings]
    top_rings = [r for r in top_rings if r[0] >= 0.96 * s]

    tee = loft("top_tee", top_rings, top, segments=20)
    weight_z(tee, arm)
    shirt = loft("top_shirt", top_rings, top, segments=20)
    weight_z(shirt, arm)
    hoodie = loft("top_hoodie", top_rings, top, segments=20)
    weight_z(hoodie, arm)

    # collars and hoodie details
    collar = add_torus("Collar.Shirt", (0, 0.005 * s, 1.385 * s), 0.077 * s, 0.014 * s,
                       top, rotation=(0, 0, 0))
    weight_all(collar, arm, "neck")
    hood = add_sphere("Hood", (0, 0.075 * s, 1.345 * s),
                      (0.155 * s, 0.105 * s, 0.105 * s), top, segments=20, rings=12)
    weight_all(hood, arm, "chest")
    pocket = add_box("Pocket", (0, -0.118 * s, 1.080 * s),
                     (0.190 * s, 0.025 * s, 0.070 * s), top, bevel=0.015, smooth=True)
    weight_z(pocket, arm, [(1.04, "hips"), (1.14, "spine"), (99, "chest")])

    # sleeves
    for side, sx in (("L", 1), ("R", -1)):
        wrist = Vector((sx * (sh + 0.30) * s, 0, 1.02 * s))
        elbow = Vector((sx * (sh + 0.17) * s, 0, 1.19 * s))
        shoulder = Vector((sx * sh, 0, 1.360 * s))
        for prefix in ("top_tee", "top_shirt", "top_hoodie"):
            cap = add_sphere(f"{prefix}.Shoulder.{side}", (sx * sh, 0, 1.352 * s),
                             (0.081 * s, 0.074 * s, 0.074 * s), top, segments=14, rings=10)
            weight_all(cap, arm, "upperArm." + side)
        # short sleeve
        tee_sleeve = tube(f"top_tee.Sleeve.{side}",
                          [shoulder, shoulder + (elbow - shoulder) * 0.38],
                          [0.075 * s, 0.068 * s], top, sides=12, depth=0.92,
                          weights=[{"upperArm." + side: 1.0}] * 2)
        bind(tee_sleeve, arm)
        # long sleeve (shirt + hoodie)
        for prefix in ("top_shirt", "top_hoodie"):
            sl = tube(f"{prefix}.Sleeve.{side}",
                      [shoulder, shoulder + (elbow - shoulder) * 0.58, elbow,
                       elbow + (wrist - elbow) * 0.72, wrist],
                      [0.076 * s, 0.062 * s, 0.055 * s, 0.050 * s, 0.046 * s],
                      top, sides=12, depth=0.92,
                      weights=[{"upperArm." + side: 1.0},
                               {"upperArm." + side: 0.75, "lowerArm." + side: 0.25},
                               {"upperArm." + side: 0.25, "lowerArm." + side: 0.75},
                               {"lowerArm." + side: 1.0}, {"lowerArm." + side: 0.8, "hand." + side: 0.2}])
            bind(sl, arm)
        cuff = add_torus(f"top_shirt.Cuff.{side}", (sx * (sh + 0.292) * s, 0, 1.035 * s),
                         0.048 * s, 0.010 * s, top, rotation=(0, 0, 0))
        weight_all(cuff, arm, "lowerArm." + side)
        hcuff = add_torus(f"top_hoodie.Cuff.{side}", (sx * (sh + 0.292) * s, 0, 1.035 * s),
                          0.050 * s, 0.011 * s, top, rotation=(0, 0, 0))
        weight_all(hcuff, arm, "lowerArm." + side)

    # ── bottoms ────────────────────────────────────────────────────────────
    def pants_object(prefix, bottom_z):
        waist = loft(f"{prefix}.Waist",
                     [(0.94 * s, hip * 1.52, 0.118 * s, 0.108 * s, 0),
                      (1.00 * s, hip * 1.45, 0.112 * s, 0.103 * s, 0)],
                     bottom, segments=20)
        weight_all(waist, arm, "hips")
        for side, sx in (("L", 1), ("R", -1)):
            pts = [(sx * hip, 0, 0.95 * s),
                   (sx * hip, 0, 0.78 * s),
                   (sx * hip, 0, 0.54 * s),
                   (sx * hip, 0, bottom_z)]
            leg = tube(f"{prefix}.Leg.{side}", pts,
                       [0.088 * s, 0.083 * s, 0.073 * s, 0.066 * s],
                       bottom, sides=12, depth=0.95,
                       weights=[{"upperLeg." + side: 1.0},
                                {"upperLeg." + side: 1.0},
                                {"upperLeg." + side: 0.35, "lowerLeg." + side: 0.65},
                                {"lowerLeg." + side: 1.0}])
            bind(leg, arm)
        return waist

    pants_object("bottom_pants", 0.12 * s)
    pants_object("bottom_shorts", 0.58 * s)
    # skirt
    skirt = loft("bottom_skirt",
                 [(0.58 * s, 0.235 * s, 0.160 * s, 0.160 * s, 0),
                  (0.74 * s, 0.205 * s, 0.140 * s, 0.140 * s, 0),
                  (0.92 * s, 0.160 * s, 0.120 * s, 0.108 * s, 0),
                  (1.00 * s, hip * 1.46, 0.112 * s, 0.103 * s, 0)],
                 bottom, segments=24)
    weight_all(skirt, arm, "hips")
    # dress: top + skirt in one material
    dress_top = loft("dress.Top", top_rings, mats["dress"], segments=20)
    weight_z(dress_top, arm)
    dress_skirt = loft("dress.Skirt",
                       [(0.56 * s, 0.240 * s, 0.165 * s, 0.165 * s, 0),
                        (0.78 * s, 0.190 * s, 0.135 * s, 0.135 * s, 0),
                        (0.96 * s, 0.150 * s, 0.112 * s, 0.105 * s, 0),
                        (1.02 * s, hip * 1.44, 0.110 * s, 0.102 * s, 0)],
                       mats["dress"], segments=24)
    weight_all(dress_skirt, arm, "hips")
    for side, sx in (("L", 1), ("R", -1)):
        sleeve = tube(f"dress.Sleeve.{side}",
                      [(sx * sh, 0, 1.36 * s), (sx * (sh + 0.10) * s, 0, 1.24 * s)],
                      [0.070 * s, 0.060 * s], mats["dress"], sides=12, depth=0.9,
                      weights=[{"upperArm." + side: 1.0}] * 2)
        bind(sleeve, arm)

    # ── shoes ──────────────────────────────────────────────────────────────
    for side, sx in (("L", 1), ("R", -1)):
        ankle_z = 0.11 * s
        base = add_box(f"shoes_sneaker.{side}", (sx * hip, -0.045 * s, 0.055 * s),
                       (0.088 * s, 0.180 * s, 0.095 * s), shoe, bevel=0.025, smooth=True)
        weight_all(base, arm, "foot." + side)
        sole = add_box(f"shoes_sneaker.Sole.{side}", (sx * hip, -0.045 * s, 0.012 * s),
                       (0.092 * s, 0.185 * s, 0.028 * s), mats["sole"], bevel=0.008, smooth=True)
        weight_all(sole, arm, "foot." + side)
        toe = add_sphere(f"shoes_sneaker.Toe.{side}", (sx * hip, -0.135 * s, 0.055 * s),
                         (0.080 * s, 0.045 * s, 0.050 * s), shoe, segments=12, rings=8)
        weight_all(toe, arm, "toe." + side)
        boot = add_box(f"shoes_boot.{side}", (sx * hip, -0.035 * s, 0.075 * s),
                       (0.095 * s, 0.175 * s, 0.135 * s), shoe, bevel=0.030, smooth=True)
        weight_all(boot, arm, "foot." + side)
        shaft = tube(f"shoes_boot.Shaft.{side}",
                     [(sx * hip, 0, 0.12 * s), (sx * hip, 0, 0.26 * s)],
                     [0.075 * s, 0.070 * s], shoe, sides=12, depth=0.92)
        weight_all(shaft, arm, "lowerLeg." + side)

    return body


# ── arms / hands / legs ─────────────────────────────────────────────────────

def build_arms(cfg, arm, mats):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    skin, top = mats["skin"], mats["top"]
    for side, sx in (("L", 1), ("R", -1)):
        should = Vector((sx * sh, 0, 1.36 * s))
        elbow = Vector((sx * (sh + 0.17) * s, 0, 1.19 * s))
        wrist = Vector((sx * (sh + 0.30) * s, 0, 1.02 * s))
        # deltoid, upper arm, elbow and forearm in one smooth tapered skin tube
        pts = [should, should.lerp(elbow, 0.35), elbow, elbow.lerp(wrist, 0.55), wrist]
        radii = [0.062 * s, 0.055 * s, 0.045 * s, 0.040 * s, 0.034 * s]
        weights = [
            {"shoulder." + side: 0.55, "upperArm." + side: 0.45},
            {"upperArm." + side: 1.0},
            {"upperArm." + side: 0.45, "lowerArm." + side: 0.55},
            {"lowerArm." + side: 1.0},
            {"lowerArm." + side: 0.7, "hand." + side: 0.3},
        ]
        arm_mesh = tube(f"Arm.{side}", pts, radii, skin, sides=14, depth=0.92, weights=weights)
        bind(arm_mesh, arm)
        shoulder = add_sphere(f"Shoulder.{side}", (sx * sh, 0, 1.355 * s),
                              (0.066 * s, 0.064 * s, 0.064 * s), skin, segments=16, rings=12)
        weight_all(shoulder, arm, "upperArm." + side)
        hand = build_hand(side, sx, wrist, skin, arm, s)
        # a small elbow bump is enough; the tapered tube handles the rest
    return True


def build_hand(side, sx, wrist, skin, arm, s):
    d = Vector((sx * 0.06, 0, -0.08)).normalized()
    side_v = Vector((0, 1, 0))
    palm_c = wrist + d * 0.055 * s
    palm = add_sphere(f"HandPalm.{side}", palm_c,
                      (0.039 * s, 0.027 * s, 0.050 * s), skin, segments=16, rings=10)
    weight_all(palm, arm, f"hand.{side}")
    # four fingers + thumb: small tapered tubes, weights to the hand bone
    hand_dir = d
    for i, off in enumerate((-0.024, -0.008, 0.008, 0.024)):
        length = (0.050 if i in (1, 2) else 0.043) * s
        base = palm_c + side_v * (off * s) + hand_dir * (0.028 * s)
        tip = base + hand_dir * length
        finger = tube(f"Finger{i}.{side}", [base, tip],
                      [0.010 * s, 0.007 * s], skin, sides=7, depth=0.8)
        weight_all(finger, arm, f"hand.{side}")
    thumb_base = palm_c + side_v * (-0.034 * s) - hand_dir * 0.005 * s
    thumb_tip = thumb_base + Vector((-sx * 0.030, -0.012, -0.020)).normalized() * 0.045 * s
    thumb = tube(f"Thumb.{side}", [thumb_base, thumb_tip],
                 [0.013 * s, 0.010 * s], skin, sides=8, depth=0.85)
    weight_all(thumb, arm, f"hand.{side}")
    return palm


def build_legs(cfg, arm, mats):
    s = cfg["scale"]
    hip = cfg["hip"] * s
    skin, bottom, shoe = mats["skin"], mats["bottom"], mats["shoe"]
    for side, sx in (("L", 1), ("R", -1)):
        top = Vector((sx * hip, 0, 0.94 * s))
        knee = Vector((sx * hip, 0, 0.53 * s))
        ankle = Vector((sx * hip, 0, 0.11 * s))
        pts = [top, top.lerp(knee, 0.5), knee, knee.lerp(ankle, 0.55), ankle]
        radii = [0.078 * s, 0.071 * s, 0.060 * s, 0.054 * s, 0.043 * s]
        weights = [
            {"upperLeg." + side: 1.0},
            {"upperLeg." + side: 1.0},
            {"upperLeg." + side: 0.45, "lowerLeg." + side: 0.55},
            {"lowerLeg." + side: 1.0},
            {"lowerLeg." + side: 0.7, "foot." + side: 0.3},
        ]
        leg = tube(f"Leg.{side}", pts, radii, skin, sides=14, depth=0.92, weights=weights)
        bind(leg, arm)
        knee_obj = add_sphere(f"Knee.{side}", (sx * hip, -0.008 * s, 0.53 * s),
                              (0.055 * s, 0.052 * s, 0.052 * s), skin, segments=14, rings=10)
        weight_all(knee_obj, arm, "lowerLeg." + side)
        foot = add_sphere(f"Ankle.{side}", (sx * hip, 0, 0.105 * s),
                          (0.047 * s, 0.043 * s, 0.060 * s), skin, segments=14, rings=10)
        weight_all(foot, arm, "foot." + side)


def add_body_shape_keys(obj, cfg):
    """Body-shape morphs shared by body and clothing."""
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    params = {
        "bodyShoulder": lambda p, w: p + Vector((0, 0, 0)),
        "bodyChest": lambda p, w: p,
        "bodyWaist": lambda p, w: p,
        "bodyHips": lambda p, w: p,
        "bodyBelly": lambda p, w: p,
    }
    for name in params:
        key = obj.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for i, v in enumerate(obj.data.vertices):
            co = key.data[i].co.copy()
            z = co.z
            # only torso-ish vertices
            if name == "bodyShoulder" and 1.22 * s <= z <= 1.38 * s:
                co.x *= 1.10
            elif name == "bodyChest" and 1.14 * s <= z <= 1.30 * s and co.y < 0:
                co.y -= 0.025 * s
                co.x *= 1.035
            elif name == "bodyWaist" and 1.00 * s <= z <= 1.14 * s:
                co.x *= 1.12
                co.y *= 1.08
            elif name == "bodyHips" and 0.86 * s <= z <= 1.02 * s:
                co.x *= 1.14
            elif name == "bodyBelly" and 1.00 * s <= z <= 1.15 * s and co.y < 0:
                co.y -= 0.020 * s
            key.data[i].co = co


def add_face_shape_keys(head):
    if head.data.shape_keys is None:
        head.shape_key_add(name="Basis", from_mix=False)
    c = Vector((0, 0, 0))
    for v in head.data.vertices:
        c += v.co
    c /= max(1, len(head.data.vertices))
    keys = {
        "faceWidth": lambda co: Vector(((co.x - c.x) * 1.10 + c.x, co.y, co.z)),
        "faceLength": lambda co: Vector((co.x, co.y, (co.z - c.z) * 1.10 + c.z)),
        "jawWidth": lambda co: Vector(((co.x - c.x) * (1.12 if co.z < c.z else 1.0) + c.x, co.y, co.z)),
        "chin": lambda co: Vector((co.x, co.y - (0.018 if co.z < c.z - 0.03 else 0), co.z - (0.012 if co.z < c.z - 0.05 else 0))),
        "cheek": lambda co: Vector((co.x + (0.010 if abs(co.z - c.z) < 0.04 and co.y < c.y else 0), co.y - (0.008 if abs(co.z - c.z) < 0.04 and co.y < c.y else 0), co.z)),
    }
    for name, fn in keys.items():
        key = head.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for i, v in enumerate(head.data.vertices):
            key.data[i].co = fn(v.co.copy())


# ── actions (metadata; runtime drives the actual pose) ──────────────────────

def make_action(arm, name, frames):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = action
    for frame, pose in frames:
        bpy.context.scene.frame_set(frame)
        for bone_name, rot in pose.items():
            pb = arm.pose.bones.get(bone_name)
            if not pb:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = rot
            pb.keyframe_insert("rotation_euler", frame=frame)


# ── character ───────────────────────────────────────────────────────────────

def build_character(cfg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30
    s = cfg["scale"]

    mats = {
        "skin": material("Skin", cfg["skin"], 0.78),
        "hair": material("Hair", cfg["hair"], 0.9),
        "top": material("Top", cfg["top"], 0.8),
        "bottom": material("Bottom", cfg["bottom"], 0.85),
        "shoe": material("Shoes", cfg["shoe"], 0.7),
        "sole": material("Sole", (0.06, 0.06, 0.07), 0.9),
        "dress": material("Dress", cfg.get("dress", cfg["top"]), 0.8),
        "white": material("EyeWhite", (0.96, 0.96, 0.93), 0.32),
        "iris": material("Iris", cfg["eye"], 0.4),
        "dark": material("MouthDark", (0.10, 0.035, 0.03), 0.9),
        "lip": material("Lips", cfg["lip"], 0.65),
        "teeth": material("Teeth", (0.95, 0.94, 0.88), 0.35),
        "tongue": material("Tongue", (0.72, 0.28, 0.30), 0.7),
        "metal": material("Metal", (0.55, 0.57, 0.62), 0.35, 0.6),
    }
    arm = build_armature(cfg)
    build_body(cfg, arm, mats)
    build_arms(cfg, arm, mats)
    build_legs(cfg, arm, mats)
    face = build_head(cfg, arm, mats["skin"], mats["hair"], mats["lip"], mats["white"],
                      mats["iris"], mats["dark"], mats["teeth"], mats["tongue"], mats)
    # shape keys for the face and torso
    add_face_shape_keys(face["head"])
    for name in ("Body", "top_tee", "top_shirt", "top_hoodie", "dress.Top", "Pelvis",
                 "bottom_skirt", "dress.Skirt"):
        obj = bpy.data.objects.get(name)
        if obj:
            add_body_shape_keys(obj, cfg)

    # metadata actions
    make_action(arm, "idle", [(0, {"chest": (0, 0, 0)}), (60, {"chest": (0.015, 0, 0)}), (120, {"chest": (0, 0, 0)})])
    make_action(arm, "talk", [(0, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
                              (30, {"chest": (0.01, 0.02, 0), "head": (0.02, 0.04, 0)}),
                              (60, {"chest": (0, -0.01, 0), "head": (-0.01, -0.03, 0)}),
                              (120, {"chest": (0, 0, 0), "head": (0, 0, 0)})])

    scene.frame_start = 0
    scene.frame_end = 120
    out = SRC / f"{cfg['name']}_v2.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"saved {out}")
    return out


CHARACTERS = [
    {
        "name": "mark_v2", "gender": "male", "scale": 1.00,
        "shoulder": 0.168, "hip": 0.097, "waist": 0.137, "bust": 0.0,
        "skin": (0.72, 0.50, 0.37), "lip": (0.52, 0.23, 0.21),
        "hair": (0.10, 0.075, 0.06), "eye": (0.20, 0.36, 0.27),
        "top": (0.16, 0.30, 0.55), "bottom": (0.16, 0.17, 0.20),
        "dress": (0.16, 0.30, 0.55), "shoe": (0.08, 0.08, 0.09),
        "hair_style": "short", "glasses": False,
    },
    {
        "name": "mira_v2", "gender": "female", "scale": 0.945,
        "shoulder": 0.143, "hip": 0.118, "waist": 0.116, "bust": 0.055,
        "skin": (0.86, 0.65, 0.51), "lip": (0.68, 0.30, 0.30),
        "hair": (0.46, 0.16, 0.07), "eye": (0.20, 0.45, 0.62),
        "top": (0.20, 0.45, 0.31), "bottom": (0.22, 0.17, 0.24),
        "dress": (0.55, 0.18, 0.26), "shoe": (0.24, 0.11, 0.10),
        "hair_style": "ponytail", "glasses": True,
    },
]


if __name__ == "__main__":
    for cfg in CHARACTERS:
        build_character(cfg)
