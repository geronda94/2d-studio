"""Статический guard контракта стиля компонентов (docs/COMPONENT_STYLE_CONTRACT.md).

Ловит те же дефекты, что правили вручную: материал айтема не из варианта,
хардкод радиуса/тени карточки, «сырой» hex, getColorAlpha по bg-base.

Запуск с хоста: python3 scripts/style_guard.py [--all]
  по умолчанию — эвристика (условные/шумные попадания отсеиваются);
  --all — показать всё.

Код выхода 1 при наличии нарушений (кроме явного whitelist-а).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "core/src/config/componentsRegistry.js")

# Chrome редактора — вне .slides-container, фикс. тёмный :root. Не проверяем.
CHROME = re.compile(r"(Modal|Picker|Editor|Skeleton|Preview|Divider|Logo|Toast|Confirm|EmptyState)$")
# Внутренние building-blocks, которые обязаны следовать контракту наравне с контентными.
INTERNAL_CONTENT = {"ChatMockup", "CodeWindow", "BeforeAfter", "RoiCalculator",
                    "Ecosystem", "AnimatedStats", "ProgressScale", "TechCard"}
# Осознанные исключения (docs/COMPONENT_STYLE_CONTRACT.md §5).
DARKCODE = {"TerminalMockup", "CodeWindow", "CodeExplain", "AdvancedVideoPlayer",
            "BrowserMockup", "CodeComparisonSlide"}
BRAND = {"It2bLogo", "Lampada", "PortraitLampSlide", "ProjectBrand", "OutroSlide"}
PAPER = {"ReceiptCard"}
SERVICE = {"EndMarkerSlide"}

# Паттерн -> (метка, регэксп, фильтр-разрешение)
CHECKS = [
    ("material-bg", re.compile(r"\bbg-(?:bg-base|bg-surface|bg-surface-hover|bg-hover)\b(?![/\w])")),
    ("material-var", re.compile(r"var\(\s*--(?:bg-base|bg-surface|bg-surface-hover|bg-hover)\s*[,)]")),
    ("bg-base-alpha", re.compile(r"getColorAlpha\(\s*'var\(--bg-base\)'")),
    ("radius-card", re.compile(r"\brounded-(?:sm|md|lg|xl|2xl|3xl)\b")),
    ("shadow-card", re.compile(r"\bshadow-(?:sm|md|lg|xl|2xl|inner)\b")),
]
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def registry_and_files():
    t = open(REGISTRY).read()
    body = re.search(r"componentsMap\s*=\s*\{(.*?)\}", t, re.S).group(1)
    reg = set(re.findall(r"^\s*([A-Z]\w+)\s*,?\s*$", body, re.M))
    files = {}
    for d in ("core/src/components/ui", "core/src/components/slides"):
        p = os.path.join(ROOT, d)
        for f in os.listdir(p):
            if f.endswith(".vue"):
                files[f[:-4]] = os.path.join(p, f)
    return reg, files


def allowed(name):
    if CHROME.search(name):
        return True
    if name in DARKCODE | BRAND | PAPER | SERVICE:
        return True
    return False


def scan(name, path):
    hits = []
    for i, ln in enumerate(open(path, encoding="utf-8"), 1):
        s = ln.strip()
        if s.startswith(("//", "/*", "*", "<!--")):
            continue
        for label, rx in CHECKS:
            if not rx.search(ln):
                continue
            # var(--item-*) — это правильный вариант, не дефект
            if "--item" in ln:
                continue
            # rounded-full у точек/аватаров/индикаторов — легитимен
            if label == "radius-card" and "rounded-full" in ln:
                continue
            hits.append((label, i, s[:150]))
        if HEX.search(ln) and "text-[#" not in ln:
            # ProductCard.resolveColor: legacy-hex -> token маппинг (не хардкод цвета)
            if name == "ProductCard" and "lower ===" in ln:
                continue
            hits.append(("hex", i, s[:150]))
    return hits


def main():
    show_all = "--all" in sys.argv
    reg, files = registry_and_files()
    targets = {n for n in (reg | INTERNAL_CONTENT) if n in files and not allowed(n)}
    total = 0
    for n in sorted(targets):
        hits = scan(n, files[n])
        if hits:
            total += len(hits)
            print(f"\n### {n}  ({os.path.relpath(files[n], ROOT)})")
            for label, i, t in hits:
                print(f"  {label:14} L{i}: {t}")
    print(f"\nchecked={len(targets)} violations={total}")
    if total:
        print("См. docs/COMPONENT_STYLE_CONTRACT.md §3 — материал/радиус/тень только через --item-*.")
        sys.exit(1 if show_all or total else 0)
    print("OK: контракт стиля соблюдён.")


if __name__ == "__main__":
    main()
