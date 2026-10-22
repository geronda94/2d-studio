"""Сверка: БД components.slug <-> componentsMap (registry) <-> .vue-файлы.

Запуск с хоста: python scripts/check_consistency.py (БД localhost:5435).
Код выхода 1 при дрейфе. Источник правды для slug — БД (seed_components.py).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

REGISTRY = os.path.join(ROOT, "core/src/config/componentsRegistry.js")
# Внутренние building blocks: есть .vue, нет slug в БД, не входят в componentsMap
INTERNAL = {"RoiCalculator", "Ecosystem", "AdvancedVideoPlayer",
            "ChatMockup", "BeforeAfter", "AnimatedStats",
            "CodeWindow", "TechCard", "ProgressScale",
            # внутренние примитивы/панели проекта (есть .vue, нет slug в БД)
            "Lampada", "WindowHeader", "PageSkeleton",
            "ProjectBrand", "ProjectHistory", "ProjectTeam"}


def registry_slugs():
    t = open(REGISTRY).read()
    # ключи вида `  Foo,` внутри componentsMap (shorthand properties)
    m = re.search(r"componentsMap\s*=\s*\{(.*?)\}", t, re.S)
    body = m.group(1) if m else t
    return set(re.findall(r"^\s*([A-Z]\w+)\s*,?\s*$", body, re.M))


def vue_files():
    out = set()
    for d in ("core/src/components/ui", "core/src/components/slides"):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            out.update(f[:-4] for f in os.listdir(p) if f.endswith(".vue"))
    return out


def db_slugs():
    from sqlalchemy import create_engine, text
    from backend.database import SQLALCHEMY_DATABASE_URL
    eng = create_engine(SQLALCHEMY_DATABASE_URL)
    with eng.connect() as c:
        return set(r[0] for r in c.execute(text("SELECT slug FROM components")))


def main():
    reg, vue, errors = registry_slugs(), vue_files(), []
    try:
        db = db_slugs()
    except Exception as e:
        print(f"БД недоступна: {e}\nПроверяю только registry <-> файлы.")
        db = None
    # 1. registry без .vue-файла
    for s in sorted(reg - vue):
        errors.append(f"registry без файла: {s}")
    # 2. standalone .vue без slug и без registry (исключая INTERNAL/модалки)
    if db is not None:
        for s in sorted(vue - db - reg - INTERNAL):
            # модалки/примитивы/редактор: *Modal, *Divider, *Picker, *Editor, TimePicker, It2bLogo, Safe*Preview
            if re.search(r"(Modal|Divider|Picker|Editor|Logo|Preview)$", s):
                continue
            errors.append(f".vue без slug в БД и registry: {s} (добавь в seed или INTERNAL)")
        # 3. slug в БД без registry/file
        for s in sorted(db - reg):
            errors.append(f"БД без registry: {s}")
        for s in sorted(db - vue):
            errors.append(f"БД без .vue-файла: {s}")
    print(f"registry={len(reg)} db={len(db) if db else '?'} vue={len(vue)}")
    if errors:
        print("ОШИБКИ:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK: дрейфа нет.")


if __name__ == "__main__":
    main()
