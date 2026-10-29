"""Православный священник — low-poly персонаж SceneRig (канонический humanoid).

Собран по правилам проекта (docs/RIG_FORMAT.md):

- метры, scale = 1.0; origin между ступнями; персонаж смотрит в -Y (в glTF +Z);
- rest-поза A-pose (руки ~45° вниз), кости названы канонически;
- 25 костей humanoid: root, hips, spine, chest, neck, head, jaw, eye.L/R,
  shoulder/upperArm/lowerArm/hand L/R, upperLeg/lowerLeg/foot/toe L/R;
- скиннинг: до 4 влияний на вершину, сумма весов = 1;
- морфы лица: 15 визёмов + jawOpen (липсинк) и eyeBlinkLeft/Right;
- один меш, один skin, материалы Principled BSDF, бюджет ≤ 60k треугольников.

Сборка:

    blender --background --python scripts/blender/make_priest.py
    blender --background --python scripts/blender/make_priest.py -- --render

Экспорт (пишет GLB + манифест + валидирует):

    blender --background assets/characters/src/priest_v1.blend \
      --python scripts/blender/scene_rig_export.py -- \
      --id character-priest --title "Священник" \
      --family human --archetype humanoid --license CC0 --author SceneEngine \
      --out drafts/3d/models/characters

Геометрия: ряса с широкими рукавами, пояс, наперсный крест с цепочкой,
седая борода, скуфья. Ноги и обувь — под рясой (нужны для деформации).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

import make_poly_characters_v3 as pc  # noqa: E402  (общие примитивы проекта)

SRC = ROOT / "assets" / "characters" / "src"
PREVIEW = ROOT / "drafts" / "3d" / "models" / "characters" / "preview"
OUT_BLEND = SRC / "priest_v1.blend"

# ── пропорции (те же, что у канонического рига проекта) ─────────────────────

CFG = {"scale": 1.0, "shoulder": 0.168, "hip": 0.097}
S = CFG["scale"]
SH = CFG["shoulder"] * S          # плечо, x
HIPX = CFG["hip"] * S             # бедро, x
ELBOW = (SH + 0.17, 0, 1.19)
WRIST = (SH + 0.30, 0, 1.02)
HEAD_C = Vector((0, 0, 1.635))
MOUTH_C = Vector((0, -0.118, 1.583))

# палитра: ряса почти чёрная, седина, золото креста
CASSOCK = (0.032, 0.033, 0.040)
SKIN = (0.78, 0.58, 0.45)
HAIR = (0.52, 0.51, 0.48)          # седая борода и волосы
GOLD = (0.85, 0.66, 0.26)
LEATHER = (0.045, 0.040, 0.037)
EYE_WHITE = (0.92, 0.90, 0.86)
EYE_DARK = (0.14, 0.09, 0.06)
MOUTH = (0.13, 0.065, 0.060)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


# ── веса ────────────────────────────────────────────────────────────────────

def set_weights(obj, per_vertex):
    """per_vertex: list[(index, {bone: weight})] — веса нормализуются."""
    for idx, groups in per_vertex:
        total = sum(groups.values())
        if total <= 1e-6:
            continue
        for bone, w in groups.items():
            vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
            vg.add([idx], w / total, "REPLACE")


def robe_weights(obj):
    """Ряса: таз → спина → грудь сверху, таз → бёдра к подолу (до 3 влияний)."""
    rows = []
    for v in obj.data.vertices:
        z, x = v.co.z, v.co.x
        w = {}
        if z >= 1.05:
            t = clamp((z - 1.05) / 0.33)
            w["hips"] = max(0.0, 1.0 - 2.0 * t)
            w["spine"] = max(0.0, 1.0 - abs(2.0 * t - 1.0))
            w["chest"] = max(0.0, 2.0 * t - 1.0)
        else:
            t = clamp((1.05 - z) / 0.95)
            leg = 0.92 * t
            side = clamp((x + 0.06) / 0.12)  # 0 — правая половина, 1 — левая
            w["hips"] = 1.0 - leg
            w["upperLeg.L"] = leg * side
            w["upperLeg.R"] = leg * (1.0 - side)
        rows.append((v.index, w))
    set_weights(obj, rows)


def limb_weights(obj, rings, sides):
    """Веса по кольцам tube(): rings — список {bone: w}, одинаковый на кольцо."""
    rows = []
    for k, groups in enumerate(rings):
        for i in range(sides):
            rows.append((k * sides + i, groups))
    set_weights(obj, rows)


def weight_shoulders(obj, side):
    """Верхнее кольцо рукава — на ключицу, плечо и грудь (работает shoulder.*)."""
    set_weights(obj, [(i, {"shoulder." + side: 0.35,
                           "upperArm." + side: 0.40,
                           "chest": 0.25}) for i in range(14)])


def fix_unweighted(mesh, arm):
    """Страховка: каждая вершина получает вес ближайшей кости (кап-центры tube)."""
    segments = [(b.name, b.head_local.copy(), b.tail_local.copy())
                for b in arm.data.bones if b.name != "root"]
    fixed = 0
    for v in mesh.data.vertices:
        if any(g.weight > 1e-5 for g in v.groups):
            continue
        best, best_d = "hips", 1e9
        for name, head, tail in segments:
            d = tail - head
            length2 = d.length_squared or 1.0
            t = clamp((v.co - head).dot(d) / length2)
            dist = (v.co - (head + d * t)).length
            if dist < best_d:
                best, best_d = name, dist
        vg = mesh.vertex_groups.get(best) or mesh.vertex_groups.new(name=best)
        vg.add([v.index], 1.0, "REPLACE")
        fixed += 1
    if fixed:
        print(f"weights: {fixed} vertex(es) attached to the nearest bone")


# ── геометрия ───────────────────────────────────────────────────────────────

def build_body(arm, mats):
    parts = []

    # ряса: подол шире, талия уже, плечи — самый широкий пояс
    robe = pc.loft("Robe", [
        (0.105, 0.255, 0.215, 0.215, 0.010),
        (0.450, 0.245, 0.205, 0.205, 0.010),
        (0.800, 0.225, 0.190, 0.190, 0.005),
        (1.000, 0.190, 0.160, 0.165, 0.000),
        (1.160, 0.200, 0.170, 0.165, 0.000),
        (1.280, 0.215, 0.175, 0.165, 0.000),
        (1.380, 0.225, 0.160, 0.150, 0.000),
        (1.430, 0.165, 0.120, 0.118, 0.000),
    ], mats["cassock"], segments=24)
    robe_weights(robe)
    pc.bind(robe, arm)
    parts.append(robe)

    # пояс
    belt = pc.loft("Belt", [
        (0.955, 0.197, 0.168, 0.170, 0.0),
        (1.015, 0.199, 0.169, 0.171, 0.0),
    ], mats["leather"], segments=24, cap=False)
    pc.weight_all(belt, arm, "hips")
    parts.append(belt)

    # воротник подрясника (светлая полоса у шеи)
    collar = pc.loft("Collar", [
        (1.400, 0.098, 0.092, 0.092, 0.0),
        (1.445, 0.080, 0.076, 0.076, 0.0),
    ], mats["cassock"], segments=20, cap=False)
    pc.weight_mix(collar, arm, {"chest": 0.6, "neck": 0.4})
    parts.append(collar)

    for side, sx in (("L", 1), ("R", -1)):
        # рукав: от плеча к запястью, к манжете чуть шире
        sleeve = pc.tube(
            f"Sleeve.{side}",
            [(sx * SH, 0, 1.360), (sx * (SH + 0.085), 0, 1.275),
             (sx * ELBOW[0], 0, ELBOW[2]), (sx * (ELBOW[0] + 0.065), 0, 1.105),
             (sx * (WRIST[0] + 0.035), 0, WRIST[2] - 0.028)],
            [0.092, 0.086, 0.080, 0.086, 0.094],
            mats["cassock"], sides=14, depth=0.92,
            weights=[{"chest": 0.5, "upperArm." + side: 0.5},
                     {"upperArm." + side: 1.0},
                     {"upperArm." + side: 0.5, "lowerArm." + side: 0.5},
                     {"lowerArm." + side: 1.0},
                     {"lowerArm." + side: 1.0}],
        )
        pc.bind(sleeve, arm)
        weight_shoulders(sleeve, side)
        parts.append(sleeve)

        # кисть (рукав закрывает запястье)
        hand = pc.add_sphere(f"Hand.{side}", (sx * (WRIST[0] + 0.052), 0, 0.958),
                             (0.052, 0.046, 0.076), mats["skin"], segments=16, rings=10)
        pc.weight_all(hand, arm, f"hand.{side}")
        parts.append(hand)

        # нога под рясой
        leg = pc.tube(
            f"Leg.{side}",
            [(sx * HIPX, 0, 0.930), (sx * HIPX, 0, 0.530), (sx * HIPX, 0, 0.140)],
            [0.082, 0.066, 0.052],
            mats["cassock"], sides=10,
            weights=[{"upperLeg." + side: 1.0},
                     {"upperLeg." + side: 0.5, "lowerLeg." + side: 0.5},
                     {"lowerLeg." + side: 1.0}],
        )
        pc.bind(leg, arm)
        parts.append(leg)

        # сапог: голенище + ступня + носок
        shaft = pc.tube(f"BootShaft.{side}",
                        [(sx * HIPX, 0, 0.300), (sx * HIPX, 0, 0.115)],
                        [0.070, 0.072], mats["leather"], sides=10)
        pc.weight_all(shaft, arm, f"lowerLeg.{side}")
        parts.append(shaft)

        foot = pc.add_box(f"Boot.{side}", (sx * HIPX, -0.030, 0.058),
                          (0.105, 0.230, 0.115), mats["leather"], bevel=0.020)
        pc.weight_all(foot, arm, f"foot.{side}")
        parts.append(foot)

        toe = pc.add_box(f"BootToe.{side}", (sx * HIPX, -0.165, 0.045),
                         (0.100, 0.110, 0.085), mats["leather"], bevel=0.022)
        pc.weight_all(toe, arm, f"toe.{side}")
        parts.append(toe)

    # шея
    neck = pc.tube("Neck", [(0, 0, 1.395), (0, 0, 1.505)], [0.058, 0.055],
                   mats["skin"], sides=12)
    limb_weights(neck, [{"chest": 0.5, "neck": 0.5}, {"neck": 1.0}], sides=12)
    pc.bind(neck, arm)
    parts.append(neck)

    # наперсный крест и цепочка
    cross_v = pc.add_box("CrossV", (0, -0.196, 1.200), (0.028, 0.008, 0.100),
                         mats["gold"], bevel=0.004)
    pc.weight_all(cross_v, arm, "chest")
    parts.append(cross_v)
    cross_h = pc.add_box("CrossH", (0, -0.195, 1.228), (0.070, 0.008, 0.024),
                         mats["gold"], bevel=0.004)
    pc.weight_all(cross_h, arm, "chest")
    parts.append(cross_h)
    chain = pc.add_torus("Chain", (0, 0, 1.468), 0.064, 0.0032, mats["gold"],
                         rotation=(0, 0, 0), smooth=True)
    pc.weight_mix(chain, arm, {"neck": 0.6, "chest": 0.4})
    parts.append(chain)
    for sx in (-1, 1):
        link = pc.tube(f"ChainLink.{sx}",
                       [(sx * 0.058, -0.020, 1.462), (sx * 0.050, -0.140, 1.415),
                        (sx * 0.030, -0.180, 1.340), (sx * 0.012, -0.198, 1.248)],
                       [0.0030, 0.0030, 0.0030, 0.0030], mats["gold"], sides=6)
        pc.weight_all(link, arm, "chest")
        parts.append(link)

    return parts


def build_head(arm, mats):
    parts = []
    add = pc.add_sphere

    head = add("Head", HEAD_C, (0.108, 0.118, 0.135), mats["skin"], segments=24, rings=16)
    pc.weight_all(head, arm, "head")
    parts.append(head)

    # затылок и виски — седые волосы под скуфьёй
    hair = add("Hair", (0, 0.020, 1.660), (0.113, 0.113, 0.120), mats["hair"],
               segments=20, rings=14)
    pc.weight_all(hair, arm, "head")
    parts.append(hair)

    for sx in (-1, 1):
        ear = add(f"Ear.{sx}", (sx * 0.102, 0.008, 1.638),
                  (0.014, 0.026, 0.036), mats["skin"], segments=12, rings=8)
        pc.weight_all(ear, arm, "head")
        parts.append(ear)

        sideburn = add(f"Sideburn.{sx}", (sx * 0.098, -0.020, 1.585),
                       (0.016, 0.030, 0.055), mats["hair"], segments=12, rings=8)
        pc.weight_all(sideburn, arm, "head")
        parts.append(sideburn)

    nose = add("Nose", (0, -0.112, 1.642), (0.018, 0.034, 0.022), mats["skin"],
               segments=14, rings=10)
    pc.weight_all(nose, arm, "head")
    parts.append(nose)

    for sx in (-1, 1):
        brow = pc.add_box(f"Brow.{sx}", (sx * 0.045, -0.100, 1.688),
                          (0.052, 0.014, 0.012), mats["hair"], bevel=0.004)
        pc.weight_all(brow, arm, "head")
        parts.append(brow)

    # борода: обрамляет рот и сужается к груди
    beard = add("Beard", (0, -0.030, 1.532), (0.096, 0.082, 0.104), mats["hair"],
                segments=20, rings=14)
    pc.weight_all(beard, arm, "head")
    parts.append(beard)
    beard_low = add("BeardLow", (0, -0.050, 1.452), (0.066, 0.070, 0.082),
                    mats["hair"], segments=16, rings=12)
    pc.weight_all(beard_low, arm, "head")
    parts.append(beard_low)
    mustache = add("Mustache", (0, -0.112, 1.603), (0.046, 0.018, 0.011),
                   mats["hair"], segments=14, rings=10)
    pc.weight_all(mustache, arm, "head")
    parts.append(mustache)

    # глаза: белок + радужка + зрачок (кости eye.L/R — взгляд)
    for side, sx in (("L", 1), ("R", -1)):
        white = add(f"EyeWhite.{side}", (sx * 0.042, -0.092, 1.664),
                    (0.026, 0.016, 0.022), mats["eye_white"], segments=14, rings=10)
        pc.weight_all(white, arm, f"eye.{side}")
        parts.append(white)
        iris = add(f"Iris.{side}", (sx * 0.042, -0.104, 1.664),
                   (0.012, 0.007, 0.012), mats["eye_dark"], segments=12, rings=8)
        pc.weight_all(iris, arm, f"eye.{side}")
        parts.append(iris)
        pupil = add(f"Pupil.{side}", (sx * 0.042, -0.109, 1.664),
                    (0.005, 0.003, 0.005), mats["eye_dark"], segments=10, rings=6)
        pc.weight_all(pupil, arm, f"eye.{side}")
        parts.append(pupil)
        # верхнее веко — его верха двигает морф eyeBlink*
        lid = add(f"Lid.{side}", (sx * 0.042, -0.093, 1.675),
                  (0.028, 0.017, 0.012), mats["skin"], segments=14, rings=8)
        pc.weight_all(lid, arm, "head")
        parts.append(lid)

    # рот: тёмная щель + губы (визёмы двигают этот меш)
    mouth = add("Mouth", MOUTH_C, (0.030, 0.010, 0.011), mats["mouth"],
                segments=14, rings=10)
    pc.weight_all(mouth, arm, "jaw")
    parts.append(mouth)
    lip_up = pc.add_box("LipUp", (0, -0.123, 1.594), (0.048, 0.006, 0.005),
                        mats["mouth"], bevel=0.004)
    pc.weight_all(lip_up, arm, "jaw")
    parts.append(lip_up)
    lip_low = pc.add_box("LipLow", (0, -0.122, 1.573), (0.042, 0.006, 0.006),
                         mats["mouth"], bevel=0.004)
    pc.weight_all(lip_low, arm, "jaw")
    parts.append(lip_low)

    # скуфья: мягкая шапочка с тульей
    cap = pc.loft("Skufia", [
        (1.696, 0.124, 0.124, 0.124, 0.004),
        (1.734, 0.127, 0.127, 0.127, 0.004),
        (1.772, 0.114, 0.114, 0.114, 0.004),
        (1.800, 0.086, 0.086, 0.086, 0.004),
        (1.822, 0.042, 0.042, 0.042, 0.004),
    ], mats["cassock"], segments=24)
    pc.weight_all(cap, arm, "head")
    parts.append(cap)

    return parts


# ── морфы лица на объединённом меше ─────────────────────────────────────────

VISEME_SCALE = {
    "viseme_sil": (1.00, 1.00), "viseme_PP": (0.85, 0.70), "viseme_FF": (0.95, 0.80),
    "viseme_TH": (0.95, 1.40), "viseme_DD": (1.00, 2.20), "viseme_kk": (0.95, 2.50),
    "viseme_CH": (0.85, 1.60), "viseme_SS": (1.22, 1.00), "viseme_nn": (1.00, 1.80),
    "viseme_RR": (0.90, 1.90), "viseme_aa": (1.20, 3.40), "viseme_E": (1.35, 2.20),
    "viseme_I": (1.25, 1.50), "viseme_O": (0.85, 2.80), "viseme_U": (0.70, 2.00),
    "jawOpen": (1.00, 3.60),
}


def add_face_morphs(mesh):
    verts = mesh.data.vertices
    mouth = [v for v in verts
             if abs(v.co.x) < 0.075 and v.co.y < -0.085
             and 1.535 < v.co.z < 1.600]
    lids_l = [v for v in verts
              if 0.010 < v.co.x < 0.085 and v.co.y < -0.070
              and 1.660 < v.co.z < 1.700]
    lids_r = [v for v in verts
              if -0.085 < v.co.x < -0.010 and v.co.y < -0.070
              and 1.660 < v.co.z < 1.700]

    if mesh.data.shape_keys is None:
        mesh.shape_key_add(name="Basis", from_mix=False)

    for name, (sx, sz) in VISEME_SCALE.items():
        key = mesh.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for v in mouth:
            co = key.data[v.index].co.copy()
            co.x = MOUTH_C.x + (co.x - MOUTH_C.x) * sx
            co.z = MOUTH_C.z + (co.z - MOUTH_C.z) * sz - (0.004 if name == "jawOpen" else 0.0)
            key.data[v.index].co = co

    for name, group in (("eyeBlinkLeft", lids_l), ("eyeBlinkRight", lids_r)):
        key = mesh.shape_key_add(name=name, from_mix=False)
        key.value = 0.0
        for v in group:
            co = key.data[v.index].co.copy()
            co.z -= 0.032
            co.y -= 0.004
            key.data[v.index].co = co


# ── сцена ───────────────────────────────────────────────────────────────────

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30

    mats = {
        "cassock": pc.material("Cassock", CASSOCK, 0.84),
        "skin": pc.material("Skin", SKIN, 0.70),
        "hair": pc.material("Hair", HAIR, 0.86),
        "gold": pc.material("Gold", GOLD, 0.28, 1.0),
        "leather": pc.material("Leather", LEATHER, 0.55),
        "eye_white": pc.material("EyeWhite", EYE_WHITE, 0.25),
        "eye_dark": pc.material("EyeDark", EYE_DARK, 0.32),
        "mouth": pc.material("Mouth", MOUTH, 0.62),
    }

    arm = pc.build_armature(CFG)
    arm.name = "Armature"
    parts = build_body(arm, mats) + build_head(arm, mats)

    mesh = pc.join_objects(parts)  # один меш = один skin
    mesh.name = "Priest"
    mesh.data.name = "Priest"
    fix_unweighted(mesh, arm)
    add_face_morphs(mesh)

    # метаданные-клипы, как у остальных персонажей проекта
    pc.make_action(arm, "idle", [
        (0, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
        (60, {"chest": (0.02, 0, 0), "head": (0.01, 0.01, 0)}),
        (120, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
    ])
    pc.make_action(arm, "talk", [
        (0, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
        (30, {"chest": (0.01, 0.02, 0), "head": (0.03, 0.03, 0)}),
        (60, {"chest": (0, -0.01, 0), "head": (-0.02, -0.02, 0)}),
        (120, {"chest": (0, 0, 0), "head": (0, 0, 0)}),
    ])
    arm.animation_data.action = None
    scene.frame_set(0)

    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    keys = [k.name for k in mesh.data.shape_keys.key_blocks if k.name != "Basis"] \
        if mesh.data.shape_keys else []
    print(f"saved {OUT_BLEND}")
    print(f"mesh: {len(mesh.data.vertices)} verts, ~{tris} tris, "
          f"{len(mesh.vertex_groups)} groups, {len(keys)} morphs")
    print(f"bones: {len(arm.data.bones)}")
    return arm, mesh


# ── превью (Cycles, без окна) ───────────────────────────────────────────────

def rotate_world(arm, name, world_axis, deg):
    """Повернуть кость вокруг мировой оси (поза в привычных терминах)."""
    pb = arm.pose.bones.get(name)
    if not pb:
        return
    rest = pb.bone.matrix_local.to_3x3()
    axis = (rest.inverted() @ Vector(world_axis)).normalized()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = Quaternion(axis, math.radians(deg)) @ pb.rotation_quaternion


def _look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _setup_studio():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 760
    scene.render.resolution_y = 1040
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.012, 0.013, 0.016, 1.0)
    bg.inputs[1].default_value = 1.0
    scene.world = world

    # фоновая стена и пол
    mat = pc.material("Backdrop", (0.030, 0.032, 0.038), 0.9)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 1.6, 0))
    wall = bpy.context.object
    wall.rotation_euler = (math.radians(90), 0, 0)
    wall.data.materials.append(mat)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.002))
    floor = bpy.context.object
    floor.data.materials.append(mat)

    def area(name, loc, energy, size, color=(1, 1, 1)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        light.data.color = color
        _look_at(light, (0, 0, 1.1))
        return light

    area("Key", (-2.4, -3.0, 2.9), 240, 2.2, (1.0, 0.96, 0.90))
    area("Fill", (2.6, -2.2, 1.7), 90, 2.6, (0.86, 0.92, 1.0))
    area("Rim", (0.9, 2.6, 2.6), 180, 1.8, (1.0, 0.93, 0.82))

    bpy.ops.object.camera_add(location=(-1.9, -3.35, 1.62))
    cam = bpy.context.object
    cam.data.lens = 62
    _look_at(cam, (0, 0, 1.05))
    scene.camera = cam
    return cam


def _render(path):
    scene = bpy.context.scene
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"render {path}")


def _bone_meshes(arm, mat, posed=False):
    """Октаэдры по костям — для картинки со скелетом."""
    made = []
    bones = arm.pose.bones if posed else arm.data.bones
    for bone in bones:
        if posed:
            head = arm.matrix_world @ bone.head
            tail = arm.matrix_world @ bone.tail
        else:
            head = bone.head_local.copy()
            tail = bone.tail_local.copy()
        d = tail - head
        length = d.length
        if length < 1e-4:
            continue
        d.normalize()
        ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
        u = d.cross(ref).normalized()
        v = d.cross(u).normalized()
        w = max(0.018, min(0.040, length * 0.22))
        mid = head + d * (length * 0.18)
        verts = [head, mid + u * w, mid + v * w, mid - u * w, mid - v * w, tail]
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
                 (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)]
        obj = pc.mesh_object(f"Bone_{bone.name}", verts, faces, mat, smooth=False)
        made.append(obj)
    return made


def apply_demo_pose(arm):
    """Демо-поза: шаг вперёд и благословение правой рукой."""
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    rotate_world(arm, "hips", (0, 0, 1), -7)
    rotate_world(arm, "chest", (1, 0, 0), -3)
    rotate_world(arm, "chest", (0, 0, 1), 7)
    rotate_world(arm, "neck", (1, 0, 0), 4)
    rotate_world(arm, "head", (0, 0, 1), -10)
    rotate_world(arm, "upperArm.R", (1, 0, 0), -70)
    rotate_world(arm, "lowerArm.R", (0, 1, 0), -52)
    rotate_world(arm, "hand.R", (1, 0, 0), -22)
    rotate_world(arm, "upperArm.L", (1, 0, 0), 8)
    rotate_world(arm, "upperLeg.L", (1, 0, 0), -22)
    rotate_world(arm, "lowerLeg.L", (1, 0, 0), 26)
    rotate_world(arm, "foot.L", (1, 0, 0), 4)
    rotate_world(arm, "upperLeg.R", (1, 0, 0), 12)
    rotate_world(arm, "lowerLeg.R", (1, 0, 0), 10)
    rotate_world(arm, "foot.R", (1, 0, 0), -6)
    bpy.context.view_layer.update()


def render_previews(arm, mesh, quick=False, only=""):
    """only: front | side | rig | pose | "" (все кадры)."""
    _setup_studio()
    PREVIEW.mkdir(parents=True, exist_ok=True)
    cam = bpy.context.scene.camera
    want = lambda name: not only or only == name  # noqa: E731

    # 1) модель, 3/4 спереди
    if want("front"):
        _render(PREVIEW / "priest-front.png")
    if quick or only == "front":
        return

    # 2) профиль
    if want("side"):
        cam.location = (3.3, -0.9, 1.55)
        _look_at(cam, (0, 0, 1.02))
        _render(PREVIEW / "priest-side.png")

    # 3) скелет: тело прячем, кости светятся
    if want("rig"):
        emit = bpy.data.materials.new("BoneGlow")
        emit.use_nodes = True
        nt = emit.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (0.22, 0.82, 1.0, 1.0)
        em.inputs[1].default_value = 2.2
        nt.links.new(em.outputs[0], out.inputs[0])

        mesh.hide_render = True
        bones = _bone_meshes(arm, emit)
        cam.location = (-1.4, -3.6, 1.62)
        _look_at(cam, (0, 0, 1.05))
        _render(PREVIEW / "priest-rig.png")
        mesh.hide_render = False
        for b in bones:
            bpy.data.objects.remove(b, do_unlink=True)

    # 4) тестовая поза: шаг и благословение
    if want("pose"):
        apply_demo_pose(arm)
        cam.location = (-1.9, -3.35, 1.62)
        _look_at(cam, (0, 0, 1.05))
        _render(PREVIEW / "priest-pose.png")


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="отрендерить превью (Cycles)")
    ap.add_argument("--quick", action="store_true", help="только кадр спереди")
    ap.add_argument("--only", default="", choices=["", "front", "side", "rig", "pose"],
                    help="отрендерить один кадр")
    args = ap.parse_args(argv)

    arm, mesh = build()
    if args.render:
        render_previews(arm, mesh, args.quick, args.only)


if __name__ == "__main__":
    main()
