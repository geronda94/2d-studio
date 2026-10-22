#!/usr/bin/env python3
"""Аутентификация агента для API (AUTH_MODE=on, enterprise).

Логинится супер-админом из Presentation/.env (ADMIN_EMAIL/ADMIN_PASSWORD) и
патчит `requests` так, что ВСЕ последующие вызовы идут через авторизованную
сессию; для POST/PUT/PATCH/DELETE добавляется заголовок X-CSRF-Token.

Использование: `import agent_auth` ПЕРВОЙ строкой в сборочных скриптах.
Если AUTH_MODE=off — просто ничего не делает (логин тихо пропускается).
"""
import os
import sys

import requests

BASE = os.environ.get("PRES_BASE", "http://localhost:8001")
_ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def _read_env():
    vals = {}
    try:
        with open(_ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def _authenticate():
    env = _read_env()
    email = env.get("ADMIN_EMAIL")
    password = env.get("ADMIN_PASSWORD")
    if not email or not password:
        print("[auth] ADMIN_EMAIL/ADMIN_PASSWORD не найдены — работаю без сессии", flush=True)
        return
    s = requests.Session()
    try:
        r = s.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=15)
    except Exception as e:  # noqa: BLE001
        print(f"[auth] login недоступен: {e}", flush=True)
        return
    if r.status_code != 200:
        print(f"[auth] login {r.status_code}: {r.text[:120]}", flush=True)
        return
    csrf = s.cookies.get("csrf")
    print(f"[auth] ok ({r.json().get('user', {}).get('email')}) mode={r.json().get('mode')}", flush=True)

    methods = ("get", "post", "put", "patch", "delete")

    def _wrap(method):
        def call(url, *a, **kw):
            headers = dict(kw.pop("headers", {}) or {})
            if method != "get" and csrf:
                headers.setdefault("X-CSRF-Token", csrf)
            kw["headers"] = headers
            return s.request(method.upper(), url, *a, **kw)
        return call

    for m in methods:
        setattr(requests, m, _wrap(m))
    requests.Session  # noqa: B018


_authenticate()
