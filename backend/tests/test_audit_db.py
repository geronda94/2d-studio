"""Тесты аудита (ENTERPRISE Ф1): redaction, derive_action, транзакционность."""
import os
import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import audit, models
from backend.database import Base


def make_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


class MaskTest(unittest.TestCase):
    def test_secrets_redacted(self):
        m = audit.mask({"password": "x", "token": "y", "nested": {"secret_key": "z"}})
        self.assertEqual(m["password"], "***")
        self.assertEqual(m["token"], "***")
        self.assertEqual(m["nested"]["secret_key"], "***")

    def test_pii_masked(self):
        m = audit.mask({"email": "ivan@it2b.top", "phone": "+49123"})
        self.assertNotIn("ivan@it2b.top", str(m))
        self.assertTrue(m["email"].startswith("i"))
        self.assertEqual(m["phone"], "***")

    def test_long_string_trimmed(self):
        m = audit.mask({"note": "a" * 1000})
        self.assertLessEqual(len(m["note"]), 501)


class DeriveActionTest(unittest.TestCase):
    def test_known(self):
        self.assertEqual(audit.derive_action("PUT", "/projects/5/config"), "project.config_update")
        self.assertEqual(audit.derive_action("POST", "/presentations/9/change-set"), "presentation.change_set")
        self.assertEqual(audit.derive_action("PUT", "/presentations/slides/10"), "slide.upsert")
        self.assertEqual(audit.derive_action("PUT", "/admin/users/3"), "admin.user_update")


class TransactionalAuditTest(unittest.TestCase):
    def setUp(self):
        audit.register()
        self.engine, self.Session = make_db()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def _ctx(self, **kw):
        base = {"actor_type": "user", "actor_user_id": 1, "effective_user_id": 1,
                "project_id": 7, "action": "project.config_update", "method": "PUT",
                "path": "/projects/7/config"}
        base.update(kw)
        return base

    def test_commit_writes_audit_no_outbox_without_webhook(self):
        audit.set_context(self.db, self._ctx())
        audit.queue(self.db)
        self.db.add(models.Project(slug="p", title="P", owner_id=1))
        self.db.commit()
        self.assertEqual(self.db.query(models.AuditLog).count(), 1)
        # без AUDIT_WEBHOOK_URL outbox не копим
        self.assertEqual(self.db.query(models.AuditOutbox).count(), 0)
        row = self.db.query(models.AuditLog).first()
        self.assertEqual(row.action, "project.config_update")
        self.assertEqual(row.decision, "allow")

    def test_outbox_when_webhook_set(self):
        with mock.patch.dict(os.environ, {"AUDIT_WEBHOOK_URL": "http://sink.local"}):
            audit.set_context(self.db, self._ctx())
            audit.queue(self.db)
            self.db.add(models.Project(slug="pw", title="PW", owner_id=1))
            self.db.commit()
            self.assertEqual(self.db.query(models.AuditOutbox).count(), 1)

    def test_no_duplicate_on_second_commit(self):
        audit.set_context(self.db, self._ctx())
        audit.queue(self.db)
        self.db.add(models.Project(slug="p2", title="P2", owner_id=1))
        self.db.commit()
        # второй commit без нового queue — строк не добавляет
        self.db.add(models.Project(slug="p3", title="P3", owner_id=1))
        self.db.commit()
        self.assertEqual(self.db.query(models.AuditLog).count(), 1)

    def test_rollback_writes_nothing(self):
        audit.set_context(self.db, self._ctx())
        audit.queue(self.db)
        self.db.add(models.Project(slug="q", title="Q", owner_id=1))
        self.db.rollback()
        self.assertEqual(self.db.query(models.AuditLog).count(), 0)

    def test_no_queue_no_audit(self):
        self.db.add(models.Project(slug="r", title="R", owner_id=1))
        self.db.commit()
        self.assertEqual(self.db.query(models.AuditLog).count(), 0)

    def test_audit_masks_secrets(self):
        audit.set_context(self.db, self._ctx(meta={"password": "p", "email": "a@b.c"}))
        audit.queue(self.db)
        self.db.add(models.Project(slug="s", title="S", owner_id=1))
        self.db.commit()
        row = self.db.query(models.AuditLog).first()
        self.assertEqual(row.meta["password"], "***")
        self.assertNotIn("a@b.c", str(row.meta["email"]))


if __name__ == "__main__":
    unittest.main()
