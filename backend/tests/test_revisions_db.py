"""Тесты версий проекта (ENTERPRISE Ф2): снапшот, дедуп, diff, restore."""
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models, revisions
from backend.database import Base


def make_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


class RevisionsTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        p = models.Project(slug="p", title="P", owner_id=1, config={"brand": {"name": "A"}})
        self.db.add(p)
        self.db.flush()
        self.project_id = p.id
        f = models.Folder(slug="f", title="F", project_id=p.id)
        self.db.add(f)
        self.db.flush()
        pres = models.Presentation(title="Pres", visibility="public")
        self.db.add(pres)
        self.db.flush()
        self.pres_id = pres.id
        f.presentations.append(pres)
        for i, sid in enumerate(("s1", "s2")):
            sl = models.Slide(presentation_id=pres.id, slide_id=sid, component="X",
                              start_time=i * 1000, order_index=i, title=f"t{i}")
            self.db.add(sl)
            self.db.flush()
            self.db.add(models.SlideData(slide_id=sl.id, payload={"title": f"t{i}"}))
        self.db.add(models.ProjectMember(project_id=p.id, user_id=99, role="editor"))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_snapshot_and_dedup(self):
        rev = revisions.create_revision(self.db, self.project_id, source="manual", force=True)
        self.assertIsNotNone(rev)
        self.assertEqual(rev.n, 1)
        self.assertGreater(rev.size_bytes, 0)
        # без изменений — дедуп
        self.assertIsNone(revisions.create_revision(self.db, self.project_id))

    def test_diff_and_restore(self):
        rev = revisions.create_revision(self.db, self.project_id, source="manual", force=True)
        # мутации: меняем заголовок, удаляем слайд, меняем config
        s1 = self.db.query(models.Slide).filter_by(slide_id="s1").first()
        s1.title = "changed"
        self.db.commit()
        s2 = self.db.query(models.Slide).filter_by(slide_id="s2").first()
        self.db.delete(s2)
        self.db.commit()
        proj = self.db.query(models.Project).filter_by(id=self.project_id).first()
        proj.config = {"brand": {"name": "B"}}
        self.db.commit()

        # удалённый из текущего слайд s2 при откате ВЕРНЁТСЯ → added
        diff = revisions.diff_snapshot(self.db, self.project_id, rev.snapshot)
        self.assertEqual(diff["slides"]["added"], 1)
        self.assertEqual(diff["slides"]["removed"], 0)
        self.assertGreaterEqual(diff["slides"]["changed"], 1)

        res = revisions.restore_snapshot(self.db, self.project_id, rev.snapshot, dry_run=False)
        self.assertFalse(res["dry_run"])

        # слайды восстановлены
        slides = self.db.query(models.Slide).filter_by(presentation_id=self.pres_id).all()
        self.assertEqual(len(slides), 2)
        s1 = self.db.query(models.Slide).filter_by(slide_id="s1").first()
        self.assertEqual(s1.title, "t0")
        proj = self.db.query(models.Project).filter_by(id=self.project_id).first()
        self.assertEqual(proj.config["brand"]["name"], "A")
        self.assertGreaterEqual(proj.version, 1)
        # создана ревизия restore
        last = revisions.list_revisions(self.db, self.project_id)[0]
        self.assertEqual(last.source, "restore")

    def test_restore_keeps_members(self):
        rev = revisions.create_revision(self.db, self.project_id, source="manual", force=True)
        revisions.restore_snapshot(self.db, self.project_id, rev.snapshot, dry_run=False)
        # участники не затираются контентным откатом
        self.assertEqual(self.db.query(models.ProjectMember).filter_by(
            project_id=self.project_id).count(), 1)

    def test_restore_deletes_extra_folder_and_tokens(self):
        # presentation-scope токен до снапшота
        self.db.add(models.DesignToken(presentation_id=self.pres_id, token_key="bg-base",
                                       token_type="color", value="#000", is_custom=True))
        self.db.commit()
        rev = revisions.create_revision(self.db, self.project_id, source="manual", force=True)
        # после снапшота: новая папка + участник, привязанный к ней, + удалили токен
        extra = models.Folder(slug="extra", title="Extra", project_id=self.project_id)
        self.db.add(extra)
        self.db.flush()
        m = self.db.query(models.ProjectMember).filter_by(project_id=self.project_id).first()
        m.scope_folder_id = extra.id
        self.db.query(models.DesignToken).filter_by(presentation_id=self.pres_id).delete()
        self.db.commit()
        revisions.restore_snapshot(self.db, self.project_id, rev.snapshot, dry_run=False)
        # лишняя папка удалена, ссылка участника на неё снята (FK-безопасность)
        self.assertIsNone(self.db.query(models.Folder).filter_by(slug="extra").first())
        self.db.expire_all()
        m = self.db.query(models.ProjectMember).filter_by(project_id=self.project_id).first()
        self.assertIsNone(m.scope_folder_id)
        # presentation-scope токен восстановлен
        self.assertIsNotNone(self.db.query(models.DesignToken).filter_by(
            presentation_id=self.pres_id, token_key="bg-base").first())
        # версия презентации инкрементнута
        pres = self.db.query(models.Presentation).filter_by(id=self.pres_id).first()
        self.assertGreaterEqual(pres.version, 1)

    def test_dry_run_makes_no_changes(self):
        rev = revisions.create_revision(self.db, self.project_id, source="manual", force=True)
        s1 = self.db.query(models.Slide).filter_by(slide_id="s1").first()
        s1.title = "changed"
        self.db.commit()
        revisions.restore_snapshot(self.db, self.project_id, rev.snapshot, dry_run=True)
        s1 = self.db.query(models.Slide).filter_by(slide_id="s1").first()
        self.assertEqual(s1.title, "changed")  # dry_run ничего не тронул


if __name__ == "__main__":
    unittest.main()
