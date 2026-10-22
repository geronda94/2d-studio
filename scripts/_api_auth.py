"""Сервисная авторизация для скриптов, обращающихся к API (AUTH_PLAN).

Импортируется сайд-эффектом: ставит внутренний токен (X-Internal-Token) в заголовки
всех последующих `requests.*` вызовов. Токен берётся из env INTERNAL_API_TOKEN,
иначе из .env в корне проекта.

Использование: `import _api_auth  # noqa: F401` в начале скрипта.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "backend", "::1", "host.docker.internal"}


def _is_local(url) -> bool:
    try:
        host = urlparse(str(url or "")).hostname
        return host in _LOCAL_HOSTS
    except Exception:
        return False


def _in_container() -> bool:
    # В контейнере бэкенд слушает 8000; на хосте проброшен 8001.
    return os.path.exists("/app")


def _fix_url(url):
    """Внутри контейнера localhost:8002 недоступен → переписываем на 8000."""
    u = str(url or "")
    if _in_container() and _is_local(u) and ":8002" in u:
        return u.replace(":8002", ":8000")
    return url


def _load_token():
    tok = os.environ.get("INTERNAL_API_TOKEN")
    if tok:
        return tok.strip()
    try:
        for base in (Path(__file__).resolve().parent.parent,
                     Path.cwd(), Path.cwd().parent):
            envf = base / ".env"
            if envf.exists():
                for line in envf.read_text(encoding="utf-8").splitlines():
                    if line.startswith("INTERNAL_API_TOKEN="):
                        return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def install():
    tok = _load_token()
    if not tok:
        return
    try:
        import requests
    except Exception:
        return
    header = {"X-Internal-Token": tok}
    for method in ("get", "post", "put", "patch", "delete"):
        original = getattr(requests, method, None)
        if original is None:
            continue

        def make(orig):
            def wrapped(*args, **kwargs):
                url = args[0] if args else kwargs.get("url")
                # Токен — ТОЛЬКО внутреннему API, не внешним хостам (иначе утечка).
                if _is_local(url):
                    url = _fix_url(url)
                    headers = dict(kwargs.pop("headers", {}) or {})
                    headers.update(header)
                    kwargs["headers"] = headers
                if args:
                    args = (url,) + tuple(args[1:])
                else:
                    kwargs["url"] = url
                return orig(*args, **kwargs)
            return wrapped

        setattr(requests, method, make(original))


install()
