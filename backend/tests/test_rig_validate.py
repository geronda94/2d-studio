"""Тесты SceneRig: алиасы костей, архетипы, GLB и валидатор манифестов."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.rig import glb
from backend.rig.bake import bake_clip
from backend.rig.compile import compile_rig, write_glb
from backend.rig.archetypes import (
    AVIAN,
    HUMANOID,
    INSECTOID,
    QUADRUPED,
    infer_archetype,
    map_bones,
    normalize_bone,
    required_missing,
)
from backend.rig.validate import Report, _validate_clip_data, validate_glb, validate_manifest

ROOT = Path(__file__).resolve().parents[2]
BRUNETTE = ROOT / "core" / "public" / "models" / "brunette.glb"


class BoneAliasTest(unittest.TestCase):
    def test_rpm_and_mixamo_names(self):
        cases = {
            "Hips": "hips",
            "Spine1": "spine1",
            "Spine2": "chest",
            "LeftShoulder": "shoulder.L",
            "LeftArm": "upperArm.L",
            "LeftForeArm": "lowerArm.L",
            "LeftHand": "hand.L",
            "LeftUpLeg": "upperLeg.L",
            "LeftLeg": "lowerLeg.L",
            "LeftFoot": "foot.L",
            "LeftToeBase": "toe.L",
            "mixamorig:LeftUpLeg": "upperLeg.L",
            "mixamorig:RightForeArm": "lowerArm.R",
            "LeftHandThumb1": "thumb1.L",
            "HeadTop_End": "headTop",
            "LeftEye": "eye.L",
            "spine.001": "spine1",
            "spine.002": "chest",
            "upper_arm.L": "upperArm.L",
            "forearm.R": "lowerArm.R",
            "thigh.L": "upperLeg.L",
            "shin.R": "lowerLeg.R",
            "J_Bip_C_Hips": "hips",
            "J_Bip_L_UpperArm": "upperArm.L",
        }
        for src, expected in cases.items():
            self.assertEqual(normalize_bone(src), expected, src)

    def test_unknown_bone(self):
        self.assertIsNone(normalize_bone("banana_bone"))

    def test_map_duplicates(self):
        mapping, unmapped, dup = map_bones(["Hips", "Pelvis", "Root"])
        self.assertIn("hips", mapping)
        self.assertIn("hips", dup)
        self.assertEqual(unmapped, [])


class ArchetypeTest(unittest.TestCase):
    def test_human_required(self):
        self.assertIn("upperArm.L", HUMANOID.required)
        self.assertIn("toe.R", HUMANOID.required)
        self.assertEqual(len(HUMANOID.required), 21)

    def test_insectoid_shape(self):
        self.assertIn("thorax", INSECTOID.required)
        self.assertIn("wingTip.R", INSECTOID.required)
        self.assertIn("legHind.L", INSECTOID.required)

    def test_infer(self):
        human = ["Hips", "Spine", "Spine2", "Neck", "Head",
                 "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
                 "RightShoulder", "RightArm", "RightForeArm", "RightHand",
                 "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
                 "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"]
        self.assertIs(infer_archetype(human), HUMANOID)
        bee = ["thorax", "abdomen", "head",
               "wingRoot.L", "wingMid.L", "wingTip.L",
               "wingRoot.R", "wingMid.R", "wingTip.R",
               "legFront.L", "legMid.L", "legHind.L",
               "legFront.R", "legMid.R", "legHind.R"]
        self.assertIs(infer_archetype(bee), INSECTOID)
        bird = ["hips", "spine", "chest", "neck", "head",
                "wingRoot.L", "wingMid.L", "wingTip.L",
                "wingRoot.R", "wingMid.R", "wingTip.R",
                "upperLeg.L", "lowerLeg.L", "foot.L",
                "upperLeg.R", "lowerLeg.R", "foot.R"]
        self.assertIs(infer_archetype(bird), AVIAN)
        animal = ["hips", "spine", "chest", "neck", "head",
                  "shoulder.L", "upperArm.L", "lowerArm.L", "hand.L",
                  "shoulder.R", "upperArm.R", "lowerArm.R", "hand.R",
                  "upperLeg.L", "lowerLeg.L", "foot.L", "toe.L",
                  "upperLeg.R", "lowerLeg.R", "foot.R", "toe.R", "tail1"]
        self.assertIs(infer_archetype(animal), QUADRUPED)


@unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
class BrunetteGLBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = glb.read(BRUNETTE)
        cls.names = glb.joint_names(cls.doc)

    def test_glb_header(self):
        self.assertEqual(self.doc.asset_version, "2.0")
        self.assertEqual(len(self.doc.skins), 1)
        self.assertGreater(len(self.doc.meshes), 0)

    def test_joints_and_morphs(self):
        self.assertEqual(len(self.names), 67)
        mapping, unmapped, dup = map_bones(self.names)
        self.assertEqual(required_missing(HUMANOID, mapping), [])
        self.assertEqual(unmapped, [])
        self.assertFalse(dup)
        morphs = glb.morph_target_names(self.doc)
        self.assertIn("jawOpen", morphs)
        self.assertIn("viseme_aa", morphs)
        self.assertIn("eyeBlinkLeft", morphs)

    def test_bounds_and_transforms(self):
        bounds = glb.position_bounds(self.doc)
        self.assertIsNotNone(bounds)
        lo, hi = bounds
        self.assertGreater(hi[1] - lo[1], 1.2)
        self.assertLess(hi[1] - lo[1], 2.4)

    def test_validate_passes(self):
        rep = validate_glb(BRUNETTE, HUMANOID)
        self.assertTrue(rep.ok, [i.to_dict() for i in rep.errors])
        self.assertFalse(any(i.code == "bones.missing" for i in rep.issues))
        self.assertAlmostEqual(rep.facts["height"], 1.772, places=2)

    def test_static_asset_skips_archetype(self):
        rep = validate_glb(BRUNETTE, None, require_rig=False)
        self.assertFalse(any(i.code == "bones.missing" for i in rep.issues))
        self.assertIsNone(rep.archetype)


class ClipValidationTest(unittest.TestCase):
    def _rep(self, data):
        rep = Report(path="clip.json", kind="clip")
        _validate_clip_data(Path("clip.json"), data, rep)
        return rep

    def test_good_clip(self):
        rep = self._rep({
            "format": "sceneclip/1", "name": "idle", "fps": 30,
            "duration": 2.0, "loop": True,
            "tracks": {
                "chest": {"rotation": [[0, 0, 0, 0, 1], [1, 0, 0.02, 0, 0.9998]]},
                "upperArm.L": {"rotation": [[0, 0, 0, -0.17, 0.985]]},
            },
            "face": {"viseme_sil": [[0, 1], [1.9, 1], [2.0, 0]]},
            "events": [{"t": 0.5, "name": "step"}],
        })
        self.assertEqual(rep.errors, [], [i.to_dict() for i in rep.errors])

    def test_unknown_bone(self):
        rep = self._rep({
            "format": "sceneclip/1", "name": "bad", "fps": 30, "duration": 1,
            "tracks": {"banana": {"rotation": [[0, 0, 0, 0, 1], [1, 0, 0, 0, 1]]}},
        })
        self.assertTrue(any(i.code == "clip.bone" for i in rep.errors))

    def test_unsorted_keys(self):
        rep = self._rep({
            "format": "sceneclip/1", "name": "bad", "fps": 30, "duration": 2,
            "tracks": {"chest": {"rotation": [[1, 0, 0, 0, 1], [0, 0, 0, 0, 1]]}},
        })
        self.assertTrue(any(i.code == "clip.key_order" for i in rep.errors))

    def test_time_outside(self):
        rep = self._rep({
            "format": "sceneclip/1", "name": "bad", "fps": 30, "duration": 1,
            "tracks": {"chest": {"rotation": [[0, 0, 0, 0, 1], [2, 0, 0, 0, 1]]}},
        })
        self.assertTrue(any(i.code == "clip.key_time" for i in rep.errors))


@unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
class CompileTest(unittest.TestCase):
    def test_write_glb_roundtrip(self):
        doc = glb.read(BRUNETTE)
        raw = write_glb(doc.json, doc.bin)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "roundtrip.glb"
            p.write_bytes(raw)
            again = glb.read(p)
            self.assertEqual(len(again.nodes), len(doc.nodes))
            self.assertEqual(len(glb.joint_names(again)), len(glb.joint_names(doc)))
            self.assertEqual(glb.morph_target_names(again), glb.morph_target_names(doc))


    def test_bake_clip_into_glb(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dist"
            rep, manifest_out = compile_rig(BRUNETTE.with_suffix(".scenerig.json"), out)
            self.assertTrue(rep.ok, [i.to_dict() for i in rep.errors])
            clip = {
                "format": "sceneclip/1", "name": "wave", "fps": 30,
                "duration": 2.0, "loop": True,
                "tracks": {
                    "chest": {"rotation": [[0, 0, 0, 0, 1], [1, 0, 0, 0.2588, 0.9659], [2, 0, 0, 0, 1]]},
                    "upperArm.L": {"rotation": [[0, 0, 0, 0.3827, 0.9239], [2, 0, 0, 0.3827, 0.9239]]},
                },
            }
            clip_path = Path(td) / "wave.sclip.json"
            clip_path.write_text(json.dumps(clip), encoding="utf-8")
            baked = Path(td) / "baked.glb"
            brep, baked_out = bake_clip(manifest_out, clip_path, baked)
            self.assertTrue(brep.ok, [i.to_dict() for i in brep.errors])
            doc = glb.read(baked_out)
            anims = glb.animation_info(doc)
            self.assertEqual(len(anims), 1)
            self.assertEqual(anims[0]["name"], "wave")
            self.assertAlmostEqual(anims[0]["duration"], 2.0, places=2)
            self.assertEqual(anims[0]["channels"], 2)

    def test_compile_canonicalizes_bones(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dist"
            rep, manifest_out = compile_rig(BRUNETTE.with_suffix(".scenerig.json"), out)
            self.assertTrue(rep.ok, [i.to_dict() for i in rep.errors])
            self.assertTrue(manifest_out.exists())
            compiled = out / "character-brunette.glb"
            self.assertTrue(compiled.exists())
            doc = glb.read(compiled)
            names = set(glb.joint_names(doc))
            self.assertIn("hips", names)
            self.assertIn("upperArm.L", names)
            self.assertNotIn("Hips", names)
            self.assertNotIn("LeftArm", names)
            m = json.loads(manifest_out.read_text(encoding="utf-8"))
            self.assertEqual(m["bones"]["map"], {})
            self.assertTrue(m["bones"]["canonical"])


@unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
class ManifestTest(unittest.TestCase):
    def test_rig_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "rig.glb").symlink_to(BRUNETTE)
            manifest = {
                "format": "scenerig/1",
                "id": "character-test",
                "family": "human",
                "archetype": "humanoid",
                "geometry": {"file": "rig.glb"},
                "license": {"name": "test"},
                "sockets": [{"name": "hand.R", "bone": "hand.R"}],
            }
            p = base / "rig.scenerig.json"
            p.write_text(json.dumps(manifest), encoding="utf-8")
            rep = validate_manifest(p)
            self.assertTrue(rep.ok, [i.to_dict() for i in rep.errors])
            self.assertFalse(any(i.code == "bones.missing" for i in rep.issues))

    def test_socket_unknown_bone(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "rig.glb").symlink_to(BRUNETTE)
            manifest = {
                "format": "scenerig/1",
                "id": "character-test",
                "family": "human",
                "archetype": "humanoid",
                "geometry": {"file": "rig.glb"},
                "license": {"name": "test"},
                "sockets": [{"name": "hat", "bone": "banana"}],
            }
            p = base / "rig.scenerig.json"
            p.write_text(json.dumps(manifest), encoding="utf-8")
            rep = validate_manifest(p)
            self.assertTrue(any(i.code == "socket.bone" for i in rep.issues))


if __name__ == "__main__":
    unittest.main()
