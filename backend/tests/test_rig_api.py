"""HTTP-тесты валидатора SceneRig (без БД)."""
import json
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import rig

ROOT = Path(__file__).resolve().parents[2]
BRUNETTE = ROOT / "core" / "public" / "models" / "brunette.glb"


class RigApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(rig.router)
        cls.client = TestClient(app)

    def test_archetypes(self):
        r = self.client.get("/rig/archetypes")
        self.assertEqual(r.status_code, 200)
        slugs = {a["archetype"] for a in r.json()["archetypes"]}
        self.assertEqual(slugs, {"humanoid", "quadruped", "avian", "insectoid"})

    def test_health(self):
        r = self.client.get("/rig/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

    @unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
    def test_validate_character_upload(self):
        with BRUNETTE.open("rb") as fh:
            r = self.client.post(
                "/rig/validate",
                files={"file": ("brunette.glb", fh, "model/gltf-binary")},
                data={"archetype": "humanoid"},
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"], data)
        self.assertEqual(data["archetype"], "human/humanoid")

    @unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
    def test_validate_static_upload(self):
        with BRUNETTE.open("rb") as fh:
            r = self.client.post(
                "/rig/validate",
                files={"file": ("prop.glb", fh, "model/gltf-binary")},
                data={"require_rig": "false"},
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"], data)
        self.assertIsNone(data["archetype"])

    @unittest.skipUnless(BRUNETTE.exists(), "brunette.glb is required")
    def test_validate_manifest_upload(self):
        manifest = {
            "format": "sceneasset/1", "id": "prop-test", "title": "Prop",
            "kind": "prop3d", "category": "other",
            "geometry": {"type": "gltf", "file": "prop.glb", "units": "m", "up": "Y", "facing": "+Z"},
            "anchors": {"pivot": "bottom", "ground": True, "forward": "+Z", "bounds": [1, 1, 1]},
            "license": {"name": "test"},
        }
        with BRUNETTE.open("rb") as fh:
            r = self.client.post(
                "/rig/validate-manifest",
                data={"manifest": json.dumps(manifest)},
                files={"file": ("prop.glb", fh, "model/gltf-binary")},
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"], data)
        self.assertEqual(len(data["children"]), 1)


if __name__ == "__main__":
    unittest.main()
