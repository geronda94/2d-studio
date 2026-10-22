"""Интеграционные тесты прав (AUTH_PLAN Ф2-Ф4) на in-memory SQLite.

Проверяют резолв ролей и шлюз мутаций `enforce_write` БЕЗ Postgres/FastAPI-сервера.
Запуск: docker compose exec backend python -m unittest backend.tests.test_permissions_db -v
"""
import asyncio
import datetime
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from backend import models
from backend import permissions as perm
from backend.auth import _hash_token, hash_password
from backend.database import Base


def make_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def make_request(method, path, headers=None, client=("10.0.0.9", 1234), path_params=None):
    hdr = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http", "http_version": "1.1", "method": method, "path": path,
        "raw_path": path.encode(), "query_string": b"", "headers": hdr,
        "client": client, "scheme": "http", "server": ("test", 80),
        "path_params": path_params or {},
    }
    return Request(scope)


class BaseFixture(unittest.TestCase):
    def setUp(self):
        perm.AUTH_MODE = "on"
        self._old_token = perm.INTERNAL_API_TOKEN
        perm.INTERNAL_API_TOKEN = "test-internal-token"
        self.db = make_db()
        # users
        self.owner = models.User(email="owner@x", password_hash=hash_password("p"),
                                 is_superadmin=False)
        self.editor = models.User(email="editor@x", password_hash=hash_password("p"))
        self.viewer = models.User(email="viewer@x", password_hash=hash_password("p"))
        self.stranger = models.User(email="stranger@x", password_hash=hash_password("p"))
        self.admin = models.User(email="admin@x", password_hash=hash_password("p"),
                                 is_superadmin=True)
        self.db.add_all([self.owner, self.editor, self.viewer, self.stranger, self.admin])
        self.db.flush()
        # project owned by owner, with folder + presentation
        self.project = models.Project(slug="p", title="P", owner_id=self.owner.id)
        self.db.add(self.project)
        self.db.flush()
        self.folder = models.Folder(slug="f", title="F", project_id=self.project.id)
        self.folder2 = models.Folder(slug="f2", title="F2", project_id=self.project.id)
        self.db.add_all([self.folder, self.folder2])
        self.db.flush()
        self.pres = models.Presentation(title="Pres", visibility="public")
        self.pres2 = models.Presentation(title="Pres2", visibility="public")
        self.db.add_all([self.pres, self.pres2])
        self.db.flush()
        self.folder.presentations.append(self.pres)
        self.folder2.presentations.append(self.pres2)
        # memberships
        self.db.add_all([
            models.ProjectMember(project_id=self.project.id, user_id=self.editor.id, role="editor"),
            models.ProjectMember(project_id=self.project.id, user_id=self.viewer.id, role="viewer"),
        ])
        self.db.commit()

    def tearDown(self):
        perm.INTERNAL_API_TOKEN = self._old_token
        self.db.close()

    def call(self, req):
        return asyncio.get_event_loop().run_until_complete(perm.enforce_write(req, self.db))


class RoleResolutionTest(BaseFixture):
    def test_project_role(self):
        self.assertEqual(perm.project_role(self.db, self.project.id, self.owner), "owner")
        self.assertEqual(perm.project_role(self.db, self.project.id, self.editor), "editor")
        self.assertEqual(perm.project_role(self.db, self.project.id, self.viewer), "viewer")
        self.assertIsNone(perm.project_role(self.db, self.project.id, self.stranger))
        self.assertEqual(perm.project_role(self.db, self.project.id, self.admin), "owner")

    def test_presentation_role(self):
        self.assertEqual(perm.presentation_role(self.db, self.pres.id, self.owner), "owner")
        self.assertEqual(perm.presentation_role(self.db, self.pres.id, self.editor), "editor")
        self.assertEqual(perm.presentation_role(self.db, self.pres.id, self.viewer), "viewer")
        self.assertIsNone(perm.presentation_role(self.db, self.pres.id, self.stranger))

    def test_folder_scope_limits_role(self):
        # editor ограничен папкой folder2 → pres (folder) недоступна, pres2 (folder2) доступна
        m = self.db.query(models.ProjectMember).filter_by(
            project_id=self.project.id, user_id=self.editor.id).first()
        m.scope_folder_id = self.folder2.id
        self.db.commit()
        self.assertIsNone(perm.presentation_role(self.db, self.pres.id, self.editor))
        self.assertEqual(perm.presentation_role(self.db, self.pres2.id, self.editor), "editor")

    def test_can_view_private(self):
        self.pres.visibility = "private"
        self.db.commit()
        self.assertTrue(perm.can_view_presentation(self.db, self.pres, self.viewer))
        self.assertFalse(perm.can_view_presentation(self.db, self.pres, self.stranger))
        self.assertFalse(perm.can_view_presentation(self.db, self.pres, None))
        self.pres.visibility = "public"
        self.db.commit()
        self.assertTrue(perm.can_view_presentation(self.db, self.pres, None))


class EnforceWriteTest(BaseFixture):
    def _expect(self, req, code):
        with self.assertRaises(HTTPException) as ctx:
            self.call(req)
        self.assertEqual(ctx.exception.status_code, code)

    def test_safe_methods_allowed(self):
        self.call(make_request("GET", "/presentations/1", path_params={"presentation_id": "1"}))

    def test_anonymous_mutation_401(self):
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}",
                                  path_params={"presentation_id": str(self.pres.id)}), 401)

    def test_editor_mutation_ok(self):
        self.call(make_request("PUT", f"/presentations/{self.pres.id}", headers={
            "authorization": "Bearer " + self._issue_key(self.editor)},
            path_params={"presentation_id": str(self.pres.id)}))

    def test_viewer_mutation_403(self):
        key = self._issue_key(self.viewer)
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}", headers={
            "authorization": "Bearer " + key},
            path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_style_is_owner_only(self):
        ed = self._issue_key(self.editor)
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}/style", headers={
            "authorization": "Bearer " + ed},
            path_params={"presentation_id": str(self.pres.id)}), 403)
        ow = self._issue_key(self.owner)
        self.call(make_request("PUT", f"/presentations/{self.pres.id}/style", headers={
            "authorization": "Bearer " + ow},
            path_params={"presentation_id": str(self.pres.id)}))

    def test_read_scope_key_cannot_write(self):
        key = self._issue_key(self.editor, scopes=["read"])
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}", headers={
            "authorization": "Bearer " + key},
            path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_internal_token_bypass(self):
        self.call(make_request("PUT", "/renders/999", headers={
            "x-internal-token": perm.INTERNAL_API_TOKEN}))

    def _bot_with_delegation(self, subject):
        bot = models.User(email="bot@svc", password_hash="", is_bot=True,
                          owner_user_id=self.owner.id)
        self.db.add(bot)
        self.db.flush()
        self.db.add(models.ProjectMember(project_id=self.project.id, user_id=bot.id, role="editor"))
        self.db.add(models.BotDelegation(bot_user_id=bot.id, subject_user_id=subject.id,
                                         approved_at=datetime.datetime.utcnow(),
                                         approved_by=subject.id))
        self.db.commit()
        raw = "pk_bot"
        self.db.add(models.ApiKey(key_hash=_hash_token(raw), owner_id=bot.id,
                                  kind="service", can_delegate=True,
                                  scopes=["read", "write"], is_active=True))
        self.db.commit()
        return bot, raw

    def test_bot_cap_blocks_style_even_for_superadmin_subject(self):
        bot, key = self._bot_with_delegation(self.admin)  # subject = superadmin
        hdrs = {"authorization": "Bearer " + key, "x-on-behalf-of": self.admin.email}
        # content-правка разрешена
        self.call(make_request("PUT", f"/presentations/{self.pres.id}", headers=hdrs,
                               path_params={"presentation_id": str(self.pres.id)}))
        # style (owner-операция) боту запрещена даже от имени админа
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}/style", headers=hdrs,
                                  path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_bot_cannot_manage_apikeys(self):
        bot, key = self._bot_with_delegation(self.owner)
        self._expect(make_request("POST", "/api-keys/", headers={"authorization": "Bearer " + key}), 403)

    def test_personal_key_project_scope_enforced(self):
        other = models.Project(slug="other", title="O", owner_id=self.owner.id)
        self.db.add(other)
        self.db.commit()
        raw = "pk_scope"
        self.db.add(models.ApiKey(key_hash=_hash_token(raw), owner_id=self.owner.id,
                                  kind="personal", project_id=other.id,
                                  scopes=["read", "write"], is_active=True))
        self.db.commit()
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}",
                                  headers={"authorization": "Bearer " + raw},
                                  path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_ai_run_id_validated_for_personal_key(self):
        key = self._issue_key(self.owner)
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}",
                                  headers={"authorization": "Bearer " + key,
                                           "x-ai-run-id": "fake"},
                                  path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_delegation_project_scope_enforced(self):
        other = models.Project(slug="other2", title="O2", owner_id=self.owner.id)
        self.db.add(other)
        self.db.flush()
        bot = models.User(email="bot_scope@svc", password_hash="", is_bot=True,
                          owner_user_id=self.owner.id)
        self.db.add(bot)
        self.db.flush()
        self.db.add(models.ProjectMember(project_id=self.project.id, user_id=bot.id, role="editor"))
        # делегирование ОГРАНИЧЕНО другим проектом
        self.db.add(models.BotDelegation(bot_user_id=bot.id, subject_user_id=self.owner.id,
                                         project_id=other.id,
                                         approved_at=datetime.datetime.utcnow(),
                                         approved_by=self.owner.id))
        raw = "pk_scope_deleg"
        self.db.add(models.ApiKey(key_hash=_hash_token(raw), owner_id=bot.id, kind="service",
                                  can_delegate=True, scopes=["read", "write"], is_active=True))
        self.db.commit()
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}",
                                  headers={"authorization": "Bearer " + raw,
                                           "x-on-behalf-of": self.owner.email},
                                  path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_idempotency_guard_blocks_duplicate(self):
        perm.idempotency_guard(make_request("POST", "/ai/runs", headers={"idempotency-key": "k1"}), self.db)
        with self.assertRaises(HTTPException) as ctx:
            perm.idempotency_guard(make_request("POST", "/ai/runs", headers={"idempotency-key": "k1"}), self.db)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_idempotency_guard_safe_method_ignored(self):
        # GET с ключом не пишет и не падает
        perm.idempotency_guard(make_request("GET", "/x", headers={"idempotency-key": "g1"}), self.db)

    def test_effective_subject_via_delegation(self):
        bot, key = self._bot_with_delegation(self.owner)
        k = self.db.query(models.ApiKey).filter_by(key_hash=_hash_token(key)).first()
        req = make_request("PUT", "/x", headers={
            "authorization": "Bearer " + key, "x-on-behalf-of": self.owner.email})
        eff, on_behalf, atype, err, _deleg = perm.resolve_effective_user(self.db, req, k, bot)
        self.assertIsNone(err)
        self.assertEqual(eff.id, self.owner.id)
        self.assertEqual(on_behalf, self.owner.id)
        self.assertEqual(atype, "service")

    def test_session_requires_csrf(self):
        raw = self._issue_session(self.editor)
        cookie = {"cookie": f"sid={raw}"}
        self._expect(make_request("PUT", f"/presentations/{self.pres.id}", headers=cookie,
                                  path_params={"presentation_id": str(self.pres.id)}), 403)

    def test_session_with_csrf_ok(self):
        raw, csrf = self._issue_session(self.editor, return_csrf=True)
        self.call(make_request("PUT", f"/presentations/{self.pres.id}",
                               headers={"cookie": f"sid={raw}", "x-csrf-token": csrf},
                               path_params={"presentation_id": str(self.pres.id)}))

    # helpers
    def _issue_key(self, user, scopes=None):
        raw = "pk_" + user.email
        self.db.add(models.ApiKey(key_hash=_hash_token(raw), owner_id=user.id,
                                  scopes=scopes or ["read", "write"], is_active=True))
        self.db.commit()
        return raw

    def _issue_session(self, user, return_csrf=False):
        raw = "sess_" + user.email
        csrf = "csrf_" + user.email
        self.db.add(models.UserSession(
            user_id=user.id, token_hash=_hash_token(raw), csrf_token=csrf,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1)))
        self.db.commit()
        return (raw, csrf) if return_csrf else raw


if __name__ == "__main__":
    unittest.main()
