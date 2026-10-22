"""Синхронизирует componentsRegistry.js с метаданными scripts/_orthodox_meta/*.json.

Идемпотентно: добавляет import и запись в componentsMap для каждого slug, которого нет.
Запуск: python scripts/sync_registry_from_meta.py
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "scripts", "_orthodox_meta")
REG = os.path.join(ROOT, "core", "src", "config", "componentsRegistry.js")


def main():
    slugs = sorted(json.load(open(p, encoding="utf-8"))["slug"]
                   for p in glob.glob(os.path.join(META, "*.json")))
    src = open(REG, encoding="utf-8").read()

    missing = [s for s in slugs if f"import {s} from" not in src]
    if not missing:
        print("registry up to date")
        return

    imports = "".join(f"import {s} from '../components/ui/{s}.vue'\n" for s in missing)
    # после последнего ui-импорта
    last = None
    for m in re.finditer(r"import \w+ from '\.\./components/ui/[\w]+\.vue'\n", src):
        last = m
    assert last, "no ui imports found"
    src = src[:last.end()] + imports + src[last.end():]

    entries = "".join(f"  {s},\n" for s in missing)
    idx = src.rstrip().rfind("}")
    head = src[:idx].rstrip()
    if not head.endswith(","):
        head += ","
    src = head + "\n" + entries + src[idx:]

    open(REG, "w", encoding="utf-8").write(src)
    print(f"registry patched: +{len(missing)} ({', '.join(missing)})")


if __name__ == "__main__":
    main()
