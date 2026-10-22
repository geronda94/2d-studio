"""
trim_payload_text.py — приводит тексты payload к бюджету «воздуха» (docs/COMPONENT_USAGE_RULES.md §3).

Обрезает по границе слова длинные описательные поля, чтобы слайды не превращались в «стены текста»:
  source_note/source/note/caption/footer_note → 80 символов
  description/desc/text                        → 90 символов
  subtitle                                     → 60 символов

Запуск: python scripts/trim_payload_text.py <presentation_id> [--dry]
После прогона рекомендуется визуальная проверка: scripts/qa_audit.py <id> i i+1 (desktop и mobile).
"""
import sys
import requests

from scripts import _api_auth

_api_auth.install()

LIMITS = {
    'source_note': 80, 'source': 80, 'note': 80, 'caption': 80, 'footer_note': 80,
    'description': 90, 'desc': 90, 'text': 90, 'subtitle': 60,
}
BASE = 'http://localhost:8000'


def cut(s: str, lim: int) -> str:
    s = s.strip()
    if len(s) <= lim:
        return s
    part = s[:lim]
    if ' ' in part:
        part = part[:part.rfind(' ')]
    return part.rstrip(' ,.;:—-') + '…'


def walk(o, stats):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and k in LIMITS and not v.strip().startswith('<'):
                nv = cut(v, LIMITS[k])
                if nv != v:
                    o[k] = nv
                    stats.append((k, len(v), len(nv)))
            else:
                walk(v, stats)
    elif isinstance(o, list):
        for v in o:
            walk(v, stats)


def run(pres_id: int, dry: bool = False):
    d = requests.get(f'{BASE}/presentations/{pres_id}', timeout=30).json()
    slides = sorted(d['slides'], key=lambda s: s.get('order_index', 0))
    changed = total = 0
    for s in slides:
        p = (s.get('data') or {}).get('payload')
        if not p:
            continue
        stats = []
        walk(p, stats)
        if not stats:
            continue
        if dry:
            print(s['id'], s['component'], stats)
            changed += 1
            total += len(stats)
            continue
        body = {'slide_id': s['slide_id'], 'component': s['component'], 'start_time': s['start_time'],
                'order_index': s['order_index'], 'title': s.get('title'), 'subtitle': s.get('subtitle'),
                'layout': s.get('layout'), 'data': {'payload': p}}
        r = requests.put(f'{BASE}/presentations/slides/' + str(s['id']), json=body, timeout=30)
        if r.status_code == 200:
            changed += 1
            total += len(stats)
        else:
            print('FAIL', s['id'], r.status_code, r.text[:120])
    print(f'slides changed: {changed}, strings trimmed: {total}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(int(sys.argv[1]), dry='--dry' in sys.argv)