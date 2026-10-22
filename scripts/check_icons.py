#!/usr/bin/env python3
"""Проверка иконок презентации на существование в Iconify.

Ищет все поля `icon` и `*_icon` в payload'ах слайдов и дёргает Iconify API.
Exit 1, если найдены несуществующие иконки (битые в плеере/редакторе).

Запуск: python3 scripts/check_icons.py <presentation_id>
"""
import sys
import time

import requests

try:
    import _api_auth  # noqa: F401  сервисный токен для API (AUTH_MODE=on)
except Exception:
    try:
        from scripts import _api_auth  # noqa: F401
    except Exception:
        pass

BASE = "http://localhost:8001"


def collect_icons(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "icon" or k.endswith("_icon"):
                if isinstance(v, str) and v.strip():
                    out.add(v.strip())
            else:
                collect_icons(v, out)
    elif isinstance(node, list):
        for it in node:
            collect_icons(it, out)


def iconify_ok(icon):
    if ":" not in icon:
        return "noprefix"
    prefix, name = icon.split(":", 1)
    try:
        r = requests.get(f"https://api.iconify.design/{prefix}/{name}.svg", timeout=10)
        if r.status_code == 200:
            return "ok"
        return f"missing({r.status_code})"
    except Exception as e:  # noqa: BLE001
        return f"error({e})"


def main():
    if len(sys.argv) < 2:
        print("usage: python3 scripts/check_icons.py <presentation_id>")
        sys.exit(2)
    pres_id = int(sys.argv[1])
    d = requests.get(f"{BASE}/presentations/{pres_id}").json()
    icons = set()
    for s in d["slides"]:
        collect_icons((s.get("data") or {}).get("payload") or {}, icons)
    if not icons:
        print("Иконок не найдено.")
        return
    bad = 0
    for ic in sorted(icons):
        res = iconify_ok(ic)
        mark = "OK " if res == "ok" else "!! "
        if res != "ok":
            bad += 1
        print(f"{mark}{ic:<40} {res}")
        time.sleep(0.05)
    print(f"\nВсего: {len(icons)}, проблемных: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
