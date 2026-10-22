"""Тесты аутентификации/прав (backend/auth.py, backend/permissions.py). Без БД."""
import unittest
from types import SimpleNamespace

from backend import auth
from backend import permissions as perm


class PasswordTest(unittest.TestCase):
    def test_hash_and_verify(self):
        h = auth.hash_password("supersecret1")
        self.assertTrue(h.startswith("scrypt$"))
        self.assertTrue(auth.verify_password("supersecret1", h))
        self.assertFalse(auth.verify_password("wrong", h))

    def test_salted_unique(self):
        self.assertNotEqual(auth.hash_password("x"), auth.hash_password("x"))

    def test_malformed_stored(self):
        self.assertFalse(auth.verify_password("x", "not-a-hash"))
        self.assertFalse(auth.verify_password("x", ""))
        self.assertFalse(auth.verify_password("x", None))

    def test_hash_token_sha256_hex(self):
        t = auth._hash_token("abc")
        self.assertEqual(len(t), 64)
        self.assertEqual(t, auth._hash_token("abc"))


class RankTest(unittest.TestCase):
    def test_order(self):
        self.assertLess(perm.rank(None), perm.rank("viewer"))
        self.assertLess(perm.rank("viewer"), perm.rank("editor"))
        self.assertLess(perm.rank("editor"), perm.rank("owner"))
        self.assertEqual(perm.rank("garbage"), 0)


class InternalTokenTest(unittest.TestCase):
    def _req(self, token=None):
        headers = {}
        if token is not None:
            headers["x-internal-token"] = token
        return SimpleNamespace(headers=headers)

    def test_disabled_when_no_token(self):
        old = perm.INTERNAL_API_TOKEN
        perm.INTERNAL_API_TOKEN = ""
        try:
            self.assertFalse(perm._is_internal(self._req("anything")))
        finally:
            perm.INTERNAL_API_TOKEN = old

    def test_match(self):
        old = perm.INTERNAL_API_TOKEN
        perm.INTERNAL_API_TOKEN = "s3cret"
        try:
            self.assertTrue(perm._is_internal(self._req("s3cret")))
            self.assertFalse(perm._is_internal(self._req("wrong")))
            self.assertFalse(perm._is_internal(self._req(None)))
        finally:
            perm.INTERNAL_API_TOKEN = old


if __name__ == "__main__":
    unittest.main()
