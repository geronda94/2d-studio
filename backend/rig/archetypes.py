"""Canonical SceneRig archetypes and bone-name normalisation.

Pure stdlib. Imported by the validator, the asset compiler and (later) the web
editor. Keep this module free of FastAPI / database imports.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Archetype:
    family: str
    archetype: str
    title: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    face_min: tuple[str, ...] = ()

    @property
    def slug(self) -> str:
        return f"{self.family}/{self.archetype}"

    def all_bones(self) -> tuple[str, ...]:
        return self.required + self.optional


def _pair(*names: str) -> tuple[str, ...]:
    return tuple(f"{n}.{s}" for s in ("L", "R") for n in names)


HUMANOID = Archetype(
    family="human",
    archetype="humanoid",
    title="Humanoid",
    required=(
        "hips", "spine", "chest", "neck", "head",
        *_pair("shoulder"),
        *_pair("upperArm"),
        *_pair("lowerArm"),
        *_pair("hand"),
        *_pair("upperLeg"),
        *_pair("lowerLeg"),
        *_pair("foot"),
        *_pair("toe"),
    ),
    optional=(
        "root", "spine1", "spine2", "headTop", "jaw",
        *_pair("eye"),
        *_pair("toeEnd"),
        *_pair(
            "thumb1", "thumb2", "thumb3", "thumb4",
            "index1", "index2", "index3", "index4",
            "middle1", "middle2", "middle3", "middle4",
            "ring1", "ring2", "ring3", "ring4",
            "pinky1", "pinky2", "pinky3", "pinky4",
        ),
    ),
    face_min=("jawOpen", "viseme_sil"),
)

QUADRUPED = Archetype(
    family="animal",
    archetype="quadruped",
    title="Quadruped",
    required=(
        "hips", "spine", "chest", "neck", "head",
        *_pair("shoulder"),
        *_pair("upperArm"),
        *_pair("lowerArm"),
        *_pair("hand"),
        *_pair("upperLeg"),
        *_pair("lowerLeg"),
        *_pair("foot"),
        *_pair("toe"),
    ),
    optional=(
        "root", "spine1", "jaw", "tail1", "tail2", "tail3", "tail4",
        *_pair("ear"),
        *_pair("eye"),
    ),
    face_min=(),
)

AVIAN = Archetype(
    family="winged",
    archetype="avian",
    title="Avian",
    required=(
        "hips", "spine", "chest", "neck", "head",
        *_pair("wingRoot"),
        *_pair("wingMid"),
        *_pair("wingTip"),
        *_pair("upperLeg"),
        *_pair("lowerLeg"),
        *_pair("foot"),
    ),
    optional=(
        "root", "spine1", "beak", "jaw", "tail1", "tail2", "tail3",
        *_pair("eye"),
        *_pair("toe"),
        *_pair("wingHind"),
    ),
    face_min=(),
)

INSECTOID = Archetype(
    family="winged",
    archetype="insectoid",
    title="Insectoid",
    required=(
        "thorax", "abdomen", "head",
        *_pair("wingRoot"),
        *_pair("wingMid"),
        *_pair("wingTip"),
        *_pair("legFront"),
        *_pair("legMid"),
        *_pair("legHind"),
    ),
    optional=(
        "root", "stinger", "wingHind.L", "wingHind.R",
        *_pair("antenna"),
        *_pair("mandible"),
        *_pair("eye"),
        "legFront1.L", "legFront2.L", "legFront3.L",
        "legFront1.R", "legFront2.R", "legFront3.R",
        "legMid1.L", "legMid2.L", "legMid3.L",
        "legMid1.R", "legMid2.R", "legMid3.R",
        "legHind1.L", "legHind2.L", "legHind3.L",
        "legHind1.R", "legHind2.R", "legHind3.R",
    ),
    face_min=(),
)

ARCHETYPES: dict[str, Archetype] = {
    "humanoid": HUMANOID,
    "quadruped": QUADRUPED,
    "avian": AVIAN,
    "insectoid": INSECTOID,
}

FAMILY_TO_ARCHETYPES = {
    "human": ("humanoid",),
    "animal": ("quadruped",),
    "winged": ("avian", "insectoid"),
}


# ── name normalisation ──────────────────────────────────────────────────────

# Explicit source-name aliases (already lower-case, no separators).
ALIASES: dict[str, str] = {
    # root / pelvis
    "root": "root",
    "armature": "root",
    "skeleton": "root",
    "hips": "hips",
    "pelvis": "hips",
    "hip": "hips",
    # spine
    "spine": "spine",
    "spine1": "spine1",
    "spine2": "chest",
    "spine3": "neck",
    "spine4": "head",
    "spine001": "spine1",
    "spine002": "chest",
    "spine003": "neck",
    "spine004": "head",
    "chest": "chest",
    "upperchest": "chest",
    "neck": "neck",
    "head": "head",
    "headtop": "headTop",
    "headtopend": "headTop",
    "jaw": "jaw",
    # face helpers
    "eye": "eye",
    "lefteye": "eye.L",
    "righteye": "eye.R",
    "beak": "beak",
    # animal / winged
    "tail": "tail1",
    "tail1": "tail1",
    "tail2": "tail2",
    "tail3": "tail3",
    "tail4": "tail4",
    "ear": "ear",
    "wingroot": "wingRoot",
    "wingmid": "wingMid",
    "wingtip": "wingTip",
    "winghind": "wingHind",
    "thorax": "thorax",
    "abdomen": "abdomen",
    "stinger": "stinger",
    "antenna": "antenna",
    "mandible": "mandible",
    "legfront": "legFront",
    "legmid": "legMid",
    "leghind": "legHind",
    # VRM 1.0 humanoid (J_Bip_*)
    "jbipchips": "hips",
    "jbipcspine": "spine",
    "jbipcchest": "chest",
    "jbipcupperchest": "chest",
    "jbipcneck": "neck",
    "jbipchead": "head",
    "jbiplshoulder": "shoulder.L",
    "jbiprshoulder": "shoulder.R",
    "jbiplupperarm": "upperArm.L",
    "jbiprupperarm": "upperArm.R",
    "jbipllowerarm": "lowerArm.L",
    "jbiprlowerarm": "lowerArm.R",
    "jbiplhand": "hand.L",
    "jbiprhand": "hand.R",
    "jbiplupperleg": "upperLeg.L",
    "jbiprupperleg": "upperLeg.R",
    "jbipllowerleg": "lowerLeg.L",
    "jbiprlowerleg": "lowerLeg.R",
    "jbiplfoot": "foot.L",
    "jbiprfoot": "foot.R",
    "jbipltoebase": "toe.L",
    "jbiprtoebase": "toe.R",
    "jadjlfaceeye": "eye.L",
    "jadjrfaceeye": "eye.R",
}

# Base names after a side suffix has been removed.
BASE_ALIASES: dict[str, str] = {
    "shoulder": "shoulder",
    "clavicle": "shoulder",
    "upperarm": "upperArm",
    "arm": "upperArm",
    "lowerarm": "lowerArm",
    "forearm": "lowerArm",
    "hand": "hand",
    "wrist": "hand",
    "upleg": "upperLeg",
    "upperleg": "upperLeg",
    "thigh": "upperLeg",
    "leg": "lowerLeg",
    "lowerleg": "lowerLeg",
    "shin": "lowerLeg",
    "calf": "lowerLeg",
    "foot": "foot",
    "ankle": "foot",
    "toe": "toe",
    "toebase": "toe",
    "toeend": "toeEnd",
    "eye": "eye",
    "ear": "ear",
    "wingroot": "wingRoot",
    "wingmid": "wingMid",
    "wingtip": "wingTip",
    "winghind": "wingHind",
    "legfront": "legFront",
    "legmid": "legMid",
    "leghind": "legHind",
    "antenna": "antenna",
    "mandible": "mandible",
    "thumb": "thumb",
    "index": "index",
    "middle": "middle",
    "ring": "ring",
    "pinky": "pinky",
}

_SIDE_LEFT = re.compile(r"(?:^|[._\- ])l(?:$|[._\- ])|left", re.I)
_SIDE_RIGHT = re.compile(r"(?:^|[._\- ])r(?:$|[._\- ])|right", re.I)
_TRAILING_SIDE = re.compile(r"([._\-])([lr])$", re.I)
_DIGIT = re.compile(r"^(thumb|index|middle|ring|pinky)(\d+)$", re.I)

_CANON_BY_KEY: dict[str, str] = {}
for _arch in ARCHETYPES.values():
    for _bone in _arch.all_bones():
        _CANON_BY_KEY[_bone.lower().replace(".", "").replace("_", "").replace("-", "")] = _bone


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _side_of(name: str) -> str | None:
    raw = name.strip()
    if _SIDE_LEFT.search(raw):
        return "L"
    if _SIDE_RIGHT.search(raw):
        return "R"
    m = _TRAILING_SIDE.search(raw)
    if m:
        return m.group(2).upper()
    return None


def _strip_side(name: str) -> str:
    raw = name.strip()
    raw = re.sub(r"(?i)(left|right)", "", raw)
    raw = re.sub(r"[._\-][lr]$", "", raw, flags=re.I)
    return raw


def normalize_bone(name: str) -> str | None:
    """Map any known rig name to its canonical SceneRig name.

    Returns None when the bone is unknown; callers keep such bones as extras.
    Never raises.
    """
    if not name or not isinstance(name, str):
        return None
    raw = name.strip()
    if not raw:
        return None
    # Drop namespaces such as "mixamorig:" or "Armature|".
    raw = raw.split(":")[-1].split("|")[-1].strip()
    key = _key(raw)

    # 1. Explicit alias table.
    if key in ALIASES:
        return ALIASES[key]

    # 2. Direct canonical spelling (upperArm.L, upperArm_L, upperArmL).
    if key in _CANON_BY_KEY:
        return _CANON_BY_KEY[key]

    # 3. Side + base alias.
    side = _side_of(raw)
    base_raw = _strip_side(raw)
    base_key = _key(base_raw)
    if base_key in BASE_ALIASES:
        base = BASE_ALIASES[base_key]
        if side and base not in ("eye",):
            return f"{base}.{side}"
        if base == "eye" and side:
            return f"eye.{side}"
        if base in ("wingRoot", "wingMid", "wingTip", "wingHind", "ear", "legFront", "legMid", "legHind", "antenna", "mandible"):
            return f"{base}.{side}" if side else base
        return base

    # 4. Fingers: LeftHandThumb1 -> thumb1.L
    m = _DIGIT.match(base_key.replace("hand", "", 1))
    if m:
        base = f"{m.group(1).lower()}{m.group(2)}"
        return f"{base}.{side}" if side else base

    # 5. Segment suffixes: legFront1, legMid2, legHind3.
    m = re.match(r"^(legfront|legmid|leghind)(\d+)$", base_key)
    if m:
        base = {"legfront": "legFront", "legmid": "legMid", "leghind": "legHind"}[m.group(1)]
        return f"{base}{m.group(2)}.{side}" if side else f"{base}{m.group(2)}"

    return None


def map_bones(names: list[str]) -> tuple[dict[str, str], list[str], dict[str, list[str]]]:
    """Map source bone names to canonical names.

    Returns (mapping, unmapped, duplicates) where duplicates lists canonical
    names that received more than one source bone.
    """
    mapping: dict[str, str] = {}
    unmapped: list[str] = []
    duplicates: dict[str, list[str]] = {}
    for name in names:
        canon = normalize_bone(name)
        if not canon:
            unmapped.append(name)
            continue
        if canon in mapping:
            duplicates.setdefault(canon, [mapping[canon]]).append(name)
            continue
        mapping[canon] = name
    return mapping, unmapped, duplicates


def infer_archetype(names: list[str]) -> Archetype:
    """Pick the archetype with the best coverage of required bones."""
    mapping, _, _ = map_bones(names)
    mapped = set(mapping)
    best: tuple[float, int, Archetype] | None = None
    for arch in ARCHETYPES.values():
        req = set(arch.required)
        coverage = len(req & mapped) / len(req) if req else 0.0
        optional_hits = len(set(arch.optional) & mapped)
        score = (coverage, optional_hits, arch)
        if best is None or score[:2] > best[:2]:
            best = score
    return best[2] if best else HUMANOID


def required_missing(archetype: Archetype, mapping: dict[str, str]) -> list[str]:
    return [b for b in archetype.required if b not in mapping]


def face_min_missing(archetype: Archetype, morphs: list[str]) -> list[str]:
    present = set(morphs)
    return [m for m in archetype.face_min if m not in present]


def archetype_by_name(name: str) -> Archetype | None:
    return ARCHETYPES.get((name or "").strip().lower())


def archetypes_payload() -> list[dict]:
    return [
        {
            "family": a.family,
            "archetype": a.archetype,
            "title": a.title,
            "slug": a.slug,
            "required": list(a.required),
            "optional": list(a.optional),
            "face_min": list(a.face_min),
        }
        for a in ARCHETYPES.values()
    ]
