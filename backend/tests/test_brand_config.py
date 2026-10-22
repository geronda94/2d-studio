"""Тесты BRAND KIT (backend/brand_config.py). Без БД и FastAPI.

Запуск: docker compose exec backend python -m unittest backend.tests.test_brand_config -v
"""
import json
import unittest
from types import SimpleNamespace
from unittest import mock

from backend import brand_config as bc


class PublicConfigTest(unittest.TestCase):
    CFG = {
        "brand": {"name": "IT2B", "logo": "/media/l.png", "qr_data": "https://t.me/x"},
        "contacts": {"telegram": "@x", "email": "hi@x.io", "phone": "+49"},
        "defaults": {"OutroSlide": {"headline": "hi"}},
        "voice": {"voice": "Charon"},
        "audio": {"bgm": "/media/b.mp3"},
    }

    def test_strips_private_and_business(self):
        out = bc.public_config(self.CFG)
        self.assertEqual(set(out.keys()), {"brand", "defaults", "contacts"})
        self.assertNotIn("email", out["contacts"])
        self.assertNotIn("phone", out["contacts"])
        self.assertEqual(out["contacts"]["telegram"], "@x")
        self.assertNotIn("voice", out)
        self.assertNotIn("audio", out)

    def test_non_dict_returns_empty(self):
        self.assertEqual(bc.public_config(None), {})
        self.assertEqual(bc.public_config("nope"), {})

    def test_missing_sections_ok(self):
        self.assertEqual(bc.public_config({"brand": {"name": "A"}}), {"brand": {"name": "A"}})


class MergeConfigTest(unittest.TestCase):
    def test_deep_merge_keeps_siblings(self):
        old = {"brand": {"name": "A", "logo": "/l.png"}, "voice": {"voice": "Charon"},
               "defaults": {"X": {"a": 1}}}
        merged = bc.merge_config(old, {"brand": {"name": "B"}})
        self.assertEqual(merged["brand"], {"name": "B", "logo": "/l.png"})  # logo сохранился
        self.assertEqual(merged["voice"], {"voice": "Charon"})
        self.assertEqual(merged["defaults"], {"X": {"a": 1}})

    def test_null_deletes_key(self):
        old = {"brand": {"name": "A", "logo": "/l.png"}}
        merged = bc.merge_config(old, {"brand": {"logo": None}})
        self.assertEqual(merged["brand"], {"name": "A"})

    def test_defaults_deep_merge_component(self):
        old = {"defaults": {"OutroSlide": {"headline": "H", "handle": "@x"}}}
        merged = bc.merge_config(old, {"defaults": {"OutroSlide": {"headline": "New"}}})
        self.assertEqual(merged["defaults"]["OutroSlide"], {"headline": "New", "handle": "@x"})

    def test_unknown_top_level_preserved(self):
        merged = bc.merge_config({"legal": {"x": 1}}, {"brand": {"name": "B"}})
        self.assertEqual(merged["legal"], {"x": 1})

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            bc.merge_config({}, ["not", "a", "dict"])

    def test_oversize_raises(self):
        huge = {"brand": {"x": "A" * (bc.MAX_CONFIG_BYTES + 10)}}
        with self.assertRaises(ValueError):
            bc.merge_config({}, huge)

    def test_old_none_ok(self):
        self.assertEqual(bc.merge_config(None, {"brand": {"name": "A"}}), {"brand": {"name": "A"}})


class LocalMediaPathTest(unittest.TestCase):
    def test_empty_and_unknown_scheme_none(self):
        self.assertIsNone(bc.local_media_path(""))
        self.assertIsNone(bc.local_media_path("/etc/passwd"))
        self.assertIsNone(bc.local_media_path("http://x/y.mp3"))

    def test_missing_file_none(self):
        with mock.patch("backend.brand_config.os.path.exists", return_value=False):
            self.assertIsNone(bc.local_media_path("/media/nope.mp3"))

    def test_existing_maps(self):
        with mock.patch("backend.brand_config.os.path.exists", return_value=True):
            self.assertEqual(bc.local_media_path("/media/a.mp3"), "/app/backend/media/a.mp3")
            self.assertEqual(bc.local_media_path("/uploads/b.mp3"), "/app/uploads/b.mp3")


class ProbeDurationTest(unittest.TestCase):
    def setUp(self):
        bc._DURATION_CACHE.clear()

    def _fake_run(self, dur):
        return SimpleNamespace(stdout=json.dumps({"format": {"duration": str(dur)}}))

    def test_parses_and_caches(self):
        with mock.patch("subprocess.run", return_value=self._fake_run(12.5)) as run:
            self.assertEqual(bc.probe_duration_ms("/x.mp3"), 12500)
            self.assertEqual(bc.probe_duration_ms("/x.mp3"), 12500)
            self.assertEqual(run.call_count, 1)  # второй раз из кэша

    def test_fallback_on_error(self):
        with mock.patch("subprocess.run", side_effect=RuntimeError("boom")):
            self.assertEqual(bc.probe_duration_ms("/x.mp3", fallback=777), 777)

    def test_empty_path(self):
        self.assertEqual(bc.probe_duration_ms("", fallback=5), 5)


class SeedBgmTest(unittest.TestCase):
    def test_no_bgm_no_timeline(self):
        pres = SimpleNamespace(audio_timeline=None)
        self.assertFalse(bc.seed_bgm_from_config(pres, {"audio": {}}))
        self.assertIsNone(pres.audio_timeline)

    def test_missing_file_skips(self):
        pres = SimpleNamespace(audio_timeline=None)
        ok = bc.seed_bgm_from_config(
            pres, {"audio": {"bgm": "/media/nope.mp3"}},
            path_resolver=lambda s: None, duration_probe=lambda p, fallback=0: 1000,
        )
        self.assertFalse(ok)
        self.assertIsNone(pres.audio_timeline)

    def test_unknown_duration_skips(self):
        pres = SimpleNamespace(audio_timeline=None)
        ok = bc.seed_bgm_from_config(
            pres, {"audio": {"bgm": "/media/a.mp3"}},
            path_resolver=lambda s: "/app/backend/media/a.mp3",
            duration_probe=lambda p, fallback=0: 0,
        )
        self.assertFalse(ok)
        self.assertIsNone(pres.audio_timeline)

    def test_success_builds_bgm_track(self):
        pres = SimpleNamespace(audio_timeline=None)
        ok = bc.seed_bgm_from_config(
            pres, {"audio": {"bgm": "/media/a.mp3", "volume": 0.2}},
            path_resolver=lambda s: "/app/backend/media/a.mp3",
            duration_probe=lambda p, fallback=0: 30000,
        )
        self.assertTrue(ok)
        tracks = pres.audio_timeline["tracks"]
        self.assertEqual([t["id"] for t in tracks], ["main", "bgm"])
        clip = tracks[1]["clips"][0]
        self.assertEqual(clip["end_time"], 30000)
        self.assertEqual(clip["volume"], 0.2)
        self.assertEqual(clip["src"], "/media/a.mp3")


if __name__ == "__main__":
    unittest.main()


class ResolveSpeechParamsTest(unittest.TestCase):
    def test_request_wins(self):
        sp = bc.resolve_speech_params({"voice": "Puck"}, {"voice": {"voice": "Charon"}})
        self.assertEqual(sp["voice"], "Puck")

    def test_config_over_default(self):
        sp = bc.resolve_speech_params({}, {"voice": {"voice": "Fenrir", "temperature": 0.5}})
        self.assertEqual(sp["voice"], "Fenrir")
        self.assertEqual(sp["temperature"], 0.5)

    def test_default_when_nothing(self):
        sp = bc.resolve_speech_params({}, {})
        self.assertEqual(sp["voice"], "Charon")
        self.assertEqual(sp["temperature"], 0.9)

    def test_bad_temperature_falls_back(self):
        sp = bc.resolve_speech_params({"temperature": "abc"}, {})
        self.assertEqual(sp["temperature"], 0.9)
