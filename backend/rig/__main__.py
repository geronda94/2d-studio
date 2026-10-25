"""CLI: python -m backend.rig <command> ...

Commands:
  archetypes                 list canonical archetypes and bones
  scan <glb>                 inspect/validate a GLB
  validate <json|glb>        validate a manifest or a GLB
  compile <manifest>         rename bones to canonical and write dist GLB
  bake <manifest> <clip>     bake a *.sclip.json into the GLB

Exit codes: 0 = ok, 1 = validation errors, 2 = cannot read input.
"""
from __future__ import annotations

import argparse
import json
import sys

from .archetypes import archetypes_payload, archetype_by_name
from .bake import bake_clip
from .compile import compile_rig
from .validate import print_report, validate_glb, validate_path


def _json_out(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_archetypes(_args) -> int:
    if _args.json:
        _json_out(archetypes_payload())
    else:
        for a in archetypes_payload():
            print(f"{a['slug']:<18} {a['title']}")
            print(f"  required: {', '.join(a['required'])}")
            if a["optional"]:
                print(f"  optional: {', '.join(a['optional'])}")
            if a["face_min"]:
                print(f"  face min: {', '.join(a['face_min'])}")
            print()
    return 0


def cmd_scan(args) -> int:
    arch = None
    if args.archetype:
        arch = archetype_by_name(args.archetype)
        if arch is None:
            print(f"unknown archetype: {args.archetype}", file=sys.stderr)
            print("known: " + ", ".join(a["archetype"] for a in archetypes_payload()),
                  file=sys.stderr)
            return 2
    rep = validate_glb(args.path, arch)
    if args.json:
        _json_out(rep.to_dict())
    else:
        print_report(rep)
    return 0 if rep.ok else 1


def cmd_validate(args) -> int:
    rep = validate_path(args.path, args.archetype)
    if args.json:
        _json_out(rep.to_dict())
    else:
        print_report(rep)
    return 0 if rep.ok else 1


def cmd_bake(args) -> int:
    rep, out = bake_clip(args.manifest, args.clip, args.out, replace=not args.append)
    if args.json:
        _json_out({"report": rep.to_dict(), "output": str(out)})
    else:
        print_report(rep)
        print(f"output: {out}")
    return 0 if rep.ok else 1


def cmd_compile(args) -> int:
    rep, out = compile_rig(args.path, args.out)
    if args.json:
        _json_out({"report": rep.to_dict(), "output": str(out)})
    else:
        print_report(rep)
        print(f"output: {out}")
    return 0 if rep.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.rig",
                                     description="SceneRig validator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_arch = sub.add_parser("archetypes", help="list canonical archetypes")
    p_arch.add_argument("--json", action="store_true")
    p_arch.set_defaults(func=cmd_archetypes)

    p_scan = sub.add_parser("scan", help="inspect/validate a GLB")
    p_scan.add_argument("path")
    p_scan.add_argument("--archetype", default=None)
    p_scan.add_argument("--json", action="store_true")
    p_scan.set_defaults(func=cmd_scan)

    p_val = sub.add_parser("validate", help="validate a manifest or GLB")
    p_val.add_argument("path")
    p_val.add_argument("--archetype", default=None)
    p_val.add_argument("--json", action="store_true")
    p_val.set_defaults(func=cmd_validate)

    p_bake = sub.add_parser("bake", help="bake a sceneclip into the GLB")
    p_bake.add_argument("manifest")
    p_bake.add_argument("clip")
    p_bake.add_argument("--out", default=None)
    p_bake.add_argument("--append", action="store_true",
                        help="keep an existing animation with the same name")
    p_bake.add_argument("--json", action="store_true")
    p_bake.set_defaults(func=cmd_bake)

    p_compile = sub.add_parser("compile", help="rename bones to canonical and write dist")
    p_compile.add_argument("path")
    p_compile.add_argument("--out", default=None)
    p_compile.add_argument("--json", action="store_true")
    p_compile.set_defaults(func=cmd_compile)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"not found: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
