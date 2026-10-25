"""Generate two stylized low-poly humanoid characters for SceneRig.

Run:
    blender --background --python scripts/blender/make_poly_characters.py

Writes assets/characters/src/{mark,mira}.blend. Export with
scripts/blender/scene_rig_export.py.

Design: rigid/segmented low-poly body with canonical 21-bone humanoid rig,
Oculus-15 viseme shape keys on the mouth, eye-blink keys, simple idle/talk
actions. Characters are CC0 originals made from primitives.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "characters" / "src"
SRC.mkdir(parents=True, exist_ok=True)


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


def apply_common(obj, mat, smooth=False):
    if mat:
        obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = smooth
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def add_sphere(name, loc, scale, mat, segments=16, rings=10, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_common(obj, mat, smooth)
    return obj


def add_cylinder(name, loc, radius, depth, mat, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=loc,
                                        rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply_common(obj, mat, False)
    return obj


def add_cylinder_between(name, p1, p2, radius, mat, vertices=10):
    a, b = Vector(p1), Vector(p2)
    d = b - a
    length = d.length
    if length < 1e-6:
        return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    apply_common(obj, mat, False)
    return obj


def add_box(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_common(obj, mat, False)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def add_torus(name, loc, major, minor, mat, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=16, minor_segments=8,
                                     location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply_common(obj, mat, True)
    return obj


def add_cone(name, loc, r1, r2, depth, mat, rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2,
                                    depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply_common(obj, mat, False)
    return obj


# ── rig ─────────────────────────────────────────────────────────────────────

def build_armature(cfg):
    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = bpy.context.object
    arm_obj.name = "Armature"
    arm = arm_obj.data
    arm.name = "SceneRig"
    for bone in list(arm.edit_bones):
        arm.edit_bones.remove(bone)

    created = {}

    def bone(name, head, tail, parent=None):
        eb = arm.edit_bones.new(name)
        eb.head = Vector((head[0] * s, head[1] * s, head[2] * s))
        eb.tail = Vector((tail[0] * s, tail[1] * s, tail[2] * s))
        eb.use_connect = False
        if parent:
            eb.parent = created[parent]
        created[name] = eb
        return eb

    bone("root", (0, 0, 0), (0, 0, 0.12))
    bone("hips", (0, 0, 0.92), (0, 0, 1.04), "root")
    bone("spine", (0, 0, 1.04), (0, 0, 1.18), "hips")
    bone("chest", (0, 0, 1.18), (0, 0, 1.38), "spine")
    bone("neck", (0, 0, 1.38), (0, 0, 1.50), "chest")
    bone("head", (0, 0, 1.50), (0, 0, 1.72), "neck")
    bone("jaw", (0, -0.055, 1.60), (0, -0.085, 1.53), "head")
    for side, sx in (("L", 1), ("R", -1)):
        bone(f"eye.{side}", (sx * 0.05, -0.105, 1.65), (sx * 0.05, -0.125, 1.65), "head")
        bone(f"shoulder.{side}", (0, 0, 1.36), (sx * sh, 0, 1.36), "chest")
        bone(f"upperArm.{side}", (sx * sh, 0, 1.36), (sx * (sh + 0.19), 0, 1.18), f"shoulder.{side}")
        bone(f"lowerArm.{side}", (sx * (sh + 0.19), 0, 1.18), (sx * (sh + 0.35), 0, 1.02), f"upperArm.{side}")
        bone(f"hand.{side}", (sx * (sh + 0.35), 0, 1.02), (sx * (sh + 0.43), 0, 0.96), f"lowerArm.{side}")
        bone(f"upperLeg.{side}", (sx * hip, 0, 0.94), (sx * hip, 0, 0.52), "hips")
        bone(f"lowerLeg.{side}", (sx * hip, 0, 0.52), (sx * hip, 0, 0.10), f"upperLeg.{side}")
        bone(f"foot.{side}", (sx * hip, 0, 0.10), (sx * hip, -0.10, 0.04), f"lowerLeg.{side}")
        bone(f"toe.{side}", (sx * hip, -0.10, 0.04), (sx * hip, -0.22, 0.04), f"foot.{side}")

    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm_obj


def weight(obj, arm, groups: dict[str, float]):
    total = sum(groups.values()) or 1.0
    for name, w in groups.items():
        vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        vg.add(list(range(len(obj.data.vertices))), w / total, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()


def weight_by_z(obj, arm):
    """Torso/jacket: blend hips/spine/chest by world Z."""
    groups = {
        "hips": obj.vertex_groups.new(name="hips"),
        "spine": obj.vertex_groups.new(name="spine"),
        "chest": obj.vertex_groups.new(name="chest"),
    }
    # bone heights in this character's scale are encoded in the mesh already
    zs = sorted(v.co.z for v in obj.data.vertices)
    if not zs:
        return
    zmin, zmax = zs[0], zs[-1]
    # 0..0.38 -> hips; 0.38..0.72 -> spine; 0.72..1 -> chest
    for v in obj.data.vertices:
        u = (v.co.z - zmin) / (zmax - zmin + 1e-6)
        if u <= 0.42:
            groups["hips"].add([v.index], 1.0, "REPLACE")
        elif u <= 0.62:
            t = (u - 0.42) / 0.20
            groups["hips"].add([v.index], 1 - t, "REPLACE")
            groups["spine"].add([v.index], t, "REPLACE")
        elif u <= 0.82:
            t = (u - 0.62) / 0.20
            groups["spine"].add([v.index], 1 - t, "REPLACE")
            groups["chest"].add([v.index], t, "REPLACE")
        else:
            groups["chest"].add([v.index], 1.0, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()


def join_mouth(parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "Mouth"
    return obj


# ── lip-sync shape keys ─────────────────────────────────────────────────────

VISEME_SCALE = {
    "viseme_sil": (1.00, 1.00, 0.000),
    "viseme_PP":  (0.85, 0.70, 0.001),
    "viseme_FF":  (0.95, 0.80, 0.001),
    "viseme_TH":  (0.95, 1.40, 0.001),
    "viseme_DD":  (1.00, 2.20, 0.000),
    "viseme_kk":  (0.95, 2.50, 0.000),
    "viseme_CH":  (0.85, 1.60, 0.000),
    "viseme_SS":  (1.22, 1.00, 0.000),
    "viseme_nn":  (1.00, 1.80, 0.000),
    "viseme_RR":  (0.90, 1.90, 0.000),
    "viseme_aa":  (1.20, 3.40, -0.001),
    "viseme_E":   (1.35, 2.20, 0.000),
    "viseme_I":   (1.25, 1.50, 0.000),
    "viseme_O":   (0.85, 2.80, -0.001),
    "viseme_U":   (0.70, 2.00, 0.000),
    "jawOpen":    (1.00, 3.60, -0.002),
    "mouthSmile": (1.30, 1.10, 0.001),
    "mouthFrown": (0.90, 1.10, -0.001),
}


def add_mouth_shape_keys(obj, center=None):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    # The joined object's origin is at the mouth; shape keys must use the
    # LOCAL centre, not the world centre, or the morph moves the mouth away.
    center = Vector((0, 0, 0))
    for v in obj.data.vertices:
        center += v.co
    center /= max(1, len(obj.data.vertices))
    # vertices that belong to the tongue
    tongue_group = obj.vertex_groups.get("part_tongue")
    tongue = set()
    if tongue_group:
        gi = tongue_group.index
        for v in obj.data.vertices:
            for g in v.groups:
                if g.group == gi and g.weight > 0.5:
                    tongue.add(v.index)
    c = Vector(center)
    for name, (sx, sz, dz) in VISEME_SCALE.items():
        key = obj.shape_key_add(name=name, from_mix=False)
        key.slider_min = 0.0
        key.slider_max = 1.0
        key.value = 0.0
        for i, v in enumerate(obj.data.vertices):
            co = key.data[i].co.copy()
            co.x = c.x + (co.x - c.x) * sx
            co.z = c.z + (co.z - c.z) * sz + dz
            if name == "viseme_TH" and i in tongue:
                co.y -= 0.004
                co.z += 0.003
            key.data[i].co = co


def add_blink_shape_keys(obj, center, key_name):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    key = obj.shape_key_add(name=key_name, from_mix=False)
    key.value = 0.0
    # Local centre of this eye mesh (its object origin is at the eye).
    c = Vector((0, 0, 0))
    for v in obj.data.vertices:
        c += v.co
    c /= max(1, len(obj.data.vertices))
    for i, v in enumerate(obj.data.vertices):
        co = key.data[i].co.copy()
        co.z = c.z + (co.z - c.z) * 0.12
        co.y = c.y + (co.y - c.y) * 0.55
        key.data[i].co = co


# ── character ───────────────────────────────────────────────────────────────

def build_character(cfg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30
    scene.frame_start = 0
    scene.frame_end = 120

    s = cfg["scale"]
    sh = cfg["shoulder"] * s
    hip = cfg["hip"] * s
    skin = material("Skin", cfg["skin"], 0.8)
    hair = material("Hair", cfg["hair"], 0.9)
    top = material("Top", cfg["top"], 0.8)
    bottom = material("Bottom", cfg["bottom"], 0.85)
    shoe = material("Shoes", cfg["shoe"], 0.7)
    white = material("EyeWhite", (0.95, 0.95, 0.95), 0.35)
    iris = material("Iris", cfg["eye"], 0.4)
    dark = material("MouthDark", (0.10, 0.035, 0.03), 0.9)
    lip = material("Lips", cfg["lip"], 0.65)
    teeth = material("Teeth", (0.95, 0.94, 0.88), 0.35)
    tongue = material("Tongue", (0.72, 0.28, 0.30), 0.7)
    metal = material("Metal", (0.55, 0.57, 0.62), 0.35, 0.6)

    arm = build_armature(cfg)
    meshes = []

    def add(obj, mat, smooth=False):
        apply_common(obj, mat, smooth)
        meshes.append(obj)
        return obj

    # torso / jacket
    torso = add_cylinder("Jacket", (0, 0, 1.20 * s), 0.178 * s, 0.38 * s, top,
                         vertices=14)
    torso.scale.y = 0.70
    bpy.ops.object.select_all(action="DESELECT")
    torso.select_set(True)
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # pelvis / pants
    pelvis = add_sphere("Pelvis", (0, 0, 0.96 * s), (0.165 * s, 0.125 * s, 0.11 * s), bottom)
    weight(pelvis, arm, {"hips": 1.0})

    # neck + head
    neck = add_cylinder("Neck", (0, 0, 1.43 * s), 0.055 * s, 0.13 * s, skin)
    head = add_sphere("Head", (0, -0.005 * s, 1.61 * s),
                      (0.137 * s, 0.128 * s, 0.165 * s), skin, segments=20, rings=14)
    for side, sx in (("L", 1), ("R", -1)):
        ear = add_sphere(f"Ear.{side}", (sx * 0.135 * s, 0, 1.61 * s),
                         (0.022 * s, 0.012 * s, 0.032 * s), skin)
        weight(ear, arm, {"head": 1.0})
    # hair
    hair_cap = add_sphere("HairCap", (0, 0.022 * s, 1.675 * s),
                          (0.152 * s, 0.125 * s, 0.125 * s), hair, segments=18, rings=12)
    if cfg["hair_style"] == "bob":
        back = add_sphere("HairBack", (0, 0.065 * s, 1.56 * s),
                          (0.155 * s, 0.105 * s, 0.19 * s), hair)
        weight(back, arm, {"head": 1.0})
        for side, sx in (("L", 1), ("R", -1)):
            strand = add_cylinder_between(f"HairSide.{side}",
                                          (sx * 0.13 * s, 0.02 * s, 1.63 * s),
                                          (sx * 0.14 * s, 0.02 * s, 1.42 * s),
                                          0.035 * s, hair, vertices=8)
            weight(strand, arm, {"head": 1.0})
    else:
        # Short hair: the cap provides a clean hairline; no blocky fringe.
        pass

    # eyes, brows, nose
    for side, sx in (("L", 1), ("R", -1)):
        ex, ey, ez = sx * 0.043 * s, -0.124 * s, 1.655 * s
        eye = add_sphere(f"EyeWhite.{side}", (ex, ey, ez),
                         (0.018 * s, 0.010 * s, 0.022 * s), white)
        iris_obj = add_sphere(f"Iris.{side}", (ex, ey - 0.007 * s, ez),
                              (0.0085 * s, 0.004 * s, 0.0105 * s), iris, segments=12, rings=8)
        pupil = add_sphere(f"Pupil.{side}", (ex, ey - 0.009 * s, ez),
                           (0.0045 * s, 0.002 * s, 0.0055 * s), dark, segments=10, rings=6)
        blink_name = "eyeBlinkLeft" if side == "L" else "eyeBlinkRight"
        for part in (eye, iris_obj, pupil):
            weight(part, arm, {f"eye.{side}": 1.0})
            add_blink_shape_keys(part, (ex, ey, ez), blink_name)
        brow = add_box(f"Brow.{side}", (sx * 0.047 * s, -0.132 * s, 1.692 * s),
                       (0.023 * s, 0.006 * s, 0.004 * s), hair, bevel=0.0015)
        weight(brow, arm, {"head": 1.0})
    nose = add_sphere("Nose", (0, -0.142 * s, 1.625 * s),
                      (0.014 * s, 0.022 * s, 0.018 * s), skin, segments=12, rings=8)
    weight(nose, arm, {"head": 1.0})

    # mouth: cavity + lips + teeth + tongue -> one mesh with visemes
    mouth_center = (0, -0.136 * s, 1.5745 * s)
    cavity = add_sphere("MouthCavity", (0, -0.132 * s, 1.5745 * s),
                        (0.028 * s, 0.008 * s, 0.010 * s), dark, segments=16, rings=8)
    upper_lip = add_sphere("UpperLip", (0, -0.136 * s, 1.5800 * s),
                           (0.030 * s, 0.007 * s, 0.0045 * s), lip, segments=16, rings=8)
    lower_lip = add_sphere("LowerLip", (0, -0.136 * s, 1.5690 * s),
                           (0.031 * s, 0.007 * s, 0.0055 * s), lip, segments=16, rings=8)
    teeth_obj = add_box("Teeth", (0, -0.135 * s, 1.5780 * s),
                        (0.020 * s, 0.003 * s, 0.0030 * s), teeth, bevel=0.0012)
    tongue_obj = add_sphere("Tongue", (0, -0.134 * s, 1.5700 * s),
                            (0.012 * s, 0.004 * s, 0.0040 * s), tongue, segments=12, rings=8)
    for part in (cavity, upper_lip, lower_lip, teeth_obj, tongue_obj):
        part.vertex_groups.new(name="part_tongue").add(
            list(range(len(part.data.vertices))), 1.0, "REPLACE")
    # only the tongue should get the tongue group
    for part in (cavity, upper_lip, lower_lip, teeth_obj):
        vg = part.vertex_groups.get("part_tongue")
        if vg:
            vg.remove(list(range(len(part.data.vertices))))
    mouth = join_mouth([cavity, upper_lip, lower_lip, teeth_obj, tongue_obj])
    add_mouth_shape_keys(mouth, mouth_center)
    part_group = mouth.vertex_groups.get("part_tongue")
    if part_group:
        mouth.vertex_groups.remove(part_group)
    weight(mouth, arm, {"head": 1.0})
    meshes.append(mouth)

    # arms
    for side, sx in (("L", 1), ("R", -1)):
        shoulder = add_sphere(f"Shoulder.{side}", (sx * sh, 0, 1.36 * s),
                              (0.052 * s, 0.052 * s, 0.052 * s), top)
        weight(shoulder, arm, {f"shoulder.{side}": 0.7, "chest": 0.3})
        upper = add_cylinder_between(f"UpperArm.{side}",
                                     (sx * sh, 0, 1.36 * s),
                                     (sx * (sh + 0.19) * 1.0, 0, 1.18 * s),
                                     0.048 * s, top)
        weight(upper, arm, {f"upperArm.{side}": 1.0})
        elbow = add_sphere(f"Elbow.{side}", (sx * (sh + 0.19), 0, 1.18 * s),
                           (0.049 * s, 0.049 * s, 0.049 * s), top)
        weight(elbow, arm, {f"upperArm.{side}": 0.5, f"lowerArm.{side}": 0.5})
        lower = add_cylinder_between(f"LowerArm.{side}",
                                     (sx * (sh + 0.19), 0, 1.18 * s),
                                     (sx * (sh + 0.35), 0, 1.02 * s),
                                     0.042 * s, top)
        weight(lower, arm, {f"lowerArm.{side}": 1.0})
        wrist = add_sphere(f"Wrist.{side}", (sx * (sh + 0.35), 0, 1.02 * s),
                           (0.042 * s, 0.042 * s, 0.042 * s), skin)
        weight(wrist, arm, {f"lowerArm.{side}": 0.3, f"hand.{side}": 0.7})
        hand = add_sphere(f"Hand.{side}", (sx * (sh + 0.39), 0, 0.99 * s),
                          (0.038 * s, 0.030 * s, 0.050 * s), skin)
        weight(hand, arm, {f"hand.{side}": 1.0})

    # legs
    for side, sx in (("L", 1), ("R", -1)):
        hipj = add_sphere(f"Hip.{side}", (sx * hip, 0, 0.94 * s),
                          (0.058 * s, 0.058 * s, 0.058 * s), bottom)
        weight(hipj, arm, {"hips": 0.5, f"upperLeg.{side}": 0.5})
        thigh = add_cylinder_between(f"Thigh.{side}",
                                     (sx * hip, 0, 0.94 * s),
                                     (sx * hip, 0, 0.52 * s),
                                     0.062 * s, bottom)
        weight(thigh, arm, {f"upperLeg.{side}": 1.0})
        knee = add_sphere(f"Knee.{side}", (sx * hip, 0, 0.52 * s),
                          (0.060 * s, 0.060 * s, 0.060 * s), bottom)
        weight(knee, arm, {f"upperLeg.{side}": 0.5, f"lowerLeg.{side}": 0.5})
        shin = add_cylinder_between(f"Shin.{side}",
                                    (sx * hip, 0, 0.52 * s),
                                    (sx * hip, 0, 0.10 * s),
                                    0.052 * s, bottom)
        weight(shin, arm, {f"lowerLeg.{side}": 1.0})
        ankle = add_sphere(f"Ankle.{side}", (sx * hip, 0, 0.10 * s),
                           (0.050 * s, 0.050 * s, 0.050 * s), shoe)
        weight(ankle, arm, {f"lowerLeg.{side}": 0.3, f"foot.{side}": 0.7})
        shoe_obj = add_box(f"Shoe.{side}", (sx * hip, -0.035 * s, 0.045 * s),
                           (0.075 * s, 0.13 * s, 0.09 * s), shoe, bevel=0.012)
        weight(shoe_obj, arm, {f"foot.{side}": 1.0})
        toe_obj = add_box(f"Toe.{side}", (sx * hip, -0.145 * s, 0.045 * s),
                          (0.070 * s, 0.075 * s, 0.080 * s), shoe, bevel=0.010)
        weight(toe_obj, arm, {f"toe.{side}": 1.0})

    # collar / belt / hood details
    collar = add_torus("Collar", (0, 0, 1.385 * s), 0.085 * s, 0.022 * s, top,
                       rotation=(0, 0, 0))
    weight(collar, arm, {"chest": 0.6, "neck": 0.4})
    belt = add_torus("Belt", (0, 0, 1.035 * s), 0.155 * s, 0.015 * s, metal,
                     rotation=(0, 0, 0))
    weight(belt, arm, {"hips": 1.0})
    if cfg.get("hood"):
        hood = add_sphere("Hood", (0, 0.09 * s, 1.36 * s),
                          (0.16 * s, 0.10 * s, 0.10 * s), top)
        weight(hood, arm, {"chest": 0.7, "neck": 0.3})
    if cfg.get("glasses"):
        for side, sx in (("L", 1), ("R", -1)):
            frame = add_torus(f"Glass.{side}", (sx * 0.055 * s, -0.142 * s, 1.655 * s),
                              0.026 * s, 0.003 * s, dark)
            weight(frame, arm, {"head": 1.0})
        bridge = add_box("GlassBridge", (0, -0.144 * s, 1.657 * s),
                         (0.03 * s, 0.004 * s, 0.004 * s), dark, bevel=0.001)
        weight(bridge, arm, {"head": 1.0})

    # skin / neck weights
    weight(neck, arm, {"neck": 1.0})
    weight(head, arm, {"head": 1.0})
    weight(hair_cap, arm, {"head": 1.0})

    # torso weight by z
    weight_by_z(torso, arm)

    # idle + talk actions
    make_action(arm, "idle", [
        (0, {"chest": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0), "upperArm.L": (0.0, 0.0, 0.02), "upperArm.R": (0.0, 0.0, -0.02)}),
        (30, {"chest": (0.015, 0.0, 0.0), "head": (0.0, 0.03, 0.0), "upperArm.L": (0.0, 0.0, 0.035), "upperArm.R": (0.0, 0.0, -0.035)}),
        (60, {"chest": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0), "upperArm.L": (0.0, 0.0, 0.02), "upperArm.R": (0.0, 0.0, -0.02)}),
        (90, {"chest": (-0.012, 0.0, 0.0), "head": (0.0, -0.03, 0.0), "upperArm.L": (0.0, 0.0, 0.015), "upperArm.R": (0.0, 0.0, -0.015)}),
        (120, {"chest": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0), "upperArm.L": (0.0, 0.0, 0.02), "upperArm.R": (0.0, 0.0, -0.02)}),
    ])
    make_action(arm, "talk", [
        (0, {"chest": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0), "upperArm.L": (0.0, 0.0, 0.02), "upperArm.R": (0.0, 0.0, -0.02), "lowerArm.L": (0.0, 0.0, 0.0), "lowerArm.R": (0.0, 0.0, 0.0)}),
        (20, {"chest": (0.01, 0.02, 0.0), "head": (0.02, 0.04, 0.0), "upperArm.L": (0.0, 0.0, 0.10), "upperArm.R": (0.0, 0.0, -0.04), "lowerArm.L": (0.12, 0.0, 0.0), "lowerArm.R": (0.0, 0.0, 0.0)}),
        (45, {"chest": (0.0, -0.01, 0.0), "head": (-0.01, -0.03, 0.0), "upperArm.L": (0.0, 0.0, 0.03), "upperArm.R": (0.0, 0.0, -0.12), "lowerArm.L": (0.02, 0.0, 0.0), "lowerArm.R": (0.15, 0.0, 0.0)}),
        (75, {"chest": (0.015, 0.01, 0.0), "head": (0.0, 0.02, 0.0), "upperArm.L": (0.0, 0.0, 0.08), "upperArm.R": (0.0, 0.0, -0.06), "lowerArm.L": (0.10, 0.0, 0.0), "lowerArm.R": (0.05, 0.0, 0.0)}),
        (120, {"chest": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0), "upperArm.L": (0.0, 0.0, 0.02), "upperArm.R": (0.0, 0.0, -0.02), "lowerArm.L": (0.0, 0.0, 0.0), "lowerArm.R": (0.0, 0.0, 0.0)}),
    ])

    # scene frame range
    scene.frame_start = 0
    scene.frame_end = 120
    scene.render.fps = 30

    out = SRC / f"{cfg['name']}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"saved {out}: {len(meshes)} meshes, {len(bpy.data.actions)} actions")
    return out


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


CHARACTERS = [
    {
        "name": "mark",
        "scale": 1.00,
        "shoulder": 0.155,
        "hip": 0.10,
        "skin": (0.72, 0.50, 0.37),
        "lip": (0.55, 0.24, 0.22),
        "hair": (0.10, 0.075, 0.06),
        "eye": (0.18, 0.38, 0.28),
        "top": (0.16, 0.30, 0.55),
        "bottom": (0.16, 0.17, 0.20),
        "shoe": (0.08, 0.08, 0.09),
        "hair_style": "short",
        "hood": True,
        "glasses": False,
    },
    {
        "name": "mira",
        "scale": 0.94,
        "shoulder": 0.14,
        "hip": 0.105,
        "skin": (0.86, 0.65, 0.51),
        "lip": (0.68, 0.30, 0.30),
        "hair": (0.46, 0.16, 0.07),
        "eye": (0.20, 0.45, 0.62),
        "top": (0.20, 0.45, 0.31),
        "bottom": (0.22, 0.17, 0.24),
        "shoe": (0.24, 0.11, 0.10),
        "hair_style": "bob",
        "hood": False,
        "glasses": True,
    },
]


if __name__ == "__main__":
    for cfg in CHARACTERS:
        build_character(cfg)
