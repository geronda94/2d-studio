#!/usr/bin/env python3
"""Generate the SceneEngine Rive character rig (RML) and build character.riv.

The rig is a cutout skeleton: bones drive rigid vector parts, while the face
(eyes, brows, 10 visemes) is driven by view-model numbers.  A JS controller
sets those numbers from seek(t), so the result stays deterministic.

Usage:
    python3 scripts/build_rive_character.py            # build .riv
    python3 scripts/build_rive_character.py --rml      # only write scene.rml
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "core" / "rive" / "character"
OUT = ROOT / "core" / "public" / "rive" / "character.riv"

# ---------------------------------------------------------------------------
# id allocator
# ---------------------------------------------------------------------------
_next_id = 100


def nid() -> str:
    global _next_id
    _next_id += 1
    return f"0:{_next_id}"


def esc(v) -> str:
    return str(v).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def attrs(**kw) -> str:
    return " ".join(f'{k.rstrip("_")}="{esc(v)}"' for k, v in kw.items() if v is not None)


# ---------------------------------------------------------------------------
# view model
# ---------------------------------------------------------------------------
VM_NAME = "Character"

COLORS = {
    "skin": "FFF2CBA4", "skinLight": "FFFBE0C4", "skinDark": "FFC68C60",
    "hair": "FF3B2C24", "hairLight": "FF6B4C3C",
    "shirt": "FF2F6FB3", "shirtLight": "FF5E9BD8", "shirtDark": "FF1E4A7C",
    "pants": "FF2A3444", "pantsLight": "FF3D4A5E",
    "shoe": "FF1B2230", "shoeLight": "FF39465C",
    "lip": "FFC2726B", "iris": "FF4A7FB5",
    "scarf": "FFB23A48", "skirt": "FF35405A", "cassock": "FF23242B",
}

# name -> (initial value, kind) kind: n number, c color
PROPS: dict[str, tuple[object, str]] = {
    # root / torso
    "rootX": (300, "n"), "rootY": (560, "n"), "rootRot": (-math.pi / 2, "n"),
    "spine": (0, "n"), "chest": (0, "n"), "neck": (0, "n"), "head": (0, "n"),
    # arms (rotations are radians, relative to the parent bone)
    "shoulderL": (-math.pi / 2, "n"), "shoulderR": (math.pi / 2, "n"),
    "upperArmL": (-math.pi / 2, "n"), "upperArmR": (math.pi / 2, "n"),
    "foreArmL": (0, "n"), "foreArmR": (0, "n"),
    "handL": (0, "n"), "handR": (0, "n"),
    # legs
    "hipL": (-math.pi / 2, "n"), "hipR": (math.pi / 2, "n"),
    "thighL": (-math.pi / 2, "n"), "thighR": (math.pi / 2, "n"),
    "shinL": (0, "n"), "shinR": (0, "n"),
    "footL": (math.pi / 2, "n"), "footR": (-math.pi / 2, "n"),
    # face
    "headYaw": (0, "n"), "headPitch": (0, "n"),
    "blink": (0, "n"), "gazeX": (0, "n"), "gazeY": (0, "n"),
    "browYL": (0, "n"), "browYR": (0, "n"), "browTiltL": (0, "n"), "browTiltR": (0, "n"),
    # visemes 0..9 (opacity)
    **{f"m{i}": (1 if i == 0 else 0, "n") for i in range(10)},
    # wardrobe / variants (opacity)
    "beard": (1, "n"), "glasses": (0, "n"), "scarfOn": (0, "n"),
    "skirtOn": (0, "n"), "cassockOn": (0, "n"), "blazerOn": (0, "n"),
    "longHair": (0, "n"), "hatOn": (0, "n"),
}

for _k, _v in COLORS.items():
    PROPS[_k] = (_v, "c")

prop_ids: dict[str, str] = {}
vm_id = ""
vm_instance_id = ""


def vm_block() -> str:
    global vm_id, vm_instance_id
    for k in PROPS:
        prop_ids[k] = nid()
    inst = nid()
    vm_instance_id = inst
    vm_id = nid()
    out = [f'<ViewModel defaultInstanceId="{inst}" name="{VM_NAME}" id="{vm_id}">']
    # deterministic order: numbers first, then colours
    for k, (v, kind) in PROPS.items():
        if kind == "n":
            out.append(f'  <ViewModelPropertyNumber name="{k}" id="{prop_ids[k]}"/>')
    for k, (v, kind) in PROPS.items():
        if kind == "c":
            out.append(f'  <ViewModelPropertyColor name="{k}" id="{prop_ids[k]}"/>')
    out.append(f'  <ViewModelInstance exports="true" name="Default" id="{inst}">')
    for k, (v, kind) in PROPS.items():
        if kind == "n":
            out.append(f'    <ViewModelInstanceNumber propertyValue="{v}" viewModelPropertyId="{prop_ids[k]}"/>')
        else:
            out.append(f'    <ViewModelInstanceColor propertyValue="{v}" viewModelPropertyId="{prop_ids[k]}"/>')
    out.append('  </ViewModelInstance>')
    out.append('</ViewModel>')
    return "\n".join(out)


def bind(name: str, key: int) -> str:
    return f'<DataBindContext sourcePathIds="{vm_id}-{prop_ids[name]}" propertyKey="{key}"/>'


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------
def solid(name: str, color: str | None = None, color_bind: str | None = None) -> str:
    if color_bind:
        return (f'<SolidColor name="{name}" colorValue="{COLORS.get(color_bind, "FF888888")}">'
                f'{bind(color_bind, 37)}</SolidColor>')
    return f'<SolidColor name="{name}" colorValue="{color}"/>'


def fill(name: str, color: str | None = None, color_bind: str | None = None) -> str:
    return f'<Fill name="{name}">{solid(name + "Color", color, color_bind)}</Fill>'


def stroke(name: str, color: str, thickness: float = 2, opacity: float | None = None) -> str:
    a = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<Stroke name="{name}" thickness="{thickness}" cap="round" join="round"{a}>{solid(name + "Color", color)}</Stroke>'


def rect(w, h, *, x=0, y=0, ox=0.5, oy=0.5, r=0) -> str:
    rr = (f' cornerRadiusTL="{r}" cornerRadiusTR="{r}" cornerRadiusBL="{r}" cornerRadiusBR="{r}"' if r else "")
    return (f'<Rectangle width="{w}" height="{h}" originX="{ox}" originY="{oy}" name="Path"{rr}/>')


def ellipse(w, h, *, ox=0.5, oy=0.5) -> str:
    return f'<Ellipse width="{w}" height="{h}" originX="{ox}" originY="{oy}" name="Path"/>'


def path(points, *, closed=True, clockwise=True, name="Path") -> str:
    verts = []
    for p in points:
        if len(p) == 2:
            verts.append(f'<StraightVertex x="{p[0]}" y="{p[1]}"/>')
        else:
            verts.append(f'<CubicMirroredVertex x="{p[0]}" y="{p[1]}" rotation="{p[2]}" distance="{p[3]}"/>')
    return (f'<PointsPath isClosed="{str(closed).lower()}" isClockwise="{str(clockwise).lower()}" name="{name}">'
            + "".join(verts) + '</PointsPath>')


def shape(body: str, *, x=0, y=0, rot=0, scale_x=None, scale_y=None, opacity=None,
          opacity_bind=None, name="Part", fill_color=None, fill_bind=None,
          stroke_color=None, stroke_w=2, shadow=None) -> str:
    sid = nid()
    a = [f'x="{x}"', f'y="{y}"', f'name="{name}"', f'id="{sid}"']
    if rot:
        a.append(f'rotation="{rot}"')
    if scale_x is not None:
        a.append(f'scaleX="{scale_x}"')
    if scale_y is not None:
        a.append(f'scaleY="{scale_y}"')
    if opacity is not None:
        a.append(f'opacity="{opacity}"')
    binds = ""
    if opacity_bind:
        binds += bind(opacity_bind, 18)
    if shadow:
        a.append(f'blendModeValue="3"')
    inner = [body]
    if fill_color or fill_bind:
        inner.append(fill(name + "Fill", fill_color, fill_bind))
    if stroke_color:
        inner.append(stroke(name + "Stroke", stroke_color, stroke_w))
    if shadow:
        inner.append(f'<Fill name="Shadow"><SolidColor name="ShadowColor" colorValue="{shadow}"/></Fill>')
    return f'<Shape {" ".join(a)}>{binds}{"".join(inner)}</Shape>'


def shape_with_binds(body: str, *, x=0, y=0, rot=0, opacity_bind=None,
                     x_bind=None, y_bind=None, rot_bind=None, scale_y_bind=None,
                     name="Part", fill_color=None, fill_bind=None,
                     stroke_color=None, stroke_w=2) -> str:
    sid = nid()
    a = [f'x="{x}"', f'y="{y}"', f'name="{name}"', f'id="{sid}"']
    if rot:
        a.append(f'rotation="{rot}"')
    binds = ""
    if x_bind:
        binds += bind(x_bind, 13)
    if y_bind:
        binds += bind(y_bind, 14)
    if rot_bind:
        binds += bind(rot_bind, 15)
    if scale_y_bind:
        binds += bind(scale_y_bind, 17)
    if opacity_bind:
        binds += bind(opacity_bind, 18)
    inner = [body]
    if fill_color or fill_bind:
        inner.append(fill(name + "Fill", fill_color, fill_bind))
    if stroke_color:
        inner.append(stroke(name + "Stroke", stroke_color, stroke_w))
    return f'<Shape {" ".join(a)}>{binds}{"".join(inner)}</Shape>'


def node_with_binds(inner: str, *, x=0, y=0, rot=0, x_bind=None, y_bind=None,
                    rot_bind=None, name="Node") -> str:
    sid = nid()
    a = [f'x="{x}"', f'y="{y}"', f'name="{name}"', f'id="{sid}"']
    if rot:
        a.append(f'rotation="{rot}"')
    binds = ""
    if x_bind:
        binds += bind(x_bind, 13)
    if y_bind:
        binds += bind(y_bind, 14)
    if rot_bind:
        binds += bind(rot_bind, 15)
    return f'<Node {" ".join(a)}>{binds}{inner}</Node>'


# ---------------------------------------------------------------------------
# bones
# ---------------------------------------------------------------------------
BONES = [
    # name, parent, length, rotation, x, y, bind rotation
    ("root", None, 0, -math.pi / 2, 300, 560, "rootRot"),
    ("spine", "root", 110, 0, None, None, "spine"),
    ("chest", "spine", 80, 0, None, None, "chest"),
    ("neck", "chest", 50, 0, None, None, "neck"),
    ("head", "neck", 0, 0, None, None, "head"),

    ("shoulderL", "chest", 105, -math.pi / 2, None, None, "shoulderL"),
    ("upperArmL", "shoulderL", 135, math.pi / 2, None, None, "upperArmL"),
    ("foreArmL", "upperArmL", 120, 0, None, None, "foreArmL"),
    ("handL", "foreArmL", 46, 0, None, None, "handL"),

    ("shoulderR", "chest", 105, math.pi / 2, None, None, "shoulderR"),
    ("upperArmR", "shoulderR", 135, math.pi / 2, None, None, "upperArmR"),
    ("foreArmR", "upperArmR", 120, 0, None, None, "foreArmR"),
    ("handR", "foreArmR", 46, 0, None, None, "handR"),

    ("hipL", "root", 55, -math.pi / 2, None, None, "hipL"),
    ("thighL", "hipL", 165, math.pi / 2, None, None, "thighL"),
    ("shinL", "thighL", 155, 0, None, None, "shinL"),
    ("footL", "shinL", 56, math.pi / 2, None, None, "footL"),

    ("hipR", "root", 55, math.pi / 2, None, None, "hipR"),
    ("thighR", "hipR", 165, math.pi / 2, None, None, "thighR"),
    ("shinR", "thighR", 155, 0, None, None, "shinR"),
    ("footR", "shinR", 56, -math.pi / 2, None, None, "footR"),
]


def bone_tree() -> str:
    by_parent: dict[str | None, list] = {}
    for b in BONES:
        by_parent.setdefault(b[1], []).append(b)

    def emit(b) -> str:
        name, parent, length, rot, x, y, rbind = b
        tag = "RootBone" if parent is None else "Bone"
        a = [f'length="{length}"', f'rotation="{rot}"', f'name="{name}"', f'id="{nid()}"']
        if x is not None:
            a += [f'x="{x}"', f'y="{y}"']
        binds = ""
        if parent is None:
            binds += bind("rootX", 90) + bind("rootY", 91) + bind("rootRot", 15)
        elif rbind:
            binds += bind(rbind, 15)
        children = []
        if name == "spine":
            children.append(torso())
        elif name == "neck":
            pass  # the neck is covered by the head/torso; a shape here would paint over the mouth
        elif name == "head":
            children.append(face())
        elif name.startswith("upperArm"):
            side = name[-1]
            children.append(limb("upperArm", 135, 44, "shirt", "shirtLight", "shirtDark", side))
        elif name.startswith("foreArm"):
            side = name[-1]
            children.append(limb("foreArm", 120, 36, "shirt", "shirtLight", "shirtDark", side))
        elif name.startswith("thigh"):
            side = name[-1]
            children.append(limb("thigh", 165, 58, "pants", "pantsLight", "pants", side))
        elif name.startswith("shin"):
            side = name[-1]
            children.append(limb("shin", 155, 44, "pants", "pantsLight", "pants", side))
        elif name.startswith("shoulder"):
            children.append(shape(ellipse(38, 38), x=length - 4, name="shoulderCap" + name[-1], fill_bind="shirt"))
        elif name.startswith("hand"):
            side = name[-1]
            children.append(hand(side))
        elif name.startswith("foot"):
            side = name[-1]
            children.append(shape(ellipse(34, 34), x=0, name="ankle" + side, fill_bind="pants"))
            children.append(foot(side))
        for ch in by_parent.get(name, []):
            children.append(emit(ch))
        return f'<{tag} {" ".join(a)}>{binds}{"".join(children)}</{tag}>'

    return emit(by_parent[None][0])


# ---------------------------------------------------------------------------
# art
# ---------------------------------------------------------------------------
def limb(kind: str, length: float, thick: float, c1: str, c2: str, c3: str, side: str) -> str:
    # A capsule along +x. A lighter inner stripe gives volume.
    body = rect(length, thick, ox=0, oy=0.5, r=thick / 2)
    out = shape(ellipse(thick * 0.96, thick * 0.96), x=0, name=kind + side + "Joint", fill_bind=c1)
    out += shape(body, name=kind + side, fill_bind=c1)
    # highlight stripe
    out += shape(rect(length * 0.82, thick * 0.28, ox=0, oy=0.5, r=thick * 0.14),
                 x=length * 0.08, y=-thick * 0.18, name=kind + side + "Hi", fill_bind=c2, opacity=0.55)
    # shade at the far edge
    out += shape(rect(length * 0.9, thick * 0.22, ox=0, oy=0.5, r=thick * 0.11),
                 x=length * 0.05, y=thick * 0.24, name=kind + side + "Sh", fill_bind=c3, opacity=0.45)
    return out


def hand(side: str) -> str:
    out = shape(ellipse(36, 40), x=0, name="wrist" + side, fill_bind="skin")
    out += shape(ellipse(50, 54), x=26, name="hand" + side, fill_bind="skin")
    out += shape(ellipse(22, 28), x=34, y=-16, rot=-0.35, name="thumb" + side, fill_bind="skinLight")
    return out


def foot(side: str) -> str:
    out = shape(rect(84, 30, ox=0, oy=0.5, r=15), x=-8, y=0, name="shoe" + side, fill_bind="shoe")
    out += shape(rect(76, 8, ox=0, oy=0.5, r=4), x=-4, y=12, name="sole" + side, fill_color="FFDCE3EC")
    out += shape(ellipse(30, 22), x=62, y=-2, name="toe" + side, fill_bind="shoeLight")
    return out


def neck_part() -> str:
    return shape(rect(53, 46, ox=0, oy=0.5, r=10), name="neck", fill_bind="skin")


def torso() -> str:
    # Draw order in Rive is front-to-back: details first, base body last.
    front = []
    pts = [(0, -92), (170, -100), (170, 100), (0, 92)]
    # side shading
    front.append(shape(path([(0, 30), (170, 52), (170, 100), (0, 92)]), name="torsoShade",
                       fill_bind="shirtDark", opacity=0.30))
    front.append(shape(path([(0, -84), (170, -92), (170, -40), (0, -58)]), name="torsoHi",
                       fill_bind="shirtLight", opacity=0.20))
    # collar
    front.append(shape(path([(134, -44), (170, -24), (156, 4), (130, -14)]), name="collarL",
                       fill_bind="shirtLight", stroke_color="FF102A46", stroke_w=1.4))
    front.append(shape(path([(134, 44), (170, 24), (156, -4), (130, 14)]), name="collarR",
                       fill_bind="shirtLight", stroke_color="FF102A46", stroke_w=1.4))
    # placket + buttons
    front.append(shape(rect(150, 4, ox=0, oy=0.5), x=16, name="placket", fill_bind="shirtDark", opacity=0.5))
    for i, xx in enumerate((42, 70, 98)):
        front.append(shape(ellipse(8, 8), x=xx, y=0, name=f"button{i}", fill_color="FFEAF0F7"))
    # belt
    front.append(shape(rect(16, 196, ox=0, oy=0.5, r=4), x=2, name="belt", fill_color="FF1E2635"))
    front.append(shape(rect(14, 34, ox=0, oy=0.5, r=3), x=4, name="buckle", fill_color="FFC8D2E0"))
    # skirt / cassock / blazer overlays (toggled by VM opacity)
    skirt_pts = [(4, -104), (150, -118), (150, 118), (4, 104)]
    front.append(shape(path([(-10, -110), (-160, -132), (-160, 132), (-10, 110)]),
                       name="skirtLower", fill_bind="skirt", opacity_bind="skirtOn"))
    front.append(shape(path(skirt_pts), name="skirt", fill_bind="skirt", opacity_bind="skirtOn"))
    cassock_pts = [(4, -108), (240, -120), (240, 120), (4, 108)]
    front.append(shape(path([(-10, -115), (-335, -140), (-335, 140), (-10, 115)]),
                       name="cassockLower", fill_bind="cassock", opacity_bind="cassockOn"))
    front.append(shape(path(cassock_pts), name="cassock", fill_bind="cassock", opacity_bind="cassockOn"))
    front.append(shape(path([(108, -100), (170, -70), (170, -10), (134, -22)]), name="lapelL",
                       fill_bind="shirtDark", opacity_bind="blazerOn"))
    front.append(shape(path([(108, 100), (170, 70), (170, 10), (134, 22)]), name="lapelR",
                       fill_bind="shirtDark", opacity_bind="blazerOn"))
    # base body behind the details
    back = shape(path(pts), name="torso", fill_bind="shirt")
    return "".join(front) + back


def face() -> str:
    # Rive paints the first child on top. Build the face front-to-back.
    fid = nid()
    front = []
    back = []

    # ears and the back of the head are behind the face
    back.append(shape(ellipse(22, 34), x=-66, y=-12, name="earL", fill_bind="skin"))
    back.append(shape(ellipse(22, 34), x=66, y=-12, name="earR", fill_bind="skin"))
    back.append(shape(ellipse(132, 158), y=-18, name="head", fill_bind="skin",
                      stroke_color="FF7A4A2C", stroke_w=1.4))
    back.append(shape(path([(-70, -40), (-82, 70), (-60, 104), (-28, 88), (-38, -18)]),
                      name="longHairL", fill_bind="hair", opacity_bind="longHair"))
    back.append(shape(path([(70, -40), (82, 70), (60, 104), (28, 88), (38, -18)]),
                      name="longHairR", fill_bind="hair", opacity_bind="longHair"))

    # eyes: lids and gaze sit on top of the whites
    for side, sx in (("L", -30), ("R", 30)):
        front.append(shape_with_binds(rect(40, 22, ox=0.5, oy=0, r=11), x=sx, y=-31,
                                      name="lid" + side, fill_bind="skin", scale_y_bind="blink"))
    gaze = ""
    for side, sx in (("L", -30), ("R", 30)):
        gaze += shape(ellipse(14, 14), x=sx, y=-22, name="iris" + side, fill_bind="iris")
        gaze += shape(ellipse(6, 6), x=sx, y=-22, name="pupil" + side, fill_color="FF101820")
        gaze += shape(ellipse(3.5, 3.5), x=sx - 4, y=-27, name="glint" + side, fill_color="FFFFFFFF")
    front.append(node_with_binds(gaze, name="gaze", x_bind="gazeX", y_bind="gazeY"))
    for side, sx in (("L", -30), ("R", 30)):
        front.append(shape(ellipse(36, 18), x=sx, y=-22, name="eyeWhite" + side, fill_color="FFF7FAFF"))

    # brows: a node per side so y/tilt are offsets from the authored position
    for side, sx, yb, tb in (("L", -30, "browYL", "browTiltL"), ("R", 30, "browYR", "browTiltR")):
        brow = shape(path([(-16, 2), (0, -4), (16, 2)], closed=False), name="brow" + side,
                     stroke_color="FF3B2C24", stroke_w=3.6)
        front.append(node_with_binds(brow, x=sx, y=-52, name="browNode" + side,
                                     y_bind=yb, rot_bind=tb))

    # soft face shading
    front.append(shape(ellipse(24, 12), x=-44, y=22, name="blushL", fill_color="FFE8736B", opacity=0.16))
    front.append(shape(ellipse(24, 12), x=44, y=22, name="blushR", fill_color="FFE8736B", opacity=0.13))
    front.append(shape(ellipse(48, 18), y=84, name="chinShade", fill_color="FF8A5A3A", opacity=0.16))
    # nose
    front.append(shape(path([(2, 10), (7, 20), (1, 25)], closed=False), name="nose",
                       stroke_color="FFB07A54", stroke_w=2.6))

    # mouth: teeth/tongue first (top), then the active viseme, then the lip line
    mouths = [
        (48, 3, 0), (54, 30, 1), (24, 5, 0), (48, 12, 0), (50, 22, 0),
        (24, 16, 0), (32, 18, 0), (36, 28, 1), (30, 26, 0), (22, 12, 0),
    ]
    for i, (mw, mh, teeth) in enumerate(mouths):
        if teeth:
            front.append(shape_with_binds(rect(mw * 0.8, 4, ox=0.5, oy=0, r=2), y=32 - mh / 2,
                                          name=f"teeth{i}", fill_color="FFF4F7FA", opacity_bind=f"m{i}"))
    front.append(shape(ellipse(18, 11), y=40, name="tongue", fill_color="FFC7606A",
                       opacity_bind="m7"))
    for i, (mw, mh, teeth) in enumerate(mouths):
        front.append(shape_with_binds(ellipse(mw, max(4, mh)), y=34, name=f"viseme{i}",
                                      fill_color="FF3A1A1C", opacity_bind=f"m{i}"))
    front.append(shape(ellipse(54, 8), y=34, name="lipBase", fill_bind="lip"))

    # beard, glasses, hair, scarf on top
    front.append(shape(path([(-54, 50), (54, 50), (48, 84), (24, 100), (0, 104), (-24, 100), (-48, 84)]),
                       name="beard", fill_bind="hair",
                       opacity_bind="beard"))
    for sx in (-30, 30):
        front.append(shape(rect(44, 30, ox=0.5, oy=0.5, r=8), x=sx, y=-22, name="glass" + str(sx),
                           fill_color="FF000000", stroke_color="FF9FB3C8", stroke_w=3,
                           opacity_bind="glasses"))
    front.append(shape(rect(22, 3, ox=0.5, oy=0.5, r=1), y=-22, name="glassBridge",
                       fill_color="FF9FB3C8", opacity_bind="glasses"))
    front.append(shape(path([(-84, -24), (-80, 38), (-62, 92), (-42, 104), (-34, 82), (-44, 30), (-60, -22)]),
                       name="scarfL", fill_bind="scarf", opacity_bind="scarfOn"))
    front.append(shape(path([(84, -24), (80, 38), (62, 92), (42, 104), (34, 82), (44, 30), (60, -22)]),
                       name="scarfR", fill_bind="scarf", opacity_bind="scarfOn"))
    front.append(shape(path([(-74, -72), (-30, -94), (30, -94), (74, -72), (66, -48),
                             (30, -62), (-30, -62), (-66, -48)]),
                       name="scarfTop", fill_bind="scarf", opacity_bind="scarfOn"))
    front.append(shape(path([(-72, -34), (-60, -78), (-20, -98), (24, -98), (64, -76), (74, -32),
                             (58, -50), (30, -62), (0, -66), (-30, -62), (-58, -50)]),
                       name="hair", fill_bind="hair"))
    front.append(shape(path([(-62, -54), (-16, -72), (34, -64), (10, -48), (-22, -40), (-48, -42)]),
                       name="fringe", fill_bind="hairLight", opacity=0.55))

    inner = "".join(front) + "".join(back)
    return f'<Node x="0" y="0" rotation="{math.pi / 2}" name="Face" id="{fid}">' + inner + '</Node>'


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------
def build_rml() -> str:
    global _next_id
    _next_id = 100
    prop_ids.clear()
    # allocate VM first so ids are stable; vm_block sets vm_id/vm_instance_id
    vm = vm_block()

    artboard_id = "0:2"
    sm_id = "0:7"
    layer_id = "0:8"
    anim_id = "0:6"
    entry_target = "0:12"

    scene = bone_tree()
    rml = f'''<Rive version="1" kind="fragment">
  <Artboard defaultStateMachineId="{sm_id}" viewModelId="{vm_id}" viewModelInstanceId="{vm_instance_id}" styleId="0:5" width="600" height="1000" name="Character" id="{artboard_id}">
    <LayoutComponentStyle name="Artboard Style" id="0:5"/>
    {scene}
    <StateMachine name="State Machine 1" id="{sm_id}">
      <StateMachineLayer name="Layer 1" id="{layer_id}">
        <AnyState x="200" y="-120"/>
        <ExitState x="400" y="-120"/>
        <EntryState><StateTransition stateToId="{entry_target}"/></EntryState>
        <AnimationState x="200" animationId="{anim_id}" id="{entry_target}"/>
      </StateMachineLayer>
    </StateMachine>
    <LinearAnimation duration="60" name="Idle" id="{anim_id}"/>
  </Artboard>
{vm}
</Rive>
'''
    return rml


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rml", action="store_true", help="only write scene.rml")
    args = ap.parse_args()

    PROJECT.mkdir(parents=True, exist_ok=True)
    (PROJECT / "rive.yaml").write_text(
        "name: character\nmain: Character\noutput:\n  dir: build\n", encoding="utf-8")
    (PROJECT / ".gitignore").write_text("build/\n", encoding="utf-8")

    rml = build_rml()
    (PROJECT / "scene.rml").write_text(rml, encoding="utf-8")
    if args.rml:
        print(f"wrote {PROJECT / 'scene.rml'}")
        return 0

    rive = shutil.which("rive") or os.path.expanduser("~/.rive/bin/rive")
    cmd = [rive, str(PROJECT), "--once"]
    print(" ".join(cmd))
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        return res.returncode
    built = PROJECT / "build" / "character.riv"
    if not built.exists():
        print("build did not produce character.riv", file=sys.stderr)
        return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(built, OUT)
    print(f"copied -> {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
