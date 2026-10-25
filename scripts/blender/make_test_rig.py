"""Create a minimal canonical humanoid rig for pipeline tests.

    blender --background --python scripts/blender/make_test_rig.py -- /tmp/rig.blend

Not production content: one cube skinned to hips, 21 canonical bones, A-pose,
one jawOpen shape key.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


BONES = {
    "hips":       ((0, 0, 1.00), (0, 0, 1.15), None),
    "spine":      ((0, 0, 1.15), (0, 0, 1.30), "hips"),
    "chest":      ((0, 0, 1.30), (0, 0, 1.45), "spine"),
    "neck":       ((0, 0, 1.45), (0, 0, 1.55), "chest"),
    "head":       ((0, 0, 1.55), (0, 0, 1.75), "neck"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES.update({
        f"shoulder.{side}": ((0, 0, 1.42), (0.12 * sx, 0, 1.42), "chest"),
        f"upperArm.{side}": ((0.12 * sx, 0, 1.42), (0.32 * sx, 0, 1.25), f"shoulder.{side}"),
        f"lowerArm.{side}": ((0.32 * sx, 0, 1.25), (0.50 * sx, 0, 1.08), f"upperArm.{side}"),
        f"hand.{side}":     ((0.50 * sx, 0, 1.08), (0.58 * sx, 0, 1.02), f"lowerArm.{side}"),
        f"upperLeg.{side}": ((0.10 * sx, 0, 1.00), (0.10 * sx, 0, 0.55), "hips"),
        f"lowerLeg.{side}": ((0.10 * sx, 0, 0.55), (0.10 * sx, 0, 0.10), f"upperLeg.{side}"),
        f"foot.{side}":     ((0.10 * sx, 0, 0.10), (0.10 * sx, -0.10, 0.02), f"lowerLeg.{side}"),
        f"toe.{side}":      ((0.10 * sx, -0.10, 0.02), (0.10 * sx, -0.24, 0.02), f"foot.{side}"),
    })


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = bpy.context.object
    arm_obj.name = "Armature"
    arm = arm_obj.data
    arm.name = "SceneRig"
    for bone in list(arm.edit_bones):
        arm.edit_bones.remove(bone)
    created = {}
    for name, (head, tail, parent) in BONES.items():
        eb = arm.edit_bones.new(name)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.use_connect = False
        if parent:
            eb.parent = created[parent]
        created[name] = eb
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.9))
    mesh_obj = bpy.context.object
    mesh_obj.name = "Body"
    mesh_obj.scale = (0.3, 0.2, 1.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    vg = mesh_obj.vertex_groups.new(name="hips")
    vg.add(list(range(len(mesh_obj.data.vertices))), 1.0, "REPLACE")

    mesh_obj.shape_key_add(name="Basis", from_mix=False)
    jaw = mesh_obj.shape_key_add(name="jawOpen", from_mix=False)
    for i in range(len(mesh_obj.data.vertices)):
        jaw.data[i].co.z += 0.01
    viseme = mesh_obj.shape_key_add(name="viseme_sil", from_mix=False)
    for i in range(len(mesh_obj.data.vertices)):
        viseme.data[i].co.y -= 0.005

    mesh_obj.parent = arm_obj
    bpy.context.view_layer.objects.active = arm_obj
    return arm_obj


if __name__ == "__main__":
    argv = sys.argv
    out = None
    if "--" in argv:
        rest = argv[argv.index("--") + 1:]
        if rest:
            out = Path(rest[0])
    build()
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(out))
        print(f"saved {out}")
