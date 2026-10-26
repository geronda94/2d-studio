"""SceneRig polygonal character generator v3.

Run the built-in Mark/Mira pair:
    blender --background --python scripts/blender/make_poly_characters_v3.py

Or generate any number of variants from a JSON preset:
    blender --background --python scripts/blender/make_poly_characters_v3.py -- \
        --config assets/characters/presets/nora.json

Then export each .blend with scripts/blender/scene_rig_export.py.

The characters are original CC0 low-poly humans built from lofted meshes:
gender-shaped torso, tapered limbs, hands with fingers and a thumb, a shaped
head with inset eyes, eyelids, blink morphs, a layered fringe, several hair
styles and a small wardrobe.  All meshes are weighted to the canonical
25-bone SceneRig skeleton.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "characters" / "src"
SRC.mkdir(parents=True, exist_ok=True)
TAU = math.pi * 2


# ── materials ───────────────────────────────────────────────────────────────

def _color(value):
    """Accept ``#rrggbb`` in JSON presets as well as an RGB triple."""
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        return tuple(int(value[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    return tuple(value)


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


def add_oriented_sphere(name, loc, scale, mat, z_axis, y_axis=(0, 1, 0),
                        segments=20, rings=14, smooth=True):
    """Ellipsoid whose local +Z follows ``z_axis`` and local +Y follows
    ``y_axis`` (projected).  Used for palms, where the thin axis must be the
    palm normal rather than a world axis."""
    obj = add_sphere(name, (0, 0, 0), scale, mat, segments=segments,
                     rings=rings, smooth=smooth)
    z = Vector(z_axis).normalized()
    y = Vector(y_axis)
    y = y - z * y.dot(z)
    if y.length < 1e-6:
        y = Vector((0, 0, 1))
    y.normalize()
    x = y.cross(z).normalized()
    y = z.cross(x).normalized()
    from mathutils import Matrix
    obj.matrix_world = (Matrix.Translation(Vector(loc)) @
                        Matrix((x, y, z)).transposed().to_4x4())
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    return obj


def assign_group(obj, bone):
    vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    return obj


def rotate_mesh(obj, center, axis, angle):
    from mathutils import Matrix
    rot = Matrix.Rotation(angle, 4, Vector(axis).normalized())
    c = Vector(center)
    for v in obj.data.vertices:
        v.co = c + rot @ (v.co - c)


def add_morph_key(obj, name, offset):
    """Create a shape key that translates every vertex by ``offset`` (metres)."""
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    key = obj.shape_key_add(name=name, from_mix=False)
    key.value = 0.0
    off = Vector(offset)
    for i, v in enumerate(obj.data.vertices):
        key.data[i].co = v.co + off


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


def weight_mix(obj, arm, groups):
    """Weight every vertex by a bone->weight dict (normalised)."""
    total = sum(groups.values()) or 1.0
    for name, w in groups.items():
        vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        vg.add(list(range(len(obj.data.vertices))), w / total, "REPLACE")
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
    # The old head was ~0.33 m tall on a 1.8 m body, which is what made the
    # character read as a doll.  0.26 m is stylised but much closer to life.
    head = add_sphere("Head", (0, -0.002 * s, 1.632 * s),
                      (0.128 * s, 0.118 * s, 0.136 * s), skin, segments=32, rings=24)
    for v in head.data.vertices:
        # vertex coordinates are local to the head object's origin
        nz = v.co.z / (0.136 * s)  # -1 (chin) .. +1 (crown)
        nx = v.co.x / (0.128 * s)
        # jaw taper below the cheekbones
        if nz < -0.10:
            k = (-nz - 0.10) / 0.90
            v.co.x *= 1.0 - k * (0.32 if g == "female" else 0.26)
            if v.co.y < 0:
                v.co.y *= 1.0 - k * 0.08
        # chin forward and a little lift
        if nz < -0.55 and v.co.y < 0:
            k = (-nz - 0.55) / 0.45
            v.co.y -= 0.014 * s * k
            v.co.z += 0.004 * s * k
        # cheekbones
        if -0.35 < nz < 0.15 and abs(nx) > 0.45 and v.co.y < 0:
            v.co.x *= 1.0 + 0.040 * (1.0 - abs(nz + 0.10) / 0.25)
        # flatter back of the skull
        if v.co.y > 0:
            v.co.y *= 0.94
        # brow ridge (male only)
        if g == "male" and 0.18 < nz < 0.42 and v.co.y < 0:
            v.co.y -= 0.003 * s
        # shallow eye sockets so the eyeballs sit in the face instead of on it
        for sx in (1, -1):
            dx = (v.co.x - sx * 0.043 * s) / (0.030 * s)
            dz = (v.co.z - 0.017 * s) / (0.022 * s)
            if v.co.y < 0 and dx * dx + dz * dz < 1.0:
                v.co.y += 0.004 * s
    weight_all(head, arm, "head")

    # neck
    neck = tube("Neck", [(0, 0.005, 1.38 * s), (0, 0.008, 1.500 * s)],
                [0.052 * s, 0.045 * s], skin, sides=16, depth=0.92,
                weights=[{"neck": 0.55, "chest": 0.45}, {"neck": 1.0}])
    bind(neck, arm)

    # ears
    for side, sx in (("L", 1), ("R", -1)):
        ear = add_sphere(f"Ear.{side}", (sx * 0.124 * s, 0.006 * s, 1.625 * s),
                         (0.013 * s, 0.009 * s, 0.023 * s), skin, segments=14, rings=10)
        weight_all(ear, arm, "head")

    # Eyes: inset sclera with iris, pupil and catchlight.  The skin-coloured
    # blink patch sits inside the skull at rest and slides in front of the eye
    # when the runtime drives eyeBlinkLeft/Right.
    ex = 0.037 * s
    ey = -0.113 * s
    ez = 1.647 * s
    es = 0.95 if g == "male" else 1.00
    for side, sx in (("L", 1), ("R", -1)):
        eye = add_sphere(f"EyeWhite.{side}", (sx * ex, ey, ez),
                         (0.0150 * es * s, 0.0072 * s, 0.0138 * es * s), white,
                         segments=20, rings=14)
        weight_all(eye, arm, f"eye.{side}")
        iris_obj = add_sphere(f"Iris.{side}", (sx * ex, ey - 0.006 * s, ez),
                              (0.0078 * s, 0.0025 * s, 0.0084 * s), iris,
                              segments=16, rings=10)
        weight_all(iris_obj, arm, f"eye.{side}")
        pupil = add_sphere(f"Pupil.{side}", (sx * ex, ey - 0.0085 * s, ez),
                           (0.0036 * s, 0.0014 * s, 0.0040 * s), dark,
                           segments=12, rings=8)
        weight_all(pupil, arm, f"eye.{side}")
        catch = add_sphere(f"Catchlight.{side}",
                           (sx * ex - 0.003 * s, ey - 0.0095 * s, ez + 0.004 * s),
                           (0.0014 * s, 0.0008 * s, 0.0014 * s), white,
                           segments=8, rings=6)
        weight_all(catch, arm, f"eye.{side}")

        # the blink patch below is the only lid geometry, so the eye stays open
        blink = add_sphere(f"Blink.{side}", (sx * ex, 0.010 * s, ez),
                           (0.0175 * es * s, 0.0028 * s, 0.0145 * es * s), skin,
                           segments=18, rings=12)
        lash = tube(f"BlinkLash.{side}",
                    [(sx * (ex - 0.016 * es) * s, 0.006 * s, ez + 0.012 * s),
                     (sx * ex * s, 0.006 * s, ez + 0.014 * s),
                     (sx * (ex + 0.016 * es) * s, 0.006 * s, ez + 0.011 * s)],
                    [0.0011 * s, 0.0016 * s, 0.0009 * s], dark, sides=5, depth=0.7)
        blink = join_objects([blink, lash])
        blink.name = f"Blink.{side}"
        add_morph_key(blink, "eyeBlinkLeft" if side == "L" else "eyeBlinkRight",
                      (0, -0.134 * s, 0))
        weight_all(blink, arm, "head")

    # Eyelids and creases: skin arcs make the eye read as an eye, not a
    # sphere stuck on the face.  The upper lid also carries the lash line.
    for side, sx in (("L", 1), ("R", -1)):
        cx = sx * ex
        # upper lid: from inner corner to outer corner, arching over the eye
        up = []
        for i in range(7):
            u = -1.0 + i / 3.0
            up.append((cx + u * 0.020 * es * s,
                       ey - 0.004 * s,
                       ez + (0.013 + 0.004 * (1.0 - u * u)) * es * s))
        lid = tube(f"EyelidUpper.{side}", up,
                   [0.0028 * s, 0.0046 * s, 0.0050 * s, 0.0048 * s,
                    0.0040 * s, 0.0031 * s, 0.0022 * s], skin, sides=6, depth=0.65)
        weight_all(lid, arm, "head")
        # lower lid: shallower, slightly darker crease
        lo = []
        for i in range(5):
            u = -1.0 + i / 2.0
            lo.append((cx + u * 0.017 * es * s,
                       ey - 0.001 * s,
                       ez - (0.012 + 0.0025 * (1.0 - u * u)) * es * s))
        lid_low = tube(f"EyelidLower.{side}", lo,
                       [0.0014 * s, 0.0022 * s, 0.0024 * s, 0.0020 * s, 0.0012 * s],
                       skin, sides=5, depth=0.6)
        weight_all(lid_low, arm, "head")
        # crease above the lid (reads as an eye fold, not a painted line)
        crease = tube(f"EyeCrease.{side}",
                      [(cx - 0.018 * es * s, ey - 0.003 * s, ez + 0.024 * es * s),
                       (cx, ey - 0.004 * s, ez + 0.027 * es * s),
                       (cx + 0.018 * es * s, ey - 0.003 * s, ez + 0.021 * es * s)],
                      [0.0010 * s, 0.0013 * s, 0.0009 * s], hair, sides=4, depth=0.55)
        weight_all(crease, arm, "head")
        # tear duct / inner corner
        duct = add_sphere(f"TearDuct.{side}", (cx - sx * 0.020 * es * s, ey - 0.003 * s, ez - 0.003 * s),
                          (0.0025 * s, 0.0018 * s, 0.0030 * s), lip, segments=8, rings=6)
        weight_all(duct, arm, "head")

    # Brows: thicker and closer to the eyes than the old pair.
    for side, sx in (("L", 1), ("R", -1)):
        bz = 1.684 * s
        pts = [(sx * 0.022 * s, -0.108 * s, bz),
               (sx * 0.041 * s, -0.112 * s, bz + 0.003 * s),
               (sx * 0.059 * s, -0.107 * s, bz - 0.001 * s)]
        brow = tube(f"Brow.{side}", pts,
                    [(0.0055 if g == "male" else 0.0045) * s,
                     (0.0065 if g == "male" else 0.0050) * s,
                     (0.0030 if g == "male" else 0.0026) * s],
                    hair, sides=7, depth=0.75)
        weight_all(brow, arm, "head")

    # Nose: short bridge, rounded tip, small wings.
    nose = tube("Nose",
                [(0, -0.109 * s, 1.664 * s),
                 (0, -0.118 * s, 1.632 * s),
                 (0, -0.124 * s, 1.614 * s)],
                [0.009 * s, 0.014 * s, 0.017 * s], skin, sides=10, depth=0.80)
    weight_all(nose, arm, "head")
    tip = add_sphere("NoseTip", (0, -0.122 * s, 1.611 * s),
                     (0.014 * s, 0.009 * s, 0.010 * s), skin, segments=14, rings=10)
    weight_all(tip, arm, "head")
    for side, sx in (("L", 1), ("R", -1)):
        wing = add_sphere(f"NoseWing.{side}", (sx * 0.014 * s, -0.118 * s, 1.612 * s),
                          (0.0065 * s, 0.0065 * s, 0.0048 * s), skin, segments=10, rings=8)
        weight_all(wing, arm, "head")
        nostril = add_sphere(f"Nostril.{side}", (sx * 0.008 * s, -0.125 * s, 1.607 * s),
                             (0.0020 * s, 0.0016 * s, 0.0015 * s), dark, segments=8, rings=6)
        weight_all(nostril, arm, "head")

    # mouth assembled into one mesh for the viseme morphs
    czm = 1.578 * s
    cavity = add_sphere("MouthCavity", (0, -0.108 * s, czm),
                        (0.026 * s, 0.0050 * s, 0.0055 * s), dark, segments=18, rings=10)
    # One soft upper lip and one fuller lower lip; the seam between them is
    # the mouth line, not a ring of separate pink balls.
    upper = add_sphere("UpperLip", (0, -0.111 * s, czm + 0.0036 * s),
                       (0.032 * s, 0.0052 * s, 0.0045 * s), lip, segments=22, rings=12)
    lower = add_sphere("LowerLip", (0, -0.111 * s, czm - 0.0040 * s),
                       (0.032 * s, 0.0052 * s, 0.0058 * s), lip, segments=22, rings=12)
    for side, sx in (("L", 1), ("R", -1)):
        corner = add_sphere(f"LipCorner.{side}", (sx * 0.029 * s, -0.108 * s, czm),
                            (0.0032 * s, 0.0034 * s, 0.0042 * s), lip, segments=8, rings=6)
        upper = join_objects([upper, corner])
    # philtrum and nasolabial folds (the natural folds around the mouth)
    philtrum = tube("Philtrum",
                    [(0, -0.116 * s, 1.615 * s), (0, -0.112 * s, 1.598 * s),
                     (0, -0.109 * s, 1.586 * s)],
                    [0.0022 * s, 0.0028 * s, 0.0022 * s], skin, sides=6, depth=0.6)
    weight_all(philtrum, arm, "head")
    for side, sx in (("L", 1), ("R", -1)):
        fold = tube(f"Nasolabial.{side}",
                    [(sx * 0.016 * s, -0.114 * s, 1.612 * s),
                     (sx * 0.024 * s, -0.110 * s, 1.596 * s),
                     (sx * 0.029 * s, -0.105 * s, 1.578 * s)],
                    [0.0020 * s, 0.0026 * s, 0.0016 * s], skin, sides=5, depth=0.55)
        weight_all(fold, arm, "head")
    # a soft crease under the lower lip
    chin_crease = tube("ChinCrease",
                       [(-0.022 * s, -0.107 * s, czm - 0.014 * s),
                        (0, -0.111 * s, czm - 0.016 * s),
                        (0.022 * s, -0.107 * s, czm - 0.014 * s)],
                       [0.0012 * s, 0.0017 * s, 0.0012 * s], skin, sides=5, depth=0.55)
    weight_all(chin_crease, arm, "head")
    teeth_obj = add_box("Teeth", (0, -0.108 * s, czm + 0.0030 * s),
                        (0.018 * s, 0.0025 * s, 0.0028 * s), teeth, bevel=0.0012)
    tongue_obj = add_sphere("Tongue", (0, -0.106 * s, czm - 0.0020 * s),
                            (0.012 * s, 0.0035 * s, 0.0035 * s), tongue, segments=12, rings=8)
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
    mouth_line = tube("MouthLine",
                      [(-0.028 * s, -0.1155 * s, czm),
                       (-0.012 * s, -0.1165 * s, czm + 0.0006 * s),
                       (0, -0.1170 * s, czm + 0.0008 * s),
                       (0.012 * s, -0.1165 * s, czm + 0.0006 * s),
                       (0.028 * s, -0.1155 * s, czm)],
                      [0.0010 * s, 0.0014 * s, 0.0015 * s, 0.0014 * s, 0.0010 * s],
                      mats["dark"], sides=5, depth=0.45)
    weight_all(mouth_line, arm, "head")

    # Hair: a skull-hugging cap plus a layered fringe.  The fringe covers the
    # cap/head intersection, which is what made the old bowl cut look jagged.
    hair_cap = add_sphere("HairCap", (0, 0.010 * s, 1.702 * s),
                          (0.136 * s, 0.124 * s, 0.108 * s), hair,
                          segments=28, rings=18)
    weight_all(hair_cap, arm, "head")
    for v in hair_cap.data.vertices:
        if v.co.z < -0.020 * s and v.co.y < 0:
            v.co.y += 0.060 * s
    # Layered flat locks instead of a solid visor: each lock is an ellipsoid
    # flattened against the forehead.  Male hair sweeps to the left; female
    # hair parts in the middle.
    if g == "male":
        locks = 5
        for i in range(locks):
            u = (i / (locks - 1)) * 2.0 - 1.0
            top = Vector((0.035 * s + u * 0.018 * s, -0.070 * s, 1.746 * s))
            tip = Vector((-0.072 * s + u * 0.052 * s,
                          -0.128 * s,
                          1.682 * s + abs(u) * 0.005 * s))
            d = tip - top
            c = (top + tip) * 0.5
            lock = add_oriented_sphere(f"Fringe.{i}", c,
                                       (0.022 * s, 0.0085 * s, d.length * 0.58),
                                       hair, d, (0, 1, 0),
                                       segments=18, rings=10)
            weight_all(lock, arm, "head")
    else:
        locks = 7
        for i in range(locks):
            u = (i / (locks - 1)) * 2.0 - 1.0
            top = Vector((u * 0.018 * s, -0.070 * s, 1.746 * s))
            tip = Vector((u * 0.098 * s,
                          -0.126 * s - 0.003 * s * (1.0 - abs(u)),
                          1.680 * s - 0.005 * s * (1.0 - abs(u))))
            d = tip - top
            c = (top + tip) * 0.5
            lock = add_oriented_sphere(f"Fringe.{i}", c,
                                       (0.023 * s, 0.0080 * s, d.length * 0.58),
                                       hair, d, (0, 1, 0),
                                       segments=18, rings=10)
            weight_all(lock, arm, "head")

    if cfg["hair_style"] in ("bob", "ponytail"):
        back = add_sphere("HairBack", (0, 0.065 * s, 1.585 * s),
                          (0.132 * s, 0.092 * s, 0.165 * s), hair,
                          segments=22, rings=16)
        weight_all(back, arm, "head")
        for side, sx in (("L", 1), ("R", -1)):
            strand = tube(f"HairSide.{side}",
                          [(sx * 0.112 * s, 0.015 * s, 1.670 * s),
                           (sx * 0.122 * s, 0.030 * s, 1.560 * s),
                           (sx * 0.112 * s, 0.035 * s, 1.480 * s)],
                          [0.024 * s, 0.026 * s, 0.016 * s], hair, sides=10, depth=0.9)
            weight_all(strand, arm, "head")
    if cfg["hair_style"] == "ponytail":
        tail = tube("HairTail",
                    [(0, 0.115 * s, 1.700 * s),
                     (0, 0.155 * s, 1.600 * s),
                     (0, 0.170 * s, 1.500 * s)],
                    [0.035 * s, 0.045 * s, 0.014 * s], hair, sides=12, depth=1.0)
        weight_all(tail, arm, "head")
    if cfg["hair_style"] == "bun":
        bun = add_sphere("HairBun", (0, 0.110 * s, 1.715 * s),
                         (0.052 * s, 0.052 * s, 0.052 * s), hair,
                         segments=18, rings=14)
        weight_all(bun, arm, "head")
    if cfg["hair_style"] == "short":
        for side, sx in (("L", 1), ("R", -1)):
            sideburn = add_box(f"Sideburn.{side}", (sx * 0.118 * s, 0.004 * s, 1.625 * s),
                               (0.018 * s, 0.025 * s, 0.040 * s), hair, bevel=0.004, smooth=True)
            weight_all(sideburn, arm, "head")

    # glasses / hood are optional accessories, kept as separate meshes
    if cfg.get("glasses"):
        for side, sx in (("L", 1), ("R", -1)):
            frame = add_torus(f"Glass.{side}", (sx * 0.039 * s, -0.124 * s, 1.648 * s),
                              0.018 * s, 0.0016 * s, dark)
            weight_all(frame, arm, "head")
            temple = tube(f"GlassTemple.{side}",
                          [(sx * 0.056 * s, -0.122 * s, 1.650 * s),
                           (sx * 0.100 * s, -0.060 * s, 1.650 * s),
                           (sx * 0.116 * s, 0.002 * s, 1.646 * s)],
                          [0.0012 * s, 0.0012 * s, 0.0010 * s], dark,
                          sides=5, depth=0.7)
            weight_all(temple, arm, "head")
        bridge = add_box("GlassBridge", (0, -0.124 * s, 1.650 * s),
                         (0.016 * s, 0.0022 * s, 0.0022 * s), dark, bevel=0.001)
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
        (1.06 * s, waist * 0.86, 0.100 * s, 0.092 * s, 0),
        (1.16 * s, waist * 0.98, 0.106 * s + bust * 0.30, 0.098 * s, 0),
        (1.26 * s, sh * 1.00, 0.112 * s + bust, 0.100 * s, 0),
        (1.34 * s, sh * 1.18, 0.104 * s, 0.098 * s, 0),
        (1.365 * s, sh * 1.10, 0.096 * s, 0.092 * s, 0),
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
    top_rings = [(0.94 * s, hip * 1.72, 0.140 * s, 0.130 * s, 0)]
    top_rings += [(z, rx + 0.016 * s, rf + 0.014 * s, rb + 0.014 * s, y)
                  for z, rx, rf, rb, y in rings if z >= 0.98 * s]

    tee = loft("top_tee", top_rings, top, segments=20)
    weight_z(tee, arm)
    shirt = loft("top_shirt", top_rings, top, segments=20)
    weight_z(shirt, arm)
    hoodie = loft("top_hoodie", top_rings, top, segments=20)
    weight_z(hoodie, arm)

    # collars and hoodie details
    tee_collar = add_torus("Collar.Tee", (0, 0.005 * s, 1.385 * s), 0.074 * s, 0.010 * s,
                           top, rotation=(0, 0, 0))
    weight_all(tee_collar, arm, "neck")
    collar = add_torus("Collar.Shirt", (0, 0.005 * s, 1.385 * s), 0.077 * s, 0.014 * s,
                       top, rotation=(0, 0, 0))
    weight_all(collar, arm, "neck")
    hood_collar = add_torus("Collar.Hoodie", (0, 0.005 * s, 1.383 * s), 0.078 * s, 0.012 * s,
                            top, rotation=(0, 0, 0))
    weight_all(hood_collar, arm, "neck")
    # Hood down: a rolled U-fold behind the neck plus a soft drape.
    # A sphere here reads as a ball, so the hood is made from an arc tube
    # and a flattened back panel.
    hpts = []
    hrad = []
    for i in range(9):
        a = math.radians(15 + i * 18)
        hpts.append((0.118 * s * math.cos(a), 0.050 * s + 0.108 * s * math.sin(a),
                     1.365 * s + 0.010 * s * math.sin(a)))
        hrad.append(0.035 * s)
    hood = tube("Hood", hpts, hrad, top, sides=10, depth=0.82)
    weight_all(hood, arm, "chest")
    drape = add_sphere("HoodDrape", (0, 0.135 * s, 1.265 * s),
                       (0.135 * s, 0.040 * s, 0.115 * s), top, segments=22, rings=14)
    weight_all(drape, arm, "chest")
    lining = add_sphere("HoodLining", (0, 0.112 * s, 1.285 * s),
                        (0.106 * s, 0.018 * s, 0.085 * s), mats["dark"], segments=18, rings=12)
    weight_all(lining, arm, "chest")
    pocket = add_box("Pocket", (0, -0.118 * s, 1.080 * s),
                     (0.180 * s, 0.022 * s, 0.065 * s), top, bevel=0.015, smooth=True)
    weight_z(pocket, arm, [(1.04, "hips"), (1.14, "spine"), (99, "chest")])
    # shirt placket + buttons
    placket = add_box("Placket", (0, -0.116 * s, 1.185 * s),
                      (0.014 * s, 0.004 * s, 0.205 * s), top, bevel=0.002, smooth=True)
    weight_z(placket, arm, [(1.04, "hips"), (1.14, "spine"), (99, "chest")])
    for i in range(4):
        button = add_sphere(f"Button.{i}", (0, -0.119 * s, (1.10 + i * 0.075) * s),
                            (0.0055 * s, 0.0022 * s, 0.0055 * s),
                            mats["metal"], segments=10, rings=8)
        weight_z(button, arm, [(1.04, "hips"), (1.14, "spine"), (99, "chest")])
    # hoodie drawstrings with metal tips
    for side, sx in (("L", 1), ("R", -1)):
        cord = tube(f"Drawstring.{side}",
                    [(sx * 0.018 * s, -0.104 * s, 1.370 * s),
                     (sx * 0.022 * s, -0.112 * s, 1.300 * s),
                     (sx * 0.026 * s, -0.116 * s, 1.235 * s)],
                    [0.0045 * s, 0.0040 * s, 0.0032 * s], top,
                    sides=6, depth=0.8)
        weight_all(cord, arm, "chest")
        tip = add_box(f"DrawstringTip.{side}", (sx * 0.026 * s, -0.116 * s, 1.230 * s),
                      (0.006 * s, 0.006 * s, 0.012 * s), mats["metal"],
                      bevel=0.0015, smooth=True)
        weight_all(tip, arm, "chest")

    # sleeves
    for side, sx in (("L", 1), ("R", -1)):
        wrist = Vector((sx * (sh + 0.30) * s, 0, 1.02 * s))
        elbow = Vector((sx * (sh + 0.17) * s, 0, 1.19 * s))
        s0 = Vector((sx * (sh - 0.085) * s, 0, 1.365 * s))   # inside the torso
        s1 = Vector((sx * (sh - 0.015) * s, 0, 1.340 * s))   # shoulder seam
        s2 = Vector((sx * (sh + 0.082) * s, 0, 1.292 * s))   # upper arm
        # The sleeve starts inside the torso; no sphere patch on the deltoid.
        # A sphere there is what made the old shoulders look like pads.
        # Low shoulder seam ridge: fills the seam without a sphere pad.
        for prefix in ("top_tee", "top_shirt", "top_hoodie"):
            seam = tube(f"{prefix}.Seam.{side}",
                        [(sx * (sh - 0.045) * s, 0, 1.358 * s),
                         (sx * (sh + 0.010) * s, 0, 1.348 * s),
                         (sx * (sh + 0.065) * s, 0, 1.322 * s)],
                        [0.014 * s, 0.018 * s, 0.013 * s], top, sides=7, depth=0.7,
                        cap=True)
            weight_mix(seam, arm, {"shoulder." + side: 0.55, "upperArm." + side: 0.45})
        # Flattened cover over the sleeve/torso seam (a sphere here turns into
        # the shoulder-pad look; a squashed ellipsoid reads as a fabric seam).
        for prefix in ("top_tee", "top_shirt", "top_hoodie"):
            pad = add_sphere(f"{prefix}.ShoulderPad.{side}",
                             (sx * (sh - 0.018) * s, 0, 1.350 * s),
                             (0.070 * s, 0.058 * s, 0.032 * s), top,
                             segments=16, rings=10)
            weight_mix(pad, arm, {"shoulder." + side: 0.55, "upperArm." + side: 0.45})
        # short sleeve: three rings near the shoulder keep the cloth attached
        tee_sleeve = tube(f"top_tee.Sleeve.{side}",
                          [s0, s1, s2],
                          [0.086 * s, 0.078 * s, 0.068 * s], top, sides=16, depth=0.92,
                          weights=[{"shoulder." + side: 0.70, "chest": 0.30},
                                   {"shoulder." + side: 0.40, "upperArm." + side: 0.60},
                                   {"upperArm." + side: 1.0}],
                          cap=True)
        bind(tee_sleeve, arm)
        tee_cuff = add_torus(f"top_tee.Cuff.{side}",
                             (sx * (sh + 0.090) * s, 0, 1.290 * s),
                             0.069 * s, 0.007 * s, top, rotation=(0, 0, 0))
        weight_all(tee_cuff, arm, "upperArm." + side)
        # long sleeve (shirt + hoodie)
        for prefix in ("top_shirt", "top_hoodie"):
            sl = tube(f"{prefix}.Sleeve.{side}",
                      [s0, s1, s2, elbow,
                       elbow + (wrist - elbow) * 0.72, wrist],
                      [0.086 * s, 0.078 * s, 0.068 * s, 0.056 * s, 0.049 * s, 0.045 * s],
                      top, sides=16, depth=0.92, cap=False,
                      weights=[{"shoulder." + side: 0.70, "chest": 0.30},
                               {"shoulder." + side: 0.40, "upperArm." + side: 0.60},
                               {"upperArm." + side: 1.0},
                               {"upperArm." + side: 0.25, "lowerArm." + side: 0.75},
                               {"lowerArm." + side: 1.0},
                               {"lowerArm." + side: 0.80, "hand." + side: 0.20}])
            bind(sl, arm)
        cuff = add_torus(f"top_shirt.Cuff.{side}", (sx * (sh + 0.292) * s, 0, 1.035 * s),
                         0.048 * s, 0.010 * s, top, rotation=(0, 0, 0))
        weight_all(cuff, arm, "lowerArm." + side)
        hcuff = add_torus(f"top_hoodie.Cuff.{side}", (sx * (sh + 0.292) * s, 0, 1.035 * s),
                          0.050 * s, 0.011 * s, top, rotation=(0, 0, 0))
        weight_all(hcuff, arm, "lowerArm." + side)

    # ── bottoms ────────────────────────────────────────────────────────────
    def pants_object(prefix, bottom_z):
        # A pelvis shell (not just two leg tubes) closes the crotch and covers
        # the skin between the legs.  The legs continue below it.
        pelvis = loft(f"{prefix}.Pelvis",
                      [(0.78 * s, hip * 1.55, 0.112 * s, 0.104 * s, 0),
                       (0.86 * s, hip * 1.78, 0.132 * s, 0.120 * s, 0),
                       (0.94 * s, hip * 1.66, 0.132 * s, 0.124 * s, 0)],
                      bottom, segments=20)
        weight_all(pelvis, arm, "hips")
        band = loft(f"{prefix}.Waistband",
                    [(0.925 * s, hip * 1.58, 0.128 * s, 0.120 * s, 0),
                     (0.960 * s, hip * 1.56, 0.126 * s, 0.118 * s, 0)],
                    mats["belt"], segments=20)
        weight_all(band, arm, "hips")
        for side, sx in (("L", 1), ("R", -1)):
            pts = [(sx * hip, 0, 0.94 * s),
                   (sx * hip, 0, 0.78 * s),
                   (sx * hip, 0, 0.54 * s),
                   (sx * hip, 0, bottom_z)]
            leg = tube(f"{prefix}.Leg.{side}", pts,
                       [0.094 * s, 0.086 * s, 0.075 * s, 0.067 * s],
                       bottom, sides=12, depth=0.95,
                       weights=[{"upperLeg." + side: 1.0},
                                {"upperLeg." + side: 1.0},
                                {"upperLeg." + side: 0.35, "lowerLeg." + side: 0.65},
                                {"lowerLeg." + side: 1.0}])
            bind(leg, arm)
            cuff = add_torus(f"{prefix}.Cuff.{side}", (sx * hip, 0, bottom_z + 0.018 * s),
                             0.070 * s, 0.008 * s, bottom, rotation=(0, 0, 0))
            weight_all(cuff, arm, ("upperLeg." if bottom_z > 0.55 * s else "lowerLeg.") + side)
        return pelvis

    pants_object("bottom_pants", 0.12 * s)
    pants_object("bottom_shorts", 0.58 * s)
    # skirt with a few soft pleats
    skirt = loft("bottom_skirt",
                 [(0.58 * s, 0.245 * s, 0.165 * s, 0.165 * s, 0),
                  (0.74 * s, 0.215 * s, 0.146 * s, 0.146 * s, 0),
                  (0.88 * s, 0.185 * s, 0.126 * s, 0.116 * s, 0),
                  (0.94 * s, hip * 1.62, 0.128 * s, 0.120 * s, 0)],
                 bottom, segments=32)
    for v in skirt.data.vertices:
        if v.co.z < 0.96 * s:
            ang = math.atan2(v.co.y, v.co.x)
            f = 1.0 + 0.012 * math.cos(6.0 * ang)
            v.co.x *= f
            v.co.y *= f
    weight_all(skirt, arm, "hips")
    # dress: top + skirt in one material
    dress_top = loft("dress.Top", top_rings, mats["dress"], segments=20)
    weight_z(dress_top, arm)
    dress_skirt = loft("dress.Skirt",
                       [(0.56 * s, 0.240 * s, 0.165 * s, 0.165 * s, 0),
                        (0.78 * s, 0.190 * s, 0.135 * s, 0.135 * s, 0),
                        (0.94 * s, hip * 1.60, 0.120 * s, 0.110 * s, 0)],
                       mats["dress"], segments=32)
    for v in dress_skirt.data.vertices:
        if v.co.z < 0.96 * s:
            ang = math.atan2(v.co.y, v.co.x)
            f = 1.0 + 0.012 * math.cos(6.0 * ang)
            v.co.x *= f
            v.co.y *= f
    weight_all(dress_skirt, arm, "hips")
    for side, sx in (("L", 1), ("R", -1)):
        sleeve = tube(f"dress.Sleeve.{side}",
                      [(sx * (sh - 0.035) * s, 0, 1.36 * s), (sx * (sh + 0.10) * s, 0, 1.24 * s)],
                      [0.075 * s, 0.062 * s], mats["dress"], sides=16, depth=0.9, cap=False,
                      weights=[{"upperArm." + side: 1.0}] * 2)
        bind(sleeve, arm)

    # ── shoes ──────────────────────────────────────────────────────────────
    for side, sx in (("L", 1), ("R", -1)):
        # sneaker
        sole = add_box(f"shoes_sneaker.Sole.{side}", (sx * hip, -0.040 * s, 0.014 * s),
                       (0.090 * s, 0.195 * s, 0.026 * s), mats["sole"],
                       bevel=0.010, smooth=True)
        weight_all(sole, arm, "foot." + side)
        base = add_box(f"shoes_sneaker.{side}", (sx * hip, -0.045 * s, 0.065 * s),
                       (0.080 * s, 0.170 * s, 0.080 * s), shoe,
                       bevel=0.030, smooth=True)
        weight_all(base, arm, "foot." + side)
        toe = add_sphere(f"shoes_sneaker.Toe.{side}", (sx * hip, -0.128 * s, 0.062 * s),
                         (0.078 * s, 0.050 * s, 0.045 * s), shoe,
                         segments=14, rings=10)
        weight_all(toe, arm, "toe." + side)
        heel = add_box(f"shoes_sneaker.Heel.{side}", (sx * hip, 0.055 * s, 0.065 * s),
                       (0.070 * s, 0.030 * s, 0.070 * s), shoe,
                       bevel=0.010, smooth=True)
        weight_all(heel, arm, "foot." + side)
        tongue = add_box(f"shoes_sneaker.Tongue.{side}", (sx * hip, -0.060 * s, 0.105 * s),
                         (0.038 * s, 0.055 * s, 0.010 * s), shoe,
                         bevel=0.004, smooth=True)
        weight_all(tongue, arm, "foot." + side)
        for i, yy in enumerate((-0.095, -0.070, -0.045)):
            lace = add_box(f"shoes_sneaker.Lace.{i}.{side}",
                           (sx * hip, yy * s, 0.112 * s),
                           (0.042 * s, 0.006 * s, 0.005 * s), mats["lace"],
                           bevel=0.0015, smooth=True)
            weight_all(lace, arm, "foot." + side)

        # boot
        bsole = add_box(f"shoes_boot.Sole.{side}", (sx * hip, -0.040 * s, 0.016 * s),
                        (0.094 * s, 0.200 * s, 0.030 * s), mats["sole"],
                        bevel=0.010, smooth=True)
        weight_all(bsole, arm, "foot." + side)
        boot = add_box(f"shoes_boot.{side}", (sx * hip, -0.035 * s, 0.085 * s),
                       (0.090 * s, 0.170 * s, 0.140 * s), shoe,
                       bevel=0.030, smooth=True)
        weight_all(boot, arm, "foot." + side)
        btoe = add_box(f"shoes_boot.Toe.{side}", (sx * hip, -0.120 * s, 0.058 * s),
                       (0.082 * s, 0.085 * s, 0.058 * s), shoe, bevel=0.025, smooth=True)
        weight_all(btoe, arm, "toe." + side)
        shaft = tube(f"shoes_boot.Shaft.{side}",
                     [(sx * hip, 0, 0.13 * s), (sx * hip, 0, 0.27 * s)],
                     [0.076 * s, 0.070 * s], shoe, sides=16, depth=0.92,
                     cap=False)
        weight_all(shaft, arm, "lowerLeg." + side)

    return body


# ── arms / hands / legs ─────────────────────────────────────────────────────

def build_arms(cfg, arm, mats):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    skin, top = mats["skin"], mats["top"]
    for side, sx in (("L", 1), ("R", -1)):
        should = Vector((sx * sh, 0, 1.335 * s))
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
        hand = build_hand(side, sx, wrist, skin, arm, s)
        # a small elbow bump is enough; the tapered tube handles the rest
    return True


def build_hand(side, sx, wrist, skin, arm, s):
    """Relaxed hand in A-pose: palm faces the thigh, fingers point down the
    arm line, thumb sits on the forward edge.  The palm's thin axis is X and
    its width runs front-to-back, which is what makes the old version look
    like the hands were screwed on backwards."""
    d = Vector((sx * 0.06, 0, -0.08)).normalized()
    palm_c = wrist + d * 0.048 * s
    parts = []
    palm = add_oriented_sphere(f"HandPalm.{side}", palm_c,
                               (0.033 * s, 0.052 * s, 0.060 * s), skin,
                               d, (0, sx, 0), segments=18, rings=12)
    assign_group(palm, f"hand.{side}")
    parts.append(palm)

    # Four fingers across the palm width (front-to-back), with a slight curl
    # toward the palm so the hand reads as relaxed instead of flat.
    fingers = [
        (-0.029, 0.046, 0.0122),  # index (thumb side, front)
        (-0.010, 0.050, 0.0128),  # middle
        (0.010, 0.046, 0.0122),   # ring
        (0.029, 0.041, 0.0112),   # little
    ]
    for i, (off, length, radius) in enumerate(fingers):
        base = palm_c + Vector((0, off * s, 0)) + d * (0.040 * s)
        mid = base + d * (length * 0.52 * s) + Vector((-sx * 0.003 * s, 0, 0))
        tip = mid + d * (length * 0.48 * s) + Vector((-sx * 0.008 * s, 0, off * 0.12 * s))
        finger = tube(f"Finger{i}.{side}", [base, mid, tip],
                      [radius * s, radius * 0.82 * s, radius * 0.56 * s],
                      skin, sides=8, depth=0.86)
        assign_group(finger, f"hand.{side}")
        parts.append(finger)
        knob = add_sphere(f"FingerTip{i}.{side}", tip,
                          (radius * 0.56 * s, radius * 0.56 * s, radius * 0.56 * s),
                          skin, segments=10, rings=8)
        assign_group(knob, f"hand.{side}")
        parts.append(knob)

    # Thumb on the forward edge: down, forward and slightly inward.
    tdir = Vector((-sx * 0.22, -0.52, -0.82)).normalized()
    base = palm_c + Vector((0, -0.038 * s, 0)) + d * (0.006 * s)
    mid = base + tdir * (0.026 * s)
    tip = mid + tdir * (0.024 * s) + Vector((0, -0.004 * s, 0))
    thumb = tube(f"Thumb.{side}", [base, mid, tip],
                 [0.013 * s, 0.0105 * s, 0.0078 * s], skin, sides=9, depth=0.9)
    assign_group(thumb, f"hand.{side}")
    parts.append(thumb)
    tknob = add_sphere(f"ThumbTip.{side}", tip,
                       (0.0078 * s, 0.0078 * s, 0.0078 * s), skin,
                       segments=10, rings=8)
    assign_group(tknob, f"hand.{side}")
    parts.append(tknob)

    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    hand = bpy.context.object
    hand.name = f"Hand.{side}"
    # NO extra rotation around the arm axis.  The palm normal already faces
    # the thigh, fingers follow the forearm downward and the thumb points
    # forward (-Y).  Any extra roll turns the fingers backwards (bug #hand-1).
    bind(hand, arm)
    return hand


def build_legs(cfg, arm, mats):
    s = cfg["scale"]
    hip = cfg["hip"] * s
    skin, bottom, shoe = mats["skin"], mats["bottom"], mats["shoe"]
    for side, sx in (("L", 1), ("R", -1)):
        top = Vector((sx * hip, 0, 0.94 * s))
        knee = Vector((sx * hip, 0, 0.53 * s))
        ankle = Vector((sx * hip, 0, 0.11 * s))
        pts = [top, top.lerp(knee, 0.5), knee, knee.lerp(ankle, 0.55), ankle]
        radii = [0.070 * s, 0.069 * s, 0.060 * s, 0.054 * s, 0.043 * s]
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
    """Body-shape morphs shared by the torso, clothing and accessories.

    The old version used local vertex coordinates, which was wrong for
    objects whose origin sits at their location (spheres, tori, boxes).  Work
    in world space and convert back, so sleeves, cuffs, belt and skirt all
    follow the torso.
    """
    s = cfg["scale"]
    mw = obj.matrix_world.copy()
    inv = mw.inverted()
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    for name in ("bodyShoulder", "bodyChest", "bodyWaist", "bodyHips", "bodyBelly"):
        key = obj.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for i, v in enumerate(obj.data.vertices):
            w = mw @ v.co
            z = w.z
            co = w.copy()
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
            key.data[i].co = inv @ co


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
    for key in ("skin", "hair", "top", "bottom", "shoe", "dress", "belt",
                "lip", "eye"):
        if key in cfg:
            cfg[key] = _color(cfg[key])

    mats = {
        "skin": material("Skin", cfg["skin"], 0.78),
        "hair": material("Hair", cfg["hair"], 0.9),
        "hair_dark": material("HairDark", tuple(c * 0.72 for c in cfg["hair"]), 0.9),
        "top": material("Top", cfg["top"], 0.8),
        "bottom": material("Bottom", cfg["bottom"], 0.85),
        "shoe": material("Shoes", cfg["shoe"], 0.7),
        "sole": material("Sole", (0.06, 0.06, 0.07), 0.9),
        "belt": material("Belt", cfg.get("belt", (0.09, 0.08, 0.07)), 0.75),
        "lace": material("Lace", (0.88, 0.86, 0.80), 0.7),
        "dress": material("Dress", cfg.get("dress", cfg["top"]), 0.8),
        "white": material("EyeWhite", (0.96, 0.96, 0.93), 0.32),
        "iris": material("Iris", cfg["eye"], 0.4),
        "dark": material("MouthDark", (0.10, 0.035, 0.03), 0.9),
        "lip": material("Lips", cfg["lip"], 0.65),
        "teeth": material("Teeth", (0.18, 0.09, 0.075), 0.55),
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
    skip = ("Head", "Ear.", "EyeWhite", "Iris.", "Pupil.", "Catchlight.",
            "Blink.", "BlinkLash.", "Brow.", "Nose", "Mouth", "UpperLip",
            "LowerLip", "LipCorner.", "Hair", "Fringe", "Glass", "Sideburn.",
            "Arm.", "Hand.", "Leg.", "Knee.", "Ankle.", "Neck", "shoes_",
            "Shoe")
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name.startswith(skip):
            continue
        add_body_shape_keys(obj, cfg)

    # metadata actions
    make_action(arm, "idle", [(0, {"chest": (0, 0, 0)}), (60, {"chest": (0.015, 0, 0)}), (120, {"chest": (0, 0, 0)})])
    make_action(arm, "talk", [(0, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
                              (30, {"chest": (0.01, 0.02, 0), "head": (0.02, 0.04, 0)}),
                              (60, {"chest": (0, -0.01, 0), "head": (-0.01, -0.03, 0)}),
                              (120, {"chest": (0, 0, 0), "head": (0, 0, 0)})])

    scene.frame_start = 0
    scene.frame_end = 120
    out = SRC / f"{cfg['name']}_v3.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"saved {out}")
    return out


CHARACTERS = [
    {
        "name": "mark", "gender": "male", "scale": 1.00,
        "shoulder": 0.168, "hip": 0.097, "waist": 0.137, "bust": 0.0,
        "skin": (0.74, 0.53, 0.40), "lip": (0.55, 0.26, 0.24),
        "hair": (0.09, 0.065, 0.05), "eye": (0.18, 0.35, 0.26),
        "top": (0.14, 0.28, 0.48), "bottom": (0.16, 0.17, 0.20),
        "dress": (0.14, 0.28, 0.48), "shoe": (0.12, 0.12, 0.13),
        "belt": (0.08, 0.07, 0.06),
        "hair_style": "short", "glasses": False,
    },
    {
        "name": "mira", "gender": "female", "scale": 0.945,
        "shoulder": 0.143, "hip": 0.118, "waist": 0.116, "bust": 0.055,
        "skin": (0.86, 0.66, 0.53), "lip": (0.62, 0.28, 0.28),
        "hair": (0.35, 0.13, 0.06), "eye": (0.20, 0.42, 0.55),
        "top": (0.18, 0.38, 0.32), "bottom": (0.30, 0.18, 0.26),
        "dress": (0.42, 0.16, 0.24), "shoe": (0.32, 0.16, 0.12),
        "belt": (0.12, 0.08, 0.06),
        "hair_style": "ponytail", "glasses": False,
    },
]


def _cli():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", action="append", default=[],
                    help="JSON preset or list of presets (repeatable)")
    ap.add_argument("--name", default=None, help="only this character id")
    return ap.parse_args(argv)


def load_configs(args):
    configs = []
    for path in args.config:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict) and "characters" in data:
            data = data["characters"]
        if isinstance(data, dict):
            data = [data]
        configs.extend(data)
    if not configs:
        configs = list(CHARACTERS)
    if args.name:
        configs = [c for c in configs if c.get("name") == args.name]
    if not configs:
        raise SystemExit("no character configs selected")
    return configs


if __name__ == "__main__":
    for cfg in load_configs(_cli()):
        build_character(cfg)
